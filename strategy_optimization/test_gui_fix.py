#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
測試GUI修復的腳本
"""

import subprocess
import sys
import json
import os

def test_backtest_execution():
    """測試回測執行和輸出捕獲"""
    print("🧪 測試回測執行和輸出捕獲...")
    
    # 測試配置
    gui_config = {
        "trade_lots": 3,
        "start_date": "2024-11-01",
        "end_date": "2024-11-13",
        "lot_settings": {
            "lot1": {"trigger": 15, "trailing": 20},
            "lot2": {"trigger": 40, "trailing": 20, "protection": 2.0},
            "lot3": {"trigger": 65, "trailing": 20, "protection": 2.0}
        },
        "filters": {
            "range_filter": {"enabled": False, "max_range_points": 50},
            "risk_filter": {"enabled": False, "daily_loss_limit": 150, "profit_target": 200},
            "stop_loss_filter": {"enabled": False, "fixed_stop_loss": 15.0, "use_range_midpoint": False}
        }
    }
    
    # 構建命令
    cmd = [
        sys.executable,
        "multi_Profit-Funded Risk_多口.py",
        "--start-date", gui_config["start_date"],
        "--end-date", gui_config["end_date"],
        "--gui-mode",
        "--config", json.dumps(gui_config, ensure_ascii=False)
    ]
    
    print(f"🚀 執行命令: {' '.join(cmd)}")
    
    try:
        # 執行回測
        result = subprocess.run(
            cmd,
            cwd=os.path.dirname(os.path.abspath(__file__)),
            capture_output=True,
            text=True,
            encoding='utf-8',
            errors='replace'
        )
        
        print(f"🔧 返回碼: {result.returncode}")
        print(f"📏 stdout 長度: {len(result.stdout) if result.stdout else 0}")
        print(f"📏 stderr 長度: {len(result.stderr) if result.stderr else 0}")
        
        if result.stdout:
            print("\n📈 stdout 內容 (前500字符):")
            print(result.stdout[:500])
            print("..." if len(result.stdout) > 500 else "")
        
        if result.stderr:
            print("\n⚠️ stderr 內容:")
            print(result.stderr)
        
        # 測試統計數據提取
        print("\n🔍 測試統計數據提取...")
        test_stats_extraction(result)
        
        return result
        
    except Exception as e:
        print(f"❌ 執行失敗: {e}")
        return None

def test_stats_extraction(result):
    """測試統計數據提取邏輯"""
    full_output = result.stdout + "\n" + (result.stderr or "")
    output_lines = full_output.split('\n')
    stats = {}
    
    print("🔍 搜尋統計數據...")
    found_lines = []
    
    for i, line in enumerate(output_lines):
        if any(keyword in line for keyword in ['總交易天數', '總交易次數', '獲利次數', '虧損次數', '勝率', '總損益']):
            found_lines.append(f"第{i}行: {line}")
    
    if found_lines:
        print("✅ 找到包含統計關鍵字的行:")
        for line in found_lines:
            print(f"  {line}")
    else:
        print("❌ 未找到包含統計關鍵字的行")
    
    # 提取統計數據 - 使用修復後的邏輯
    for line in output_lines:
        original_line = line.strip()

        # 處理不同的日誌格式，更精確地提取內容
        clean_line = original_line
        if '] INFO [' in line:
            # 分割日誌格式: [時間] INFO [模組:行號] 內容
            parts = line.split('] ')
            if len(parts) >= 3:  # 確保有足夠的部分
                clean_line = parts[2].strip()  # 取第三部分作為實際內容

        # 測試各種匹配模式
        if '總交易天數:' in clean_line:
            try:
                value = clean_line.split('總交易天數:')[1].strip()
                stats['trading_days'] = value
                print(f"✅ 提取總交易天數: {value}")
            except Exception as e:
                print(f"❌ 提取總交易天數失敗: {e}")
        elif '總交易次數:' in clean_line:
            try:
                value = clean_line.split('總交易次數:')[1].strip()
                stats['total_trades'] = value
                print(f"✅ 提取總交易次數: {value}")
            except Exception as e:
                print(f"❌ 提取總交易次數失敗: {e}")
        elif '獲利次數:' in clean_line:
            try:
                value = clean_line.split('獲利次數:')[1].strip()
                stats['winning_trades'] = value
                print(f"✅ 提取獲利次數: {value}")
            except Exception as e:
                print(f"❌ 提取獲利次數失敗: {e}")
        elif '虧損次數:' in clean_line:
            try:
                value = clean_line.split('虧損次數:')[1].strip()
                stats['losing_trades'] = value
                print(f"✅ 提取虧損次數: {value}")
            except Exception as e:
                print(f"❌ 提取虧損次數失敗: {e}")
        elif '勝率:' in clean_line:
            try:
                value = clean_line.split('勝率:')[1].strip()
                stats['win_rate'] = value
                print(f"✅ 提取勝率: {value}")
            except Exception as e:
                print(f"❌ 提取勝率失敗: {e}")
        elif '總損益(' in clean_line and '口):' in clean_line:
            try:
                value = clean_line.split('):')[1].strip()
                stats['total_pnl'] = value
                print(f"✅ 提取總損益: {value}")
            except Exception as e:
                print(f"❌ 提取總損益失敗: {e}")
    
    print(f"\n📊 最終提取的統計數據: {stats}")
    return stats

if __name__ == "__main__":
    print("🧪 開始測試GUI修復...")
    result = test_backtest_execution()
    
    if result and result.returncode == 0:
        print("\n✅ 測試完成 - 回測執行成功")
    else:
        print("\n❌ 測試完成 - 回測執行失敗")
