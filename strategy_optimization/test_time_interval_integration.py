#!/usr/bin/env python3
"""
時間區間分析功能集成測試
驗證所有組件是否正確集成和工作
"""

import logging
import sys
import unittest
from pathlib import Path
from unittest.mock import Mock, patch

# 添加項目根目錄到路徑
project_root = Path(__file__).parent.parent
sys.path.append(str(project_root))

# 設置日誌
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class TestTimeIntervalIntegration(unittest.TestCase):
    """時間區間分析集成測試"""
    
    def setUp(self):
        """測試設置"""
        self.test_start_date = "2024-11-04"
        self.test_end_date = "2024-11-10"  # 使用較短的測試期間
    
    def test_time_interval_config_import(self):
        """測試時間區間配置模組導入"""
        try:
            from time_interval_config import TimeIntervalConfig
            config_manager = TimeIntervalConfig()
            self.assertIsNotNone(config_manager)
            logger.info("✅ TimeIntervalConfig 導入成功")
        except ImportError as e:
            self.fail(f"❌ TimeIntervalConfig 導入失敗: {e}")
    
    def test_time_interval_optimizer_import(self):
        """測試時間區間優化器模組導入"""
        try:
            from time_interval_optimizer import TimeIntervalOptimizer
            optimizer = TimeIntervalOptimizer(self.test_start_date, self.test_end_date)
            self.assertIsNotNone(optimizer)
            logger.info("✅ TimeIntervalOptimizer 導入成功")
        except ImportError as e:
            self.fail(f"❌ TimeIntervalOptimizer 導入失敗: {e}")
    
    def test_enhanced_mdd_optimizer_adapted_import(self):
        """測試適配的MDD優化器模組導入"""
        try:
            from enhanced_mdd_optimizer_adapted import EnhancedMDDOptimizer
            optimizer = EnhancedMDDOptimizer('test_mode')
            self.assertIsNotNone(optimizer)
            logger.info("✅ EnhancedMDDOptimizer 適配版導入成功")
        except ImportError as e:
            self.fail(f"❌ EnhancedMDDOptimizer 適配版導入失敗: {e}")
    
    def test_mdd_search_config_adapted_import(self):
        """測試適配的MDD搜索配置模組導入"""
        try:
            from mdd_search_config_adapted import MDDSearchConfig
            config = MDDSearchConfig.get_quick_search_config()
            self.assertIsNotNone(config)
            logger.info("✅ MDDSearchConfig 適配版導入成功")
        except ImportError as e:
            self.fail(f"❌ MDDSearchConfig 適配版導入失敗: {e}")
    
    def test_time_interval_report_generator_import(self):
        """測試時間區間報告生成器模組導入"""
        try:
            from time_interval_report_generator import TimeIntervalReportGenerator
            generator = TimeIntervalReportGenerator()
            self.assertIsNotNone(generator)
            logger.info("✅ TimeIntervalReportGenerator 導入成功")
        except ImportError as e:
            self.fail(f"❌ TimeIntervalReportGenerator 導入失敗: {e}")
    
    def test_experiment_controller_integration(self):
        """測試實驗控制器集成"""
        try:
            from experiment_controller import ExperimentController
            controller = ExperimentController()
            
            # 檢查是否有時間區間分析方法
            self.assertTrue(hasattr(controller, 'run_time_interval_analysis'))
            logger.info("✅ ExperimentController 時間區間分析方法存在")
        except ImportError as e:
            self.fail(f"❌ ExperimentController 集成失敗: {e}")
    
    def test_config_manager_functionality(self):
        """測試配置管理器功能"""
        try:
            from time_interval_config import TimeIntervalConfig
            
            config_manager = TimeIntervalConfig()
            
            # 測試列出可用配置
            available_configs = config_manager.list_available_configs()
            self.assertIsInstance(available_configs, dict)
            self.assertGreater(len(available_configs), 0)
            
            # 測試獲取配置
            config = config_manager.get_config('quick_test')
            self.assertIsInstance(config, dict)
            self.assertIn('time_intervals', config)
            self.assertIn('stop_loss_ranges', config)
            
            # 測試自定義配置
            custom_config = config_manager.create_custom_config(
                name="測試配置",
                time_intervals=[("10:30", "10:32")],
                stop_loss_ranges={'lot1': [15], 'lot2': [20], 'lot3': [25]}
            )
            self.assertIsInstance(custom_config, dict)
            
            logger.info("✅ 配置管理器功能測試通過")
            
        except Exception as e:
            self.fail(f"❌ 配置管理器功能測試失敗: {e}")
    
    def test_mdd_search_config_functionality(self):
        """測試MDD搜索配置功能"""
        try:
            from mdd_search_config_adapted import MDDSearchConfig
            
            # 測試各種配置
            configs_to_test = [
                'quick', 'detailed', 'focused', 'time_focus',
                'range_boundary', 'time_interval_analysis'
            ]
            
            for config_name in configs_to_test:
                config = MDDSearchConfig.get_config_by_name(config_name)
                self.assertIsInstance(config, dict)
                logger.info(f"✅ {config_name} 配置測試通過")
            
            # 測試列出所有配置
            all_configs = MDDSearchConfig.list_all_configs()
            self.assertIsInstance(all_configs, dict)
            
            logger.info("✅ MDD搜索配置功能測試通過")
            
        except Exception as e:
            self.fail(f"❌ MDD搜索配置功能測試失敗: {e}")
    
    def test_enhanced_mdd_optimizer_basic_functionality(self):
        """測試增強MDD優化器基本功能（使用模擬）"""
        try:
            from enhanced_mdd_optimizer_adapted import EnhancedMDDOptimizer

            optimizer = EnhancedMDDOptimizer('test_mode')
            optimizer.set_date_range(self.test_start_date, self.test_end_date)

            # 測試生成實驗組合
            optimizer.config = {
                'stop_loss_ranges': {
                    'lot1': [15, 20],
                    'lot2': [20, 25],
                    'lot3': [25, 30]
                },
                'take_profit_ranges': {
                    'unified': [50, 60]
                },
                'time_intervals': [("10:30", "10:32")]
            }

            combinations = optimizer.generate_experiment_combinations()
            self.assertIsInstance(combinations, list)
            self.assertGreater(len(combinations), 0)

            logger.info("✅ 增強MDD優化器基本功能測試通過")
            
        except Exception as e:
            self.fail(f"❌ 增強MDD優化器基本功能測試失敗: {e}")
    
    def test_report_generator_basic_functionality(self):
        """測試報告生成器基本功能"""
        try:
            from time_interval_report_generator import TimeIntervalReportGenerator
            
            generator = TimeIntervalReportGenerator()
            
            # 測試模擬數據
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
                    }
                ],
                'config_name': 'test_config',
                'total_experiments': 10,
                'successful_experiments': 8,
                'time_intervals_analyzed': 2,
                'timestamp': '2024-01-01T00:00:00'
            }
            
            # 測試HTML報告生成（不實際生成文件）
            html_content = generator._create_time_interval_html(mock_results, 'test_config')
            self.assertIsInstance(html_content, str)
            self.assertIn('時間區間MDD分析報告', html_content)
            
            logger.info("✅ 報告生成器基本功能測試通過")
            
        except Exception as e:
            self.fail(f"❌ 報告生成器基本功能測試失敗: {e}")
    
    def test_integration_workflow(self):
        """測試完整集成工作流程（不執行實際回測）"""
        try:
            from time_interval_config import TimeIntervalConfig
            from time_interval_optimizer import TimeIntervalOptimizer
            
            # 1. 創建配置
            config_manager = TimeIntervalConfig()
            config = config_manager.get_config('quick_test')
            
            # 2. 創建優化器
            optimizer = TimeIntervalOptimizer(self.test_start_date, self.test_end_date)
            
            # 3. 驗證配置轉換
            mdd_config = optimizer._convert_to_mdd_config(config)
            self.assertIsInstance(mdd_config, dict)
            self.assertIn('analysis_mode', mdd_config)
            
            logger.info("✅ 集成工作流程測試通過")
            
        except Exception as e:
            self.fail(f"❌ 集成工作流程測試失敗: {e}")

def run_integration_tests():
    """執行集成測試"""
    logger.info("🧪 開始時間區間分析功能集成測試")
    
    # 創建測試套件
    test_suite = unittest.TestLoader().loadTestsFromTestCase(TestTimeIntervalIntegration)
    
    # 執行測試
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(test_suite)
    
    # 報告結果
    if result.wasSuccessful():
        logger.info("🎊 所有集成測試通過！")
        logger.info("✅ 時間區間分析功能已準備就緒")
    else:
        logger.error("❌ 部分集成測試失敗")
        logger.error(f"失敗數: {len(result.failures)}")
        logger.error(f"錯誤數: {len(result.errors)}")
    
    return result.wasSuccessful()

if __name__ == "__main__":
    success = run_integration_tests()
    sys.exit(0 if success else 1)
