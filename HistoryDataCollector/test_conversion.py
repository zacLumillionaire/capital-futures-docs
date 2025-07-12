#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
測試資料轉換過程
"""

import os
import sys
import sqlite3
from datetime import datetime
from decimal import Decimal

# 添加專案路徑
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from database.postgres_importer import PostgreSQLImporter

def test_data_conversion():
    """測試資料轉換過程"""
    try:
        print("🔍 測試資料轉換過程...")
        
        # 連接SQLite讀取資料
        sqlite_conn = sqlite3.connect('data/history_data.db')
        sqlite_conn.row_factory = sqlite3.Row
        
        # 查詢前5筆資料
        sqlite_cursor = sqlite_conn.execute("""
            SELECT * FROM kline_data 
            WHERE symbol = ? AND kline_type = ?
            ORDER BY trade_date, trade_time
            LIMIT 5
        """, ('MTX00', 'MINUTE'))
        
        rows = sqlite_cursor.fetchall()
        print(f"📊 查詢到 {len(rows)} 筆資料")
        
        # 創建轉換器
        importer = PostgreSQLImporter()
        
        # 測試轉換每筆資料
        for i, row in enumerate(rows, 1):
            print(f"\n--- 第{i}筆資料 ---")
            print(f"原始資料: {dict(row)}")
            
            # 嘗試轉換
            converted = importer.convert_kline_to_stock_price_format(dict(row))
            
            if converted:
                print(f"轉換成功: {converted}")
            else:
                print("❌ 轉換失敗")
        
        sqlite_conn.close()
        
    except Exception as e:
        print(f"❌ 測試過程中發生錯誤: {e}")
        import traceback
        traceback.print_exc()

def test_date_parsing():
    """測試日期解析"""
    print("\n🕐 測試日期解析...")
    
    # 測試不同的日期格式
    test_dates = [
        "2025/04/08 15:01",
        "2025/4/8 15:01", 
        "2025/04/08",
        "2025-04-08 15:01",
        "None"
    ]
    
    for date_str in test_dates:
        print(f"\n測試日期: '{date_str}'")
        try:
            # 嘗試解析完整的日期時間格式
            trade_datetime = datetime.strptime(date_str, '%Y/%m/%d %H:%M')
            print(f"  ✅ 解析成功: {trade_datetime}")
        except ValueError:
            try:
                # 嘗試只有日期的格式
                trade_datetime = datetime.strptime(date_str, '%Y/%m/%d')
                trade_datetime = trade_datetime.replace(hour=13, minute=45, second=0)
                print(f"  ✅ 日期格式解析成功: {trade_datetime}")
            except ValueError:
                print(f"  ❌ 解析失敗")

if __name__ == "__main__":
    test_date_parsing()
    test_data_conversion()
