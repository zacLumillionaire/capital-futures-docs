#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
多部位停損問題重現測試
測試場景：3個SHORT部位同時觸發停損，驗證當前的錯誤行為
"""

import sys
import os
import time
from datetime import datetime

# 添加框架路徑
sys.path.append(os.path.join(os.path.dirname(__file__), 'Capital_Official_Framework'))

def test_multi_position_stop_loss():
    """
    測試多部位同時觸發停損的問題
    重現LOG中的錯誤場景
    """
    print("🧪 開始測試多部位停損問題重現...")
    print("=" * 60)
    
    try:
        # 導入必要模組
        from stop_loss_executor import StopLossExecutor
        from optimized_risk_manager import OptimizedRiskManager
        from simplified_order_tracker import GlobalExitManager
        from stop_loss_monitor import StopLossTrigger
        
        print("✅ 模組導入成功")
        
        # 創建測試實例
        global_exit_manager = GlobalExitManager()
        stop_executor = StopLossExecutor(console_enabled=True)
        
        print("✅ 測試實例創建成功")
        
        # 模擬3個SHORT部位的停損觸發
        positions = [
            {"id": 1, "direction": "SHORT", "entry_price": 21535.0},
            {"id": 2, "direction": "SHORT", "entry_price": 21535.0}, 
            {"id": 3, "direction": "SHORT", "entry_price": 21535.0}
        ]
        
        # 模擬觸發價格 (LOG中的21600.0)
        trigger_price = 21600.0
        
        print(f"\n📊 測試場景設定:")
        print(f"  - 部位數量: {len(positions)}")
        print(f"  - 進場價格: 21535.0")
        print(f"  - 觸發價格: {trigger_price}")
        print(f"  - 方向: SHORT")
        
        # 創建停損觸發器
        triggers = []
        for pos in positions:
            trigger = StopLossTrigger(
                position_id=pos["id"],
                group_id=1,
                direction=pos["direction"],
                current_price=trigger_price,
                stop_loss_price=trigger_price,
                trigger_time=datetime.now().strftime('%H:%M:%S'),
                trigger_reason="初始停損觸發: SHORT部位",
                breach_amount=65.0  # 21600 - 21535
            )
            triggers.append(trigger)
        
        print(f"\n🚨 開始模擬同時觸發停損...")
        
        # 同時觸發所有部位的停損
        results = []
        for i, trigger in enumerate(triggers, 1):
            print(f"\n--- 觸發部位 {i} ---")
            result = stop_executor.execute_stop_loss(trigger)
            results.append(result)
            
            print(f"部位{i} 執行結果: {'成功' if result.success else '失敗'}")
            if not result.success:
                print(f"失敗原因: {result.error_message}")
            
            # 短暫延遲模擬真實情況
            time.sleep(0.1)
        
        # 分析結果
        print(f"\n📈 測試結果分析:")
        success_count = sum(1 for r in results if r.success)
        failed_count = len(results) - success_count
        
        print(f"  - 成功執行: {success_count}/{len(results)}")
        print(f"  - 執行失敗: {failed_count}/{len(results)}")
        
        # 檢查是否重現了問題
        if failed_count > 0:
            print(f"\n🔍 問題重現成功！")
            print(f"  - 預期行為: 所有部位都應該能成功平倉")
            print(f"  - 實際行為: {failed_count}個部位平倉失敗")
            
            # 分析失敗原因
            for i, result in enumerate(results, 1):
                if not result.success:
                    print(f"  - 部位{i}失敗原因: {result.error_message}")
        else:
            print(f"\n✅ 所有部位都成功平倉 (問題可能已修復)")
        
        return failed_count > 0
        
    except Exception as e:
        print(f"❌ 測試執行失敗: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_lock_mechanism():
    """
    測試鎖定機制的具體行為
    """
    print(f"\n🔒 測試鎖定機制...")
    
    try:
        from simplified_order_tracker import GlobalExitManager
        
        manager = GlobalExitManager()
        
        # 測試相同的trigger_source
        trigger_source = "stop_loss_初始停損觸發: SHORT部位"
        
        # 第一個部位標記
        result1 = manager.mark_exit("2", trigger_source, "initial_stop_loss")
        print(f"部位2標記結果: {result1}")
        
        # 第二個部位嘗試標記 (應該被阻止)
        result2 = manager.mark_exit("3", trigger_source, "initial_stop_loss")
        print(f"部位3標記結果: {result2}")
        
        # 檢查鎖定狀態
        can_exit_2 = manager.can_exit("2", trigger_source)
        can_exit_3 = manager.can_exit("3", trigger_source)
        
        print(f"部位2可以平倉: {can_exit_2}")
        print(f"部位3可以平倉: {can_exit_3}")
        
        return not result2  # 如果部位3被阻止，說明問題存在
        
    except Exception as e:
        print(f"❌ 鎖定機制測試失敗: {e}")
        return False

if __name__ == "__main__":
    print("🚀 多部位停損問題診斷測試")
    print("=" * 60)
    
    # 測試1: 重現多部位停損問題
    issue_reproduced = test_multi_position_stop_loss()
    
    # 測試2: 驗證鎖定機制問題
    lock_issue = test_lock_mechanism()
    
    print(f"\n📋 總結:")
    print(f"  - 多部位停損問題重現: {'是' if issue_reproduced else '否'}")
    print(f"  - 鎖定機制問題存在: {'是' if lock_issue else '否'}")
    
    if issue_reproduced or lock_issue:
        print(f"\n🎯 確認問題存在，可以開始修復工作")
    else:
        print(f"\n✅ 問題可能已經修復或測試環境不同")
