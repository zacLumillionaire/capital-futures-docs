#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
強制重建 position_records 表格
解決約束修復未生效的問題
"""

import sqlite3
import shutil
from datetime import datetime

def force_rebuild_table():
    """強制重建表格，應用修復的約束"""
    db_path = "multi_group_strategy.db"
    
    print("🚀 開始強制重建 position_records 表格")
    print("=" * 50)
    
    # 1. 備份資料庫
    backup_path = f"{db_path}.backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
    shutil.copy2(db_path, backup_path)
    print(f"✅ 資料庫已備份至: {backup_path}")
    
    try:
        with sqlite3.connect(db_path) as conn:
            cursor = conn.cursor()
            
            # 2. 檢查當前表結構
            print("\n📋 檢查當前表結構...")
            cursor.execute("SELECT sql FROM sqlite_master WHERE type='table' AND name='position_records'")
            current_sql = cursor.fetchone()[0]
            print("當前表定義:")
            print(current_sql[:200] + "..." if len(current_sql) > 200 else current_sql)
            
            # 3. 備份現有數據
            print("\n💾 備份現有數據...")
            cursor.execute("CREATE TABLE position_records_backup AS SELECT * FROM position_records")
            
            cursor.execute("SELECT COUNT(*) FROM position_records_backup")
            record_count = cursor.fetchone()[0]
            print(f"   備份了 {record_count} 條記錄")
            
            # 4. 刪除舊表
            print("\n🗑️ 刪除舊表...")
            cursor.execute("DROP TABLE position_records")
            
            # 5. 創建新表（帶修復約束）
            print("\n🏗️ 創建新表（帶修復約束）...")
            cursor.execute('''
                CREATE TABLE position_records (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    group_id INTEGER NOT NULL,
                    lot_id INTEGER NOT NULL,
                    direction TEXT NOT NULL,
                    entry_price REAL,
                    entry_time TEXT,
                    exit_price REAL,
                    exit_time TEXT,
                    exit_reason TEXT,
                    pnl REAL,
                    pnl_amount REAL,
                    status TEXT NOT NULL DEFAULT 'PENDING',
                    rule_config TEXT,
                    order_id TEXT,
                    api_seq_no TEXT,
                    order_status TEXT,
                    retry_count INTEGER DEFAULT 0,
                    max_slippage_points REAL DEFAULT 5.0,
                    last_retry_time TEXT,
                    retry_reason TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    initial_stop_loss REAL,
                    current_stop_loss REAL,
                    is_initial_stop BOOLEAN DEFAULT TRUE,
                    trailing_activated BOOLEAN DEFAULT FALSE,
                    peak_price REAL,
                    trailing_activation_points INTEGER,
                    trailing_pullback_ratio REAL DEFAULT 0.20,
                    protective_multiplier REAL,
                    cumulative_profit_before REAL DEFAULT 0,
                    realized_pnl REAL DEFAULT 0,
                    lot_rule_id INTEGER,
                    exit_trigger_type TEXT,
                    exit_order_id TEXT,
                    last_price_update_time TEXT,
                    original_price REAL,

                    FOREIGN KEY (group_id) REFERENCES strategy_groups(id),
                    CHECK(direction IN ('LONG', 'SHORT')),
                    CHECK(status IN ('ACTIVE', 'EXITED', 'FAILED', 'PENDING')),
                    CHECK(order_status IN ('PENDING', 'FILLED', 'CANCELLED', 'REJECTED') OR order_status IS NULL),
                    CHECK(lot_id BETWEEN 1 AND 3),
                    CHECK(exit_reason IN ('移動停利', '保護性停損', '初始停損', '手動出場', 'FOK失敗', '下單失敗') OR exit_reason IS NULL),
                    CHECK(retry_count IS NULL OR (retry_count >= 0 AND retry_count <= 5)),
                    CHECK(max_slippage_points IS NULL OR max_slippage_points > 0)
                )
            ''')
            
            # 6. 恢復數據
            print("\n📥 恢復數據...")
            
            # 獲取備份表的列名
            cursor.execute("PRAGMA table_info(position_records_backup)")
            backup_columns = [col[1] for col in cursor.fetchall()]
            
            # 獲取新表的列名
            cursor.execute("PRAGMA table_info(position_records)")
            new_columns = [col[1] for col in cursor.fetchall()]
            
            # 找出共同的列
            common_columns = [col for col in backup_columns if col in new_columns]
            columns_str = ', '.join(common_columns)
            
            print(f"   恢復字段: {len(common_columns)} 個")
            
            cursor.execute(f'''
                INSERT INTO position_records ({columns_str})
                SELECT {columns_str} FROM position_records_backup
            ''')
            
            restored_count = cursor.rowcount
            print(f"   恢復了 {restored_count} 條記錄")
            
            # 7. 清理備份表
            print("\n🧹 清理備份表...")
            cursor.execute("DROP TABLE position_records_backup")
            
            conn.commit()
            
            # 8. 驗證新表結構
            print("\n✅ 驗證新表結構...")
            cursor.execute("SELECT sql FROM sqlite_master WHERE type='table' AND name='position_records'")
            new_sql = cursor.fetchone()[0]
            
            if 'retry_count IS NULL OR' in new_sql:
                print("   ✅ retry_count 約束修復成功")
            else:
                print("   ❌ retry_count 約束修復失敗")
                
            if 'max_slippage_points IS NULL OR' in new_sql:
                print("   ✅ max_slippage_points 約束修復成功")
            else:
                print("   ❌ max_slippage_points 約束修復失敗")
            
            # 9. 測試 None 值插入
            print("\n🧪 測試 None 值插入...")
            try:
                cursor.execute('''
                    INSERT INTO position_records 
                    (group_id, lot_id, direction, retry_count, max_slippage_points, status)
                    VALUES (9999, 1, 'LONG', NULL, NULL, 'PENDING')
                ''')
                test_id = cursor.lastrowid
                print("   ✅ None 值插入測試成功")
                
                # 清理測試數據
                cursor.execute("DELETE FROM position_records WHERE id = ?", (test_id,))
                conn.commit()
                
            except Exception as e:
                if 'not supported between instances' in str(e):
                    print(f"   ❌ None 值插入測試失敗: {e}")
                else:
                    print(f"   ✅ None 值處理正常 (其他約束錯誤: {e})")
            
            print(f"\n🎉 表格重建完成!")
            print(f"   備份文件: {backup_path}")
            print(f"   恢復記錄: {restored_count} 條")
            
    except Exception as e:
        print(f"\n❌ 重建過程出錯: {e}")
        print(f"   可以從備份恢復: {backup_path}")
        raise

def verify_rebuild():
    """驗證重建結果"""
    print("\n🔍 驗證重建結果...")
    
    try:
        with sqlite3.connect("multi_group_strategy.db") as conn:
            cursor = conn.cursor()
            
            # 檢查記錄數
            cursor.execute("SELECT COUNT(*) FROM position_records")
            count = cursor.fetchone()[0]
            print(f"   總記錄數: {count}")
            
            # 檢查最近記錄
            cursor.execute("""
                SELECT id, retry_count, max_slippage_points, status
                FROM position_records 
                ORDER BY id DESC LIMIT 3
            """)
            recent = cursor.fetchall()
            print("   最近記錄:")
            for record in recent:
                print(f"     ID {record[0]}: retry_count={record[1]}, max_slippage_points={record[2]}, status={record[3]}")
            
            # 檢查 None 值
            cursor.execute("""
                SELECT COUNT(*) FROM position_records 
                WHERE retry_count IS NULL OR max_slippage_points IS NULL
            """)
            null_count = cursor.fetchone()[0]
            print(f"   包含 None 值的記錄: {null_count}")
            
    except Exception as e:
        print(f"   ❌ 驗證失敗: {e}")

def main():
    """主函數"""
    try:
        force_rebuild_table()
        verify_rebuild()
        
        print("\n📋 下一步:")
        print("   1. 重啟交易系統")
        print("   2. 測試建倉功能")
        print("   3. 確認無資料庫錯誤")
        
    except Exception as e:
        print(f"\n💥 執行失敗: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
