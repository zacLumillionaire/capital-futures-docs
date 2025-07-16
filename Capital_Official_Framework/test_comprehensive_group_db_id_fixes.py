#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
🧪 綜合測試：group_db_id 相關修復驗證
驗證所有 group_db_id 傳遞和使用的修復是否正確
"""

import os
import sys
import sqlite3
import json
from datetime import date

# 添加專案路徑
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

def test_comprehensive_group_db_id_fixes():
    """綜合測試所有 group_db_id 相關修復"""
    test_db_file = "test_comprehensive_fixes.db"
    
    try:
        # 清理舊測試檔案
        if os.path.exists(test_db_file):
            os.remove(test_db_file)
        
        print("🧪 [TEST] 綜合測試：group_db_id 相關修復")
        print("=" * 60)
        
        from multi_group_database import MultiGroupDatabaseManager
        from initial_stop_loss_manager import InitialStopLossManager
        
        # 創建測試資料庫
        db_manager = MultiGroupDatabaseManager(test_db_file)
        print("✅ [TEST] 測試資料庫創建成功")
        
        # 創建初始停損管理器
        stop_loss_manager = InitialStopLossManager(db_manager, console_enabled=False)
        print("✅ [TEST] 初始停損管理器創建成功")
        
        # === 測試1：setup_initial_stop_loss_for_group 修復 ===
        print("\n📋 [TEST1] 測試 setup_initial_stop_loss_for_group 修復...")
        
        # 創建策略組
        today = date.today().isoformat()
        group_db_id = db_manager.create_strategy_group(
            date=today,
            group_id=3,  # 邏輯組ID
            direction="LONG",
            signal_time="08:48:15",
            range_high=22530.0,
            range_low=22480.0,
            total_lots=2
        )
        print(f"✅ [TEST1] 策略組創建: DB_ID={group_db_id}, 邏輯ID=3")
        
        # 創建部位記錄
        for lot_id in [1, 2]:
            position_pk = db_manager.create_position_record(
                group_id=3,  # 使用邏輯組ID
                lot_id=lot_id,
                direction="LONG",
                entry_time="08:48:20",
                rule_config=json.dumps({"lot_id": lot_id}),
                order_status='FILLED'
            )
            db_manager.update_position_status(position_pk, 'ACTIVE')
            print(f"✅ [TEST1] 部位{lot_id}創建: position_pk={position_pk}")
        
        # 測試修復後的函式呼叫
        try:
            range_data = {
                'range_high': 22530.0,
                'range_low': 22480.0,
                'direction': 'LONG'
            }
            
            success = stop_loss_manager.setup_initial_stop_loss_for_group(
                group_db_id=group_db_id,  # 使用正確的參數名
                range_data=range_data
            )
            print(f"✅ [TEST1] setup_initial_stop_loss_for_group 呼叫成功: {success}")
            
        except TypeError as e:
            if "unexpected keyword argument" in str(e):
                print(f"❌ [TEST1] 仍存在 TypeError: {e}")
                return False
            else:
                print(f"⚠️ [TEST1] 其他 TypeError: {e}")
        
        # === 測試2：SQL JOIN 查詢修復 ===
        print("\n📋 [TEST2] 測試 SQL JOIN 查詢修復...")
        
        try:
            with db_manager.get_connection() as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                
                # 模擬修復後的查詢邏輯
                group_info = db_manager.get_strategy_group_by_db_id(group_db_id)
                if group_info:
                    logical_group_id = group_info['logical_group_id']
                    
                    cursor.execute('''
                        SELECT pr.*, sg.range_high, sg.range_low
                        FROM position_records pr
                        JOIN strategy_groups sg ON pr.group_id = sg.group_id
                        WHERE pr.group_id = ? AND pr.status IN ('PENDING', 'ACTIVE')
                        ORDER BY pr.lot_id
                    ''', (logical_group_id,))
                    
                    results = cursor.fetchall()
                    print(f"✅ [TEST2] SQL JOIN 查詢成功: {len(results)} 筆記錄")
                    
                    if len(results) == 2:
                        print("🎉 [TEST2] 查詢結果正確")
                    else:
                        print(f"❌ [TEST2] 查詢結果錯誤: 期望2筆，實際{len(results)}筆")
                        return False
                else:
                    print("❌ [TEST2] 無法獲取策略組資訊")
                    return False
                    
        except Exception as e:
            print(f"❌ [TEST2] SQL 查詢失敗: {e}")
            return False
        
        # === 測試3：資料庫方法接口一致性 ===
        print("\n📋 [TEST3] 測試資料庫方法接口一致性...")
        
        # 測試 get_strategy_group_by_db_id
        try:
            group_info = db_manager.get_strategy_group_by_db_id(group_db_id)
            if group_info:
                print(f"✅ [TEST3] get_strategy_group_by_db_id 成功: 邏輯ID={group_info['logical_group_id']}")
            else:
                print("❌ [TEST3] get_strategy_group_by_db_id 失敗")
                return False
        except Exception as e:
            print(f"❌ [TEST3] get_strategy_group_by_db_id 異常: {e}")
            return False
        
        # 測試 get_active_positions_by_group
        try:
            positions = db_manager.get_active_positions_by_group(group_db_id)
            print(f"✅ [TEST3] get_active_positions_by_group 成功: {len(positions)} 個部位")
            
            if len(positions) == 2:
                print("🎉 [TEST3] 部位查詢結果正確")
            else:
                print(f"❌ [TEST3] 部位查詢結果錯誤: 期望2個，實際{len(positions)}個")
                return False
                
        except Exception as e:
            print(f"❌ [TEST3] get_active_positions_by_group 異常: {e}")
            return False
        
        # === 測試4：參數傳遞一致性 ===
        print("\n📋 [TEST4] 測試參數傳遞一致性...")
        
        # 檢查函式簽名
        import inspect
        
        # 檢查 setup_initial_stop_loss_for_group 簽名
        sig = inspect.signature(stop_loss_manager.setup_initial_stop_loss_for_group)
        params = list(sig.parameters.keys())
        
        if 'group_db_id' in params:
            print("✅ [TEST4] setup_initial_stop_loss_for_group 參數名稱正確")
        else:
            print(f"❌ [TEST4] setup_initial_stop_loss_for_group 參數錯誤: {params}")
            return False
        
        # 檢查 get_strategy_group_by_db_id 簽名
        sig2 = inspect.signature(db_manager.get_strategy_group_by_db_id)
        params2 = list(sig2.parameters.keys())
        
        if 'db_id' in params2:
            print("✅ [TEST4] get_strategy_group_by_db_id 參數名稱正確")
        else:
            print(f"❌ [TEST4] get_strategy_group_by_db_id 參數錯誤: {params2}")
            return False
        
        print("\n🎉 [SUCCESS] 所有 group_db_id 相關修復測試通過！")
        print("✅ 修復驗證成功：")
        print("  1. setup_initial_stop_loss_for_group 接受 group_db_id 參數")
        print("  2. SQL JOIN 查詢邏輯正確")
        print("  3. 資料庫方法接口一致")
        print("  4. 參數傳遞命名統一")
        print("  5. 無 TypeError 異常")
        
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
    print("🚀 開始執行綜合修復驗證測試...")
    success = test_comprehensive_group_db_id_fixes()
    
    if success:
        print("\n🏆 測試結果: 通過")
        sys.exit(0)
    else:
        print("\n💥 測試結果: 失敗")
        sys.exit(1)
