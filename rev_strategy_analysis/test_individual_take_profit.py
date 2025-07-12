#!/usr/bin/env python3
"""
測試每口獨立停利功能
驗證GUI新增的每口停利設定是否正常工作
"""

import json
import subprocess
import sys
import os
from datetime import datetime

def test_individual_take_profit():
    """測試每口獨立停利功能"""
    
    print("🧪 測試每口獨立停利功能")
    print("=" * 60)
    
    # 測試配置：啟用每口獨立停利
    test_config = {
        "trade_lots": 3,
        "start_date": "2024-11-04",
        "end_date": "2024-11-05",  # 只測試2天
        "range_start_time": "10:30",
        "range_end_time": "10:31",
        "fixed_stop_mode": True,  # 啟用固定停損模式
        "individual_take_profit_enabled": True,  # 🎯 啟用每口獨立停利
        "lot_settings": {
            "lot1": {
                "trigger": 15,
                "trailing": 0,
                "take_profit": 50  # 🎯 第1口停利50點
            },
            "lot2": {
                "trigger": 25,
                "trailing": 0,
                "protection": 0,
                "take_profit": 70  # 🎯 第2口停利70點
            },
            "lot3": {
                "trigger": 35,
                "trailing": 0,
                "protection": 0,
                "take_profit": 90  # 🎯 第3口停利90點
            }
        },
        "filters": {
            "range_filter": {
                "enabled": False,
                "max_range_points": 50
            },
            "risk_filter": {
                "enabled": False,
                "daily_loss_limit": 150,
                "profit_target": 200
            },
            "stop_loss_filter": {
                "enabled": False,
                "stop_loss_type": "range_boundary",
                "fixed_stop_loss_points": 15.0
            }
        }
    }
    
    print("📋 測試配置:")
    print(f"  - 交易口數: {test_config['trade_lots']}")
    print(f"  - 測試期間: {test_config['start_date']} ~ {test_config['end_date']}")
    print(f"  - 時間區間: {test_config['range_start_time']}-{test_config['range_end_time']}")
    print(f"  - 固定停損模式: {test_config['fixed_stop_mode']}")
    print(f"  - 每口獨立停利: {test_config['individual_take_profit_enabled']}")
    print("  - 每口停利設定:")
    for lot_name, lot_config in test_config['lot_settings'].items():
        if 'take_profit' in lot_config:
            print(f"    * {lot_name}: 停損{lot_config['trigger']}點, 停利{lot_config['take_profit']}點")
    print()
    
    # 構建命令
    cmd = [
        sys.executable,
        "rev_multi_Profit-Funded Risk_多口.py",
        "--start-date", test_config["start_date"],
        "--end-date", test_config["end_date"],
        "--gui-mode",
        "--config", json.dumps(test_config, ensure_ascii=False)
    ]
    
    print("🚀 執行測試...")
    print(f"命令: {' '.join(cmd[:6])} --config [CONFIG_JSON]")
    print()
    
    try:
        # 執行回測
        result = subprocess.run(
            cmd,
            cwd=os.path.dirname(os.path.abspath(__file__)),
            capture_output=True,
            text=True,
            encoding='utf-8',
            errors='replace',
            timeout=60  # 60秒超時
        )
        
        print("📊 執行結果:")
        print("=" * 40)
        
        if result.returncode == 0:
            print("✅ 測試執行成功!")
            print()
            print("📈 回測輸出:")
            print("-" * 60)
            print(result.stdout)
            print("-" * 60)

            if result.stderr:
                print("⚠️ 錯誤輸出:")
                print(result.stderr)
                print("-" * 60)

            # 檢查是否包含每口停利相關的LOG
            output_text = result.stdout + (result.stderr or "")
            if "固定停利" in output_text:
                print("✅ 檢測到固定停利功能正常運作")
            elif "第1口" in output_text and "第2口" in output_text:
                print("✅ 檢測到多口交易LOG，功能可能正常運作")
            else:
                print("⚠️  未檢測到預期的交易LOG，可能需要進一步檢查")
                print("🔍 輸出內容關鍵字檢查:")
                keywords = ["固定停利", "第1口", "第2口", "第3口", "停利", "停損", "LONG", "SHORT"]
                for keyword in keywords:
                    if keyword in output_text:
                        print(f"  ✓ 找到: {keyword}")
                    else:
                        print(f"  ✗ 未找到: {keyword}")
                
        else:
            print("❌ 測試執行失敗!")
            print(f"返回碼: {result.returncode}")
            print("錯誤輸出:")
            print(result.stderr)
            
    except subprocess.TimeoutExpired:
        print("⏰ 測試執行超時 (60秒)")
    except Exception as e:
        print(f"❌ 測試執行異常: {e}")
    
    print()
    print("🏁 測試完成")

if __name__ == "__main__":
    test_individual_take_profit()
