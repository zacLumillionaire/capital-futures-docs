#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
檢查PostgreSQL中的實際資料
"""

import sys
import os

# 添加專案路徑
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

def check_postgres_data():
    """檢查PostgreSQL中的實際資料"""
    try:
        print("🔍 檢查PostgreSQL中的實際資料...")
        
        # 導入必要的模組
        from shared import get_conn_cur_from_pool_b
        from app_setup import init_all_db_pools
        
        # 初始化連線池
        init_all_db_pools()
        print("✅ 連線池初始化成功")
        
        with get_conn_cur_from_pool_b(as_dict=True) as (conn, cursor):
            
            # 檢查總筆數
            cursor.execute("SELECT COUNT(*) as total FROM stock_prices")
            total = cursor.fetchone()['total']
            print(f"📊 PostgreSQL中總共有 {total} 筆資料")
            
            # 檢查最新的10筆資料
            cursor.execute("""
                SELECT trade_datetime, open_price, high_price, low_price, close_price, volume
                FROM stock_prices 
                ORDER BY trade_datetime DESC 
                LIMIT 10
            """)
            
            recent_data = cursor.fetchall()
            print(f"\n📈 最新10筆資料:")
            for i, row in enumerate(recent_data, 1):
                print(f"  {i}. {row['trade_datetime']} O:{row['open_price']} H:{row['high_price']} L:{row['low_price']} C:{row['close_price']} V:{row['volume']}")
                
                # 檢查是否所有價格都相同
                if row['open_price'] == row['high_price'] == row['low_price'] == row['close_price']:
                    print(f"     ⚠️ 警告：所有價格都相同！")
                
                if row['volume'] == 0:
                    print(f"     ⚠️ 警告：成交量為0！")
            
            # 檢查最早的10筆資料
            cursor.execute("""
                SELECT trade_datetime, open_price, high_price, low_price, close_price, volume
                FROM stock_prices 
                ORDER BY trade_datetime ASC 
                LIMIT 10
            """)
            
            earliest_data = cursor.fetchall()
            print(f"\n📈 最早10筆資料:")
            for i, row in enumerate(earliest_data, 1):
                print(f"  {i}. {row['trade_datetime']} O:{row['open_price']} H:{row['high_price']} L:{row['low_price']} C:{row['close_price']} V:{row['volume']}")
                
                # 檢查是否所有價格都相同
                if row['open_price'] == row['high_price'] == row['low_price'] == row['close_price']:
                    print(f"     ⚠️ 警告：所有價格都相同！")
                
                if row['volume'] == 0:
                    print(f"     ⚠️ 警告：成交量為0！")
            
            # 檢查特定時間的資料（對應SQLite中的資料）
            cursor.execute("""
                SELECT trade_datetime, open_price, high_price, low_price, close_price, volume
                FROM stock_prices 
                WHERE trade_datetime >= '2025-04-02 15:01:00'
                AND trade_datetime <= '2025-04-02 15:05:00'
                ORDER BY trade_datetime ASC
            """)
            
            specific_data = cursor.fetchall()
            print(f"\n📈 2025-04-02 15:01-15:05的資料 (對應SQLite):")
            if specific_data:
                for i, row in enumerate(specific_data, 1):
                    print(f"  {i}. {row['trade_datetime']} O:{row['open_price']} H:{row['high_price']} L:{row['low_price']} C:{row['close_price']} V:{row['volume']}")
            else:
                print("  ❌ 沒有找到對應時間的資料")
            
            # 統計異常資料
            cursor.execute("""
                SELECT COUNT(*) as count
                FROM stock_prices 
                WHERE open_price = high_price 
                AND high_price = low_price 
                AND low_price = close_price
            """)
            
            same_price_count = cursor.fetchone()['count']
            print(f"\n⚠️ 所有價格相同的資料筆數: {same_price_count}")
            
            cursor.execute("""
                SELECT COUNT(*) as count
                FROM stock_prices 
                WHERE volume = 0
            """)
            
            zero_volume_count = cursor.fetchone()['count']
            print(f"⚠️ 成交量為0的資料筆數: {zero_volume_count}")
            
    except Exception as e:
        print(f"❌ 檢查失敗: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    check_postgres_data()
