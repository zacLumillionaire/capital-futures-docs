# test_connection.py
import logging
from app_setup import init_all_db_pools
import shared

# --- 設定日誌 ---
logging.basicConfig(
    level=logging.INFO,
    format='[%(asctime)s] %(levelname)s [%(name)s.%(funcName)s:%(lineno)d] %(message)s',
    datefmt='%Y-%m-%dT%H:%M:%S%z'
)
logger = logging.getLogger(__name__)

def check_db_connection():
    """
    執行一個簡單的資料庫查詢來驗證連線。
    """
    logger.info("🚀 開始進行資料庫連線測試...")
    try:
        logger.info("⏳ 正在嘗試從 pool_b 取得連線和游標...")
        with shared.get_conn_cur_from_pool_b() as (conn, cur):
            logger.info("✅ 成功取得連線和游標。")
            
            logger.info("⏳ 正在執行一個簡單的測試查詢 (SELECT 1)...")
            cur.execute("SELECT 1;")
            result = cur.fetchone()
            logger.info(f"✅ 查詢執行成功，資料庫返回: {result}")
            
            if result and result[0] == 1:
                logger.info("🎉🎉🎉 資料庫連線功能完全正常！")
            else:
                logger.error("❌ 查詢結果不符合預期！")

    except Exception as e:
        logger.error(f"❌ 在測試資料庫連線時發生錯誤: {e}", exc_info=True)

def main():
    """
    主函式，初始化並執行連線測試。
    """
    logger.info("▶️  連線測試程式開始執行...")

    try:
        init_all_db_pools()
        logger.info("✅ 資料庫連線池初始化函式已呼叫。")
    except Exception as e:
        logger.error(f"❌ 資料庫連線池初始化過程中拋出異常: {e}", exc_info=True)
        return

    check_db_connection()

    logger.info("⏹️  連線測試程式執行完畢。")

if __name__ == '__main__':
    main()
