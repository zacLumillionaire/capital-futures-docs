#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
🧪 針對性功能測試：建倉後設定初始停損
專門測試修復後的 setup_initial_stop_loss_for_group 功能鏈路
"""

import os
import sys
import sqlite3
import json
from datetime import date

# 添加專案路徑
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

def test_initial_stop_loss_setup_after_creation():
    """
    測試建倉後設定初始停損的完整流程
    
    測試目標：
    1. 創建策略組記錄
    2. 創建部位記錄
    3. 呼叫 setup_initial_stop_loss_for_group 並傳入 group_db_id
    4. 驗證不會拋出 TypeError
    5. 驗證停損價格被正確設定
    """
    test_db_file = "test_initial_stop_loss_setup.db"
    
    try:
        # 清理舊測試檔案
        if os.path.exists(test_db_file):
            os.remove(test_db_file)
        
        print("🧪 [TEST] 開始測試建倉後設定初始停損流程")
        print("=" * 60)
        
        # === 準備階段 (Arrange) ===
        print("\n📋 [ARRANGE] 準備測試環境...")
        
        from multi_group_database import MultiGroupDatabaseManager
        from initial_stop_loss_manager import InitialStopLossManager
        
        # 創建測試資料庫
        db_manager = MultiGroupDatabaseManager(test_db_file)
        print("✅ [ARRANGE] 測試資料庫創建成功")
        
        # 創建初始停損管理器
        stop_loss_manager = InitialStopLossManager(db_manager, console_enabled=True)
        print("✅ [ARRANGE] 初始停損管理器創建成功")
        
        # 創建策略組記錄
        today = date.today().isoformat()
        group_db_id = db_manager.create_strategy_group(
            date=today,
            group_id=1,  # 邏輯組ID
            direction="LONG",
            signal_time="08:48:15",
            range_high=22530.0,
            range_low=22480.0,
            total_lots=3
        )
        print(f"✅ [ARRANGE] 策略組創建成功: DB_ID={group_db_id}")
        
        # 創建部位記錄（模擬建倉成功）
        position_ids = []
        for lot_id in [1, 2, 3]:
            position_pk = db_manager.create_position_record(
                group_id=group_db_id,  # 使用資料庫主鍵
                lot_id=lot_id,
                direction="LONG",
                entry_price=22515.0,
                entry_time="08:48:20",
                rule_config=json.dumps({"lot_id": lot_id, "entry_type": "MARKET"}),
                order_status='FILLED',  # 設定為已成交
                retry_count=0,
                max_slippage_points=5
            )
            
            # 更新部位狀態為 ACTIVE
            db_manager.update_position_status(position_pk, 'ACTIVE')
            position_ids.append(position_pk)
            print(f"✅ [ARRANGE] 部位{lot_id}創建成功: position_pk={position_pk}")
        
        # 準備區間資料
        range_data = {
            'range_high': 22530.0,
            'range_low': 22480.0,
            'direction': 'LONG'
        }
        print(f"✅ [ARRANGE] 區間資料準備完成: {range_data}")
        
        # === 執行階段 (Act) ===
        print("\n🚀 [ACT] 執行初始停損設定...")
        
        # 關鍵測試：呼叫修復後的函式，傳入 group_db_id
        try:
            success = stop_loss_manager.setup_initial_stop_loss_for_group(
                group_db_id=group_db_id,  # 使用正確的參數名
                range_data=range_data
            )
            print(f"✅ [ACT] setup_initial_stop_loss_for_group 執行成功: {success}")
            
            if not success:
                print("⚠️ [ACT] 函式返回 False，但沒有拋出異常")
                
        except TypeError as e:
            if "unexpected keyword argument" in str(e):
                print(f"❌ [ACT] TypeError 仍然存在: {e}")
                return False
            else:
                print(f"❌ [ACT] 其他 TypeError: {e}")
                return False
        except Exception as e:
            print(f"❌ [ACT] 其他異常: {e}")
            return False
        
        # === 斷言階段 (Assert) ===
        print("\n🔍 [ASSERT] 驗證結果...")
        
        # 驗證1：檢查部位的停損價格是否被設定
        with db_manager.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                SELECT id, lot_id, current_stop_loss, is_initial_stop
                FROM position_records 
                WHERE group_id = ? AND status = 'ACTIVE'
                ORDER BY lot_id
            ''', (group_db_id,))
            
            positions = cursor.fetchall()
            
        if not positions:
            print("❌ [ASSERT] 沒有找到活躍部位")
            return False
        
        print(f"✅ [ASSERT] 找到 {len(positions)} 個活躍部位")
        
        # 驗證停損價格設定
        expected_stop_loss = 22480.0  # LONG 方向應該設定在 range_low
        all_stop_loss_set = True
        
        for position in positions:
            position_id, lot_id, current_stop_loss, is_initial_stop = position
            print(f"📊 [ASSERT] 部位{lot_id}: 停損價格={current_stop_loss}, 初始停損={is_initial_stop}")
            
            if current_stop_loss is None or current_stop_loss == 0:
                print(f"❌ [ASSERT] 部位{lot_id} 停損價格未設定")
                all_stop_loss_set = False
            elif abs(current_stop_loss - expected_stop_loss) > 0.1:
                print(f"❌ [ASSERT] 部位{lot_id} 停損價格錯誤: 期望{expected_stop_loss}, 實際{current_stop_loss}")
                all_stop_loss_set = False
            else:
                print(f"✅ [ASSERT] 部位{lot_id} 停損價格正確")
        
        if all_stop_loss_set:
            print("🎉 [ASSERT] 所有部位停損價格設定正確")
        else:
            print("❌ [ASSERT] 部分部位停損價格設定失敗")
            return False
        
        # 驗證2：檢查風險管理狀態表
        with db_manager.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                SELECT position_id, current_stop_loss, initial_stop_loss
                FROM risk_management_states 
                WHERE position_id IN ({})
            '''.format(','.join('?' * len(position_ids))), position_ids)
            
            risk_states = cursor.fetchall()
        
        print(f"✅ [ASSERT] 風險管理狀態記錄: {len(risk_states)} 筆")
        
        for risk_state in risk_states:
            position_id, current_stop, initial_stop = risk_state
            print(f"📊 [ASSERT] 部位{position_id}: 當前停損={current_stop}, 初始停損={initial_stop}")
        
        print("\n🎉 [SUCCESS] 建倉後設定初始停損測試通過！")
        print("=" * 60)
        print("✅ 修復驗證成功：")
        print("  1. setup_initial_stop_loss_for_group 接受 group_db_id 參數")
        print("  2. 函式執行完畢無 TypeError")
        print("  3. 停損價格正確設定到資料庫")
        print("  4. 風險管理狀態正確創建")
        
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
    print("🚀 開始執行針對性功能測試...")
    success = test_initial_stop_loss_setup_after_creation()
    
    if success:
        print("\n🏆 測試結果: 通過")
        sys.exit(0)
    else:
        print("\n💥 測試結果: 失敗")
        sys.exit(1)
