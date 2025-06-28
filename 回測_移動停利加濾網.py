# 台指期開盤策略回測_完整模組化版本_V3.py
import logging
from datetime import time
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
    """定義可選擇的停損策略類型"""
    RANGE_BOUNDARY = auto()
    OPENING_PRICE = auto()
    FIXED_POINTS = auto()

@dataclass
class StrategyConfig:
    """策略設定的中央控制面板。"""
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
    """
    將 StrategyConfig 物件格式化為人類易讀的摘要字串。
    """
    summary_lines = ["\n📋======= 策略設定摘要 =======📋"]
    
    # 停利策略
    if config.use_trailing_stop:
        line = (f"  - 停利策略：移動停利 (啟用)\n"
                f"    - 觸發點數: {config.trailing_activation_points} 點\n"
                f"    - 回檔比例: {config.trailing_pullback_percent:%}")
        summary_lines.append(line)
    else:
        line = (f"  - 停利策略：固定停利 (停用移動停利)\n"
                f"    - 停利點數: {config.fixed_take_profit_points} 點")
        summary_lines.append(line)

    # 停損策略
    sl_type_map = {
        StopLossType.RANGE_BOUNDARY: "區間邊緣停損",
        StopLossType.OPENING_PRICE: "8:46開盤價停損",
        StopLossType.FIXED_POINTS: "固定點數停損"
    }
    sl_line = f"  - 停損策略：{sl_type_map[config.stop_loss_type]}"
    if config.stop_loss_type == StopLossType.FIXED_POINTS:
        sl_line += f" ({config.fixed_stop_loss_points} 點)"
    summary_lines.append(sl_line)

    # 濾網
    range_filter_status = "啟用" if config.use_range_size_filter else "停用"
    range_line = f"  - 區間大小濾網：{range_filter_status}"
    if config.use_range_size_filter:
        range_line += f" (上限: {config.max_opening_range_points} 點)"
    summary_lines.append(range_line)

    volume_filter_status = "啟用" if config.use_volume_filter else "停用"
    summary_lines.append(f"  - 成交量濾網：{volume_filter_status}")

    return "\n".join(summary_lines)


def run_backtest(config: StrategyConfig):
    """執行完整的回測流程，使用傳入的 config 物件進行設定。"""
    # 【新功能】在開頭印出設定摘要
    logger.info(format_config_summary(config))
    
    try:
        with shared.get_conn_cur_from_pool_b(as_dict=True) as (conn, cur):
            cur.execute("SELECT DISTINCT trade_datetime::date as trade_day FROM stock_prices ORDER BY trade_day;")
            trade_days = [row['trade_day'] for row in cur.fetchall()]
            logger.info(f"🔍 找到 {len(trade_days)} 個交易日進行回測。")

            total_pnl, winning_trades, losing_trades = Decimal(0), 0, 0

            for day in trade_days:
                cur.execute("SELECT * FROM stock_prices WHERE trade_datetime::date = %s ORDER BY trade_datetime;", (day,))
                all_day_candles = cur.fetchall()
                day_session_candles = [c for c in all_day_candles if time(8, 45) <= c['trade_datetime'].time() <= time(13, 45)]

                if len(day_session_candles) < 3: continue

                candles_846_847 = [c for c in day_session_candles if c['trade_datetime'].time() in [time(8, 46), time(8, 47)]]
                if len(candles_846_847) != 2:
                    logger.warning(f"⚠️ {day}: 在日盤中找不到完整的 8:46 和 8:47 K棒，跳過此日。")
                    continue

                range_high = max(c['high_price'] for c in candles_846_847)
                range_low = min(c['low_price'] for c in candles_846_847)
                opening_range_size = range_high - range_low
                logger.info(f"--- {day} | 開盤區間: {range_low} - {range_high} (大小: {opening_range_size}點) ---")

                if config.use_range_size_filter and opening_range_size > config.max_opening_range_points:
                    logger.warning(f"  🟡 跳過 | 開盤區間 {opening_range_size}點 > 設定上限 {config.max_opening_range_points}點，今日不交易。")
                    continue
                
                sl_level_opening_price = None
                if config.stop_loss_type == StopLossType.OPENING_PRICE:
                    candle_846 = next((c for c in candles_846_847 if c['trade_datetime'].time() == time(8, 46)), None)
                    if candle_846: sl_level_opening_price = candle_846['open_price']
                    else: logger.error(f"  ❌ 無法設定開盤價停損，找不到 8:46 K棒。"); continue

                position, entry_price, pnl = None, Decimal(0), Decimal(0)
                entry_time = None

                for i, candle in enumerate(day_session_candles):
                    current_time = candle['trade_datetime'].time()
                    if current_time < time(8, 48): continue
                    if position: continue

                    volume_condition_met = (not config.use_volume_filter) or \
                                           (candle['volume'] > (max(c['volume'] for c in day_session_candles[:i]) if i > 0 else 0))

                    if candle['close_price'] > range_high and volume_condition_met:
                        position, entry_price, entry_time = 'LONG', candle['close_price'], current_time
                        logger.info(f"  📈 LONG  | 進場: {entry_time}, 價格: {entry_price}")
                    elif candle['low_price'] < range_low and volume_condition_met:
                        position, entry_price, entry_time = 'SHORT', candle['close_price'], current_time
                        logger.info(f"  📉 SHORT | 進場: {entry_time}, 價格: {entry_price}")
                
                if position:
                    peak_price_after_entry, trailing_stop_activated = Decimal(0), False # 移動停利變數
                    if position == 'LONG': peak_price_after_entry = entry_price
                    else: peak_price_after_entry = entry_price

                    for candle in day_session_candles:
                        if candle['trade_datetime'].time() <= entry_time: continue
                        
                        current_time = candle['trade_datetime'].time()
                        stop_loss_triggered = False
                        
                        # 停損檢查
                        if position == 'LONG':
                            if config.stop_loss_type == StopLossType.RANGE_BOUNDARY and candle['close_price'] < range_low: stop_loss_triggered = True
                            elif config.stop_loss_type == StopLossType.OPENING_PRICE and sl_level_opening_price and candle['close_price'] < sl_level_opening_price: stop_loss_triggered = True
                            elif config.stop_loss_type == StopLossType.FIXED_POINTS and candle['low_price'] <= entry_price - config.fixed_stop_loss_points: stop_loss_triggered = True
                        elif position == 'SHORT':
                            if config.stop_loss_type == StopLossType.RANGE_BOUNDARY and candle['close_price'] > range_high: stop_loss_triggered = True
                            elif config.stop_loss_type == StopLossType.OPENING_PRICE and sl_level_opening_price and candle['close_price'] > sl_level_opening_price: stop_loss_triggered = True
                            elif config.stop_loss_type == StopLossType.FIXED_POINTS and candle['high_price'] >= entry_price + config.fixed_stop_loss_points: stop_loss_triggered = True
                        
                        if stop_loss_triggered:
                            pnl = (candle['close_price'] - entry_price) if position == 'LONG' else (entry_price - candle['close_price'])
                            logger.info(f"  ❌ 停損 ({config.stop_loss_type.name}) | 出場: {current_time}, 價格: {candle['close_price']}, 損益: {pnl:.2f}"); break

                        # 停利檢查
                        if position == 'LONG':
                            if config.use_trailing_stop:
                                peak_price_after_entry = max(peak_price_after_entry, candle['high_price'])
                                if not trailing_stop_activated and peak_price_after_entry >= entry_price + config.trailing_activation_points:
                                    trailing_stop_activated = True; logger.info(f"  🔔 移動停利已啟動 | 時間: {current_time}")
                                if trailing_stop_activated:
                                    stop_price = peak_price_after_entry - (peak_price_after_entry - entry_price) * config.trailing_pullback_percent
                                    if candle['low_price'] <= stop_price:
                                        pnl = stop_price - entry_price; logger.info(f"  ✅ 移動停利 | 出場價格: {stop_price:.2f}, 損益: +{pnl}"); break
                            else:
                                if candle['high_price'] >= entry_price + config.fixed_take_profit_points:
                                    pnl = config.fixed_take_profit_points; logger.info(f"  ✅ 固定停利 | 出場價格: {entry_price + pnl}, 損益: +{pnl}"); break
                        elif position == 'SHORT':
                            if config.use_trailing_stop:
                                peak_price_after_entry = min(peak_price_after_entry, candle['low_price'])
                                if not trailing_stop_activated and peak_price_after_entry <= entry_price - config.trailing_activation_points:
                                    trailing_stop_activated = True; logger.info(f"  🔔 移動停利已啟動 | 時間: {current_time}")
                                if trailing_stop_activated:
                                    stop_price = peak_price_after_entry + (entry_price - peak_price_after_entry) * config.trailing_pullback_percent
                                    if candle['high_price'] >= stop_price:
                                        pnl = entry_price - stop_price; logger.info(f"  ✅ 移動停利 | 出場價格: {stop_price:.2f}, 損益: +{pnl}"); break
                            else:
                                if candle['low_price'] <= entry_price - config.fixed_take_profit_points:
                                    pnl = config.fixed_take_profit_points; logger.info(f"  ✅ 固定停利 | 出場價格: {entry_price - pnl}, 損益: +{pnl}"); break

                if position and pnl == 0:
                    exit_price = day_session_candles[-1]['close_price']
                    pnl = (exit_price - entry_price) if position == 'LONG' else (entry_price - exit_price)
                    logger.info(f"  ⚪️ 收盤平倉 | 出場價格: {exit_price}, 損益: {pnl}")

                if pnl > 0: winning_trades += 1
                elif pnl < 0: losing_trades += 1
                total_pnl += pnl

            logger.info("====== 回測結果總結 ======")
            trade_count = winning_trades + losing_trades
            win_rate = (winning_trades / trade_count * 100) if trade_count > 0 else 0
            logger.info(f"總交易天數: {len(trade_days)}")
            logger.info(f"總交易次數: {trade_count}")
            logger.info(f"獲利次數: {winning_trades}")
            logger.info(f"虧損次數: {losing_trades}")
            logger.info(f"勝率: {win_rate:.2f}%")
            logger.info(f"總損益: {total_pnl:.2f}")
            
            # 【新功能】在結尾再次印出設定摘要
            logger.info(format_config_summary(config))
            logger.info("===========================")

    except Exception as e:
        logger.error(f"❌ 執行回測時發生錯誤: {e}", exc_info=True)

def main():
    logger.info("▶️  回測程式開始執行...")
    try:
        init_all_db_pools()
        logger.info("✅ 資料庫連線池初始化成功。")
    except Exception as e:
        logger.error(f"❌ 資料庫連線池初始化失敗: {e}", exc_info=True)
        return

    config_to_run = StrategyConfig(
        use_range_size_filter=False,
        use_volume_filter=False,
        use_trailing_stop=True, # <--- 改 False True 來測試移動停利
        stop_loss_type=StopLossType.RANGE_BOUNDARY,
        trailing_activation_points=Decimal(15), # 移動停利觸發點
        trailing_pullback_percent=Decimal('0.20')  # 20%回檔
    )
    run_backtest(config_to_run)
    logger.info("⏹️  回測程式執行完畢。")

if __name__ == '__main__':
    main()