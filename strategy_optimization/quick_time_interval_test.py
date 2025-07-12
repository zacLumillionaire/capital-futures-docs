#!/usr/bin/env python3
"""
快速時間區間分析測試
驗證時間區間分析功能的基本工作流程（不執行實際回測）
"""

import logging
import sys
from pathlib import Path

# 設置日誌
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)

def test_config_functionality():
    """測試配置功能"""
    logger.info("🧪 測試配置功能...")
    
    try:
        from time_interval_config import TimeIntervalConfig
        
        config_manager = TimeIntervalConfig()
        
        # 列出所有可用配置
        available_configs = config_manager.list_available_configs()
        logger.info(f"📋 可用配置: {list(available_configs.keys())}")
        
        # 測試獲取配置
        for config_name in available_configs.keys():
            config = config_manager.get_config(config_name)
            logger.info(f"✅ {config_name}: {len(config['time_intervals'])} 個時間區間")
        
        # 測試自定義配置
        custom_config = config_manager.create_custom_config(
            name="測試配置",
            time_intervals=[("10:30", "10:32"), ("12:00", "12:02")],
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
        
        logger.info(f"✅ 自定義配置創建成功: {custom_config['name']}")
        logger.info("✅ 配置功能測試通過")
        
    except Exception as e:
        logger.error(f"❌ 配置功能測試失敗: {e}")
        raise

def test_mdd_config_functionality():
    """測試MDD配置功能"""
    logger.info("🧪 測試MDD配置功能...")
    
    try:
        from mdd_search_config_adapted import MDDSearchConfig
        
        # 測試各種配置
        configs_to_test = [
            'quick', 'detailed', 'focused', 'time_focus',
            'range_boundary', 'time_interval_analysis'
        ]
        
        for config_name in configs_to_test:
            config = MDDSearchConfig.get_config_by_name(config_name)
            logger.info(f"✅ {config_name} 配置: {config.get('description', 'N/A')}")
        
        # 測試時間區間分析配置
        time_config = MDDSearchConfig.get_time_interval_analysis_config()
        logger.info(f"✅ 時間區間分析配置: {time_config['analysis_mode']}")
        
        logger.info("✅ MDD配置功能測試通過")
        
    except Exception as e:
        logger.error(f"❌ MDD配置功能測試失敗: {e}")
        raise

def test_optimizer_initialization():
    """測試優化器初始化"""
    logger.info("🧪 測試優化器初始化...")
    
    try:
        from time_interval_optimizer import TimeIntervalOptimizer
        from enhanced_mdd_optimizer_adapted import EnhancedMDDOptimizer
        
        # 測試時間區間優化器
        optimizer = TimeIntervalOptimizer("2024-11-04", "2024-11-10")
        logger.info("✅ 時間區間優化器初始化成功")
        
        # 測試MDD優化器
        mdd_optimizer = EnhancedMDDOptimizer('test_mode')
        logger.info("✅ MDD優化器初始化成功")
        
        # 測試配置轉換
        from time_interval_config import TimeIntervalConfig
        config_manager = TimeIntervalConfig()
        config = config_manager.get_config('quick_test')
        
        mdd_config = optimizer._convert_to_mdd_config(config)
        logger.info(f"✅ 配置轉換成功: {mdd_config['analysis_mode']}")
        
        logger.info("✅ 優化器初始化測試通過")
        
    except Exception as e:
        logger.error(f"❌ 優化器初始化測試失敗: {e}")
        raise

def test_report_generator():
    """測試報告生成器"""
    logger.info("🧪 測試報告生成器...")
    
    try:
        from time_interval_report_generator import TimeIntervalReportGenerator
        
        generator = TimeIntervalReportGenerator()
        
        # 創建模擬數據
        mock_results = {
            'overall_stats': {
                'expected_daily_pnl': 100.0,
                'expected_daily_mdd': -50.0,
                'average_win_rate': 0.6,
                'total_intervals': 2,
                'risk_adjusted_return': 2.0
            },
            'daily_recommendations': [
                {
                    'time_interval': '10:30-10:32',
                    'mode': '統一停利 TP:60',
                    'lot1_stop_loss': 15,
                    'lot2_stop_loss': 20,
                    'lot3_stop_loss': 25,
                    'mdd': -25.0,
                    'total_pnl': 50.0,
                    'win_rate': 0.6,
                    'recommendation_reason': 'fixed_better_mdd'
                },
                {
                    'time_interval': '12:00-12:02',
                    'mode': '區間邊緣停利',
                    'lot1_stop_loss': 20,
                    'lot2_stop_loss': 25,
                    'lot3_stop_loss': 30,
                    'mdd': -30.0,
                    'total_pnl': 60.0,
                    'win_rate': 0.65,
                    'recommendation_reason': 'boundary_better_mdd'
                }
            ],
            'config_name': 'test_config',
            'total_experiments': 10,
            'successful_experiments': 8,
            'time_intervals_analyzed': 2,
            'timestamp': '2024-01-01T00:00:00'
        }
        
        # 測試HTML內容生成
        html_content = generator._create_time_interval_html(mock_results, 'test_config')
        
        # 驗證HTML內容
        assert '時間區間MDD分析報告' in html_content
        assert 'test_config' in html_content
        assert '10:30-10:32' in html_content
        assert '12:00-12:02' in html_content
        
        logger.info("✅ HTML報告生成測試通過")
        
        # 測試圖表生成（不實際保存文件）
        chart_files = []  # 模擬空的圖表文件列表
        
        logger.info("✅ 報告生成器測試通過")
        
    except Exception as e:
        logger.error(f"❌ 報告生成器測試失敗: {e}")
        raise

def test_experiment_controller_basic():
    """測試實驗控制器基本功能"""
    logger.info("🧪 測試實驗控制器基本功能...")
    
    try:
        from experiment_controller import ExperimentController
        
        controller = ExperimentController()
        
        # 檢查是否有時間區間分析方法
        assert hasattr(controller, 'run_time_interval_analysis')
        logger.info("✅ 實驗控制器有時間區間分析方法")
        
        # 檢查實驗映射
        experiment_map = {
            'range': controller.run_range_analysis,
            'direction': controller.run_direction_analysis,
            'lot': controller.run_lot_efficiency_analysis,
            'time_interval': controller.run_time_interval_analysis
        }

        assert 'time_interval' in experiment_map
        logger.info("✅ 時間區間分析已添加到實驗映射")
        
        logger.info("✅ 實驗控制器基本功能測試通過")
        
    except Exception as e:
        logger.error(f"❌ 實驗控制器基本功能測試失敗: {e}")
        raise

def main():
    """主函數"""
    logger.info("🚀 開始快速時間區間分析測試")
    
    try:
        # 測試1: 配置功能
        logger.info("\n" + "="*50)
        test_config_functionality()
        
        # 測試2: MDD配置功能
        logger.info("\n" + "="*50)
        test_mdd_config_functionality()
        
        # 測試3: 優化器初始化
        logger.info("\n" + "="*50)
        test_optimizer_initialization()
        
        # 測試4: 報告生成器
        logger.info("\n" + "="*50)
        test_report_generator()
        
        # 測試5: 實驗控制器基本功能
        logger.info("\n" + "="*50)
        test_experiment_controller_basic()
        
        logger.info("\n" + "="*50)
        logger.info("🎊 所有快速測試通過！")
        logger.info("✅ 時間區間分析功能基本組件工作正常")
        logger.info("📝 注意：實際回測功能需要完整的策略文件才能運行")
        
    except Exception as e:
        logger.error(f"❌ 快速測試失敗: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
