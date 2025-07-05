#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
測試 API 資料收集和匯入功能
驗證從群益API收集的資料能否成功匯入到PostgreSQL
"""

import os
import sys
import time
import logging

# 添加專案路徑
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from database.postgres_importer import PostgreSQLImporter
from database.db_manager import DatabaseManager
from utils.logger import setup_logger, get_logger

# 設定日誌
setup_logger()
logger = get_logger(__name__)

def check_postgresql_tables():
    """檢查PostgreSQL表格是否存在"""
    logger.info("🔍 檢查PostgreSQL表格...")
    
    try:
        importer = PostgreSQLImporter()
        
        if not importer.postgres_initialized:
            logger.error("❌ PostgreSQL未初始化")
            return False
        
        import shared
        with shared.get_conn_cur_from_pool_b(as_dict=True) as (pg_conn, pg_cursor):
            # 檢查表格是否存在
            tables_to_check = ['stock_prices', 'tick_prices', 'best5_prices']
            existing_tables = []
            
            for table_name in tables_to_check:
                pg_cursor.execute("""
                    SELECT EXISTS (
                        SELECT FROM information_schema.tables 
                        WHERE table_name = %s
                    )
                """, (table_name,))
                
                exists = pg_cursor.fetchone()['exists']
                if exists:
                    existing_tables.append(table_name)
                    logger.info(f"✅ 表格 {table_name} 存在")
                else:
                    logger.warning(f"⚠️ 表格 {table_name} 不存在")
            
            logger.info(f"📊 找到 {len(existing_tables)}/{len(tables_to_check)} 個表格")
            return len(existing_tables) >= 2  # 至少要有2個表格
            
    except Exception as e:
        logger.error(f"❌ 檢查PostgreSQL表格失敗: {e}")
        return False

def check_sqlite_data():
    """檢查SQLite中是否有資料可匯入"""
    logger.info("🔍 檢查SQLite資料...")
    
    try:
        db_manager = DatabaseManager()
        stats = db_manager.get_data_statistics()
        
        if not stats:
            logger.warning("⚠️ 無法取得SQLite統計資料")
            return False
        
        logger.info("📊 SQLite資料統計:")
        logger.info(f"  - K線資料: {stats['kline_count']} 筆")
        logger.info(f"  - 逐筆資料: {stats['tick_count']} 筆")
        logger.info(f"  - 五檔資料: {stats['best5_count']} 筆")
        logger.info(f"  - 總計: {stats['total_count']} 筆")
        
        has_data = stats['total_count'] > 0
        if has_data:
            logger.info("✅ SQLite中有資料可匯入")
        else:
            logger.warning("⚠️ SQLite中沒有資料")
        
        return has_data
        
    except Exception as e:
        logger.error(f"❌ 檢查SQLite資料失敗: {e}")
        return False

def test_kline_import():
    """測試K線資料匯入"""
    logger.info("🧪 測試K線資料匯入...")
    
    try:
        importer = PostgreSQLImporter()
        
        start_time = time.time()
        success = importer.import_kline_to_postgres(
            symbol='MTX00',
            kline_type='MINUTE',
            batch_size=5000,
            optimize_performance=True
        )
        elapsed_time = time.time() - start_time
        
        if success:
            logger.info(f"✅ K線資料匯入成功 (耗時: {elapsed_time:.2f}秒)")
            return True
        else:
            logger.error("❌ K線資料匯入失敗")
            return False
            
    except Exception as e:
        logger.error(f"❌ K線資料匯入測試失敗: {e}")
        return False

def test_tick_import():
    """測試逐筆資料匯入"""
    logger.info("🧪 測試逐筆資料匯入...")
    
    try:
        importer = PostgreSQLImporter()
        
        start_time = time.time()
        success = importer.import_tick_to_postgres(
            symbol='MTX00',
            batch_size=5000,
            optimize_performance=True
        )
        elapsed_time = time.time() - start_time
        
        if success:
            logger.info(f"✅ 逐筆資料匯入成功 (耗時: {elapsed_time:.2f}秒)")
            return True
        else:
            logger.error("❌ 逐筆資料匯入失敗")
            return False
            
    except Exception as e:
        logger.error(f"❌ 逐筆資料匯入測試失敗: {e}")
        return False

def test_best5_import():
    """測試五檔資料匯入"""
    logger.info("🧪 測試五檔資料匯入...")
    
    try:
        importer = PostgreSQLImporter()
        
        start_time = time.time()
        success = importer.import_best5_to_postgres(
            symbol='MTX00',
            batch_size=5000,
            optimize_performance=True
        )
        elapsed_time = time.time() - start_time
        
        if success:
            logger.info(f"✅ 五檔資料匯入成功 (耗時: {elapsed_time:.2f}秒)")
            return True
        else:
            logger.error("❌ 五檔資料匯入失敗")
            return False
            
    except Exception as e:
        logger.error(f"❌ 五檔資料匯入測試失敗: {e}")
        return False

def test_all_import():
    """測試全部資料匯入"""
    logger.info("🧪 測試全部資料匯入...")
    
    try:
        importer = PostgreSQLImporter()
        
        start_time = time.time()
        success = importer.import_all_data_to_postgres(
            symbol='MTX00',
            batch_size=5000,
            optimize_performance=True
        )
        elapsed_time = time.time() - start_time
        
        if success:
            logger.info(f"✅ 全部資料匯入成功 (耗時: {elapsed_time:.2f}秒)")
            return True
        else:
            logger.error("❌ 全部資料匯入失敗")
            return False
            
    except Exception as e:
        logger.error(f"❌ 全部資料匯入測試失敗: {e}")
        return False

def check_import_results():
    """檢查匯入結果"""
    logger.info("🔍 檢查匯入結果...")
    
    try:
        importer = PostgreSQLImporter()
        stats = importer.get_postgres_data_statistics()
        
        if not stats:
            logger.warning("⚠️ 無法取得PostgreSQL統計資料")
            return False
        
        logger.info("📊 PostgreSQL匯入結果:")
        logger.info(f"  - K線資料: {stats['kline_count']:,} 筆")
        logger.info(f"  - 逐筆資料: {stats['tick_count']:,} 筆")
        logger.info(f"  - 五檔資料: {stats['best5_count']:,} 筆")
        logger.info(f"  - 總計: {stats['total_count']:,} 筆")
        
        return stats['total_count'] > 0
        
    except Exception as e:
        logger.error(f"❌ 檢查匯入結果失敗: {e}")
        return False

def main():
    """主函數"""
    logger.info("🚀 開始 API 資料收集和匯入測試...")
    logger.info("=" * 80)
    
    # 步驟1: 檢查PostgreSQL表格
    logger.info("步驟1: 檢查PostgreSQL表格")
    if not check_postgresql_tables():
        logger.error("❌ PostgreSQL表格檢查失敗")
        logger.info("請先執行以下SQL腳本建立表格:")
        logger.info("  - create_tables_simple.sql")
        return False
    
    # 步驟2: 檢查SQLite資料
    logger.info("\n步驟2: 檢查SQLite資料")
    if not check_sqlite_data():
        logger.warning("⚠️ SQLite中沒有資料")
        logger.info("請先使用GUI或CLI模式收集資料")
        logger.info("建議收集步驟:")
        logger.info("  1. 啟動程式: python main.py --mode gui")
        logger.info("  2. 登入群益API")
        logger.info("  3. 勾選逐筆資料和五檔資料")
        logger.info("  4. 收集5-10分鐘資料")
        return False
    
    # 步驟3: 測試匯入功能
    logger.info("\n步驟3: 測試匯入功能")
    
    test_results = {}
    
    # 測試K線匯入
    test_results['kline'] = test_kline_import()
    
    # 測試逐筆匯入
    test_results['tick'] = test_tick_import()
    
    # 測試五檔匯入
    test_results['best5'] = test_best5_import()
    
    # 步驟4: 檢查匯入結果
    logger.info("\n步驟4: 檢查匯入結果")
    result_check = check_import_results()
    
    # 總結
    logger.info("\n" + "=" * 80)
    logger.info("📊 測試結果總結:")
    
    success_count = sum(1 for success in test_results.values() if success)
    total_count = len(test_results)
    
    for test_name, result in test_results.items():
        status = "✅ 成功" if result else "❌ 失敗"
        logger.info(f"  {test_name} 匯入: {status}")
    
    logger.info(f"  匯入結果檢查: {'✅ 成功' if result_check else '❌ 失敗'}")
    
    overall_success = success_count == total_count and result_check
    success_rate = (success_count / total_count) * 100
    
    logger.info(f"\n🎯 總體成功率: {success_count}/{total_count} ({success_rate:.1f}%)")
    
    if overall_success:
        logger.info("🎉 所有測試通過！API資料匯入功能正常運作")
    elif success_count > 0:
        logger.info("✅ 部分測試通過，基本功能可用")
    else:
        logger.warning("⚠️ 所有測試失敗，請檢查設定和資料")
    
    return overall_success

if __name__ == "__main__":
    try:
        success = main()
        sys.exit(0 if success else 1)
    except Exception as e:
        logger.error(f"❌ 測試程式執行失敗: {e}")
        sys.exit(1)
