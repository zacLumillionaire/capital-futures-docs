#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
效能比較測試
"""

import sys
import os
import time

# 添加專案路徑
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

def test_performance():
    """測試不同匯入方式的效能"""
    try:
        print("🚀 效能比較測試...")
        
        # 導入必要的模組
        from app_setup import init_all_db_pools
        from database.postgres_importer import PostgreSQLImporter
        
        # 初始化連線池
        init_all_db_pools()
        print("✅ 連線池初始化成功")
        
        # 創建匯入器
        importer = PostgreSQLImporter()
        
        print("\n" + "="*60)
        print("🔥 方法1：COPY命令（超高速）")
        print("="*60)
        
        start_time = time.time()
        success = importer.import_kline_to_postgres(
            symbol='MTX00',
            kline_type='MINUTE',
            use_copy=True
        )
        copy_time = time.time() - start_time
        
        if success:
            print(f"✅ COPY方式完成，總耗時: {copy_time:.2f}秒")
        else:
            print("❌ COPY方式失敗")
            
            print("\n" + "="*60)
            print("🔧 方法2：批量INSERT（優化版）")
            print("="*60)
            
            start_time = time.time()
            success = importer.import_kline_to_postgres(
                symbol='MTX00',
                kline_type='MINUTE',
                batch_size=1000,
                use_copy=False
            )
            batch_time = time.time() - start_time
            
            if success:
                print(f"✅ 批量INSERT完成，總耗時: {batch_time:.2f}秒")
            else:
                print("❌ 批量INSERT失敗")
        
        # 檢查最終結果
        print("\n🔍 檢查最終結果...")
        importer.check_postgres_data()
        
    except Exception as e:
        print(f"❌ 測試失敗: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_performance()
