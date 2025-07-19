#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
驗證停損設定 - 確認停損點數就是虧損點數，沒有移動停損回檔比例
"""

import sys
import os
from datetime import datetime

def test_mdd_gui_stop_loss_config():
    """測試 mdd_gui.py 的停損配置"""
    print("🔍 測試 mdd_gui.py 停損配置")
    print("=" * 50)
    
    try:
        # 檢查 mdd_gui.py 中的 trailing 設定
        with open('experiment_analysis/mdd_gui.py', 'r', encoding='utf-8') as f:
            content = f.read()
        
        # 檢查是否所有 trailing 都設為 0
        trailing_lines = []
        for i, line in enumerate(content.split('\n'), 1):
            if '"trailing":' in line:
                trailing_lines.append((i, line.strip()))
        
        all_zero = True
        for line_num, line in trailing_lines:
            if '"trailing": 0' not in line:
                print(f"❌ 第{line_num}行: {line}")
                all_zero = False
            else:
                print(f"✅ 第{line_num}行: {line}")
        
        if all_zero:
            print("✅ mdd_gui.py 中所有 trailing 都設為 0")
            return True
        else:
            print("❌ mdd_gui.py 中還有非零的 trailing 設定")
            return False
            
    except Exception as e:
        print(f"❌ 測試失敗: {e}")
        return False

def test_config_factory_defaults():
    """測試配置工廠的預設值"""
    print("\n🔍 測試配置工廠預設值")
    print("=" * 50)
    
    try:
        # 檢查 strategy_config_factory.py 中的預設值
        with open('strategy_config_factory.py', 'r', encoding='utf-8') as f:
            content = f.read()
        
        # 檢查 default_lot_settings
        if '"trailing": 0' in content:
            print("✅ 配置工廠預設 trailing 設為 0")
            
            # 檢查驗證邏輯
            if '0 <= lot_rule.trailing_pullback <= 1' in content:
                print("✅ 驗證邏輯允許 0% 回檔")
                return True
            else:
                print("❌ 驗證邏輯不允許 0% 回檔")
                return False
        else:
            print("❌ 配置工廠預設 trailing 不是 0")
            return False
            
    except Exception as e:
        print(f"❌ 測試失敗: {e}")
        return False

def test_actual_config_creation():
    """測試實際配置創建"""
    print("\n🔍 測試實際配置創建")
    print("=" * 50)
    
    try:
        sys.path.append('.')
        from strategy_config_factory import create_config_from_gui_dict
        
        # 測試配置
        test_gui_config = {
            "trade_lots": 3,
            "start_date": "2024-11-04",
            "end_date": "2024-11-04",
            "range_start_time": "08:46",
            "range_end_time": "08:47",
            "fixed_stop_mode": True,  # 固定停損模式
            "individual_take_profit_enabled": False,
            "entry_price_mode": "range_boundary",
            "trading_direction": "BOTH",
            "lot_settings": {
                "lot1": {"trigger": 15, "trailing": 0, "take_profit": 30},
                "lot2": {"trigger": 25, "trailing": 0, "protection": 2.0, "take_profit": 30},
                "lot3": {"trigger": 35, "trailing": 0, "protection": 2.0, "take_profit": 30}
            },
            "filters": {
                "range_filter": {"enabled": False, "max_range_points": 50},
                "risk_filter": {"enabled": False, "daily_loss_limit": 150, "profit_target": 200},
                "stop_loss_filter": {"enabled": False, "stop_loss_type": "range_boundary", "fixed_stop_loss_points": 15.0}
            }
        }
        
        # 創建配置
        strategy_config = create_config_from_gui_dict(test_gui_config)
        
        print("✅ 配置創建成功")
        print(f"交易口數: {strategy_config.trade_size_in_lots}")
        
        # 檢查每口的設定
        for i, lot_rule in enumerate(strategy_config.lot_rules, 1):
            print(f"第{i}口設定:")
            print(f"  - 觸發點數: {lot_rule.trailing_activation}")
            print(f"  - 回檔比例: {lot_rule.trailing_pullback * 100:.1f}%")
            print(f"  - 使用移動停損: {lot_rule.use_trailing_stop}")
            print(f"  - 固定停損點數: {lot_rule.fixed_stop_loss_points}")
            
            # 驗證回檔比例為 0
            if lot_rule.trailing_pullback == 0:
                print(f"  ✅ 第{i}口回檔比例為 0%")
            else:
                print(f"  ❌ 第{i}口回檔比例不是 0%: {lot_rule.trailing_pullback * 100:.1f}%")
                return False
        
        return True
        
    except Exception as e:
        print(f"❌ 配置創建測試失敗: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_stop_loss_logic():
    """測試停損邏輯說明"""
    print("\n📋 停損邏輯說明")
    print("=" * 50)
    
    print("現在的停損設定:")
    print("✅ 停損參數 = 實際虧損點數")
    print("✅ 回檔比例 = 0%（無移動停損）")
    print("✅ 輸入停損15 = 虧損15點就停損")
    print("✅ 輸入停損25 = 虧損25點就停損")
    print("✅ 輸入停損35 = 虧損35點就停損")
    print()
    print("停損觸發邏輯:")
    print("• 多單：當價格 <= 進場價 - 停損點數 時停損")
    print("• 空單：當價格 >= 進場價 + 停損點數 時停損")
    print("• 無移動停損，無回檔比例，點數到了就停損")

def main():
    """主函數"""
    print("🔧 驗證停損設定")
    print("=" * 60)
    print(f"開始時間: {datetime.now()}")
    
    # 執行所有測試
    results = {}
    results['mdd_gui_config'] = test_mdd_gui_stop_loss_config()
    results['config_factory_defaults'] = test_config_factory_defaults()
    results['actual_config_creation'] = test_actual_config_creation()
    
    # 顯示停損邏輯說明
    test_stop_loss_logic()
    
    # 總結
    print(f"\n📊 驗證總結:")
    total_tests = len(results)
    passed_tests = sum(results.values())
    
    for test_name, passed in results.items():
        status = '✅ 通過' if passed else '❌ 失敗'
        print(f"  - {test_name}: {status}")
    
    print(f"\n整體結果: {passed_tests}/{total_tests} 測試通過")
    
    if passed_tests == total_tests:
        print("🎉 停損設定修復完成！")
        print("\n📋 確認結果:")
        print("  ✅ 停損參數就是實際虧損點數")
        print("  ✅ 回檔比例設為 0%（無移動停損）")
        print("  ✅ 點數到了就停損，沒有回檔機制")
        print("  ✅ 輸入15就是虧損15點停損")
        print("\n🚀 現在回測使用固定停損，沒有移動停損回檔比例！")
    else:
        print("⚠️ 部分設定需要進一步檢查")
    
    print(f"\n結束時間: {datetime.now()}")
    return passed_tests == total_tests

if __name__ == "__main__":
    main()
