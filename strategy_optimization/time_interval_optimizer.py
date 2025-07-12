#!/usr/bin/env python3
"""
時間區間優化器
專門用於多時間區間的MDD優化分析
整合 enhanced_mdd_optimizer 功能並適配當前策略
"""

import logging
import pandas as pd
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Any, Optional

from time_interval_config import TimeIntervalConfig
from enhanced_mdd_optimizer_adapted import EnhancedMDDOptimizer
from mdd_search_config_adapted import MDDSearchConfig

logger = logging.getLogger(__name__)

class TimeIntervalOptimizer:
    """時間區間優化器"""
    
    def __init__(self, start_date: str = None, end_date: str = None):
        self.config_manager = TimeIntervalConfig()
        self.start_date = start_date or "2024-11-04"
        self.end_date = end_date or "2025-06-27"
        
        # 結果存儲
        self.results_dir = Path("data/processed")
        self.results_dir.mkdir(exist_ok=True)
        
        logger.info("🎯 時間區間優化器初始化完成")
        logger.info(f"📅 回測期間: {self.start_date} 到 {self.end_date}")
    
    def set_date_range(self, start_date: str, end_date: str):
        """設定回測日期範圍"""
        self.start_date = start_date
        self.end_date = end_date
        logger.info(f"📅 更新回測期間: {start_date} 到 {end_date}")
    
    def list_available_configs(self) -> Dict[str, str]:
        """列出所有可用的配置"""
        return self.config_manager.list_available_configs()
    
    def run_time_interval_analysis(self, 
                                 config_name: str = 'standard_analysis',
                                 max_workers: int = 2,
                                 sample_size: Optional[int] = None) -> Dict[str, Any]:
        """執行時間區間分析"""
        
        logger.info(f"🚀 開始時間區間分析: {config_name}")
        
        # 獲取配置
        config = self.config_manager.get_config(config_name)
        logger.info(f"📊 {self.config_manager.get_config_summary(config)}")
        
        # 驗證配置
        is_valid, errors = self.config_manager.validate_config(config)
        if not is_valid:
            error_msg = f"配置驗證失敗: {'; '.join(errors)}"
            logger.error(error_msg)
            raise ValueError(error_msg)
        
        # 轉換為 enhanced_mdd_optimizer 格式
        mdd_config = self._convert_to_mdd_config(config)
        
        # 創建 MDD 優化器
        optimizer = EnhancedMDDOptimizer(config_name)
        optimizer.config = mdd_config
        optimizer.set_date_range(self.start_date, self.end_date)
        
        # 執行優化
        results = optimizer.run_optimization(
            max_workers=max_workers,
            sample_size=sample_size,
            individual_tp=True
        )
        
        # 處理和分析結果
        analysis_results = self._analyze_time_interval_results(results, config)
        
        # 保存結果
        self._save_analysis_results(analysis_results, config_name)
        
        return analysis_results
    
    def _convert_to_mdd_config(self, config: Dict[str, Any]) -> Dict[str, Any]:
        """將時間區間配置轉換為 MDD 優化器配置格式"""
        
        mdd_config = {
            'analysis_mode': 'per_time_interval',
            'time_intervals': config['time_intervals'],
            'stop_loss_ranges': config['stop_loss_ranges'],
            'take_profit_ranges': config['take_profit_ranges'],
            'optimization_target': config.get('optimization_target', 'mdd_minimization'),
            'stop_loss_modes': config.get('stop_loss_modes', {'fixed_points': True}),
            'trailing_stop_config': config.get('trailing_stop_config', {})
        }
        
        # 估算組合數
        interval_count = len(config['time_intervals'])
        stop_loss_combinations = (
            len(config['stop_loss_ranges']['lot1']) *
            len(config['stop_loss_ranges']['lot2']) *
            len(config['stop_loss_ranges']['lot3'])
        )
        
        unified_tp = len(config['take_profit_ranges']['unified'])
        individual_tp = len(config['take_profit_ranges']['individual']) ** 3
        boundary_tp = 1
        
        total_combinations = interval_count * stop_loss_combinations * (unified_tp + individual_tp + boundary_tp)
        
        mdd_config['estimated_combinations'] = {
            'per_interval_analysis': total_combinations,
            'breakdown': f"{stop_loss_combinations} 停損組合 × {unified_tp + individual_tp + boundary_tp} 停利模式 × {interval_count} 時間區間"
        }
        
        return mdd_config
    
    def _analyze_time_interval_results(self, results: List[Dict], config: Dict[str, Any]) -> Dict[str, Any]:
        """分析時間區間結果"""
        
        logger.info("📊 開始分析時間區間結果...")
        
        # 過濾成功的結果
        successful_results = [r for r in results if r.get('status') == 'success']
        
        if not successful_results:
            logger.error("❌ 沒有成功的實驗結果")
            return {'status': 'failed', 'error': 'No successful results'}
        
        # 轉換為 DataFrame
        df = pd.DataFrame(successful_results)
        
        # 按時間區間分組分析
        interval_analysis = {}
        time_intervals = df['time_interval'].unique()
        
        for interval in sorted(time_intervals):
            interval_df = df[df['time_interval'] == interval]
            interval_analysis[interval] = self._analyze_single_interval(interval_df)
        
        # 生成每日交易建議
        daily_recommendations = self._generate_daily_recommendations(interval_analysis)
        
        # 計算總體統計
        overall_stats = self._calculate_overall_stats(daily_recommendations)
        
        analysis_results = {
            'status': 'success',
            'config_name': config.get('name', '未命名'),
            'total_experiments': len(results),
            'successful_experiments': len(successful_results),
            'time_intervals_analyzed': len(time_intervals),
            'interval_analysis': interval_analysis,
            'daily_recommendations': daily_recommendations,
            'overall_stats': overall_stats,
            'raw_results': successful_results,
            'timestamp': datetime.now().isoformat()
        }
        
        return analysis_results
    
    def _analyze_single_interval(self, interval_df: pd.DataFrame) -> Dict[str, Any]:
        """分析單一時間區間的結果"""
        
        # 分別找固定停利和區間邊緣停利的最佳結果
        fixed_tp_df = interval_df[
            (interval_df.get('take_profit_mode', '') != 'range_boundary') &
            (~interval_df['experiment_id'].str.contains('RangeBoundary', na=False))
        ]
        boundary_df = interval_df[
            (interval_df.get('take_profit_mode', '') == 'range_boundary') |
            (interval_df['experiment_id'].str.contains('RangeBoundary', na=False))
        ]
        
        analysis = {
            'total_experiments': len(interval_df),
            'best_fixed_tp': None,
            'best_boundary_tp': None,
            'recommended_config': None,
            'stats': {
                'avg_mdd': interval_df['mdd'].mean(),
                'avg_pnl': interval_df['total_pnl'].mean(),
                'avg_win_rate': interval_df['win_rate'].mean()
            }
        }
        
        # 分析固定停利結果
        if not fixed_tp_df.empty:
            best_fixed_idx = fixed_tp_df['mdd'].idxmax()  # MDD最大(最小負值)
            analysis['best_fixed_tp'] = fixed_tp_df.loc[best_fixed_idx].to_dict()
        
        # 分析區間邊緣停利結果
        if not boundary_df.empty:
            best_boundary_idx = boundary_df['mdd'].idxmax()
            analysis['best_boundary_tp'] = boundary_df.loc[best_boundary_idx].to_dict()
        
        # 決定推薦配置
        if analysis['best_fixed_tp'] and analysis['best_boundary_tp']:
            if analysis['best_boundary_tp']['mdd'] > analysis['best_fixed_tp']['mdd']:
                analysis['recommended_config'] = analysis['best_boundary_tp']
                analysis['recommendation_reason'] = 'boundary_better_mdd'
            else:
                analysis['recommended_config'] = analysis['best_fixed_tp']
                analysis['recommendation_reason'] = 'fixed_better_mdd'
        elif analysis['best_boundary_tp']:
            analysis['recommended_config'] = analysis['best_boundary_tp']
            analysis['recommendation_reason'] = 'boundary_only'
        elif analysis['best_fixed_tp']:
            analysis['recommended_config'] = analysis['best_fixed_tp']
            analysis['recommendation_reason'] = 'fixed_only'
        
        return analysis
    
    def _generate_daily_recommendations(self, interval_analysis: Dict[str, Any]) -> List[Dict[str, Any]]:
        """生成每日交易配置建議"""
        
        recommendations = []
        
        for interval, analysis in interval_analysis.items():
            if analysis['recommended_config']:
                config = analysis['recommended_config']
                
                # 確定停利模式描述
                if config.get('take_profit_mode') == 'range_boundary':
                    tp_mode = "區間邊緣停利"
                elif 'take_profit' in config and pd.notna(config['take_profit']):
                    tp_mode = f"統一停利 TP:{int(config['take_profit'])}"
                elif 'lot1_take_profit' in config:
                    tp_mode = f"各口獨立停利 L1:{int(config['lot1_take_profit'])} L2:{int(config['lot2_take_profit'])} L3:{int(config['lot3_take_profit'])}"
                else:
                    tp_mode = "未知停利模式"
                
                recommendation = {
                    'time_interval': interval,
                    'mode': tp_mode,
                    'lot1_stop_loss': config['lot1_stop_loss'],
                    'lot2_stop_loss': config['lot2_stop_loss'],
                    'lot3_stop_loss': config['lot3_stop_loss'],
                    'mdd': config['mdd'],
                    'total_pnl': config['total_pnl'],
                    'win_rate': config['win_rate'],
                    'experiment_id': config['experiment_id'],
                    'recommendation_reason': analysis['recommendation_reason']
                }
                
                recommendations.append(recommendation)
        
        return recommendations
    
    def _calculate_overall_stats(self, recommendations: List[Dict[str, Any]]) -> Dict[str, Any]:
        """計算總體統計"""
        
        if not recommendations:
            return {}
        
        total_mdd = sum(rec['mdd'] for rec in recommendations)
        total_pnl = sum(rec['total_pnl'] for rec in recommendations)
        avg_win_rate = sum(rec['win_rate'] for rec in recommendations) / len(recommendations)
        
        # 統計停利模式分布
        mode_distribution = {}
        for rec in recommendations:
            mode_type = rec['mode'].split()[0]  # 取第一個詞作為類型
            mode_distribution[mode_type] = mode_distribution.get(mode_type, 0) + 1
        
        return {
            'total_intervals': len(recommendations),
            'expected_daily_mdd': total_mdd,
            'expected_daily_pnl': total_pnl,
            'average_win_rate': avg_win_rate,
            'mode_distribution': mode_distribution,
            'risk_adjusted_return': total_pnl / (abs(total_mdd) + 1) if total_mdd != 0 else 0
        }
    
    def _save_analysis_results(self, results: Dict[str, Any], config_name: str):
        """保存分析結果"""
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        # 保存完整結果 JSON
        results_file = self.results_dir / f"time_interval_analysis_{config_name}_{timestamp}.json"
        
        import json
        with open(results_file, 'w', encoding='utf-8') as f:
            json.dump(results, f, indent=2, ensure_ascii=False, default=str)
        
        logger.info(f"💾 分析結果已保存: {results_file}")
        
        # 保存每日建議 CSV
        if results.get('daily_recommendations'):
            recommendations_df = pd.DataFrame(results['daily_recommendations'])
            csv_file = self.results_dir / f"daily_recommendations_{config_name}_{timestamp}.csv"
            recommendations_df.to_csv(csv_file, index=False, encoding='utf-8-sig')
            logger.info(f"💾 每日建議已保存: {csv_file}")
        
        return results_file
