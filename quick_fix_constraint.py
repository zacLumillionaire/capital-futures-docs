#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
快速修復資料庫約束
"""

import sqlite3
import shutil
from datetime import datetime

def main():
    print('🔧 快速修復資料庫約束')
    
    # 備份
    backup_name = f'multi_group_strategy.db.backup_{datetime.now().strftime("%Y%m%d_%H%M%S")}'
    shutil.copy2('multi_group_strategy.db', backup_name)
    print(f'✅ 備份完成: {backup_name}')
    
    # 修復約束
    conn = sqlite3.connect('multi_group_strategy.db')
    cursor = conn.cursor()
    
    try:
        # 創建新表
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
        
        # 複製數據
        cursor.execute('INSERT INTO risk_management_states_new SELECT * FROM risk_management_states')
        
        # 替換表
        cursor.execute('DROP TABLE risk_management_states')
        cursor.execute('ALTER TABLE risk_management_states_new RENAME TO risk_management_states')
        
        conn.commit()
        print('✅ 約束修復完成')
        
        # 測試新約束
        cursor.execute("""
            INSERT INTO risk_management_states 
            (position_id, peak_price, last_update_time, update_reason)
            VALUES (999, 22335.0, '00:31:03', '初始化')
        """)
        cursor.execute('DELETE FROM risk_management_states WHERE position_id = 999')
        conn.commit()
        print('✅ 測試通過')
        
        return True
        
    except Exception as e:
        print(f'❌ 修復失敗: {e}')
        conn.rollback()
        return False
    finally:
        conn.close()

if __name__ == "__main__":
    if main():
        print('🎉 修復完成，可以重新啟動策略機')
    else:
        print('❌ 修復失敗')
