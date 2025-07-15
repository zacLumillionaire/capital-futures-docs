#!/usr/bin/env python3
"""
PostgreSQL 到 SQLite 數據導出工具
支持全量導出和增量更新
"""

import sqlite3
import sys
import os
from datetime import datetime, timedelta
from pathlib import Path

# 添加當前目錄到路徑
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

import shared
import app_setup

class SQLiteExporter:
    def __init__(self, sqlite_path="stock_data.sqlite"):
        self.sqlite_path = Path(__file__).parent / sqlite_path
        self.setup_sqlite()
    
    def setup_sqlite(self):
        """創建SQLite數據庫和表結構"""
        conn = sqlite3.connect(self.sqlite_path)
        cursor = conn.cursor()
        
        # 創建表結構（對應PostgreSQL）
        cursor.execute("""
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
        
        # 創建索引（對應PostgreSQL的函數索引）
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_date 
            ON stock_prices (date(trade_datetime))
        """)
        
        # 創建時間範圍索引
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_datetime 
            ON stock_prices (trade_datetime)
        """)
        
        conn.commit()
        conn.close()
        print(f"✅ SQLite數據庫已創建: {self.sqlite_path}")
    
    def get_sqlite_date_range(self):
        """獲取SQLite中現有數據的日期範圍"""
        conn = sqlite3.connect(self.sqlite_path)
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT 
                MIN(date(trade_datetime)) as min_date,
                MAX(date(trade_datetime)) as max_date,
                COUNT(*) as total_records
            FROM stock_prices
        """)
        
        result = cursor.fetchone()
        conn.close()
        
        if result and result[0]:
            return {
                'min_date': result[0],
                'max_date': result[1], 
                'total_records': result[2]
            }
        return None
    
    def export_full_data(self):
        """全量導出PostgreSQL數據到SQLite"""
        print("🚀 開始全量數據導出...")
        
        # 初始化PostgreSQL連接
        try:
            app_setup.init_all_db_pools()
            print("✅ PostgreSQL連接池初始化成功")
        except Exception as e:
            print(f"❌ PostgreSQL連接失敗: {e}")
            return False
        
        try:
            with shared.get_conn_cur_from_pool_b(as_dict=True) as (pg_conn, pg_cur):
                # 查詢所有數據
                print("📊 正在從PostgreSQL讀取數據...")
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
                """)
                
                rows = pg_cur.fetchall()
                print(f"📈 讀取到 {len(rows)} 筆記錄")
                
                # 寫入SQLite
                sqlite_conn = sqlite3.connect(self.sqlite_path)
                sqlite_cursor = sqlite_conn.cursor()
                
                # 清空現有數據
                sqlite_cursor.execute("DELETE FROM stock_prices")
                
                # 批量插入
                print("💾 正在寫入SQLite...")
                for row in rows:
                    sqlite_cursor.execute("""
                        INSERT INTO stock_prices (
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
                sqlite_conn.close()
                
                print(f"✅ 成功導出 {len(rows)} 筆記錄到SQLite")
                return True
                
        except Exception as e:
            print(f"❌ 導出過程發生錯誤: {e}")
            return False
    
    def export_incremental_data(self, start_date=None):
        """增量導出新數據"""
        print("🔄 開始增量數據更新...")
        
        # 獲取SQLite現有數據範圍
        sqlite_info = self.get_sqlite_date_range()
        if not sqlite_info:
            print("⚠️ SQLite無數據，執行全量導出")
            return self.export_full_data()
        
        # 確定更新起始日期
        if start_date:
            update_from = start_date
        else:
            # 從SQLite最後日期的下一天開始
            last_date = datetime.strptime(sqlite_info['max_date'], '%Y-%m-%d')
            update_from = (last_date + timedelta(days=1)).strftime('%Y-%m-%d')
        
        print(f"📅 從 {update_from} 開始更新數據")
        
        # 初始化PostgreSQL連接
        try:
            app_setup.init_all_db_pools()
        except Exception as e:
            print(f"❌ PostgreSQL連接失敗: {e}")
            return False
        
        try:
            with shared.get_conn_cur_from_pool_b(as_dict=True) as (pg_conn, pg_cur):
                # 查詢新數據
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
                    WHERE trade_datetime::date >= %s
                    ORDER BY trade_datetime
                """, (update_from,))
                
                new_rows = pg_cur.fetchall()
                
                if not new_rows:
                    print("✅ 沒有新數據需要更新")
                    return True
                
                print(f"📈 找到 {len(new_rows)} 筆新記錄")
                
                # 寫入SQLite
                sqlite_conn = sqlite3.connect(self.sqlite_path)
                sqlite_cursor = sqlite_conn.cursor()
                
                # 使用REPLACE INTO避免重複
                for row in new_rows:
                    sqlite_cursor.execute("""
                        REPLACE INTO stock_prices (
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
                sqlite_conn.close()
                
                print(f"✅ 成功更新 {len(new_rows)} 筆記錄")
                return True
                
        except Exception as e:
            print(f"❌ 增量更新失敗: {e}")
            return False
    
    def verify_data(self):
        """驗證SQLite數據完整性"""
        print("🔍 驗證數據完整性...")
        
        sqlite_info = self.get_sqlite_date_range()
        if not sqlite_info:
            print("❌ SQLite無數據")
            return False
        
        print(f"📊 SQLite數據統計:")
        print(f"  - 總記錄數: {sqlite_info['total_records']:,}")
        print(f"  - 日期範圍: {sqlite_info['min_date']} 至 {sqlite_info['max_date']}")
        
        # 檢查數據樣本
        conn = sqlite3.connect(self.sqlite_path)
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT trade_datetime, close_price 
            FROM stock_prices 
            ORDER BY trade_datetime 
            LIMIT 5
        """)
        
        sample_data = cursor.fetchall()
        print(f"📋 數據樣本:")
        for row in sample_data:
            print(f"  - {row[0]}: {row[1]}")
        
        conn.close()
        return True

def main():
    """主函數"""
    import argparse
    
    parser = argparse.ArgumentParser(description='PostgreSQL到SQLite數據導出工具')
    parser.add_argument('--mode', choices=['full', 'incremental'], default='full',
                       help='導出模式: full(全量) 或 incremental(增量)')
    parser.add_argument('--from-date', help='增量更新起始日期 (YYYY-MM-DD)')
    
    args = parser.parse_args()
    
    exporter = SQLiteExporter()
    
    if args.mode == 'full':
        success = exporter.export_full_data()
    else:
        success = exporter.export_incremental_data(args.from_date)
    
    if success:
        exporter.verify_data()
        print("🎉 數據導出完成！")
    else:
        print("❌ 數據導出失敗！")

if __name__ == "__main__":
    main()
