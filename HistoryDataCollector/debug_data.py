#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import sqlite3
import sys
import os

def debug_sqlite_data():
    """檢查SQLite中的實際資料格式"""
    # 檢查兩個可能的資料庫檔案
    db_paths = ["data/collector.db", "data/history_data.db"]

    for db_path in db_paths:
        print(f"\n🔍 檢查資料庫: {db_path}")
        if not os.path.exists(db_path):
            print(f"❌ 找不到資料庫檔案: {db_path}")
            continue

        check_database(db_path)

def check_database(db_path):
    
    """檢查單個資料庫檔案"""
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # 檢查所有表
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
        tables = cursor.fetchall()
        print("📊 資料庫中的表:")
        for table in tables:
            print(f"   {table[0]}")

        if not tables:
            print("   沒有找到任何表")
            return

        # 尋找kline_data表
        kline_table = None
        for table in tables:
            if table[0] == 'kline_data':
                kline_table = table[0]
                break

        if not kline_table:
            print("   沒有找到kline_data表")
            return

        print(f"\n使用表: {kline_table}")

        # 檢查表結構
        cursor.execute(f"PRAGMA table_info({kline_table})")
        columns = cursor.fetchall()
        print(f"📊 {kline_table}表結構:")
        for col in columns:
            print(f"   {col[1]} ({col[2]})")

        print("\n" + "="*50)

        # 檢查前5筆資料
        cursor.execute(f"""
            SELECT trade_date, trade_time, open_price, high_price, low_price, close_price, volume
            FROM {kline_table}
            ORDER BY trade_date, trade_time
            LIMIT 5
        """)
        
        rows = cursor.fetchall()
        print("📈 前5筆K線資料:")
        for i, row in enumerate(rows, 1):
            print(f"   {i}. 日期: {row[0]}, 時間: {row[1]}, OHLC: {row[2]}/{row[3]}/{row[4]}/{row[5]}, 量: {row[6]}")
        
        print("\n" + "="*50)
        
        # 檢查時間格式的變化
        cursor.execute(f"""
            SELECT DISTINCT trade_time
            FROM {kline_table}
            ORDER BY trade_time
            LIMIT 10
        """)
        
        times = cursor.fetchall()
        print("🕐 時間格式樣本:")
        for time_val in times:
            print(f"   '{time_val[0]}'")
        
        conn.close()
        
    except Exception as e:
        print(f"❌ 檢查資料時發生錯誤: {e}")

if __name__ == "__main__":
    debug_sqlite_data()
