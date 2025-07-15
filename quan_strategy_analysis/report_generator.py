# report_generator.py - 報告生成器
"""
生成HTML和PDF格式的策略分析報告
整合統計數據和圖表
"""

import logging
import json
import base64
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Tuple, Optional, Any
import pandas as pd
from jinja2 import Template

from config import REPORT_CONFIG, CHARTS_DIR, REPORTS_DIR, PROCESSED_DIR, OUTPUT_FILES
from utils import format_number, ensure_directory_exists

logger = logging.getLogger(__name__)

class ReportGenerator:
    """策略分析報告生成器"""
    
    def __init__(self, daily_df: pd.DataFrame, events_df: pd.DataFrame, 
                 statistics: Dict[str, Any], chart_files: Dict[str, str]):
        self.daily_df = daily_df
        self.events_df = events_df
        self.statistics = statistics
        self.chart_files = chart_files
        
        # 確保輸出目錄存在
        ensure_directory_exists(REPORTS_DIR)
    
    def generate_html_report(self) -> str:
        """生成HTML報告"""
        logger.info("開始生成HTML報告...")
        
        # 準備報告數據
        report_data = self._prepare_report_data()
        
        # 生成HTML內容
        html_content = self._generate_html_content(report_data)
        
        # 儲存HTML報告
        html_file = REPORTS_DIR / OUTPUT_FILES['html_report']
        with open(html_file, 'w', encoding='utf-8') as f:
            f.write(html_content)
        
        logger.info(f"HTML報告已生成: {html_file}")
        return str(html_file)
    
    def _prepare_report_data(self) -> Dict[str, Any]:
        """準備報告數據"""
        # 基本統計
        basic_metrics = self.statistics.get('basic_metrics', {})
        risk_metrics = self.statistics.get('risk_metrics', {})
        trade_analysis = self.statistics.get('trade_analysis', {})
        lot_analysis = self.statistics.get('lot_analysis', {})
        
        # 圖表數據（轉換為base64）
        chart_data = {}
        for chart_name, chart_path in self.chart_files.items():
            if chart_path and Path(chart_path).exists() and chart_path.endswith('.png'):
                with open(chart_path, 'rb') as f:
                    chart_data[chart_name] = base64.b64encode(f.read()).decode('utf-8')
        
        # 交易摘要表
        trade_summary = self._create_trade_summary_table()
        
        # 月度績效表
        monthly_summary = self._create_monthly_summary_table()
        
        return {
            'report_title': REPORT_CONFIG['title'],
            'generation_time': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            'basic_metrics': basic_metrics,
            'risk_metrics': risk_metrics,
            'trade_analysis': trade_analysis,
            'lot_analysis': lot_analysis,
            'chart_data': chart_data,
            'trade_summary': trade_summary,
            'monthly_summary': monthly_summary,
            'total_trades': len(self.daily_df[self.daily_df['direction'].notna()]),
            'analysis_period': self._get_analysis_period()
        }
    
    def _create_trade_summary_table(self) -> List[Dict[str, Any]]:
        """創建交易摘要表"""
        if self.daily_df.empty:
            return []

        # 確保日期格式正確
        if 'trade_date' in self.daily_df.columns:
            self.daily_df['trade_date'] = pd.to_datetime(self.daily_df['trade_date'])

        summary = []
        for _, row in self.daily_df.iterrows():
            if pd.notna(row['direction']):
                # 處理日期
                date_str = ''
                if pd.notna(row['trade_date']):
                    if isinstance(row['trade_date'], str):
                        date_str = row['trade_date']
                    else:
                        date_str = row['trade_date'].strftime('%Y-%m-%d')

                # 處理時間
                time_str = ''
                if pd.notna(row.get('entry_time')):
                    if isinstance(row['entry_time'], str):
                        time_str = row['entry_time']
                    else:
                        time_str = row['entry_time'].strftime('%H:%M:%S')

                summary.append({
                    'date': date_str,
                    'direction': row['direction'],
                    'entry_price': int(row['entry_price']) if pd.notna(row['entry_price']) else '',
                    'entry_time': time_str,
                    'pnl': f"{row['total_pnl']:+.0f}" if pd.notna(row['total_pnl']) else '',
                    'lots': int(row['total_lots']) if pd.notna(row['total_lots']) else '',
                    'range_low': int(row['range_low']) if pd.notna(row['range_low']) else '',
                    'range_high': int(row['range_high']) if pd.notna(row['range_high']) else ''
                })

        return summary
    
    def _create_monthly_summary_table(self) -> List[Dict[str, Any]]:
        """創建月度摘要表"""
        if self.daily_df.empty:
            return []

        try:
            # 確保日期格式正確
            if 'trade_date' in self.daily_df.columns:
                self.daily_df['trade_date'] = pd.to_datetime(self.daily_df['trade_date'])

            # 按月統計
            self.daily_df['year_month'] = self.daily_df['trade_date'].dt.to_period('M')
            monthly_stats = self.daily_df.groupby('year_month').agg({
                'total_pnl': ['sum', 'count'],
                'direction': lambda x: (x == 'LONG').sum()
            })

            monthly_stats.columns = ['total_pnl', 'trade_count', 'long_count']
            monthly_stats['short_count'] = monthly_stats['trade_count'] - monthly_stats['long_count']

            # 計算勝率
            win_counts = self.daily_df[self.daily_df['total_pnl'] > 0].groupby('year_month').size()
            monthly_stats['win_count'] = win_counts.reindex(monthly_stats.index, fill_value=0)
            monthly_stats['win_rate'] = (monthly_stats['win_count'] / monthly_stats['trade_count'] * 100).fillna(0)

            summary = []
            for period, row in monthly_stats.iterrows():
                summary.append({
                    'month': str(period),
                    'total_pnl': f"{row['total_pnl']:+.0f}",
                    'trade_count': int(row['trade_count']),
                    'long_count': int(row['long_count']),
                    'short_count': int(row['short_count']),
                    'win_rate': f"{row['win_rate']:.1f}%"
                })

            return summary
        except Exception as e:
            logger.warning(f"創建月度摘要表時發生錯誤: {e}")
            return []
    
    def _get_analysis_period(self) -> str:
        """獲取分析期間"""
        if self.daily_df.empty:
            return "無資料"

        try:
            # 確保日期格式正確
            if 'trade_date' in self.daily_df.columns:
                self.daily_df['trade_date'] = pd.to_datetime(self.daily_df['trade_date'])

            start_date = self.daily_df['trade_date'].min().strftime('%Y-%m-%d')
            end_date = self.daily_df['trade_date'].max().strftime('%Y-%m-%d')
            return f"{start_date} 至 {end_date}"
        except Exception as e:
            logger.warning(f"獲取分析期間時發生錯誤: {e}")
            return "無法確定期間"
    
    def _generate_html_content(self, report_data: Dict[str, Any]) -> str:
        """生成HTML內容"""
        html_template = """
<!DOCTYPE html>
<html lang="zh-TW">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{{ report_title }}</title>
    <style>
        body {
            font-family: 'Microsoft JhengHei', Arial, sans-serif;
            margin: 0;
            padding: 20px;
            background-color: #f5f5f5;
            color: #333;
        }
        .container {
            max-width: 1200px;
            margin: 0 auto;
            background-color: white;
            padding: 30px;
            border-radius: 10px;
            box-shadow: 0 0 20px rgba(0,0,0,0.1);
        }
        .header {
            text-align: center;
            border-bottom: 3px solid #2E86AB;
            padding-bottom: 20px;
            margin-bottom: 30px;
        }
        .header h1 {
            color: #2E86AB;
            margin: 0;
            font-size: 2.5em;
        }
        .header p {
            color: #666;
            margin: 10px 0 0 0;
            font-size: 1.1em;
        }
        .metrics-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
            gap: 20px;
            margin-bottom: 30px;
        }
        .metric-card {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 20px;
            border-radius: 10px;
            text-align: center;
            box-shadow: 0 4px 15px rgba(0,0,0,0.1);
        }
        .metric-card h3 {
            margin: 0 0 10px 0;
            font-size: 1.1em;
            opacity: 0.9;
        }
        .metric-card .value {
            font-size: 2em;
            font-weight: bold;
            margin: 0;
        }
        .section {
            margin-bottom: 40px;
        }
        .section h2 {
            color: #2E86AB;
            border-left: 4px solid #2E86AB;
            padding-left: 15px;
            margin-bottom: 20px;
        }
        .chart-container {
            text-align: center;
            margin: 20px 0;
        }
        .chart-container img {
            max-width: 100%;
            height: auto;
            border-radius: 8px;
            box-shadow: 0 2px 10px rgba(0,0,0,0.1);
        }
        table {
            width: 100%;
            border-collapse: collapse;
            margin: 20px 0;
            background: white;
            border-radius: 8px;
            overflow: hidden;
            box-shadow: 0 2px 10px rgba(0,0,0,0.1);
        }
        th, td {
            padding: 12px;
            text-align: left;
            border-bottom: 1px solid #ddd;
        }
        th {
            background-color: #2E86AB;
            color: white;
            font-weight: bold;
        }
        tr:hover {
            background-color: #f5f5f5;
        }
        .positive {
            color: #28a745;
            font-weight: bold;
        }
        .negative {
            color: #dc3545;
            font-weight: bold;
        }
        .footer {
            text-align: center;
            margin-top: 40px;
            padding-top: 20px;
            border-top: 1px solid #ddd;
            color: #666;
        }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>{{ report_title }}</h1>
            <p>分析期間: {{ analysis_period }}</p>
            <p>報告生成時間: {{ generation_time }}</p>
        </div>

        <!-- 關鍵指標 -->
        <div class="section">
            <h2>關鍵績效指標</h2>
            <div class="metrics-grid">
                <div class="metric-card">
                    <h3>總損益</h3>
                    <p class="value">{{ "%.0f"|format(basic_metrics.total_pnl or 0) }}</p>
                </div>
                <div class="metric-card">
                    <h3>勝率</h3>
                    <p class="value">{{ "%.1f%%"|format(basic_metrics.win_rate or 0) }}</p>
                </div>
                <div class="metric-card">
                    <h3>獲利因子</h3>
                    <p class="value">{{ "%.2f"|format(basic_metrics.profit_factor or 0) }}</p>
                </div>
                <div class="metric-card">
                    <h3>最大回撤</h3>
                    <p class="value">{{ "%.1f%%"|format((risk_metrics.max_drawdown or 0) * 100) }}</p>
                </div>
                <div class="metric-card">
                    <h3>夏普比率</h3>
                    <p class="value">{{ "%.2f"|format(risk_metrics.sharpe_ratio or 0) }}</p>
                </div>
                <div class="metric-card">
                    <h3>總交易次數</h3>
                    <p class="value">{{ total_trades }}</p>
                </div>
            </div>
        </div>

        <!-- 圖表區域 -->
        <div class="section">
            <h2>視覺化分析</h2>
            
            {% if chart_data.daily_pnl %}
            <div class="chart-container">
                <h3>每日損益分析</h3>
                <img src="data:image/png;base64,{{ chart_data.daily_pnl }}" alt="每日損益分析">
            </div>
            {% endif %}
            
            {% if chart_data.equity_curve %}
            <div class="chart-container">
                <h3>資金曲線</h3>
                <img src="data:image/png;base64,{{ chart_data.equity_curve }}" alt="資金曲線">
            </div>
            {% endif %}
            
            {% if chart_data.pnl_distribution %}
            <div class="chart-container">
                <h3>損益分布</h3>
                <img src="data:image/png;base64,{{ chart_data.pnl_distribution }}" alt="損益分布">
            </div>
            {% endif %}
            
            {% if chart_data.direction_analysis %}
            <div class="chart-container">
                <h3>多空分析</h3>
                <img src="data:image/png;base64,{{ chart_data.direction_analysis }}" alt="多空分析">
            </div>
            {% endif %}
        </div>

        <!-- 交易明細 -->
        <div class="section">
            <h2>交易明細</h2>
            <table>
                <thead>
                    <tr>
                        <th>日期</th>
                        <th>方向</th>
                        <th>進場價</th>
                        <th>進場時間</th>
                        <th>口數</th>
                        <th>損益</th>
                        <th>區間低點</th>
                        <th>區間高點</th>
                    </tr>
                </thead>
                <tbody>
                    {% for trade in trade_summary %}
                    <tr>
                        <td>{{ trade.date }}</td>
                        <td>{{ trade.direction }}</td>
                        <td>{{ trade.entry_price }}</td>
                        <td>{{ trade.entry_time }}</td>
                        <td>{{ trade.lots }}</td>
                        <td class="{% if trade.pnl.startswith('+') %}positive{% else %}negative{% endif %}">{{ trade.pnl }}</td>
                        <td>{{ trade.range_low }}</td>
                        <td>{{ trade.range_high }}</td>
                    </tr>
                    {% endfor %}
                </tbody>
            </table>
        </div>

        <!-- 月度摘要 -->
        {% if monthly_summary %}
        <div class="section">
            <h2>月度績效摘要</h2>
            <table>
                <thead>
                    <tr>
                        <th>月份</th>
                        <th>總損益</th>
                        <th>交易次數</th>
                        <th>多單次數</th>
                        <th>空單次數</th>
                        <th>勝率</th>
                    </tr>
                </thead>
                <tbody>
                    {% for month in monthly_summary %}
                    <tr>
                        <td>{{ month.month }}</td>
                        <td class="{% if month.total_pnl.startswith('+') %}positive{% else %}negative{% endif %}">{{ month.total_pnl }}</td>
                        <td>{{ month.trade_count }}</td>
                        <td>{{ month.long_count }}</td>
                        <td>{{ month.short_count }}</td>
                        <td>{{ month.win_rate }}</td>
                    </tr>
                    {% endfor %}
                </tbody>
            </table>
        </div>
        {% endif %}

        <div class="footer">
            <p>本報告由策略分析工具自動生成</p>
        </div>
    </div>
</body>
</html>
        """
        
        template = Template(html_template)
        return template.render(**report_data)

def generate_strategy_report(daily_df: pd.DataFrame, events_df: pd.DataFrame,
                           statistics: Dict[str, Any], chart_files: Dict[str, str]) -> str:
    """生成策略分析報告的主函數"""
    generator = ReportGenerator(daily_df, events_df, statistics, chart_files)
    return generator.generate_html_report()

if __name__ == "__main__":
    import json
    from config import PROCESSED_DIR, OUTPUT_FILES, CHARTS_DIR
    
    # 載入資料
    daily_file = PROCESSED_DIR / OUTPUT_FILES['daily_pnl']
    events_file = PROCESSED_DIR / 'trade_events.csv'
    stats_file = PROCESSED_DIR / OUTPUT_FILES['statistics']
    
    if daily_file.exists() and events_file.exists() and stats_file.exists():
        daily_df = pd.read_csv(daily_file, index_col=0)
        events_df = pd.read_csv(events_file, index_col=0)
        
        with open(stats_file, 'r', encoding='utf-8') as f:
            statistics = json.load(f)
        
        # 模擬圖表檔案
        chart_files = {
            'daily_pnl': str(CHARTS_DIR / 'daily_pnl_analysis.png'),
            'equity_curve': str(CHARTS_DIR / 'equity_curve.png'),
            'pnl_distribution': str(CHARTS_DIR / 'pnl_distribution.png'),
            'direction_analysis': str(CHARTS_DIR / 'direction_analysis.png')
        }
        
        # 生成報告
        report_file = generate_strategy_report(daily_df, events_df, statistics, chart_files)
        print(f"報告已生成: {report_file}")
    else:
        print("找不到必要的資料檔案")
