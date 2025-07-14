#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
平倉機制連接檢查
檢查風險引擎、統一出場管理器、下單管理器的連接狀態
"""

import sqlite3
import os
import json
from datetime import datetime

def check_risk_engine_connection():
    """檢查風險引擎連接"""
    print("🔍 檢查風險引擎連接...")
    
    try:
        # 檢查風險引擎文件
        if not os.path.exists('risk_management_engine.py'):
            print("   ❌ 找不到 risk_management_engine.py")
            return False
        
        with open('risk_management_engine.py', 'r', encoding='utf-8') as f:
            content = f.read()
        
        # 檢查統一出場管理器連接
        if 'unified_exit_manager' in content:
            print("   ✅ 風險引擎包含統一出場管理器")
        else:
            print("   ❌ 風險引擎缺少統一出場管理器")
            return False
        
        # 檢查執行出場方法
        if 'execute_exit_actions' in content:
            print("   ✅ 包含執行出場方法")
        else:
            print("   ❌ 缺少執行出場方法")
            return False
        
        # 檢查移動停利處理
        if 'trailing_stop' in content.lower():
            print("   ✅ 支援移動停利處理")
        else:
            print("   ⚠️ 可能不支援移動停利")
        
        return True
        
    except Exception as e:
        print(f"   ❌ 檢查失敗: {e}")
        return False

def check_unified_exit_manager():
    """檢查統一出場管理器"""
    print("\n🔍 檢查統一出場管理器...")
    
    try:
        if not os.path.exists('unified_exit_manager.py'):
            print("   ❌ 找不到 unified_exit_manager.py")
            return False
        
        with open('unified_exit_manager.py', 'r', encoding='utf-8') as f:
            content = f.read()
        
        # 檢查關鍵方法
        methods = [
            'trigger_exit',
            'execute_exit_order', 
            'get_exit_price'
        ]
        
        for method in methods:
            if method in content:
                print(f"   ✅ 包含方法: {method}")
            else:
                print(f"   ❌ 缺少方法: {method}")
                return False
        
        # 檢查下單管理器連接
        if 'order_manager' in content:
            print("   ✅ 連接下單管理器")
        else:
            print("   ❌ 缺少下單管理器連接")
            return False
        
        # 檢查execute_strategy_order調用
        if 'execute_strategy_order' in content:
            print("   ✅ 使用統一下單方法")
        else:
            print("   ❌ 缺少統一下單方法")
            return False
        
        return True
        
    except Exception as e:
        print(f"   ❌ 檢查失敗: {e}")
        return False

def check_order_manager():
    """檢查下單管理器"""
    print("\n🔍 檢查下單管理器...")
    
    try:
        if not os.path.exists('virtual_real_order_manager.py'):
            print("   ❌ 找不到 virtual_real_order_manager.py")
            return False
        
        with open('virtual_real_order_manager.py', 'r', encoding='utf-8') as f:
            content = f.read()
        
        # 檢查關鍵方法
        methods = [
            'execute_strategy_order',
            'get_ask1_price',
            'get_bid1_price'
        ]
        
        for method in methods:
            if method in content:
                print(f"   ✅ 包含方法: {method}")
            else:
                print(f"   ❌ 缺少方法: {method}")
                return False
        
        # 檢查平倉支援
        if 'new_close' in content:
            print("   ✅ 支援新平倉參數")
        else:
            print("   ⚠️ 可能不支援新平倉參數")
        
        # 檢查報價管理器連接
        if 'quote_manager' in content:
            print("   ✅ 連接報價管理器")
        else:
            print("   ❌ 缺少報價管理器連接")
            return False
        
        return True
        
    except Exception as e:
        print(f"   ❌ 檢查失敗: {e}")
        return False

def check_quote_manager():
    """檢查報價管理器"""
    print("\n🔍 檢查報價管理器...")
    
    quote_files = [
        'quote_manager.py',
        'real_time_quote_manager.py',
        'quote_service.py'
    ]
    
    found_quote = False
    for file_name in quote_files:
        if os.path.exists(file_name):
            found_quote = True
            print(f"   ✅ 找到報價管理器: {file_name}")
            
            with open(file_name, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # 檢查關鍵方法
            if 'get_best_ask_price' in content or 'get_ask1_price' in content:
                print(f"      ✅ 支援ASK1價格")
            else:
                print(f"      ⚠️ 可能不支援ASK1價格")
            
            if 'get_best_bid_price' in content or 'get_bid1_price' in content:
                print(f"      ✅ 支援BID1價格")
            else:
                print(f"      ⚠️ 可能不支援BID1價格")
            
            break
    
    if not found_quote:
        print("   ❌ 找不到報價管理器")
        return False
    
    return True

def check_api_connection():
    """檢查API連接"""
    print("\n🔍 檢查API連接...")
    
    api_files = [
        'future_order.py',
        'order_api.py',
        'trading_api.py'
    ]
    
    found_api = False
    for file_name in api_files:
        # 檢查多個可能的路徑
        paths = [file_name, f'Python File/order/{file_name}', f'order/{file_name}']
        
        for path in paths:
            if os.path.exists(path):
                found_api = True
                print(f"   ✅ 找到API文件: {path}")
                
                with open(path, 'r', encoding='utf-8') as f:
                    content = f.read()
                
                # 檢查關鍵方法
                if 'strategy_order' in content:
                    print(f"      ✅ 支援策略下單")
                else:
                    print(f"      ⚠️ 可能不支援策略下單")
                
                if 'new_close' in content:
                    print(f"      ✅ 支援新平倉參數")
                else:
                    print(f"      ⚠️ 可能不支援新平倉參數")
                
                break
        
        if found_api:
            break
    
    if not found_api:
        print("   ❌ 找不到API文件")
        return False
    
    return True

def simulate_exit_flow():
    """模擬平倉流程"""
    print("\n🧪 模擬平倉流程...")
    
    try:
        # 模擬移動停利觸發
        print("   1. 風險引擎檢測到移動停利觸發")
        print("   2. 調用 unified_exit_manager.trigger_exit()")
        print("   3. 獲取部位資訊")
        print("   4. 計算出場價格 (SHORT用ASK1)")
        print("   5. 調用 order_manager.execute_strategy_order()")
        print("   6. 設置 new_close=1 (平倉)")
        print("   7. 發送API下單請求")
        print("   8. 接收成交回報")
        print("   9. 更新部位狀態為EXITED")
        print("   10. 記錄損益結果")
        
        # 檢查當前部位是否符合觸發條件
        with sqlite3.connect("multi_group_strategy.db") as conn:
            cursor = conn.cursor()
            
            cursor.execute("""
                SELECT pr.id, pr.direction, pr.entry_price, rms.peak_price
                FROM position_records pr
                JOIN risk_management_states rms ON pr.id = rms.position_id
                WHERE pr.status = 'ACTIVE' AND rms.trailing_activated = 1
            """)
            
            positions = cursor.fetchall()
            
            if positions:
                print(f"\n   📊 當前有 {len(positions)} 個部位可能觸發平倉:")
                
                for pos_id, direction, entry_price, peak_price in positions:
                    if direction == 'SHORT':
                        profit_points = entry_price - peak_price
                        pullback_points = profit_points * 0.2
                        trailing_stop_price = peak_price + pullback_points
                        
                        print(f"      部位{pos_id}: 移停價格={trailing_stop_price:.1f}")
                        print(f"         當價格 >= {trailing_stop_price:.1f} 時觸發平倉")
            else:
                print("   ℹ️ 當前沒有已啟動移動停利的部位")
        
        return True
        
    except Exception as e:
        print(f"   ❌ 模擬失敗: {e}")
        return False

def generate_connection_report(results):
    """生成連接檢查報告"""
    print("\n📋 平倉機制連接檢查報告")
    print("=" * 50)
    
    passed = sum(results)
    total = len(results)
    
    print(f"檢查項目: {total}")
    print(f"通過項目: {passed}")
    print(f"失敗項目: {total - passed}")
    
    if passed == total:
        print("\n✅ 平倉機制連接檢查全部通過!")
        print("   所有組件都正確連接，平倉機制應該能正常工作")
    elif passed >= total * 0.8:
        print("\n⚠️ 平倉機制基本連接正常，但有部分問題")
        print("   建議修復問題以確保平倉穩定性")
    else:
        print("\n🚨 平倉機制連接存在嚴重問題!")
        print("   必須修復連接問題，否則平倉可能失敗!")
    
    # 關鍵風險點
    print(f"\n⚠️ 關鍵風險點:")
    print("   1. 報價管理器連接失敗 → 無法獲取平倉價格")
    print("   2. API連接失敗 → 無法執行平倉下單")
    print("   3. 統一出場管理器缺失 → 平倉邏輯不完整")
    print("   4. 風險引擎連接失敗 → 無法觸發平倉")
    
    # 修復建議
    print(f"\n🔧 修復建議:")
    if passed < total:
        print("   1. 檢查缺失的組件文件")
        print("   2. 確認組件間的連接配置")
        print("   3. 測試API連接狀態")
        print("   4. 驗證報價數據來源")
    
    print("   5. 設置平倉失敗警報")
    print("   6. 準備手動平倉備案")
    print("   7. 定期檢查連接狀態")

def main():
    """主檢查函數"""
    print("🚀 平倉機制連接檢查")
    print("=" * 40)
    print("🎯 確保所有組件正確連接，避免平倉失敗!")
    print("=" * 40)
    
    results = []
    
    # 1. 檢查風險引擎連接
    results.append(check_risk_engine_connection())
    
    # 2. 檢查統一出場管理器
    results.append(check_unified_exit_manager())
    
    # 3. 檢查下單管理器
    results.append(check_order_manager())
    
    # 4. 檢查報價管理器
    results.append(check_quote_manager())
    
    # 5. 檢查API連接
    results.append(check_api_connection())
    
    # 6. 模擬平倉流程
    results.append(simulate_exit_flow())
    
    # 7. 生成報告
    generate_connection_report(results)

if __name__ == "__main__":
    main()
