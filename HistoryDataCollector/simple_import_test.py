#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
簡單的匯入測試
"""

import sqlite3
import sys
import os
from datetime import datetime
from decimal import Decimal

# 添加專案路徑
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

def test_data_conversion():
    """測試資料轉換"""
    print("🔍 測試資料轉換...")
    
    # 連接SQLite
    conn = sqlite3.connect('data/history_data.db')
    conn.row_factory = sqlite3.Row
    
    # 查詢前5筆資料
    cursor = conn.execute("""
        SELECT * FROM kline_data 
        WHERE symbol = 'MTX00' AND kline_type = 'MINUTE'
        ORDER BY trade_date, trade_time
        LIMIT 5
    """)
    
    rows = cursor.fetchall()
    print(f"📊 查詢到 {len(rows)} 筆資料")
    
    for i, row in enumerate(rows, 1):
        print(f"\n--- 第{i}筆資料 ---")
        row_dict = dict(row)
        print(f"原始資料: {row_dict}")
        
        # 手動轉換資料
        try:
            date_str = str(row_dict['trade_date']).strip()
            print(f"日期字串: '{date_str}'")
            
            # 解析日期時間
            try:
                trade_datetime = datetime.strptime(date_str, '%Y/%m/%d %H:%M')
                print(f"✅ 日期解析成功: {trade_datetime}")
            except ValueError as e:
                print(f"❌ 日期解析失敗: {e}")
                continue
            
            # 轉換為目標格式
            converted = {
                'trade_datetime': trade_datetime,
                'open_price': Decimal(str(row_dict['open_price'])),
                'high_price': Decimal(str(row_dict['high_price'])),
                'low_price': Decimal(str(row_dict['low_price'])),
                'close_price': Decimal(str(row_dict['close_price'])),
                'price_change': Decimal('0.00'),
                'percentage_change': Decimal('0.0000'),
                'volume': row_dict['volume'] or 0
            }
            
            print(f"✅ 轉換成功: {converted}")
            
        except Exception as e:
            print(f"❌ 轉換失敗: {e}")
    
    conn.close()

def test_simple_postgres_insert():
    """測試簡單的PostgreSQL插入"""
    try:
        print("\n🔌 測試PostgreSQL連接...")
        
        # 導入必要的模組
        sys.path.append('../')
        from shared import get_conn_cur_from_pool_b
        from app_setup import init_all_db_pools
        
        # 初始化連線池
        init_all_db_pools()
        print("✅ 連線池初始化成功")
        
        # 測試插入一筆資料
        with get_conn_cur_from_pool_b(as_dict=False) as (conn, cursor):
            
            # 檢查表是否存在
            cursor.execute("""
                SELECT EXISTS (
                    SELECT FROM information_schema.tables
                    WHERE table_name = 'stock_prices'
                )
            """)
            
            if cursor.fetchone()[0]:
                print("✅ stock_prices表存在")
                
                # 插入測試資料
                test_data = (
                    datetime(2025, 7, 5, 9, 0, 0),  # trade_datetime
                    Decimal('22000.00'),            # open_price
                    Decimal('22010.00'),            # high_price
                    Decimal('21990.00'),            # low_price
                    Decimal('22005.00'),            # close_price
                    Decimal('5.00'),                # price_change
                    Decimal('0.0227'),              # percentage_change
                    1000                            # volume
                )
                
                cursor.execute("""
                    INSERT INTO stock_prices (
                        trade_datetime, open_price, high_price, low_price,
                        close_price, price_change, percentage_change, volume
                    ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                """, test_data)
                
                conn.commit()
                print("✅ 測試資料插入成功")
                
                # 查詢剛插入的資料
                cursor.execute("""
                    SELECT * FROM stock_prices 
                    WHERE trade_datetime = %s
                """, (test_data[0],))
                
                result = cursor.fetchone()
                if result:
                    print(f"✅ 查詢成功: {result}")
                else:
                    print("❌ 查詢失敗")
                    
            else:
                print("❌ stock_prices表不存在")
                
    except Exception as e:
        print(f"❌ PostgreSQL測試失敗: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_data_conversion()
    test_simple_postgres_insert()
