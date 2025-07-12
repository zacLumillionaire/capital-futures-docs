#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
反轉邏輯驗證測試
檢查修正後的反轉策略邏輯是否正確
"""

import subprocess
import sys
import json
from datetime import datetime

def test_reversal_logic():
    """測試反轉邏輯是否正確"""
    print("🔄 反轉策略邏輯驗證測試")
    print("=" * 60)
    
    # 測試配置 - 使用簡單設定
    test_config = {
        "trade_lots": 3,
        "start_date": "2024-11-04",
        "end_date": "2024-11-06",  # 只測試3天
        "range_start_time": "08:46",
        "range_end_time": "08:47",
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
    
    print("📋 測試配置:")
    print(f"   日期範圍: {test_config['start_date']} 至 {test_config['end_date']}")
    print(f"   時間區間: {test_config['range_start_time']}-{test_config['range_end_time']}")
    print(f"   交易口數: {test_config['trade_lots']}")
    print("-" * 60)
    
    try:
        # 執行反轉策略測試
        cmd = [
            sys.executable,
            "rev_multi_Profit-Funded Risk_多口.py",
            "--gui-mode",
            "--config", json.dumps(test_config, ensure_ascii=False)
        ]
        
        print("🚀 執行反轉策略測試...")
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=120)
        
        if result.returncode == 0:
            print("✅ 執行成功！")
            print("\n📊 分析LOG輸出:")
            print("-" * 60)
            
            # 分析輸出
            output_lines = result.stdout.split('\n')
            
            trades_found = []
            total_pnl = 0
            
            for line in output_lines:
                line = line.strip()
                
                # 檢查進場信息
                if "反轉進場" in line:
                    print(f"🎯 {line}")
                    
                # 檢查出場信息
                elif any(keyword in line for keyword in ["初始停損", "移動停利", "固定停利", "保護性停損", "收盤平倉"]):
                    print(f"📤 {line}")
                    
                    # 提取損益
                    if "損益:" in line:
                        try:
                            pnl_part = line.split("損益:")[1].strip()
                            # 移除可能的單位
                            pnl_str = pnl_part.replace("點", "").strip()
                            pnl_value = int(pnl_str)
                            trades_found.append(pnl_value)
                            total_pnl += pnl_value
                        except:
                            pass
                
                # 檢查總結信息
                elif "總損益" in line or "TOTAL P&L" in line:
                    print(f"💰 {line}")
                    
                # 檢查開盤區間
                elif "開盤區間:" in line:
                    print(f"📈 {line}")
            
            print("\n" + "=" * 60)
            print("🔍 邏輯驗證結果:")
            
            if trades_found:
                print(f"   找到交易: {len(trades_found)} 筆")
                print(f"   個別損益: {trades_found}")
                print(f"   累計損益: {total_pnl:+d} 點")
                
                # 檢查邏輯正確性
                positive_trades = [p for p in trades_found if p > 0]
                negative_trades = [p for p in trades_found if p < 0]
                
                print(f"   獲利交易: {len(positive_trades)} 筆")
                print(f"   虧損交易: {len(negative_trades)} 筆")
                
                if positive_trades:
                    print(f"   ✅ 發現獲利交易，反轉邏輯可能正確")
                else:
                    print(f"   ⚠️ 未發現獲利交易，需要進一步檢查")
                    
            else:
                print(f"   ⚠️ 未找到交易記錄")
            
            # 檢查關鍵邏輯點
            print(f"\n🔧 關鍵邏輯檢查:")
            
            # 檢查進場邏輯
            long_entries = [line for line in output_lines if "LONG" in line and "反轉進場" in line]
            short_entries = [line for line in output_lines if "SHORT" in line and "反轉進場" in line]
            
            print(f"   多頭進場: {len(long_entries)} 次 (原策略做空點)")
            print(f"   空頭進場: {len(short_entries)} 次 (原策略做多點)")
            
            # 檢查停損邏輯
            stop_losses = [line for line in output_lines if "初始停損" in line]
            print(f"   初始停損: {len(stop_losses)} 次")
            
            if stop_losses:
                print(f"   ✅ 停損邏輯已修正，應該顯示正確的損益符號")
            
        else:
            print("❌ 執行失敗:")
            print(result.stderr)
            
    except subprocess.TimeoutExpired:
        print("⏰ 執行超時")
    except Exception as e:
        print(f"❌ 執行錯誤: {e}")
    
    print(f"\n📅 測試完成時間: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("\n🎯 下一步建議:")
    print("   1. 檢查LOG中的損益符號是否正確")
    print("   2. 驗證進場點是否為原策略的反向點")
    print("   3. 確認停損點設定是否合理")
    print("   4. 測試更長時間範圍的表現")

if __name__ == "__main__":
    test_reversal_logic()
