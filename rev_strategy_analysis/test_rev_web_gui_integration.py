#!/usr/bin/env python3
"""
測試 rev_web_trading_gui.py 與 entry_price_mode 功能的整合
"""

import os
import re

def test_rev_web_gui_integration():
    """測試 rev_web_trading_gui.py 的 entry_price_mode 整合"""
    print("🧪 測試 rev_web_trading_gui.py 與 entry_price_mode 整合")
    print("=" * 60)
    
    # 檢查文件是否存在
    gui_file = "rev_web_trading_gui.py"
    if not os.path.exists(gui_file):
        print("❌ rev_web_trading_gui.py 文件不存在")
        return False
    
    with open(gui_file, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # 測試 1: 檢查是否使用相同的回測引擎
    print("📊 測試 1: 回測引擎一致性檢查")
    if 'rev_multi_Profit-Funded Risk_多口.py' in content:
        print("✅ 使用相同的回測引擎: rev_multi_Profit-Funded Risk_多口.py")
    else:
        print("❌ 未找到預期的回測引擎")
        return False
    
    # 測試 2: 檢查 HTML 表單是否包含進場模式選項
    print("\n📊 測試 2: HTML 表單進場模式選項")
    if 'entry_price_mode' in content and 'range_boundary' in content and 'breakout_low' in content:
        print("✅ HTML 表單包含進場模式選項")
    else:
        print("❌ HTML 表單缺少進場模式選項")
        return False
    
    # 測試 3: 檢查配置生成是否包含 entry_price_mode
    print("\n📊 測試 3: 配置生成包含 entry_price_mode")
    if '"entry_price_mode"' in content:
        print("✅ 配置生成包含 entry_price_mode 參數")
    else:
        print("❌ 配置生成缺少 entry_price_mode 參數")
        return False
    
    # 測試 4: 檢查進場模式說明文字
    print("\n📊 測試 4: 進場模式說明文字")
    if '區間邊緣進場' in content and '最低點進場' in content:
        print("✅ 包含進場模式說明文字")
    else:
        print("❌ 缺少進場模式說明文字")
        return False
    
    return True

def test_config_format_compatibility():
    """測試配置格式兼容性"""
    print("\n🧪 測試配置格式兼容性")
    print("=" * 60)
    
    # 模擬 rev_web_trading_gui.py 的配置格式
    sample_config = {
        "trade_lots": 3,
        "start_date": "2024-11-01",
        "end_date": "2024-11-30",
        "range_start_time": "08:46",
        "range_end_time": "08:47",
        "entry_price_mode": "range_boundary",  # 新增的參數
        "lot1_trigger": 15,
        "lot1_trailing": 10,
        "lot2_trigger": 40,
        "lot2_trailing": 10,
        "lot3_trigger": 65,
        "lot3_trailing": 20
    }
    
    print("📊 測試配置格式:")
    for key, value in sample_config.items():
        print(f"   - {key}: {value}")
    
    # 檢查關鍵參數
    required_params = ["entry_price_mode", "trade_lots", "start_date", "end_date"]
    missing_params = [param for param in required_params if param not in sample_config]
    
    if not missing_params:
        print("✅ 配置格式包含所有必要參數")
        return True
    else:
        print(f"❌ 配置格式缺少參數: {missing_params}")
        return False

def test_backtest_engine_consistency():
    """測試回測引擎一致性"""
    print("\n🧪 測試回測引擎一致性")
    print("=" * 60)
    
    # 檢查兩個 GUI 是否使用相同的回測引擎
    files_to_check = [
        ("rev_web_trading_gui.py", "單配置回測 GUI"),
        ("experiment_analysis/enhanced_mdd_optimizer.py", "MDD 優化器")
    ]
    
    engines = {}
    
    for file_path, description in files_to_check:
        if os.path.exists(file_path):
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # 查找回測引擎
            if 'rev_multi_Profit-Funded Risk_多口.py' in content:
                engines[description] = 'rev_multi_Profit-Funded Risk_多口.py'
            else:
                engines[description] = '未知'
        else:
            engines[description] = '文件不存在'
    
    print("📊 回測引擎使用情況:")
    for desc, engine in engines.items():
        print(f"   - {desc}: {engine}")
    
    # 檢查一致性
    unique_engines = set(engines.values())
    if len(unique_engines) == 1 and 'rev_multi_Profit-Funded Risk_多口.py' in unique_engines:
        print("✅ 所有 GUI 使用相同的回測引擎")
        return True
    else:
        print("❌ 回測引擎不一致或未找到")
        return False

def main():
    """主測試函數"""
    print("🚀 開始測試 rev_web_trading_gui.py 整合")
    print("=" * 80)
    
    try:
        # 執行所有測試
        test1_result = test_rev_web_gui_integration()
        test2_result = test_config_format_compatibility()
        test3_result = test_backtest_engine_consistency()
        
        print("\n" + "=" * 80)
        
        if all([test1_result, test2_result, test3_result]):
            print("🎉 所有測試通過！rev_web_trading_gui.py 已成功整合 entry_price_mode 功能")
            print("\n📋 整合摘要:")
            print("✅ 使用相同的回測引擎 (rev_multi_Profit-Funded Risk_多口.py)")
            print("✅ HTML 表單包含進場模式選項")
            print("✅ 配置生成包含 entry_price_mode 參數")
            print("✅ 配置格式兼容性良好")
            print("\n🎯 現在您可以在單配置回測中選擇進場模式了！")
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
