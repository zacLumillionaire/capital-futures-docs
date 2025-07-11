#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
調試FIFO匹配問題的測試腳本
模擬追價紀錄中的問題場景
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from simplified_order_tracker import SimplifiedOrderTracker
import time

def test_fifo_issue_simulation():
    """模擬追價紀錄中的FIFO問題"""
    print("🧪 開始模擬FIFO匹配問題...")
    
    # 創建簡化追蹤器
    tracker = SimplifiedOrderTracker(console_enabled=True)
    
    # 模擬回調函數
    def mock_fill_callback(group_id, price, qty, filled_lots, total_lots):
        print(f"📞 [MOCK_CALLBACK] 組{group_id}成交回調: {qty}口 @{price}, 進度:{filled_lots}/{total_lots}")
    
    # 註冊回調
    tracker.add_fill_callback(mock_fill_callback)
    
    print("\n📋 步驟1: 註冊策略組10 (3口 @22573)")
    success = tracker.register_strategy_group(
        group_id=10,
        total_lots=3,
        direction="SHORT",
        target_price=22573.0,
        product="TM0000"
    )
    print(f"註冊結果: {success}")
    
    # 更新已送出口數
    print("\n📤 步驟2: 更新已送出口數 (3口)")
    tracker.update_submitted_lots(group_id=10, lots=3)
    
    # 檢查初始狀態
    group = tracker.get_strategy_group(10)
    if group:
        print(f"📊 初始狀態: {group.filled_lots}/{group.total_lots}, 完成={group.is_complete()}")
    
    print("\n" + "="*60)
    print("🔍 開始模擬成交回報處理...")
    
    # 模擬第一口成交 @22574 (滑價)
    print("\n📋 步驟3: 第一口成交 @22574")
    result1 = tracker._handle_fill_report_fifo(22574.0, 1, "TM2507")
    print(f"第一口處理結果: {result1}")
    
    # 檢查狀態
    if group:
        print(f"📊 第一口後狀態: {group.filled_lots}/{group.total_lots}, 完成={group.is_complete()}")
    
    # 模擬第二口成交 @22573
    print("\n📋 步驟4: 第二口成交 @22573")
    result2 = tracker._handle_fill_report_fifo(22573.0, 1, "TM2507")
    print(f"第二口處理結果: {result2}")
    
    # 檢查狀態
    if group:
        print(f"📊 第二口後狀態: {group.filled_lots}/{group.total_lots}, 完成={group.is_complete()}")
    
    # 模擬第三口成交 @22573
    print("\n📋 步驟5: 第三口成交 @22573")
    result3 = tracker._handle_fill_report_fifo(22573.0, 1, "TM2507")
    print(f"第三口處理結果: {result3}")
    
    # 檢查最終狀態
    if group:
        print(f"📊 最終狀態: {group.filled_lots}/{group.total_lots}, 完成={group.is_complete()}")
    
    print("\n" + "="*60)
    print("📊 測試結果總結:")
    print(f"- 第一口成交: {'✅' if result1 else '❌'}")
    print(f"- 第二口成交: {'✅' if result2 else '❌'}")
    print(f"- 第三口成交: {'✅' if result3 else '❌'}")
    
    if group:
        print(f"- 最終成交口數: {group.filled_lots}/3")
        print(f"- 策略組完成: {'✅' if group.is_complete() else '❌'}")
    
    return result1, result2, result3

def test_duplicate_callback_issue():
    """測試重複回調問題"""
    print("\n🧪 測試重複回調問題...")
    
    tracker = SimplifiedOrderTracker(console_enabled=True)
    
    # 計數器
    callback_count = 0
    
    def counting_callback(group_id, price, qty, filled_lots, total_lots):
        nonlocal callback_count
        callback_count += 1
        print(f"📞 [CALLBACK_{callback_count}] 組{group_id}: {qty}口 @{price}")
    
    # 測試重複註冊
    print("📝 測試回調重複註冊...")
    tracker.add_fill_callback(counting_callback)
    tracker.add_fill_callback(counting_callback)  # 重複註冊
    tracker.add_fill_callback(counting_callback)  # 再次重複註冊
    
    print(f"回調數量: {len(tracker.fill_callbacks)}")
    
    # 註冊策略組並測試
    tracker.register_strategy_group(1, 1, "LONG", 22500.0, "TM0000")
    tracker.update_submitted_lots(1, 1)
    
    # 觸發成交
    print("🔥 觸發成交...")
    tracker._handle_fill_report_fifo(22500.0, 1, "TM0000")
    
    print(f"總回調次數: {callback_count}")
    return callback_count

if __name__ == "__main__":
    print("🚀 開始FIFO問題調試...")
    
    # 測試1: 模擬追價紀錄問題
    result1, result2, result3 = test_fifo_issue_simulation()
    
    # 測試2: 重複回調問題
    callback_count = test_duplicate_callback_issue()
    
    print("\n" + "="*60)
    print("🎯 調試結論:")
    
    if not result2 or not result3:
        print("❌ 發現FIFO匹配問題：第二或第三口成交失敗")
        print("   可能原因：")
        print("   1. 策略組狀態被錯誤更新")
        print("   2. 重複處理導致filled_lots計算錯誤")
        print("   3. 異步處理影響FIFO匹配")
    else:
        print("✅ FIFO匹配正常")
    
    if callback_count > 1:
        print(f"❌ 發現重複回調問題：回調被執行{callback_count}次")
    else:
        print("✅ 回調機制正常")
