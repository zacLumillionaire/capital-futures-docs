#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
測試JSON序列化修復
"""

import requests
import json
import time

def test_status_endpoint():
    """測試/status端點是否能正常返回JSON"""
    try:
        print("🧪 測試 /status 端點...")
        response = requests.get("http://localhost:8080/status", timeout=5)
        
        print(f"📊 HTTP狀態碼: {response.status_code}")
        
        if response.status_code == 200:
            try:
                data = response.json()
                print("✅ JSON解析成功")
                print(f"📋 回測狀態: {data}")
                return True
            except json.JSONDecodeError as e:
                print(f"❌ JSON解析失敗: {e}")
                print(f"📄 原始回應: {response.text}")
                return False
        else:
            print(f"❌ HTTP錯誤: {response.status_code}")
            print(f"📄 錯誤內容: {response.text}")
            return False
            
    except requests.exceptions.RequestException as e:
        print(f"❌ 請求失敗: {e}")
        return False

def test_backtest_execution():
    """測試完整的回測執行流程"""
    try:
        print("\n🚀 測試回測執行...")
        
        # 測試配置
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
            "risk_filter_enabled": False
        }
        
        # 啟動回測
        print("📤 發送回測請求...")
        response = requests.post("http://localhost:8080/run_backtest",
                               json=config, timeout=10)
        
        if response.status_code != 200:
            print(f"❌ 回測啟動失敗: {response.status_code}")
            return False
            
        print("✅ 回測已啟動，等待完成...")
        
        # 輪詢狀態直到完成
        max_wait = 60  # 最多等待60秒
        start_time = time.time()
        
        while time.time() - start_time < max_wait:
            status_response = requests.get("http://localhost:8080/status", timeout=5)
            
            if status_response.status_code != 200:
                print(f"❌ 狀態查詢失敗: {status_response.status_code}")
                return False
                
            status_data = status_response.json()
            
            if status_data.get('completed'):
                print("✅ 回測完成！")
                print(f"📊 最終狀態: {status_data}")
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
    print("🧪 開始測試JSON序列化修復...")
    
    # 測試1: 基本狀態端點
    if test_status_endpoint():
        print("✅ 測試1通過: /status端點正常")
    else:
        print("❌ 測試1失敗: /status端點異常")
        exit(1)
    
    # 測試2: 完整回測流程
    if test_backtest_execution():
        print("✅ 測試2通過: 完整回測流程正常")
    else:
        print("❌ 測試2失敗: 回測流程異常")
        exit(1)
    
    print("\n🎉 所有測試通過！JSON序列化修復成功！")
