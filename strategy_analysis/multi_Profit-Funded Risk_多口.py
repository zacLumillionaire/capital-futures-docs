# 回測_Profit-Funded Risk_多口.py
import logging
from datetime import time, date
from decimal import Decimal
from dataclasses import dataclass, field
from enum import Enum, auto
from app_setup import init_all_db_pools
import shared

# 🚀 數據源配置
USE_SQLITE = True  # True: 使用本機SQLite, False: 使用遠程PostgreSQL

if USE_SQLITE:
    import sqlite_connection

# --- 設定日誌 ---
logging.basicConfig(level=logging.INFO, format='[%(asctime)s] %(levelname)s [%(name)s.%(funcName)s:%(lineno)d] %(message)s', datefmt='%Y-%m-%dT%H:%M:%S%z')
logger = logging.getLogger(__name__)

# ==============================================================================
# 1. 策略設定與輔助函式
# ==============================================================================
class StopLossType(Enum):
    RANGE_BOUNDARY = auto(); OPENING_PRICE = auto(); FIXED_POINTS = auto()

@dataclass
class LotRule:
    """描述「單一口部位」的出場邏輯。"""
    use_trailing_stop: bool = True
    fixed_tp_points: Decimal | None = None
    trailing_activation: Decimal | None = None
    trailing_pullback: Decimal | None = None
    protective_stop_multiplier: Decimal | None = None

@dataclass
class RangeFilter:
    """區間過濾濾網設定"""
    use_range_size_filter: bool = False
    max_range_points: Decimal = Decimal(50)        # 區間寬度上限

@dataclass
class RiskConfig:
    """風險管理濾網設定"""
    use_risk_filter: bool = False                  # 是否啟用風險濾網
    daily_loss_limit: Decimal = Decimal(150)       # 每日虧損限制(點數)
    profit_target: Decimal = Decimal(200)          # 每日獲利目標

@dataclass
class StopLossConfig:
    """停損設定濾網"""
    stop_loss_type: StopLossType = StopLossType.RANGE_BOUNDARY
    fixed_stop_loss_points: Decimal = Decimal(15)  # 固定點數停損
    use_range_midpoint: bool = False               # 使用區間中點

@dataclass
class StrategyConfig:
    """策略設定的中央控制面板。"""
    trade_size_in_lots: int = 3
    stop_loss_type: StopLossType = StopLossType.RANGE_BOUNDARY
    fixed_stop_loss_points: Decimal = Decimal(15)
    lot_rules: list[LotRule] = field(default_factory=list)

    # === 新增交易方向配置 ===
    trading_direction: str = "BOTH"  # "LONG_ONLY", "SHORT_ONLY", "BOTH"

    # === 新增濾網配置 (預設不啟用，保持向後相容) ===
    range_filter: RangeFilter = field(default_factory=RangeFilter)
    risk_config: RiskConfig = field(default_factory=RiskConfig)
    stop_loss_config: StopLossConfig = field(default_factory=StopLossConfig)

def format_config_summary(config: StrategyConfig) -> str:
    """將 StrategyConfig 物件格式化為人類易讀的摘要字串。"""
    summary_lines = [f"\n📋======= 策略設定摘要 (交易口數: {config.trade_size_in_lots}) =======📋"]

    # 停損策略顯示 (優先使用濾網設定，向後相容)
    stop_loss_type = config.stop_loss_config.stop_loss_type if hasattr(config, 'stop_loss_config') else config.stop_loss_type
    fixed_points = config.stop_loss_config.fixed_stop_loss_points if hasattr(config, 'stop_loss_config') else config.fixed_stop_loss_points

    sl_type_map = { StopLossType.RANGE_BOUNDARY: "區間邊緣", StopLossType.OPENING_PRICE: "8:46開盤價", StopLossType.FIXED_POINTS: "固定點數" }
    sl_line = f"  - 初始停損策略：{sl_type_map[stop_loss_type]}"
    if stop_loss_type == StopLossType.FIXED_POINTS:
        sl_line += f" ({fixed_points} 點)"

    # 檢查是否使用區間中點
    if hasattr(config, 'stop_loss_config') and config.stop_loss_config.use_range_midpoint:
        sl_line += " [使用區間中點]"

    summary_lines.append(sl_line)

    # === 濾網設定顯示 ===
    if hasattr(config, 'range_filter') or hasattr(config, 'risk_config'):
        summary_lines.append("  --- 濾網設定 ---")

        # 區間過濾濾網
        if hasattr(config, 'range_filter'):
            range_status = "啟用" if config.range_filter.use_range_size_filter else "停用"
            range_line = f"  - 區間大小濾網：{range_status}"
            if config.range_filter.use_range_size_filter:
                range_line += f" (上限: {config.range_filter.max_range_points} 點)"
            summary_lines.append(range_line)

        # 風險管理濾網
        if hasattr(config, 'risk_config'):
            risk_status = "啟用" if config.risk_config.use_risk_filter else "停用"
            summary_lines.append(f"  - 風險管理濾網：{risk_status}")
            if config.risk_config.use_risk_filter:
                summary_lines.append(f"    - 每日虧損限制：{config.risk_config.daily_loss_limit} 點")
                summary_lines.append(f"    - 每日獲利目標：{config.risk_config.profit_target} 點")

    summary_lines.append("  --- 各口數出場規則 ---")
    for i, rule in enumerate(config.lot_rules):
        lot_num = i + 1
        summary_lines.append(f"  - [第 {lot_num} 口單]")
        if rule.use_trailing_stop and rule.trailing_activation is not None and rule.trailing_pullback is not None:
            summary_lines.append(f"    - 停利: 移動停利 (觸發:{rule.trailing_activation}點, 回檔:{rule.trailing_pullback:%})")
        elif rule.fixed_tp_points is not None:
            summary_lines.append(f"    - 停利: 固定停利 ({rule.fixed_tp_points}點)")
        else:
            summary_lines.append(f"    - 停利: 持有至收盤")

        if rule.protective_stop_multiplier is not None:
             summary_lines.append(f"    - 保護性停損: 前序累積獲利 * {rule.protective_stop_multiplier}")
    return "\n".join(summary_lines)

# ==============================================================================
# 2. 濾網檢查函式
# ==============================================================================
def apply_range_filter(config: StrategyConfig, range_high: Decimal, range_low: Decimal, day: date) -> tuple[bool, str]:
    """套用區間過濾濾網"""
    if not hasattr(config, 'range_filter') or not config.range_filter.use_range_size_filter:
        return True, "區間濾網未啟用"

    range_size = range_high - range_low
    if range_size > config.range_filter.max_range_points:
        return False, f"區間過大被過濾 ({range_size}點 > {config.range_filter.max_range_points}點)"

    return True, f"通過區間濾網 ({range_size}點)"

def apply_risk_filter(config: StrategyConfig, current_daily_pnl: Decimal) -> tuple[bool, str]:
    """套用風險管理濾網（保留原有邏輯以確保向後兼容）"""
    if not hasattr(config, 'risk_config') or not config.risk_config.use_risk_filter:
        return True, "風險濾網未啟用"

    # 檢查每日虧損限制
    if current_daily_pnl <= -config.risk_config.daily_loss_limit:
        return False, f"達到每日虧損限制 ({current_daily_pnl}點 <= -{config.risk_config.daily_loss_limit}點)"

    # 檢查每日獲利目標
    if current_daily_pnl >= config.risk_config.profit_target:
        return False, f"達到每日獲利目標 ({current_daily_pnl}點 >= {config.risk_config.profit_target}點)"

    return True, "通過風險濾網"

def check_daily_risk_limit(config: StrategyConfig, current_daily_pnl: Decimal) -> tuple[bool, str, str]:
    """檢查當日風險限制（用於交易進行中）

    🚀 性能優化：快速檢查，避免不必要的字符串格式化

    Returns:
        tuple[bool, str, str]: (是否通過檢查, 訊息, 退場類型)
    """
    # 🚀 優化：提前返回，避免不必要的檢查
    if not hasattr(config, 'risk_config') or not config.risk_config.use_risk_filter:
        return True, "風險濾網未啟用", ""

    # 🚀 優化：先檢查數值範圍，只有在觸發時才格式化字符串
    loss_limit = -config.risk_config.daily_loss_limit
    profit_target = config.risk_config.profit_target

    # 檢查當日虧損限制
    if current_daily_pnl <= loss_limit:
        return False, f"觸發當日虧損限制，強制平倉 ({current_daily_pnl}點 <= {loss_limit}點)", "risk_loss_exit"

    # 檢查當日獲利目標
    if current_daily_pnl >= profit_target:
        return False, f"達到當日獲利目標，強制平倉 ({current_daily_pnl}點 >= {profit_target}點)", "risk_profit_exit"

    return True, "", ""  # 🚀 優化：通過時不需要訊息

def get_initial_stop_loss(config: StrategyConfig, range_high: Decimal, range_low: Decimal, position: str) -> Decimal:
    """根據停損配置計算初始停損點"""
    # 優先使用濾網設定，向後相容
    if hasattr(config, 'stop_loss_config'):
        stop_config = config.stop_loss_config
    else:
        # 向後相容：使用原有設定
        stop_config = StopLossConfig(
            stop_loss_type=config.stop_loss_type,
            fixed_stop_loss_points=config.fixed_stop_loss_points,
            use_range_midpoint=False
        )

    if stop_config.use_range_midpoint:
        # 使用區間中點作為停損
        midpoint = (range_high + range_low) / 2
        return midpoint
    elif stop_config.stop_loss_type == StopLossType.FIXED_POINTS:
        # 使用固定點數停損 (這裡需要進場價，暫時返回區間邊緣)
        return range_low if position == 'LONG' else range_high
    else:
        # 預設：使用區間邊緣
        return range_low if position == 'LONG' else range_high

# ==============================================================================
# 3. 核心交易邏輯函式
# ==============================================================================
def _run_multi_lot_logic(day_session_candles: list, trade_candles: list, config: StrategyConfig, range_high, range_low) -> tuple[Decimal, str]:
    """支援任意口數，並使用正確序列檢查的邏輯"""
    position, entry_price, entry_time, entry_candle_index = None, Decimal(0), None, -1

    for i, candle in enumerate(trade_candles):
        # 🚀 【新增】根據交易方向配置過濾信號
        if candle['close_price'] > range_high and config.trading_direction in ["LONG_ONLY", "BOTH"]:
            position, entry_price, entry_time, entry_candle_index = 'LONG', candle['close_price'], candle['trade_datetime'].time(), i
            break
        elif candle['low_price'] < range_low and config.trading_direction in ["SHORT_ONLY", "BOTH"]:
            position, entry_price, entry_time, entry_candle_index = 'SHORT', candle['close_price'], candle['trade_datetime'].time(), i
            break

    if not position: return Decimal(0), ""

    # 🚀 【移除舊邏輯】不再使用累積虧損檢查，改用風控停損點方式

    logger.info(f"  📈 LONG  | 進場 {config.trade_size_in_lots} 口 | 時間: {entry_time}, 價格: {int(round(entry_price))}" if position == 'LONG'
                else f"  📉 SHORT | 進場 {config.trade_size_in_lots} 口 | 時間: {entry_time}, 價格: {int(round(entry_price))}")

    lots = []
    # 使用新的停損配置函式
    initial_sl = get_initial_stop_loss(config, range_high, range_low, position)

    # 🚀 【新增】風控停損點計算
    risk_sl = None
    if hasattr(config, 'risk_config') and config.risk_config.use_risk_filter and config.risk_config.daily_loss_limit > 0:
        risk_loss_per_lot = config.risk_config.daily_loss_limit / config.trade_size_in_lots
        if position == 'LONG':
            risk_sl = entry_price - risk_loss_per_lot
        else:  # SHORT
            risk_sl = entry_price + risk_loss_per_lot

        # 選擇較近的停損點（更保守的）
        if position == 'LONG':
            final_sl = max(initial_sl, risk_sl)  # LONG: 較高的停損點較保守
        else:  # SHORT
            final_sl = min(initial_sl, risk_sl)  # SHORT: 較低的停損點較保守

        if final_sl != initial_sl:
            logger.info(f"  🛡️ 風控停損啟用 | 區間停損: {int(round(initial_sl))}, 風控停損: {int(round(risk_sl))}, 採用: {int(round(final_sl))}")
    else:
        final_sl = initial_sl

    for i in range(config.trade_size_in_lots):
        rule = config.lot_rules[i] if i < len(config.lot_rules) else config.lot_rules[-1]
        lots.append({'id': i + 1, 'rule': rule, 'status': 'active', 'pnl': Decimal(0), 'peak_price': entry_price, 'trailing_on': False, 'stop_loss': final_sl, 'is_initial_stop': True})

    for exit_candle in trade_candles[entry_candle_index + 1:]:
        if all(lot['status'] != 'active' for lot in lots): break
        current_time = exit_candle['trade_datetime'].time()

        # 🔄 修正執行順序：先檢查個別口數的停損點（包括保護性停損）
        exited_in_this_candle = False
        for lot in lots:
            if lot['status'] != 'active': continue

            # 檢查是否觸及該口的停損點
            stop_triggered = False
            if position == 'LONG':
                stop_triggered = exit_candle['low_price'] <= lot['stop_loss']
            else:  # SHORT
                stop_triggered = exit_candle['high_price'] >= lot['stop_loss']

            if stop_triggered:
                lot['pnl'] = lot['stop_loss'] - entry_price if position == 'LONG' else entry_price - lot['stop_loss']
                lot['status'] = 'exited'

                # 根據停損類型顯示不同訊息
                if lot['is_initial_stop']:
                    logger.info(f"  ❌ 第{lot['id']}口初始停損 | 時間: {current_time}, 出場價: {int(round(lot['stop_loss']))}, 損益: {int(round(lot['pnl']))}")
                else:
                    logger.info(f"  🛡️ 第{lot['id']}口保護性停損 | 時間: {current_time}, 出場價: {int(round(lot['stop_loss']))}, 損益: {int(round(lot['pnl']))}")

                exited_in_this_candle = True

        if exited_in_this_candle: continue
            
        cumulative_pnl_before_candle = sum(l['pnl'] for l in lots if l['status'] == 'exited')

        for lot in lots:
            if lot['status'] != 'active': continue
            
            rule = lot['rule']
            exited_by_tp = False
            if rule.use_trailing_stop and rule.trailing_activation is not None and rule.trailing_pullback is not None:
                if position == 'LONG':
                    lot['peak_price'] = max(lot['peak_price'], exit_candle['high_price'])
                    if not lot['trailing_on'] and lot['peak_price'] >= entry_price + rule.trailing_activation:
                        lot['trailing_on'] = True; logger.info(f"  🔔 第{lot['id']}口移動停利啟動 | 時間: {current_time}")
                    if lot['trailing_on']:
                        stop_price = lot['peak_price'] - (lot['peak_price'] - entry_price) * rule.trailing_pullback
                        if exit_candle['low_price'] <= stop_price: lot['pnl'], lot['status'], exited_by_tp = stop_price - entry_price, 'exited', True
                elif position == 'SHORT':
                    lot['peak_price'] = min(lot['peak_price'], exit_candle['low_price'])
                    if not lot['trailing_on'] and lot['peak_price'] <= entry_price - rule.trailing_activation:
                        lot['trailing_on'] = True; logger.info(f"  🔔 第{lot['id']}口移動停利啟動 | 時間: {current_time}")
                    if lot['trailing_on']:
                        stop_price = lot['peak_price'] + (entry_price - lot['peak_price']) * rule.trailing_pullback
                        if exit_candle['high_price'] >= stop_price: lot['pnl'], lot['status'], exited_by_tp = entry_price - stop_price, 'exited', True
                
                if exited_by_tp: 
                    exit_p = entry_price + lot['pnl'] if position == 'LONG' else entry_price - lot['pnl']
                    logger.info(f"  ✅ 第{lot['id']}口移動停利 | 時間: {current_time}, 價格: {int(round(exit_p))}, 損益: +{int(round(lot['pnl']))}")
            
            elif rule.fixed_tp_points is not None:
                if (position == 'LONG' and exit_candle['high_price'] >= entry_price + rule.fixed_tp_points) or \
                   (position == 'SHORT' and exit_candle['low_price'] <= entry_price - rule.fixed_tp_points):
                    lot['pnl'], lot['status'], exited_by_tp = rule.fixed_tp_points, 'exited', True
                    logger.info(f"  ✅ 第{lot['id']}口固定停利 | 時間: {current_time}, 損益: +{int(round(lot['pnl']))}")

            if exited_by_tp:
                # 🚀 【新增】第一口出場時，移除所有剩餘口數的風控停損，改回原始停損
                if lot['id'] == 1:  # 第一口出場
                    original_sl = get_initial_stop_loss(config, range_high, range_low, position)
                    for remaining_lot in lots:
                        if remaining_lot['status'] == 'active' and remaining_lot['is_initial_stop']:
                            if remaining_lot['stop_loss'] != original_sl:
                                remaining_lot['stop_loss'] = original_sl
                                logger.info(f"    🔄 第{remaining_lot['id']}口停損點恢復為區間邊緣: {int(round(original_sl))}")

                next_lot = next((l for l in lots if l['id'] == lot['id'] + 1), None)
                if next_lot and next_lot['status'] == 'active' and next_lot['rule'].protective_stop_multiplier is not None:
                    total_profit_so_far = cumulative_pnl_before_candle + lot['pnl']
                    stop_loss_amount = total_profit_so_far * next_lot['rule'].protective_stop_multiplier
                    new_sl = entry_price - stop_loss_amount if position == 'LONG' else entry_price + stop_loss_amount
                    next_lot['stop_loss'], next_lot['is_initial_stop'] = new_sl, False
                    logger.info(f"    - 第{next_lot['id']}口單停損點更新為: {int(round(new_sl))} (基於累積獲利 {int(round(total_profit_so_far))})")

        # 🚀 【新優化】只檢查獲利目標，虧損限制已在進場前檢查
        # 🐛 修正：只有在風險管理啟用且設定了獲利目標時才檢查
        if (hasattr(config, 'risk_config') and config.risk_config.use_risk_filter and
            config.risk_config.profit_target > 0):
            # 🔍 DEBUG: 添加調試信息
            # logger.debug(f"  🔍 執行風險管理獲利目標檢查 | 時間: {current_time}")

            active_lots = [l for l in lots if l['status'] == 'active']

            if active_lots:  # 只有在有活躍部位時才檢查獲利目標
                exited_pnl = sum(l['pnl'] for l in lots if l['status'] == 'exited')
                active_count = len(active_lots)
                current_price_diff = Decimal(exit_candle['close_price'] - entry_price if position == 'LONG' else entry_price - exit_candle['close_price'])
                active_pnl = current_price_diff * active_count
                current_daily_pnl = Decimal(exited_pnl) + active_pnl

                # 只檢查獲利目標
                if current_daily_pnl >= config.risk_config.profit_target:
                    logger.info(f"  🚨 風險管理獲利平倉 | 達到當日獲利目標 ({current_daily_pnl}點 >= {config.risk_config.profit_target}點) | 時間: {current_time}, 平倉價: {int(round(exit_candle['close_price']))}")

                    # 計算並記錄各口的損益明細
                    for lot in active_lots:
                        lot_pnl = exit_candle['close_price'] - entry_price if position == 'LONG' else entry_price - exit_candle['close_price']
                        lot['pnl'] = lot_pnl
                        lot['status'] = 'exited'
                        logger.info(f"    🚨 第{lot['id']}口風險平倉 | 損益: {int(round(lot_pnl)):+d}點")
                    break

    if position:
        active_lots = [lot for lot in lots if lot['status'] == 'active']
        if active_lots:
            exit_price = day_session_candles[-1]['close_price']
            eod_pnl = (exit_price - entry_price) if position == 'LONG' else (entry_price - exit_price)
            for lot in active_lots: lot['pnl'], lot['status'] = eod_pnl, 'exited'
            logger.info(f"  ⚪️ 收盤平倉剩餘 {len(active_lots)} 口 | 損益: {int(round(eod_pnl))}")
    
    return Decimal(sum(l['pnl'] for l in lots)) if lots else Decimal(0), position or ""

# ==============================================================================
# 3. 主回測函式
# ==============================================================================
def run_backtest(config: StrategyConfig, start_date: str | None = None, end_date: str | None = None, silent: bool = False,
                 range_start_time: str | None = None, range_end_time: str | None = None):
    """
    執行回測

    Args:
        config: 策略配置
        start_date: 開始日期 (格式: 'YYYY-MM-DD')，可選
        end_date: 結束日期 (格式: 'YYYY-MM-DD')，可選
        silent: 是否靜默模式（不輸出日誌）
        range_start_time: 開盤區間開始時間 (格式: 'HH:MM')，可選，預設08:46
        range_end_time: 開盤區間結束時間 (格式: 'HH:MM')，可選，預設08:47

    Returns:
        dict: 回測結果統計
    """
    # 處理自定義開盤區間時間
    range_start_hour, range_start_min = 8, 46  # 預設值
    range_end_hour, range_end_min = 8, 47      # 預設值

    if range_start_time:
        try:
            range_start_hour, range_start_min = map(int, range_start_time.split(':'))
        except ValueError:
            if not silent:
                logger.warning(f"⚠️ 開盤區間開始時間格式錯誤: {range_start_time}，使用預設值 08:46")

    if range_end_time:
        try:
            range_end_hour, range_end_min = map(int, range_end_time.split(':'))
        except ValueError:
            if not silent:
                logger.warning(f"⚠️ 開盤區間結束時間格式錯誤: {range_end_time}，使用預設值 08:47")

    # 顯示時間區間資訊
    if not silent:
        if start_date or end_date:
            date_info = f"📅 回測時間區間: {start_date or '開始'} 至 {end_date or '結束'}"
            logger.info(date_info)

        # 顯示開盤區間時間設定
        range_time_info = f"🕐 開盤區間時間: {range_start_hour:02d}:{range_start_min:02d} 至 {range_end_hour:02d}:{range_end_min:02d}"
        logger.info(range_time_info)

        logger.info(format_config_summary(config))

    try:
        # 🚀 根據配置選擇數據源
        if USE_SQLITE:
            context_manager = sqlite_connection.get_conn_cur_from_sqlite_with_adapter(as_dict=True)
        else:
            context_manager = shared.get_conn_cur_from_pool_b(as_dict=True)

        with context_manager as (conn, cur):
            # 構建SQL查詢，根據時間區間過濾
            base_query = "SELECT DISTINCT trade_datetime::date as trade_day FROM stock_prices"
            conditions = []
            params = []

            if start_date:
                conditions.append("trade_datetime::date >= %s")
                params.append(start_date)

            if end_date:
                conditions.append("trade_datetime::date <= %s")
                params.append(end_date)

            if conditions:
                query = f"{base_query} WHERE {' AND '.join(conditions)} ORDER BY trade_day;"
            else:
                query = f"{base_query} ORDER BY trade_day;"

            cur.execute(query, tuple(params))
            trade_days = [row['trade_day'] for row in cur.fetchall()]
            logger.info(f"🔍 找到 {len(trade_days)} 個交易日進行回測。")
            total_pnl, winning_trades, losing_trades = Decimal(0), 0, 0
            cumulative_pnl = Decimal(0)  # 🚀 新增：追蹤累積損益

            # 🚀 【新增】多空分別統計
            long_pnl, short_pnl = Decimal(0), Decimal(0)
            long_trades, short_trades = 0, 0
            long_wins, short_wins = 0, 0

            for day in trade_days:
                cur.execute("SELECT * FROM stock_prices WHERE trade_datetime::date = %s ORDER BY trade_datetime;", (day,))
                day_session_candles = [c for c in cur.fetchall() if time(8, 45) <= c['trade_datetime'].time() <= time(13, 45)]
                if len(day_session_candles) < 3: continue

                # 使用自定義的開盤區間時間
                range_times = [time(range_start_hour, range_start_min), time(range_end_hour, range_end_min)]
                candles_range = [c for c in day_session_candles if c['trade_datetime'].time() in range_times]
                if len(candles_range) != 2:
                    if not silent:
                        logger.warning(f"⚠️ {day}: 找不到開盤區間K棒 ({range_start_hour:02d}:{range_start_min:02d}-{range_end_hour:02d}:{range_end_min:02d})")
                    continue

                range_high, range_low = max(c['high_price'] for c in candles_range), min(c['low_price'] for c in candles_range)

                # === 套用區間過濾濾網 ===
                range_passed, range_msg = apply_range_filter(config, range_high, range_low, day)
                if not range_passed:
                    logger.info(f"--- {day} | 開盤區間: {range_low} - {range_high} | {range_msg} | 跳過交易 ---")
                    continue

                logger.info(f"--- {day} | 開盤區間: {range_low} - {range_high} | {range_msg} ---")

                # 交易開始時間設為開盤區間結束後1分鐘
                trade_start_hour = range_end_hour
                trade_start_min = range_end_min + 1
                if trade_start_min >= 60:
                    trade_start_hour += 1
                    trade_start_min -= 60

                trade_candles = [c for c in day_session_candles if c['trade_datetime'].time() >= time(trade_start_hour, trade_start_min)]

                # 🚀 【新邏輯】使用風控停損點方式，不再需要累積損益參數
                day_pnl, trade_direction = _run_multi_lot_logic(day_session_candles, trade_candles, config, range_high, range_low)

                if day_pnl != 0:
                    is_long_trade = (trade_direction == 'LONG')

                    if day_pnl > 0:
                        winning_trades += 1
                        if is_long_trade: long_wins += 1
                        else: short_wins += 1
                    else:
                        losing_trades += 1

                    # 更新多空統計
                    if is_long_trade:
                        long_trades += 1
                        long_pnl += day_pnl
                    else:
                        short_trades += 1
                        short_pnl += day_pnl

                total_pnl += day_pnl
                cumulative_pnl += day_pnl  # 🚀 更新累積損益

            # 計算統計數據
            trade_count = winning_trades + losing_trades
            win_rate = (winning_trades / trade_count * 100) if trade_count > 0 else 0
            long_win_rate = (long_wins / long_trades * 100) if long_trades > 0 else 0
            short_win_rate = (short_wins / short_trades * 100) if short_trades > 0 else 0

            if not silent:
                logger.info("====== 回測結果總結 ======")
                logger.info(f"總交易天數: {len(trade_days)}")
                logger.info(f"總交易次數: {trade_count}")
                logger.info(f"獲利次數: {winning_trades}")
                logger.info(f"虧損次數: {losing_trades}")
                logger.info(f"勝率: {win_rate:.2f}%")
                logger.info(f"總損益({config.trade_size_in_lots}口): {total_pnl:.2f}")
                logger.info(format_config_summary(config))
                logger.info("===========================")

            # 返回結構化結果
            return {
                'total_pnl': float(total_pnl),
                'long_pnl': float(long_pnl),
                'short_pnl': float(short_pnl),
                'total_trades': trade_count,
                'long_trades': long_trades,
                'short_trades': short_trades,
                'winning_trades': winning_trades,
                'losing_trades': losing_trades,
                'long_wins': long_wins,
                'short_wins': short_wins,
                'win_rate': win_rate / 100,
                'long_win_rate': long_win_rate / 100,
                'short_win_rate': short_win_rate / 100,
                'trade_days': len(trade_days)
            }

    except Exception as e:
        if not silent:
            logger.error(f"❌ 執行回測時發生錯誤: {e}", exc_info=True)
        return {
            'total_pnl': 0.0, 'long_pnl': 0.0, 'short_pnl': 0.0,
            'total_trades': 0, 'long_trades': 0, 'short_trades': 0,
            'winning_trades': 0, 'losing_trades': 0, 'long_wins': 0, 'short_wins': 0,
            'win_rate': 0.0, 'long_win_rate': 0.0, 'short_win_rate': 0.0, 'trade_days': 0
        }



def create_strategy_config_from_gui(gui_config):
    """從GUI配置創建策略配置對象"""
    trade_lots = gui_config["trade_lots"]
    lot_settings = gui_config["lot_settings"]
    filters = gui_config["filters"]

    # 創建口數規則
    lot_rules = []

    # 第1口
    lot_rules.append(LotRule(
        use_trailing_stop=True,
        trailing_activation=Decimal(str(lot_settings["lot1"]["trigger"])),
        trailing_pullback=Decimal(str(lot_settings["lot1"]["trailing"])) / 100
    ))

    # 第2口 (如果有)
    if trade_lots >= 2:
        lot_rules.append(LotRule(
            use_trailing_stop=True,
            trailing_activation=Decimal(str(lot_settings["lot2"]["trigger"])),
            trailing_pullback=Decimal(str(lot_settings["lot2"]["trailing"])) / 100,
            protective_stop_multiplier=Decimal(str(lot_settings["lot2"]["protection"]))
        ))

    # 第3口 (如果有)
    if trade_lots >= 3:
        lot_rules.append(LotRule(
            use_trailing_stop=True,
            trailing_activation=Decimal(str(lot_settings["lot3"]["trigger"])),
            trailing_pullback=Decimal(str(lot_settings["lot3"]["trailing"])) / 100,
            protective_stop_multiplier=Decimal(str(lot_settings["lot3"]["protection"]))
        ))

    # 創建濾網配置
    range_filter = RangeFilter(
        use_range_size_filter=filters["range_filter"]["enabled"],
        max_range_points=Decimal(str(filters["range_filter"].get("max_range_points", 50)))
    )

    risk_config = RiskConfig(
        use_risk_filter=filters["risk_filter"]["enabled"],
        daily_loss_limit=Decimal(str(filters["risk_filter"].get("daily_loss_limit", 150))),
        profit_target=Decimal(str(filters["risk_filter"].get("profit_target", 200)))
    )

    # 停損配置 (根據GUI設定決定)
    if filters["stop_loss_filter"]["enabled"]:
        stop_loss_type_str = filters["stop_loss_filter"].get("stop_loss_type", "range_boundary")
        use_range_midpoint = False

        if stop_loss_type_str == "range_boundary":
            stop_loss_type = StopLossType.RANGE_BOUNDARY
        elif stop_loss_type_str == "range_midpoint":
            stop_loss_type = StopLossType.RANGE_BOUNDARY  # 使用區間邊緣類型但啟用中點
            use_range_midpoint = True
        elif stop_loss_type_str == "fixed_points":
            stop_loss_type = StopLossType.FIXED_POINTS
        else:
            stop_loss_type = StopLossType.RANGE_BOUNDARY

        stop_loss_config = StopLossConfig(
            stop_loss_type=stop_loss_type,
            fixed_stop_loss_points=Decimal(str(filters["stop_loss_filter"].get("fixed_stop_loss_points", 15))),
            use_range_midpoint=use_range_midpoint
        )
    else:
        stop_loss_config = StopLossConfig()

    # 創建策略配置
    strategy_config = StrategyConfig(
        trade_size_in_lots=trade_lots,
        stop_loss_type=stop_loss_config.stop_loss_type,
        lot_rules=lot_rules,
        trading_direction=gui_config.get("trading_direction", "BOTH"),  # 🚀 新增交易方向
        range_filter=range_filter,
        risk_config=risk_config,
        stop_loss_config=stop_loss_config
    )

    return strategy_config


def main():
    import argparse
    import json

    # 添加命令行參數支持
    parser = argparse.ArgumentParser(description='Profit-Funded Risk 多口交易策略回測')
    parser.add_argument('--start-date', type=str, help='2024-08-01')
    parser.add_argument('--end-date', type=str, help='2024-08-31')
    parser.add_argument('--gui-mode', action='store_true', help='GUI模式執行')
    parser.add_argument('--config', type=str, help='GUI配置JSON字串')
    args = parser.parse_args()

    # 處理GUI模式
    if args.gui_mode and args.config:
        try:
            # 初始化資料庫連線池
            logger.info("🎮 GUI模式：初始化資料庫連線池...")
            init_all_db_pools()
            logger.info("✅ GUI模式：資料庫連線池初始化成功。")

            gui_config = json.loads(args.config)
            start_date = gui_config["start_date"]
            end_date = gui_config["end_date"]
            range_start_time = gui_config.get("range_start_time")  # 可選參數
            range_end_time = gui_config.get("range_end_time")      # 可選參數

            # 從GUI配置創建策略配置
            strategy_config = create_strategy_config_from_gui(gui_config)

            # 執行回測
            logger.info("🎮 GUI模式：開始執行回測...")
            result = run_backtest(strategy_config, start_date, end_date, False, range_start_time, range_end_time)

            # 輸出結構化結果供批次實驗解析
            if result and isinstance(result, dict):
                import json
                print(f"BACKTEST_RESULT_JSON: {json.dumps(result, ensure_ascii=False)}")
                logger.info(f"🎮 GUI模式：回測完成，總損益: {result.get('total_pnl', 0):.2f}")

            return

        except Exception as e:
            logger.error(f"❌ GUI模式執行失敗：{e}")
            return

    # 驗證日期格式
    start_date, end_date = args.start_date, args.end_date
    if start_date:
        try:
            from datetime import datetime
            datetime.strptime(start_date, '%Y-%m-%d')
        except ValueError:
            logger.error("❌ 開始日期格式錯誤，請使用 YYYY-MM-DD 格式")
            return

    if end_date:
        try:
            from datetime import datetime
            datetime.strptime(end_date, '%Y-%m-%d')
        except ValueError:
            logger.error("❌ 結束日期格式錯誤，請使用 YYYY-MM-DD 格式")
            return

    logger.info("▶️  回測程式開始執行...")

    # 🚀 根據配置初始化數據源
    if USE_SQLITE:
        try:
            sqlite_connection.init_sqlite_connection()
            logger.info("✅ SQLite連接初始化成功。")
        except Exception as e:
            logger.error(f"❌ SQLite連接初始化失敗: {e}", exc_info=True)
            return
    else:
        try:
            init_all_db_pools()
            logger.info("✅ PostgreSQL連線池初始化成功。")
        except Exception as e:
            logger.error(f"❌ PostgreSQL連線池初始化失敗: {e}", exc_info=True)
            return

    # --- 策略實驗室 ---

    # 正確的【單口移動停利】設定範例
    config_single_lot_trailing_tp = StrategyConfig(
        trade_size_in_lots=1,
        stop_loss_type=StopLossType.RANGE_BOUNDARY, # 假設初始停損不變
        lot_rules=[
            LotRule(
                # 明確指令
                use_trailing_stop=True,
                fixed_tp_points=None,  # 確保不使用固定停利

                # 提供移動停利所需參數
                trailing_activation=Decimal(15),
                trailing_pullback=Decimal('0.20')
            )
        ]
    )
    


    # 【新範例】：雙口交易，兩口都使用移動停利
    config_two_lots_trailing_tp = StrategyConfig(
        trade_size_in_lots=2,
        stop_loss_type=StopLossType.RANGE_BOUNDARY,
        lot_rules=[
            # 第 1 口規則
            LotRule(
                use_trailing_stop=True,
                trailing_activation=Decimal(15),
                trailing_pullback=Decimal('0.20')
            ),
            # 第 2 口規則
            LotRule(
                use_trailing_stop=True,
                trailing_activation=Decimal(40),
                trailing_pullback=Decimal('0.20'),
                protective_stop_multiplier=Decimal('2.0') # 使用第一口的獲利來保護
            )
        ]
    )

    # 範例3：我們之前設計的複雜三口單策略
    config_three_lots = StrategyConfig(
        trade_size_in_lots=3,
        stop_loss_type=StopLossType.RANGE_BOUNDARY,
        lot_rules=[
            LotRule(
                use_trailing_stop=True,
                trailing_activation=Decimal(15),
                trailing_pullback=Decimal('0.20')
            ),
            # 第 2 口規則
            LotRule(
                use_trailing_stop=True,
                trailing_activation=Decimal(40),
                trailing_pullback=Decimal('0.20'),
                protective_stop_multiplier=Decimal('2.0') # 使用第一口的獲利來保護
            ),
            # 第 3 口規則
            LotRule(
                use_trailing_stop=True,
                trailing_activation=Decimal(65),
                trailing_pullback=Decimal('0.20'),
                protective_stop_multiplier=Decimal('2.0') # 使用第二口的獲利來保護
            )
        ]
    )

    config_4_lots = StrategyConfig(
        trade_size_in_lots=4,
        stop_loss_type=StopLossType.RANGE_BOUNDARY,
        lot_rules=[
            LotRule(
                use_trailing_stop=True,
                trailing_activation=Decimal(15),
                trailing_pullback=Decimal('0.20')
            ),
            # 第 2 口規則
            LotRule(
                use_trailing_stop=True,
                trailing_activation=Decimal(40),
                trailing_pullback=Decimal('0.20'),
                protective_stop_multiplier=Decimal('2.0') # 使用累積獲利來保護
            ),
            # 第 3 口規則
            LotRule(
                use_trailing_stop=True,
                trailing_activation=Decimal(65),
                trailing_pullback=Decimal('0.20'),
                protective_stop_multiplier=Decimal('2.0') # 使用累積獲利來保護
            ),
            # 第 4 口規則
            LotRule(
                use_trailing_stop=True,
                trailing_activation=Decimal(80),
                trailing_pullback=Decimal('0.40'),
                protective_stop_multiplier=Decimal('1.0') # 使用累積獲利來保護
            )
        ]
    )
    
    # === 新增濾網測試配置 ===
    config_with_filters = StrategyConfig(
        trade_size_in_lots=3,
        stop_loss_type=StopLossType.RANGE_BOUNDARY,
        lot_rules=[
            LotRule(
                use_trailing_stop=True,
                trailing_activation=Decimal(15),
                trailing_pullback=Decimal('0.20')
            ),
            LotRule(
                use_trailing_stop=True,
                trailing_activation=Decimal(40),
                trailing_pullback=Decimal('0.20'),
                protective_stop_multiplier=Decimal('2.0')
            ),
            LotRule(
                use_trailing_stop=True,
                trailing_activation=Decimal(65),
                trailing_pullback=Decimal('0.20'),
                protective_stop_multiplier=Decimal('2.0')
            )
        ],
        # 啟用濾網
        range_filter=RangeFilter(
            use_range_size_filter=True,
            max_range_points=Decimal(50)
        ),
        risk_config=RiskConfig(
            use_risk_filter=True,  # 明確啟用風險濾網
            daily_loss_limit=Decimal(150),
            profit_target=Decimal(200)
        ),
        stop_loss_config=StopLossConfig(
            stop_loss_type=StopLossType.RANGE_BOUNDARY,
            use_range_midpoint=False
        )
    )

    # --- 選擇要執行的測試 ---
    # logger.info("\n---------- [測試] 執行單口固定停利設定 ----------")
    # run_backtest(config_single_lot_trailing_tp, start_date, end_date)

    # logger.info("\n---------- [測試] 執行單口移動停利設定 ----------")
    # run_backtest(config_two_lots_trailing_tp, start_date, end_date)

    # 第三階段：驗證測試 - 先執行原始配置確認結果一致
    logger.info("\n---------- [驗證] 執行原始三口交易設定 (無濾網) ----------")
    run_backtest(config_three_lots, start_date, end_date)

    logger.info("\n---------- [測試] 執行三口交易設定 (啟用濾網) ----------")
    run_backtest(config_with_filters, start_date, end_date)

    # 🚀 第三階段B：測試風險管理濾網觸發
    logger.info("\n---------- [測試] 風險管理濾網觸發測試 ----------")
    config_strict_risk = StrategyConfig(
        trade_size_in_lots=3,
        stop_loss_type=StopLossType.RANGE_BOUNDARY,
        lot_rules=[
            LotRule(trailing_activation=Decimal('15'), trailing_pullback=Decimal('0.2')),
            LotRule(trailing_activation=Decimal('40'), trailing_pullback=Decimal('0.2'), protective_stop_multiplier=Decimal('2.0')),
            LotRule(trailing_activation=Decimal('65'), trailing_pullback=Decimal('0.2'), protective_stop_multiplier=Decimal('2.0'))
        ],
        risk_config=RiskConfig(
            use_risk_filter=True,
            daily_loss_limit=Decimal('100'),  # 設定較低限制來測試觸發
            profit_target=Decimal('200')
        )
    )
    run_backtest(config_strict_risk, start_date, end_date)

    # 第四階段：凱利公式分析
    logger.info("\n---------- [分析] 凱利公式資金管理分析 ----------")
    try:
        from kelly_formula_analyzer import analyze_backtest_results

        # 從原始配置的回測結果進行凱利分析
        # 這裡我們手動提取交易結果進行分析
        sample_log_content = """
--- 2024-11-01 | 開盤區間: 22345 - 22407 | 區間濾網未啟用 ---
損益: +13
損益: +35
損益: +64
--- 2024-11-06 | 開盤區間: 23116 - 23273 | 區間濾網未啟用 ---
損益: +25
損益: +35
損益: +58
--- 2024-11-07 | 開盤區間: 23124 - 23191 | 區間濾網未啟用 ---
損益: +15
損益: +37
損益: -104
--- 2024-11-08 | 開盤區間: 23746 - 23793 | 區間濾網未啟用 ---
損益: -48
損益: -48
損益: -48
--- 2024-11-11 | 開盤區間: 23537 - 23585 | 區間濾網未啟用 ---
損益: -68
損益: -68
損益: -68
--- 2024-11-12 | 開盤區間: 22985 - 23062 | 區間濾網未啟用 ---
損益: +21
損益: +62
損益: +62
"""

        kelly_report = analyze_backtest_results(log_content=sample_log_content, max_lots=10)
        logger.info(kelly_report)

    except ImportError:
        logger.warning("⚠️ 無法導入凱利公式分析模組，跳過分析")
    except Exception as e:
        logger.error(f"❌ 凱利公式分析時發生錯誤：{e}")

    logger.info("⏹️  回測程式執行完畢。")

if __name__ == '__main__':
    main()
