#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
平倉機制 Phase 4 測試腳本
測試累積獲利保護機制的完整功能，包含保護倍數邏輯和狀態管理
"""

import os
import sys
import sqlite3
import time
from datetime import datetime

def test_cumulative_profit_protection_manager():
    """測試累積獲利保護管理器"""
    print("🧪 測試累積獲利保護管理器")
    print("=" * 60)
    
    try:
        from multi_group_database import MultiGroupDatabaseManager
        from exit_mechanism_database_extension import extend_database_for_exit_mechanism
        from cumulative_profit_protection_manager import create_cumulative_profit_protection_manager
        
        # 創建測試資料庫
        test_db_file = "test_protection_phase4.db"
        if os.path.exists(test_db_file):
            os.remove(test_db_file)
        
        print("[TEST] 📁 創建測試資料庫...")
        db_manager = MultiGroupDatabaseManager(test_db_file)
        extend_database_for_exit_mechanism(db_manager)
        
        # 創建保護管理器
        protection_manager = create_cumulative_profit_protection_manager(db_manager, console_enabled=True)
        
        # 設定測試回調
        protection_updates = []
        def test_callback(update_info):
            protection_updates.append(update_info)
            print(f"[TEST] 🛡️ 保護更新回調: 部位{update_info.position_id}, 停損 {update_info.old_stop_loss} → {update_info.new_stop_loss}")
        
        protection_manager.add_protection_callback(test_callback)
        
        # 插入測試數據 (3口策略，第1口已獲利平倉)
        print("[TEST] 📊 準備測試數據...")
        with db_manager.get_connection() as conn:
            cursor = conn.cursor()
            
            # 插入策略組
            cursor.execute('''
                INSERT INTO strategy_groups 
                (date, direction, range_high, range_low, status, total_groups, lots_per_group)
                VALUES ('2025-07-05', 'LONG', 22500.0, 22400.0, 'ACTIVE', 1, 3)
            ''')
            group_id = cursor.lastrowid
            
            # 插入3口部位
            positions_data = [
                (group_id, 1, 'LONG', 22450.0, 'EXITED', 22470.0, 20.0),   # 第1口: 已平倉，獲利20點
                (group_id, 2, 'LONG', 22450.0, 'ACTIVE', 22400.0, None),   # 第2口: 活躍，初始停損
                (group_id, 3, 'LONG', 22450.0, 'ACTIVE', 22400.0, None)    # 第3口: 活躍，初始停損
            ]
            
            position_ids = []
            for group_id, lot_id, direction, entry_price, status, stop_loss, pnl in positions_data:
                cursor.execute('''
                    INSERT INTO position_records 
                    (group_id, lot_id, direction, entry_price, status, 
                     current_stop_loss, is_initial_stop, realized_pnl, lot_rule_id)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', (group_id, lot_id, direction, entry_price, status, stop_loss, 
                      status == 'ACTIVE', pnl, lot_id))
                position_ids.append(cursor.lastrowid)
            
            # 插入口數規則 (第2、3口有2.0倍保護)
            cursor.execute('''
                INSERT OR REPLACE INTO lot_exit_rules 
                (rule_name, lot_number, trailing_activation_points, trailing_pullback_ratio, 
                 protective_stop_multiplier, is_default)
                VALUES 
                ('測試規則', 1, 15, 0.20, NULL, TRUE),
                ('測試規則', 2, 40, 0.20, 2.0, TRUE),
                ('測試規則', 3, 65, 0.20, 2.0, TRUE)
            ''')
            
            conn.commit()
        
        # 測試保護性停損更新
        print("[TEST] 🛡️ 測試保護性停損更新...")
        
        # 第1口已獲利20點，應該更新第2、3口的保護性停損
        updates = protection_manager.update_protective_stops_for_group(group_id, position_ids[0])
        
        print(f"[TEST] 保護更新數量: {len(updates)}")
        
        if len(updates) == 2:  # 應該更新第2、3口
            print("[TEST] ✅ 保護更新數量正確")
            
            # 驗證保護計算
            for update in updates:
                expected_protection = 20.0 * 2.0  # 20點獲利 × 2.0倍保護 = 40點保護
                expected_new_stop = 22450.0 + expected_protection  # 進場價 + 保護金額 = 22490.0
                
                if abs(update.new_stop_loss - expected_new_stop) < 0.1:
                    print(f"[TEST] ✅ 部位{update.position_id} 保護計算正確: {update.new_stop_loss}")
                else:
                    print(f"[TEST] ❌ 部位{update.position_id} 保護計算錯誤: {update.new_stop_loss} vs {expected_new_stop}")
                    return False
        else:
            print(f"[TEST] ❌ 保護更新數量錯誤: {len(updates)}/2")
            return False
        
        # 檢查回調是否執行
        if len(protection_updates) == 2:
            print("[TEST] ✅ 保護回調函數執行成功")
        else:
            print(f"[TEST] ❌ 保護回調執行錯誤: {len(protection_updates)}/2")
            return False
        
        # 列印保護狀態
        protection_manager.print_protection_status()
        
        print("[TEST] 🎉 累積獲利保護管理器測試通過!")
        return True
        
    except Exception as e:
        print(f"[TEST] ❌ 累積獲利保護管理器測試失敗: {e}")
        return False
    finally:
        # 清理測試檔案
        if os.path.exists(test_db_file):
            os.remove(test_db_file)


def test_stop_loss_state_manager():
    """測試停損狀態管理器"""
    print("\n🧪 測試停損狀態管理器")
    print("=" * 60)
    
    try:
        from multi_group_database import MultiGroupDatabaseManager
        from exit_mechanism_database_extension import extend_database_for_exit_mechanism
        from stop_loss_state_manager import create_stop_loss_state_manager, StopLossType
        
        # 創建測試資料庫
        test_db_file = "test_state_phase4.db"
        if os.path.exists(test_db_file):
            os.remove(test_db_file)
        
        print("[TEST] 📁 創建測試環境...")
        db_manager = MultiGroupDatabaseManager(test_db_file)
        extend_database_for_exit_mechanism(db_manager)
        
        # 創建狀態管理器
        state_manager = create_stop_loss_state_manager(db_manager, console_enabled=True)
        
        # 設定測試回調
        state_transitions = []
        def test_callback(transition_info):
            state_transitions.append(transition_info)
            print(f"[TEST] 🔄 狀態轉換回調: 部位{transition_info.position_id}, {transition_info.from_type.value} → {transition_info.to_type.value}")
        
        state_manager.add_transition_callback(test_callback)
        
        # 插入測試數據 (初始停損狀態的部位)
        print("[TEST] 📊 準備測試數據...")
        with db_manager.get_connection() as conn:
            cursor = conn.cursor()
            
            # 插入策略組
            cursor.execute('''
                INSERT INTO strategy_groups 
                (date, direction, range_high, range_low, status, total_groups, lots_per_group)
                VALUES ('2025-07-05', 'LONG', 22500.0, 22400.0, 'ACTIVE', 1, 1)
            ''')
            group_id = cursor.lastrowid
            
            # 插入初始停損狀態的部位
            cursor.execute('''
                INSERT INTO position_records 
                (group_id, lot_id, direction, entry_price, status, 
                 current_stop_loss, is_initial_stop)
                VALUES (?, 1, 'LONG', 22450.0, 'ACTIVE', 22400.0, TRUE)
            ''', (group_id,))
            position_id = cursor.lastrowid
            
            conn.commit()
        
        # 測試狀態轉換
        print("[TEST] 🔄 測試狀態轉換...")
        
        # 測試1: 轉換為保護性停損
        transition = state_manager.transition_to_protective_stop(
            position_id, 22490.0, "累積獲利保護"
        )
        
        if transition:
            print("[TEST] ✅ 保護性停損轉換成功:")
            print(f"[TEST]   轉換類型: {transition.from_type.value} → {transition.to_type.value}")
            print(f"[TEST]   停損變化: {transition.old_stop_loss} → {transition.new_stop_loss}")
            
            # 驗證狀態
            current_type = state_manager.get_position_stop_type(position_id)
            if current_type == StopLossType.PROTECTIVE:
                print("[TEST] ✅ 停損狀態正確: PROTECTIVE")
            else:
                print(f"[TEST] ❌ 停損狀態錯誤: {current_type}")
                return False
        else:
            print("[TEST] ❌ 保護性停損轉換失敗")
            return False
        
        # 測試2: 轉換為移動停利
        transition2 = state_manager.transition_to_trailing_stop(position_id, 22480.0)
        
        if transition2:
            print("[TEST] ✅ 移動停利轉換成功:")
            print(f"[TEST]   轉換類型: {transition2.from_type.value} → {transition2.to_type.value}")
            
            # 驗證狀態
            current_type = state_manager.get_position_stop_type(position_id)
            if current_type == StopLossType.TRAILING:
                print("[TEST] ✅ 停損狀態正確: TRAILING")
            else:
                print(f"[TEST] ❌ 停損狀態錯誤: {current_type}")
                return False
        else:
            print("[TEST] ❌ 移動停利轉換失敗")
            return False
        
        # 檢查回調是否執行
        if len(state_transitions) == 2:
            print("[TEST] ✅ 狀態轉換回調函數執行成功")
        else:
            print(f"[TEST] ❌ 狀態轉換回調執行錯誤: {len(state_transitions)}/2")
            return False
        
        # 列印狀態管理狀態
        state_manager.print_state_status()
        
        print("[TEST] 🎉 停損狀態管理器測試通過!")
        return True
        
    except Exception as e:
        print(f"[TEST] ❌ 停損狀態管理器測試失敗: {e}")
        return False
    finally:
        # 清理測試檔案
        if os.path.exists(test_db_file):
            os.remove(test_db_file)


def test_protection_calculation_accuracy():
    """測試保護性停損計算準確性"""
    print("\n🧪 測試保護性停損計算準確性")
    print("=" * 60)
    
    try:
        from cumulative_profit_protection_manager import CumulativeProfitProtectionManager
        
        print("[TEST] 🧮 測試保護計算邏輯...")
        
        # 測試案例
        test_cases = [
            {
                'name': '做多 - 2倍保護',
                'direction': 'LONG',
                'entry_price': 22450.0,
                'cumulative_profit': 20.0,
                'protection_multiplier': 2.0,
                'expected_stop': 22490.0  # 22450 + (20 * 2.0)
            },
            {
                'name': '做空 - 2倍保護',
                'direction': 'SHORT',
                'entry_price': 22450.0,
                'cumulative_profit': 15.0,
                'protection_multiplier': 2.0,
                'expected_stop': 22420.0  # 22450 - (15 * 2.0)
            },
            {
                'name': '做多 - 1.5倍保護',
                'direction': 'LONG',
                'entry_price': 22500.0,
                'cumulative_profit': 30.0,
                'protection_multiplier': 1.5,
                'expected_stop': 22545.0  # 22500 + (30 * 1.5)
            }
        ]
        
        # 創建臨時實例進行計算測試
        manager = CumulativeProfitProtectionManager(None, console_enabled=False)
        
        for case in test_cases:
            calculated_stop = manager._calculate_protective_stop_price(
                case['direction'], 
                case['entry_price'], 
                case['cumulative_profit'], 
                case['protection_multiplier']
            )
            
            if abs(calculated_stop - case['expected_stop']) < 0.01:
                print(f"[TEST] ✅ {case['name']}: {calculated_stop} (正確)")
            else:
                print(f"[TEST] ❌ {case['name']}: {calculated_stop} vs {case['expected_stop']} (錯誤)")
                return False
        
        print("[TEST] 🎉 保護性停損計算準確性測試通過!")
        return True
        
    except Exception as e:
        print(f"[TEST] ❌ 保護性停損計算準確性測試失敗: {e}")
        return False


def test_integrated_protection_system():
    """測試整合保護系統"""
    print("\n🧪 測試整合保護系統")
    print("=" * 60)
    
    try:
        print("[TEST] 🔗 測試系統整合...")
        
        # 測試模組導入
        from cumulative_profit_protection_manager import create_cumulative_profit_protection_manager
        from stop_loss_state_manager import create_stop_loss_state_manager
        
        print("[TEST] ✅ 所有保護模組導入成功")
        
        # 測試配置整合
        from exit_mechanism_config import get_default_exit_config_for_multi_group
        config = get_default_exit_config_for_multi_group()
        
        # 驗證保護倍數配置
        expected_multipliers = [None, 2.0, 2.0]  # 第1口無保護，第2、3口2倍保護
        actual_multipliers = [rule.protective_stop_multiplier for rule in config.lot_rules]
        
        if actual_multipliers == expected_multipliers:
            print(f"[TEST] ✅ 保護倍數配置正確: {actual_multipliers}")
        else:
            print(f"[TEST] ❌ 保護倍數配置錯誤: {actual_multipliers} vs {expected_multipliers}")
            return False
        
        print("[TEST] 🎉 整合保護系統測試通過!")
        return True
        
    except Exception as e:
        print(f"[TEST] ❌ 整合保護系統測試失敗: {e}")
        return False


def main():
    """主測試函數"""
    print("🚀 平倉機制 Phase 4 測試開始")
    print("=" * 80)
    print(f"測試時間: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("測試範圍: 累積獲利保護機制 - 保護管理器、狀態管理、計算準確性")
    print("=" * 80)
    
    # 執行測試
    tests = [
        ("累積獲利保護管理器", test_cumulative_profit_protection_manager),
        ("停損狀態管理器", test_stop_loss_state_manager),
        ("保護性停損計算準確性", test_protection_calculation_accuracy),
        ("整合保護系統", test_integrated_protection_system)
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
    print("📊 Phase 4 測試結果總結")
    print("=" * 80)
    
    passed = 0
    total = len(results)
    
    for test_name, result in results:
        status = "✅ 通過" if result else "❌ 失敗"
        print(f"{test_name:25} : {status}")
        if result:
            passed += 1
    
    print("-" * 80)
    print(f"總計: {passed}/{total} 個測試通過")
    
    if passed == total:
        print("🎉 Phase 4 所有測試通過! 累積獲利保護機制準備就緒")
        print("🚀 可以開始 Phase 5: 系統整合與測試")
        return True
    else:
        print("⚠️ 部分測試失敗，請檢查問題後重新測試")
        return False


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
