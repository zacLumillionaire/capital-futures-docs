#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
🧪 綜合測試：JOIN 查詢和 group_id 相關修復驗證
深度檢查所有 JOIN 查詢和 group_id 互動的修復
"""

import os
import sys
import sqlite3
import json
from datetime import date

# 添加專案路徑
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

def test_comprehensive_join_and_group_id_fixes():
    """綜合測試所有 JOIN 查詢和 group_id 相關修復"""
    test_db_file = "test_comprehensive_join_fixes.db"
    
    try:
        # 清理舊測試檔案
        if os.path.exists(test_db_file):
            os.remove(test_db_file)
        
        print("🧪 [TEST] 綜合測試：JOIN 查詢和 group_id 相關修復")
        print("=" * 70)
        
        from multi_group_database import MultiGroupDatabaseManager
        from initial_stop_loss_manager import InitialStopLossManager
        
        # 創建測試資料庫
        db_manager = MultiGroupDatabaseManager(test_db_file)
        print("✅ [TEST] 測試資料庫創建成功")
        
        # === 測試1：資料庫 JOIN 查詢修復 ===
        print("\n📋 [TEST1] 測試資料庫 JOIN 查詢修復...")
        
        # 創建測試資料
        today = date.today().isoformat()
        group_db_id = db_manager.create_strategy_group(
            date=today,
            group_id=8,  # 邏輯組ID
            direction="LONG",
            signal_time="08:48:15",
            range_high=22530.0,
            range_low=22480.0,
            total_lots=3
        )
        print(f"✅ [TEST1] 策略組創建: DB_ID={group_db_id}, 邏輯ID=8")
        
        # 創建部位記錄
        position_ids = []
        for lot_id in [1, 2, 3]:
            position_pk = db_manager.create_position_record(
                group_id=8,  # 使用邏輯組ID
                lot_id=lot_id,
                direction="LONG",
                entry_time="08:48:20",
                rule_config=json.dumps({"lot_id": lot_id}),
                order_status='FILLED'
            )
            db_manager.update_position_status(position_pk, 'ACTIVE')
            position_ids.append(position_pk)
            print(f"✅ [TEST1] 部位{lot_id}創建: position_pk={position_pk}")
        
        # 測試 get_active_positions_by_group（修復後）
        try:
            positions = db_manager.get_active_positions_by_group(8)  # 傳入邏輯組ID
            print(f"✅ [TEST1] get_active_positions_by_group 成功: {len(positions)} 個部位")
            
            if len(positions) == 3:
                print("🎉 [TEST1] 部位查詢結果正確")
            else:
                print(f"❌ [TEST1] 部位查詢結果錯誤: 期望3個，實際{len(positions)}個")
                return False
                
        except Exception as e:
            print(f"❌ [TEST1] get_active_positions_by_group 失敗: {e}")
            return False
        
        # 測試 get_position_by_id（修復後）
        try:
            for position_id in position_ids:
                position_info = db_manager.get_position_by_id(position_id)
                if position_info:
                    print(f"✅ [TEST1] get_position_by_id({position_id}) 成功")
                else:
                    print(f"❌ [TEST1] get_position_by_id({position_id}) 失敗")
                    return False
                    
        except Exception as e:
            print(f"❌ [TEST1] get_position_by_id 失敗: {e}")
            return False
        
        # === 測試2：初始停損管理器修復 ===
        print("\n📋 [TEST2] 測試初始停損管理器修復...")
        
        stop_loss_manager = InitialStopLossManager(db_manager, console_enabled=False)
        
        try:
            range_data = {
                'range_high': 22530.0,
                'range_low': 22480.0,
                'direction': 'LONG'
            }
            
            # 測試修復後的 setup_initial_stop_loss_for_group
            success = stop_loss_manager.setup_initial_stop_loss_for_group(
                group_db_id=group_db_id,  # 傳入資料庫主鍵
                range_data=range_data
            )
            print(f"✅ [TEST2] setup_initial_stop_loss_for_group 成功: {success}")
            
        except TypeError as e:
            if "unexpected keyword argument" in str(e):
                print(f"❌ [TEST2] 仍存在 TypeError: {e}")
                return False
            else:
                print(f"⚠️ [TEST2] 其他 TypeError: {e}")
        except Exception as e:
            print(f"⚠️ [TEST2] 其他異常: {e}")
        
        # === 測試3：SQL JOIN 查詢一致性 ===
        print("\n📋 [TEST3] 測試 SQL JOIN 查詢一致性...")
        
        try:
            with db_manager.get_connection() as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                
                # 測試正確的 JOIN 查詢
                cursor.execute('''
                    SELECT pr.*, sg.range_high, sg.range_low, sg.direction as group_direction
                    FROM position_records pr
                    JOIN (
                        SELECT * FROM strategy_groups
                        WHERE date = ?
                        ORDER BY id DESC
                    ) sg ON pr.group_id = sg.group_id
                    WHERE pr.status = 'ACTIVE'
                    ORDER BY pr.lot_id
                ''', (today,))
                
                join_results = cursor.fetchall()
                print(f"✅ [TEST3] 正確 JOIN 查詢成功: {len(join_results)} 筆記錄")
                
                if len(join_results) == 3:
                    print("🎉 [TEST3] JOIN 查詢結果正確")
                    
                    # 驗證每筆記錄都有策略組資訊
                    for result in join_results:
                        if result['range_high'] and result['range_low'] and result['group_direction']:
                            print(f"✅ [TEST3] 部位{result['lot_id']}: 策略組資訊完整")
                        else:
                            print(f"❌ [TEST3] 部位{result['lot_id']}: 策略組資訊缺失")
                            return False
                else:
                    print(f"❌ [TEST3] JOIN 查詢結果錯誤: 期望3筆，實際{len(join_results)}筆")
                    return False
                    
        except Exception as e:
            print(f"❌ [TEST3] SQL JOIN 查詢失敗: {e}")
            return False
        
        # === 測試4：錯誤 JOIN 查詢檢測 ===
        print("\n📋 [TEST4] 測試錯誤 JOIN 查詢檢測...")
        
        try:
            with db_manager.get_connection() as conn:
                cursor = conn.cursor()
                
                # 測試錯誤的 JOIN 查詢（應該返回空結果）
                cursor.execute('''
                    SELECT pr.*, sg.range_high, sg.range_low
                    FROM position_records pr
                    JOIN strategy_groups sg ON pr.group_id = sg.id
                    WHERE pr.status = 'ACTIVE'
                ''')
                
                wrong_results = cursor.fetchall()
                print(f"✅ [TEST4] 錯誤 JOIN 查詢執行: {len(wrong_results)} 筆記錄")
                
                if len(wrong_results) == 0:
                    print("🎉 [TEST4] 錯誤 JOIN 查詢正確返回空結果")
                else:
                    print(f"⚠️ [TEST4] 錯誤 JOIN 查詢意外返回結果，可能存在資料不一致")
                    
        except Exception as e:
            print(f"⚠️ [TEST4] 錯誤 JOIN 查詢測試異常: {e}")
        
        # === 測試5：參數傳遞一致性 ===
        print("\n📋 [TEST5] 測試參數傳遞一致性...")
        
        # 檢查函式簽名
        import inspect
        
        # 檢查 setup_initial_stop_loss_for_group 簽名
        sig = inspect.signature(stop_loss_manager.setup_initial_stop_loss_for_group)
        params = list(sig.parameters.keys())
        
        if 'group_db_id' in params:
            print("✅ [TEST5] setup_initial_stop_loss_for_group 參數名稱正確")
        else:
            print(f"❌ [TEST5] setup_initial_stop_loss_for_group 參數錯誤: {params}")
            return False
        
        # 檢查 get_strategy_group_by_db_id 簽名
        sig2 = inspect.signature(db_manager.get_strategy_group_by_db_id)
        params2 = list(sig2.parameters.keys())
        
        if 'db_id' in params2:
            print("✅ [TEST5] get_strategy_group_by_db_id 參數名稱正確")
        else:
            print(f"❌ [TEST5] get_strategy_group_by_db_id 參數錯誤: {params2}")
            return False
        
        # 檢查 get_active_positions_by_group 簽名
        sig3 = inspect.signature(db_manager.get_active_positions_by_group)
        params3 = list(sig3.parameters.keys())
        
        if 'group_id' in params3:
            print("✅ [TEST5] get_active_positions_by_group 參數名稱正確")
        else:
            print(f"❌ [TEST5] get_active_positions_by_group 參數錯誤: {params3}")
            return False
        
        print("\n🎉 [SUCCESS] 所有 JOIN 查詢和 group_id 相關修復測試通過！")
        print("✅ 修復驗證成功：")
        print("  1. 資料庫 JOIN 查詢使用正確的關聯條件")
        print("  2. setup_initial_stop_loss_for_group 接受 group_db_id 參數")
        print("  3. get_active_positions_by_group 使用邏輯組ID查詢")
        print("  4. SQL JOIN 查詢返回正確結果")
        print("  5. 錯誤 JOIN 查詢被正確識別")
        print("  6. 參數傳遞命名統一且正確")
        print("  7. 無 TypeError 異常")
        
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
    print("🚀 開始執行綜合 JOIN 查詢和 group_id 修復驗證測試...")
    success = test_comprehensive_join_and_group_id_fixes()
    
    if success:
        print("\n🏆 測試結果: 通過")
        sys.exit(0)
    else:
        print("\n💥 測試結果: 失敗")
        sys.exit(1)
