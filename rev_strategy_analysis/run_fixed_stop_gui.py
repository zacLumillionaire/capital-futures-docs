#!/usr/bin/env python3
"""
通過GUI模式運行固定停損測試
"""

import subprocess
import json
import sys
import os

def run_fixed_stop_gui_test():
    """通過GUI模式運行固定停損測試"""
    
    # 🎯 固定停損模式配置
    gui_config = {
        "fixed_stop_mode": True,  # 🔑 關鍵設置：啟用固定停損模式
        "trade_lots": 3,
        "start_date": "2024-11-04",
        "end_date": "2024-11-10", 
        "range_start_time": "08:55",
        "range_end_time": "08:57",
        "lot_settings": {
            "lot1": {
                "trigger": 14,
                "trailing": 0,    # 0% 回檔
                "protection": 0   # 停用保護性停損
            },
            "lot2": {
                "trigger": 40,
                "trailing": 0,    # 0% 回檔  
                "protection": 0   # 停用保護性停損
            },
            "lot3": {
                "trigger": 41,
                "trailing": 0,    # 0% 回檔
                "protection": 0   # 停用保護性停損
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
                "fixed_stop_loss_points": 20,
                "use_range_midpoint": False
            }
        }
    }
    
    # 轉換為JSON字串
    config_json = json.dumps(gui_config)
    
    print("🎯 固定停損模式GUI測試")
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
    
    # 構建命令
    cmd = [
        "python", 
        "rev_multi_Profit-Funded Risk_多口.py",
        "--gui-mode",
        "--config", 
        config_json
    ]
    
    print("執行命令：")
    print(" ".join(cmd))
    print()
    
    # 執行命令
    try:
        result = subprocess.run(cmd, cwd=".", capture_output=False, text=True)
        return result.returncode
    except Exception as e:
        print(f"❌ 執行失敗：{e}")
        return 1

if __name__ == "__main__":
    # 切換到正確的目錄
    script_dir = os.path.dirname(os.path.abspath(__file__))
    os.chdir(script_dir)
    
    exit_code = run_fixed_stop_gui_test()
    sys.exit(exit_code)
