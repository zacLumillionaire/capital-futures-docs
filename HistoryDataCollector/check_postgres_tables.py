#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
檢查PostgreSQL中的表
"""

import sys
import os

# 添加專案路徑
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

def check_postgres_tables():
    """檢查PostgreSQL中的表"""
    try:
        # 導入必要的模組
        from shared import get_conn_cur_from_pool_b
        from app_setup import init_all_db_pools
        
        print("🔍 檢查PostgreSQL中的表...")
        
        # 初始化連線池
        init_all_db_pools()
        print("✅ 連線池初始化成功")
        
        # 檢查PostgreSQL中的表
        with get_conn_cur_from_pool_b(as_dict=True) as (conn, cursor):
            # 查詢所有表
            cursor.execute("""
                SELECT table_name 
                FROM information_schema.tables 
                WHERE table_schema = 'public' 
                ORDER BY table_name
            """)
            
            tables = cursor.fetchall()
            print(f"\n📊 PostgreSQL中的表 (共{len(tables)}個):")
            for table in tables:
                print(f"  - {table['table_name']}")
                
            # 檢查是否有包含price的表
            cursor.execute("""
                SELECT table_name 
                FROM information_schema.tables 
                WHERE table_schema = 'public' 
                AND table_name LIKE '%price%'
            """)
            
            price_tables = cursor.fetchall()
            print(f"\n💰 包含'price'的表 (共{len(price_tables)}個):")
            for table in price_tables:
                print(f"  - {table['table_name']}")
                
            # 檢查是否有包含stock的表
            cursor.execute("""
                SELECT table_name 
                FROM information_schema.tables 
                WHERE table_schema = 'public' 
                AND table_name LIKE '%stock%'
            """)
            
            stock_tables = cursor.fetchall()
            print(f"\n📈 包含'stock'的表 (共{len(stock_tables)}個):")
            for table in stock_tables:
                print(f"  - {table['table_name']}")
                
                # 如果找到stock相關的表，檢查其結構
                cursor.execute(f"""
                    SELECT column_name, data_type 
                    FROM information_schema.columns 
                    WHERE table_name = '{table['table_name']}'
                    ORDER BY ordinal_position
                """)
                
                columns = cursor.fetchall()
                print(f"    表結構:")
                for col in columns:
                    print(f"      {col['column_name']}: {col['data_type']}")
                    
    except Exception as e:
        print(f"❌ 檢查過程中發生錯誤: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    check_postgres_tables()
