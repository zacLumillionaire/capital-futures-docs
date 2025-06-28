# 台指期開盤策略回測_完整模組化版本_V9_整合多重停損.py
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
# 1. 策略設定與輔助函式 (此部分不變)
# ==============================================================================

class StopLossType(Enum):
    RANGE_BOUNDARY = auto(); OPENING_PRICE = auto(); FIXED_POINTS = auto()

@dataclass
class StrategyConfig:
    use_trend_filter: bool = False
    use_range_size_filter: bool = False
    use_volume_filter: bool = False
    use_trailing_stop: bool = False
    stop_loss_type: StopLossType = StopLossType.RANGE_BOUNDARY
    max_opening_range_points: Decimal = Decimal(100)
    trailing_activation_points: Decimal = Decimal(25)
    trailing_pullback_percent: Decimal = Decimal('0.20')
    fixed_take_profit_points: Decimal = Decimal(15)
    fixed_stop_loss_points: Decimal = Decimal(40)

def format_config_summary(config: StrategyConfig) -> str:
    summary_lines = ["\n📋======= 策略設定摘要 =======📋"]
    if config.use_trailing_stop:
        line = (f"  - 停利策略：移動停利 (啟用)\n"
                f"    - 觸發點數: {config.trailing_activation_points} 點\n"
                f"    - 回檔比例: {config.trailing_pullback_percent:%}")
    else:
        line = (f"  - 停利策略：固定停利\n"
                f"    - 停利點數: {config.fixed_take_profit_points} 點")
    summary_lines.append(line)
    sl_type_map = { StopLossType.RANGE_BOUNDARY: "區間邊緣停損", StopLossType.OPENING_PRICE: "8:46開盤價停損", StopLossType.FIXED_POINTS: "固定點數停損" }
    sl_line = f"  - 停損策略：{sl_type_map[config.stop_loss_type]}"
    if config.stop_loss_type == StopLossType.FIXED_POINTS: sl_line += f" ({config.fixed_stop_loss_points} 點)"
    summary_lines.append(sl_line)
    
    summary_lines.append("  --- 濾網設定 ---")
    trend_filter_status = "啟用" if config.use_trend_filter else "停用"
    summary_lines.append(f"  - 趨勢濾網 (今開 vs 昨收)：{trend_filter_status}")
    range_filter_status = "啟用" if config.use_range_size_filter else "停用"
    range_line = f"  - 區間大小濾網：{range_filter_status}"
    if config.use_range_size_filter: range_line += f" (上限: {config.max_opening_range_points} 點)"
    summary_lines.append(range_line)
    volume_filter_status = "啟用" if config.use_volume_filter else "停用"
    summary_lines.append(f"  - 成交量濾網：{volume_filter_status}")
    return "\n".join(summary_lines)


def run_backtest(config: StrategyConfig):
    """執行完整的回測流程，使用傳入的 config 物件進行設定。"""
    logger.info(format_config_summary(config))
    
    try:
        with shared.get_conn_cur_from_pool_b(as_dict=True) as (conn, cur):
            cur.execute("SELECT DISTINCT trade_datetime::date as trade_day FROM stock_prices ORDER BY trade_day;")
            trade_days = [row['trade_day'] for row in cur.fetchall()]
            logger.info(f"🔍 找到 {len(trade_days)} 個交易日進行回測。")

            total_pnl, winning_trades, losing_trades = Decimal(0), 0, 0
            prev_day_close = None

            for day in trade_days:
                # ... (每日資料準備與趨勢濾網判斷邏輯不變) ...
                cur.execute("SELECT * FROM stock_prices WHERE trade_datetime::date = %s ORDER BY trade_datetime;", (day,))
                all_day_candles = cur.fetchall()
                day_session_candles = [c for c in all_day_candles if time(8, 45) <= c['trade_datetime'].time() <= time(13, 45)]
                if len(day_session_candles) < 3: continue
                trend_ok_for_long, trend_ok_for_short = True, True
                if config.use_trend_filter:
                    if prev_day_close is None:
                        logger.warning(f"--- {day} | 無法應用趨勢濾網 (無前一日資料)，跳過此日 ---")
                        if day_session_candles: prev_day_close = day_session_candles[-1]['close_price']
                        continue
                    today_open = day_session_candles[0]['open_price']
                    trend_ok_for_long = today_open > prev_day_close; trend_ok_for_short = today_open < prev_day_close
                    trend_dir = "偏多" if trend_ok_for_long else "偏空" if trend_ok_for_short else "中性"
                    logger.info(f"--- {day} | 今開({today_open}) vs 昨收({prev_day_close}) | 趨勢: {trend_dir} ---")
                else:
                    logger.info(f"--- {day} ---")

                # ... (開盤區間計算與其他濾網邏輯不變) ...
                candles_846_847 = [c for c in day_session_candles if c['trade_datetime'].time() in [time(8, 46), time(8, 47)]]
                if len(candles_846_847) != 2:
                    logger.warning(f"⚠️ {day}: 在日盤中找不到完整的 8:46 和 8:47 K棒，跳過此日。")
                    if config.use_trend_filter and day_session_candles: prev_day_close = day_session_candles[-1]['close_price']
                    continue
                range_high, range_low = max(c['high_price'] for c in candles_846_847), min(c['low_price'] for c in candles_846_847)
                logger.info(f"    開盤區間: {range_low} - {range_high}")

                # --- 【新功能】根據停損模式，預先準備停損價位 ---
                sl_level_opening_price = None
                if config.stop_loss_type == StopLossType.OPENING_PRICE:
                    candle_846 = next((c for c in candles_846_847 if c['trade_datetime'].time() == time(8, 46)), None)
                    if candle_846:
                        sl_level_opening_price = candle_846['open_price']
                        logger.info(f"    設定停損點位 (開盤價): {sl_level_opening_price}")
                    else:
                        logger.error(f"  ❌ {day}: 無法設定開盤價停損，找不到 8:46 K棒。")
                        if config.use_trend_filter and day_session_candles: prev_day_close = day_session_candles[-1]['close_price']
                        continue

                # ... (進場前的變數初始化與進場迴圈邏輯不變) ...
                position, entry_price, pnl, entry_candle_index = None, Decimal(0), Decimal(0), -1
                trade_candles = [c for c in day_session_candles if c['trade_datetime'].time() >= time(8, 48)]
                for i, candle in enumerate(trade_candles):
                    if candle['close_price'] > range_high:
                        if config.use_trend_filter and not trend_ok_for_long: logger.info(f"  - LONG信號過濾 | 時間: {candle['trade_datetime'].time()}, 原因: 不符趨勢偏多條件。當日不再交易。"); break
                        position, entry_price, entry_candle_index = 'LONG', candle['close_price'], i
                        logger.info(f"  📈 LONG  | 進場時間: {candle['trade_datetime'].time()}, 進場價格: {entry_price}"); break
                    elif candle['low_price'] < range_low:
                        if config.use_trend_filter and not trend_ok_for_short: logger.info(f"  - SHORT信號過濾 | 時間: {candle['trade_datetime'].time()}, 原因: 不符趨勢偏空條件。當日不再交易。"); break
                        position, entry_price, entry_candle_index = 'SHORT', candle['close_price'], i
                        logger.info(f"  📉 SHORT | 進場時間: {candle['trade_datetime'].time()}, 進場價格: {entry_price}"); break
                
                if position:
                    peak_price_after_entry = entry_price
                    trailing_stop_activated = False
                    
                    for exit_candle in trade_candles[entry_candle_index + 1:]:
                        current_time = exit_candle['trade_datetime'].time()
                        
                        # --- 【邏輯修改】1. 停損檢查 (優先權最高，三選一) ---
                        stop_loss_triggered = False
                        if position == 'LONG':
                            if config.stop_loss_type == StopLossType.RANGE_BOUNDARY and exit_candle['close_price'] < range_low: stop_loss_triggered = True
                            elif config.stop_loss_type == StopLossType.OPENING_PRICE and sl_level_opening_price and exit_candle['close_price'] < sl_level_opening_price: stop_loss_triggered = True
                            elif config.stop_loss_type == StopLossType.FIXED_POINTS and exit_candle['low_price'] <= entry_price - config.fixed_stop_loss_points: stop_loss_triggered = True
                        elif position == 'SHORT':
                            if config.stop_loss_type == StopLossType.RANGE_BOUNDARY and exit_candle['close_price'] > range_high: stop_loss_triggered = True
                            elif config.stop_loss_type == StopLossType.OPENING_PRICE and sl_level_opening_price and exit_candle['close_price'] > sl_level_opening_price: stop_loss_triggered = True
                            elif config.stop_loss_type == StopLossType.FIXED_POINTS and exit_candle['high_price'] >= entry_price + config.fixed_stop_loss_points: stop_loss_triggered = True
                        
                        if stop_loss_triggered:
                            pnl = (exit_candle['close_price'] - entry_price) if position == 'LONG' else (entry_price - exit_candle['close_price'])
                            logger.info(f"  ❌ 停損 ({config.stop_loss_type.name}) | 出場: {current_time}, 價格: {exit_candle['close_price']}, 損益: {pnl:.2f}")
                            break

                        # 2. 停利檢查 (二選一，邏輯不變)
                        if config.use_trailing_stop:
                            if position == 'LONG':
                                peak_price_after_entry = max(peak_price_after_entry, exit_candle['high_price'])
                                if not trailing_stop_activated and peak_price_after_entry >= entry_price + config.trailing_activation_points:
                                    trailing_stop_activated = True; logger.info(f"  🔔 移動停利已啟動 | 時間: {current_time}")
                                if trailing_stop_activated:
                                    stop_price = peak_price_after_entry - (peak_price_after_entry - entry_price) * config.trailing_pullback_percent
                                    if exit_candle['low_price'] <= stop_price:
                                        pnl = stop_price - entry_price; logger.info(f"  ✅ 移動停利 | 出場價格: {stop_price:.2f}, 損益: +{pnl}"); break
                            elif position == 'SHORT':
                                peak_price_after_entry = min(peak_price_after_entry, exit_candle['low_price'])
                                if not trailing_stop_activated and peak_price_after_entry <= entry_price - config.trailing_activation_points:
                                    trailing_stop_activated = True; logger.info(f"  🔔 移動停利已啟動 | 時間: {current_time}")
                                if trailing_stop_activated:
                                    stop_price = peak_price_after_entry + (entry_price - peak_price_after_entry) * config.trailing_pullback_percent
                                    if exit_candle['high_price'] >= stop_price:
                                        pnl = entry_price - stop_price; logger.info(f"  ✅ 移動停利 | 出場價格: {stop_price:.2f}, 損益: +{pnl}"); break
                        else:
                            if position == 'LONG' and exit_candle['high_price'] >= entry_price + config.fixed_take_profit_points:
                                pnl = config.fixed_take_profit_points; logger.info(f"  ✅ 固定停利 | 出場價格: {entry_price + pnl}, 損益: +{pnl}"); break
                            elif position == 'SHORT' and exit_candle['low_price'] <= entry_price - config.fixed_take_profit_points:
                                pnl = config.fixed_take_profit_points; logger.info(f"  ✅ 固定停利 | 出場價格: {entry_price - pnl}, 損益: +{pnl}"); break
                
                if position and pnl == 0:
                    exit_price = day_session_candles[-1]['close_price']
                    pnl = (exit_price - entry_price) if position == 'LONG' else (entry_price - exit_price)
                    logger.info(f"  ⚪️ 收盤平倉 | 出場價格: {exit_price}, 損益: {pnl}")
                
                if pnl > 0: winning_trades += 1
                elif pnl < 0: losing_trades += 1
                total_pnl += pnl
                
                if config.use_trend_filter and day_session_candles:
                    prev_day_close = day_session_candles[-1]['close_price']

            logger.info("====== 回測結果總結 ======")
            trade_count = winning_trades + losing_trades
            win_rate = (winning_trades / trade_count * 100) if trade_count > 0 else 0
            logger.info(f"總交易天數: {len(trade_days)}")
            logger.info(f"總交易次數: {trade_count}")
            logger.info(f"獲利次數: {winning_trades}")
            logger.info(f"虧損次數: {losing_trades}")
            logger.info(f"勝率: {win_rate:.2f}%")
            logger.info(f"總損益: {total_pnl:.2f}")
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
    # 範例：啟用「開盤價停損」並搭配移動停利
    config_opening_price_stop = StrategyConfig(
        stop_loss_type=StopLossType.RANGE_BOUNDARY, # <--- 啟用開盤價停損
        use_trailing_stop=True, # <--- 搭配移動停利
        trailing_activation_points=Decimal(15)
    )
    
    logger.info("\n---------- [測試] 執行「開盤價停損」+「移動停利」設定 ----------")
    run_backtest(config_opening_price_stop)
    
    logger.info("⏹️  回測程式執行完畢。")

if __name__ == '__main__':
    main()