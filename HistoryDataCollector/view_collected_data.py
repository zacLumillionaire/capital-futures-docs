#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
查看收集到的資料工具
用於檢視SQLite中尚未匯入PostgreSQL的資料
"""

import sqlite3
import sys
import os
from datetime import datetime

def view_data_summary():
    """查看資料摘要"""
    db_path = "data/history_data.db"
    
    if not os.path.exists(db_path):
        print(f"❌ 找不到資料庫檔案: {db_path}")
        return
    
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        print("📊 收集資料摘要")
        print("=" * 50)
        
        # 檢查K線資料
        cursor.execute("""
            SELECT 
                symbol,
                kline_type,
                COUNT(*) as count,
                MIN(trade_date) as start_date,
                MAX(trade_date) as end_date
            FROM kline_data 
            GROUP BY symbol, kline_type
            ORDER BY symbol, kline_type
        """)
        
        kline_results = cursor.fetchall()
        if kline_results:
            print("📈 K線資料:")
            for row in kline_results:
                symbol, kline_type, count, start_date, end_date = row
                print(f"   {symbol} {kline_type}: {count:,} 筆 ({start_date} ~ {end_date})")
        else:
            print("📈 K線資料: 無")
        
        # 檢查逐筆資料
        cursor.execute("SELECT COUNT(*) FROM tick_data")
        tick_count = cursor.fetchone()[0]
        print(f"📊 逐筆資料: {tick_count:,} 筆")
        
        # 檢查五檔資料
        cursor.execute("SELECT COUNT(*) FROM best5_data")
        best5_count = cursor.fetchone()[0]
        print(f"📋 五檔資料: {best5_count:,} 筆")
        
        # 總計
        total = sum([row[2] for row in kline_results]) + tick_count + best5_count
        print(f"📊 總計: {total:,} 筆")
        
        conn.close()
        
    except Exception as e:
        print(f"❌ 查看資料時發生錯誤: {e}")

def view_recent_kline_data(limit=20):
    """查看最新的K線資料"""
    db_path = "data/history_data.db"
    
    if not os.path.exists(db_path):
        print(f"❌ 找不到資料庫檔案: {db_path}")
        return
    
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        print(f"\n📈 最新 {limit} 筆K線資料")
        print("=" * 80)
        
        cursor.execute("""
            SELECT 
                symbol,
                kline_type,
                trade_date,
                trade_time,
                open_price,
                high_price,
                low_price,
                close_price,
                volume
            FROM kline_data 
            ORDER BY trade_date DESC, trade_time DESC 
            LIMIT ?
        """, (limit,))
        
        results = cursor.fetchall()
        if results:
            print(f"{'商品':<8} {'類型':<8} {'日期時間':<16} {'開盤':<8} {'最高':<8} {'最低':<8} {'收盤':<8} {'量':<8}")
            print("-" * 80)
            
            for row in results:
                symbol, kline_type, trade_date, trade_time, open_p, high_p, low_p, close_p, volume = row
                time_str = trade_time if trade_time else ""
                print(f"{symbol:<8} {kline_type:<8} {trade_date:<16} {open_p:<8.0f} {high_p:<8.0f} {low_p:<8.0f} {close_p:<8.0f} {volume or 0:<8}")
        else:
            print("沒有K線資料")
        
        conn.close()
        
    except Exception as e:
        print(f"❌ 查看K線資料時發生錯誤: {e}")

def view_specific_date_data(date_str):
    """查看特定日期的資料"""
    db_path = "data/history_data.db"
    
    if not os.path.exists(db_path):
        print(f"❌ 找不到資料庫檔案: {db_path}")
        return
    
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        print(f"\n📅 {date_str} 的K線資料")
        print("=" * 80)
        
        # 轉換日期格式 (YYYYMMDD -> YYYY/MM/DD)
        if len(date_str) == 8:
            formatted_date = f"{date_str[:4]}/{date_str[4:6]}/{date_str[6:8]}"
        else:
            formatted_date = date_str
        
        cursor.execute("""
            SELECT 
                symbol,
                kline_type,
                trade_date,
                COUNT(*) as count,
                MIN(open_price) as min_open,
                MAX(high_price) as max_high,
                MIN(low_price) as min_low,
                MAX(close_price) as max_close,
                SUM(volume) as total_volume
            FROM kline_data 
            WHERE trade_date LIKE ?
            GROUP BY symbol, kline_type, trade_date
            ORDER BY symbol, kline_type
        """, (f"%{formatted_date}%",))
        
        results = cursor.fetchall()
        if results:
            print(f"{'商品':<8} {'類型':<8} {'日期':<12} {'筆數':<6} {'最低開':<8} {'最高高':<8} {'最低低':<8} {'最高收':<8} {'總量':<10}")
            print("-" * 80)
            
            for row in results:
                symbol, kline_type, trade_date, count, min_open, max_high, min_low, max_close, total_vol = row
                print(f"{symbol:<8} {kline_type:<8} {trade_date:<12} {count:<6} {min_open:<8.0f} {max_high:<8.0f} {min_low:<8.0f} {max_close:<8.0f} {total_vol or 0:<10}")
        else:
            print(f"沒有找到 {date_str} 的資料")
        
        conn.close()
        
    except Exception as e:
        print(f"❌ 查看特定日期資料時發生錯誤: {e}")

def view_collection_log():
    """查看收集記錄"""
    db_path = "data/history_data.db"
    
    if not os.path.exists(db_path):
        print(f"❌ 找不到資料庫檔案: {db_path}")
        return
    
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        print(f"\n📋 最近收集記錄")
        print("=" * 80)
        
        cursor.execute("""
            SELECT 
                collection_type,
                symbol,
                start_time,
                end_time,
                records_count,
                status,
                parameters
            FROM collection_log 
            ORDER BY start_time DESC 
            LIMIT 10
        """)
        
        results = cursor.fetchall()
        if results:
            print(f"{'類型':<8} {'商品':<8} {'開始時間':<20} {'結束時間':<20} {'筆數':<8} {'狀態':<10}")
            print("-" * 80)
            
            for row in results:
                coll_type, symbol, start_time, end_time, count, status, params = row
                end_time_str = end_time[:19] if end_time else "進行中"
                print(f"{coll_type:<8} {symbol:<8} {start_time[:19]:<20} {end_time_str:<20} {count or 0:<8} {status:<10}")
        else:
            print("沒有收集記錄")
        
        conn.close()
        
    except Exception as e:
        print(f"❌ 查看收集記錄時發生錯誤: {e}")

def main():
    """主選單"""
    print("🔍 收集資料查看工具")
    print("=" * 30)
    print("1. 查看資料摘要")
    print("2. 查看最新K線資料")
    print("3. 查看特定日期資料")
    print("4. 查看收集記錄")
    print("5. 退出")
    print("=" * 30)
    
    while True:
        choice = input("\n請選擇 (1-5): ")
        
        if choice == '1':
            view_data_summary()
        elif choice == '2':
            try:
                limit = int(input("顯示筆數 (預設20): ") or "20")
                view_recent_kline_data(limit)
            except ValueError:
                view_recent_kline_data(20)
        elif choice == '3':
            date_str = input("輸入日期 (YYYYMMDD，如20250705): ")
            if date_str:
                view_specific_date_data(date_str)
        elif choice == '4':
            view_collection_log()
        elif choice == '5':
            print("👋 再見！")
            break
        else:
            print("❌ 無效選擇")

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n❌ 使用者中斷")
    except Exception as e:
        print(f"\n❌ 發生錯誤: {e}")
