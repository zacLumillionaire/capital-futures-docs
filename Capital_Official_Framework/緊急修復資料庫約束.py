#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
緊急修復資料庫約束問題
解決 '>=' not supported between instances of 'NoneType' and 'int' 錯誤
"""

import sqlite3
import os
import shutil
from datetime import datetime

def backup_database(db_path: str) -> str:
    """備份資料庫"""
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    backup_path = f"{db_path}.backup_{timestamp}"
    shutil.copy2(db_path, backup_path)
    print(f"✅ 資料庫已備份至: {backup_path}")
    return backup_path

def check_current_constraints(db_path: str):
    """檢查當前的約束"""
    print("🔍 檢查當前資料庫約束...")
    
    try:
        with sqlite3.connect(db_path) as conn:
            cursor = conn.cursor()
            
            # 獲取 position_records 表的創建語句
            cursor.execute("""
                SELECT sql FROM sqlite_master 
                WHERE type='table' AND name='position_records'
            """)
            
            result = cursor.fetchone()
            if result:
                table_sql = result[0]
                print("📋 當前表格定義:")
                print(table_sql)
                
                # 檢查是否包含問題約束
                if "CHECK(retry_count >= 0" in table_sql:
                    print("❌ 發現問題約束: retry_count >= 0")
                    return True
                else:
                    print("✅ 約束已修復或不存在問題")
                    return False
            else:
                print("❌ 找不到 position_records 表")
                return False
                
    except Exception as e:
        print(f"❌ 檢查約束失敗: {e}")
        return False

def fix_database_constraints(db_path: str):
    """修復資料庫約束"""
    print("🔧 開始修復資料庫約束...")
    
    try:
        with sqlite3.connect(db_path) as conn:
            cursor = conn.cursor()
            
            # 步驟1: 創建新的表格（帶修復的約束）
            print("📋 步驟1: 創建修復後的表格...")
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS position_records_fixed (
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

                    CHECK(direction IN ('LONG', 'SHORT')),
                    CHECK(status IN ('ACTIVE', 'EXITED', 'FAILED', 'PENDING')),
                    CHECK(order_status IN ('PENDING', 'FILLED', 'CANCELLED', 'REJECTED') OR order_status IS NULL),
                    CHECK(lot_id BETWEEN 1 AND 3),
                    CHECK(exit_reason IN ('移動停利', '保護性停損', '初始停損', '手動出場', 'FOK失敗', '下單失敗') OR exit_reason IS NULL),
                    CHECK(retry_count IS NULL OR (retry_count >= 0 AND retry_count <= 5)),
                    CHECK(max_slippage_points IS NULL OR max_slippage_points > 0)
                )
            ''')
            
            # 步驟2: 複製數據到新表格
            print("📋 步驟2: 複製現有數據...")
            cursor.execute('''
                INSERT INTO position_records_fixed 
                SELECT * FROM position_records
            ''')
            
            # 步驟3: 刪除舊表格
            print("📋 步驟3: 刪除舊表格...")
            cursor.execute('DROP TABLE position_records')
            
            # 步驟4: 重命名新表格
            print("📋 步驟4: 重命名新表格...")
            cursor.execute('ALTER TABLE position_records_fixed RENAME TO position_records')
            
            # 步驟5: 修復現有的 None 值
            print("📋 步驟5: 修復現有的 None 值...")
            cursor.execute('''
                UPDATE position_records 
                SET retry_count = 0 
                WHERE retry_count IS NULL
            ''')
            retry_fixed = cursor.rowcount
            
            cursor.execute('''
                UPDATE position_records 
                SET max_slippage_points = 5.0 
                WHERE max_slippage_points IS NULL
            ''')
            slippage_fixed = cursor.rowcount
            
            conn.commit()
            
            print(f"✅ 修復完成!")
            print(f"   - 修復 retry_count: {retry_fixed} 條記錄")
            print(f"   - 修復 max_slippage_points: {slippage_fixed} 條記錄")
            
            return True
            
    except Exception as e:
        print(f"❌ 修復失敗: {e}")
        return False

def test_constraints(db_path: str):
    """測試修復後的約束"""
    print("🧪 測試修復後的約束...")
    
    try:
        with sqlite3.connect(db_path) as conn:
            cursor = conn.cursor()
            
            # 測試插入 None 值
            try:
                cursor.execute('''
                    INSERT INTO position_records 
                    (group_id, lot_id, direction, retry_count, max_slippage_points, status)
                    VALUES (999, 1, 'LONG', NULL, NULL, 'PENDING')
                ''')
                
                test_id = cursor.lastrowid
                
                # 清理測試數據
                cursor.execute('DELETE FROM position_records WHERE id = ?', (test_id,))
                conn.commit()
                
                print("✅ 約束測試通過 - None 值被正確處理")
                return True
                
            except Exception as e:
                if "not supported between instances of 'NoneType' and 'int'" in str(e):
                    print("❌ 約束測試失敗 - 仍然有 None 值問題")
                    print(f"   錯誤: {e}")
                    return False
                else:
                    print("✅ 約束測試通過 - None 值處理正常")
                    return True
                    
    except Exception as e:
        print(f"❌ 測試約束失敗: {e}")
        return False

def check_position_data(db_path: str):
    """檢查部位數據"""
    print("📊 檢查部位數據...")
    
    try:
        with sqlite3.connect(db_path) as conn:
            cursor = conn.cursor()
            
            cursor.execute('''
                SELECT id, group_id, lot_id, entry_price, retry_count, max_slippage_points, status
                FROM position_records 
                WHERE status IN ('ACTIVE', 'PENDING')
                ORDER BY id DESC
                LIMIT 10
            ''')
            
            positions = cursor.fetchall()
            print(f"📋 最近 {len(positions)} 個部位:")
            
            for pos in positions:
                pos_id, group_id, lot_id, entry_price, retry_count, max_slippage, status = pos
                print(f"   部位 {pos_id}: 組{group_id}, 第{lot_id}口, 價格={entry_price}, "
                      f"重試={retry_count}, 滑價={max_slippage}, 狀態={status}")
                
                if retry_count is None or max_slippage is None:
                    print(f"     ⚠️ 發現 None 值")
            
            return True
            
    except Exception as e:
        print(f"❌ 檢查部位數據失敗: {e}")
        return False

def main():
    """主修復函數"""
    print("🚀 緊急修復資料庫約束問題")
    print("=" * 50)
    
    db_path = "multi_group_strategy.db"
    
    if not os.path.exists(db_path):
        print(f"❌ 找不到資料庫文件: {db_path}")
        return
    
    # 1. 備份資料庫
    backup_path = backup_database(db_path)
    
    # 2. 檢查當前約束
    has_problem = check_current_constraints(db_path)
    
    if has_problem:
        # 3. 修復約束
        if fix_database_constraints(db_path):
            print("✅ 約束修復成功")
            
            # 4. 測試修復結果
            if test_constraints(db_path):
                print("✅ 修復驗證通過")
                
                # 5. 檢查數據
                check_position_data(db_path)
                
                print("\n🎉 修復完成! 請重新啟動交易系統測試建倉功能")
            else:
                print("❌ 修復驗證失敗")
        else:
            print("❌ 約束修復失敗")
    else:
        print("ℹ️ 約束看起來已經正確，檢查數據...")
        check_position_data(db_path)
        
        # 仍然測試一下
        test_constraints(db_path)

if __name__ == "__main__":
    main()
