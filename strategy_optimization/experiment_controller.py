# experiment_controller.py - 實驗控制器
"""
統一控制所有策略優化實驗
提供簡單的介面來執行各種分析
"""

import logging
import argparse
import sys
import os
from pathlib import Path
from datetime import datetime
import json

# 導入數據庫初始化
from app_setup import init_all_db_pools

# 導入各個分析器
from range_analyzer import RangeAnalyzer
from direction_optimizer import DirectionOptimizer
from lot_efficiency_analyzer import LotEfficiencyAnalyzer
from time_interval_optimizer import TimeIntervalOptimizer

# 設定日誌
logging.basicConfig(
    level=logging.INFO,
    format='[%(asctime)s] %(levelname)s [%(name)s] %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
logger = logging.getLogger(__name__)

class ExperimentController:
    """實驗控制器主類別"""
    
    def __init__(self):
        self.results = {}
        self.start_time = datetime.now()

        # 初始化數據庫連接池
        try:
            logger.info("🔌 初始化數據庫連接池...")
            init_all_db_pools()
            logger.info("✅ 數據庫連接池初始化成功")
        except Exception as e:
            logger.error(f"❌ 數據庫連接池初始化失敗: {e}")
            raise
        
    def run_all_experiments(self, start_date: str = None, end_date: str = None):
        """執行所有實驗"""
        logger.info("🚀 開始執行完整的策略優化實驗套件...")
        
        experiments = [
            ("range_analysis", "開盤區間分析", self.run_range_analysis),
            ("direction_analysis", "方向性偏差分析", self.run_direction_analysis),
            ("lot_efficiency", "口數效率分析", self.run_lot_efficiency_analysis),
            ("time_interval_analysis", "時間區間MDD分析", self.run_time_interval_analysis)
        ]
        
        for exp_name, exp_desc, exp_func in experiments:
            try:
                logger.info(f"📊 開始執行: {exp_desc}")
                result = exp_func(start_date, end_date)
                self.results[exp_name] = {
                    'status': 'success',
                    'result': result,
                    'timestamp': datetime.now().isoformat()
                }
                logger.info(f"✅ {exp_desc} 完成")
            except Exception as e:
                logger.error(f"❌ {exp_desc} 失敗: {e}")
                self.results[exp_name] = {
                    'status': 'failed',
                    'error': str(e),
                    'timestamp': datetime.now().isoformat()
                }
        
        # 生成綜合報告
        self.generate_comprehensive_report()
        
        logger.info("🎉 所有實驗完成！")
    
    def run_range_analysis(self, start_date: str = None, end_date: str = None):
        """執行開盤區間分析"""
        analyzer = RangeAnalyzer()
        
        # 收集區間統計數據
        range_df = analyzer.collect_range_statistics(start_date, end_date)
        
        if range_df.empty:
            raise Exception("無法收集區間數據")
        
        # 分析區間大小分布
        stats = analyzer.analyze_range_size_distribution(range_df)
        
        # 測試不同過濾閾值
        thresholds = [20, 25, 30, 35, 40, 45, 50, 60, 70]
        filter_results = analyzer.test_range_filters(thresholds, start_date, end_date)
        
        # 生成報告
        report_file = analyzer.create_range_analysis_report(range_df, filter_results)
        
        return {
            'range_statistics': stats,
            'filter_test_results': filter_results.to_dict('records') if not filter_results.empty else [],
            'report_file': report_file,
            'total_days': len(range_df)
        }
    
    def run_direction_analysis(self, start_date: str = None, end_date: str = None):
        """執行方向性偏差分析"""
        optimizer = DirectionOptimizer()
        
        # 執行方向性比較
        comparison_results = optimizer.run_directional_comparison(start_date, end_date)
        
        # 生成報告
        report_file = optimizer.create_direction_analysis_report(comparison_results)
        
        return {
            'comparison_results': comparison_results,
            'report_file': report_file
        }
    
    def run_lot_efficiency_analysis(self, start_date: str = None, end_date: str = None):
        """執行口數效率分析"""
        analyzer = LotEfficiencyAnalyzer()
        
        # 執行口數比較
        comparison_results = analyzer.run_lot_comparison(start_date, end_date)
        
        # 分析個別口數表現
        individual_analysis = analyzer.analyze_individual_lot_performance(start_date, end_date)
        
        # 生成報告
        report_file = analyzer.create_lot_analysis_report(comparison_results, individual_analysis)
        
        return {
            'comparison_results': comparison_results,
            'individual_analysis': individual_analysis,
            'report_file': report_file
        }
    
    def run_single_experiment(self, experiment_name: str, start_date: str = None, end_date: str = None):
        """執行單一實驗"""
        experiment_map = {
            'range': self.run_range_analysis,
            'direction': self.run_direction_analysis,
            'lot': self.run_lot_efficiency_analysis,
            'time_interval': self.run_time_interval_analysis
        }
        
        if experiment_name not in experiment_map:
            raise ValueError(f"未知的實驗名稱: {experiment_name}")
        
        logger.info(f"🧪 執行單一實驗: {experiment_name}")
        return experiment_map[experiment_name](start_date, end_date)

    def run_time_interval_analysis(self, start_date: str = None, end_date: str = None,
                                 config_name: str = 'standard_analysis',
                                 max_workers: int = 2,
                                 sample_size: int = None):
        """執行時間區間MDD分析"""
        logger.info("🕙 開始時間區間MDD分析...")

        try:
            # 創建時間區間優化器
            optimizer = TimeIntervalOptimizer(start_date, end_date)

            # 列出可用配置
            available_configs = optimizer.list_available_configs()
            logger.info(f"📋 可用配置: {list(available_configs.keys())}")

            # 執行分析
            results = optimizer.run_time_interval_analysis(
                config_name=config_name,
                max_workers=max_workers,
                sample_size=sample_size
            )

            # 生成報告
            report_file = self._generate_time_interval_report(results, config_name)

            logger.info("✅ 時間區間MDD分析完成")

            return {
                'analysis_results': results,
                'report_file': report_file,
                'config_used': config_name,
                'available_configs': available_configs
            }

        except Exception as e:
            logger.error(f"❌ 時間區間分析失敗: {e}")
            raise

    def _generate_time_interval_report(self, results: dict, config_name: str) -> str:
        """生成時間區間分析報告"""
        logger.info("📋 生成時間區間分析報告...")

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        report_file = f"reports/time_interval_analysis_{config_name}_{timestamp}.html"

        # 創建報告目錄
        os.makedirs("reports", exist_ok=True)

        # 生成HTML報告
        html_content = self._create_time_interval_html(results, config_name)

        with open(report_file, 'w', encoding='utf-8') as f:
            f.write(html_content)

        logger.info(f"✅ 時間區間分析報告已生成: {report_file}")
        return report_file

    def _create_time_interval_html(self, results: dict, config_name: str) -> str:
        """創建時間區間分析HTML報告"""

        # 基本信息
        overall_stats = results.get('overall_stats', {})
        daily_recommendations = results.get('daily_recommendations', [])
        interval_analysis = results.get('interval_analysis', {})

        html_content = f"""
<!DOCTYPE html>
<html lang="zh-TW">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>時間區間MDD分析報告 - {config_name}</title>
    <style>
        body {{ font-family: 'Microsoft JhengHei', Arial, sans-serif; margin: 20px; background-color: #f5f5f5; }}
        .container {{ max-width: 1200px; margin: 0 auto; background: white; padding: 30px; border-radius: 10px; box-shadow: 0 0 20px rgba(0,0,0,0.1); }}
        .header {{ text-align: center; margin-bottom: 30px; padding: 20px; background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; border-radius: 10px; }}
        .section {{ margin: 30px 0; padding: 20px; border: 1px solid #ddd; border-radius: 8px; background: #fafafa; }}
        .section h2 {{ color: #333; border-bottom: 2px solid #667eea; padding-bottom: 10px; }}
        .stats-grid {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 15px; margin: 20px 0; }}
        .stat-card {{ background: white; padding: 15px; border-radius: 8px; text-align: center; box-shadow: 0 2px 5px rgba(0,0,0,0.1); }}
        .stat-value {{ font-size: 24px; font-weight: bold; color: #667eea; }}
        .stat-label {{ color: #666; margin-top: 5px; }}
        .recommendations-table {{ width: 100%; border-collapse: collapse; margin: 20px 0; }}
        .recommendations-table th, .recommendations-table td {{ border: 1px solid #ddd; padding: 12px; text-align: center; }}
        .recommendations-table th {{ background-color: #667eea; color: white; }}
        .recommendations-table tr:nth-child(even) {{ background-color: #f9f9f9; }}
        .interval-details {{ margin: 15px 0; padding: 15px; background: white; border-radius: 5px; }}
        .positive {{ color: #28a745; }}
        .negative {{ color: #dc3545; }}
        .neutral {{ color: #6c757d; }}
        .highlight {{ background-color: #fff3cd; border-left: 4px solid #ffc107; padding: 10px; margin: 10px 0; }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>🕙 時間區間MDD分析報告</h1>
            <p>配置: {config_name} | 生成時間: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
        </div>

        <div class="section">
            <h2>📊 總體統計</h2>
            <div class="stats-grid">
                <div class="stat-card">
                    <div class="stat-value {'positive' if overall_stats.get('expected_daily_pnl', 0) > 0 else 'negative'}">{overall_stats.get('expected_daily_pnl', 0):.2f}</div>
                    <div class="stat-label">預期每日損益</div>
                </div>
                <div class="stat-card">
                    <div class="stat-value negative">{overall_stats.get('expected_daily_mdd', 0):.2f}</div>
                    <div class="stat-label">預期每日MDD</div>
                </div>
                <div class="stat-card">
                    <div class="stat-value neutral">{overall_stats.get('average_win_rate', 0):.2%}</div>
                    <div class="stat-label">平均勝率</div>
                </div>
                <div class="stat-card">
                    <div class="stat-value neutral">{overall_stats.get('total_intervals', 0)}</div>
                    <div class="stat-label">分析區間數</div>
                </div>
                <div class="stat-card">
                    <div class="stat-value neutral">{overall_stats.get('risk_adjusted_return', 0):.3f}</div>
                    <div class="stat-label">風險調整收益</div>
                </div>
            </div>
        </div>

        <div class="section">
            <h2>📋 每日交易配置建議</h2>
            <table class="recommendations-table">
                <thead>
                    <tr>
                        <th>時間區間</th>
                        <th>停利模式</th>
                        <th>L1停損</th>
                        <th>L2停損</th>
                        <th>L3停損</th>
                        <th>MDD</th>
                        <th>損益</th>
                        <th>勝率</th>
                        <th>推薦原因</th>
                    </tr>
                </thead>
                <tbody>
        """

        # 添加每日建議表格內容
        for rec in daily_recommendations:
            reason_map = {
                'boundary_better_mdd': '區間邊緣MDD更佳',
                'fixed_better_mdd': '固定停利MDD更佳',
                'boundary_only': '僅區間邊緣可用',
                'fixed_only': '僅固定停利可用'
            }
            reason_text = reason_map.get(rec.get('recommendation_reason', ''), '未知')

            html_content += f"""
                    <tr>
                        <td>{rec['time_interval']}</td>
                        <td>{rec['mode']}</td>
                        <td>{int(rec['lot1_stop_loss'])}</td>
                        <td>{int(rec['lot2_stop_loss'])}</td>
                        <td>{int(rec['lot3_stop_loss'])}</td>
                        <td class="{'positive' if rec['mdd'] > 0 else 'negative'}">{rec['mdd']:.2f}</td>
                        <td class="{'positive' if rec['total_pnl'] > 0 else 'negative'}">{rec['total_pnl']:.2f}</td>
                        <td>{rec['win_rate']:.2%}</td>
                        <td>{reason_text}</td>
                    </tr>
            """

        html_content += """
                </tbody>
            </table>
        </div>
        """

        # 添加各區間詳細分析
        if interval_analysis:
            html_content += """
        <div class="section">
            <h2>🔍 各時間區間詳細分析</h2>
            """

            for interval, analysis in interval_analysis.items():
                html_content += f"""
            <div class="interval-details">
                <h3>🕙 {interval}</h3>
                <p><strong>實驗數量:</strong> {analysis['total_experiments']}</p>
                <p><strong>平均MDD:</strong> <span class="negative">{analysis['stats']['avg_mdd']:.2f}</span></p>
                <p><strong>平均損益:</strong> <span class="{'positive' if analysis['stats']['avg_pnl'] > 0 else 'negative'}">{analysis['stats']['avg_pnl']:.2f}</span></p>
                <p><strong>平均勝率:</strong> {analysis['stats']['avg_win_rate']:.2%}</p>
                """

                if analysis.get('best_fixed_tp'):
                    fixed = analysis['best_fixed_tp']
                    html_content += f"""
                <div class="highlight">
                    <strong>最佳固定停利:</strong> MDD {fixed['mdd']:.2f}, 損益 {fixed['total_pnl']:.2f},
                    停損 L1:{int(fixed['lot1_stop_loss'])} L2:{int(fixed['lot2_stop_loss'])} L3:{int(fixed['lot3_stop_loss'])}
                </div>
                """

                if analysis.get('best_boundary_tp'):
                    boundary = analysis['best_boundary_tp']
                    html_content += f"""
                <div class="highlight">
                    <strong>最佳區間邊緣:</strong> MDD {boundary['mdd']:.2f}, 損益 {boundary['total_pnl']:.2f},
                    停損 L1:{int(boundary['lot1_stop_loss'])} L2:{int(boundary['lot2_stop_loss'])} L3:{int(boundary['lot3_stop_loss'])}
                </div>
                """

                html_content += "</div>"

            html_content += "</div>"

        # 結尾
        html_content += f"""
        <div class="section">
            <h2>📈 實驗摘要</h2>
            <p><strong>配置名稱:</strong> {results.get('config_name', config_name)}</p>
            <p><strong>總實驗數:</strong> {results.get('total_experiments', 0)}</p>
            <p><strong>成功實驗數:</strong> {results.get('successful_experiments', 0)}</p>
            <p><strong>分析時間區間數:</strong> {results.get('time_intervals_analyzed', 0)}</p>
            <p><strong>生成時間:</strong> {results.get('timestamp', datetime.now().isoformat())}</p>
        </div>
    </div>
</body>
</html>
        """

        return html_content
    
    def generate_comprehensive_report(self):
        """生成綜合實驗報告"""
        logger.info("📋 生成綜合實驗報告...")
        
        # 創建綜合報告HTML
        html_content = self._create_comprehensive_html()
        
        # 保存報告
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        report_file = f"reports/comprehensive_experiment_report_{timestamp}.html"
        
        with open(report_file, 'w', encoding='utf-8') as f:
            f.write(html_content)
        
        # 保存結果JSON
        results_file = f"data/processed/experiment_results_{timestamp}.json"
        with open(results_file, 'w', encoding='utf-8') as f:
            json.dump(self.results, f, indent=2, ensure_ascii=False, default=str)
        
        logger.info(f"✅ 綜合報告已生成: {report_file}")
        logger.info(f"✅ 實驗結果已保存: {results_file}")
        
        return report_file
    
    def _create_comprehensive_html(self) -> str:
        """創建綜合HTML報告"""
        execution_time = (datetime.now() - self.start_time).total_seconds()
        
        html = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <title>Comprehensive Strategy Optimization Report</title>
            <style>
                body {{ font-family: Arial, sans-serif; margin: 20px; line-height: 1.6; }}
                .header {{ background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); 
                          color: white; padding: 30px; border-radius: 10px; text-align: center; }}
                .summary {{ background-color: #f8f9fa; padding: 20px; border-radius: 5px; margin: 20px 0; }}
                .experiment {{ margin: 30px 0; padding: 20px; border: 1px solid #ddd; border-radius: 5px; }}
                .success {{ border-left: 5px solid #28a745; }}
                .failed {{ border-left: 5px solid #dc3545; }}
                .metrics {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 15px; margin: 20px 0; }}
                .metric-card {{ background: white; padding: 15px; border-radius: 5px; box-shadow: 0 2px 4px rgba(0,0,0,0.1); }}
                .metric-value {{ font-size: 24px; font-weight: bold; color: #2c3e50; }}
                .metric-label {{ color: #7f8c8d; font-size: 14px; }}
                .recommendations {{ background-color: #fff3cd; padding: 20px; border-radius: 5px; border-left: 5px solid #ffc107; }}
                .nav {{ background-color: #343a40; padding: 10px; border-radius: 5px; margin: 20px 0; }}
                .nav a {{ color: white; text-decoration: none; margin: 0 15px; }}
                .nav a:hover {{ text-decoration: underline; }}
            </style>
        </head>
        <body>
            <div class="header">
                <h1>🚀 Strategy Optimization Experiment Report</h1>
                <p>Comprehensive Analysis of Profit-Funded Risk Multi-Lot Strategy</p>
                <p>Generated on: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
                <p>Execution Time: {execution_time:.1f} seconds</p>
            </div>
            
            <div class="nav">
                <a href="#summary">📊 Executive Summary</a>
                <a href="#range">📏 Range Analysis</a>
                <a href="#direction">🎯 Direction Analysis</a>
                <a href="#lot">💼 Lot Efficiency</a>
                <a href="#recommendations">💡 Recommendations</a>
            </div>
            
            <div id="summary" class="summary">
                <h2>📊 Executive Summary</h2>
                {self._generate_executive_summary()}
            </div>
            
            <div id="experiments">
                {self._generate_experiment_sections()}
            </div>
            
            <div id="recommendations" class="recommendations">
                <h2>💡 Strategic Recommendations</h2>
                {self._generate_recommendations()}
            </div>
            
            <div class="summary">
                <h2>📁 Generated Reports</h2>
                {self._generate_report_links()}
            </div>
        </body>
        </html>
        """
        
        return html
    
    def _generate_executive_summary(self) -> str:
        """生成執行摘要"""
        total_experiments = len(self.results)
        successful_experiments = sum(1 for r in self.results.values() if r['status'] == 'success')
        
        summary = f"""
        <div class="metrics">
            <div class="metric-card">
                <div class="metric-value">{total_experiments}</div>
                <div class="metric-label">Total Experiments</div>
            </div>
            <div class="metric-card">
                <div class="metric-value">{successful_experiments}</div>
                <div class="metric-label">Successful</div>
            </div>
            <div class="metric-card">
                <div class="metric-value">{total_experiments - successful_experiments}</div>
                <div class="metric-label">Failed</div>
            </div>
            <div class="metric-card">
                <div class="metric-value">{(successful_experiments/total_experiments*100):.0f}%</div>
                <div class="metric-label">Success Rate</div>
            </div>
        </div>
        
        <p>This comprehensive analysis examined the Profit-Funded Risk multi-lot strategy across three key dimensions:</p>
        <ul>
            <li><strong>Range Analysis</strong>: Opening range size impact on profitability</li>
            <li><strong>Direction Bias</strong>: Long vs Short performance comparison</li>
            <li><strong>Lot Efficiency</strong>: Marginal utility of each trading lot</li>
        </ul>
        """
        
        return summary
    
    def _generate_experiment_sections(self) -> str:
        """生成實驗結果區段"""
        sections = ""
        
        experiment_titles = {
            'range_analysis': '📏 Opening Range Analysis',
            'direction_analysis': '🎯 Direction Bias Analysis', 
            'lot_efficiency': '💼 Lot Efficiency Analysis'
        }
        
        for exp_name, result in self.results.items():
            title = experiment_titles.get(exp_name, exp_name.title())
            status_class = "success" if result['status'] == 'success' else "failed"
            
            sections += f"""
            <div id="{exp_name}" class="experiment {status_class}">
                <h2>{title}</h2>
                <p><strong>Status:</strong> {result['status'].title()}</p>
                <p><strong>Timestamp:</strong> {result['timestamp']}</p>
                
                {self._generate_experiment_details(exp_name, result)}
            </div>
            """
        
        return sections
    
    def _generate_experiment_details(self, exp_name: str, result: dict) -> str:
        """生成實驗詳細內容"""
        if result['status'] == 'failed':
            return f"<p><strong>Error:</strong> {result.get('error', 'Unknown error')}</p>"
        
        if exp_name == 'range_analysis':
            return self._generate_range_details(result['result'])
        elif exp_name == 'direction_analysis':
            return self._generate_direction_details(result['result'])
        elif exp_name == 'lot_efficiency':
            return self._generate_lot_details(result['result'])
        
        return "<p>Details not available.</p>"
    
    def _generate_range_details(self, result: dict) -> str:
        """生成區間分析詳細內容"""
        stats = result.get('range_statistics', {})
        
        return f"""
        <div class="metrics">
            <div class="metric-card">
                <div class="metric-value">{result.get('total_days', 0)}</div>
                <div class="metric-label">Trading Days Analyzed</div>
            </div>
            <div class="metric-card">
                <div class="metric-value">{stats.get('mean_range', 0):.1f}</div>
                <div class="metric-label">Average Range Size (pts)</div>
            </div>
            <div class="metric-card">
                <div class="metric-value">{stats.get('breakout_rate', 0):.1%}</div>
                <div class="metric-label">Breakout Rate</div>
            </div>
        </div>
        <p><strong>Report:</strong> <a href="{result.get('report_file', '#')}">View Detailed Range Analysis</a></p>
        """
    
    def _generate_direction_details(self, result: dict) -> str:
        """生成方向分析詳細內容"""
        comparison = result.get('comparison_results', {})
        
        details = "<h3>Performance Comparison:</h3><ul>"
        for direction, data in comparison.items():
            stats = data.get('stats', {})
            details += f"<li><strong>{data.get('description', direction)}</strong>: "
            details += f"PnL {stats.get('total_pnl', 0):.1f}, "
            details += f"Win Rate {stats.get('win_rate', 0):.1%}</li>"
        details += "</ul>"
        
        details += f"<p><strong>Report:</strong> <a href=\"{result.get('report_file', '#')}\">View Detailed Direction Analysis</a></p>"
        
        return details
    
    def _generate_lot_details(self, result: dict) -> str:
        """生成口數分析詳細內容"""
        comparison = result.get('comparison_results', {})
        
        details = "<h3>Lot Performance Comparison:</h3><ul>"
        for lot_config, data in comparison.items():
            lot_count = data.get('lot_count', 0)
            stats = data.get('stats', {})
            metrics = data.get('efficiency_metrics', {})
            details += f"<li><strong>{lot_count} Lots</strong>: "
            details += f"Total PnL {stats.get('total_pnl', 0):.1f}, "
            details += f"Sharpe {metrics.get('sharpe_ratio', 0):.3f}</li>"
        details += "</ul>"
        
        details += f"<p><strong>Report:</strong> <a href=\"{result.get('report_file', '#')}\">View Detailed Lot Analysis</a></p>"
        
        return details
    
    def _generate_recommendations(self) -> str:
        """生成策略建議"""
        recommendations = [
            "🎯 <strong>Direction Focus</strong>: Based on historical bias analysis, consider focusing on the more profitable direction",
            "📏 <strong>Range Filtering</strong>: Implement optimal range size filters to improve entry quality", 
            "💼 <strong>Lot Optimization</strong>: Evaluate whether reducing lot count improves risk-adjusted returns",
            "⏰ <strong>Time Factors</strong>: Consider time-based filters for better market timing",
            "🔄 <strong>Continuous Monitoring</strong>: Regularly re-run these analyses to adapt to changing market conditions"
        ]
        
        return "<ul>" + "".join(f"<li>{rec}</li>" for rec in recommendations) + "</ul>"
    
    def _generate_report_links(self) -> str:
        """生成報告連結"""
        links = []
        
        for exp_name, result in self.results.items():
            if result['status'] == 'success' and 'result' in result:
                report_file = result['result'].get('report_file')
                if report_file:
                    exp_title = exp_name.replace('_', ' ').title()
                    links.append(f"<li><a href=\"{report_file}\">{exp_title} Report</a></li>")
        
        if links:
            return "<ul>" + "".join(links) + "</ul>"
        else:
            return "<p>No detailed reports available.</p>"


def main():
    """主函數"""
    parser = argparse.ArgumentParser(description='Strategy Optimization Experiment Controller')
    parser.add_argument('--experiment', '-e', choices=['all', 'range', 'direction', 'lot'], 
                       default='all', help='Experiment to run')
    parser.add_argument('--start-date', '-s', help='Start date (YYYY-MM-DD)')
    parser.add_argument('--end-date', '-d', help='End date (YYYY-MM-DD)')
    
    args = parser.parse_args()
    
    controller = ExperimentController()
    
    try:
        if args.experiment == 'all':
            controller.run_all_experiments(args.start_date, args.end_date)
        else:
            result = controller.run_single_experiment(args.experiment, args.start_date, args.end_date)
            logger.info(f"✅ 實驗 {args.experiment} 完成")
            
    except Exception as e:
        logger.error(f"❌ 實驗執行失敗: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
