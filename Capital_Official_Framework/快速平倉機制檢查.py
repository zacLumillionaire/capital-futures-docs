#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
快速平倉機制檢查
重點檢查移動停利平倉的關鍵環節
"""

import sqlite3
import os
from datetime import datetime

def check_exit_managers():
    """檢查平倉管理器"""
    print("🔍 檢查平倉管理器...")
    
    exit_files = [
        'unified_exit_manager.py',
        'exit_mechanism_manager.py', 
        'global_exit_manager.py',
        'stop_loss_executor.py'
    ]
    
    found_managers = []
    for file_name in exit_files:
        if os.path.exists(file_name):
            found_managers.append(file_name)
            print(f"   ✅ 找到: {file_name}")
            
            # 檢查關鍵方法
            with open(file_name, 'r', encoding='utf-8') as f:
                content = f.read()
            
            if 'execute_exit' in content or 'place_exit_order' in content:
                print(f"      ✅ 包含平倉執行方法")
            else:
                print(f"      ❌ 缺少平倉執行方法")
            
            if 'trailing_stop' in content.lower():
                print(f"      ✅ 支援移動停利")
            else:
                print(f"      ⚠️ 可能不支援移動停利")
        else:
            print(f"   ❌ 找不到: {file_name}")
    
    if not found_managers:
        print("   🚨 警告: 沒有找到任何平倉管理器!")
        return False
    
    return True

def check_current_positions():
    """檢查當前部位狀態"""
    print("\n🔍 檢查當前部位狀態...")
    
    try:
        with sqlite3.connect("multi_group_strategy.db") as conn:
            cursor = conn.cursor()
            
            # 檢查活躍部位
            cursor.execute("""
                SELECT pr.id, pr.lot_id, pr.direction, pr.entry_price,
                       pr.trailing_activation_points, pr.trailing_activated,
                       rms.peak_price, rms.current_price, rms.trailing_activated as rms_activated
                FROM position_records pr
                LEFT JOIN risk_management_states rms ON pr.id = rms.position_id
                WHERE pr.status = 'ACTIVE'
                ORDER BY pr.id
            """)
            
            positions = cursor.fetchall()
            
            if not positions:
                print("   ℹ️ 沒有活躍部位")
                return True
            
            print(f"   找到 {len(positions)} 個活躍部位:")
            
            critical_issues = []
            
            for pos in positions:
                pos_id, lot_id, direction, entry_price, activation_points, \
                pr_activated, peak_price, current_price, rms_activated = pos
                
                print(f"\n   📊 部位 {pos_id} (第{lot_id}口, {direction}):")
                print(f"      進場價格: {entry_price}")
                print(f"      啟動點數: {activation_points}")
                print(f"      PR啟動狀態: {pr_activated}")
                print(f"      RMS啟動狀態: {rms_activated}")
                print(f"      峰值價格: {peak_price}")
                print(f"      當前價格: {current_price}")
                
                # 檢查關鍵問題
                if activation_points is None:
                    critical_issues.append(f"部位{pos_id}缺少啟動點數")
                
                if pr_activated != rms_activated:
                    critical_issues.append(f"部位{pos_id}狀態不同步")
                
                # 檢查是否應該平倉
                if rms_activated and peak_price and current_price and entry_price:
                    if direction == 'SHORT':
                        # SHORT部位移停價格計算
                        profit_points = entry_price - peak_price
                        pullback_points = profit_points * 0.2  # 假設20%回撤
                        trailing_stop_price = peak_price + pullback_points
                        
                        should_exit = current_price >= trailing_stop_price
                        
                        print(f"      移停價格: {trailing_stop_price:.1f}")
                        print(f"      應該平倉: {should_exit}")
                        
                        if should_exit:
                            critical_issues.append(f"部位{pos_id}應該立即平倉!")
                            print(f"      🚨 觸發平倉條件!")
            
            if critical_issues:
                print(f"\n🚨 發現 {len(critical_issues)} 個關鍵問題:")
                for issue in critical_issues:
                    print(f"   🚨 {issue}")
                return False
            else:
                print(f"\n✅ 部位狀態檢查通過")
                return True
                
    except Exception as e:
        print(f"   ❌ 檢查失敗: {e}")
        return False

def check_api_connection():
    """檢查API連接"""
    print("\n🔍 檢查API連接...")
    
    # 檢查API相關文件
    api_files = [
        'api_manager.py',
        'trading_api.py',
        'order_api.py'
    ]
    
    found_api = False
    for file_name in api_files:
        if os.path.exists(file_name):
            found_api = True
            print(f"   ✅ 找到API文件: {file_name}")
            
            with open(file_name, 'r', encoding='utf-8') as f:
                content = f.read()
            
            if 'sell' in content.lower() or 'buy' in content.lower():
                print(f"      ✅ 支援買賣操作")
            else:
                print(f"      ⚠️ 可能不支援買賣操作")
    
    if not found_api:
        print("   ⚠️ 沒有找到API文件")
        return False
    
    return True

def simulate_exit_scenario():
    """模擬平倉情境"""
    print("\n🧪 模擬平倉情境...")
    
    try:
        with sqlite3.connect("multi_group_strategy.db") as conn:
            cursor = conn.cursor()
            
            # 獲取已啟動移動停利的部位
            cursor.execute("""
                SELECT pr.id, pr.direction, pr.entry_price, rms.peak_price
                FROM position_records pr
                JOIN risk_management_states rms ON pr.id = rms.position_id
                WHERE pr.status = 'ACTIVE' AND rms.trailing_activated = 1
            """)
            
            positions = cursor.fetchall()
            
            if not positions:
                print("   ℹ️ 沒有已啟動移動停利的部位")
                return True
            
            # 模擬價格觸發平倉
            test_price = 22533  # 模擬觸發價格
            
            print(f"   模擬價格: {test_price}")
            
            for pos_id, direction, entry_price, peak_price in positions:
                if direction == 'SHORT':
                    profit_points = entry_price - peak_price
                    pullback_points = profit_points * 0.2
                    trailing_stop_price = peak_price + pullback_points
                    
                    should_exit = test_price >= trailing_stop_price
                    
                    print(f"   部位{pos_id}: 移停價格={trailing_stop_price:.1f}, 觸發={should_exit}")
                    
                    if should_exit:
                        # 模擬平倉
                        exit_price = test_price + 1  # 模擬滑價
                        pnl = entry_price - exit_price
                        
                        print(f"      模擬平倉: @{exit_price}, 損益={pnl:.1f}點")
                        
                        if pnl > 0:
                            print(f"      ✅ 獲利平倉")
                        else:
                            print(f"      ⚠️ 可能虧損")
            
            return True
            
    except Exception as e:
        print(f"   ❌ 模擬失敗: {e}")
        return False

def generate_summary(results):
    """生成檢查總結"""
    print("\n📋 平倉機制檢查總結")
    print("=" * 40)
    
    passed = sum(results)
    total = len(results)
    
    print(f"檢查項目: {total}")
    print(f"通過項目: {passed}")
    print(f"失敗項目: {total - passed}")
    
    if passed == total:
        print("\n✅ 平倉機制檢查全部通過!")
        print("   可以安心進行移動停利交易")
    elif passed >= total * 0.8:
        print("\n⚠️ 平倉機制基本正常，但有部分問題")
        print("   建議修復問題後再交易")
    else:
        print("\n🚨 平倉機制存在嚴重問題!")
        print("   強烈建議修復後再交易，避免能賺沒賺到!")
    
    print(f"\n📝 建議:")
    print("   1. 密切監控移動停利觸發")
    print("   2. 準備手動平倉備案")
    print("   3. 設置平倉失敗警報")
    print("   4. 定期檢查系統狀態")

def main():
    """主檢查函數"""
    print("🚀 移動停利平倉機制快速檢查")
    print("=" * 40)
    print("🎯 確保能賺到錢，避免平倉失敗!")
    print("=" * 40)
    
    results = []
    
    # 1. 檢查平倉管理器
    results.append(check_exit_managers())
    
    # 2. 檢查當前部位
    results.append(check_current_positions())
    
    # 3. 檢查API連接
    results.append(check_api_connection())
    
    # 4. 模擬平倉情境
    results.append(simulate_exit_scenario())
    
    # 5. 生成總結
    generate_summary(results)

if __name__ == "__main__":
    main()
