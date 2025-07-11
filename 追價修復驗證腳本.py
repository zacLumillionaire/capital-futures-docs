#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
追價修復驗證腳本
用於測試修復後的追價機制是否正常工作
"""

import sys
import os
import time

# 添加路徑
current_dir = os.path.dirname(__file__)
capital_framework_path = os.path.join(current_dir, 'Capital_Official_Framework')
if capital_framework_path not in sys.path:
    sys.path.insert(0, capital_framework_path)

from simplified_order_tracker import SimplifiedOrderTracker, StrategyGroup

def test_retry_mechanism():
    """測試口級別追價機制"""
    print("🧪 開始測試口級別追價機制修復效果...")

    # 創建簡化追蹤器
    tracker = SimplifiedOrderTracker(console_enabled=True)

    # 註冊策略組（模擬3口建倉）
    group_id = 9
    tracker.register_strategy_group(
        group_id=group_id,
        total_lots=3,
        direction="LONG",
        target_price=22680.0,
        product="TM0000"
    )

    print(f"\n✅ 已註冊策略組{group_id}: 3口 LONG @22680")

    # 模擬第1口取消
    print(f"\n📋 模擬第1口取消回報...")
    cancel_data_1 = "2315545598018,TF,C,N,F020000,6363839,BNF20,TW,TM2507,,y4828,0.000000,,,,,,,,,0,,,20250711,19:29:03,,0000000,7174,y,20250714,2120000101823,A,FITM,202507,,,,,0000001576,,B,20250711,,,,,N,,2315545598018"
    result_1 = tracker.process_order_reply(cancel_data_1)
    print(f"第1口取消處理結果: {result_1}")

    # 等待一下，模擬時間間隔
    time.sleep(0.2)

    # 模擬第2口取消
    print(f"\n📋 模擬第2口取消回報...")
    cancel_data_2 = "2315545598019,TF,C,N,F020000,6363839,BNF20,TW,TM2507,,z4822,0.000000,,,,,,,,,0,,,20250711,19:29:03,,0000000,7174,y,20250714,2120000101824,A,FITM,202507,,,,,0000001574,,B,20250711,,,,,N,,2315545598019"
    result_2 = tracker.process_order_reply(cancel_data_2)
    print(f"第2口取消處理結果: {result_2}")

    # 等待一下，模擬時間間隔
    time.sleep(0.2)

    # 模擬第3口取消
    print(f"\n📋 模擬第3口取消回報...")
    cancel_data_3 = "2315545597912,TF,C,N,F020000,6363839,BNF20,TW,TM2507,,s4826,0.000000,,,,,,,,,0,,,20250711,19:29:04,,0000000,7174,y,20250714,2120000101825,A,FITM,202507,,,,,0000001577,,B,20250711,,,,,N,,2315545597912"
    result_3 = tracker.process_order_reply(cancel_data_3)
    print(f"第3口取消處理結果: {result_3}")

    # 檢查策略組狀態
    group = tracker.strategy_groups.get(group_id)
    if group:
        print(f"\n📊 最終策略組狀態:")
        print(f"  - 組ID: {group.group_id}")
        print(f"  - 總口數: {group.total_lots}")
        print(f"  - 已成交: {group.filled_lots}")
        print(f"  - 已取消: {group.cancelled_lots}")
        print(f"  - 剩餘口數: {group.remaining_lots}")
        print(f"  - 組級別追價次數: {group.retry_count}")
        print(f"  - 最大追價次數: {group.max_retries}")
        print(f"  - 是否在追價: {group.is_retrying}")
        print(f"  - 正在追價的口: {group.active_retry_lots}")

        # 🔧 新增：顯示每口的追價次數
        print(f"  - 各口追價次數:")
        for lot_index in range(1, group.total_lots + 1):
            retry_count = group.individual_retry_counts.get(lot_index, 0)
            needs_retry = group.needs_retry_for_lot(lot_index)
            print(f"    第{lot_index}口: {retry_count}次 (需要追價: {needs_retry})")

    # 檢查全局追價管理器狀態
    print(f"\n🔒 全局追價管理器狀態:")
    print(f"  - 鎖定超時: {tracker.global_retry_manager.retry_timeout}秒")
    print(f"  - 當前鎖定: {len(tracker.global_retry_manager.retry_locks)}個")
    for key, timestamp in tracker.global_retry_manager.retry_locks.items():
        elapsed = time.time() - timestamp
        print(f"    {key}: {elapsed:.2f}秒前")

def test_global_retry_manager():
    """測試全局追價管理器"""
    print("\n🧪 測試全局追價管理器...")
    
    from simplified_order_tracker import GlobalRetryManager
    
    manager = GlobalRetryManager()
    group_key = "group_9_TM0000"
    
    # 第一次標記
    result1 = manager.mark_retry(group_key)
    print(f"第1次標記結果: {result1}")
    
    # 立即第二次標記（應該被阻止）
    result2 = manager.mark_retry(group_key)
    print(f"立即第2次標記結果: {result2}")
    
    # 等待超時後再次標記
    print(f"等待{manager.retry_timeout}秒...")
    time.sleep(manager.retry_timeout + 0.01)
    
    result3 = manager.mark_retry(group_key)
    print(f"超時後第3次標記結果: {result3}")

if __name__ == "__main__":
    print("🚀 追價修復驗證腳本")
    print("=" * 50)
    
    try:
        # 測試全局追價管理器
        test_global_retry_manager()
        
        print("\n" + "=" * 50)
        
        # 測試追價機制
        test_retry_mechanism()
        
        print("\n✅ 測試完成！")
        
    except Exception as e:
        print(f"\n❌ 測試失敗: {e}")
        import traceback
        traceback.print_exc()
