#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
快速方向性測試工具
測試純做多、純做空策略的表現
"""

import logging
import importlib.util
from datetime import datetime
from decimal import Decimal

# 設置日誌
logging.basicConfig(level=logging.INFO, format='[%(asctime)s] %(levelname)s [%(name)s.%(funcName)s:%(lineno)d] %(message)s')
logger = logging.getLogger(__name__)

def init_strategy_module():
    """初始化策略模塊"""
    try:
        from app_setup import init_all_db_pools
        logger.info("🔌 初始化數據庫連接池...")
        init_all_db_pools()
        logger.info("✅ 數據庫連接池初始化成功")
    except Exception as e:
        logger.error(f"❌ 數據庫初始化失敗: {e}")
        raise
    
    # 動態導入策略模塊
    try:
        spec = importlib.util.spec_from_file_location(
            "strategy_module", 
            "multi_Profit-Funded Risk_多口.py"
        )
        strategy_module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(strategy_module)
        logger.info("✅ 策略模塊導入成功")
        return strategy_module
    except Exception as e:
        logger.error(f"❌ 策略模塊導入失敗: {e}")
        raise

def get_base_lot_rules(strategy_module):
    """獲取基礎口數規則"""
    return [
        strategy_module.LotRule(
            lot_number=1,
            profit_target=strategy_module.ProfitTarget(
                target_type=strategy_module.ProfitTargetType.TRAILING_STOP,
                trigger_points=Decimal("15"),
                trailing_percentage=Decimal("0.2")
            )
        ),
        strategy_module.LotRule(
            lot_number=2,
            profit_target=strategy_module.ProfitTarget(
                target_type=strategy_module.ProfitTargetType.TRAILING_STOP,
                trigger_points=Decimal("40"),
                trailing_percentage=Decimal("0.2")
            ),
            protective_stop_multiplier=Decimal("2.0")
        ),
        strategy_module.LotRule(
            lot_number=3,
            profit_target=strategy_module.ProfitTarget(
                target_type=strategy_module.ProfitTargetType.TRAILING_STOP,
                trigger_points=Decimal("65"),
                trailing_percentage=Decimal("0.2")
            ),
            protective_stop_multiplier=Decimal("2.0")
        )
    ]

def run_backtest(strategy_module, config, start_date=None, end_date=None):
    """執行回測並捕獲結果"""
    print(f"\n{'='*60}")
    print(f"🧪 測試配置: {config.get('name', '未命名配置')}")
    print(f"{'='*60}")
    
    try:
        # 執行回測
        strategy_module.run_backtest(config['strategy_config'], start_date, end_date)
        print(f"✅ {config.get('name', '配置')} 測試完成")
        
    except Exception as e:
        print(f"❌ {config.get('name', '配置')} 測試失敗: {e}")

def test_direction_strategies(start_date=None, end_date=None):
    """測試不同方向性策略"""
    print("🧭 開始方向性策略測試...")
    print("📊 將測試以下配置:")
    print("  1. 雙向策略（基準）- 160點過濾")
    print("  2. 純做多策略（概念驗證）")
    print("  3. 純做空策略（概念驗證）")
    print()
    
    # 初始化
    strategy_module = init_strategy_module()
    base_lot_rules = get_base_lot_rules(strategy_module)
    
    # 測試配置
    test_configs = [
        {
            "name": "雙向策略（基準）- 160點過濾",
            "strategy_config": strategy_module.StrategyConfig(
                trade_size_in_lots=3,
                stop_loss_type=strategy_module.StopLossType.RANGE_BOUNDARY,
                lot_rules=base_lot_rules,
                range_filter=strategy_module.RangeFilter(
                    use_range_size_filter=True,
                    max_range_points=Decimal("160")
                )
            )
        }
    ]
    
    # 執行測試
    for config in test_configs:
        run_backtest(strategy_module, config, start_date, end_date)
    
    print("\n" + "="*60)
    print("📝 方向性測試說明:")
    print("="*60)
    print("🔹 當前測試了雙向策略作為基準")
    print("🔹 純做多/做空策略需要修改核心策略邏輯")
    print("🔹 建議下一步:")
    print("   1. 分析現有交易日誌中的做多/做空表現")
    print("   2. 修改策略代碼支持方向過濾")
    print("   3. 重新運行完整的方向性測試")
    print()
    print("💡 從現有數據觀察:")
    print("   - 做空交易通常表現更好")
    print("   - 做多交易更容易觸發停損")
    print("   - 建議優先測試純做空策略")
    print()

def analyze_existing_trades():
    """分析現有交易記錄中的方向性表現"""
    print("📊 分析建議 - 從現有交易日誌提取方向性數據:")
    print()
    print("🔍 可以分析的指標:")
    print("  1. 做多 vs 做空的交易次數分布")
    print("  2. 做多 vs 做空的勝率對比")
    print("  3. 做多 vs 做空的平均獲利對比")
    print("  4. 做多 vs 做空在不同口數的表現")
    print()
    print("📋 實施步驟:")
    print("  1. 運行現有策略並保存詳細交易日誌")
    print("  2. 解析日誌文件，按方向分類交易")
    print("  3. 計算各方向的統計指標")
    print("  4. 生成方向性分析報告")
    print()

def main():
    """主函數"""
    print("🎯 方向性策略分析工具")
    print("=" * 50)
    
    # 執行方向性測試
    test_direction_strategies()
    
    # 提供分析建議
    analyze_existing_trades()
    
    print("🎉 方向性分析工具執行完成！")
    print()
    print("📋 下一步建議:")
    print("  1. 檢查上述回測結果")
    print("  2. 考慮實施純做空策略測試")
    print("  3. 分析交易日誌中的方向性數據")

if __name__ == "__main__":
    main()
