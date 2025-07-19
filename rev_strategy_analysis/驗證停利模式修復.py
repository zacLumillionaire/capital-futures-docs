#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
驗證停利模式修復
"""

import sys
import os
from datetime import datetime

def calculate_expected_experiments():
    """計算預期的實驗數量"""
    print("🧮 計算預期實驗數量")
    print("=" * 50)
    
    # 測試參數
    test_params = {
        'stop_loss_ranges': {'lot1': [15], 'lot2': [25], 'lot3': [35]},
        'take_profit_ranges': {'unified': [55], 'individual': [30, 40, 50]},
        'time_intervals': [['10:30', '10:32'], ['12:00', '12:02']]
    }
    
    # 停損組合
    stop_loss_combinations = (
        len(test_params['stop_loss_ranges']['lot1']) *
        len(test_params['stop_loss_ranges']['lot2']) *
        len(test_params['stop_loss_ranges']['lot3'])
    )
    print(f"停損組合: {stop_loss_combinations}")
    
    # 停利模式組合
    unified_combinations = len(test_params['take_profit_ranges']['unified'])
    individual_combinations = (
        len(test_params['take_profit_ranges']['individual']) ** 3  # 3口各自選擇
    )
    range_boundary_combinations = 1  # 區間邊緣停利
    
    total_take_profit_combinations = (
        unified_combinations + individual_combinations + range_boundary_combinations
    )
    
    print(f"停利模式組合:")
    print(f"  - 統一停利: {unified_combinations}")
    print(f"  - 個別停利: {individual_combinations} (3^3 = {len(test_params['take_profit_ranges']['individual'])}^3)")
    print(f"  - 區間邊緣停利: {range_boundary_combinations}")
    print(f"  - 總計: {total_take_profit_combinations}")
    
    # 時間區間
    time_intervals = len(test_params['time_intervals'])
    print(f"時間區間: {time_intervals}")
    
    # 總實驗數
    total_experiments = stop_loss_combinations * total_take_profit_combinations * time_intervals
    print(f"\n📊 預期總實驗數: {stop_loss_combinations} × {total_take_profit_combinations} × {time_intervals} = {total_experiments}")
    
    return total_experiments

def verify_take_profit_logic():
    """驗證停利邏輯修復"""
    print("\n🔍 驗證停利邏輯修復")
    print("=" * 50)
    
    try:
        with open('experiment_analysis/mdd_gui.py', 'r', encoding='utf-8') as f:
            content = f.read()
        
        checks = []
        checks.append(('移除if-elif邏輯', 'elif \'individual\' in take_profit_ranges:' not in content))
        checks.append(('添加停利組合列表', 'all_take_profit_combinations = []' in content))
        checks.append(('統一停利模式', '\'mode\': \'unified_fixed\'' in content))
        checks.append(('個別停利模式', '\'mode\': \'individual_fixed\'' in content))
        checks.append(('區間邊緣停利模式', '\'mode\': \'range_boundary\'' in content))
        checks.append(('遍歷停利組合', 'for tp_combination in all_take_profit_combinations:' in content))
        checks.append(('停利模式記錄', '\'take_profit_mode\': tp_combination[\'mode\']' in content))
        checks.append(('停利模式日誌', 'tp_combination[\'mode\']' in content))
        
        all_passed = all(check[1] for check in checks)
        if all_passed:
            print("✅ 停利邏輯修復正確")
            return True
        else:
            print("❌ 停利邏輯修復有問題:")
            for name, passed in checks:
                print(f"  - {name}: {'✅' if passed else '❌'}")
            return False
            
    except Exception as e:
        print(f"❌ 停利邏輯驗證失敗: {e}")
        return False

def verify_experiment_structure():
    """驗證實驗結構"""
    print("\n🔍 驗證實驗結構")
    print("=" * 50)
    
    try:
        with open('experiment_analysis/mdd_gui.py', 'r', encoding='utf-8') as f:
            content = f.read()
        
        # 檢查嵌套循環結構
        checks = []
        checks.append(('時間區間循環', 'for time_interval in time_intervals:' in content))
        checks.append(('停損循環L1', 'for l1_sl in lot1_stop_loss:' in content))
        checks.append(('停損循環L2', 'for l2_sl in lot2_stop_loss:' in content))
        checks.append(('停損循環L3', 'for l3_sl in lot3_stop_loss:' in content))
        checks.append(('停利組合循環', 'for tp_combination in all_take_profit_combinations:' in content))
        checks.append(('停利循環L1', 'for l1_tp in tp_combination[\'lot1\']:' in content))
        checks.append(('停利循環L2', 'for l2_tp in tp_combination[\'lot2\']:' in content))
        checks.append(('停利循環L3', 'for l3_tp in tp_combination[\'lot3\']:' in content))
        
        all_passed = all(check[1] for check in checks)
        if all_passed:
            print("✅ 實驗結構正確")
            return True
        else:
            print("❌ 實驗結構有問題:")
            for name, passed in checks:
                print(f"  - {name}: {'✅' if passed else '❌'}")
            return False
            
    except Exception as e:
        print(f"❌ 實驗結構驗證失敗: {e}")
        return False

def verify_configuration_logic():
    """驗證配置邏輯"""
    print("\n🔍 驗證配置邏輯")
    print("=" * 50)
    
    try:
        with open('experiment_analysis/mdd_gui.py', 'r', encoding='utf-8') as f:
            content = f.read()
        
        checks = []
        checks.append(('停利模式判斷', 'if tp_combination[\'mode\'] == \'range_boundary\':' in content))
        checks.append(('區間停利配置', 'individual_tp_enabled = False' in content))
        checks.append(('固定停利配置', 'fixed_stop_mode = True' in content))
        checks.append(('動態配置設定', 'fixed_stop_mode = fixed_stop_mode' in content))
        
        all_passed = all(check[1] for check in checks)
        if all_passed:
            print("✅ 配置邏輯正確")
            return True
        else:
            print("❌ 配置邏輯有問題:")
            for name, passed in checks:
                print(f"  - {name}: {'✅' if passed else '❌'}")
            return False
            
    except Exception as e:
        print(f"❌ 配置邏輯驗證失敗: {e}")
        return False

def main():
    """主函數"""
    print("🔧 驗證停利模式修復")
    print("=" * 60)
    print(f"開始時間: {datetime.now()}")
    
    # 計算預期實驗數量
    expected_experiments = calculate_expected_experiments()
    
    # 驗證各項修復
    results = {}
    results['take_profit_logic'] = verify_take_profit_logic()
    results['experiment_structure'] = verify_experiment_structure()
    results['configuration_logic'] = verify_configuration_logic()
    
    # 總結
    print(f"\n📊 驗證總結:")
    total_tests = len(results)
    passed_tests = sum(results.values())
    
    for test_name, passed in results.items():
        status = '✅ 通過' if passed else '❌ 失敗'
        print(f"  - {test_name}: {status}")
    
    print(f"\n整體結果: {passed_tests}/{total_tests} 測試通過")
    
    if passed_tests == total_tests:
        print("🎉 停利模式修復完成！")
        print("\n📋 修復詳情:")
        print("  ✅ 修復了 if-elif 邏輯，現在會執行所有三種停利模式")
        print("  ✅ 統一停利模式：使用您輸入的統一停利值")
        print("  ✅ 個別停利模式：測試所有個別停利值的組合")
        print("  ✅ 區間邊緣停利模式：自動添加")
        print(f"  ✅ 預期實驗數量：{expected_experiments} 個實驗")
        print("\n🚀 現在 individual: [30, 40, 50] 會產生 3×3×3=27 個組合！")
        print("加上統一停利和區間邊緣停利，總共會有更多實驗。")
    else:
        print("⚠️ 部分修復需要進一步檢查")
    
    print(f"\n結束時間: {datetime.now()}")
    return passed_tests == total_tests

if __name__ == "__main__":
    main()
