#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
參數優化器 - 反轉策略實驗系統
支援大量參數組合的自動化回測實驗

實驗範圍:
- 停損點: 15-100點，步長5點 (18個測試點)
- 停利點: 30-100點，步長10點 (8個測試點)  
- 時間區間: 10:30~10:31, 11:30~11:31, 12:30~12:31 (3個區間)
- 總實驗次數: 18×8×3 = 432次

評估指標: 總損益優先，且以多空都獲利的情況優先
"""

import os
import sys
import json
import subprocess
import pandas as pd
import numpy as np
from datetime import datetime
from concurrent.futures import ProcessPoolExecutor, as_completed
import logging
from pathlib import Path

# 設置日誌
log_dir = Path("results")
log_dir.mkdir(parents=True, exist_ok=True)

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(log_dir / 'parameter_optimization.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class ParameterOptimizer:
    """參數優化器主類"""
    
    def __init__(self, base_config=None):
        """初始化優化器
        
        Args:
            base_config: 基礎配置字典，包含固定的回測參數
        """
        self.base_config = base_config or {
            "trade_lots": 3,  # 固定3口
            "start_date": "2024-11-04",
            "end_date": "2025-06-27",
            "lot_settings": {
                "lot1": {"trigger": 15, "trailing": 20, "protection": 0.5},
                "lot2": {"trigger": 25, "trailing": 30, "protection": 0.6},
                "lot3": {"trigger": 35, "trailing": 40, "protection": 0.7}
            },
            "filters": {
                "range_filter": {"enabled": False, "max_range_points": 50},
                "risk_filter": {"enabled": False, "daily_loss_limit": 150, "profit_target": 200},
                "stop_loss_filter": {"enabled": False, "stop_loss_type": "range_boundary", "fixed_stop_loss_points": 20, "use_range_midpoint": False}
            }
        }
        
        # 實驗參數範圍
        self.stop_loss_range = list(range(15, 101, 5))  # [15, 20, 25, ..., 100]
        self.take_profit_range = list(range(30, 101, 10))  # [30, 40, 50, ..., 100]
        self.time_intervals = [
            ("10:30", "10:31"),
            ("11:30", "11:31"), 
            ("12:30", "12:31")
        ]
        
        # 結果存儲
        self.results = []
        self.results_dir = Path("results")
        self.results_dir.mkdir(parents=True, exist_ok=True)
        
    def generate_experiment_combinations(self):
        """生成所有實驗參數組合"""
        combinations = []
        
        for time_start, time_end in self.time_intervals:
            for stop_loss_points in self.stop_loss_range:
                for take_profit_points in self.take_profit_range:
                    combination = {
                        'time_interval': (time_start, time_end),
                        'stop_loss_points': stop_loss_points,
                        'take_profit_points': take_profit_points,
                        'experiment_id': f"{time_start.replace(':', '')}-{time_end.replace(':', '')}_SL{stop_loss_points}_TP{take_profit_points}"
                    }
                    combinations.append(combination)
        
        logger.info(f"📊 生成 {len(combinations)} 個實驗組合")
        return combinations
    
    def create_experiment_config(self, combination):
        """為單個實驗組合創建配置"""
        config = self.base_config.copy()
        
        # 設置時間區間
        config["range_start_time"] = combination['time_interval'][0]
        config["range_end_time"] = combination['time_interval'][1]
        
        # 設置實驗模式參數
        config["experiment_mode"] = True
        config["experiment_stop_loss_points"] = combination['stop_loss_points']
        config["experiment_take_profit_points"] = combination['take_profit_points']
        
        return config
    
    def run_single_experiment(self, combination):
        """執行單個實驗"""
        try:
            experiment_id = combination['experiment_id']
            logger.info(f"🧪 開始實驗: {experiment_id}")
            
            # 創建實驗配置
            config = self.create_experiment_config(combination)
            config_json = json.dumps(config, ensure_ascii=False)
            
            # 🧪 使用簡化回測引擎進行實驗
            cmd = [
                sys.executable,
                "simple_backtest_engine.py",
                "--config", config_json
            ]
            
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=300,  # 5分鐘超時
                cwd=os.getcwd()
            )
            
            if result.returncode != 0:
                logger.error(f"❌ 實驗 {experiment_id} 執行失敗: {result.stderr}")
                return None
            
            # 解析結果
            output = result.stdout
            if "BACKTEST_RESULT_START" in output and "BACKTEST_RESULT_END" in output:
                start_idx = output.find("BACKTEST_RESULT_START") + len("BACKTEST_RESULT_START")
                end_idx = output.find("BACKTEST_RESULT_END")
                result_json = output[start_idx:end_idx].strip()
                
                try:
                    backtest_result = json.loads(result_json)
                    
                    # 整合實驗結果
                    experiment_result = {
                        'experiment_id': experiment_id,
                        'time_interval': f"{combination['time_interval'][0]}-{combination['time_interval'][1]}",
                        'stop_loss_points': combination['stop_loss_points'],
                        'take_profit_points': combination['take_profit_points'],
                        'total_pnl': backtest_result.get('total_pnl', 0),
                        'total_trades': backtest_result.get('total_trades', 0),
                        'win_rate': backtest_result.get('win_rate', 0),
                        'long_pnl': backtest_result.get('long_pnl', 0),
                        'short_pnl': backtest_result.get('short_pnl', 0),
                        'long_trades': backtest_result.get('long_trades', 0),
                        'short_trades': backtest_result.get('short_trades', 0),
                        'max_drawdown': backtest_result.get('max_drawdown', 0),
                        'sharpe_ratio': backtest_result.get('sharpe_ratio', 0),
                        'both_profitable': (backtest_result.get('long_pnl', 0) > 0 and backtest_result.get('short_pnl', 0) > 0)
                    }
                    
                    logger.info(f"✅ 實驗 {experiment_id} 完成 - 總損益: {experiment_result['total_pnl']:.2f}")
                    return experiment_result
                    
                except json.JSONDecodeError as e:
                    logger.error(f"❌ 實驗 {experiment_id} 結果解析失敗: {e}")
                    return None
            else:
                logger.error(f"❌ 實驗 {experiment_id} 未找到有效結果")
                return None
                
        except subprocess.TimeoutExpired:
            logger.error(f"❌ 實驗 {experiment_id} 執行超時")
            return None
        except Exception as e:
            logger.error(f"❌ 實驗 {experiment_id} 執行異常: {e}")
            return None
    
    def run_batch_experiments(self, max_workers=4):
        """批量執行實驗（支援並行）"""
        combinations = self.generate_experiment_combinations()
        
        logger.info(f"🚀 開始批量實驗，總計 {len(combinations)} 個組合")
        logger.info(f"⚡ 使用 {max_workers} 個並行進程")
        
        completed_count = 0
        
        if max_workers == 1:
            # 單進程執行
            for combination in combinations:
                result = self.run_single_experiment(combination)
                if result:
                    self.results.append(result)
                completed_count += 1
                logger.info(f"📈 進度: {completed_count}/{len(combinations)} ({completed_count/len(combinations)*100:.1f}%)")
        else:
            # 多進程並行執行
            with ProcessPoolExecutor(max_workers=max_workers) as executor:
                future_to_combination = {
                    executor.submit(self.run_single_experiment, combination): combination 
                    for combination in combinations
                }
                
                for future in as_completed(future_to_combination):
                    result = future.result()
                    if result:
                        self.results.append(result)
                    completed_count += 1
                    logger.info(f"📈 進度: {completed_count}/{len(combinations)} ({completed_count/len(combinations)*100:.1f}%)")
        
        logger.info(f"🎉 批量實驗完成！成功執行 {len(self.results)} 個實驗")
        return self.results
    
    def save_results_to_csv(self, filename=None):
        """保存結果到CSV文件"""
        if not self.results:
            logger.warning("⚠️ 沒有實驗結果可保存")
            return None
        
        if filename is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"parameter_optimization_results_{timestamp}.csv"
        
        filepath = self.results_dir / filename
        
        df = pd.DataFrame(self.results)
        df.to_csv(filepath, index=False, encoding='utf-8-sig')
        
        logger.info(f"💾 實驗結果已保存到: {filepath}")
        return filepath
    
    def analyze_results(self):
        """分析實驗結果"""
        if not self.results:
            logger.warning("⚠️ 沒有實驗結果可分析")
            return None
        
        df = pd.DataFrame(self.results)
        
        # 基本統計
        logger.info("📊 實驗結果分析:")
        logger.info(f"總實驗次數: {len(df)}")
        logger.info(f"獲利實驗數: {len(df[df['total_pnl'] > 0])}")
        logger.info(f"多空都獲利實驗數: {len(df[df['both_profitable']])}")
        
        # 最佳結果（總損益）
        best_total = df.loc[df['total_pnl'].idxmax()]
        logger.info(f"\n🏆 最佳總損益實驗:")
        logger.info(f"實驗ID: {best_total['experiment_id']}")
        logger.info(f"總損益: {best_total['total_pnl']:.2f}")
        logger.info(f"停損點: {best_total['stop_loss_points']}, 停利點: {best_total['take_profit_points']}")
        
        # 最佳多空都獲利結果
        both_profitable = df[df['both_profitable']]
        if not both_profitable.empty:
            best_both = both_profitable.loc[both_profitable['total_pnl'].idxmax()]
            logger.info(f"\n🎯 最佳多空都獲利實驗:")
            logger.info(f"實驗ID: {best_both['experiment_id']}")
            logger.info(f"總損益: {best_both['total_pnl']:.2f}")
            logger.info(f"多頭損益: {best_both['long_pnl']:.2f}, 空頭損益: {best_both['short_pnl']:.2f}")
        
        return df


if __name__ == "__main__":
    # 創建優化器實例
    optimizer = ParameterOptimizer()
    
    # 執行批量實驗
    results = optimizer.run_batch_experiments(max_workers=2)  # 使用2個並行進程
    
    # 分析結果
    optimizer.analyze_results()
    
    # 保存結果
    optimizer.save_results_to_csv()
