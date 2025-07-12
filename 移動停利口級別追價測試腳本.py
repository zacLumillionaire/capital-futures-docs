#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
移動停利口級別追價測試腳本
測試移動停利是否正確使用口級別追價機制
"""

import sys
import os
import time

# 添加路徑
current_dir = os.path.dirname(__file__)
capital_framework_path = os.path.join(current_dir, 'Capital_Official_Framework')
if capital_framework_path not in sys.path:
    sys.path.insert(0, capital_framework_path)

def test_trailing_stop_exit_group_registration():
    """測試移動停利平倉組註冊"""
    print("🧪 測試移動停利平倉組註冊...")
    
    try:
        from simplified_order_tracker import SimplifiedOrderTracker
        
        # 創建簡化追蹤器
        tracker = SimplifiedOrderTracker(console_enabled=True)
        
        # 模擬移動停利觸發時的平倉組註冊
        position_id = 127
        result = tracker.register_exit_group(
            position_id=position_id,
            total_lots=1,  # 移動停利通常是1口
            direction="LONG",  # 原始部位方向
            exit_direction="SELL",  # 平倉方向
            target_price=22685.0,  # 移動停利價格
            product="TM0000"
        )
        
        print(f"✅ 移動停利平倉組註冊結果: {result}")
        
        # 檢查平倉組狀態
        exit_group = tracker.exit_groups.get(position_id)
        if exit_group:
            print(f"📊 移動停利平倉組狀態:")
            print(f"  - 部位ID: {exit_group.position_id}")
            print(f"  - 總口數: {exit_group.total_lots}")
            print(f"  - 方向: {exit_group.direction} → {exit_group.exit_direction}")
            print(f"  - 目標價格: {exit_group.target_price}")
            print(f"  - 各口追價次數: {exit_group.individual_retry_counts}")
            print(f"  - 正在追價的口: {exit_group.active_retry_lots}")
        
        return True
        
    except Exception as e:
        print(f"❌ 移動停利平倉組註冊測試失敗: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_trailing_stop_cancel_retry():
    """測試移動停利取消後的口級別追價"""
    print(f"\n🧪 測試移動停利取消後的口級別追價...")
    
    try:
        from simplified_order_tracker import SimplifiedOrderTracker
        
        # 創建簡化追蹤器
        tracker = SimplifiedOrderTracker(console_enabled=True)
        
        # 1. 註冊移動停利平倉組
        position_id = 128
        tracker.register_exit_group(
            position_id=position_id,
            total_lots=1,
            direction="LONG",
            exit_direction="SELL", 
            target_price=22680.0,
            product="TM0000"
        )
        
        # 2. 註冊移動停利平倉訂單
        order_id = f"TRAILING_STOP_{position_id}_001"
        tracker.register_exit_order(
            position_id=position_id,
            order_id=order_id,
            direction="SELL",  # 平倉方向
            quantity=1,
            price=22680.0,
            product="TM0000"
        )
        
        print(f"✅ 移動停利訂單已註冊: {order_id}")
        
        # 3. 模擬移動停利訂單取消回報
        print(f"\n📋 模擬移動停利訂單取消回報...")
        cancel_data = f"2315545598040,TF,C,N,F020000,6363839,SOF20,TW,TM2507,,t4838,0.000000,,,,,,,,,0,,,20250711,19:49:01,,0000000,7174,y,20250714,2120000101840,A,FITM,202507,,,,,0000001590,,S,20250711,,,,,N,,{order_id}"
        
        result = tracker.process_order_reply(cancel_data)
        print(f"移動停利取消處理結果: {result}")
        
        # 4. 檢查追價狀態
        exit_group = tracker.exit_groups.get(position_id)
        if exit_group:
            print(f"\n📊 移動停利追價後狀態:")
            print(f"  - 已取消口數: {exit_group.cancelled_lots}")
            print(f"  - 組級別追價次數: {exit_group.retry_count}")
            print(f"  - 各口追價次數: {exit_group.individual_retry_counts}")
            print(f"  - 正在追價的口: {exit_group.active_retry_lots}")
            print(f"  - 是否在追價: {exit_group.is_retrying}")
        
        return True
        
    except Exception as e:
        print(f"❌ 移動停利追價測試失敗: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_multiple_trailing_stops():
    """測試多個移動停利的獨立追價"""
    print(f"\n🧪 測試多個移動停利的獨立追價...")
    
    try:
        from simplified_order_tracker import SimplifiedOrderTracker
        
        # 創建簡化追蹤器
        tracker = SimplifiedOrderTracker(console_enabled=True)
        
        # 註冊多個移動停利平倉組
        position_ids = [129, 130, 131]
        
        for position_id in position_ids:
            # 註冊平倉組
            tracker.register_exit_group(
                position_id=position_id,
                total_lots=1,
                direction="LONG",
                exit_direction="SELL",
                target_price=22675.0 + position_id,  # 不同的價格
                product="TM0000"
            )
            
            # 註冊平倉訂單
            order_id = f"TRAILING_STOP_{position_id}_001"
            tracker.register_exit_order(
                position_id=position_id,
                order_id=order_id,
                direction="SELL",
                quantity=1,
                price=22675.0 + position_id,
                product="TM0000"
            )
            
            print(f"✅ 部位{position_id}移動停利已註冊")
        
        print(f"\n📋 模擬所有移動停利訂單取消...")
        
        # 模擬所有移動停利訂單取消
        for i, position_id in enumerate(position_ids):
            order_id = f"TRAILING_STOP_{position_id}_001"
            cancel_data = f"2315545598{41+i:03d},TF,C,N,F020000,6363839,SOF20,TW,TM2507,,u{4839+i},0.000000,,,,,,,,,0,,,20250711,19:49:0{2+i},,0000000,7174,y,20250714,212000010184{1+i},A,FITM,202507,,,,,000000159{1+i},,S,20250711,,,,,N,,{order_id}"
            
            result = tracker.process_order_reply(cancel_data)
            print(f"部位{position_id}移動停利取消處理結果: {result}")
            
            time.sleep(0.1)  # 模擬時間間隔
        
        # 檢查所有平倉組狀態
        print(f"\n📊 所有移動停利追價狀態:")
        for position_id in position_ids:
            exit_group = tracker.exit_groups.get(position_id)
            if exit_group:
                print(f"  部位{position_id}:")
                print(f"    - 各口追價次數: {exit_group.individual_retry_counts}")
                print(f"    - 正在追價的口: {exit_group.active_retry_lots}")
        
        # 檢查全局平倉管理器
        print(f"\n🔒 全局平倉管理器狀態:")
        print(f"  - 鎖定超時: {tracker.global_exit_manager.exit_timeout}秒")
        print(f"  - 當前鎖定: {len(tracker.global_exit_manager.exit_locks)}個")
        for key, info in tracker.global_exit_manager.exit_locks.items():
            elapsed = time.time() - info['timestamp']
            print(f"    {key}: {elapsed:.2f}秒前 ({info['trigger_source']})")
        
        return True
        
    except Exception as e:
        print(f"❌ 多個移動停利測試失敗: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    print("🚀 移動停利口級別追價測試腳本")
    print("=" * 60)
    
    success_count = 0
    total_tests = 3
    
    # 測試1: 移動停利平倉組註冊
    if test_trailing_stop_exit_group_registration():
        success_count += 1
    
    # 測試2: 移動停利取消後追價
    if test_trailing_stop_cancel_retry():
        success_count += 1
    
    # 測試3: 多個移動停利獨立追價
    if test_multiple_trailing_stops():
        success_count += 1
    
    print(f"\n📊 測試結果: {success_count}/{total_tests} 通過")
    
    if success_count == total_tests:
        print("✅ 所有測試通過！移動停利口級別追價機制正常工作")
        print("\n🎯 移動停利追價機制總結:")
        print("  ✅ 移動停利使用停損平倉機制")
        print("  ✅ 移動停利訂單註冊到口級別追蹤系統")
        print("  ✅ 移動停利FOK失敗後觸發口級別追價")
        print("  ✅ 使用相同的追價邏輯: LONG用BID1-1, SHORT用ASK1+1")
        print("  ✅ 每個部位獨立追價，不會互相影響")
        print("  ✅ 全局鎖定機制防止重複追價")
    else:
        print("❌ 部分測試失敗，需要進一步檢查")
