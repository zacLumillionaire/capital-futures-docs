#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
移動停利平倉關鍵問題診斷
快速檢查移動停利平倉的關鍵問題
"""

import sqlite3
import os

def check_critical_issues():
    """檢查關鍵問題"""
    print("🚨 移動停利平倉關鍵問題診斷")
    print("=" * 50)
    
    issues = []
    
    # 1. 檢查關鍵文件存在
    print("1️⃣ 檢查關鍵文件...")
    required_files = [
        'risk_management_engine.py',
        'unified_exit_manager.py',
        'virtual_real_order_manager.py'
    ]
    
    for file_name in required_files:
        if os.path.exists(file_name):
            print(f"   ✅ {file_name}")
        else:
            print(f"   ❌ {file_name}")
            issues.append(f"缺少關鍵文件: {file_name}")
    
    # 2. 檢查當前部位狀態
    print("\n2️⃣ 檢查當前部位狀態...")
    try:
        with sqlite3.connect("multi_group_strategy.db") as conn:
            cursor = conn.cursor()
            
            # 檢查活躍部位
            cursor.execute("""
                SELECT pr.id, pr.direction, pr.entry_price, pr.trailing_activated,
                       rms.peak_price, rms.trailing_activated as rms_activated
                FROM position_records pr
                LEFT JOIN risk_management_states rms ON pr.id = rms.position_id
                WHERE pr.status = 'ACTIVE'
            """)
            
            positions = cursor.fetchall()
            
            if not positions:
                print("   ℹ️ 沒有活躍部位")
            else:
                print(f"   找到 {len(positions)} 個活躍部位:")
                
                for pos_id, direction, entry_price, pr_activated, peak_price, rms_activated in positions:
                    print(f"      部位{pos_id} ({direction}): 進場={entry_price}, 峰值={peak_price}")
                    print(f"         PR啟動={pr_activated}, RMS啟動={rms_activated}")
                    
                    # 檢查移動停利觸發條件
                    if rms_activated and peak_price and entry_price:
                        if direction == 'SHORT':
                            profit_points = entry_price - peak_price
                            pullback_points = profit_points * 0.2
                            trailing_stop_price = peak_price + pullback_points
                            
                            # 模擬當前價格
                            current_price = 22513  # 從日誌中看到的價格
                            should_exit = current_price >= trailing_stop_price
                            
                            print(f"         移停價格: {trailing_stop_price:.1f}")
                            print(f"         當前價格: {current_price}")
                            print(f"         應該平倉: {should_exit}")
                            
                            if should_exit:
                                issues.append(f"部位{pos_id}應該立即平倉但未執行")
                                print(f"         🚨 應該立即平倉!")
                    
                    # 檢查狀態同步
                    if pr_activated != rms_activated:
                        issues.append(f"部位{pos_id}狀態不同步")
                        print(f"         ⚠️ 狀態不同步")
    
    except Exception as e:
        print(f"   ❌ 檢查失敗: {e}")
        issues.append(f"資料庫檢查失敗: {e}")
    
    # 3. 檢查風險引擎連接
    print("\n3️⃣ 檢查風險引擎連接...")
    try:
        with open('risk_management_engine.py', 'r', encoding='utf-8') as f:
            risk_content = f.read()
        
        if 'unified_exit_manager' in risk_content:
            print("   ✅ 風險引擎包含統一出場管理器")
        else:
            print("   ❌ 風險引擎缺少統一出場管理器")
            issues.append("風險引擎缺少統一出場管理器連接")
        
        if 'execute_exit_actions' in risk_content:
            print("   ✅ 包含執行出場方法")
        else:
            print("   ❌ 缺少執行出場方法")
            issues.append("風險引擎缺少執行出場方法")
    
    except Exception as e:
        print(f"   ❌ 檢查失敗: {e}")
        issues.append(f"風險引擎檢查失敗: {e}")
    
    # 4. 檢查統一出場管理器
    print("\n4️⃣ 檢查統一出場管理器...")
    try:
        with open('unified_exit_manager.py', 'r', encoding='utf-8') as f:
            exit_content = f.read()
        
        if 'trigger_exit' in exit_content:
            print("   ✅ 包含觸發出場方法")
        else:
            print("   ❌ 缺少觸發出場方法")
            issues.append("統一出場管理器缺少觸發出場方法")
        
        if 'execute_strategy_order' in exit_content:
            print("   ✅ 使用統一下單方法")
        else:
            print("   ❌ 缺少統一下單方法")
            issues.append("統一出場管理器缺少統一下單方法")
        
        if 'new_close=1' in exit_content:
            print("   ✅ 設置平倉參數")
        else:
            print("   ⚠️ 可能缺少平倉參數設置")
            issues.append("統一出場管理器可能缺少平倉參數")
    
    except Exception as e:
        print(f"   ❌ 檢查失敗: {e}")
        issues.append(f"統一出場管理器檢查失敗: {e}")
    
    # 5. 檢查下單管理器
    print("\n5️⃣ 檢查下單管理器...")
    try:
        with open('virtual_real_order_manager.py', 'r', encoding='utf-8') as f:
            order_content = f.read()
        
        if 'get_ask1_price' in order_content and 'get_bid1_price' in order_content:
            print("   ✅ 支援價格獲取")
        else:
            print("   ❌ 缺少價格獲取方法")
            issues.append("下單管理器缺少價格獲取方法")
        
        if 'quote_manager' in order_content:
            print("   ✅ 連接報價管理器")
        else:
            print("   ❌ 缺少報價管理器連接")
            issues.append("下單管理器缺少報價管理器連接")
    
    except Exception as e:
        print(f"   ❌ 檢查失敗: {e}")
        issues.append(f"下單管理器檢查失敗: {e}")
    
    # 6. 檢查API文件
    print("\n6️⃣ 檢查API文件...")
    api_paths = [
        'order_service/FutureOrder.py',
        '../Python File/order/future_order.py'
    ]
    
    found_api = False
    for path in api_paths:
        if os.path.exists(path):
            found_api = True
            print(f"   ✅ 找到API文件: {path}")
            break
    
    if not found_api:
        print("   ❌ 找不到API文件")
        issues.append("找不到API文件")
    
    # 總結
    print(f"\n📋 診斷總結")
    print("=" * 30)
    
    if not issues:
        print("✅ 未發現關鍵問題")
        print("   移動停利平倉機制應該能正常工作")
        print("   建議檢查系統運行狀態和連接")
    else:
        print(f"🚨 發現 {len(issues)} 個關鍵問題:")
        for i, issue in enumerate(issues, 1):
            print(f"   {i}. {issue}")
        
        print(f"\n🔧 緊急修復建議:")
        print("   1. 立即修復關鍵問題")
        print("   2. 檢查系統組件連接")
        print("   3. 驗證API連接狀態")
        print("   4. 準備手動平倉備案")
    
    # 風險評估
    critical_count = len([issue for issue in issues if any(keyword in issue for keyword in ['缺少', '失敗', '不同步'])])
    
    if critical_count == 0:
        risk_level = "低風險"
        recommendation = "可以安心交易"
    elif critical_count <= 2:
        risk_level = "中風險"
        recommendation = "建議修復後交易"
    else:
        risk_level = "高風險"
        recommendation = "必須修復後才能交易"
    
    print(f"\n🎯 風險評估: {risk_level}")
    print(f"📝 建議: {recommendation}")
    
    return len(issues) == 0

def main():
    """主診斷函數"""
    success = check_critical_issues()
    
    if success:
        print("\n🎉 診斷完成：移動停利平倉機制準備就緒!")
    else:
        print("\n⚠️ 診斷完成：發現問題需要修復!")

if __name__ == "__main__":
    main()
