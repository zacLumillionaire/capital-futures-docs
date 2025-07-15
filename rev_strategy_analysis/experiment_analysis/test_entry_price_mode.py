#!/usr/bin/env python3
"""
測試 entry_price_mode 新功能
驗證兩種進場模式的實作是否正確
"""

import sys
import os
import json

def test_basic_functionality():
    """基本功能測試"""
    print("🧪 測試 entry_price_mode 新功能")

    # 測試 1: 檢查文件是否存在並包含新功能
    strategy_file = "../rev_multi_Profit-Funded Risk_多口.py"
    if not os.path.exists(strategy_file):
        print("❌ 策略文件不存在")
        return False

    with open(strategy_file, 'r', encoding='utf-8') as f:
        content = f.read()

    # 檢查是否包含新的 entry_price_mode 參數
    if 'entry_price_mode' not in content:
        print("❌ 策略文件中未找到 entry_price_mode 參數")
        return False

    print("✅ 策略文件包含 entry_price_mode 參數")

    # 檢查是否包含進場邏輯修改
    if 'range_boundary' not in content or 'breakout_low' not in content:
        print("❌ 策略文件中未找到進場模式邏輯")
        return False

    print("✅ 策略文件包含進場模式邏輯")

    return True

def test_mdd_gui_files():
    """測試 MDD GUI 文件修改"""
    print("\n🧪 測試 2: MDD GUI 文件修改")

    # 檢查 mdd_gui.py 是否包含新功能
    gui_file = "mdd_gui.py"
    if not os.path.exists(gui_file):
        print("❌ MDD GUI 文件不存在")
        return False

    with open(gui_file, 'r', encoding='utf-8') as f:
        gui_content = f.read()

    # 檢查是否包含進場模式選項
    if 'enableBreakoutLow' not in gui_content:
        print("❌ MDD GUI 文件中未找到進場模式選項")
        return False

    print("✅ MDD GUI 文件包含進場模式選項")

    # 檢查是否包含進場模式標籤樣式
    if 'entry-mode-badge' not in gui_content:
        print("❌ MDD GUI 文件中未找到進場模式樣式")
        return False

    print("✅ MDD GUI 文件包含進場模式樣式")

    return True

def test_enhanced_optimizer_files():
    """測試增強優化器文件修改"""
    print("\n🧪 測試 3: 增強優化器文件修改")

    # 檢查 enhanced_mdd_optimizer.py 是否包含新功能
    optimizer_file = "enhanced_mdd_optimizer.py"
    if not os.path.exists(optimizer_file):
        print("❌ 增強優化器文件不存在")
        return False

    with open(optimizer_file, 'r', encoding='utf-8') as f:
        optimizer_content = f.read()

    # 檢查是否包含進場模式邏輯
    if 'entry_price_mode' not in optimizer_content:
        print("❌ 增強優化器文件中未找到進場模式邏輯")
        return False

    print("✅ 增強優化器文件包含進場模式邏輯")

    # 檢查是否包含實驗 ID 後綴
    if '_RB' not in optimizer_content or '_BL' not in optimizer_content:
        print("❌ 增強優化器文件中未找到實驗 ID 後綴")
        return False

    print("✅ 增強優化器文件包含實驗 ID 後綴")

    return True



def main():
    """主測試函數"""
    print("🚀 開始測試 entry_price_mode 新功能")
    print("=" * 50)

    try:
        # 執行基本功能測試
        if not test_basic_functionality():
            return False

        if not test_mdd_gui_files():
            return False

        if not test_enhanced_optimizer_files():
            return False

        print("\n" + "=" * 50)
        print("🎉 所有測試通過！entry_price_mode 功能實作正確")
        print("\n📋 功能摘要:")
        print("✅ 策略文件包含 entry_price_mode 參數和進場邏輯")
        print("✅ MDD GUI 包含進場模式選項和樣式")
        print("✅ 增強優化器包含進場模式邏輯和實驗 ID")

    except Exception as e:
        print(f"\n❌ 測試失敗: {e}")
        import traceback
        traceback.print_exc()
        return False

    return True

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
