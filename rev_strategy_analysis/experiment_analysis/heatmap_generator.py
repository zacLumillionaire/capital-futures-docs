#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
熱力圖生成器 - 反轉策略實驗系統
生成停損vs停利的二維熱力圖分析

功能:
- 二維熱力圖分析 (停損點 vs 停利點)
- 支援多個時間區間的比較
- 自動識別最佳參數區域
- 生成互動式圖表
"""

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
import plotly.graph_objects as go
import plotly.express as px
from plotly.subplots import make_subplots
import logging
from pathlib import Path

# 設置中文字體
plt.rcParams['font.sans-serif'] = ['Arial Unicode MS', 'SimHei', 'DejaVu Sans']
plt.rcParams['axes.unicode_minus'] = False

logger = logging.getLogger(__name__)

class HeatmapGenerator:
    """熱力圖生成器主類"""
    
    def __init__(self, results_df=None):
        """初始化熱力圖生成器
        
        Args:
            results_df: 實驗結果DataFrame
        """
        self.results_df = results_df
        self.output_dir = Path("results/heatmap_analysis")
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
    def load_results_from_csv(self, csv_path):
        """從CSV文件載入實驗結果"""
        try:
            self.results_df = pd.read_csv(csv_path)
            logger.info(f"✅ 成功載入實驗結果: {len(self.results_df)} 筆記錄")
            return True
        except Exception as e:
            logger.error(f"❌ 載入CSV失敗: {e}")
            return False
    
    def create_pivot_table(self, time_interval=None, metric='total_pnl'):
        """創建用於熱力圖的透視表
        
        Args:
            time_interval: 指定時間區間，None表示使用所有區間
            metric: 評估指標 ('total_pnl', 'win_rate', 'long_pnl', 'short_pnl')
        
        Returns:
            pivot_table: 透視表
        """
        if self.results_df is None:
            logger.error("❌ 沒有實驗結果數據")
            return None
        
        # 篩選時間區間
        df = self.results_df.copy()
        if time_interval:
            df = df[df['time_interval'] == time_interval]
        
        if df.empty:
            logger.warning(f"⚠️ 指定時間區間 {time_interval} 沒有數據")
            return None
        
        # 創建透視表
        pivot = df.pivot_table(
            values=metric,
            index='stop_loss_points',
            columns='take_profit_points',
            aggfunc='mean'  # 如果有重複組合，取平均值
        )
        
        return pivot
    
    def generate_matplotlib_heatmap(self, time_interval=None, metric='total_pnl', save_path=None):
        """使用matplotlib生成靜態熱力圖"""
        pivot = self.create_pivot_table(time_interval, metric)
        if pivot is None:
            return None
        
        # 設置圖表大小和樣式
        plt.figure(figsize=(12, 8))
        
        # 創建熱力圖
        sns.heatmap(
            pivot,
            annot=True,
            fmt='.1f',
            cmap='RdYlGn',
            center=0,
            cbar_kws={'label': f'{metric} (點)'},
            linewidths=0.5
        )
        
        # 設置標題和標籤
        title = f'停損vs停利熱力圖 - {metric}'
        if time_interval:
            title += f' ({time_interval})'
        
        plt.title(title, fontsize=16, fontweight='bold')
        plt.xlabel('停利點數', fontsize=12)
        plt.ylabel('停損點數', fontsize=12)
        plt.xticks(rotation=45)
        plt.yticks(rotation=0)
        
        # 調整布局
        plt.tight_layout()
        
        # 保存圖表
        if save_path is None:
            interval_suffix = f"_{time_interval.replace(':', '').replace('-', '_')}" if time_interval else "_all"
            save_path = self.output_dir / f"heatmap_{metric}{interval_suffix}.png"
        
        plt.savefig(save_path, dpi=300, bbox_inches='tight')
        plt.close()
        
        logger.info(f"💾 熱力圖已保存: {save_path}")
        return save_path
    
    def generate_plotly_heatmap(self, time_interval=None, metric='total_pnl', save_path=None):
        """使用plotly生成互動式熱力圖"""
        pivot = self.create_pivot_table(time_interval, metric)
        if pivot is None:
            return None
        
        # 創建互動式熱力圖
        fig = go.Figure(data=go.Heatmap(
            z=pivot.values,
            x=pivot.columns,
            y=pivot.index,
            colorscale='RdYlGn',
            zmid=0,
            text=pivot.values,
            texttemplate="%{text:.1f}",
            textfont={"size": 10},
            colorbar=dict(title=f"{metric} (點)")
        ))
        
        # 設置標題和標籤
        title = f'停損vs停利熱力圖 - {metric}'
        if time_interval:
            title += f' ({time_interval})'
        
        fig.update_layout(
            title=title,
            xaxis_title='停利點數',
            yaxis_title='停損點數',
            width=800,
            height=600
        )
        
        # 保存互動式圖表
        if save_path is None:
            interval_suffix = f"_{time_interval.replace(':', '').replace('-', '_')}" if time_interval else "_all"
            save_path = self.output_dir / f"interactive_heatmap_{metric}{interval_suffix}.html"
        
        fig.write_html(save_path)
        
        logger.info(f"💾 互動式熱力圖已保存: {save_path}")
        return save_path
    
    def generate_comparison_heatmaps(self, metric='total_pnl'):
        """生成多時間區間比較熱力圖"""
        if self.results_df is None:
            logger.error("❌ 沒有實驗結果數據")
            return None
        
        # 獲取所有時間區間
        time_intervals = self.results_df['time_interval'].unique()
        
        # 創建子圖
        fig = make_subplots(
            rows=1, cols=len(time_intervals),
            subplot_titles=time_intervals,
            shared_yaxes=True
        )
        
        for i, interval in enumerate(time_intervals):
            pivot = self.create_pivot_table(interval, metric)
            if pivot is not None:
                fig.add_trace(
                    go.Heatmap(
                        z=pivot.values,
                        x=pivot.columns,
                        y=pivot.index,
                        colorscale='RdYlGn',
                        zmid=0,
                        showscale=(i == len(time_intervals) - 1),  # 只在最後一個子圖顯示色階
                        colorbar=dict(title=f"{metric} (點)") if i == len(time_intervals) - 1 else None
                    ),
                    row=1, col=i+1
                )
        
        # 更新布局
        fig.update_layout(
            title=f'時間區間比較熱力圖 - {metric}',
            height=500,
            width=300 * len(time_intervals)
        )
        
        # 更新軸標籤
        for i in range(len(time_intervals)):
            fig.update_xaxes(title_text='停利點數', row=1, col=i+1)
            if i == 0:
                fig.update_yaxes(title_text='停損點數', row=1, col=i+1)
        
        # 保存比較圖
        save_path = self.output_dir / f"comparison_heatmap_{metric}.html"
        fig.write_html(save_path)
        
        logger.info(f"💾 比較熱力圖已保存: {save_path}")
        return save_path
    
    def find_optimal_parameters(self, metric='total_pnl', top_n=10):
        """找出最佳參數組合"""
        if self.results_df is None:
            logger.error("❌ 沒有實驗結果數據")
            return None
        
        # 按指標排序
        sorted_df = self.results_df.sort_values(metric, ascending=False)
        top_results = sorted_df.head(top_n)
        
        logger.info(f"🏆 Top {top_n} 最佳參數組合 ({metric}):")
        for i, (_, row) in enumerate(top_results.iterrows(), 1):
            logger.info(f"{i:2d}. 停損:{row['stop_loss_points']:3d} 停利:{row['take_profit_points']:3d} "
                       f"區間:{row['time_interval']} {metric}:{row[metric]:8.2f}")
        
        return top_results
    
    def generate_all_heatmaps(self, metrics=None):
        """生成所有類型的熱力圖"""
        if metrics is None:
            metrics = ['total_pnl', 'win_rate', 'long_pnl', 'short_pnl']
        
        if self.results_df is None:
            logger.error("❌ 沒有實驗結果數據")
            return
        
        logger.info("🎨 開始生成所有熱力圖...")
        
        # 獲取所有時間區間
        time_intervals = self.results_df['time_interval'].unique()
        
        generated_files = []
        
        for metric in metrics:
            logger.info(f"📊 生成 {metric} 熱力圖...")
            
            # 生成整體熱力圖
            static_path = self.generate_matplotlib_heatmap(metric=metric)
            interactive_path = self.generate_plotly_heatmap(metric=metric)
            if static_path:
                generated_files.append(static_path)
            if interactive_path:
                generated_files.append(interactive_path)
            
            # 生成各時間區間熱力圖
            for interval in time_intervals:
                static_path = self.generate_matplotlib_heatmap(interval, metric)
                interactive_path = self.generate_plotly_heatmap(interval, metric)
                if static_path:
                    generated_files.append(static_path)
                if interactive_path:
                    generated_files.append(interactive_path)
            
            # 生成比較熱力圖
            comparison_path = self.generate_comparison_heatmaps(metric)
            if comparison_path:
                generated_files.append(comparison_path)
        
        logger.info(f"🎉 熱力圖生成完成！共生成 {len(generated_files)} 個文件")
        return generated_files
    
    def create_summary_report(self):
        """創建總結報告"""
        if self.results_df is None:
            logger.error("❌ 沒有實驗結果數據")
            return None
        
        report_path = self.output_dir / "heatmap_analysis_report.txt"
        
        with open(report_path, 'w', encoding='utf-8') as f:
            f.write("=" * 60 + "\n")
            f.write("反轉策略參數優化熱力圖分析報告\n")
            f.write("=" * 60 + "\n\n")
            
            # 基本統計
            f.write(f"實驗總數: {len(self.results_df)}\n")
            f.write(f"獲利實驗數: {len(self.results_df[self.results_df['total_pnl'] > 0])}\n")
            f.write(f"多空都獲利實驗數: {len(self.results_df[self.results_df['both_profitable']])}\n\n")
            
            # 各指標最佳結果
            metrics = ['total_pnl', 'long_pnl', 'short_pnl', 'win_rate']
            for metric in metrics:
                f.write(f"最佳 {metric}:\n")
                top_results = self.find_optimal_parameters(metric, top_n=5)
                for i, (_, row) in enumerate(top_results.iterrows(), 1):
                    f.write(f"  {i}. 停損:{row['stop_loss_points']} 停利:{row['take_profit_points']} "
                           f"區間:{row['time_interval']} 值:{row[metric]:.2f}\n")
                f.write("\n")
        
        logger.info(f"📋 分析報告已保存: {report_path}")
        return report_path


if __name__ == "__main__":
    # 示例用法
    generator = HeatmapGenerator()
    
    # 載入實驗結果（需要先運行parameter_optimizer.py）
    csv_files = list(Path("results").glob("parameter_optimization_results_*.csv"))
    if csv_files:
        latest_csv = max(csv_files, key=lambda x: x.stat().st_mtime)
        if generator.load_results_from_csv(latest_csv):
            # 生成所有熱力圖
            generator.generate_all_heatmaps()
            
            # 創建總結報告
            generator.create_summary_report()
            
            # 找出最佳參數
            generator.find_optimal_parameters('total_pnl', top_n=10)
    else:
        logger.warning("⚠️ 未找到實驗結果文件，請先運行parameter_optimizer.py")
