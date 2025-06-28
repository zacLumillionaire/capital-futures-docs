# 台指期開盤策略回測_完全同步版_V2.py
import logging
from datetime import time
from decimal import Decimal
from app_setup import init_all_db_pools
import shared

# --- 設定日誌 ---
logging.basicConfig(
    level=logging.INFO,
    format='[%(asctime)s] %(levelname)s [%(name)s.%(funcName)s:%(lineno)d] %(message)s',
    datefmt='%Y-%m-%dT%H:%M:%S%z'
)
logger = logging.getLogger(__name__)

def run_backtest(take_profit_points=Decimal(15)):
    """
    執行完整的回測流程，包含進出場與損益計算。
    (已修正時光倒流問題，並同步日盤資料濾網)
    
    Args:
        take_profit_points (Decimal): 獲利點數。
    """
    logger.info(f"🚀 開始執行回測... (停利點數: {take_profit_points}點, 完全同步邏輯)")
    
    try:
        with shared.get_conn_cur_from_pool_b(as_dict=True) as (conn, cur):
            cur.execute("SELECT DISTINCT trade_datetime::date as trade_day FROM stock_prices ORDER BY trade_day;")
            trade_days = [row['trade_day'] for row in cur.fetchall()]
            logger.info(f"🔍 找到 {len(trade_days)} 個交易日進行回測。")

            total_pnl = Decimal(0)
            winning_trades = 0
            losing_trades = 0

            for day in trade_days:
                cur.execute(
                    "SELECT * FROM stock_prices WHERE trade_datetime::date = %s ORDER BY trade_datetime;",
                    (day,)
                )
                all_day_candles = cur.fetchall()

                day_session_candles = [
                    c for c in all_day_candles 
                    if time(8, 45) <= c['trade_datetime'].time() <= time(13, 45)
                ]

                if len(day_session_candles) < 3:
                    continue

                candles_846_847 = [c for c in day_session_candles if c['trade_datetime'].time() in [time(8, 46), time(8, 47)]]
                if len(candles_846_847) != 2:
                    logger.warning(f"⚠️ {day}: 在日盤中找不到完整的 8:46 和 8:47 K棒，跳過此日。")
                    continue

                range_high = max(c['high_price'] for c in candles_846_847)
                range_low = min(c['low_price'] for c in candles_846_847)
                logger.info(f"--- {day} | 開盤區間: {range_low} - {range_high} ---")

                position = None
                entry_price = Decimal(0)
                pnl = Decimal(0)
                entry_candle_index = -1

                trade_candles = [c for c in day_session_candles if c['trade_datetime'].time() >= time(8, 48)]

                # 第一段：尋找進場點
                for i, candle in enumerate(trade_candles):
                    if candle['close_price'] > range_high:
                        position, entry_price, entry_candle_index = 'LONG', candle['close_price'], i
                        logger.info(f"  📈 LONG  | 進場時間: {candle['trade_datetime'].time()}, 進場價格: {entry_price}")
                        break
                    elif candle['low_price'] < range_low:
                        position, entry_price, entry_candle_index = 'SHORT', candle['close_price'], i
                        logger.info(f"  📉 SHORT | 進場時間: {candle['trade_datetime'].time()}, 進場價格: {entry_price}")
                        break
                
                # 第二段：監控出場點
                if position:
                    for candle in trade_candles[entry_candle_index + 1:]:
                        if position == 'LONG':
                            if candle['high_price'] >= entry_price + take_profit_points:
                                pnl = take_profit_points
                                logger.info(f"  ✅ 停利 | 出場時間: {candle['trade_datetime'].time()}, 出場價格: {entry_price + pnl}, 損益: +{pnl}")
                                break
                            elif candle['close_price'] < range_low:
                                pnl = candle['close_price'] - entry_price
                                logger.info(f"  ❌ 停損 | 出場時間: {candle['trade_datetime'].time()}, 出場價格: {candle['close_price']}, 損益: {pnl}")
                                break
                        elif position == 'SHORT':
                            if candle['low_price'] <= entry_price - take_profit_points:
                                pnl = take_profit_points
                                logger.info(f"  ✅ 停利 | 出場時間: {candle['trade_datetime'].time()}, 出場價格: {entry_price - pnl}, 損益: +{pnl}")
                                break
                            elif candle['close_price'] > range_high:
                                pnl = entry_price - candle['close_price']
                                # 【錯誤修正】這裡使用了正確的 candle['close_price']
                                logger.info(f"  ❌ 停損 | 出場時間: {candle['trade_datetime'].time()}, 出場價格: {candle['close_price']}, 損益: {pnl}")
                                break
                
                if position and pnl == 0:
                    exit_price = day_session_candles[-1]['close_price']
                    if position == 'LONG': pnl = exit_price - entry_price
                    else: pnl = entry_price - exit_price
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

    run_backtest(take_profit_points=Decimal(15))
    logger.info("⏹️  回測程式執行完畢。")

if __name__ == '__main__':
    main()