#!/usr/bin/env python3
import sqlite3
import os

def quick_diagnosis():
    print("🔍 快速診斷開始...")
    
    db_path = "multi_group_strategy.db"
    
    # 1. 檢查資料庫文件
    if not os.path.exists(db_path):
        print("❌ 資料庫文件不存在")
        return
    
    print(f"✅ 資料庫文件存在: {db_path}")
    
    try:
        with sqlite3.connect(db_path) as conn:
            cursor = conn.cursor()
            
            # 2. 檢查表結構
            print("\n📋 檢查表結構...")
            cursor.execute("SELECT sql FROM sqlite_master WHERE type='table' AND name='position_records'")
            result = cursor.fetchone()
            
            if result:
                table_sql = result[0]
                print("當前表定義:")
                print(table_sql)
                
                # 檢查約束
                if 'retry_count IS NULL OR' in table_sql:
                    print("✅ retry_count 約束已修復")
                else:
                    print("❌ retry_count 約束未修復")
                    
                if 'max_slippage_points IS NULL OR' in table_sql:
                    print("✅ max_slippage_points 約束已修復")
                else:
                    print("❌ max_slippage_points 約束未修復")
            else:
                print("❌ position_records 表不存在")
                return
            
            # 3. 測試 None 值插入
            print("\n🧪 測試 None 值插入...")
            try:
                cursor.execute("""
                    INSERT INTO position_records 
                    (group_id, lot_id, direction, retry_count, max_slippage_points, status)
                    VALUES (9999, 1, 'LONG', NULL, NULL, 'PENDING')
                """)
                test_id = cursor.lastrowid
                print("✅ None 值插入成功")
                
                # 清理
                cursor.execute("DELETE FROM position_records WHERE id = ?", (test_id,))
                conn.commit()
                
            except Exception as e:
                if 'not supported between instances' in str(e):
                    print(f"❌ None 值插入失敗: {e}")
                    print("🔧 約束修復未生效，需要重建表格")
                else:
                    print(f"✅ None 值處理正常 (其他約束錯誤: {e})")
            
            # 4. 檢查現有數據
            print("\n📊 檢查現有數據...")
            cursor.execute("""
                SELECT COUNT(*) FROM position_records 
                WHERE retry_count IS NULL OR max_slippage_points IS NULL
            """)
            null_count = cursor.fetchone()[0]
            print(f"包含 None 值的記錄數: {null_count}")
            
            # 5. 檢查最近記錄
            cursor.execute("""
                SELECT id, retry_count, max_slippage_points, status
                FROM position_records 
                ORDER BY id DESC LIMIT 5
            """)
            recent = cursor.fetchall()
            print("最近的記錄:")
            for record in recent:
                print(f"  ID {record[0]}: retry_count={record[1]}, max_slippage_points={record[2]}, status={record[3]}")
    
    except Exception as e:
        print(f"❌ 診斷過程出錯: {e}")

if __name__ == "__main__":
    quick_diagnosis()
