# visualization.py - 視覺化工具
"""
生成各種分析圖表
包含每日損益、資金曲線、分布圖等
"""

import logging
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
import seaborn as sns
import plotly.graph_objects as go
import plotly.express as px
from plotly.subplots import make_subplots
from datetime import datetime
from typing import Dict, List, Tuple, Optional, Any
from pathlib import Path

from config import CHART_CONFIG, CHARTS_DIR, PROCESSED_DIR, OUTPUT_FILES, ANALYSIS_CONFIG
from utils import format_number, ensure_directory_exists, format_currency, points_to_currency

logger = logging.getLogger(__name__)

# 設定matplotlib使用英文字體避免中文顯示問題
plt.rcParams['font.family'] = 'DejaVu Sans'
plt.rcParams['axes.unicode_minus'] = False

class StrategyVisualizer:
    """策略視覺化工具"""
    
    def __init__(self, daily_df: pd.DataFrame, events_df: pd.DataFrame, statistics: Dict[str, Any]):
        self.daily_df = daily_df.copy()
        self.events_df = events_df.copy()
        self.statistics = statistics
        
        # 確保日期格式正確
        if not self.daily_df.empty:
            self.daily_df['trade_date'] = pd.to_datetime(self.daily_df['trade_date'])
            self.daily_df = self.daily_df.sort_values('trade_date')
            
        if not self.events_df.empty:
            self.events_df['trade_date'] = pd.to_datetime(self.events_df['trade_date'])
            self.events_df['timestamp'] = pd.to_datetime(self.events_df['timestamp'])
        
        # 設定圖表樣式
        plt.style.use('default')
        sns.set_palette(CHART_CONFIG['color_palette'])
        
        # 確保輸出目錄存在
        ensure_directory_exists(CHARTS_DIR)
    
    def create_all_charts(self) -> Dict[str, str]:
        """生成所有圖表"""
        logger.info("開始生成圖表...")
        
        chart_files = {}
        
        # 每日損益圖表
        chart_files['daily_pnl'] = self.create_daily_pnl_chart()
        
        # 資金曲線圖
        chart_files['equity_curve'] = self.create_equity_curve_chart()
        
        # 損益分布圖
        chart_files['pnl_distribution'] = self.create_pnl_distribution_chart()
        
        # 口數貢獻圖
        chart_files['lot_contribution'] = self.create_lot_contribution_chart()
        
        # 月度績效圖
        chart_files['monthly_performance'] = self.create_monthly_performance_chart()
        
        # 回撤分析圖
        chart_files['drawdown_analysis'] = self.create_drawdown_analysis_chart()
        
        # 交易方向分析圖
        chart_files['direction_analysis'] = self.create_direction_analysis_chart()
        
        # 互動式儀表板
        chart_files['interactive_dashboard'] = self.create_interactive_dashboard()
        
        logger.info(f"圖表生成完成，共生成 {len(chart_files)} 個圖表")
        return chart_files
    
    def create_daily_pnl_chart(self) -> str:
        """創建每日損益圖表"""
        if self.daily_df.empty:
            return ""
        
        fig, (ax1, ax2) = plt.subplots(2, 1, figsize=CHART_CONFIG['figure_size'], height_ratios=[2, 1])
        
        # 上圖：每日損益柱狀圖（轉換為台幣）
        daily_pnl_currency = self.daily_df['total_pnl'] * ANALYSIS_CONFIG['point_value']
        colors = ['green' if x > 0 else 'red' for x in self.daily_df['total_pnl']]
        bars = ax1.bar(self.daily_df['trade_date'], daily_pnl_currency, color=colors, alpha=0.7)

        ax1.set_title('Daily P&L Analysis', fontsize=CHART_CONFIG['title_size'], fontweight='bold')
        ax1.set_ylabel('P&L (NT$)', fontsize=CHART_CONFIG['font_size'])
        ax1.grid(True, alpha=0.3)
        ax1.axhline(y=0, color='black', linestyle='-', alpha=0.5)

        # 添加數值標籤（顯示台幣金額）
        for bar, currency_value in zip(bars, daily_pnl_currency):
            height = bar.get_height()
            ax1.text(bar.get_x() + bar.get_width()/2., height + (500 if height > 0 else -1500),
                    f'NT${currency_value:,.0f}', ha='center', va='bottom' if height > 0 else 'top', fontsize=8)
        
        # 下圖：累積損益曲線（轉換為台幣）
        cumulative_pnl = self.daily_df['total_pnl'].cumsum()
        cumulative_pnl_currency = cumulative_pnl * ANALYSIS_CONFIG['point_value']
        ax2.plot(self.daily_df['trade_date'], cumulative_pnl_currency, marker='o', linewidth=2, markersize=4)
        ax2.set_title('Cumulative P&L Curve', fontsize=CHART_CONFIG['font_size'])
        ax2.set_ylabel('Cumulative P&L (NT$)', fontsize=CHART_CONFIG['font_size'])
        ax2.set_xlabel('Date', fontsize=CHART_CONFIG['font_size'])
        ax2.grid(True, alpha=0.3)
        ax2.axhline(y=0, color='black', linestyle='-', alpha=0.5)
        
        # 格式化日期軸
        for ax in [ax1, ax2]:
            ax.xaxis.set_major_formatter(mdates.DateFormatter('%m-%d'))
            ax.xaxis.set_major_locator(mdates.DayLocator(interval=1))
            plt.setp(ax.xaxis.get_majorticklabels(), rotation=45)
        
        plt.tight_layout()
        
        # 儲存圖表
        filename = 'daily_pnl_analysis.png'
        filepath = CHARTS_DIR / filename
        plt.savefig(filepath, dpi=CHART_CONFIG['dpi'], bbox_inches='tight')
        plt.close()

        logger.info(f"Daily P&L chart saved: {filepath}")
        return str(filepath)
    
    def create_equity_curve_chart(self) -> str:
        """創建資金曲線圖"""
        if self.daily_df.empty:
            return ""
        
        fig, ax = plt.subplots(figsize=CHART_CONFIG['figure_size'])
        
        # 計算資金曲線（轉換為台幣）
        equity_curve = self.daily_df['total_pnl'].cumsum()
        equity_curve_currency = equity_curve * ANALYSIS_CONFIG['point_value']
        drawdown = self._calculate_drawdown_series(equity_curve)
        drawdown_currency = drawdown * ANALYSIS_CONFIG['point_value']

        # 繪製資金曲線
        ax.plot(self.daily_df['trade_date'], equity_curve_currency, linewidth=2, label='Equity Curve', color='blue')

        # 繪製回撤區域
        ax.fill_between(self.daily_df['trade_date'], equity_curve_currency, equity_curve_currency + drawdown_currency,
                       alpha=0.3, color='red', label='Drawdown Area')

        ax.set_title('Equity Curve & Drawdown Analysis', fontsize=CHART_CONFIG['title_size'], fontweight='bold')
        ax.set_ylabel('Cumulative P&L (NT$)', fontsize=CHART_CONFIG['font_size'])
        ax.set_xlabel('Date', fontsize=CHART_CONFIG['font_size'])
        ax.grid(True, alpha=0.3)
        ax.legend()
        
        # 添加統計資訊
        max_dd = self.statistics.get('risk_metrics', {}).get('max_drawdown', 0)
        total_return = equity_curve.iloc[-1] if len(equity_curve) > 0 else 0
        total_return_currency = total_return * ANALYSIS_CONFIG['point_value']

        textstr = f'Total Return: NT${total_return_currency:,.0f}\nMax Drawdown: {max_dd:.2%}'
        props = dict(boxstyle='round', facecolor='wheat', alpha=0.8)
        ax.text(0.02, 0.98, textstr, transform=ax.transAxes, fontsize=10,
                verticalalignment='top', bbox=props)
        
        # 格式化日期軸
        ax.xaxis.set_major_formatter(mdates.DateFormatter('%m-%d'))
        plt.setp(ax.xaxis.get_majorticklabels(), rotation=45)
        
        plt.tight_layout()
        
        # 儲存圖表
        filename = 'equity_curve.png'
        filepath = CHARTS_DIR / filename
        plt.savefig(filepath, dpi=CHART_CONFIG['dpi'], bbox_inches='tight')
        plt.close()

        logger.info(f"Equity curve chart saved: {filepath}")
        return str(filepath)
    
    def create_pnl_distribution_chart(self) -> str:
        """創建損益分布圖"""
        if self.daily_df.empty:
            return ""
        
        fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(15, 6))
        
        # 左圖：損益直方圖（轉換為台幣）
        pnl_currency = self.daily_df['total_pnl'] * ANALYSIS_CONFIG['point_value']
        ax1.hist(pnl_currency, bins=10, alpha=0.7, color='skyblue', edgecolor='black')
        mean_currency = pnl_currency.mean()
        ax1.axvline(mean_currency, color='red', linestyle='--',
                   label=f'Mean: NT${mean_currency:,.0f}')
        ax1.set_title('P&L Distribution Histogram', fontsize=CHART_CONFIG['title_size'])
        ax1.set_xlabel('P&L (NT$)', fontsize=CHART_CONFIG['font_size'])
        ax1.set_ylabel('Frequency', fontsize=CHART_CONFIG['font_size'])
        ax1.grid(True, alpha=0.3)
        ax1.legend()
        
        # 右圖：盒鬚圖（轉換為台幣）
        box_data = [
            (self.daily_df[self.daily_df['total_pnl'] > 0]['total_pnl'] * ANALYSIS_CONFIG['point_value']).dropna(),
            (self.daily_df[self.daily_df['total_pnl'] < 0]['total_pnl'] * ANALYSIS_CONFIG['point_value']).dropna()
        ]
        labels = ['Winning Trades', 'Losing Trades']

        bp = ax2.boxplot(box_data, labels=labels, patch_artist=True)
        bp['boxes'][0].set_facecolor('lightgreen')
        bp['boxes'][1].set_facecolor('lightcoral')

        ax2.set_title('Win/Loss Distribution', fontsize=CHART_CONFIG['title_size'])
        ax2.set_ylabel('P&L (NT$)', fontsize=CHART_CONFIG['font_size'])
        ax2.grid(True, alpha=0.3)
        
        plt.tight_layout()
        
        # 儲存圖表
        filename = 'pnl_distribution.png'
        filepath = CHARTS_DIR / filename
        plt.savefig(filepath, dpi=CHART_CONFIG['dpi'], bbox_inches='tight')
        plt.close()

        logger.info(f"P&L distribution chart saved: {filepath}")
        return str(filepath)
    
    def create_lot_contribution_chart(self) -> str:
        """創建口數貢獻圖"""
        if self.events_df.empty:
            return ""
        
        # 計算各口數的貢獻
        lot_pnl = self.events_df[self.events_df['pnl'].notna()].groupby('lot_number')['pnl'].sum()
        
        if lot_pnl.empty:
            return ""
        
        fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(15, 6))
        
        # 左圖：口數貢獻柱狀圖（轉換為台幣）
        lot_pnl_currency = lot_pnl * ANALYSIS_CONFIG['point_value']
        colors = ['green' if x > 0 else 'red' for x in lot_pnl.values]
        bars = ax1.bar([f'Lot {int(i)}' for i in lot_pnl.index], lot_pnl_currency.values, color=colors, alpha=0.7)

        ax1.set_title('P&L Contribution by Lot', fontsize=CHART_CONFIG['title_size'])
        ax1.set_ylabel('P&L (NT$)', fontsize=CHART_CONFIG['font_size'])
        ax1.grid(True, alpha=0.3)
        ax1.axhline(y=0, color='black', linestyle='-', alpha=0.5)

        # 添加數值標籤
        for bar, value in zip(bars, lot_pnl_currency.values):
            height = bar.get_height()
            ax1.text(bar.get_x() + bar.get_width()/2., height + (500 if height > 0 else -1500),
                    f'NT${int(value):,}', ha='center', va='bottom' if height > 0 else 'top')
        
        # 右圖：口數貢獻圓餅圖（只顯示正值）
        positive_lot_pnl = lot_pnl[lot_pnl > 0]
        if not positive_lot_pnl.empty:
            ax2.pie(positive_lot_pnl.values, labels=[f'Lot {int(i)}' for i in positive_lot_pnl.index],
                   autopct='%1.1f%%', startangle=90)
            ax2.set_title('Profitable Lots Contribution', fontsize=CHART_CONFIG['title_size'])
        
        plt.tight_layout()
        
        # 儲存圖表
        filename = 'lot_contribution.png'
        filepath = CHARTS_DIR / filename
        plt.savefig(filepath, dpi=CHART_CONFIG['dpi'], bbox_inches='tight')
        plt.close()

        logger.info(f"Lot contribution chart saved: {filepath}")
        return str(filepath)
    
    def create_monthly_performance_chart(self) -> str:
        """創建月度績效圖"""
        if self.daily_df.empty:
            return ""

        # 按月統計
        self.daily_df['year_month'] = self.daily_df['trade_date'].dt.to_period('M')
        monthly_pnl = self.daily_df.groupby('year_month')['total_pnl'].sum()

        if monthly_pnl.empty:
            return ""

        fig, ax = plt.subplots(figsize=CHART_CONFIG['figure_size'])

        colors = ['green' if x > 0 else 'red' for x in monthly_pnl.values]
        monthly_pnl_currency = monthly_pnl * ANALYSIS_CONFIG['point_value']
        bars = ax.bar(range(len(monthly_pnl)), monthly_pnl_currency.values, color=colors, alpha=0.7)

        ax.set_title('Monthly Performance Analysis', fontsize=CHART_CONFIG['title_size'], fontweight='bold')
        ax.set_ylabel('Monthly P&L (NT$)', fontsize=CHART_CONFIG['font_size'])
        ax.set_xlabel('Month', fontsize=CHART_CONFIG['font_size'])
        ax.set_xticks(range(len(monthly_pnl)))
        ax.set_xticklabels([str(period) for period in monthly_pnl.index], rotation=45)
        ax.grid(True, alpha=0.3)
        ax.axhline(y=0, color='black', linestyle='-', alpha=0.5)

        # 添加數值標籤
        for bar, value in zip(bars, monthly_pnl_currency.values):
            height = bar.get_height()
            ax.text(bar.get_x() + bar.get_width()/2., height + (500 if height > 0 else -1500),
                    f'NT${int(value):,}', ha='center', va='bottom' if height > 0 else 'top')

        plt.tight_layout()

        # 儲存圖表
        filename = 'monthly_performance.png'
        filepath = CHARTS_DIR / filename
        plt.savefig(filepath, dpi=CHART_CONFIG['dpi'], bbox_inches='tight')
        plt.close()

        logger.info(f"Monthly performance chart saved: {filepath}")
        return str(filepath)

    def create_drawdown_analysis_chart(self) -> str:
        """創建回撤分析圖"""
        if self.daily_df.empty:
            return ""

        equity_curve = self.daily_df['total_pnl'].cumsum()
        drawdown = self._calculate_drawdown_series(equity_curve)
        drawdown_pct = drawdown / equity_curve.expanding().max() * 100

        fig, ax = plt.subplots(figsize=CHART_CONFIG['figure_size'])

        ax.fill_between(self.daily_df['trade_date'], 0, drawdown_pct,
                       alpha=0.7, color='red', label='Drawdown %')
        ax.plot(self.daily_df['trade_date'], drawdown_pct, color='darkred', linewidth=1)

        ax.set_title('Drawdown Analysis', fontsize=CHART_CONFIG['title_size'], fontweight='bold')
        ax.set_ylabel('Drawdown (%)', fontsize=CHART_CONFIG['font_size'])
        ax.set_xlabel('Date', fontsize=CHART_CONFIG['font_size'])
        ax.grid(True, alpha=0.3)
        ax.legend()

        # 標記最大回撤點
        max_dd_idx = drawdown_pct.idxmin()
        max_dd_value = drawdown_pct.min()
        ax.annotate(f'Max DD: {max_dd_value:.1f}%',
                   xy=(self.daily_df.iloc[max_dd_idx]['trade_date'], max_dd_value),
                   xytext=(10, 10), textcoords='offset points',
                   bbox=dict(boxstyle='round,pad=0.3', facecolor='yellow', alpha=0.7),
                   arrowprops=dict(arrowstyle='->', connectionstyle='arc3,rad=0'))

        # 格式化日期軸
        ax.xaxis.set_major_formatter(mdates.DateFormatter('%m-%d'))
        plt.setp(ax.xaxis.get_majorticklabels(), rotation=45)

        plt.tight_layout()

        # 儲存圖表
        filename = 'drawdown_analysis.png'
        filepath = CHARTS_DIR / filename
        plt.savefig(filepath, dpi=CHART_CONFIG['dpi'], bbox_inches='tight')
        plt.close()

        logger.info(f"Drawdown analysis chart saved: {filepath}")
        return str(filepath)

    def create_direction_analysis_chart(self) -> str:
        """創建交易方向分析圖"""
        if self.daily_df.empty:
            return ""

        # 統計多空交易
        direction_stats = self.daily_df.groupby('direction').agg({
            'total_pnl': ['sum', 'mean', 'count']
        }).round(2)

        direction_stats.columns = ['總損益', '平均損益', '交易次數']
        direction_stats = direction_stats.reset_index()

        fig, ((ax1, ax2), (ax3, ax4)) = plt.subplots(2, 2, figsize=(15, 10))

        # 左上：多空總損益比較（轉換為台幣）
        total_pnl_currency = direction_stats['總損益'] * ANALYSIS_CONFIG['point_value']
        bars1 = ax1.bar(direction_stats['direction'], total_pnl_currency,
                       color=['green', 'red'], alpha=0.7)
        ax1.set_title('Long vs Short Total P&L', fontsize=CHART_CONFIG['font_size'])
        ax1.set_ylabel('Total P&L (NT$)', fontsize=CHART_CONFIG['font_size'])
        ax1.grid(True, alpha=0.3)

        for bar, value in zip(bars1, direction_stats['總損益']):
            height = bar.get_height()
            ax1.text(bar.get_x() + bar.get_width()/2., height + (5 if height > 0 else -15),
                    f'{value}', ha='center', va='bottom' if height > 0 else 'top')

        # 右上：多空平均損益比較（轉換為台幣）
        avg_pnl_currency = direction_stats['平均損益'] * ANALYSIS_CONFIG['point_value']
        bars2 = ax2.bar(direction_stats['direction'], avg_pnl_currency,
                       color=['green', 'red'], alpha=0.7)
        ax2.set_title('Long vs Short Average P&L', fontsize=CHART_CONFIG['font_size'])
        ax2.set_ylabel('Average P&L (NT$)', fontsize=CHART_CONFIG['font_size'])
        ax2.grid(True, alpha=0.3)

        for bar, value in zip(bars2, direction_stats['平均損益']):
            height = bar.get_height()
            ax2.text(bar.get_x() + bar.get_width()/2., height + (2 if height > 0 else -5),
                    f'{value}', ha='center', va='bottom' if height > 0 else 'top')

        # 左下：多空交易次數比較
        wedges, texts, autotexts = ax3.pie(direction_stats['交易次數'], labels=direction_stats['direction'],
                                          autopct='%1.1f%%', colors=['green', 'red'])
        for wedge in wedges:
            wedge.set_alpha(0.7)
        ax3.set_title('Long vs Short Trade Count', fontsize=CHART_CONFIG['font_size'])

        # 右下：多空勝率比較
        win_rates = []
        for direction in direction_stats['direction']:
            direction_trades = self.daily_df[self.daily_df['direction'] == direction]
            wins = len(direction_trades[direction_trades['total_pnl'] > 0])
            total = len(direction_trades)
            win_rate = wins / total * 100 if total > 0 else 0
            win_rates.append(win_rate)

        bars4 = ax4.bar(direction_stats['direction'], win_rates,
                       color=['green', 'red'], alpha=0.7)
        ax4.set_title('Long vs Short Win Rate', fontsize=CHART_CONFIG['font_size'])
        ax4.set_ylabel('Win Rate (%)', fontsize=CHART_CONFIG['font_size'])
        ax4.set_ylim(0, 100)
        ax4.grid(True, alpha=0.3)

        for bar, value in zip(bars4, win_rates):
            height = bar.get_height()
            ax4.text(bar.get_x() + bar.get_width()/2., height + 2,
                    f'{value:.1f}%', ha='center', va='bottom')

        plt.tight_layout()

        # 儲存圖表
        filename = 'direction_analysis.png'
        filepath = CHARTS_DIR / filename
        plt.savefig(filepath, dpi=CHART_CONFIG['dpi'], bbox_inches='tight')
        plt.close()

        logger.info(f"Direction analysis chart saved: {filepath}")
        return str(filepath)

    def create_interactive_dashboard(self) -> str:
        """創建互動式儀表板"""
        if self.daily_df.empty:
            return ""

        # 創建子圖
        fig = make_subplots(
            rows=2, cols=2,
            subplot_titles=('Daily P&L', 'Cumulative P&L', 'P&L Distribution', 'Lot Contribution'),
            specs=[[{"secondary_y": False}, {"secondary_y": False}],
                   [{"secondary_y": False}, {"secondary_y": False}]]
        )

        # 每日損益柱狀圖（轉換為台幣）
        daily_pnl_currency = self.daily_df['total_pnl'] * ANALYSIS_CONFIG['point_value']
        colors = ['green' if x > 0 else 'red' for x in self.daily_df['total_pnl']]
        fig.add_trace(
            go.Bar(x=self.daily_df['trade_date'], y=daily_pnl_currency,
                   marker_color=colors, name='Daily P&L', showlegend=False),
            row=1, col=1
        )

        # 累積損益曲線（轉換為台幣）
        cumulative_pnl = self.daily_df['total_pnl'].cumsum()
        cumulative_pnl_currency = cumulative_pnl * ANALYSIS_CONFIG['point_value']
        fig.add_trace(
            go.Scatter(x=self.daily_df['trade_date'], y=cumulative_pnl_currency,
                      mode='lines+markers', name='Cumulative P&L', showlegend=False),
            row=1, col=2
        )

        # 損益分布直方圖（轉換為台幣）
        fig.add_trace(
            go.Histogram(x=daily_pnl_currency, nbinsx=10,
                        name='P&L Distribution', showlegend=False),
            row=2, col=1
        )

        # 口數貢獻（如果有事件資料）
        if not self.events_df.empty:
            lot_pnl = self.events_df[self.events_df['pnl'].notna()].groupby('lot_number')['pnl'].sum()
            if not lot_pnl.empty:
                lot_pnl_currency = lot_pnl * ANALYSIS_CONFIG['point_value']
                fig.add_trace(
                    go.Bar(x=[f'Lot {int(i)}' for i in lot_pnl.index], y=lot_pnl_currency.values,
                          name='Lot Contribution', showlegend=False),
                    row=2, col=2
                )

        # 更新佈局
        fig.update_layout(
            title_text="Strategy Analysis Interactive Dashboard",
            title_x=0.5,
            height=800,
            showlegend=False
        )

        # 儲存互動式圖表
        filename = 'interactive_dashboard.html'
        filepath = CHARTS_DIR / filename
        fig.write_html(str(filepath))

        logger.info(f"Interactive dashboard saved: {filepath}")
        return str(filepath)

    def _calculate_drawdown_series(self, equity_curve: pd.Series) -> pd.Series:
        """計算回撤序列"""
        peak = equity_curve.expanding().max()
        drawdown = equity_curve - peak
        return drawdown

def create_all_visualizations(daily_df: pd.DataFrame, events_df: pd.DataFrame,
                            statistics: Dict[str, Any]) -> Dict[str, str]:
    """生成所有視覺化圖表的主函數"""
    visualizer = StrategyVisualizer(daily_df, events_df, statistics)
    return visualizer.create_all_charts()

if __name__ == "__main__":
    import json
    from config import PROCESSED_DIR, OUTPUT_FILES

    # 載入資料
    daily_file = PROCESSED_DIR / OUTPUT_FILES['daily_pnl']
    events_file = PROCESSED_DIR / 'trade_events.csv'
    stats_file = PROCESSED_DIR / OUTPUT_FILES['statistics']

    if daily_file.exists() and events_file.exists() and stats_file.exists():
        daily_df = pd.read_csv(daily_file, index_col=0)
        events_df = pd.read_csv(events_file, index_col=0)

        with open(stats_file, 'r', encoding='utf-8') as f:
            statistics = json.load(f)

        # 生成圖表
        chart_files = create_all_visualizations(daily_df, events_df, statistics)

        print("圖表生成完成：")
        for chart_type, filepath in chart_files.items():
            print(f"  {chart_type}: {filepath}")
    else:
        print("找不到必要的資料檔案，請先執行 data_extractor.py 和 statistics_calculator.py")
