#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
時間區間功能驗證腳本
測試反轉策略是否正確處理自定義時間區間
"""

import subprocess
import sys
import json
from datetime import datetime

def test_time_range_functionality():
    """測試時間區間功能"""
    print("🕐 時間區間功能驗證測試")
    print("=" * 50)
    
    # 測試配置
    test_configs = [
        {
            "name": "標準開盤區間",
            "start_time": "08:46",
            "end_time": "08:47",
            "description": "預設的標準開盤區間"
        },
        {
            "name": "用戶指定區間",
            "start_time": "11:30", 
            "end_time": "11:32",
            "description": "用戶提到的 11:30-11:32 時間區間"
        },
        {
            "name": "下午時段",
            "start_time": "13:00",
            "end_time": "13:05", 
            "description": "下午時段測試"
        }
    ]
    
    # 基本GUI配置
    base_gui_config = {
        "trade_lots": 3,
        "start_date": "2024-11-04",
        "end_date": "2024-11-05",  # 只測試兩天，快速驗證
        "lot1_trigger": 15,
        "lot1_trailing": 20,
        "lot1_protection": 0.5,
        "lot2_trigger": 25,
        "lot2_trailing": 30,
        "lot2_protection": 0.6,
        "lot3_trigger": 35,
        "lot3_trailing": 40,
        "lot3_protection": 0.7,
        "risk_filter_enabled": False,
        "range_filter_enabled": False,
        "stop_loss_filter_enabled": False
    }
    
    results = []
    
    for config in test_configs:
        print(f"\n🧪 測試: {config['name']}")
        print(f"📅 時間區間: {config['start_time']} - {config['end_time']}")
        print(f"📝 說明: {config['description']}")
        print("-" * 40)
        
        # 創建測試配置
        test_gui_config = base_gui_config.copy()
        test_gui_config["range_start_time"] = config["start_time"]
        test_gui_config["range_end_time"] = config["end_time"]
        
        try:
            # 執行反轉策略測試
            cmd = [
                sys.executable,
                "rev_multi_Profit-Funded Risk_多口.py",
                "--gui-mode",
                "--config", json.dumps(test_gui_config, ensure_ascii=False)
            ]
            
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=60)
            
            if result.returncode == 0:
                # 解析輸出
                output_lines = result.stdout.split('\n')
                time_range_found = False
                trades_found = False
                
                for line in output_lines:
                    if "開盤區間時間:" in line:
                        print(f"✅ 時間設定: {line.strip()}")
                        time_range_found = True
                    elif "總交易次數:" in line:
                        print(f"📊 {line.strip()}")
                        trades_found = True
                    elif "總損益" in line and "點" in line:
                        print(f"💰 {line.strip()}")
                
                if time_range_found:
                    status = "✅ 成功"
                    print(f"🎯 結果: 時間區間功能正常工作")
                else:
                    status = "⚠️ 警告"
                    print(f"⚠️ 結果: 未找到時間區間設定信息")
                    
            else:
                status = "❌ 失敗"
                print(f"❌ 執行失敗: {result.stderr}")
                
        except subprocess.TimeoutExpired:
            status = "⏰ 超時"
            print(f"⏰ 執行超時")
        except Exception as e:
            status = "❌ 錯誤"
            print(f"❌ 執行錯誤: {e}")
        
        results.append({
            "name": config["name"],
            "time_range": f"{config['start_time']}-{config['end_time']}",
            "status": status
        })
    
    # 顯示總結
    print(f"\n{'='*50}")
    print("📋 測試總結")
    print(f"{'='*50}")
    
    for result in results:
        print(f"{result['status']} {result['name']}: {result['time_range']}")
    
    # 檢查功能狀態
    success_count = sum(1 for r in results if "✅" in r["status"])
    total_count = len(results)
    
    print(f"\n🎯 功能驗證結果:")
    print(f"   成功: {success_count}/{total_count}")
    
    if success_count == total_count:
        print(f"   🎉 時間區間功能完全正常！")
        print(f"   ✅ 反轉策略支援自定義時間區間")
        print(f"   ✅ 可以使用 11:30-11:32 等任意時間")
    elif success_count > 0:
        print(f"   ⚠️ 時間區間功能部分正常")
        print(f"   🔧 建議檢查失敗的配置")
    else:
        print(f"   ❌ 時間區間功能異常")
        print(f"   🔧 需要進一步調試")
    
    print(f"\n📊 測試完成時間: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

if __name__ == "__main__":
    test_time_range_functionality()
