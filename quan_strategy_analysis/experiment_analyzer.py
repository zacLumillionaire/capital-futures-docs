#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
實驗結果分析系統
提供實驗結果的查詢、分析、排序和可視化功能
"""

import sqlite3
import pandas as pd
import json
import matplotlib.pyplot as plt
import seaborn as sns
from typing import List, Dict, Any, Optional, Tuple
import numpy as np
from pathlib import Path
import logging

# 設定中文字體和後端
import matplotlib
matplotlib.use('Agg')  # 使用非交互式後端
plt.rcParams['font.sans-serif'] = ['Arial Unicode MS', 'SimHei', 'DejaVu Sans']
plt.rcParams['axes.unicode_minus'] = False

logger = logging.getLogger(__name__)

class ExperimentAnalyzer:
    """實驗結果分析器"""
    
    def __init__(self, db_path: str = "batch_experiments.db"):
        self.db_path = db_path
        
    def load_results_dataframe(self, success_only: bool = True, trading_direction: Optional[str] = None) -> pd.DataFrame:
        """載入實驗結果為 DataFrame

        Args:
            success_only: 是否只載入成功的實驗
            trading_direction: 交易方向過濾 ('LONG_ONLY', 'SHORT_ONLY', 'BOTH', None=所有)
        """
        with sqlite3.connect(self.db_path) as conn:
            query = "SELECT * FROM experiments"
            conditions = []

            if success_only:
                conditions.append("success = 1")

            # 按交易方向過濾
            if trading_direction:
                conditions.append(f"json_extract(parameters, '$.trading_direction') = '{trading_direction}'")

            if conditions:
                query += " WHERE " + " AND ".join(conditions)

            query += " ORDER BY experiment_id"

            df = pd.read_sql_query(query, conn)

            # 解析參數 JSON
            if not df.empty:
                parameters_df = pd.json_normalize(df['parameters'].apply(json.loads))
                df = pd.concat([df.drop('parameters', axis=1), parameters_df], axis=1)

                if trading_direction:
                    logger.info(f"按交易方向 {trading_direction} 過濾後，剩餘 {len(df)} 個實驗")

            return df
    
    def get_summary_statistics(self, trading_direction: Optional[str] = None) -> Dict[str, Any]:
        """獲取實驗摘要統計"""
        df = self.load_results_dataframe(success_only=False, trading_direction=trading_direction)
        
        if df.empty:
            return {"error": "無實驗數據"}
        
        success_df = df[df['success'] == True]

        # 添加交易方向信息到摘要
        direction_info = ""
        if trading_direction:
            direction_info = f" ({trading_direction})"
        
        summary = {
            "total_experiments": len(df),
            "successful_experiments": len(success_df),
            "success_rate": len(success_df) / len(df) * 100 if len(df) > 0 else 0,
            "avg_execution_time": df['execution_time'].mean(),
            "total_execution_time": df['execution_time'].sum()
        }
        
        if not success_df.empty:
            summary.update({
                "best_total_pnl": success_df['total_pnl'].max(),
                "worst_total_pnl": success_df['total_pnl'].min(),
                "avg_total_pnl": success_df['total_pnl'].mean(),
                "best_win_rate": success_df['win_rate'].max(),
                "avg_win_rate": success_df['win_rate'].mean(),
                "min_max_drawdown": success_df['max_drawdown'].min(),
                "avg_max_drawdown": success_df['max_drawdown'].mean()
            })
        
        return summary
    
    def get_top_results(self, metric: str = "total_pnl", top_n: int = 10, ascending: bool = False, trading_direction: Optional[str] = None) -> pd.DataFrame:
        """獲取最佳結果"""
        df = self.load_results_dataframe(success_only=True, trading_direction=trading_direction)
        
        if df.empty:
            return pd.DataFrame()
        
        # 確保指標存在
        if metric not in df.columns:
            logger.warning(f"指標 {metric} 不存在，使用 total_pnl")
            metric = "total_pnl"
        
        return df.nlargest(top_n, metric) if not ascending else df.nsmallest(top_n, metric)
    
    def analyze_parameter_sensitivity(self, target_metric: str = "total_pnl", trading_direction: Optional[str] = None) -> Dict[str, float]:
        """分析參數敏感度"""
        df = self.load_results_dataframe(success_only=True, trading_direction=trading_direction)
        
        if df.empty:
            return {}
        
        # 選擇數值型參數
        numeric_params = [
            'lot1_trigger', 'lot1_trailing', 
            'lot2_trigger', 'lot2_trailing', 'lot2_protection',
            'lot3_trigger', 'lot3_trailing', 'lot3_protection'
        ]
        
        sensitivity = {}
        
        for param in numeric_params:
            if param in df.columns:
                correlation = df[param].corr(df[target_metric])
                sensitivity[param] = abs(correlation) if not pd.isna(correlation) else 0
        
        # 按敏感度排序
        return dict(sorted(sensitivity.items(), key=lambda x: x[1], reverse=True))
    
    def find_optimal_parameters(self, metric: str = "total_pnl", trading_direction: Optional[str] = None) -> Dict[str, Any]:
        """找到最佳參數組合"""
        df = self.load_results_dataframe(success_only=True, trading_direction=trading_direction)
        
        if df.empty:
            return {}
        
        best_row = df.loc[df[metric].idxmax()]
        
        optimal_params = {
            "experiment_id": best_row['experiment_id'],
            "metric_value": best_row[metric],
            "parameters": {
                "lot1_trigger": best_row.get('lot1_trigger'),
                "lot1_trailing": best_row.get('lot1_trailing'),
                "lot2_trigger": best_row.get('lot2_trigger'),
                "lot2_trailing": best_row.get('lot2_trailing'),
                "lot2_protection": best_row.get('lot2_protection'),
                "lot3_trigger": best_row.get('lot3_trigger'),
                "lot3_trailing": best_row.get('lot3_trailing'),
                "lot3_protection": best_row.get('lot3_protection')
            },
            "performance": {
                "total_pnl": best_row.get('total_pnl'),
                "win_rate": best_row.get('win_rate'),
                "max_drawdown": best_row.get('max_drawdown'),
                "total_trades": best_row.get('total_trades')
            }
        }
        
        return optimal_params
    
    def generate_performance_charts(self, output_dir: str = "charts", trading_direction: Optional[str] = None) -> List[str]:
        """生成性能分析圖表"""
        df = self.load_results_dataframe(success_only=True, trading_direction=trading_direction)
        
        if df.empty:
            logger.warning("無成功的實驗數據，無法生成圖表")
            return []
        
        Path(output_dir).mkdir(exist_ok=True)
        chart_files = []

        try:
            # 設定圖表樣式
            plt.style.use('default')
            fig_size = (12, 8)

            # 1. 總損益分布圖
            plt.figure(figsize=fig_size)
            plt.hist(df['total_pnl'], bins=20, alpha=0.7, color='skyblue', edgecolor='black')
            plt.title('Total PnL Distribution', fontsize=16, fontweight='bold')
            plt.xlabel('Total PnL (Points)', fontsize=12)
            plt.ylabel('Frequency', fontsize=12)
            plt.grid(True, alpha=0.3)
            chart_file = f"{output_dir}/total_pnl_distribution.png"
            plt.savefig(chart_file, dpi=300, bbox_inches='tight')
            plt.close()
            chart_files.append(chart_file)

            # 2. 勝率 vs 總損益散點圖
            plt.figure(figsize=fig_size)
            plt.scatter(df['win_rate'], df['total_pnl'], alpha=0.6, color='green')
            plt.title('Win Rate vs Total PnL', fontsize=16, fontweight='bold')
            plt.xlabel('Win Rate (%)', fontsize=12)
            plt.ylabel('Total PnL (Points)', fontsize=12)
            plt.grid(True, alpha=0.3)

            # 添加趨勢線
            z = np.polyfit(df['win_rate'], df['total_pnl'], 1)
            p = np.poly1d(z)
            plt.plot(df['win_rate'], p(df['win_rate']), "r--", alpha=0.8)

            chart_file = f"{output_dir}/winrate_vs_pnl.png"
            plt.savefig(chart_file, dpi=300, bbox_inches='tight')
            plt.close()
            chart_files.append(chart_file)

            # 3. 參數敏感度分析
            sensitivity = self.analyze_parameter_sensitivity()
            if sensitivity:
                plt.figure(figsize=fig_size)
                params = list(sensitivity.keys())
                values = list(sensitivity.values())

                bars = plt.bar(params, values, color='orange', alpha=0.7)
                plt.title('Parameter Sensitivity Analysis', fontsize=16, fontweight='bold')
                plt.xlabel('Parameters', fontsize=12)
                plt.ylabel('Correlation (Absolute)', fontsize=12)
                plt.xticks(rotation=45)
                plt.grid(True, alpha=0.3)

                # 添加數值標籤
                for bar, value in zip(bars, values):
                    plt.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 0.01,
                            f'{value:.3f}', ha='center', va='bottom')

                chart_file = f"{output_dir}/parameter_sensitivity.png"
                plt.savefig(chart_file, dpi=300, bbox_inches='tight')
                plt.close()
                chart_files.append(chart_file)

            # 4. 最大回撤分析
            if 'max_drawdown' in df.columns and df['max_drawdown'].notna().any():
                plt.figure(figsize=fig_size)
                plt.hist(df['max_drawdown'], bins=15, alpha=0.7, color='red', edgecolor='black')
                plt.title('Maximum Drawdown Distribution', fontsize=16, fontweight='bold')
                plt.xlabel('Maximum Drawdown (Points)', fontsize=12)
                plt.ylabel('Frequency', fontsize=12)
                plt.grid(True, alpha=0.3)
                chart_file = f"{output_dir}/max_drawdown_distribution.png"
                plt.savefig(chart_file, dpi=300, bbox_inches='tight')
                plt.close()
                chart_files.append(chart_file)

            # 5. 多空損益對比
            if 'long_pnl' in df.columns and 'short_pnl' in df.columns:
                plt.figure(figsize=fig_size)
                plt.scatter(df['long_pnl'], df['short_pnl'], alpha=0.6, color='purple')
                plt.title('Long vs Short PnL', fontsize=16, fontweight='bold')
                plt.xlabel('Long PnL (Points)', fontsize=12)
                plt.ylabel('Short PnL (Points)', fontsize=12)
                plt.grid(True, alpha=0.3)

                # 添加對角線
                max_val = max(df['long_pnl'].max(), df['short_pnl'].max())
                min_val = min(df['long_pnl'].min(), df['short_pnl'].min())
                plt.plot([min_val, max_val], [min_val, max_val], 'r--', alpha=0.5)

                chart_file = f"{output_dir}/long_vs_short_pnl.png"
                plt.savefig(chart_file, dpi=300, bbox_inches='tight')
                plt.close()
                chart_files.append(chart_file)

            logger.info(f"✅ 生成了 {len(chart_files)} 個圖表")
            return chart_files

        except Exception as e:
            logger.error(f"生成圖表時發生錯誤: {e}")
            import traceback
            traceback.print_exc()
            return []
    
    def export_results_to_csv(self, filename: Optional[str] = None) -> str:
        """匯出結果到 CSV"""
        df = self.load_results_dataframe(success_only=False)
        
        if filename is None:
            from datetime import datetime
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"experiment_results_{timestamp}.csv"
        
        df.to_csv(filename, index=False, encoding='utf-8-sig')
        logger.info(f"✅ 結果已匯出到: {filename}")
        return filename
    
    def generate_analysis_report(self, output_file: Optional[str] = None, trading_direction: Optional[str] = None) -> str:
        """生成分析報告

        Args:
            output_file: 輸出文件名
            trading_direction: 交易方向過濾 ('LONG_ONLY', 'SHORT_ONLY', 'BOTH', None=所有)
        """
        if output_file is None:
            from datetime import datetime
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            if trading_direction:
                direction_suffix = trading_direction.lower()
                output_file = f"experiment_analysis_report_{direction_suffix}_{timestamp}.html"
            else:
                output_file = f"experiment_analysis_report_{timestamp}.html"

        # 獲取分析數據（按交易方向過濾）
        summary = self.get_summary_statistics(trading_direction)
        top_results = self.get_top_results("total_pnl", 10, False, trading_direction)
        optimal_params = self.find_optimal_parameters("total_pnl", trading_direction)
        sensitivity = self.analyze_parameter_sensitivity("total_pnl", trading_direction)

        # 🚀 修復圖表路徑問題：將圖表生成在HTML文件的同一目錄下
        output_dir = Path(output_file).parent
        chart_dir = output_dir / "charts"
        chart_files = self.generate_performance_charts(str(chart_dir), trading_direction)
        
        # 生成 HTML 報告
        direction_title = ""
        if trading_direction:
            direction_map = {
                'LONG_ONLY': '只做多',
                'SHORT_ONLY': '只做空',
                'BOTH': '多空混合'
            }
            direction_title = f" - {direction_map.get(trading_direction, trading_direction)}"

        html_content = f"""
<!DOCTYPE html>
<html lang="zh-TW">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>批次實驗分析報告{direction_title}</title>
    <style>
        body {{ font-family: Arial, sans-serif; margin: 20px; background-color: #f5f5f5; }}
        .container {{ max-width: 1200px; margin: 0 auto; background: white; padding: 30px; border-radius: 10px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); }}
        h1, h2 {{ color: #333; }}
        .summary-grid {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 20px; margin: 20px 0; }}
        .summary-card {{ background: #f8f9fa; padding: 15px; border-radius: 8px; text-align: center; }}
        .summary-value {{ font-size: 24px; font-weight: bold; color: #2e7d32; }}
        .summary-label {{ font-size: 14px; color: #666; margin-top: 5px; }}
        table {{ width: 100%; border-collapse: collapse; margin: 20px 0; }}
        th, td {{ padding: 10px; text-align: left; border-bottom: 1px solid #ddd; }}
        th {{ background-color: #4CAF50; color: white; }}
        .chart-container {{ text-align: center; margin: 20px 0; }}
        .chart-container img {{ max-width: 100%; height: auto; border: 1px solid #ddd; border-radius: 5px; }}
        .optimal-params {{ background: #e8f5e8; padding: 15px; border-radius: 8px; margin: 20px 0; }}
    </style>
</head>
<body>
    <div class="container">
        <h1>📊 批次實驗分析報告{direction_title}</h1>
        <p>報告生成時間: {pd.Timestamp.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
        
        <h2>📈 實驗摘要</h2>
        <div class="summary-grid">
            <div class="summary-card">
                <div class="summary-value">{summary.get('total_experiments', 0)}</div>
                <div class="summary-label">總實驗數</div>
            </div>
            <div class="summary-card">
                <div class="summary-value">{summary.get('successful_experiments', 0)}</div>
                <div class="summary-label">成功實驗數</div>
            </div>
            <div class="summary-card">
                <div class="summary-value">{summary.get('success_rate', 0):.1f}%</div>
                <div class="summary-label">成功率</div>
            </div>
            <div class="summary-card">
                <div class="summary-value">{summary.get('best_total_pnl', 0):.1f}</div>
                <div class="summary-label">最佳總損益</div>
            </div>
            <div class="summary-card">
                <div class="summary-value">{summary.get('best_win_rate', 0):.1f}%</div>
                <div class="summary-label">最佳勝率</div>
            </div>
            <div class="summary-card">
                <div class="summary-value">{summary.get('total_execution_time', 0):.1f}s</div>
                <div class="summary-label">總執行時間</div>
            </div>
        </div>
        
        <h2>🏆 最佳參數組合</h2>
        <div class="optimal-params">
            <h3>實驗 {optimal_params.get('experiment_id', 'N/A')} - 總損益: {optimal_params.get('metric_value', 0):.1f} 點</h3>
            <p><strong>參數設定:</strong></p>
            <ul>
                <li>第1口: 觸發 {optimal_params.get('parameters', {}).get('lot1_trigger', 'N/A')} 點, 回檔 {optimal_params.get('parameters', {}).get('lot1_trailing', 'N/A')}%</li>
                <li>第2口: 觸發 {optimal_params.get('parameters', {}).get('lot2_trigger', 'N/A')} 點, 回檔 {optimal_params.get('parameters', {}).get('lot2_trailing', 'N/A')}%, 保護 {optimal_params.get('parameters', {}).get('lot2_protection', 'N/A')}x</li>
                <li>第3口: 觸發 {optimal_params.get('parameters', {}).get('lot3_trigger', 'N/A')} 點, 回檔 {optimal_params.get('parameters', {}).get('lot3_trailing', 'N/A')}%, 保護 {optimal_params.get('parameters', {}).get('lot3_protection', 'N/A')}x</li>
            </ul>
            <p><strong>績效表現:</strong></p>
            <ul>
                <li>總損益: {optimal_params.get('performance', {}).get('total_pnl', 'N/A')} 點</li>
                <li>勝率: {optimal_params.get('performance', {}).get('win_rate', 'N/A')}%</li>
                <li>總交易次數: {optimal_params.get('performance', {}).get('total_trades', 'N/A')}</li>
                <li>最大回撤: {optimal_params.get('performance', {}).get('max_drawdown', 'N/A')} 點</li>
            </ul>
        </div>
        
        <h2>📊 性能分析圖表</h2>
        """
        
        # 添加圖表（使用相對路徑）
        for chart_file in chart_files:
            chart_name = Path(chart_file).stem.replace('_', ' ').title()
            # 🚀 修復：使用相對路徑引用圖表
            relative_chart_path = Path(chart_file).relative_to(output_dir)
            html_content += f"""
        <div class="chart-container">
            <h3>{chart_name}</h3>
            <img src="{relative_chart_path}" alt="{chart_name}">
        </div>
        """
        
        html_content += """
    </div>
</body>
</html>
        """
        
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(html_content)
        
        logger.info(f"✅ 分析報告已生成: {output_file}")
        return output_file

if __name__ == "__main__":
    # 示例使用
    analyzer = ExperimentAnalyzer()
    
    # 生成分析報告
    report_file = analyzer.generate_analysis_report()
    print(f"📋 分析報告已生成: {report_file}")
    
    # 顯示摘要統計
    summary = analyzer.get_summary_statistics()
    print("\n📊 實驗摘要:")
    for key, value in summary.items():
        print(f"  - {key}: {value}")
    
    # 顯示最佳結果
    top_results = analyzer.get_top_results("total_pnl", 3)
    if not top_results.empty:
        print("\n🏆 前3名結果:")
        for i, (_, row) in enumerate(top_results.iterrows(), 1):
            print(f"  {i}. 實驗 {row['experiment_id']}: {row['total_pnl']:.1f} 點 (勝率: {row['win_rate']:.1f}%)")
