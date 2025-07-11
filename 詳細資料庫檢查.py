#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
詳細資料庫檢查 - 分析平倉問題的根本原因
"""

import sqlite3
from datetime import date

def check_join_query():
    """檢查JOIN查詢邏輯"""
    print("🔍 檢查JOIN查詢邏輯...")
    
    try:
        conn = sqlite3.connect('Capital_Official_Framework/multi_group_strategy.db')
        cursor = conn.cursor()
        
        today = date.today().isoformat()
        problem_positions = [133, 134, 135]
        
        for position_id in problem_positions:
            print(f"\n📊 部位{position_id}詳細檢查:")
            
            # 1. 檢查部位記錄
            cursor.execute('''
                SELECT id, status, group_id, direction, entry_price, created_at
                FROM position_records 
                WHERE id = ?
            ''', (position_id,))
            
            pos_row = cursor.fetchone()
            if pos_row:
                print(f"  ✅ 部位記錄存在:")
                print(f"    - ID: {pos_row[0]}")
                print(f"    - 狀態: {pos_row[1]}")
                print(f"    - 組ID: {pos_row[2]}")
                print(f"    - 方向: {pos_row[3]}")
                print(f"    - 進場價: {pos_row[4]}")
                print(f"    - 建立時間: {pos_row[5]}")
                
                group_id = pos_row[2]
                
                # 2. 檢查對應的策略組
                cursor.execute('''
                    SELECT id, group_id, date, direction, range_high, range_low
                    FROM strategy_groups 
                    WHERE group_id = ? AND date = ?
                    ORDER BY id DESC
                ''', (group_id, today))
                
                group_rows = cursor.fetchall()
                if group_rows:
                    print(f"  ✅ 策略組記錄存在 ({len(group_rows)}個):")
                    for i, group_row in enumerate(group_rows):
                        print(f"    [{i+1}] ID={group_row[0]}, 組={group_row[1]}, 日期={group_row[2]}")
                        print(f"        方向={group_row[3]}, 高={group_row[4]}, 低={group_row[5]}")
                else:
                    print(f"  ❌ 策略組記錄不存在 (組{group_id}, 日期{today})")
                
                # 3. 測試完整的JOIN查詢
                cursor.execute('''
                    SELECT pr.id, pr.status, pr.group_id, 
                           sg.range_high, sg.range_low, sg.direction as group_direction
                    FROM position_records pr
                    JOIN (
                        SELECT * FROM strategy_groups
                        WHERE date = ?
                        ORDER BY id DESC
                    ) sg ON pr.group_id = sg.group_id
                    WHERE pr.id = ? AND pr.status = 'ACTIVE'
                ''', (today, position_id))
                
                join_row = cursor.fetchone()
                if join_row:
                    print(f"  ✅ JOIN查詢成功:")
                    print(f"    - 部位ID: {join_row[0]}")
                    print(f"    - 狀態: {join_row[1]}")
                    print(f"    - 組ID: {join_row[2]}")
                    print(f"    - 範圍高: {join_row[3]}")
                    print(f"    - 範圍低: {join_row[4]}")
                    print(f"    - 組方向: {join_row[5]}")
                else:
                    print(f"  ❌ JOIN查詢失敗")
                    
                    # 分步診斷JOIN失敗原因
                    print(f"  🔍 JOIN失敗診斷:")
                    
                    # 檢查狀態條件
                    if pos_row[1] != 'ACTIVE':
                        print(f"    - 狀態不符: {pos_row[1]} != 'ACTIVE'")
                    
                    # 檢查日期條件
                    cursor.execute('''
                        SELECT COUNT(*) FROM strategy_groups 
                        WHERE date = ?
                    ''', (today,))
                    date_count = cursor.fetchone()[0]
                    print(f"    - 今日策略組總數: {date_count}")
                    
                    # 檢查組ID匹配
                    cursor.execute('''
                        SELECT COUNT(*) FROM strategy_groups 
                        WHERE group_id = ? AND date = ?
                    ''', (group_id, today))
                    group_match_count = cursor.fetchone()[0]
                    print(f"    - 組ID匹配數: {group_match_count}")
                    
            else:
                print(f"  ❌ 部位記錄不存在")
        
        conn.close()
        
    except Exception as e:
        print(f"❌ JOIN查詢檢查失敗: {e}")

def check_strategy_groups():
    """檢查策略組狀態"""
    print("\n🔍 檢查策略組狀態...")
    
    try:
        conn = sqlite3.connect('Capital_Official_Framework/multi_group_strategy.db')
        cursor = conn.cursor()
        
        today = date.today().isoformat()
        
        # 檢查今日所有策略組
        cursor.execute('''
            SELECT id, group_id, date, direction, range_high, range_low
            FROM strategy_groups 
            WHERE date = ?
            ORDER BY id DESC
        ''', (today,))
        
        groups = cursor.fetchall()
        print(f"📊 今日策略組 ({len(groups)}個):")
        
        for group in groups:
            print(f"  組{group[1]}: ID={group[0]}, 方向={group[3]}, 高={group[4]}, 低={group[5]}")
        
        # 特別檢查組49
        cursor.execute('''
            SELECT * FROM strategy_groups 
            WHERE group_id = 49 AND date = ?
        ''', (today,))
        
        group_49 = cursor.fetchall()
        if group_49:
            print(f"\n📊 組49詳細信息:")
            for row in group_49:
                print(f"  {row}")
        else:
            print(f"\n❌ 組49在今日不存在")
        
        conn.close()
        
    except Exception as e:
        print(f"❌ 策略組檢查失敗: {e}")

def check_database_performance():
    """檢查資料庫性能"""
    print("\n🔍 檢查資料庫性能...")
    
    try:
        import time
        conn = sqlite3.connect('Capital_Official_Framework/multi_group_strategy.db', timeout=5.0)
        cursor = conn.cursor()
        
        today = date.today().isoformat()
        
        # 測試查詢性能
        for position_id in [133, 134, 135]:
            start_time = time.time()
            
            cursor.execute('''
                SELECT pr.*, sg.range_high, sg.range_low, sg.direction as group_direction
                FROM position_records pr
                JOIN (
                    SELECT * FROM strategy_groups
                    WHERE date = ?
                    ORDER BY id DESC
                ) sg ON pr.group_id = sg.group_id
                WHERE pr.id = ? AND pr.status = 'ACTIVE'
            ''', (today, position_id))
            
            result = cursor.fetchone()
            elapsed = (time.time() - start_time) * 1000
            
            print(f"  部位{position_id}: {elapsed:.1f}ms {'成功' if result else '失敗'}")
            
            if elapsed > 100:
                print(f"    ⚠️ 查詢延遲過高: {elapsed:.1f}ms")
        
        conn.close()
        
    except Exception as e:
        print(f"❌ 性能檢查失敗: {e}")

def main():
    print("🚨 詳細資料庫檢查 - 平倉問題診斷")
    print("=" * 60)
    
    check_join_query()
    check_strategy_groups()
    check_database_performance()
    
    print("\n" + "=" * 60)
    print("📋 診斷總結:")
    print("1. 如果JOIN查詢失敗，問題在於查詢邏輯")
    print("2. 如果策略組不存在，問題在於資料不一致")
    print("3. 如果查詢延遲過高，問題在於性能")
    print("4. 如果部位狀態不是ACTIVE，問題在於狀態管理")

if __name__ == "__main__":
    main()
