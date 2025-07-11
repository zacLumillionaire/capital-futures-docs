#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
統一移動停利計算器性能測試
對比統一計算器 vs 分散式組件的性能差異
"""

import time
import threading
from datetime import datetime

# 導入相關模組
from trailing_stop_calculator import TrailingStopCalculator
from async_db_updater import AsyncDatabaseUpdater
from multi_group_database import MultiGroupDatabaseManager

# 導入分散式組件
from trailing_stop_activator import create_trailing_stop_activator
from peak_price_tracker import create_peak_price_tracker
from drawdown_monitor import create_drawdown_monitor

def test_unified_calculator_performance():
    """測試統一計算器性能"""
    print("🚀 測試統一移動停利計算器性能...")
    
    try:
        # 初始化
        db_manager = MultiGroupDatabaseManager("test_unified_perf.db")
        async_updater = AsyncDatabaseUpdater(db_manager, console_enabled=False)
        async_updater.start()
        
        calculator = TrailingStopCalculator(db_manager, async_updater, console_enabled=False)
        
        # 註冊測試部位
        test_positions = []
        for i in range(10):
            position_id = 1000 + i
            calculator.register_position(
                position_id=position_id,
                direction="LONG",
                entry_price=22400.0,
                activation_points=15.0,
                pullback_percent=0.2
            )
            test_positions.append(position_id)
        
        # 性能測試：1000次價格更新
        start_time = time.time()
        for i in range(1000):
            price = 22400 + (i % 100)  # 價格在22400-22500之間變動
            
            for position_id in test_positions:
                calculator.update_price(position_id, price)
        
        unified_time = time.time() - start_time
        
        # 獲取統計信息
        stats = calculator.get_statistics()
        
        print(f"✅ 統一計算器測試完成:")
        print(f"   處理時間: {unified_time:.3f}秒")
        print(f"   平均每次: {(unified_time/10000)*1000:.3f}ms")
        print(f"   統計信息: {stats}")
        
        async_updater.stop()
        return unified_time
        
    except Exception as e:
        print(f"❌ 統一計算器測試失敗: {e}")
        return None

def test_distributed_components_performance():
    """測試分散式組件性能"""
    print("🔄 測試分散式移動停利組件性能...")
    
    try:
        # 初始化
        db_manager = MultiGroupDatabaseManager("test_distributed_perf.db")
        
        # 創建分散式組件
        activator = create_trailing_stop_activator(db_manager, console_enabled=False)
        tracker = create_peak_price_tracker(db_manager, console_enabled=False)
        monitor = create_drawdown_monitor(db_manager, console_enabled=False)
        
        # 創建測試部位（需要在資料庫中創建）
        current_date = datetime.now().strftime("%Y%m%d")
        for i in range(10):
            group_id = db_manager.create_strategy_group(
                date=current_date,
                group_id=2000 + i,
                direction="LONG",
                signal_time="09:00:00",
                range_high=22500.0,
                range_low=22400.0,
                total_lots=1
            )
            
            position_id = db_manager.create_position_record(
                group_id=group_id,
                lot_id=1,
                direction="LONG",
                entry_time="09:00:00",
                rule_config='{"lot_id": 1, "trailing_activation": 15}',
                order_status='PENDING'
            )
            
            # 確認成交
            db_manager.confirm_position_filled(
                position_id=position_id,
                actual_fill_price=22400.0,
                fill_time="09:00:00",
                order_status='FILLED'
            )
            
            # 創建風險管理狀態
            db_manager.create_risk_management_state(
                position_id=position_id,
                peak_price=22400.0,
                current_time="09:00:00",
                update_reason="初始化"
            )
        
        # 性能測試：1000次價格更新
        start_time = time.time()
        for i in range(1000):
            price = 22400 + (i % 100)  # 價格在22400-22500之間變動
            timestamp = "09:00:00"
            
            # 調用分散式組件（模擬報價處理）
            activator.check_trailing_stop_activation(price, timestamp)
            tracker.update_peak_prices(price, timestamp)
            monitor.monitor_drawdown_triggers(price, timestamp)
        
        distributed_time = time.time() - start_time
        
        print(f"✅ 分散式組件測試完成:")
        print(f"   處理時間: {distributed_time:.3f}秒")
        print(f"   平均每次: {(distributed_time/10000)*1000:.3f}ms")
        
        return distributed_time
        
    except Exception as e:
        print(f"❌ 分散式組件測試失敗: {e}")
        return None

def main():
    """主測試函數"""
    print("📊 移動停利系統性能對比測試")
    print("=" * 50)
    
    # 測試統一計算器
    unified_time = test_unified_calculator_performance()
    
    print()
    
    # 測試分散式組件
    distributed_time = test_distributed_components_performance()
    
    print()
    print("📈 性能對比結果:")
    print("=" * 30)
    
    if unified_time and distributed_time:
        improvement = ((distributed_time - unified_time) / distributed_time) * 100
        speedup = distributed_time / unified_time
        
        print(f"統一計算器: {unified_time:.3f}秒")
        print(f"分散式組件: {distributed_time:.3f}秒")
        print(f"性能提升: {improvement:.1f}%")
        print(f"速度倍數: {speedup:.1f}x")
        
        if improvement > 50:
            print("🎉 統一計算器顯著優於分散式組件！")
        elif improvement > 0:
            print("✅ 統一計算器性能更佳")
        else:
            print("⚠️ 需要進一步優化")
    else:
        print("❌ 測試失敗，無法比較性能")

if __name__ == "__main__":
    main()
