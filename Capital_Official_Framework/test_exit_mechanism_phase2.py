#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
平倉機制 Phase 2 測試腳本
測試區間邊緣停損機制的完整功能
"""

import os
import sys
import sqlite3
import time
from datetime import datetime

def test_initial_stop_loss_manager():
    """測試初始停損管理器"""
    print("🧪 測試初始停損管理器")
    print("=" * 60)
    
    try:
        from multi_group_database import MultiGroupDatabaseManager
        from exit_mechanism_database_extension import extend_database_for_exit_mechanism
        from initial_stop_loss_manager import create_initial_stop_loss_manager
        
        # 創建測試資料庫
        test_db_file = "test_stop_loss_phase2.db"
        if os.path.exists(test_db_file):
            os.remove(test_db_file)
        
        print("[TEST] 📁 創建測試資料庫...")
        db_manager = MultiGroupDatabaseManager(test_db_file)
        extend_database_for_exit_mechanism(db_manager)
        
        # 創建停損管理器
        print("[TEST] 🛡️ 創建停損管理器...")
        stop_loss_manager = create_initial_stop_loss_manager(db_manager, console_enabled=True)
        
        # 模擬插入測試部位
        print("[TEST] 📊 插入測試部位...")
        with db_manager.get_connection() as conn:
            cursor = conn.cursor()
            
            # 插入策略組
            cursor.execute('''
                INSERT INTO strategy_groups 
                (date, direction, range_high, range_low, status, total_groups, lots_per_group)
                VALUES ('2025-07-05', 'LONG', 22500.0, 22400.0, 'ACTIVE', 1, 3)
            ''')
            group_id = cursor.lastrowid
            
            # 插入測試部位
            test_positions = [
                (group_id, 1, 'LONG', 22450.0, 'ACTIVE'),
                (group_id, 2, 'LONG', 22460.0, 'ACTIVE'),
                (group_id, 3, 'LONG', 22470.0, 'ACTIVE')
            ]
            
            for group_id, lot_id, direction, entry_price, status in test_positions:
                cursor.execute('''
                    INSERT INTO position_records 
                    (group_id, lot_id, direction, entry_price, status, created_at)
                    VALUES (?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
                ''', (group_id, lot_id, direction, entry_price, status))
            
            conn.commit()
        
        # 測試停損設定
        print("[TEST] 🎯 測試停損設定...")
        range_data = {'range_high': 22500.0, 'range_low': 22400.0}
        success = stop_loss_manager.setup_initial_stop_loss_for_group(group_id, range_data)
        
        if success:
            print("[TEST] ✅ 停損設定成功")
            
            # 驗證停損資訊
            stop_losses = stop_loss_manager.get_active_stop_losses()
            print(f"[TEST] 📊 活躍停損數量: {len(stop_losses)}")
            
            for stop_loss in stop_losses:
                print(f"[TEST]   部位{stop_loss.position_id}: 停損@{stop_loss.stop_loss_price}")
            
            # 列印停損狀態
            stop_loss_manager.print_stop_loss_status()
            
        else:
            print("[TEST] ❌ 停損設定失敗")
            return False
        
        print("[TEST] 🎉 初始停損管理器測試通過!")
        return True
        
    except Exception as e:
        print(f"[TEST] ❌ 初始停損管理器測試失敗: {e}")
        return False
    finally:
        # 清理測試檔案
        if os.path.exists(test_db_file):
            os.remove(test_db_file)


def test_stop_loss_monitor():
    """測試停損監控器"""
    print("\n🧪 測試停損監控器")
    print("=" * 60)
    
    try:
        from multi_group_database import MultiGroupDatabaseManager
        from exit_mechanism_database_extension import extend_database_for_exit_mechanism
        from initial_stop_loss_manager import create_initial_stop_loss_manager
        from stop_loss_monitor import create_stop_loss_monitor
        
        # 創建測試資料庫
        test_db_file = "test_monitor_phase2.db"
        if os.path.exists(test_db_file):
            os.remove(test_db_file)
        
        print("[TEST] 📁 創建測試環境...")
        db_manager = MultiGroupDatabaseManager(test_db_file)
        extend_database_for_exit_mechanism(db_manager)
        
        # 創建管理器
        stop_loss_manager = create_initial_stop_loss_manager(db_manager, console_enabled=False)
        monitor = create_stop_loss_monitor(db_manager, console_enabled=True)
        
        # 設定測試回調
        triggered_stops = []
        def test_callback(trigger_info):
            triggered_stops.append(trigger_info)
            print(f"[TEST] 🚨 回調觸發: 部位{trigger_info.position_id}, 價格{trigger_info.current_price}")
        
        monitor.add_stop_loss_callback(test_callback)
        
        # 插入測試數據
        print("[TEST] 📊 準備測試數據...")
        with db_manager.get_connection() as conn:
            cursor = conn.cursor()
            
            # 插入策略組 (做多，停損在22400)
            cursor.execute('''
                INSERT INTO strategy_groups 
                (date, direction, range_high, range_low, status, total_groups, lots_per_group)
                VALUES ('2025-07-05', 'LONG', 22500.0, 22400.0, 'ACTIVE', 1, 1)
            ''')
            group_id = cursor.lastrowid
            
            # 插入部位
            cursor.execute('''
                INSERT INTO position_records 
                (group_id, lot_id, direction, entry_price, status, current_stop_loss, is_initial_stop)
                VALUES (?, 1, 'LONG', 22450.0, 'ACTIVE', 22400.0, TRUE)
            ''', (group_id,))
            
            conn.commit()
        
        # 測試價格監控
        print("[TEST] 🔍 測試價格監控...")
        
        # 測試1: 正常價格 (不觸發)
        triggers = monitor.monitor_stop_loss_breach(22420.0)
        print(f"[TEST] 正常價格 22420: 觸發數量 {len(triggers)}")
        
        # 測試2: 觸發停損價格
        triggers = monitor.monitor_stop_loss_breach(22399.0)  # 跌破停損點
        print(f"[TEST] 觸發價格 22399: 觸發數量 {len(triggers)}")
        
        if len(triggers) > 0:
            trigger = triggers[0]
            print(f"[TEST] ✅ 停損觸發成功:")
            print(f"[TEST]   部位ID: {trigger.position_id}")
            print(f"[TEST]   觸發價格: {trigger.current_price}")
            print(f"[TEST]   停損價格: {trigger.stop_loss_price}")
            print(f"[TEST]   突破金額: {trigger.breach_amount:.1f} 點")
        
        # 檢查回調是否執行
        if len(triggered_stops) > 0:
            print("[TEST] ✅ 回調函數執行成功")
        else:
            print("[TEST] ❌ 回調函數未執行")
            return False
        
        # 列印監控狀態
        monitor.print_monitoring_status()
        
        print("[TEST] 🎉 停損監控器測試通過!")
        return True
        
    except Exception as e:
        print(f"[TEST] ❌ 停損監控器測試失敗: {e}")
        return False
    finally:
        # 清理測試檔案
        if os.path.exists(test_db_file):
            os.remove(test_db_file)


def test_stop_loss_executor():
    """測試停損執行器"""
    print("\n🧪 測試停損執行器")
    print("=" * 60)
    
    try:
        from multi_group_database import MultiGroupDatabaseManager
        from exit_mechanism_database_extension import extend_database_for_exit_mechanism
        from stop_loss_executor import create_stop_loss_executor
        from stop_loss_monitor import StopLossTrigger
        
        # 創建測試資料庫
        test_db_file = "test_executor_phase2.db"
        if os.path.exists(test_db_file):
            os.remove(test_db_file)
        
        print("[TEST] 📁 創建測試環境...")
        db_manager = MultiGroupDatabaseManager(test_db_file)
        extend_database_for_exit_mechanism(db_manager)
        
        # 創建執行器 (模擬模式)
        executor = create_stop_loss_executor(
            db_manager, 
            virtual_real_order_manager=None,  # 使用模擬模式
            console_enabled=True
        )
        
        # 插入測試數據
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
            
            # 插入部位
            cursor.execute('''
                INSERT INTO position_records 
                (group_id, lot_id, direction, entry_price, status, current_stop_loss)
                VALUES (?, 1, 'LONG', 22450.0, 'ACTIVE', 22400.0)
            ''', (group_id,))
            position_id = cursor.lastrowid
            
            conn.commit()
        
        # 創建模擬觸發資訊
        print("[TEST] 🚨 創建模擬停損觸發...")
        trigger_info = StopLossTrigger(
            position_id=position_id,
            group_id=group_id,
            direction="LONG",
            current_price=22399.0,
            stop_loss_price=22400.0,
            trigger_time=datetime.now().strftime('%H:%M:%S'),
            trigger_reason="測試停損觸發",
            breach_amount=1.0
        )
        
        # 執行停損
        print("[TEST] ⚡ 執行停損...")
        result = executor.execute_stop_loss(trigger_info)
        
        if result.success:
            print("[TEST] ✅ 停損執行成功:")
            print(f"[TEST]   訂單ID: {result.order_id}")
            print(f"[TEST]   執行價格: {result.execution_price}")
            print(f"[TEST]   損益: {result.pnl:.1f} 點")
            
            # 驗證資料庫更新
            with db_manager.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute('SELECT status, exit_price, realized_pnl FROM position_records WHERE id = ?', (position_id,))
                row = cursor.fetchone()
                
                if row and row[0] == 'EXITED':
                    print("[TEST] ✅ 資料庫狀態更新成功")
                    print(f"[TEST]   出場價格: {row[1]}")
                    print(f"[TEST]   實現損益: {row[2]:.1f} 點")
                else:
                    print("[TEST] ❌ 資料庫狀態更新失敗")
                    return False
        else:
            print(f"[TEST] ❌ 停損執行失敗: {result.error_message}")
            return False
        
        # 列印執行摘要
        executor.print_execution_summary()
        
        print("[TEST] 🎉 停損執行器測試通過!")
        return True
        
    except Exception as e:
        print(f"[TEST] ❌ 停損執行器測試失敗: {e}")
        return False
    finally:
        # 清理測試檔案
        if os.path.exists(test_db_file):
            os.remove(test_db_file)


def test_integrated_stop_loss_system():
    """測試整合停損系統"""
    print("\n🧪 測試整合停損系統")
    print("=" * 60)
    
    try:
        print("[TEST] 🔗 測試系統整合...")
        
        # 測試模組導入
        from initial_stop_loss_manager import create_initial_stop_loss_manager
        from stop_loss_monitor import create_stop_loss_monitor
        from stop_loss_executor import create_stop_loss_executor
        
        print("[TEST] ✅ 所有停損模組導入成功")
        
        # 測試配置整合
        from exit_mechanism_config import get_default_exit_config_for_multi_group
        config = get_default_exit_config_for_multi_group()
        
        print(f"[TEST] ✅ 平倉配置載入成功: {config.total_lots}口")
        
        # 測試資料庫整合
        from multi_group_database import MultiGroupDatabaseManager
        from exit_mechanism_database_extension import extend_database_for_exit_mechanism
        
        test_db_file = "test_integrated_phase2.db"
        if os.path.exists(test_db_file):
            os.remove(test_db_file)
        
        db_manager = MultiGroupDatabaseManager(test_db_file)
        extend_database_for_exit_mechanism(db_manager)
        
        print("[TEST] ✅ 資料庫整合成功")
        
        print("[TEST] 🎉 整合停損系統測試通過!")
        return True
        
    except Exception as e:
        print(f"[TEST] ❌ 整合停損系統測試失敗: {e}")
        return False
    finally:
        # 清理測試檔案
        if os.path.exists(test_db_file):
            os.remove(test_db_file)


def main():
    """主測試函數"""
    print("🚀 平倉機制 Phase 2 測試開始")
    print("=" * 80)
    print(f"測試時間: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("測試範圍: 區間邊緣停損機制 - 管理器、監控器、執行器")
    print("=" * 80)
    
    # 執行測試
    tests = [
        ("初始停損管理器", test_initial_stop_loss_manager),
        ("停損監控器", test_stop_loss_monitor),
        ("停損執行器", test_stop_loss_executor),
        ("整合停損系統", test_integrated_stop_loss_system)
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
    print("📊 Phase 2 測試結果總結")
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
        print("🎉 Phase 2 所有測試通過! 區間邊緣停損機制準備就緒")
        print("🚀 可以開始 Phase 3: 分層移動停利機制")
        return True
    else:
        print("⚠️ 部分測試失敗，請檢查問題後重新測試")
        return False


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
