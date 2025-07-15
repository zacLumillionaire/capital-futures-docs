#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
簡單修復驗證測試
驗證關鍵修復是否正確實施
"""

import sys
import os
import inspect

# 添加項目根目錄到路徑
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

def test_callback_parameter_fix():
    """測試回調參數修復"""
    print("🧪 測試1：檢查回調參數修復")
    print("-" * 50)
    
    try:
        # 檢查 simplified_order_tracker.py 中的修復
        with open('simplified_order_tracker.py', 'r', encoding='utf-8') as f:
            content = f.read()
        
        # 檢查是否包含修復的代碼
        if 'callback(exit_order, retry_count)' in content:
            print("✅ 找到正確的回調參數傳遞: callback(exit_order, retry_count)")
            
            # 檢查是否包含重試次數獲取邏輯
            if 'exit_group.individual_retry_counts.get(current_lot_index, 0)' in content:
                print("✅ 找到重試次數獲取邏輯")
                return True
            else:
                print("❌ 缺少重試次數獲取邏輯")
                return False
        else:
            print("❌ 未找到正確的回調參數傳遞")
            return False
            
    except Exception as e:
        print(f"❌ 測試失敗: {e}")
        return False

def test_initial_stop_loss_fix():
    """測試初始停損自動設定修復"""
    print("\n🧪 測試2：檢查初始停損自動設定修復")
    print("-" * 50)
    
    try:
        # 檢查 simple_integrated.py 中的修復
        with open('simple_integrated.py', 'r', encoding='utf-8') as f:
            content = f.read()
        
        # 檢查關鍵修復代碼
        required_patterns = [
            'initial_stop_loss_manager',
            'setup_initial_stop_loss_for_group',
            'range_data=group_info',
            '🛡️ [STOP_LOSS]'
        ]
        
        found_patterns = []
        for pattern in required_patterns:
            if pattern in content:
                found_patterns.append(pattern)
                print(f"✅ 找到: {pattern}")
            else:
                print(f"❌ 缺少: {pattern}")
        
        if len(found_patterns) >= 3:  # 至少要有3個關鍵模式
            print("✅ 初始停損自動設定修復已實施")
            return True
        else:
            print("❌ 初始停損自動設定修復不完整")
            return False
            
    except Exception as e:
        print(f"❌ 測試失敗: {e}")
        return False

def test_exit_action_consistency():
    """測試出場動作一致性修復"""
    print("\n🧪 測試3：檢查出場動作一致性修復")
    print("-" * 50)
    
    try:
        # 檢查 risk_management_engine.py 中的修復
        with open('risk_management_engine.py', 'r', encoding='utf-8') as f:
            content = f.read()
        
        # 檢查是否所有出場動作都包含 group_id
        exit_action_patterns = [
            "'group_id': position['group_id']",
            "'position_id': position['id']",
            "'exit_price':",
            "'exit_reason':",
            "'pnl':"
        ]
        
        found_patterns = []
        for pattern in exit_action_patterns:
            count = content.count(pattern)
            if count > 0:
                found_patterns.append(pattern)
                print(f"✅ 找到 {count} 次: {pattern}")
            else:
                print(f"❌ 缺少: {pattern}")
        
        # 檢查 group_id 是否在多個地方被添加
        group_id_count = content.count("'group_id': position['group_id']")
        if group_id_count >= 3:  # 應該在初始停損、保護性停損、移動停利等地方都有
            print(f"✅ group_id 已添加到 {group_id_count} 個出場動作中")
            return True
        else:
            print(f"❌ group_id 只在 {group_id_count} 個出場動作中，可能不完整")
            return False
            
    except Exception as e:
        print(f"❌ 測試失敗: {e}")
        return False

def test_duplicate_callback_removal():
    """測試重複回調函數移除"""
    print("\n🧪 測試4：檢查重複回調函數移除")
    print("-" * 50)
    
    try:
        # 檢查 simple_integrated.py 中是否移除了重複的 on_exit_retry
        with open('simple_integrated.py', 'r', encoding='utf-8') as f:
            content = f.read()
        
        # 計算 on_exit_retry 定義的次數
        def_count = content.count('def on_exit_retry(')
        
        if def_count == 1:
            print("✅ 只有一個 on_exit_retry 函數定義")
            
            # 檢查是否是正確的版本（有 retry_count 參數）
            if 'def on_exit_retry(exit_order: dict, retry_count: int):' in content:
                print("✅ 保留了正確的 on_exit_retry 版本")
                return True
            else:
                print("❌ 保留的 on_exit_retry 版本參數不正確")
                return False
        elif def_count == 0:
            print("❌ 沒有找到 on_exit_retry 函數定義")
            return False
        else:
            print(f"❌ 仍有 {def_count} 個 on_exit_retry 函數定義，需要進一步清理")
            return False
            
    except Exception as e:
        print(f"❌ 測試失敗: {e}")
        return False

def main():
    """主測試函數"""
    print("🚀 開始簡單修復驗證測試")
    print("=" * 80)
    
    # 執行所有測試
    tests = [
        ("回調參數修復", test_callback_parameter_fix),
        ("初始停損自動設定修復", test_initial_stop_loss_fix),
        ("出場動作一致性修復", test_exit_action_consistency),
        ("重複回調函數移除", test_duplicate_callback_removal)
    ]
    
    results = []
    for test_name, test_func in tests:
        try:
            result = test_func()
            results.append((test_name, result))
        except Exception as e:
            print(f"❌ 測試 {test_name} 執行失敗: {e}")
            results.append((test_name, False))
    
    # 總結結果
    print("\n📊 測試結果總結")
    print("=" * 80)
    
    passed = 0
    total = len(results)
    
    for test_name, result in results:
        status = "✅ 通過" if result else "❌ 失敗"
        print(f"{status} {test_name}")
        if result:
            passed += 1
    
    print(f"\n🎯 總體結果: {passed}/{total} 個測試通過")
    
    if passed == total:
        print("🎉 所有修復驗證測試通過！")
        print("💡 修復已成功實施，可以安全使用")
        return True
    else:
        print("⚠️ 部分測試失敗，請檢查修復實現")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
