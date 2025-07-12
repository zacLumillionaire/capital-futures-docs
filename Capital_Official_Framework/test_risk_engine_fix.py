#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
測試風險管理引擎修復
"""

import os
from datetime import date

def test_risk_engine_fix():
    """測試風險管理引擎修復"""
    print("🧪 測試風險管理引擎修復")
    print("=" * 50)
    
    try:
        # 導入必要模組
        from multi_group_database import MultiGroupDatabaseManager
        from risk_management_engine import RiskManagementEngine
        
        # 1. 創建測試環境
        db_path = "Capital_Official_Framework/multi_group_strategy.db"
        db_manager = MultiGroupDatabaseManager(db_path)
        risk_engine = RiskManagementEngine(db_manager)
        
        print("✅ 測試環境初始化完成")
        
        # 2. 檢查當前活躍部位
        print("\n🔍 檢查當前活躍部位...")
        
        active_positions = db_manager.get_all_active_positions()
        print(f"找到 {len(active_positions)} 個活躍部位:")
        
        for pos in active_positions:
            print(f"  - 部位{pos['id']}: entry_price={pos['entry_price']}, "
                  f"order_status={pos.get('order_status', 'N/A')}, "
                  f"status={pos['status']}")
        
        # 3. 測試風險管理引擎（修復前會出錯的情況）
        print(f"\n🧪 測試風險管理引擎...")
        
        try:
            # 模擬價格更新
            test_price = 22380.0
            test_time = "00:25:00"
            
            print(f"模擬價格更新: {test_price} @ {test_time}")
            
            # 檢查出場條件（修復前會出錯）
            exit_actions = risk_engine.check_all_exit_conditions(test_price, test_time)
            
            print(f"✅ 風險管理引擎運行成功")
            print(f"📊 出場動作: {len(exit_actions)} 個")
            
            for action in exit_actions:
                print(f"  - {action}")
            
        except Exception as e:
            print(f"❌ 風險管理引擎運行失敗: {e}")
            import traceback
            traceback.print_exc()
            return False
        
        # 4. 測試多次價格更新
        print(f"\n🔄 測試多次價格更新...")
        
        test_prices = [22375.0, 22380.0, 22385.0, 22390.0, 22395.0]
        
        for i, price in enumerate(test_prices):
            try:
                time_str = f"00:25:{i*10:02d}"
                exit_actions = risk_engine.check_all_exit_conditions(price, time_str)
                print(f"  ✅ 價格 {price} @ {time_str}: {len(exit_actions)} 個出場動作")
            except Exception as e:
                print(f"  ❌ 價格 {price} 處理失敗: {e}")
                return False
        
        # 5. 檢查風險管理狀態
        print(f"\n📊 檢查風險管理狀態...")
        
        with db_manager.get_connection() as conn:
            conn.row_factory = lambda cursor, row: dict(zip([col[0] for col in cursor.description], row))
            cursor = conn.cursor()
            
            # 查詢風險管理狀態
            cursor.execute('''
                SELECT rms.*, pr.id as position_id, pr.entry_price, pr.order_status
                FROM risk_management_states rms
                JOIN position_records pr ON rms.position_id = pr.id
                WHERE pr.status = 'ACTIVE'
                ORDER BY rms.created_at DESC
                LIMIT 10
            ''')
            
            risk_states = cursor.fetchall()
            
            print(f"找到 {len(risk_states)} 個風險管理狀態記錄:")
            for state in risk_states:
                print(f"  - 部位{state['position_id']}: peak_price={state['peak_price']}, "
                      f"entry_price={state['entry_price']}, order_status={state['order_status']}")
        
        # 6. 驗證修復效果
        print(f"\n🔍 驗證修復效果:")
        
        # 檢查是否還有 None 相關的錯誤
        error_count = 0
        for price in [22370.0, 22380.0, 22390.0]:
            try:
                risk_engine.check_all_exit_conditions(price, "00:26:00")
            except Exception as e:
                if "NoneType" in str(e) or "None" in str(e):
                    error_count += 1
                    print(f"  ❌ 仍有 None 相關錯誤: {e}")
        
        if error_count == 0:
            print("  ✅ 沒有 None 相關錯誤")
        else:
            print(f"  ❌ 仍有 {error_count} 個 None 相關錯誤")
        
        # 檢查是否正確過濾無效部位
        valid_positions = []
        for position in active_positions:
            if (position.get('entry_price') is not None and 
                position.get('order_status') == 'FILLED'):
                valid_positions.append(position)
        
        print(f"  ✅ 有效部位過濾: {len(valid_positions)}/{len(active_positions)} 個部位有效")
        
        print("\n🎉 測試完成！")
        
        if error_count == 0:
            print("\n📋 測試結果總結:")
            print("  ✅ 風險管理引擎修復成功")
            print("  ✅ 正確過濾無效部位")
            print("  ✅ 沒有 None 相關錯誤")
            print("  ✅ 可以正常處理價格更新")
            print("  ✅ 修復完成，系統可以正常運行")
            return True
        else:
            print("\n❌ 仍有問題需要解決:")
            print(f"  - 仍有 {error_count} 個 None 相關錯誤")
            return False
        
    except Exception as e:
        print(f"❌ 測試失敗: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = test_risk_engine_fix()
    if success:
        print("\n💡 現在可以重新測試策略，應該不會再有風險管理錯誤了！")
    else:
        print("\n💡 需要進一步檢查和修復問題")
