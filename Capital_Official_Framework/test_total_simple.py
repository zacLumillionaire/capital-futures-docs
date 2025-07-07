# -*- coding: utf-8 -*-
"""
簡單的總量管理器測試
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

def test_step_by_step():
    """逐步測試總量管理器"""
    print("🧪 開始逐步測試總量管理器...")
    
    # 步驟1: 測試TotalLotTracker導入
    print("\n📋 步驟1: 測試TotalLotTracker導入")
    try:
        from total_lot_tracker import TotalLotTracker, TrackerStatus
        print("✅ TotalLotTracker導入成功")
        
        tracker = TotalLotTracker(
            strategy_id="test_1",
            total_target_lots=3,
            lots_per_group=1,
            direction="LONG",
            product="TM0000",
            console_enabled=True
        )
        print("✅ TotalLotTracker創建成功")
        
    except Exception as e:
        print(f"❌ TotalLotTracker測試失敗: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    # 步驟2: 測試TotalLotManager導入
    print("\n📋 步驟2: 測試TotalLotManager導入")
    try:
        from total_lot_manager import TotalLotManager
        print("✅ TotalLotManager導入成功")
        
        manager = TotalLotManager(console_enabled=True)
        print("✅ TotalLotManager創建成功")
        
    except Exception as e:
        print(f"❌ TotalLotManager測試失敗: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    # 步驟3: 測試基本功能
    print("\n📋 步驟3: 測試基本功能")
    try:
        # 創建策略追蹤器
        success = manager.create_strategy_tracker(
            strategy_id="strategy_1",
            total_target_lots=2,
            lots_per_group=1,
            direction="LONG",
            product="TM0000"
        )
        print(f"✅ 創建策略追蹤器: {'成功' if success else '失敗'}")
        
        # 檢查追蹤器
        tracker = manager.get_tracker("strategy_1")
        if tracker:
            print(f"✅ 獲取追蹤器成功: {tracker.strategy_id}")
        else:
            print("❌ 獲取追蹤器失敗")
            return False

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
        success = manager.process_order_reply(mock_reply)
        print(f"✅ 處理回報: {'成功' if success else '失敗'}")

        # 檢查追蹤器狀態
        tracker = manager.get_tracker("strategy_1")
        if tracker:
            print(f"✅ 追蹤器狀態: {tracker.total_filled_lots}/{tracker.total_target_lots}")

        # 檢查統計
        stats = manager.get_statistics()
        print(f"✅ 統計信息: {stats}")

    except Exception as e:
        print(f"❌ 回報處理測試失敗: {e}")
        import traceback
        traceback.print_exc()
        return False

    print("\n🎉 所有步驟測試通過！")
    return True

if __name__ == "__main__":
    test_step_by_step()
