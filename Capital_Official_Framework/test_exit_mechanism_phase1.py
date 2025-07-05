#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
平倉機制 Phase 1 測試腳本
測試資料庫結構擴展和配置載入的正確性
"""

import os
import sys
import sqlite3
from datetime import datetime

def test_database_extension():
    """測試資料庫擴展功能"""
    print("🧪 測試資料庫擴展功能")
    print("=" * 60)
    
    try:
        # 導入必要模組
        from multi_group_database import MultiGroupDatabaseManager
        from exit_mechanism_database_extension import extend_database_for_exit_mechanism
        
        # 創建測試資料庫
        test_db_file = "test_exit_mechanism.db"
        if os.path.exists(test_db_file):
            os.remove(test_db_file)
        
        print("[TEST] 📁 創建測試資料庫...")
        db_manager = MultiGroupDatabaseManager(test_db_file)
        
        # 執行資料庫擴展
        print("[TEST] 🔧 執行資料庫擴展...")
        success = extend_database_for_exit_mechanism(db_manager)
        
        if not success:
            print("[TEST] ❌ 資料庫擴展失敗")
            return False
        
        # 驗證新表格是否存在
        print("[TEST] 🔍 驗證新表格...")
        with db_manager.get_connection() as conn:
            cursor = conn.cursor()
            
            # 檢查新表格
            required_tables = ['group_exit_status', 'exit_events', 'lot_exit_rules']
            for table in required_tables:
                cursor.execute(
                    "SELECT name FROM sqlite_master WHERE type='table' AND name=?",
                    (table,)
                )
                if cursor.fetchone():
                    print(f"[TEST] ✅ 表格 {table} 存在")
                else:
                    print(f"[TEST] ❌ 表格 {table} 不存在")
                    return False
            
            # 檢查 position_records 新欄位
            cursor.execute("PRAGMA table_info(position_records)")
            columns = {row[1] for row in cursor.fetchall()}
            
            required_columns = [
                'initial_stop_loss', 'current_stop_loss', 'is_initial_stop',
                'trailing_activated', 'peak_price', 'trailing_activation_points',
                'protective_multiplier', 'lot_rule_id'
            ]
            
            for column in required_columns:
                if column in columns:
                    print(f"[TEST] ✅ 欄位 position_records.{column} 存在")
                else:
                    print(f"[TEST] ❌ 欄位 position_records.{column} 不存在")
                    return False
            
            # 檢查預設規則
            cursor.execute("SELECT COUNT(*) FROM lot_exit_rules WHERE is_default = TRUE")
            default_rules_count = cursor.fetchone()[0]
            if default_rules_count == 3:
                print(f"[TEST] ✅ 預設規則數量正確: {default_rules_count}")
            else:
                print(f"[TEST] ❌ 預設規則數量錯誤: {default_rules_count}/3")
                return False
        
        print("[TEST] 🎉 資料庫擴展測試通過!")
        return True
        
    except Exception as e:
        print(f"[TEST] ❌ 資料庫擴展測試失敗: {e}")
        return False
    finally:
        # 清理測試檔案
        if os.path.exists(test_db_file):
            os.remove(test_db_file)


def test_exit_config():
    """測試平倉配置功能"""
    print("\n🧪 測試平倉配置功能")
    print("=" * 60)
    
    try:
        from exit_mechanism_config import (
            LotExitRule, GroupExitConfig, ExitMechanismConfigManager,
            get_default_exit_config_for_multi_group
        )
        
        # 測試 LotExitRule
        print("[TEST] 🔧 測試 LotExitRule...")
        rule1 = LotExitRule(1, 15, 0.20, None)
        rule2 = LotExitRule(2, 40, 0.20, 2.0)
        rule3 = LotExitRule(3, 65, 0.20, 2.0)
        
        print(f"[TEST] ✅ 第1口規則: {rule1.description}")
        print(f"[TEST] ✅ 第2口規則: {rule2.description}")
        print(f"[TEST] ✅ 第3口規則: {rule3.description}")
        
        # 測試 GroupExitConfig
        print("[TEST] 📋 測試 GroupExitConfig...")
        config = GroupExitConfig(
            group_id="test_group",
            total_lots=3,
            lot_rules=[rule1, rule2, rule3]
        )
        
        print(f"[TEST] ✅ 組別配置: {config.group_id}")
        print(f"[TEST] ✅ 總口數: {config.total_lots}")
        print(f"[TEST] ✅ 規則數量: {len(config.lot_rules)}")
        
        # 測試配置管理器
        print("[TEST] ⚙️ 測試配置管理器...")
        config_manager = ExitMechanismConfigManager(console_enabled=False)
        
        # 測試預設配置
        default_config = get_default_exit_config_for_multi_group()
        print(f"[TEST] ✅ 預設配置: {default_config.group_id}")
        print(f"[TEST] ✅ 預設口數: {default_config.total_lots}")
        
        # 驗證規則配置
        expected_activations = [15, 40, 65]
        expected_multipliers = [None, 2.0, 2.0]
        
        for i, rule in enumerate(default_config.lot_rules):
            if rule.trailing_activation_points == expected_activations[i]:
                print(f"[TEST] ✅ 第{rule.lot_number}口啟動點位正確: {rule.trailing_activation_points}")
            else:
                print(f"[TEST] ❌ 第{rule.lot_number}口啟動點位錯誤: {rule.trailing_activation_points}")
                return False
            
            if rule.protective_stop_multiplier == expected_multipliers[i]:
                print(f"[TEST] ✅ 第{rule.lot_number}口保護倍數正確: {rule.protective_stop_multiplier}")
            else:
                print(f"[TEST] ❌ 第{rule.lot_number}口保護倍數錯誤: {rule.protective_stop_multiplier}")
                return False
        
        # 測試JSON序列化
        print("[TEST] 📄 測試JSON序列化...")
        json_str = config.to_json()
        restored_config = GroupExitConfig.from_json(json_str)
        
        if restored_config.group_id == config.group_id:
            print("[TEST] ✅ JSON序列化測試通過")
        else:
            print("[TEST] ❌ JSON序列化測試失敗")
            return False
        
        print("[TEST] 🎉 平倉配置測試通過!")
        return True
        
    except Exception as e:
        print(f"[TEST] ❌ 平倉配置測試失敗: {e}")
        return False


def test_multi_group_integration():
    """測試多組策略整合"""
    print("\n🧪 測試多組策略整合")
    print("=" * 60)
    
    try:
        from multi_group_config import create_preset_configs
        from exit_mechanism_config import get_default_exit_config_for_multi_group
        
        # 測試多組策略配置
        print("[TEST] 📊 測試多組策略配置...")
        presets = create_preset_configs()
        
        # 檢查1組3口配置是否存在
        if "標準配置 (3口×1組)" in presets:
            config = presets["標準配置 (3口×1組)"]
            print(f"[TEST] ✅ 找到標準配置: {config.total_groups}組 × {config.lots_per_group}口")
            
            if config.total_groups == 1 and config.lots_per_group == 3:
                print("[TEST] ✅ 配置符合1組3口要求")
            else:
                print(f"[TEST] ❌ 配置不符合要求: {config.total_groups}組 × {config.lots_per_group}口")
                return False
        else:
            print("[TEST] ❌ 未找到標準配置 (3口×1組)")
            return False
        
        # 測試平倉配置整合
        print("[TEST] 🔧 測試平倉配置整合...")
        exit_config = get_default_exit_config_for_multi_group()
        
        # 驗證配置一致性
        if exit_config.total_lots == config.lots_per_group:
            print(f"[TEST] ✅ 平倉配置與多組配置一致: {exit_config.total_lots}口")
        else:
            print(f"[TEST] ❌ 配置不一致: 平倉{exit_config.total_lots}口 vs 多組{config.lots_per_group}口")
            return False
        
        print("[TEST] 🎉 多組策略整合測試通過!")
        return True
        
    except Exception as e:
        print(f"[TEST] ❌ 多組策略整合測試失敗: {e}")
        return False


def test_console_logging():
    """測試Console日誌輸出"""
    print("\n🧪 測試Console日誌輸出")
    print("=" * 60)
    
    try:
        from exit_mechanism_config import ExitMechanismConfigManager
        
        # 測試啟用Console日誌
        print("[TEST] 📝 測試Console日誌輸出...")
        config_manager = ExitMechanismConfigManager(console_enabled=True)
        
        # 測試載入配置 (應該有Console輸出)
        config = config_manager.get_preset_config("回測標準配置 (3口)")
        
        if config:
            print("[TEST] ✅ Console日誌輸出正常")
        else:
            print("[TEST] ❌ 配置載入失敗")
            return False
        
        print("[TEST] 🎉 Console日誌測試通過!")
        return True
        
    except Exception as e:
        print(f"[TEST] ❌ Console日誌測試失敗: {e}")
        return False


def main():
    """主測試函數"""
    print("🚀 平倉機制 Phase 1 測試開始")
    print("=" * 80)
    print(f"測試時間: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("測試範圍: 資料庫結構擴展、配置載入、多組策略整合")
    print("=" * 80)
    
    # 執行測試
    tests = [
        ("資料庫擴展", test_database_extension),
        ("平倉配置", test_exit_config),
        ("多組策略整合", test_multi_group_integration),
        ("Console日誌", test_console_logging)
    ]
    
    results = []
    for test_name, test_func in tests:
        try:
            result = test_func()
            results.append((test_name, result))
        except Exception as e:
            print(f"[MAIN] ❌ 測試 {test_name} 發生異常: {e}")
            results.append((test_name, False))
    
    # 總結報告
    print("\n" + "=" * 80)
    print("📊 測試結果總結")
    print("=" * 80)
    
    passed = 0
    total = len(results)
    
    for test_name, result in results:
        status = "✅ 通過" if result else "❌ 失敗"
        print(f"{test_name:20} : {status}")
        if result:
            passed += 1
    
    print("-" * 80)
    print(f"總計: {passed}/{total} 個測試通過")
    
    if passed == total:
        print("🎉 所有測試通過! Phase 1 準備就緒")
        return True
    else:
        print("⚠️ 部分測試失敗，請檢查問題後重新測試")
        return False


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
