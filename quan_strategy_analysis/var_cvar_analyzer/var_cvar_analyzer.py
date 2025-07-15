#!/usr/bin/env python3
"""
VaR (風險價值) 與 CVaR (條件風險價值) 分析器

本模組提供完整的風險分析功能：
1. 從策略回測中獲取每日損益數據
2. 計算 VaR (Value at Risk) - 風險價值
3. 計算 CVaR (Conditional Value at Risk) - 條件風險價值
4. 生成風險分析報告和視覺化圖表

作者: 量化策略分析團隊
日期: 2025-07-14
"""

import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from datetime import datetime
import os
import sys

# 導入策略核心模組
from strategy_core import StrategyConfig, LotRule, StopLossType, RangeFilter, RiskConfig, StopLossConfig, run_backtest
from decimal import Decimal

# 設定中文字體
plt.rcParams['font.sans-serif'] = ['Arial Unicode MS', 'SimHei', 'DejaVu Sans']
plt.rcParams['axes.unicode_minus'] = False

# 設定 seaborn 樣式
sns.set_style("whitegrid")
sns.set_palette("husl")


def get_historical_pnls(config: StrategyConfig, start_date: str = None, end_date: str = None, silent: bool = True,
                       range_start_time: str = None, range_end_time: str = None) -> list:
    """
    獲取策略的歷史每日損益列表

    這個函式的目的是將「數據獲取」的邏輯與「風險計算」的邏輯清晰地分開。
    它作為回測引擎和風險分析之間的橋樑。

    Args:
        config (StrategyConfig): 策略配置物件，包含所有交易參數
        start_date (str, optional): 回測開始日期，格式 'YYYY-MM-DD'
        end_date (str, optional): 回測結束日期，格式 'YYYY-MM-DD'
        silent (bool): 是否靜默模式，預設為 True 以減少日誌輸出
        range_start_time (str, optional): 開盤區間開始時間，格式 'HH:MM'，如 '10:00'
        range_end_time (str, optional): 開盤區間結束時間，格式 'HH:MM'，如 '10:15'

    Returns:
        list: 每日損益列表，每個元素代表一個交易日的總損益（以點數計算）

    Raises:
        Exception: 當回測執行失敗或無法獲取數據時

    Example:
        >>> config = StrategyConfig(trade_size_in_lots=3)
        >>> daily_pnls = get_historical_pnls(config, '2024-01-01', '2024-12-31',
        ...                                  range_start_time='10:00', range_end_time='10:15')
        >>> print(f"獲取了 {len(daily_pnls)} 個交易日的損益數據")
    """
    try:
        print("🔄 正在執行回測以獲取歷史損益數據...")
        
        # 呼叫策略核心的回測函式
        backtest_result = run_backtest(
            config=config,
            start_date=start_date,
            end_date=end_date,
            silent=silent,
            range_start_time=range_start_time,
            range_end_time=range_end_time
        )
        
        # 從回測結果中提取每日損益列表
        daily_pnl_list = backtest_result.get('daily_pnl_list', [])
        
        if not daily_pnl_list:
            print("⚠️  警告：回測結果中沒有每日損益數據")
            return []
            
        print(f"✅ 成功獲取 {len(daily_pnl_list)} 個交易日的損益數據")
        print(f"📊 損益範圍：{min(daily_pnl_list):.1f} 至 {max(daily_pnl_list):.1f} 點")
        
        return daily_pnl_list
        
    except Exception as e:
        print(f"❌ 獲取歷史損益數據時發生錯誤: {e}")
        raise


def calculate_var(pnl_list: list, confidence_level: float = 0.95) -> float:
    """
    計算風險價值 (Value at Risk, VaR)

    VaR 是衡量在正常市場條件下，在給定信心水準內，
    投資組合在特定時間內可能遭受的最大損失。

    Args:
        pnl_list (list): 每日損益列表
        confidence_level (float): 信心水準，預設 0.95 (95%)

    Returns:
        float: VaR 值（通常為負數，表示潛在損失）

    Note:
        - 對於 95% 信心水準，我們計算第 5 個百分位數
        - VaR 值為負數表示損失，正數表示獲利
        - 例如：VaR = -50 表示有 95% 的信心，單日損失不會超過 50 點
    """
    if not pnl_list:
        return 0.0

    # 轉換為 float 列表以避免 Decimal 類型問題
    float_pnl_list = [float(pnl) for pnl in pnl_list]

    # 轉換為 NumPy 陣列以便計算
    pnl_array = np.array(float_pnl_list)

    # 計算左側尾部的百分位數（損失的百分位數）
    percentile = (1 - confidence_level) * 100
    var_value = np.percentile(pnl_array, percentile)

    return float(var_value)


def calculate_cvar(pnl_list: list, var_value: float) -> float:
    """
    計算條件風險價值 (Conditional Value at Risk, CVaR)

    CVaR 又稱為預期損失 (Expected Shortfall)，
    它計算超過 VaR 閾值的極端損失的平均值。
    CVaR 提供了比 VaR 更保守的風險估計。

    Args:
        pnl_list (list): 每日損益列表
        var_value (float): 已計算的 VaR 值

    Returns:
        float: CVaR 值（預期極端損失的平均值）

    Note:
        - CVaR 總是小於或等於 VaR（更保守的估計）
        - 它回答了「如果發生極端情況，平均損失會是多少？」
        - CVaR 考慮了尾部風險的嚴重程度
    """
    if not pnl_list:
        return 0.0

    # 轉換為 float 列表以避免 Decimal 類型問題
    float_pnl_list = [float(pnl) for pnl in pnl_list]

    # 轉換為 NumPy 陣列
    pnl_array = np.array(float_pnl_list)

    # 篩選出所有小於或等於 VaR 值的極端損失
    extreme_losses = pnl_array[pnl_array <= var_value]

    if len(extreme_losses) == 0:
        return var_value  # 如果沒有極端損失，返回 VaR 值

    # 計算極端損失的平均值
    cvar_value = np.mean(extreme_losses)

    return float(cvar_value)


def print_risk_report(var_value: float, cvar_value: float, confidence_level: float = 0.95,
                     total_days: int = 0, pnl_list: list = None, time_horizon_days: int = 21):
    """
    生成並打印風險分析報告

    Args:
        var_value (float): VaR 值
        cvar_value (float): CVaR 值
        confidence_level (float): 信心水準
        total_days (int): 總交易日數
        pnl_list (list): 損益列表，用於額外統計
        time_horizon_days (int): 週期風險估算的時間長度（交易日），預設21天
    """
    print("\n" + "="*60)
    print("📈 風險價值 (VaR) 與 條件風險價值 (CVaR) 分析報告")
    print("="*60)
    
    # 基本資訊
    print(f"📅 分析期間: {total_days} 個交易日")
    print(f"🎯 信心水準: {confidence_level*100:.0f}%")
    print()
    
    # VaR 分析
    print("🔴 Daily VaR (風險價值):")
    print(f"   數值: {var_value:.1f} 點")
    if var_value < 0:
        print(f"   💡 解讀: 在任何一個交易日，我們有{confidence_level*100:.0f}%的信心，")
        print(f"           虧損不會超過 {abs(var_value):.1f} 點。")
        print(f"           換言之，平均每{int(1/(1-confidence_level))}個交易日，")
        print(f"           可能會有1天虧損會超過這個數字。")
    else:
        print(f"   💡 解讀: 策略在{confidence_level*100:.0f}%的情況下都能獲利")
    print()
    
    # CVaR 分析  
    print("🔴 Daily CVaR (條件風險價值/預期損失):")
    print(f"   數值: {cvar_value:.1f} 點")
    if cvar_value < 0:
        print(f"   💡 解讀: 在發生了那{(1-confidence_level)*100:.0f}%的極端壞情況時，")
        print(f"           我們的平均虧損預計為 {abs(cvar_value):.1f} 點。")
        print(f"           這是對尾部風險更保守的估計。")
    else:
        print(f"   💡 解讀: 即使在極端情況下，策略仍可能獲利")
    print()

    # === 週期風險估算 (基於時間平方根法則) ===
    print("="*60)
    print("📈 週期風險估算 (基於時間平方根法則)")
    print("="*60)
    print(f"週期長度: {time_horizon_days} 個交易日")
    print()

    # 使用時間平方根法則計算週期性 VaR
    import math
    scaled_var = var_value * math.sqrt(time_horizon_days)

    print(f"週期性 VaR ({confidence_level*100:.0f}%): {scaled_var:.1f} 點")
    if scaled_var < 0:
        print(f"   💡 解讀：基於每日風險數據推算，我們有{confidence_level*100:.0f}%的信心，")
        print(f"           在未來{time_horizon_days}個交易日內，策略的累積虧損不會超過 {abs(scaled_var):.1f} 點。")
    else:
        print(f"   💡 解讀：基於每日風險數據推算，策略在{time_horizon_days}個交易日內")
        print(f"           有{confidence_level*100:.0f}%的機會保持獲利狀態。")
    print()

    # 重要提醒和假設說明
    print("⚠️  重要提醒與假設限制:")
    print("   📋 時間平方根法則假設:")
    print("      • 每日報酬率相互獨立且隨機分佈")
    print("      • 波動率在時間內保持相對穩定")
    print("      • 不考慮波動率聚集效應")
    print()
    print("   🎯 實際應用建議:")
    print("      • 此為基於統計模型的簡化估算，具備高度參考價值")
    print("      • 在真實市場中（如金融危機、波動率聚集時）可能存在誤差")
    print("      • 建議結合其他風險管理工具進行綜合評估")
    print("      • 定期重新計算以反映最新的市場條件")
    print()

    # 提供不同時間週期的參考
    common_horizons = [5, 10, 21, 63, 252]  # 1週、2週、1月、1季、1年
    horizon_names = ["1週", "2週", "1月", "1季", "1年"]

    print("📅 常見時間週期的風險估算參考:")
    print("   時間週期    交易日數    週期性VaR")
    print("   " + "-"*35)
    for days, name in zip(common_horizons, horizon_names):
        period_var = var_value * math.sqrt(days)
        print(f"   {name:<8}    {days:>3}天      {period_var:>8.1f} 點")
    print()

    # 額外統計資訊
    if pnl_list:
        pnl_array = np.array(pnl_list)
        print("📊 額外統計資訊:")
        print(f"   平均日損益: {np.mean(pnl_array):.1f} 點")
        print(f"   損益標準差: {np.std(pnl_array):.1f} 點")
        print(f"   最大單日獲利: {np.max(pnl_array):.1f} 點")
        print(f"   最大單日虧損: {np.min(pnl_array):.1f} 點")
        print(f"   獲利交易日: {np.sum(pnl_array > 0)} 天 ({np.sum(pnl_array > 0)/len(pnl_array)*100:.1f}%)")
        print(f"   虧損交易日: {np.sum(pnl_array < 0)} 天 ({np.sum(pnl_array < 0)/len(pnl_array)*100:.1f}%)")
    
    print("="*60)


def create_risk_visualization(pnl_list: list, var_value: float, cvar_value: float, 
                            confidence_level: float = 0.95, save_path: str = None):
    """
    創建風險分析的視覺化圖表
    
    Args:
        pnl_list (list): 每日損益列表
        var_value (float): VaR 值
        cvar_value (float): CVaR 值
        confidence_level (float): 信心水準
        save_path (str): 圖片保存路徑，如果為 None 則顯示圖表
    """
    if not pnl_list:
        print("⚠️  無法創建視覺化：損益列表為空")
        return
        
    # 創建圖表
    plt.figure(figsize=(12, 8))
    
    # 繪製損益分佈直方圖
    plt.hist(pnl_list, bins=50, alpha=0.7, color='skyblue', edgecolor='black', density=True)
    
    # 添加 VaR 和 CVaR 線
    plt.axvline(var_value, color='red', linestyle='--', linewidth=2, 
                label=f'VaR ({confidence_level*100:.0f}%): {var_value:.1f} 點')
    plt.axvline(cvar_value, color='darkred', linestyle='-', linewidth=2,
                label=f'CVaR: {cvar_value:.1f} 點')
    
    # 添加平均值線
    mean_pnl = np.mean(pnl_list)
    plt.axvline(mean_pnl, color='green', linestyle=':', linewidth=2,
                label=f'平均值: {mean_pnl:.1f} 點')
    
    # 設定圖表標題和標籤
    plt.title('每日損益分佈與風險指標\nDaily P&L Distribution with Risk Metrics', 
              fontsize=16, fontweight='bold', pad=20)
    plt.xlabel('每日損益 (點)', fontsize=12)
    plt.ylabel('機率密度', fontsize=12)
    
    # 添加圖例
    plt.legend(fontsize=11, loc='upper right')
    
    # 添加網格
    plt.grid(True, alpha=0.3)
    
    # 調整佈局
    plt.tight_layout()
    
    # 保存或顯示圖表
    if save_path:
        plt.savefig(save_path, dpi=300, bbox_inches='tight')
        print(f"📊 風險分析圖表已保存至: {save_path}")
    else:
        plt.show()
    
    plt.close()


def analyze_trading_direction_risk(base_config, start_date, end_date):
    """
    分析不同交易方向的風險特徵

    Args:
        base_config: 基礎策略配置
        start_date: 開始日期
        end_date: 結束日期

    Returns:
        dict: 包含各交易方向風險分析結果的字典
    """
    directions = ["BOTH", "LONG_ONLY", "SHORT_ONLY"]
    results = {}

    print("\n🔍 正在分析不同交易方向的風險特徵...")
    print("-" * 60)

    for direction in directions:
        print(f"\n📊 分析 {direction} 策略...")

        # 創建該方向的配置
        direction_config = StrategyConfig(
            trade_size_in_lots=base_config.trade_size_in_lots,
            stop_loss_type=base_config.stop_loss_type,
            trading_direction=direction,
            lot_rules=base_config.lot_rules,
            range_filter=base_config.range_filter
        )

        # 獲取該方向的損益數據
        daily_pnl_list = get_historical_pnls(
            config=direction_config,
            start_date=start_date,
            end_date=end_date,
            silent=True,
            range_start_time="08:58",
            range_end_time="09:02"
        )

        if daily_pnl_list:
            # 計算風險指標
            var_value = calculate_var(daily_pnl_list, 0.95)
            cvar_value = calculate_cvar(daily_pnl_list, var_value)

            # 基本統計
            pnl_array = np.array([float(pnl) for pnl in daily_pnl_list])

            results[direction] = {
                'daily_pnl_list': daily_pnl_list,
                'var': var_value,
                'cvar': cvar_value,
                'mean_pnl': np.mean(pnl_array),
                'std_pnl': np.std(pnl_array),
                'max_profit': np.max(pnl_array),
                'max_loss': np.min(pnl_array),
                'win_rate': np.sum(pnl_array > 0) / len(pnl_array) * 100,
                'total_days': len(daily_pnl_list)
            }

            print(f"   交易日數: {len(daily_pnl_list)}")
            print(f"   VaR (95%): {var_value:.1f} 點")
            print(f"   CVaR: {cvar_value:.1f} 點")
            print(f"   平均日損益: {np.mean(pnl_array):.1f} 點")
            print(f"   勝率: {np.sum(pnl_array > 0) / len(pnl_array) * 100:.1f}%")
        else:
            print(f"   ⚠️ {direction} 策略無交易數據")
            results[direction] = None

    return results


if __name__ == '__main__':
    """
    主執行區塊 - 執行完整的 VaR/CVaR 分析流程
    """
    print("🚀 VaR/CVaR 風險分析器啟動")
    print("="*50)

    try:
        # === 步驟 1: 創建策略配置 ===
        print("📋 步驟 1: 設定策略配置")

        # === 交易方向設定 ===
        # 可選擇：
        # "LONG_ONLY"  - 只做多（只有多方訊號出現才進場）
        # "SHORT_ONLY" - 只做空（只有空方訊號出現才進場）
        # "BOTH"       - 多空都做（預設）
        trading_direction = "LONG_ONLY"  # 🔧 在此修改交易方向 BOTH LONG_ONLY SHORT_ONLY

        # 創建一個標準的3口策略配置（根據用戶偏好設定）
        config = StrategyConfig(
            trade_size_in_lots=3,
            stop_loss_type=StopLossType.RANGE_BOUNDARY,
            trading_direction=trading_direction,  # 🚀 新增交易方向控制
            lot_rules=[
                # 第1口：15點觸發，10%回撤
                LotRule(
                    use_trailing_stop=True,
                    fixed_tp_points=None,
                    trailing_activation=Decimal('20'),
                    trailing_pullback=Decimal('0.10')
                ),
                # 第2口：40點觸發，10%回撤，2倍保護
                LotRule(
                    use_trailing_stop=True,
                    fixed_tp_points=None,
                    trailing_activation=Decimal('30'),
                    trailing_pullback=Decimal('0.10'),
                    protective_stop_multiplier=Decimal('2')
                ),
                # 第3口：41點觸發，20%回撤，2倍保護
                LotRule(
                    use_trailing_stop=True,
                    fixed_tp_points=None,
                    trailing_activation=Decimal('40'),
                    trailing_pullback=Decimal('0.20'),
                    protective_stop_multiplier=Decimal('2')
                )
            ],
            # 使用160點區間過濾（用戶偏好設定）
            range_filter=RangeFilter(
                use_range_size_filter=True,
                max_range_points=Decimal('160')
            )
        )

        # 根據交易方向顯示不同的策略描述
        direction_desc = {
            "LONG_ONLY": "只做多策略",
            "SHORT_ONLY": "只做空策略",
            "BOTH": "多空雙向策略"
        }

        print(f"✅ 策略配置完成：3口多層次移動停利策略 ({direction_desc.get(trading_direction, trading_direction)})")
        print(f"   - 交易方向：{trading_direction}")
        print(f"   - 第1口：20點觸發，10%回撤")
        print(f"   - 第2口：40點觸發，10%回撤，2倍保護")
        print(f"   - 第3口：50點觸發，20%回撤，2倍保護")
        print(f"   - 區間過濾：最大160點")
        print()

        # === 步驟 2: 獲取歷史損益數據 ===
        print("📊 步驟 2: 獲取歷史損益數據")

        # 使用用戶驗證的日期範圍
        start_date = "2024-11-04"
        end_date = "2025-06-28"

        print(f"📅 分析期間：{start_date} 至 {end_date}")

        daily_pnl_list = get_historical_pnls(
            config=config,
            start_date=start_date,
            end_date=end_date,
            silent=True,  # 靜默模式減少日誌輸出
            range_start_time="10:00",  # 修改開盤區間開始時間
            range_end_time="10:15"     # 修改開盤區間結束時間
        )

        # 檢查數據有效性
        if not daily_pnl_list:
            print("❌ 錯誤：無法獲取有效的損益數據")
            print("   請檢查：")
            print("   1. 數據庫連接是否正常")
            print("   2. 指定的日期範圍是否包含交易數據")
            print("   3. 策略配置是否正確")
            sys.exit(1)

        print(f"✅ 成功獲取 {len(daily_pnl_list)} 個交易日的損益數據")
        print()

        # === 步驟 3: 計算風險指標 ===
        print("🧮 步驟 3: 計算風險指標")

        # 設定信心水準
        confidence_level = 0.95  # 95% 信心水準

        # 計算 VaR
        print("   正在計算 VaR (風險價值)...")
        var_value = calculate_var(daily_pnl_list, confidence_level)

        # 計算 CVaR
        print("   正在計算 CVaR (條件風險價值)...")
        cvar_value = calculate_cvar(daily_pnl_list, var_value)

        print("✅ 風險指標計算完成")
        print()

        # === 步驟 4: 生成風險報告 ===
        print("📋 步驟 4: 生成風險分析報告")

        print_risk_report(
            var_value=var_value,
            cvar_value=cvar_value,
            confidence_level=confidence_level,
            total_days=len(daily_pnl_list),
            pnl_list=daily_pnl_list,
            time_horizon_days=21  # 預設21個交易日（約1個月）
        )

        # === 步驟 5: 創建視覺化圖表 ===
        print("\n📊 步驟 5: 創建風險分析視覺化")

        # 生成時間戳
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

        # 創建當次分析的專屬資料夾
        analysis_folder = f"var_cvar_analysis_{timestamp}"
        reports_dir = os.path.join("var_cvar_reports", analysis_folder)
        os.makedirs(reports_dir, exist_ok=True)

        print(f"📁 創建分析資料夾: {reports_dir}")

        # 創建圖表文件名
        chart_filename = f"risk_distribution_chart.png"
        chart_path = os.path.join(reports_dir, chart_filename)

        # 生成視覺化圖表
        create_risk_visualization(
            pnl_list=daily_pnl_list,
            var_value=var_value,
            cvar_value=cvar_value,
            confidence_level=confidence_level,
            save_path=chart_path
        )

        # === 步驟 6: 生成文字報告文件 ===
        print("📄 步驟 6: 保存分析報告")

        report_filename = f"analysis_report.txt"
        report_path = os.path.join(reports_dir, report_filename)

        # 將報告內容寫入文件
        with open(report_path, 'w', encoding='utf-8') as f:
            f.write("VaR/CVaR 風險分析報告\n")
            f.write("="*60 + "\n")
            f.write(f"生成時間: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
            f.write(f"分析期間: {start_date} 至 {end_date}\n")
            f.write(f"總交易日數: {len(daily_pnl_list)} 天\n")
            f.write(f"信心水準: {confidence_level*100:.0f}%\n\n")

            f.write("策略配置:\n")
            f.write(f"- 交易口數: {config.trade_size_in_lots} 口\n")
            f.write(f"- 交易方向: {config.trading_direction}\n")
            f.write(f"- 停損類型: {config.stop_loss_type.name} (區間邊緣停損)\n")
            f.write(f"- 開盤區間時間: 10:00-10:15\n")
            f.write(f"- 區間過濾: {'啟用' if config.range_filter.use_range_size_filter else '停用'}\n")
            if config.range_filter.use_range_size_filter:
                f.write(f"- 最大區間: {config.range_filter.max_range_points} 點\n")

            # 添加口數規則詳細信息
            f.write("- 口數規則:\n")
            for i, lot_rule in enumerate(config.lot_rules, 1):
                activation = float(lot_rule.trailing_activation) if lot_rule.trailing_activation else 0
                pullback = float(lot_rule.trailing_pullback) * 100 if lot_rule.trailing_pullback else 0
                f.write(f"  第{i}口: {activation:.0f}點觸發, {pullback:.0f}%回撤")
                if lot_rule.protective_stop_multiplier and lot_rule.protective_stop_multiplier > 1:
                    f.write(f", {lot_rule.protective_stop_multiplier}倍保護")
                f.write("\n")
            f.write("\n")

            f.write("風險指標:\n")
            f.write(f"- VaR (95%): {var_value:.2f} 點\n")
            f.write(f"- CVaR: {cvar_value:.2f} 點\n\n")

            # 週期風險估算
            import math
            time_horizon_days = 21  # 預設21個交易日
            scaled_var = var_value * math.sqrt(time_horizon_days)
            f.write("週期風險估算 (基於時間平方根法則):\n")
            f.write(f"- 週期長度: {time_horizon_days} 個交易日\n")
            f.write(f"- 週期性 VaR (95%): {scaled_var:.2f} 點\n")
            f.write(f"- 估算說明: 基於每日VaR使用時間平方根法則推算\n")
            f.write(f"- 重要提醒: 此為統計模型簡化估算，實際市場可能存在誤差\n\n")

            # 基本統計
            pnl_array = np.array(daily_pnl_list)
            f.write("基本統計:\n")
            f.write(f"- 平均日損益: {np.mean(pnl_array):.2f} 點\n")
            f.write(f"- 標準差: {np.std(pnl_array):.2f} 點\n")
            f.write(f"- 最大獲利: {np.max(pnl_array):.2f} 點\n")
            f.write(f"- 最大虧損: {np.min(pnl_array):.2f} 點\n")
            f.write(f"- 獲利天數: {np.sum(pnl_array > 0)} 天\n")
            f.write(f"- 虧損天數: {np.sum(pnl_array < 0)} 天\n")
            f.write(f"- 勝率: {np.sum(pnl_array > 0)/len(pnl_array)*100:.1f}%\n")

        print(f"✅ 分析報告已保存至: {report_path}")

        # === 完成總結 ===
        print("\n🎉 VaR/CVaR 風險分析完成！")
        print("="*50)
        print("📁 分析結果已保存至專屬資料夾:")
        print(f"   � 資料夾: {reports_dir}")
        print(f"   �📊 視覺化圖表: {chart_filename}")
        print(f"   📄 分析報告: {report_filename}")
        print()
        print("💡 風險管理建議:")
        if var_value < 0:
            print(f"   - 建議設定每日風險限額不超過 {abs(var_value):.0f} 點")
            print(f"   - 極端情況下可能面臨 {abs(cvar_value):.0f} 點的平均損失")
        print("   - 定期檢視風險指標，適時調整策略參數")
        print("   - 考慮在極端市場條件下暫停交易")

        # === 步驟 7: 交易方向比較分析（可選） ===
        print("\n🔄 步驟 7: 交易方向比較分析")

        # 執行不同交易方向的風險比較
        direction_results = analyze_trading_direction_risk(config, start_date, end_date)

        # 生成比較報告
        print("\n📊 交易方向風險比較總結:")
        print("=" * 60)
        print(f"{'方向':<12} {'交易日':<8} {'VaR(95%)':<10} {'CVaR':<10} {'平均損益':<10} {'勝率':<8}")
        print("-" * 60)

        for direction, result in direction_results.items():
            if result:
                print(f"{direction:<12} {result['total_days']:<8} {result['var']:<10.1f} "
                      f"{result['cvar']:<10.1f} {result['mean_pnl']:<10.1f} {result['win_rate']:<8.1f}%")
            else:
                print(f"{direction:<12} {'無數據':<8} {'-':<10} {'-':<10} {'-':<10} {'-':<8}")

        print("=" * 60)
        print("💡 方向選擇建議:")

        # 找出最佳風險調整後收益的方向
        best_direction = None
        best_ratio = float('-inf')

        for direction, result in direction_results.items():
            if result and result['std_pnl'] > 0:
                # 計算夏普比率的簡化版本（平均收益/標準差）
                ratio = result['mean_pnl'] / result['std_pnl']
                if ratio > best_ratio:
                    best_ratio = ratio
                    best_direction = direction

        if best_direction:
            print(f"   - 風險調整後收益最佳: {best_direction}")

        # VaR 最小的方向
        valid_results = [(d, r) for d, r in direction_results.items() if r]
        if valid_results:
            min_var_direction = min(valid_results, key=lambda x: abs(x[1]['var']))
            print(f"   - VaR 風險最小: {min_var_direction[0]} (VaR: {min_var_direction[1]['var']:.1f})")

        print(f"\n📋 完整路徑:")
        print(f"   {os.path.abspath(chart_path)}")
        print(f"   {os.path.abspath(report_path)}")

    except KeyboardInterrupt:
        print("\n⚠️  用戶中斷執行")
        sys.exit(0)
    except Exception as e:
        print(f"\n❌ 執行過程中發生錯誤: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
