#!/usr/bin/env python3
"""
敏感度分析器調試腳本

用於診斷為什麼敏感度分析結果都是 nan
"""

import logging
import numpy as np
import pandas as pd
from decimal import Decimal

# 設定日誌
logging.basicConfig(level=logging.INFO, format='[%(asctime)s] %(levelname)s: %(message)s')
logger = logging.getLogger(__name__)

def test_single_backtest():
    """測試單次回測是否正常"""
    logger.info("🔍 測試單次回測...")
    
    try:
        import strategy_sensitivity_analyzer
        
        # 測試參數
        test_params = np.array([15.0, 0.20, 40.0, 0.15, 65.0, 0.25, 2.0])
        
        # 執行單次回測
        result = strategy_sensitivity_analyzer.evaluate_for_salib(
            test_params, 
            "BOTH", 
            "2024-11-04", 
            "2025-06-28", 
            "08:45", 
            "08:47"
        )
        
        logger.info(f"   單次回測結果: {result}")
        
        if result == -999999.0:
            logger.error("   ❌ 回測失敗，返回錯誤值")
            return False
        else:
            logger.info("   ✅ 單次回測成功")
            return True
            
    except Exception as e:
        logger.error(f"   ❌ 單次回測異常: {e}")
        return False

def test_multiple_backtests():
    """測試多次回測的變異性"""
    logger.info("🔍 測試多次回測變異性...")
    
    try:
        import strategy_sensitivity_analyzer
        from SALib.sample import sobol as sobol_sample
        
        # 使用小樣本測試
        problem = strategy_sensitivity_analyzer.problem
        param_values = sobol_sample.sample(problem, N=8)  # 只生成少量樣本
        
        logger.info(f"   生成了 {len(param_values)} 個測試樣本")
        
        results = []
        for i, params in enumerate(param_values[:10]):  # 只測試前10個
            result = strategy_sensitivity_analyzer.evaluate_for_salib(
                params, 
                "BOTH", 
                "2024-11-04", 
                "2025-06-28", 
                "08:45", 
                "08:47"
            )
            results.append(result)
            logger.info(f"   樣本 {i+1}: 參數={params[:3]}, 結果={result:.6f}")
        
        results = np.array(results)
        valid_results = results[results > -999999]
        
        if len(valid_results) > 0:
            logger.info(f"   📊 結果統計:")
            logger.info(f"      有效結果: {len(valid_results)}/{len(results)}")
            logger.info(f"      最小值: {valid_results.min():.6f}")
            logger.info(f"      最大值: {valid_results.max():.6f}")
            logger.info(f"      平均值: {valid_results.mean():.6f}")
            logger.info(f"      標準差: {valid_results.std():.6f}")
            logger.info(f"      唯一值: {len(np.unique(valid_results))}")
            
            if valid_results.std() < 1e-10:
                logger.warning("   ⚠️ 所有結果幾乎相同，這會導致敏感度分析失敗")
                return False
            else:
                logger.info("   ✅ 結果有足夠的變異性")
                return True
        else:
            logger.error("   ❌ 沒有有效結果")
            return False
            
    except Exception as e:
        logger.error(f"   ❌ 多次回測測試異常: {e}")
        return False

def test_calculate_backtest_metrics():
    """直接測試回測函數"""
    logger.info("🔍 測試回測函數...")
    
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
        
        # 執行回測
        result = strategy_sensitivity_analyzer.calculate_backtest_metrics(
            config, "2024-11-04", "2025-06-28", "08:45", "08:47", silent=False
        )
        
        logger.info(f"   📊 回測結果:")
        for key, value in result.items():
            logger.info(f"      {key}: {value}")
        
        if result['total_trades'] > 0:
            logger.info("   ✅ 回測函數正常，有交易記錄")
            return True
        else:
            logger.warning("   ⚠️ 回測函數正常，但沒有交易記錄")
            return False
            
    except Exception as e:
        logger.error(f"   ❌ 回測函數測試異常: {e}")
        return False

def test_data_availability():
    """測試數據可用性"""
    logger.info("🔍 測試數據可用性...")
    
    try:
        import sqlite_connection
        
        # 檢查數據庫連接
        with sqlite_connection.get_conn_cur_from_sqlite_with_adapter(as_dict=True) as (conn, cur):
            # 檢查數據範圍
            cur.execute("SELECT MIN(trade_datetime), MAX(trade_datetime), COUNT(*) FROM stock_prices")
            min_date, max_date, total_count = cur.fetchone().values()
            
            logger.info(f"   📊 數據統計:")
            logger.info(f"      數據範圍: {min_date} 到 {max_date}")
            logger.info(f"      總記錄數: {total_count}")
            
            # 檢查指定時間範圍的數據
            cur.execute("""
                SELECT COUNT(DISTINCT trade_datetime::date) as days,
                       COUNT(*) as records
                FROM stock_prices 
                WHERE trade_datetime::date BETWEEN '2024-11-04' AND '2025-06-28'
            """)
            result = cur.fetchone()
            days, records = result['days'], result['records']
            
            logger.info(f"   📊 目標時間範圍數據:")
            logger.info(f"      交易日數: {days}")
            logger.info(f"      記錄數: {records}")
            
            if days > 0:
                logger.info("   ✅ 數據可用")
                return True
            else:
                logger.error("   ❌ 目標時間範圍沒有數據")
                return False
                
    except Exception as e:
        logger.error(f"   ❌ 數據可用性測試異常: {e}")
        return False

def main():
    """主診斷函數"""
    logger.info("🚀 敏感度分析器診斷開始")
    logger.info("=" * 50)
    
    tests = [
        ("數據可用性測試", test_data_availability),
        ("回測函數測試", test_calculate_backtest_metrics),
        ("單次回測測試", test_single_backtest),
        ("多次回測變異性測試", test_multiple_backtests)
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
    logger.info("🔍 診斷完成")

if __name__ == '__main__':
    main()
