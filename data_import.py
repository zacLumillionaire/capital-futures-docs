# data_import.py
import csv
import logging
import os
from app_setup import init_all_db_pools
import shared
from psycopg2.extras import execute_values # 專為批次匯入優化的函式

# --- 設定日誌 ---
logging.basicConfig(
    level=logging.INFO,
    format='[%(asctime)s] %(levelname)s [%(name)s.%(funcName)s:%(lineno)d] %(message)s',
    datefmt='%Y-%m-%dT%H:%M:%S%z'
)
logger = logging.getLogger(__name__)

def import_stock_data(file_path, batch_size=1000):
    """
    從指定的 CSV 檔案高效地批次匯入股票資料到資料庫。
    """
    logger.info(f"🔍 正在檢查檔案路徑: {file_path}")
    if not os.path.exists(file_path):
        logger.error(f"❌ 檔案不存在或路徑錯誤: {file_path}")
        return
    logger.info(f"✅ 檔案已找到: {file_path}")

    logger.info(f"🚀 開始從 {file_path} 進行批次匯入，每批次 {batch_size} 筆...")

    try:
        with shared.get_conn_cur_from_pool_b() as (conn, cur):
            logger.info("✅ 資料庫連線成功。")
            
            with open(file_path, 'r', encoding='utf-8') as f:
                reader = csv.reader(f)
                try:
                    header = next(reader)
                    logger.info(f"🔍 CSV 檔案標頭 (已跳過): {header}")
                except StopIteration:
                    logger.warning("⚠️ CSV 檔案是空的，沒有任何資料可匯入。")
                    return

                sql = """
                    INSERT INTO stock_prices (
                        trade_datetime, open_price, high_price, low_price,
                        close_price, price_change, percentage_change, volume
                    ) VALUES %s;
                """
                
                batch_data = []
                total_rows_processed = 0
                for row in reader:
                    # 在這裡可以加入資料清洗或轉換的邏輯
                    batch_data.append(row)
                    if len(batch_data) >= batch_size:
                        try:
                            logger.info(f"⏳ 正在匯入一批次 ({len(batch_data)} 筆) 資料...")
                            execute_values(cur, sql, batch_data)
                            conn.commit()
                            total_rows_processed += len(batch_data)
                            logger.info(f"✅ 批次匯入成功。目前總計匯入 {total_rows_processed} 筆。")
                            batch_data = [] # 清空批次
                        except Exception as e:
                            logger.error(f"❌ 批次匯入失敗: {e}", exc_info=True)
                            conn.rollback()
                            # 選擇性：可以將失敗的 batch_data 存到另一個檔案以便後續分析
                            batch_data = []


                # 處理最後一批不足 batch_size 的資料
                if batch_data:
                    try:
                        logger.info(f"⏳ 正在匯入最後一批 ({len(batch_data)} 筆) 資料...")
                        execute_values(cur, sql, batch_data)
                        conn.commit()
                        total_rows_processed += len(batch_data)
                        logger.info(f"✅ 最後一批匯入成功。")
                    except Exception as e:
                        logger.error(f"❌ 最後一批匯入失敗: {e}", exc_info=True)
                        conn.rollback()

            logger.info(f"🏁 資料匯入完成。總共成功匯入 {total_rows_processed} 筆資料。")

    except Exception as e:
        logger.error(f"❌ 匯入過程中發生嚴重錯誤: {e}", exc_info=True)

def main():
    """
    主函式，用於初始化並執行資料匯入。
    """
    logger.info("▶️  資料匯入程式開始執行...")

    try:
        init_all_db_pools()
        logger.info("✅ 資料庫連線池初始化成功。")
    except Exception as e:
        logger.error(f"❌ 資料庫連線池初始化失敗: {e}", exc_info=True)
        return

    # --- 設定你要匯入的 CSV 檔案路徑 ---
    csv_file_path = "/Users/z/chrome下載/TX00_台指近_分鐘線_clean - TX00_台指近_分鐘線.csv" 

    import_stock_data(csv_file_path)

    logger.info("⏹️  資料匯入程式執行完畢。")

if __name__ == '__main__':
    main()
