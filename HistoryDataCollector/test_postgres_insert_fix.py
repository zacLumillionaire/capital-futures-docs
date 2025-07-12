#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
測試PostgreSQL插入修復
"""

import sys
import os

# 添加專案路徑
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

def test_postgres_insert():
    """測試PostgreSQL插入功能"""
    try:
        print("🚀 測試PostgreSQL插入修復...")
        
        # 導入必要的模組
        from app_setup import init_all_db_pools
        from database.postgres_importer import PostgreSQLImporter
        
        # 初始化連線池
        init_all_db_pools()
        print("✅ 連線池初始化成功")
        
        # 創建匯入器
        importer = PostgreSQLImporter()
        
        # 檢查PostgreSQL中現有資料
        print("\n🔍 檢查PostgreSQL現有資料...")
        importer.check_postgres_data()
        
        # 測試匯入少量資料
        print("\n📊 測試匯入前10筆MINUTE資料...")
        success = importer.import_kline_to_postgres(
            symbol='MTX00',
            kline_type='MINUTE',
            batch_size=5  # 小批量測試
        )
        
        if success:
            print("✅ 測試匯入成功")
            
            # 再次檢查PostgreSQL資料
            print("\n🔍 檢查匯入後的PostgreSQL資料...")
            importer.check_postgres_data()
            
        else:
            print("❌ 測試匯入失敗")
            
    except Exception as e:
        print(f"❌ 測試失敗: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_postgres_insert()
