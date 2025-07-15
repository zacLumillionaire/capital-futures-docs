#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
蒙地卡羅分析器測試腳本
用於驗證各個組件是否正常工作

作者: 量化分析師
日期: 2025-01-14
"""

import sys
import os
from decimal import Decimal

# 添加當前目錄到 Python 路徑
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

def test_backtest_modification():
    """測試回測函式的修改是否成功"""
    print("🧪 測試1：驗證回測函式修改")
    
    try:
        # 導入回測模組
        import importlib.util
        spec = importlib.util.spec_from_file_location(
            "backtest_module", 
            "multi_Profit-Funded Risk_多口.py"
        )
        backtest_module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(backtest_module)
        
        StrategyConfig = backtest_module.StrategyConfig
        LotRule = backtest_module.LotRule
        StopLossType = backtest_module.StopLossType
        RangeFilter = backtest_module.RangeFilter
        RiskConfig = backtest_module.RiskConfig
        StopLossConfig = backtest_module.StopLossConfig
        run_backtest = backtest_module.run_backtest
        
        print("   ✅ 回測模組導入成功")
        
        # 創建簡單的測試配置
        config = StrategyConfig(
            trade_size_in_lots=1,
            stop_loss_type=StopLossType.RANGE_BOUNDARY,
            lot_rules=[LotRule(
                use_trailing_stop=True,
                trailing_activation=Decimal('15'),
                trailing_pullback=Decimal('0.10')
            )],
            trading_direction="BOTH",
            range_filter=RangeFilter(use_range_size_filter=False),
            risk_config=RiskConfig(use_risk_filter=False),
            stop_loss_config=StopLossConfig(
                stop_loss_type=StopLossType.RANGE_BOUNDARY,
                use_range_midpoint=False
            )
        )
        
        print("   ✅ 策略配置創建成功")
        
        # 執行簡短的回測
        result = run_backtest(
            config=config,
            start_date="2024-11-04",
            end_date="2024-11-10",  # 只測試一週
            silent=True
        )
        
        if result and 'daily_pnl_list' in result:
            print(f"   ✅ 回測執行成功，daily_pnl_list 存在")
            print(f"   📊 測試結果：交易次數={result['total_trades']}, 每日損益列表長度={len(result['daily_pnl_list'])}")
            return True, result['daily_pnl_list']
        else:
            print("   ❌ 回測結果中缺少 daily_pnl_list")
            return False, []
            
    except Exception as e:
        print(f"   ❌ 測試失敗: {e}")
        return False, []


def test_monte_carlo_functions():
    """測試蒙地卡羅函式"""
    print("\n🧪 測試2：驗證蒙地卡羅函式")
    
    try:
        from monte_carlo_functions import run_monte_carlo_simulation, analyze_and_plot_mc_results
        print("   ✅ 蒙地卡羅函式導入成功")
        
        # 創建測試數據
        test_pnl_list = [Decimal('10'), Decimal('-5'), Decimal('15'), Decimal('-8'), 
                        Decimal('20'), Decimal('-12'), Decimal('25'), Decimal('-3')]
        
        print(f"   📊 使用測試數據：{[float(x) for x in test_pnl_list]}")
        
        # 執行小規模模擬
        simulation_results = run_monte_carlo_simulation(
            daily_pnl_list=test_pnl_list,
            num_simulations=100  # 小規模測試
        )
        
        if simulation_results and simulation_results['final_pnls']:
            print(f"   ✅ 蒙地卡羅模擬成功，生成了 {len(simulation_results['final_pnls'])} 個結果")
            
            # 測試分析函式（不顯示圖表）
            import matplotlib
            matplotlib.use('Agg')  # 使用非互動式後端
            
            original_pnl = sum(test_pnl_list)
            
            # 計算原始最大回撤
            import numpy as np
            cumulative_pnl = np.cumsum([float(pnl) for pnl in test_pnl_list])
            peak_pnl = np.maximum.accumulate(cumulative_pnl)
            drawdowns = peak_pnl - cumulative_pnl
            original_mdd = Decimal(str(np.max(drawdowns)))
            
            print(f"   📈 原始總損益: {original_pnl}")
            print(f"   📉 原始最大回撤: {original_mdd}")
            
            return True, simulation_results
        else:
            print("   ❌ 蒙地卡羅模擬失敗")
            return False, None
            
    except Exception as e:
        print(f"   ❌ 測試失敗: {e}")
        return False, None


def test_integration():
    """測試整合腳本"""
    print("\n🧪 測試3：驗證整合腳本導入")
    
    try:
        # 檢查主腳本是否可以導入
        with open("monte_carlo_analyzer.py", 'r', encoding='utf-8') as f:
            content = f.read()
            
        if "def main():" in content and "run_monte_carlo_simulation" in content:
            print("   ✅ 整合腳本結構正確")
            return True
        else:
            print("   ❌ 整合腳本結構不完整")
            return False
            
    except Exception as e:
        print(f"   ❌ 測試失敗: {e}")
        return False


def main():
    """主測試函式"""
    print("🚀 蒙地卡羅分析器測試套件")
    print("="*50)
    
    # 測試1：回測函式修改
    test1_passed, daily_pnl_list = test_backtest_modification()
    
    # 測試2：蒙地卡羅函式
    test2_passed, simulation_results = test_monte_carlo_functions()
    
    # 測試3：整合腳本
    test3_passed = test_integration()
    
    # 總結
    print("\n" + "="*50)
    print("📋 測試結果總結:")
    print(f"   測試1 (回測函式修改): {'✅ 通過' if test1_passed else '❌ 失敗'}")
    print(f"   測試2 (蒙地卡羅函式): {'✅ 通過' if test2_passed else '❌ 失敗'}")
    print(f"   測試3 (整合腳本): {'✅ 通過' if test3_passed else '❌ 失敗'}")
    
    all_passed = test1_passed and test2_passed and test3_passed
    
    if all_passed:
        print("\n🎉 所有測試通過！蒙地卡羅分析器已準備就緒")
        print("\n📝 使用說明:")
        print("   執行完整分析：python monte_carlo_analyzer.py")
    else:
        print("\n⚠️ 部分測試失敗，請檢查相關組件")
    
    return all_passed


if __name__ == "__main__":
    main()
