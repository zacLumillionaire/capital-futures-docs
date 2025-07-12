#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
測試停損濾網功能
"""

import requests
import json
import time

def test_stop_loss_filter_range_boundary():
    """測試區間邊緣停損"""
    print("🧪 測試停損濾網 - 區間邊緣...")
    
    config = {
        "start_date": "2024-11-01",
        "end_date": "2024-11-13",
        "trade_lots": 3,
        "lot1_trigger": 15,
        "lot1_trailing": 20,
        "lot2_trigger": 40,
        "lot2_trailing": 20,
        "lot2_protection": 2.0,
        "lot3_trigger": 65,
        "lot3_trailing": 20,
        "lot3_protection": 2.0,
        "range_filter_enabled": False,
        "risk_filter_enabled": False,
        "stop_loss_filter_enabled": True,
        "stop_loss_type": "range_boundary",
        "fixed_stop_loss_points": 15
    }
    
    return run_backtest_test(config, "區間邊緣停損")

def test_stop_loss_filter_range_midpoint():
    """測試區間中點停損"""
    print("🧪 測試停損濾網 - 區間中點...")
    
    config = {
        "start_date": "2024-11-01",
        "end_date": "2024-11-13",
        "trade_lots": 3,
        "lot1_trigger": 15,
        "lot1_trailing": 20,
        "lot2_trigger": 40,
        "lot2_trailing": 20,
        "lot2_protection": 2.0,
        "lot3_trigger": 65,
        "lot3_trailing": 20,
        "lot3_protection": 2.0,
        "range_filter_enabled": False,
        "risk_filter_enabled": False,
        "stop_loss_filter_enabled": True,
        "stop_loss_type": "range_midpoint",
        "fixed_stop_loss_points": 15
    }
    
    return run_backtest_test(config, "區間中點停損")

def test_stop_loss_filter_fixed_points():
    """測試固定點數停損"""
    print("🧪 測試停損濾網 - 固定點數...")
    
    config = {
        "start_date": "2024-11-01",
        "end_date": "2024-11-13",
        "trade_lots": 3,
        "lot1_trigger": 15,
        "lot1_trailing": 20,
        "lot2_trigger": 40,
        "lot2_trailing": 20,
        "lot2_protection": 2.0,
        "lot3_trigger": 65,
        "lot3_trailing": 20,
        "lot3_protection": 2.0,
        "range_filter_enabled": False,
        "risk_filter_enabled": False,
        "stop_loss_filter_enabled": True,
        "stop_loss_type": "fixed_points",
        "fixed_stop_loss_points": 20
    }
    
    return run_backtest_test(config, "固定點數停損(20點)")

def run_backtest_test(config, test_name):
    """執行回測測試"""
    try:
        print(f"📤 發送回測請求: {test_name}")
        response = requests.post("http://localhost:8080/run_backtest", 
                               json=config, timeout=10)
        
        if response.status_code != 200:
            print(f"❌ 回測啟動失敗: {response.status_code}")
            return False
            
        print("✅ 回測已啟動，等待完成...")
        
        # 輪詢狀態直到完成
        max_wait = 60
        start_time = time.time()
        
        while time.time() - start_time < max_wait:
            status_response = requests.get("http://localhost:8080/status", timeout=5)
            
            if status_response.status_code != 200:
                print(f"❌ 狀態查詢失敗: {status_response.status_code}")
                return False
                
            status_data = status_response.json()
            
            if status_data.get('completed'):
                print(f"✅ {test_name} 完成！")
                
                # 檢查結果中的停損策略設定
                result = status_data.get('result', {})
                stderr_output = result.get('stderr', '')
                
                if '停損策略' in stderr_output:
                    print(f"📊 停損策略設定已反映在回測中")
                    
                    # 提取策略摘要
                    lines = stderr_output.split('\n')
                    for line in lines:
                        if '初始停損策略' in line:
                            print(f"🎯 {line.strip()}")
                        elif '使用區間中點' in line:
                            print(f"🎯 {line.strip()}")
                
                return True
            elif status_data.get('error'):
                print(f"❌ 回測錯誤: {status_data['error']}")
                return False
            elif status_data.get('running'):
                print("⏳ 回測進行中...")
                time.sleep(2)
            else:
                print("⏸️ 回測狀態未知，繼續等待...")
                time.sleep(2)
        
        print("⏰ 回測超時")
        return False
        
    except Exception as e:
        print(f"❌ 測試過程中發生錯誤: {e}")
        return False

if __name__ == "__main__":
    print("🧪 開始測試停損濾網功能...")
    
    tests = [
        test_stop_loss_filter_range_boundary,
        test_stop_loss_filter_range_midpoint,
        test_stop_loss_filter_fixed_points
    ]
    
    passed = 0
    total = len(tests)
    
    for test_func in tests:
        if test_func():
            passed += 1
            print("✅ 測試通過\n")
        else:
            print("❌ 測試失敗\n")
        
        # 等待一下再執行下一個測試
        time.sleep(2)
    
    print(f"🎉 測試完成: {passed}/{total} 通過")
    
    if passed == total:
        print("✅ 所有停損濾網功能測試通過！")
    else:
        print("❌ 部分測試失敗，需要進一步檢查")
