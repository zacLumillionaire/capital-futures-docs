#!/usr/bin/env python3
"""
策略敏感度分析器 - 演示版本

這是一個簡化的演示版本，用於驗證 SALib 敏感度分析的基本功能。
使用模擬數據來展示如何分析策略參數對最大回撤的影響。

執行方式：
    python demo_sensitivity_analyzer.py
"""

import logging
import numpy as np
import pandas as pd
from decimal import Decimal

# SALib 導入
from SALib.analyze import sobol
from SALib.sample import sobol as sobol_sample

# 設定日誌
logging.basicConfig(level=logging.INFO, format='[%(asctime)s] %(levelname)s: %(message)s')
logger = logging.getLogger(__name__)

# ==============================================================================
# 模擬策略評估函數
# ==============================================================================

def simulate_strategy_mdd(params: np.ndarray, trading_direction: str) -> float:
    """
    模擬策略的最大回撤計算
    
    這是一個簡化的模擬函數，用於演示敏感度分析的概念。
    在實際應用中，這裡會調用真實的回測引擎。
    
    Args:
        params: 參數陣列 [lot1_trigger, lot1_pullback, lot2_trigger, lot2_pullback, 
                         lot3_trigger, lot3_pullback, protection_multiplier]
        trading_direction: 交易方向
        
    Returns:
        float: 負MDD值（用於最小化優化）
    """
    lot1_trigger, lot1_pullback, lot2_trigger, lot2_pullback, lot3_trigger, lot3_pullback, protection_multiplier = params
    
    # 模擬邏輯：基於參數計算模擬的MDD
    # 這裡使用一些啟發式規則來模擬真實策略的行為
    
    # 基礎MDD（假設範圍在20-100點之間）
    base_mdd = 50.0
    
    # 觸發點影響：觸發點越高，MDD可能越大（因為進場較晚）
    trigger_effect = (lot1_trigger + lot2_trigger + lot3_trigger) / 3.0 - 40.0
    
    # 回檔百分比影響：回檔百分比越大，MDD可能越小（停利較寬鬆）
    pullback_effect = -((lot1_pullback + lot2_pullback + lot3_pullback) / 3.0 - 0.2) * 100
    
    # 保護性停損影響：倍數越高，MDD可能越小
    protection_effect = -(protection_multiplier - 2.0) * 10
    
    # 交易方向影響
    direction_effect = 0.0
    if trading_direction == "LONG_ONLY":
        direction_effect = -5.0  # 多頭策略稍微保守
    elif trading_direction == "SHORT_ONLY":
        direction_effect = 5.0   # 空頭策略風險稍高
    
    # 添加一些隨機性來模擬市場不確定性
    random_effect = np.random.normal(0, 5)
    
    # 計算最終MDD
    simulated_mdd = base_mdd + trigger_effect + pullback_effect + protection_effect + direction_effect + random_effect
    
    # 確保MDD為正值
    simulated_mdd = max(simulated_mdd, 5.0)
    
    # 返回負MDD（用於最小化優化）
    return -simulated_mdd

# ==============================================================================
# SALib 問題定義
# ==============================================================================

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

# 交易方向列表
TRADING_DIRECTIONS = ['LONG_ONLY', 'SHORT_ONLY', 'BOTH']

# ==============================================================================
# 主要分析函數
# ==============================================================================

def run_demo_sensitivity_analysis(sample_size: int = 64):
    """
    執行演示版敏感度分析
    
    Args:
        sample_size: SALib 樣本數
    """
    logger.info("🚀 策略敏感度分析器 - 演示版本")
    logger.info(f"🎲 樣本數: {sample_size}")
    logger.info("=" * 60)
    
    results = {}
    
    # 設定隨機種子以確保結果可重現
    np.random.seed(42)
    
    for trading_direction in TRADING_DIRECTIONS:
        logger.info(f"\n📊 分析交易方向: {trading_direction}")
        
        try:
            # 1. 生成樣本
            logger.info(f"   🎲 生成 Sobol 樣本...")
            param_values = sobol_sample.sample(problem, N=sample_size)
            logger.info(f"   ✅ 生成了 {len(param_values)} 個參數組合")
            
            # 2. 執行模擬評估
            logger.info(f"   🔄 執行模擬評估...")
            Y = np.zeros(len(param_values))
            
            for i, params in enumerate(param_values):
                Y[i] = simulate_strategy_mdd(params, trading_direction)
            
            logger.info(f"   ✅ 模擬評估完成")
            logger.info(f"   📈 MDD範圍: {-Y.max():.2f} 到 {-Y.min():.2f} 點")
            
            # 3. 執行 Sobol 分析
            logger.info(f"   📈 執行 Sobol 敏感度分析...")
            Si = sobol.analyze(problem, Y)
            
            # 4. 儲存結果
            results[trading_direction] = {
                'Si': Si,
                'Y_values': Y,
                'param_values': param_values
            }
            
            # 5. 顯示結果
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
            
        except Exception as e:
            logger.error(f"❌ {trading_direction} 分析失敗: {e}")
            results[trading_direction] = {'error': str(e)}
    
    # 顯示最終摘要
    logger.info("\n" + "="*60)
    logger.info("📊 敏感度分析完整結果摘要")
    logger.info("="*60)
    
    for direction, result in results.items():
        if 'error' in result:
            logger.info(f"\n❌ {direction}: 分析失敗 - {result['error']}")
            continue
            
        logger.info(f"\n📈 {direction} 交易方向結果:")
        
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
            
        # 計算平均MDD
        avg_mdd = -np.mean(result['Y_values'])
        logger.info(f"   📊 平均模擬MDD: {avg_mdd:.2f} 點")
    
    logger.info("\n✅ 演示版敏感度分析完成！")
    logger.info("\n💡 說明：")
    logger.info("   - 這是使用模擬數據的演示版本")
    logger.info("   - 實際版本會使用真實的回測引擎")
    logger.info("   - ST值越高的參數對MDD影響越大，應優先優化")
    
    return results

if __name__ == '__main__':
    # 執行演示分析
    demo_results = run_demo_sensitivity_analysis(sample_size=64)
