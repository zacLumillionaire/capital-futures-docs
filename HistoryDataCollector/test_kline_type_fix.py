#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
測試K線類型修正
"""

import sys
import os
import sqlite3

# 添加專案路徑
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

def test_sqlite_data():
    """檢查SQLite中的實際資料"""
    print("🔍 檢查SQLite資料庫...")
    
    conn = sqlite3.connect('data/history_data.db')
    conn.row_factory = sqlite3.Row
    
    # 檢查所有資料
    cursor = conn.execute("""
        SELECT symbol, kline_type, COUNT(*) as count,
               MIN(trade_date) as min_date, MAX(trade_date) as max_date
        FROM kline_data 
        GROUP BY symbol, kline_type
        ORDER BY symbol, kline_type
    """)
    
    results = cursor.fetchall()
    print("📊 SQLite中的K線資料:")
    for row in results:
        print(f"  - {row['symbol']} {row['kline_type']}: {row['count']} 筆 ({row['min_date']} ~ {row['max_date']})")
    
    conn.close()

def test_postgres_import():
    """測試PostgreSQL匯入"""
    try:
        print("\n🚀 測試PostgreSQL匯入...")
        
        # 導入必要的模組
        from app_setup import init_all_db_pools
        from database.postgres_importer import PostgreSQLImporter
        
        # 初始化連線池
        init_all_db_pools()
        print("✅ 連線池初始化成功")
        
        # 創建匯入器
        importer = PostgreSQLImporter()
        
        # 測試匯入MINUTE資料
        print("\n📊 測試匯入MINUTE資料...")
        success = importer.import_kline_to_postgres(
            symbol='MTX00',
            kline_type='MINUTE',
            batch_size=10
        )
        
        if success:
            print("✅ MINUTE資料匯入測試成功")
        else:
            print("❌ MINUTE資料匯入測試失敗")
            
    except Exception as e:
        print(f"❌ 測試失敗: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_sqlite_data()
    test_postgres_import()
