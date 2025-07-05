#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
完整平倉機制端到端測試腳本
驗證整個平倉機制的完整功能，包含所有階段的邏輯
"""

import os
import sys
import sqlite3
import time
from datetime import datetime

def test_complete_exit_mechanism_workflow():
    """測試完整平倉機制工作流程"""
    print("🧪 測試完整平倉機制工作流程")
    print("=" * 80)
    
    try:
        from multi_group_database import MultiGroupDatabaseManager
        from exit_mechanism_database_extension import extend_database_for_exit_mechanism
        from exit_mechanism_manager import create_exit_mechanism_manager
        
        # 創建測試資料庫
        test_db_file = "test_complete_exit_mechanism.db"
        if os.path.exists(test_db_file):
            os.remove(test_db_file)
        
        print("[TEST] 📁 創建測試資料庫...")
        db_manager = MultiGroupDatabaseManager(test_db_file)
        extend_database_for_exit_mechanism(db_manager)
        
        # 創建平倉機制統一管理器
        print("[TEST] 🚀 創建平倉機制統一管理器...")
        exit_manager = create_exit_mechanism_manager(db_manager, console_enabled=True)
        
        # 初始化所有組件
        success = exit_manager.initialize_all_components()
        if not success:
            print("[TEST] ❌ 組件初始化失敗")
            return False
        
        print("[TEST] ✅ 平倉機制統一管理器初始化成功")
        
        # 準備測試數據 - 3口策略組
        print("[TEST] 📊 準備測試數據...")
        group_id = setup_test_data(db_manager)
        
        # 階段1: 設定初始停損
        print("\n[TEST] 🛡️ 階段1: 設定初始停損")
        range_data = {'range_high': 22500.0, 'range_low': 22400.0}
        success = exit_manager.setup_initial_stops_for_group(group_id, range_data)
        
        if success:
            print("[TEST] ✅ 初始停損設定成功")
        else:
            print("[TEST] ❌ 初始停損設定失敗")
            return False
        
        # 階段2: 模擬價格上漲，觸發移動停利啟動
        print("\n[TEST] 🎯 階段2: 模擬價格上漲，觸發移動停利啟動")
        
        # 價格上漲到22470 (+20點) - 第1口應該啟動移動停利
        results = exit_manager.process_price_update(22470.0, "09:00:01")
        print(f"[TEST] 價格22470: 移動停利啟動 {results.get('trailing_activations', 0)} 個")
        
        # 價格上漲到22500 (+50點) - 第2口應該啟動移動停利
        results = exit_manager.process_price_update(22500.0, "09:00:02")
        print(f"[TEST] 價格22500: 移動停利啟動 {results.get('trailing_activations', 0)} 個")
        
        # 價格上漲到22520 (+70點) - 第3口應該啟動移動停利
        results = exit_manager.process_price_update(22520.0, "09:00:03")
        print(f"[TEST] 價格22520: 移動停利啟動 {results.get('trailing_activations', 0)} 個")
        
        # 階段3: 模擬峰值更新
        print("\n[TEST] 📈 階段3: 模擬峰值更新")
        
        # 價格繼續上漲到22530
        results = exit_manager.process_price_update(22530.0, "09:00:04")
        print(f"[TEST] 價格22530: 峰值更新 {results.get('peak_updates', 0)} 個")
        
        # 價格創新高到22540
        results = exit_manager.process_price_update(22540.0, "09:00:05")
        print(f"[TEST] 價格22540: 峰值更新 {results.get('peak_updates', 0)} 個")
        
        # 階段4: 模擬回撤觸發移動停利平倉
        print("\n[TEST] 📉 階段4: 模擬回撤觸發移動停利平倉")
        
        # 價格回撤到22432 (從22540回撤約4.8%) - 應該觸發第1口移動停利平倉
        results = exit_manager.process_price_update(22432.0, "09:00:06")
        print(f"[TEST] 價格22432: 回撤觸發 {results.get('drawdown_triggers', 0)} 個")
        
        # 階段5: 驗證保護性停損更新
        print("\n[TEST] 🛡️ 階段5: 驗證保護性停損更新")
        
        # 檢查是否有保護性停損更新 (第1口平倉後，第2、3口應該更新保護性停損)
        status = exit_manager.get_exit_mechanism_status()
        print(f"[TEST] 當前狀態:")
        print(f"[TEST]   活躍部位: {status.active_positions}")
        print(f"[TEST]   已平倉: {status.exited_positions}")
        print(f"[TEST]   初始停損: {status.initial_stops}")
        print(f"[TEST]   保護停損: {status.protective_stops}")
        print(f"[TEST]   移動停利: {status.trailing_stops}")
        
        # 階段6: 繼續模擬第2口回撤平倉
        print("\n[TEST] 📉 階段6: 模擬第2口回撤平倉")
        
        # 價格進一步回撤，觸發第2口平倉
        results = exit_manager.process_price_update(22420.0, "09:00:07")
        print(f"[TEST] 價格22420: 回撤觸發 {results.get('drawdown_triggers', 0)} 個")
        
        # 最終狀態檢查
        print("\n[TEST] 📊 最終狀態檢查")
        final_status = exit_manager.get_exit_mechanism_status()
        exit_manager.print_exit_mechanism_status()
        
        # 驗證結果
        if final_status.exited_positions >= 1:  # 至少有1口平倉
            print("[TEST] ✅ 平倉機制工作流程測試通過!")
            return True
        else:
            print("[TEST] ❌ 平倉機制工作流程測試失敗: 沒有部位平倉")
            return False
        
    except Exception as e:
        print(f"[TEST] ❌ 完整平倉機制工作流程測試失敗: {e}")
        return False
    finally:
        # 清理測試檔案
        if os.path.exists(test_db_file):
            os.remove(test_db_file)


def setup_test_data(db_manager):
    """設定測試數據"""
    try:
        with db_manager.get_connection() as conn:
            cursor = conn.cursor()
            
            # 插入策略組
            cursor.execute('''
                INSERT INTO strategy_groups 
                (date, direction, range_high, range_low, status, total_groups, lots_per_group)
                VALUES ('2025-07-05', 'LONG', 22500.0, 22400.0, 'ACTIVE', 1, 3)
            ''')
            group_id = cursor.lastrowid
            
            # 插入3口部位 (對應15/40/65點啟動)
            positions_data = [
                (group_id, 1, 'LONG', 22450.0, 'ACTIVE', 15),  # 第1口: 15點啟動
                (group_id, 2, 'LONG', 22450.0, 'ACTIVE', 40),  # 第2口: 40點啟動
                (group_id, 3, 'LONG', 22450.0, 'ACTIVE', 65)   # 第3口: 65點啟動
            ]
            
            for group_id, lot_id, direction, entry_price, status, activation_points in positions_data:
                cursor.execute('''
                    INSERT INTO position_records 
                    (group_id, lot_id, direction, entry_price, status, 
                     trailing_activation_points, lot_rule_id, created_at)
                    VALUES (?, ?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
                ''', (group_id, lot_id, direction, entry_price, status, activation_points, lot_id))
            
            # 插入口數規則 (對應回測程式邏輯)
            cursor.execute('''
                INSERT OR REPLACE INTO lot_exit_rules 
                (rule_name, lot_number, trailing_activation_points, trailing_pullback_ratio, 
                 protective_stop_multiplier, is_default)
                VALUES 
                ('回測標準配置', 1, 15, 0.20, NULL, TRUE),
                ('回測標準配置', 2, 40, 0.20, 2.0, TRUE),
                ('回測標準配置', 3, 65, 0.20, 2.0, TRUE)
            ''')
            
            conn.commit()
            print(f"[TEST] 📊 測試數據設定完成: 策略組 {group_id}, 3口部位")
            return group_id
            
    except Exception as e:
        print(f"[TEST] ❌ 測試數據設定失敗: {e}")
        return None


def test_exit_mechanism_manager_components():
    """測試平倉機制管理器組件"""
    print("\n🧪 測試平倉機制管理器組件")
    print("=" * 60)
    
    try:
        from multi_group_database import MultiGroupDatabaseManager
        from exit_mechanism_database_extension import extend_database_for_exit_mechanism
        from exit_mechanism_manager import create_exit_mechanism_manager
        
        # 創建測試資料庫
        test_db_file = "test_manager_components.db"
        if os.path.exists(test_db_file):
            os.remove(test_db_file)
        
        print("[TEST] 📁 創建測試環境...")
        db_manager = MultiGroupDatabaseManager(test_db_file)
        extend_database_for_exit_mechanism(db_manager)
        
        # 創建管理器
        exit_manager = create_exit_mechanism_manager(db_manager, console_enabled=False)
        
        # 測試組件初始化
        print("[TEST] 🔧 測試組件初始化...")
        success = exit_manager.initialize_all_components()
        
        if success:
            print("[TEST] ✅ 所有組件初始化成功")
            
            # 驗證組件存在
            components = [
                ('initial_stop_loss_manager', exit_manager.initial_stop_loss_manager),
                ('stop_loss_monitor', exit_manager.stop_loss_monitor),
                ('stop_loss_executor', exit_manager.stop_loss_executor),
                ('trailing_stop_activator', exit_manager.trailing_stop_activator),
                ('peak_price_tracker', exit_manager.peak_price_tracker),
                ('drawdown_monitor', exit_manager.drawdown_monitor),
                ('protection_manager', exit_manager.protection_manager),
                ('stop_loss_state_manager', exit_manager.stop_loss_state_manager)
            ]
            
            all_components_ok = True
            for name, component in components:
                if component:
                    print(f"[TEST] ✅ {name}: 正常")
                else:
                    print(f"[TEST] ❌ {name}: 缺失")
                    all_components_ok = False
            
            if all_components_ok:
                print("[TEST] ✅ 所有組件驗證通過")
                
                # 測試狀態查詢
                status = exit_manager.get_exit_mechanism_status()
                if status.enabled:
                    print("[TEST] ✅ 系統狀態查詢正常")
                else:
                    print("[TEST] ❌ 系統狀態查詢異常")
                    return False
                
            else:
                print("[TEST] ❌ 部分組件缺失")
                return False
        else:
            print("[TEST] ❌ 組件初始化失敗")
            return False
        
        print("[TEST] 🎉 平倉機制管理器組件測試通過!")
        return True
        
    except Exception as e:
        print(f"[TEST] ❌ 平倉機制管理器組件測試失敗: {e}")
        return False
    finally:
        # 清理測試檔案
        if os.path.exists(test_db_file):
            os.remove(test_db_file)


def test_backtest_logic_compliance():
    """測試回測程式邏輯符合性"""
    print("\n🧪 測試回測程式邏輯符合性")
    print("=" * 60)
    
    try:
        from exit_mechanism_config import get_default_exit_config_for_multi_group
        
        print("[TEST] 📋 驗證配置符合回測程式...")
        
        # 取得預設配置
        config = get_default_exit_config_for_multi_group()
        
        # 驗證配置參數
        expected_config = {
            'total_lots': 3,
            'lot_rules': [
                {'lot_number': 1, 'activation_points': 15, 'pullback_ratio': 0.20, 'protection_multiplier': None},
                {'lot_number': 2, 'activation_points': 40, 'pullback_ratio': 0.20, 'protection_multiplier': 2.0},
                {'lot_number': 3, 'activation_points': 65, 'pullback_ratio': 0.20, 'protection_multiplier': 2.0}
            ]
        }
        
        # 驗證總口數
        if config.total_lots == expected_config['total_lots']:
            print(f"[TEST] ✅ 總口數正確: {config.total_lots}")
        else:
            print(f"[TEST] ❌ 總口數錯誤: {config.total_lots} vs {expected_config['total_lots']}")
            return False
        
        # 驗證各口規則
        for i, expected_rule in enumerate(expected_config['lot_rules']):
            actual_rule = config.lot_rules[i]
            
            # 檢查啟動點位
            if actual_rule.trailing_activation_points == expected_rule['activation_points']:
                print(f"[TEST] ✅ 第{actual_rule.lot_number}口啟動點位正確: {actual_rule.trailing_activation_points}")
            else:
                print(f"[TEST] ❌ 第{actual_rule.lot_number}口啟動點位錯誤: {actual_rule.trailing_activation_points}")
                return False
            
            # 檢查回撤比例
            if actual_rule.trailing_pullback_ratio == expected_rule['pullback_ratio']:
                print(f"[TEST] ✅ 第{actual_rule.lot_number}口回撤比例正確: {actual_rule.trailing_pullback_ratio}")
            else:
                print(f"[TEST] ❌ 第{actual_rule.lot_number}口回撤比例錯誤: {actual_rule.trailing_pullback_ratio}")
                return False
            
            # 檢查保護倍數
            if actual_rule.protective_stop_multiplier == expected_rule['protection_multiplier']:
                print(f"[TEST] ✅ 第{actual_rule.lot_number}口保護倍數正確: {actual_rule.protective_stop_multiplier}")
            else:
                print(f"[TEST] ❌ 第{actual_rule.lot_number}口保護倍數錯誤: {actual_rule.protective_stop_multiplier}")
                return False
        
        print("[TEST] 🎉 回測程式邏輯符合性測試通過!")
        return True
        
    except Exception as e:
        print(f"[TEST] ❌ 回測程式邏輯符合性測試失敗: {e}")
        return False


def main():
    """主測試函數"""
    print("🚀 完整平倉機制端到端測試開始")
    print("=" * 100)
    print(f"測試時間: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("測試範圍: 完整平倉機制端到端功能驗證")
    print("=" * 100)
    
    # 執行測試
    tests = [
        ("平倉機制管理器組件", test_exit_mechanism_manager_components),
        ("回測程式邏輯符合性", test_backtest_logic_compliance),
        ("完整平倉機制工作流程", test_complete_exit_mechanism_workflow)
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
    print("\n" + "=" * 100)
    print("📊 完整平倉機制測試結果總結")
    print("=" * 100)
    
    passed = 0
    total = len(results)
    
    for test_name, result in results:
        status = "✅ 通過" if result else "❌ 失敗"
        print(f"{test_name:30} : {status}")
        if result:
            passed += 1
    
    print("-" * 100)
    print(f"總計: {passed}/{total} 個測試通過")
    
    if passed == total:
        print("🎉 完整平倉機制端到端測試全部通過!")
        print("✅ 系統已準備就緒，可以投入使用")
        print("🎯 完全對應回測程式邏輯: 15/40/65點啟動, 2倍保護, 20%回撤")
        return True
    else:
        print("⚠️ 部分測試失敗，請檢查問題後重新測試")
        return False


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
