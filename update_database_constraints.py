#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
更新資料庫約束
修復 risk_management_states 表的 update_reason 約束
"""

import sqlite3
import os
import sys
import shutil
from datetime import datetime

def backup_database(db_path):
    """備份資料庫"""
    if not os.path.exists(db_path):
        print(f"❌ 資料庫文件不存在: {db_path}")
        return None
        
    backup_path = f"{db_path}.backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
    try:
        shutil.copy2(db_path, backup_path)
        print(f"✅ 資料庫已備份: {backup_path}")
        return backup_path
    except Exception as e:
        print(f"❌ 備份失敗: {e}")
        return None

def check_current_constraint(db_path):
    """檢查當前約束"""
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # 獲取表結構
        cursor.execute("SELECT sql FROM sqlite_master WHERE type='table' AND name='risk_management_states'")
        result = cursor.fetchone()
        
        if result:
            table_sql = result[0]
            print("📋 當前表結構:")
            print(table_sql)
            
            # 檢查是否包含新的約束值
            if '成交初始化' in table_sql:
                print("✅ 約束已包含 '成交初始化'")
                return True
            else:
                print("❌ 約束缺少 '成交初始化'")
                return False
        else:
            print("❌ 找不到 risk_management_states 表")
            return False
            
    except Exception as e:
        print(f"❌ 檢查約束失敗: {e}")
        return False
    finally:
        conn.close()

def update_database_constraint(db_path):
    """更新資料庫約束"""
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        print("🔧 開始更新資料庫約束...")
        
        # 1. 創建新表結構
        cursor.execute('''
            CREATE TABLE risk_management_states_new (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                position_id INTEGER NOT NULL,
                peak_price REAL NOT NULL,
                current_stop_loss REAL,
                trailing_activated BOOLEAN DEFAULT FALSE,
                protection_activated BOOLEAN DEFAULT FALSE,
                last_update_time TEXT NOT NULL,
                update_reason TEXT,
                previous_stop_loss REAL,
                
                FOREIGN KEY (position_id) REFERENCES position_records(id),
                CHECK(update_reason IN ('價格更新', '移動停利啟動', '保護性停損更新', '初始化', '成交初始化', '簡化追蹤成交確認') OR update_reason IS NULL)
            )
        ''')
        print("✅ 創建新表結構")
        
        # 2. 複製現有數據
        cursor.execute('''
            INSERT INTO risk_management_states_new 
            SELECT * FROM risk_management_states
        ''')
        print("✅ 複製現有數據")
        
        # 3. 刪除舊表
        cursor.execute('DROP TABLE risk_management_states')
        print("✅ 刪除舊表")
        
        # 4. 重命名新表
        cursor.execute('ALTER TABLE risk_management_states_new RENAME TO risk_management_states')
        print("✅ 重命名新表")
        
        conn.commit()
        print("🎉 資料庫約束更新完成!")
        
        return True
        
    except Exception as e:
        print(f"❌ 更新失敗: {e}")
        conn.rollback()
        return False
    finally:
        conn.close()

def test_new_constraint(db_path):
    """測試新約束"""
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        print("🧪 測試新約束...")
        
        # 測試插入有效的 update_reason
        test_values = ['初始化', '成交初始化', '價格更新', '移動停利啟動', '保護性停損更新']
        
        for value in test_values:
            try:
                cursor.execute('''
                    INSERT INTO risk_management_states 
                    (position_id, peak_price, last_update_time, update_reason)
                    VALUES (999, 22000.0, '00:00:00', ?)
                ''', (value,))
                print(f"✅ 測試通過: '{value}'")
            except Exception as e:
                print(f"❌ 測試失敗: '{value}' - {e}")
        
        # 清理測試數據
        cursor.execute('DELETE FROM risk_management_states WHERE position_id = 999')
        conn.commit()
        
        return True
        
    except Exception as e:
        print(f"❌ 測試失敗: {e}")
        return False
    finally:
        conn.close()

def main():
    """主函數"""
    print("🚀 開始更新資料庫約束")
    print("=" * 60)
    
    # 查找資料庫文件
    possible_paths = [
        "multi_group_strategy.db",
        "Capital_Official_Framework/multi_group_strategy.db",
        "strategy.db"
    ]
    
    db_path = None
    for path in possible_paths:
        if os.path.exists(path):
            db_path = path
            break
    
    if not db_path:
        print("❌ 找不到資料庫文件")
        print("請確認資料庫文件位置，或手動指定路徑")
        return False
    
    print(f"📁 找到資料庫: {db_path}")
    
    # 1. 檢查當前約束
    if check_current_constraint(db_path):
        print("✅ 約束已經是最新的，無需更新")
        return True
    
    # 2. 備份資料庫
    backup_path = backup_database(db_path)
    if not backup_path:
        print("❌ 備份失敗，停止更新")
        return False
    
    # 3. 更新約束
    if not update_database_constraint(db_path):
        print("❌ 更新失敗")
        return False
    
    # 4. 測試新約束
    if not test_new_constraint(db_path):
        print("❌ 測試失敗")
        return False
    
    # 5. 驗證更新
    if check_current_constraint(db_path):
        print("🎉 資料庫約束更新成功!")
        print(f"📁 備份文件: {backup_path}")
        print("\n📝 現在可以使用以下 update_reason 值:")
        print("  - '初始化'")
        print("  - '成交初始化'")
        print("  - '價格更新'")
        print("  - '移動停利啟動'")
        print("  - '保護性停損更新'")
        print("  - '簡化追蹤成交確認'")
        return True
    else:
        print("❌ 驗證失敗")
        return False

if __name__ == "__main__":
    success = main()
    if not success:
        print("\n❌ 更新失敗，請檢查錯誤訊息")
        sys.exit(1)
    else:
        print("\n✅ 更新完成，可以重新啟動策略機")
