#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
快速反轉邏輯測試
使用正確的GUI配置格式測試反轉策略
"""

import subprocess
import sys
import json
from datetime import datetime

def test_reversal_with_correct_config():
    """使用正確配置測試反轉邏輯"""
    print("🔄 快速反轉邏輯測試")
    print("=" * 50)
    
    # 完整的GUI配置格式
    gui_config = {
        "trade_lots": 3,
        "start_date": "2024-11-04",
        "end_date": "2024-11-06",
        "range_start_time": "08:46",
        "range_end_time": "08:47",
        "lot_settings": {
            "lot1": {
                "trigger": 15,
                "trailing": 20,
                "protection": 0.5
            },
            "lot2": {
                "trigger": 25,
                "trailing": 30,
                "protection": 0.6
            },
            "lot3": {
                "trigger": 35,
                "trailing": 40,
                "protection": 0.7
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
    
    print("📋 測試配置:")
    print(f"   日期範圍: {gui_config['start_date']} 至 {gui_config['end_date']}")
    print(f"   時間區間: {gui_config['range_start_time']}-{gui_config['range_end_time']}")
    print(f"   交易口數: {gui_config['trade_lots']}")
    print(f"   所有濾網: 已停用")
    print("-" * 50)
    
    try:
        # 執行反轉策略測試
        config_json = json.dumps(gui_config, ensure_ascii=False)
        cmd = [
            sys.executable,
            "rev_multi_Profit-Funded Risk_多口.py",
            "--gui-mode",
            "--config", config_json
        ]
        
        print("🚀 執行反轉策略測試...")
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=120)
        
        if result.returncode == 0:
            print("✅ 執行成功！")
            print("\n📊 詳細LOG分析:")
            print("-" * 50)
            
            # 分析輸出
            output_lines = result.stdout.split('\n')
            
            entry_count = 0
            exit_count = 0
            total_pnl = 0
            
            for line in output_lines:
                line = line.strip()
                
                # 檢查進場信息
                if "反轉進場" in line:
                    entry_count += 1
                    print(f"🎯 進場 {entry_count}: {line}")
                    
                # 檢查出場信息
                elif any(keyword in line for keyword in ["初始停損", "移動停利", "固定停利", "保護性停損", "收盤平倉"]):
                    exit_count += 1
                    print(f"📤 出場 {exit_count}: {line}")
                    
                    # 提取損益
                    if "損益:" in line:
                        try:
                            pnl_part = line.split("損益:")[1].strip()
                            # 處理帶符號的數字
                            pnl_str = pnl_part.replace("點", "").strip()
                            if pnl_str.startswith('+'):
                                pnl_value = int(pnl_str[1:])
                            elif pnl_str.startswith('-'):
                                pnl_value = -int(pnl_str[1:])
                            else:
                                pnl_value = int(pnl_str)
                            total_pnl += pnl_value
                        except Exception as e:
                            print(f"   ⚠️ 損益解析錯誤: {e}")
                
                # 檢查開盤區間
                elif "開盤區間:" in line:
                    print(f"📈 {line}")
                    
                # 檢查總結
                elif "總損益" in line or "TOTAL P&L" in line:
                    print(f"💰 {line}")
            
            print("\n" + "=" * 50)
            print("🔍 測試結果總結:")
            print(f"   進場次數: {entry_count}")
            print(f"   出場次數: {exit_count}")
            print(f"   累計損益: {total_pnl:+d} 點")
            
            # 邏輯驗證
            if entry_count > 0:
                print(f"   ✅ 發現交易，反轉邏輯正在運作")
                if total_pnl > 0:
                    print(f"   🎉 累計獲利，反轉策略可能有效")
                elif total_pnl < 0:
                    print(f"   ⚠️ 累計虧損，需要檢查邏輯")
                else:
                    print(f"   ➖ 損益平衡")
            else:
                print(f"   ❌ 未發現交易，可能有問題")
                
        else:
            print("❌ 執行失敗:")
            print(result.stderr)
            if result.stdout:
                print("標準輸出:")
                print(result.stdout)
            
    except subprocess.TimeoutExpired:
        print("⏰ 執行超時")
    except Exception as e:
        print(f"❌ 執行錯誤: {e}")
    
    print(f"\n📅 測試完成: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

if __name__ == "__main__":
    test_reversal_with_correct_config()
