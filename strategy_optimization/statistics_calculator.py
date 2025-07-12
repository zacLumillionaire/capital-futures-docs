# statistics_calculator.py - 統計計算器
"""
計算各種交易統計指標和績效分析
包含基本指標、風險指標、口數分析等
"""

import logging
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import Dict, List, Tuple, Optional, Any
import json

from config import ANALYSIS_CONFIG, METRICS_CONFIG, OUTPUT_FILES, PROCESSED_DIR
from utils import (
    calculate_drawdown, calculate_max_drawdown, calculate_sharpe_ratio,
    calculate_sortino_ratio, calculate_profit_factor, safe_divide
)

logger = logging.getLogger(__name__)

class StrategyStatistics:
    """策略統計分析器"""
    
    def __init__(self, daily_df: pd.DataFrame, events_df: pd.DataFrame):
        self.daily_df = daily_df.copy()
        self.events_df = events_df.copy()
        self.statistics = {}
        
        # 確保日期格式正確
        if not self.daily_df.empty:
            self.daily_df['trade_date'] = pd.to_datetime(self.daily_df['trade_date'])
            self.daily_df = self.daily_df.sort_values('trade_date')
        
        if not self.events_df.empty:
            self.events_df['trade_date'] = pd.to_datetime(self.events_df['trade_date'])
            self.events_df['timestamp'] = pd.to_datetime(self.events_df['timestamp'])
    
    def calculate_all_statistics(self) -> Dict[str, Any]:
        """計算所有統計指標"""
        logger.info("開始計算統計指標...")
        
        # 基本績效指標
        self.statistics['basic_metrics'] = self._calculate_basic_metrics()
        
        # 風險指標
        self.statistics['risk_metrics'] = self._calculate_risk_metrics()
        
        # 交易分析
        self.statistics['trade_analysis'] = self._calculate_trade_analysis()
        
        # 口數分析
        self.statistics['lot_analysis'] = self._calculate_lot_analysis()
        
        # 時間分析
        self.statistics['time_analysis'] = self._calculate_time_analysis()
        
        # 月度分析
        self.statistics['monthly_analysis'] = self._calculate_monthly_analysis()
        
        logger.info("統計指標計算完成")
        return self.statistics
    
    def _calculate_basic_metrics(self) -> Dict[str, Any]:
        """計算基本績效指標"""
        if self.daily_df.empty:
            return {}
        
        # 基本數據
        total_trades = len(self.daily_df[self.daily_df['direction'].notna()])
        winning_trades = len(self.daily_df[self.daily_df['total_pnl'] > 0])
        losing_trades = len(self.daily_df[self.daily_df['total_pnl'] < 0])
        
        # 損益統計
        total_pnl = self.daily_df['total_pnl'].sum()
        avg_pnl = self.daily_df['total_pnl'].mean()
        
        wins = self.daily_df[self.daily_df['total_pnl'] > 0]['total_pnl']
        losses = self.daily_df[self.daily_df['total_pnl'] < 0]['total_pnl']
        
        avg_win = wins.mean() if len(wins) > 0 else 0
        avg_loss = losses.mean() if len(losses) > 0 else 0
        max_win = wins.max() if len(wins) > 0 else 0
        max_loss = losses.min() if len(losses) > 0 else 0
        
        # 勝率和獲利因子
        win_rate = safe_divide(winning_trades, total_trades) * 100
        profit_factor = calculate_profit_factor(wins, losses)
        
        # 期望值
        expectancy = safe_divide(total_pnl, total_trades)
        
        return {
            'total_trades': total_trades,
            'winning_trades': winning_trades,
            'losing_trades': losing_trades,
            'win_rate': win_rate,
            'total_pnl': total_pnl,
            'avg_pnl': avg_pnl,
            'avg_win': avg_win,
            'avg_loss': avg_loss,
            'max_win': max_win,
            'max_loss': max_loss,
            'profit_factor': profit_factor,
            'expectancy': expectancy,
            'total_trading_days': len(self.daily_df)
        }
    
    def _calculate_risk_metrics(self) -> Dict[str, Any]:
        """計算風險指標"""
        if self.daily_df.empty:
            return {}
        
        # 建立權益曲線
        equity_curve = self.daily_df['total_pnl'].cumsum()
        returns = self.daily_df['total_pnl'] / ANALYSIS_CONFIG['initial_capital']
        
        # 回撤分析
        drawdown = calculate_drawdown(equity_curve)
        max_dd, peak_idx, trough_idx = calculate_max_drawdown(equity_curve)
        
        # 風險調整報酬
        sharpe_ratio = calculate_sharpe_ratio(returns, ANALYSIS_CONFIG['risk_free_rate'])
        sortino_ratio = calculate_sortino_ratio(returns, ANALYSIS_CONFIG['risk_free_rate'])
        
        # 波動率
        volatility = returns.std() * np.sqrt(ANALYSIS_CONFIG['trading_days_per_year'])
        
        # 連續虧損分析
        consecutive_losses = self._calculate_consecutive_losses()
        
        return {
            'max_drawdown': max_dd,
            'max_drawdown_duration': trough_idx - peak_idx if peak_idx != trough_idx else 0,
            'sharpe_ratio': sharpe_ratio,
            'sortino_ratio': sortino_ratio,
            'volatility': volatility,
            'max_consecutive_losses': consecutive_losses['max_count'],
            'max_consecutive_loss_amount': consecutive_losses['max_amount'],
            'current_drawdown': drawdown.iloc[-1] if len(drawdown) > 0 else 0
        }
    
    def _calculate_trade_analysis(self) -> Dict[str, Any]:
        """計算交易分析"""
        if self.daily_df.empty:
            return {}
        
        # 方向分析
        long_trades = self.daily_df[self.daily_df['direction'] == 'LONG']
        short_trades = self.daily_df[self.daily_df['direction'] == 'SHORT']
        
        long_pnl = long_trades['total_pnl'].sum() if len(long_trades) > 0 else 0
        short_pnl = short_trades['total_pnl'].sum() if len(short_trades) > 0 else 0
        
        long_win_rate = safe_divide(len(long_trades[long_trades['total_pnl'] > 0]), len(long_trades)) * 100
        short_win_rate = safe_divide(len(short_trades[short_trades['total_pnl'] > 0]), len(short_trades)) * 100
        
        # 持倉時間分析（基於事件）
        holding_times = self._calculate_holding_times()
        
        return {
            'long_trades_count': len(long_trades),
            'short_trades_count': len(short_trades),
            'long_total_pnl': long_pnl,
            'short_total_pnl': short_pnl,
            'long_win_rate': long_win_rate,
            'short_win_rate': short_win_rate,
            'avg_holding_time_minutes': holding_times['avg_minutes'],
            'max_holding_time_minutes': holding_times['max_minutes'],
            'min_holding_time_minutes': holding_times['min_minutes']
        }
    
    def _calculate_lot_analysis(self) -> Dict[str, Any]:
        """計算口數分析"""
        if self.events_df.empty:
            return {}
        
        # 各口單表現分析
        lot_performance = {}
        
        for lot_num in range(1, 4):  # 假設最多3口
            lot_events = self.events_df[
                (self.events_df['lot_number'] == lot_num) & 
                (self.events_df['pnl'].notna())
            ]
            
            if len(lot_events) > 0:
                lot_performance[f'lot_{lot_num}'] = {
                    'total_pnl': lot_events['pnl'].sum(),
                    'avg_pnl': lot_events['pnl'].mean(),
                    'win_rate': safe_divide(len(lot_events[lot_events['pnl'] > 0]), len(lot_events)) * 100,
                    'trade_count': len(lot_events)
                }
        
        # 移動停利效果分析
        trailing_exits = self.events_df[self.events_df['event_type'] == 'trailing_exit']
        initial_stops = self.events_df[self.events_df['event_type'] == 'initial_stop']
        protective_stops = self.events_df[self.events_df['event_type'] == 'protective_stop']
        
        return {
            'lot_performance': lot_performance,
            'trailing_stop_count': len(trailing_exits),
            'trailing_stop_pnl': trailing_exits['pnl'].sum() if len(trailing_exits) > 0 else 0,
            'initial_stop_count': len(initial_stops),
            'initial_stop_pnl': initial_stops['pnl'].sum() if len(initial_stops) > 0 else 0,
            'protective_stop_count': len(protective_stops),
            'protective_stop_pnl': protective_stops['pnl'].sum() if len(protective_stops) > 0 else 0
        }
    
    def _calculate_time_analysis(self) -> Dict[str, Any]:
        """計算時間分析"""
        if self.daily_df.empty:
            return {}
        
        # 週間分析
        self.daily_df['weekday'] = self.daily_df['trade_date'].dt.day_name()
        weekday_performance = self.daily_df.groupby('weekday')['total_pnl'].agg(['sum', 'mean', 'count']).to_dict()
        
        # 月份分析
        self.daily_df['month'] = self.daily_df['trade_date'].dt.month
        monthly_performance = self.daily_df.groupby('month')['total_pnl'].agg(['sum', 'mean', 'count']).to_dict()
        
        return {
            'weekday_performance': weekday_performance,
            'monthly_performance': monthly_performance
        }
    
    def _calculate_monthly_analysis(self) -> Dict[str, Any]:
        """計算月度分析"""
        if self.daily_df.empty:
            return {}
        
        # 按月統計
        self.daily_df['year_month'] = self.daily_df['trade_date'].dt.to_period('M')
        monthly_stats = self.daily_df.groupby('year_month').agg({
            'total_pnl': ['sum', 'mean', 'count'],
            'direction': lambda x: (x == 'LONG').sum()  # LONG交易次數
        }).round(2)
        
        # 計算月度勝率
        monthly_wins = self.daily_df[self.daily_df['total_pnl'] > 0].groupby('year_month').size()
        monthly_total = self.daily_df.groupby('year_month').size()
        monthly_win_rate = (monthly_wins / monthly_total * 100).fillna(0)
        
        return {
            'monthly_stats': monthly_stats.to_dict(),
            'monthly_win_rate': monthly_win_rate.to_dict()
        }
    
    def _calculate_consecutive_losses(self) -> Dict[str, Any]:
        """計算連續虧損"""
        if self.daily_df.empty:
            return {'max_count': 0, 'max_amount': 0}
        
        losses = self.daily_df['total_pnl'] < 0
        consecutive_count = 0
        max_consecutive_count = 0
        consecutive_amount = 0
        max_consecutive_amount = 0
        
        for i, is_loss in enumerate(losses):
            if is_loss:
                consecutive_count += 1
                consecutive_amount += self.daily_df.iloc[i]['total_pnl']
            else:
                max_consecutive_count = max(max_consecutive_count, consecutive_count)
                max_consecutive_amount = min(max_consecutive_amount, consecutive_amount)
                consecutive_count = 0
                consecutive_amount = 0
        
        # 檢查最後一段
        max_consecutive_count = max(max_consecutive_count, consecutive_count)
        max_consecutive_amount = min(max_consecutive_amount, consecutive_amount)
        
        return {
            'max_count': max_consecutive_count,
            'max_amount': max_consecutive_amount
        }
    
    def _calculate_holding_times(self) -> Dict[str, Any]:
        """計算持倉時間"""
        if self.events_df.empty:
            return {'avg_minutes': 0, 'max_minutes': 0, 'min_minutes': 0}
        
        holding_times = []
        
        # 按交易日分組計算持倉時間
        for trade_date in self.events_df['trade_date'].unique():
            day_events = self.events_df[self.events_df['trade_date'] == trade_date].sort_values('timestamp')
            
            entry_events = day_events[day_events['event_type'] == 'entry']
            exit_events = day_events[day_events['event_type'].isin(['trailing_exit', 'initial_stop', 'protective_stop', 'eod_close'])]
            
            if len(entry_events) > 0 and len(exit_events) > 0:
                entry_time = entry_events.iloc[0]['timestamp']
                last_exit_time = exit_events.iloc[-1]['timestamp']
                
                holding_duration = (last_exit_time - entry_time).total_seconds() / 60  # 轉換為分鐘
                holding_times.append(holding_duration)
        
        if holding_times:
            return {
                'avg_minutes': np.mean(holding_times),
                'max_minutes': np.max(holding_times),
                'min_minutes': np.min(holding_times)
            }
        else:
            return {'avg_minutes': 0, 'max_minutes': 0, 'min_minutes': 0}
    
    def save_statistics(self) -> None:
        """儲存統計結果"""
        output_file = PROCESSED_DIR / OUTPUT_FILES['statistics']
        
        # 轉換numpy類型為Python原生類型以便JSON序列化
        def convert_numpy_types(obj):
            if isinstance(obj, np.integer):
                return int(obj)
            elif isinstance(obj, np.floating):
                return float(obj)
            elif isinstance(obj, np.ndarray):
                return obj.tolist()
            elif isinstance(obj, dict):
                return {str(key): convert_numpy_types(value) for key, value in obj.items()}
            elif isinstance(obj, list):
                return [convert_numpy_types(item) for item in obj]
            elif isinstance(obj, tuple):
                return list(obj)
            elif hasattr(obj, 'to_dict'):
                return convert_numpy_types(obj.to_dict())
            else:
                return obj
        
        converted_stats = convert_numpy_types(self.statistics)
        
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(converted_stats, f, ensure_ascii=False, indent=2, default=str)
        
        logger.info(f"統計結果已儲存到: {output_file}")
    
    def print_summary(self) -> None:
        """列印統計摘要"""
        if not self.statistics:
            print("尚未計算統計指標")
            return
        
        basic = self.statistics.get('basic_metrics', {})
        risk = self.statistics.get('risk_metrics', {})
        
        print("\n" + "="*50)
        print("策略績效統計摘要")
        print("="*50)
        
        print(f"總交易次數: {basic.get('total_trades', 0)}")
        print(f"獲利次數: {basic.get('winning_trades', 0)}")
        print(f"虧損次數: {basic.get('losing_trades', 0)}")
        print(f"勝率: {basic.get('win_rate', 0):.2f}%")
        print(f"總損益: {basic.get('total_pnl', 0):.2f}")
        print(f"平均損益: {basic.get('avg_pnl', 0):.2f}")
        print(f"獲利因子: {basic.get('profit_factor', 0):.2f}")
        print(f"最大回撤: {risk.get('max_drawdown', 0):.2%}")
        print(f"夏普比率: {risk.get('sharpe_ratio', 0):.2f}")
        print("="*50)

def calculate_strategy_statistics(daily_df: pd.DataFrame, events_df: pd.DataFrame) -> Dict[str, Any]:
    """計算策略統計指標的主函數"""
    calculator = StrategyStatistics(daily_df, events_df)
    statistics = calculator.calculate_all_statistics()
    calculator.save_statistics()
    calculator.print_summary()
    return statistics

if __name__ == "__main__":
    from config import PROCESSED_DIR, OUTPUT_FILES
    
    # 載入資料
    daily_file = PROCESSED_DIR / OUTPUT_FILES['daily_pnl']
    events_file = PROCESSED_DIR / 'trade_events.csv'
    
    if daily_file.exists() and events_file.exists():
        daily_df = pd.read_csv(daily_file, index_col=0)
        events_df = pd.read_csv(events_file, index_col=0)
        
        # 計算統計
        stats = calculate_strategy_statistics(daily_df, events_df)
    else:
        print("找不到處理後的資料檔案，請先執行 data_extractor.py")
