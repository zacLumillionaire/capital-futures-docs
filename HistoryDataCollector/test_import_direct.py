#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
直接測試匯入功能
"""

import sys
import os

# 添加專案路徑
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

def test_import():
    """直接測試匯入功能"""
    try:
        # 導入必要的模組
        from app_setup import init_all_db_pools
        from database.postgres_importer import PostgreSQLImporter
        
        print("🚀 開始測試匯入功能...")
        
        # 初始化連線池
        init_all_db_pools()
        print("✅ 連線池初始化成功")
        
        # 創建匯入器
        importer = PostgreSQLImporter()
        print("✅ PostgreSQL匯入器創建成功")
        
        # 檢查SQLite資料
        print("🔍 檢查SQLite資料...")
        importer.check_sqlite_data()
        
        # 執行匯入（只匯入前50筆測試）
        print("🚀 開始匯入前50筆資料...")
        success = importer.import_kline_to_postgres(
            symbol='MTX00',
            kline_type='MINUTE',
            batch_size=10  # 小批量測試
        )
        
        if success:
            print("✅ 匯入測試成功！")
            
            # 檢查PostgreSQL資料
            print("🔍 檢查匯入後的PostgreSQL資料...")
            importer.check_postgres_data()
            
        else:
            print("❌ 匯入測試失敗")
            
    except Exception as e:
        print(f"❌ 測試過程中發生錯誤: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_import()
