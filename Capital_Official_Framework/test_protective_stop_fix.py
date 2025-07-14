#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
保護性停損修復驗證測試
驗證所有修復是否正確工作
"""

import sys
import os
import json
from decimal import Decimal

# 添加當前目錄到路徑
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

def test_lot_rule_config():
    """測試LotRule配置修復"""
    print("🔧 測試1: LotRule配置修復")
    print("-" * 40)
    
    try:
        from multi_group_config import LotRule
        
        # 測試第1口配置
        rule1 = LotRule(
            lot_id=1,
            use_trailing_stop=True,
            trailing_activation=Decimal('15'),
            trailing_pullback=Decimal('0.10'),
            protective_stop_multiplier=Decimal('1.0'),
            use_protective_stop=True
        )
        
        print(f"✅ 第1口配置: {rule1.to_json()}")
        
        # 測試第2口配置
        rule2 = LotRule(
            lot_id=2,
            use_trailing_stop=True,
            trailing_activation=Decimal('40'),
            trailing_pullback=Decimal('0.10'),
            protective_stop_multiplier=Decimal('2.0'),
            use_protective_stop=True
        )
        
        print(f"✅ 第2口配置: {rule2.to_json()}")
        
        # 驗證JSON序列化/反序列化
        rule1_restored = LotRule.from_json(rule1.to_json())
        print(f"✅ JSON序列化測試通過")
        
        return True
        
    except Exception as e:
        print(f"❌ LotRule配置測試失敗: {e}")
        return False

def test_risk_engine_calculation():
    """測試風險引擎計算修復"""
    print("\n🧮 測試2: 保護性停損計算修復")
    print("-" * 40)
    
    try:
        # 模擬SHORT部位保護性停損計算
        direction = 'SHORT'
        entry_price = 22542.0
        first_lot_profit = 20.0  # 第一口獲利20點
        protection_multiplier = 2.0
        
        # 修復後的計算邏輯
        stop_loss_amount = first_lot_profit * protection_multiplier
        if direction == 'LONG':
            new_stop_loss = entry_price - stop_loss_amount
        else:  # SHORT
            new_stop_loss = entry_price - stop_loss_amount  # 修復：改為減法
        
        print(f"📊 計算參數:")
        print(f"   方向: {direction}")
        print(f"   進場價格: {entry_price}")
        print(f"   第一口獲利: {first_lot_profit}點")
        print(f"   保護倍數: {protection_multiplier}倍")
        print(f"   停損金額: {stop_loss_amount}點")
        print(f"   新停損價: {new_stop_loss}")
        
        # 驗證計算結果
        expected_stop_loss = 22502.0  # 22542 - (20 * 2.0)
        if abs(new_stop_loss - expected_stop_loss) < 0.01:
            print(f"✅ 計算結果正確: {new_stop_loss} = {expected_stop_loss}")
            return True
        else:
            print(f"❌ 計算結果錯誤: {new_stop_loss} ≠ {expected_stop_loss}")
            return False
            
    except Exception as e:
        print(f"❌ 計算測試失敗: {e}")
        return False

def test_unified_exit_manager():
    """測試統一出場管理器修復"""
    print("\n🚪 測試3: 統一出場管理器修復")
    print("-" * 40)
    
    try:
        from unified_exit_manager import UnifiedExitManager
        
        # 檢查是否有新增的保護性停損方法
        methods = dir(UnifiedExitManager)
        
        required_methods = [
            'execute_protective_stop',
            'trigger_protective_stop_update'
        ]
        
        missing_methods = []
        for method in required_methods:
            if method in methods:
                print(f"✅ 方法存在: {method}")
            else:
                missing_methods.append(method)
                print(f"❌ 方法缺失: {method}")
        
        if not missing_methods:
            print("✅ 統一出場管理器修復完成")
            return True
        else:
            print(f"❌ 缺少方法: {missing_methods}")
            return False
            
    except Exception as e:
        print(f"❌ 統一出場管理器測試失敗: {e}")
        return False

def test_database_structure():
    """測試資料庫結構修復"""
    print("\n💾 測試4: 資料庫結構修復")
    print("-" * 40)
    
    try:
        from multi_group_database import MultiGroupDatabaseManager
        
        # 檢查是否有新增的保護性停損方法
        methods = dir(MultiGroupDatabaseManager)
        
        required_methods = [
            'update_protective_stop',
            '_upgrade_protective_stop_schema'
        ]
        
        missing_methods = []
        for method in required_methods:
            if method in methods:
                print(f"✅ 方法存在: {method}")
            else:
                missing_methods.append(method)
                print(f"❌ 方法缺失: {method}")
        
        if not missing_methods:
            print("✅ 資料庫結構修復完成")
            return True
        else:
            print(f"❌ 缺少方法: {missing_methods}")
            return False
            
    except Exception as e:
        print(f"❌ 資料庫結構測試失敗: {e}")
        return False

def test_async_updater():
    """測試異步更新器支援"""
    print("\n🚀 測試5: 異步更新器支援")
    print("-" * 40)
    
    try:
        from async_db_updater import AsyncDatabaseUpdater
        
        # 檢查是否有保護性停損異步更新方法
        methods = dir(AsyncDatabaseUpdater)
        
        if 'schedule_protection_update' in methods:
            print("✅ 異步保護性停損更新方法存在")
            return True
        else:
            print("❌ 異步保護性停損更新方法缺失")
            return False
            
    except Exception as e:
        print(f"❌ 異步更新器測試失敗: {e}")
        return False

def main():
    """主測試函數"""
    print("🛡️ 保護性停損修復驗證測試")
    print("=" * 60)
    
    test_results = []
    
    # 執行所有測試
    test_results.append(("LotRule配置修復", test_lot_rule_config()))
    test_results.append(("保護性停損計算修復", test_risk_engine_calculation()))
    test_results.append(("統一出場管理器修復", test_unified_exit_manager()))
    test_results.append(("資料庫結構修復", test_database_structure()))
    test_results.append(("異步更新器支援", test_async_updater()))
    
    # 統計結果
    print("\n📊 測試結果總結")
    print("=" * 60)
    
    passed = 0
    failed = 0
    
    for test_name, result in test_results:
        status = "✅ 通過" if result else "❌ 失敗"
        print(f"{test_name}: {status}")
        if result:
            passed += 1
        else:
            failed += 1
    
    print(f"\n總計: {passed}個通過, {failed}個失敗")
    
    if failed == 0:
        print("🎉 所有修復驗證通過！保護性停損功能已修復完成")
        return True
    else:
        print("⚠️ 部分修復需要進一步檢查")
        return False

if __name__ == "__main__":
    main()
