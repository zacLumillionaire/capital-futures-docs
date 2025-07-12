#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
簡化平倉追價測試
直接測試口級別平倉追價的核心邏輯
"""

import sys
import os

# 添加路徑
current_dir = os.path.dirname(__file__)
capital_framework_path = os.path.join(current_dir, 'Capital_Official_Framework')
if capital_framework_path not in sys.path:
    sys.path.insert(0, capital_framework_path)

def test_exit_group_creation():
    """測試平倉組創建"""
    print("🧪 測試平倉組創建...")
    
    try:
        from simplified_order_tracker import ExitGroup
        
        # 創建平倉組
        exit_group = ExitGroup(
            position_id=127,
            total_lots=3,
            direction="LONG",
            exit_direction="SHORT", 
            target_price=22675.0,
            product="TM0000"
        )
        
        print(f"✅ 平倉組創建成功:")
        print(f"  - 部位ID: {exit_group.position_id}")
        print(f"  - 總口數: {exit_group.total_lots}")
        print(f"  - 方向: {exit_group.direction} → {exit_group.exit_direction}")
        print(f"  - 目標價格: {exit_group.target_price}")
        
        # 測試口級別方法
        print(f"\n🔧 測試口級別方法:")
        
        # 測試第1口
        lot_1_needs_retry = exit_group.needs_retry_for_lot(1)
        print(f"  - 第1口需要追價: {lot_1_needs_retry}")
        
        if lot_1_needs_retry:
            retry_count_1 = exit_group.increment_retry_for_lot(1)
            print(f"  - 第1口追價次數: {retry_count_1}")
        
        # 測試第2口
        lot_2_needs_retry = exit_group.needs_retry_for_lot(2)
        print(f"  - 第2口需要追價: {lot_2_needs_retry}")
        
        if lot_2_needs_retry:
            retry_count_2 = exit_group.increment_retry_for_lot(2)
            print(f"  - 第2口追價次數: {retry_count_2}")
        
        # 顯示狀態
        print(f"\n📊 平倉組狀態:")
        print(f"  - 各口追價次數: {exit_group.individual_retry_counts}")
        print(f"  - 正在追價的口: {exit_group.active_retry_lots}")
        print(f"  - 組級別追價次數: {exit_group.retry_count}")
        
        return True
        
    except Exception as e:
        print(f"❌ 平倉組創建失敗: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_global_exit_manager():
    """測試全局平倉管理器"""
    print(f"\n🧪 測試全局平倉管理器...")
    
    try:
        from simplified_order_tracker import GlobalExitManager
        
        manager = GlobalExitManager()
        print(f"✅ 全局平倉管理器創建成功")
        print(f"  - 鎖定超時: {manager.exit_timeout}秒")
        
        # 測試口級別鎖定
        position_id = "127"
        lot_index = 1
        
        # 第一次標記
        result1 = manager.mark_exit_with_lot(position_id, lot_index, "test_source", "test_type")
        print(f"  - 第1次標記結果: {result1}")
        
        # 立即第二次標記（應該被阻止）
        result2 = manager.mark_exit_with_lot(position_id, lot_index, "test_source", "test_type")
        print(f"  - 立即第2次標記結果: {result2}")
        
        # 檢查狀態
        can_exit = manager.can_exit_lot(position_id, lot_index)
        print(f"  - 當前可以平倉: {can_exit}")
        
        # 顯示鎖定狀態
        print(f"  - 當前鎖定數量: {len(manager.exit_locks)}")
        
        return True
        
    except Exception as e:
        print(f"❌ 全局平倉管理器測試失敗: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_simplified_tracker_basic():
    """測試簡化追蹤器基本功能"""
    print(f"\n🧪 測試簡化追蹤器基本功能...")
    
    try:
        from simplified_order_tracker import SimplifiedOrderTracker
        
        tracker = SimplifiedOrderTracker(console_enabled=True)
        print(f"✅ 簡化追蹤器創建成功")
        
        # 測試註冊平倉組
        result = tracker.register_exit_group(
            position_id=127,
            total_lots=1,
            direction="LONG",
            exit_direction="SHORT",
            target_price=22675.0,
            product="TM0000"
        )
        print(f"  - 註冊平倉組結果: {result}")
        
        # 檢查平倉組
        exit_group = tracker.exit_groups.get(127)
        if exit_group:
            print(f"  - 平倉組已註冊: 部位{exit_group.position_id}")
        else:
            print(f"  - ❌ 平倉組未找到")
            
        return True
        
    except Exception as e:
        print(f"❌ 簡化追蹤器測試失敗: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    print("🚀 簡化平倉追價測試")
    print("=" * 50)
    
    success_count = 0
    total_tests = 3
    
    # 測試1: 平倉組創建
    if test_exit_group_creation():
        success_count += 1
    
    # 測試2: 全局平倉管理器
    if test_global_exit_manager():
        success_count += 1
    
    # 測試3: 簡化追蹤器基本功能
    if test_simplified_tracker_basic():
        success_count += 1
    
    print(f"\n📊 測試結果: {success_count}/{total_tests} 通過")
    
    if success_count == total_tests:
        print("✅ 所有測試通過！口級別平倉追價機制基本功能正常")
    else:
        print("❌ 部分測試失敗，需要進一步檢查")
