#!/usr/bin/env python3
"""
測試 LONG/SHORT PNL 修復
"""

import subprocess
import sys
import json
from pathlib import Path

def test_rev_multi_json_output():
    """測試 rev_multi_Profit-Funded Risk_多口.py 的 JSON 輸出"""
    
    print("=== 測試 rev_multi_Profit-Funded Risk_多口.py JSON 輸出 ===")
    
    # 模擬 GUI 配置
    gui_config = {
        "start_date": "2024-11-04",
        "end_date": "2024-11-08",
        "range_start_time": "12:00",
        "range_end_time": "12:02",
        "trade_lots": 3,
        "lot_settings": [
            {
                "trigger_points": 15,
                "trailing_pullback": 0.1,
                "protection_multiplier": 2.0
            },
            {
                "trigger_points": 15,
                "trailing_pullback": 0.1,
                "protection_multiplier": 2.0
            },
            {
                "trigger_points": 15,
                "trailing_pullback": 0.1,
                "protection_multiplier": 2.0
            }
        ],
        "filters": {
            "range_filter": {"enabled": False, "max_range_points": 160},
            "risk_config": {"enabled": False, "daily_loss_limit": 100, "profit_target": 200},
            "stop_loss_config": {"enabled": False, "stop_loss_type": "range_boundary"}
        },
        "take_profit_mode": "range_boundary",
        "simplified_mode": False,
        "fixed_stop_mode": False,
        "individual_take_profit_enabled": False
    }
    
    try:
        # 調用 rev_multi_Profit-Funded Risk_多口.py
        cmd = [
            sys.executable, '../rev_multi_Profit-Funded Risk_多口.py',
            '--gui-mode',
            '--config', json.dumps(gui_config, ensure_ascii=False)
        ]
        
        print(f"執行命令: {' '.join(cmd)}")
        
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=60,
            cwd=Path(__file__).parent
        )
        
        print(f"返回碼: {result.returncode}")
        print(f"stdout 長度: {len(result.stdout)}")
        print(f"stderr 長度: {len(result.stderr)}")
        
        if result.stderr:
            print("\n=== stderr 內容 ===")
            stderr_lines = result.stderr.split('\n')
            for i, line in enumerate(stderr_lines[-20:]):  # 顯示最後20行
                print(f"{i}: {line}")
            
            # 尋找 JSON 行
            json_found = False
            for line in stderr_lines:
                if line.strip().startswith('{') and 'long_pnl' in line:
                    print(f"\n🔍 找到 JSON 行: {line.strip()}")
                    try:
                        result_data = json.loads(line.strip())
                        print(f"✅ JSON 解析成功:")
                        print(f"  total_pnl: {result_data.get('total_pnl')}")
                        print(f"  long_pnl: {result_data.get('long_pnl')}")
                        print(f"  short_pnl: {result_data.get('short_pnl')}")
                        json_found = True
                        
                        # 驗證數據
                        if (result_data.get('long_pnl') is not None and 
                            result_data.get('short_pnl') is not None):
                            print("✅ LONG/SHORT PNL 數據正確")
                            return True
                        else:
                            print("❌ LONG/SHORT PNL 數據缺失")
                            return False
                            
                    except Exception as e:
                        print(f"❌ JSON 解析失敗: {e}")
                        return False
            
            if not json_found:
                print("❌ 未找到 JSON 輸出")
                return False
        else:
            print("❌ 沒有 stderr 輸出")
            return False
            
    except subprocess.TimeoutExpired:
        print("❌ 執行超時")
        return False
    except Exception as e:
        print(f"❌ 執行失敗: {e}")
        return False

def test_enhanced_mdd_optimizer_parsing():
    """測試 enhanced_mdd_optimizer.py 的解析邏輯"""
    
    print("\n=== 測試 enhanced_mdd_optimizer.py 解析邏輯 ===")
    
    # 模擬包含 JSON 的 stderr 輸出
    mock_stderr = """
2025-07-11 21:08:31,402 - INFO - 🔍 找到 5 個交易日進行回測。
2025-07-11 21:08:31,402 - INFO - 📅 2024-11-04: 無交易
2025-07-11 21:08:31,402 - INFO - 📅 2024-11-05: 無交易
總損益(3口): 300.00
{"total_pnl": 300.0, "long_pnl": 150.0, "short_pnl": 150.0, "total_trades": 6}
"""
    
    # 導入解析函數
    sys.path.insert(0, str(Path(__file__).parent))
    try:
        from enhanced_mdd_optimizer import EnhancedMDDOptimizer
        
        optimizer = EnhancedMDDOptimizer('test')
        mdd, total_pnl, long_pnl, short_pnl = optimizer._parse_strategy_output(mock_stderr)
        
        print(f"解析結果:")
        print(f"  MDD: {mdd}")
        print(f"  total_pnl: {total_pnl}")
        print(f"  long_pnl: {long_pnl}")
        print(f"  short_pnl: {short_pnl}")
        
        if (total_pnl == 300.0 and long_pnl == 150.0 and short_pnl == 150.0):
            print("✅ enhanced_mdd_optimizer 解析正確")
            return True
        else:
            print("❌ enhanced_mdd_optimizer 解析錯誤")
            return False
            
    except Exception as e:
        print(f"❌ enhanced_mdd_optimizer 測試失敗: {e}")
        return False

if __name__ == "__main__":
    print("開始測試 LONG/SHORT PNL 修復...")
    
    # 注意：第一個測試需要數據庫，可能會失敗，但我們主要關注 JSON 輸出格式
    success1 = test_rev_multi_json_output()
    success2 = test_enhanced_mdd_optimizer_parsing()
    
    if success1 and success2:
        print("\n🎉 所有測試通過！LONG/SHORT PNL 修復成功。")
    elif success2:
        print("\n⚠️  解析邏輯正確，但可能需要檢查數據庫連接。")
    else:
        print("\n❌ 測試失敗，需要進一步檢查。")
