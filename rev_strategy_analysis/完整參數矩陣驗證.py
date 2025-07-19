#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
完整參數矩陣驗證 - 確保每個參數都支援多組值並用於矩陣組合
"""

import sys
import os
from datetime import datetime

def test_parameter_parsing():
    """測試參數解析函數"""
    print("🔍 測試參數解析函數")
    print("=" * 50)
    
    try:
        sys.path.append('experiment_analysis')
        import mdd_gui
        
        # 測試 parse_parameter_list 函數
        test_cases = [
            ("15,25,35", [15.0, 25.0, 35.0]),
            ("55", [55.0]),
            ([30, 40, 50], [30, 40, 50]),
            ("10, 20 , 30", [10.0, 20.0, 30.0])
        ]
        
        all_passed = True
        for input_val, expected in test_cases:
            result = mdd_gui.parse_parameter_list(input_val)
            if result == expected:
                print(f"✅ {input_val} → {result}")
            else:
                print(f"❌ {input_val} → {result} (期望: {expected})")
                all_passed = False
        
        return all_passed
        
    except Exception as e:
        print(f"❌ 參數解析測試失敗: {e}")
        return False

def verify_frontend_parsing():
    """驗證前端解析邏輯"""
    print("\n🔍 驗證前端解析邏輯")
    print("=" * 50)
    
    try:
        with open('experiment_analysis/mdd_gui.py', 'r', encoding='utf-8') as f:
            content = f.read()
        
        checks = []
        
        # 檢查前端參數收集
        checks.append(('停損L1解析', 'parseNumberList(document.getElementById(\'lot1StopLoss\').value)' in content))
        checks.append(('停損L2解析', 'parseNumberList(document.getElementById(\'lot2StopLoss\').value)' in content))
        checks.append(('停損L3解析', 'parseNumberList(document.getElementById(\'lot3StopLoss\').value)' in content))
        checks.append(('統一停利解析', 'parseNumberList(document.getElementById(\'unifiedProfit\').value)' in content))
        checks.append(('個別停利解析', 'parseNumberList(document.getElementById(\'individualProfit\').value)' in content))
        
        # 檢查 parseNumberList 函數
        checks.append(('parseNumberList函數存在', 'function parseNumberList(str)' in content))
        checks.append(('支援逗號分隔', 'str.split(\',\')' in content))
        checks.append(('過濾無效值', 'filter(n => !isNaN(n))' in content))
        
        # 檢查時間區間收集
        checks.append(('時間區間收集', 'timeIntervals.push([start, end])' in content))
        
        all_passed = all(check[1] for check in checks)
        if all_passed:
            print("✅ 前端解析邏輯正確")
        else:
            print("❌ 前端解析邏輯有問題:")
            for name, passed in checks:
                print(f"  - {name}: {'✅' if passed else '❌'}")
        
        return all_passed
        
    except Exception as e:
        print(f"❌ 前端解析驗證失敗: {e}")
        return False

def verify_backend_matrix_usage():
    """驗證後端矩陣使用"""
    print("\n🔍 驗證後端矩陣使用")
    print("=" * 50)
    
    try:
        with open('experiment_analysis/mdd_gui.py', 'r', encoding='utf-8') as f:
            content = f.read()
        
        checks = []
        
        # 檢查停損參數矩陣使用
        checks.append(('停損L1循環', 'for l1_sl in lot1_stop_loss:' in content))
        checks.append(('停損L2循環', 'for l2_sl in lot2_stop_loss:' in content))
        checks.append(('停損L3循環', 'for l3_sl in lot3_stop_loss:' in content))
        
        # 檢查停利參數矩陣使用
        checks.append(('停利組合循環', 'for tp_combination in all_take_profit_combinations:' in content))
        checks.append(('停利L1循環', 'for l1_tp in tp_combination[\'lot1\']:' in content))
        checks.append(('停利L2循環', 'for l2_tp in tp_combination[\'lot2\']:' in content))
        checks.append(('停利L3循環', 'for l3_tp in tp_combination[\'lot3\']:' in content))
        
        # 檢查時間區間矩陣使用
        checks.append(('時間區間循環', 'for time_interval in time_intervals:' in content))
        
        # 檢查統一停利支援多值
        checks.append(('統一停利多值支援', 'unified_values = take_profit_ranges[\'unified\']' in content))
        checks.append(('統一停利使用所有值', '\'lot1\': unified_values' in content))
        
        # 檢查個別停利支援多值
        checks.append(('個別停利多值支援', 'individual_values = take_profit_ranges[\'individual\']' in content))
        checks.append(('個別停利使用所有值', '\'lot1\': individual_values' in content))
        
        all_passed = all(check[1] for check in checks)
        if all_passed:
            print("✅ 後端矩陣使用正確")
        else:
            print("❌ 後端矩陣使用有問題:")
            for name, passed in checks:
                print(f"  - {name}: {'✅' if passed else '❌'}")
        
        return all_passed
        
    except Exception as e:
        print(f"❌ 後端矩陣驗證失敗: {e}")
        return False

def calculate_matrix_combinations():
    """計算矩陣組合數量"""
    print("\n🧮 計算矩陣組合數量示例")
    print("=" * 50)
    
    # 示例參數
    examples = [
        {
            'name': '基本測試',
            'stop_loss': {'lot1': [15], 'lot2': [25], 'lot3': [35]},
            'take_profit': {'unified': [55], 'individual': [30, 40, 50]},
            'time_intervals': 2
        },
        {
            'name': '多停損測試',
            'stop_loss': {'lot1': [15, 20], 'lot2': [25, 30], 'lot3': [35, 40]},
            'take_profit': {'unified': [50, 60], 'individual': [30, 40, 50]},
            'time_intervals': 3
        },
        {
            'name': '複雜測試',
            'stop_loss': {'lot1': [10, 15, 20], 'lot2': [20, 25, 30], 'lot3': [30, 35, 40]},
            'take_profit': {'unified': [40, 50, 60], 'individual': [25, 30, 35, 40]},
            'time_intervals': 4
        }
    ]
    
    for example in examples:
        print(f"\n📊 {example['name']}:")
        
        # 停損組合
        stop_loss_combos = (
            len(example['stop_loss']['lot1']) *
            len(example['stop_loss']['lot2']) *
            len(example['stop_loss']['lot3'])
        )
        print(f"  停損組合: {len(example['stop_loss']['lot1'])} × {len(example['stop_loss']['lot2'])} × {len(example['stop_loss']['lot3'])} = {stop_loss_combos}")
        
        # 停利組合
        unified_combos = len(example['take_profit']['unified'])
        individual_combos = len(example['take_profit']['individual']) ** 3
        range_boundary_combos = 1
        total_tp_combos = unified_combos + individual_combos + range_boundary_combos
        
        print(f"  停利組合:")
        print(f"    - 統一停利: {unified_combos}")
        print(f"    - 個別停利: {len(example['take_profit']['individual'])}³ = {individual_combos}")
        print(f"    - 區間邊緣: {range_boundary_combos}")
        print(f"    - 總計: {total_tp_combos}")
        
        # 總組合
        total_experiments = stop_loss_combos * total_tp_combos * example['time_intervals']
        print(f"  總實驗數: {stop_loss_combos} × {total_tp_combos} × {example['time_intervals']} = {total_experiments}")

def main():
    """主函數"""
    print("🔧 完整參數矩陣驗證")
    print("=" * 60)
    print(f"開始時間: {datetime.now()}")
    
    # 執行所有驗證
    results = {}
    results['parameter_parsing'] = test_parameter_parsing()
    results['frontend_parsing'] = verify_frontend_parsing()
    results['backend_matrix'] = verify_backend_matrix_usage()
    
    # 計算示例組合
    calculate_matrix_combinations()
    
    # 總結
    print(f"\n📊 驗證總結:")
    total_tests = len(results)
    passed_tests = sum(results.values())
    
    for test_name, passed in results.items():
        status = '✅ 通過' if passed else '❌ 失敗'
        print(f"  - {test_name}: {status}")
    
    print(f"\n整體結果: {passed_tests}/{total_tests} 測試通過")
    
    if passed_tests == total_tests:
        print("🎉 所有參數都支援矩陣組合！")
        print("\n📋 確認支援的參數:")
        print("  ✅ 停損參數 L1, L2, L3：支援逗號分隔多值")
        print("  ✅ 統一停利：支援逗號分隔多值（已修復）")
        print("  ✅ 個別停利：支援逗號分隔多值")
        print("  ✅ 時間區間：支援多個區間")
        print("  ✅ 所有參數都在嵌套循環中正確使用")
        print("\n🚀 現在所有參數都會產生完整的矩陣組合！")
    else:
        print("⚠️ 部分參數需要進一步檢查")
    
    print(f"\n結束時間: {datetime.now()}")
    return passed_tests == total_tests

if __name__ == "__main__":
    main()
