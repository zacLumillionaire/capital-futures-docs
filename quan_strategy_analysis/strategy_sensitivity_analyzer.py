"""
策略敏感度分析器 - 使用 SALib 進行 Sobol 敏感度分析

🎯 腳本目的：
    這個腳本能夠利用 SALib 函式庫，對 Profit-Funded Risk 多口交易策略進行 Sobol 敏感度分析，
    找出在特定時間區段內對最大回撤（MDD）影響最大的參數。

🚀 主要功能：
    1. 重構原始回測程式，使其可被 SALib 重複呼叫
    2. 定義參數空間，包含 7 個數值型參數
    3. 分別對三種交易方向（多頭、空頭、雙向）進行敏感度分析
    4. 生成詳細的敏感度分析報告

📊 分析參數：
    - lot1_trigger: 第1口觸發點 (10-30 點)
    - lot1_pullback: 第1口回檔百分比 (5%-30%)
    - lot2_trigger: 第2口觸發點 (25-60 點)
    - lot2_pullback: 第2口回檔百分比 (5%-30%)
    - lot3_trigger: 第3口觸發點 (40-80 點)
    - lot3_pullback: 第3口回檔百分比 (10%-40%)
    - protection_multiplier: 保護性停損倍數 (1.0-3.0 倍)

🔧 如何執行：
    python strategy_sensitivity_analyzer.py

📈 如何解讀結果：
    ST (總敏感度指數)：
        - 代表一個參數對模型輸出(負MDD)的總貢獻度
        - 包含參數自身的直接影響以及與其他參數的交互作用影響
        - ST值越高的參數，是影響MDD的關鍵因子，應優先進行優化

    S1 (一階敏感度指數)：
        - 代表參數的直接影響，不包含交互作用
        - S1值高表示該參數單獨對結果有重要影響

    負MDD值：
        - 我們返回 -MDD 來進行最小化優化
        - 負MDD值越大表示MDD越小（回撤越小，策略越穩定）

⚠️ 注意事項：
    1. 確保 stock_data.sqlite 資料庫存在且包含足夠的歷史數據
    2. 樣本數建議從小值（如64）開始測試，確認無誤後再增加
    3. 完整分析可能需要數小時，建議在性能較好的機器上運行

作者：量化分析團隊
日期：2025-07-14
版本：1.0
"""

import logging
import numpy as np
import pandas as pd
from datetime import time, date, datetime
from decimal import Decimal
from dataclasses import dataclass, field
from enum import Enum, auto
from typing import Dict, List, Tuple, Any, Optional
import multiprocessing
import os
import matplotlib.pyplot as plt
import seaborn as sns

# SALib 導入
from SALib.analyze import sobol
from SALib.sample import sobol as sobol_sample  # 新版本使用 sobol.sample

# 導入原始回測模組
import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# 使用 importlib 來處理特殊字符的文件名
import importlib.util
spec = importlib.util.spec_from_file_location("backtest_module", "multi_Profit-Funded Risk_多口.py")
if spec is not None and spec.loader is not None:
    backtest_module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(backtest_module)

    # 從模組中導入需要的類和函數
    StrategyConfig = backtest_module.StrategyConfig
    LotRule = backtest_module.LotRule
    RangeFilter = backtest_module.RangeFilter
    RiskConfig = backtest_module.RiskConfig
    StopLossConfig = backtest_module.StopLossConfig
    StopLossType = backtest_module.StopLossType
    USE_SQLITE = backtest_module.USE_SQLITE
    apply_range_filter = backtest_module.apply_range_filter
    _run_multi_lot_logic = backtest_module._run_multi_lot_logic
else:
    raise ImportError("無法載入回測模組")

if USE_SQLITE:
    import sqlite_connection
else:
    import shared

# 設定日誌
logging.basicConfig(level=logging.INFO, format='[%(asctime)s] %(levelname)s [%(name)s.%(funcName)s:%(lineno)d] %(message)s', datefmt='%Y-%m-%dT%H:%M:%S%z')
logger = logging.getLogger(__name__)

# ==============================================================================
# Task 1: 改造回測程式，使其可被函式呼叫
# ==============================================================================

def calculate_backtest_metrics(config: StrategyConfig, start_date: str, end_date: str, 
                             range_start_time: str, range_end_time: str, silent: bool = True) -> Dict[str, float]:
    """
    執行回測並返回績效指標字典，包含最大回撤(MDD)
    
    Args:
        config: 策略配置
        start_date: 開始日期 (格式: 'YYYY-MM-DD')
        end_date: 結束日期 (格式: 'YYYY-MM-DD')
        range_start_time: 開盤區間開始時間 (格式: 'HH:MM')
        range_end_time: 開盤區間結束時間 (格式: 'HH:MM')
        silent: 是否靜默模式（不輸出日誌）
        
    Returns:
        dict: 包含 total_pnl, max_drawdown, win_rate, total_trades 等指標的字典
    """
    # 處理自定義開盤區間時間
    range_start_hour, range_start_min = map(int, range_start_time.split(':'))
    range_end_hour, range_end_min = map(int, range_end_time.split(':'))
    
    try:
        # 根據配置選擇數據源
        if USE_SQLITE:
            context_manager = sqlite_connection.get_conn_cur_from_sqlite_with_adapter(as_dict=True)
        else:
            context_manager = shared.get_conn_cur_from_pool_b(as_dict=True)

        with context_manager as (conn, cur):
            # 構建SQL查詢
            base_query = "SELECT DISTINCT trade_datetime::date as trade_day FROM stock_prices"
            conditions = ["trade_datetime::date >= %s", "trade_datetime::date <= %s"]
            params = [start_date, end_date]
            
            query = f"{base_query} WHERE {' AND '.join(conditions)} ORDER BY trade_day;"
            cur.execute(query, tuple(params))
            trade_days = [row['trade_day'] for row in cur.fetchall()]
            
            if not silent:
                logger.info(f"🔍 找到 {len(trade_days)} 個交易日進行回測。")
            
            total_pnl, winning_trades, losing_trades = Decimal(0), 0, 0
            cumulative_pnl = Decimal(0)
            peak_pnl = Decimal(0)  # 追蹤累積損益峰值
            max_drawdown = Decimal(0)  # 追蹤最大回撤
            
            # 多空分別統計
            long_pnl, short_pnl = Decimal(0), Decimal(0)
            long_trades, short_trades = 0, 0
            long_wins, short_wins = 0, 0

            for day in trade_days:
                cur.execute("SELECT * FROM stock_prices WHERE trade_datetime::date = %s ORDER BY trade_datetime;", (day,))
                day_session_candles = [c for c in cur.fetchall() if time(8, 45) <= c['trade_datetime'].time() <= time(13, 45)]
                if len(day_session_candles) < 3: 
                    continue

                # 使用自定義的開盤區間時間
                range_times = [time(range_start_hour, range_start_min), time(range_end_hour, range_end_min)]
                candles_range = [c for c in day_session_candles if c['trade_datetime'].time() in range_times]
                if len(candles_range) != 2:
                    continue

                range_high, range_low = max(c['high_price'] for c in candles_range), min(c['low_price'] for c in candles_range)

                # 套用區間過濾濾網
                range_passed, range_msg = apply_range_filter(config, range_high, range_low, day)
                if not range_passed:
                    continue

                # 交易開始時間設為開盤區間結束後1分鐘
                trade_start_hour = range_end_hour
                trade_start_min = range_end_min + 1
                if trade_start_min >= 60:
                    trade_start_hour += 1
                    trade_start_min -= 60

                trade_candles = [c for c in day_session_candles if c['trade_datetime'].time() >= time(trade_start_hour, trade_start_min)]

                # 執行交易邏輯
                day_pnl, trade_direction = _run_multi_lot_logic(day_session_candles, trade_candles, config, range_high, range_low)

                if day_pnl != 0:
                    is_long_trade = (trade_direction == 'LONG')

                    if day_pnl > 0:
                        winning_trades += 1
                        if is_long_trade: 
                            long_wins += 1
                        else: 
                            short_wins += 1
                    else:
                        losing_trades += 1

                    # 更新多空統計
                    if is_long_trade:
                        long_trades += 1
                        long_pnl += day_pnl
                    else:
                        short_trades += 1
                        short_pnl += day_pnl

                total_pnl += day_pnl
                cumulative_pnl += day_pnl
                
                # 🚀 計算最大回撤
                if cumulative_pnl > peak_pnl:
                    peak_pnl = cumulative_pnl
                
                current_drawdown = peak_pnl - cumulative_pnl
                if current_drawdown > max_drawdown:
                    max_drawdown = current_drawdown

            # 計算統計數據
            trade_count = winning_trades + losing_trades
            win_rate = (winning_trades / trade_count) if trade_count > 0 else 0
            long_win_rate = (long_wins / long_trades) if long_trades > 0 else 0
            short_win_rate = (short_wins / short_trades) if short_trades > 0 else 0

            return {
                'total_pnl': float(total_pnl),
                'max_drawdown': float(max_drawdown),  # 🚀 關鍵：返回MDD
                'long_pnl': float(long_pnl),
                'short_pnl': float(short_pnl),
                'total_trades': trade_count,
                'long_trades': long_trades,
                'short_trades': short_trades,
                'winning_trades': winning_trades,
                'losing_trades': losing_trades,
                'long_wins': long_wins,
                'short_wins': short_wins,
                'win_rate': win_rate,
                'long_win_rate': long_win_rate,
                'short_win_rate': short_win_rate,
                'trade_days': len(trade_days)
            }

    except Exception as e:
        if not silent:
            logger.error(f"❌ 執行回測時發生錯誤: {e}", exc_info=True)
        return {
            'total_pnl': 0.0, 'max_drawdown': 0.0, 'long_pnl': 0.0, 'short_pnl': 0.0,
            'total_trades': 0, 'long_trades': 0, 'short_trades': 0,
            'winning_trades': 0, 'losing_trades': 0, 'long_wins': 0, 'short_wins': 0,
            'win_rate': 0.0, 'long_win_rate': 0.0, 'short_win_rate': 0.0, 'trade_days': 0
        }


def evaluate_for_salib(params: np.ndarray, trading_direction: str, start_date: str, end_date: str, 
                      range_start_time: str, range_end_time: str) -> float:
    """
    SALib 適配器函式：將參數陣列轉換為策略配置並執行回測
    
    Args:
        params: SALib 產生的參數陣列 [lot1_trigger, lot1_pullback, lot2_trigger, lot2_pullback, 
                                   lot3_trigger, lot3_pullback, protection_multiplier]
        trading_direction: 交易方向 ("LONG_ONLY", "SHORT_ONLY", "BOTH")
        start_date: 開始日期
        end_date: 結束日期
        range_start_time: 開盤區間開始時間
        range_end_time: 開盤區間結束時間
        
    Returns:
        float: 負MDD值（用於最小化優化）
    """
    try:
        # 臨時設置日誌級別為 WARNING 以抑制 INFO 級別的交易日誌
        original_level = logging.getLogger().level
        logging.getLogger().setLevel(logging.WARNING)

        # 解析參數
        lot1_trigger, lot1_pullback, lot2_trigger, lot2_pullback, lot3_trigger, lot3_pullback, protection_multiplier = params

        # 創建策略配置
        lot_rules = [
            LotRule(
                use_trailing_stop=True,
                trailing_activation=Decimal(str(lot1_trigger)),
                trailing_pullback=Decimal(str(lot1_pullback))
            ),
            LotRule(
                use_trailing_stop=True,
                trailing_activation=Decimal(str(lot2_trigger)),
                trailing_pullback=Decimal(str(lot2_pullback)),
                protective_stop_multiplier=Decimal(str(protection_multiplier))
            ),
            LotRule(
                use_trailing_stop=True,
                trailing_activation=Decimal(str(lot3_trigger)),
                trailing_pullback=Decimal(str(lot3_pullback)),
                protective_stop_multiplier=Decimal(str(protection_multiplier))
            )
        ]

        config = StrategyConfig(
            trade_size_in_lots=3,
            stop_loss_type=StopLossType.RANGE_BOUNDARY,
            lot_rules=lot_rules,
            trading_direction=trading_direction,
            range_filter=RangeFilter(),  # 使用預設值
            risk_config=RiskConfig(),    # 使用預設值
            stop_loss_config=StopLossConfig()  # 使用預設值
        )

        # 執行回測
        result = calculate_backtest_metrics(config, start_date, end_date, range_start_time, range_end_time, silent=True)

        # 恢復原始日誌級別
        logging.getLogger().setLevel(original_level)

        # 返回負MDD（用於最小化優化）
        mdd = result['max_drawdown']
        return -mdd

    except Exception as e:
        # 恢復原始日誌級別
        logging.getLogger().setLevel(original_level)

        # 記錄錯誤的參數組合和錯誤訊息
        param_str = f"[{lot1_trigger:.2f}, {lot1_pullback:.3f}, {lot2_trigger:.2f}, {lot2_pullback:.3f}, {lot3_trigger:.2f}, {lot3_pullback:.3f}, {protection_multiplier:.2f}]"
        logger.error(f"❌ SALib 評估函式錯誤: {e} | 錯誤參數: {param_str} | 交易方向: {trading_direction}")
        return -999999.0  # 返回極大的負值表示失敗


# ==============================================================================
# Task 2: 定義SALib問題與參數空間
# ==============================================================================

# 定義 SALib 問題空間
problem = {
    'num_vars': 7,
    'names': [
        'lot1_trigger',      # 第1口觸發點
        'lot1_pullback',     # 第1口回檔百分比
        'lot2_trigger',      # 第2口觸發點
        'lot2_pullback',     # 第2口回檔百分比
        'lot3_trigger',      # 第3口觸發點
        'lot3_pullback',     # 第3口回檔百分比
        'protection_multiplier'  # 保護性停損倍數
    ],
    'bounds': [
        [10, 30],      # lot1_trigger: 10-30 點
        [0.05, 0.30],  # lot1_pullback: 5%-30%
        [25, 60],      # lot2_trigger: 25-60 點
        [0.05, 0.30],  # lot2_pullback: 5%-30%
        [40, 80],      # lot3_trigger: 40-80 點
        [0.10, 0.40],  # lot3_pullback: 10%-40%
        [1.0, 3.0]     # protection_multiplier: 1.0-3.0 倍
    ]
}

# 交易方向列表（分類變數）
TRADING_DIRECTIONS = ['LONG_ONLY', 'SHORT_ONLY', 'BOTH']


# ==============================================================================
# 並行處理輔助函數
# ==============================================================================

def evaluate_single_param_set(args):
    """
    單個參數組合的評估函數（用於並行處理）

    Args:
        args: tuple containing (params, trading_direction, start_date, end_date, range_start_time, range_end_time)

    Returns:
        float: 負MDD值
    """
    # 在每個子進程中設置日誌級別為 WARNING 以抑制交易日誌
    import logging
    logging.getLogger().setLevel(logging.WARNING)

    params, trading_direction, start_date, end_date, range_start_time, range_end_time = args
    return evaluate_for_salib(params, trading_direction, start_date, end_date, range_start_time, range_end_time)


class ProgressTracker:
    """進度追蹤器"""
    def __init__(self, total_tasks, update_interval=5):
        self.total_tasks = total_tasks
        self.completed_tasks = 0
        self.update_interval = update_interval  # 每5%更新一次
        self.last_reported_percentage = 0

    def update(self, increment=1):
        """更新進度"""
        self.completed_tasks += increment
        current_percentage = (self.completed_tasks / self.total_tasks) * 100

        # 每5%報告一次進度
        if current_percentage - self.last_reported_percentage >= self.update_interval:
            logger.info(f"   📊 進度更新: {self.completed_tasks}/{self.total_tasks} ({current_percentage:.1f}%)")
            self.last_reported_percentage = current_percentage

        # 完成時報告
        if self.completed_tasks >= self.total_tasks:
            logger.info(f"   ✅ 計算完成: {self.total_tasks}/{self.total_tasks} (100.0%)")


def evaluate_with_progress(args_with_tracker):
    """帶進度追蹤的評估函數"""
    args, tracker = args_with_tracker
    result = evaluate_single_param_set(args)
    tracker.update()
    return result


# 全局進度追蹤器（用於並行處理）
_global_progress_tracker = None

def init_global_progress_tracker(total_tasks):
    """初始化全局進度追蹤器"""
    global _global_progress_tracker
    _global_progress_tracker = ProgressTracker(total_tasks)

def update_global_progress():
    """更新全局進度"""
    global _global_progress_tracker
    if _global_progress_tracker:
        _global_progress_tracker.update()

def evaluate_single_param_set_with_progress(args):
    """帶全局進度追蹤的評估函數"""
    # 在每個子進程中設置日誌級別為 WARNING 以抑制交易日誌
    import logging
    logging.getLogger().setLevel(logging.WARNING)

    result = evaluate_single_param_set(args)
    update_global_progress()
    return result


def create_report_directory():
    """
    創建實驗報告目錄

    Returns:
        str: 報告目錄路徑
    """
    base_dir = "/Users/z/big/my-capital-project/quan_strategy_analysis/SALIB_report"
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    report_dir = os.path.join(base_dir, f"sensitivity_analysis_{timestamp}")

    os.makedirs(report_dir, exist_ok=True)
    logger.info(f"📁 創建報告目錄: {report_dir}")

    return report_dir


def save_sensitivity_plot(df_results, trading_direction, report_dir):
    """
    保存敏感度分析圖表

    Args:
        df_results: 包含敏感度結果的DataFrame
        trading_direction: 交易方向
        report_dir: 報告目錄路徑
    """
    try:
        # 設定中文字體（如果需要）
        plt.rcParams['font.sans-serif'] = ['Arial Unicode MS', 'SimHei', 'DejaVu Sans']
        plt.rcParams['axes.unicode_minus'] = False

        # 按ST值排序（升序，方便繪圖）
        df_plot = df_results.sort_values('ST', ascending=True)

        # 創建圖表
        plt.figure(figsize=(12, 8))
        bars = plt.barh(df_plot['Parameter'], df_plot['ST'], color='skyblue')

        # 設定標題和標籤
        plt.title(f'Sobol 敏感度分析結果 - {trading_direction} 交易方向', fontsize=16, fontweight='bold')
        plt.xlabel('總敏感度指數 (ST)', fontsize=12)
        plt.ylabel('參數', fontsize=12)

        # 添加數值標籤
        for bar, value in zip(bars, df_plot['ST']):
            plt.text(value + 0.01, bar.get_y() + bar.get_height()/2,
                    f'{value:.4f}', va='center', fontsize=10)

        # 調整佈局
        plt.tight_layout()
        plt.grid(axis='x', alpha=0.3)

        # 保存圖片
        plot_path = os.path.join(report_dir, f'sensitivity_{trading_direction}.png')
        plt.savefig(plot_path, dpi=300, bbox_inches='tight')
        logger.info(f"📊 保存敏感度圖表: {plot_path}")

        # 顯示圖表（可選）
        # plt.show()
        plt.close()

    except Exception as e:
        logger.error(f"❌ 保存圖表失敗 ({trading_direction}): {e}")


def save_sensitivity_csv(df_results, trading_direction, report_dir, additional_info=None):
    """
    保存敏感度分析CSV結果

    Args:
        df_results: 包含敏感度結果的DataFrame
        trading_direction: 交易方向
        report_dir: 報告目錄路徑
        additional_info: 額外信息字典
    """
    try:
        # 添加額外信息列
        if additional_info:
            for key, value in additional_info.items():
                df_results[key] = value

        # 保存CSV
        csv_path = os.path.join(report_dir, f'sensitivity_results_{trading_direction}.csv')
        df_results.to_csv(csv_path, index=False, encoding='utf-8-sig')
        logger.info(f"💾 保存敏感度CSV: {csv_path}")

    except Exception as e:
        logger.error(f"❌ 保存CSV失敗 ({trading_direction}): {e}")


# ==============================================================================
# Task 3: 實現主執行流程
# ==============================================================================

def run_sensitivity_analysis(target_time_slot: Tuple[str, str], sample_size: int = 64,
                           start_date: str = "2024-11-04", end_date: str = "2025-06-28",
                           use_parallel: bool = True, num_processes: Optional[int] = None) -> Dict[str, Any]:
    """
    執行完整的敏感度分析流程

    Args:
        target_time_slot: 目標時間區段，例如 ('08:46', '08:47')
        sample_size: SALib 樣本數
        start_date: 回測開始日期
        end_date: 回測結束日期
        use_parallel: 是否使用並行處理
        num_processes: 並行處理核心數（None時自動設定為CPU核心數-4）

    Returns:
        dict: 包含所有交易方向分析結果的字典
    """
    range_start_time, range_end_time = target_time_slot
    results = {}

    # 設定並行處理核心數
    if num_processes is None:
        # 根據您的CPU核心數設定進程數，預設使用4核心
        num_processes = min(4, multiprocessing.cpu_count() - 1)
    if num_processes < 1:
        num_processes = 1

    # 創建報告目錄
    report_dir = create_report_directory()

    logger.info(f"🎯 開始敏感度分析 | 時間區段: {range_start_time}-{range_end_time} | 樣本數: {sample_size}")
    if use_parallel:
        logger.info(f"🔥 使用 {num_processes} 個核心並行計算...")
    else:
        logger.info(f"🔄 使用單核心順序計算...")

    # 初始化數據源
    if USE_SQLITE:
        try:
            sqlite_connection.init_sqlite_connection()
            logger.info("✅ SQLite連接初始化成功。")
        except Exception as e:
            logger.error(f"❌ SQLite連接初始化失敗: {e}")
            return {}
    else:
        try:
            from app_setup import init_all_db_pools
            init_all_db_pools()
            logger.info("✅ PostgreSQL連線池初始化成功。")
        except Exception as e:
            logger.error(f"❌ PostgreSQL連線池初始化失敗: {e}")
            return {}

    # 對每個交易方向分別進行分析
    for trading_direction in TRADING_DIRECTIONS:
        logger.info(f"\n📊 分析交易方向: {trading_direction}")

        try:
            # 1. 生成樣本
            logger.info(f"   🎲 生成 Sobol 樣本...")
            param_values = sobol_sample.sample(problem, N=sample_size)
            logger.info(f"   ✅ 生成了 {len(param_values)} 個參數組合")

            # 2. 執行回測
            logger.info(f"   🔄 執行回測...")
            Y = np.zeros(len(param_values))

            if use_parallel and len(param_values) > 10:  # 只有樣本數足夠大時才使用並行
                # 並行處理
                logger.info(f"   🚀 使用 {num_processes} 核心並行處理...")

                # 創建進度追蹤器
                progress_tracker = ProgressTracker(len(param_values), update_interval=5)

                # 準備參數（不使用進度追蹤的簡單版本）
                args_list = [(params, trading_direction, start_date, end_date, range_start_time, range_end_time)
                           for params in param_values]

                # 使用進程池並行計算
                with multiprocessing.Pool(processes=num_processes) as pool:
                    # 執行並行計算
                    results_list = pool.map(evaluate_single_param_set, args_list)
                    Y = np.array(results_list)

                # 手動更新進度到100%
                logger.info(f"   ✅ 並行計算完成: {len(param_values)}/{len(param_values)} (100.0%)")

            else:
                # 順序處理
                progress_tracker = ProgressTracker(len(param_values), update_interval=5)

                for i, params in enumerate(param_values):
                    Y[i] = evaluate_for_salib(params, trading_direction, start_date, end_date,
                                            range_start_time, range_end_time)

                    # 更新進度（每5%顯示一次）
                    current_percentage = ((i + 1) / len(param_values)) * 100
                    if current_percentage - progress_tracker.last_reported_percentage >= 5:
                        logger.info(f"   📊 進度更新: {i+1}/{len(param_values)} ({current_percentage:.1f}%)")
                        progress_tracker.last_reported_percentage = current_percentage

                # 完成時報告
                logger.info(f"   ✅ 順序計算完成: {len(param_values)}/{len(param_values)} (100.0%)")

            logger.info(f"   ✅ 回測完成，有效結果: {np.sum(Y > -999999)} / {len(Y)}")

            # 🔍 診斷：檢查 Y 值的分佈
            valid_Y = Y[Y > -999999]
            if len(valid_Y) > 0:
                logger.info(f"   📊 MDD 統計: 最小={-valid_Y.max():.2f}, 最大={-valid_Y.min():.2f}, 平均={-valid_Y.mean():.2f}, 標準差={valid_Y.std():.4f}")
                logger.info(f"   📊 唯一值數量: {len(np.unique(valid_Y))}")

                # 檢查是否所有值都相同
                if valid_Y.std() < 1e-10:
                    logger.warning(f"   ⚠️ 警告：所有 MDD 值幾乎相同 ({-valid_Y.mean():.6f})，敏感度分析可能無效")
                    logger.warning(f"   💡 建議：檢查參數範圍是否合理，或增加樣本數")
            else:
                logger.error(f"   ❌ 沒有有效的回測結果！")
                continue

            # 3. 執行 Sobol 分析
            logger.info(f"   📈 執行 Sobol 敏感度分析...")
            Si = sobol.analyze(problem, Y)

            # 4. 格式化結果
            results[trading_direction] = {
                'Si': Si,
                'Y_values': Y,
                'param_values': param_values,
                'valid_results': np.sum(Y > -999999),
                'total_samples': len(Y)
            }

            # 5. 顯示結果摘要
            logger.info(f"   📋 {trading_direction} 敏感度分析結果:")

            # 手動創建 DataFrame（因為新版 SALib 可能沒有 to_df 方法）
            sensitivity_data = {
                'Parameter': problem['names'],
                'S1': Si['S1'],
                'ST': Si['ST']
            }
            df_results = pd.DataFrame(sensitivity_data)

            # 顯示總敏感度指數 (ST) 排序
            st_sorted = df_results.sort_values('ST', ascending=False)
            logger.info(f"   🏆 總敏感度指數 (ST) 排名:")
            for rank, (_, row) in enumerate(st_sorted.iterrows(), 1):
                param_name = row['Parameter']
                logger.info(f"      {rank}. {param_name}: ST={row['ST']:.4f}, S1={row['S1']:.4f}")

            # 6. 保存結果和視覺化
            logger.info(f"   💾 保存分析結果...")

            # 添加額外信息
            additional_info = {
                'Trading_Direction': trading_direction,
                'Sample_Size': sample_size,
                'Time_Slot': f"{range_start_time}-{range_end_time}",
                'Analysis_Date': datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                'Valid_Results': np.sum(Y > -999999),
                'Total_Samples': len(Y)
            }

            # 保存CSV結果
            save_sensitivity_csv(df_results, trading_direction, report_dir, additional_info)

            # 保存視覺化圖表
            save_sensitivity_plot(df_results, trading_direction, report_dir)

        except Exception as e:
            logger.error(f"❌ {trading_direction} 分析失敗: {e}")
            results[trading_direction] = {'error': str(e)}

    return results


if __name__ == '__main__':
    # 設定分析目標
    TARGET_TIME_SLOT = ('11:00', '11:02')  # 目標時間區段
    N = 64  # SALib 樣本數（建議從小值開始測試）

    logger.info("🚀 策略敏感度分析器啟動")
    logger.info(f"📅 分析時間區段: {TARGET_TIME_SLOT[0]} - {TARGET_TIME_SLOT[1]} (開盤區間)")
    logger.info(f"🎲 樣本數: {N}")

    # 執行分析
    analysis_results = run_sensitivity_analysis(
        target_time_slot=TARGET_TIME_SLOT,
        sample_size=N,
        start_date="2024-11-04",
        end_date="2025-06-28",
        use_parallel=True,  # 啟用並行處理
        num_processes=4     # 使用4核心
    )

    # 顯示最終結果摘要
    logger.info("\n" + "="*60)
    logger.info("📊 敏感度分析完整結果摘要")
    logger.info("="*60)

    for direction, result in analysis_results.items():
        if 'error' in result:
            logger.info(f"\n❌ {direction}: 分析失敗 - {result['error']}")
            continue

        logger.info(f"\n📈 {direction} 交易方向結果:")
        logger.info(f"   有效樣本: {result['valid_results']} / {result['total_samples']}")

        # 顯示最重要的參數
        Si = result['Si']
        sensitivity_data = {
            'Parameter': problem['names'],
            'S1': Si['S1'],
            'ST': Si['ST']
        }
        df_results = pd.DataFrame(sensitivity_data)
        top_params = df_results.sort_values('ST', ascending=False).head(3)

        logger.info(f"   🏆 影響MDD最大的前3個參數:")
        for rank, (_, row) in enumerate(top_params.iterrows(), 1):
            param_name = row['Parameter']
            logger.info(f"      {rank}. {param_name}: ST={row['ST']:.4f}")

    logger.info("\n✅ 敏感度分析完成！")
