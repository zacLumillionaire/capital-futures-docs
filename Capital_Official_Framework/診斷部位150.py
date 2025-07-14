#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
診斷部位150平倉失敗問題
"""

import sqlite3
from datetime import date

def check_position_150():
    """檢查部位150的詳細狀態"""
    print("🔍 診斷部位150平倉失敗問題")
    print("=" * 50)
    
    try:
        # 連接資料庫
        conn = sqlite3.connect('multi_group_strategy.db', timeout=5.0)
        cursor = conn.cursor()
        
        today = date.today().isoformat()
        position_id = 150
        
        print(f"📅 檢查日期: {today}")
        print(f"🎯 目標部位: {position_id}")
        print()
        
        # 1. 檢查部位記錄是否存在
        print("1️⃣ 檢查部位記錄...")
        cursor.execute('''
            SELECT id, status, group_id, direction, entry_price, 
                   entry_time, exit_price, exit_time, created_at
            FROM position_records 
            WHERE id = ?
        ''', (position_id,))
        
        pos_row = cursor.fetchone()
        if pos_row:
            print(f"✅ 部位{position_id}記錄存在:")
            print(f"   - ID: {pos_row[0]}")
            print(f"   - 狀態: {pos_row[1]}")
            print(f"   - 組ID: {pos_row[2]}")
            print(f"   - 方向: {pos_row[3]}")
            print(f"   - 進場價: {pos_row[4]}")
            print(f"   - 進場時間: {pos_row[5]}")
            print(f"   - 出場價: {pos_row[6] if pos_row[6] else '未平倉'}")
            print(f"   - 出場時間: {pos_row[7] if pos_row[7] else '未平倉'}")
            print(f"   - 建立時間: {pos_row[8]}")
            
            group_id = pos_row[2]
            status = pos_row[1]
            
            # 2. 檢查對應的策略組
            print(f"\n2️⃣ 檢查策略組 {group_id}...")
            cursor.execute('''
                SELECT id, group_id, date, direction, range_high, range_low, status
                FROM strategy_groups 
                WHERE group_id = ? AND date = ?
                ORDER BY id DESC
            ''', (group_id, today))
            
            group_rows = cursor.fetchall()
            if group_rows:
                print(f"✅ 策略組記錄存在 ({len(group_rows)}個):")
                for i, group_row in enumerate(group_rows):
                    print(f"   [{i+1}] DB_ID={group_row[0]}, 組={group_row[1]}, 日期={group_row[2]}")
                    print(f"       方向={group_row[3]}, 高={group_row[4]}, 低={group_row[5]}, 狀態={group_row[6]}")
            else:
                print(f"❌ 策略組記錄不存在 (組{group_id}, 日期{today})")
                return
            
            # 3. 測試unified_exit_manager使用的查詢
            print(f"\n3️⃣ 測試unified_exit_manager查詢...")
            cursor.execute('''
                SELECT pr.*, sg.direction as group_direction, sg.date, sg.range_high, sg.range_low
                FROM position_records pr
                JOIN (
                    SELECT * FROM strategy_groups
                    WHERE date = ?
                    ORDER BY id DESC
                ) sg ON pr.group_id = sg.group_id
                WHERE pr.id = ?
            ''', (today, position_id))
            
            join_row = cursor.fetchone()
            if join_row:
                print(f"✅ unified_exit_manager查詢成功")
                print(f"   - 部位ID: {join_row[0]}")
                print(f"   - 狀態: {join_row[7]}")  # status欄位位置
                print(f"   - 組方向: {join_row[-4]}")  # group_direction
                print(f"   - 範圍高: {join_row[-2]}")  # range_high
                print(f"   - 範圍低: {join_row[-1]}")  # range_low
            else:
                print(f"❌ unified_exit_manager查詢失敗")
                
                # 詳細診斷失敗原因
                print(f"\n🔍 診斷失敗原因:")
                
                # 檢查狀態條件
                if status != 'ACTIVE':
                    print(f"   ⚠️ 部位狀態不是ACTIVE: {status}")
                else:
                    print(f"   ✅ 部位狀態正確: {status}")
                
                # 檢查日期條件
                cursor.execute('''
                    SELECT COUNT(*) FROM strategy_groups 
                    WHERE date = ?
                ''', (today,))
                date_count = cursor.fetchone()[0]
                print(f"   📅 今日策略組總數: {date_count}")
                
                # 檢查組ID匹配
                cursor.execute('''
                    SELECT COUNT(*) FROM strategy_groups 
                    WHERE group_id = ? AND date = ?
                ''', (group_id, today))
                group_match_count = cursor.fetchone()[0]
                print(f"   🔗 組ID匹配數: {group_match_count}")
                
                # 測試簡化查詢
                print(f"\n4️⃣ 測試簡化查詢方案...")
                cursor.execute('''
                    SELECT * FROM position_records WHERE id = ? AND status = 'ACTIVE'
                ''', (position_id,))
                simple_pos = cursor.fetchone()
                
                if simple_pos:
                    print(f"✅ 簡化部位查詢成功")
                    
                    cursor.execute('''
                        SELECT range_high, range_low, direction
                        FROM strategy_groups
                        WHERE group_id = ? AND date = ?
                        ORDER BY id DESC
                        LIMIT 1
                    ''', (group_id, today))
                    simple_group = cursor.fetchone()
                    
                    if simple_group:
                        print(f"✅ 簡化策略組查詢成功")
                        print(f"   建議: 使用分步查詢替代複雜JOIN")
                    else:
                        print(f"❌ 簡化策略組查詢失敗")
                else:
                    print(f"❌ 簡化部位查詢失敗")
        else:
            print(f"❌ 部位{position_id}記錄不存在")
        
        conn.close()
        
    except Exception as e:
        print(f"❌ 診斷失敗: {e}")

def check_all_active_positions():
    """檢查所有活躍部位"""
    print(f"\n5️⃣ 檢查所有活躍部位...")
    
    try:
        conn = sqlite3.connect('multi_group_strategy.db', timeout=5.0)
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT id, status, group_id, direction, entry_price
            FROM position_records 
            WHERE status = 'ACTIVE'
            ORDER BY id
        ''')
        
        active_positions = cursor.fetchall()
        if active_positions:
            print(f"📊 活躍部位總數: {len(active_positions)}")
            for pos in active_positions:
                print(f"   部位{pos[0]}: 狀態={pos[1]}, 組={pos[2]}, 方向={pos[3]}, 價格={pos[4]}")
        else:
            print(f"⚠️ 沒有活躍部位")
        
        conn.close()
        
    except Exception as e:
        print(f"❌ 檢查活躍部位失敗: {e}")

def main():
    check_position_150()
    check_all_active_positions()
    
    print(f"\n" + "=" * 50)
    print("📋 診斷總結:")
    print("1. 如果部位記錄存在但JOIN查詢失敗，問題在於查詢邏輯")
    print("2. 如果部位狀態不是ACTIVE，unified_exit_manager會拒絕處理")
    print("3. 如果策略組記錄不存在，JOIN會失敗")
    print("4. 建議使用分步查詢替代複雜JOIN以提高穩定性")

if __name__ == "__main__":
    main()
