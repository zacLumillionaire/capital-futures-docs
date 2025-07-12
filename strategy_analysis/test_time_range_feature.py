#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
測試自定義時間區間功能
驗證Web GUI的時間區間輸入功能是否正常工作
"""

import requests
import json
import time

def test_custom_time_range():
    """測試自定義時間區間功能"""
    
    # 測試配置 - 使用10:00-10:01作為開盤區間
    test_config = {
        "trade_lots": 3,
        "start_date": "2024-11-04",
        "end_date": "2024-11-05",
        "range_start_time": "10:00",  # 自定義開盤區間開始時間
        "range_end_time": "10:01",    # 自定義開盤區間結束時間
        "lot1_trigger": 15,
        "lot1_trailing": 20,
        "lot2_trigger": 40,
        "lot2_trailing": 20,
        "lot2_protection": 2.0,
        "lot3_trigger": 65,
        "lot3_trailing": 20,
        "lot3_protection": 2.0,
        "range_filter_enabled": False,
        "max_range_points": 50,
        "risk_filter_enabled": False,
        "daily_loss_limit": 150,
        "profit_target": 200,
        "stop_loss_filter_enabled": False,
        "stop_loss_type": "range_boundary",
        "fixed_stop_loss_points": 15.0
    }
    
    print("🧪 測試自定義時間區間功能")
    print(f"📅 測試期間: {test_config['start_date']} 至 {test_config['end_date']}")
    print(f"🕐 自定義開盤區間: {test_config['range_start_time']} 至 {test_config['range_end_time']}")
    print("⏳ 預期交易開始時間: 10:02")
    
    try:
        # 發送回測請求
        response = requests.post(
            'http://localhost:8080/run_backtest',
            headers={'Content-Type': 'application/json'},
            json=test_config,
            timeout=60
        )
        
        if response.status_code == 200:
            result = response.json()
            if result.get('success'):
                print("✅ 回測請求發送成功")
                
                # 等待回測完成
                print("⏳ 等待回測完成...")
                for i in range(30):  # 最多等待30秒
                    time.sleep(1)
                    status_response = requests.get('http://localhost:8080/status')
                    if status_response.status_code == 200:
                        status = status_response.json()
                        if status.get('completed'):
                            print("✅ 回測執行完成")
                            print(f"📊 回測結果: {status.get('result', 'N/A')}")
                            return True
                        elif status.get('error'):
                            print(f"❌ 回測執行錯誤: {status.get('error')}")
                            return False
                
                print("⏰ 回測執行超時")
                return False
            else:
                print(f"❌ 回測請求失敗: {result.get('error', 'Unknown error')}")
                return False
        else:
            print(f"❌ HTTP請求失敗: {response.status_code}")
            return False
            
    except Exception as e:
        print(f"❌ 測試執行錯誤: {e}")
        return False

def test_default_time_range():
    """測試預設時間區間功能（向後兼容性測試）"""
    
    # 測試配置 - 不指定時間區間，應該使用預設的08:46-08:47
    test_config = {
        "trade_lots": 3,
        "start_date": "2024-11-04",
        "end_date": "2024-11-05",
        # 不設定 range_start_time 和 range_end_time
        "lot1_trigger": 15,
        "lot1_trailing": 20,
        "lot2_trigger": 40,
        "lot2_trailing": 20,
        "lot2_protection": 2.0,
        "lot3_trigger": 65,
        "lot3_trailing": 20,
        "lot3_protection": 2.0,
        "range_filter_enabled": False,
        "max_range_points": 50,
        "risk_filter_enabled": False,
        "daily_loss_limit": 150,
        "profit_target": 200,
        "stop_loss_filter_enabled": False,
        "stop_loss_type": "range_boundary",
        "fixed_stop_loss_points": 15.0
    }
    
    print("\n🧪 測試預設時間區間功能（向後兼容性）")
    print(f"📅 測試期間: {test_config['start_date']} 至 {test_config['end_date']}")
    print("🕐 使用預設開盤區間: 08:46 至 08:47")
    print("⏳ 預期交易開始時間: 08:48")
    
    try:
        # 發送回測請求
        response = requests.post(
            'http://localhost:8080/run_backtest',
            headers={'Content-Type': 'application/json'},
            json=test_config,
            timeout=60
        )
        
        if response.status_code == 200:
            result = response.json()
            if result.get('success'):
                print("✅ 向後兼容性測試通過")
                return True
            else:
                print(f"❌ 向後兼容性測試失敗: {result.get('error', 'Unknown error')}")
                return False
        else:
            print(f"❌ HTTP請求失敗: {response.status_code}")
            return False
            
    except Exception as e:
        print(f"❌ 向後兼容性測試錯誤: {e}")
        return False

if __name__ == "__main__":
    print("🚀 開始測試自定義時間區間功能")
    print("=" * 50)
    
    # 測試自定義時間區間
    custom_test_result = test_custom_time_range()
    
    # 測試向後兼容性
    default_test_result = test_default_time_range()
    
    print("\n" + "=" * 50)
    print("📋 測試結果總結:")
    print(f"  自定義時間區間功能: {'✅ 通過' if custom_test_result else '❌ 失敗'}")
    print(f"  向後兼容性: {'✅ 通過' if default_test_result else '❌ 失敗'}")
    
    if custom_test_result and default_test_result:
        print("\n🎉 所有測試通過！自定義時間區間功能已成功實現！")
    else:
        print("\n⚠️ 部分測試失敗，請檢查實現")
