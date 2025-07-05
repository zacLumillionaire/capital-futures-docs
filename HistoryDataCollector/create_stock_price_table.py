#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
創建stock_price表
"""

import sys
import os

# 添加專案路徑
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

def create_stock_price_table():
    """創建stock_prices表"""
    try:
        # 導入必要的模組
        from shared import get_conn_cur_from_pool_b
        from app_setup import init_all_db_pools

        print("🔧 創建stock_prices表...")

        # 初始化連線池
        init_all_db_pools()
        print("✅ 連線池初始化成功")

        # 創建表
        with get_conn_cur_from_pool_b(as_dict=False) as (conn, cursor):

            # 檢查表是否已存在
            cursor.execute("""
                SELECT EXISTS (
                    SELECT FROM information_schema.tables
                    WHERE table_name = 'stock_prices'
                )
            """)

            exists = cursor.fetchone()[0]

            if exists:
                print("⚠️ stock_prices表已存在")
                
                # 檢查表結構
                cursor.execute("""
                    SELECT column_name, data_type
                    FROM information_schema.columns
                    WHERE table_name = 'stock_prices'
                    ORDER BY ordinal_position
                """)

                columns = cursor.fetchall()
                print("📋 現有表結構:")
                for col in columns:
                    print(f"  {col[0]}: {col[1]}")

            else:
                print("🔨 創建stock_prices表...")

                # 根據你提供的表結構創建表
                create_table_sql = """
                CREATE TABLE stock_prices (
                    trade_datetime timestamp without time zone,
                    open_price numeric(10,2),
                    high_price numeric(10,2),
                    low_price numeric(10,2),
                    close_price numeric(10,2),
                    price_change numeric(10,2),
                    percentage_change numeric(8,4),
                    volume bigint
                )
                """

                cursor.execute(create_table_sql)

                # 創建索引以提高查詢效能
                cursor.execute("""
                    CREATE INDEX IF NOT EXISTS idx_stock_prices_datetime
                    ON stock_prices (trade_datetime)
                """)

                conn.commit()
                print("✅ stock_prices表創建成功")

                # 檢查創建後的表結構
                cursor.execute("""
                    SELECT column_name, data_type
                    FROM information_schema.columns
                    WHERE table_name = 'stock_prices'
                    ORDER BY ordinal_position
                """)

                columns = cursor.fetchall()
                print("📋 新創建的表結構:")
                for col in columns:
                    print(f"  {col[0]}: {col[1]}")
                    
    except Exception as e:
        print(f"❌ 創建表時發生錯誤: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    create_stock_price_table()
