#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import sqlite3

print('🔍 檢查當前資料庫狀態')
print('=' * 40)

conn = sqlite3.connect('multi_group_strategy.db')
cursor = conn.cursor()

# 檢查表格是否存在
cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='lot_exit_rules'")
table_exists = cursor.fetchone()

if table_exists:
    print('✅ lot_exit_rules 表格存在')
    
    # 檢查預設規則數量
    cursor.execute('SELECT COUNT(*) FROM lot_exit_rules WHERE is_default = 1')
    default_count = cursor.fetchone()[0]
    print(f'📊 預設規則數量: {default_count}')
    
    # 檢查總規則數量
    cursor.execute('SELECT COUNT(*) FROM lot_exit_rules')
    total_count = cursor.fetchone()[0]
    print(f'📊 總規則數量: {total_count}')
    
    # 顯示所有預設規則
    cursor.execute('''
        SELECT id, lot_number, trailing_activation_points, protective_stop_multiplier, created_at
        FROM lot_exit_rules 
        WHERE is_default = 1
        ORDER BY lot_number
    ''')
    
    rules = cursor.fetchall()
    print('\n📋 預設規則詳情:')
    for rule in rules:
        print(f'  ID={rule[0]}: 第{rule[1]}口 {rule[2]}點啟動 保護倍數={rule[3]} 時間={rule[4]}')
        
    # 檢查是否有重複
    cursor.execute('''
        SELECT lot_number, COUNT(*) as count
        FROM lot_exit_rules 
        WHERE is_default = 1
        GROUP BY lot_number
        HAVING count > 1
    ''')
    
    duplicates = cursor.fetchall()
    if duplicates:
        print('\n⚠️ 發現重複規則:')
        for dup in duplicates:
            print(f'  第{dup[0]}口: {dup[1]}個重複')
    else:
        print('\n✅ 無重複規則')
        
else:
    print('❌ lot_exit_rules 表格不存在')

conn.close()
