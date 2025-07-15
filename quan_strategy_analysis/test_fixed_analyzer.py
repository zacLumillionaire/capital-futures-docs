#!/usr/bin/env python3
"""
測試修復後的敏感度分析器
"""

import logging
import numpy as np

logging.basicConfig(level=logging.INFO, format='[%(asctime)s] %(levelname)s: %(message)s')
logger = logging.getLogger(__name__)

def test_fixed_backtest():
    """測試修復後的回測"""
    logger.info("🔍 測試修復後的回測...")
    
    try:
        import strategy_sensitivity_analyzer
        
        # 測試參數
        test_params = np.array([15.0, 0.20, 40.0, 0.15, 65.0, 0.25, 2.0])
        
        # 使用正確的時間區間 08:46-08:47
        result = strategy_sensitivity_analyzer.evaluate_for_salib(
            test_params, 
            "BOTH", 
            "2024-11-04", 
            "2025-06-28", 
            "08:46", 
            "08:47"
        )
        
        logger.info(f"   修復後回測結果: {result}")
        
        if result != -999999.0:
            logger.info("   ✅ 修復後回測成功")
            return True
        else:
            logger.error("   ❌ 修復後回測仍然失敗")
            return False
            
    except Exception as e:
        logger.error(f"   ❌ 修復後回測異常: {e}")
        return False

def test_multiple_fixed_backtests():
    """測試多次修復後的回測"""
    logger.info("🔍 測試多次修復後的回測...")
    
    try:
        import strategy_sensitivity_analyzer
        from SALib.sample import sobol as sobol_sample
        
        # 使用小樣本測試
        problem = strategy_sensitivity_analyzer.problem
        param_values = sobol_sample.sample(problem, N=4)  # 只生成少量樣本
        
        logger.info(f"   生成了 {len(param_values)} 個測試樣本")
        
        results = []
        for i, params in enumerate(param_values[:5]):  # 只測試前5個
            result = strategy_sensitivity_analyzer.evaluate_for_salib(
                params, 
                "BOTH", 
                "2024-11-04", 
                "2025-06-28", 
                "08:46", 
                "08:47"
            )
            results.append(result)
            logger.info(f"   樣本 {i+1}: 結果={result:.6f}")
        
        results = np.array(results)
        valid_results = results[results > -999999]
        
        if len(valid_results) > 0:
            logger.info(f"   📊 修復後結果統計:")
            logger.info(f"      有效結果: {len(valid_results)}/{len(results)}")
            logger.info(f"      最小值: {valid_results.min():.6f}")
            logger.info(f"      最大值: {valid_results.max():.6f}")
            logger.info(f"      平均值: {valid_results.mean():.6f}")
            logger.info(f"      標準差: {valid_results.std():.6f}")
            logger.info(f"      唯一值: {len(np.unique(valid_results))}")
            
            if valid_results.std() > 1e-10:
                logger.info("   ✅ 修復後結果有足夠的變異性")
                return True
            else:
                logger.warning("   ⚠️ 修復後結果仍然變異性不足")
                return False
        else:
            logger.error("   ❌ 修復後沒有有效結果")
            return False
            
    except Exception as e:
        logger.error(f"   ❌ 修復後多次回測測試異常: {e}")
        return False

def test_direct_backtest_with_correct_time():
    """直接測試使用正確時間的回測函數"""
    logger.info("🔍 直接測試使用正確時間的回測函數...")
    
    try:
        import strategy_sensitivity_analyzer
        from decimal import Decimal
        
        # 創建測試配置
        lot_rules = [
            strategy_sensitivity_analyzer.LotRule(
                use_trailing_stop=True,
                trailing_activation=Decimal('15'),
                trailing_pullback=Decimal('0.20')
            ),
            strategy_sensitivity_analyzer.LotRule(
                use_trailing_stop=True,
                trailing_activation=Decimal('40'),
                trailing_pullback=Decimal('0.15'),
                protective_stop_multiplier=Decimal('2.0')
            ),
            strategy_sensitivity_analyzer.LotRule(
                use_trailing_stop=True,
                trailing_activation=Decimal('65'),
                trailing_pullback=Decimal('0.25'),
                protective_stop_multiplier=Decimal('2.0')
            )
        ]
        
        config = strategy_sensitivity_analyzer.StrategyConfig(
            trade_size_in_lots=3,
            stop_loss_type=strategy_sensitivity_analyzer.StopLossType.RANGE_BOUNDARY,
            lot_rules=lot_rules,
            trading_direction="BOTH",
            range_filter=strategy_sensitivity_analyzer.RangeFilter(),
            risk_config=strategy_sensitivity_analyzer.RiskConfig(),
            stop_loss_config=strategy_sensitivity_analyzer.StopLossConfig()
        )
        
        # 使用正確的時間區間 08:46-08:47
        result = strategy_sensitivity_analyzer.calculate_backtest_metrics(
            config, "2024-11-04", "2025-06-28", "08:46", "08:47", silent=False
        )
        
        logger.info(f"   📊 修復後回測結果:")
        for key, value in result.items():
            logger.info(f"      {key}: {value}")
        
        if result['total_trades'] > 0:
            logger.info("   ✅ 修復後回測函數正常，有交易記錄")
            return True
        else:
            logger.warning("   ⚠️ 修復後回測函數正常，但仍沒有交易記錄")
            return False
            
    except Exception as e:
        logger.error(f"   ❌ 修復後回測函數測試異常: {e}")
        return False

def main():
    """主測試函數"""
    logger.info("🚀 測試修復後的敏感度分析器")
    logger.info("=" * 50)
    
    tests = [
        ("修復後回測函數測試", test_direct_backtest_with_correct_time),
        ("修復後單次回測測試", test_fixed_backtest),
        ("修復後多次回測變異性測試", test_multiple_fixed_backtests)
    ]
    
    for test_name, test_func in tests:
        logger.info(f"\n📋 執行: {test_name}")
        try:
            if test_func():
                logger.info(f"✅ {test_name} 通過")
            else:
                logger.error(f"❌ {test_name} 失敗")
        except Exception as e:
            logger.error(f"❌ {test_name} 異常: {e}")
    
    logger.info("\n" + "=" * 50)
    logger.info("🔍 修復測試完成")

if __name__ == '__main__':
    main()
