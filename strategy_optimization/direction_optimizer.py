# direction_optimizer.py - 方向性偏差分析工具
"""
深度分析做多做空的績效差異
研究方向性偏差的根本原因和優化策略
"""

import logging
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from decimal import Decimal
from datetime import time, date, datetime
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
import shared

# 設定日誌
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class DirectionOptimizer:
    """方向性偏差分析器"""
    
    def __init__(self):
        self.results_cache = {}
        
    def create_directional_config(self, direction: str = "BOTH", lot_count: int = 3) -> StrategyConfig:
        """創建方向性測試配置"""
        base_lot_rules = [
            LotRule(use_trailing_stop=True, trailing_activation=Decimal(15), trailing_pullback=Decimal('0.20')),
            LotRule(use_trailing_stop=True, trailing_activation=Decimal(40), trailing_pullback=Decimal('0.20'), protective_stop_multiplier=Decimal('2.0')),
            LotRule(use_trailing_stop=True, trailing_activation=Decimal(65), trailing_pullback=Decimal('0.20'), protective_stop_multiplier=Decimal('2.0'))
        ]
        
        config = StrategyConfig(
            trade_size_in_lots=lot_count,
            stop_loss_type=StopLossType.RANGE_BOUNDARY,
            lot_rules=base_lot_rules[:lot_count]
        )
        
        # 添加方向限制標記（需要修改主策略支援）
        config.direction_filter = direction
        return config
    
    def run_directional_comparison(self, start_date: str = None, end_date: str = None) -> Dict:
        """執行方向性比較實驗"""
        logger.info("🧪 開始方向性比較實驗...")
        
        results = {}
        
        # 測試配置
        test_configs = [
            ("BOTH", "雙向交易"),
            ("LONG_ONLY", "純做多"),
            ("SHORT_ONLY", "純做空")
        ]
        
        for direction, description in test_configs:
            logger.info(f"測試 {description} 策略...")
            
            # 由於原策略不支援方向過濾，我們需要手動實現
            if direction == "BOTH":
                result = self._run_standard_backtest(start_date, end_date)
            else:
                result = self._run_directional_backtest(direction, start_date, end_date)
            
            results[direction] = {
                'description': description,
                'stats': result
            }
        
        return results
    
    def _run_standard_backtest(self, start_date: str = None, end_date: str = None) -> Dict:
        """執行標準雙向回測"""
        config = self.create_directional_config("BOTH")
        return self._execute_backtest_with_logging(config, start_date, end_date)
    
    def _run_directional_backtest(self, direction: str, start_date: str = None, end_date: str = None) -> Dict:
        """執行單方向回測（手動實現方向過濾）"""
        logger.info(f"執行 {direction} 方向回測...")
        
        try:
            with shared.get_conn_cur_from_pool_b(as_dict=True) as (conn, cur):
                # 獲取交易日
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
                
                total_pnl = 0
                winning_trades = 0
                losing_trades = 0
                long_trades = 0
                short_trades = 0
                long_pnl = 0
                short_pnl = 0
                
                for day in trade_days:
                    day_result = self._simulate_single_day_directional(cur, day, direction)
                    
                    if day_result['traded']:
                        total_pnl += day_result['pnl']
                        if day_result['pnl'] > 0:
                            winning_trades += 1
                        else:
                            losing_trades += 1
                        
                        if day_result['direction'] == 'LONG':
                            long_trades += 1
                            long_pnl += day_result['pnl']
                        else:
                            short_trades += 1
                            short_pnl += day_result['pnl']
                
                return {
                    'total_pnl': total_pnl,
                    'winning_trades': winning_trades,
                    'losing_trades': losing_trades,
                    'total_trades': winning_trades + losing_trades,
                    'win_rate': winning_trades / max(winning_trades + losing_trades, 1),
                    'long_trades': long_trades,
                    'short_trades': short_trades,
                    'long_pnl': long_pnl,
                    'short_pnl': short_pnl
                }
                
        except Exception as e:
            logger.error(f"方向性回測失敗: {e}")
            return {}
    
    def _simulate_single_day_directional(self, cur, day: date, direction_filter: str) -> Dict:
        """模擬單日方向性交易"""
        cur.execute("SELECT * FROM stock_prices WHERE trade_datetime::date = %s ORDER BY trade_datetime;", (day,))
        day_candles = [c for c in cur.fetchall() if time(8, 45) <= c['trade_datetime'].time() <= time(13, 45)]
        
        if len(day_candles) < 3:
            return {'traded': False, 'pnl': 0, 'direction': None}
        
        # 計算開盤區間
        candles_846_847 = [c for c in day_candles if c['trade_datetime'].time() in [time(8, 46), time(8, 47)]]
        if len(candles_846_847) != 2:
            return {'traded': False, 'pnl': 0, 'direction': None}
        
        range_high = max(c['high_price'] for c in candles_846_847)
        range_low = min(c['low_price'] for c in candles_846_847)
        
        # 尋找突破
        trade_candles = [c for c in day_candles if c['trade_datetime'].time() >= time(8, 48)]
        
        for candle in trade_candles:
            # 檢查做多突破
            if candle['close_price'] > range_high and direction_filter in ['BOTH', 'LONG_ONLY']:
                pnl = self._calculate_simple_pnl(trade_candles, candle, 'LONG', range_high, range_low)
                return {'traded': True, 'pnl': pnl, 'direction': 'LONG'}
            
            # 檢查做空突破
            elif candle['close_price'] < range_low and direction_filter in ['BOTH', 'SHORT_ONLY']:
                pnl = self._calculate_simple_pnl(trade_candles, candle, 'SHORT', range_high, range_low)
                return {'traded': True, 'pnl': pnl, 'direction': 'SHORT'}
        
        return {'traded': False, 'pnl': 0, 'direction': None}
    
    def _calculate_simple_pnl(self, trade_candles: List, entry_candle: Dict, position: str, range_high: float, range_low: float) -> float:
        """簡化的損益計算（用於方向性測試）"""
        entry_price = entry_candle['close_price']
        entry_index = trade_candles.index(entry_candle)
        
        # 設定停損
        if position == 'LONG':
            stop_loss = range_low
        else:
            stop_loss = range_high
        
        # 檢查後續K棒的停損和收盤
        for candle in trade_candles[entry_index + 1:]:
            # 檢查停損
            if position == 'LONG' and candle['low_price'] <= stop_loss:
                return float(stop_loss - entry_price)
            elif position == 'SHORT' and candle['high_price'] >= stop_loss:
                return float(entry_price - stop_loss)
        
        # 收盤平倉
        exit_price = trade_candles[-1]['close_price']
        if position == 'LONG':
            return float(exit_price - entry_price)
        else:
            return float(entry_price - exit_price)
    
    def _execute_backtest_with_logging(self, config: StrategyConfig, start_date: str = None, end_date: str = None) -> Dict:
        """執行回測並捕獲日誌"""
        import io
        import sys
        from contextlib import redirect_stdout, redirect_stderr
        
        log_capture = io.StringIO()
        
        try:
            with redirect_stdout(log_capture), redirect_stderr(log_capture):
                run_backtest(config, start_date, end_date)
            
            log_content = log_capture.getvalue()
            return self._parse_backtest_log(log_content)
            
        except Exception as e:
            logger.error(f"回測執行失敗: {e}")
            return {}
    
    def _parse_backtest_log(self, log_content: str) -> Dict:
        """解析回測日誌"""
        lines = log_content.split('\n')
        
        stats = {
            'total_pnl': 0,
            'winning_trades': 0,
            'losing_trades': 0,
            'long_trades': 0,
            'short_trades': 0,
            'long_pnl': 0,
            'short_pnl': 0
        }
        
        current_day_pnl = 0
        current_direction = None
        
        for line in lines:
            if '📈 LONG' in line:
                current_direction = 'LONG'
                stats['long_trades'] += 1
            elif '📉 SHORT' in line:
                current_direction = 'SHORT'
                stats['short_trades'] += 1
            elif '當日損益:' in line:
                try:
                    pnl_str = line.split('當日損益:')[1].strip()
                    current_day_pnl = float(pnl_str)
                    stats['total_pnl'] += current_day_pnl
                    
                    if current_day_pnl > 0:
                        stats['winning_trades'] += 1
                    elif current_day_pnl < 0:
                        stats['losing_trades'] += 1
                    
                    if current_direction == 'LONG':
                        stats['long_pnl'] += current_day_pnl
                    elif current_direction == 'SHORT':
                        stats['short_pnl'] += current_day_pnl
                        
                except:
                    pass
        
        stats['total_trades'] = stats['winning_trades'] + stats['losing_trades']
        stats['win_rate'] = stats['winning_trades'] / max(stats['total_trades'], 1)
        
        return stats
    
    def analyze_time_based_bias(self, start_date: str = None, end_date: str = None) -> Dict:
        """分析時間因子對方向偏差的影響"""
        logger.info("📅 分析時間因子對方向偏差的影響...")
        
        results = {
            'monthly': {},
            'weekly': {},
            'quarterly': {}
        }
        
        # 按月份分析
        for month in range(1, 13):
            month_start = f"2023-{month:02d}-01"
            if month == 12:
                month_end = "2023-12-31"
            else:
                month_end = f"2023-{month+1:02d}-01"
            
            month_result = self.run_directional_comparison(month_start, month_end)
            results['monthly'][month] = month_result
        
        return results
    
    def create_direction_analysis_report(self, comparison_results: Dict, time_analysis: Dict = None) -> str:
        """生成方向性分析報告"""
        logger.info("📋 生成方向性分析報告...")
        
        # 創建視覺化
        self._create_direction_visualizations(comparison_results, time_analysis)
        
        # 生成HTML報告
        html_content = self._generate_direction_html_report(comparison_results, time_analysis)
        
        # 保存報告
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        report_file = f"reports/direction_analysis_report_{timestamp}.html"
        
        with open(report_file, 'w', encoding='utf-8') as f:
            f.write(html_content)
        
        logger.info(f"✅ 方向性分析報告已生成: {report_file}")
        return report_file
    
    def _create_direction_visualizations(self, comparison_results: Dict, time_analysis: Dict = None):
        """創建方向性分析視覺化"""
        plt.style.use('default')
        plt.rcParams['font.sans-serif'] = ['Arial', 'DejaVu Sans']
        
        fig, axes = plt.subplots(2, 2, figsize=(15, 12))
        
        # 1. 總損益比較
        directions = list(comparison_results.keys())
        pnls = [comparison_results[d]['stats'].get('total_pnl', 0) for d in directions]
        
        axes[0, 0].bar(directions, pnls, color=['blue', 'green', 'red'])
        axes[0, 0].set_title('Total PnL by Direction')
        axes[0, 0].set_ylabel('Total PnL')
        axes[0, 0].grid(True, alpha=0.3)
        
        # 2. 勝率比較
        win_rates = [comparison_results[d]['stats'].get('win_rate', 0) for d in directions]
        axes[0, 1].bar(directions, win_rates, color=['blue', 'green', 'red'])
        axes[0, 1].set_title('Win Rate by Direction')
        axes[0, 1].set_ylabel('Win Rate')
        axes[0, 1].set_ylim(0, 1)
        axes[0, 1].grid(True, alpha=0.3)
        
        # 3. 交易次數比較
        trade_counts = [comparison_results[d]['stats'].get('total_trades', 0) for d in directions]
        axes[1, 0].bar(directions, trade_counts, color=['blue', 'green', 'red'])
        axes[1, 0].set_title('Total Trades by Direction')
        axes[1, 0].set_ylabel('Number of Trades')
        axes[1, 0].grid(True, alpha=0.3)
        
        # 4. 平均每筆損益
        avg_pnls = [pnls[i] / max(trade_counts[i], 1) for i in range(len(directions))]
        axes[1, 1].bar(directions, avg_pnls, color=['blue', 'green', 'red'])
        axes[1, 1].set_title('Average PnL per Trade')
        axes[1, 1].set_ylabel('Average PnL')
        axes[1, 1].grid(True, alpha=0.3)
        
        plt.tight_layout()
        plt.savefig('charts/direction_analysis.png', dpi=300, bbox_inches='tight')
        plt.close()
    
    def _generate_direction_html_report(self, comparison_results: Dict, time_analysis: Dict = None) -> str:
        """生成方向性分析HTML報告"""
        html = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <title>Direction Analysis Report</title>
            <style>
                body {{ font-family: Arial, sans-serif; margin: 20px; }}
                .header {{ background-color: #f0f0f0; padding: 20px; border-radius: 5px; }}
                .section {{ margin: 20px 0; }}
                .comparison-table {{ border-collapse: collapse; width: 100%; }}
                .comparison-table th, .comparison-table td {{ border: 1px solid #ddd; padding: 8px; text-align: center; }}
                .comparison-table th {{ background-color: #f2f2f2; }}
                .chart {{ text-align: center; margin: 20px 0; }}
                .highlight {{ background-color: #ffffcc; }}
            </style>
        </head>
        <body>
            <div class="header">
                <h1>📊 Direction Bias Analysis Report</h1>
                <p>Generated on: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
            </div>
            
            <div class="section">
                <h2>📈 Direction Comparison Results</h2>
                {self._generate_comparison_table(comparison_results)}
            </div>
            
            <div class="chart">
                <h2>📊 Analysis Charts</h2>
                <img src="../charts/direction_analysis.png" alt="Direction Analysis Charts" style="max-width: 100%;">
            </div>
            
            <div class="section">
                <h2>🔍 Key Findings</h2>
                {self._generate_key_findings(comparison_results)}
            </div>
        </body>
        </html>
        """
        return html
    
    def _generate_comparison_table(self, comparison_results: Dict) -> str:
        """生成比較表格"""
        table_html = '''
        <table class="comparison-table">
            <tr>
                <th>Strategy</th>
                <th>Total PnL</th>
                <th>Win Rate</th>
                <th>Total Trades</th>
                <th>Avg PnL/Trade</th>
                <th>Long Trades</th>
                <th>Short Trades</th>
                <th>Long PnL</th>
                <th>Short PnL</th>
            </tr>
        '''
        
        for direction, data in comparison_results.items():
            stats = data['stats']
            avg_pnl = stats.get('total_pnl', 0) / max(stats.get('total_trades', 1), 1)
            
            table_html += f'''
            <tr>
                <td>{data['description']}</td>
                <td>{stats.get('total_pnl', 0):.1f}</td>
                <td>{stats.get('win_rate', 0):.1%}</td>
                <td>{stats.get('total_trades', 0)}</td>
                <td>{avg_pnl:.1f}</td>
                <td>{stats.get('long_trades', 0)}</td>
                <td>{stats.get('short_trades', 0)}</td>
                <td>{stats.get('long_pnl', 0):.1f}</td>
                <td>{stats.get('short_pnl', 0):.1f}</td>
            </tr>
            '''
        
        table_html += '</table>'
        return table_html
    
    def _generate_key_findings(self, comparison_results: Dict) -> str:
        """生成關鍵發現"""
        findings = []
        
        # 比較做多做空績效
        both_stats = comparison_results.get('BOTH', {}).get('stats', {})
        long_pnl = both_stats.get('long_pnl', 0)
        short_pnl = both_stats.get('short_pnl', 0)
        
        if abs(short_pnl) > abs(long_pnl) * 1.5:
            findings.append("🔍 <strong>做空明顯優於做多</strong>：做空損益遠大於做多，建議考慮專注做空策略")
        
        # 比較純方向策略
        long_only_pnl = comparison_results.get('LONG_ONLY', {}).get('stats', {}).get('total_pnl', 0)
        short_only_pnl = comparison_results.get('SHORT_ONLY', {}).get('stats', {}).get('total_pnl', 0)
        
        if short_only_pnl > long_only_pnl * 1.2:
            findings.append("📈 <strong>純做空策略表現最佳</strong>：建議考慮只做空的策略配置")
        
        findings_html = '<ul>'
        for finding in findings:
            findings_html += f'<li>{finding}</li>'
        findings_html += '</ul>'
        
        return findings_html


def main():
    """主函數 - 執行方向性分析實驗"""
    optimizer = DirectionOptimizer()
    
    # 執行方向性比較
    comparison_results = optimizer.run_directional_comparison()
    
    # 分析時間因子（可選）
    # time_analysis = optimizer.analyze_time_based_bias()
    
    # 生成報告
    report_file = optimizer.create_direction_analysis_report(comparison_results)
    logger.info(f"✅ 方向性分析完成，報告已生成: {report_file}")


if __name__ == "__main__":
    main()
