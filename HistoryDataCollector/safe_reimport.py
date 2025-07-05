#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
安全的重新匯入腳本
"""

import sys
import os

# 添加專案路徑
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

def safe_reimport():
    """安全的重新匯入"""
    try:
        print("🚀 安全重新匯入程序...")
        
        # 導入必要的模組
        from shared import get_conn_cur_from_pool_b
        from app_setup import init_all_db_pools
        from database.postgres_importer import PostgreSQLImporter
        
        # 初始化連線池
        init_all_db_pools()
        print("✅ 連線池初始化成功")
        
        # 步驟1：檢查現有資料
        print("\n📊 步驟1：檢查現有資料...")
        with get_conn_cur_from_pool_b(as_dict=True) as (conn, cursor):
            cursor.execute("SELECT COUNT(*) as total FROM stock_prices")
            total = cursor.fetchone()['total']
            print(f"  目前有 {total} 筆資料")
            
            if total > 0:
                confirm = input(f"\n⚠️ 發現 {total} 筆現有資料，是否要清空重新匯入？(y/N): ").strip().lower()
                if confirm == 'y':
                    print("🗑️ 清空現有資料...")
                    cursor.execute("TRUNCATE TABLE stock_prices")
                    conn.commit()
                    print("✅ 資料已清空")
                else:
                    print("❌ 使用者取消操作")
                    return
        
        # 步驟2：重新匯入
        print("\n📊 步驟2：重新匯入資料...")
        importer = PostgreSQLImporter()
        
        # 使用小批次，詳細監控
        success = importer.import_kline_to_postgres(
            symbol='MTX00',
            kline_type='MINUTE',
            batch_size=100  # 使用小批次以便監控
        )
        
        if success:
            print("✅ 重新匯入完成")
            
            # 步驟3：驗證資料
            print("\n📊 步驟3：驗證匯入的資料...")
            with get_conn_cur_from_pool_b(as_dict=True) as (conn, cursor):
                # 檢查總筆數
                cursor.execute("SELECT COUNT(*) as total FROM stock_prices")
                total = cursor.fetchone()['total']
                print(f"  匯入後總筆數: {total}")
                
                # 檢查異常資料
                cursor.execute("""
                    SELECT COUNT(*) as count
                    FROM stock_prices 
                    WHERE open_price = high_price 
                    AND high_price = low_price 
                    AND low_price = close_price
                """)
                same_price_count = cursor.fetchone()['count']
                
                cursor.execute("SELECT COUNT(*) as count FROM stock_prices WHERE volume = 0")
                zero_volume_count = cursor.fetchone()['count']
                
                print(f"  異常資料統計:")
                print(f"    所有價格相同: {same_price_count} 筆")
                print(f"    成交量為0: {zero_volume_count} 筆")
                
                # 顯示前5筆資料
                cursor.execute("""
                    SELECT trade_datetime, open_price, high_price, low_price, close_price, volume
                    FROM stock_prices 
                    ORDER BY trade_datetime ASC 
                    LIMIT 5
                """)
                
                sample_data = cursor.fetchall()
                print(f"  前5筆資料樣本:")
                for i, row in enumerate(sample_data, 1):
                    print(f"    {i}. {row['trade_datetime']} O:{row['open_price']} H:{row['high_price']} L:{row['low_price']} C:{row['close_price']} V:{row['volume']}")
                
                if same_price_count == 0 and zero_volume_count == 0:
                    print("🎉 資料驗證通過！沒有發現異常資料")
                else:
                    print("⚠️ 發現異常資料，請檢查日誌")
        else:
            print("❌ 重新匯入失敗")
            
    except Exception as e:
        print(f"❌ 重新匯入過程失敗: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    safe_reimport()
