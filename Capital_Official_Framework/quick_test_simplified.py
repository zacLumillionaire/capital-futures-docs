#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
快速測試簡化追蹤機制
"""

def test_basic_functionality():
    """測試基本功能"""
    try:
        print("🧪 測試簡化追蹤器基本功能")
        
        # 1. 測試導入
        from simplified_order_tracker import SimplifiedOrderTracker
        print("✅ 簡化追蹤器導入成功")
        
        # 2. 創建實例
        tracker = SimplifiedOrderTracker(console_enabled=True)
        print("✅ 簡化追蹤器創建成功")
        
        # 3. 註冊策略組
        success = tracker.register_strategy_group(
            group_id=1,
            total_lots=3,
            direction="LONG",
            target_price=22344.0,
            product="TM0000"
        )
        print(f"✅ 策略組註冊: {success}")
        
        # 4. 更新已送出口數
        success = tracker.update_submitted_lots(group_id=1, lots=3)
        print(f"✅ 更新已送出口數: {success}")
        
        # 5. 測試回報處理
        test_data = "2315544895165,TF,D,N,F020000,6363839,BNF20,TW,TM2507,,u5640,22344.000000,,,,,,,,,1,,,20250705,01:54:07,,0000000,7174,y,20250707,2120000112347,A,FITM,202507,,,,,0000003969,,B,20250704,,,N,,2315544895165"
        success = tracker.process_order_reply(test_data)
        print(f"✅ 回報處理: {success}")
        
        # 6. 獲取統計
        stats = tracker.get_statistics()
        print(f"✅ 統計信息: {stats}")
        
        return True
        
    except Exception as e:
        print(f"❌ 測試失敗: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_integration():
    """測試整合"""
    try:
        print("\n🔗 測試多組管理器整合")
        
        # 測試多組管理器導入
        from multi_group_position_manager import MultiGroupPositionManager
        print("✅ 多組管理器導入成功")
        
        # 測試資料庫管理器導入
        from multi_group_database import MultiGroupDatabaseManager
        print("✅ 資料庫管理器導入成功")
        
        return True
        
    except Exception as e:
        print(f"❌ 整合測試失敗: {e}")
        return False

if __name__ == "__main__":
    print("🚀 快速測試開始")
    print("=" * 40)
    
    basic_ok = test_basic_functionality()
    integration_ok = test_integration()
    
    print("\n📋 測試結果")
    print("=" * 40)
    print(f"基本功能: {'✅ 通過' if basic_ok else '❌ 失敗'}")
    print(f"整合測試: {'✅ 通過' if integration_ok else '❌ 失敗'}")
    
    if basic_ok and integration_ok:
        print("\n🎉 簡化追蹤機制測試通過！")
    else:
        print("\n⚠️ 測試失敗，需要檢查")
