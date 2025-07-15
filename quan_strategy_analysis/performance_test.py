#!/usr/bin/env python3
"""
性能測試腳本 - 測試數據庫查詢性能
"""

import time
import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from datetime import datetime, time as dt_time
import shared
import app_setup

def test_db_performance():
    """測試數據庫查詢性能"""
    
    print("🔍 測試數據庫查詢性能...")
    
    # 初始化數據庫連線池
    try:
        app_setup.init_all_db_pools()
        print("✅ 資料庫連線池初始化成功。")
    except Exception as e:
        print(f"❌ 資料庫連線池初始化失敗: {e}")
        return
    
    try:
        with shared.get_conn_cur_from_pool_b(as_dict=True) as (conn, cur):
            # 測試1：查詢交易日列表
            start_time = time.time()
            base_query = "SELECT DISTINCT trade_datetime::date as trade_day FROM stock_prices"
            conditions = ["trade_datetime::date >= %s", "trade_datetime::date <= %s"]
            query = f"{base_query} WHERE {' AND '.join(conditions)} ORDER BY trade_day;"
            params = ['2024-11-01', '2024-11-05']
            
            cur.execute(query, params)
            trade_days = [row['trade_day'] for row in cur.fetchall()]
            end_time = time.time()
            
            print(f"📅 查詢交易日列表: {len(trade_days)} 天, 耗時: {end_time - start_time:.3f} 秒")
            
            # 測試2：逐日查詢數據
            total_query_time = 0
            for day in trade_days:
                start_time = time.time()
                cur.execute("SELECT * FROM stock_prices WHERE trade_datetime::date = %s ORDER BY trade_datetime;", (day,))
                day_data = cur.fetchall()
                end_time = time.time()
                
                query_time = end_time - start_time
                total_query_time += query_time
                
                # 過濾交易時段數據
                day_session_candles = [c for c in day_data if dt_time(8, 45) <= c['trade_datetime'].time() <= dt_time(13, 45)]
                
                print(f"  📊 {day}: 查詢 {len(day_data)} 筆數據, 交易時段 {len(day_session_candles)} 筆, 耗時: {query_time:.3f} 秒")
            
            print(f"\n📈 總查詢時間: {total_query_time:.3f} 秒")
            print(f"📈 平均每日查詢時間: {total_query_time / len(trade_days):.3f} 秒")
            
            # 測試3：一次性查詢所有數據
            start_time = time.time()
            cur.execute("""
                SELECT * FROM stock_prices 
                WHERE trade_datetime::date >= %s AND trade_datetime::date <= %s 
                ORDER BY trade_datetime
            """, ['2024-11-01', '2024-11-05'])
            all_data = cur.fetchall()
            end_time = time.time()
            
            print(f"\n🚀 一次性查詢所有數據: {len(all_data)} 筆, 耗時: {end_time - start_time:.3f} 秒")
            
            # 按日分組
            grouped_data = {}
            for row in all_data:
                day = row['trade_datetime'].date()
                if day not in grouped_data:
                    grouped_data[day] = []
                grouped_data[day].append(row)
            
            print(f"📊 分組後: {len(grouped_data)} 天")
            
    except Exception as e:
        print(f"❌ 測試失敗: {e}")

if __name__ == "__main__":
    test_db_performance()
