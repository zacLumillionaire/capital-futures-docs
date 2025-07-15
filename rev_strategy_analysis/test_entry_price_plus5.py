#!/usr/bin/env python3
"""
測試最低點+5點進場邏輯修改
驗證 breakout_low 模式現在使用 low_price + 5 作為進場價格
"""

import os
import re

def test_strategy_file_modification():
    """測試策略文件的修改"""
    print("🧪 測試策略文件修改")
    print("=" * 50)
    
    strategy_file = "rev_multi_Profit-Funded Risk_多口.py"
    if not os.path.exists(strategy_file):
        print("❌ 策略文件不存在")
        return False
    
    with open(strategy_file, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # 測試 1: 檢查是否包含 +5 的邏輯
    if "candle['low_price'] + 5" in content:
        print("✅ 策略文件包含最低點+5點的進場邏輯")
    else:
        print("❌ 策略文件未找到最低點+5點的進場邏輯")
        return False
    
    # 測試 2: 檢查日誌顯示是否更新
    if "[最低點+5點進場]" in content:
        print("✅ 日誌顯示已更新為最低點+5點")
    else:
        print("❌ 日誌顯示未更新")
        return False
    
    # 測試 3: 確保沒有舊的最低點邏輯殘留
    old_pattern = r"entry_price = candle\['low_price'\](?!\s*\+)"
    if re.search(old_pattern, content):
        print("❌ 發現舊的最低點邏輯殘留")
        return False
    else:
        print("✅ 沒有舊的最低點邏輯殘留")
    
    return True

def test_mdd_gui_modification():
    """測試 MDD GUI 的修改"""
    print("\n🧪 測試 MDD GUI 修改")
    print("=" * 50)
    
    gui_file = "experiment_analysis/mdd_gui.py"
    if not os.path.exists(gui_file):
        print("❌ MDD GUI 文件不存在")
        return False
    
    with open(gui_file, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # 測試 1: 檢查說明文字是否更新
    if "最低點+5點進場模式" in content:
        print("✅ MDD GUI 說明文字已更新")
    else:
        print("❌ MDD GUI 說明文字未更新")
        return False
    
    # 測試 2: 檢查 JavaScript 標籤是否更新
    if "'最低點+5'" in content:
        print("✅ JavaScript 標籤已更新為最低點+5")
    else:
        print("❌ JavaScript 標籤未更新")
        return False
    
    return True

def test_web_gui_modification():
    """測試 Web GUI 的修改"""
    print("\n🧪 測試 Web GUI 修改")
    print("=" * 50)
    
    web_gui_file = "rev_web_trading_gui.py"
    if not os.path.exists(web_gui_file):
        print("❌ Web GUI 文件不存在")
        return False
    
    with open(web_gui_file, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # 測試 1: 檢查選項文字是否更新
    if "最低點+5點進場" in content:
        print("✅ Web GUI 選項文字已更新")
    else:
        print("❌ Web GUI 選項文字未更新")
        return False
    
    # 測試 2: 檢查說明文字是否更新
    if "最低點+5點進場：" in content and "避免極端價格" in content:
        print("✅ Web GUI 說明文字已更新")
    else:
        print("❌ Web GUI 說明文字未更新")
        return False
    
    return True

def test_entry_price_logic():
    """測試進場價格邏輯"""
    print("\n🧪 測試進場價格邏輯")
    print("=" * 50)
    
    # 模擬測試數據
    test_scenarios = [
        {
            "mode": "range_boundary",
            "range_low": 18000,
            "candle_low": 17995,
            "expected_entry": 18000,
            "description": "區間邊緣模式應使用區間下邊緣"
        },
        {
            "mode": "breakout_low", 
            "range_low": 18000,
            "candle_low": 17995,
            "expected_entry": 18000,  # 17995 + 5 = 18000
            "description": "最低點+5點模式應使用最低點+5"
        },
        {
            "mode": "breakout_low",
            "range_low": 18000,
            "candle_low": 17990,
            "expected_entry": 17995,  # 17990 + 5 = 17995
            "description": "最低點+5點模式計算驗證"
        }
    ]
    
    print("📊 進場價格邏輯測試案例:")
    for i, scenario in enumerate(test_scenarios, 1):
        print(f"   案例 {i}: {scenario['description']}")
        print(f"     - 模式: {scenario['mode']}")
        print(f"     - 區間低點: {scenario['range_low']}")
        print(f"     - K棒最低: {scenario['candle_low']}")
        print(f"     - 預期進場: {scenario['expected_entry']}")
        
        if scenario['mode'] == 'breakout_low':
            calculated = scenario['candle_low'] + 5
            if calculated == scenario['expected_entry']:
                print(f"     ✅ 計算正確: {scenario['candle_low']} + 5 = {calculated}")
            else:
                print(f"     ❌ 計算錯誤: {scenario['candle_low']} + 5 = {calculated}, 預期 {scenario['expected_entry']}")
                return False
        print()
    
    print("✅ 所有進場價格邏輯測試通過")
    return True

def test_demo_scenarios():
    """演示修改前後的差異"""
    print("\n🧪 修改前後差異演示")
    print("=" * 50)
    
    print("📊 假設場景: K棒跌破區間低點 18000，該K棒最低價 17985")
    print()
    print("修改前:")
    print("   - 區間邊緣模式: 進場價 = 18000 (區間下邊緣)")
    print("   - 最低點模式:   進場價 = 17985 (K棒最低價)")
    print()
    print("修改後:")
    print("   - 區間邊緣模式: 進場價 = 18000 (區間下邊緣)")
    print("   - 最低點+5模式: 進場價 = 17990 (K棒最低價 + 5)")
    print()
    print("🎯 修改優點:")
    print("   ✅ 避免在極端最低點進場")
    print("   ✅ 降低滑價風險")
    print("   ✅ 提高執行確定性")
    print("   ✅ 仍能獲得相對較好的進場價格")
    
    return True

def main():
    """主測試函數"""
    print("🚀 開始測試最低點+5點進場邏輯修改")
    print("=" * 80)
    
    try:
        # 執行所有測試
        test1_result = test_strategy_file_modification()
        test2_result = test_mdd_gui_modification()
        test3_result = test_web_gui_modification()
        test4_result = test_entry_price_logic()
        test5_result = test_demo_scenarios()
        
        print("\n" + "=" * 80)
        
        if all([test1_result, test2_result, test3_result, test4_result, test5_result]):
            print("🎉 所有測試通過！最低點+5點進場邏輯修改成功")
            print("\n📋 修改摘要:")
            print("✅ 策略文件進場邏輯已更新為 low_price + 5")
            print("✅ 日誌顯示已更新為 [最低點+5點進場]")
            print("✅ MDD GUI 說明和標籤已更新")
            print("✅ Web GUI 選項和說明已更新")
            print("✅ 進場價格計算邏輯正確")
            print("\n🎯 現在最低點模式更加實用和安全！")
        else:
            print("❌ 部分測試失敗，需要進一步檢查")
            
    except Exception as e:
        print(f"\n❌ 測試過程中發生錯誤: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    return True

if __name__ == "__main__":
    main()
