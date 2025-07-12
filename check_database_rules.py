#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
檢查資料庫中的預設規則
"""

import sqlite3

def check_database_rules():
    """檢查資料庫中的預設規則"""
    print("🔍 檢查資料庫中的預設規則")
    print("=" * 50)
    
    try:
        # 連接資料庫
        conn = sqlite3.connect('multi_group_strategy.db')
        cursor = conn.cursor()
        
        # 檢查表格是否存在
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='lot_exit_rules'")
        if not cursor.fetchone():
            print("❌ lot_exit_rules 表格不存在")
            return
        
        # 檢查總規則數
        cursor.execute('SELECT COUNT(*) FROM lot_exit_rules')
        total_count = cursor.fetchone()[0]
        print(f"📊 總規則數: {total_count}")
        
        # 檢查預設規則數
        cursor.execute('SELECT COUNT(*) FROM lot_exit_rules WHERE is_default = 1')
        default_count = cursor.fetchone()[0]
        print(f"📊 預設規則數: {default_count}")
        
        # 顯示所有規則
        print("\n📋 所有規則詳情:")
        cursor.execute('''
            SELECT id, rule_name, lot_number, trailing_activation_points, 
                   protective_stop_multiplier, is_default, created_at
            FROM lot_exit_rules 
            ORDER BY id
        ''')
        rules = cursor.fetchall()
        
        for rule in rules:
            is_default = "✅" if rule[5] else "❌"
            print(f"  ID={rule[0]}: {rule[1]} 第{rule[2]}口 {rule[3]}點啟動 "
                  f"保護倍數={rule[4]} 預設={is_default} 時間={rule[6]}")
        
        # 檢查重複規則
        print("\n🔍 檢查重複規則:")
        cursor.execute('''
            SELECT rule_name, lot_number, COUNT(*) as count 
            FROM lot_exit_rules 
            GROUP BY rule_name, lot_number 
            HAVING count > 1
        ''')
        duplicates = cursor.fetchall()
        
        if duplicates:
            print("  ⚠️ 發現重複規則:")
            for dup in duplicates:
                print(f"    {dup[0]} 第{dup[1]}口: {dup[2]}次")
        else:
            print("  ✅ 無重複規則")
        
        # 分析問題
        print(f"\n📊 問題分析:")
        print(f"  期望預設規則數: 3")
        print(f"  實際預設規則數: {default_count}")
        
        if default_count == 99:
            print("  🔍 可能原因: 重複插入導致規則數量異常")
            print("  💡 建議: 清理重複規則或重建表格")
        elif default_count > 3:
            print("  🔍 可能原因: 多次執行初始化導致重複插入")
            print("  💡 建議: 使用 INSERT OR IGNORE 或檢查現有規則")
        elif default_count < 3:
            print("  🔍 可能原因: 插入過程中出現錯誤")
            print("  💡 建議: 檢查插入邏輯和約束條件")
        
        conn.close()
        
    except Exception as e:
        print(f"❌ 檢查失敗: {e}")

if __name__ == "__main__":
    check_database_rules()
