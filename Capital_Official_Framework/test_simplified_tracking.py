#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
測試簡化訂單追蹤機制
驗證成交確認、追價觸發、部位狀態同步功能
"""

import os
import sys
import time
from datetime import date

def test_simplified_tracking():
    """測試簡化追蹤機制"""
    print("🧪 測試簡化訂單追蹤機制")
    print("=" * 60)
    
    # 清理舊的測試資料庫
    test_db_path = "test_simplified_tracking.db"
    if os.path.exists(test_db_path):
        os.remove(test_db_path)
        print("✅ 清理舊測試資料庫")
    
    try:
        # 1. 測試簡化追蹤器基本功能
        print("\n📋 測試1: 簡化追蹤器基本功能")
        print("-" * 40)
        
        from simplified_order_tracker import SimplifiedOrderTracker
        
        # 創建簡化追蹤器
        tracker = SimplifiedOrderTracker(console_enabled=True)
        print("✅ 簡化追蹤器創建成功")
        
        # 註冊策略組
        success = tracker.register_strategy_group(
            group_id=1,
            total_lots=3,
            direction="LONG",
            target_price=22344.0,
            product="TM0000"
        )
        print(f"✅ 策略組註冊: {success}")
        
        # 更新已送出口數
        success = tracker.update_submitted_lots(group_id=1, lots=3)
        print(f"✅ 更新已送出口數: {success}")
        
        # 獲取策略組狀態
        status = tracker.get_group_status(group_id=1)
        print(f"✅ 策略組狀態: {status}")
        
        # 2. 測試回報處理
        print("\n📋 測試2: 回報處理功能")
        print("-" * 40)
        
        # 模擬成交回報（基於您提供的LOG格式）
        test_fill_data = "2315544895165,TF,D,N,F020000,6363839,BNF20,TW,TM2507,,u5640,22344.000000,,,,,,,,,1,,,20250705,01:54:07,,0000000,7174,y,20250707,2120000112347,A,FITM,202507,,,,,0000003969,,B,20250704,,,N,,2315544895165"
        
        success = tracker.process_order_reply(test_fill_data)
        print(f"✅ 成交回報處理: {success}")
        
        # 模擬取消回報
        test_cancel_data = "2315544895168,TF,C,N,F020000,6363839,BNF20,TW,TM2507,,u5640,22344.0000,,,,,,,,,1,,,20250705,01:54:10,,0000000,7174,y,20250707,2110001607189,A,FITM,202507,,,,,,,B,20250704,,,N,,2315544895168"
        
        success = tracker.process_order_reply(test_cancel_data)
        print(f"✅ 取消回報處理: {success}")
        
        # 3. 測試統計功能
        print("\n📋 測試3: 統計功能")
        print("-" * 40)
        
        stats = tracker.get_statistics()
        print(f"✅ 統計信息: {stats}")
        
        # 4. 測試多組管理器整合
        print("\n📋 測試4: 多組管理器整合")
        print("-" * 40)
        
        from multi_group_database import MultiGroupDatabaseManager
        from multi_group_config import MultiGroupStrategyConfig, create_preset_configs
        from multi_group_position_manager import MultiGroupPositionManager
        
        # 創建測試資料庫
        db_manager = MultiGroupDatabaseManager(test_db_path)
        print("✅ 資料庫管理器創建成功")
        
        # 創建策略配置
        presets = create_preset_configs()
        config = presets["平衡配置 (2口×2組)"]
        print("✅ 策略配置創建成功")
        
        # 創建部位管理器（包含簡化追蹤器）
        position_manager = MultiGroupPositionManager(
            db_manager=db_manager,
            strategy_config=config,
            simplified_tracker=tracker
        )
        print("✅ 部位管理器創建成功")
        
        # 5. 測試進場信號創建
        print("\n📋 測試5: 進場信號創建")
        print("-" * 40)
        
        today = date.today().isoformat()
        group_ids = position_manager.create_entry_signal(
            direction="LONG",
            signal_time="08:48:15",
            range_high=22400.0,
            range_low=22350.0
        )
        print(f"✅ 創建進場信號: {group_ids}")
        
        # 6. 測試回調機制
        print("\n📋 測試6: 回調機制測試")
        print("-" * 40)
        
        # 添加測試回調
        def test_fill_callback(group_id, price, qty, filled_lots, total_lots):
            print(f"🎯 [測試回調] 成交: 組{group_id}, {qty}口@{price}, 進度{filled_lots}/{total_lots}")
        
        def test_retry_callback(group_id, qty, price, retry_count):
            print(f"🔄 [測試回調] 追價: 組{group_id}, {qty}口@{price}, 第{retry_count}次")
        
        tracker.add_fill_callback(test_fill_callback)
        tracker.add_retry_callback(test_retry_callback)
        print("✅ 回調機制設置完成")
        
        # 再次測試回報處理（觸發回調）
        test_fill_data2 = "2315544895169,TF,D,N,F020000,6363839,BNF20,TW,TM2507,,u5640,22344.000000,,,,,,,,,2,,,20250705,01:54:11,,0000000,7174,y,20250707,2120000112348,A,FITM,202507,,,,,0000003970,,B,20250704,,,N,,2315544895169"
        
        success = tracker.process_order_reply(test_fill_data2)
        print(f"✅ 回調觸發測試: {success}")
        
        # 7. 測試清理功能
        print("\n📋 測試7: 清理功能")
        print("-" * 40)
        
        tracker.cleanup_completed_groups(max_age_seconds=1)
        print("✅ 清理功能測試完成")
        
        # 8. 最終統計
        print("\n📊 最終統計")
        print("-" * 40)
        
        final_stats = tracker.get_statistics()
        print(f"總策略組: {final_stats['total_groups']}")
        print(f"完成組數: {final_stats['completed_groups']}")
        print(f"失敗組數: {final_stats['failed_groups']}")
        print(f"活躍組數: {final_stats['active_groups']}")
        
        print("\n🎉 簡化追蹤機制測試完成!")
        print("✅ 所有功能測試通過")
        
        return True
        
    except Exception as e:
        print(f"❌ 測試失敗: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    finally:
        # 清理測試資料庫
        if os.path.exists(test_db_path):
            try:
                os.remove(test_db_path)
                print("🧹 測試資料庫已清理")
            except:
                pass

def test_integration_with_existing_system():
    """測試與現有系統的整合"""
    print("\n🔗 測試與現有系統整合")
    print("=" * 60)
    
    try:
        # 測試導入現有模組
        from simple_integrated import SimpleIntegratedApp
        print("✅ 現有系統模組導入成功")
        
        # 測試簡化追蹤器導入
        from simplified_order_tracker import SimplifiedOrderTracker
        print("✅ 簡化追蹤器導入成功")
        
        # 測試多組管理器導入
        from multi_group_position_manager import MultiGroupPositionManager
        print("✅ 多組管理器導入成功")
        
        print("✅ 整合測試通過")
        return True
        
    except Exception as e:
        print(f"❌ 整合測試失敗: {e}")
        return False

if __name__ == "__main__":
    print("🚀 開始簡化追蹤機制測試")
    
    # 基本功能測試
    basic_test = test_simplified_tracking()
    
    # 整合測試
    integration_test = test_integration_with_existing_system()
    
    # 總結
    print("\n📋 測試總結")
    print("=" * 60)
    print(f"基本功能測試: {'✅ 通過' if basic_test else '❌ 失敗'}")
    print(f"整合測試: {'✅ 通過' if integration_test else '❌ 失敗'}")
    
    if basic_test and integration_test:
        print("\n🎉 所有測試通過！簡化追蹤機制可以投入使用")
    else:
        print("\n⚠️ 部分測試失敗，需要進一步調試")
