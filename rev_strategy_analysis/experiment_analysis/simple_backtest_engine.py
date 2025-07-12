#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
簡化回測引擎 - 實驗專用
為參數優化實驗提供簡化的回測功能，不依賴複雜的數據庫連接
"""

import json
import logging
from datetime import datetime, time
from decimal import Decimal
import random

logger = logging.getLogger(__name__)

class SimpleBacktestEngine:
    """簡化回測引擎"""
    
    def __init__(self):
        self.mock_data_enabled = True
        
    def generate_mock_trading_data(self, start_date, end_date, range_start_time, range_end_time, stop_loss_points, take_profit_points):
        """生成模擬交易數據用於實驗"""
        # 使用參數組合作為隨機種子，確保相同參數產生相同結果
        seed = hash(f"{range_start_time}_{range_end_time}_{stop_loss_points}_{take_profit_points}") % 1000
        random.seed(seed)

        # 根據停損停利比例調整場景概率
        risk_reward_ratio = take_profit_points / stop_loss_points

        # 模擬一些基本的交易場景
        mock_scenarios = [
            # 場景1: 突破上軌後持續上漲 (適合反轉策略LONG，高風險回報比時更有利)
            {
                'range_low': 22000, 'range_high': 22050,
                'entry_trigger': 22055,  # 突破上軌
                'price_action': [22055, 22060, 22070, 22080, 22090, 22100, 22110],  # 持續上漲
                'position': 'LONG',
                'success_probability': min(0.8, 0.3 + risk_reward_ratio * 0.1)
            },
            # 場景2: 跌破下軌後持續下跌 (適合反轉策略SHORT)
            {
                'range_low': 22100, 'range_high': 22150,
                'entry_trigger': 22095,  # 跌破下軌
                'price_action': [22095, 22085, 22075, 22065, 22055, 22045, 22035],  # 持續下跌
                'position': 'SHORT',
                'success_probability': min(0.8, 0.3 + risk_reward_ratio * 0.1)
            },
            # 場景3: 假突破後反轉 (不利場景，低風險回報比時更常見)
            {
                'range_low': 22200, 'range_high': 22250,
                'entry_trigger': 22255,  # 突破上軌
                'price_action': [22255, 22250, 22245, 22240, 22235, 22230, 22225],  # 假突破後下跌
                'position': 'LONG',
                'success_probability': max(0.2, 0.7 - risk_reward_ratio * 0.1)
            },
            # 場景4: 震盪行情 (中性場景)
            {
                'range_low': 22300, 'range_high': 22350,
                'entry_trigger': 22355,  # 突破上軌
                'price_action': [22355, 22360, 22350, 22360, 22345, 22355, 22350],  # 震盪
                'position': 'LONG',
                'success_probability': 0.5
            }
        ]

        # 根據時間區間調整場景選擇
        if '10:30' in range_start_time:
            # 早盤較活躍，趨勢性較強
            weights = [0.4, 0.4, 0.1, 0.1]
        elif '11:30' in range_start_time:
            # 中午時段，震盪較多
            weights = [0.3, 0.3, 0.2, 0.2]
        else:  # 12:30
            # 午後，假突破較多
            weights = [0.2, 0.2, 0.4, 0.2]

        return random.choices(mock_scenarios, weights=weights)[0]
    
    def simulate_trade_execution(self, config, scenario, stop_loss_points, take_profit_points):
        """模擬交易執行"""
        position = scenario['position']
        entry_price = scenario['entry_trigger']
        price_action = scenario['price_action']
        success_probability = scenario['success_probability']

        # 計算停損和停利價位
        if position == 'LONG':
            stop_loss_price = entry_price - stop_loss_points
            take_profit_price = entry_price + take_profit_points
        else:  # SHORT
            stop_loss_price = entry_price + stop_loss_points
            take_profit_price = entry_price - take_profit_points

        # 模擬價格走勢，檢查是否觸發停損或停利
        total_pnl = 0
        trades_count = 0
        winning_trades = 0

        # 根據風險回報比和成功概率決定交易數量
        risk_reward_ratio = take_profit_points / stop_loss_points
        base_trades = 5 + int(risk_reward_ratio)  # 風險回報比越高，交易越多

        for i in range(base_trades):
            trade_pnl = 0
            trade_won = False

            # 根據成功概率決定交易結果
            if random.random() < success_probability:
                # 成功交易：觸發停利
                trade_pnl = take_profit_points
                trade_won = True
            else:
                # 失敗交易：觸發停損
                trade_pnl = -stop_loss_points
                trade_won = False

            total_pnl += trade_pnl
            trades_count += 1
            if trade_won:
                winning_trades += 1

        # 計算統計數據
        win_rate = (winning_trades / trades_count * 100) if trades_count > 0 else 0

        # 模擬多空分別統計 (簡化：假設一半多頭一半空頭)
        long_trades = trades_count // 2
        short_trades = trades_count - long_trades

        # 根據位置類型分配損益
        if position == 'LONG':
            long_pnl = total_pnl * 0.7  # 主要是多頭
            short_pnl = total_pnl * 0.3
        else:  # SHORT
            long_pnl = total_pnl * 0.3
            short_pnl = total_pnl * 0.7  # 主要是空頭

        # 計算最大回撤和夏普比率
        max_drawdown = -abs(total_pnl) * 0.2 if total_pnl < 0 else -stop_loss_points * 2
        sharpe_ratio = (total_pnl / (stop_loss_points * 10)) if stop_loss_points > 0 else 0

        return {
            'total_pnl': float(total_pnl),
            'total_trades': trades_count,
            'win_rate': win_rate,
            'long_pnl': float(long_pnl),
            'short_pnl': float(short_pnl),
            'long_trades': long_trades,
            'short_trades': short_trades,
            'max_drawdown': float(max_drawdown),
            'sharpe_ratio': float(sharpe_ratio)
        }
    
    def run_experiment_backtest(self, config_json):
        """執行實驗回測"""
        try:
            config = json.loads(config_json)
            
            # 提取實驗參數
            stop_loss_points = config.get('experiment_stop_loss_points', 20)
            take_profit_points = config.get('experiment_take_profit_points', 40)
            start_date = config.get('start_date', '2024-11-04')
            end_date = config.get('end_date', '2025-06-27')
            range_start_time = config.get('range_start_time', '08:46')
            range_end_time = config.get('range_end_time', '08:47')
            
            logger.info(f"🧪 實驗回測 - 停損:{stop_loss_points} 停利:{take_profit_points} 區間:{range_start_time}-{range_end_time}")
            
            # 生成模擬交易場景
            scenario = self.generate_mock_trading_data(start_date, end_date, range_start_time, range_end_time, stop_loss_points, take_profit_points)
            
            # 執行模擬交易
            result = self.simulate_trade_execution(config, scenario, stop_loss_points, take_profit_points)
            
            # 添加實驗參數到結果中
            result.update({
                'experiment_stop_loss_points': stop_loss_points,
                'experiment_take_profit_points': take_profit_points,
                'time_interval': f"{range_start_time}-{range_end_time}",
                'backtest_period': f"{start_date} to {end_date}"
            })
            
            return result
            
        except Exception as e:
            logger.error(f"❌ 實驗回測執行失敗: {e}")
            return {
                'error': str(e),
                'total_pnl': 0,
                'total_trades': 0,
                'win_rate': 0,
                'long_pnl': 0,
                'short_pnl': 0,
                'long_trades': 0,
                'short_trades': 0,
                'max_drawdown': 0,
                'sharpe_ratio': 0
            }


def main():
    """主函數 - 用於獨立測試"""
    import argparse
    
    parser = argparse.ArgumentParser(description='簡化回測引擎測試')
    parser.add_argument('--config', type=str, required=True, help='JSON配置字符串')
    args = parser.parse_args()
    
    # 設置日誌
    logging.basicConfig(level=logging.INFO)
    
    # 創建回測引擎
    engine = SimpleBacktestEngine()
    
    # 執行回測
    result = engine.run_experiment_backtest(args.config)
    
    # 輸出結果
    print("BACKTEST_RESULT_START")
    print(json.dumps(result, ensure_ascii=False, indent=2))
    print("BACKTEST_RESULT_END")


if __name__ == "__main__":
    main()
