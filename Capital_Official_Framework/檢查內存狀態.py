#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
檢查 OptimizedRiskManager 內存狀態
需要在虛擬測試機運行時執行
"""

import sys
import os

def check_memory_state():
    """檢查內存狀態"""
    print("🧠 檢查 OptimizedRiskManager 內存狀態")
    print("=" * 60)
    
    try:
        # 導入必要模組
        from optimized_risk_manager import OptimizedRiskManager
        from multi_group_database import MultiGroupDatabaseManager
        
        # 連接到測試資料庫
        db_manager = MultiGroupDatabaseManager("test_virtual_strategy.db")
        
        # 創建風險管理器實例
        risk_manager = OptimizedRiskManager(db_manager, console_enabled=True)
        
        print("\n📊 當前內存狀態:")
        print(f"position_cache 數量: {len(risk_manager.position_cache)}")
        print(f"activation_cache 數量: {len(risk_manager.activation_cache)}")
        print(f"trailing_cache 數量: {len(risk_manager.trailing_cache)}")
        print(f"stop_loss_cache 數量: {len(risk_manager.stop_loss_cache)}")
        
        # 詳細顯示緩存內容
        print("\n🔍 詳細緩存內容:")
        
        print("\n📍 position_cache:")
        for pos_id, pos_data in risk_manager.position_cache.items():
            print(f"  部位 {pos_id}:")
            print(f"    entry_price: {pos_data.get('entry_price')}")
            print(f"    direction: {pos_data.get('direction')}")
            print(f"    status: {pos_data.get('status')}")
        
        print("\n🎯 activation_cache:")
        for pos_id, activation_price in risk_manager.activation_cache.items():
            print(f"  部位 {pos_id}: 啟動點位 = {activation_price}")
        
        print("\n📈 trailing_cache:")
        for pos_id, trailing_data in risk_manager.trailing_cache.items():
            print(f"  部位 {pos_id}:")
            print(f"    activated: {trailing_data.get('activated')}")
            print(f"    peak_price: {trailing_data.get('peak_price')}")
            print(f"    direction: {trailing_data.get('direction')}")
        
        print("\n🛡️ stop_loss_cache:")
        for pos_id, stop_price in risk_manager.stop_loss_cache.items():
            print(f"  部位 {pos_id}: 停損點位 = {stop_price}")
        
        # 手動測試價格更新
        print("\n🧪 手動測試價格更新:")
        test_prices = [21502.0, 21507.0, 21525.0, 21527.0, 21549.0]
        
        for test_price in test_prices:
            print(f"\n測試價格: {test_price}")
            result = risk_manager.update_price(test_price)
            print(f"  結果: {result}")
            
            # 檢查啟動狀態變化
            print("  啟動狀態檢查:")
            for pos_id, trailing_data in risk_manager.trailing_cache.items():
                activated = trailing_data.get('activated', False)
                peak = trailing_data.get('peak_price', 0)
                print(f"    部位 {pos_id}: activated={activated}, peak={peak}")
        
        return True
        
    except Exception as e:
        print(f"❌ 檢查失敗: {e}")
        import traceback
        traceback.print_exc()
        return False

def simulate_position_creation():
    """模擬部位創建過程"""
    print("\n🎭 模擬部位創建過程:")
    print("=" * 60)
    
    try:
        from optimized_risk_manager import OptimizedRiskManager
        from multi_group_database import MultiGroupDatabaseManager
        
        db_manager = MultiGroupDatabaseManager("test_virtual_strategy.db")
        risk_manager = OptimizedRiskManager(db_manager, console_enabled=True)
        
        # 模擬部位數據
        position_data_27 = {
            'id': 27,
            'direction': 'LONG',
            'entry_price': 21487.0,
            'range_high': 21540.0,
            'range_low': 21510.0,
            'group_id': 1
        }
        
        position_data_28 = {
            'id': 28,
            'direction': 'LONG',
            'entry_price': 21487.0,
            'range_high': 21540.0,
            'range_low': 21510.0,
            'group_id': 1
        }
        
        print("🎯 模擬新部位事件:")
        risk_manager.on_new_position(position_data_27)
        risk_manager.on_new_position(position_data_28)
        
        print("\n📊 模擬後的緩存狀態:")
        print(f"activation_cache: {risk_manager.activation_cache}")
        print(f"trailing_cache: {risk_manager.trailing_cache}")
        
        # 測試價格更新
        print("\n🧪 測試價格更新:")
        test_price = 21507.0
        result = risk_manager.update_price(test_price)
        print(f"價格 {test_price} 更新結果: {result}")
        
        return True
        
    except Exception as e:
        print(f"❌ 模擬失敗: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    print("選擇檢查模式:")
    print("1. 檢查現有內存狀態")
    print("2. 模擬部位創建過程")
    
    choice = input("請輸入選擇 (1 或 2): ").strip()
    
    if choice == "1":
        check_memory_state()
    elif choice == "2":
        simulate_position_creation()
    else:
        print("執行所有檢查:")
        check_memory_state()
        simulate_position_creation()
