#!/usr/bin/env python3
"""
風險管理濾網測試腳本
測試新實現的風險管理功能是否正常運作
"""

import sys
import json
from decimal import Decimal
from datetime import datetime

# 添加當前目錄到路徑
sys.path.append('.')

def test_risk_management():
    """測試風險管理濾網功能"""
    print("🧪 開始測試風險管理濾網功能...")
    
    # 測試配置：啟用風險管理濾網，設定較小的虧損限制以便觸發
    test_config = {
        "trade_lots": 3,
        "start_date": "2024-11-01",
        "end_date": "2024-11-05",  # 只測試幾天
        "lot_settings": {
            "lot1": {"trigger": 15, "trailing": 20},
            "lot2": {"trigger": 40, "trailing": 20, "protection": 2},
            "lot3": {"trigger": 65, "trailing": 20, "protection": 2}
        },
        "filters": {
            "range_filter": {
                "enabled": False,
                "max_range_points": 50
            },
            "risk_filter": {
                "enabled": True,
                "daily_loss_limit": 50,  # 設定較小的虧損限制，容易觸發
                "profit_target": 100     # 設定較小的獲利目標，容易觸發
            },
            "stop_loss_filter": {
                "enabled": False,
                "stop_loss_type": "range_boundary",
                "fixed_stop_loss_points": 30,
                "use_range_midpoint": False
            }
        }
    }
    
    print(f"📋 測試配置:")
    print(f"  - 日期範圍: {test_config['start_date']} 至 {test_config['end_date']}")
    print(f"  - 風險管理: 啟用")
    print(f"  - 虧損限制: {test_config['filters']['risk_filter']['daily_loss_limit']} 點")
    print(f"  - 獲利目標: {test_config['filters']['risk_filter']['profit_target']} 點")
    
    # 執行測試
    import subprocess
    cmd = [
        sys.executable,
        "multi_Profit-Funded Risk_多口.py",
        "--start-date", test_config["start_date"],
        "--end-date", test_config["end_date"],
        "--gui-mode",
        "--config", json.dumps(test_config, ensure_ascii=False)
    ]
    
    print(f"\n🚀 執行測試命令...")
    print(f"命令: {' '.join(cmd)}")
    
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=60)
        
        print(f"\n📊 測試結果:")
        print(f"返回碼: {result.returncode}")
        
        if result.stdout:
            print(f"\n📝 標準輸出:")
            # 查找風險管理相關的日誌
            lines = result.stdout.split('\n')
            risk_lines = [line for line in lines if '風險管理' in line or '🚨' in line]
            
            if risk_lines:
                print("🎯 發現風險管理觸發:")
                for line in risk_lines:
                    print(f"  {line}")
            else:
                print("ℹ️ 未發現風險管理觸發（可能虧損/獲利未達到設定限制）")
            
            # 顯示最後幾行總結
            summary_lines = lines[-10:]
            print(f"\n📋 執行總結:")
            for line in summary_lines:
                if line.strip():
                    print(f"  {line}")
        
        if result.stderr:
            print(f"\n❌ 錯誤輸出:")
            print(result.stderr)
            
    except subprocess.TimeoutExpired:
        print("⏰ 測試超時（60秒）")
    except Exception as e:
        print(f"❌ 測試執行失敗: {e}")

def test_without_risk_management():
    """測試未啟用風險管理時的行為（確保向後兼容）"""
    print("\n🧪 測試未啟用風險管理的情況...")
    
    test_config = {
        "trade_lots": 3,
        "start_date": "2024-11-01",
        "end_date": "2024-11-02",  # 只測試一天
        "lot_settings": {
            "lot1": {"trigger": 15, "trailing": 20},
            "lot2": {"trigger": 40, "trailing": 20, "protection": 2},
            "lot3": {"trigger": 65, "trailing": 20, "protection": 2}
        },
        "filters": {
            "range_filter": {"enabled": False, "max_range_points": 50},
            "risk_filter": {"enabled": False, "daily_loss_limit": 150, "profit_target": 200},
            "stop_loss_filter": {"enabled": False, "stop_loss_type": "range_boundary", "fixed_stop_loss_points": 30, "use_range_midpoint": False}
        }
    }
    
    print(f"📋 測試配置: 風險管理濾網停用")
    
    import subprocess
    cmd = [
        sys.executable,
        "multi_Profit-Funded Risk_多口.py",
        "--start-date", test_config["start_date"],
        "--end-date", test_config["end_date"],
        "--gui-mode",
        "--config", json.dumps(test_config, ensure_ascii=False)
    ]
    
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
        
        print(f"📊 測試結果: 返回碼 {result.returncode}")
        
        if result.stdout:
            lines = result.stdout.split('\n')
            # 確認沒有風險管理相關日誌
            risk_lines = [line for line in lines if '風險管理' in line or '🚨' in line]
            
            if not risk_lines:
                print("✅ 確認：未啟用風險管理時沒有相關日誌（正常）")
            else:
                print("⚠️ 警告：未啟用風險管理但發現相關日誌")
                for line in risk_lines:
                    print(f"  {line}")
        
    except Exception as e:
        print(f"❌ 測試失敗: {e}")

if __name__ == "__main__":
    # 初始化資料庫連線池
    try:
        import app_setup
        app_setup.init_all_db_pools()
        print("✅ 資料庫連線池初始化成功")
    except Exception as e:
        print(f"❌ 資料庫初始化失敗: {e}")
        sys.exit(1)
    
    # 執行測試
    test_without_risk_management()
    test_risk_management()
    
    print("\n🎉 測試完成！")
