#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
手動初始化平倉機制資料庫
"""

import sqlite3
import shutil
from datetime import datetime

def create_lot_exit_rules_table(cursor):
    """創建口數平倉規則配置表"""
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS lot_exit_rules (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            rule_name TEXT NOT NULL,
            lot_number INTEGER NOT NULL,
            trailing_activation_points INTEGER NOT NULL,
            trailing_pullback_ratio REAL NOT NULL DEFAULT 0.20,
            protective_stop_multiplier REAL,
            description TEXT,
            is_default BOOLEAN DEFAULT FALSE,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            
            CHECK(lot_number BETWEEN 1 AND 3),
            CHECK(trailing_activation_points > 0),
            CHECK(trailing_pullback_ratio BETWEEN 0.1 AND 0.5),
            CHECK(protective_stop_multiplier IS NULL OR protective_stop_multiplier > 0)
        )
    ''')
    print("✅ 創建 lot_exit_rules 表格")

def insert_default_rules(cursor):
    """插入預設規則"""
    # 先檢查是否已有預設規則
    cursor.execute("SELECT COUNT(*) FROM lot_exit_rules WHERE is_default = 1")
    existing_count = cursor.fetchone()[0]
    
    if existing_count > 0:
        print(f"📊 已存在 {existing_count} 個預設規則，先清理...")
        cursor.execute("DELETE FROM lot_exit_rules WHERE is_default = 1")
    
    # 插入正確的預設規則
    default_rules = [
        ('回測標準規則', 1, 15, 0.20, None, '第1口: 15點啟動移動停利'),
        ('回測標準規則', 2, 40, 0.20, 2.0, '第2口: 40點啟動移動停利, 2倍保護'),
        ('回測標準規則', 3, 65, 0.20, 2.0, '第3口: 65點啟動移動停利, 2倍保護')
    ]
    
    for rule_data in default_rules:
        cursor.execute('''
            INSERT INTO lot_exit_rules 
            (rule_name, lot_number, trailing_activation_points, trailing_pullback_ratio, 
             protective_stop_multiplier, description, is_default)
            VALUES (?, ?, ?, ?, ?, ?, TRUE)
        ''', rule_data)
    
    print("✅ 插入預設規則: 15/40/65點啟動, 2倍保護")

def create_other_exit_tables(cursor):
    """創建其他平倉相關表格"""
    
    # group_exit_status 表格
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS group_exit_status (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            group_id INTEGER NOT NULL,
            total_lots INTEGER NOT NULL,
            exited_lots INTEGER DEFAULT 0,
            exit_method TEXT,
            exit_start_time TEXT,
            exit_complete_time TEXT,
            is_complete BOOLEAN DEFAULT FALSE,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            
            FOREIGN KEY (group_id) REFERENCES strategy_groups(id),
            CHECK(exited_lots >= 0),
            CHECK(exited_lots <= total_lots),
            CHECK(exit_method IN ('MANUAL', 'TRAILING_STOP', 'INITIAL_STOP', 'PROTECTION_STOP', 'TIME_EXIT') OR exit_method IS NULL)
        )
    ''')
    print("✅ 創建 group_exit_status 表格")
    
    # exit_events 表格
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS exit_events (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            position_id INTEGER NOT NULL,
            group_id INTEGER NOT NULL,
            lot_id INTEGER NOT NULL,
            exit_method TEXT NOT NULL,
            exit_price REAL NOT NULL,
            exit_time TEXT NOT NULL,
            pnl REAL,
            exit_reason TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            
            FOREIGN KEY (position_id) REFERENCES position_records(id),
            FOREIGN KEY (group_id) REFERENCES strategy_groups(id),
            CHECK(exit_method IN ('MANUAL', 'TRAILING_STOP', 'INITIAL_STOP', 'PROTECTION_STOP', 'TIME_EXIT')),
            CHECK(lot_id BETWEEN 1 AND 3)
        )
    ''')
    print("✅ 創建 exit_events 表格")

def create_indexes(cursor):
    """創建索引"""
    indexes = [
        'CREATE INDEX IF NOT EXISTS idx_lot_exit_rules_default ON lot_exit_rules(is_default, lot_number)',
        'CREATE INDEX IF NOT EXISTS idx_group_exit_status_group ON group_exit_status(group_id)',
        'CREATE INDEX IF NOT EXISTS idx_exit_events_position ON exit_events(position_id)',
        'CREATE INDEX IF NOT EXISTS idx_exit_events_group ON exit_events(group_id)'
    ]
    
    for index_sql in indexes:
        cursor.execute(index_sql)
    
    print("✅ 創建索引")

def main():
    print('🚀 手動初始化平倉機制資料庫')
    print('=' * 50)
    
    # 備份資料庫
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    backup_name = f'multi_group_strategy.db.backup_manual_init_{timestamp}'
    shutil.copy2('multi_group_strategy.db', backup_name)
    print(f'✅ 資料庫已備份: {backup_name}')
    
    conn = sqlite3.connect('multi_group_strategy.db')
    cursor = conn.cursor()
    
    try:
        # 1. 創建 lot_exit_rules 表格
        create_lot_exit_rules_table(cursor)
        
        # 2. 插入預設規則
        insert_default_rules(cursor)
        
        # 3. 創建其他平倉相關表格
        create_other_exit_tables(cursor)
        
        # 4. 創建索引
        create_indexes(cursor)
        
        conn.commit()
        
        # 5. 驗證結果
        cursor.execute("SELECT COUNT(*) FROM lot_exit_rules WHERE is_default = 1")
        rule_count = cursor.fetchone()[0]
        
        print(f'\n📊 驗證結果:')
        print(f'  預設規則數量: {rule_count}')
        
        if rule_count == 3:
            print('🎉 平倉機制資料庫初始化成功！')
            
            # 顯示規則詳情
            cursor.execute('''
                SELECT lot_number, trailing_activation_points, protective_stop_multiplier, description
                FROM lot_exit_rules 
                WHERE is_default = 1
                ORDER BY lot_number
            ''')
            
            rules = cursor.fetchall()
            print('\n📋 預設規則:')
            for rule in rules:
                lot_num, points, multiplier, desc = rule
                multiplier_str = f', {multiplier}倍保護' if multiplier else ''
                print(f'  第{lot_num}口: {points}點啟動{multiplier_str}')
            
            return True
        else:
            print(f'❌ 規則數量不正確: {rule_count}/3')
            return False
            
    except Exception as e:
        print(f'❌ 初始化失敗: {e}')
        conn.rollback()
        return False
    finally:
        conn.close()

if __name__ == "__main__":
    success = main()
    
    if success:
        print('\n✅ 修復完成！')
        print('📝 建議:')
        print('1. 重新啟動策略機')
        print('2. 確認不再出現「資料庫擴展失敗」訊息')
        print('3. 出場點位監控功能現在可以正常運作')
    else:
        print('\n❌ 修復失敗，請檢查錯誤訊息')
