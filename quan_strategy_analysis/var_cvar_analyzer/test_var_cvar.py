#!/usr/bin/env python3
"""
VaR/CVaR 分析器測試腳本

用於測試 VaR/CVaR 分析器的基本功能
"""

import sys
import os
import numpy as np
from decimal import Decimal

# 導入我們的分析器
from var_cvar_analyzer import calculate_var, calculate_cvar, print_risk_report, create_risk_visualization
from strategy_core import StrategyConfig, LotRule, StopLossType, RangeFilter

def test_var_cvar_calculations():
    """測試 VaR 和 CVaR 計算函數"""
    print("🧪 測試 VaR/CVaR 計算函數")
    print("-" * 40)
    
    # 創建測試數據：模擬損益分佈
    np.random.seed(42)  # 設定隨機種子以確保結果可重現
    
    # 生成正態分佈的損益數據（平均獲利5點，標準差20點）
    test_pnl_list = np.random.normal(5, 20, 1000).tolist()
    
    print(f"📊 測試數據：{len(test_pnl_list)} 個模擬交易日")
    print(f"   平均損益：{np.mean(test_pnl_list):.2f} 點")
    print(f"   標準差：{np.std(test_pnl_list):.2f} 點")
    print()
    
    # 測試 VaR 計算
    confidence_levels = [0.90, 0.95, 0.99]
    
    for confidence in confidence_levels:
        var_value = calculate_var(test_pnl_list, confidence)
        cvar_value = calculate_cvar(test_pnl_list, var_value)
        
        print(f"📈 信心水準 {confidence*100:.0f}%:")
        print(f"   VaR: {var_value:.2f} 點")
        print(f"   CVaR: {cvar_value:.2f} 點")
        print()
    
    # 測試邊界情況
    print("🔍 測試邊界情況:")
    
    # 空列表
    empty_var = calculate_var([])
    empty_cvar = calculate_cvar([], 0)
    print(f"   空列表 - VaR: {empty_var}, CVaR: {empty_cvar}")
    
    # 單一值
    single_var = calculate_var([10.0])
    single_cvar = calculate_cvar([10.0], single_var)
    print(f"   單一值 - VaR: {single_var}, CVaR: {single_cvar}")
    
    # 全部獲利
    profit_list = [10, 20, 30, 40, 50]
    profit_var = calculate_var(profit_list)
    profit_cvar = calculate_cvar(profit_list, profit_var)
    print(f"   全部獲利 - VaR: {profit_var}, CVaR: {profit_cvar}")
    
    # 全部虧損
    loss_list = [-10, -20, -30, -40, -50]
    loss_var = calculate_var(loss_list)
    loss_cvar = calculate_cvar(loss_list, loss_var)
    print(f"   全部虧損 - VaR: {loss_var}, CVaR: {loss_cvar}")
    
    print("✅ VaR/CVaR 計算測試完成")
    return test_pnl_list


def test_report_generation(test_pnl_list):
    """測試報告生成功能"""
    print("\n📋 測試報告生成功能")
    print("-" * 40)
    
    # 計算風險指標
    var_value = calculate_var(test_pnl_list, 0.95)
    cvar_value = calculate_cvar(test_pnl_list, var_value)
    
    # 生成報告
    print_risk_report(
        var_value=var_value,
        cvar_value=cvar_value,
        confidence_level=0.95,
        total_days=len(test_pnl_list),
        pnl_list=test_pnl_list
    )
    
    print("✅ 報告生成測試完成")


def test_visualization(test_pnl_list):
    """測試視覺化功能"""
    print("\n📊 測試視覺化功能")
    print("-" * 40)
    
    # 計算風險指標
    var_value = calculate_var(test_pnl_list, 0.95)
    cvar_value = calculate_cvar(test_pnl_list, var_value)
    
    # 創建測試報告目錄
    test_reports_dir = "test_reports"
    os.makedirs(test_reports_dir, exist_ok=True)
    
    # 生成視覺化圖表
    chart_path = os.path.join(test_reports_dir, "test_var_cvar_chart.png")
    
    try:
        create_risk_visualization(
            pnl_list=test_pnl_list,
            var_value=var_value,
            cvar_value=cvar_value,
            confidence_level=0.95,
            save_path=chart_path
        )
        print("✅ 視覺化測試完成")
    except Exception as e:
        print(f"⚠️  視覺化測試失敗: {e}")
        print("   這可能是因為缺少圖形顯示環境，但不影響核心功能")


def test_strategy_config():
    """測試策略配置創建"""
    print("\n⚙️  測試策略配置")
    print("-" * 40)
    
    try:
        # 創建測試配置
        config = StrategyConfig(
            trade_size_in_lots=3,
            stop_loss_type=StopLossType.RANGE_BOUNDARY,
            lot_rules=[
                LotRule(
                    use_trailing_stop=True,
                    trailing_activation=Decimal('15'),
                    trailing_pullback=Decimal('0.10')
                ),
                LotRule(
                    use_trailing_stop=True,
                    trailing_activation=Decimal('40'),
                    trailing_pullback=Decimal('0.10'),
                    protective_stop_multiplier=Decimal('2')
                ),
                LotRule(
                    use_trailing_stop=True,
                    trailing_activation=Decimal('41'),
                    trailing_pullback=Decimal('0.20'),
                    protective_stop_multiplier=Decimal('2')
                )
            ],
            range_filter=RangeFilter(
                use_range_size_filter=True,
                max_range_points=Decimal('160')
            )
        )
        
        print("✅ 策略配置創建成功")
        print(f"   交易口數: {config.trade_size_in_lots}")
        print(f"   停損類型: {config.stop_loss_type.name}")
        print(f"   口數規則: {len(config.lot_rules)} 個")
        print(f"   區間過濾: {'啟用' if config.range_filter.use_range_size_filter else '停用'}")
        
    except Exception as e:
        print(f"❌ 策略配置測試失敗: {e}")


if __name__ == '__main__':
    """執行所有測試"""
    print("🚀 VaR/CVaR 分析器測試開始")
    print("=" * 50)
    
    try:
        # 測試計算函數
        test_pnl_data = test_var_cvar_calculations()
        
        # 測試報告生成
        test_report_generation(test_pnl_data)
        
        # 測試視覺化
        test_visualization(test_pnl_data)
        
        # 測試策略配置
        test_strategy_config()
        
        print("\n🎉 所有測試完成！")
        print("=" * 50)
        print("💡 如果所有測試都通過，您可以運行主程式：")
        print("   python var_cvar_analyzer.py")
        
    except Exception as e:
        print(f"\n❌ 測試過程中發生錯誤: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
