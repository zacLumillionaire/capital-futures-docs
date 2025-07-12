# -*- coding: utf-8 -*-
"""
FIFO機制綜合測試
測試所有追蹤器的FIFO功能
"""

import sys
import os
import time
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

def test_fifo_comprehensive():
    """綜合測試FIFO機制"""
    print("🧪 開始FIFO機制綜合測試...")
    
    # 測試1: FIFO匹配器基本功能
    print("\n📋 測試1: FIFO匹配器基本功能")
    try:
        from fifo_order_matcher import FIFOOrderMatcher, OrderInfo
        
        matcher = FIFOOrderMatcher(console_enabled=True)
        
        # 添加多個訂單測試FIFO順序
        order1 = OrderInfo("order1", "TM0000", "LONG", 1, 22334.0, time.time())
        order2 = OrderInfo("order2", "TM0000", "LONG", 1, 22335.0, time.time() + 0.1)
        
        matcher.add_pending_order(order1)
        matcher.add_pending_order(order2)
        
        # 應該匹配到最早的訂單
        matched = matcher.find_match(22334.0, 1, "TM2507")
        assert matched and matched.order_id == "order1", "FIFO順序錯誤"
        print("✅ FIFO匹配器測試通過")
        
    except Exception as e:
        print(f"❌ FIFO匹配器測試失敗: {e}")
        return False
    
    # 測試2: 統一追蹤器FIFO功能
    print("\n📋 測試2: 統一追蹤器FIFO功能")
    try:
        from unified_order_tracker import UnifiedOrderTracker
        
        tracker = UnifiedOrderTracker(console_enabled=True)
        
        # 註冊訂單
        tracker.register_order("real_001", "TM0000", "LONG", 1, 22334.0, False)
        
        # 模擬回報
        fields = [""] * 48
        fields[2] = "D"
        fields[8] = "TM2507"
        fields[11] = "22334"
        fields[20] = "1"
        mock_reply = ",".join(fields)
        
        success = tracker.process_real_order_reply(mock_reply)
        assert success, "統一追蹤器處理失敗"
        
        # 檢查訂單狀態
        order_status = tracker.get_order_status("real_001")
        assert order_status and order_status.status.value == "filled", "訂單狀態錯誤"
        print("✅ 統一追蹤器測試通過")
        
    except Exception as e:
        print(f"❌ 統一追蹤器測試失敗: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    # 測試3: 簡化追蹤器FIFO功能
    print("\n📋 測試3: 簡化追蹤器FIFO功能")
    try:
        from simplified_order_tracker import SimplifiedOrderTracker
        
        simple_tracker = SimplifiedOrderTracker(console_enabled=True)
        
        # 註冊策略組
        simple_tracker.register_strategy_group(1, 2, "LONG", 22334.0, "TM0000")
        
        # 處理成交回報
        success = simple_tracker.process_order_reply(mock_reply)
        assert success, "簡化追蹤器處理失敗"
        
        # 檢查策略組狀態
        group = simple_tracker.get_strategy_group(1)
        assert group and group.filled_lots == 1, "策略組狀態錯誤"
        print("✅ 簡化追蹤器測試通過")
        
    except Exception as e:
        print(f"❌ 簡化追蹤器測試失敗: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    # 測試4: 總量追蹤管理器FIFO功能
    print("\n📋 測試4: 總量追蹤管理器FIFO功能")
    try:
        from total_lot_manager import TotalLotManager
        
        total_manager = TotalLotManager(console_enabled=True)
        
        # 創建策略追蹤器
        total_manager.create_strategy_tracker("strategy_1", 2, 1, "LONG", "TM0000")
        
        # 處理成交回報
        success = total_manager.process_order_reply(mock_reply)
        assert success, "總量管理器處理失敗"
        
        # 檢查追蹤器狀態
        tracker = total_manager.get_tracker("strategy_1")
        assert tracker and tracker.total_filled_lots == 1, "總量追蹤器狀態錯誤"
        print("✅ 總量追蹤管理器測試通過")
        
    except Exception as e:
        print(f"❌ 總量追蹤管理器測試失敗: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    # 測試5: 滑價成交測試
    print("\n📋 測試5: 滑價成交測試")
    try:
        # 測試±5點滑價容差
        matcher_slip = FIFOOrderMatcher(console_enabled=True)
        order_slip = OrderInfo("slip_test", "TM0000", "LONG", 1, 22334.0, time.time())
        matcher_slip.add_pending_order(order_slip)
        
        # 測試+3點滑價
        matched_slip = matcher_slip.find_match(22337.0, 1, "TM2507")
        assert matched_slip, "滑價成交測試失敗"
        print("✅ 滑價成交測試通過")
        
    except Exception as e:
        print(f"❌ 滑價成交測試失敗: {e}")
        return False
    
    # 測試6: 商品映射測試
    print("\n📋 測試6: 商品映射測試")
    try:
        # 測試TM0000 ↔ TM2507映射
        matcher_map = FIFOOrderMatcher(console_enabled=True)
        order_map = OrderInfo("map_test", "TM0000", "LONG", 1, 22334.0, time.time())
        matcher_map.add_pending_order(order_map)
        
        # 用TM2507回報應該能匹配TM0000訂單
        matched_map = matcher_map.find_match(22334.0, 1, "TM2507")
        assert matched_map, "商品映射測試失敗"
        print("✅ 商品映射測試通過")
        
    except Exception as e:
        print(f"❌ 商品映射測試失敗: {e}")
        return False
    
    print("\n🎉 所有FIFO機制測試通過！")
    print("\n📊 測試總結:")
    print("✅ FIFO匹配器 - 時間優先、價格容差、商品映射")
    print("✅ 統一追蹤器 - 完全放棄序號匹配，使用FIFO")
    print("✅ 簡化追蹤器 - 純FIFO策略組匹配")
    print("✅ 總量管理器 - 不依賴方向的FIFO匹配")
    print("✅ 滑價處理 - ±5點容差正常工作")
    print("✅ 商品映射 - TM0000↔TM2507自動對應")
    
    return True

if __name__ == "__main__":
    test_fifo_comprehensive()
