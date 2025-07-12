#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
反轉策略驗證測試腳本
對比原始策略與反轉策略的表現，驗證反轉效果
"""

import subprocess
import sys
import os
from datetime import datetime
import json

def run_strategy_test(script_name, start_date, end_date, description):
    """執行策略測試並返回結果"""
    print(f"\n{'='*60}")
    print(f"🧪 {description}")
    print(f"📅 測試期間: {start_date} 至 {end_date}")
    print(f"📄 執行腳本: {script_name}")
    print(f"{'='*60}")
    
    try:
        # 執行策略腳本
        cmd = [sys.executable, script_name, "--start-date", start_date, "--end-date", end_date]
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=300)
        
        if result.returncode != 0:
            print(f"❌ 執行失敗: {result.stderr}")
            return None
            
        # 解析結果
        output_lines = result.stdout.split('\n')
        results = {}
        
        for line in output_lines:
            if "總交易次數:" in line:
                results['total_trades'] = int(line.split(':')[1].strip())
            elif "勝率:" in line:
                results['win_rate'] = float(line.split(':')[1].strip().replace('%', ''))
            elif "總損益(3口):" in line:
                results['total_pnl'] = float(line.split(':')[1].strip())
                
        return results
        
    except subprocess.TimeoutExpired:
        print("❌ 執行超時")
        return None
    except Exception as e:
        print(f"❌ 執行錯誤: {e}")
        return None

def format_results(results, strategy_name):
    """格式化結果顯示"""
    if not results:
        return f"{strategy_name}: 測試失敗"
        
    return f"""
{strategy_name}:
  📊 總交易次數: {results.get('total_trades', 'N/A')}
  🎯 勝率: {results.get('win_rate', 'N/A'):.2f}%
  💰 總損益: {results.get('total_pnl', 'N/A'):.2f} 點
  💵 NT$價值: {results.get('total_pnl', 0) * 50:,.0f} 元
"""

def calculate_improvement(original, reversed_strategy):
    """計算改善效果"""
    if not original or not reversed_strategy:
        return "無法計算改善效果"
        
    pnl_improvement = reversed_strategy.get('total_pnl', 0) - original.get('total_pnl', 0)
    win_rate_improvement = reversed_strategy.get('win_rate', 0) - original.get('win_rate', 0)
    
    return f"""
🚀 改善效果分析:
  📈 損益改善: {pnl_improvement:+.2f} 點 ({pnl_improvement * 50:+,.0f} NT$)
  🎯 勝率提升: {win_rate_improvement:+.2f}%
  📊 改善倍數: {abs(pnl_improvement / original.get('total_pnl', 1)):.2f}x
"""

def main():
    """主測試函數"""
    print("🔄 台指期貨反轉策略驗證測試")
    print("=" * 60)
    
    # 測試配置
    test_periods = [
        {
            "start": "2024-11-04",
            "end": "2025-06-27",
            "description": "完整測試期間 (原始虧損-1982.0點期間)"
        },
        {
            "start": "2024-11-04", 
            "end": "2024-12-31",
            "description": "2024年末測試"
        },
        {
            "start": "2025-01-01",
            "end": "2025-06-27", 
            "description": "2025年初測試"
        }
    ]
    
    all_results = []
    
    for period in test_periods:
        print(f"\n🧪 測試期間: {period['description']}")
        
        # 測試原始策略
        original_results = run_strategy_test(
            "multi_Profit-Funded Risk_多口.py",
            period["start"],
            period["end"],
            f"原始策略測試 - {period['description']}"
        )
        
        # 測試反轉策略  
        reversed_results = run_strategy_test(
            "rev_multi_Profit-Funded Risk_多口.py",
            period["start"],
            period["end"],
            f"反轉策略測試 - {period['description']}"
        )
        
        # 顯示對比結果
        print(f"\n📊 {period['description']} - 結果對比:")
        print("=" * 50)
        print(format_results(original_results, "🔴 原始策略"))
        print(format_results(reversed_results, "🔄 反轉策略"))
        print(calculate_improvement(original_results, reversed_results))
        
        # 保存結果
        all_results.append({
            "period": period,
            "original": original_results,
            "reversed": reversed_results
        })
    
    # 生成總結報告
    print(f"\n{'='*60}")
    print("📋 總結報告")
    print(f"{'='*60}")
    
    for i, result in enumerate(all_results, 1):
        period = result["period"]
        original = result["original"]
        reversed_strategy = result["reversed"]
        
        if original and reversed_strategy:
            improvement = reversed_strategy.get('total_pnl', 0) - original.get('total_pnl', 0)
            print(f"\n{i}. {period['description']}:")
            print(f"   原始: {original.get('total_pnl', 0):.1f}點 → 反轉: {reversed_strategy.get('total_pnl', 0):.1f}點")
            print(f"   改善: {improvement:+.1f}點 ({improvement*50:+,.0f} NT$)")
    
    print(f"\n✅ 反轉策略驗證測試完成!")
    print(f"📊 測試時間: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

if __name__ == "__main__":
    main()
