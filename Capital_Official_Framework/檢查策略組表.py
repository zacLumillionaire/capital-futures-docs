#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
檢查策略組表內容
"""

import sqlite3
from datetime import date

def check_strategy_groups():
    """檢查策略組表的詳細內容"""
    print("🔍 檢查策略組表內容")
    print("=" * 50)
    
    try:
        conn = sqlite3.connect('multi_group_strategy.db', timeout=5.0)
        cursor = conn.cursor()
        
        today = date.today().isoformat()
        print(f"📅 今日日期: {today}")
        print()
        
        # 1. 檢查所有策略組記錄
        print("1️⃣ 所有策略組記錄:")
        cursor.execute('''
            SELECT id, date, group_id, direction, range_high, range_low, status, created_at
            FROM strategy_groups 
            ORDER BY id DESC
            LIMIT 20
        ''')
        
        all_groups = cursor.fetchall()
        if all_groups:
            print(f"📊 最近20筆策略組記錄:")
            for group in all_groups:
                print(f"   DB_ID={group[0]}, 日期={group[1]}, 組={group[2]}, 方向={group[3]}")
                print(f"   高={group[4]}, 低={group[5]}, 狀態={group[6]}, 建立={group[7]}")
                print()
        else:
            print("❌ 沒有策略組記錄")
            return
        
        # 2. 檢查今日策略組
        print("2️⃣ 今日策略組記錄:")
        cursor.execute('''
            SELECT id, date, group_id, direction, range_high, range_low, status
            FROM strategy_groups 
            WHERE date = ?
            ORDER BY id DESC
        ''', (today,))
        
        today_groups = cursor.fetchall()
        if today_groups:
            print(f"📊 今日策略組數量: {len(today_groups)}")
            for group in today_groups:
                print(f"   DB_ID={group[0]}, 組={group[2]}, 方向={group[3]}, 狀態={group[6]}")
        else:
            print(f"❌ 今日({today})沒有策略組記錄")
        
        # 3. 檢查組56的記錄
        print("3️⃣ 檢查組56的所有記錄:")
        cursor.execute('''
            SELECT id, date, group_id, direction, range_high, range_low, status, created_at
            FROM strategy_groups 
            WHERE group_id = 56
            ORDER BY id DESC
        ''', )
        
        group56_records = cursor.fetchall()
        if group56_records:
            print(f"📊 組56的記錄數量: {len(group56_records)}")
            for record in group56_records:
                print(f"   DB_ID={record[0]}, 日期={record[1]}, 組={record[2]}")
                print(f"   方向={record[3]}, 高={record[4]}, 低={record[5]}")
                print(f"   狀態={record[6]}, 建立={record[7]}")
                print()
        else:
            print("❌ 沒有組56的記錄")
        
        # 4. 檢查最近的策略組創建
        print("4️⃣ 最近創建的策略組:")
        cursor.execute('''
            SELECT id, date, group_id, direction, created_at
            FROM strategy_groups 
            ORDER BY created_at DESC
            LIMIT 10
        ''')
        
        recent_groups = cursor.fetchall()
        if recent_groups:
            print(f"📊 最近10個策略組:")
            for group in recent_groups:
                print(f"   DB_ID={group[0]}, 日期={group[1]}, 組={group[2]}, 方向={group[3]}, 建立={group[4]}")
        
        conn.close()
        
    except Exception as e:
        print(f"❌ 檢查失敗: {e}")

def check_position_group_mismatch():
    """檢查部位與策略組的不匹配情況"""
    print(f"\n5️⃣ 檢查部位與策略組不匹配...")
    
    try:
        conn = sqlite3.connect('multi_group_strategy.db', timeout=5.0)
        cursor = conn.cursor()
        
        # 查找有部位但沒有對應策略組的情況
        cursor.execute('''
            SELECT DISTINCT pr.group_id, COUNT(*) as position_count
            FROM position_records pr
            LEFT JOIN strategy_groups sg ON pr.group_id = sg.group_id AND sg.date = ?
            WHERE pr.status = 'ACTIVE' AND sg.id IS NULL
            GROUP BY pr.group_id
        ''', (date.today().isoformat(),))
        
        orphan_groups = cursor.fetchall()
        if orphan_groups:
            print(f"⚠️ 發現孤立部位 (有部位但沒有對應策略組):")
            for group_id, count in orphan_groups:
                print(f"   組{group_id}: {count}個活躍部位")
        else:
            print(f"✅ 沒有孤立部位")
        
        conn.close()
        
    except Exception as e:
        print(f"❌ 檢查孤立部位失敗: {e}")

def main():
    check_strategy_groups()
    check_position_group_mismatch()
    
    print(f"\n" + "=" * 50)
    print("📋 分析結論:")
    print("1. 如果今日沒有策略組記錄，說明策略組創建有問題")
    print("2. 如果組56存在但日期不對，說明日期匹配有問題")
    print("3. 如果完全沒有組56記錄，說明策略組創建失敗")

if __name__ == "__main__":
    main()
