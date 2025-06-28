# 台指期開盤策略回測_完整模組化版本_V13_單雙口切換.py
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
class StrategyConfig:
    """策略設定的中央控制面板。"""
    trade_size_in_lots: int = 2
    stop_loss_type: StopLossType = StopLossType.RANGE_BOUNDARY
    fixed_stop_loss_points: Decimal = Decimal(40)
    use_lot1_trailing_stop: bool = False
    lot1_fixed_tp_points: Decimal = Decimal(20)
    lot1_trailing_activation: Decimal = Decimal(15)
    lot1_trailing_pullback: Decimal = Decimal('0.2')
    lot2_stop_loss_multiplier: Decimal = Decimal('2.0')
    use_lot2_trailing_stop: bool = True
    lot2_trailing_activation: Decimal = Decimal(80)
    lot2_trailing_pullback: Decimal = Decimal('0.2')

def format_config_summary(config: StrategyConfig) -> str:
    summary_lines = ["\n📋======= 策略設定摘要 =======📋"]
    if config.trade_size_in_lots == 2:
        summary_lines.append("  - 交易策略：雙口進階分批出場")
        if config.use_lot1_trailing_stop:
            summary_lines.append(f"  - 第1口單(停利): 移動停利 (觸發:{config.lot1_trailing_activation}點, 回檔:{config.lot1_trailing_pullback:%})")
        else:
            summary_lines.append(f"  - 第1口單(停利): 固定停利 ({config.lot1_fixed_tp_points}點)")
        summary_lines.append(f"  - 第2口單(停損): 第1口獲利 * {config.lot2_stop_loss_multiplier}")
        if config.use_lot2_trailing_stop:
            summary_lines.append(f"  - 第2口單(停利): 移動停利 (觸發:{config.lot2_trailing_activation}點, 回檔:{config.lot2_trailing_pullback:%})")
        else:
            summary_lines.append(f"  - 第2口單(停利): 持有至收盤")
    else:
        summary_lines.append("  - 交易策略：單口交易")
        if config.use_lot1_trailing_stop:
            summary_lines.append(f"  - 停利策略: 移動停利 (觸發:{config.lot1_trailing_activation}點, 回檔:{config.lot1_trailing_pullback:%})")
        else:
            summary_lines.append(f"  - 停利策略: 固定停利 ({config.lot1_fixed_tp_points}點)")

    sl_type_map = { StopLossType.RANGE_BOUNDARY: "區間邊緣", StopLossType.OPENING_PRICE: "8:46開盤價", StopLossType.FIXED_POINTS: "固定點數" }
    sl_line = f"  - 停損策略：{sl_type_map[config.stop_loss_type]}"
    if config.stop_loss_type == StopLossType.FIXED_POINTS: sl_line += f" ({config.fixed_stop_loss_points} 點)"
    summary_lines.append(sl_line)
    return "\n".join(summary_lines)

# ==============================================================================
# 2. 核心交易邏輯函式 (拆分)
# ==============================================================================

def _run_single_lot_logic(day_session_candles: list, trade_candles: list, config: StrategyConfig, range_high, range_low) -> Decimal:
    """處理單口交易的完整邏輯"""
    position, entry_price, pnl, entry_candle_index = None, Decimal(0), Decimal(0), -1
    
    for i, candle in enumerate(trade_candles):
        if candle['close_price'] > range_high:
            position, entry_price, entry_candle_index = 'LONG', candle['close_price'], i
            logger.info(f"  📈 LONG  | 進場 1 口 | 時間: {candle['trade_datetime'].time()}, 價格: {entry_price}"); break
        elif candle['low_price'] < range_low:
            position, entry_price, entry_candle_index = 'SHORT', candle['close_price'], i
            logger.info(f"  📉 SHORT | 進場 1 口 | 時間: {candle['trade_datetime'].time()}, 價格: {entry_price}"); break
    
    if position:
        peak_price = entry_price
        trailing_on = False
        for exit_candle in trade_candles[entry_candle_index + 1:]:
            if (position == 'LONG' and exit_candle['close_price'] < range_low) or \
               (position == 'SHORT' and exit_candle['close_price'] > range_high):
                pnl = (exit_candle['close_price'] - entry_price) if position == 'LONG' else (entry_price - exit_candle['close_price'])
                logger.info(f"  ❌ 停損 | 出場時間: {exit_candle['trade_datetime'].time()}, 價格: {exit_candle['close_price']}, 損益: {pnl}"); break
            
            if config.use_lot1_trailing_stop:
                if position == 'LONG':
                    peak_price = max(peak_price, exit_candle['high_price'])
                    if not trailing_on and peak_price >= entry_price + config.lot1_trailing_activation: trailing_on = True
                    if trailing_on:
                        stop_price = peak_price - (peak_price - entry_price) * config.lot1_trailing_pullback
                        if exit_candle['low_price'] <= stop_price:
                            pnl = stop_price - entry_price; logger.info(f"  ✅ 移動停利 | 價格: {stop_price:.2f}, 損益: +{pnl}"); break
                else: # SHORT
                    peak_price = min(peak_price, exit_candle['low_price'])
                    if not trailing_on and peak_price <= entry_price - config.lot1_trailing_activation: trailing_on = True
                    if trailing_on:
                        stop_price = peak_price + (entry_price - peak_price) * config.lot1_trailing_pullback
                        if exit_candle['high_price'] >= stop_price:
                            pnl = entry_price - stop_price; logger.info(f"  ✅ 移動停利 | 價格: {stop_price:.2f}, 損益: +{pnl}"); break
            else: # 固定停利
                if (position == 'LONG' and exit_candle['high_price'] >= entry_price + config.lot1_fixed_tp_points) or \
                   (position == 'SHORT' and exit_candle['low_price'] <= entry_price - config.lot1_fixed_tp_points):
                    pnl = config.lot1_fixed_tp_points; logger.info(f"  ✅ 固定停利 | 損益: +{pnl}"); break
        
        if position and pnl == 0:
            exit_price = day_session_candles[-1]['close_price']
            pnl = (exit_price - entry_price) if position == 'LONG' else (entry_price - exit_price)
            logger.info(f"  ⚪️ 收盤平倉 | 出場價格: {exit_price}, 損益: {pnl}")

    return pnl

def _run_two_lot_logic(day_session_candles: list, trade_candles: list, config: StrategyConfig, range_high, range_low) -> Decimal:
    """處理雙口分批出場的完整邏輯"""
    position, entry_price, entry_time = None, Decimal(0), None
    position_size, pnl_lot1, pnl_lot2 = 0, Decimal(0), Decimal(0)
    lot1_exited, lot2_exited = False, False
    lot1_peak, lot1_trailing_on = Decimal(0), False
    lot2_peak, lot2_trailing_on = Decimal(0), False
    new_stop_for_lot2 = None

    entry_candle_index = -1
    for i, candle in enumerate(trade_candles):
        if candle['close_price'] > range_high:
            position, entry_price, entry_time, position_size = 'LONG', candle['close_price'], candle['trade_datetime'].time(), 2
            entry_candle_index = i; logger.info(f"  📈 LONG  | 進場 {position_size} 口 | 時間: {entry_time}, 價格: {entry_price}"); break
        elif candle['low_price'] < range_low:
            position, entry_price, entry_time, position_size = 'SHORT', candle['close_price'], candle['trade_datetime'].time(), 2
            entry_candle_index = i; logger.info(f"  📉 SHORT | 進場 {position_size} 口 | 時間: {entry_time}, 價格: {entry_price}"); break

    if position:
        lot1_peak = lot2_peak = entry_price
        for exit_candle in trade_candles[entry_candle_index + 1:]:
            if position_size == 0: break
            current_time = exit_candle['trade_datetime'].time()
            
            initial_stop_triggered = False
            if position == 'LONG' and not lot1_exited and exit_candle['close_price'] < range_low: initial_stop_triggered = True
            elif position == 'SHORT' and not lot1_exited and exit_candle['close_price'] > range_high: initial_stop_triggered = True
            
            if initial_stop_triggered:
                loss = (exit_candle['close_price'] - entry_price) if position == 'LONG' else (entry_price - exit_candle['close_price'])
                if not lot1_exited: pnl_lot1 = loss
                if not lot2_exited: pnl_lot2 = loss
                lot1_exited = True; lot2_exited = True; position_size = 0
                logger.info(f"  ❌ 初始停損 | 所有部位出場 | 時間: {current_time}, 價格: {exit_candle['close_price']}, 單口虧損: {loss}"); break
            
            if lot1_exited and not lot2_exited and new_stop_for_lot2 is not None:
                if (position == 'LONG' and exit_candle['low_price'] <= new_stop_for_lot2) or \
                   (position == 'SHORT' and exit_candle['high_price'] >= new_stop_for_lot2):
                    pnl_lot2 = new_stop_for_lot2 - entry_price if position == 'LONG' else entry_price - new_stop_for_lot2
                    lot2_exited = True; position_size -= 1
                    logger.info(f"  🛡️ 第二口單觸及保護性停損 | 時間: {current_time}, 出場價: {new_stop_for_lot2:.2f}, 損益: {pnl_lot2}"); continue
            
            if not lot1_exited:
                if config.use_lot1_trailing_stop:
                    if position == 'LONG':
                        lot1_peak = max(lot1_peak, exit_candle['high_price'])
                        if not lot1_trailing_on and lot1_peak >= entry_price + config.lot1_trailing_activation:
                            lot1_trailing_on = True; logger.info(f"  🔔 第1口移動停利啟動 | 時間: {current_time}")
                        if lot1_trailing_on:
                            stop_price = lot1_peak - (lot1_peak - entry_price) * config.lot1_trailing_pullback
                            if exit_candle['low_price'] <= stop_price:
                                pnl_lot1 = stop_price - entry_price; lot1_exited = True; position_size -= 1
                                logger.info(f"  ✅ 第1口移動停利 | 時間: {current_time}, 價格: {stop_price:.2f}, 損益: +{pnl_lot1}")
                                if new_stop_for_lot2 is None: new_stop_for_lot2 = entry_price - (pnl_lot1 * config.lot2_stop_loss_multiplier)
                                logger.info(f"    - 第2口單停損點更新為: {new_stop_for_lot2:.2f}")
                    elif position == 'SHORT':
                        lot1_peak = min(lot1_peak, exit_candle['low_price'])
                        if not lot1_trailing_on and lot1_peak <= entry_price - config.lot1_trailing_activation:
                            lot1_trailing_on = True; logger.info(f"  🔔 第1口移動停利啟動 | 時間: {current_time}")
                        if lot1_trailing_on:
                            stop_price = lot1_peak + (entry_price - lot1_peak) * config.lot1_trailing_pullback
                            if exit_candle['high_price'] >= stop_price:
                                pnl_lot1 = entry_price - stop_price; lot1_exited = True; position_size -= 1
                                logger.info(f"  ✅ 第1口移動停利 | 時間: {current_time}, 價格: {stop_price:.2f}, 損益: +{pnl_lot1}")
                                if new_stop_for_lot2 is None: new_stop_for_lot2 = entry_price + (pnl_lot1 * config.lot2_stop_loss_multiplier)
                                logger.info(f"    - 第2口單停損點更新為: {new_stop_for_lot2:.2f}")
                else:
                    if (position == 'LONG' and exit_candle['high_price'] >= entry_price + config.lot1_fixed_tp_points) or \
                       (position == 'SHORT' and exit_candle['low_price'] <= entry_price - config.lot1_fixed_tp_points):
                        pnl_lot1 = config.lot1_fixed_tp_points; lot1_exited = True; position_size -= 1
                        logger.info(f"  ✅ 第1口固定停利 | 時間: {current_time}, 損益: +{pnl_lot1}")
                        if position == 'LONG': new_stop_for_lot2 = entry_price - (pnl_lot1 * config.lot2_stop_loss_multiplier)
                        else: new_stop_for_lot2 = entry_price + (pnl_lot1 * config.lot2_stop_loss_multiplier)
                        logger.info(f"    - 第2口單停損點更新為: {new_stop_for_lot2:.2f}")

            if not lot2_exited and config.use_lot2_trailing_stop:
                if position == 'LONG':
                    lot2_peak = max(lot2_peak, exit_candle['high_price'])
                    if not lot2_trailing_on and lot2_peak >= entry_price + config.lot2_trailing_activation:
                        lot2_trailing_on = True; logger.info(f"  🔔 第2口移動停利啟動 | 時間: {current_time}")
                    if lot2_trailing_on:
                        stop_price = lot2_peak - (lot2_peak - entry_price) * config.lot2_trailing_pullback
                        if exit_candle['low_price'] <= stop_price:
                            pnl_lot2 = stop_price - entry_price; lot2_exited = True; position_size -= 1
                            logger.info(f"  ✅ 第2口移動停利 | 時間: {current_time}, 價格: {stop_price:.2f}, 損益: +{pnl_lot2}")
                elif position == 'SHORT':
                    lot2_peak = min(lot2_peak, exit_candle['low_price'])
                    if not lot2_trailing_on and lot2_peak <= entry_price - config.lot2_trailing_activation:
                        lot2_trailing_on = True; logger.info(f"  🔔 第2口移動停利啟動 | 時間: {current_time}")
                    if lot2_trailing_on:
                        stop_price = lot2_peak + (entry_price - lot2_peak) * config.lot2_trailing_pullback
                        if exit_candle['high_price'] >= stop_price:
                            pnl_lot2 = entry_price - stop_price; lot2_exited = True; position_size -= 1
                            logger.info(f"  ✅ 第2口移動停利 | 時間: {current_time}, 價格: {stop_price:.2f}, 損益: +{pnl_lot2}")

    day_pnl = pnl_lot1 + pnl_lot2
    if position and position_size > 0:
        exit_price = day_session_candles[-1]['close_price']
        eod_pnl = (exit_price - entry_price) if position == 'LONG' else (entry_price - exit_price)
        if not lot1_exited: pnl_lot1 = eod_pnl
        if not lot2_exited: pnl_lot2 = eod_pnl
        day_pnl = pnl_lot1 + pnl_lot2
        logger.info(f"  ⚪️ 收盤平倉剩餘 {position_size} 口 | 總損益: {day_pnl:.2f}")

    return day_pnl

# ==============================================================================
# 3. 主回測函式 (總開關)
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
                
                day_pnl = Decimal(0)
                trade_candles = [c for c in day_session_candles if c['trade_datetime'].time() >= time(8, 48)]

                if config.trade_size_in_lots == 1:
                    day_pnl = _run_single_lot_logic(day_session_candles, trade_candles, config, range_high, range_low)
                elif config.trade_size_in_lots == 2:
                    day_pnl = _run_two_lot_logic(day_session_candles, trade_candles, config, range_high, range_low)

                if day_pnl > 0: winning_trades += 1
                elif day_pnl < 0: losing_trades += 1
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

    # 實驗1：單口交易
    config_single_lot = StrategyConfig(
        trade_size_in_lots=1,
        use_lot1_trailing_stop=True,
        lot1_fixed_tp_points=Decimal(15),
    )
    
    # 實驗2：雙口交易
    config_two_lot = StrategyConfig(
        trade_size_in_lots=2,
        use_lot1_trailing_stop=True,
        lot1_fixed_tp_points=Decimal(20),
        use_lot2_trailing_stop=True,
        lot2_stop_loss_multiplier=Decimal('2'),
        lot2_trailing_activation=Decimal(40),
        lot2_trailing_pullback=Decimal('0.2')
    )
    
    # logger.info("\n---------- [測試] 執行單口交易設定 ----------")
    # run_backtest(config_single_lot)
    
    logger.info("\n---------- [測試] 執行雙口交易設定 ----------")
    run_backtest(config_two_lot)

    logger.info("⏹️  回測程式執行完畢。")

if __name__ == '__main__':
    main()