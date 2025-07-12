#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import sqlite3

print('🚀 修復平倉機制資料庫')

conn = sqlite3.connect('multi_group_strategy.db')
cursor = conn.cursor()

try:
    # 創建 lot_exit_rules 表格
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
    print('✅ 創建 lot_exit_rules 表格')
    
    # 清理現有預設規則
    cursor.execute('DELETE FROM lot_exit_rules WHERE is_default = 1')
    
    # 插入正確的預設規則
    rules = [
        ('回測標準規則', 1, 15, 0.20, None, '第1口: 15點啟動移動停利'),
        ('回測標準規則', 2, 40, 0.20, 2.0, '第2口: 40點啟動移動停利, 2倍保護'),
        ('回測標準規則', 3, 65, 0.20, 2.0, '第3口: 65點啟動移動停利, 2倍保護')
    ]
    
    for rule in rules:
        cursor.execute('''
            INSERT INTO lot_exit_rules 
            (rule_name, lot_number, trailing_activation_points, trailing_pullback_ratio, 
             protective_stop_multiplier, description, is_default)
            VALUES (?, ?, ?, ?, ?, ?, TRUE)
        ''', rule)
    
    print('✅ 插入預設規則: 15/40/65點啟動, 2倍保護')
    
    conn.commit()
    
    # 驗證結果
    cursor.execute('SELECT COUNT(*) FROM lot_exit_rules WHERE is_default = 1')
    count = cursor.fetchone()[0]
    print(f'📊 預設規則數量: {count}')
    
    if count == 3:
        print('🎉 平倉機制資料庫初始化成功！')
        print('✅ 出場點位監控功能現在可以正常運作')
    else:
        print(f'❌ 規則數量不正確: {count}/3')
        
except Exception as e:
    print(f'❌ 修復失敗: {e}')
finally:
    conn.close()
