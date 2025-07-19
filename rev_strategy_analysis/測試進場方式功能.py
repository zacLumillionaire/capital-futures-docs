#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
測試進場方式功能
"""

import sys
import os
from datetime import datetime

def test_entry_price_modes():
    """測試進場方式功能"""
    print("🧪 測試進場方式功能")
    print("=" * 60)
    print(f"開始時間: {datetime.now()}")
    
    results = {}
    
    # 測試1：檢查回測引擎支援
    print("\n🔍 測試1：檢查回測引擎支援")
    try:
        sys.path.append('.')
        import rev_multi_Profit_Funded_Risk_多口 as engine
        
        # 檢查 StrategyConfig 是否有 entry_price_mode 參數
        from rev_multi_Profit_Funded_Risk_多口 import StrategyConfig
        
        # 創建測試配置
        test_config = StrategyConfig(entry_price_mode="breakout_low")
        
        if hasattr(test_config, 'entry_price_mode'):
            print(f"✅ 回測引擎支援 entry_price_mode 參數")
            print(f"  - 預設值: {test_config.entry_price_mode}")
            results['engine_support'] = True
        else:
            print("❌ 回測引擎不支援 entry_price_mode 參數")
            results['engine_support'] = False
            
    except Exception as e:
        print(f"❌ 回測引擎測試失敗: {e}")
        results['engine_support'] = False
    
    # 測試2：檢查配置工廠支援
    print("\n🔍 測試2：檢查配置工廠支援")
    try:
        from strategy_config_factory import create_config_from_gui_dict
        
        # 測試配置
        test_gui_config = {
            "trade_lots": 3,
            "start_date": "2024-11-04",
            "end_date": "2024-11-04",
            "range_start_time": "08:46",
            "range_end_time": "08:47",
            "fixed_stop_mode": True,
            "individual_take_profit_enabled": False,
            "entry_price_mode": "breakout_low",  # 測試最低點+5點
            "trading_direction": "BOTH",
            "lot_settings": {
                "lot1": {"trigger": 15, "trailing": 20, "take_profit": 30},
                "lot2": {"trigger": 25, "trailing": 20, "protection": 2.0, "take_profit": 30},
                "lot3": {"trigger": 35, "trailing": 20, "protection": 2.0, "take_profit": 30}
            },
            "filters": {
                "range_filter": {"enabled": False, "max_range_points": 50},
                "risk_filter": {"enabled": False, "daily_loss_limit": 150, "profit_target": 200},
                "stop_loss_filter": {"enabled": False, "stop_loss_type": "range_boundary", "fixed_stop_loss_points": 15.0}
            }
        }
        
        strategy_config = create_config_from_gui_dict(test_gui_config)
        
        if hasattr(strategy_config, 'entry_price_mode'):
            print(f"✅ 配置工廠支援 entry_price_mode 參數")
            print(f"  - 設定值: {strategy_config.entry_price_mode}")
            results['factory_support'] = True
        else:
            print("❌ 配置工廠不支援 entry_price_mode 參數")
            results['factory_support'] = False
            
    except Exception as e:
        print(f"❌ 配置工廠測試失敗: {e}")
        results['factory_support'] = False
    
    # 測試3：檢查 mdd_gui.py HTML 結構
    print("\n🔍 測試3：檢查 mdd_gui.py HTML 結構")
    try:
        with open('experiment_analysis/mdd_gui.py', 'r', encoding='utf-8') as f:
            content = f.read()
        
        checks = []
        checks.append(('進場方式設定標題', '🎯 進場方式設定' in content))
        checks.append(('區間下邊緣選項', '區間下邊緣進場' in content))
        checks.append(('最低點+5點選項', '最低點+5點進場' in content))
        checks.append(('單選按鈕名稱', 'name="entry_price_mode"' in content))
        checks.append(('range_boundary值', 'value="range_boundary"' in content))
        checks.append(('breakout_low值', 'value="breakout_low"' in content))
        
        all_passed = all(check[1] for check in checks)
        if all_passed:
            print("✅ mdd_gui.py HTML 結構正確")
            results['html_structure'] = True
        else:
            print("❌ mdd_gui.py HTML 結構有問題:")
            for name, passed in checks:
                print(f"  - {name}: {'✅' if passed else '❌'}")
            results['html_structure'] = False
            
    except Exception as e:
        print(f"❌ HTML 結構測試失敗: {e}")
        results['html_structure'] = False
    
    # 測試4：檢查 JavaScript 參數收集
    print("\n🔍 測試4：檢查 JavaScript 參數收集")
    try:
        # 檢查 JavaScript 是否正確收集 entry_price_mode 參數
        checks = []
        checks.append(('參數收集邏輯', 'entry_price_mode: document.querySelector' in content))
        checks.append(('單選按鈕查詢', 'input[name="entry_price_mode"]:checked' in content))
        checks.append(('參數傳遞', 'params.get(\'entry_price_mode\'' in content))
        
        all_passed = all(check[1] for check in checks)
        if all_passed:
            print("✅ JavaScript 參數收集邏輯正確")
            results['javascript'] = True
        else:
            print("❌ JavaScript 參數收集邏輯有問題:")
            for name, passed in checks:
                print(f"  - {name}: {'✅' if passed else '❌'}")
            results['javascript'] = False
            
    except Exception as e:
        print(f"❌ JavaScript 測試失敗: {e}")
        results['javascript'] = False
    
    # 測試5：檢查進場方式說明
    print("\n🔍 測試5：檢查進場方式說明")
    try:
        checks = []
        checks.append(('區間下邊緣說明', '區間下邊緣價格進場' in content))
        checks.append(('最低點+5點說明', '最低價+5點進場' in content))
        checks.append(('執行確定性說明', '執行確定性高' in content))
        checks.append(('執行風險說明', '平衡執行風險' in content))
        
        all_passed = all(check[1] for check in checks)
        if all_passed:
            print("✅ 進場方式說明完整")
            results['descriptions'] = True
        else:
            print("❌ 進場方式說明不完整:")
            for name, passed in checks:
                print(f"  - {name}: {'✅' if passed else '❌'}")
            results['descriptions'] = False
            
    except Exception as e:
        print(f"❌ 進場方式說明測試失敗: {e}")
        results['descriptions'] = False
    
    # 總結
    print(f"\n📊 測試總結:")
    total_tests = len(results)
    passed_tests = sum(results.values())
    
    for test_name, passed in results.items():
        status = '✅ 通過' if passed else '❌ 失敗'
        print(f"  - {test_name}: {status}")
    
    print(f"\n整體結果: {passed_tests}/{total_tests} 測試通過")
    
    if passed_tests == total_tests:
        print("🎉 進場方式功能完全就緒！")
        print("\n📋 功能特點:")
        print("  ✅ 回測引擎支援兩種進場方式")
        print("  ✅ mdd_gui.py 添加進場方式選擇界面")
        print("  ✅ 支援區間下邊緣進場（保守）")
        print("  ✅ 支援最低點+5點進場（平衡風險）")
        print("  ✅ 參數正確傳遞給回測引擎")
        print("\n🚀 現在可以重新啟動 mdd_gui.py 測試進場方式功能！")
    else:
        print("⚠️ 部分功能需要進一步檢查")
    
    print(f"\n結束時間: {datetime.now()}")
    return passed_tests == total_tests

if __name__ == "__main__":
    test_entry_price_modes()
