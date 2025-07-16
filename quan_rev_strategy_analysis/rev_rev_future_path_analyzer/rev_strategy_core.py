# rev_strategy_core.py
"""
反轉策略核心模組 - 包含所有可複用的回測組件
從 rev_multi_Profit-Funded Risk_多口.py 提取的核心功能
"""

import logging
from datetime import time, date
from decimal import Decimal
from dataclasses import dataclass, field
from enum import Enum, auto
import sys
import os

# 添加專案根目錄到路徑以導入共享模組
# 當前文件路徑: quan_rev_strategy_analysis/rev_rev_future_path_analyzer/rev_strategy_core.py
# 需要添加到: /Users/z/big/my-capital-project/
project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.append(project_root)

# 添加 rev_strategy_analysis 目錄到路徑以導入 sqlite_connection
rev_strategy_path = os.path.join(project_root, 'rev_strategy_analysis')
sys.path.append(rev_strategy_path)

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
    # 🎯 新增：固定停損點數（用於替代移動停損的固定停損模式）
    fixed_stop_loss_points: Decimal | None = None

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
    """反轉策略設定的中央控制面板。"""
    trade_size_in_lots: int = 3
    stop_loss_type: StopLossType = StopLossType.RANGE_BOUNDARY
    fixed_stop_loss_points: Decimal = Decimal(15)
    lot_rules: list[LotRule] = field(default_factory=list)

    # === 新增濾網配置 (預設不啟用，保持向後相容) ===
    range_filter: RangeFilter = field(default_factory=RangeFilter)
    risk_config: RiskConfig = field(default_factory=RiskConfig)
    stop_loss_config: StopLossConfig = field(default_factory=StopLossConfig)

    # === 新增進場價格模式配置 (預設使用區間邊緣，保持向後相容) ===
    entry_price_mode: str = "range_boundary"  # "range_boundary" 或 "breakout_low"

    # === 新增交易方向配置 (預設多空都做，保持向後相容) ===
    trading_direction: str = "BOTH"  # "LONG_ONLY", "SHORT_ONLY", "BOTH"

def format_config_summary(config: StrategyConfig) -> str:
    """將 StrategyConfig 物件格式化為人類易讀的摘要字串。"""
    summary_lines = [f"\n📋======= 🔄反轉策略設定摘要 (交易口數: {config.trade_size_in_lots}) =======📋"]

    # 停損策略顯示 (優先使用濾網設定，向後相容)
    stop_loss_type = config.stop_loss_config.stop_loss_type if hasattr(config, 'stop_loss_config') else config.stop_loss_type
    fixed_points = config.stop_loss_config.fixed_stop_loss_points if hasattr(config, 'stop_loss_config') else config.fixed_stop_loss_points

    # 🔄 反轉策略：修正術語描述
    sl_type_map = { StopLossType.RANGE_BOUNDARY: "區間邊緣", StopLossType.OPENING_PRICE: "8:46開盤價", StopLossType.FIXED_POINTS: "固定點數" }
    sl_line = f"  - 停利目標設定：{sl_type_map[stop_loss_type]} (反轉策略：原停損點變停利點)"
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

        # 🚀 修復：正確顯示停損模式
        if rule.fixed_stop_loss_points is not None:
            summary_lines.append(f"    - 停損: 固定停損 ({rule.fixed_stop_loss_points}點)")
        elif rule.use_trailing_stop and rule.trailing_activation is not None and rule.trailing_pullback is not None:
            summary_lines.append(f"    - 停損: 移動停損 (觸發:{rule.trailing_activation}點, 回檔:{rule.trailing_pullback:%})")
        else:
            summary_lines.append(f"    - 停損: 區間邊緣停損")

        # 🚀 修復：正確顯示停利模式
        if rule.fixed_tp_points is not None:
            summary_lines.append(f"    - 停利: 固定停利 ({rule.fixed_tp_points}點)")
        else:
            summary_lines.append(f"    - 停利: 區間邊緣停利")

        # 🚀 修復：只在有保護性停損時才顯示
        if rule.protective_stop_multiplier is not None and rule.protective_stop_multiplier > 0:
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
    """🔄 反轉策略：計算停利目標點 (原策略的停損點變成反轉策略的停利點)

    注意：雖然函數名稱是 get_initial_stop_loss，但在反轉策略中實際返回的是停利目標點
    """
    # 🔄 反轉策略邏輯：
    # - 原策略的停損點 → 反轉策略的停利點
    # - 原策略的停利點 → 反轉策略的停損點
    #
    # 因此，初始停損應該基於移動停損機制，而不是固定在區間邊緣
    # 這個函數返回的是「停利目標」，實際停損由移動停損機制處理

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
        # 使用區間中點作為停利目標
        midpoint = (range_high + range_low) / 2
        return midpoint
    elif stop_config.stop_loss_type == StopLossType.FIXED_POINTS:
        # 🔄 反轉策略：原策略的停損點變成停利點
        return range_high if position == 'LONG' else range_low
    else:
        # 🔄 反轉策略：原策略的停損點（區間邊緣）變成停利點
        return range_high if position == 'LONG' else range_low

# ==============================================================================
# 3. 核心交易邏輯函式
# ==============================================================================
def _run_multi_lot_logic(day_session_candles: list, trade_candles: list, config: StrategyConfig, range_high, range_low) -> tuple[Decimal, str, dict]:
    """支援任意口數，並使用正確序列檢查的邏輯 - 反轉策略版本"""
    position, entry_price, entry_time, entry_candle_index = None, Decimal(0), None, -1

    # 🔄 【反轉策略】進場邏輯完全反轉 + 🚀 【新增】交易方向過濾
    for i, candle in enumerate(trade_candles):
        # 🚀 【新增】檢查交易方向配置，只在允許的方向進場
        trading_direction = getattr(config, 'trading_direction', 'BOTH')  # 向後相容

        if candle['close_price'] > range_high and trading_direction in ["SHORT_ONLY", "BOTH"]:
            # 原本做多的點改為做空（反轉策略）
            position, entry_price, entry_time, entry_candle_index = 'SHORT', candle['close_price'], candle['trade_datetime'].time(), i
            break
        elif candle['low_price'] < range_low and trading_direction in ["LONG_ONLY", "BOTH"]:
            # 原本做空的點改為做多（反轉策略） - 根據 entry_price_mode 選擇進場價格
            if hasattr(config, 'entry_price_mode') and config.entry_price_mode == "range_boundary":
                # 使用區間下邊緣作為進場價格
                entry_price = range_low
            else:
                # 預設或 "breakout_low" 模式：使用跌破時的最低點+5點
                entry_price = candle['low_price'] + 5

            position, entry_time, entry_candle_index = 'LONG', candle['trade_datetime'].time(), i
            break

    if not position: return Decimal(0), "", {}

    # 🔄 【反轉策略】日誌顯示反轉後的實際進場方向和進場價格模式
    entry_mode_desc = ""
    if hasattr(config, 'entry_price_mode'):
        if config.entry_price_mode == "range_boundary":
            entry_mode_desc = " [區間邊緣進場]"
        elif config.entry_price_mode == "breakout_low":
            entry_mode_desc = " [最低點+5點進場]"

    logger.info(f"  📈 LONG  | 反轉進場 {config.trade_size_in_lots} 口 | 時間: {entry_time}, 價格: {int(round(entry_price))}{entry_mode_desc} (原策略做空點)" if position == 'LONG'
                else f"  📉 SHORT | 反轉進場 {config.trade_size_in_lots} 口 | 時間: {entry_time}, 價格: {int(round(entry_price))}{entry_mode_desc} (原策略做多點)")

    lots = []
    # 🎯 取得停利目標點（雖然函數名稱是 get_initial_stop_loss，但實際返回停利目標）
    profit_target_price = get_initial_stop_loss(config, range_high, range_low, position)

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
            final_sl = max(profit_target_price, risk_sl)  # LONG: 較高的停損點較保守
        else:  # SHORT
            final_sl = min(profit_target_price, risk_sl)  # SHORT: 較低的停損點較保守

        if final_sl != profit_target_price:
            logger.info(f"  🛡️ 風控停損啟用 | 停利目標: {int(round(profit_target_price))}, 風控停損: {int(round(risk_sl))}, 採用: {int(round(final_sl))}")
    else:
        final_sl = profit_target_price

    # 🔄 反轉策略：停損點設定邏輯完全改變
    # 原策略：移動停利機制（獲利保護）
    # 反轉策略：移動停損機制（虧損保護）
    #
    # 重要：不再使用固定的區間邊緣作為停損點！
    # 而是使用移動停損機制，基於GUI面板的觸發點數和回檔比例

    # 🔄 反轉策略：初始停損點設定
    # 不使用區間邊緣，而是設定一個寬鬆的初始值，讓移動停損機制接管
    if risk_sl is not None:
        # 如果有風控停損，使用風控停損作為最大虧損限制
        final_sl = risk_sl
    else:
        # 設定一個寬鬆的初始停損點，實際停損完全由移動停損機制控制
        # 這個值應該足夠寬鬆，不會在移動停損啟動前被觸發
        if position == 'LONG':
            final_sl = entry_price - Decimal('200')  # 寬鬆的初始停損
        else:  # SHORT
            final_sl = entry_price + Decimal('200')  # 寬鬆的初始停損

    for i in range(config.trade_size_in_lots):
        rule = config.lot_rules[i] if i < len(config.lot_rules) else config.lot_rules[-1]
        lot_id = i + 1

        # 🎯 計算每口的個別停損點
        if rule.fixed_stop_loss_points is not None:
            # 固定停損模式：使用觸發點數作為停損點
            if position == 'LONG':
                lot_stop_loss = entry_price - rule.fixed_stop_loss_points
            else:  # SHORT
                lot_stop_loss = entry_price + rule.fixed_stop_loss_points
            logger.info(f"    📊 第{lot_id}口設定 | 🎯固定停損模式 | 停損點數: {rule.fixed_stop_loss_points}點 | 停損點位: {int(round(lot_stop_loss))}")
        elif rule.use_trailing_stop and rule.trailing_activation is not None:
            # 移動停損模式
            lot_stop_loss = final_sl
            # 🔍 顯示GUI設定的觸發點數和實際停損點位
            if position == 'LONG':
                trigger_stop_loss = entry_price - rule.trailing_activation
            else:  # SHORT
                trigger_stop_loss = entry_price + rule.trailing_activation
            logger.info(f"    📊 第{lot_id}口設定 | 🔄移動停損模式 | GUI觸發點數: {rule.trailing_activation}點 | 觸發停損點位: {int(round(trigger_stop_loss))} | 回檔比例: {rule.trailing_pullback:%} | 初始停損點位: {int(round(lot_stop_loss))}")
        else:
            # 預設模式
            lot_stop_loss = final_sl
            logger.info(f"    📊 第{lot_id}口設定 | ⚙️預設停損模式 | 停損點位: {int(round(lot_stop_loss))}")

        if rule.protective_stop_multiplier is not None:
            logger.info(f"    🛡️ 第{lot_id}口保護性停損倍數: {rule.protective_stop_multiplier}")

        lots.append({
            'id': lot_id,
            'rule': rule,
            'status': 'active',
            'pnl': Decimal(0),
            'peak_price': entry_price,  # 🔄 反轉策略：追蹤最不利價格而非最有利價格
            'trailing_on': False,
            'stop_loss': lot_stop_loss,  # 使用個別計算的停損點
            'is_initial_stop': True
        })

    for exit_candle in trade_candles[entry_candle_index + 1:]:
        if all(lot['status'] != 'active' for lot in lots): break
        current_time = exit_candle['trade_datetime'].time()

        # 🔄 反轉策略：先檢查停利點（區間邊緣），再檢查停損點
        exited_in_this_candle = False

        # 🎯 第一步：檢查停利點
        for lot in lots:
            if lot['status'] != 'active': continue

            rule = lot['rule']
            tp_triggered = False
            exit_price = None

            # 🎯 優先檢查每口獨立停利設定
            if rule.fixed_tp_points is not None:
                if position == 'LONG':
                    tp_price = entry_price + rule.fixed_tp_points
                    if exit_candle['high_price'] >= tp_price:
                        tp_triggered = True
                        exit_price = tp_price
                        lot['pnl'] = rule.fixed_tp_points  # LONG: 停利點數就是獲利
                else:  # SHORT
                    tp_price = entry_price - rule.fixed_tp_points
                    if exit_candle['low_price'] <= tp_price:
                        tp_triggered = True
                        exit_price = tp_price
                        lot['pnl'] = rule.fixed_tp_points  # SHORT: 停利點數就是獲利

                if tp_triggered:
                    lot['status'] = 'exited'
                    exited_in_this_candle = True
                    logger.info(f"  ✅ 第{lot['id']}口固定停利 | 時間: {current_time}, 出場價: {int(round(exit_price or 0))}, 損益: {int(round(lot['pnl'])):+d}")
                    continue

            # 🎯 如果沒有每口獨立停利，則使用區間邊緣停利邏輯
            if rule.fixed_tp_points is None:  # 🔧 只有在沒有設定固定停利時才使用區間邊緣停利
                if position == 'LONG':
                    tp_triggered = exit_candle['high_price'] >= range_high  # 原策略SHORT的停損點
                    if tp_triggered:
                        exit_price = range_high
                        lot['pnl'] = range_high - entry_price
                else:  # SHORT
                    tp_triggered = exit_candle['low_price'] <= range_low   # 原策略LONG的停損點
                    if tp_triggered:
                        exit_price = range_low
                        lot['pnl'] = entry_price - range_low

                if tp_triggered:
                    lot['status'] = 'exited'
                    exited_in_this_candle = True

                    # 根據實際損益顯示停利或停損
                    if lot['pnl'] > 0:
                        logger.info(f"  ✅ 第{lot['id']}口觸及停利點 | 時間: {current_time}, 出場價: {int(round(exit_price or 0))}, 損益: {int(round(lot['pnl'])):+d}")
                    else:
                        logger.info(f"  ❌ 第{lot['id']}口觸及停損點 | 時間: {current_time}, 出場價: {int(round(exit_price or 0))}, 損益: {int(round(lot['pnl'])):+d}")

        # 🎯 第二步：檢查移動停損點
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

                # 🔄 反轉策略：根據實際損益顯示正確的訊息類型
                pnl_display = f"{int(round(lot['pnl'])):+d}"  # 確保顯示正負號

                # 在反轉策略中，根據實際損益決定是停利還是停損
                if lot['pnl'] > 0:  # 實際獲利
                    if lot['is_initial_stop']:
                        logger.info(f"  ✅ 第{lot['id']}口觸及停利點 | 時間: {current_time}, 出場價: {int(round(lot['stop_loss']))}, 損益: {pnl_display}")
                    else:
                        logger.info(f"  ✅ 第{lot['id']}口保護性停利 | 時間: {current_time}, 出場價: {int(round(lot['stop_loss']))}, 損益: {pnl_display}")
                else:  # 實際虧損
                    if lot['is_initial_stop']:
                        logger.info(f"  ❌ 第{lot['id']}口初始停損 | 時間: {current_time}, 出場價: {int(round(lot['stop_loss']))}, 損益: {pnl_display}")
                    else:
                        logger.info(f"  🛡️ 第{lot['id']}口保護性停損 | 時間: {current_time}, 出場價: {int(round(lot['stop_loss']))}, 損益: {pnl_display}")

                exited_in_this_candle = True

        if exited_in_this_candle: continue

        cumulative_pnl_before_candle = sum(l['pnl'] for l in lots if l['status'] == 'exited')

        for lot in lots:
            if lot['status'] != 'active': continue

            rule = lot['rule']
            # 🔄 反轉策略：移動停損邏輯（原移動停利邏輯反轉）
            exited_by_sl = False
            if rule.use_trailing_stop and rule.trailing_activation is not None and rule.trailing_pullback is not None:
                if position == 'LONG':
                    # LONG：追蹤最低價，虧損達到觸發點後啟動移動停損
                    lot['peak_price'] = min(lot['peak_price'], exit_candle['low_price'])
                    if not lot['trailing_on'] and lot['peak_price'] <= entry_price - rule.trailing_activation:
                        lot['trailing_on'] = True; logger.info(f"  🔔 第{lot['id']}口移動停損啟動 | 時間: {current_time}")
                    if lot['trailing_on']:
                        # 當價格反彈時，停損點跟隨上移
                        stop_price = lot['peak_price'] + (entry_price - lot['peak_price']) * rule.trailing_pullback
                        if exit_candle['high_price'] >= stop_price:
                            lot['pnl'], lot['status'], exited_by_sl = stop_price - entry_price, 'exited', True
                elif position == 'SHORT':
                    # SHORT：追蹤最高價，虧損達到觸發點後啟動移動停損
                    lot['peak_price'] = max(lot['peak_price'], exit_candle['high_price'])
                    if not lot['trailing_on'] and lot['peak_price'] >= entry_price + rule.trailing_activation:
                        lot['trailing_on'] = True; logger.info(f"  🔔 第{lot['id']}口移動停損啟動 | 時間: {current_time}")
                    if lot['trailing_on']:
                        # 當價格回檔時，停損點跟隨下移
                        stop_price = lot['peak_price'] - (lot['peak_price'] - entry_price) * rule.trailing_pullback
                        if exit_candle['low_price'] <= stop_price:
                            lot['pnl'], lot['status'], exited_by_sl = entry_price - stop_price, 'exited', True

                if exited_by_sl:
                    exit_p = entry_price + lot['pnl'] if position == 'LONG' else entry_price - lot['pnl']
                    # 根據實際損益顯示停損或停利
                    if lot['pnl'] < 0:
                        logger.info(f"  ❌ 第{lot['id']}口移動停損 | 時間: {current_time}, 價格: {int(round(exit_p))}, 損益: {int(round(lot['pnl'])):+d}")
                    else:
                        logger.info(f"  ✅ 第{lot['id']}口移動停利 | 時間: {current_time}, 價格: {int(round(exit_p))}, 損益: {int(round(lot['pnl'])):+d}")

            if exited_by_sl:
                # 🚀 【新增】第一口出場時，移除所有剩餘口數的風控停損，改回停利目標
                if lot['id'] == 1:  # 第一口出場
                    profit_target = get_initial_stop_loss(config, range_high, range_low, position)  # 實際是停利目標
                    for remaining_lot in lots:
                        if remaining_lot['status'] == 'active' and remaining_lot['is_initial_stop']:
                            if remaining_lot['stop_loss'] != profit_target:
                                remaining_lot['stop_loss'] = profit_target
                                logger.info(f"    🎯 第{remaining_lot['id']}口停利目標設為區間邊緣: {int(round(profit_target))}")

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
            logger.info(f"  ⚪️ 收盤平倉剩餘 {len(active_lots)} 口 | 損益: {int(round(eod_pnl)):+d}")

    # 🚀 【新增】計算各口PnL統計
    total_pnl = Decimal(sum(l['pnl'] for l in lots)) if lots else Decimal(0)

    # 建立各口PnL字典（最多支援3口）
    lot_pnl_details = {
        'lot1_pnl': Decimal(0),
        'lot2_pnl': Decimal(0),
        'lot3_pnl': Decimal(0)
    }

    # 填入實際的各口PnL
    for lot in lots:
        lot_id = lot['id']
        if lot_id == 1:
            lot_pnl_details['lot1_pnl'] = lot['pnl']
        elif lot_id == 2:
            lot_pnl_details['lot2_pnl'] = lot['pnl']
        elif lot_id == 3:
            lot_pnl_details['lot3_pnl'] = lot['pnl']

    return total_pnl, position or "", lot_pnl_details

# ==============================================================================
# 4. 主回測函式
# ==============================================================================
def run_rev_backtest(config: StrategyConfig, start_date: str | None = None, end_date: str | None = None, silent: bool = False,
                 range_start_time: str | None = None, range_end_time: str | None = None, enable_console_log: bool = True):
    """
    執行反轉策略回測

    Args:
        config: 反轉策略配置
        start_date: 開始日期 (格式: 'YYYY-MM-DD')，可選
        end_date: 結束日期 (格式: 'YYYY-MM-DD')，可選
        silent: 是否靜默模式（不輸出日誌）
        range_start_time: 開盤區間開始時間 (格式: 'HH:MM')，可選，預設08:46
        range_end_time: 開盤區間結束時間 (格式: 'HH:MM')，可選，預設08:47
        enable_console_log: 是否啟用主控台日誌輸出（預設True）

    Returns:
        dict: 回測結果統計，包含 daily_pnl_list 用於未來路徑分析
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

            # 🚀 【Task 1 新增】MDD計算變數
            peak_pnl = Decimal(0)  # 資金曲線峰值
            max_drawdown = Decimal(0)  # 最大回撤

            # 🚀 【新增】多空分別統計
            long_pnl, short_pnl = Decimal(0), Decimal(0)
            long_trades, short_trades = 0, 0
            long_wins, short_wins = 0, 0

            # 🚀 【新增】各口PnL累積統計
            total_lot1_pnl, total_lot2_pnl, total_lot3_pnl = Decimal(0), Decimal(0), Decimal(0)

            # 🚀 【新增】每日損益列表，用於未來路徑分析
            daily_pnl_list = []

            for day in trade_days:
                cur.execute("SELECT * FROM stock_prices WHERE trade_datetime::date = %s ORDER BY trade_datetime;", (day,))
                day_session_candles = [c for c in cur.fetchall() if time(8, 45) <= c['trade_datetime'].time() <= time(13, 45)]
                if len(day_session_candles) < 3: continue

                # 🔍 【修正】使用整個時間區間的所有K棒來計算開盤區間
                range_start_time_obj = time(range_start_hour, range_start_min)
                range_end_time_obj = time(range_end_hour, range_end_min)

                # 取得指定時間區間內的所有K棒
                candles_range = [c for c in day_session_candles
                               if range_start_time_obj <= c['trade_datetime'].time() <= range_end_time_obj]

                if len(candles_range) == 0:
                    if not silent:
                        logger.warning(f"⚠️ {day}: 找不到開盤區間K棒 ({range_start_hour:02d}:{range_start_min:02d}-{range_end_hour:02d}:{range_end_min:02d})")
                    continue

                # 計算區間高低點
                range_high = max(c['high_price'] for c in candles_range)
                range_low = min(c['low_price'] for c in candles_range)

                # === 套用區間過濾濾網 ===
                range_passed, range_msg = apply_range_filter(config, range_high, range_low, day)
                if not range_passed:
                    if not silent:
                        logger.info(f"--- {day} | 開盤區間: {range_low} - {range_high} | {range_msg} | 跳過交易 ---")
                    continue

                if not silent:
                    logger.info(f"--- {day} | 開盤區間: {range_low} - {range_high} | {range_msg} ---")

                # 交易開始時間設為開盤區間結束後1分鐘
                trade_start_hour = range_end_hour
                trade_start_min = range_end_min + 1
                if trade_start_min >= 60:
                    trade_start_hour += 1
                    trade_start_min -= 60

                trade_candles = [c for c in day_session_candles if c['trade_datetime'].time() >= time(trade_start_hour, trade_start_min)]

                # 執行交易邏輯
                day_pnl, trade_direction, lot_pnl_details = _run_multi_lot_logic(day_session_candles, trade_candles, config, range_high, range_low)

                # 記錄每日損益
                daily_pnl_list.append(float(day_pnl))

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

                    # 🚀 【新增】累積各口PnL統計
                    total_lot1_pnl += lot_pnl_details['lot1_pnl']
                    total_lot2_pnl += lot_pnl_details['lot2_pnl']
                    total_lot3_pnl += lot_pnl_details['lot3_pnl']

                total_pnl += day_pnl
                cumulative_pnl += day_pnl  # 🚀 更新累積損益

                # 🚀 【Task 1 新增】更新MDD計算
                if cumulative_pnl > peak_pnl:
                    peak_pnl = cumulative_pnl
                current_drawdown = peak_pnl - cumulative_pnl
                if current_drawdown > max_drawdown:
                    max_drawdown = current_drawdown

            # 計算統計數據
            trade_count = winning_trades + losing_trades
            win_rate = (winning_trades / trade_count * 100) if trade_count > 0 else 0
            long_win_rate = (long_wins / long_trades * 100) if long_trades > 0 else 0
            short_win_rate = (short_wins / short_trades * 100) if short_trades > 0 else 0

            # 🚀 【Task 1 修改】使用 enable_console_log 控制日誌輸出
            if not silent and enable_console_log:
                logger.info("====== 反轉策略回測結果總結 ======")
                logger.info(f"總交易天數: {len(trade_days)}")
                logger.info(f"總交易次數: {trade_count}")
                logger.info(f"獲利次數: {winning_trades}")
                logger.info(f"虧損次數: {losing_trades}")
                logger.info(f"勝率: {win_rate:.2f}%")
                logger.info(f"總損益({config.trade_size_in_lots}口): {total_pnl:.2f}")
                logger.info(f"最大回撤: {max_drawdown:.2f}")
                logger.info("===========================")

            # 🚀 【Task 1 修改】返回結構化結果，新增 daily_pnl_list 用於未來路徑分析
            return {
                'total_pnl': float(total_pnl),
                'long_pnl': float(long_pnl),
                'short_pnl': float(short_pnl),
                'max_drawdown': float(max_drawdown),
                'lot1_pnl': float(total_lot1_pnl),
                'lot2_pnl': float(total_lot2_pnl),
                'lot3_pnl': float(total_lot3_pnl),
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
                'trade_days': len(trade_days),
                'daily_pnl_list': daily_pnl_list  # 🚀 【新增】每日損益列表
            }

    except Exception as e:
        if not silent:
            logger.error(f"❌ 執行回測時發生錯誤: {e}", exc_info=True)
        return {
            'total_pnl': 0.0, 'long_pnl': 0.0, 'short_pnl': 0.0, 'max_drawdown': 0.0,
            'lot1_pnl': 0.0, 'lot2_pnl': 0.0, 'lot3_pnl': 0.0,
            'total_trades': 0, 'long_trades': 0, 'short_trades': 0,
            'winning_trades': 0, 'losing_trades': 0, 'long_wins': 0, 'short_wins': 0,
            'win_rate': 0.0, 'long_win_rate': 0.0, 'short_win_rate': 0.0, 'trade_days': 0,
            'daily_pnl_list': []  # 🚀 【新增】空的每日損益列表
        }
