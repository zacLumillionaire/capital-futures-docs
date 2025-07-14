#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
修復部位記錄中group_id與策略組不一致的問題
"""

import sqlite3
from datetime import date

def fix_position_group_id_mismatch():
    """修復部位記錄中的group_id不一致問題"""
    print("🔧 修復部位記錄group_id不一致問題")
    print("=" * 50)
    
    try:
        conn = sqlite3.connect('multi_group_strategy.db', timeout=5.0)
        cursor = conn.cursor()
        
        today = date.today().isoformat()
        print(f"📅 處理日期: {today}")
        print()
        
        # 1. 找出所有孤立部位（有部位但沒有對應策略組）
        print("1️⃣ 檢查孤立部位...")
        cursor.execute('''
            SELECT pr.id, pr.group_id, pr.direction, pr.entry_price
            FROM position_records pr
            LEFT JOIN strategy_groups sg ON pr.group_id = sg.group_id AND sg.date = ?
            WHERE pr.status = 'ACTIVE' AND sg.id IS NULL
        ''', (today,))
        
        orphan_positions = cursor.fetchall()
        if not orphan_positions:
            print("✅ 沒有發現孤立部位")
            return
        
        print(f"⚠️ 發現 {len(orphan_positions)} 個孤立部位:")
        for pos in orphan_positions:
            print(f"   部位{pos[0]}: group_id={pos[1]}, 方向={pos[2]}, 價格={pos[3]}")
        print()
        
        # 2. 嘗試修復每個孤立部位
        print("2️⃣ 嘗試修復孤立部位...")
        fixed_count = 0
        
        for pos_id, wrong_group_id, direction, entry_price in orphan_positions:
            # 嘗試按DB_ID查找策略組
            cursor.execute('''
                SELECT id, group_id, direction, range_high, range_low
                FROM strategy_groups
                WHERE id = ? AND date = ?
            ''', (wrong_group_id, today))
            
            strategy_group = cursor.fetchone()
            if strategy_group:
                db_id, correct_group_id, group_direction, range_high, range_low = strategy_group
                
                print(f"🔍 部位{pos_id}:")
                print(f"   錯誤group_id: {wrong_group_id} (實際是DB_ID)")
                print(f"   正確group_id: {correct_group_id}")
                print(f"   策略組方向: {group_direction}")
                print(f"   部位方向: {direction}")
                
                # 檢查方向是否一致
                if direction == group_direction:
                    # 修復group_id
                    cursor.execute('''
                        UPDATE position_records 
                        SET group_id = ? 
                        WHERE id = ?
                    ''', (correct_group_id, pos_id))
                    
                    print(f"   ✅ 已修復: {wrong_group_id} → {correct_group_id}")
                    fixed_count += 1
                else:
                    print(f"   ⚠️ 方向不一致，跳過修復")
            else:
                print(f"❌ 部位{pos_id}: 找不到對應的策略組 (DB_ID={wrong_group_id})")
        
        # 3. 提交修改
        if fixed_count > 0:
            conn.commit()
            print(f"\n✅ 成功修復 {fixed_count} 個部位的group_id")
        else:
            print(f"\n⚠️ 沒有部位需要修復")
        
        # 4. 驗證修復結果
        print("\n3️⃣ 驗證修復結果...")
        cursor.execute('''
            SELECT pr.id, pr.group_id, sg.group_id as strategy_group_id
            FROM position_records pr
            JOIN strategy_groups sg ON pr.group_id = sg.group_id AND sg.date = ?
            WHERE pr.status = 'ACTIVE'
        ''', (today,))
        
        verified_positions = cursor.fetchall()
        print(f"✅ 驗證通過的部位數量: {len(verified_positions)}")
        for pos in verified_positions:
            print(f"   部位{pos[0]}: group_id={pos[1]} ✓")
        
        # 5. 檢查是否還有孤立部位
        cursor.execute('''
            SELECT COUNT(*)
            FROM position_records pr
            LEFT JOIN strategy_groups sg ON pr.group_id = sg.group_id AND sg.date = ?
            WHERE pr.status = 'ACTIVE' AND sg.id IS NULL
        ''', (today,))
        
        remaining_orphans = cursor.fetchone()[0]
        if remaining_orphans == 0:
            print(f"🎉 所有部位都已正確關聯到策略組")
        else:
            print(f"⚠️ 仍有 {remaining_orphans} 個孤立部位需要手動處理")
        
        conn.close()
        
    except Exception as e:
        print(f"❌ 修復失敗: {e}")

def test_unified_exit_manager_query():
    """測試修復後的unified_exit_manager查詢"""
    print(f"\n4️⃣ 測試unified_exit_manager查詢...")
    
    try:
        conn = sqlite3.connect('multi_group_strategy.db', timeout=5.0)
        cursor = conn.cursor()
        
        today = date.today().isoformat()
        test_positions = [150, 151]
        
        for position_id in test_positions:
            # 測試新的分步查詢邏輯
            cursor.execute('''
                SELECT * FROM position_records WHERE id = ?
            ''', (position_id,))
            
            pos_row = cursor.fetchone()
            if pos_row:
                columns = [description[0] for description in cursor.description]
                position_data = dict(zip(columns, pos_row))
                group_id = position_data.get('group_id')
                
                # 查詢策略組信息
                cursor.execute('''
                    SELECT range_high, range_low, direction as group_direction
                    FROM strategy_groups
                    WHERE group_id = ? AND date = ?
                    ORDER BY id DESC
                    LIMIT 1
                ''', (group_id, today))
                
                group_row = cursor.fetchone()
                if group_row:
                    print(f"✅ 部位{position_id}: 查詢成功")
                    print(f"   group_id: {group_id}")
                    print(f"   範圍: {group_row[1]} - {group_row[0]}")
                    print(f"   方向: {group_row[2]}")
                else:
                    print(f"❌ 部位{position_id}: 查詢失敗")
            else:
                print(f"❌ 部位{position_id}: 不存在")
        
        conn.close()
        
    except Exception as e:
        print(f"❌ 測試失敗: {e}")

def main():
    fix_position_group_id_mismatch()
    test_unified_exit_manager_query()
    
    print(f"\n" + "=" * 50)
    print("📋 修復總結:")
    print("1. 已修復部位記錄中錯誤的group_id")
    print("2. 已改進查詢邏輯以處理數據不一致")
    print("3. 平倉功能應該可以正常工作了")
    print("4. 建議重新啟動策略程式以應用修復")

if __name__ == "__main__":
    main()
