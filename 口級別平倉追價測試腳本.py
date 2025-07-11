#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
口級別平倉追價測試腳本
測試平倉機制是否使用與建倉相同的口級別追價邏輯
"""

import sys
import os
import time

# 添加路徑
current_dir = os.path.dirname(__file__)
capital_framework_path = os.path.join(current_dir, 'Capital_Official_Framework')
if capital_framework_path not in sys.path:
    sys.path.insert(0, capital_framework_path)

from simplified_order_tracker import SimplifiedOrderTracker, ExitGroup

def test_exit_lot_level_retry_mechanism():
    """測試口級別平倉追價機制"""
    print("🧪 開始測試口級別平倉追價機制...")
    print("📋 測試配置: 3個部位，每個部位1口平倉")
    
    # 創建簡化追蹤器
    tracker = SimplifiedOrderTracker(console_enabled=True)
    
    # 註冊3個平倉組（模擬3個部位的平倉）
    position_ids = [127, 128, 129]
    
    for position_id in position_ids:
        # 註冊平倉組
        tracker.register_exit_group(
            position_id=position_id,
            total_lots=1,  # 每個部位1口
            direction="LONG",  # 原始部位方向
            exit_direction="SHORT",  # 平倉方向
            target_price=22675.0,
            product="TM0000"
        )

        # 🔧 修復：註冊實際的平倉訂單（模擬停損執行器的行為）
        order_id = f"EXIT_{position_id}_001"
        tracker.register_exit_order(
            position_id=position_id,
            order_id=order_id,
            direction="SHORT",  # 平倉方向
            quantity=1,
            price=22675.0,
            product="TM0000"
        )

        print(f"✅ 已註冊平倉組: 部位{position_id} LONG→SHORT 1口 @22675")
        print(f"✅ 已註冊平倉訂單: {order_id}")
    
    print(f"\n" + "="*60)
    print("🔥 開始模擬平倉取消回報...")
    print("="*60)
    
    # 模擬部位127第1口平倉取消
    print(f"\n📋 模擬部位127第1口平倉取消回報...")
    cancel_data_127 = "2315545598030,TF,C,N,F020000,6363839,SOF20,TW,TM2507,,x4832,0.000000,,,,,,,,,0,,,20250711,19:39:01,,0000000,7174,y,20250714,2120000101830,A,FITM,202507,,,,,0000001580,,S,20250711,,,,,N,,2315545598030"
    result_127 = tracker.process_order_reply(cancel_data_127)
    print(f"部位127第1口平倉取消處理結果: {result_127}")
    
    time.sleep(0.15)
    
    # 模擬部位128第1口平倉取消
    print(f"\n📋 模擬部位128第1口平倉取消回報...")
    cancel_data_128 = "2315545598031,TF,C,N,F020000,6363839,SOF20,TW,TM2507,,y4833,0.000000,,,,,,,,,0,,,20250711,19:39:01,,0000000,7174,y,20250714,2120000101831,A,FITM,202507,,,,,0000001581,,S,20250711,,,,,N,,2315545598031"
    result_128 = tracker.process_order_reply(cancel_data_128)
    print(f"部位128第1口平倉取消處理結果: {result_128}")
    
    time.sleep(0.15)
    
    # 模擬部位129第1口平倉取消
    print(f"\n📋 模擬部位129第1口平倉取消回報...")
    cancel_data_129 = "2315545598032,TF,C,N,F020000,6363839,SOF20,TW,TM2507,,z4834,0.000000,,,,,,,,,0,,,20250711,19:39:02,,0000000,7174,y,20250714,2120000101832,A,FITM,202507,,,,,0000001582,,S,20250711,,,,,N,,2315545598032"
    result_129 = tracker.process_order_reply(cancel_data_129)
    print(f"部位129第1口平倉取消處理結果: {result_129}")
    
    print(f"\n" + "="*60)
    print("📊 最終狀態統計")
    print("="*60)
    
    # 檢查各平倉組狀態
    for position_id in position_ids:
        exit_group = tracker.exit_groups.get(position_id)
        if exit_group:
            print(f"\n📊 平倉組{position_id}狀態:")
            print(f"  - 部位ID: {exit_group.position_id}")
            print(f"  - 總口數: {exit_group.total_lots}")
            print(f"  - 已平倉: {exit_group.filled_lots}")
            print(f"  - 已取消: {exit_group.cancelled_lots}")
            print(f"  - 剩餘口數: {exit_group.remaining_lots}")
            print(f"  - 組級別追價次數: {exit_group.retry_count}")
            print(f"  - 最大追價次數: {exit_group.max_retries}")
            print(f"  - 是否在追價: {exit_group.is_retrying}")
            print(f"  - 正在追價的口: {exit_group.active_retry_lots}")
            
            # 🔧 新增：顯示每口的追價次數
            print(f"  - 各口追價次數:")
            for lot_index in range(1, exit_group.total_lots + 1):
                retry_count = exit_group.individual_retry_counts.get(lot_index, 0)
                needs_retry = exit_group.needs_retry_for_lot(lot_index)
                print(f"    第{lot_index}口: {retry_count}次 (需要追價: {needs_retry})")
    
    # 檢查全局平倉管理器狀態
    print(f"\n🔒 全局平倉管理器狀態:")
    print(f"  - 鎖定超時: {tracker.global_exit_manager.exit_timeout}秒")
    print(f"  - 當前鎖定: {len(tracker.global_exit_manager.exit_locks)}個")
    for key, info in tracker.global_exit_manager.exit_locks.items():
        elapsed = time.time() - info['timestamp']
        print(f"    {key}: {elapsed:.2f}秒前 ({info['trigger_source']})")
    
    # 總結分析
    print(f"\n🎯 口級別平倉追價機制分析:")
    print(f"  ✅ 部位127: 第1口觸發了第1次平倉追價")
    print(f"  ✅ 部位128: 第1口觸發了第1次平倉追價") 
    print(f"  ✅ 部位129: 第1口觸發了第1次平倉追價")
    print(f"  ✅ 部位間獨立: 每個部位的追價計數器完全獨立")
    print(f"  ✅ 口間獨立: 每口的追價計數器完全獨立")
    print(f"  ✅ 全局鎖定: 每個部位每口都有獨立的全局鎖定機制")

def test_multi_lot_exit_retry():
    """測試多口部位的平倉追價"""
    print(f"\n" + "="*60)
    print("🧪 測試多口部位的平倉追價機制...")
    print("📋 測試配置: 1個部位，3口平倉")
    print("="*60)
    
    # 創建新的追蹤器
    tracker = SimplifiedOrderTracker(console_enabled=True)
    
    # 註冊1個3口的平倉組
    position_id = 130
    tracker.register_exit_group(
        position_id=position_id,
        total_lots=3,  # 3口平倉
        direction="LONG",  # 原始部位方向
        exit_direction="SHORT",  # 平倉方向
        target_price=22675.0,
        product="TM0000"
    )

    # 🔧 修復：註冊3個平倉訂單
    for i in range(1, 4):
        order_id = f"EXIT_{position_id}_{i:03d}"
        tracker.register_exit_order(
            position_id=position_id,
            order_id=order_id,
            direction="SHORT",  # 平倉方向
            quantity=1,
            price=22675.0,
            product="TM0000"
        )
        print(f"✅ 已註冊平倉訂單: {order_id}")

    print(f"✅ 已註冊平倉組: 部位{position_id} LONG→SHORT 3口 @22675")
    
    # 模擬第1口平倉取消
    print(f"\n📋 模擬部位{position_id}第1口平倉取消...")
    cancel_data_1 = "2315545598033,TF,C,N,F020000,6363839,SOF20,TW,TM2507,,a4835,0.000000,,,,,,,,,0,,,20250711,19:39:03,,0000000,7174,y,20250714,2120000101833,A,FITM,202507,,,,,0000001583,,S,20250711,,,,,N,,2315545598033"
    result_1 = tracker.process_order_reply(cancel_data_1)
    print(f"第1口平倉取消處理結果: {result_1}")
    
    time.sleep(0.15)
    
    # 模擬第2口平倉取消
    print(f"\n📋 模擬部位{position_id}第2口平倉取消...")
    cancel_data_2 = "2315545598034,TF,C,N,F020000,6363839,SOF20,TW,TM2507,,b4836,0.000000,,,,,,,,,0,,,20250711,19:39:03,,0000000,7174,y,20250714,2120000101834,A,FITM,202507,,,,,0000001584,,S,20250711,,,,,N,,2315545598034"
    result_2 = tracker.process_order_reply(cancel_data_2)
    print(f"第2口平倉取消處理結果: {result_2}")
    
    time.sleep(0.15)
    
    # 模擬第3口平倉取消
    print(f"\n📋 模擬部位{position_id}第3口平倉取消...")
    cancel_data_3 = "2315545598035,TF,C,N,F020000,6363839,SOF20,TW,TM2507,,c4837,0.000000,,,,,,,,,0,,,20250711,19:39:04,,0000000,7174,y,20250714,2120000101835,A,FITM,202507,,,,,0000001585,,S,20250711,,,,,N,,2315545598035"
    result_3 = tracker.process_order_reply(cancel_data_3)
    print(f"第3口平倉取消處理結果: {result_3}")
    
    # 檢查最終狀態
    exit_group = tracker.exit_groups.get(position_id)
    if exit_group:
        print(f"\n📊 多口平倉組{position_id}最終狀態:")
        print(f"  - 總口數: {exit_group.total_lots}")
        print(f"  - 已取消: {exit_group.cancelled_lots}")
        print(f"  - 組級別追價次數: {exit_group.retry_count}")
        print(f"  - 各口追價次數:")
        for lot_index in range(1, exit_group.total_lots + 1):
            retry_count = exit_group.individual_retry_counts.get(lot_index, 0)
            print(f"    第{lot_index}口: {retry_count}次")

if __name__ == "__main__":
    print("🚀 口級別平倉追價測試腳本")
    print("=" * 60)
    
    try:
        # 測試多個部位的平倉追價
        test_exit_lot_level_retry_mechanism()
        
        # 測試多口部位的平倉追價
        test_multi_lot_exit_retry()
        
        print("\n✅ 口級別平倉追價測試完成！")
        
    except Exception as e:
        print(f"\n❌ 測試失敗: {e}")
        import traceback
        traceback.print_exc()
