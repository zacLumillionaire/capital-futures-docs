# 台指期開盤策略回測_移動停利版.py
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

def run_backtest(
    trailing_activation_points=Decimal(25),
    trailing_pullback_percent=Decimal('0.20') # 20%回檔
):
    """
    執行完整的回測流程，包含進出場與損益計算（採用移動停利）。
    
    Args:
        trailing_activation_points (Decimal): 啟動移動停利的獲利點數。
        trailing_pullback_percent (Decimal): 從最高獲利點回檔的百分比。
    """
    logger.info(f"🚀 開始執行回測... (移動停利啟動點數: {trailing_activation_points}點, 回檔比例: {trailing_pullback_percent:%})")
    
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
                day_candles = cur.fetchall()

                if len(day_candles) < 3:
                    continue

                candles_846_847 = [c for c in day_candles if c['trade_datetime'].time() in [time(8, 46), time(8, 47)]]
                if len(candles_846_847) != 2:
                    logger.warning(f"⚠️ {day}: 找不到完整的 8:46 和 8:47 K棒，跳過此日。")
                    continue

                range_high = max(c['high_price'] for c in candles_846_847)
                range_low = min(c['low_price'] for c in candles_846_847)
                logger.info(f"--- {day} | 開盤區間: {range_low} - {range_high} ---")

                position = None
                entry_price = Decimal(0)
                pnl = Decimal(0)
                
                # 移動停利相關變數
                peak_price_after_entry = Decimal(0)
                trailing_stop_activated = False

                # 從 8:48 開始檢查交易信號
                trade_candles = [c for c in day_candles if c['trade_datetime'].time() >= time(8, 48)]

                for candle in trade_candles:
                    current_time = candle['trade_datetime'].time()

                    # 尚未進場，檢查進場信號
                    if position is None:
                        if candle['close_price'] > range_high:
                            position = 'LONG'
                            entry_price = candle['close_price']
                            peak_price_after_entry = entry_price # 初始化最高價
                            logger.info(f"  📈 LONG  | 進場時間: {current_time}, 進場價格: {entry_price}")
                        elif candle['low_price'] < range_low:
                            position = 'SHORT'
                            entry_price = candle['close_price']
                            peak_price_after_entry = entry_price # 初始化最低價
                            logger.info(f"  📉 SHORT | 進場時間: {current_time}, 進場價格: {entry_price}")
                    
                    # 已進場，檢查出場信號
                    if position == 'LONG':
                        # 1. 檢查原始停損 (優先)
                        if candle['close_price'] < range_low:
                            exit_price = candle['close_price']
                            pnl = exit_price - entry_price
                            logger.info(f"  ❌ 停損 | 出場時間: {current_time}, 出場價格: {exit_price}, 損益: {pnl}")
                            break # 當日交易結束

                        # 2. 更新波段最高價
                        peak_price_after_entry = max(peak_price_after_entry, candle['high_price'])

                        # 3. 檢查是否啟動移動停利
                        if not trailing_stop_activated and peak_price_after_entry >= entry_price + trailing_activation_points:
                            trailing_stop_activated = True
                            logger.info(f"  🔔 移動停利已啟動 | 時間: {current_time}, 目前最高價: {peak_price_after_entry}")

                        # 4. 如果已啟動，檢查回檔是否觸發出場
                        if trailing_stop_activated:
                            total_gain = peak_price_after_entry - entry_price
                            pullback_amount = total_gain * trailing_pullback_percent
                            trailing_stop_price = peak_price_after_entry - pullback_amount
                            
                            if candle['low_price'] <= trailing_stop_price:
                                exit_price = trailing_stop_price # 以設定的停利價出場
                                pnl = exit_price - entry_price
                                logger.info(f"  ✅ 移動停利 | 出場時間: {current_time}, 最高價: {peak_price_after_entry}, 回檔觸發價: {trailing_stop_price:.2f}, 損益: +{pnl}")
                                break # 當日交易結束

                    elif position == 'SHORT':
                        # 1. 檢查原始停損 (優先)
                        if candle['close_price'] > range_high:
                            exit_price = candle['close_price']
                            pnl = entry_price - exit_price
                            logger.info(f"  ❌ 停損 | 出場時間: {current_time}, 出場價格: {exit_price}, 損益: {pnl}")
                            break # 當日交易結束
                        
                        # 2. 更新波段最低價
                        peak_price_after_entry = min(peak_price_after_entry, candle['low_price'])
                        
                        # 3. 檢查是否啟動移動停利
                        if not trailing_stop_activated and peak_price_after_entry <= entry_price - trailing_activation_points:
                            trailing_stop_activated = True
                            logger.info(f"  🔔 移動停利已啟動 | 時間: {current_time}, 目前最低價: {peak_price_after_entry}")

                        # 4. 如果已啟動，檢查回檔是否觸發出場
                        if trailing_stop_activated:
                            total_gain = entry_price - peak_price_after_entry
                            pullback_amount = total_gain * trailing_pullback_percent
                            trailing_stop_price = peak_price_after_entry + pullback_amount
                            
                            if candle['high_price'] >= trailing_stop_price:
                                exit_price = trailing_stop_price # 以設定的停利價出場
                                pnl = entry_price - exit_price
                                logger.info(f"  ✅ 移動停利 | 出場時間: {current_time}, 最低價: {peak_price_after_entry}, 回檔觸發價: {trailing_stop_price:.2f}, 損益: +{pnl}")
                                break # 當日交易結束
                
                if position and pnl == 0: # 如果到收盤還未出場，強制平倉
                    exit_price = day_candles[-1]['close_price']
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
    """
    主函式，初始化並執行回測。
    """
    logger.info("▶️  回測程式開始執行...")
    try:
        init_all_db_pools()
        logger.info("✅ 資料庫連線池初始化成功。")
    except Exception as e:
        logger.error(f"❌ 資料庫連線池初始化失敗: {e}", exc_info=True)
        return

    # 在這裡可以調整移動停利的參數來進行測試
    run_backtest(
        trailing_activation_points=Decimal(15),  # 獲利超過25點
        trailing_pullback_percent=Decimal('0.20') # 就啟動從最高點回檔20%出場的機制
    )

    logger.info("⏹️  回測程式執行完畢。")

if __name__ == '__main__':
    main()