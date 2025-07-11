#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
驗證移動停利系統優化
檢查統一計算器是否正確整合到 simple_integrated.py
"""

import sys
import os

def verify_simple_integrated_changes():
    """驗證 simple_integrated.py 中的修改"""
    print("🔍 驗證 simple_integrated.py 中的優化...")
    
    try:
        with open('simple_integrated.py', 'r', encoding='utf-8') as f:
            content = f.read()
        
        checks = [
            ("統一計算器初始化", "from trailing_stop_calculator import TrailingStopCalculator"),
            ("統一計算器創建", "self.trailing_calculator = TrailingStopCalculator"),
            ("連接止損執行器", "set_trailing_stop_calculator(self.trailing_calculator)"),
            ("統一模式標誌", "self.unified_trailing_enabled = True"),
            ("報價處理優化", "unified_trailing_enabled"),
            ("純內存計算", "get_active_positions()"),
            ("回退機制", "trailing_stop_system_enabled")
        ]
        
        results = []
        for check_name, check_pattern in checks:
            if check_pattern in content:
                results.append(f"✅ {check_name}: 已實現")
            else:
                results.append(f"❌ {check_name}: 未找到")
        
        for result in results:
            print(f"   {result}")
        
        success_count = sum(1 for r in results if r.startswith("✅"))
        total_count = len(results)
        
        print(f"\n📊 整合完成度: {success_count}/{total_count} ({success_count/total_count*100:.1f}%)")
        
        return success_count == total_count
        
    except Exception as e:
        print(f"❌ 驗證失敗: {e}")
        return False

def verify_position_manager_changes():
    """驗證 multi_group_position_manager.py 中的修改"""
    print("\n🔍 驗證 multi_group_position_manager.py 中的優化...")
    
    try:
        with open('multi_group_position_manager.py', 'r', encoding='utf-8') as f:
            content = f.read()
        
        checks = [
            ("部位註冊機制", "_register_position_to_trailing_calculator"),
            ("移動停利配置", "_get_group_trailing_config"),
            ("父引用訪問", "_parent_ref"),
            ("異步更新整合", "async_success_1 and async_success_2"),
            ("分層配置", "activation_points")
        ]
        
        results = []
        for check_name, check_pattern in checks:
            if check_pattern in content:
                results.append(f"✅ {check_name}: 已實現")
            else:
                results.append(f"❌ {check_name}: 未找到")
        
        for result in results:
            print(f"   {result}")
        
        success_count = sum(1 for r in results if r.startswith("✅"))
        total_count = len(results)
        
        print(f"\n📊 整合完成度: {success_count}/{total_count} ({success_count/total_count*100:.1f}%)")
        
        return success_count == total_count
        
    except Exception as e:
        print(f"❌ 驗證失敗: {e}")
        return False

def verify_component_availability():
    """驗證組件可用性"""
    print("\n🔍 驗證組件可用性...")
    
    components = [
        ("統一移動停利計算器", "trailing_stop_calculator", "TrailingStopCalculator"),
        ("止損執行器", "stop_loss_executor", "StopLossExecutor"),
        ("異步更新器", "async_db_updater", "AsyncDatabaseUpdater"),
        ("多組資料庫管理器", "multi_group_database", "MultiGroupDatabaseManager")
    ]
    
    results = []
    for comp_name, module_name, class_name in components:
        try:
            module = __import__(module_name)
            cls = getattr(module, class_name)
            results.append(f"✅ {comp_name}: 可用")
        except Exception as e:
            results.append(f"❌ {comp_name}: 不可用 ({e})")
    
    for result in results:
        print(f"   {result}")
    
    success_count = sum(1 for r in results if r.startswith("✅"))
    total_count = len(results)
    
    print(f"\n📊 組件可用性: {success_count}/{total_count} ({success_count/total_count*100:.1f}%)")
    
    return success_count == total_count

def main():
    """主驗證函數"""
    print("🧪 移動停利系統優化驗證")
    print("=" * 50)
    
    # 切換到正確的目錄
    os.chdir(os.path.dirname(os.path.abspath(__file__)))
    
    # 執行各項驗證
    simple_integrated_ok = verify_simple_integrated_changes()
    position_manager_ok = verify_position_manager_changes()
    components_ok = verify_component_availability()
    
    print("\n" + "=" * 50)
    print("📋 驗證總結:")
    
    if simple_integrated_ok:
        print("✅ simple_integrated.py 優化完成")
    else:
        print("❌ simple_integrated.py 優化不完整")
    
    if position_manager_ok:
        print("✅ multi_group_position_manager.py 優化完成")
    else:
        print("❌ multi_group_position_manager.py 優化不完整")
    
    if components_ok:
        print("✅ 所有組件可用")
    else:
        print("❌ 部分組件不可用")
    
    overall_success = simple_integrated_ok and position_manager_ok and components_ok
    
    if overall_success:
        print("\n🎉 優化驗證通過！系統已準備好使用統一移動停利計算器")
        print("💡 建議:")
        print("   1. 重啟 simple_integrated.py")
        print("   2. 觀察日誌中的 [TRAILING] 🎯 統一移動停利計算器已啟動")
        print("   3. 監控報價處理延遲改善")
    else:
        print("\n⚠️ 優化驗證未完全通過，請檢查上述問題")
    
    return overall_success

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
