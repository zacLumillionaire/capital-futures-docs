#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
做多策略優化實驗工具
專門針對做多交易的表現優化進行實驗
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

def test_long_optimization_strategies(start_date=None, end_date=None):
    """測試做多策略優化方案"""
    print("📈 做多策略優化實驗")
    print("=" * 60)
    print("🎯 實驗目標: 提升做多交易的獲利和勝率")
    print("📊 將測試以下優化方案:")
    print("  1. 基準配置 (160點過濾)")
    print("  2. 做多專用區間過濾優化")
    print("  3. 做多專用停利點優化") 
    print("  4. 做多專用保護停損優化")
    print("  5. 做多時機選擇優化")
    print()
    
    # 初始化
    strategy_module = init_strategy_module()
    
    # 獲取基礎配置（需要根據實際策略模塊調整）
    base_config = {
        "name": "基準配置 - 160點過濾",
        "description": "當前最佳配置，作為對照組",
        "strategy_config": "需要根據實際模塊結構創建"
    }
    
    # 優化配置列表
    optimization_configs = [
        {
            "name": "做多區間過濾優化 - 120點",
            "description": "針對做多交易使用更嚴格的120點區間過濾",
            "optimization_type": "range_filter_long",
            "parameters": {"max_range_points": 120}
        },
        {
            "name": "做多區間過濾優化 - 100點", 
            "description": "針對做多交易使用更嚴格的100點區間過濾",
            "optimization_type": "range_filter_long",
            "parameters": {"max_range_points": 100}
        },
        {
            "name": "做多停利點優化 - 提早停利",
            "description": "做多時使用更保守的停利點設置",
            "optimization_type": "profit_target_long",
            "parameters": {
                "lot1_trigger": 12,  # 從15降到12
                "lot2_trigger": 30,  # 從40降到30
                "lot3_trigger": 50   # 從65降到50
            }
        },
        {
            "name": "做多停利點優化 - 更積極停利",
            "description": "做多時使用更積極的停利點設置",
            "optimization_type": "profit_target_long", 
            "parameters": {
                "lot1_trigger": 10,  # 從15降到10
                "lot2_trigger": 25,  # 從40降到25
                "lot3_trigger": 40   # 從65降到40
            }
        },
        {
            "name": "做多保護停損優化 - 更緊停損",
            "description": "做多時使用更緊的保護停損",
            "optimization_type": "protective_stop_long",
            "parameters": {
                "lot2_multiplier": 1.5,  # 從2.0降到1.5
                "lot3_multiplier": 1.5   # 從2.0降到1.5
            }
        },
        {
            "name": "做多時機優化 - 小區間+強勢突破",
            "description": "做多時要求更小區間(80點)且突破幅度更大",
            "optimization_type": "entry_timing_long",
            "parameters": {
                "max_range_points": 80,
                "min_breakout_ratio": 0.3  # 突破幅度需達到區間的30%
            }
        }
    ]
    
    print("🔬 開始執行優化實驗...")
    print()
    
    # 先運行基準測試
    print("📊 步驟 1: 運行基準配置")
    # run_backtest(strategy_module, base_config, start_date, end_date)
    
    # 說明各個優化方案
    print("\n📋 優化方案說明:")
    print("=" * 60)
    
    for i, config in enumerate(optimization_configs, 1):
        print(f"\n🔹 方案 {i}: {config['name']}")
        print(f"   💡 理論依據: {config['description']}")
        print(f"   🔧 優化類型: {config['optimization_type']}")
        print(f"   ⚙️  參數調整: {config['parameters']}")
        
        # 解釋每個優化的邏輯
        if config['optimization_type'] == 'range_filter_long':
            print(f"   📈 預期效果: 過濾大區間可能減少做多時的假突破")
            
        elif config['optimization_type'] == 'profit_target_long':
            print(f"   📈 預期效果: 提早停利可能提高做多勝率，減少回撤風險")
            
        elif config['optimization_type'] == 'protective_stop_long':
            print(f"   📈 預期效果: 更緊停損可能減少做多時的大幅虧損")
            
        elif config['optimization_type'] == 'entry_timing_long':
            print(f"   📈 預期效果: 更嚴格的進場條件可能提高做多成功率")

def explain_optimization_rationale():
    """解釋優化策略的理論依據"""
    print("\n🧠 做多策略優化理論依據:")
    print("=" * 60)
    
    print("\n1️⃣ 區間過濾優化:")
    print("   💭 觀察: 大區間往往伴隨高波動，做多容易遇到假突破")
    print("   🎯 策略: 對做多使用更嚴格的區間過濾")
    print("   📊 測試: 120點、100點過濾 vs 160點基準")
    
    print("\n2️⃣ 停利點優化:")
    print("   💭 觀察: 做多時市場回撤風險較高")
    print("   🎯 策略: 使用更保守/積極的停利點")
    print("   📊 測試: 提早停利 vs 延遲停利")
    
    print("\n3️⃣ 保護停損優化:")
    print("   💭 觀察: 做多時第三口經常大幅虧損")
    print("   🎯 策略: 對做多使用更緊的保護停損")
    print("   📊 測試: 1.5倍 vs 2.0倍停損距離")
    
    print("\n4️⃣ 進場時機優化:")
    print("   💭 觀察: 做多需要更強的動能確認")
    print("   🎯 策略: 要求更小區間+更大突破幅度")
    print("   📊 測試: 組合條件篩選")

def implementation_suggestions():
    """實施建議"""
    print("\n🛠️ 實施建議:")
    print("=" * 60)
    
    print("\n📋 實驗執行順序:")
    print("  1. 先測試區間過濾優化（最容易實施）")
    print("  2. 再測試停利點優化（中等複雜度）")
    print("  3. 最後測試組合優化（最複雜）")
    
    print("\n🔧 技術實施方案:")
    print("  1. 修改策略配置類，支持做多/做空差異化參數")
    print("  2. 在交易邏輯中添加方向判斷")
    print("  3. 根據方向應用不同的參數設置")
    
    print("\n📊 評估指標:")
    print("  - 做多交易勝率變化")
    print("  - 做多平均獲利變化") 
    print("  - 做多最大虧損變化")
    print("  - 整體策略表現影響")
    
    print("\n⚠️ 風險控制:")
    print("  - 避免過度優化歷史數據")
    print("  - 保持足夠的做多交易樣本")
    print("  - 監控做空表現不受影響")

def main():
    """主函數"""
    print("📈 做多策略優化實驗工具")
    print("=" * 50)
    
    # 執行優化測試說明
    test_long_optimization_strategies()
    
    # 解釋優化理論
    explain_optimization_rationale()
    
    # 提供實施建議
    implementation_suggestions()
    
    print("\n🎉 做多策略優化分析完成！")
    print("\n📋 下一步行動:")
    print("  1. 選擇優先測試的優化方案")
    print("  2. 修改策略代碼支持差異化參數")
    print("  3. 執行實際的優化測試")
    print("  4. 分析結果並選擇最佳配置")

if __name__ == "__main__":
    main()
