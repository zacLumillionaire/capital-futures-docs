#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
添加唯一約束和索引優化
為 lot_exit_rules 表添加複合唯一約束，防止重複數據插入
"""

import sqlite3
import os
import shutil
from datetime import datetime

def backup_database(db_path):
    """備份資料庫"""
    if os.path.exists(db_path):
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_path = f"{db_path}.backup_unique_constraint_{timestamp}"
        shutil.copy2(db_path, backup_path)
        print(f"✅ 資料庫已備份: {backup_path}")
        return backup_path
    return None

def check_current_schema(cursor):
    """檢查當前表結構"""
    print("🔍 檢查當前表結構...")
    
    # 獲取表結構
    cursor.execute("SELECT sql FROM sqlite_master WHERE type='table' AND name='lot_exit_rules'")
    result = cursor.fetchone()
    
    if result:
        table_sql = result[0]
        print("📋 當前表結構:")
        print(table_sql)
        
        # 檢查是否已有唯一約束
        if 'UNIQUE(' in table_sql and 'rule_name' in table_sql:
            print("✅ 表格已有唯一約束")
            return True
        else:
            print("⚠️ 表格缺少唯一約束")
            return False
    else:
        print("❌ 找不到 lot_exit_rules 表")
        return False

def check_indexes(cursor):
    """檢查現有索引"""
    print("\n🔍 檢查現有索引...")
    
    cursor.execute("PRAGMA index_list(lot_exit_rules)")
    indexes = cursor.fetchall()
    
    if indexes:
        print("📋 現有索引:")
        for idx in indexes:
            index_name = idx[1]
            is_unique = "UNIQUE" if idx[2] else "NON-UNIQUE"
            print(f"  - {index_name} ({is_unique})")
            
            # 檢查索引詳情
            cursor.execute(f"PRAGMA index_info({index_name})")
            idx_info = cursor.fetchall()
            for info in idx_info:
                print(f"    欄位: {info[2]}")
    else:
        print("📋 無現有索引")
    
    return len(indexes)

def add_unique_constraint_and_indexes(db_path):
    """添加唯一約束和索引"""
    print("🔧 開始添加唯一約束和索引...")
    
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # 檢查當前狀態
        has_constraint = check_current_schema(cursor)
        index_count = check_indexes(cursor)
        
        if has_constraint:
            print("✅ 表格已有唯一約束，無需修改")
            conn.close()
            return True
        
        print("\n🔧 開始重建表格添加唯一約束...")
        
        # 1. 創建新表結構（帶唯一約束）
        cursor.execute('''
            CREATE TABLE lot_exit_rules_new (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                rule_name TEXT NOT NULL,
                lot_number INTEGER NOT NULL,
                trailing_activation_points INTEGER NOT NULL,
                trailing_pullback_ratio REAL NOT NULL DEFAULT 0.20,
                protective_stop_multiplier REAL,
                description TEXT,
                is_default BOOLEAN DEFAULT FALSE,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                
                -- 約束
                CHECK(lot_number BETWEEN 1 AND 3),
                CHECK(trailing_activation_points > 0),
                CHECK(trailing_pullback_ratio BETWEEN 0.1 AND 0.5),
                CHECK(protective_stop_multiplier IS NULL OR protective_stop_multiplier > 0),
                
                -- 唯一約束（防止重複）
                UNIQUE(rule_name, lot_number, is_default)
            )
        ''')
        print("✅ 創建新表結構（帶唯一約束）")
        
        # 2. 複製現有數據
        cursor.execute('''
            INSERT INTO lot_exit_rules_new 
            SELECT * FROM lot_exit_rules
        ''')
        print("✅ 複製現有數據")
        
        # 3. 刪除舊表
        cursor.execute('DROP TABLE lot_exit_rules')
        print("✅ 刪除舊表")
        
        # 4. 重命名新表
        cursor.execute('ALTER TABLE lot_exit_rules_new RENAME TO lot_exit_rules')
        print("✅ 重命名新表")
        
        # 5. 創建索引（提高查詢性能）
        print("\n🔧 創建索引...")
        
        # 為預設規則查詢創建索引
        cursor.execute('''
            CREATE INDEX IF NOT EXISTS idx_lot_exit_rules_default 
            ON lot_exit_rules(is_default, lot_number)
        ''')
        print("✅ 創建預設規則索引")
        
        # 為規則名稱查詢創建索引
        cursor.execute('''
            CREATE INDEX IF NOT EXISTS idx_lot_exit_rules_name 
            ON lot_exit_rules(rule_name)
        ''')
        print("✅ 創建規則名稱索引")
        
        # 為口數查詢創建索引
        cursor.execute('''
            CREATE INDEX IF NOT EXISTS idx_lot_exit_rules_lot_number 
            ON lot_exit_rules(lot_number)
        ''')
        print("✅ 創建口數索引")
        
        conn.commit()
        print("✅ 提交變更")
        
        # 6. 驗證結果
        print("\n🧪 驗證結果...")
        
        # 檢查數據完整性
        cursor.execute("SELECT COUNT(*) FROM lot_exit_rules")
        total_count = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM lot_exit_rules WHERE is_default = 1")
        default_count = cursor.fetchone()[0]
        
        print(f"📊 總規則數: {total_count}")
        print(f"📊 預設規則數: {default_count}")
        
        # 檢查新的約束和索引
        has_constraint_new = check_current_schema(cursor)
        index_count_new = check_indexes(cursor)
        
        conn.close()
        
        if has_constraint_new and default_count == 3:
            print("\n🎉 唯一約束和索引添加成功！")
            print("✅ 防止重複數據插入")
            print("✅ 提高查詢性能")
            return True
        else:
            print("\n⚠️ 添加過程可能有問題")
            return False
            
    except Exception as e:
        print(f"❌ 添加唯一約束失敗: {e}")
        if 'conn' in locals():
            conn.rollback()
            conn.close()
        return False

def test_unique_constraint(db_path):
    """測試唯一約束是否生效"""
    print("\n🧪 測試唯一約束...")
    
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # 嘗試插入重複的預設規則（應該失敗）
        try:
            cursor.execute('''
                INSERT INTO lot_exit_rules 
                (rule_name, lot_number, trailing_activation_points, trailing_pullback_ratio, 
                 protective_stop_multiplier, description, is_default)
                VALUES ('回測標準規則', 1, 15, 0.20, NULL, '測試重複規則', 1)
            ''')
            conn.commit()
            print("❌ 唯一約束未生效：重複插入成功")
            
            # 清理測試數據
            cursor.execute("DELETE FROM lot_exit_rules WHERE description = '測試重複規則'")
            conn.commit()
            return False
            
        except sqlite3.IntegrityError as e:
            if "UNIQUE constraint failed" in str(e):
                print("✅ 唯一約束生效：重複插入被阻止")
                return True
            else:
                print(f"❌ 其他約束錯誤: {e}")
                return False
                
    except Exception as e:
        print(f"❌ 測試失敗: {e}")
        return False
    finally:
        if 'conn' in locals():
            conn.close()

def main():
    """主函數"""
    print("🚀 添加唯一約束和索引優化")
    print("=" * 50)
    
    db_path = "multi_group_strategy.db"
    
    if not os.path.exists(db_path):
        print(f"❌ 資料庫檔案不存在: {db_path}")
        return False
    
    # 備份資料庫
    backup_path = backup_database(db_path)
    if not backup_path:
        print("❌ 備份失敗，停止操作")
        return False
    
    # 添加唯一約束和索引
    success = add_unique_constraint_and_indexes(db_path)
    
    if success:
        # 測試唯一約束
        test_success = test_unique_constraint(db_path)
        
        if test_success:
            print("\n🎉 所有操作完成！")
            print("\n📋 改進效果:")
            print("  ✅ 防止重複規則插入")
            print("  ✅ 提高查詢性能")
            print("  ✅ 數據完整性保護")
            print(f"\n💾 備份檔案: {backup_path}")
            return True
        else:
            print("\n⚠️ 約束添加成功但測試未通過")
            return False
    else:
        print("\n❌ 操作失敗")
        print(f"💡 可以從備份恢復: {backup_path}")
        return False

if __name__ == "__main__":
    main()
