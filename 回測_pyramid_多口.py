# 回測_Profit-Funded Risk_多口.py
import logging
from datetime import time, date
from decimal import Decimal
from dataclasses import dataclass, field
from enum import Enum, auto
from app_setup import init_all_db_pools
import shared

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
class StrategyConfig:
    """策略設定的中央控制面板。"""
    trade_size_in_lots: int = 3
    stop_loss_type: StopLossType = StopLossType.RANGE_BOUNDARY
    fixed_stop_loss_points: Decimal = Decimal(15)
    lot_rules: list[LotRule] = field(default_factory=list)

def format_config_summary(config: StrategyConfig) -> str:
    """將 StrategyConfig 物件格式化為人類易讀的摘要字串。"""
    summary_lines = [f"\n📋======= 策略設定摘要 (交易口數: {config.trade_size_in_lots}) =======📋"]
    
    sl_type_map = { StopLossType.RANGE_BOUNDARY: "區間邊緣", StopLossType.OPENING_PRICE: "8:46開盤價", StopLossType.FIXED_POINTS: "固定點數" }
    sl_line = f"  - 初始停損策略：{sl_type_map[config.stop_loss_type]}"
    if config.stop_loss_type == StopLossType.FIXED_POINTS: sl_line += f" ({config.fixed_stop_loss_points} 點)"
    summary_lines.append(sl_line)
    
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
# 2. 核心交易邏輯函式
# ==============================================================================
def _run_multi_lot_logic(day_session_candles: list, trade_candles: list, config: StrategyConfig, range_high, range_low) -> Decimal:
    """支援任意口數，並使用正確序列檢查的邏輯"""
    position, entry_price, entry_time, entry_candle_index = None, Decimal(0), None, -1
    
    for i, candle in enumerate(trade_candles):
        if candle['close_price'] > range_high:
            position, entry_price, entry_time, entry_candle_index = 'LONG', candle['close_price'], candle['trade_datetime'].time(), i
            logger.info(f"  📈 LONG  | 進場 {config.trade_size_in_lots} 口 | 時間: {entry_time}, 價格: {entry_price}"); break
        elif candle['low_price'] < range_low:
            position, entry_price, entry_time, entry_candle_index = 'SHORT', candle['close_price'], candle['trade_datetime'].time(), i
            logger.info(f"  📉 SHORT | 進場 {config.trade_size_in_lots} 口 | 時間: {entry_time}, 價格: {entry_price}"); break
    
    if not position: return Decimal(0)

    lots = []
    initial_sl = range_low if position == 'LONG' else range_high
    for i in range(config.trade_size_in_lots):
        rule = config.lot_rules[i] if i < len(config.lot_rules) else config.lot_rules[-1]
        lots.append({'id': i + 1, 'rule': rule, 'status': 'active', 'pnl': Decimal(0), 'peak_price': entry_price, 'trailing_on': False, 'stop_loss': initial_sl, 'is_initial_stop': True})

    for exit_candle in trade_candles[entry_candle_index + 1:]:
        if all(lot['status'] != 'active' for lot in lots): break
        current_time = exit_candle['trade_datetime'].time()

        active_lots_before_check = [lot for lot in lots if lot['status'] == 'active']

        # 1. 檢查初始停損
        if any(lot['is_initial_stop'] for lot in active_lots_before_check):
            if (position == 'LONG' and exit_candle['close_price'] < initial_sl) or (position == 'SHORT' and exit_candle['close_price'] > initial_sl):
                loss = (exit_candle['close_price'] - entry_price) if position == 'LONG' else (entry_price - exit_candle['close_price'])
                for lot in active_lots_before_check:
                    if lot['is_initial_stop']: lot['pnl'], lot['status'] = loss, 'exited'
                logger.info(f"  ❌ 初始停損 | 所有初始部位出場 | 時間: {current_time}, 價格: {exit_candle['close_price']}, 單口虧損: {loss}"); break
        
        # 2. 依序檢查每口單的出場條件
        cumulative_pnl_before_candle = sum(l['pnl'] for l in lots if l['status'] == 'exited')

        for lot in lots:
            if lot['status'] != 'active': continue

            # 保護性停損檢查
            if not lot['is_initial_stop']:
                if (position == 'LONG' and exit_candle['low_price'] <= lot['stop_loss']) or \
                   (position == 'SHORT' and exit_candle['high_price'] >= lot['stop_loss']):
                    lot['pnl'] = lot['stop_loss'] - entry_price if position == 'LONG' else entry_price - lot['stop_loss']
                    lot['status'] = 'exited'
                    logger.info(f"  🛡️ 第{lot['id']}口單觸及保護性停損 | 時間: {current_time}, 出場價: {lot['stop_loss']:.2f}, 損益: {lot['pnl']}"); continue

            # 停利檢查
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
                if exited_by_tp: logger.info(f"  ✅ 第{lot['id']}口移動停利 | 時間: {current_time}, 價格: {entry_price + lot['pnl'] if position == 'LONG' else entry_price - lot['pnl']:.2f}, 損益: +{lot['pnl']}")
            
            elif rule.fixed_tp_points is not None:
                if (position == 'LONG' and exit_candle['high_price'] >= entry_price + rule.fixed_tp_points) or \
                   (position == 'SHORT' and exit_candle['low_price'] <= entry_price - rule.fixed_tp_points):
                    lot['pnl'], lot['status'], exited_by_tp = rule.fixed_tp_points, 'exited', True
                    logger.info(f"  ✅ 第{lot['id']}口固定停利 | 時間: {current_time}, 損益: +{lot['pnl']}")

            if exited_by_tp:
                next_lot = next((l for l in lots if l['id'] == lot['id'] + 1), None)
                if next_lot and next_lot['status'] == 'active' and next_lot['rule'].protective_stop_multiplier is not None:
                    total_profit_so_far = cumulative_pnl_before_candle + lot['pnl']
                    stop_loss_amount = total_profit_so_far * next_lot['rule'].protective_stop_multiplier
                    new_sl = entry_price - stop_loss_amount if position == 'LONG' else entry_price + stop_loss_amount
                    next_lot['stop_loss'], next_lot['is_initial_stop'] = new_sl, False
                    logger.info(f"    - 第{next_lot['id']}口單停損點更新為: {new_sl:.2f} (基於累積獲利 {total_profit_so_far:.2f})")

    if position:
        active_lots = [lot for lot in lots if lot['status'] == 'active']
        if active_lots:
            exit_price = day_session_candles[-1]['close_price']
            eod_pnl = (exit_price - entry_price) if position == 'LONG' else (entry_price - exit_price)
            for lot in active_lots: lot['pnl'], lot['status'] = eod_pnl, 'exited'
            logger.info(f"  ⚪️ 收盤平倉剩餘 {len(active_lots)} 口 | 損益: {eod_pnl}")
    
    return sum(l['pnl'] for l in lots) if lots else Decimal(0)

# ==============================================================================
# 3. 主回測函式
# ==============================================================================
def run_backtest(config: StrategyConfig):
    logger.info(format_config_summary(config))
    try:
        with shared.get_conn_cur_from_pool_b(as_dict=True) as (conn, cur):
            cur.execute("SELECT DISTINCT trade_datetime::date as trade_day FROM stock_prices ORDER BY trade_day;")
            trade_days = [row['trade_day'] for row in cur.fetchall()]
            logger.info(f"🔍 找到 {len(trade_days)} 個交易日進行回測。")
            total_pnl, winning_trades, losing_trades = Decimal(0), 0, 0

            for day in trade_days:
                cur.execute("SELECT * FROM stock_prices WHERE trade_datetime::date = %s ORDER BY trade_datetime;", (day,))
                day_session_candles = [c for c in cur.fetchall() if time(8, 45) <= c['trade_datetime'].time() <= time(13, 45)]
                if len(day_session_candles) < 3: continue
                
                candles_846_847 = [c for c in day_session_candles if c['trade_datetime'].time() in [time(8, 46), time(8, 47)]]
                if len(candles_846_847) != 2: logger.warning(f"⚠️ {day}: 找不到開盤區間K棒"); continue
                
                range_high, range_low = max(c['high_price'] for c in candles_846_847), min(c['low_price'] for c in candles_846_847)
                logger.info(f"--- {day} | 開盤區間: {range_low} - {range_high} ---")
                
                trade_candles = [c for c in day_session_candles if c['trade_datetime'].time() >= time(8, 48)]
                day_pnl = _run_multi_lot_logic(day_session_candles, trade_candles, config, range_high, range_low)

                if day_pnl != 0:
                    if day_pnl > 0: winning_trades += 1
                    else: losing_trades += 1
                total_pnl += day_pnl

            logger.info("====== 回測結果總結 ======")
            trade_count = winning_trades + losing_trades
            win_rate = (winning_trades / trade_count * 100) if trade_count > 0 else 0
            logger.info(f"總交易天數: {len(trade_days)}")
            logger.info(f"總交易次數: {trade_count}")
            logger.info(f"獲利次數: {winning_trades}")
            logger.info(f"虧損次數: {losing_trades}")
            logger.info(f"勝率: {win_rate:.2f}%")
            logger.info(f"總損益({config.trade_size_in_lots}口): {total_pnl:.2f}")
            logger.info(format_config_summary(config))
            logger.info("===========================")

    except Exception as e:
        logger.error(f"❌ 執行回測時發生錯誤: {e}", exc_info=True)



def main():
    logger.info("▶️  回測程式開始執行...")
    try:
        init_all_db_pools(); logger.info("✅ 資料庫連線池初始化成功。")
    except Exception as e:
        logger.error(f"❌ 資料庫連線池初始化失敗: {e}", exc_info=True); return

    # --- 策略實驗室 ---

    # 範例：執行您設計的3口單「金字塔式鎖利」策略
    config_pyramid = StrategyConfig(
        trade_size_in_lots=4,
        stop_loss_type=StopLossType.RANGE_BOUNDARY, # 初始停損為區間邊緣
        lot_rules=[
            # Lot 1: 斥候兵 -> 固定停利20點
            LotRule(
                use_trailing_stop=False,
                fixed_tp_points=Decimal(15)
            ),
            # Lot 2: 主力軍 -> 標準移動停利
            LotRule(
                use_trailing_stop=True,
                trailing_activation=Decimal(40),
                trailing_pullback=Decimal('0.20')
            ),
            # Lot 3: 夢想單 -> 抱到收盤
            LotRule(
                use_trailing_stop=False,
                fixed_tp_points=None # 不設定任何停利條件
            ),
            # Lot 3: 夢想單 -> 抱到收盤
            LotRule(
                use_trailing_stop=False,
                fixed_tp_points=None # 不設定任何停利條件
            )
        ]
    )
    
    logger.info("\n---------- [測試] 執行三口金字塔策略 ----------")
    run_backtest(config_pyramid)

    logger.info("⏹️  回測程式執行完畢。")


if __name__ == '__main__':
    main()
