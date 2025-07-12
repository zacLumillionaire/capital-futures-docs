#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
實驗執行控制器 - 反轉策略參數優化系統
主要控制器，協調參數優化和熱力圖生成

功能:
- 統一的實驗執行入口
- 自動化的完整實驗流程
- 結果分析和報告生成
- 錯誤處理和恢復機制
"""

import os
import sys
import time
import logging
from datetime import datetime
from pathlib import Path

# 添加當前目錄到Python路徑
current_dir = Path(__file__).parent
sys.path.insert(0, str(current_dir))

from parameter_optimizer import ParameterOptimizer
from heatmap_generator import HeatmapGenerator

# 設置日誌
log_dir = Path("results")
log_dir.mkdir(parents=True, exist_ok=True)

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(log_dir / 'experiment_runner.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class ExperimentRunner:
    """實驗執行控制器主類"""
    
    def __init__(self, config=None):
        """初始化實驗控制器
        
        Args:
            config: 實驗配置字典
        """
        self.config = config or {
            'max_workers': 2,  # 並行進程數
            'timeout_per_experiment': 300,  # 單個實驗超時時間（秒）
            'retry_failed': True,  # 是否重試失敗的實驗
            'generate_heatmaps': True,  # 是否生成熱力圖
            'save_intermediate_results': True,  # 是否保存中間結果
        }
        
        self.results_dir = Path("results")
        self.results_dir.mkdir(parents=True, exist_ok=True)
        
        self.optimizer = None
        self.heatmap_generator = None
        self.experiment_start_time = None
        
    def setup_experiment_environment(self):
        """設置實驗環境"""
        logger.info("🔧 設置實驗環境...")
        
        # 檢查必要的文件
        required_files = [
            "exp_rev_multi_Profit-Funded Risk_多口.py",
            "parameter_optimizer.py",
            "heatmap_generator.py"
        ]
        
        missing_files = []
        for file_path in required_files:
            if not Path(file_path).exists():
                missing_files.append(file_path)
        
        if missing_files:
            logger.error(f"❌ 缺少必要文件: {missing_files}")
            return False
        
        # 創建結果目錄結構
        subdirs = [
            "results/stop_loss_experiments",
            "results/take_profit_experiments",
            "results/heatmap_analysis"
        ]
        
        for subdir in subdirs:
            Path(subdir).mkdir(parents=True, exist_ok=True)
        
        logger.info("✅ 實驗環境設置完成")
        return True
    
    def run_parameter_optimization(self):
        """執行參數優化實驗"""
        logger.info("🚀 開始參數優化實驗...")
        self.experiment_start_time = time.time()
        
        # 創建優化器
        self.optimizer = ParameterOptimizer()
        
        # 執行批量實驗
        try:
            results = self.optimizer.run_batch_experiments(
                max_workers=self.config['max_workers']
            )
            
            if not results:
                logger.error("❌ 參數優化實驗失敗，沒有獲得任何結果")
                return False
            
            # 分析結果
            self.optimizer.analyze_results()
            
            # 保存結果
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            csv_path = self.optimizer.save_results_to_csv(
                f"parameter_optimization_results_{timestamp}.csv"
            )
            
            experiment_duration = time.time() - self.experiment_start_time
            logger.info(f"⏱️ 參數優化完成，耗時: {experiment_duration/60:.1f} 分鐘")
            
            return csv_path
            
        except Exception as e:
            logger.error(f"❌ 參數優化過程中發生錯誤: {e}")
            return False
    
    def generate_analysis_reports(self, csv_path):
        """生成分析報告和熱力圖"""
        if not self.config['generate_heatmaps']:
            logger.info("⏭️ 跳過熱力圖生成")
            return True
        
        logger.info("📊 開始生成分析報告和熱力圖...")
        
        try:
            # 創建熱力圖生成器
            self.heatmap_generator = HeatmapGenerator()
            
            # 載入實驗結果
            if not self.heatmap_generator.load_results_from_csv(csv_path):
                logger.error("❌ 無法載入實驗結果")
                return False
            
            # 生成所有熱力圖
            generated_files = self.heatmap_generator.generate_all_heatmaps()
            
            # 創建總結報告
            report_path = self.heatmap_generator.create_summary_report()
            
            # 找出最佳參數組合
            logger.info("\n" + "="*60)
            logger.info("🏆 最佳參數組合分析:")
            logger.info("="*60)
            
            metrics = ['total_pnl', 'long_pnl', 'short_pnl', 'win_rate']
            for metric in metrics:
                logger.info(f"\n📈 {metric} 最佳組合:")
                self.heatmap_generator.find_optimal_parameters(metric, top_n=3)
            
            logger.info(f"\n✅ 分析報告生成完成，共生成 {len(generated_files)} 個圖表文件")
            return True
            
        except Exception as e:
            logger.error(f"❌ 生成分析報告時發生錯誤: {e}")
            return False
    
    def create_experiment_summary(self, csv_path):
        """創建實驗總結"""
        summary_path = self.results_dir / "experiment_summary.txt"
        
        try:
            total_duration = time.time() - self.experiment_start_time
            
            with open(summary_path, 'w', encoding='utf-8') as f:
                f.write("=" * 80 + "\n")
                f.write("反轉策略參數優化實驗總結報告\n")
                f.write("=" * 80 + "\n\n")
                
                f.write(f"實驗開始時間: {datetime.fromtimestamp(self.experiment_start_time).strftime('%Y-%m-%d %H:%M:%S')}\n")
                f.write(f"實驗結束時間: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
                f.write(f"總耗時: {total_duration/60:.1f} 分鐘\n\n")
                
                f.write("實驗配置:\n")
                for key, value in self.config.items():
                    f.write(f"  {key}: {value}\n")
                f.write("\n")
                
                f.write("實驗範圍:\n")
                f.write("  停損點: 15-100點，步長5點 (18個測試點)\n")
                f.write("  停利點: 30-100點，步長10點 (8個測試點)\n")
                f.write("  時間區間: 10:30~10:31, 11:30~11:31, 12:30~12:31 (3個區間)\n")
                f.write("  總實驗次數: 18×8×3 = 432次\n\n")
                
                if self.optimizer and self.optimizer.results:
                    f.write(f"實際完成實驗: {len(self.optimizer.results)} 次\n")
                    f.write(f"成功率: {len(self.optimizer.results)/432*100:.1f}%\n\n")
                
                f.write("生成文件:\n")
                f.write(f"  實驗結果CSV: {csv_path}\n")
                f.write(f"  熱力圖分析: results/heatmap_analysis/\n")
                f.write(f"  日誌文件: results/experiment_runner.log\n")
                
            logger.info(f"📋 實驗總結已保存: {summary_path}")
            return summary_path
            
        except Exception as e:
            logger.error(f"❌ 創建實驗總結時發生錯誤: {e}")
            return None
    
    def run_complete_experiment(self):
        """執行完整的實驗流程"""
        logger.info("🎯 開始完整實驗流程...")
        logger.info("=" * 80)
        
        # 1. 設置環境
        if not self.setup_experiment_environment():
            logger.error("❌ 實驗環境設置失敗")
            return False
        
        # 2. 執行參數優化
        csv_path = self.run_parameter_optimization()
        if not csv_path:
            logger.error("❌ 參數優化失敗")
            return False
        
        # 3. 生成分析報告
        if not self.generate_analysis_reports(csv_path):
            logger.error("❌ 分析報告生成失敗")
            return False
        
        # 4. 創建實驗總結
        summary_path = self.create_experiment_summary(csv_path)
        
        # 5. 完成提示
        total_duration = time.time() - self.experiment_start_time
        logger.info("=" * 80)
        logger.info("🎉 完整實驗流程執行完成！")
        logger.info(f"⏱️ 總耗時: {total_duration/60:.1f} 分鐘")
        logger.info(f"📊 實驗結果: {csv_path}")
        if summary_path:
            logger.info(f"📋 實驗總結: {summary_path}")
        logger.info("📈 熱力圖分析: results/heatmap_analysis/")
        logger.info("=" * 80)
        
        return True
    
    def run_quick_test(self, sample_size=10):
        """執行快速測試（少量實驗組合）"""
        logger.info(f"⚡ 開始快速測試 (樣本數: {sample_size})...")
        
        # 修改優化器以只執行部分實驗
        self.optimizer = ParameterOptimizer()
        
        # 生成所有組合但只取前N個
        all_combinations = self.optimizer.generate_experiment_combinations()
        test_combinations = all_combinations[:sample_size]
        
        logger.info(f"🧪 執行 {len(test_combinations)} 個測試實驗...")
        
        results = []
        for combination in test_combinations:
            result = self.optimizer.run_single_experiment(combination)
            if result:
                results.append(result)
        
        if results:
            self.optimizer.results = results
            csv_path = self.optimizer.save_results_to_csv("quick_test_results.csv")
            logger.info(f"✅ 快速測試完成，結果保存至: {csv_path}")
            return csv_path
        else:
            logger.error("❌ 快速測試失敗")
            return False


def main():
    """主函數"""
    import argparse
    
    parser = argparse.ArgumentParser(description='反轉策略參數優化實驗控制器')
    parser.add_argument('--quick-test', action='store_true', help='執行快速測試')
    parser.add_argument('--sample-size', type=int, default=10, help='快速測試樣本數')
    parser.add_argument('--max-workers', type=int, default=2, help='並行進程數')
    parser.add_argument('--no-heatmaps', action='store_true', help='不生成熱力圖')
    
    args = parser.parse_args()
    
    # 創建實驗配置
    config = {
        'max_workers': args.max_workers,
        'timeout_per_experiment': 300,
        'retry_failed': True,
        'generate_heatmaps': not args.no_heatmaps,
        'save_intermediate_results': True,
    }
    
    # 創建實驗控制器
    runner = ExperimentRunner(config)
    
    # 執行實驗
    if args.quick_test:
        success = runner.run_quick_test(args.sample_size)
    else:
        success = runner.run_complete_experiment()
    
    if success:
        logger.info("🎊 實驗執行成功！")
        sys.exit(0)
    else:
        logger.error("💥 實驗執行失敗！")
        sys.exit(1)


if __name__ == "__main__":
    main()
