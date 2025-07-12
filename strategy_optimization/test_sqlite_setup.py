#!/usr/bin/env python3
"""
測試 SQLite 配置
"""

import logging
import os
from pathlib import Path

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def test_sqlite_files():
    """測試 SQLite 檔案是否存在"""
    logger.info("🧪 測試 SQLite 檔案")

    # 檢查 SQLite 檔案
    sqlite_files = [
        "sqlite_connection.py",
        "stock_data.sqlite"
    ]

    all_exist = True
    for file_name in sqlite_files:
        file_path = Path(file_name)
        if file_path.exists():
            if file_name.endswith('.sqlite'):
                size_mb = file_path.stat().st_size / (1024 * 1024)
                logger.info(f"✅ {file_name} 存在 ({size_mb:.2f} MB)")
            else:
                logger.info(f"✅ {file_name} 存在")
        else:
            logger.error(f"❌ {file_name} 不存在")
            all_exist = False

    return all_exist

def test_sqlite_connection():
    """測試 SQLite 連接"""
    logger.info("🧪 測試 SQLite 連接")
    
    try:
        import sqlite_connection
        
        # 初始化連接
        sqlite_connection.init_sqlite_connection()
        logger.info("✅ SQLite 連接初始化成功")
        
        # 測試查詢
        with sqlite_connection.get_conn_cur_from_sqlite_with_adapter(as_dict=True) as (conn, cur):
            # 測試基本查詢
            cur.execute("SELECT COUNT(*) as count FROM stock_prices")
            result = cur.fetchone()
            logger.info(f"📊 SQLite 記錄總數: {result['count'] if result else 0}")
            
            # 測試日期範圍
            cur.execute("""
                SELECT 
                    MIN(date(trade_datetime)) as min_date,
                    MAX(date(trade_datetime)) as max_date
                FROM stock_prices
            """)
            result = cur.fetchone()
            if result:
                logger.info(f"📈 數據範圍: {result['min_date']} 至 {result['max_date']}")
        
        return True
        
    except Exception as e:
        logger.error(f"❌ SQLite 連接測試失敗: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_app_setup():
    """測試 app_setup 配置"""
    logger.info("🧪 測試 app_setup 配置")
    
    try:
        from app_setup import USE_SQLITE, init_all_db_pools
        
        logger.info(f"🔧 USE_SQLITE = {USE_SQLITE}")
        
        if USE_SQLITE:
            logger.info("✅ 配置為使用 SQLite")
            
            # 測試初始化
            init_all_db_pools()
            logger.info("✅ 資料庫初始化成功")
            
            # 測試 shared 模組
            import shared
            logger.info(f"🔧 SQLite 模式: {shared.is_sqlite_mode()}")
            
            # 測試連接
            with shared.get_conn_cur_from_pool_b(as_dict=True) as (conn, cur):
                cur.execute("SELECT COUNT(*) as count FROM stock_prices LIMIT 1")
                result = cur.fetchone()
                logger.info(f"📊 通過 shared 模組查詢成功: {result}")
            
        else:
            logger.warning("⚠️ 配置為使用 PostgreSQL")
        
        return True
        
    except Exception as e:
        logger.error(f"❌ app_setup 測試失敗: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_strategy_execution():
    """測試策略執行"""
    logger.info("🧪 測試策略執行")

    try:
        # 測試策略程式是否能正常初始化資料庫
        import importlib.util
        spec = importlib.util.spec_from_file_location("strategy", "multi_Profit-Funded Risk_多口.py")
        strategy_module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(strategy_module)

        # 測試初始化
        strategy_module.init_all_db_pools()
        logger.info("✅ 策略程式資料庫初始化成功")

        return True

    except Exception as e:
        logger.error(f"❌ 策略執行測試失敗: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """主測試函數"""
    logger.info("🎯 開始 SQLite 配置測試")
    
    tests = [
        ("檔案檢查", test_sqlite_files),
        ("SQLite 連接", test_sqlite_connection),
        ("app_setup 配置", test_app_setup),
        ("策略執行", test_strategy_execution)
    ]
    
    results = []
    
    for test_name, test_func in tests:
        logger.info(f"\n{'='*50}")
        logger.info(f"🧪 {test_name}")
        logger.info(f"{'='*50}")
        
        try:
            success = test_func()
            results.append((test_name, success))
        except Exception as e:
            logger.error(f"❌ {test_name} 測試異常: {e}")
            results.append((test_name, False))
    
    # 總結
    logger.info(f"\n{'='*50}")
    logger.info("📊 測試結果總結")
    logger.info(f"{'='*50}")
    
    all_passed = True
    for test_name, success in results:
        status = "✅ 通過" if success else "❌ 失敗"
        logger.info(f"   {test_name}: {status}")
        if not success:
            all_passed = False
    
    if all_passed:
        logger.info("\n🎊 所有測試通過！SQLite 配置正常")
        logger.info("💡 現在可以高速執行:")
        logger.info("   python run_time_interval_analysis.py interactive")
    else:
        logger.error("\n❌ 部分測試失敗，需要修正問題")

if __name__ == "__main__":
    main()
