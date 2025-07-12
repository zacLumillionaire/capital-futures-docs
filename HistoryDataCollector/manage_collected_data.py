#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
收集資料管理工具
支援查看、刪除、清空SQLite中的收集資料
適用於重新收集前的資料清理
"""

import sqlite3
import sys
import os
from datetime import datetime

def get_db_connection():
    """取得資料庫連接"""
    db_path = "data/history_data.db"
    
    if not os.path.exists(db_path):
        print(f"❌ 找不到資料庫檔案: {db_path}")
        return None
    
    return sqlite3.connect(db_path)

def show_data_summary():
    """顯示資料摘要"""
    conn = get_db_connection()
    if not conn:
        return
    
    try:
        cursor = conn.cursor()
        
        print("\n📊 當前資料摘要")
        print("=" * 60)
        
        # K線資料統計
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
        
        # 其他資料統計
        cursor.execute("SELECT COUNT(*) FROM tick_data")
        tick_count = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM best5_data")
        best5_count = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM collection_log")
        log_count = cursor.fetchone()[0]
        
        print(f"📊 逐筆資料: {tick_count:,} 筆")
        print(f"📋 五檔資料: {best5_count:,} 筆")
        print(f"📝 收集記錄: {log_count:,} 筆")
        
        total = sum([row[2] for row in kline_results]) + tick_count + best5_count
        print(f"📊 總計: {total:,} 筆")
        
        conn.close()
        return kline_results, tick_count, best5_count, log_count
        
    except Exception as e:
        print(f"❌ 查看資料時發生錯誤: {e}")
        conn.close()
        return None, 0, 0, 0

def delete_by_symbol_and_type():
    """刪除指定商品和K線類型的資料"""
    conn = get_db_connection()
    if not conn:
        return
    
    try:
        # 顯示可用的商品和類型
        cursor = conn.cursor()
        cursor.execute("""
            SELECT DISTINCT symbol, kline_type, COUNT(*) as count
            FROM kline_data 
            GROUP BY symbol, kline_type
            ORDER BY symbol, kline_type
        """)
        
        available_data = cursor.fetchall()
        if not available_data:
            print("❌ 沒有K線資料可刪除")
            conn.close()
            return
        
        print("\n📋 可刪除的資料:")
        for i, (symbol, kline_type, count) in enumerate(available_data, 1):
            print(f"   {i}. {symbol} {kline_type}: {count:,} 筆")
        
        # 選擇要刪除的資料
        try:
            choice = int(input(f"\n選擇要刪除的資料 (1-{len(available_data)}): ")) - 1
            if choice < 0 or choice >= len(available_data):
                print("❌ 無效選擇")
                conn.close()
                return
        except ValueError:
            print("❌ 請輸入數字")
            conn.close()
            return
        
        symbol, kline_type, count = available_data[choice]
        
        # 確認刪除
        confirm = input(f"\n⚠️  確定要刪除 {symbol} {kline_type} 的 {count:,} 筆資料嗎？(y/N): ")
        if confirm.lower() != 'y':
            print("❌ 已取消")
            conn.close()
            return
        
        # 執行刪除
        cursor.execute("""
            DELETE FROM kline_data 
            WHERE symbol = ? AND kline_type = ?
        """, (symbol, kline_type))
        
        deleted_count = cursor.rowcount
        conn.commit()
        
        print(f"✅ 已刪除 {symbol} {kline_type} 的 {deleted_count:,} 筆資料")
        
        conn.close()
        
    except Exception as e:
        print(f"❌ 刪除資料時發生錯誤: {e}")
        conn.close()

def delete_by_date_range():
    """刪除指定日期範圍的資料"""
    conn = get_db_connection()
    if not conn:
        return
    
    try:
        cursor = conn.cursor()
        
        # 顯示日期範圍
        cursor.execute("""
            SELECT 
                MIN(trade_date) as min_date,
                MAX(trade_date) as max_date,
                COUNT(*) as total_count
            FROM kline_data
        """)
        
        result = cursor.fetchone()
        if not result or result[2] == 0:
            print("❌ 沒有K線資料可刪除")
            conn.close()
            return
        
        min_date, max_date, total_count = result
        print(f"\n📅 現有資料日期範圍: {min_date} ~ {max_date} (共 {total_count:,} 筆)")
        
        # 輸入要刪除的日期範圍
        start_date = input("輸入開始日期 (YYYY/MM/DD 或 YYYYMMDD): ").strip()
        end_date = input("輸入結束日期 (YYYY/MM/DD 或 YYYYMMDD): ").strip()
        
        if not start_date or not end_date:
            print("❌ 日期不能為空")
            conn.close()
            return
        
        # 轉換日期格式
        if len(start_date) == 8:  # YYYYMMDD
            start_date = f"{start_date[:4]}/{start_date[4:6]}/{start_date[6:8]}"
        if len(end_date) == 8:  # YYYYMMDD
            end_date = f"{end_date[:4]}/{end_date[4:6]}/{end_date[6:8]}"
        
        # 檢查要刪除的資料
        cursor.execute("""
            SELECT COUNT(*) FROM kline_data 
            WHERE trade_date >= ? AND trade_date <= ?
        """, (start_date, end_date))
        
        delete_count = cursor.fetchone()[0]
        if delete_count == 0:
            print(f"❌ 在 {start_date} ~ {end_date} 範圍內沒有找到資料")
            conn.close()
            return
        
        # 確認刪除
        confirm = input(f"\n⚠️  確定要刪除 {start_date} ~ {end_date} 的 {delete_count:,} 筆資料嗎？(y/N): ")
        if confirm.lower() != 'y':
            print("❌ 已取消")
            conn.close()
            return
        
        # 執行刪除
        cursor.execute("""
            DELETE FROM kline_data 
            WHERE trade_date >= ? AND trade_date <= ?
        """, (start_date, end_date))
        
        deleted_count = cursor.rowcount
        conn.commit()
        
        print(f"✅ 已刪除 {start_date} ~ {end_date} 的 {deleted_count:,} 筆資料")
        
        conn.close()
        
    except Exception as e:
        print(f"❌ 刪除資料時發生錯誤: {e}")
        conn.close()

def clear_all_data():
    """清空所有資料"""
    conn = get_db_connection()
    if not conn:
        return
    
    try:
        cursor = conn.cursor()
        
        # 統計現有資料
        cursor.execute("SELECT COUNT(*) FROM kline_data")
        kline_count = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM tick_data")
        tick_count = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM best5_data")
        best5_count = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM collection_log")
        log_count = cursor.fetchone()[0]
        
        total_count = kline_count + tick_count + best5_count + log_count
        
        if total_count == 0:
            print("❌ 資料庫已經是空的")
            conn.close()
            return
        
        print(f"\n⚠️  即將清空所有資料:")
        print(f"   📈 K線資料: {kline_count:,} 筆")
        print(f"   📊 逐筆資料: {tick_count:,} 筆")
        print(f"   📋 五檔資料: {best5_count:,} 筆")
        print(f"   📝 收集記錄: {log_count:,} 筆")
        print(f"   📊 總計: {total_count:,} 筆")
        
        # 雙重確認
        confirm1 = input("\n⚠️  確定要清空所有資料嗎？這個操作無法復原！(y/N): ")
        if confirm1.lower() != 'y':
            print("❌ 已取消")
            conn.close()
            return
        
        confirm2 = input("⚠️  再次確認：真的要清空所有資料嗎？(y/N): ")
        if confirm2.lower() != 'y':
            print("❌ 已取消")
            conn.close()
            return
        
        # 執行清空
        cursor.execute("DELETE FROM kline_data")
        cursor.execute("DELETE FROM tick_data")
        cursor.execute("DELETE FROM best5_data")
        cursor.execute("DELETE FROM collection_log")
        
        # 重置自增ID
        cursor.execute("DELETE FROM sqlite_sequence")
        
        conn.commit()
        
        print("✅ 所有資料已清空")
        
        conn.close()
        
    except Exception as e:
        print(f"❌ 清空資料時發生錯誤: {e}")
        conn.close()

def backup_database():
    """備份資料庫"""
    try:
        import shutil
        
        source = "data/history_data.db"
        if not os.path.exists(source):
            print("❌ 找不到資料庫檔案")
            return
        
        # 建立備份檔名
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_name = f"data/history_data_backup_{timestamp}.db"
        
        # 執行備份
        shutil.copy2(source, backup_name)
        
        # 檢查檔案大小
        source_size = os.path.getsize(source)
        backup_size = os.path.getsize(backup_name)
        
        print(f"✅ 資料庫已備份到: {backup_name}")
        print(f"📊 檔案大小: {source_size:,} bytes → {backup_size:,} bytes")
        
    except Exception as e:
        print(f"❌ 備份資料庫時發生錯誤: {e}")

def main():
    """主選單"""
    print("🗂️  收集資料管理工具")
    print("=" * 40)
    print("1. 查看資料摘要")
    print("2. 刪除指定商品/類型資料")
    print("3. 刪除指定日期範圍資料")
    print("4. 清空所有資料")
    print("5. 備份資料庫")
    print("6. 退出")
    print("=" * 40)
    
    while True:
        choice = input("\n請選擇 (1-6): ")
        
        if choice == '1':
            show_data_summary()
        elif choice == '2':
            delete_by_symbol_and_type()
        elif choice == '3':
            delete_by_date_range()
        elif choice == '4':
            clear_all_data()
        elif choice == '5':
            backup_database()
        elif choice == '6':
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
