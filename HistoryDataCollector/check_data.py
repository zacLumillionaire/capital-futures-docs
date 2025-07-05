#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
檢查收集到的資料
"""

import os
import sys
import sqlite3
from datetime import datetime

# 添加專案路徑
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from history_config import DATABASE_PATH
from database.db_manager import DatabaseManager

def check_database_data():
    """檢查資料庫中的資料"""
    try:
        print("🔍 檢查資料庫中的資料...")
        
        # 直接連接資料庫
        conn = sqlite3.connect(DATABASE_PATH)
        conn.row_factory = sqlite3.Row
        
        # 檢查K線資料
        print("\n📊 K線資料統計:")
        cursor = conn.execute("""
            SELECT 
                symbol,
                kline_type,
                COUNT(*) as count,
                MIN(trade_date) as min_date,
                MAX(trade_date) as max_date,
                MIN(trade_time) as min_time,
                MAX(trade_time) as max_time
            FROM kline_data 
            GROUP BY symbol, kline_type
            ORDER BY symbol, kline_type
        """)
        
        for row in cursor.fetchall():
            print(f"  {row['symbol']} {row['kline_type']}: {row['count']} 筆")
            print(f"    日期範圍: {row['min_date']} ~ {row['max_date']}")
            if row['min_time'] and row['max_time']:
                print(f"    時間範圍: {row['min_time']} ~ {row['max_time']}")
        
        # 顯示最新的10筆K線資料
        print("\n📈 最新10筆K線資料:")
        cursor = conn.execute("""
            SELECT 
                symbol, kline_type, trade_date, trade_time,
                open_price, high_price, low_price, close_price, volume,
                created_at
            FROM kline_data 
            ORDER BY created_at DESC 
            LIMIT 10
        """)
        
        for row in cursor.fetchall():
            time_str = f" {row['trade_time']}" if row['trade_time'] else ""
            print(f"  {row['symbol']} {row['trade_date']}{time_str}")
            print(f"    開:{row['open_price']} 高:{row['high_price']} 低:{row['low_price']} 收:{row['close_price']} 量:{row['volume']}")
        
        # 檢查逐筆資料
        print("\n📊 逐筆資料統計:")
        cursor = conn.execute("""
            SELECT 
                symbol,
                COUNT(*) as count,
                MIN(trade_date) as min_date,
                MAX(trade_date) as max_date
            FROM tick_data 
            GROUP BY symbol
            ORDER BY symbol
        """)
        
        tick_rows = cursor.fetchall()
        if tick_rows:
            for row in tick_rows:
                print(f"  {row['symbol']}: {row['count']} 筆 ({row['min_date']} ~ {row['max_date']})")
        else:
            print("  無逐筆資料")
        
        # 檢查五檔資料
        print("\n📊 五檔資料統計:")
        cursor = conn.execute("""
            SELECT 
                symbol,
                COUNT(*) as count,
                MIN(trade_date) as min_date,
                MAX(trade_date) as max_date
            FROM best5_data 
            GROUP BY symbol
            ORDER BY symbol
        """)
        
        best5_rows = cursor.fetchall()
        if best5_rows:
            for row in best5_rows:
                print(f"  {row['symbol']}: {row['count']} 筆 ({row['min_date']} ~ {row['max_date']})")
        else:
            print("  無五檔資料")
        
        conn.close()
        
    except Exception as e:
        print(f"❌ 檢查資料時發生錯誤: {e}")

def export_kline_data_to_csv():
    """匯出K線資料到CSV檔案"""
    try:
        print("\n💾 匯出K線資料到CSV檔案...")
        
        conn = sqlite3.connect(DATABASE_PATH)
        conn.row_factory = sqlite3.Row
        
        # 查詢所有K線資料
        cursor = conn.execute("""
            SELECT 
                symbol, kline_type, trade_date, trade_time,
                open_price, high_price, low_price, close_price, volume,
                created_at
            FROM kline_data 
            ORDER BY symbol, trade_date, trade_time
        """)
        
        rows = cursor.fetchall()
        if not rows:
            print("  ❌ 沒有K線資料可匯出")
            return
        
        # 建立CSV檔案
        csv_filename = f"kline_data_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
        csv_path = os.path.join(os.path.dirname(__file__), csv_filename)
        
        with open(csv_path, 'w', encoding='utf-8-sig') as f:
            # 寫入標題
            f.write("商品代碼,K線類型,交易日期,交易時間,開盤價,最高價,最低價,收盤價,成交量,建立時間\n")
            
            # 寫入資料
            for row in rows:
                f.write(f"{row['symbol']},{row['kline_type']},{row['trade_date']},{row['trade_time'] or ''},"
                       f"{row['open_price']},{row['high_price']},{row['low_price']},{row['close_price']},"
                       f"{row['volume'] or ''},{row['created_at']}\n")
        
        print(f"  ✅ 已匯出 {len(rows)} 筆資料到: {csv_path}")
        
        conn.close()
        
    except Exception as e:
        print(f"❌ 匯出資料時發生錯誤: {e}")

def show_sample_data():
    """顯示樣本資料"""
    try:
        print("\n📋 顯示樣本資料 (前20筆):")
        
        conn = sqlite3.connect(DATABASE_PATH)
        conn.row_factory = sqlite3.Row
        
        cursor = conn.execute("""
            SELECT 
                symbol, kline_type, trade_date, trade_time,
                open_price, high_price, low_price, close_price, volume
            FROM kline_data 
            ORDER BY trade_date, trade_time
            LIMIT 20
        """)
        
        print("  商品    日期      時間    開盤    最高    最低    收盤    成交量")
        print("  " + "="*70)
        
        for row in cursor.fetchall():
            time_str = row['trade_time'] or "      "
            print(f"  {row['symbol']:<6} {row['trade_date']} {time_str} "
                  f"{row['open_price']:>7.2f} {row['high_price']:>7.2f} {row['low_price']:>7.2f} "
                  f"{row['close_price']:>7.2f} {row['volume'] or 0:>8}")
        
        conn.close()
        
    except Exception as e:
        print(f"❌ 顯示樣本資料時發生錯誤: {e}")

if __name__ == "__main__":
    print("🔍 群益期貨歷史資料檢查工具")
    print("="*50)
    
    # 檢查資料庫是否存在
    if not os.path.exists(DATABASE_PATH):
        print(f"❌ 資料庫檔案不存在: {DATABASE_PATH}")
        sys.exit(1)
    
    # 執行檢查
    check_database_data()
    show_sample_data()
    export_kline_data_to_csv()
    
    print("\n✅ 檢查完成！")
