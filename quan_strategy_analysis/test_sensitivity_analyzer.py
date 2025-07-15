#!/usr/bin/env python3
"""
策略敏感度分析器測試腳本
用於驗證基本功能是否正常
"""

import sys
import os
import logging

# 設定日誌
logging.basicConfig(level=logging.INFO, format='[%(asctime)s] %(levelname)s: %(message)s')
logger = logging.getLogger(__name__)

def test_imports():
    """測試所有必要的導入"""
    logger.info("🔍 測試導入...")
    
    try:
        # 測試 SALib
        from SALib.analyze import sobol
        from SALib.sample import saltelli
        logger.info("✅ SALib 導入成功")
    except ImportError as e:
        logger.error(f"❌ SALib 導入失敗: {e}")
        return False
    
    try:
        # 測試 numpy, pandas
        import numpy as np
        import pandas as pd
        logger.info("✅ NumPy, Pandas 導入成功")
    except ImportError as e:
        logger.error(f"❌ NumPy/Pandas 導入失敗: {e}")
        return False
    
    try:
        # 測試回測模組導入
        import importlib.util
        spec = importlib.util.spec_from_file_location("backtest_module", "multi_Profit-Funded Risk_多口.py")
        if spec is not None and spec.loader is not None:
            backtest_module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(backtest_module)
            logger.info("✅ 回測模組導入成功")
            
            # 測試關鍵類和函數
            StrategyConfig = backtest_module.StrategyConfig
            LotRule = backtest_module.LotRule
            logger.info("✅ 關鍵類導入成功")
            
        else:
            logger.error("❌ 無法載入回測模組")
            return False
            
    except Exception as e:
        logger.error(f"❌ 回測模組導入失敗: {e}")
        return False
    
    return True

def test_salib_basic():
    """測試 SALib 基本功能"""
    logger.info("🧪 測試 SALib 基本功能...")
    
    try:
        from SALib.analyze import sobol
        from SALib.sample import saltelli
        import numpy as np
        
        # 定義簡單的測試問題
        problem = {
            'num_vars': 3,
            'names': ['x1', 'x2', 'x3'],
            'bounds': [[0, 1], [0, 1], [0, 1]]
        }
        
        # 生成樣本
        param_values = saltelli.sample(problem, N=8)  # 小樣本測試
        logger.info(f"✅ 生成了 {len(param_values)} 個樣本")
        
        # 模擬評估函數 (簡單的線性組合)
        Y = np.sum(param_values, axis=1)
        
        # 執行分析
        Si = sobol.analyze(problem, Y)
        logger.info("✅ Sobol 分析完成")
        
        # 顯示結果
        df_results = Si.to_df()
        logger.info("✅ 結果轉換為 DataFrame 成功")
        
        return True
        
    except Exception as e:
        logger.error(f"❌ SALib 測試失敗: {e}")
        return False

def test_strategy_config():
    """測試策略配置創建"""
    logger.info("⚙️ 測試策略配置創建...")
    
    try:
        import importlib.util
        spec = importlib.util.spec_from_file_location("backtest_module", "multi_Profit-Funded Risk_多口.py")
        if spec is not None and spec.loader is not None:
            backtest_module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(backtest_module)
            
            StrategyConfig = backtest_module.StrategyConfig
            LotRule = backtest_module.LotRule
            StopLossType = backtest_module.StopLossType
            RangeFilter = backtest_module.RangeFilter
            RiskConfig = backtest_module.RiskConfig
            StopLossConfig = backtest_module.StopLossConfig
            
            from decimal import Decimal
            
            # 創建測試配置
            lot_rules = [
                LotRule(
                    use_trailing_stop=True,
                    trailing_activation=Decimal('15'),
                    trailing_pullback=Decimal('0.20')
                ),
                LotRule(
                    use_trailing_stop=True,
                    trailing_activation=Decimal('40'),
                    trailing_pullback=Decimal('0.20'),
                    protective_stop_multiplier=Decimal('2.0')
                ),
                LotRule(
                    use_trailing_stop=True,
                    trailing_activation=Decimal('65'),
                    trailing_pullback=Decimal('0.20'),
                    protective_stop_multiplier=Decimal('2.0')
                )
            ]
            
            config = StrategyConfig(
                trade_size_in_lots=3,
                stop_loss_type=StopLossType.RANGE_BOUNDARY,
                lot_rules=lot_rules,
                trading_direction="BOTH",
                range_filter=RangeFilter(),
                risk_config=RiskConfig(),
                stop_loss_config=StopLossConfig()
            )
            
            logger.info("✅ 策略配置創建成功")
            logger.info(f"   交易口數: {config.trade_size_in_lots}")
            logger.info(f"   交易方向: {config.trading_direction}")
            logger.info(f"   口數規則數量: {len(config.lot_rules)}")
            
            return True
            
    except Exception as e:
        logger.error(f"❌ 策略配置測試失敗: {e}")
        return False

def main():
    """主測試函數"""
    logger.info("🚀 策略敏感度分析器測試開始")
    logger.info("=" * 50)
    
    tests = [
        ("導入測試", test_imports),
        ("SALib 基本功能測試", test_salib_basic),
        ("策略配置測試", test_strategy_config)
    ]
    
    passed = 0
    total = len(tests)
    
    for test_name, test_func in tests:
        logger.info(f"\n📋 執行: {test_name}")
        try:
            if test_func():
                logger.info(f"✅ {test_name} 通過")
                passed += 1
            else:
                logger.error(f"❌ {test_name} 失敗")
        except Exception as e:
            logger.error(f"❌ {test_name} 異常: {e}")
    
    logger.info("\n" + "=" * 50)
    logger.info(f"📊 測試結果: {passed}/{total} 通過")
    
    if passed == total:
        logger.info("🎉 所有測試通過！敏感度分析器準備就緒。")
        return True
    else:
        logger.error("⚠️ 部分測試失敗，請檢查環境配置。")
        return False

if __name__ == '__main__':
    success = main()
    sys.exit(0 if success else 1)
