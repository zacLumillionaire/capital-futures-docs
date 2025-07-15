# monte_carlo_functions.py
"""
蒙地卡羅模擬分析函式庫
用於對交易策略進行穩健性分析

作者: 量化分析師
日期: 2025-01-14
"""

import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from decimal import Decimal
from typing import List, Dict, Tuple
import copy


def run_monte_carlo_simulation(daily_pnl_list: List[Decimal], num_simulations: int = 2000) -> Dict:
    """
    執行蒙地卡羅模擬分析
    
    Args:
        daily_pnl_list: 從回測獲得的每日損益列表
        num_simulations: 模擬次數，預設為2000次
    
    Returns:
        dict: 包含模擬結果的字典
            - 'final_pnls': 所有模擬的最終總損益列表
            - 'max_drawdowns': 所有模擬的最大回撤列表
    """
    if not daily_pnl_list:
        print("⚠️ 警告：每日損益列表為空，無法進行蒙地卡羅模擬")
        return {'final_pnls': [], 'max_drawdowns': []}
    
    print(f"🎲 開始蒙地卡羅模擬...")
    print(f"   📊 原始交易日數: {len(daily_pnl_list)}")
    print(f"   🔄 模擬次數: {num_simulations}")
    
    # 初始化結果容器
    simulated_final_pnls = []
    simulated_max_drawdowns = []
    
    # 將 Decimal 轉換為 float 以便 numpy 處理
    pnl_array = np.array([float(pnl) for pnl in daily_pnl_list])
    
    # 執行模擬迴圈
    for i in range(num_simulations):
        # 顯示進度（每10%顯示一次）
        if (i + 1) % (num_simulations // 10) == 0:
            progress = (i + 1) / num_simulations * 100
            print(f"   🔄 模擬進度: {progress:.0f}% ({i + 1}/{num_simulations})")
        
        # 複製並打亂損益列表
        shuffled_pnl = pnl_array.copy()
        np.random.shuffle(shuffled_pnl)
        
        # 計算新的資金曲線和統計數據
        final_pnl, max_drawdown = _calculate_equity_curve_stats(shuffled_pnl)
        
        # 記錄結果
        simulated_final_pnls.append(final_pnl)
        simulated_max_drawdowns.append(max_drawdown)
    
    print(f"✅ 蒙地卡羅模擬完成！")
    
    return {
        'final_pnls': simulated_final_pnls,
        'max_drawdowns': simulated_max_drawdowns
    }


def _calculate_equity_curve_stats(pnl_sequence: np.ndarray) -> Tuple[float, float]:
    """
    計算資金曲線的統計數據
    
    Args:
        pnl_sequence: 損益序列
    
    Returns:
        tuple: (最終總損益, 最大回撤)
    """
    # 計算累積損益曲線
    cumulative_pnl = np.cumsum(pnl_sequence)
    
    # 最終總損益
    final_pnl = cumulative_pnl[-1]
    
    # 計算最大回撤 (MDD)
    # 追蹤累積損益的峰值
    peak_pnl = np.maximum.accumulate(cumulative_pnl)
    
    # 計算每個時點的回撤
    drawdowns = peak_pnl - cumulative_pnl
    
    # 最大回撤
    max_drawdown = np.max(drawdowns)
    
    return float(final_pnl), float(max_drawdown)


def analyze_and_plot_mc_results(simulation_results: Dict,
                               original_total_pnl: Decimal,
                               original_max_drawdown: Decimal,
                               output_dir: str = None) -> None:
    """
    分析並視覺化蒙地卡羅模擬結果
    
    Args:
        simulation_results: 模擬結果字典
        original_total_pnl: 原始回測的總損益
        original_max_drawdown: 原始回測的最大回撤
    """
    simulated_final_pnls = simulation_results['final_pnls']
    simulated_max_drawdowns = simulation_results['max_drawdowns']
    
    if not simulated_final_pnls or not simulated_max_drawdowns:
        print("⚠️ 警告：模擬結果為空，無法進行分析")
        return
    
    # 轉換原始數據為 float
    orig_pnl = float(original_total_pnl)
    orig_mdd = float(original_max_drawdown)
    
    print(f"\n📈 蒙地卡羅模擬結果分析")
    print(f"=" * 50)
    
    # 設定中文字體
    plt.rcParams['font.sans-serif'] = ['Arial Unicode MS', 'SimHei', 'DejaVu Sans']
    plt.rcParams['axes.unicode_minus'] = False
    
    # 創建圖表佈局
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(15, 6))
    
    # 動態計算合適的分箱數量，避免分箱錯誤
    pnl_unique_count = len(set(simulated_final_pnls))
    mdd_unique_count = len(set(simulated_max_drawdowns))

    # 確保分箱數量合理
    pnl_bins = max(5, min(50, pnl_unique_count))
    mdd_bins = max(5, min(50, mdd_unique_count))

    # 如果數據範圍太小，使用自動分箱
    pnl_range = max(simulated_final_pnls) - min(simulated_final_pnls)
    mdd_range = max(simulated_max_drawdowns) - min(simulated_max_drawdowns)

    if pnl_range == 0:
        pnl_bins = 1
    elif pnl_range < 10:
        pnl_bins = max(3, int(pnl_range))

    if mdd_range == 0:
        mdd_bins = 1
    elif mdd_range < 10:
        mdd_bins = max(3, int(mdd_range))

    # 第一個子圖：總損益分佈
    try:
        ax1.hist(simulated_final_pnls, bins=pnl_bins, alpha=0.7, color='skyblue', edgecolor='black')
    except ValueError:
        # 如果還是有問題，使用最簡單的分箱方式
        ax1.hist(simulated_final_pnls, bins='auto', alpha=0.7, color='skyblue', edgecolor='black')
    ax1.axvline(orig_pnl, color='red', linestyle='--', linewidth=2,
                label=f'原始回測結果: {orig_pnl:.2f}')
    ax1.set_title('模擬總損益分佈 (Final PnL Distribution)', fontsize=14, fontweight='bold')
    ax1.set_xlabel('總損益 (點數)', fontsize=12)
    ax1.set_ylabel('頻率', fontsize=12)
    ax1.legend()
    ax1.grid(True, alpha=0.3)

    # 第二個子圖：MDD分佈
    try:
        ax2.hist(simulated_max_drawdowns, bins=mdd_bins, alpha=0.7, color='lightcoral', edgecolor='black')
    except ValueError:
        # 如果還是有問題，使用最簡單的分箱方式
        ax2.hist(simulated_max_drawdowns, bins='auto', alpha=0.7, color='lightcoral', edgecolor='black')
    ax2.axvline(orig_mdd, color='red', linestyle='--', linewidth=2,
                label=f'原始回測結果: {orig_mdd:.2f}')
    ax2.set_title('模擬最大回撤分佈 (Max Drawdown Distribution)', fontsize=14, fontweight='bold')
    ax2.set_xlabel('最大回撤 (點數)', fontsize=12)
    ax2.set_ylabel('頻率', fontsize=12)
    ax2.legend()
    ax2.grid(True, alpha=0.3)
    
    plt.tight_layout()

    # 保存圖表到指定資料夾
    if output_dir:
        import os
        chart_path = os.path.join(output_dir, "monte_carlo_analysis.png")
        plt.savefig(chart_path, dpi=300, bbox_inches='tight')
        print(f"📊 圖表已保存: {chart_path}")

        # 也保存為高解析度PDF
        pdf_path = os.path.join(output_dir, "monte_carlo_analysis.pdf")
        plt.savefig(pdf_path, dpi=300, bbox_inches='tight')
        print(f"📊 PDF圖表已保存: {pdf_path}")

    plt.show()

    # 計算統計摘要
    _print_statistical_summary(simulated_final_pnls, simulated_max_drawdowns,
                              orig_pnl, orig_mdd)


def _print_statistical_summary(simulated_pnls: List[float], 
                              simulated_mdds: List[float],
                              original_pnl: float, 
                              original_mdd: float) -> None:
    """
    印出統計摘要報告
    """
    pnl_array = np.array(simulated_pnls)
    mdd_array = np.array(simulated_mdds)
    
    print(f"\n📊 統計摘要報告")
    print(f"=" * 50)
    
    # 總損益統計
    print(f"💰 總損益分析:")
    print(f"   原始回測結果: {original_pnl:.2f} 點")
    print(f"   模擬平均值: {np.mean(pnl_array):.2f} 點")
    print(f"   模擬中位數: {np.median(pnl_array):.2f} 點")
    print(f"   模擬標準差: {np.std(pnl_array):.2f} 點")
    print(f"   5% 分位數 (最差5%): {np.percentile(pnl_array, 5):.2f} 點")
    print(f"   95% 分位數 (最佳5%): {np.percentile(pnl_array, 95):.2f} 點")
    
    # 原始結果在分佈中的位置
    pnl_percentile = (np.sum(pnl_array <= original_pnl) / len(pnl_array)) * 100
    print(f"   原始結果百分位: {pnl_percentile:.1f}%")
    
    print(f"\n📉 最大回撤分析:")
    print(f"   原始回測結果: {original_mdd:.2f} 點")
    print(f"   模擬平均值: {np.mean(mdd_array):.2f} 點")
    print(f"   模擬中位數: {np.median(mdd_array):.2f} 點")
    print(f"   模擬標準差: {np.std(mdd_array):.2f} 點")
    print(f"   5% 分位數 (最佳5%): {np.percentile(mdd_array, 5):.2f} 點")
    print(f"   95% 分位數 (最差5%): {np.percentile(mdd_array, 95):.2f} 點")
    
    # 原始結果在分佈中的位置
    mdd_percentile = (np.sum(mdd_array <= original_mdd) / len(mdd_array)) * 100
    print(f"   原始結果百分位: {mdd_percentile:.1f}%")
    
    # 風險分析
    print(f"\n⚠️ 風險分析:")
    worse_pnl_prob = (np.sum(pnl_array < original_pnl) / len(pnl_array)) * 100
    worse_mdd_prob = (np.sum(mdd_array > original_mdd) / len(mdd_array)) * 100
    
    print(f"   獲得更差總損益的機率: {worse_pnl_prob:.1f}%")
    print(f"   遭遇更大回撤的機率: {worse_mdd_prob:.1f}%")
    
    # 穩健性評估
    print(f"\n🎯 策略穩健性評估:")
    if pnl_percentile > 50:
        print(f"   ✅ 總損益表現: 優於隨機重組的 {pnl_percentile:.1f}% 情況")
    else:
        print(f"   ⚠️ 總損益表現: 僅優於隨機重組的 {pnl_percentile:.1f}% 情況")
    
    if mdd_percentile < 50:
        print(f"   ✅ 回撤控制: 優於隨機重組的 {100-mdd_percentile:.1f}% 情況")
    else:
        print(f"   ⚠️ 回撤控制: 僅優於隨機重組的 {100-mdd_percentile:.1f}% 情況")
    
    print(f"=" * 50)
