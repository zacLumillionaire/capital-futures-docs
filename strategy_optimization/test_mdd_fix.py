#!/usr/bin/env python3
"""
測試MDD修復是否正確
"""

import subprocess
import sys
import os

def test_mdd_calculation():
    """測試MDD計算是否正確"""
    
    # 準備測試配置 - 使用簡化的時間區間配置格式
    test_config = {
        "start_date": "2024-11-04",
        "end_date": "2024-12-31",
        "range_start_time": "10:30",
        "range_end_time": "10:32",
        "trade_lots": 3,
        "lot_settings": {
            "lot1": {"trigger": 15, "trailing": 10, "protection": 1.0},
            "lot2": {"trigger": 40, "trailing": 10, "protection": 1.0},
            "lot3": {"trigger": 41, "trailing": 20, "protection": 1.0}
        },
        "filters": {
            "range_filter": {"enabled": False},
            "risk_filter": {"enabled": False},
            "stop_loss_filter": {"enabled": True, "stop_loss_type": "range_boundary"}
        },
        "stop_loss_mode": "range_boundary",
        "take_profit_mode": "trailing_stop"
    }
    
    import json
    config_json = json.dumps(test_config)
    
    # 運行策略
    cmd = [
        sys.executable,
        "multi_Profit-Funded Risk_多口.py",
        "--start-date", "2024-11-04",
        "--end-date", "2024-12-31",
        "--gui-mode",
        "--config", config_json
    ]
    
    print("🧪 測試MDD計算修復...")
    print(f"📋 命令: {' '.join(cmd)}")
    
    try:
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=30,
            cwd=os.getcwd()
        )
        
        print(f"📤 返回碼: {result.returncode}")
        print(f"📊 標準輸出長度: {len(result.stdout)}")
        print(f"📊 錯誤輸出長度: {len(result.stderr)}")
        
        # 檢查輸出中是否包含MDD
        output_to_check = result.stderr if result.stderr else result.stdout
        
        print("\n🔍 檢查輸出內容:")
        if "最大回撤:" in output_to_check:
            print("✅ 找到最大回撤輸出")
            
            # 提取MDD值
            for line in output_to_check.split('\n'):
                if "最大回撤:" in line:
                    print(f"📈 {line.strip()}")
        else:
            print("❌ 未找到最大回撤輸出")
        
        if "總損益" in output_to_check:
            print("✅ 找到總損益輸出")
            for line in output_to_check.split('\n'):
                if "總損益" in line:
                    print(f"💰 {line.strip()}")
        else:
            print("❌ 未找到總損益輸出")
            
        # 顯示完整輸出用於調試
        print("\n📋 完整stderr輸出:")
        print("=" * 50)
        print(result.stderr)
        print("=" * 50)
        
        if result.stdout:
            print("\n📋 完整stdout輸出:")
            print("=" * 50)
            print(result.stdout)
            print("=" * 50)
        
        return result.returncode == 0
        
    except subprocess.TimeoutExpired:
        print("❌ 測試超時")
        return False
    except Exception as e:
        print(f"❌ 測試失敗: {e}")
        return False

if __name__ == "__main__":
    success = test_mdd_calculation()
    if success:
        print("\n🎉 MDD修復測試成功！")
    else:
        print("\n💥 MDD修復測試失敗！")
