#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
平倉機制 Phase 3 測試腳本
測試分層移動停利機制的完整功能，包含15/40/65點分層啟動
"""

import os
import sys
import sqlite3
import time
from datetime import datetime

def test_trailing_stop_activator():
    """測試移動停利啟動器"""
    print("🧪 測試移動停利啟動器")
    print("=" * 60)
    
    try:
        from multi_group_database import MultiGroupDatabaseManager
        from exit_mechanism_database_extension import extend_database_for_exit_mechanism
        from trailing_stop_activator import create_trailing_stop_activator
        
        # 創建測試資料庫
        test_db_file = "test_trailing_phase3.db"
        if os.path.exists(test_db_file):
            os.remove(test_db_file)
        
        print("[TEST] 📁 創建測試資料庫...")
        db_manager = MultiGroupDatabaseManager(test_db_file)
        extend_database_for_exit_mechanism(db_manager)
        
        # 創建啟動器
        activator = create_trailing_stop_activator(db_manager, console_enabled=True)
        
        # 設定測試回調
        activated_positions = []
        def test_callback(activation_info):
            activated_positions.append(activation_info)
            print(f"[TEST] 🎯 回調觸發: 部位{activation_info.position_id}, {activation_info.activation_points}點啟動")
        
        activator.add_activation_callback(test_callback)
        
        # 插入測試數據 (3口不同啟動點位)
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
            
            # 插入3口部位，不同啟動點位
            test_positions = [
                (group_id, 1, 'LONG', 22450.0, 'ACTIVE', 15),  # 第1口: 15點啟動
                (group_id, 2, 'LONG', 22450.0, 'ACTIVE', 40),  # 第2口: 40點啟動
                (group_id, 3, 'LONG', 22450.0, 'ACTIVE', 65)   # 第3口: 65點啟動
            ]
            
            for group_id, lot_id, direction, entry_price, status, activation_points in test_positions:
                cursor.execute('''
                    INSERT INTO position_records 
                    (group_id, lot_id, direction, entry_price, status, 
                     trailing_activated, is_initial_stop, trailing_activation_points)
                    VALUES (?, ?, ?, ?, ?, FALSE, TRUE, ?)
                ''', (group_id, lot_id, direction, entry_price, status, activation_points))
            
            conn.commit()
        
        # 測試分層啟動
        print("[TEST] 🎯 測試分層啟動...")
        
        # 測試1: 價格上漲10點 (無啟動)
        activations = activator.check_trailing_stop_activation(22460.0)
        print(f"[TEST] 價格22460 (+10點): 啟動數量 {len(activations)}")
        
        # 測試2: 價格上漲20點 (第1口啟動)
        activations = activator.check_trailing_stop_activation(22470.0)
        print(f"[TEST] 價格22470 (+20點): 啟動數量 {len(activations)}")
        
        # 測試3: 價格上漲50點 (第2口啟動)
        activations = activator.check_trailing_stop_activation(22500.0)
        print(f"[TEST] 價格22500 (+50點): 啟動數量 {len(activations)}")
        
        # 測試4: 價格上漲70點 (第3口啟動)
        activations = activator.check_trailing_stop_activation(22520.0)
        print(f"[TEST] 價格22520 (+70點): 啟動數量 {len(activations)}")
        
        # 驗證啟動結果
        total_activated = len(activated_positions)
        if total_activated == 3:
            print("[TEST] ✅ 所有3口都已啟動")
            
            # 驗證啟動點位
            activation_points = [pos.activation_points for pos in activated_positions]
            expected_points = [15, 40, 65]
            
            if sorted(activation_points) == sorted(expected_points):
                print("[TEST] ✅ 啟動點位正確: 15/40/65點")
            else:
                print(f"[TEST] ❌ 啟動點位錯誤: {activation_points}")
                return False
        else:
            print(f"[TEST] ❌ 啟動數量錯誤: {total_activated}/3")
            return False
        
        # 列印啟動狀態
        activator.print_activation_status()
        
        print("[TEST] 🎉 移動停利啟動器測試通過!")
        return True
        
    except Exception as e:
        print(f"[TEST] ❌ 移動停利啟動器測試失敗: {e}")
        return False
    finally:
        # 清理測試檔案
        if os.path.exists(test_db_file):
            os.remove(test_db_file)


def test_peak_price_tracker():
    """測試峰值價格追蹤器"""
    print("\n🧪 測試峰值價格追蹤器")
    print("=" * 60)
    
    try:
        from multi_group_database import MultiGroupDatabaseManager
        from exit_mechanism_database_extension import extend_database_for_exit_mechanism
        from peak_price_tracker import create_peak_price_tracker
        
        # 創建測試資料庫
        test_db_file = "test_peak_phase3.db"
        if os.path.exists(test_db_file):
            os.remove(test_db_file)
        
        print("[TEST] 📁 創建測試環境...")
        db_manager = MultiGroupDatabaseManager(test_db_file)
        extend_database_for_exit_mechanism(db_manager)
        
        # 創建追蹤器
        tracker = create_peak_price_tracker(db_manager, console_enabled=True)
        
        # 設定測試回調
        peak_updates = []
        def test_callback(update_info):
            peak_updates.append(update_info)
            print(f"[TEST] 📈 峰值更新: 部位{update_info.position_id}, {update_info.old_peak} → {update_info.new_peak}")
        
        tracker.add_update_callback(test_callback)
        
        # 插入測試數據 (已啟動移動停利的部位)
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
            
            # 插入已啟動移動停利的部位
            cursor.execute('''
                INSERT INTO position_records 
                (group_id, lot_id, direction, entry_price, status, 
                 trailing_activated, peak_price)
                VALUES (?, 1, 'LONG', 22450.0, 'ACTIVE', TRUE, 22470.0)
            ''', (group_id,))
            position_id = cursor.lastrowid
            
            conn.commit()
        
        # 測試峰值更新
        print("[TEST] 📈 測試峰值更新...")
        
        # 測試1: 價格下跌 (不更新峰值)
        updates = tracker.update_peak_prices(22460.0)
        print(f"[TEST] 價格22460 (下跌): 更新數量 {len(updates)}")
        
        # 測試2: 價格創新高 (更新峰值)
        updates = tracker.update_peak_prices(22480.0)
        print(f"[TEST] 價格22480 (新高): 更新數量 {len(updates)}")
        
        # 測試3: 再次創新高
        updates = tracker.update_peak_prices(22490.0)
        print(f"[TEST] 價格22490 (再新高): 更新數量 {len(updates)}")
        
        # 驗證峰值更新
        if len(peak_updates) >= 2:
            print("[TEST] ✅ 峰值更新正常")
            
            # 檢查最終峰值
            current_peaks = tracker.get_current_peaks()
            if position_id in current_peaks and current_peaks[position_id] == 22490.0:
                print("[TEST] ✅ 最終峰值正確: 22490.0")
            else:
                print(f"[TEST] ❌ 最終峰值錯誤: {current_peaks.get(position_id)}")
                return False
        else:
            print(f"[TEST] ❌ 峰值更新次數不足: {len(peak_updates)}")
            return False
        
        # 列印追蹤狀態
        tracker.print_peak_status()
        
        print("[TEST] 🎉 峰值價格追蹤器測試通過!")
        return True
        
    except Exception as e:
        print(f"[TEST] ❌ 峰值價格追蹤器測試失敗: {e}")
        return False
    finally:
        # 清理測試檔案
        if os.path.exists(test_db_file):
            os.remove(test_db_file)


def test_drawdown_monitor():
    """測試20%回撤監控器"""
    print("\n🧪 測試20%回撤監控器")
    print("=" * 60)
    
    try:
        from multi_group_database import MultiGroupDatabaseManager
        from exit_mechanism_database_extension import extend_database_for_exit_mechanism
        from drawdown_monitor import create_drawdown_monitor
        
        # 創建測試資料庫
        test_db_file = "test_drawdown_phase3.db"
        if os.path.exists(test_db_file):
            os.remove(test_db_file)
        
        print("[TEST] 📁 創建測試環境...")
        db_manager = MultiGroupDatabaseManager(test_db_file)
        extend_database_for_exit_mechanism(db_manager)
        
        # 創建監控器
        monitor = create_drawdown_monitor(db_manager, console_enabled=True)
        
        # 設定測試回調
        triggered_drawdowns = []
        def test_callback(trigger_info):
            triggered_drawdowns.append(trigger_info)
            print(f"[TEST] 🚨 回撤觸發: 部位{trigger_info.position_id}, 回撤{trigger_info.drawdown_ratio:.1%}")
        
        monitor.add_drawdown_callback(test_callback)
        
        # 插入測試數據 (已啟動移動停利，峰值22500)
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
            
            # 插入已啟動移動停利的部位，峰值22500
            cursor.execute('''
                INSERT INTO position_records 
                (group_id, lot_id, direction, entry_price, status, 
                 trailing_activated, peak_price, trailing_pullback_ratio)
                VALUES (?, 1, 'LONG', 22450.0, 'ACTIVE', TRUE, 22500.0, 0.20)
            ''', (group_id,))
            position_id = cursor.lastrowid
            
            conn.commit()
        
        # 測試回撤監控
        print("[TEST] 📉 測試回撤監控...")
        
        # 測試1: 輕微回撤 (不觸發)
        triggers = monitor.monitor_drawdown_triggers(22480.0)  # 回撤0.89%
        print(f"[TEST] 價格22480 (回撤0.89%): 觸發數量 {len(triggers)}")
        
        # 測試2: 15%回撤 (不觸發)
        triggers = monitor.monitor_drawdown_triggers(22425.0)  # 回撤3.33%
        print(f"[TEST] 價格22425 (回撤3.33%): 觸發數量 {len(triggers)}")
        
        # 測試3: 20%回撤 (觸發)
        triggers = monitor.monitor_drawdown_triggers(22400.0)  # 回撤4.44%
        print(f"[TEST] 價格22400 (回撤4.44%): 觸發數量 {len(triggers)}")
        
        # 驗證回撤觸發
        if len(triggered_drawdowns) > 0:
            trigger = triggered_drawdowns[0]
            print("[TEST] ✅ 回撤觸發成功:")
            print(f"[TEST]   部位ID: {trigger.position_id}")
            print(f"[TEST]   峰值價格: {trigger.peak_price}")
            print(f"[TEST]   當前價格: {trigger.current_price}")
            print(f"[TEST]   回撤比例: {trigger.drawdown_ratio:.1%}")
            print(f"[TEST]   回撤點數: {trigger.drawdown_points:.1f} 點")
            
            # 驗證回撤計算
            expected_drawdown = (22500.0 - 22400.0) / 22500.0
            if abs(trigger.drawdown_ratio - expected_drawdown) < 0.001:
                print("[TEST] ✅ 回撤計算正確")
            else:
                print(f"[TEST] ❌ 回撤計算錯誤: {trigger.drawdown_ratio:.3%} vs {expected_drawdown:.3%}")
                return False
        else:
            print("[TEST] ❌ 回撤未觸發")
            return False
        
        # 列印監控狀態
        monitor.print_monitoring_status()
        
        print("[TEST] 🎉 20%回撤監控器測試通過!")
        return True
        
    except Exception as e:
        print(f"[TEST] ❌ 20%回撤監控器測試失敗: {e}")
        return False
    finally:
        # 清理測試檔案
        if os.path.exists(test_db_file):
            os.remove(test_db_file)


def test_integrated_trailing_system():
    """測試整合移動停利系統"""
    print("\n🧪 測試整合移動停利系統")
    print("=" * 60)
    
    try:
        print("[TEST] 🔗 測試系統整合...")
        
        # 測試模組導入
        from trailing_stop_activator import create_trailing_stop_activator
        from peak_price_tracker import create_peak_price_tracker
        from drawdown_monitor import create_drawdown_monitor
        
        print("[TEST] ✅ 所有移動停利模組導入成功")
        
        # 測試配置整合
        from exit_mechanism_config import get_default_exit_config_for_multi_group
        config = get_default_exit_config_for_multi_group()
        
        # 驗證分層配置
        expected_activations = [15, 40, 65]
        actual_activations = [rule.trailing_activation_points for rule in config.lot_rules]
        
        if actual_activations == expected_activations:
            print(f"[TEST] ✅ 分層配置正確: {actual_activations}")
        else:
            print(f"[TEST] ❌ 分層配置錯誤: {actual_activations} vs {expected_activations}")
            return False
        
        # 驗證回撤比例
        expected_pullback = 0.20
        actual_pullbacks = [rule.trailing_pullback_ratio for rule in config.lot_rules]
        
        if all(pb == expected_pullback for pb in actual_pullbacks):
            print(f"[TEST] ✅ 回撤比例正確: {expected_pullback}")
        else:
            print(f"[TEST] ❌ 回撤比例錯誤: {actual_pullbacks}")
            return False
        
        print("[TEST] 🎉 整合移動停利系統測試通過!")
        return True
        
    except Exception as e:
        print(f"[TEST] ❌ 整合移動停利系統測試失敗: {e}")
        return False


def main():
    """主測試函數"""
    print("🚀 平倉機制 Phase 3 測試開始")
    print("=" * 80)
    print(f"測試時間: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("測試範圍: 分層移動停利機制 - 啟動器、峰值追蹤、回撤監控")
    print("=" * 80)
    
    # 執行測試
    tests = [
        ("移動停利啟動器", test_trailing_stop_activator),
        ("峰值價格追蹤器", test_peak_price_tracker),
        ("20%回撤監控器", test_drawdown_monitor),
        ("整合移動停利系統", test_integrated_trailing_system)
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
    print("📊 Phase 3 測試結果總結")
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
        print("🎉 Phase 3 所有測試通過! 分層移動停利機制準備就緒")
        print("🚀 可以開始 Phase 4: 累積獲利保護機制")
        return True
    else:
        print("⚠️ 部分測試失敗，請檢查問題後重新測試")
        return False


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
