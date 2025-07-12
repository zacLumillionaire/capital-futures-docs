#!/usr/bin/env python3
"""
測試GUI的固定停損模式功能
"""

import requests
import json
import time

def test_gui_fixed_stop_mode():
    """測試GUI的固定停損模式"""
    
    # GUI服務器地址
    base_url = "http://localhost:8080"
    
    # 🎯 固定停損模式配置
    config_data = {
        "trade_lots": 3,
        "start_date": "2024-11-04",
        "end_date": "2024-11-10",
        "range_start_time": "08:55",
        "range_end_time": "08:57",
        "fixed_stop_mode": True,  # 🔑 啟用固定停損模式
        "lot1_trigger": 14,
        "lot1_trailing": 0,
        "lot2_trigger": 40,
        "lot2_trailing": 0,
        "lot2_protection": 0,
        "lot3_trigger": 41,
        "lot3_trailing": 0,
        "lot3_protection": 0,
        "range_filter_enabled": False,
        "risk_filter_enabled": False,
        "stop_loss_filter_enabled": False
    }
    
    print("🎯 測試GUI固定停損模式")
    print("="*60)
    print("配置說明：")
    print("  - fixed_stop_mode: True  ← 🔑 啟用固定停損模式")
    print("  - 第1口：14點固定停損")
    print("  - 第2口：40點固定停損")  
    print("  - 第3口：41點固定停損")
    print("  - 無保護性停損")
    print("  - 無移動停損")
    print("="*60)
    print()
    
    try:
        # 檢查GUI服務器狀態
        print("🔍 檢查GUI服務器狀態...")
        response = requests.get(f"{base_url}/status", timeout=5)
        if response.status_code == 200:
            print("✅ GUI服務器運行正常")
        else:
            print("❌ GUI服務器狀態異常")
            return False
            
        # 發送回測請求
        print("🚀 發送回測請求...")
        response = requests.post(
            f"{base_url}/run_backtest",
            headers={'Content-Type': 'application/json'},
            json=config_data,
            timeout=10
        )
        
        if response.status_code == 200:
            result = response.json()
            if result.get('success'):
                print("✅ 回測請求發送成功")
                
                # 等待回測完成
                print("⏳ 等待回測完成...")
                max_wait = 60  # 最多等待60秒
                wait_time = 0
                
                while wait_time < max_wait:
                    time.sleep(2)
                    wait_time += 2
                    
                    status_response = requests.get(f"{base_url}/status", timeout=5)
                    if status_response.status_code == 200:
                        status_data = status_response.json()
                        
                        if status_data.get('completed'):
                            print("✅ 回測執行完成")
                            if status_data.get('report_ready'):
                                print("📊 報告已準備就緒")
                                return True
                            else:
                                print("📊 正在生成報告...")
                        elif status_data.get('error'):
                            print(f"❌ 回測執行失敗: {status_data.get('error')}")
                            return False
                        elif status_data.get('running'):
                            print(f"⏳ 回測進行中... ({wait_time}s)")
                        else:
                            print(f"🔄 等待中... ({wait_time}s)")
                    else:
                        print("❌ 無法獲取狀態")
                        return False
                
                print("⏰ 等待超時")
                return False
                
            else:
                print(f"❌ 回測請求失敗: {result.get('error', '未知錯誤')}")
                return False
        else:
            print(f"❌ HTTP請求失敗: {response.status_code}")
            return False
            
    except requests.exceptions.ConnectionError:
        print("❌ 無法連接到GUI服務器，請確保GUI服務器正在運行")
        print("   啟動命令: python rev_web_trading_gui.py")
        return False
    except requests.exceptions.Timeout:
        print("❌ 請求超時")
        return False
    except Exception as e:
        print(f"❌ 發生錯誤: {e}")
        return False

def show_expected_log_format():
    """顯示預期的LOG格式"""
    print("\n" + "="*60)
    print("🎯 預期的固定停損模式LOG格式：")
    print("="*60)
    print("📊 第1口設定 | 🎯固定停損模式 | 停損點數: 14點 | 停損點位: [計算值]")
    print("📊 第2口設定 | 🎯固定停損模式 | 停損點數: 40點 | 停損點位: [計算值]")
    print("📊 第3口設定 | 🎯固定停損模式 | 停損點數: 41點 | 停損點位: [計算值]")
    print()
    print("✅ 應該看到：")
    print("  - 🎯固定停損模式 標識")
    print("  - 每口有明確的停損點數")
    print("  - 沒有 🛡️ 保護性停損倍數")
    print("  - 沒有 🔔 移動停損啟動")
    print("  - 沒有 停損點更新 訊息")
    print("  - 第2口停損點維持不變，不會因第1口表現而調整")
    print("="*60)

if __name__ == "__main__":
    success = test_gui_fixed_stop_mode()
    
    if success:
        print("\n🎉 GUI固定停損模式測試成功！")
        show_expected_log_format()
    else:
        print("\n❌ GUI固定停損模式測試失敗")
        print("\n💡 故障排除建議：")
        print("1. 確保GUI服務器正在運行: python rev_web_trading_gui.py")
        print("2. 檢查瀏覽器是否能訪問: http://localhost:8080")
        print("3. 查看GUI服務器的控制台輸出")
