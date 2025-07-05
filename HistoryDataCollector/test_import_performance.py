#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
測試PostgreSQL匯入性能
比較不同匯入方法的速度
"""

import os
import sys
import logging
import time

# 添加專案路徑
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from database.postgres_importer_optimized import PostgreSQLImporterOptimized
from database.postgres_importer import PostgreSQLImporter
from utils.logger import setup_logger, get_logger

# 設定日誌
setup_logger()
logger = get_logger(__name__)

def test_original_importer():
    """測試原始匯入器"""
    logger.info("🧪 測試原始匯入器...")
    
    try:
        importer = PostgreSQLImporter()
        if not importer.postgres_initialized:
            logger.error("❌ PostgreSQL未初始化")
            return None
        
        start_time = time.time()
        success = importer.import_kline_to_postgres(
            symbol='MTX00',
            kline_type='MINUTE',
            batch_size=1000
        )
        elapsed_time = time.time() - start_time
        
        logger.info(f"📊 原始匯入器: {'成功' if success else '失敗'} (耗時: {elapsed_time:.2f}秒)")
        return elapsed_time if success else None
        
    except Exception as e:
        logger.error(f"❌ 原始匯入器測試失敗: {e}")
        return None

def test_optimized_importer():
    """測試優化匯入器"""
    logger.info("🧪 測試優化匯入器...")
    
    try:
        importer = PostgreSQLImporterOptimized()
        if not importer.postgres_initialized:
            logger.error("❌ PostgreSQL未初始化")
            return {}
        
        # 測試不同方法
        methods = ['copy', 'executemany', 'batch']
        results = {}
        
        for method in methods:
            logger.info(f"🔬 測試方法: {method}")
            
            # 清空表格以確保測試公平性
            clear_table()
            
            start_time = time.time()
            success = importer.import_kline_to_postgres_fast(
                symbol='MTX00',
                kline_type='MINUTE',
                method=method
            )
            elapsed_time = time.time() - start_time
            
            results[method] = {
                'success': success,
                'time': elapsed_time if success else None
            }
            
            logger.info(f"📊 {method} 方法: {'成功' if success else '失敗'} (耗時: {elapsed_time:.2f}秒)")
        
        return results
        
    except Exception as e:
        logger.error(f"❌ 優化匯入器測試失敗: {e}")
        return {}

def clear_table():
    """清空stock_prices表"""
    try:
        import shared
        with shared.get_conn_cur_from_pool_b(as_dict=False) as (pg_conn, pg_cursor):
            pg_cursor.execute("DELETE FROM stock_prices")
            pg_conn.commit()
        logger.info("🗑️ 已清空stock_prices表")
    except Exception as e:
        logger.warning(f"⚠️ 清空表格失敗: {e}")

def get_data_count():
    """取得資料筆數"""
    try:
        import shared
        with shared.get_conn_cur_from_pool_b(as_dict=False) as (pg_conn, pg_cursor):
            pg_cursor.execute("SELECT COUNT(*) FROM stock_prices")
            count = pg_cursor.fetchone()[0]
        return count
    except Exception as e:
        logger.error(f"❌ 取得資料筆數失敗: {e}")
        return 0

def analyze_table_structure():
    """分析表格結構和索引"""
    logger.info("🔍 分析stock_prices表結構...")
    
    try:
        import shared
        with shared.get_conn_cur_from_pool_b(as_dict=True) as (pg_conn, pg_cursor):
            # 檢查表格結構
            pg_cursor.execute("""
                SELECT column_name, data_type, is_nullable
                FROM information_schema.columns
                WHERE table_name = 'stock_prices'
                ORDER BY ordinal_position
            """)
            columns = pg_cursor.fetchall()
            
            logger.info("📋 表格欄位:")
            for col in columns:
                logger.info(f"  - {col['column_name']}: {col['data_type']} ({'NULL' if col['is_nullable'] == 'YES' else 'NOT NULL'})")
            
            # 檢查索引
            pg_cursor.execute("""
                SELECT indexname, indexdef
                FROM pg_indexes
                WHERE tablename = 'stock_prices'
            """)
            indexes = pg_cursor.fetchall()
            
            logger.info("🔑 表格索引:")
            for idx in indexes:
                logger.info(f"  - {idx['indexname']}: {idx['indexdef']}")
            
            # 檢查約束
            pg_cursor.execute("""
                SELECT constraint_name, constraint_type
                FROM information_schema.table_constraints
                WHERE table_name = 'stock_prices'
            """)
            constraints = pg_cursor.fetchall()
            
            logger.info("🔒 表格約束:")
            for const in constraints:
                logger.info(f"  - {const['constraint_name']}: {const['constraint_type']}")
                
    except Exception as e:
        logger.error(f"❌ 分析表格結構失敗: {e}")

def suggest_optimizations():
    """建議優化方案"""
    logger.info("💡 性能優化建議:")
    
    suggestions = [
        "1. 使用COPY命令進行大量資料匯入 (最快)",
        "2. 使用psycopg2.extras.execute_values進行批量插入",
        "3. 在匯入前暫時移除非必要索引",
        "4. 調整PostgreSQL設定: synchronous_commit = OFF",
        "5. 增加work_mem設定以提升排序和雜湊操作性能",
        "6. 使用較大的batch_size (5000-10000)",
        "7. 在匯入完成後再建立索引",
        "8. 考慮使用UNLOGGED表格進行臨時匯入"
    ]
    
    for suggestion in suggestions:
        logger.info(f"  {suggestion}")

def main():
    """主函數"""
    logger.info("🚀 開始PostgreSQL匯入性能測試...")
    
    # 分析表格結構
    analyze_table_structure()
    
    # 檢查初始資料筆數
    initial_count = get_data_count()
    logger.info(f"📊 初始資料筆數: {initial_count}")
    
    # 清空表格
    clear_table()
    
    # 測試優化匯入器
    logger.info("\n" + "="*80)
    logger.info("測試優化匯入器")
    logger.info("="*80)
    
    optimized_results = test_optimized_importer()
    
    # 顯示結果比較
    logger.info("\n" + "="*80)
    logger.info("性能測試結果總結")
    logger.info("="*80)
    
    if optimized_results:
        logger.info("🏆 優化匯入器結果:")
        fastest_method = None
        fastest_time = float('inf')
        
        for method, result in optimized_results.items():
            if result['success'] and result['time']:
                logger.info(f"  {method}: {result['time']:.2f}秒")
                if result['time'] < fastest_time:
                    fastest_time = result['time']
                    fastest_method = method
            else:
                logger.info(f"  {method}: 失敗")
        
        if fastest_method:
            logger.info(f"🥇 最快方法: {fastest_method} ({fastest_time:.2f}秒)")
            
            # 計算性能提升
            data_count = get_data_count()
            if data_count > 0:
                speed = data_count / fastest_time
                logger.info(f"📈 匯入速度: {speed:.0f} 筆/秒")
                
                # 與5分鐘比較
                original_time = 5 * 60  # 5分鐘
                improvement = original_time / fastest_time
                logger.info(f"🚀 性能提升: {improvement:.1f}倍 (從5分鐘縮短到{fastest_time:.1f}秒)")
    
    # 提供優化建議
    logger.info("\n" + "="*80)
    suggest_optimizations()
    
    logger.info("\n✅ 性能測試完成！")

if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        logger.error(f"❌ 測試程式執行失敗: {e}", exc_info=True)
        sys.exit(1)
