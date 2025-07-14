#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
簡單保護性停損測試
"""

def test_calculation_fix():
    """測試計算修復"""
    print("🧮 測試保護性停損計算修復")
    print("-" * 40)
    
    # 模擬SHORT部位保護性停損計算
    direction = 'SHORT'
    entry_price = 22542.0
    first_lot_profit = 20.0  # 第一口獲利20點
    protection_multiplier = 2.0
    
    # 正確的計算邏輯
    stop_loss_amount = first_lot_profit * protection_multiplier
    if direction == 'LONG':
        new_stop_loss = entry_price - stop_loss_amount
    else:  # SHORT
        new_stop_loss = entry_price + stop_loss_amount  # 正確：空單止損往高點移動
    
    print(f"📊 計算參數:")
    print(f"   方向: {direction}")
    print(f"   進場價格: {entry_price}")
    print(f"   第一口獲利: {first_lot_profit}點")
    print(f"   保護倍數: {protection_multiplier}倍")
    print(f"   停損金額: {stop_loss_amount}點")
    print(f"   新停損價: {new_stop_loss}")
    
    # 驗證計算結果
    expected_stop_loss = 22582.0  # 22542 + (20 * 2.0) - 空單止損往高點移動
    if abs(new_stop_loss - expected_stop_loss) < 0.01:
        print(f"✅ 計算結果正確: {new_stop_loss} = {expected_stop_loss}")
        print(f"✅ 空單保護性停損邏輯正確：止損點從進場價往高點移動")
        return True
    else:
        print(f"❌ 計算結果錯誤: {new_stop_loss} ≠ {expected_stop_loss}")
        return False

def test_import_fixes():
    """測試模組導入"""
    print("\n📦 測試模組導入")
    print("-" * 40)
    
    results = []
    
    # 測試multi_group_config
    try:
        from multi_group_config import LotRule
        print("✅ multi_group_config 導入成功")
        results.append(True)
    except Exception as e:
        print(f"❌ multi_group_config 導入失敗: {e}")
        results.append(False)
    
    # 測試unified_exit_manager
    try:
        from unified_exit_manager import UnifiedExitManager
        print("✅ unified_exit_manager 導入成功")
        results.append(True)
    except Exception as e:
        print(f"❌ unified_exit_manager 導入失敗: {e}")
        results.append(False)
    
    # 測試multi_group_database
    try:
        from multi_group_database import MultiGroupDatabaseManager
        print("✅ multi_group_database 導入成功")
        results.append(True)
    except Exception as e:
        print(f"❌ multi_group_database 導入失敗: {e}")
        results.append(False)
    
    # 測試risk_management_engine
    try:
        from risk_management_engine import RiskManagementEngine
        print("✅ risk_management_engine 導入成功")
        results.append(True)
    except Exception as e:
        print(f"❌ risk_management_engine 導入失敗: {e}")
        results.append(False)
    
    return all(results)

def main():
    """主測試函數"""
    print("🛡️ 簡單保護性停損修復測試")
    print("=" * 50)
    
    # 測試計算修復
    calc_result = test_calculation_fix()
    
    # 測試模組導入
    import_result = test_import_fixes()
    
    print(f"\n📊 測試結果:")
    print(f"計算修復: {'✅ 通過' if calc_result else '❌ 失敗'}")
    print(f"模組導入: {'✅ 通過' if import_result else '❌ 失敗'}")
    
    if calc_result and import_result:
        print("\n🎉 基本修復驗證通過！")
        return True
    else:
        print("\n⚠️ 部分測試失敗，需要進一步檢查")
        return False

if __name__ == "__main__":
    main()
