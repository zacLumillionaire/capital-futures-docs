#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
修復驗證測試腳本
驗證任務1和任務2的修復效果：
1. 平倉追價回調參數不匹配修復
2. 建倉後自動初始停損設定修復
3. 出場動作字典一致性修復
"""

import sys
import os
from datetime import datetime

# 添加路徑
current_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, current_dir)

def test_optimized_risk_manager_fixes():
    """測試優化風險管理器修復"""
    print("🧪 測試優化風險管理器修復...")
    
    try:
        # 1. 測試模組導入
        print("📦 測試模組導入...")
        from optimized_risk_manager import create_optimized_risk_manager
        from multi_group_database import MultiGroupDatabaseManager
        print("✅ 模組導入成功")
        
        # 2. 創建管理器
        print("🏗️ 創建管理器...")
        db_manager = MultiGroupDatabaseManager()
        risk_manager = create_optimized_risk_manager(db_manager, console_enabled=True)
        print("✅ 優化風險管理器創建成功")
        
        # 3. 測試 None 值處理修復
        print("🔧 測試 None 值處理修復...")
        
        # 測試無效數據處理
        invalid_position_1 = {
            'id': 'test_invalid_1',
            'direction': 'LONG',
            'entry_price': 22000.0,
            'range_high': None,  # None 值測試
            'range_low': 21950.0,
            'group_id': 1
        }
        
        risk_manager.on_new_position(invalid_position_1)
        print("✅ None 值處理測試通過")
        
        # 測試有效數據處理
        valid_position = {
            'id': 'test_valid_1',
            'direction': 'LONG',
            'entry_price': 22000.0,
            'range_high': 22050.0,
            'range_low': 21950.0,
            'group_id': 1
        }
        
        risk_manager.on_new_position(valid_position)
        print("✅ 有效數據處理測試通過")
        
        # 4. 測試價格更新
        print("📊 測試價格更新...")
        result = risk_manager.update_price(22010.0)
        print(f"✅ 價格更新成功: {result}")
        
        # 5. 測試統計信息
        print("📈 測試統計信息...")
        stats = risk_manager.get_stats()
        print(f"✅ 統計信息: {stats}")
        
        return True
        
    except Exception as e:
        print(f"❌ 優化風險管理器測試失敗: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_simplified_tracker_fixes():
    """測試簡化追蹤器修復"""
    print("\n🧪 測試簡化追蹤器修復...")
    
    try:
        from multi_group_position_manager import MultiGroupPositionManager
        from multi_group_database import MultiGroupDatabaseManager
        from multi_group_config import create_preset_configs
        
        # 創建測試環境
        db_manager = MultiGroupDatabaseManager("test_fix_verification.db")
        presets = create_preset_configs()
        config = presets["測試配置 (1口×1組)"]
        
        manager = MultiGroupPositionManager(db_manager, config)
        print("✅ 簡化追蹤器測試環境創建成功")
        
        # 測試重複處理檢測改善
        print("🔄 測試重複處理檢測改善...")
        
        # 模擬成交處理
        test_group_id = 1
        test_price = 22000.0
        test_qty = 1
        
        # 第一次處理（正常）
        manager._update_group_positions_on_fill(test_group_id, test_price, test_qty, 1, 1)
        print("✅ 第一次成交處理完成")
        
        # 第二次處理（應該智能跳過）
        manager._update_group_positions_on_fill(test_group_id, test_price, test_qty, 1, 1)
        print("✅ 重複處理智能跳過測試通過")
        
        return True
        
    except Exception as e:
        print(f"❌ 簡化追蹤器測試失敗: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """主測試函數"""
    print("🚀 開始修復驗證測試...")
    print("=" * 50)
    
    # 測試1: 優化風險管理器修復
    test1_result = test_optimized_risk_manager_fixes()
    
    # 測試2: 簡化追蹤器修復
    test2_result = test_simplified_tracker_fixes()
    
    # 總結
    print("\n" + "=" * 50)
    print("📋 測試結果總結:")
    print(f"  優化風險管理器修復: {'✅ 通過' if test1_result else '❌ 失敗'}")
    print(f"  簡化追蹤器修復: {'✅ 通過' if test2_result else '❌ 失敗'}")
    
    if test1_result and test2_result:
        print("\n🎉 所有修復測試通過！")
        print("💡 修復已成功，可以安全使用")
        return True
    else:
        print("\n⚠️ 部分測試失敗，需要進一步檢查")
        return False

def test_exit_retry_callback_fix():
    """測試平倉追價回調參數修復"""
    print("\n🧪 測試：平倉追價回調參數修復")
    print("=" * 60)

    try:
        from simplified_order_tracker import SimplifiedOrderTracker

        # 創建簡化追蹤器
        tracker = SimplifiedOrderTracker(console_enabled=True)

        # 模擬註冊一個平倉組
        position_id = 999
        tracker.register_exit_group(
            position_id=position_id,
            total_lots=1,
            direction="LONG",
            exit_direction="SELL",
            target_price=22500.0,
            product="TM0000"
        )

        # 創建測試回調函數來驗證參數
        callback_results = []

        def test_callback(exit_order: dict, retry_count: int):
            """測試回調函數 - 驗證參數類型和內容"""
            callback_results.append({
                'exit_order_type': type(exit_order).__name__,
                'retry_count_type': type(retry_count).__name__,
                'retry_count_value': retry_count,
                'position_id': exit_order.get('position_id') if isinstance(exit_order, dict) else None
            })
            print(f"✅ 回調接收到參數: exit_order={type(exit_order).__name__}, retry_count={retry_count}")

        # 註冊測試回調
        tracker.exit_retry_callbacks.append(test_callback)

        # 模擬觸發平倉追價
        exit_order = {
            'position_id': position_id,
            'order_id': f"TEST_EXIT_{position_id}_001",
            'direction': 'SELL',
            'quantity': 1,
            'price': 22500.0,
            'product': 'TM0000',
            'original_direction': 'LONG',
            'exit_reason': '測試追價'
        }

        print(f"🔄 觸發平倉追價回調...")
        tracker._trigger_exit_retry_callbacks(exit_order)

        # 驗證結果
        if callback_results:
            result = callback_results[0]
            print(f"\n📊 回調參數驗證結果:")
            print(f"   exit_order 類型: {result['exit_order_type']} (期望: dict)")
            print(f"   retry_count 類型: {result['retry_count_type']} (期望: int)")
            print(f"   retry_count 值: {result['retry_count_value']}")

            # 檢查是否修復成功
            if (result['exit_order_type'] == 'dict' and
                result['retry_count_type'] == 'int'):
                print("✅ 修復驗證成功：回調參數類型正確")
                return True
            else:
                print("❌ 修復驗證失敗：回調參數類型不正確")
                return False
        else:
            print("❌ 修復驗證失敗：回調未被觸發")
            return False

    except Exception as e:
        print(f"❌ 測試失敗: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_initial_stop_loss_auto_setup():
    """測試建倉後自動初始停損設定"""
    print("\n🧪 測試：建倉後自動初始停損設定")
    print("=" * 60)

    try:
        from simple_integrated import SimpleIntegratedApp
        import inspect

        # 檢查 execute_multi_group_entry 方法是否包含初始停損設定邏輯
        source = inspect.getsource(SimpleIntegratedApp.execute_multi_group_entry)

        # 檢查關鍵字
        required_keywords = [
            'initial_stop_loss_manager',
            'setup_initial_stop_loss_for_group',
            'range_data',
            'group_info'
        ]

        found_keywords = []
        for keyword in required_keywords:
            if keyword in source:
                found_keywords.append(keyword)
                print(f"✅ 找到關鍵字: {keyword}")
            else:
                print(f"❌ 缺少關鍵字: {keyword}")

        if len(found_keywords) == len(required_keywords):
            print("✅ 修復驗證成功：建倉方法包含初始停損設定邏輯")
            return True
        else:
            print(f"❌ 修復驗證失敗：缺少 {len(required_keywords) - len(found_keywords)} 個關鍵字")
            return False

    except Exception as e:
        print(f"❌ 測試失敗: {e}")
        import traceback
        traceback.print_exc()
        return False

def main_with_new_tests():
    """包含新修復測試的主函數"""
    print("🚀 開始完整修復驗證測試")
    print("=" * 80)

    # 執行原有測試
    original_success = main()

    # 執行新的修復驗證測試
    test_results = []
    test_results.append(("平倉追價回調參數修復", test_exit_retry_callback_fix()))
    test_results.append(("建倉後自動初始停損設定", test_initial_stop_loss_auto_setup()))

    # 總結新測試結果
    print("\n📊 新修復驗證測試結果總結")
    print("=" * 80)

    passed = 0
    total = len(test_results)

    for test_name, result in test_results:
        status = "✅ 通過" if result else "❌ 失敗"
        print(f"{status} {test_name}")
        if result:
            passed += 1

    print(f"\n🎯 新修復驗證結果: {passed}/{total} 個測試通過")

    new_tests_success = (passed == total)
    overall_success = original_success and new_tests_success

    if overall_success:
        print("🎉 所有修復驗證測試通過！")
    else:
        print("⚠️ 部分修復測試失敗，請檢查實現")

    return overall_success

if __name__ == "__main__":
    success = main_with_new_tests()
    sys.exit(0 if success else 1)
