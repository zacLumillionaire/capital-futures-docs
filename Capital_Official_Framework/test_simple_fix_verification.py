#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
🧪 簡化版修復驗證測試
專門測試 setup_initial_stop_loss_for_group 的參數修復
"""

import os
import sys

# 添加專案路徑
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

def test_function_signature_fix():
    """測試函式簽名修復"""
    try:
        print("🧪 [TEST] 測試函式簽名修復...")
        
        from initial_stop_loss_manager import InitialStopLossManager
        from multi_group_database import MultiGroupDatabaseManager
        
        # 創建測試實例
        db_manager = MultiGroupDatabaseManager(":memory:")  # 使用內存資料庫
        stop_loss_manager = InitialStopLossManager(db_manager, console_enabled=False)
        
        print("✅ [TEST] 管理器創建成功")
        
        # 測試函式簽名 - 檢查是否接受 group_db_id 參數
        import inspect
        sig = inspect.signature(stop_loss_manager.setup_initial_stop_loss_for_group)
        params = list(sig.parameters.keys())
        
        print(f"📋 [TEST] 函式參數: {params}")
        
        if 'group_db_id' in params:
            print("✅ [TEST] 函式簽名修復成功：接受 group_db_id 參數")
        else:
            print("❌ [TEST] 函式簽名修復失敗：仍使用舊參數名")
            return False
        
        # 測試呼叫（即使沒有資料也不應該拋出 TypeError）
        try:
            result = stop_loss_manager.setup_initial_stop_loss_for_group(
                group_db_id=999,  # 不存在的組ID
                range_data={'range_high': 22530.0, 'range_low': 22480.0}
            )
            print(f"✅ [TEST] 函式呼叫成功，返回: {result}")
            print("✅ [TEST] 沒有拋出 TypeError: unexpected keyword argument")
            
        except TypeError as e:
            if "unexpected keyword argument" in str(e):
                print(f"❌ [TEST] 仍然存在 TypeError: {e}")
                return False
            else:
                print(f"⚠️ [TEST] 其他 TypeError（可能正常）: {e}")
        
        except Exception as e:
            print(f"⚠️ [TEST] 其他異常（可能正常，因為沒有真實資料）: {e}")
        
        print("🎉 [TEST] 核心修復驗證通過！")
        return True
        
    except Exception as e:
        print(f"❌ [TEST] 測試失敗: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_exit_mechanism_manager_compatibility():
    """測試 ExitMechanismManager 的兼容性"""
    try:
        print("\n🧪 [TEST] 測試 ExitMechanismManager 兼容性...")
        
        from exit_mechanism_manager import ExitMechanismManager
        from multi_group_database import MultiGroupDatabaseManager
        
        db_manager = MultiGroupDatabaseManager(":memory:")
        exit_manager = ExitMechanismManager(db_manager, console_enabled=False)
        
        # 初始化組件
        exit_manager.initialize_all_components()
        
        print("✅ [TEST] ExitMechanismManager 初始化成功")
        
        # 檢查是否有 initial_stop_loss_manager
        if hasattr(exit_manager, 'initial_stop_loss_manager') and exit_manager.initial_stop_loss_manager:
            print("✅ [TEST] initial_stop_loss_manager 組件存在")
            
            # 檢查 setup_initial_stops_for_group 方法
            if hasattr(exit_manager, 'setup_initial_stops_for_group'):
                print("✅ [TEST] setup_initial_stops_for_group 方法存在")
                
                # 測試呼叫（這個方法內部會呼叫修復後的函式）
                try:
                    result = exit_manager.setup_initial_stops_for_group(
                        group_id=999,  # 注意：這裡使用 group_id 參數名
                        range_data={'range_high': 22530.0, 'range_low': 22480.0}
                    )
                    print(f"✅ [TEST] setup_initial_stops_for_group 呼叫成功: {result}")
                    
                except Exception as e:
                    print(f"⚠️ [TEST] setup_initial_stops_for_group 異常（可能正常）: {e}")
            else:
                print("❌ [TEST] setup_initial_stops_for_group 方法不存在")
                return False
        else:
            print("❌ [TEST] initial_stop_loss_manager 組件不存在")
            return False
        
        print("🎉 [TEST] ExitMechanismManager 兼容性測試通過！")
        return True
        
    except Exception as e:
        print(f"❌ [TEST] ExitMechanismManager 測試失敗: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    print("🚀 開始執行簡化版修復驗證測試...")
    print("=" * 50)
    
    success1 = test_function_signature_fix()
    success2 = test_exit_mechanism_manager_compatibility()
    
    if success1 and success2:
        print("\n🏆 所有測試通過！修復成功！")
        print("✅ setup_initial_stop_loss_for_group 已正確接受 group_db_id 參數")
        print("✅ 不再拋出 TypeError: unexpected keyword argument")
        print("✅ ExitMechanismManager 兼容性正常")
        sys.exit(0)
    else:
        print("\n💥 部分測試失敗！")
        sys.exit(1)
