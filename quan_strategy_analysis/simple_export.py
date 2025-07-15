#!/usr/bin/env python3
"""
簡化的數據導出腳本 - 用於診斷問題
"""

import sqlite3
import sys
import os
from pathlib import Path

# 添加當前目錄到路徑
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

import shared
import app_setup

def simple_export():
    """簡化的數據導出"""
    print("🚀 開始簡化數據導出...")
    
    # 初始化PostgreSQL連接
    try:
        app_setup.init_all_db_pools()
        print("✅ PostgreSQL連接池初始化成功")
    except Exception as e:
        print(f"❌ PostgreSQL連接失敗: {e}")
        return False
    
    # 創建SQLite數據庫
    sqlite_path = Path(__file__).parent / "stock_data.sqlite"
    
    try:
        # 先測試PostgreSQL查詢
        print("📊 測試PostgreSQL查詢...")
        with shared.get_conn_cur_from_pool_b(as_dict=True) as (pg_conn, pg_cur):
            # 先查詢記錄總數
            pg_cur.execute("SELECT COUNT(*) as total FROM stock_prices")
            total_count = pg_cur.fetchone()['total']
            print(f"📈 PostgreSQL總記錄數: {total_count:,}")
            
            # 查詢日期範圍
            pg_cur.execute("""
                SELECT 
                    MIN(trade_datetime::date) as min_date,
                    MAX(trade_datetime::date) as max_date
                FROM stock_prices
            """)
            date_range = pg_cur.fetchone()
            print(f"📅 日期範圍: {date_range['min_date']} 至 {date_range['max_date']}")
            
            # 分批查詢數據
            print("📊 開始分批讀取數據...")
            batch_size = 5000
            offset = 0
            
            # 創建SQLite數據庫
            sqlite_conn = sqlite3.connect(sqlite_path)
            sqlite_cursor = sqlite_conn.cursor()
            
            # 創建表結構
            sqlite_cursor.execute("""
                CREATE TABLE IF NOT EXISTS stock_prices (
                    trade_datetime TEXT PRIMARY KEY,
                    open_price INTEGER,
                    high_price INTEGER,
                    low_price INTEGER,
                    close_price INTEGER,
                    price_change INTEGER,
                    percentage_change REAL,
                    volume INTEGER
                )
            """)
            
            # 創建索引
            sqlite_cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_date 
                ON stock_prices (date(trade_datetime))
            """)
            
            total_exported = 0
            
            while True:
                # 分批查詢
                pg_cur.execute("""
                    SELECT 
                        trade_datetime,
                        open_price,
                        high_price,
                        low_price,
                        close_price,
                        price_change,
                        percentage_change,
                        volume
                    FROM stock_prices 
                    ORDER BY trade_datetime
                    LIMIT %s OFFSET %s
                """, (batch_size, offset))
                
                batch_rows = pg_cur.fetchall()
                
                if not batch_rows:
                    break
                
                print(f"  📦 處理批次 {offset//batch_size + 1}: {len(batch_rows)} 筆記錄")
                
                # 批量插入SQLite
                for row in batch_rows:
                    sqlite_cursor.execute("""
                        INSERT OR REPLACE INTO stock_prices (
                            trade_datetime, open_price, high_price, low_price,
                            close_price, price_change, percentage_change, volume
                        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                    """, (
                        row['trade_datetime'].isoformat(),
                        row['open_price'],
                        row['high_price'],
                        row['low_price'],
                        row['close_price'],
                        row['price_change'],
                        float(row['percentage_change']) if row['percentage_change'] else None,
                        row['volume']
                    ))
                
                sqlite_conn.commit()
                total_exported += len(batch_rows)
                
                print(f"  ✅ 已導出 {total_exported:,} / {total_count:,} 筆記錄 ({total_exported/total_count*100:.1f}%)")
                
                offset += batch_size
            
            sqlite_conn.close()
            
            print(f"🎉 數據導出完成！總共導出 {total_exported:,} 筆記錄")
            
            # 驗證SQLite數據
            print("🔍 驗證SQLite數據...")
            sqlite_conn = sqlite3.connect(sqlite_path)
            sqlite_cursor = sqlite_conn.cursor()
            
            sqlite_cursor.execute("SELECT COUNT(*) FROM stock_prices")
            sqlite_count = sqlite_cursor.fetchone()[0]
            
            sqlite_cursor.execute("""
                SELECT 
                    MIN(date(trade_datetime)) as min_date,
                    MAX(date(trade_datetime)) as max_date
                FROM stock_prices
            """)
            sqlite_range = sqlite_cursor.fetchone()
            
            sqlite_conn.close()
            
            print(f"📊 SQLite驗證結果:")
            print(f"  - 記錄數: {sqlite_count:,}")
            print(f"  - 日期範圍: {sqlite_range[0]} 至 {sqlite_range[1]}")
            
            if sqlite_count == total_count:
                print("✅ 數據完整性驗證通過！")
                return True
            else:
                print(f"❌ 數據不完整！PostgreSQL: {total_count}, SQLite: {sqlite_count}")
                return False
                
    except Exception as e:
        print(f"❌ 導出過程發生錯誤: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    simple_export()
