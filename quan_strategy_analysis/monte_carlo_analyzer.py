#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
蒙地卡羅策略穩健性分析器
Monte Carlo Strategy Robustness Analyzer

這個腳本執行以下分析流程：
1. 使用現有的回測引擎執行標準回測
2. 收集每日損益數據
3. 對每日損益進行數千次隨機重組（蒙地卡羅模擬）
4. 計算每次重組的總損益和最大回撤
5. 視覺化分析結果，評估策略的穩健性

使用方法：
    python monte_carlo_analyzer.py

作者: 量化分析師
日期: 2025-01-14
版本: 1.0
"""

import sys
import os
from decimal import Decimal
from datetime import datetime

# 添加當前目錄到 Python 路徑
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

def create_output_directory():
    """建立輸出資料夾"""
    # 建立主要的 monte_carlo_analyzer 資料夾
    current_dir = os.path.dirname(os.path.abspath(__file__))
    main_output_dir = os.path.join(current_dir, "monte_carlo_analyzer")
    if not os.path.exists(main_output_dir):
        os.makedirs(main_output_dir)
        print(f"📁 建立主要輸出資料夾: {main_output_dir}")

    # 建立以時間戳記命名的子資料夾
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    session_dir = os.path.join(main_output_dir, f"analysis_{timestamp}")
    os.makedirs(session_dir, exist_ok=True)
    print(f"📁 建立分析會話資料夾: {session_dir}")

    return session_dir

def save_analysis_summary(session_dir, original_result, simulation_results, original_mdd):
    """保存分析摘要到文字檔案"""
    summary_file = os.path.join(session_dir, "analysis_summary.txt")

    with open(summary_file, 'w', encoding='utf-8') as f:
        f.write("蒙地卡羅策略穩健性分析報告\n")
        f.write("=" * 50 + "\n")
        f.write(f"分析時間: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")

        # 原始回測結果
        f.write("📊 原始回測結果摘要\n")
        f.write("-" * 30 + "\n")
        f.write(f"總損益: {original_result['total_pnl']:.2f} 點\n")
        f.write(f"多頭損益: {original_result['long_pnl']:.2f} 點\n")
        f.write(f"空頭損益: {original_result['short_pnl']:.2f} 點\n")
        f.write(f"總交易次數: {original_result['total_trades']}\n")
        f.write(f"多頭交易: {original_result['long_trades']}\n")
        f.write(f"空頭交易: {original_result['short_trades']}\n")
        f.write(f"獲利次數: {original_result['winning_trades']}\n")
        f.write(f"虧損次數: {original_result['losing_trades']}\n")
        f.write(f"總勝率: {original_result['win_rate']*100:.2f}%\n")
        f.write(f"多頭勝率: {original_result['long_win_rate']*100:.2f}%\n")
        f.write(f"空頭勝率: {original_result['short_win_rate']*100:.2f}%\n")
        f.write(f"回測交易日數: {original_result['trade_days']}\n")
        f.write(f"有交易的日數: {len(original_result['daily_pnl_list'])}\n")
        f.write(f"估算最大回撤: {original_mdd:.2f} 點\n\n")

        # 蒙地卡羅模擬結果
        if simulation_results and simulation_results['final_pnls']:
            import numpy as np
            pnl_array = np.array(simulation_results['final_pnls'])
            mdd_array = np.array(simulation_results['max_drawdowns'])

            f.write("🎲 蒙地卡羅模擬結果\n")
            f.write("-" * 30 + "\n")
            f.write(f"模擬次數: {len(simulation_results['final_pnls'])}\n")
            f.write(f"總損益平均: {np.mean(pnl_array):.2f} 點\n")
            f.write(f"總損益標準差: {np.std(pnl_array):.2f} 點\n")
            f.write(f"總損益中位數: {np.median(pnl_array):.2f} 點\n")
            f.write(f"總損益5%分位數: {np.percentile(pnl_array, 5):.2f} 點\n")
            f.write(f"總損益95%分位數: {np.percentile(pnl_array, 95):.2f} 點\n\n")

            f.write(f"MDD平均: {np.mean(mdd_array):.2f} 點\n")
            f.write(f"MDD標準差: {np.std(mdd_array):.2f} 點\n")
            f.write(f"MDD中位數: {np.median(mdd_array):.2f} 點\n")
            f.write(f"MDD5%分位數: {np.percentile(mdd_array, 5):.2f} 點\n")
            f.write(f"MDD95%分位數: {np.percentile(mdd_array, 95):.2f} 點\n\n")

            # 穩健性評估
            orig_pnl = float(original_result['total_pnl'])
            pnl_percentile = (np.sum(pnl_array <= orig_pnl) / len(pnl_array)) * 100
            mdd_percentile = (np.sum(mdd_array <= original_mdd) / len(mdd_array)) * 100

            f.write("🎯 策略穩健性評估\n")
            f.write("-" * 30 + "\n")
            f.write(f"原始總損益百分位: {pnl_percentile:.1f}%\n")
            f.write(f"原始MDD百分位: {mdd_percentile:.1f}%\n")

            if pnl_percentile > 50:
                f.write(f"✅ 總損益表現優於隨機重組的 {pnl_percentile:.1f}% 情況\n")
            else:
                f.write(f"⚠️ 總損益表現僅優於隨機重組的 {pnl_percentile:.1f}% 情況\n")

            if mdd_percentile < 50:
                f.write(f"✅ 回撤控制優於隨機重組的 {100-mdd_percentile:.1f}% 情況\n")
            else:
                f.write(f"⚠️ 回撤控制僅優於隨機重組的 {100-mdd_percentile:.1f}% 情況\n")

    print(f"📄 分析摘要已保存: {summary_file}")
    return summary_file

# 導入回測模組
try:
    # 使用 importlib 來導入包含特殊字符的模組
    import importlib.util
    spec = importlib.util.spec_from_file_location(
        "backtest_module",
        "multi_Profit-Funded Risk_多口.py"
    )
    backtest_module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(backtest_module)

    # 從模組中導入需要的類和函數
    StrategyConfig = backtest_module.StrategyConfig
    LotRule = backtest_module.LotRule
    StopLossType = backtest_module.StopLossType
    RangeFilter = backtest_module.RangeFilter
    RiskConfig = backtest_module.RiskConfig
    StopLossConfig = backtest_module.StopLossConfig
    run_backtest = backtest_module.run_backtest

    print("✅ 成功導入回測模組")
except Exception as e:
    print(f"❌ 導入回測模組失敗: {e}")
    print("請確認 'multi_Profit-Funded Risk_多口.py' 檔案存在於當前目錄")
    sys.exit(1)

# 導入蒙地卡羅分析函式
try:
    from monte_carlo_functions import (
        run_monte_carlo_simulation,
        analyze_and_plot_mc_results
    )
    print("✅ 成功導入蒙地卡羅分析模組")
except ImportError as e:
    print(f"❌ 導入蒙地卡羅分析模組失敗: {e}")
    print("請確認 'monte_carlo_functions.py' 檔案存在於當前目錄")
    sys.exit(1)


def create_default_strategy_config() -> StrategyConfig:
    """
    創建預設的策略配置
    
    Returns:
        StrategyConfig: 預設策略配置
    """
    # 根據用戶偏好設定的三口交易策略
    lot_rules = [
        # 第1口：觸發15點，10%回撤
        LotRule(
            use_trailing_stop=True,
            trailing_activation=Decimal('25'),
            trailing_pullback=Decimal('0.10')
        ),
        # 第2口：觸發40點，10%回撤，2倍保護
        LotRule(
            use_trailing_stop=True,
            trailing_activation=Decimal('25'),
            trailing_pullback=Decimal('0.20'),
            protective_stop_multiplier=Decimal('2')
        ),
        # 第3口：觸發41點，20%回撤，2倍保護
        LotRule(
            use_trailing_stop=True,
            trailing_activation=Decimal('45'),
            trailing_pullback=Decimal('0.20'),
            protective_stop_multiplier=Decimal('2')
        )
    ]
    
    config = StrategyConfig(
        trade_size_in_lots=3,
        stop_loss_type=StopLossType.RANGE_BOUNDARY,
        lot_rules=lot_rules,
        trading_direction="BOTH",  # 多空都做
        range_filter=RangeFilter(use_range_size_filter=False),
        risk_config=RiskConfig(use_risk_filter=False),
        stop_loss_config=StopLossConfig(
            stop_loss_type=StopLossType.RANGE_BOUNDARY,
            use_range_midpoint=False
        )
    )
    
    return config


def print_original_backtest_summary(result: dict) -> None:
    """
    印出原始回測結果摘要
    
    Args:
        result: 回測結果字典
    """
    print(f"\n" + "="*60)
    print(f"📊 原始回測結果摘要")
    print(f"="*60)
    
    print(f"💰 損益統計:")
    print(f"   總損益: {result['total_pnl']:.2f} 點")
    print(f"   多頭損益: {result['long_pnl']:.2f} 點")
    print(f"   空頭損益: {result['short_pnl']:.2f} 點")
    
    print(f"\n📈 交易統計:")
    print(f"   總交易次數: {result['total_trades']}")
    print(f"   多頭交易: {result['long_trades']}")
    print(f"   空頭交易: {result['short_trades']}")
    print(f"   獲利次數: {result['winning_trades']}")
    print(f"   虧損次數: {result['losing_trades']}")
    
    print(f"\n🎯 勝率統計:")
    print(f"   總勝率: {result['win_rate']*100:.2f}%")
    print(f"   多頭勝率: {result['long_win_rate']*100:.2f}%")
    print(f"   空頭勝率: {result['short_win_rate']*100:.2f}%")
    
    print(f"\n📅 其他資訊:")
    print(f"   回測交易日數: {result['trade_days']}")
    print(f"   有交易的日數: {len(result['daily_pnl_list'])}")
    
    # 計算簡單的最大回撤（基於每日損益）
    if result['daily_pnl_list']:
        import numpy as np
        cumulative_pnl = np.cumsum([float(pnl) for pnl in result['daily_pnl_list']])
        peak_pnl = np.maximum.accumulate(cumulative_pnl)
        drawdowns = peak_pnl - cumulative_pnl
        max_drawdown = np.max(drawdowns)
        print(f"   估算最大回撤: {max_drawdown:.2f} 點")
    
    print(f"="*60)


def main():
    """
    主執行函式
    """
    print(f"🚀 蒙地卡羅策略穩健性分析器")
    print(f"開始時間: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"="*60)

    # 建立輸出資料夾
    session_dir = create_output_directory()
    
    # 步驟1：設定策略配置
    print(f"\n📋 步驟1：設定策略配置")
    config = create_default_strategy_config()
    print(f"✅ 策略配置完成 - 三口交易策略 (15/40/41點觸發)")
    
    # 步驟2：執行原始回測
    print(f"\n🔄 步驟2：執行原始回測")
    print(f"回測期間: 2024-11-04 至 2025-06-28")
    print(f"開盤區間: 08:46-08:47")
    
    try:
        result = run_backtest(
            config=config,
            start_date="2024-11-04",
            end_date="2025-06-28",
            silent=False,  # 顯示詳細回測過程
            range_start_time="10:15",
            range_end_time="10:30"
        )
        
        if not result or result['total_trades'] == 0:
            print("❌ 回測失敗或沒有交易記錄")
            return
            
        print(f"✅ 原始回測完成")
        
    except Exception as e:
        print(f"❌ 回測執行失敗: {e}")
        return
    
    # 步驟3：印出原始回測摘要
    print_original_backtest_summary(result)
    
    # 檢查是否有足夠的交易數據
    daily_pnl_list = result['daily_pnl_list']
    if len(daily_pnl_list) < 10:
        print(f"⚠️ 警告：交易日數太少 ({len(daily_pnl_list)} 天)，蒙地卡羅模擬可能不夠準確")
        response = input("是否繼續進行模擬？(y/n): ")
        if response.lower() != 'y':
            print("分析中止")
            return
    
    # 步驟4：執行蒙地卡羅模擬
    print(f"\n🎲 步驟3：執行蒙地卡羅模擬")
    num_simulations = 2000
    print(f"模擬次數: {num_simulations}")
    
    try:
        simulation_results = run_monte_carlo_simulation(
            daily_pnl_list=daily_pnl_list,
            num_simulations=num_simulations
        )
        
        if not simulation_results['final_pnls']:
            print("❌ 蒙地卡羅模擬失敗")
            return
            
        print(f"✅ 蒙地卡羅模擬完成")
        
    except Exception as e:
        print(f"❌ 蒙地卡羅模擬失敗: {e}")
        return
    
    # 步驟5：分析與視覺化結果
    print(f"\n📊 步驟4：分析與視覺化結果")
    
    # 計算原始回測的最大回撤
    import numpy as np
    cumulative_pnl = np.cumsum([float(pnl) for pnl in daily_pnl_list])
    peak_pnl = np.maximum.accumulate(cumulative_pnl)
    drawdowns = peak_pnl - cumulative_pnl
    original_max_drawdown = Decimal(str(np.max(drawdowns)))
    
    try:
        analyze_and_plot_mc_results(
            simulation_results=simulation_results,
            original_total_pnl=Decimal(str(result['total_pnl'])),
            original_max_drawdown=original_max_drawdown,
            output_dir=session_dir
        )

        print(f"✅ 分析完成")

    except Exception as e:
        print(f"❌ 結果分析失敗: {e}")
        return

    # 保存分析摘要
    try:
        save_analysis_summary(session_dir, result, simulation_results, float(original_max_drawdown))
        print(f"✅ 分析摘要已保存")
    except Exception as e:
        print(f"⚠️ 保存分析摘要失敗: {e}")

    print(f"\n🎉 蒙地卡羅策略穩健性分析完成！")
    print(f"📁 所有結果已保存至: {session_dir}")
    print(f"結束時間: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")


if __name__ == "__main__":
    main()
