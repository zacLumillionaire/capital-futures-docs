#!/usr/bin/env python3
"""
反轉策略未來路徑分析器

這個腳本能夠：
1. 執行一次標準回測，以獲取策略的歷史每日損益特徵（平均值μ 和 標準差σ）
2. 基於這些特徵，使用蒙地卡羅方法模擬數千條未來可能的資金曲線路徑
3. 將所有模擬路徑繪製成一張「義大利麵圖」(Spaghetti Chart) 進行視覺化
4. 量化分析未來的獲利潛力、風險暴露機率和最終資金分佈，生成一份完整的分析報告

使用方法:
    # 使用預設配置
    python rev_future_path_analyzer.py

    # 使用指定的配置文件
    python rev_future_path_analyzer.py --config conservative_config.yml

    # 使用其他配置範例
    python rev_future_path_analyzer.py --config aggressive_config.yml

配置文件:
    所有參數都可以通過 config.yml 文件進行配置，包括：
    - simulation_params: 蒙地卡羅模擬參數
    - backtest_params: 回測時間範圍和設定
    - strategy_params: 交易策略參數
    - output_params: 輸出格式設定

作者: Augment Agent
日期: 2025-07-16
版本: 2.0 (支援外部配置文件)
"""

import numpy as np
import matplotlib.pyplot as plt
import matplotlib
matplotlib.use('Agg')  # 使用非互動式後端
import seaborn as sns
import yaml
import argparse
from decimal import Decimal
from datetime import datetime
import os
import sys

# 添加當前目錄到路徑以導入核心模組
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# 導入核心模組
from rev_strategy_core import (
    run_rev_backtest, StrategyConfig, LotRule, RangeFilter,
    RiskConfig, StopLossConfig, StopLossType
)

# 🚀 【重構】導入統一的配置工廠
sys.path.append(os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'rev_strategy_analysis'))
from strategy_config_factory import create_rev_core_compatible_config

# 設定中文字體
plt.rcParams['font.sans-serif'] = ['Arial Unicode MS', 'SimHei', 'DejaVu Sans']
plt.rcParams['axes.unicode_minus'] = False

def load_config(config_path: str) -> dict:
    """
    從YAML文件中讀取配置參數

    Args:
        config_path: 配置文件的路徑

    Returns:
        dict: 包含所有配置參數的字典

    Raises:
        FileNotFoundError: 當配置文件不存在時
        yaml.YAMLError: 當YAML格式錯誤時
    """
    try:
        with open(config_path, 'r', encoding='utf-8') as file:
            config = yaml.safe_load(file)
            print(f"✅ 成功讀取配置文件: {config_path}")
            return config
    except FileNotFoundError:
        print(f"❌ 配置文件不存在: {config_path}")
        print("   請確保配置文件存在，或使用 --config 參數指定正確的路徑")
        raise
    except yaml.YAMLError as e:
        print(f"❌ 配置文件格式錯誤: {e}")
        print("   請檢查YAML語法是否正確")
        raise
    except Exception as e:
        print(f"❌ 讀取配置文件時發生錯誤: {e}")
        raise

# 🚀 【重構】移除舊的配置創建函數，現在使用統一的配置工廠



def rev_simulate_future_paths(historical_daily_pnl: list[Decimal], num_simulations: int, 
                             num_future_days: int, initial_capital: float) -> list:
    """
    使用蒙地卡羅方法模擬未來資金曲線路徑
    
    Args:
        historical_daily_pnl: 從回測得到的歷史每日損益列表
        num_simulations: 模擬的總次數（例如 2000）
        num_future_days: 要預測的未來交易日天數（例如 60）
        initial_capital: 模擬的起始資金
        
    Returns:
        list: 包含所有模擬路徑的列表，每條路徑是一個NumPy陣列
    """
    # 轉換為numpy陣列以便計算
    pnl_array = np.array([float(pnl) for pnl in historical_daily_pnl])
    
    # 計算統計特徵
    mu = np.mean(pnl_array)  # 平均值
    sigma = np.std(pnl_array)  # 標準差
    
    print(f"📊 歷史每日損益統計特徵:")
    print(f"   樣本數量: {len(pnl_array)} 天")
    print(f"   平均值 (μ): {mu:.2f} 點")
    print(f"   標準差 (σ): {sigma:.2f} 點")
    print(f"   最大值: {np.max(pnl_array):.2f} 點")
    print(f"   最小值: {np.min(pnl_array):.2f} 點")
    
    # 初始化結果列表
    all_paths = []
    
    print(f"🎲 開始蒙地卡羅模擬...")
    print(f"   模擬次數: {num_simulations}")
    print(f"   未來天數: {num_future_days}")
    print(f"   起始資金: {initial_capital}")
    
    # 執行模擬迴圈
    for i in range(num_simulations):
        # 生成隨機每日損益
        random_daily_pnl = np.random.normal(loc=mu, scale=sigma, size=num_future_days)
        
        # 計算累積損益並加上起始資金
        cumulative_pnl = np.cumsum(random_daily_pnl)
        equity_curve = initial_capital + cumulative_pnl
        
        # 將路徑添加到結果列表
        all_paths.append(equity_curve)
        
        # 顯示進度
        if (i + 1) % (num_simulations // 10) == 0:
            progress = (i + 1) / num_simulations * 100
            print(f"   進度: {progress:.0f}% ({i + 1}/{num_simulations})")
    
    print(f"✅ 蒙地卡羅模擬完成，生成 {len(all_paths)} 條路徑")
    
    return all_paths

def analyze_and_plot_future_paths(all_paths: list, initial_capital: float,
                                 profit_target_pct: float, risk_limit_pct: float,
                                 output_dir: str = None, chart_config: dict = None) -> dict:
    """
    分析並繪製未來路徑的義大利麵圖

    Args:
        all_paths: 從模擬獲得的路徑列表
        initial_capital: 起始資金
        profit_target_pct: 獲利目標百分比（例如 0.20 代表20%）
        risk_limit_pct: 風險底線百分比（例如 0.15 代表15%）
        output_dir: 輸出目錄，如果為None則使用當前目錄
        chart_config: 圖表配置參數

    Returns:
        dict: 分析結果統計
    """
    if output_dir is None:
        output_dir = os.path.dirname(os.path.abspath(__file__))

    # 確保輸出目錄存在
    os.makedirs(output_dir, exist_ok=True)

    # 從配置中獲取圖表參數
    if chart_config is None:
        chart_config = {}

    chart_width = chart_config.get('chart_size_width', 14)
    chart_height = chart_config.get('chart_size_height', 10)
    chart_dpi = chart_config.get('chart_dpi', 300)
    chart_format = chart_config.get('chart_format', 'png')
    chart_filename_prefix = chart_config.get('chart_filename_prefix', 'future_paths_spaghetti_chart')
    
    # 計算目標線和風險線
    profit_target_line = initial_capital * (1 + profit_target_pct)
    risk_limit_line = initial_capital * (1 - risk_limit_pct)
    
    print(f"📈 開始分析未來路徑...")
    print(f"   起始資金: {initial_capital:,.0f}")
    print(f"   獲利目標: {profit_target_line:,.0f} (+{profit_target_pct:.1%})")
    print(f"   風險底線: {risk_limit_line:,.0f} (-{risk_limit_pct:.1%})")
    
    # 創建圖表（使用配置的尺寸）
    plt.figure(figsize=(chart_width, chart_height))
    
    # 繪製所有路徑（義大利麵圖）
    for i, path in enumerate(all_paths):
        plt.plot(path, linewidth=0.5, alpha=0.1, color='blue')
        
        # 顯示進度
        if (i + 1) % (len(all_paths) // 10) == 0:
            progress = (i + 1) / len(all_paths) * 100
            print(f"   繪圖進度: {progress:.0f}% ({i + 1}/{len(all_paths)})")
    
    # 繪製參考線
    plt.axhline(y=initial_capital, color='black', linestyle='-', linewidth=2, label=f'起始資金: {initial_capital:,.0f}')
    plt.axhline(y=profit_target_line, color='green', linestyle='--', linewidth=2, label=f'獲利目標: {profit_target_line:,.0f} (+{profit_target_pct:.1%})')
    plt.axhline(y=risk_limit_line, color='red', linestyle='--', linewidth=2, label=f'風險底線: {risk_limit_line:,.0f} (-{risk_limit_pct:.1%})')
    
    # 設定圖表標題和標籤
    plt.title(f'反轉策略未來{len(all_paths[0])}天資金曲線蒙地卡羅模擬\n({len(all_paths):,}條模擬路徑)', fontsize=16, fontweight='bold')
    plt.xlabel('交易日', fontsize=12)
    plt.ylabel('資金 (點)', fontsize=12)
    plt.legend(fontsize=10)
    plt.grid(True, alpha=0.3)
    
    # 保存圖表（使用配置的參數）
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    chart_filename = f"{chart_filename_prefix}_{timestamp}.{chart_format}"
    chart_path = os.path.join(output_dir, chart_filename)
    plt.savefig(chart_path, dpi=chart_dpi, bbox_inches='tight', format=chart_format)
    plt.close()
    
    print(f"📊 義大利麵圖已保存: {chart_path}")
    
    # 計算分析指標
    print(f"🔍 計算分析指標...")
    
    # 統計觸及獲利目標的路徑
    profit_target_reached = 0
    risk_limit_breached = 0
    final_values = []
    
    for path in all_paths:
        # 檢查是否曾經觸及或超過獲利目標
        if np.any(path >= profit_target_line):
            profit_target_reached += 1
            
        # 檢查是否曾經觸及或跌破風險底線
        if np.any(path <= risk_limit_line):
            risk_limit_breached += 1
            
        # 記錄最終資金
        final_values.append(path[-1])
    
    # 計算百分比
    profit_target_pct_reached = (profit_target_reached / len(all_paths)) * 100
    risk_limit_pct_breached = (risk_limit_breached / len(all_paths)) * 100
    
    # 計算最終資金分位數
    final_values = np.array(final_values)
    percentile_5 = np.percentile(final_values, 5)
    percentile_50 = np.percentile(final_values, 50)
    percentile_95 = np.percentile(final_values, 95)
    
    # 輸出分析報告
    # 計算預期平均損益
    expected_pnl = np.mean(final_values) - initial_capital
    profit_target_amount = profit_target_pct * initial_capital
    risk_limit_amount = risk_limit_pct * initial_capital

    print(f"\n" + "="*60)
    print(f"🎯 未來路徑分析報告")
    print(f"="*60)
    print(f"🎯 獲利潛力分析:")
    print(f"   • 觸及獲利目標 (+{profit_target_amount:.0f}點) 的機率：{profit_target_pct_reached:.1f}%")
    print(f"   • 獲利目標：+{profit_target_amount:.0f} 點")
    print(f"")
    print(f"⚠️  風險暴露分析:")
    print(f"   • 觸及風險底線 ({risk_limit_amount:.0f}點) 的機率：{risk_limit_pct_breached:.1f}%")
    print(f"   • 風險底線：{risk_limit_amount:.0f} 點")
    print(f"")
    print(f"📈 最終資金分佈:")
    print(f"   • 平均最終資金：{np.mean(final_values):,.0f} 點")
    print(f"   • 標準差：{np.std(final_values):,.0f} 點")
    print(f"   • 5% 分位數 (悲觀情境)：{percentile_5:,.0f} 點")
    print(f"   • 50% 分位數 (中位數)：{percentile_50:,.0f} 點")
    print(f"   • 95% 分位數 (樂觀情境)：{percentile_95:,.0f} 點")
    print(f"")
    print(f"💰 預期平均損益：{expected_pnl:+.0f} 點")
    print(f"="*60)
    
    # 返回分析結果
    return {
        'profit_target_reached_pct': profit_target_pct_reached,
        'risk_limit_breached_pct': risk_limit_pct_breached,
        'final_values_percentiles': {
            '5%': percentile_5,
            '50%': percentile_50,
            '95%': percentile_95
        },
        'final_values_stats': {
            'mean': np.mean(final_values),
            'std': np.std(final_values),
            'max': np.max(final_values),
            'min': np.min(final_values)
        },
        'chart_path': chart_path
    }

if __name__ == '__main__':
    # === 解析命令列參數 ===
    parser = argparse.ArgumentParser(
        description='反轉策略未來路徑分析器 - 使用蒙地卡羅方法預測未來資金曲線',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
使用範例:
  python rev_future_path_analyzer.py                    # 使用預設配置
  python rev_future_path_analyzer.py --config custom.yml  # 使用自定義配置

配置文件說明:
  配置文件使用YAML格式，包含以下主要部分：
  - simulation_params: 蒙地卡羅模擬參數
  - backtest_params: 回測時間範圍和設定
  - strategy_params: 交易策略參數
  - output_params: 輸出格式設定
        """
    )

    parser.add_argument(
        '--config',
        type=str,
        default='config.yml',
        help='配置文件路徑 (預設: config.yml)'
    )

    args = parser.parse_args()

    print("🚀 反轉策略未來路徑分析器啟動")
    print("="*60)

    # === 讀取配置文件 ===
    try:
        config = load_config(args.config)
    except Exception as e:
        print(f"❌ 無法讀取配置文件，程式終止")
        exit(1)

    # === 從配置中提取參數 ===
    simulation_params = config.get('simulation_params', {})
    backtest_params = config.get('backtest_params', {})
    strategy_params = config.get('strategy_params', {})
    output_params = config.get('output_params', {})
    advanced_params = config.get('advanced_params', {})

    # 模擬參數
    NUM_SIMULATIONS = simulation_params.get('num_simulations', 2000)
    NUM_FUTURE_DAYS = simulation_params.get('num_future_days', 60)
    PROFIT_TARGET_PCT = simulation_params.get('profit_target_pct', 0.20)
    RISK_LIMIT_PCT = simulation_params.get('risk_limit_pct', 0.15)
    INITIAL_CAPITAL = simulation_params.get('initial_capital', 100000)

    # 設定隨機種子（如果指定）
    random_seed = advanced_params.get('random_seed')
    if random_seed is not None:
        np.random.seed(random_seed)
        print(f"🎲 設定隨機種子: {random_seed}")

    # 設定字體（從配置讀取）
    font_family = output_params.get('font_family', ['Arial Unicode MS', 'SimHei', 'DejaVu Sans'])
    plt.rcParams['font.sans-serif'] = font_family

    print(f"📋 分析參數設定:")
    print(f"   配置文件: {args.config}")
    print(f"   模擬次數: {NUM_SIMULATIONS:,}")
    print(f"   未來預測天數: {NUM_FUTURE_DAYS}")
    print(f"   獲利目標: {PROFIT_TARGET_PCT:.1%}")
    print(f"   風險底線: {RISK_LIMIT_PCT:.1%}")
    print(f"   起始資金: {INITIAL_CAPITAL:,} 點")
    print()

    # === 創建反轉策略配置 ===
    print("⚙️  從配置文件創建反轉策略配置...")

    try:
        # 🚀 【重構】使用與 rev_strategy_core 兼容的配置
        strategy_config = create_rev_core_compatible_config()
        print("✅ 策略配置創建完成（使用兼容配置）")

        # 顯示策略配置摘要
        print(f"📊 策略配置摘要:")
        print(f"   交易口數: {strategy_config.trade_size_in_lots}")
        print(f"   交易方向: {strategy_config.trading_direction}")
        print(f"   區間過濾: {'啟用' if strategy_config.range_filter.use_range_size_filter else '停用'}")
        if strategy_config.range_filter.use_range_size_filter:
            print(f"   區間上限: {strategy_config.range_filter.max_range_points} 點")
        print(f"   風險管理: {'啟用' if strategy_config.risk_config.use_risk_filter else '停用'}")
        print(f"   各口設定: {len(strategy_config.lot_rules)} 口交易規則")

    except Exception as e:
        print(f"❌ 創建策略配置失敗: {e}")
        exit(1)

    # === 執行原始回測 ===
    print("\n📊 步驟1: 執行原始回測以獲取歷史每日損益...")

    try:
        # 初始化數據庫連接
        use_sqlite = backtest_params.get('use_sqlite', True)
        if use_sqlite:
            import sqlite_connection
            sqlite_connection.init_sqlite_connection()
            print("✅ SQLite連接初始化成功")
        else:
            from app_setup import init_all_db_pools
            init_all_db_pools()
            print("✅ PostgreSQL連線池初始化成功")

        # 從配置中提取回測參數
        start_date = backtest_params.get('start_date', '2024-11-04')
        end_date = backtest_params.get('end_date', '2025-06-28')
        range_start_time = backtest_params.get('range_start_time', '08:46')
        range_end_time = backtest_params.get('range_end_time', '08:47')
        silent_mode = backtest_params.get('silent_mode', False)
        enable_console_log = backtest_params.get('enable_console_log', True)

        print(f"📅 回測參數:")
        print(f"   時間範圍: {start_date} 至 {end_date}")
        print(f"   開盤區間: {range_start_time} - {range_end_time}")
        print(f"   數據源: {'SQLite' if use_sqlite else 'PostgreSQL'}")

        # 執行回測
        backtest_results = run_rev_backtest(
            config=strategy_config,
            start_date=start_date,
            end_date=end_date,
            silent=silent_mode,
            range_start_time=range_start_time,
            range_end_time=range_end_time,
            enable_console_log=enable_console_log
        )

        print(f"✅ 回測完成")
        print(f"   總損益: {backtest_results['total_pnl']:.2f} 點")
        print(f"   最大回撤: {backtest_results['max_drawdown']:.2f} 點")
        print(f"   交易次數: {backtest_results['total_trades']}")
        print(f"   勝率: {backtest_results['win_rate']:.1%}")
        print(f"   每日損益樣本數: {len(backtest_results['daily_pnl_list'])}")

        # 檢查是否有足夠的歷史數據
        if len(backtest_results['daily_pnl_list']) < 10:
            print("❌ 歷史數據不足，無法進行可靠的未來路徑分析")
            print("   建議增加回測時間範圍或檢查數據源")
            exit(1)

    except Exception as e:
        print(f"❌ 回測執行失敗: {e}")
        print("   請檢查數據庫連接和配置")
        exit(1)

    # === 執行蒙地卡羅模擬 ===
    print(f"\n🎲 步驟2: 執行蒙地卡羅模擬...")

    try:
        # 轉換每日損益為Decimal列表
        historical_daily_pnl = [Decimal(str(pnl)) for pnl in backtest_results['daily_pnl_list']]

        # 執行模擬
        all_simulation_paths = rev_simulate_future_paths(
            historical_daily_pnl=historical_daily_pnl,
            num_simulations=NUM_SIMULATIONS,
            num_future_days=NUM_FUTURE_DAYS,
            initial_capital=INITIAL_CAPITAL
        )

        print("✅ 蒙地卡羅模擬完成")

    except Exception as e:
        print(f"❌ 蒙地卡羅模擬失敗: {e}")
        exit(1)

    # === 分析與視覺化 ===
    print(f"\n📈 步驟3: 分析與視覺化未來路徑...")

    try:
        # 從配置中創建報告目錄
        base_report_dir = output_params.get('base_report_dir', 'future_path_reports')
        use_timestamp_folder = output_params.get('use_timestamp_folder', True)

        if use_timestamp_folder:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            report_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                                     base_report_dir,
                                     f"future_path_analysis_{timestamp}")
        else:
            report_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), base_report_dir)

        os.makedirs(report_dir, exist_ok=True)

        # 執行分析（使用配置參數）
        analysis_results = analyze_and_plot_future_paths(
            all_paths=all_simulation_paths,
            initial_capital=INITIAL_CAPITAL,
            profit_target_pct=PROFIT_TARGET_PCT,
            risk_limit_pct=RISK_LIMIT_PCT,
            output_dir=report_dir,
            chart_config=output_params  # 傳遞圖表配置
        )

        print("✅ 分析與視覺化完成")
        print(f"📁 報告保存位置: {report_dir}")

    except Exception as e:
        print(f"❌ 分析與視覺化失敗: {e}")
        exit(1)

    # === 生成總結報告 ===
    print(f"\n📝 生成總結報告...")

    try:
        summary_filename = output_params.get('summary_filename', 'analysis_summary.txt')
        report_file = os.path.join(report_dir, summary_filename)

        # 確保策略配置和回測參數可用於報告生成
        with open(report_file, 'w', encoding='utf-8') as f:
            f.write("反轉策略未來路徑分析報告\n")
            f.write("="*60 + "\n")
            f.write(f"生成時間: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
            f.write(f"分析期間: {backtest_params.get('start_date', '2024-11-04')} 至 {backtest_params.get('end_date', '2025-06-28')}\n")
            f.write(f"總交易日數: {len(backtest_results['daily_pnl_list'])} 天\n\n")

            f.write("📋 策略配置：\n")
            f.write(f"   • 回測時間區間：{backtest_params.get('start_date', '2024-11-04')} 至 {backtest_params.get('end_date', '2025-06-28')}\n")
            f.write(f"   • 開盤區間時間：{backtest_params.get('range_start_time', '08:46')} 至 {backtest_params.get('range_end_time', '08:47')}\n")
            f.write(f"   • 交易口數：{strategy_config.trade_size_in_lots}\n")
            f.write(f"   • 交易方向：{strategy_config.trading_direction}\n")
            f.write(f"   • 停損類型：{strategy_config.stop_loss_type.name if hasattr(strategy_config.stop_loss_type, 'name') else strategy_config.stop_loss_type}\n")

            # 區間過濾信息
            if strategy_config.range_filter.use_range_size_filter:
                f.write(f"   • 區間過濾：啟用 (上限: {strategy_config.range_filter.max_range_points} 點)\n")
            else:
                f.write(f"   • 區間過濾：停用\n")

            # 各口設定詳細信息
            f.write(f"   • 各口設定：\n")
            for i, lot_rule in enumerate(strategy_config.lot_rules, 1):
                if lot_rule.use_trailing_stop:
                    activation = float(lot_rule.trailing_activation) if lot_rule.trailing_activation else 0
                    pullback = float(lot_rule.trailing_pullback) * 100 if lot_rule.trailing_pullback else 0
                    f.write(f"     - 第{i}口：{activation:.0f}點觸發，{pullback:.1f}%回撤")
                    if lot_rule.protective_stop_multiplier and lot_rule.protective_stop_multiplier > 1:
                        f.write(f"，{lot_rule.protective_stop_multiplier}倍保護性停損")
                    if lot_rule.fixed_tp_points:
                        f.write(f"，{lot_rule.fixed_tp_points}點固定停利")
                    f.write("\n")
                else:
                    f.write(f"     - 第{i}口：固定停損停利模式\n")
            f.write("\n")

            f.write("📊 模擬參數：\n")
            f.write(f"   • 模擬次數：{NUM_SIMULATIONS:,} 次\n")
            f.write(f"   • 預測天數：{NUM_FUTURE_DAYS} 天\n")
            f.write(f"   • 起始資金：{INITIAL_CAPITAL:,} 點\n\n")

            # 計算獲利目標和風險底線的絕對值
            profit_target_amount = PROFIT_TARGET_PCT * INITIAL_CAPITAL
            risk_limit_amount = RISK_LIMIT_PCT * INITIAL_CAPITAL
            expected_pnl = analysis_results['final_values_stats']['mean'] - INITIAL_CAPITAL

            f.write("🎯 獲利潛力分析：\n")
            f.write(f"   • 觸及獲利目標 (+{profit_target_amount:.0f}點) 的機率：{analysis_results['profit_target_reached_pct']:.1f}%\n")
            f.write(f"   • 獲利目標：+{profit_target_amount:.0f} 點\n\n")

            f.write("⚠️  風險暴露分析：\n")
            f.write(f"   • 觸及風險底線 ({risk_limit_amount:.0f}點) 的機率：{analysis_results['risk_limit_breached_pct']:.1f}%\n")
            f.write(f"   • 風險底線：{risk_limit_amount:.0f} 點\n\n")

            f.write("📈 最終資金分佈：\n")
            f.write(f"   • 平均最終資金：{analysis_results['final_values_stats']['mean']:,.0f} 點\n")
            f.write(f"   • 標準差：{analysis_results['final_values_stats']['std']:,.0f} 點\n")
            f.write(f"   • 5% 分位數 (悲觀情境)：{analysis_results['final_values_percentiles']['5%']:,.0f} 點\n")
            f.write(f"   • 50% 分位數 (中位數)：{analysis_results['final_values_percentiles']['50%']:,.0f} 點\n")
            f.write(f"   • 95% 分位數 (樂觀情境)：{analysis_results['final_values_percentiles']['95%']:,.0f} 點\n\n")

            f.write(f"💰 預期平均損益：{expected_pnl:+.0f} 點\n")
            f.write("="*60 + "\n")
            f.write(f"報告生成時間：{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")

        print(f"✅ 總結報告已保存: {report_file}")

    except Exception as e:
        print(f"❌ 生成總結報告失敗: {e}")

    print(f"\n🎉 反轉策略未來路徑分析完成！")
    print(f"📁 所有結果已保存到: {report_dir}")
    print("="*60)
