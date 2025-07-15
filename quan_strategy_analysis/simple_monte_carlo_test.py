#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
簡化的蒙地卡羅測試腳本
用於驗證核心功能是否正常工作

作者: 量化分析師
日期: 2025-01-14
"""

import sys
import os
from decimal import Decimal
import numpy as np
import matplotlib.pyplot as plt

# 添加當前目錄到 Python 路徑
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

def simple_monte_carlo_test():
    """簡化的蒙地卡羅測試"""
    print("🧪 簡化蒙地卡羅測試")
    print("="*50)
    
    # 創建測試數據（模擬每日損益）
    test_daily_pnl = [
        Decimal('103'), Decimal('95'), Decimal('-144'), Decimal('155'), Decimal('102'),
        Decimal('96'), Decimal('31'), Decimal('111'), Decimal('-81'), Decimal('107'),
        Decimal('-138'), Decimal('90'), Decimal('89'), Decimal('-132'), Decimal('113'),
        Decimal('131'), Decimal('-99'), Decimal('38'), Decimal('-162'), Decimal('26'),
        Decimal('105'), Decimal('-90'), Decimal('158'), Decimal('87'), Decimal('115'),
        Decimal('-74'), Decimal('106'), Decimal('18'), Decimal('114'), Decimal('92')
    ]
    
    print(f"📊 測試數據：{len(test_daily_pnl)} 個交易日")
    
    # 計算原始統計
    original_total_pnl = sum(test_daily_pnl)
    print(f"💰 原始總損益: {original_total_pnl} 點")
    
    # 計算原始最大回撤
    cumulative_pnl = np.cumsum([float(pnl) for pnl in test_daily_pnl])
    peak_pnl = np.maximum.accumulate(cumulative_pnl)
    drawdowns = peak_pnl - cumulative_pnl
    original_max_drawdown = np.max(drawdowns)
    print(f"📉 原始最大回撤: {original_max_drawdown:.2f} 點")
    
    # 執行蒙地卡羅模擬
    print(f"\n🎲 執行蒙地卡羅模擬...")
    num_simulations = 1000
    
    simulated_final_pnls = []
    simulated_max_drawdowns = []
    
    pnl_array = np.array([float(pnl) for pnl in test_daily_pnl])
    
    for i in range(num_simulations):
        if (i + 1) % 200 == 0:
            print(f"   進度: {(i + 1) / num_simulations * 100:.0f}%")
        
        # 隨機重組
        shuffled_pnl = pnl_array.copy()
        np.random.shuffle(shuffled_pnl)
        
        # 計算統計
        final_pnl = np.sum(shuffled_pnl)
        
        # 計算最大回撤
        cum_pnl = np.cumsum(shuffled_pnl)
        peak = np.maximum.accumulate(cum_pnl)
        dd = peak - cum_pnl
        max_dd = np.max(dd)
        
        simulated_final_pnls.append(final_pnl)
        simulated_max_drawdowns.append(max_dd)
    
    print(f"✅ 模擬完成！")
    
    # 分析結果
    print(f"\n📈 結果分析:")
    print(f"   模擬次數: {num_simulations}")
    print(f"   總損益平均: {np.mean(simulated_final_pnls):.2f} 點")
    print(f"   總損益標準差: {np.std(simulated_final_pnls):.2f} 點")
    print(f"   MDD平均: {np.mean(simulated_max_drawdowns):.2f} 點")
    print(f"   MDD標準差: {np.std(simulated_max_drawdowns):.2f} 點")
    
    # 計算百分位
    pnl_percentile = (np.sum(np.array(simulated_final_pnls) <= float(original_total_pnl)) / len(simulated_final_pnls)) * 100
    mdd_percentile = (np.sum(np.array(simulated_max_drawdowns) <= original_max_drawdown) / len(simulated_max_drawdowns)) * 100
    
    print(f"\n🎯 穩健性評估:")
    print(f"   原始總損益百分位: {pnl_percentile:.1f}%")
    print(f"   原始MDD百分位: {mdd_percentile:.1f}%")
    
    if pnl_percentile > 50:
        print(f"   ✅ 總損益表現優於隨機重組的 {pnl_percentile:.1f}% 情況")
    else:
        print(f"   ⚠️ 總損益表現僅優於隨機重組的 {pnl_percentile:.1f}% 情況")
    
    if mdd_percentile < 50:
        print(f"   ✅ 回撤控制優於隨機重組的 {100-mdd_percentile:.1f}% 情況")
    else:
        print(f"   ⚠️ 回撤控制僅優於隨機重組的 {100-mdd_percentile:.1f}% 情況")
    
    # 嘗試繪製圖表（如果可能的話）
    try:
        print(f"\n📊 生成視覺化圖表...")
        
        # 設定非互動式後端
        plt.switch_backend('Agg')
        
        fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(12, 5))
        
        # 總損益分佈
        ax1.hist(simulated_final_pnls, bins=30, alpha=0.7, color='skyblue', edgecolor='black')
        ax1.axvline(float(original_total_pnl), color='red', linestyle='--', linewidth=2, 
                    label=f'原始結果: {original_total_pnl}')
        ax1.set_title('模擬總損益分佈')
        ax1.set_xlabel('總損益 (點數)')
        ax1.set_ylabel('頻率')
        ax1.legend()
        ax1.grid(True, alpha=0.3)
        
        # MDD分佈
        ax2.hist(simulated_max_drawdowns, bins=30, alpha=0.7, color='lightcoral', edgecolor='black')
        ax2.axvline(original_max_drawdown, color='red', linestyle='--', linewidth=2, 
                    label=f'原始結果: {original_max_drawdown:.2f}')
        ax2.set_title('模擬最大回撤分佈')
        ax2.set_xlabel('最大回撤 (點數)')
        ax2.set_ylabel('頻率')
        ax2.legend()
        ax2.grid(True, alpha=0.3)
        
        plt.tight_layout()
        
        # 保存圖表
        chart_path = 'monte_carlo_test_results.png'
        plt.savefig(chart_path, dpi=300, bbox_inches='tight')
        print(f"   ✅ 圖表已保存: {chart_path}")
        
        plt.close()
        
    except Exception as e:
        print(f"   ⚠️ 圖表生成失敗: {e}")
    
    print(f"\n🎉 簡化蒙地卡羅測試完成！")
    return True


if __name__ == "__main__":
    simple_monte_carlo_test()
