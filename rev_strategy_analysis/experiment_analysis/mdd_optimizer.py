#!/usr/bin/env python3
"""
MDD最小化參數優化器
專門尋找最小最大回撤(Maximum Drawdown)的最佳參數組合
支援三口獨立停損停利設定
"""

import os
import sys
import logging
import pandas as pd
import itertools
from concurrent.futures import ProcessPoolExecutor
from datetime import datetime
import subprocess
import json
from pathlib import Path

# 設定日誌
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('results/mdd_optimization.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class MDDOptimizer:
    """MDD最小化參數優化器"""
    
    def __init__(self):
        self.results_dir = Path("results")
        self.results_dir.mkdir(exist_ok=True)
        
        # === 擴展參數範圍設定 ===
        # 停損點數範圍 (每口獨立) - 更細緻的搜索
        self.stop_loss_ranges = {
            'lot1': list(range(10, 31, 2)),    # 第1口: 10-30點，步長2 (11個值)
            'lot2': list(range(15, 46, 2)),    # 第2口: 15-45點，步長2 (16個值)
            'lot3': list(range(20, 51, 2))     # 第3口: 20-50點，步長2 (16個值)
        }

        # 停利點數範圍 (每口獨立) - 支援個別設定
        self.take_profit_ranges = {
            'lot1': list(range(30, 101, 5)),   # 第1口: 30-100點，步長5 (15個值)
            'lot2': list(range(30, 101, 5)),   # 第2口: 30-100點，步長5 (15個值)
            'lot3': list(range(30, 101, 5))    # 第3口: 30-100點，步長5 (15個值)
        }

        # 擴展時間區間 - 包含2分鐘區間
        self.time_intervals = [
            ("10:30", "10:31"),  # 早盤活躍 1分鐘
            ("10:30", "10:32"),  # 早盤活躍 2分鐘
            ("11:30", "11:31"),  # 中午震盪 1分鐘
            ("11:30", "11:32"),  # 中午震盪 2分鐘
            ("12:30", "12:31"),  # 午後時段 1分鐘
            ("12:30", "12:32"),  # 午後時段 2分鐘
            ("09:00", "09:01"),  # 開盤第一分鐘
            ("13:30", "13:31"),  # 尾盤時段
        ]
        
        # 回測期間
        self.start_date = "2024-11-04"
        self.end_date = "2025-06-27"
        
        logger.info(f"📊 MDD優化器初始化完成")
        logger.info(f"   第1口停損範圍: {list(self.stop_loss_ranges['lot1'])}")
        logger.info(f"   第2口停損範圍: {list(self.stop_loss_ranges['lot2'])}")
        logger.info(f"   第3口停損範圍: {list(self.stop_loss_ranges['lot3'])}")
        logger.info(f"   停利範圍: {list(self.take_profit_range)}")
        logger.info(f"   時間區間: {self.time_intervals}")
    
    def generate_experiment_combinations(self, individual_tp=False):
        """生成所有實驗組合

        Args:
            individual_tp: 是否使用每口獨立停利設定
        """
        combinations = []

        if individual_tp:
            # 每口獨立停利設定 (組合數量會很大)
            for time_interval in self.time_intervals:
                for lot1_sl in self.stop_loss_ranges['lot1']:
                    for lot2_sl in self.stop_loss_ranges['lot2']:
                        for lot3_sl in self.stop_loss_ranges['lot3']:
                            for lot1_tp in self.take_profit_ranges['lot1']:
                                for lot2_tp in self.take_profit_ranges['lot2']:
                                    for lot3_tp in self.take_profit_ranges['lot3']:
                                        # 確保停損遞增約束
                                        if lot1_sl <= lot2_sl <= lot3_sl:
                                            combination = {
                                                'time_interval': f"{time_interval[0]}-{time_interval[1]}",
                                                'lot1_stop_loss': lot1_sl,
                                                'lot2_stop_loss': lot2_sl,
                                                'lot3_stop_loss': lot3_sl,
                                                'lot1_take_profit': lot1_tp,
                                                'lot2_take_profit': lot2_tp,
                                                'lot3_take_profit': lot3_tp,
                                                'experiment_id': f"{time_interval[0]}{time_interval[1]}_L1SL{lot1_sl}TP{lot1_tp}_L2SL{lot2_sl}TP{lot2_tp}_L3SL{lot3_sl}TP{lot3_tp}"
                                            }
                                            combinations.append(combination)
        else:
            # 統一停利設定 (較少組合數量)
            unified_take_profit_range = list(range(30, 101, 10))  # 30-100點，步長10
            for time_interval in self.time_intervals:
                for lot1_sl in self.stop_loss_ranges['lot1']:
                    for lot2_sl in self.stop_loss_ranges['lot2']:
                        for lot3_sl in self.stop_loss_ranges['lot3']:
                            for take_profit in unified_take_profit_range:
                                # 確保停損遞增約束
                                if lot1_sl <= lot2_sl <= lot3_sl:
                                    combination = {
                                        'time_interval': f"{time_interval[0]}-{time_interval[1]}",
                                        'lot1_stop_loss': lot1_sl,
                                        'lot2_stop_loss': lot2_sl,
                                        'lot3_stop_loss': lot3_sl,
                                        'take_profit': take_profit,
                                        'experiment_id': f"{time_interval[0]}{time_interval[1]}_L1SL{lot1_sl}_L2SL{lot2_sl}_L3SL{lot3_sl}_TP{take_profit}"
                                    }
                                    combinations.append(combination)

        logger.info(f"📊 生成了 {len(combinations)} 個實驗組合")
        return combinations
    
    def create_experiment_config(self, params):
        """創建實驗配置"""
        config = {
            'start_date': self.start_date,
            'end_date': self.end_date,
            'range_start_time': params['time_interval'].split('-')[0],
            'range_end_time': params['time_interval'].split('-')[1],
            'trade_lots': 3,
            'fixed_stop_mode': True,  # 使用固定停損模式
            'individual_take_profit_enabled': True,  # 🎯 啟用每口獨立停利設定
            'lot_settings': {},
            'filters': {
                'range_filter': {'enabled': False},
                'risk_filter': {'enabled': False},
                'stop_loss_filter': {'enabled': False}
            }
        }

        # 根據參數類型設定每口配置
        if 'lot1_take_profit' in params:
            # 每口獨立停利設定
            config['lot_settings'] = {
                'lot1': {
                    'trigger': params['lot1_stop_loss'],
                    'trailing': 0,
                    'take_profit': params['lot1_take_profit']
                },
                'lot2': {
                    'trigger': params['lot2_stop_loss'],
                    'trailing': 0,
                    'take_profit': params['lot2_take_profit']
                },
                'lot3': {
                    'trigger': params['lot3_stop_loss'],
                    'trailing': 0,
                    'take_profit': params['lot3_take_profit']
                }
            }
        else:
            # 統一停利設定
            config['lot_settings'] = {
                'lot1': {
                    'trigger': params['lot1_stop_loss'],
                    'trailing': 0,
                    'take_profit': params['take_profit']
                },
                'lot2': {
                    'trigger': params['lot2_stop_loss'],
                    'trailing': 0,
                    'take_profit': params['take_profit']
                },
                'lot3': {
                    'trigger': params['lot3_stop_loss'],
                    'trailing': 0,
                    'take_profit': params['take_profit']
                }
            }
        return config
    
    def run_single_experiment(self, params):
        """執行單個實驗"""
        try:
            experiment_id = params['experiment_id']
            logger.info(f"🧪 開始實驗: {experiment_id}")
            
            # 創建實驗配置
            config = self.create_experiment_config(params)
            
            # 調用真實的策略引擎 (與GUI相同)
            result = subprocess.run([
                sys.executable, '../rev_multi_Profit-Funded Risk_多口.py',
                '--start-date', config['start_date'],
                '--end-date', config['end_date'],
                '--gui-mode',
                '--config', json.dumps(config, ensure_ascii=False)
            ], capture_output=True, text=True, timeout=300, encoding='utf-8', errors='replace')
            
            if result.returncode == 0:
                # 解析真實策略引擎的輸出 (從stderr中提取LOG信息)
                output = result.stderr  # 策略引擎的LOG在stderr中

                # 解析關鍵統計數據
                total_pnl = None
                max_drawdown = None
                win_rate = None
                total_trades = None

                # 計算最大回撤的變數
                current_pnl = 0
                peak_pnl = 0
                max_dd = 0

                for line in output.split('\n'):
                    if "總損益(3口):" in line:
                        try:
                            total_pnl = float(line.split("總損益(3口):")[1].strip())
                        except:
                            pass
                    elif "勝率:" in line:
                        try:
                            win_rate_str = line.split("勝率:")[1].strip().replace('%', '')
                            win_rate = float(win_rate_str)
                        except:
                            pass
                    elif "總交易次數:" in line:
                        try:
                            total_trades = int(line.split("總交易次數:")[1].strip())
                        except:
                            pass
                    # 解析每筆交易的損益來計算MDD
                    elif "損益:" in line and ("第1口" in line or "第2口" in line or "第3口" in line):
                        try:
                            pnl_str = line.split("損益:")[1].strip()
                            if pnl_str.startswith('+'):
                                pnl = float(pnl_str[1:])
                            elif pnl_str.startswith('-'):
                                pnl = -float(pnl_str[1:])
                            else:
                                pnl = float(pnl_str)

                            current_pnl += pnl
                            peak_pnl = max(peak_pnl, current_pnl)
                            drawdown = peak_pnl - current_pnl
                            max_dd = max(max_dd, drawdown)
                        except:
                            pass

                # 設定最大回撤
                max_drawdown = -max_dd if max_dd > 0 else 0

                if total_pnl is not None:
                    result_data = {
                        'experiment_id': experiment_id,
                        'time_interval': params['time_interval'],
                        'lot1_stop_loss': params['lot1_stop_loss'],
                        'lot2_stop_loss': params['lot2_stop_loss'],
                        'lot3_stop_loss': params['lot3_stop_loss'],
                        'take_profit': params['take_profit'],
                        'total_pnl': total_pnl,
                        'max_drawdown': max_drawdown,
                        'win_rate': win_rate,
                        'total_trades': total_trades
                    }

                    logger.info(f"✅ 實驗 {experiment_id} 完成 - MDD: {max_drawdown:.2f}, P&L: {total_pnl:.2f}")
                    return result_data
                else:
                    logger.error(f"❌ 實驗 {experiment_id} 無法解析結果")
                    return None
            else:
                logger.error(f"❌ 實驗 {experiment_id} 執行失敗: {result.stderr}")
                return None
                
        except Exception as e:
            logger.error(f"❌ 實驗 {params['experiment_id']} 異常: {str(e)}")
            return None
    
    def run_optimization(self, max_workers=2, sample_size=None, individual_tp=False):
        """執行MDD優化

        Args:
            max_workers: 並行工作數量
            sample_size: 樣本數量限制
            individual_tp: 是否使用每口獨立停利設定
        """
        logger.info("🚀 開始MDD最小化參數優化...")
        logger.info(f"🎯 配置模式: {'每口獨立停利' if individual_tp else '統一停利'}")

        # 生成實驗組合
        combinations = self.generate_experiment_combinations(individual_tp=individual_tp)

        # 如果指定樣本數量，隨機選擇
        if sample_size and sample_size < len(combinations):
            import random
            random.seed(42)  # 固定種子確保可重現
            combinations = random.sample(combinations, sample_size)
            logger.info(f"🎯 隨機選擇 {sample_size} 個實驗進行測試")
        
        # 並行執行實驗
        results = []
        with ProcessPoolExecutor(max_workers=max_workers) as executor:
            futures = [executor.submit(self.run_single_experiment, params) for params in combinations]
            
            for i, future in enumerate(futures):
                try:
                    result = future.result(timeout=600)  # 10分鐘超時
                    if result:
                        results.append(result)
                    
                    # 進度報告
                    if (i + 1) % 10 == 0:
                        logger.info(f"📈 進度: {i + 1}/{len(combinations)} ({(i + 1)/len(combinations)*100:.1f}%)")
                        
                except Exception as e:
                    logger.error(f"❌ 實驗執行異常: {str(e)}")
        
        # 保存結果
        if results:
            df = pd.DataFrame(results)
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            csv_file = self.results_dir / f"mdd_optimization_results_{timestamp}.csv"
            df.to_csv(csv_file, index=False)
            logger.info(f"💾 結果已保存到: {csv_file}")
            
            # 分析最佳結果
            self.analyze_results(df)
            
            return df
        else:
            logger.error("❌ 沒有有效的實驗結果")
            return None
    
    def analyze_results(self, df):
        """分析實驗結果，重點關注MDD"""
        logger.info("\n" + "="*60)
        logger.info("📊 MDD最小化分析結果")
        logger.info("="*60)
        
        # 基本統計
        logger.info(f"總實驗數: {len(df)}")
        logger.info(f"有效結果數: {len(df.dropna())}")
        
        if 'max_drawdown' in df.columns:
            # 按MDD排序 (MDD通常是負值，越接近0越好)
            df_sorted = df.sort_values('max_drawdown', ascending=False)  # 降序，最小回撤在前
            
            logger.info(f"\n🏆 MDD最小 TOP 10:")
            logger.info("-" * 80)
            for i, row in df_sorted.head(10).iterrows():
                logger.info(f"{i+1:2d}. MDD:{row['max_drawdown']:8.2f} | "
                          f"總P&L:{row.get('total_pnl', 0):8.2f} | "
                          f"L1SL:{row['lot1_stop_loss']:2d} L2SL:{row['lot2_stop_loss']:2d} L3SL:{row['lot3_stop_loss']:2d} | "
                          f"TP:{row['take_profit']:3d} | {row['time_interval']}")
            
            # 額外分析：MDD vs 總收益的平衡
            if 'total_pnl' in df.columns:
                # 計算風險調整收益 (總收益 / |MDD|)
                df['risk_adjusted_return'] = df['total_pnl'] / abs(df['max_drawdown'].replace(0, 1))
                df_risk_sorted = df.sort_values('risk_adjusted_return', ascending=False)
                
                logger.info(f"\n💎 風險調整收益 TOP 10 (總收益/|MDD|):")
                logger.info("-" * 80)
                for i, row in df_risk_sorted.head(10).iterrows():
                    logger.info(f"{i+1:2d}. 風險調整收益:{row['risk_adjusted_return']:6.2f} | "
                              f"MDD:{row['max_drawdown']:8.2f} | "
                              f"總P&L:{row['total_pnl']:8.2f} | "
                              f"L1SL:{row['lot1_stop_loss']:2d} L2SL:{row['lot2_stop_loss']:2d} L3SL:{row['lot3_stop_loss']:2d} | "
                              f"TP:{row['take_profit']:3d}")
        
        logger.info("="*60)

    def create_mdd_visualization(self, df):
        """創建MDD可視化圖表"""
        try:
            import matplotlib.pyplot as plt
            import seaborn as sns
            import numpy as np

            # 設定中文字體
            plt.rcParams['font.sans-serif'] = ['Arial Unicode MS', 'SimHei', 'DejaVu Sans']
            plt.rcParams['axes.unicode_minus'] = False

            # 創建圖表目錄
            viz_dir = self.results_dir / "mdd_visualization"
            viz_dir.mkdir(exist_ok=True)

            # 1. MDD vs 總收益散點圖
            plt.figure(figsize=(12, 8))
            scatter = plt.scatter(df['max_drawdown'], df['total_pnl'],
                                c=df['win_rate'], cmap='RdYlGn', alpha=0.7, s=60)
            plt.colorbar(scatter, label='Win Rate (%)')
            plt.xlabel('Maximum Drawdown (Points)')
            plt.ylabel('Total P&L (Points)')
            plt.title('MDD vs Total P&L (Color: Win Rate)')
            plt.grid(True, alpha=0.3)

            # 標註最佳點
            best_mdd_idx = df['max_drawdown'].idxmax()  # 最小回撤
            best_risk_adj_idx = df['risk_adjusted_return'].idxmax() if 'risk_adjusted_return' in df.columns else best_mdd_idx

            plt.annotate(f'Best MDD\n{df.loc[best_mdd_idx, "experiment_id"]}',
                        xy=(df.loc[best_mdd_idx, 'max_drawdown'], df.loc[best_mdd_idx, 'total_pnl']),
                        xytext=(10, 10), textcoords='offset points',
                        bbox=dict(boxstyle='round,pad=0.3', facecolor='yellow', alpha=0.7),
                        arrowprops=dict(arrowstyle='->', connectionstyle='arc3,rad=0'))

            plt.tight_layout()
            plt.savefig(viz_dir / 'mdd_vs_pnl_scatter.png', dpi=300, bbox_inches='tight')
            plt.close()

            # 2. 停損參數熱力圖
            if len(df) > 10:  # 確保有足夠數據
                plt.figure(figsize=(15, 10))

                # 創建停損組合的平均MDD
                pivot_data = df.groupby(['lot1_stop_loss', 'lot2_stop_loss'])['max_drawdown'].mean().unstack()

                sns.heatmap(pivot_data, annot=True, fmt='.1f', cmap='RdYlGn',
                           cbar_kws={'label': 'Average MDD (Points)'})
                plt.title('Average MDD by Lot1 vs Lot2 Stop Loss')
                plt.xlabel('Lot2 Stop Loss (Points)')
                plt.ylabel('Lot1 Stop Loss (Points)')
                plt.tight_layout()
                plt.savefig(viz_dir / 'mdd_heatmap_lot1_lot2.png', dpi=300, bbox_inches='tight')
                plt.close()

            logger.info(f"📊 MDD可視化圖表已保存到: {viz_dir}")

        except ImportError:
            logger.warning("⚠️ matplotlib/seaborn 未安裝，跳過可視化")
        except Exception as e:
            logger.error(f"❌ 創建可視化時發生錯誤: {str(e)}")

def main():
    """主函數"""
    import argparse

    parser = argparse.ArgumentParser(description='MDD最小化參數優化器')
    parser.add_argument('--sample-size', type=int, help='樣本數量 (用於快速測試)')
    parser.add_argument('--max-workers', type=int, default=2, help='並行進程數')
    parser.add_argument('--create-viz', action='store_true', help='創建可視化圖表')
    parser.add_argument('--individual-tp', action='store_true', help='使用每口獨立停利設定 (組合數量會大幅增加)')
    parser.add_argument('--focus-mode', choices=['unified', 'individual', 'both'], default='unified',
                       help='搜索模式: unified=統一停利, individual=每口獨立停利, both=兩種都測試')

    args = parser.parse_args()

    optimizer = MDDOptimizer()

    if args.sample_size:
        logger.info(f"⚡ 快速測試模式 - 樣本數: {args.sample_size}")
    else:
        logger.info("🎯 完整優化模式")

    # 根據模式執行優化
    if args.focus_mode == 'both':
        logger.info("🔄 執行兩種模式的對比測試...")

        # 統一停利模式
        logger.info("📊 第一階段: 統一停利模式")
        results_unified = optimizer.run_optimization(
            max_workers=args.max_workers,
            sample_size=args.sample_size,
            individual_tp=False
        )

        # 每口獨立停利模式
        logger.info("📊 第二階段: 每口獨立停利模式")
        results_individual = optimizer.run_optimization(
            max_workers=args.max_workers,
            sample_size=args.sample_size,
            individual_tp=True
        )

        results = results_unified  # 主要結果
    else:
        individual_tp = args.individual_tp or args.focus_mode == 'individual'
        results = optimizer.run_optimization(
            max_workers=args.max_workers,
            sample_size=args.sample_size,
            individual_tp=individual_tp
        )

    if results is not None:
        if args.create_viz:
            optimizer.create_mdd_visualization(results)
        logger.info("🎊 MDD優化完成！")
    else:
        logger.error("❌ MDD優化失敗")

if __name__ == "__main__":
    main()
