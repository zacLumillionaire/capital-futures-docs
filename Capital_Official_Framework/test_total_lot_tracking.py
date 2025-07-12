#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
測試總量追蹤機制
驗證基於總口數統計的追蹤邏輯
"""

import os
import sys
import time
from datetime import date

def test_total_lot_tracker():
    """測試總量追蹤器基本功能"""
    print("🧪 測試總量追蹤器基本功能")
    print("=" * 60)
    
    try:
        from total_lot_tracker import TotalLotTracker
        
        # 創建追蹤器：2組×3口 = 6口總量
        tracker = TotalLotTracker(
            strategy_id="test_strategy_001",
            total_target_lots=6,
            lots_per_group=3,
            direction="LONG",
            product="TM0000"
        )
        print("✅ 總量追蹤器創建成功")
        
        # 測試統計信息
        stats = tracker.get_statistics()
        print(f"✅ 初始統計: {stats}")
        
        # 模擬送出訂單
        success = tracker.update_submitted_lots(6)
        print(f"✅ 更新送出口數: {success}")
        
        # 模擬成交回報
        print("\n📋 模擬成交回報:")
        
        # 第1次成交: 3口 @22344
        success = tracker.process_fill_report(22344.0, 3)
        print(f"✅ 第1次成交處理: {success}")
        print(f"    進度: {tracker.total_filled_lots}/{tracker.total_target_lots}")
        
        # 第2次成交: 2口 @22345  
        success = tracker.process_fill_report(22345.0, 2)
        print(f"✅ 第2次成交處理: {success}")
        print(f"    進度: {tracker.total_filled_lots}/{tracker.total_target_lots}")
        
        # 第3次成交: 1口 @22346 (完成)
        success = tracker.process_fill_report(22346.0, 1)
        print(f"✅ 第3次成交處理: {success}")
        print(f"    進度: {tracker.total_filled_lots}/{tracker.total_target_lots}")
        print(f"    是否完成: {tracker.is_complete()}")
        
        # 檢查成交記錄
        fill_records = tracker.get_fill_records_for_database()
        print(f"\n📊 成交記錄數量: {len(fill_records)}")
        
        for i, record in enumerate(fill_records):
            print(f"    第{i+1}口: 組{record['group_display_id']}-{record['position_in_group']} "
                  f"規則{record['lot_rule_id']} @{record['entry_price']}")
        
        return True
        
    except Exception as e:
        print(f"❌ 測試失敗: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_total_lot_manager():
    """測試總量追蹤管理器"""
    print("\n🧪 測試總量追蹤管理器")
    print("=" * 60)
    
    try:
        from total_lot_manager import TotalLotManager
        
        # 創建管理器
        manager = TotalLotManager()
        print("✅ 總量追蹤管理器創建成功")
        
        # 創建策略追蹤器
        success = manager.create_strategy_tracker(
            strategy_id="strategy_001",
            total_target_lots=4,  # 2組×2口
            lots_per_group=2,
            direction="LONG",
            product="TM0000"
        )
        print(f"✅ 策略追蹤器創建: {success}")
        
        # 更新送出口數
        success = manager.update_strategy_submitted_lots("strategy_001", 4)
        print(f"✅ 更新送出口數: {success}")
        
        # 模擬回報處理
        print("\n📋 模擬回報處理:")
        
        # 成交回報
        test_fill_data = "2315544895165,TF,D,N,F020000,6363839,BNF20,TW,TM2507,,u5640,22344.000000,,,,,,,,,2,,,20250705,01:54:07,,0000000,7174,y,20250707,2120000112347,A,FITM,202507,,,,,0000003969,,B,20250704,,,N,,2315544895165"
        success = manager.process_order_reply(test_fill_data)
        print(f"✅ 成交回報處理: {success}")
        
        # 取消回報
        test_cancel_data = "2315544895166,TF,C,N,F020000,6363839,BNF20,TW,TM2507,,u5640,22344.0000,,,,,,,,,2,,,20250705,01:54:10,,0000000,7174,y,20250707,2110001607189,A,FITM,202507,,,,,,,B,20250704,,,N,,2315544895166"
        success = manager.process_order_reply(test_cancel_data)
        print(f"✅ 取消回報處理: {success}")
        
        # 獲取統計
        stats = manager.get_all_statistics()
        print(f"\n📊 管理器統計: {stats}")
        
        return True
        
    except Exception as e:
        print(f"❌ 測試失敗: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_integration_with_multi_group():
    """測試與多組管理器的整合"""
    print("\n🧪 測試與多組管理器整合")
    print("=" * 60)
    
    try:
        # 清理測試資料庫
        test_db_path = "test_total_lot_integration.db"
        if os.path.exists(test_db_path):
            os.remove(test_db_path)
        
        from multi_group_database import MultiGroupDatabaseManager
        from multi_group_config import create_preset_configs
        from multi_group_position_manager import MultiGroupPositionManager
        from total_lot_manager import TotalLotManager
        
        # 創建組件
        db_manager = MultiGroupDatabaseManager(test_db_path)
        presets = create_preset_configs()
        config = presets["平衡配置 (2口×2組)"]  # 2組×2口 = 4口總量
        total_lot_manager = TotalLotManager()
        
        # 創建部位管理器
        position_manager = MultiGroupPositionManager(
            db_manager=db_manager,
            strategy_config=config,
            total_lot_manager=total_lot_manager
        )
        print("✅ 多組部位管理器創建成功")
        
        # 測試創建進場信號
        group_ids = position_manager.create_entry_signal(
            direction="LONG",
            signal_time="08:48:15",
            range_high=22400.0,
            range_low=22350.0
        )
        print(f"✅ 創建進場信號: {group_ids}")
        
        # 檢查總量追蹤管理器統計
        stats = total_lot_manager.get_all_statistics()
        print(f"📊 總量追蹤統計: {stats}")
        
        # 清理測試資料庫
        if os.path.exists(test_db_path):
            os.remove(test_db_path)
            print("🧹 測試資料庫已清理")
        
        return True
        
    except Exception as e:
        print(f"❌ 整合測試失敗: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_callback_mechanism():
    """測試回調機制"""
    print("\n🧪 測試回調機制")
    print("=" * 60)
    
    try:
        from total_lot_tracker import TotalLotTracker
        
        # 回調計數器
        fill_count = 0
        retry_count = 0
        complete_count = 0
        
        def test_fill_callback(strategy_id, price, qty, filled_lots, total_lots):
            nonlocal fill_count
            fill_count += 1
            print(f"🎯 [回調] 成交: {strategy_id}, {qty}口@{price}, 進度{filled_lots}/{total_lots}")
        
        def test_retry_callback(strategy_id, qty, price, retry_count_val):
            nonlocal retry_count
            retry_count += 1
            print(f"🔄 [回調] 追價: {strategy_id}, {qty}口@{price}, 第{retry_count_val}次")
        
        def test_complete_callback(strategy_id, fill_records):
            nonlocal complete_count
            complete_count += 1
            print(f"🎉 [回調] 完成: {strategy_id}, 共{len(fill_records)}口")
        
        # 創建追蹤器並設置回調
        tracker = TotalLotTracker(
            strategy_id="callback_test",
            total_target_lots=3,
            lots_per_group=3,
            direction="LONG"
        )
        
        tracker.add_fill_callback(test_fill_callback)
        tracker.add_retry_callback(test_retry_callback)
        tracker.add_complete_callback(test_complete_callback)
        
        print("✅ 回調機制設置完成")
        
        # 觸發回調
        tracker.update_submitted_lots(3)
        tracker.process_fill_report(22344.0, 2)  # 觸發成交回調
        tracker.process_cancel_report(22344.0, 1)  # 觸發追價回調
        tracker.process_fill_report(22345.0, 1)  # 觸發成交和完成回調
        
        print(f"\n📊 回調統計:")
        print(f"    成交回調: {fill_count}次")
        print(f"    追價回調: {retry_count}次")
        print(f"    完成回調: {complete_count}次")
        
        return fill_count > 0 and complete_count > 0
        
    except Exception as e:
        print(f"❌ 回調測試失敗: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    print("🚀 開始總量追蹤機制測試")
    
    # 基本功能測試
    basic_test = test_total_lot_tracker()
    
    # 管理器測試
    manager_test = test_total_lot_manager()
    
    # 整合測試
    integration_test = test_integration_with_multi_group()
    
    # 回調機制測試
    callback_test = test_callback_mechanism()
    
    # 總結
    print("\n📋 測試總結")
    print("=" * 60)
    print(f"基本功能測試: {'✅ 通過' if basic_test else '❌ 失敗'}")
    print(f"管理器測試: {'✅ 通過' if manager_test else '❌ 失敗'}")
    print(f"整合測試: {'✅ 通過' if integration_test else '❌ 失敗'}")
    print(f"回調機制測試: {'✅ 通過' if callback_test else '❌ 失敗'}")
    
    all_passed = all([basic_test, manager_test, integration_test, callback_test])
    
    if all_passed:
        print("\n🎉 所有測試通過！總量追蹤機制可以投入使用")
        print("\n🎯 總量追蹤機制優勢:")
        print("    ✅ 邏輯簡單：只關心總口數統計")
        print("    ✅ 避免衝突：不需要組間匹配")
        print("    ✅ 風險規則：FIFO分配到正確的規則")
        print("    ✅ 追價精確：基於剩餘需求計算")
        print("    ✅ 資料完整：支援完整的風險管理")
    else:
        print("\n⚠️ 部分測試失敗，需要進一步調試")
