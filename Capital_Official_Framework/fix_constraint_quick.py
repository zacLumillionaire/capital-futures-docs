#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
快速修復資料庫約束問題
"""

import sqlite3
import os
import shutil
from datetime import datetime

def backup_database(db_path):
    """備份資料庫"""
    if os.path.exists(db_path):
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_path = f"{db_path}.backup_{timestamp}"
        shutil.copy2(db_path, backup_path)
        print(f"✅ 資料庫已備份: {backup_path}")
        return backup_path
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
            print(f"當前表結構:\n{table_sql}")
            
            # 檢查是否包含新的約束值
            if '成交初始化' in table_sql and '簡化追蹤成交確認' in table_sql:
                print("✅ 約束已包含所有必要值")
                return True
            else:
                print("❌ 約束缺少必要值")
                return False
        else:
            print("❌ 找不到 risk_management_states 表")
            return False
            
    except Exception as e:
        print(f"❌ 檢查約束失敗: {e}")
        return False
    finally:
        conn.close()

def update_constraint(db_path):
    """更新約束"""
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        print("🔧 開始更新約束...")
        
        # 1. 創建新表
        cursor.execute("""
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
        """)
        print("✅ 創建新表結構")
        
        # 2. 複製數據
        cursor.execute("INSERT INTO risk_management_states_new SELECT * FROM risk_management_states")
        print("✅ 複製現有數據")
        
        # 3. 替換表
        cursor.execute("DROP TABLE risk_management_states")
        cursor.execute("ALTER TABLE risk_management_states_new RENAME TO risk_management_states")
        print("✅ 替換表結構")
        
        conn.commit()
        print("🎉 約束更新完成!")
        
        # 4. 測試新約束
        print("🧪 測試新約束...")
        cursor.execute("""
            INSERT INTO risk_management_states 
            (position_id, peak_price, last_update_time, update_reason)
            VALUES (999, 22000.0, '00:00:00', '成交初始化')
        """)
        print("✅ 測試通過: 成交初始化")
        
        # 清理測試數據
        cursor.execute("DELETE FROM risk_management_states WHERE position_id = 999")
        conn.commit()
        
        return True
        
    except Exception as e:
        print(f"❌ 更新約束失敗: {e}")
        return False
    finally:
        conn.close()

def main():
    """主函數"""
    # 查找資料庫文件
    possible_paths = [
        "multi_group_strategy.db",
        "../multi_group_strategy.db",
        "../../multi_group_strategy.db",
        "Capital_Official_Framework/multi_group_strategy.db"
    ]
    
    db_path = None
    for path in possible_paths:
        if os.path.exists(path):
            db_path = path
            break
    
    if not db_path:
        print("❌ 找不到資料庫文件")
        print("請確認以下路徑之一存在資料庫文件:")
        for path in possible_paths:
            print(f"  - {path}")
        return False
    
    print(f"📁 找到資料庫文件: {db_path}")
    
    # 檢查當前約束
    if check_current_constraint(db_path):
        print("✅ 約束已經是最新版本，無需更新")
        return True
    
    # 備份資料庫
    backup_path = backup_database(db_path)
    if not backup_path:
        print("❌ 備份失敗")
        return False
    
    # 更新約束
    if update_constraint(db_path):
        print("✅ 約束更新成功!")
        print(f"📁 備份文件: {backup_path}")
        print("\n📝 現在支援的 update_reason 值:")
        print("  - '初始化'")
        print("  - '成交初始化'")
        print("  - '價格更新'")
        print("  - '移動停利啟動'")
        print("  - '保護性停損更新'")
        print("  - '簡化追蹤成交確認'")
        return True
    else:
        print("❌ 約束更新失敗")
        return False

if __name__ == "__main__":
    print("🔧 修復資料庫約束問題")
    print("=" * 50)
    
    success = main()
    
    if success:
        print("\n🎉 修復完成！可以重新啟動策略機")
    else:
        print("\n❌ 修復失敗，請檢查錯誤訊息")
