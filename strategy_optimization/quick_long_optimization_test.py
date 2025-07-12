#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
快速做多優化測試工具
實際執行做多策略優化實驗
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

def run_backtest(strategy_module, config, start_date=None, end_date=None):
    """執行回測並捕獲結果"""
    print(f"\n{'='*80}")
    print(f"🧪 測試配置: {config.get('name', '未命名配置')}")
    print(f"📋 說明: {config.get('description', '無說明')}")
    print(f"{'='*80}")
    
    try:
        # 執行回測
        strategy_module.run_backtest(config['strategy_config'], start_date, end_date)
        print(f"✅ {config.get('name', '配置')} 測試完成")
        
    except Exception as e:
        print(f"❌ {config.get('name', '配置')} 測試失敗: {e}")

def test_long_optimization_phase1(start_date=None, end_date=None):
    """第一階段：區間過濾優化測試"""
    print("🔬 第一階段：做多區間過濾優化測試")
    print("=" * 60)
    print("🎯 測試目標: 找出做多交易的最佳區間過濾閾值")
    print("📊 測試閾值: [160, 120, 100, 80] 點")
    print()
    
    # 初始化
    strategy_module = init_strategy_module()
    
    # 測試不同的區間過濾閾值
    range_thresholds = [160, 120, 100, 80]
    
    for threshold in range_thresholds:
        config = {
            "name": f"區間過濾 {threshold}點",
            "description": f"使用{threshold}點區間過濾的策略配置",
            "strategy_config": strategy_module.StrategyConfig(
                trade_size_in_lots=3,
                stop_loss_type=strategy_module.StopLossType.RANGE_BOUNDARY,
                lot_rules=get_base_lot_rules(strategy_module),
                range_filter=strategy_module.RangeFilter(
                    use_range_size_filter=True,
                    max_range_points=Decimal(str(threshold))
                )
            )
        }
        
        run_backtest(strategy_module, config, start_date, end_date)
    
    print("\n📊 第一階段測試完成")
    print("💡 請觀察不同閾值下做多交易的表現差異")

def get_base_lot_rules(strategy_module):
    """獲取基礎口數規則"""
    return [
        strategy_module.LotRule(
            use_trailing_stop=True,
            trailing_activation=Decimal(15),
            trailing_pullback=Decimal('0.20')
        ),
        strategy_module.LotRule(
            use_trailing_stop=True,
            trailing_activation=Decimal(40),
            trailing_pullback=Decimal('0.20'),
            protective_stop_multiplier=Decimal('2.0')
        ),
        strategy_module.LotRule(
            use_trailing_stop=True,
            trailing_activation=Decimal(65),
            trailing_pullback=Decimal('0.20'),
            protective_stop_multiplier=Decimal('2.0')
        )
    ]

def test_long_optimization_phase2(start_date=None, end_date=None):
    """第二階段：停利點優化測試（概念說明）"""
    print("\n🔬 第二階段：做多停利點優化（概念設計）")
    print("=" * 60)
    print("🎯 測試目標: 優化做多交易的停利點設置")
    print()
    
    print("📋 優化方案設計:")
    print("  1. 基準配置: 15/40/65點停利觸發")
    print("  2. 保守配置: 12/30/50點停利觸發（提早停利）")
    print("  3. 積極配置: 10/25/40點停利觸發（更早停利）")
    print("  4. 混合配置: 12/35/55點停利觸發（平衡方案）")
    print()
    
    print("💡 理論依據:")
    print("  - 做多時市場回撤風險較高")
    print("  - 提早停利可能提高勝率")
    print("  - 需要平衡獲利空間和風險控制")
    print()
    
    print("⚠️ 實施需求:")
    print("  - 需要修改策略代碼支持差異化停利點")
    print("  - 需要在交易邏輯中添加方向判斷")
    print("  - 建議先完成第一階段測試")

def analyze_current_results():
    """分析當前結果並提供建議"""
    print("\n📊 當前實驗狀態分析:")
    print("=" * 60)
    
    print("✅ 已完成:")
    print("  - 160點區間過濾優化（11.8倍獲利提升）")
    print("  - 做多優化實驗設計")
    print("  - 第一階段區間過濾測試框架")
    
    print("\n🔄 進行中:")
    print("  - 做多專用區間過濾測試")
    print("  - 尋找做多交易的最佳過濾閾值")
    
    print("\n📋 下一步建議:")
    print("  1. 執行第一階段區間過濾測試")
    print("  2. 分析不同閾值下的做多表現")
    print("  3. 選擇最佳做多過濾閾值")
    print("  4. 設計第二階段停利點優化")
    
    print("\n🎯 預期成果:")
    print("  - 找到做多交易的最佳區間過濾")
    print("  - 提升做多勝率和平均獲利")
    print("  - 為後續優化提供數據基礎")

def implementation_roadmap():
    """實施路線圖"""
    print("\n🗺️ 做多優化實施路線圖:")
    print("=" * 60)
    
    print("📅 第1週 - 區間過濾優化:")
    print("  ✅ 設計實驗框架")
    print("  🔄 測試不同區間閾值 [160, 120, 100, 80]")
    print("  📊 分析做多表現差異")
    print("  🎯 確定最佳做多過濾閾值")
    
    print("\n📅 第2週 - 停利點優化:")
    print("  🔧 修改策略代碼支持差異化停利")
    print("  🧪 測試不同停利點組合")
    print("  📈 評估勝率和獲利改善")
    print("  ⚖️ 平衡風險和收益")
    
    print("\n📅 第3週 - 組合優化:")
    print("  🔗 結合最佳區間過濾和停利點")
    print("  🧪 測試保護停損優化")
    print("  📊 進行綜合性能評估")
    print("  🎉 確定最終優化配置")
    
    print("\n🎯 成功指標:")
    print("  - 做多勝率提升 >5%")
    print("  - 做多平均獲利提升 >20%")
    print("  - 整體策略表現不下降")
    print("  - 風險調整收益改善")

def main():
    """主函數"""
    print("📈 做多策略優化實驗 - 第一階段執行")
    print("=" * 50)
    
    # 執行第一階段測試
    test_long_optimization_phase1()
    
    # 說明第二階段設計
    test_long_optimization_phase2()
    
    # 分析當前狀態
    analyze_current_results()
    
    # 提供實施路線圖
    implementation_roadmap()
    
    print("\n🎉 做多優化實驗第一階段準備完成！")
    print("\n📋 立即行動:")
    print("  1. 觀察上述區間過濾測試結果")
    print("  2. 比較不同閾值下的做多表現")
    print("  3. 選擇表現最佳的做多過濾閾值")
    print("  4. 準備第二階段停利點優化")

if __name__ == "__main__":
    main()
