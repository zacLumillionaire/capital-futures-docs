# range_analyzer.py - 開盤區間特性分析工具
"""
分析開盤區間大小與交易績效的關係
重點研究：區間大小分布、獲利相關性、最佳過濾閾值
"""

import logging
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from decimal import Decimal
from datetime import time, date
from typing import Dict, List, Tuple, Optional
import json

import importlib.util
import sys

# 動態導入包含特殊字符的模組
spec = importlib.util.spec_from_file_location("strategy_module", "multi_Profit-Funded Risk_多口.py")
strategy_module = importlib.util.module_from_spec(spec)
sys.modules["strategy_module"] = strategy_module
spec.loader.exec_module(strategy_module)

# 從動態導入的模組中獲取需要的類別和函數
StrategyConfig = strategy_module.StrategyConfig
RangeFilter = strategy_module.RangeFilter
run_backtest = strategy_module.run_backtest
StopLossType = strategy_module.StopLossType
LotRule = strategy_module.LotRule
from statistics_calculator import calculate_strategy_statistics
from data_extractor import extract_trading_data
import shared

# 設定日誌
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class RangeAnalyzer:
    """開盤區間分析器"""
    
    def __init__(self):
        self.range_data = []
        self.results_cache = {}
        
    def collect_range_statistics(self, start_date: str = None, end_date: str = None) -> pd.DataFrame:
        """收集所有交易日的開盤區間統計數據"""
        logger.info("🔍 開始收集開盤區間統計數據...")
        
        try:
            with shared.get_conn_cur_from_pool_b(as_dict=True) as (conn, cur):
                # 構建查詢
                base_query = "SELECT DISTINCT trade_datetime::date as trade_day FROM stock_prices"
                conditions = []
                params = []
                
                if start_date:
                    conditions.append("trade_datetime::date >= %s")
                    params.append(start_date)
                if end_date:
                    conditions.append("trade_datetime::date <= %s")
                    params.append(end_date)
                
                if conditions:
                    query = f"{base_query} WHERE {' AND '.join(conditions)} ORDER BY trade_day;"
                else:
                    query = f"{base_query} ORDER BY trade_day;"
                
                cur.execute(query, params)
                trade_days = [row['trade_day'] for row in cur.fetchall()]
                
                range_stats = []
                
                for day in trade_days:
                    cur.execute("SELECT * FROM stock_prices WHERE trade_datetime::date = %s ORDER BY trade_datetime;", (day,))
                    day_candles = [c for c in cur.fetchall() if time(8, 45) <= c['trade_datetime'].time() <= time(13, 45)]
                    
                    if len(day_candles) < 3:
                        continue
                    
                    # 取得8:46-8:47的K棒
                    candles_846_847 = [c for c in day_candles if c['trade_datetime'].time() in [time(8, 46), time(8, 47)]]
                    if len(candles_846_847) != 2:
                        continue
                    
                    range_high = max(c['high_price'] for c in candles_846_847)
                    range_low = min(c['low_price'] for c in candles_846_847)
                    range_size = float(range_high - range_low)
                    
                    # 計算當日是否有突破和方向
                    trade_candles = [c for c in day_candles if c['trade_datetime'].time() >= time(8, 48)]
                    breakout_direction = None
                    breakout_time = None
                    
                    for candle in trade_candles:
                        if candle['close_price'] > range_high:
                            breakout_direction = 'LONG'
                            breakout_time = candle['trade_datetime'].time()
                            break
                        elif candle['close_price'] < range_low:
                            breakout_direction = 'SHORT'
                            breakout_time = candle['trade_datetime'].time()
                            break
                    
                    range_stats.append({
                        'date': day,
                        'range_high': float(range_high),
                        'range_low': float(range_low),
                        'range_size': range_size,
                        'breakout_direction': breakout_direction,
                        'breakout_time': breakout_time,
                        'has_breakout': breakout_direction is not None
                    })
                
                df = pd.DataFrame(range_stats)
                logger.info(f"✅ 收集了 {len(df)} 個交易日的區間數據")
                return df
                
        except Exception as e:
            logger.error(f"❌ 收集區間統計數據失敗: {e}")
            return pd.DataFrame()
    
    def analyze_range_size_distribution(self, df: pd.DataFrame) -> Dict:
        """分析區間大小分布"""
        logger.info("📊 分析區間大小分布...")
        
        stats = {
            'total_days': len(df),
            'mean_range': df['range_size'].mean(),
            'median_range': df['range_size'].median(),
            'std_range': df['range_size'].std(),
            'min_range': df['range_size'].min(),
            'max_range': df['range_size'].max(),
            'percentiles': {
                '25%': df['range_size'].quantile(0.25),
                '50%': df['range_size'].quantile(0.50),
                '75%': df['range_size'].quantile(0.75),
                '90%': df['range_size'].quantile(0.90),
                '95%': df['range_size'].quantile(0.95)
            }
        }
        
        # 突破率分析
        breakout_rate = df['has_breakout'].mean()
        stats['breakout_rate'] = breakout_rate
        
        # 方向分析
        breakout_df = df[df['has_breakout']]
        if len(breakout_df) > 0:
            direction_counts = breakout_df['breakout_direction'].value_counts()
            stats['direction_distribution'] = direction_counts.to_dict()
            stats['long_ratio'] = direction_counts.get('LONG', 0) / len(breakout_df)
            stats['short_ratio'] = direction_counts.get('SHORT', 0) / len(breakout_df)
        
        return stats
    
    def test_range_filters(self, range_thresholds: List[float], start_date: str = None, end_date: str = None) -> pd.DataFrame:
        """測試不同區間過濾閾值的效果"""
        logger.info(f"🧪 測試區間過濾閾值: {range_thresholds}")
        
        results = []
        
        # 基準配置（無過濾）
        base_config = StrategyConfig(
            trade_size_in_lots=3,
            stop_loss_type=StopLossType.RANGE_BOUNDARY,
            lot_rules=[
                LotRule(use_trailing_stop=True, trailing_activation=Decimal(15), trailing_pullback=Decimal('0.20')),
                LotRule(use_trailing_stop=True, trailing_activation=Decimal(40), trailing_pullback=Decimal('0.20'), protective_stop_multiplier=Decimal('2.0')),
                LotRule(use_trailing_stop=True, trailing_activation=Decimal(65), trailing_pullback=Decimal('0.20'), protective_stop_multiplier=Decimal('2.0'))
            ]
        )
        
        # 測試無過濾的基準
        logger.info("測試基準配置（無區間過濾）...")
        baseline_result = self._run_single_backtest(base_config, "baseline", start_date, end_date)
        results.append(baseline_result)
        
        # 測試各種閾值
        for threshold in range_thresholds:
            logger.info(f"測試區間過濾閾值: {threshold} 點...")
            
            config = StrategyConfig(
                trade_size_in_lots=3,
                stop_loss_type=StopLossType.RANGE_BOUNDARY,
                lot_rules=base_config.lot_rules,
                range_filter=RangeFilter(
                    use_range_size_filter=True,
                    max_range_points=Decimal(str(threshold))
                )
            )
            
            result = self._run_single_backtest(config, f"filter_{threshold}", start_date, end_date)
            results.append(result)
        
        return pd.DataFrame(results)
    
    def _run_single_backtest(self, config: StrategyConfig, test_name: str, start_date: str = None, end_date: str = None) -> Dict:
        """執行單次回測並提取關鍵指標"""
        try:
            # 使用日誌處理器捕獲日誌
            import logging
            import io

            # 創建內存日誌處理器
            log_stream = io.StringIO()
            handler = logging.StreamHandler(log_stream)
            handler.setLevel(logging.INFO)
            formatter = logging.Formatter('%(message)s')
            handler.setFormatter(formatter)

            # 獲取策略模塊的logger
            strategy_logger = logging.getLogger('strategy_module')
            strategy_logger.addHandler(handler)
            original_level = strategy_logger.level
            strategy_logger.setLevel(logging.INFO)

            try:
                # 執行回測
                run_backtest(config, start_date, end_date)

                # 獲取日誌內容
                log_content = log_stream.getvalue()

                # 解析日誌提取統計數據
                stats = self._parse_backtest_log(log_content)
                stats['test_name'] = test_name
                stats['config'] = config

                return stats

            finally:
                # 清理日誌處理器
                strategy_logger.removeHandler(handler)
                strategy_logger.setLevel(original_level)
                handler.close()

        except Exception as e:
            logger.error(f"回測失敗 {test_name}: {e}")
            return {'test_name': test_name, 'error': str(e), 'total_pnl': 0, 'total_trades': 0, 'win_rate': 0}
    
    def _parse_backtest_log(self, log_content: str) -> Dict:
        """解析回測日誌提取統計數據"""
        lines = log_content.split('\n')

        stats = {
            'total_pnl': 0,
            'winning_trades': 0,
            'losing_trades': 0,
            'total_trades': 0,
            'long_trades': 0,
            'short_trades': 0,
            'long_pnl': 0,
            'short_pnl': 0
        }

        current_day_pnl = 0
        current_direction = None

        for line in lines:
            # 檢測交易方向
            if '📈 LONG' in line or 'LONG 突破' in line:
                current_direction = 'LONG'
                stats['long_trades'] += 1
            elif '📉 SHORT' in line or 'SHORT 突破' in line:
                current_direction = 'SHORT'
                stats['short_trades'] += 1

            # 檢測當日損益 - 支持多種格式
            if '當日損益:' in line or '當日PnL:' in line or '總損益:' in line:
                try:
                    # 提取數字部分
                    if '當日損益:' in line:
                        pnl_str = line.split('當日損益:')[1].strip()
                    elif '當日PnL:' in line:
                        pnl_str = line.split('當日PnL:')[1].strip()
                    elif '總損益:' in line:
                        pnl_str = line.split('總損益:')[1].strip()

                    # 清理字符串，只保留數字和符號
                    import re
                    pnl_match = re.search(r'[+-]?\d+\.?\d*', pnl_str)
                    if pnl_match:
                        current_day_pnl = float(pnl_match.group())
                        stats['total_pnl'] += current_day_pnl

                        if current_day_pnl > 0:
                            stats['winning_trades'] += 1
                        elif current_day_pnl < 0:
                            stats['losing_trades'] += 1

                        if current_direction == 'LONG':
                            stats['long_pnl'] += current_day_pnl
                        elif current_direction == 'SHORT':
                            stats['short_pnl'] += current_day_pnl

                except Exception as e:
                    logger.debug(f"解析損益失敗: {line}, 錯誤: {e}")
                    pass

            # 檢測總結行
            if '總獲利交易:' in line and '總虧損交易:' in line:
                try:
                    import re
                    win_match = re.search(r'總獲利交易:\s*(\d+)', line)
                    loss_match = re.search(r'總虧損交易:\s*(\d+)', line)
                    if win_match and loss_match:
                        stats['winning_trades'] = int(win_match.group(1))
                        stats['losing_trades'] = int(loss_match.group(1))
                except:
                    pass

        stats['total_trades'] = stats['winning_trades'] + stats['losing_trades']
        stats['win_rate'] = stats['winning_trades'] / max(stats['total_trades'], 1)

        return stats
    
    def create_range_analysis_report(self, range_df: pd.DataFrame, filter_results: pd.DataFrame) -> str:
        """生成區間分析報告"""
        logger.info("📋 生成區間分析報告...")
        
        # 創建圖表
        self._create_range_visualizations(range_df, filter_results)
        
        # 生成HTML報告
        html_content = self._generate_range_html_report(range_df, filter_results)
        
        # 保存報告
        from datetime import datetime
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        report_file = f"reports/range_analysis_report_{timestamp}.html"
        
        with open(report_file, 'w', encoding='utf-8') as f:
            f.write(html_content)
        
        logger.info(f"✅ 區間分析報告已生成: {report_file}")
        return report_file
    
    def _create_range_visualizations(self, range_df: pd.DataFrame, filter_results: pd.DataFrame):
        """創建區間分析視覺化圖表"""
        plt.style.use('default')
        plt.rcParams['font.sans-serif'] = ['Arial', 'DejaVu Sans']
        plt.rcParams['axes.unicode_minus'] = False
        
        # 1. 區間大小分布圖
        fig, axes = plt.subplots(2, 2, figsize=(15, 12))
        
        # 區間大小直方圖
        axes[0, 0].hist(range_df['range_size'], bins=30, alpha=0.7, color='skyblue', edgecolor='black')
        axes[0, 0].set_title('Range Size Distribution')
        axes[0, 0].set_xlabel('Range Size (Points)')
        axes[0, 0].set_ylabel('Frequency')
        axes[0, 0].grid(True, alpha=0.3)
        
        # 區間大小箱線圖
        axes[0, 1].boxplot(range_df['range_size'])
        axes[0, 1].set_title('Range Size Box Plot')
        axes[0, 1].set_ylabel('Range Size (Points)')
        axes[0, 1].grid(True, alpha=0.3)
        
        # 突破方向分布
        if 'breakout_direction' in range_df.columns:
            breakout_counts = range_df['breakout_direction'].value_counts()
            axes[1, 0].pie(breakout_counts.values, labels=breakout_counts.index, autopct='%1.1f%%')
            axes[1, 0].set_title('Breakout Direction Distribution')
        
        # 過濾效果比較
        if not filter_results.empty:
            filter_results_clean = filter_results.dropna(subset=['total_pnl'])
            axes[1, 1].bar(range(len(filter_results_clean)), filter_results_clean['total_pnl'])
            axes[1, 1].set_title('Filter Performance Comparison')
            axes[1, 1].set_xlabel('Filter Configuration')
            axes[1, 1].set_ylabel('Total PnL')
            axes[1, 1].set_xticks(range(len(filter_results_clean)))
            axes[1, 1].set_xticklabels(filter_results_clean['test_name'], rotation=45)
        
        plt.tight_layout()
        plt.savefig('charts/range_analysis.png', dpi=300, bbox_inches='tight')
        plt.close()
    
    def _generate_range_html_report(self, range_df: pd.DataFrame, filter_results: pd.DataFrame) -> str:
        """生成HTML格式的區間分析報告"""
        stats = self.analyze_range_size_distribution(range_df)
        
        html = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <title>Range Analysis Report</title>
            <style>
                body {{ font-family: Arial, sans-serif; margin: 20px; }}
                .header {{ background-color: #f0f0f0; padding: 20px; border-radius: 5px; }}
                .section {{ margin: 20px 0; }}
                .stats-table {{ border-collapse: collapse; width: 100%; }}
                .stats-table th, .stats-table td {{ border: 1px solid #ddd; padding: 8px; text-align: left; }}
                .stats-table th {{ background-color: #f2f2f2; }}
                .chart {{ text-align: center; margin: 20px 0; }}
            </style>
        </head>
        <body>
            <div class="header">
                <h1>📊 Opening Range Analysis Report</h1>
                <p>Generated on: {pd.Timestamp.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
            </div>
            
            <div class="section">
                <h2>📈 Range Size Statistics</h2>
                <table class="stats-table">
                    <tr><th>Metric</th><th>Value</th></tr>
                    <tr><td>Total Trading Days</td><td>{stats['total_days']}</td></tr>
                    <tr><td>Mean Range Size</td><td>{stats['mean_range']:.2f} points</td></tr>
                    <tr><td>Median Range Size</td><td>{stats['median_range']:.2f} points</td></tr>
                    <tr><td>Standard Deviation</td><td>{stats['std_range']:.2f} points</td></tr>
                    <tr><td>Min Range Size</td><td>{stats['min_range']:.2f} points</td></tr>
                    <tr><td>Max Range Size</td><td>{stats['max_range']:.2f} points</td></tr>
                    <tr><td>75th Percentile</td><td>{stats['percentiles']['75%']:.2f} points</td></tr>
                    <tr><td>90th Percentile</td><td>{stats['percentiles']['90%']:.2f} points</td></tr>
                    <tr><td>95th Percentile</td><td>{stats['percentiles']['95%']:.2f} points</td></tr>
                </table>
            </div>
            
            <div class="section">
                <h2>🎯 Breakout Analysis</h2>
                <table class="stats-table">
                    <tr><th>Metric</th><th>Value</th></tr>
                    <tr><td>Overall Breakout Rate</td><td>{stats.get('breakout_rate', 0):.1%}</td></tr>
                    <tr><td>Long Breakout Ratio</td><td>{stats.get('long_ratio', 0):.1%}</td></tr>
                    <tr><td>Short Breakout Ratio</td><td>{stats.get('short_ratio', 0):.1%}</td></tr>
                </table>
            </div>
            
            <div class="chart">
                <h2>📊 Analysis Charts</h2>
                <img src="../charts/range_analysis.png" alt="Range Analysis Charts" style="max-width: 100%;">
            </div>
            
            <div class="section">
                <h2>🧪 Filter Test Results</h2>
                {self._generate_filter_results_table(filter_results)}
            </div>
        </body>
        </html>
        """
        
        return html
    
    def _generate_filter_results_table(self, filter_results: pd.DataFrame) -> str:
        """生成過濾測試結果表格"""
        if filter_results.empty:
            return "<p>No filter test results available.</p>"
        
        table_html = '<table class="stats-table"><tr><th>Test Name</th><th>Total PnL</th><th>Win Rate</th><th>Total Trades</th><th>Long/Short Ratio</th></tr>'
        
        for _, row in filter_results.iterrows():
            if 'error' in row:
                continue
            
            long_short_ratio = f"{row.get('long_trades', 0)}/{row.get('short_trades', 0)}"
            table_html += f"""
            <tr>
                <td>{row.get('test_name', 'N/A')}</td>
                <td>{row.get('total_pnl', 0):.1f}</td>
                <td>{row.get('win_rate', 0):.1%}</td>
                <td>{row.get('total_trades', 0)}</td>
                <td>{long_short_ratio}</td>
            </tr>
            """
        
        table_html += '</table>'
        return table_html


def main():
    """主函數 - 執行區間分析實驗"""
    analyzer = RangeAnalyzer()
    
    # 收集區間統計數據
    range_df = analyzer.collect_range_statistics()
    
    if range_df.empty:
        logger.error("❌ 無法收集區間數據，實驗終止")
        return
    
    # 分析區間大小分布
    stats = analyzer.analyze_range_size_distribution(range_df)
    logger.info(f"📊 區間統計: 平均 {stats['mean_range']:.1f} 點，中位數 {stats['median_range']:.1f} 點")
    
    # 測試不同過濾閾值
    thresholds = [70, 100, 130, 160]
    filter_results = analyzer.test_range_filters(thresholds)
    
    # 生成報告
    report_file = analyzer.create_range_analysis_report(range_df, filter_results)
    logger.info(f"✅ 實驗完成，報告已生成: {report_file}")


if __name__ == "__main__":
    main()
