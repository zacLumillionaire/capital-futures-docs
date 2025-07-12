#!/usr/bin/env python3
"""
時間區間分析使用示例
展示如何使用新的時間區間分析功能
"""

import logging
import sys
from pathlib import Path

# 添加項目根目錄到路徑
project_root = Path(__file__).parent.parent
sys.path.append(str(project_root))

from experiment_controller import ExperimentController
from time_interval_optimizer import TimeIntervalOptimizer
from time_interval_config import TimeIntervalConfig
from time_interval_report_generator import TimeIntervalReportGenerator

# 設置日誌
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('time_interval_analysis.log', encoding='utf-8')
    ]
)

logger = logging.getLogger(__name__)

def example_1_basic_analysis():
    """示例1: 基本時間區間分析"""
    logger.info("🚀 示例1: 基本時間區間分析")
    
    try:
        # 使用 ExperimentController 執行分析
        controller = ExperimentController()
        
        # 執行標準時間區間分析
        result = controller.run_time_interval_analysis(
            start_date="2024-11-04",
            end_date="2025-06-27",
            config_name='quick_test',  # 使用快速測試配置
            max_workers=2,
            sample_size=50  # 限制樣本數量以加快測試
        )
        
        logger.info("✅ 基本分析完成")
        logger.info(f"📋 報告文件: {result['report_file']}")
        
        return result
        
    except Exception as e:
        logger.error(f"❌ 基本分析失敗: {e}")
        raise

def example_2_custom_config():
    """示例2: 自定義配置分析"""
    logger.info("🚀 示例2: 自定義配置分析")
    
    try:
        # 創建時間區間配置管理器
        config_manager = TimeIntervalConfig()
        
        # 創建自定義配置
        custom_config = config_manager.create_custom_config(
            name="測試配置",
            time_intervals=[
                ("10:30", "10:32"),
                ("12:30", "12:32")
            ],
            stop_loss_ranges={
                'lot1': [15, 20],
                'lot2': [20, 25],
                'lot3': [25, 30]
            },
            take_profit_ranges={
                'unified': [50, 60],
                'individual': [40, 50, 60]
            }
        )
        
        logger.info(f"📊 自定義配置摘要:\n{config_manager.get_config_summary(custom_config)}")
        
        # 使用自定義配置執行分析
        optimizer = TimeIntervalOptimizer("2024-11-04", "2025-06-27")
        
        # 注意：這裡需要將自定義配置保存到配置管理器中才能使用
        # 或者直接使用 optimizer 的內部方法
        
        logger.info("✅ 自定義配置示例完成")
        
    except Exception as e:
        logger.error(f"❌ 自定義配置分析失敗: {e}")
        raise

def example_3_comprehensive_analysis():
    """示例3: 綜合分析"""
    logger.info("🚀 示例3: 綜合分析")
    
    try:
        # 使用綜合分析配置
        controller = ExperimentController()
        
        result = controller.run_time_interval_analysis(
            config_name='standard_analysis',
            max_workers=4,  # 使用更多並行進程
            sample_size=None  # 不限制樣本數量
        )
        
        logger.info("✅ 綜合分析完成")
        
        # 生成額外的詳細報告
        report_generator = TimeIntervalReportGenerator()
        comprehensive_report = report_generator.generate_comprehensive_report(
            result['analysis_results'],
            'comprehensive_analysis'
        )
        
        logger.info(f"📋 綜合報告: {comprehensive_report}")
        
        return result
        
    except Exception as e:
        logger.error(f"❌ 綜合分析失敗: {e}")
        raise

def example_4_multiple_config_comparison():
    """示例4: 多配置比較"""
    logger.info("🚀 示例4: 多配置比較")
    
    try:
        controller = ExperimentController()
        
        # 測試多個配置
        configs_to_test = ['quick_test', 'focused_mdd']
        results = []
        
        for config_name in configs_to_test:
            logger.info(f"📊 測試配置: {config_name}")
            
            result = controller.run_time_interval_analysis(
                config_name=config_name,
                max_workers=2,
                sample_size=30  # 限制樣本以加快比較
            )
            
            results.append(result['analysis_results'])
        
        # 生成比較報告
        report_generator = TimeIntervalReportGenerator()
        comparison_report = report_generator.generate_comparison_report(
            results, configs_to_test
        )
        
        logger.info(f"📋 比較報告: {comparison_report}")
        logger.info("✅ 多配置比較完成")
        
        return comparison_report
        
    except Exception as e:
        logger.error(f"❌ 多配置比較失敗: {e}")
        raise

def example_5_list_available_configs():
    """示例5: 列出所有可用配置"""
    logger.info("🚀 示例5: 列出所有可用配置")
    
    try:
        config_manager = TimeIntervalConfig()
        available_configs = config_manager.list_available_configs()
        
        logger.info("📋 可用的時間區間配置:")
        for name, description in available_configs.items():
            logger.info(f"   {name}: {description}")
        
        # 顯示每個配置的詳細信息
        for name in available_configs.keys():
            config = config_manager.get_config(name)
            logger.info(f"\n📊 {name} 配置詳情:")
            logger.info(f"   時間區間數: {len(config['time_intervals'])}")
            logger.info(f"   預估實驗數: {config.get('estimated_experiments', 'N/A')}")
            
            if config['time_intervals']:
                logger.info(f"   時間區間: {config['time_intervals'][:3]}...")  # 顯示前3個
        
        logger.info("✅ 配置列表完成")
        
    except Exception as e:
        logger.error(f"❌ 配置列表失敗: {e}")
        raise

def main():
    """主函數 - 執行所有示例"""
    logger.info("🎯 開始時間區間分析示例")
    
    try:
        # 示例1: 基本分析
        logger.info("\n" + "="*60)
        example_1_basic_analysis()
        
        # 示例2: 自定義配置
        logger.info("\n" + "="*60)
        example_2_custom_config()
        
        # 示例5: 列出配置
        logger.info("\n" + "="*60)
        example_5_list_available_configs()
        
        # 可選：執行更複雜的示例（需要更多時間）
        run_advanced_examples = input("\n是否執行進階示例？(y/n): ").lower() == 'y'
        
        if run_advanced_examples:
            # 示例3: 綜合分析
            logger.info("\n" + "="*60)
            example_3_comprehensive_analysis()
            
            # 示例4: 多配置比較
            logger.info("\n" + "="*60)
            example_4_multiple_config_comparison()
        
        logger.info("\n🎊 所有示例執行完成！")
        logger.info("📁 請檢查 reports/ 目錄查看生成的報告")
        logger.info("📁 請檢查 data/processed/ 目錄查看原始結果")
        
    except Exception as e:
        logger.error(f"❌ 示例執行失敗: {e}")
        raise

if __name__ == "__main__":
    main()
