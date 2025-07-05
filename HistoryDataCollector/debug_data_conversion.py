#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
調試資料轉換問題
"""

import sqlite3
import sys
import os
from datetime import datetime
from decimal import Decimal

# 添加專案路徑
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

def debug_conversion():
    """調試資料轉換問題"""
    print("🔍 調試資料轉換問題...")
    
    # 連接SQLite
    conn = sqlite3.connect('data/history_data.db')
    conn.row_factory = sqlite3.Row
    
    # 查詢前5筆原始資料
    cursor = conn.execute("""
        SELECT * FROM kline_data 
        WHERE symbol = 'MTX00' AND kline_type = 'MINUTE'
        ORDER BY trade_date, trade_time
        LIMIT 5
    """)
    
    rows = cursor.fetchall()
    print(f"📊 查詢到 {len(rows)} 筆原始資料")
    
    for i, row in enumerate(rows, 1):
        print(f"\n--- 第{i}筆原始資料 ---")
        row_dict = dict(row)
        
        # 顯示所有欄位
        for key, value in row_dict.items():
            print(f"  {key}: {value} ({type(value).__name__})")
        
        # 手動執行轉換邏輯
        print(f"\n--- 轉換過程 ---")
        try:
            date_str = str(row_dict['trade_date']).strip()
            print(f"  date_str: '{date_str}'")
            
            # 解析日期時間
            trade_datetime = datetime.strptime(date_str, '%Y/%m/%d %H:%M')
            print(f"  trade_datetime: {trade_datetime}")
            
            # 檢查價格資料
            print(f"  原始價格:")
            print(f"    open_price: {row_dict['open_price']} ({type(row_dict['open_price']).__name__})")
            print(f"    high_price: {row_dict['high_price']} ({type(row_dict['high_price']).__name__})")
            print(f"    low_price: {row_dict['low_price']} ({type(row_dict['low_price']).__name__})")
            print(f"    close_price: {row_dict['close_price']} ({type(row_dict['close_price']).__name__})")
            print(f"    volume: {row_dict['volume']} ({type(row_dict['volume']).__name__})")
            
            # 轉換價格
            converted_open = Decimal(str(row_dict['open_price']))
            converted_high = Decimal(str(row_dict['high_price']))
            converted_low = Decimal(str(row_dict['low_price']))
            converted_close = Decimal(str(row_dict['close_price']))
            converted_volume = row_dict['volume'] or 0
            
            print(f"  轉換後價格:")
            print(f"    open_price: {converted_open}")
            print(f"    high_price: {converted_high}")
            print(f"    low_price: {converted_low}")
            print(f"    close_price: {converted_close}")
            print(f"    volume: {converted_volume}")
            
            # 檢查是否所有價格都相同
            if converted_open == converted_high == converted_low == converted_close:
                print(f"  ⚠️ 警告：所有價格都相同！")
            
            if converted_volume == 0:
                print(f"  ⚠️ 警告：成交量為0！")
                
        except Exception as e:
            print(f"  ❌ 轉換失敗: {e}")
    
    conn.close()

def check_sqlite_schema():
    """檢查SQLite表結構"""
    print(f"\n🔍 檢查SQLite表結構...")
    
    conn = sqlite3.connect('data/history_data.db')
    cursor = conn.cursor()
    
    # 檢查表結構
    cursor.execute("PRAGMA table_info(kline_data)")
    columns = cursor.fetchall()
    
    print("📋 kline_data表結構:")
    for col in columns:
        print(f"  {col[1]}: {col[2]} (nullable: {not col[3]})")
    
    conn.close()

if __name__ == "__main__":
    check_sqlite_schema()
    debug_conversion()
