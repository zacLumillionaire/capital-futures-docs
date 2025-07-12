#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
參數優化系統 - 大量回測不同參數組合
目標：找出 LONG P&L 和總 P&L 最佳的配置
"""

import sys
import os
import time
import csv
from datetime import datetime
from decimal import Decimal
from itertools import product
from dataclasses import dataclass
from typing import List, Dict, Tuple

# 添加當前目錄到路徑
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# 導入現有模組
import importlib.util
import sys

# 動態導入模組
module_name = "multi_Profit-Funded Risk_多口"
file_path = "multi_Profit-Funded Risk_多口.py"

spec = importlib.util.spec_from_file_location(module_name, file_path)
strategy_module = importlib.util.module_from_spec(spec)
sys.modules[module_name] = strategy_module
spec.loader.exec_module(strategy_module)

# 導入需要的類和函數
StrategyConfig = strategy_module.StrategyConfig
LotRule = strategy_module.LotRule
StopLossType = strategy_module.StopLossType
StopLossConfig = strategy_module.StopLossConfig
RangeFilter = strategy_module.RangeFilter
RiskConfig = strategy_module.RiskConfig
run_backtest = strategy_module.run_backtest

@dataclass
class OptimizationResult:
    """優化結果數據類"""
    config_id: int
    lot1_trigger: int
    lot1_pullback: float
    lot2_trigger: int
    lot2_pullback: float
    lot3_trigger: int
    lot3_pullback: float
    total_pnl: float
    long_pnl: float
    short_pnl: float
    total_trades: int
    long_trades: int
    short_trades: int
    win_rate: float
    long_win_rate: float
    short_win_rate: float
    execution_time: float

class ParameterOptimizer:
    """參數優化器"""
    
    def __init__(self, start_date: str, end_date: str):
        self.start_date = start_date
        self.end_date = end_date
        self.results: List[OptimizationResult] = []
        
    def generate_parameter_combinations(self) -> List[Dict]:
        """生成所有參數組合"""
        # 參數範圍定義
        lot1_triggers = list(range(10, 31))  # 第1口: 10-30點
        lot1_pullbacks = [0.10, 0.15, 0.20, 0.25, 0.30]  # 第1口: 10%-30%
        lot2_triggers = list(range(30, 41))  # 第2口: 30-40點
        lot2_pullbacks = [0.10, 0.15, 0.20, 0.25, 0.30]  # 第2口: 10%-30%
        lot3_triggers = [41]  # 第3口: 固定41點
        lot3_pullbacks = [0.20]  # 第3口: 固定20%
        
        combinations = []
        config_id = 1
        
        for lot1_trigger, lot1_pullback, lot2_trigger, lot2_pullback, lot3_trigger, lot3_pullback in product(
            lot1_triggers, lot1_pullbacks, lot2_triggers, lot2_pullbacks, lot3_triggers, lot3_pullbacks
        ):
            combinations.append({
                'config_id': config_id,
                'lot1_trigger': lot1_trigger,
                'lot1_pullback': lot1_pullback,
                'lot2_trigger': lot2_trigger,
                'lot2_pullback': lot2_pullback,
                'lot3_trigger': lot3_trigger,
                'lot3_pullback': lot3_pullback
            })
            config_id += 1
            
        return combinations
    
    def create_strategy_config(self, params: Dict) -> StrategyConfig:
        """根據參數創建策略配置"""
        return StrategyConfig(
            trade_size_in_lots=3,
            stop_loss_type=StopLossType.RANGE_BOUNDARY,
            lot_rules=[
                # 第1口：變化參數
                LotRule(
                    use_trailing_stop=True,
                    trailing_activation=params['lot1_trigger'],
                    trailing_pullback=params['lot1_pullback'],
                    protective_stop_multiplier=None
                ),
                # 第2口：變化參數
                LotRule(
                    use_trailing_stop=True,
                    trailing_activation=params['lot2_trigger'],
                    trailing_pullback=params['lot2_pullback'],
                    protective_stop_multiplier=1.0
                ),
                # 第3口：變化參數
                LotRule(
                    use_trailing_stop=True,
                    trailing_activation=params['lot3_trigger'],
                    trailing_pullback=params['lot3_pullback'],
                    protective_stop_multiplier=1.0
                )
            ],
            # 明確設置濾網為停用狀態
            range_filter=RangeFilter(use_range_size_filter=False, max_range_points=0),
            risk_config=RiskConfig(use_risk_filter=False, daily_loss_limit=0, profit_target=0)
        )
    
    def run_single_backtest(self, config: StrategyConfig) -> Tuple[float, float, float, int, int, int, float, float, float]:
        """執行單次回測並返回結果"""
        try:
            # 執行回測
            result = run_backtest(config, self.start_date, self.end_date, silent=True)

            # 解析結果 - 確保result不為None
            if result is None:
                return 0.0, 0.0, 0.0, 0, 0, 0, 0.0, 0.0, 0.0

            total_pnl = float(result.get('total_pnl', 0))
            long_pnl = float(result.get('long_pnl', 0))
            short_pnl = float(result.get('short_pnl', 0))
            total_trades = int(result.get('total_trades', 0))
            long_trades = int(result.get('long_trades', 0))
            short_trades = int(result.get('short_trades', 0))
            win_rate = float(result.get('win_rate', 0))
            long_win_rate = float(result.get('long_win_rate', 0))
            short_win_rate = float(result.get('short_win_rate', 0))

            return total_pnl, long_pnl, short_pnl, total_trades, long_trades, short_trades, win_rate, long_win_rate, short_win_rate

        except Exception as e:
            print(f"回測執行錯誤: {e}")
            return 0.0, 0.0, 0.0, 0, 0, 0, 0.0, 0.0, 0.0
    
    def run_optimization(self):
        """執行完整的參數優化"""
        print("🚀 開始參數優化...")
        
        # 生成所有參數組合
        combinations = self.generate_parameter_combinations()
        total_combinations = len(combinations)
        
        print(f"📊 總共需要測試 {total_combinations} 種配置")
        print(f"📅 回測時間區間: {self.start_date} 至 {self.end_date}")
        print("=" * 60)
        
        start_time = time.time()
        
        for i, params in enumerate(combinations, 1):
            # 創建配置
            config = self.create_strategy_config(params)
            
            # 執行回測
            backtest_start = time.time()
            total_pnl, long_pnl, short_pnl, total_trades, long_trades, short_trades, win_rate, long_win_rate, short_win_rate = self.run_single_backtest(config)
            execution_time = time.time() - backtest_start
            
            # 記錄結果
            result = OptimizationResult(
                config_id=params['config_id'],
                lot1_trigger=params['lot1_trigger'],
                lot1_pullback=params['lot1_pullback'],
                lot2_trigger=params['lot2_trigger'],
                lot2_pullback=params['lot2_pullback'],
                lot3_trigger=params['lot3_trigger'],
                lot3_pullback=params['lot3_pullback'],
                total_pnl=total_pnl,
                long_pnl=long_pnl,
                short_pnl=short_pnl,
                total_trades=total_trades,
                long_trades=long_trades,
                short_trades=short_trades,
                win_rate=win_rate,
                long_win_rate=long_win_rate,
                short_win_rate=short_win_rate,
                execution_time=execution_time
            )
            self.results.append(result)
            
            # 進度顯示
            if i % 50 == 0 or i == total_combinations:
                elapsed = time.time() - start_time
                avg_time = elapsed / i
                remaining = (total_combinations - i) * avg_time
                print(f"進度: {i}/{total_combinations} ({i/total_combinations*100:.1f}%) | "
                      f"已用時: {elapsed:.1f}s | 預估剩餘: {remaining:.1f}s")
        
        total_time = time.time() - start_time
        print(f"\n✅ 優化完成！總耗時: {total_time:.1f}秒")
        
    def generate_reports(self):
        """生成優化報告"""
        if not self.results:
            print("❌ 沒有結果數據，無法生成報告")
            return
            
        print("\n📊 生成優化報告...")
        
        # 按LONG P&L排序
        long_pnl_top10 = sorted(self.results, key=lambda x: x.long_pnl, reverse=True)[:10]
        
        # 按總P&L排序
        total_pnl_top10 = sorted(self.results, key=lambda x: x.total_pnl, reverse=True)[:10]
        
        # 生成控制台報告
        self._print_console_report(long_pnl_top10, total_pnl_top10)
        
        # 生成CSV報告
        self._save_csv_reports(long_pnl_top10, total_pnl_top10)
        
    def _print_console_report(self, long_top10: List[OptimizationResult], total_top10: List[OptimizationResult]):
        """打印控制台報告"""
        print("\n" + "="*80)
        print("🏆 參數優化結果報告")
        print("="*80)
        print(f"總測試配置: {len(self.results)}")
        print(f"回測區間: {self.start_date} 至 {self.end_date}")
        
        print("\n📈 LONG P&L 前10名:")
        print("排名 | 配置ID | 第1口觸發 | 第1口回檔 | 第2口觸發 | 第2口回檔 | 第3口觸發 | 第3口回檔 | LONG P&L | 總P&L | LONG勝率")
        print("-" * 120)
        for i, result in enumerate(long_top10, 1):
            print(f"{i:2d}   | {result.config_id:4d}   | {result.lot1_trigger:6d}   | "
                  f"{result.lot1_pullback:6.0%}   | {result.lot2_trigger:6d}   | "
                  f"{result.lot2_pullback:6.0%}   | {result.lot3_trigger:6d}   | "
                  f"{result.lot3_pullback:6.0%}   | {result.long_pnl:7.1f}  | {result.total_pnl:6.1f} | {result.long_win_rate:6.1%}")

        print("\n📊 總P&L 前10名:")
        print("排名 | 配置ID | 第1口觸發 | 第1口回檔 | 第2口觸發 | 第2口回檔 | 第3口觸發 | 第3口回檔 | 總P&L | LONG P&L | 總勝率")
        print("-" * 120)
        for i, result in enumerate(total_top10, 1):
            print(f"{i:2d}   | {result.config_id:4d}   | {result.lot1_trigger:6d}   | "
                  f"{result.lot1_pullback:6.0%}   | {result.lot2_trigger:6d}   | "
                  f"{result.lot2_pullback:6.0%}   | {result.lot3_trigger:6d}   | "
                  f"{result.lot3_pullback:6.0%}   | {result.total_pnl:6.1f}  | {result.long_pnl:7.1f} | {result.win_rate:6.1%}")
        
    def _save_csv_reports(self, long_top10: List[OptimizationResult], total_top10: List[OptimizationResult]):
        """保存CSV報告"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        # 保存完整結果
        full_filename = f"optimization_full_results_{timestamp}.csv"
        self._save_results_to_csv(self.results, full_filename, "完整優化結果")
        
        # 保存LONG P&L前10名
        long_filename = f"optimization_long_top10_{timestamp}.csv"
        self._save_results_to_csv(long_top10, long_filename, "LONG P&L前10名")
        
        # 保存總P&L前10名
        total_filename = f"optimization_total_top10_{timestamp}.csv"
        self._save_results_to_csv(total_top10, total_filename, "總P&L前10名")
        
    def _save_results_to_csv(self, results: List[OptimizationResult], filename: str, description: str):
        """保存結果到CSV文件"""
        try:
            with open(filename, 'w', newline='', encoding='utf-8') as csvfile:
                fieldnames = [
                    '配置ID', '第1口觸發點', '第1口回檔率', '第2口觸發點', '第2口回檔率', '第3口觸發點', '第3口回檔率',
                    '總P&L', 'LONG_P&L', 'SHORT_P&L',
                    '總交易次數', 'LONG交易次數', 'SHORT交易次數',
                    '總勝率', 'LONG勝率', 'SHORT勝率', '執行時間'
                ]
                
                writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
                writer.writeheader()
                
                for result in results:
                    writer.writerow({
                        '配置ID': result.config_id,
                        '第1口觸發點': result.lot1_trigger,
                        '第1口回檔率': f"{result.lot1_pullback:.0%}",
                        '第2口觸發點': result.lot2_trigger,
                        '第2口回檔率': f"{result.lot2_pullback:.0%}",
                        '第3口觸發點': result.lot3_trigger,
                        '第3口回檔率': f"{result.lot3_pullback:.0%}",
                        '總P&L': f"{result.total_pnl:.1f}",
                        'LONG_P&L': f"{result.long_pnl:.1f}",
                        'SHORT_P&L': f"{result.short_pnl:.1f}",
                        '總交易次數': result.total_trades,
                        'LONG交易次數': result.long_trades,
                        'SHORT交易次數': result.short_trades,
                        '總勝率': f"{result.win_rate:.1%}",
                        'LONG勝率': f"{result.long_win_rate:.1%}",
                        'SHORT勝率': f"{result.short_win_rate:.1%}",
                        '執行時間': f"{result.execution_time:.3f}s"
                    })
            
            print(f"✅ {description} 已保存至: {filename}")
            
        except Exception as e:
            print(f"❌ 保存CSV文件失敗: {e}")

def main():
    """主函數"""
    print("🎯 參數優化系統")
    print("=" * 50)
    
    # 固定的回測時間區間
    start_date = "2024-11-04"
    end_date = "2025-06-28"
    
    # 創建優化器
    optimizer = ParameterOptimizer(start_date, end_date)
    
    # 執行優化
    optimizer.run_optimization()
    
    # 生成報告
    optimizer.generate_reports()
    
    print("\n🎉 參數優化完成！")

if __name__ == "__main__":
    main()
