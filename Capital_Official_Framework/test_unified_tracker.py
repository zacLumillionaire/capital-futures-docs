# -*- coding: utf-8 -*-
"""
測試統一追蹤器的FIFO功能
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from unified_order_tracker import UnifiedOrderTracker
import time

def test_unified_tracker_fifo():
    """測試統一追蹤器的FIFO功能"""
    print("🧪 開始測試統一追蹤器FIFO功能...")
    
    # 創建追蹤器
    tracker = UnifiedOrderTracker(console_enabled=True)
    
    # 測試1: 註冊實際訂單
    print("\n📋 測試1: 註冊實際訂單")
    success = tracker.register_order(
        order_id="test_real_001",
        product="TM0000",
        direction="LONG",
        quantity=1,
        price=22334.0,
        is_virtual=False
    )
    assert success, "註冊實際訂單失敗"
    print("✅ 實際訂單註冊成功")
    
    # 測試2: 模擬成交回報
    print("\n📋 測試2: 模擬成交回報")
    # 模擬OnNewData回報格式 - 確保有足夠的欄位
    # fields[2]=Type, fields[8]=Product, fields[11]=Price, fields[20]=Qty
    fields = [""] * 48  # 創建48個空欄位
    fields[0] = "2315544965069"  # KeyNo
    fields[1] = "F"              # Market
    fields[2] = "D"              # Type (成交)
    fields[3] = "N"              # OrderErr
    fields[8] = "TM2507"         # Product
    fields[11] = "22334"         # Price
    fields[20] = "1"             # Qty
    fields[47] = "2315544965069" # SeqNo

    mock_reply = ",".join(fields)
    
    success = tracker.process_real_order_reply(mock_reply)
    assert success, "處理成交回報失敗"
    print("✅ 成交回報處理成功")
    
    # 測試3: 檢查統計
    print("\n📋 測試3: 檢查統計")
    stats = tracker.fifo_matcher.get_statistics()
    print(f"📊 FIFO統計: {stats}")
    assert stats['total_matched'] == 1, "成交統計錯誤"
    print("✅ 統計檢查通過")
    
    # 測試4: 註冊虛擬訂單（不應進入FIFO）
    print("\n📋 測試4: 註冊虛擬訂單")
    success = tracker.register_order(
        order_id="test_virtual_001",
        product="TM0000",
        direction="SHORT",
        quantity=2,
        price=22340.0,
        is_virtual=True
    )
    assert success, "註冊虛擬訂單失敗"
    
    # 虛擬訂單不應影響FIFO統計
    stats_after = tracker.fifo_matcher.get_statistics()
    assert stats_after['total_registered'] == stats['total_registered'], "虛擬訂單錯誤進入FIFO"
    print("✅ 虛擬訂單測試通過")
    
    print("\n🎉 所有測試通過！")

if __name__ == "__main__":
    test_unified_tracker_fifo()
