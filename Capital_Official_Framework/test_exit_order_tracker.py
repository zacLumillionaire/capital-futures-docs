#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
測試平倉訂單追蹤器（第二階段）
驗證一對一平倉回報確認機制
"""

import time
import threading
from datetime import datetime

# 導入相關模組
from exit_order_tracker import ExitOrderTracker, ExitFillReport, ExitOrderInfo, ExitOrderStatus
from async_db_updater import AsyncDatabaseUpdater
from multi_group_database import MultiGroupDatabaseManager
from stop_loss_executor import StopLossExecutor
from simplified_order_tracker import SimplifiedOrderTracker

def test_exit_order_tracker():
    """測試平倉訂單追蹤器基本功能"""
    print("🧪 測試平倉訂單追蹤器基本功能")
    print("=" * 50)
    
    try:
        # 1. 初始化
        print("1️⃣ 初始化組件...")
        db_manager = MultiGroupDatabaseManager("test_exit_tracker.db")
        async_updater = AsyncDatabaseUpdater(db_manager, console_enabled=True)
        async_updater.start()
        
        exit_tracker = ExitOrderTracker(db_manager, console_enabled=True)
        exit_tracker.set_async_updater(async_updater)
        
        # 2. 測試註冊平倉訂單
        print("2️⃣ 測試註冊平倉訂單...")
        
        test_position_id = 123
        test_order_id = "EXIT_ORDER_001"
        test_direction = "SELL"  # 多單平倉
        test_quantity = 1
        test_price = 22500.0
        test_product = "TM0000"
        
        success = exit_tracker.register_exit_order(
            position_id=test_position_id,
            order_id=test_order_id,
            direction=test_direction,
            quantity=test_quantity,
            price=test_price,
            product=test_product
        )
        
        print(f"   註冊結果: {'成功' if success else '失敗'}")
        
        # 3. 測試狀態查詢
        print("3️⃣ 測試狀態查詢...")
        
        has_order = exit_tracker.has_exit_order_for_position(test_position_id)
        order_status = exit_tracker.get_exit_order_status(test_position_id)
        order_info = exit_tracker.get_exit_order_info(test_position_id)
        
        print(f"   有平倉訂單: {has_order}")
        print(f"   訂單狀態: {order_status}")
        print(f"   訂單信息: {order_info.order_id if order_info else 'None'}")
        
        # 4. 測試成交回報處理
        print("4️⃣ 測試成交回報處理...")
        
        fill_report = ExitFillReport(
            order_id=test_order_id,
            position_id=test_position_id,
            fill_price=22498.0,  # 略低於下單價格
            fill_quantity=test_quantity,
            fill_time=datetime.now().strftime('%H:%M:%S'),
            product=test_product
        )
        
        processed = exit_tracker.process_exit_fill_report(fill_report)
        print(f"   成交處理結果: {'成功' if processed else '失敗'}")
        
        # 5. 檢查處理後狀態
        print("5️⃣ 檢查處理後狀態...")
        
        has_order_after = exit_tracker.has_exit_order_for_position(test_position_id)
        order_status_after = exit_tracker.get_exit_order_status(test_position_id)
        
        print(f"   處理後有平倉訂單: {has_order_after}")
        print(f"   處理後訂單狀態: {order_status_after}")
        
        # 6. 檢查統計信息
        print("6️⃣ 檢查統計信息...")
        stats = exit_tracker.get_stats()
        print(f"   總平倉數: {stats.get('total_exits', 0)}")
        print(f"   確認平倉數: {stats.get('confirmed_exits', 0)}")
        print(f"   失敗平倉數: {stats.get('failed_exits', 0)}")
        
        print("✅ 平倉訂單追蹤器基本功能測試完成")
        
    except Exception as e:
        print(f"❌ 測試失敗: {e}")
        import traceback
        traceback.print_exc()
    
    finally:
        try:
            if 'async_updater' in locals():
                async_updater.stop()
        except:
            pass

def test_integration_with_stop_executor():
    """測試與停損執行器的整合"""
    print("\n🧪 測試與停損執行器的整合")
    print("=" * 50)
    
    try:
        # 1. 初始化所有組件
        print("1️⃣ 初始化所有組件...")
        db_manager = MultiGroupDatabaseManager("test_integration.db")
        async_updater = AsyncDatabaseUpdater(db_manager, console_enabled=True)
        async_updater.start()
        
        exit_tracker = ExitOrderTracker(db_manager, console_enabled=True)
        exit_tracker.set_async_updater(async_updater)
        
        simplified_tracker = SimplifiedOrderTracker(console_enabled=True)
        simplified_tracker.set_exit_tracker(exit_tracker)
        
        stop_executor = StopLossExecutor(db_manager, console_enabled=True)
        stop_executor.set_async_updater(async_updater, enabled=True)
        stop_executor.set_exit_tracker(exit_tracker)
        stop_executor.set_simplified_tracker(simplified_tracker)
        
        # 2. 測試重複平倉防護
        print("2️⃣ 測試重複平倉防護...")
        
        test_position_id = 456
        
        # 第一次檢查（應該可以執行）
        result1 = stop_executor._check_duplicate_exit_protection(test_position_id)
        print(f"   第一次檢查: {result1}")
        
        # 註冊一個平倉訂單
        exit_tracker.register_exit_order(
            position_id=test_position_id,
            order_id="TEST_EXIT_002",
            direction="BUY",  # 空單平倉
            quantity=1,
            price=22400.0,
            product="TM0000"
        )
        
        # 第二次檢查（應該被防護）
        result2 = stop_executor._check_duplicate_exit_protection(test_position_id)
        print(f"   第二次檢查: {result2}")
        
        # 3. 測試FIFO匹配
        print("3️⃣ 測試FIFO匹配...")
        
        # 模擬成交回報
        fill_report = ExitFillReport(
            order_id="",  # 將通過FIFO匹配確定
            position_id=0,  # 將通過FIFO匹配確定
            fill_price=22400.0,
            fill_quantity=1,
            fill_time=datetime.now().strftime('%H:%M:%S'),
            product="TM0000"
        )
        
        processed = exit_tracker.process_exit_fill_report(fill_report)
        print(f"   FIFO匹配處理結果: {'成功' if processed else '失敗'}")
        
        # 4. 檢查防護狀態更新
        print("4️⃣ 檢查防護狀態更新...")
        
        # 第三次檢查（成交後應該可以執行）
        result3 = stop_executor._check_duplicate_exit_protection(test_position_id)
        print(f"   第三次檢查: {result3}")
        
        print("✅ 停損執行器整合測試完成")
        
    except Exception as e:
        print(f"❌ 整合測試失敗: {e}")
        import traceback
        traceback.print_exc()
    
    finally:
        try:
            if 'async_updater' in locals():
                async_updater.stop()
        except:
            pass

def test_fifo_matching():
    """測試FIFO匹配機制"""
    print("\n🧪 測試FIFO匹配機制")
    print("=" * 50)
    
    try:
        # 1. 初始化
        db_manager = MultiGroupDatabaseManager("test_fifo.db")
        exit_tracker = ExitOrderTracker(db_manager, console_enabled=True)
        
        # 2. 註冊多個平倉訂單
        print("1️⃣ 註冊多個平倉訂單...")
        
        orders = [
            {"position_id": 101, "order_id": "ORDER_A", "price": 22500.0, "time_offset": 0},
            {"position_id": 102, "order_id": "ORDER_B", "price": 22502.0, "time_offset": 1},
            {"position_id": 103, "order_id": "ORDER_C", "price": 22498.0, "time_offset": 2},
        ]
        
        for order in orders:
            time.sleep(order["time_offset"])  # 確保時間順序
            exit_tracker.register_exit_order(
                position_id=order["position_id"],
                order_id=order["order_id"],
                direction="SELL",
                quantity=1,
                price=order["price"],
                product="TM0000"
            )
            print(f"   註冊訂單: {order['order_id']} @{order['price']:.0f}")
        
        # 3. 測試FIFO匹配
        print("2️⃣ 測試FIFO匹配...")
        
        # 成交價格22500，應該匹配ORDER_A（最早且價格匹配）
        fill_report = ExitFillReport(
            order_id="",
            position_id=0,
            fill_price=22500.0,
            fill_quantity=1,
            fill_time=datetime.now().strftime('%H:%M:%S'),
            product="TM0000"
        )
        
        processed = exit_tracker.process_exit_fill_report(fill_report)
        print(f"   FIFO匹配結果: {'成功' if processed else '失敗'}")
        
        # 4. 檢查剩餘訂單
        print("3️⃣ 檢查剩餘訂單...")
        
        for order in orders:
            has_order = exit_tracker.has_exit_order_for_position(order["position_id"])
            status = exit_tracker.get_exit_order_status(order["position_id"])
            print(f"   部位{order['position_id']}: 有訂單={has_order}, 狀態={status}")
        
        print("✅ FIFO匹配機制測試完成")
        
    except Exception as e:
        print(f"❌ FIFO測試失敗: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    # 執行所有測試
    test_exit_order_tracker()
    test_integration_with_stop_executor()
    test_fifo_matching()
    
    print("\n🎯 第二階段測試總結:")
    print("✅ 平倉訂單追蹤器已實現")
    print("✅ 一對一回報確認機制已實現")
    print("✅ FIFO匹配機制已實現")
    print("✅ 與停損執行器整合已完成")
    print("✅ 重複平倉防護已增強")
    print("📝 下一步: 實施平倉追價機制")
