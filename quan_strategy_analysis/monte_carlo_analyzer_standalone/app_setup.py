# app_setup.py
import os
import logging
from psycopg2 import pool as pg_pool
import shared

logger = logging.getLogger(__name__)

def init_all_db_pools() -> None:
    """
    Initializes the database connection pool for the to-wp database (pool_b).
    """
    logger.info("🚀 開始初始化資料庫連線池...")
    
    # We only need the DSN for the 'to-wp' database (DSN_B)
    DSN_B_ENV = os.getenv("HEROKU_B_DATABASE_URL")
    DSN_B_FALLBACK = "postgres://u458ccuiv3j0n9:p1a9b01ba96b99cccf60a8dd2a31f53c4726257b459138fd3dc7fe08a9b3ab1f7@c4df9f07a05oq6.cluster-czrs8kj4isg7.us-east-1.rds.amazonaws.com:5432/da8jlhg63jv4g1"
    DSN_B = DSN_B_ENV or DSN_B_FALLBACK
    
    if not DSN_B:
        logger.error("❌ 資料庫 DSN (HEROKU_B_DATABASE_URL) 未設定！")
        raise RuntimeError("資料庫 DSN (HEROKU_B_DATABASE_URL) 環境變數未設定！")
        
    try:
        # Create the connection pool for the 'to-wp' database
        pool_b = pg_pool.SimpleConnectionPool(1, 10, DSN_B, sslmode="require")
        
        # Set the pool in the shared module.
        shared.set_db_pool(pool_b)
        
        logger.info("✅ to-wp 資料庫連線池已成功建立並注入 shared 模組。")
        
    except Exception as e:
        logger.error(f"❌ 初始化資料庫連線池時發生錯誤: {e}", exc_info=True)
        raise
