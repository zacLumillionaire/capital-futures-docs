#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
修復資料庫約束問題
"""

import sqlite3
import shutil
from datetime import datetime

def main():
    print("🔧 修復資料庫約束問題")
    print("=" * 40)
    
    # 備份資料庫
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    backup_path = f'multi_group_strategy.db.backup_{timestamp}'
    shutil.copy2('multi_group_strategy.db', backup_path)
    print(f'✅ 資料庫已備份: {backup_path}')
    
    # 更新約束
    conn = sqlite3.connect('multi_group_strategy.db')
    cursor = conn.cursor()
    
    try:
        print('🔧 開始更新資料庫約束...')
        
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
        print('✅ 創建新表結構')
        
        # 複製數據
        cursor.execute('INSERT INTO risk_management_states_new SELECT * FROM risk_management_states')
        print('✅ 複製現有數據')
        
        # 替換表
        cursor.execute('DROP TABLE risk_management_states')
        cursor.execute('ALTER TABLE risk_management_states_new RENAME TO risk_management_states')
        print('✅ 替換表結構')
        
        conn.commit()
        print('🎉 資料庫約束更新完成!')
        
        # 測試新約束
        print('🧪 測試新約束...')
        cursor.execute("""
            INSERT INTO risk_management_states 
            (position_id, peak_price, last_update_time, update_reason)
            VALUES (999, 22000.0, '00:00:00', '成交初始化')
        """)
        print('✅ 測試通過: 成交初始化')
        
        # 清理測試數據
        cursor.execute('DELETE FROM risk_management_states WHERE position_id = 999')
        conn.commit()
        
        print('📝 現在支援的 update_reason 值:')
        print('  - 初始化')
        print('  - 成交初始化')
        print('  - 價格更新')
        print('  - 移動停利啟動')
        print('  - 保護性停損更新')
        print('  - 簡化追蹤成交確認')
        
        return True
        
    except Exception as e:
        print(f'❌ 更新失敗: {e}')
        conn.rollback()
        return False
    finally:
        conn.close()

if __name__ == "__main__":
    success = main()
    if success:
        print('\n✅ 修復完成，可以重新啟動策略機')
    else:
        print('\n❌ 修復失敗，請檢查錯誤訊息')
