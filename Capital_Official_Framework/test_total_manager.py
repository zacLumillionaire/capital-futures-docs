# -*- coding: utf-8 -*-
"""
測試總量追蹤管理器的FIFO功能
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from total_lot_manager import TotalLotManager
import time

def test_total_manager_fifo():
    """測試總量追蹤管理器的FIFO功能"""
    print("🧪 開始測試總量追蹤管理器FIFO功能...")
    
    # 創建管理器
    manager = TotalLotManager(console_enabled=True)
    
    # 測試1: 創建策略追蹤器
    print("\n📋 測試1: 創建策略追蹤器")
    success = manager.create_strategy_tracker(
        strategy_id="strategy_1",
        total_target_lots=3,
        lots_per_group=1,
        direction="LONG",
        product="TM0000"
    )
    assert success, "創建策略追蹤器失敗"
    print("✅ 策略追蹤器創建成功")
    
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
    
    success = manager.process_order_reply(mock_reply)
    assert success, "處理成交回報失敗"
    print("✅ 成交回報處理成功")
    
    # 測試3: 檢查追蹤器狀態
    print("\n📋 測試3: 檢查追蹤器狀態")
    tracker = manager.get_tracker("strategy_1")
    assert tracker is not None, "找不到追蹤器"
    print(f"✅ 追蹤器狀態: {tracker.filled_lots}/{tracker.total_target_lots}")
    
    # 測試4: 繼續成交直到完成
    print("\n📋 測試4: 完成策略")
    for i in range(2):  # 再成交2口
        success = manager.process_order_reply(mock_reply)
        assert success, f"處理第{i+2}次成交失敗"
    
    # 檢查是否完成
    tracker = manager.get_tracker("strategy_1")
    assert tracker.is_complete(), "策略應該已完成"
    print("✅ 策略完成測試通過")
    
    # 測試5: 測試取消回報
    print("\n📋 測試5: 測試取消回報")
    # 創建新的策略追蹤器
    manager.create_strategy_tracker(
        strategy_id="strategy_2",
        total_target_lots=2,
        lots_per_group=1,
        direction="SHORT",
        product="TM0000"
    )
    
    # 模擬取消回報
    fields[2] = "C"              # Type (取消)
    fields[11] = "22340"         # Price
    fields[20] = "1"             # Qty
    mock_cancel = ",".join(fields)
    
    success = manager.process_order_reply(mock_cancel)
    assert success, "處理取消回報失敗"
    print("✅ 取消回報處理成功")
    
    # 檢查統計
    stats = manager.get_statistics()
    print(f"\n📊 最終統計: {stats}")
    
    print("\n🎉 所有測試通過！")

if __name__ == "__main__":
    test_total_manager_fifo()
