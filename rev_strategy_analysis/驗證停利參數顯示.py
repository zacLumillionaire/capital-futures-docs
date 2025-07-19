#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
驗證停利參數顯示修復
"""

import sys
import os
from datetime import datetime

def verify_profit_parameter_display():
    """驗證停利參數顯示修復"""
    print("🔧 驗證停利參數顯示修復")
    print("=" * 60)
    print(f"開始時間: {datetime.now()}")
    
    results = {}
    
    # 測試1：檢查前端 JavaScript 修復
    print("\n🔍 測試1：檢查前端 JavaScript 修復")
    try:
        with open('experiment_analysis/mdd_gui.py', 'r', encoding='utf-8') as f:
            content = f.read()
        
        checks = []
        checks.append(('移除硬編碼統一停利30', '統一停利 30' not in content))
        checks.append(('動態獲取統一停利值', 'document.getElementById(\'unifiedProfit\').value' in content))
        checks.append(('動態獲取個別停利值', 'document.getElementById(\'individualProfit\').value' in content))
        checks.append(('使用模板字符串', '`統一停利 ${unifiedProfit}`' in content))
        checks.append(('使用模板字符串個別', '`個別停利 ${individualProfit}`' in content))
        
        all_passed = all(check[1] for check in checks)
        if all_passed:
            print("✅ 前端 JavaScript 修復正確")
            results['frontend_fix'] = True
        else:
            print("❌ 前端 JavaScript 修復有問題:")
            for name, passed in checks:
                print(f"  - {name}: {'✅' if passed else '❌'}")
            results['frontend_fix'] = False
            
    except Exception as e:
        print(f"❌ 前端修復檢查失敗: {e}")
        results['frontend_fix'] = False
    
    # 測試2：檢查實際回測參數傳遞
    print("\n🔍 測試2：檢查實際回測參數傳遞")
    try:
        checks = []
        checks.append(('停利參數使用變數', '"take_profit": l1_tp' in content))
        checks.append(('停利參數使用變數2', '"take_profit": l2_tp' in content))
        checks.append(('停利參數使用變數3', '"take_profit": l3_tp' in content))
        checks.append(('停利參數來源正確', 'lot1_take_profit' in content))
        checks.append(('停利參數來源正確2', 'lot2_take_profit' in content))
        checks.append(('停利參數來源正確3', 'lot3_take_profit' in content))
        
        all_passed = all(check[1] for check in checks)
        if all_passed:
            print("✅ 實際回測參數傳遞正確")
            results['backend_params'] = True
        else:
            print("❌ 實際回測參數傳遞有問題:")
            for name, passed in checks:
                print(f"  - {name}: {'✅' if passed else '❌'}")
            results['backend_params'] = False
            
    except Exception as e:
        print(f"❌ 回測參數檢查失敗: {e}")
        results['backend_params'] = False
    
    # 測試3：檢查解析邏輯修復
    print("\n🔍 測試3：檢查解析邏輯修復")
    try:
        checks = []
        checks.append(('移除硬編碼解析', '統一停利 30' not in content or content.count('統一停利 30') == 0))
        checks.append(('動態停利類型', 'stop_profit_type = \'統一停利\'' in content))
        checks.append(('動態個別停利', 'stop_profit_type = \'個別停利\'' in content))
        checks.append(('前端動態添加註釋', '數字將在前端動態添加' in content))
        
        all_passed = all(check[1] for check in checks)
        if all_passed:
            print("✅ 解析邏輯修復正確")
            results['parsing_fix'] = True
        else:
            print("❌ 解析邏輯修復有問題:")
            for name, passed in checks:
                print(f"  - {name}: {'✅' if passed else '❌'}")
            results['parsing_fix'] = False
            
    except Exception as e:
        print(f"❌ 解析邏輯檢查失敗: {e}")
        results['parsing_fix'] = False
    
    # 測試4：檢查參數解析邏輯
    print("\n🔍 測試4：檢查參數解析邏輯")
    try:
        # 檢查停利參數解析是否正確
        checks = []
        checks.append(('統一停利解析', 'unified_tp = take_profit_ranges[\'unified\'][0]' in content))
        checks.append(('個別停利解析', 'base_tp = take_profit_ranges[\'individual\'][0]' in content))
        checks.append(('停利參數修復', 'lot1_take_profit = [30]' in content))  # 這個需要修復
        
        # 檢查是否還有硬編碼的30
        hardcoded_30_count = content.count('lot1_take_profit = [30]')
        if hardcoded_30_count > 0:
            print(f"⚠️ 發現 {hardcoded_30_count} 處硬編碼停利參數30，需要修復")
            results['parameter_parsing'] = False
        else:
            print("✅ 參數解析邏輯正確")
            results['parameter_parsing'] = True
            
    except Exception as e:
        print(f"❌ 參數解析檢查失敗: {e}")
        results['parameter_parsing'] = False
    
    # 總結
    print(f"\n📊 驗證總結:")
    total_tests = len(results)
    passed_tests = sum(results.values())
    
    for test_name, passed in results.items():
        status = '✅ 通過' if passed else '❌ 失敗'
        print(f"  - {test_name}: {status}")
    
    print(f"\n整體結果: {passed_tests}/{total_tests} 測試通過")
    
    if passed_tests == total_tests:
        print("🎉 停利參數顯示修復完成！")
        print("\n📋 修復詳情:")
        print("  ✅ 前端 JavaScript 動態獲取停利參數值")
        print("  ✅ 移除硬編碼的 '統一停利 30'")
        print("  ✅ 實際回測參數傳遞正確")
        print("  ✅ 表格顯示將反映實際輸入值")
        print("\n🚀 現在當您輸入統一停利80時，表格會正確顯示 '統一停利 80'！")
    else:
        print("⚠️ 部分修復需要進一步處理")
        
        # 如果參數解析有問題，提供修復建議
        if not results.get('parameter_parsing', True):
            print("\n🔧 需要額外修復停利參數解析邏輯")
    
    print(f"\n結束時間: {datetime.now()}")
    return passed_tests == total_tests

if __name__ == "__main__":
    verify_profit_parameter_display()
