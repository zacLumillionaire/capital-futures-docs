# shared.py
"""
集中放置：
- to-wp 資料庫連線池 (由主程式注入)
- 通用 get_conn_cur() 取連線／游標
"""

from psycopg2 import extras
from tenacity import retry, stop_after_attempt, wait_fixed, before_sleep_log
import logging

logger = logging.getLogger(__name__)

# 連線池（啟動時由 app_setup.py 注入）
db_pool_b = None

def set_db_pool(pool):
    """主程式完成 pool 建立後呼叫，把 pool 注入給其他模組用"""
    global db_pool_b
    logger.info("🔌 shared.py: 正在設定 db_pool_b...")
    db_pool_b = pool # to-wp 資料庫
    if db_pool_b:
        logger.info("✅ shared.py: db_pool_b 已成功設定。")
    else:
        logger.warning("⚠️ shared.py: 傳入的 pool 為 None！")


# 在重試之間打印日誌，這樣我們就能看到 tenacity 正在工作
log_before_retry = before_sleep_log(logger, logging.INFO)

@retry(stop=stop_after_attempt(3), wait=wait_fixed(5), before_sleep=log_before_retry)
def get_conn_cur(pool_obj, release=True, as_dict=False):
    """取得 (conn, cur)，離開 with 會自動歸還連線"""
    logger.info("➡️  進入 get_conn_cur 函式...")
    if pool_obj is None:
        logger.error("❌ DB 連線池 (pool_obj) 是 None！無法取得連線。")
        raise RuntimeError("DB 連線池尚未注入，請先呼叫 set_db_pool()")
    
    logger.info("⏳ 正在從連線池 (pool_obj) 取得連線 (getconn)...")
    try:
        conn = pool_obj.getconn()
        logger.info("✅ 成功從連線池取得連線 (conn)。")
    except Exception as e:
        logger.error(f"❌ 從連線池 getconn() 時發生錯誤: {e}", exc_info=True)
        raise # 重新拋出異常以觸發 retry

    logger.info("⏳ 正在建立資料庫游標 (cursor)...")
    cur = conn.cursor(cursor_factory=extras.DictCursor) if as_dict else conn.cursor()
    logger.info("✅ 成功建立資料庫游標 (cur)。")

    class Wrapper:
        def __enter__(self):
            logger.info("🎁 返回 (conn, cur) 上下文管理器。")
            return conn, cur

        def __exit__(self, exc_type, exc_val, exc_tb):
            logger.info("🚪 正在離開 (conn, cur) 上下文...")
            cur.close()
            if release:
                logger.info("📬 正在將連線歸還到連線池 (putconn)...")
                pool_obj.putconn(conn)
                logger.info("✅ 連線已成功歸還。")

    return Wrapper()

@retry(stop=stop_after_attempt(3), wait=wait_fixed(10))
def get_conn_cur_from_pool_b(release=True, as_dict=False):
    """從 pool_b 取得 (conn, cur)"""
    logger.info("➡️  準備從 pool_b 取得連線...")
    return get_conn_cur(db_pool_b, release, as_dict)