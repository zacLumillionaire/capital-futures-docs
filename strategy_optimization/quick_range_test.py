#!/usr/bin/env python3
"""
快速區間過濾測試工具
直接修改策略配置並運行回測，避免複雜的日誌捕獲
"""

import importlib.util
import sys
from decimal import Decimal
from app_setup import init_all_db_pools

# 動態導入策略模組
spec = importlib.util.spec_from_file_location("strategy_module", "multi_Profit-Funded Risk_多口.py")
strategy_module = importlib.util.module_from_spec(spec)
sys.modules["strategy_module"] = strategy_module
spec.loader.exec_module(strategy_module)

# 導入需要的類別
StrategyConfig = strategy_module.StrategyConfig
RangeFilter = strategy_module.RangeFilter
StopLossType = strategy_module.StopLossType
LotRule = strategy_module.LotRule
run_backtest = strategy_module.run_backtest

def test_range_thresholds(thresholds, start_date=None, end_date=None):
    """測試不同的區間閾值"""
    print("🧪 開始測試區間過濾閾值...")
    print(f"📊 測試閾值: {thresholds}")
    print("=" * 60)
    
    # 初始化數據庫
    init_all_db_pools()
    
    # 基準配置
    base_lot_rules = [
        LotRule(use_trailing_stop=True, trailing_activation=Decimal(15), trailing_pullback=Decimal('0.20')),
        LotRule(use_trailing_stop=True, trailing_activation=Decimal(40), trailing_pullback=Decimal('0.20'), protective_stop_multiplier=Decimal('2.0')),
        LotRule(use_trailing_stop=True, trailing_activation=Decimal(65), trailing_pullback=Decimal('0.20'), protective_stop_multiplier=Decimal('2.0'))
    ]
    
    results = []
    
    # 測試基準（無過濾）
    print("\n🔹 測試基準配置（無區間過濾）")
    base_config = StrategyConfig(
        trade_size_in_lots=3,
        stop_loss_type=StopLossType.RANGE_BOUNDARY,
        lot_rules=base_lot_rules
    )
    
    print("開始回測...")
    run_backtest(base_config, start_date, end_date)
    print("基準測試完成\n")
    
    # 測試各個閾值
    for threshold in thresholds:
        print(f"\n🔹 測試 {threshold} 點過濾")
        
        config = StrategyConfig(
            trade_size_in_lots=3,
            stop_loss_type=StopLossType.RANGE_BOUNDARY,
            lot_rules=base_lot_rules,
            range_filter=RangeFilter(
                use_range_size_filter=True,
                max_range_points=Decimal(str(threshold))
            )
        )
        
        print("開始回測...")
        run_backtest(config, start_date, end_date)
        print(f"{threshold} 點過濾測試完成\n")
    
    print("🎉 所有測試完成！")
    print("\n💡 使用建議：")
    print("1. 觀察各配置的總損益和交易次數")
    print("2. 比較勝率和平均每筆獲利")
    print("3. 選擇平衡獲利和交易頻率的最佳閾值")

if __name__ == "__main__":
    # 您想要測試的閾值
    test_thresholds = [70, 100, 130, 160]
    
    # 可以指定測試時間範圍（可選）
    # test_range_thresholds(test_thresholds, "2024-12-01", "2024-12-31")
    
    # 或測試全部數據
    test_range_thresholds(test_thresholds)
