"""
未來路徑分析器 - Forecasting Future Equity Curve Paths

這個工具能夠：
1. 執行一次標準回測，以獲取策略的歷史每日損益特徵（平均值μ 和 標準差σ）
2. 基於這些特徵，使用蒙地卡羅方法模擬數千條未來可能的資金曲線路徑
3. 將所有模擬路徑繪製成一張「義大利麵圖」(Spaghetti Chart) 進行視覺化
4. 量化分析未來的獲利潛力、風險暴露機率和最終資金分佈，生成一份完整的分析報告

使用方法：
    python future_path_analyzer.py

作者：Augment Agent
日期：2025-07-14
"""

import numpy as np
import matplotlib.pyplot as plt
import matplotlib
from decimal import Decimal
from typing import List, Optional
import logging
import os
from datetime import datetime

# 設定中文字體支援
matplotlib.rcParams['font.sans-serif'] = ['Arial Unicode MS', 'SimHei', 'DejaVu Sans']
matplotlib.rcParams['axes.unicode_minus'] = False

# 導入策略核心模組
from strategy_core import run_backtest, StrategyConfig, LotRule, StopLossType

# 設定日誌
logging.basicConfig(level=logging.INFO, format='[%(asctime)s] %(levelname)s: %(message)s')
logger = logging.getLogger(__name__)

def simulate_future_paths(historical_daily_pnl: List[Decimal], num_simulations: int,
                         num_future_days: int, initial_capital: float) -> List[np.ndarray]:
    """
    使用蒙地卡羅方法模擬未來資金曲線路徑

    Args:
        historical_daily_pnl: 從回測得到的歷史每日損益列表
        num_simulations: 模擬的總次數（例如 2000）
        num_future_days: 要預測的未來交易日天數（例如 60）
        initial_capital: 模擬的起始資金

    Returns:
        List[np.ndarray]: 包含所有模擬路徑的列表，每條路徑都是一個NumPy陣列
    """
    logger.info(f"🎲 開始蒙地卡羅模擬：{num_simulations} 次模擬，{num_future_days} 天預測")

    # 將 Decimal 轉換為 float 以便 numpy 處理
    pnl_array = np.array([float(pnl) for pnl in historical_daily_pnl])

    # 計算歷史每日損益的統計特徵
    mu = np.mean(pnl_array)  # 平均值
    sigma = np.std(pnl_array)  # 標準差

    logger.info(f"📊 歷史損益統計特徵：")
    logger.info(f"   - 樣本數量：{len(pnl_array)} 個交易日")
    logger.info(f"   - 平均每日損益 (μ)：{mu:.2f} 點")
    logger.info(f"   - 標準差 (σ)：{sigma:.2f} 點")
    logger.info(f"   - 起始資金：{initial_capital:,.0f}")

    # 初始化存放所有模擬路徑的列表
    all_paths = []

    # 執行蒙地卡羅模擬
    for i in range(num_simulations):
        # 生成隨機每日損益序列（基於歷史統計特徵）
        random_daily_pnl = np.random.normal(loc=mu, scale=sigma, size=num_future_days)

        # 計算累積損益並加上起始資金，形成資金曲線路徑
        cumulative_pnl = np.cumsum(random_daily_pnl)
        equity_curve = initial_capital + cumulative_pnl

        # 將起始資金點加到路徑開頭
        full_path = np.concatenate([[initial_capital], equity_curve])

        # 添加到路徑列表
        all_paths.append(full_path)

        # 每完成 10% 顯示進度
        if (i + 1) % (num_simulations // 10) == 0:
            progress = (i + 1) / num_simulations * 100
            logger.info(f"   模擬進度：{progress:.0f}% ({i + 1}/{num_simulations})")

    logger.info(f"✅ 蒙地卡羅模擬完成！生成了 {len(all_paths)} 條未來路徑")

    return all_paths


def analyze_and_plot_future_paths(all_paths: List[np.ndarray], initial_capital: float,
                                 profit_target_pct: Optional[float] = None, risk_limit_pct: Optional[float] = None,
                                 profit_target_abs: Optional[float] = None, risk_limit_abs: Optional[float] = None,
                                 save_reports: bool = True, strategy_config=None,
                                 start_date: str = "", end_date: str = "",
                                 range_start_time: str = "", range_end_time: str = "") -> None:
    """
    分析並視覺化未來路徑，繪製義大利麵圖並計算關鍵風險指標

    Args:
        all_paths: 從模擬獲得的所有路徑列表
        initial_capital: 起始資金
        profit_target_pct: 獲利目標百分比（例如 0.20 代表20%）
        risk_limit_pct: 風險底線百分比（例如 0.15 代表15%）
    """
    logger.info(f"📊 開始分析 {len(all_paths)} 條模擬路徑")

    # 計算目標線和風險線 (支援絕對值和百分比兩種模式)
    if profit_target_abs is not None and risk_limit_abs is not None:
        # 絕對值模式
        profit_target = profit_target_abs
        risk_limit = risk_limit_abs
        logger.info(f"📈 分析參數 (絕對值模式)：")
        logger.info(f"   - 起始點數：{initial_capital:,.0f}")
        logger.info(f"   - 獲利目標：{profit_target:+,.0f} 點")
        logger.info(f"   - 風險底線：{risk_limit:+,.0f} 點")
    else:
        # 百分比模式
        if profit_target_pct is None or risk_limit_pct is None:
            raise ValueError("在百分比模式下，profit_target_pct 和 risk_limit_pct 不能為 None")
        profit_target = initial_capital * (1 + profit_target_pct)
        risk_limit = initial_capital * (1 - risk_limit_pct)
        logger.info(f"📈 分析參數 (百分比模式)：")
        logger.info(f"   - 起始資金：{initial_capital:,.0f}")
        logger.info(f"   - 獲利目標：{profit_target:,.0f} (+{profit_target_pct:.1%})")
        logger.info(f"   - 風險底線：{risk_limit:,.0f} (-{risk_limit_pct:.1%})")

    # 創建圖表
    plt.figure(figsize=(14, 10))

    # 繪製所有模擬路徑（義大利麵圖）
    for i, path in enumerate(all_paths):
        plt.plot(range(len(path)), path, color='lightblue', alpha=0.1, linewidth=0.5)

        # 每繪製 200 條路徑顯示一次進度
        if (i + 1) % 200 == 0:
            progress = (i + 1) / len(all_paths) * 100
            logger.info(f"   繪圖進度：{progress:.0f}% ({i + 1}/{len(all_paths)})")

    # 繪製重要的水平線
    plt.axhline(y=initial_capital, color='black', linestyle='-', linewidth=2, label=f'起始資金 ({initial_capital:,.0f})')
    plt.axhline(y=profit_target, color='green', linestyle='--', linewidth=2, label=f'獲利目標 ({profit_target:,.0f})')
    plt.axhline(y=risk_limit, color='red', linestyle='--', linewidth=2, label=f'風險底線 ({risk_limit:,.0f})')

    # 設定圖表標題和標籤
    num_days = len(all_paths[0]) - 1  # 減1因為包含起始點
    plt.title(f'未來{num_days}天資金曲線蒙地卡羅模擬\n({len(all_paths):,} 次模擬)', fontsize=16, fontweight='bold')
    plt.xlabel('交易日', fontsize=12)
    plt.ylabel('資金 (點)', fontsize=12)
    plt.legend(fontsize=10)
    plt.grid(True, alpha=0.3)

    # 美化圖表
    plt.tight_layout()

    logger.info("📊 義大利麵圖繪製完成")

    # ==========================================
    # 計算分析指標
    # ==========================================
    logger.info("🔍 計算風險與回報指標...")

    # 統計觸及獲利目標的路徑
    paths_hit_profit = 0
    paths_hit_risk = 0
    final_values = []

    for path in all_paths:
        # 檢查是否曾經觸及或超過獲利目標
        if np.any(path >= profit_target):
            paths_hit_profit += 1

        # 檢查是否曾經觸及或跌破風險底線
        if np.any(path <= risk_limit):
            paths_hit_risk += 1

        # 收集最終資金值
        final_values.append(path[-1])

    # 計算百分比
    profit_hit_pct = (paths_hit_profit / len(all_paths)) * 100
    risk_hit_pct = (paths_hit_risk / len(all_paths)) * 100

    # 計算最終資金分位數
    final_values = np.array(final_values)
    percentile_5 = np.percentile(final_values, 5)
    percentile_50 = np.percentile(final_values, 50)  # 中位數
    percentile_95 = np.percentile(final_values, 95)

    # 計算平均最終資金和標準差
    mean_final = np.mean(final_values)
    std_final = np.std(final_values)

    # ==========================================
    # 輸出分析報告
    # ==========================================
    print("\n" + "="*60)
    print("🎯 未來路徑分析報告")
    print("="*60)
    print(f"📊 模擬參數：")
    print(f"   • 模擬次數：{len(all_paths):,} 次")
    print(f"   • 預測天數：{len(all_paths[0])-1} 天")
    print(f"   • 起始資金：{initial_capital:,.0f} 點")
    print()
    print(f"🎯 獲利潛力分析：")
    if profit_target_abs is not None:
        # 絕對值模式
        print(f"   • 觸及獲利目標 ({profit_target:+,.0f}點) 的機率：{profit_hit_pct:.1f}%")
        print(f"   • 獲利目標：{profit_target:+,.0f} 點")
    else:
        # 百分比模式
        print(f"   • 觸及獲利目標 (+{profit_target_pct:.1%}) 的機率：{profit_hit_pct:.1f}%")
        print(f"   • 獲利目標金額：{profit_target:,.0f} 點")
    print()
    print(f"⚠️  風險暴露分析：")
    if risk_limit_abs is not None:
        # 絕對值模式
        print(f"   • 觸及風險底線 ({risk_limit:+,.0f}點) 的機率：{risk_hit_pct:.1f}%")
        print(f"   • 風險底線：{risk_limit:+,.0f} 點")
    else:
        # 百分比模式
        print(f"   • 觸及風險底線 (-{risk_limit_pct:.1%}) 的機率：{risk_hit_pct:.1f}%")
        print(f"   • 風險底線金額：{risk_limit:,.0f} 點")
    print()
    print(f"📈 最終資金分佈：")
    print(f"   • 平均最終資金：{mean_final:,.0f} 點")
    print(f"   • 標準差：{std_final:,.0f} 點")
    print(f"   • 5% 分位數 (悲觀情境)：{percentile_5:,.0f} 點")
    print(f"   • 50% 分位數 (中位數)：{percentile_50:,.0f} 點")
    print(f"   • 95% 分位數 (樂觀情境)：{percentile_95:,.0f} 點")
    print()

    # 計算預期報酬率
    if profit_target_abs is not None:
        # 絕對值模式：顯示平均損益點數
        print(f"💰 預期平均損益：{mean_final:+.0f} 點")
    else:
        # 百分比模式：計算報酬率
        if initial_capital != 0:
            expected_return_pct = ((mean_final - initial_capital) / initial_capital) * 100
            print(f"💰 預期報酬率：{expected_return_pct:+.2f}%")
        else:
            print(f"💰 預期平均損益：{mean_final:+.0f} 點")
    print("="*60)

    # 保存報告和圖片
    if save_reports:
        # 創建報告資料夾
        reports_dir = "future_path_analyzer_reports"
        os.makedirs(reports_dir, exist_ok=True)

        # 生成時間戳
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

        # 保存圖片
        chart_filename = f"future_paths_spaghetti_chart_{timestamp}.png"
        chart_path = os.path.join(reports_dir, chart_filename)
        plt.savefig(chart_path, dpi=300, bbox_inches='tight')
        logger.info(f"📊 義大利麵圖已保存：{chart_path}")

        # 生成並保存文字報告
        report_filename = f"future_paths_analysis_report_{timestamp}.txt"
        report_path = os.path.join(reports_dir, report_filename)

        with open(report_path, 'w', encoding='utf-8') as f:
            f.write("="*60 + "\n")
            f.write("🎯 未來路徑分析報告\n")
            f.write("="*60 + "\n")

            # 策略配置資訊
            f.write("📋 策略配置：\n")
            f.write(f"   • 回測時間區間：{start_date} 至 {end_date}\n")
            f.write(f"   • 開盤區間時間：{range_start_time} 至 {range_end_time}\n")
            f.write(f"   • 交易口數：{strategy_config.trade_size_in_lots if strategy_config else 'N/A'}\n")
            f.write(f"   • 停損類型：區間邊緣\n")

            if strategy_config and strategy_config.lot_rules:
                f.write("   • 各口設定：\n")
                for i, rule in enumerate(strategy_config.lot_rules):
                    lot_num = i + 1
                    if rule.use_trailing_stop and rule.trailing_activation and rule.trailing_pullback:
                        f.write(f"     - 第{lot_num}口：{rule.trailing_activation}點觸發，{rule.trailing_pullback:.1%}回撤")
                        if rule.protective_stop_multiplier:
                            f.write(f"，{rule.protective_stop_multiplier}倍保護性停損")
                        f.write("\n")
            f.write("\n")

            f.write(f"📊 模擬參數：\n")
            f.write(f"   • 模擬次數：{len(all_paths):,} 次\n")
            f.write(f"   • 預測天數：{len(all_paths[0])-1} 天\n")
            f.write(f"   • 起始資金：{initial_capital:,.0f} 點\n")
            f.write("\n")

            if profit_target_abs is not None:
                f.write(f"🎯 獲利潛力分析：\n")
                f.write(f"   • 觸及獲利目標 ({profit_target:+,.0f}點) 的機率：{profit_hit_pct:.1f}%\n")
                f.write(f"   • 獲利目標：{profit_target:+,.0f} 點\n")
                f.write("\n")
                f.write(f"⚠️  風險暴露分析：\n")
                f.write(f"   • 觸及風險底線 ({risk_limit:+,.0f}點) 的機率：{risk_hit_pct:.1f}%\n")
                f.write(f"   • 風險底線：{risk_limit:+,.0f} 點\n")
            else:
                f.write(f"🎯 獲利潛力分析：\n")
                f.write(f"   • 觸及獲利目標 (+{profit_target_pct:.1%}) 的機率：{profit_hit_pct:.1f}%\n")
                f.write(f"   • 獲利目標金額：{profit_target:,.0f} 點\n")
                f.write("\n")
                f.write(f"⚠️  風險暴露分析：\n")
                f.write(f"   • 觸及風險底線 (-{risk_limit_pct:.1%}) 的機率：{risk_hit_pct:.1f}%\n")
                f.write(f"   • 風險底線金額：{risk_limit:,.0f} 點\n")

            f.write("\n")
            f.write(f"📈 最終資金分佈：\n")
            f.write(f"   • 平均最終資金：{mean_final:,.0f} 點\n")
            f.write(f"   • 標準差：{std_final:,.0f} 點\n")
            f.write(f"   • 5% 分位數 (悲觀情境)：{percentile_5:,.0f} 點\n")
            f.write(f"   • 50% 分位數 (中位數)：{percentile_50:,.0f} 點\n")
            f.write(f"   • 95% 分位數 (樂觀情境)：{percentile_95:,.0f} 點\n")
            f.write("\n")

            if profit_target_abs is not None:
                f.write(f"💰 預期平均損益：{mean_final:+.0f} 點\n")
            else:
                if initial_capital != 0:
                    expected_return_pct = ((mean_final - initial_capital) / initial_capital) * 100
                    f.write(f"💰 預期報酬率：{expected_return_pct:+.2f}%\n")
                else:
                    f.write(f"💰 預期平均損益：{mean_final:+.0f} 點\n")

            f.write("="*60 + "\n")
            f.write(f"報告生成時間：{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")

        logger.info(f"📄 分析報告已保存：{report_path}")

    # 顯示圖表
    plt.show()

    logger.info("✅ 分析報告生成完成！")


def run_dual_analysis(daily_pnl_list, num_simulations, num_future_days,
                     initial_capital_points, profit_target_points, risk_limit_points,
                     initial_capital_pct, profit_target_pct, risk_limit_pct, save_reports: bool = True,
                     strategy_config=None, start_date: str = "", end_date: str = "",
                     range_start_time: str = "", range_end_time: str = ""):
    """
    執行雙方案分析：策略損益曲線 vs 資本報酬率
    """
    print("\n" + "="*80)
    print("🎯 雙方案未來路徑分析結果")
    print("="*80)

    # ==========================================
    # 方案一：策略損益曲線分析
    # ==========================================
    logger.info("📊 執行方案一：策略損益曲線分析")

    paths_points = simulate_future_paths(
        historical_daily_pnl=daily_pnl_list,
        num_simulations=num_simulations,
        num_future_days=num_future_days,
        initial_capital=initial_capital_points
    )

    # 分析方案一結果
    profit_target_abs = profit_target_points
    risk_limit_abs = risk_limit_points

    paths_hit_profit_1 = 0
    paths_hit_risk_1 = 0
    final_values_1 = []

    for path in paths_points:
        if np.any(path >= profit_target_abs):
            paths_hit_profit_1 += 1
        if np.any(path <= risk_limit_abs):
            paths_hit_risk_1 += 1
        final_values_1.append(path[-1])

    profit_hit_pct_1 = (paths_hit_profit_1 / len(paths_points)) * 100
    risk_hit_pct_1 = (paths_hit_risk_1 / len(paths_points)) * 100
    final_values_1 = np.array(final_values_1)

    # ==========================================
    # 方案二：資本報酬率分析
    # ==========================================
    logger.info("📊 執行方案二：資本報酬率分析")

    paths_pct = simulate_future_paths(
        historical_daily_pnl=daily_pnl_list,
        num_simulations=num_simulations,
        num_future_days=num_future_days,
        initial_capital=initial_capital_pct
    )

    # 分析方案二結果
    profit_target_abs_2 = initial_capital_pct * (1 + profit_target_pct)
    risk_limit_abs_2 = initial_capital_pct * (1 - risk_limit_pct)

    paths_hit_profit_2 = 0
    paths_hit_risk_2 = 0
    final_values_2 = []

    for path in paths_pct:
        if np.any(path >= profit_target_abs_2):
            paths_hit_profit_2 += 1
        if np.any(path <= risk_limit_abs_2):
            paths_hit_risk_2 += 1
        final_values_2.append(path[-1])

    profit_hit_pct_2 = (paths_hit_profit_2 / len(paths_pct)) * 100
    risk_hit_pct_2 = (paths_hit_risk_2 / len(paths_pct)) * 100
    final_values_2 = np.array(final_values_2)

    # 保存雙方案對比報告
    if save_reports:
        reports_dir = "future_path_analyzer_reports"
        os.makedirs(reports_dir, exist_ok=True)

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        dual_report_filename = f"dual_analysis_comparison_{timestamp}.txt"
        dual_report_path = os.path.join(reports_dir, dual_report_filename)

        with open(dual_report_path, 'w', encoding='utf-8') as f:
            f.write("="*80 + "\n")
            f.write("🎯 雙方案未來路徑分析對比報告\n")
            f.write("="*80 + "\n")

            # 策略配置資訊
            f.write("📋 策略配置：\n")
            f.write(f"   • 回測時間區間：{start_date} 至 {end_date}\n")
            f.write(f"   • 開盤區間時間：{range_start_time} 至 {range_end_time}\n")
            f.write(f"   • 交易口數：{strategy_config.trade_size_in_lots if strategy_config else 'N/A'}\n")
            f.write(f"   • 停損類型：區間邊緣\n")

            if strategy_config and strategy_config.lot_rules:
                f.write("   • 各口設定：\n")
                for i, rule in enumerate(strategy_config.lot_rules):
                    lot_num = i + 1
                    if rule.use_trailing_stop and rule.trailing_activation and rule.trailing_pullback:
                        f.write(f"     - 第{lot_num}口：{rule.trailing_activation}點觸發，{rule.trailing_pullback:.1%}回撤")
                        if rule.protective_stop_multiplier:
                            f.write(f"，{rule.protective_stop_multiplier}倍保護性停損")
                        f.write("\n")
            f.write("\n")

            f.write(f"📊 模擬參數：\n")
            f.write(f"   • 模擬次數：{num_simulations:,} 次\n")
            f.write(f"   • 預測天數：{num_future_days} 天\n")
            f.write(f"   • 歷史樣本：{len(daily_pnl_list)} 個交易日\n")
            f.write("\n")

            f.write(f"📊 方案一：策略損益曲線分析 (點數)\n")
            f.write(f"   • 觸及獲利目標 ({profit_target_points:+,}點) 機率：{profit_hit_pct_1:.1f}%\n")
            f.write(f"   • 觸及風險底線 ({risk_limit_points:+,}點) 機率：{risk_hit_pct_1:.1f}%\n")
            f.write(f"   • 平均最終損益：{np.mean(final_values_1):+,.0f} 點\n")
            f.write(f"   • 5%分位數：{np.percentile(final_values_1, 5):+,.0f} 點\n")
            f.write(f"   • 95%分位數：{np.percentile(final_values_1, 95):+,.0f} 點\n")
            f.write("\n")

            f.write(f"📊 方案二：資本報酬率分析 (百分比)\n")
            f.write(f"   • 觸及獲利目標 (+{profit_target_pct:.1%}) 機率：{profit_hit_pct_2:.1f}%\n")
            f.write(f"   • 觸及風險底線 (-{risk_limit_pct:.1%}) 機率：{risk_hit_pct_2:.1f}%\n")
            final_returns_2 = (final_values_2 - initial_capital_pct) / initial_capital_pct * 100
            f.write(f"   • 平均最終報酬率：{np.mean(final_returns_2):+.2f}%\n")
            f.write(f"   • 5%分位數報酬率：{np.percentile(final_returns_2, 5):+.2f}%\n")
            f.write(f"   • 95%分位數報酬率：{np.percentile(final_returns_2, 95):+.2f}%\n")
            f.write("\n")

            f.write("="*80 + "\n")
            f.write(f"報告生成時間：{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")

        logger.info(f"📄 雙方案對比報告已保存：{dual_report_path}")

    return (paths_points, final_values_1, profit_hit_pct_1, risk_hit_pct_1,
            paths_pct, final_values_2, profit_hit_pct_2, risk_hit_pct_2)


# ==============================================================================
# 主執行區塊
# ==============================================================================
if __name__ == '__main__':
    """
    未來路徑分析器主程式

    執行流程：
    1. 設定分析參數
    2. 執行歷史回測獲取每日損益數據
    3. 使用蒙地卡羅方法模擬未來路徑
    4. 分析並視覺化結果
    """

    logger.info("🚀 未來路徑分析器啟動")
    logger.info("="*60)

    # ==========================================
    # 1. 設定分析參數
    # ==========================================
    NUM_SIMULATIONS = 2000      # 蒙地卡羅模擬次數
    NUM_FUTURE_DAYS = 250       # 預測未來交易日天數

    # 🎯 方案一：策略損益曲線分析 (點數)
    INITIAL_CAPITAL_POINTS = 0      # 起始點數 (從0開始累積)
    PROFIT_TARGET_POINTS = 5000     # 獲利目標 (5000點)
    RISK_LIMIT_POINTS = -3000       # 風險底線 (-3000點)

    # 🎯 方案二：資本報酬率分析 (百分比) - 作為對比
    INITIAL_CAPITAL_PCT = 1000000   # 起始資金 (100萬點)
    PROFIT_TARGET_PCT = 0.20        # 獲利目標百分比 (20%)
    RISK_LIMIT_PCT = 0.15           # 風險底線百分比 (15%)

    # 回測時間區間設定
    START_DATE = "2024-11-04"   # 回測開始日期
    END_DATE = "2025-06-28"     # 回測結束日期

    # 🕐 開盤區間時間窗口設定
    RANGE_START_TIME = "08:58"  # 開盤區間開始時間
    RANGE_END_TIME = "09:02"    # 開盤區間結束時間

    logger.info(f"📋 分析參數設定：")
    logger.info(f"   • 蒙地卡羅模擬次數：{NUM_SIMULATIONS:,}")
    logger.info(f"   • 預測天數：{NUM_FUTURE_DAYS}")
    logger.info(f"   • 方案一 - 策略損益分析：")
    logger.info(f"     - 起始點數：{INITIAL_CAPITAL_POINTS} 點")
    logger.info(f"     - 獲利目標：{PROFIT_TARGET_POINTS:+,} 點")
    logger.info(f"     - 風險底線：{RISK_LIMIT_POINTS:+,} 點")
    logger.info(f"   • 方案二 - 資本報酬率分析：")
    logger.info(f"     - 起始資金：{INITIAL_CAPITAL_PCT:,} 點")
    logger.info(f"     - 獲利目標：+{PROFIT_TARGET_PCT:.1%}")
    logger.info(f"     - 風險底線：-{RISK_LIMIT_PCT:.1%}")
    logger.info(f"   • 回測區間：{START_DATE} 至 {END_DATE}")
    logger.info(f"   • 開盤區間：{RANGE_START_TIME} 至 {RANGE_END_TIME}")

    # ==========================================
    # 2. 創建策略配置並執行回測
    # ==========================================
    logger.info("\n📊 步驟 1：執行歷史回測獲取每日損益特徵")

    # 創建三口交易策略配置
    from decimal import Decimal
    strategy_config = StrategyConfig(
        trade_size_in_lots=3,
        stop_loss_type=StopLossType.RANGE_BOUNDARY,
        lot_rules=[
            # 第1口：15點觸發，20%回檔
            LotRule(
                use_trailing_stop=True,
                trailing_activation=Decimal('20'),
                trailing_pullback=Decimal('0.10')
            ),
            # 第2口：40點觸發，20%回檔，2倍保護性停損
            LotRule(
                use_trailing_stop=True,
                trailing_activation=Decimal('35'),
                trailing_pullback=Decimal('0.10'),
                protective_stop_multiplier=Decimal('2.0')
            ),
            # 第3口：65點觸發，20%回檔，2倍保護性停損
            LotRule(
                use_trailing_stop=True,
                trailing_activation=Decimal('40'),
                trailing_pullback=Decimal('0.20'),
                protective_stop_multiplier=Decimal('2.0')
            )
        ],
        trading_direction="LONG_ONLY"  # 多空都做 BOTH LONG_ONLY SHORT_ONLY
    )

    # ==========================================
    # 3. 執行回測獲取歷史數據
    # ==========================================
    try:
        # 初始化數據庫連接
        from strategy_core import sqlite_connection
        sqlite_connection.init_sqlite_connection()

        # 執行回測
        backtest_result = run_backtest(
            config=strategy_config,
            start_date=START_DATE,
            end_date=END_DATE,
            range_start_time=RANGE_START_TIME,  # 開盤區間開始時間
            range_end_time=RANGE_END_TIME,      # 開盤區間結束時間
            silent=False  # 顯示回測過程
        )

        # 獲取每日損益列表
        daily_pnl_list = backtest_result['daily_pnl_list']

        if not daily_pnl_list:
            logger.error("❌ 回測未產生任何交易數據，無法進行未來路徑分析")
            exit(1)

        logger.info(f"✅ 回測完成！獲得 {len(daily_pnl_list)} 個交易日的損益數據")
        logger.info(f"   總損益：{backtest_result['total_pnl']:.2f} 點")
        logger.info(f"   勝率：{backtest_result['win_rate']:.2%}")

    except Exception as e:
        logger.error(f"❌ 回測執行失敗：{e}")
        exit(1)

    # ==========================================
    # 4. 執行雙方案蒙地卡羅模擬與分析
    # ==========================================
    logger.info(f"\n🎲 步驟 2：執行雙方案蒙地卡羅模擬與分析")

    try:
        (paths_points, final_values_1, profit_hit_pct_1, risk_hit_pct_1,
         paths_pct, final_values_2, profit_hit_pct_2, risk_hit_pct_2) = run_dual_analysis(
            daily_pnl_list=daily_pnl_list,
            num_simulations=NUM_SIMULATIONS,
            num_future_days=NUM_FUTURE_DAYS,
            initial_capital_points=INITIAL_CAPITAL_POINTS,
            profit_target_points=PROFIT_TARGET_POINTS,
            risk_limit_points=RISK_LIMIT_POINTS,
            initial_capital_pct=INITIAL_CAPITAL_PCT,
            profit_target_pct=PROFIT_TARGET_PCT,
            risk_limit_pct=RISK_LIMIT_PCT,
            save_reports=True,
            strategy_config=strategy_config,
            start_date=START_DATE,
            end_date=END_DATE,
            range_start_time=RANGE_START_TIME,
            range_end_time=RANGE_END_TIME
        )

        # ==========================================
        # 5. 顯示對比結果
        # ==========================================
        print(f"\n📊 方案一：策略損益曲線分析 (點數)")
        print(f"   • 觸及獲利目標 ({PROFIT_TARGET_POINTS:+,}點) 機率：{profit_hit_pct_1:.1f}%")
        print(f"   • 觸及風險底線 ({RISK_LIMIT_POINTS:+,}點) 機率：{risk_hit_pct_1:.1f}%")
        print(f"   • 平均最終損益：{np.mean(final_values_1):+,.0f} 點")
        print(f"   • 5%分位數：{np.percentile(final_values_1, 5):+,.0f} 點")
        print(f"   • 95%分位數：{np.percentile(final_values_1, 95):+,.0f} 點")

        print(f"\n📊 方案二：資本報酬率分析 (百分比)")
        print(f"   • 觸及獲利目標 (+{PROFIT_TARGET_PCT:.1%}) 機率：{profit_hit_pct_2:.1f}%")
        print(f"   • 觸及風險底線 (-{RISK_LIMIT_PCT:.1%}) 機率：{risk_hit_pct_2:.1f}%")
        final_returns_2 = (final_values_2 - INITIAL_CAPITAL_PCT) / INITIAL_CAPITAL_PCT * 100
        print(f"   • 平均最終報酬率：{np.mean(final_returns_2):+.2f}%")
        print(f"   • 5%分位數報酬率：{np.percentile(final_returns_2, 5):+.2f}%")
        print(f"   • 95%分位數報酬率：{np.percentile(final_returns_2, 95):+.2f}%")

        # ==========================================
        # 6. 視覺化方案一結果
        # ==========================================
        logger.info(f"\n📊 步驟 3：視覺化策略損益曲線")

        analyze_and_plot_future_paths(
            all_paths=paths_points,
            initial_capital=INITIAL_CAPITAL_POINTS,
            profit_target_pct=None,  # 使用絕對值
            risk_limit_pct=None,     # 使用絕對值
            profit_target_abs=PROFIT_TARGET_POINTS,
            risk_limit_abs=RISK_LIMIT_POINTS,
            save_reports=True,
            strategy_config=strategy_config,
            start_date=START_DATE,
            end_date=END_DATE,
            range_start_time=RANGE_START_TIME,
            range_end_time=RANGE_END_TIME
        )

        logger.info("🎉 雙方案未來路徑分析完成！")

    except Exception as e:
        logger.error(f"❌ 分析失敗：{e}")
        exit(1)
