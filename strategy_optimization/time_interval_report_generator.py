#!/usr/bin/env python3
"""
時間區間報告生成器
專門生成時間區間分析的詳細報告，包括跨區間比較和優化建議
"""

import logging
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Any, Optional
import json

# 設置中文字體
plt.rcParams['font.sans-serif'] = ['Arial Unicode MS', 'SimHei', 'DejaVu Sans']
plt.rcParams['axes.unicode_minus'] = False

logger = logging.getLogger(__name__)

class TimeIntervalReportGenerator:
    """時間區間報告生成器"""
    
    def __init__(self, output_dir: str = "reports"):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(exist_ok=True)
        
        # 圖表輸出目錄
        self.charts_dir = self.output_dir / "charts"
        self.charts_dir.mkdir(exist_ok=True)
        
        logger.info(f"📋 時間區間報告生成器初始化完成，輸出目錄: {self.output_dir}")
    
    def generate_comprehensive_report(self, 
                                    analysis_results: Dict[str, Any],
                                    config_name: str = "time_interval_analysis") -> str:
        """生成綜合報告"""
        
        logger.info("📊 開始生成時間區間綜合分析報告...")
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        # 生成圖表
        chart_files = self._generate_charts(analysis_results, timestamp)
        
        # 生成HTML報告
        html_file = self._generate_html_report(analysis_results, config_name, timestamp, chart_files)
        
        # 生成PDF報告（如果需要）
        # pdf_file = self._generate_pdf_report(analysis_results, config_name, timestamp)
        
        # 生成Excel報告
        excel_file = self._generate_excel_report(analysis_results, config_name, timestamp)
        
        logger.info(f"✅ 綜合報告生成完成:")
        logger.info(f"   HTML: {html_file}")
        logger.info(f"   Excel: {excel_file}")
        logger.info(f"   圖表: {len(chart_files)} 個文件")
        
        return html_file
    
    def _generate_charts(self, results: Dict[str, Any], timestamp: str) -> List[str]:
        """生成分析圖表"""
        
        logger.info("📈 生成分析圖表...")
        
        chart_files = []
        daily_recommendations = results.get('daily_recommendations', [])
        
        if not daily_recommendations:
            logger.warning("⚠️  沒有每日建議數據，跳過圖表生成")
            return chart_files
        
        # 轉換為DataFrame
        df = pd.DataFrame(daily_recommendations)
        
        # 1. MDD vs 時間區間圖
        chart_file = self._create_mdd_chart(df, timestamp)
        if chart_file:
            chart_files.append(chart_file)
        
        # 2. 損益 vs 時間區間圖
        chart_file = self._create_pnl_chart(df, timestamp)
        if chart_file:
            chart_files.append(chart_file)
        
        # 3. 勝率分布圖
        chart_file = self._create_winrate_chart(df, timestamp)
        if chart_file:
            chart_files.append(chart_file)
        
        # 4. 停損設定分布圖
        chart_file = self._create_stoploss_distribution_chart(df, timestamp)
        if chart_file:
            chart_files.append(chart_file)
        
        # 5. 停利模式分布圖
        chart_file = self._create_takeprofit_mode_chart(df, timestamp)
        if chart_file:
            chart_files.append(chart_file)
        
        # 6. 風險收益散點圖
        chart_file = self._create_risk_return_scatter(df, timestamp)
        if chart_file:
            chart_files.append(chart_file)
        
        return chart_files
    
    def _create_mdd_chart(self, df: pd.DataFrame, timestamp: str) -> Optional[str]:
        """創建MDD圖表"""
        try:
            plt.figure(figsize=(12, 6))
            
            # 創建條形圖
            bars = plt.bar(range(len(df)), df['mdd'], 
                          color=['red' if x < 0 else 'green' for x in df['mdd']],
                          alpha=0.7)
            
            plt.title('Time Interval MDD Analysis', fontsize=16, fontweight='bold')
            plt.xlabel('Time Interval', fontsize=12)
            plt.ylabel('MDD', fontsize=12)
            plt.xticks(range(len(df)), df['time_interval'], rotation=45)
            plt.grid(True, alpha=0.3)
            
            # 添加數值標籤
            for i, bar in enumerate(bars):
                height = bar.get_height()
                plt.text(bar.get_x() + bar.get_width()/2., height,
                        f'{height:.1f}', ha='center', va='bottom' if height > 0 else 'top')
            
            plt.tight_layout()
            
            chart_file = self.charts_dir / f"mdd_analysis_{timestamp}.png"
            plt.savefig(chart_file, dpi=300, bbox_inches='tight')
            plt.close()
            
            return str(chart_file)
            
        except Exception as e:
            logger.error(f"❌ MDD圖表生成失敗: {e}")
            return None
    
    def _create_pnl_chart(self, df: pd.DataFrame, timestamp: str) -> Optional[str]:
        """創建損益圖表"""
        try:
            plt.figure(figsize=(12, 6))
            
            bars = plt.bar(range(len(df)), df['total_pnl'], 
                          color=['green' if x > 0 else 'red' for x in df['total_pnl']],
                          alpha=0.7)
            
            plt.title('Time Interval P&L Analysis', fontsize=16, fontweight='bold')
            plt.xlabel('Time Interval', fontsize=12)
            plt.ylabel('Total P&L', fontsize=12)
            plt.xticks(range(len(df)), df['time_interval'], rotation=45)
            plt.grid(True, alpha=0.3)
            
            # 添加數值標籤
            for i, bar in enumerate(bars):
                height = bar.get_height()
                plt.text(bar.get_x() + bar.get_width()/2., height,
                        f'{height:.1f}', ha='center', va='bottom' if height > 0 else 'top')
            
            plt.tight_layout()
            
            chart_file = self.charts_dir / f"pnl_analysis_{timestamp}.png"
            plt.savefig(chart_file, dpi=300, bbox_inches='tight')
            plt.close()
            
            return str(chart_file)
            
        except Exception as e:
            logger.error(f"❌ 損益圖表生成失敗: {e}")
            return None
    
    def _create_winrate_chart(self, df: pd.DataFrame, timestamp: str) -> Optional[str]:
        """創建勝率圖表"""
        try:
            plt.figure(figsize=(12, 6))
            
            bars = plt.bar(range(len(df)), df['win_rate'], 
                          color='skyblue', alpha=0.7)
            
            plt.title('Time Interval Win Rate Analysis', fontsize=16, fontweight='bold')
            plt.xlabel('Time Interval', fontsize=12)
            plt.ylabel('Win Rate', fontsize=12)
            plt.xticks(range(len(df)), df['time_interval'], rotation=45)
            plt.ylim(0, 1)
            plt.grid(True, alpha=0.3)
            
            # 添加數值標籤
            for i, bar in enumerate(bars):
                height = bar.get_height()
                plt.text(bar.get_x() + bar.get_width()/2., height,
                        f'{height:.1%}', ha='center', va='bottom')
            
            plt.tight_layout()
            
            chart_file = self.charts_dir / f"winrate_analysis_{timestamp}.png"
            plt.savefig(chart_file, dpi=300, bbox_inches='tight')
            plt.close()
            
            return str(chart_file)
            
        except Exception as e:
            logger.error(f"❌ 勝率圖表生成失敗: {e}")
            return None
    
    def _create_stoploss_distribution_chart(self, df: pd.DataFrame, timestamp: str) -> Optional[str]:
        """創建停損設定分布圖"""
        try:
            fig, axes = plt.subplots(1, 3, figsize=(15, 5))
            
            lots = ['lot1_stop_loss', 'lot2_stop_loss', 'lot3_stop_loss']
            lot_names = ['Lot 1', 'Lot 2', 'Lot 3']
            colors = ['lightcoral', 'lightblue', 'lightgreen']
            
            for i, (lot, name, color) in enumerate(zip(lots, lot_names, colors)):
                axes[i].hist(df[lot], bins=10, color=color, alpha=0.7, edgecolor='black')
                axes[i].set_title(f'{name} Stop Loss Distribution', fontweight='bold')
                axes[i].set_xlabel('Stop Loss Points')
                axes[i].set_ylabel('Frequency')
                axes[i].grid(True, alpha=0.3)
            
            plt.suptitle('Stop Loss Settings Distribution', fontsize=16, fontweight='bold')
            plt.tight_layout()
            
            chart_file = self.charts_dir / f"stoploss_distribution_{timestamp}.png"
            plt.savefig(chart_file, dpi=300, bbox_inches='tight')
            plt.close()
            
            return str(chart_file)
            
        except Exception as e:
            logger.error(f"❌ 停損分布圖表生成失敗: {e}")
            return None
    
    def _create_takeprofit_mode_chart(self, df: pd.DataFrame, timestamp: str) -> Optional[str]:
        """創建停利模式分布圖"""
        try:
            plt.figure(figsize=(10, 6))
            
            # 統計停利模式
            mode_counts = df['mode'].str.split().str[0].value_counts()
            
            colors = plt.cm.Set3(range(len(mode_counts)))
            wedges, texts, autotexts = plt.pie(mode_counts.values, labels=mode_counts.index, 
                                              autopct='%1.1f%%', colors=colors, startangle=90)
            
            plt.title('Take Profit Mode Distribution', fontsize=16, fontweight='bold')
            
            # 美化文字
            for autotext in autotexts:
                autotext.set_color('white')
                autotext.set_fontweight('bold')
            
            chart_file = self.charts_dir / f"takeprofit_mode_{timestamp}.png"
            plt.savefig(chart_file, dpi=300, bbox_inches='tight')
            plt.close()
            
            return str(chart_file)
            
        except Exception as e:
            logger.error(f"❌ 停利模式圖表生成失敗: {e}")
            return None
    
    def _create_risk_return_scatter(self, df: pd.DataFrame, timestamp: str) -> Optional[str]:
        """創建風險收益散點圖"""
        try:
            plt.figure(figsize=(10, 8))
            
            # 計算風險調整收益
            df['risk_adjusted_return'] = df['total_pnl'] / (abs(df['mdd']) + 1)
            
            scatter = plt.scatter(df['mdd'], df['total_pnl'], 
                                c=df['win_rate'], cmap='viridis', 
                                s=100, alpha=0.7, edgecolors='black')
            
            plt.title('Risk vs Return Analysis', fontsize=16, fontweight='bold')
            plt.xlabel('MDD', fontsize=12)
            plt.ylabel('Total P&L', fontsize=12)
            plt.grid(True, alpha=0.3)
            
            # 添加顏色條
            cbar = plt.colorbar(scatter)
            cbar.set_label('Win Rate', fontsize=12)
            
            # 添加時間區間標籤
            for i, row in df.iterrows():
                plt.annotate(row['time_interval'], 
                           (row['mdd'], row['total_pnl']),
                           xytext=(5, 5), textcoords='offset points',
                           fontsize=8, alpha=0.8)
            
            plt.tight_layout()
            
            chart_file = self.charts_dir / f"risk_return_scatter_{timestamp}.png"
            plt.savefig(chart_file, dpi=300, bbox_inches='tight')
            plt.close()
            
            return str(chart_file)
            
        except Exception as e:
            logger.error(f"❌ 風險收益散點圖生成失敗: {e}")
            return None

    def _generate_html_report(self, results: Dict[str, Any], config_name: str,
                            timestamp: str, chart_files: List[str]) -> str:
        """生成HTML報告"""

        logger.info("📄 生成HTML報告...")

        overall_stats = results.get('overall_stats', {})
        daily_recommendations = results.get('daily_recommendations', [])

        html_content = f"""
<!DOCTYPE html>
<html lang="zh-TW">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>時間區間MDD分析報告 - {config_name}</title>
    <style>
        body {{ font-family: 'Microsoft JhengHei', Arial, sans-serif; margin: 20px; background-color: #f5f5f5; }}
        .container {{ max-width: 1400px; margin: 0 auto; background: white; padding: 30px; border-radius: 10px; box-shadow: 0 0 20px rgba(0,0,0,0.1); }}
        .header {{ text-align: center; margin-bottom: 30px; padding: 20px; background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; border-radius: 10px; }}
        .section {{ margin: 30px 0; padding: 20px; border: 1px solid #ddd; border-radius: 8px; background: #fafafa; }}
        .section h2 {{ color: #333; border-bottom: 2px solid #667eea; padding-bottom: 10px; }}
        .stats-grid {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 15px; margin: 20px 0; }}
        .stat-card {{ background: white; padding: 15px; border-radius: 8px; text-align: center; box-shadow: 0 2px 5px rgba(0,0,0,0.1); }}
        .stat-value {{ font-size: 24px; font-weight: bold; color: #667eea; }}
        .stat-label {{ color: #666; margin-top: 5px; }}
        .chart-container {{ text-align: center; margin: 20px 0; }}
        .chart-container img {{ max-width: 100%; height: auto; border-radius: 8px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); }}
        .recommendations-table {{ width: 100%; border-collapse: collapse; margin: 20px 0; }}
        .recommendations-table th, .recommendations-table td {{ border: 1px solid #ddd; padding: 12px; text-align: center; }}
        .recommendations-table th {{ background-color: #667eea; color: white; }}
        .recommendations-table tr:nth-child(even) {{ background-color: #f9f9f9; }}
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
        """

        # 添加圖表
        if chart_files:
            html_content += """
        <div class="section">
            <h2>📈 分析圖表</h2>
            """

            for chart_file in chart_files:
                chart_name = Path(chart_file).name
                # 使用相對路徑
                relative_path = f"charts/{chart_name}"
                html_content += f"""
            <div class="chart-container">
                <h3>{chart_name.replace('_', ' ').replace('.png', '').title()}</h3>
                <img src="{relative_path}" alt="{chart_name}">
            </div>
                """

            html_content += "</div>"

        # 添加每日建議表格
        html_content += """
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

        # 結尾
        html_content += f"""
                </tbody>
            </table>
        </div>

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

        # 保存HTML文件
        html_file = self.output_dir / f"time_interval_analysis_{config_name}_{timestamp}.html"
        with open(html_file, 'w', encoding='utf-8') as f:
            f.write(html_content)

        return str(html_file)

    def _generate_excel_report(self, results: Dict[str, Any], config_name: str, timestamp: str) -> str:
        """生成Excel報告"""

        logger.info("📊 生成Excel報告...")

        excel_file = self.output_dir / f"time_interval_analysis_{config_name}_{timestamp}.xlsx"

        with pd.ExcelWriter(excel_file, engine='openpyxl') as writer:

            # 1. 每日建議工作表
            if results.get('daily_recommendations'):
                recommendations_df = pd.DataFrame(results['daily_recommendations'])
                recommendations_df.to_excel(writer, sheet_name='每日建議', index=False)

            # 2. 總體統計工作表
            if results.get('overall_stats'):
                stats_df = pd.DataFrame([results['overall_stats']])
                stats_df.to_excel(writer, sheet_name='總體統計', index=False)

            # 3. 原始結果工作表
            if results.get('raw_results'):
                raw_df = pd.DataFrame(results['raw_results'])
                raw_df.to_excel(writer, sheet_name='原始結果', index=False)

            # 4. 區間分析工作表
            if results.get('interval_analysis'):
                interval_data = []
                for interval, analysis in results['interval_analysis'].items():
                    row = {
                        'time_interval': interval,
                        'total_experiments': analysis['total_experiments'],
                        'avg_mdd': analysis['stats']['avg_mdd'],
                        'avg_pnl': analysis['stats']['avg_pnl'],
                        'avg_win_rate': analysis['stats']['avg_win_rate'],
                        'recommendation_reason': analysis.get('recommendation_reason', '')
                    }

                    # 添加推薦配置信息
                    if analysis.get('recommended_config'):
                        rec = analysis['recommended_config']
                        row.update({
                            'recommended_mdd': rec['mdd'],
                            'recommended_pnl': rec['total_pnl'],
                            'recommended_win_rate': rec['win_rate'],
                            'recommended_lot1_sl': rec['lot1_stop_loss'],
                            'recommended_lot2_sl': rec['lot2_stop_loss'],
                            'recommended_lot3_sl': rec['lot3_stop_loss']
                        })

                    interval_data.append(row)

                if interval_data:
                    interval_df = pd.DataFrame(interval_data)
                    interval_df.to_excel(writer, sheet_name='區間分析', index=False)

        logger.info(f"✅ Excel報告已生成: {excel_file}")
        return str(excel_file)

    def generate_comparison_report(self, multiple_results: List[Dict[str, Any]],
                                 config_names: List[str]) -> str:
        """生成多配置比較報告"""

        logger.info("📊 生成多配置比較報告...")

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

        # 創建比較數據
        comparison_data = []
        for i, (results, config_name) in enumerate(zip(multiple_results, config_names)):
            overall_stats = results.get('overall_stats', {})
            comparison_data.append({
                'config_name': config_name,
                'expected_daily_pnl': overall_stats.get('expected_daily_pnl', 0),
                'expected_daily_mdd': overall_stats.get('expected_daily_mdd', 0),
                'average_win_rate': overall_stats.get('average_win_rate', 0),
                'total_intervals': overall_stats.get('total_intervals', 0),
                'risk_adjusted_return': overall_stats.get('risk_adjusted_return', 0),
                'total_experiments': results.get('total_experiments', 0),
                'successful_experiments': results.get('successful_experiments', 0)
            })

        # 生成比較圖表
        comparison_chart = self._create_comparison_chart(comparison_data, timestamp)

        # 生成比較HTML報告
        html_file = self._generate_comparison_html(comparison_data, timestamp, comparison_chart)

        logger.info(f"✅ 多配置比較報告已生成: {html_file}")
        return html_file

    def _create_comparison_chart(self, comparison_data: List[Dict], timestamp: str) -> str:
        """創建配置比較圖表"""

        try:
            df = pd.DataFrame(comparison_data)

            fig, axes = plt.subplots(2, 2, figsize=(15, 10))

            # 1. 預期每日損益比較
            axes[0, 0].bar(df['config_name'], df['expected_daily_pnl'],
                          color=['green' if x > 0 else 'red' for x in df['expected_daily_pnl']])
            axes[0, 0].set_title('Expected Daily P&L Comparison')
            axes[0, 0].set_ylabel('P&L')
            axes[0, 0].tick_params(axis='x', rotation=45)

            # 2. 預期每日MDD比較
            axes[0, 1].bar(df['config_name'], df['expected_daily_mdd'], color='red', alpha=0.7)
            axes[0, 1].set_title('Expected Daily MDD Comparison')
            axes[0, 1].set_ylabel('MDD')
            axes[0, 1].tick_params(axis='x', rotation=45)

            # 3. 平均勝率比較
            axes[1, 0].bar(df['config_name'], df['average_win_rate'], color='blue', alpha=0.7)
            axes[1, 0].set_title('Average Win Rate Comparison')
            axes[1, 0].set_ylabel('Win Rate')
            axes[1, 0].tick_params(axis='x', rotation=45)

            # 4. 風險調整收益比較
            axes[1, 1].bar(df['config_name'], df['risk_adjusted_return'], color='purple', alpha=0.7)
            axes[1, 1].set_title('Risk Adjusted Return Comparison')
            axes[1, 1].set_ylabel('Risk Adjusted Return')
            axes[1, 1].tick_params(axis='x', rotation=45)

            plt.tight_layout()

            chart_file = self.charts_dir / f"config_comparison_{timestamp}.png"
            plt.savefig(chart_file, dpi=300, bbox_inches='tight')
            plt.close()

            return str(chart_file)

        except Exception as e:
            logger.error(f"❌ 配置比較圖表生成失敗: {e}")
            return ""

    def _generate_comparison_html(self, comparison_data: List[Dict],
                                timestamp: str, chart_file: str) -> str:
        """生成配置比較HTML報告"""

        html_content = f"""
<!DOCTYPE html>
<html lang="zh-TW">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>時間區間配置比較報告</title>
    <style>
        body {{ font-family: 'Microsoft JhengHei', Arial, sans-serif; margin: 20px; background-color: #f5f5f5; }}
        .container {{ max-width: 1200px; margin: 0 auto; background: white; padding: 30px; border-radius: 10px; box-shadow: 0 0 20px rgba(0,0,0,0.1); }}
        .header {{ text-align: center; margin-bottom: 30px; padding: 20px; background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; border-radius: 10px; }}
        .comparison-table {{ width: 100%; border-collapse: collapse; margin: 20px 0; }}
        .comparison-table th, .comparison-table td {{ border: 1px solid #ddd; padding: 12px; text-align: center; }}
        .comparison-table th {{ background-color: #667eea; color: white; }}
        .comparison-table tr:nth-child(even) {{ background-color: #f9f9f9; }}
        .chart-container {{ text-align: center; margin: 20px 0; }}
        .chart-container img {{ max-width: 100%; height: auto; border-radius: 8px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); }}
        .positive {{ color: #28a745; }}
        .negative {{ color: #dc3545; }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>📊 時間區間配置比較報告</h1>
            <p>生成時間: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
        </div>

        <div class="chart-container">
            <h2>📈 配置比較圖表</h2>
            <img src="charts/{Path(chart_file).name}" alt="配置比較圖表">
        </div>

        <h2>📋 配置比較表格</h2>
        <table class="comparison-table">
            <thead>
                <tr>
                    <th>配置名稱</th>
                    <th>預期每日損益</th>
                    <th>預期每日MDD</th>
                    <th>平均勝率</th>
                    <th>分析區間數</th>
                    <th>風險調整收益</th>
                    <th>總實驗數</th>
                    <th>成功實驗數</th>
                </tr>
            </thead>
            <tbody>
        """

        for data in comparison_data:
            html_content += f"""
                <tr>
                    <td>{data['config_name']}</td>
                    <td class="{'positive' if data['expected_daily_pnl'] > 0 else 'negative'}">{data['expected_daily_pnl']:.2f}</td>
                    <td class="negative">{data['expected_daily_mdd']:.2f}</td>
                    <td>{data['average_win_rate']:.2%}</td>
                    <td>{data['total_intervals']}</td>
                    <td>{data['risk_adjusted_return']:.3f}</td>
                    <td>{data['total_experiments']}</td>
                    <td>{data['successful_experiments']}</td>
                </tr>
            """

        html_content += """
            </tbody>
        </table>
    </div>
</body>
</html>
        """

        # 保存HTML文件
        html_file = self.output_dir / f"config_comparison_{timestamp}.html"
        with open(html_file, 'w', encoding='utf-8') as f:
            f.write(html_content)

        return str(html_file)

    def _create_time_interval_html(self, results: Dict[str, Any], config_name: str) -> str:
        """創建時間區間HTML內容（用於測試）"""

        overall_stats = results.get('overall_stats', {})
        daily_recommendations = results.get('daily_recommendations', [])

        html_content = f"""
<!DOCTYPE html>
<html lang="zh-TW">
<head>
    <meta charset="UTF-8">
    <title>時間區間MDD分析報告 - {config_name}</title>
</head>
<body>
    <h1>時間區間MDD分析報告</h1>
    <p>配置: {config_name}</p>

    <h2>總體統計</h2>
    <p>預期每日損益: {overall_stats.get('expected_daily_pnl', 0):.2f}</p>
    <p>預期每日MDD: {overall_stats.get('expected_daily_mdd', 0):.2f}</p>
    <p>平均勝率: {overall_stats.get('average_win_rate', 0):.2%}</p>

    <h2>每日建議</h2>
    <table>
        <tr>
            <th>時間區間</th>
            <th>停利模式</th>
            <th>MDD</th>
            <th>損益</th>
            <th>勝率</th>
        </tr>
        """

        for rec in daily_recommendations:
            html_content += f"""
        <tr>
            <td>{rec['time_interval']}</td>
            <td>{rec['mode']}</td>
            <td>{rec['mdd']:.2f}</td>
            <td>{rec['total_pnl']:.2f}</td>
            <td>{rec['win_rate']:.2%}</td>
        </tr>
            """

        html_content += """
    </table>
</body>
</html>
        """

        return html_content
