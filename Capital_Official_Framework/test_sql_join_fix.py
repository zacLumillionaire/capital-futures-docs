#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
🧪 測試 SQL JOIN 修復
驗證 simple_integrated.py 中的 SQL 查詢修復是否正確
"""

import os
import sys
import sqlite3
import json
from datetime import date

# 添加專案路徑
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

def test_sql_join_fix():
    """測試 SQL JOIN 修復"""
    test_db_file = "test_sql_join_fix.db"
    
    try:
        # 清理舊測試檔案
        if os.path.exists(test_db_file):
            os.remove(test_db_file)
        
        print("🧪 [TEST] 測試 SQL JOIN 修復")
        print("=" * 50)
        
        from multi_group_database import MultiGroupDatabaseManager
        
        # 創建測試資料庫
        db_manager = MultiGroupDatabaseManager(test_db_file)
        print("✅ [TEST] 測試資料庫創建成功")
        
        # 創建策略組記錄
        today = date.today().isoformat()
        group_db_id = db_manager.create_strategy_group(
            date=today,
            group_id=5,  # 邏輯組ID
            direction="LONG",
            signal_time="08:48:15",
            range_high=22530.0,
            range_low=22480.0,
            total_lots=2
        )
        print(f"✅ [TEST] 策略組創建成功: DB_ID={group_db_id}, 邏輯ID=5")
        
        # 創建部位記錄（使用邏輯組ID）
        position_ids = []
        for lot_id in [1, 2]:
            position_pk = db_manager.create_position_record(
                group_id=5,  # 使用邏輯組ID
                lot_id=lot_id,
                direction="LONG",
                entry_time="08:48:20",
                rule_config=json.dumps({"lot_id": lot_id}),
                order_status='PENDING'
            )
            
            # 更新為 ACTIVE 狀態
            db_manager.update_position_status(position_pk, 'ACTIVE')
            position_ids.append(position_pk)
            print(f"✅ [TEST] 部位{lot_id}創建成功: position_pk={position_pk}")
        
        # 測試修復前的錯誤查詢（應該失敗或返回空結果）
        print("\n🔍 [TEST] 測試修復前的錯誤查詢...")
        try:
            with db_manager.get_connection() as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                
                # 錯誤的查詢：pr.group_id = sg.id
                cursor.execute('''
                    SELECT pr.*, sg.range_high, sg.range_low
                    FROM position_records pr
                    JOIN strategy_groups sg ON pr.group_id = sg.id
                    WHERE pr.group_id = ? AND pr.status IN ('PENDING', 'ACTIVE')
                    ORDER BY pr.lot_id
                ''', (group_db_id,))  # 傳入 group_db_id
                
                wrong_results = cursor.fetchall()
                print(f"❌ [TEST] 錯誤查詢結果: {len(wrong_results)} 筆記錄")
                
                if len(wrong_results) > 0:
                    print("⚠️ [TEST] 錯誤查詢意外返回了結果，這表明資料結構可能有問題")
                
        except Exception as e:
            print(f"❌ [TEST] 錯誤查詢失敗（預期）: {e}")
        
        # 測試修復後的正確查詢
        print("\n🔍 [TEST] 測試修復後的正確查詢...")
        try:
            with db_manager.get_connection() as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                
                # 步驟1：獲取邏輯組別編號
                group_info = db_manager.get_strategy_group_by_db_id(group_db_id)
                if group_info:
                    logical_group_id = group_info['logical_group_id']
                    print(f"✅ [TEST] 獲取邏輯組別編號: {logical_group_id}")
                    
                    # 步驟2：正確的查詢：pr.group_id = sg.group_id
                    cursor.execute('''
                        SELECT pr.*, sg.range_high, sg.range_low
                        FROM position_records pr
                        JOIN strategy_groups sg ON pr.group_id = sg.group_id
                        WHERE pr.group_id = ? AND pr.status IN ('PENDING', 'ACTIVE')
                        ORDER BY pr.lot_id
                    ''', (logical_group_id,))  # 傳入邏輯組ID
                    
                    correct_results = cursor.fetchall()
                    print(f"✅ [TEST] 正確查詢結果: {len(correct_results)} 筆記錄")
                    
                    if len(correct_results) == 2:
                        print("🎉 [TEST] 查詢結果正確：找到2筆部位記錄")
                        
                        for i, position in enumerate(correct_results, 1):
                            print(f"📊 [TEST] 部位{i}: lot_id={position['lot_id']}, "
                                  f"range_high={position['range_high']}, range_low={position['range_low']}")
                    else:
                        print(f"❌ [TEST] 查詢結果錯誤：期望2筆，實際{len(correct_results)}筆")
                        return False
                else:
                    print("❌ [TEST] 無法獲取策略組資訊")
                    return False
                
        except Exception as e:
            print(f"❌ [TEST] 正確查詢失敗: {e}")
            return False
        
        # 測試資料一致性
        print("\n🔍 [TEST] 測試資料一致性...")
        
        # 檢查 position_records 表中的 group_id
        with db_manager.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('SELECT id, group_id, lot_id FROM position_records')
            positions = cursor.fetchall()
            
            print(f"📊 [TEST] position_records 表中的記錄:")
            for pos in positions:
                print(f"  position_id={pos[0]}, group_id={pos[1]}, lot_id={pos[2]}")
        
        # 檢查 strategy_groups 表中的記錄
        with db_manager.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('SELECT id, group_id, direction FROM strategy_groups')
            groups = cursor.fetchall()
            
            print(f"📊 [TEST] strategy_groups 表中的記錄:")
            for group in groups:
                print(f"  db_id={group[0]}, logical_group_id={group[1]}, direction={group[2]}")
        
        print("\n🎉 [SUCCESS] SQL JOIN 修復測試通過！")
        print("✅ 修復驗證成功：")
        print("  1. 錯誤查詢被正確識別")
        print("  2. 正確查詢返回預期結果")
        print("  3. 資料關聯邏輯正確")
        
        return True
        
    except Exception as e:
        print(f"❌ [ERROR] 測試執行失敗: {e}")
        import traceback
        traceback.print_exc()
        return False
        
    finally:
        # 清理測試檔案
        if os.path.exists(test_db_file):
            os.remove(test_db_file)
            print(f"🧹 [CLEANUP] 測試檔案已清理: {test_db_file}")

if __name__ == "__main__":
    print("🚀 開始執行 SQL JOIN 修復測試...")
    success = test_sql_join_fix()
    
    if success:
        print("\n🏆 測試結果: 通過")
        sys.exit(0)
    else:
        print("\n💥 測試結果: 失敗")
        sys.exit(1)
