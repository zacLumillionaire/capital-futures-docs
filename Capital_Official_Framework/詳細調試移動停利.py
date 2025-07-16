#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
詳細調試移動停利啟動問題
"""

import sys
import os

def debug_activation_trigger():
    """詳細調試啟動觸發邏輯"""
    print("🔍 詳細調試移動停利啟動邏輯")
    print("=" * 60)
    
    try:
        from optimized_risk_manager import OptimizedRiskManager
        from multi_group_database import MultiGroupDatabaseManager
        
        # 連接到測試資料庫
        db_manager = MultiGroupDatabaseManager("test_virtual_strategy.db")
        
        # 創建風險管理器實例
        risk_manager = OptimizedRiskManager(db_manager, console_enabled=True)
        
        print("\n📊 初始狀態:")
        print(f"activation_cache: {risk_manager.activation_cache}")
        print(f"trailing_cache: {risk_manager.trailing_cache}")
        
        # 手動調用 _check_activation_trigger
        print("\n🧪 手動測試 _check_activation_trigger:")
        
        test_cases = [
            ("27", 21502.0),  # 部位27，剛好達到啟動點
            ("27", 21507.0),  # 部位27，超過啟動點
            ("28", 21527.0),  # 部位28，剛好達到啟動點
            ("28", 21549.0),  # 部位28，超過啟動點
        ]
        
        for position_id, test_price in test_cases:
            print(f"\n測試部位 {position_id} @ 價格 {test_price}:")
            
            # 檢查緩存狀態
            activation_price = risk_manager.activation_cache.get(position_id)
            trailing_data = risk_manager.trailing_cache.get(position_id)
            
            print(f"  activation_price: {activation_price}")
            print(f"  trailing_data: {trailing_data}")
            
            if activation_price and trailing_data:
                direction = trailing_data.get('direction')
                activated = trailing_data.get('activated')
                
                print(f"  direction: {direction}")
                print(f"  already_activated: {activated}")
                
                # 檢查條件
                if direction == 'LONG':
                    condition_met = test_price >= activation_price
                    print(f"  條件檢查: {test_price} >= {activation_price} = {condition_met}")
                
                # 手動調用方法
                try:
                    result = risk_manager._check_activation_trigger(position_id, test_price)
                    print(f"  _check_activation_trigger 結果: {result}")
                    
                    # 檢查狀態變化
                    new_trailing_data = risk_manager.trailing_cache.get(position_id)
                    print(f"  更新後 trailing_data: {new_trailing_data}")
                    
                except Exception as method_error:
                    print(f"  ❌ 方法調用失敗: {method_error}")
            else:
                print(f"  ❌ 緩存數據缺失")
        
        # 測試去重機制
        print("\n🔄 測試去重機制:")
        print(f"trigger_dedup_cache: {risk_manager.trigger_dedup_cache}")
        print(f"dedup_timeout: {risk_manager.dedup_timeout}")
        print(f"min_price_change: {risk_manager.min_price_change}")
        
        # 測試 _should_skip_trigger
        for position_id, test_price in [("27", 21507.0), ("28", 21549.0)]:
            skip_result = risk_manager._should_skip_trigger(position_id, test_price, 'activation')
            print(f"  部位 {position_id} @ {test_price} 是否跳過: {skip_result}")
        
        return True
        
    except Exception as e:
        print(f"❌ 調試失敗: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_step_by_step():
    """逐步測試移動停利流程"""
    print("\n🎯 逐步測試移動停利流程")
    print("=" * 60)
    
    try:
        from optimized_risk_manager import OptimizedRiskManager
        from multi_group_database import MultiGroupDatabaseManager
        
        db_manager = MultiGroupDatabaseManager("test_virtual_strategy.db")
        risk_manager = OptimizedRiskManager(db_manager, console_enabled=True)
        
        # 步驟1：檢查 _process_cached_positions
        print("\n步驟1：測試 _process_cached_positions")
        result = risk_manager._process_cached_positions(21507.0, "test_time")
        print(f"_process_cached_positions 結果: {result}")
        
        # 步驟2：檢查具體的處理邏輯
        print("\n步驟2：檢查處理邏輯")
        with risk_manager.cache_lock:
            for position_id, position_data in risk_manager.position_cache.items():
                print(f"\n處理部位 {position_id}:")
                
                # 檢查初始停損
                stop_result = risk_manager._check_stop_loss_trigger(position_id, 21507.0)
                print(f"  初始停損檢查: {stop_result}")
                
                # 檢查移動停利啟動
                activation_result = risk_manager._check_activation_trigger(position_id, 21507.0)
                print(f"  移動停利啟動檢查: {activation_result}")
                
                # 檢查移動停利更新
                update_result = risk_manager._update_trailing_stop(position_id, 21507.0)
                print(f"  移動停利更新檢查: {update_result}")
        
        return True
        
    except Exception as e:
        print(f"❌ 逐步測試失敗: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    debug_activation_trigger()
    test_step_by_step()
