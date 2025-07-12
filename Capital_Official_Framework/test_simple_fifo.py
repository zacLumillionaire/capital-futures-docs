# -*- coding: utf-8 -*-
"""
簡單的FIFO測試
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

def test_step_by_step():
    """逐步測試"""
    print("🧪 開始逐步測試...")
    
    # 步驟1: 測試FIFO匹配器
    print("\n📋 步驟1: 測試FIFO匹配器")
    try:
        from fifo_order_matcher import FIFOOrderMatcher, OrderInfo
        print("✅ FIFO匹配器導入成功")
        
        matcher = FIFOOrderMatcher(console_enabled=True)
        print("✅ FIFO匹配器創建成功")
        
        # 測試基本功能
        order = OrderInfo(
            order_id="test_001",
            product="TM0000",
            direction="LONG",
            quantity=1,
            price=22334.0,
            submit_time=0  # 會自動設置
        )
        
        success = matcher.add_pending_order(order)
        print(f"✅ 添加訂單: {'成功' if success else '失敗'}")
        
        # 測試匹配
        matched = matcher.find_match(price=22334.0, qty=1, product="TM2507")
        print(f"✅ 匹配結果: {'成功' if matched else '失敗'}")
        
    except Exception as e:
        print(f"❌ FIFO測試失敗: {e}")
        return False
    
    # 步驟2: 測試統一追蹤器導入
    print("\n📋 步驟2: 測試統一追蹤器導入")
    try:
        from unified_order_tracker import UnifiedOrderTracker
        print("✅ 統一追蹤器導入成功")
        
        tracker = UnifiedOrderTracker(console_enabled=True)
        print("✅ 統一追蹤器創建成功")
        
    except Exception as e:
        print(f"❌ 統一追蹤器測試失敗: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    # 步驟3: 測試基本功能
    print("\n📋 步驟3: 測試基本功能")
    try:
        # 註冊訂單
        success = tracker.register_order(
            order_id="test_real_001",
            product="TM0000",
            direction="LONG",
            quantity=1,
            price=22334.0,
            is_virtual=False
        )
        print(f"✅ 註冊訂單: {'成功' if success else '失敗'}")
        
        # 檢查FIFO統計
        stats = tracker.fifo_matcher.get_statistics()
        print(f"✅ FIFO統計: {stats}")

    except Exception as e:
        print(f"❌ 基本功能測試失敗: {e}")
        import traceback
        traceback.print_exc()
        return False

    # 步驟4: 測試回報處理
    print("\n📋 步驟4: 測試回報處理")
    try:
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

        # 處理回報
        success = tracker.process_real_order_reply(mock_reply)
        print(f"✅ 處理回報: {'成功' if success else '失敗'}")

        # 檢查匹配後的統計
        stats_after = tracker.fifo_matcher.get_statistics()
        print(f"✅ 處理後統計: {stats_after}")

        # 檢查訂單狀態
        order_status = tracker.get_order_status("test_real_001")
        if order_status:
            print(f"✅ 訂單狀態: {order_status.status}")
        else:
            print("❌ 找不到訂單狀態")

    except Exception as e:
        print(f"❌ 回報處理測試失敗: {e}")
        import traceback
        traceback.print_exc()
        return False

    print("\n🎉 所有步驟測試通過！")
    return True

if __name__ == "__main__":
    test_step_by_step()
