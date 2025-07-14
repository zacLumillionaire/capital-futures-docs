#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
🔧 數據庫結構遷移腳本
將 risk_management_states 表從 update_reason 遷移到 update_category + update_message
"""

import sqlite3
import shutil
import time
from datetime import datetime

def backup_database(db_path):
    """備份數據庫"""
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    backup_path = f"{db_path}.backup_schema_migration_{timestamp}"
    shutil.copy2(db_path, backup_path)
    print(f"✅ 數據庫已備份: {backup_path}")
    return backup_path

def check_current_schema(db_path):
    """檢查當前表結構"""
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # 檢查表是否存在
        cursor.execute("""
            SELECT name FROM sqlite_master 
            WHERE type='table' AND name='risk_management_states'
        """)
        
        if not cursor.fetchone():
            print("❌ risk_management_states 表不存在")
            return False
        
        # 檢查欄位結構
        cursor.execute("PRAGMA table_info(risk_management_states)")
        columns = cursor.fetchall()
        
        print("📋 當前表結構:")
        column_names = []
        for col in columns:
            column_names.append(col[1])
            print(f"  - {col[1]} ({col[2]})")
        
        # 檢查是否已經是新結構
        has_update_category = 'update_category' in column_names
        has_update_message = 'update_message' in column_names
        has_update_reason = 'update_reason' in column_names
        
        if has_update_category and has_update_message:
            print("✅ 表結構已經是新版本")
            return True
        elif has_update_reason:
            print("⚠️ 表結構是舊版本，需要遷移")
            return False
        else:
            print("❌ 表結構異常")
            return None
            
        conn.close()
        
    except Exception as e:
        print(f"❌ 檢查表結構失敗: {e}")
        return None

def migrate_schema(db_path):
    """執行結構遷移"""
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        print("🔧 開始結構遷移...")
        
        # 1. 創建新表結構
        print("📝 創建新表結構...")
        cursor.execute('''
            CREATE TABLE risk_management_states_new (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                position_id INTEGER NOT NULL,
                peak_price REAL NOT NULL,
                current_stop_loss REAL,
                trailing_activated BOOLEAN DEFAULT FALSE,
                protection_activated BOOLEAN DEFAULT FALSE,
                last_update_time TEXT NOT NULL,
                update_category TEXT,
                update_message TEXT,
                previous_stop_loss REAL,
                
                FOREIGN KEY (position_id) REFERENCES position_records(id),
                CHECK(update_category IN ('價格更新', '移動停利啟動', '保護性停損更新', '初始化', '成交初始化', '簡化追蹤成交確認') OR update_category IS NULL),
                CHECK(update_message IS NULL OR LENGTH(update_message) > 0)
            )
        ''')
        
        # 2. 遷移現有數據
        print("📦 遷移現有數據...")
        cursor.execute('''
            INSERT INTO risk_management_states_new 
            (id, position_id, peak_price, current_stop_loss, trailing_activated, 
             protection_activated, last_update_time, update_category, update_message, previous_stop_loss)
            SELECT 
                id, position_id, peak_price, current_stop_loss, trailing_activated,
                protection_activated, last_update_time, 
                CASE 
                    WHEN update_reason IN ('價格更新', '移動停利啟動', '保護性停損更新', '初始化', '成交初始化', '簡化追蹤成交確認') 
                    THEN update_reason 
                    ELSE '初始化' 
                END as update_category,
                update_reason as update_message,
                previous_stop_loss
            FROM risk_management_states
        ''')
        
        # 3. 替換表
        print("🔄 替換表結構...")
        cursor.execute('DROP TABLE risk_management_states')
        cursor.execute('ALTER TABLE risk_management_states_new RENAME TO risk_management_states')
        
        # 4. 重建索引
        print("📊 重建索引...")
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_risk_management_states_position_id ON risk_management_states(position_id)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_risk_management_states_position_protection ON risk_management_states(position_id, protection_activated)')
        
        conn.commit()
        conn.close()
        
        print("🎉 結構遷移完成!")
        return True
        
    except Exception as e:
        print(f"❌ 結構遷移失敗: {e}")
        conn.rollback()
        conn.close()
        return False

def verify_migration(db_path):
    """驗證遷移結果"""
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # 檢查新表結構
        cursor.execute("PRAGMA table_info(risk_management_states)")
        columns = cursor.fetchall()
        
        print("📋 遷移後表結構:")
        column_names = []
        for col in columns:
            column_names.append(col[1])
            print(f"  - {col[1]} ({col[2]})")
        
        # 驗證關鍵欄位
        required_columns = ['update_category', 'update_message']
        missing_columns = [col for col in required_columns if col not in column_names]
        
        if missing_columns:
            print(f"❌ 缺少欄位: {missing_columns}")
            return False
        
        # 檢查數據
        cursor.execute("SELECT COUNT(*) FROM risk_management_states")
        count = cursor.fetchone()[0]
        print(f"📊 遷移後記錄數: {count}")
        
        # 測試插入
        print("🧪 測試新結構...")
        cursor.execute('''
            INSERT INTO risk_management_states 
            (position_id, peak_price, last_update_time, update_category, update_message)
            VALUES (99999, 22000.0, '00:00:00', '初始化', '測試插入')
        ''')
        
        cursor.execute('DELETE FROM risk_management_states WHERE position_id = 99999')
        conn.commit()
        
        print("✅ 遷移驗證成功!")
        conn.close()
        return True
        
    except Exception as e:
        print(f"❌ 遷移驗證失敗: {e}")
        return False

def main():
    """主函數"""
    db_path = "multi_group_strategy.db"
    
    print("🔧 數據庫結構遷移工具")
    print("=" * 50)
    
    # 1. 檢查當前結構
    schema_status = check_current_schema(db_path)
    
    if schema_status is True:
        print("✅ 數據庫結構已經是最新版本，無需遷移")
        return True
    elif schema_status is None:
        print("❌ 數據庫結構檢查失敗")
        return False
    
    # 2. 備份數據庫
    backup_path = backup_database(db_path)
    
    # 3. 執行遷移
    if migrate_schema(db_path):
        # 4. 驗證遷移
        if verify_migration(db_path):
            print(f"\n🎉 數據庫結構遷移完成!")
            print(f"📁 備份文件: {backup_path}")
            print("\n✅ 現在可以重新啟動策略機")
            return True
        else:
            print("❌ 遷移驗證失敗")
            return False
    else:
        print("❌ 遷移失敗")
        return False

if __name__ == "__main__":
    success = main()
    if not success:
        print("\n❌ 遷移失敗，請檢查錯誤訊息")
        print("💡 如果需要，可以從備份文件恢復數據庫")
    else:
        print("\n🚀 遷移成功，策略機已準備就緒")
