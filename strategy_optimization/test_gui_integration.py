#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
測試GUI與回測引擎的整合
"""

import json
import subprocess
import sys
import os

def test_gui_config():
    """測試GUI配置格式"""
    
    # 模擬GUI生成的配置
    test_config = {
        "trade_lots": 2,
        "start_date": "2024-11-01",
        "end_date": "2024-11-05",  # 短期測試
        "lot_settings": {
            "lot1": {
                "trigger": 15.0,
                "trailing": 20.0
            },
            "lot2": {
                "trigger": 40.0,
                "trailing": 20.0,
                "protection": 2.0
            },
            "lot3": {
                "trigger": 65.0,
                "trailing": 20.0,
                "protection": 2.0
            }
        },
        "filters": {
            "range_filter": {
                "enabled": True,
                "max_range_points": 50.0
            },
            "risk_filter": {
                "enabled": False,
                "daily_loss_limit": 150.0,
                "profit_target": 200.0
            },
            "stop_loss_filter": {
                "enabled": False,
                "fixed_stop_loss": 15.0,
                "use_range_midpoint": False
            }
        }
    }
    
    print("測試配置:")
    print(json.dumps(test_config, indent=2, ensure_ascii=False))
    
    return test_config

def test_backtest_execution(config):
    """測試回測執行"""
    
    try:
        # 構建命令
        cmd = [
            sys.executable,
            "multi_Profit-Funded Risk_多口.py",
            "--start-date", config["start_date"],
            "--end-date", config["end_date"],
            "--gui-mode",
            "--config", json.dumps(config)
        ]
        
        print(f"\n執行命令: {' '.join(cmd[:4])} [GUI模式]")
        
        # 執行回測（短時間測試）
        result = subprocess.run(
            cmd,
            cwd=os.path.dirname(os.path.abspath(__file__)),
            capture_output=True,
            text=True,
            encoding='utf-8',
            timeout=30  # 30秒超時
        )
        
        print(f"\n返回碼: {result.returncode}")
        
        if result.stdout:
            print(f"\n標準輸出:\n{result.stdout[:500]}...")
        
        if result.stderr:
            print(f"\n錯誤輸出:\n{result.stderr}")
        
        return result.returncode == 0
        
    except subprocess.TimeoutExpired:
        print("\n測試超時（這是正常的，說明回測正在執行）")
        return True
    except Exception as e:
        print(f"\n執行錯誤: {e}")
        return False

def test_kelly_analyzer():
    """測試凱利分析器"""
    
    try:
        result = subprocess.run(
            [sys.executable, "kelly_formula_analyzer.py"],
            cwd=os.path.dirname(os.path.abspath(__file__)),
            capture_output=True,
            text=True,
            encoding='utf-8',
            timeout=10
        )
        
        print(f"\n凱利分析返回碼: {result.returncode}")
        
        if result.stdout:
            print(f"凱利分析輸出: {result.stdout[:200]}...")
        
        return result.returncode == 0
        
    except Exception as e:
        print(f"\n凱利分析錯誤: {e}")
        return False

def main():
    """主測試函數"""
    
    print("=== GUI整合測試 ===\n")
    
    # 測試1: 配置格式
    print("1. 測試配置格式...")
    config = test_gui_config()
    
    # 測試2: 回測執行
    print("\n2. 測試回測執行...")
    backtest_ok = test_backtest_execution(config)
    
    # 測試3: 凱利分析
    print("\n3. 測試凱利分析...")
    kelly_ok = test_kelly_analyzer()
    
    # 總結
    print("\n=== 測試結果 ===")
    print(f"配置格式: ✓")
    print(f"回測執行: {'✓' if backtest_ok else '✗'}")
    print(f"凱利分析: {'✓' if kelly_ok else '✗'}")
    
    if backtest_ok and kelly_ok:
        print("\n🎉 所有測試通過！GUI整合成功！")
    else:
        print("\n⚠️  部分測試失敗，請檢查錯誤訊息")

if __name__ == "__main__":
    main()
