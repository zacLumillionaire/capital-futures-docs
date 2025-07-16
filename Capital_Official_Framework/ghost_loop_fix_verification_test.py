#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
「鬼打牆」重複平倉修復驗證測試
測試原子化狀態更新是否徹底解決重複觸發問題
"""

import time
import threading
import sqlite3
from datetime import datetime
from typing import Dict, List
import sys
import os

# 添加框架路徑
sys.path.insert(0, os.path.dirname(__file__))

def test_atomic_state_update():
    """測試原子化狀態更新機制"""
    print("🧪 測試1: 原子化狀態更新機制")
    print("=" * 60)
    
    try:
        from optimized_risk_manager import OptimizedRiskManager
        from simplified_order_tracker import GlobalExitManager
        
        # 創建測試用的風險管理器
        global_exit_manager = GlobalExitManager()
        risk_manager = OptimizedRiskManager(
            db_manager=None,  # 使用內存模式
            console_enabled=True
        )
        risk_manager.global_exit_manager = global_exit_manager
        
        # 模擬部位數據
        test_position_id = "999"
        position_data = {
            'id': test_position_id,
            'group_id': 1,
            'direction': 'LONG',
            'entry_price': 21500.0,
            'quantity': 1,
            'lot_id': 1,
            'range_high': 21600.0,
            'range_low': 21400.0,
            'status': 'ACTIVE'
        }
        
        # 添加到緩存
        risk_manager.position_cache[test_position_id] = position_data
        risk_manager.trailing_cache[test_position_id] = {
            'activated': True,
            'peak_price': 21550.0,
            'direction': 'LONG'
        }
        
        print(f"✅ 測試部位已添加: {test_position_id}")
        print(f"   進場價格: {position_data['entry_price']}")
        print(f"   峰值價格: 21550.0")
        print(f"   當前緩存數量: {len(risk_manager.position_cache)}")
        
        # 模擬觸發移動停利的價格（20%回撤）
        trigger_price = 21440.0  # 從21550回撤到21440，超過20%
        
        print(f"\n🎯 模擬觸發價格: {trigger_price}")
        print(f"   預期觸發移動停利（峰值21550 → 當前21440）")
        
        # 第一次價格更新
        print(f"\n📊 第一次價格更新...")
        result1 = risk_manager._process_cached_positions(trigger_price, "10:30:00")
        
        print(f"   處理結果: {result1}")
        print(f"   緩存中剩餘部位數量: {len(risk_manager.position_cache)}")
        
        # 驗證部位是否已從緩存中移除
        if test_position_id not in risk_manager.position_cache:
            print("✅ 原子化移除成功: 部位已從緩存中移除")
        else:
            print("❌ 原子化移除失敗: 部位仍在緩存中")
            return False
            
        # 第二次價格更新（模擬下一個tick）
        print(f"\n📊 第二次價格更新（模擬下一個tick）...")
        result2 = risk_manager._process_cached_positions(trigger_price, "10:30:01")
        
        print(f"   處理結果: {result2}")
        print(f"   應該沒有任何觸發（因為部位已移除）")
        
        # 驗證沒有重複觸發
        if result2['drawdown_triggers'] == 0:
            print("✅ 重複觸發防護成功: 第二次更新沒有觸發")
            return True
        else:
            print("❌ 重複觸發防護失敗: 第二次更新仍有觸發")
            return False
            
    except Exception as e:
        print(f"❌ 測試失敗: {e}")
        return False

def test_concurrent_price_updates():
    """測試並發價格更新的競態條件"""
    print("\n🧪 測試2: 並發價格更新競態條件")
    print("=" * 60)
    
    try:
        from optimized_risk_manager import OptimizedRiskManager
        from simplified_order_tracker import GlobalExitManager
        
        # 創建測試用的風險管理器
        global_exit_manager = GlobalExitManager()
        risk_manager = OptimizedRiskManager(
            db_manager=None,
            console_enabled=True
        )
        risk_manager.global_exit_manager = global_exit_manager
        
        # 模擬多個部位
        test_positions = {}
        for i in range(5):
            position_id = f"test_{i}"
            position_data = {
                'id': position_id,
                'group_id': 1,
                'direction': 'LONG',
                'entry_price': 21500.0 + i * 10,
                'quantity': 1,
                'lot_id': i + 1,
                'range_high': 21600.0 + i * 10,
                'range_low': 21400.0 + i * 10,
                'status': 'ACTIVE'
            }
            
            risk_manager.position_cache[position_id] = position_data
            risk_manager.trailing_cache[position_id] = {
                'activated': True,
                'peak_price': 21550.0 + i * 10,
                'direction': 'LONG'
            }
            test_positions[position_id] = position_data
        
        print(f"✅ 創建了 {len(test_positions)} 個測試部位")
        
        # 並發觸發測試
        trigger_results = []
        threads = []
        
        def concurrent_update(thread_id, price):
            try:
                result = risk_manager._process_cached_positions(price, f"10:30:{thread_id:02d}")
                trigger_results.append({
                    'thread_id': thread_id,
                    'result': result,
                    'remaining_positions': len(risk_manager.position_cache)
                })
            except Exception as e:
                trigger_results.append({
                    'thread_id': thread_id,
                    'error': str(e),
                    'remaining_positions': len(risk_manager.position_cache)
                })
        
        # 啟動多個線程同時觸發
        trigger_price = 21440.0
        for i in range(10):
            thread = threading.Thread(
                target=concurrent_update,
                args=(i, trigger_price)
            )
            threads.append(thread)
            thread.start()
        
        # 等待所有線程完成
        for thread in threads:
            thread.join()
        
        print(f"\n📊 並發測試結果:")
        total_triggers = 0
        for result in trigger_results:
            if 'error' not in result:
                triggers = result['result'].get('drawdown_triggers', 0)
                total_triggers += triggers
                print(f"   線程 {result['thread_id']}: 觸發 {triggers} 次, 剩餘部位 {result['remaining_positions']}")
            else:
                print(f"   線程 {result['thread_id']}: 錯誤 - {result['error']}")
        
        print(f"\n📈 總觸發次數: {total_triggers}")
        print(f"📈 最終剩餘部位: {len(risk_manager.position_cache)}")
        
        # 驗證結果
        if total_triggers <= len(test_positions):
            print("✅ 並發競態條件測試通過: 沒有過度觸發")
            return True
        else:
            print("❌ 並發競態條件測試失敗: 存在重複觸發")
            return False
            
    except Exception as e:
        print(f"❌ 並發測試失敗: {e}")
        return False

def test_stop_loss_executor_double_protection():
    """測試StopLossExecutor的雙重保護機制"""
    print("\n🧪 測試3: StopLossExecutor雙重保護機制")
    print("=" * 60)
    
    try:
        from stop_loss_executor import StopLossExecutor
        from simplified_order_tracker import GlobalExitManager
        from stop_loss_monitor import StopLossTrigger
        
        # 創建測試組件
        global_exit_manager = GlobalExitManager()
        executor = StopLossExecutor(
            db_manager=None,
            virtual_real_order_manager=None,
            console_enabled=True
        )
        executor.global_exit_manager = global_exit_manager
        
        # 創建測試觸發器
        trigger_info = StopLossTrigger(
            position_id=888,
            group_id=1,
            direction='LONG',
            current_price=21400.0,
            stop_loss_price=21400.0,
            trigger_time="10:30:00",
            trigger_reason="測試觸發",
            breach_amount=100.0
        )
        
        print(f"✅ 測試觸發器已創建: 部位 {trigger_info.position_id}")
        
        # 第一次執行（應該被前置檢查通過）
        print(f"\n🎯 第一次執行停損...")
        result1 = executor.execute_stop_loss(trigger_info)
        
        print(f"   第一次結果: success={result1.success}")
        if result1.error_message:
            print(f"   錯誤信息: {result1.error_message}")
        
        # 立即第二次執行（應該被前置檢查阻止）
        print(f"\n🎯 立即第二次執行停損...")
        result2 = executor.execute_stop_loss(trigger_info)
        
        print(f"   第二次結果: success={result2.success}")
        if result2.error_message:
            print(f"   錯誤信息: {result2.error_message}")
        
        # 驗證雙重保護
        if not result2.success and "前置檢查防止重複平倉" in result2.error_message:
            print("✅ 雙重保護機制測試通過: 前置檢查成功阻止重複執行")
            return True
        else:
            print("❌ 雙重保護機制測試失敗: 前置檢查未能阻止重複執行")
            return False
            
    except Exception as e:
        print(f"❌ 雙重保護測試失敗: {e}")
        return False

def main():
    """主測試函數"""
    print("🚀 「鬼打牆」重複平倉修復驗證測試")
    print("=" * 80)
    print("測試目標: 驗證原子化狀態更新是否徹底解決重複觸發問題")
    print("=" * 80)
    
    test_results = []
    
    # 執行所有測試
    test_results.append(("原子化狀態更新", test_atomic_state_update()))
    test_results.append(("並發競態條件", test_concurrent_price_updates()))
    test_results.append(("雙重保護機制", test_stop_loss_executor_double_protection()))
    
    # 總結結果
    print("\n" + "=" * 80)
    print("🏁 測試結果總結")
    print("=" * 80)
    
    passed_count = 0
    for test_name, result in test_results:
        status = "✅ 通過" if result else "❌ 失敗"
        print(f"{test_name}: {status}")
        if result:
            passed_count += 1
    
    print(f"\n📊 總體結果: {passed_count}/{len(test_results)} 項測試通過")
    
    if passed_count == len(test_results):
        print("🎉 所有測試通過！「鬼打牆」問題已徹底解決！")
        return True
    else:
        print("⚠️ 部分測試失敗，需要進一步檢查修復效果")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
