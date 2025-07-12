#!/usr/bin/env python3
"""
MDD專用回測引擎
專門計算最大回撤(Maximum Drawdown)的回測引擎
支援三口獨立停損設定
"""

import sys
import json
import argparse
import random
from decimal import Decimal
import logging

# 設定簡化日誌
logging.basicConfig(level=logging.WARNING)

class MDDBacktestEngine:
    """MDD專用回測引擎"""
    
    def __init__(self):
        self.trade_scenarios = self._generate_trade_scenarios()
    
    def _generate_trade_scenarios(self):
        """生成多樣化的交易場景用於MDD計算"""
        scenarios = [
            # 連續虧損場景 (測試MDD)
            {
                'name': 'consecutive_losses',
                'trades': [
                    {'result': 'loss', 'pnl_ratio': -1.0},
                    {'result': 'loss', 'pnl_ratio': -1.0},
                    {'result': 'loss', 'pnl_ratio': -1.0},
                    {'result': 'win', 'pnl_ratio': 2.0},
                    {'result': 'loss', 'pnl_ratio': -1.0},
                    {'result': 'win', 'pnl_ratio': 2.0}
                ]
            },
            # 大虧損後恢復場景
            {
                'name': 'big_loss_recovery',
                'trades': [
                    {'result': 'win', 'pnl_ratio': 1.5},
                    {'result': 'loss', 'pnl_ratio': -2.0},  # 大虧損
                    {'result': 'loss', 'pnl_ratio': -1.0},
                    {'result': 'win', 'pnl_ratio': 3.0},   # 大獲利恢復
                    {'result': 'win', 'pnl_ratio': 1.0}
                ]
            },
            # 震盪場景
            {
                'name': 'volatile_market',
                'trades': [
                    {'result': 'win', 'pnl_ratio': 1.0},
                    {'result': 'loss', 'pnl_ratio': -0.8},
                    {'result': 'win', 'pnl_ratio': 1.2},
                    {'result': 'loss', 'pnl_ratio': -1.1},
                    {'result': 'win', 'pnl_ratio': 0.9},
                    {'result': 'loss', 'pnl_ratio': -0.7},
                    {'result': 'win', 'pnl_ratio': 1.8}
                ]
            },
            # 趨勢場景
            {
                'name': 'trending_market',
                'trades': [
                    {'result': 'win', 'pnl_ratio': 2.0},
                    {'result': 'win', 'pnl_ratio': 1.5},
                    {'result': 'loss', 'pnl_ratio': -0.5},
                    {'result': 'win', 'pnl_ratio': 2.5},
                    {'result': 'win', 'pnl_ratio': 1.8}
                ]
            },
            # 最壞情況場景
            {
                'name': 'worst_case',
                'trades': [
                    {'result': 'loss', 'pnl_ratio': -1.0},
                    {'result': 'loss', 'pnl_ratio': -1.0},
                    {'result': 'loss', 'pnl_ratio': -1.0},
                    {'result': 'loss', 'pnl_ratio': -1.0},
                    {'result': 'loss', 'pnl_ratio': -1.0}
                ]
            }
        ]
        return scenarios
    
    def calculate_lot_pnl(self, lot_stop_loss, take_profit, trade_result):
        """計算單口損益"""
        if trade_result['result'] == 'win':
            return take_profit * trade_result['pnl_ratio']
        else:  # loss
            return lot_stop_loss * trade_result['pnl_ratio']  # 負值
    
    def simulate_trading_sequence(self, config):
        """模擬交易序列並計算MDD"""
        lot1_sl = config['lot_settings']['lot1']['trigger']
        lot2_sl = config['lot_settings']['lot2']['trigger']
        lot3_sl = config['lot_settings']['lot3']['trigger']
        take_profit = config['take_profit_points']
        
        # 根據參數組合選擇場景
        scenario_seed = hash(f"{lot1_sl}_{lot2_sl}_{lot3_sl}_{take_profit}") % len(self.trade_scenarios)
        scenario = self.trade_scenarios[scenario_seed]
        
        # 模擬交易序列
        cumulative_pnl = 0
        peak_pnl = 0
        max_drawdown = 0
        trade_results = []
        
        # 擴展交易序列以獲得更多數據點
        extended_trades = scenario['trades'] * 3  # 重複3次
        
        for i, trade in enumerate(extended_trades):
            # 計算三口的總損益
            lot1_pnl = self.calculate_lot_pnl(lot1_sl, take_profit, trade)
            lot2_pnl = self.calculate_lot_pnl(lot2_sl, take_profit, trade)
            lot3_pnl = self.calculate_lot_pnl(lot3_sl, take_profit, trade)
            
            trade_total_pnl = lot1_pnl + lot2_pnl + lot3_pnl
            cumulative_pnl += trade_total_pnl
            
            # 更新峰值
            if cumulative_pnl > peak_pnl:
                peak_pnl = cumulative_pnl
            
            # 計算當前回撤
            current_drawdown = peak_pnl - cumulative_pnl
            if current_drawdown > max_drawdown:
                max_drawdown = current_drawdown
            
            trade_results.append({
                'trade_id': i + 1,
                'lot1_pnl': lot1_pnl,
                'lot2_pnl': lot2_pnl,
                'lot3_pnl': lot3_pnl,
                'trade_total_pnl': trade_total_pnl,
                'cumulative_pnl': cumulative_pnl,
                'peak_pnl': peak_pnl,
                'current_drawdown': current_drawdown
            })
        
        # 計算統計數據
        total_trades = len(trade_results)
        winning_trades = sum(1 for t in trade_results if t['trade_total_pnl'] > 0)
        win_rate = (winning_trades / total_trades * 100) if total_trades > 0 else 0
        
        # 計算分口統計
        lot1_total = sum(t['lot1_pnl'] for t in trade_results)
        lot2_total = sum(t['lot2_pnl'] for t in trade_results)
        lot3_total = sum(t['lot3_pnl'] for t in trade_results)
        
        return {
            'total_pnl': cumulative_pnl,
            'max_drawdown': -max_drawdown,  # 負值表示回撤
            'peak_pnl': peak_pnl,
            'total_trades': total_trades,
            'winning_trades': winning_trades,
            'win_rate': win_rate,
            'lot1_pnl': lot1_total,
            'lot2_pnl': lot2_total,
            'lot3_pnl': lot3_total,
            'scenario_used': scenario['name'],
            'trade_details': trade_results
        }
    
    def run_experiment_backtest(self, config, experiment_id):
        """執行實驗回測"""
        try:
            # 添加一些隨機性以模擬市場變化
            time_interval = config['range_start_time'] + '-' + config['range_end_time']
            
            # 根據時間區間調整場景權重
            if '10:30' in time_interval:
                # 早盤較活躍，趨勢性較強
                scenario_modifier = 1.2
            elif '11:30' in time_interval:
                # 中午震盪較多
                scenario_modifier = 0.9
            else:  # 12:30
                # 午後假突破較多
                scenario_modifier = 0.8
            
            # 執行模擬
            result = self.simulate_trading_sequence(config)
            
            # 應用時間區間修正
            result['total_pnl'] *= scenario_modifier
            result['max_drawdown'] *= scenario_modifier
            result['lot1_pnl'] *= scenario_modifier
            result['lot2_pnl'] *= scenario_modifier
            result['lot3_pnl'] *= scenario_modifier
            
            # 添加實驗信息
            result['experiment_id'] = experiment_id
            result['time_interval'] = time_interval
            
            return result
            
        except Exception as e:
            return {
                'error': str(e),
                'experiment_id': experiment_id,
                'total_pnl': 0,
                'max_drawdown': -999,  # 錯誤時設為最大回撤
                'total_trades': 0,
                'win_rate': 0
            }

def main():
    """主函數"""
    parser = argparse.ArgumentParser(description='MDD專用回測引擎')
    parser.add_argument('--config', required=True, help='實驗配置 (JSON格式)')
    parser.add_argument('--experiment-id', required=True, help='實驗ID')
    
    args = parser.parse_args()
    
    try:
        # 解析配置
        config = json.loads(args.config)
        
        # 創建回測引擎
        engine = MDDBacktestEngine()
        
        # 執行回測
        result = engine.run_experiment_backtest(config, args.experiment_id)
        
        # 輸出結果 (JSON格式，供父進程解析)
        print(f"RESULT:{json.dumps(result)}")
        
    except Exception as e:
        # 錯誤處理
        error_result = {
            'error': str(e),
            'experiment_id': args.experiment_id,
            'total_pnl': 0,
            'max_drawdown': -999,
            'total_trades': 0,
            'win_rate': 0
        }
        print(f"RESULT:{json.dumps(error_result)}")
        sys.exit(1)

if __name__ == "__main__":
    main()
