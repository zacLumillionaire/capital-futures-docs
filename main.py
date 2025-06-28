# main.py
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

def fetch_wp_domains_data():
    """
    從 to-wp 資料庫的 wp_domains 資料表中獲取資料。
    """
    logger.info("🚀 開始從 wp_domains 獲取資料...")
    try:
        # 從 pool_b 取得連線和游標
        with shared.get_conn_cur_from_pool_b(as_dict=True) as (conn, cur):
            sql_query = "SELECT * FROM wp_domains LIMIT 5;"
            cur.execute(sql_query)
            
            results = cur.fetchall()
            
            if results:
                logger.info(f"✅ 成功從 wp_domains 獲取到 {len(results)} 筆資料：")
                for row in results:
                    print(dict(row))
            else:
                logger.info("⚠️ 在 wp_domains 資料表中找不到資料。")
                
    except Exception as e:
        logger.error(f"❌ 獲取 wp_domains 資料時發生錯誤: {e}", exc_info=True)

def main():
    """
    主函式，用於初始化並執行主要邏輯。
    """
    logger.info("▶️  程式開始執行...")
    
    # --- 應用程式啟動時的初始化 ---
    try:
        init_all_db_pools()
        logger.info("✅ 資料庫連線池初始化成功。")
    except Exception as e:
        logger.error(f"❌ 資料庫連線池初始化失敗: {e}", exc_info=True)
        return # 初始化失敗，直接退出

    # --- 執行主要任務 ---
    fetch_wp_domains_data()
    
    logger.info("⏹️  程式執行完畢。")


# --- 啟動設定 ---
if __name__ == '__main__':
    main()
