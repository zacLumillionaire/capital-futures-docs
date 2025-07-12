#!/usr/bin/env python3
"""
快速測試修正後的系統
"""

import logging
from experiment_controller import ExperimentController

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def test_quick_run():
    """快速測試運行"""
    logger.info("🎯 快速測試修正後的系統")
    
    try:
        # 創建實驗控制器
        controller = ExperimentController()
        
        # 測試時間區間分析 - 使用 focused_mdd 配置
        logger.info("🧪 測試 focused_mdd 配置")
        
        results = controller.run_time_interval_analysis(
            start_date="2024-11-04",
            end_date="2024-11-06",  # 只測試3天
            config_name='focused_mdd',
            max_workers=2,
            sample_size=10  # 只測試10個組合
        )
        
        logger.info("✅ 測試成功完成！")
        logger.info(f"📊 結果摘要:")
        
        if 'time_interval_results' in results:
            interval_results = results['time_interval_results']
            logger.info(f"   時間區間數: {len(interval_results)}")
            
            for interval, data in interval_results.items():
                if 'best_config' in data:
                    best = data['best_config']
                    logger.info(f"   {interval}: MDD={best.get('mdd', 'N/A'):.2%}, 總PnL={best.get('total_pnl', 'N/A')}")
        
        return True
        
    except Exception as e:
        logger.error(f"❌ 測試失敗: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """主測試函數"""
    logger.info("🎯 開始快速測試")
    
    success = test_quick_run()
    
    if success:
        logger.info("🎊 快速測試通過！")
        logger.info("💡 系統已修正，可以正常使用:")
        logger.info("   python run_time_interval_analysis.py interactive")
        logger.info("   選擇 focused_mdd 配置")
        logger.info("   選擇兩種停損模式都測試")
    else:
        logger.error("❌ 快速測試失敗")

if __name__ == "__main__":
    main()
