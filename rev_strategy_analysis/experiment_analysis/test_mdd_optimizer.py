#!/usr/bin/env python3
"""
MDD優化器測試腳本
快速驗證MDD最小化參數優化系統
"""

import os
import sys
import logging
from pathlib import Path

# 設定日誌
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def test_mdd_backtest_engine():
    """測試MDD回測引擎"""
    logger.info("🧪 測試MDD回測引擎...")
    
    try:
        from mdd_backtest_engine import MDDBacktestEngine
        
        # 創建測試配置
        test_config = {
            'start_date': '2024-11-04',
            'end_date': '2025-06-27',
            'range_start_time': '10:30',
            'range_end_time': '10:31',
            'trade_lots': 3,
            'fixed_stop_mode': True,
            'lot_settings': {
                'lot1': {'trigger': 15, 'trailing': 0},
                'lot2': {'trigger': 30, 'trailing': 0},
                'lot3': {'trigger': 45, 'trailing': 0}
            },
            'take_profit_points': 60,
            'filters': {
                'range_filter': {'enabled': False},
                'risk_filter': {'enabled': False},
                'stop_loss_filter': {'enabled': False}
            }
        }
        
        # 創建引擎並測試
        engine = MDDBacktestEngine()
        result = engine.run_experiment_backtest(test_config, "TEST_001")
        
        logger.info("✅ MDD回測引擎測試結果:")
        logger.info(f"   實驗ID: {result.get('experiment_id', 'N/A')}")
        logger.info(f"   總損益: {result.get('total_pnl', 0):.2f} 點")
        logger.info(f"   最大回撤: {result.get('max_drawdown', 0):.2f} 點")
        logger.info(f"   總交易數: {result.get('total_trades', 0)}")
        logger.info(f"   勝率: {result.get('win_rate', 0):.2f}%")
        logger.info(f"   第1口損益: {result.get('lot1_pnl', 0):.2f} 點")
        logger.info(f"   第2口損益: {result.get('lot2_pnl', 0):.2f} 點")
        logger.info(f"   第3口損益: {result.get('lot3_pnl', 0):.2f} 點")
        logger.info(f"   使用場景: {result.get('scenario_used', 'N/A')}")
        
        return True
        
    except Exception as e:
        logger.error(f"❌ MDD回測引擎測試失敗: {str(e)}")
        return False

def test_mdd_optimizer():
    """測試MDD優化器"""
    logger.info("🧪 測試MDD優化器...")
    
    try:
        from mdd_optimizer import MDDOptimizer
        
        # 創建優化器
        optimizer = MDDOptimizer()
        
        # 測試組合生成
        combinations = optimizer.generate_experiment_combinations()
        logger.info(f"✅ 生成了 {len(combinations)} 個實驗組合")
        
        # 顯示前5個組合
        logger.info("📋 前5個實驗組合:")
        for i, combo in enumerate(combinations[:5]):
            logger.info(f"   {i+1}. {combo['experiment_id']}")
            logger.info(f"      時間區間: {combo['time_interval']}")
            logger.info(f"      停損設定: L1={combo['lot1_stop_loss']} L2={combo['lot2_stop_loss']} L3={combo['lot3_stop_loss']}")
            logger.info(f"      停利設定: {combo['take_profit']}")
        
        # 測試配置創建
        test_params = combinations[0]
        config = optimizer.create_experiment_config(test_params)
        logger.info(f"✅ 配置創建測試成功")
        
        return True
        
    except Exception as e:
        logger.error(f"❌ MDD優化器測試失敗: {str(e)}")
        return False

def run_quick_mdd_test():
    """運行快速MDD測試"""
    logger.info("🚀 運行快速MDD測試 (5個樣本)...")
    
    try:
        from mdd_optimizer import MDDOptimizer
        
        optimizer = MDDOptimizer()
        
        # 運行小樣本測試
        results = optimizer.run_optimization(
            max_workers=1,  # 單進程避免複雜性
            sample_size=5   # 只測試5個樣本
        )
        
        if results is not None and len(results) > 0:
            logger.info("✅ 快速MDD測試成功完成！")
            logger.info(f"   獲得 {len(results)} 個有效結果")
            
            # 顯示最佳結果
            best_mdd = results.loc[results['max_drawdown'].idxmax()]
            logger.info("🏆 最佳MDD結果:")
            logger.info(f"   實驗ID: {best_mdd['experiment_id']}")
            logger.info(f"   MDD: {best_mdd['max_drawdown']:.2f} 點")
            logger.info(f"   總損益: {best_mdd['total_pnl']:.2f} 點")
            logger.info(f"   停損設定: L1={best_mdd['lot1_stop_loss']} L2={best_mdd['lot2_stop_loss']} L3={best_mdd['lot3_stop_loss']}")
            logger.info(f"   停利設定: {best_mdd['take_profit']}")
            
            return True
        else:
            logger.error("❌ 快速MDD測試未獲得有效結果")
            return False
            
    except Exception as e:
        logger.error(f"❌ 快速MDD測試失敗: {str(e)}")
        return False

def main():
    """主測試函數"""
    logger.info("🎯 開始MDD優化系統測試...")
    logger.info("="*60)
    
    # 確保結果目錄存在
    results_dir = Path("results")
    results_dir.mkdir(exist_ok=True)
    
    test_results = []
    
    # 測試1: MDD回測引擎
    logger.info("\n📋 測試1: MDD回測引擎")
    test_results.append(("MDD回測引擎", test_mdd_backtest_engine()))
    
    # 測試2: MDD優化器
    logger.info("\n📋 測試2: MDD優化器")
    test_results.append(("MDD優化器", test_mdd_optimizer()))
    
    # 測試3: 快速MDD測試
    logger.info("\n📋 測試3: 快速MDD測試")
    test_results.append(("快速MDD測試", run_quick_mdd_test()))
    
    # 總結測試結果
    logger.info("\n" + "="*60)
    logger.info("📊 測試結果總結:")
    logger.info("="*60)
    
    all_passed = True
    for test_name, result in test_results:
        status = "✅ 通過" if result else "❌ 失敗"
        logger.info(f"   {test_name}: {status}")
        if not result:
            all_passed = False
    
    if all_passed:
        logger.info("\n🎊 所有測試通過！MDD優化系統準備就緒！")
        logger.info("\n📖 使用說明:")
        logger.info("   快速測試: python mdd_optimizer.py --sample-size 20")
        logger.info("   完整優化: python mdd_optimizer.py")
        logger.info("   創建圖表: python mdd_optimizer.py --sample-size 50 --create-viz")
    else:
        logger.error("\n❌ 部分測試失敗，請檢查錯誤信息")
    
    return all_passed

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
