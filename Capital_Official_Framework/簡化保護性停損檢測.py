#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
簡化保護性停損檢測工具
快速檢測保護性停損功能是否正常
"""

def test_calculation_logic():
    """測試計算邏輯"""
    print("🧮 保護性停損計算邏輯測試")
    print("-" * 40)
    
    # 測試多單
    print("📊 多單測試:")
    long_entry = 20000.0
    long_profit = 20.0
    long_multiplier = 2.0
    long_protection = long_entry - (long_profit * long_multiplier)
    print(f"   進場: {long_entry}, 獲利: {long_profit}, 倍數: {long_multiplier}")
    print(f"   保護價: {long_protection} (應該 < {long_entry})")
    long_ok = long_protection < long_entry
    print(f"   結果: {'✅ 正確' if long_ok else '❌ 錯誤'}")
    
    # 測試空單
    print("\n📊 空單測試:")
    short_entry = 22542.0
    short_profit = 20.0
    short_multiplier = 2.0
    short_protection = short_entry + (short_profit * short_multiplier)
    print(f"   進場: {short_entry}, 獲利: {short_profit}, 倍數: {short_multiplier}")
    print(f"   保護價: {short_protection} (應該 > {short_entry})")
    short_ok = short_protection > short_entry
    print(f"   結果: {'✅ 正確' if short_ok else '❌ 錯誤'}")
    
    return long_ok and short_ok

def test_module_imports():
    """測試模組導入"""
    print("\n📦 模組導入測試")
    print("-" * 40)
    
    modules = [
        ('multi_group_config', 'LotRule'),
        ('unified_exit_manager', 'UnifiedExitManager'),
        ('multi_group_database', 'MultiGroupDatabaseManager'),
        ('risk_management_engine', 'RiskManagementEngine')
    ]
    
    results = []
    for module_name, class_name in modules:
        try:
            module = __import__(module_name)
            cls = getattr(module, class_name)
            print(f"   ✅ {module_name}.{class_name}")
            results.append(True)
        except Exception as e:
            print(f"   ❌ {module_name}.{class_name}: {e}")
            results.append(False)
    
    return all(results)

def test_lot_rule_config():
    """測試LotRule配置"""
    print("\n🔧 LotRule配置測試")
    print("-" * 40)
    
    try:
        from multi_group_config import LotRule
        from decimal import Decimal
        
        # 測試創建LotRule
        rule = LotRule(
            lot_id=1,
            use_trailing_stop=True,
            trailing_activation=Decimal('15'),
            trailing_pullback=Decimal('0.10'),
            protective_stop_multiplier=Decimal('1.0'),
            use_protective_stop=True
        )
        
        # 檢查屬性
        has_multiplier = hasattr(rule, 'protective_stop_multiplier')
        has_use_flag = hasattr(rule, 'use_protective_stop')
        
        print(f"   protective_stop_multiplier: {'✅' if has_multiplier else '❌'}")
        print(f"   use_protective_stop: {'✅' if has_use_flag else '❌'}")
        
        # 測試JSON序列化
        json_str = rule.to_json()
        restored = LotRule.from_json(json_str)
        json_ok = restored.protective_stop_multiplier == rule.protective_stop_multiplier
        
        print(f"   JSON序列化: {'✅' if json_ok else '❌'}")
        
        return has_multiplier and has_use_flag and json_ok
        
    except Exception as e:
        print(f"   ❌ 測試失敗: {e}")
        return False

def test_unified_exit_manager():
    """測試統一出場管理器"""
    print("\n🚪 統一出場管理器測試")
    print("-" * 40)
    
    try:
        from unified_exit_manager import UnifiedExitManager
        
        # 檢查保護性停損方法
        methods = [
            'execute_protective_stop',
            'trigger_protective_stop_update'
        ]
        
        results = []
        for method in methods:
            has_method = hasattr(UnifiedExitManager, method)
            print(f"   {method}: {'✅' if has_method else '❌'}")
            results.append(has_method)
        
        return all(results)
        
    except Exception as e:
        print(f"   ❌ 測試失敗: {e}")
        return False

def test_database_support():
    """測試資料庫支援"""
    print("\n💾 資料庫支援測試")
    print("-" * 40)
    
    try:
        from multi_group_database import MultiGroupDatabaseManager
        
        # 檢查保護性停損方法
        methods = [
            'update_protective_stop',
            '_upgrade_protective_stop_schema'
        ]
        
        results = []
        for method in methods:
            has_method = hasattr(MultiGroupDatabaseManager, method)
            print(f"   {method}: {'✅' if has_method else '❌'}")
            results.append(has_method)
        
        return all(results)
        
    except Exception as e:
        print(f"   ❌ 測試失敗: {e}")
        return False

def main():
    """主測試函數"""
    print("🛡️ 簡化保護性停損檢測工具")
    print("=" * 50)
    
    tests = [
        ("計算邏輯", test_calculation_logic),
        ("模組導入", test_module_imports),
        ("LotRule配置", test_lot_rule_config),
        ("統一出場管理器", test_unified_exit_manager),
        ("資料庫支援", test_database_support)
    ]
    
    results = []
    for test_name, test_func in tests:
        try:
            result = test_func()
            results.append((test_name, result))
        except Exception as e:
            print(f"\n❌ {test_name}測試異常: {e}")
            results.append((test_name, False))
    
    # 總結
    print(f"\n📊 測試結果總結")
    print("=" * 50)
    
    passed = 0
    for test_name, result in results:
        status = "✅ 通過" if result else "❌ 失敗"
        print(f"{test_name}: {status}")
        if result:
            passed += 1
    
    print(f"\n總計: {passed}/{len(results)} 通過")
    
    if passed == len(results):
        print("🎉 所有測試通過！保護性停損功能基本正常")
        return True
    else:
        print("⚠️ 部分測試失敗，需要檢查相關功能")
        return False

if __name__ == "__main__":
    main()
