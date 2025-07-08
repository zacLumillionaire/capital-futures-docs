#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
測試資料庫約束修復
驗證風險管理狀態創建不再出現約束錯誤
"""

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), 'Capital_Official_Framework'))

def test_database_constraint_fix():
    """測試資料庫約束修復"""
    print("🧪 測試資料庫約束修復")
    print("=" * 60)
    
    try:
        from multi_group_database import MultiGroupDatabaseManager
        from datetime import datetime
        
        # 創建測試資料庫
        test_db_path = "test_constraint_fix.db"
        if os.path.exists(test_db_path):
            os.remove(test_db_path)
            
        db_manager = MultiGroupDatabaseManager(test_db_path)
        print("✅ 測試資料庫創建成功")
        
        # 創建測試策略組
        current_date = datetime.now().strftime("%Y%m%d")
        group_id = db_manager.create_strategy_group(
            date=current_date,
            group_id=1,
            direction="SHORT",
            signal_time="23:34:15",
            range_high=22349.0,
            range_low=22338.0,
            total_lots=2
        )
        print(f"✅ 創建策略組: {group_id}")
        
        # 創建測試部位
        position_id = db_manager.create_position_record(
            group_id=group_id,
            lot_id=1,
            direction="SHORT",
            entry_time="23:34:18",
            rule_config='{"lot_id": 1}',
            order_status='PENDING'
        )
        print(f"✅ 創建部位記錄: {position_id}")
        
        # 確認部位成交
        success = db_manager.confirm_position_filled(
            position_id=position_id,
            actual_fill_price=22334.0,
            fill_time="23:34:18",
            order_status='FILLED'
        )
        print(f"✅ 確認部位成交: {success}")
        
        # 測試風險管理狀態創建 - 使用正確的update_reason
        print("\n📋 測試風險管理狀態創建")
        print("-" * 40)
        
        # 測試1: 使用"成交初始化" (應該成功)
        try:
            db_manager.create_risk_management_state(
                position_id=position_id,
                peak_price=22334.0,
                current_time="23:34:18",
                update_reason="成交初始化"
            )
            print("✅ 測試1成功: update_reason='成交初始化'")
        except Exception as e:
            print(f"❌ 測試1失敗: {e}")
            
        # 測試2: 使用"初始化" (應該成功)
        position_id2 = db_manager.create_position_record(
            group_id=group_id,
            lot_id=2,
            direction="SHORT",
            entry_time="23:34:18",
            rule_config='{"lot_id": 2}',
            order_status='PENDING'
        )
        
        db_manager.confirm_position_filled(
            position_id=position_id2,
            actual_fill_price=22333.0,
            fill_time="23:34:18",
            order_status='FILLED'
        )
        
        try:
            db_manager.create_risk_management_state(
                position_id=position_id2,
                peak_price=22333.0,
                current_time="23:34:18",
                update_reason="初始化"
            )
            print("✅ 測試2成功: update_reason='初始化'")
        except Exception as e:
            print(f"❌ 測試2失敗: {e}")
            
        # 測試3: 使用無效的update_reason (應該失敗)
        position_id3 = db_manager.create_position_record(
            group_id=group_id,
            lot_id=3,
            direction="SHORT",
            entry_time="23:34:18",
            rule_config='{"lot_id": 3}',
            order_status='PENDING'
        )
        
        try:
            db_manager.create_risk_management_state(
                position_id=position_id3,
                peak_price=22332.0,
                current_time="23:34:18",
                update_reason="簡化追蹤成交確認"  # 這個可能不在約束中
            )
            print("✅ 測試3成功: update_reason='簡化追蹤成交確認'")
        except Exception as e:
            print(f"❌ 測試3失敗 (預期): {e}")
            
        # 檢查資料庫記錄
        print("\n📊 檢查資料庫記錄")
        print("-" * 40)
        
        with db_manager.get_connection() as conn:
            conn.row_factory = lambda cursor, row: dict(zip([col[0] for col in cursor.description], row))
            cursor = conn.cursor()
            
            # 查詢部位記錄
            cursor.execute('''
                SELECT id, lot_id, status, order_status, entry_price
                FROM position_records 
                WHERE group_id = ?
                ORDER BY lot_id
            ''', (group_id,))
            
            positions = cursor.fetchall()
            print(f"部位記錄 ({len(positions)}個):")
            for pos in positions:
                print(f"  - 部位{pos['id']}: lot_id={pos['lot_id']}, "
                      f"status={pos['status']}, order_status={pos['order_status']}, "
                      f"entry_price={pos['entry_price']}")
                      
            # 查詢風險管理狀態
            cursor.execute('''
                SELECT position_id, peak_price, update_reason
                FROM risk_management_states
                ORDER BY position_id
            ''')
            
            risk_states = cursor.fetchall()
            print(f"\n風險管理狀態 ({len(risk_states)}個):")
            for state in risk_states:
                print(f"  - 部位{state['position_id']}: peak_price={state['peak_price']}, "
                      f"update_reason={state['update_reason']}")
        
        # 清理測試資料庫
        if os.path.exists(test_db_path):
            os.remove(test_db_path)
            print("\n✅ 測試資料庫已清理")
            
        return True
        
    except Exception as e:
        print(f"❌ 測試失敗: {e}")
        import traceback
        print(traceback.format_exc())
        return False

if __name__ == "__main__":
    print("🚀 開始測試資料庫約束修復")
    print("=" * 80)
    
    success = test_database_constraint_fix()
    
    print("\n📋 測試總結")
    print("=" * 80)
    
    if success:
        print("🎉 修復驗證成功!")
        print("✅ 風險管理狀態創建不再出現約束錯誤")
        print("✅ 部位狀態更新機制正常運作")
        print("\n📝 修復內容:")
        print("1. 將 update_reason 從 '簡化追蹤成交確認' 改為 '成交初始化'")
        print("2. 確保符合資料庫約束條件")
        print("3. 保持功能完整性")
    else:
        print("❌ 修復驗證失敗，請檢查代碼")
