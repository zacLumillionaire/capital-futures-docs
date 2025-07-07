# -*- coding: utf-8 -*-
"""
測試簡化追蹤器的FIFO功能
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from simplified_order_tracker import SimplifiedOrderTracker
import time

def test_simplified_tracker_fifo():
    """測試簡化追蹤器的FIFO功能"""
    print("🧪 開始測試簡化追蹤器FIFO功能...")
    
    # 創建追蹤器
    tracker = SimplifiedOrderTracker(console_enabled=True)
    
    # 測試1: 註冊策略組
    print("\n📋 測試1: 註冊策略組")
    success = tracker.register_strategy_group(
        group_id=1,
        total_lots=2,
        direction="LONG",
        target_price=22334.0,
        product="TM0000"
    )
    assert success, "註冊策略組失敗"
    print("✅ 策略組註冊成功")
    
    # 測試2: 模擬成交回報
    print("\n📋 測試2: 模擬成交回報")
    # 創建模擬回報
    fields = [""] * 48
    fields[0] = "2315544965069"  # KeyNo
    fields[2] = "D"              # Type (成交)
    fields[3] = "N"              # OrderErr
    fields[8] = "TM2507"         # Product
    fields[11] = "22334"         # Price
    fields[20] = "1"             # Qty
    fields[47] = "2315544965069" # SeqNo
    
    mock_reply = ",".join(fields)
    
    success = tracker.process_order_reply(mock_reply)
    assert success, "處理成交回報失敗"
    print("✅ 成交回報處理成功")
    
    # 測試3: 檢查策略組狀態
    print("\n📋 測試3: 檢查策略組狀態")
    group = tracker.get_strategy_group(1)
    assert group is not None, "找不到策略組"
    assert group.filled_lots == 1, f"成交口數錯誤: {group.filled_lots}"
    print(f"✅ 策略組狀態正確: {group.filled_lots}/{group.total_lots}")
    
    # 測試4: 再次成交完成策略組
    print("\n📋 測試4: 完成策略組")
    fields[20] = "1"  # 再成交1口
    mock_reply2 = ",".join(fields)
    
    success = tracker.process_order_reply(mock_reply2)
    assert success, "處理第二次成交失敗"
    
    # 檢查是否完成
    group = tracker.get_strategy_group(1)
    assert group.is_complete(), "策略組應該已完成"
    print("✅ 策略組完成測試通過")
    
    # 測試5: 測試取消回報
    print("\n📋 測試5: 測試取消回報")
    # 註冊新的策略組
    tracker.register_strategy_group(
        group_id=2,
        total_lots=1,
        direction="SHORT",
        target_price=22340.0,
        product="TM0000"
    )
    
    # 模擬取消回報
    fields[2] = "C"              # Type (取消)
    fields[11] = "22340"         # Price
    fields[20] = "1"             # Qty
    mock_cancel = ",".join(fields)
    
    success = tracker.process_order_reply(mock_cancel)
    assert success, "處理取消回報失敗"
    print("✅ 取消回報處理成功")
    
    # 檢查統計
    stats = tracker.get_statistics()
    print(f"\n📊 最終統計: {stats}")
    
    print("\n🎉 所有測試通過！")

if __name__ == "__main__":
    test_simplified_tracker_fifo()
