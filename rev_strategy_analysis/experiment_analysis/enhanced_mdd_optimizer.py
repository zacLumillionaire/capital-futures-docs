#!/usr/bin/env python3
"""
增強版 MDD 優化器
支援多種搜索策略和配置模式
"""

import sys
import json
import logging
import subprocess
import pandas as pd
from pathlib import Path
from datetime import datetime
from concurrent.futures import ProcessPoolExecutor
from mdd_search_config import MDDSearchConfig

# 設定日誌
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('results/enhanced_mdd_optimization.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class EnhancedMDDOptimizer:
    """增強版 MDD 優化器"""
    
    def __init__(self, config_name='quick'):
        self.results_dir = Path("results")
        self.results_dir.mkdir(exist_ok=True)
        
        # 載入搜索配置
        self.config = MDDSearchConfig.get_config_by_name(config_name)
        self.config_name = config_name
        
        # 回測期間
        self.start_date = "2024-11-04"
        self.end_date = "2025-06-28"
        
        logger.info(f"🎯 增強版 MDD 優化器初始化完成 - 配置: {config_name.upper()}")
        self._log_config_summary()
    
    def _log_config_summary(self):
        """記錄配置摘要"""
        config = self.config
        logger.info(f"   第1口停損範圍: {config['stop_loss_ranges']['lot1']}")
        logger.info(f"   第2口停損範圍: {config['stop_loss_ranges']['lot2']}")
        logger.info(f"   第3口停損範圍: {config['stop_loss_ranges']['lot3']}")
        logger.info(f"   時間區間數量: {len(config['time_intervals'])}")

        # 根據配置類型顯示預估組合數
        if 'unified' in config['estimated_combinations']:
            logger.info(f"   預估組合數 (統一停利): {config['estimated_combinations']['unified']:,}")
        if 'individual' in config['estimated_combinations']:
            logger.info(f"   預估組合數 (獨立停利): {config['estimated_combinations']['individual']:,}")
        if 'range_boundary' in config['estimated_combinations']:
            logger.info(f"   預估組合數 (區間邊緣停利): {config['estimated_combinations']['range_boundary']:,}")
        if 'per_interval_analysis' in config['estimated_combinations']:
            logger.info(f"   預估組合數 (時間區間分析): {config['estimated_combinations']['per_interval_analysis']:,}")
            logger.info(f"   分析說明: {config['estimated_combinations']['breakdown']}")
    
    def generate_experiment_combinations(self, individual_tp=False):
        """生成實驗組合"""
        combinations = []
        config = self.config

        # 檢查是否為時間區間分析模式
        if config.get('analysis_mode') == 'per_time_interval':
            # 時間區間分析模式 - 每個區間測試固定停利和區間邊緣停利
            for time_interval in config['time_intervals']:
                for lot1_sl in config['stop_loss_ranges']['lot1']:
                    for lot2_sl in config['stop_loss_ranges']['lot2']:
                        for lot3_sl in config['stop_loss_ranges']['lot3']:
                            # 確保停損遞增約束
                            if lot1_sl <= lot2_sl <= lot3_sl:
                                # 1. 區間邊緣停利
                                combination_boundary = {
                                    'time_interval': f"{time_interval[0]}-{time_interval[1]}",
                                    'lot1_stop_loss': lot1_sl,
                                    'lot2_stop_loss': lot2_sl,
                                    'lot3_stop_loss': lot3_sl,
                                    'take_profit_mode': 'range_boundary',
                                    'experiment_id': f"{time_interval[0]}{time_interval[1]}_L1SL{lot1_sl}_L2SL{lot2_sl}_L3SL{lot3_sl}_RangeBoundary"
                                }
                                combinations.append(combination_boundary)

                                # 2. 統一固定停利 (每個停利點)
                                for take_profit in config['take_profit_ranges']['unified']:
                                    combination_fixed = {
                                        'time_interval': f"{time_interval[0]}-{time_interval[1]}",
                                        'lot1_stop_loss': lot1_sl,
                                        'lot2_stop_loss': lot2_sl,
                                        'lot3_stop_loss': lot3_sl,
                                        'take_profit': take_profit,
                                        'experiment_id': f"{time_interval[0]}{time_interval[1]}_L1SL{lot1_sl}_L2SL{lot2_sl}_L3SL{lot3_sl}_TP{take_profit}"
                                    }
                                    combinations.append(combination_fixed)

                                # 3. 各口獨立停利 (每口都可以有不同停利點)
                                for lot1_tp in config['take_profit_ranges']['individual']:
                                    for lot2_tp in config['take_profit_ranges']['individual']:
                                        for lot3_tp in config['take_profit_ranges']['individual']:
                                            combination_individual = {
                                                'time_interval': f"{time_interval[0]}-{time_interval[1]}",
                                                'lot1_stop_loss': lot1_sl,
                                                'lot2_stop_loss': lot2_sl,
                                                'lot3_stop_loss': lot3_sl,
                                                'lot1_take_profit': lot1_tp,
                                                'lot2_take_profit': lot2_tp,
                                                'lot3_take_profit': lot3_tp,
                                                'experiment_id': f"{time_interval[0]}{time_interval[1]}_L1SL{lot1_sl}TP{lot1_tp}_L2SL{lot2_sl}TP{lot2_tp}_L3SL{lot3_sl}TP{lot3_tp}"
                                            }
                                            combinations.append(combination_individual)
        # 檢查是否為區間邊緣停利模式
        elif config.get('take_profit_mode') == 'range_boundary':
            # 區間邊緣停利模式 - 無需停利參數
            for time_interval in config['time_intervals']:
                for lot1_sl in config['stop_loss_ranges']['lot1']:
                    for lot2_sl in config['stop_loss_ranges']['lot2']:
                        for lot3_sl in config['stop_loss_ranges']['lot3']:
                            # 確保停損遞增約束
                            if lot1_sl <= lot2_sl <= lot3_sl:
                                combination = {
                                    'time_interval': f"{time_interval[0]}-{time_interval[1]}",
                                    'lot1_stop_loss': lot1_sl,
                                    'lot2_stop_loss': lot2_sl,
                                    'lot3_stop_loss': lot3_sl,
                                    'take_profit_mode': 'range_boundary',
                                    'experiment_id': f"{time_interval[0]}{time_interval[1]}_L1SL{lot1_sl}_L2SL{lot2_sl}_L3SL{lot3_sl}_RangeBoundary"
                                }
                                combinations.append(combination)
        elif individual_tp:
            # 每口獨立停利設定
            tp_ranges = config['take_profit_ranges']['individual']
            for time_interval in config['time_intervals']:
                for lot1_sl in config['stop_loss_ranges']['lot1']:
                    for lot2_sl in config['stop_loss_ranges']['lot2']:
                        for lot3_sl in config['stop_loss_ranges']['lot3']:
                            for lot1_tp in tp_ranges['lot1']:
                                for lot2_tp in tp_ranges['lot2']:
                                    for lot3_tp in tp_ranges['lot3']:
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
            # 統一停利設定
            tp_range = config['take_profit_ranges']['unified']
            for time_interval in config['time_intervals']:
                for lot1_sl in config['stop_loss_ranges']['lot1']:
                    for lot2_sl in config['stop_loss_ranges']['lot2']:
                        for lot3_sl in config['stop_loss_ranges']['lot3']:
                            for take_profit in tp_range:
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
            'fixed_stop_mode': True,
            'individual_take_profit_enabled': True,
            'lot_settings': {},
            'filters': {
                'range_filter': {'enabled': False},
                'risk_filter': {'enabled': False},
                'stop_loss_filter': {'enabled': False}
            }
        }
        
        # 根據參數類型設定每口配置
        if params.get('take_profit_mode') == 'range_boundary':
            # 區間邊緣停利設定 - 不設定 take_profit，使用策略原設計
            config['individual_take_profit_enabled'] = False  # 關閉個別停利
            config['lot_settings'] = {
                'lot1': {
                    'trigger': params['lot1_stop_loss'],
                    'trailing': 0
                    # 不設定 take_profit，讓策略使用區間邊緣停利
                },
                'lot2': {
                    'trigger': params['lot2_stop_loss'],
                    'trailing': 0
                },
                'lot3': {
                    'trigger': params['lot3_stop_loss'],
                    'trailing': 0
                }
            }
        elif 'lot1_take_profit' in params:
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
            # 統一停利設定 - 確保開啟個別停利模式
            config['individual_take_profit_enabled'] = True  # 明確開啟個別停利
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
            logger.info(f"🧪 開始實驗: {params['experiment_id']}")
            
            # 創建配置
            config = self.create_experiment_config(params)
            
            # 調用策略引擎
            result = subprocess.run([
                sys.executable, '../rev_multi_Profit-Funded Risk_多口.py',
                '--start-date', config['start_date'],
                '--end-date', config['end_date'],
                '--gui-mode',
                '--config', json.dumps(config, ensure_ascii=False)
            ], capture_output=True, text=True, timeout=300, encoding='utf-8', errors='replace')
            
            if result.returncode == 0:
                # 解析結果
                mdd, total_pnl, long_pnl, short_pnl = self._parse_strategy_output(result.stderr)

                if mdd is not None and total_pnl is not None:
                    logger.info(f"✅ 實驗 {params['experiment_id']} 完成 - MDD: {mdd}, P&L: {total_pnl}, LONG: {long_pnl}, SHORT: {short_pnl}")

                    # 構建結果
                    result_data = {
                        'experiment_id': params['experiment_id'],
                        'time_interval': params['time_interval'],
                        'lot1_stop_loss': params['lot1_stop_loss'],
                        'lot2_stop_loss': params['lot2_stop_loss'],
                        'lot3_stop_loss': params['lot3_stop_loss'],
                        'mdd': mdd,
                        'total_pnl': total_pnl,
                        'long_pnl': long_pnl if long_pnl is not None else 0.0,
                        'short_pnl': short_pnl if short_pnl is not None else 0.0,
                        'risk_adjusted_return': abs(total_pnl / mdd) if mdd != 0 else 0
                    }
                    
                    # 添加停利信息
                    if 'lot1_take_profit' in params:
                        result_data.update({
                            'lot1_take_profit': params['lot1_take_profit'],
                            'lot2_take_profit': params['lot2_take_profit'],
                            'lot3_take_profit': params['lot3_take_profit']
                        })
                    elif params.get('take_profit_mode') == 'range_boundary':
                        result_data['take_profit_mode'] = 'range_boundary'
                    else:
                        result_data['take_profit'] = params['take_profit']
                    
                    return result_data
                else:
                    logger.error(f"❌ 實驗 {params['experiment_id']} 結果解析失敗")
                    return None
            else:
                logger.error(f"❌ 實驗 {params['experiment_id']} 執行失敗: {result.stderr}")
                return None
                
        except Exception as e:
            logger.error(f"❌ 實驗 {params['experiment_id']} 異常: {str(e)}")
            return None
    
    def _parse_strategy_output(self, stderr_output):
        """解析策略引擎輸出"""
        try:
            lines = stderr_output.strip().split('\n')

            # 提取總損益 - 修正解析邏輯
            total_pnl = None
            long_pnl = None
            short_pnl = None

            for line in lines:
                if '總損益(' in line and '):' in line:
                    # 格式: 總損益(3口): -17.00
                    try:
                        parts = line.split('總損益(')
                        if len(parts) > 1:
                            pnl_part = parts[1].split('):')
                            if len(pnl_part) > 1:
                                pnl_str = pnl_part[1].strip()
                                total_pnl = float(pnl_str)
                    except:
                        continue

            # 從 JSON 結果中提取 LONG/SHORT PNL（如果有的話）
            # 尋找 JSON 格式的結果輸出
            for line in lines:
                if line.strip().startswith('{') and 'long_pnl' in line:
                    try:
                        import json
                        result_data = json.loads(line.strip())
                        if 'long_pnl' in result_data:
                            long_pnl = float(result_data['long_pnl'])
                        if 'short_pnl' in result_data:
                            short_pnl = float(result_data['short_pnl'])
                        if 'total_pnl' in result_data and total_pnl is None:
                            total_pnl = float(result_data['total_pnl'])
                        break
                    except:
                        continue

            # 計算 MDD
            mdd = self._calculate_mdd_from_logs(stderr_output)

            return mdd, total_pnl, long_pnl, short_pnl

        except Exception as e:
            logger.error(f"解析輸出時發生錯誤: {str(e)}")
            return None, None, None, None
    
    def _calculate_mdd_from_logs(self, stderr_output):
        """從交易日誌計算 MDD"""
        try:
            lines = stderr_output.strip().split('\n')

            current_pnl = 0
            peak_pnl = 0
            max_dd = 0

            for line in lines:
                # 修正損益解析邏輯 - 格式: 損益: +23 或 損益: -15
                if '損益:' in line:
                    try:
                        parts = line.split('損益:')
                        if len(parts) > 1:
                            pnl_str = parts[1].strip()
                            # 移除可能的額外文字，只保留數字部分
                            pnl_str = pnl_str.split()[0] if pnl_str.split() else pnl_str

                            # 處理 +23 或 -15 格式
                            if pnl_str.startswith(('+', '-')):
                                trade_pnl = float(pnl_str)
                            else:
                                trade_pnl = float(pnl_str.replace(',', ''))

                            current_pnl += trade_pnl

                            # 更新峰值
                            if current_pnl > peak_pnl:
                                peak_pnl = current_pnl

                            # 計算回撤
                            drawdown = peak_pnl - current_pnl
                            if drawdown > max_dd:
                                max_dd = drawdown
                    except Exception as parse_error:
                        logger.debug(f"解析損益行失敗: {line.strip()}, 錯誤: {parse_error}")
                        continue

            return -max_dd if max_dd > 0 else 0

        except Exception as e:
            logger.error(f"計算 MDD 時發生錯誤: {str(e)}")
            return 0

    def run_optimization(self, max_workers=2, sample_size=None, individual_tp=False):
        """執行 MDD 優化"""
        import pandas as pd

        logger.info("🚀 開始增強版 MDD 最小化參數優化...")

        # 檢查配置模式
        if self.config.get('analysis_mode') == 'per_time_interval':
            logger.info("🎯 配置模式: 時間區間分析 (固定停利 vs 區間邊緣停利)")
        elif self.config.get('take_profit_mode') == 'range_boundary':
            logger.info("🎯 配置模式: 區間邊緣停利")
        elif individual_tp:
            logger.info("🎯 配置模式: 每口獨立停利")
        else:
            logger.info("🎯 配置模式: 統一停利")

        # 生成實驗組合
        combinations = self.generate_experiment_combinations(individual_tp=individual_tp)

        # 如果指定樣本數量，隨機選擇
        if sample_size and sample_size < len(combinations):
            import random
            random.seed(42)
            combinations = random.sample(combinations, sample_size)
            logger.info(f"🎯 隨機選擇 {sample_size} 個實驗進行測試")

        # 並行執行實驗
        results = []
        with ProcessPoolExecutor(max_workers=max_workers) as executor:
            futures = [executor.submit(self.run_single_experiment, params) for params in combinations]

            for i, future in enumerate(futures):
                try:
                    result = future.result(timeout=600)
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
            filename = f"enhanced_mdd_results_{self.config_name}_{timestamp}.csv"
            filepath = self.results_dir / filename
            df.to_csv(filepath, index=False, encoding='utf-8-sig')
            logger.info(f"💾 結果已保存到: {filepath}")

            # 分析結果
            self._analyze_results(df)
            return df
        else:
            logger.error("❌ 沒有有效結果")
            return None

    def _analyze_results(self, df):
        """分析結果"""
        import pandas as pd

        logger.info("\n" + "="*60)
        logger.info("📊 增強版 MDD 最小化分析結果")
        logger.info("="*60)
        logger.info(f"總實驗數: {len(df)}")
        logger.info(f"有效結果數: {len(df[df['mdd'] != 0])}")

        # MDD 最小 TOP 10
        top_mdd = df.nlargest(10, 'mdd')  # MDD 是負數，所以用 nlargest
        logger.info("\n🏆 MDD最小 TOP 10:")
        logger.info("-" * 80)
        for i, row in top_mdd.iterrows():
            long_pnl = row.get('long_pnl', 0)
            short_pnl = row.get('short_pnl', 0)
            if 'lot1_take_profit' in row and pd.notna(row['lot1_take_profit']):
                logger.info(f"{len(top_mdd) - list(top_mdd.index).index(i):2.0f}. MDD:{row['mdd']:8.2f} | "
                           f"總P&L:{row['total_pnl']:8.2f} | LONG:{long_pnl:8.2f} | SHORT:{short_pnl:8.2f} | "
                           f"L1SL:{int(row['lot1_stop_loss']):2d}TP:{int(row['lot1_take_profit']):2d} "
                           f"L2SL:{int(row['lot2_stop_loss']):2d}TP:{int(row['lot2_take_profit']):2d} "
                           f"L3SL:{int(row['lot3_stop_loss']):2d}TP:{int(row['lot3_take_profit']):2d} | "
                           f"{row['time_interval']}")
            elif 'take_profit_mode' in row and row['take_profit_mode'] == 'range_boundary':
                logger.info(f"{len(top_mdd) - list(top_mdd.index).index(i):2.0f}. MDD:{row['mdd']:8.2f} | "
                           f"總P&L:{row['total_pnl']:8.2f} | LONG:{long_pnl:8.2f} | SHORT:{short_pnl:8.2f} | "
                           f"L1SL:{int(row['lot1_stop_loss']):2d} L2SL:{int(row['lot2_stop_loss']):2d} L3SL:{int(row['lot3_stop_loss']):2d} | "
                           f"區間邊緣停利 | {row['time_interval']}")
            else:
                take_profit_val = row.get('take_profit', 0)
                # 處理 NaN 值
                if pd.isna(take_profit_val):
                    take_profit_val = 0
                logger.info(f"{len(top_mdd) - list(top_mdd.index).index(i):2.0f}. MDD:{row['mdd']:8.2f} | "
                           f"總P&L:{row['total_pnl']:8.2f} | LONG:{long_pnl:8.2f} | SHORT:{short_pnl:8.2f} | "
                           f"L1SL:{int(row['lot1_stop_loss']):2d} L2SL:{int(row['lot2_stop_loss']):2d} L3SL:{int(row['lot3_stop_loss']):2d} | "
                           f"TP:{int(take_profit_val):2d} | {row['time_interval']}")

        # 風險調整收益 TOP 10
        top_risk_adj = df.nlargest(10, 'risk_adjusted_return')
        logger.info("\n💎 風險調整收益 TOP 10 (總收益/|MDD|):")
        logger.info("-" * 80)
        for i, row in top_risk_adj.iterrows():
            long_pnl = row.get('long_pnl', 0)
            short_pnl = row.get('short_pnl', 0)
            if 'lot1_take_profit' in row and pd.notna(row['lot1_take_profit']):
                logger.info(f"{len(top_risk_adj) - list(top_risk_adj.index).index(i):2.0f}. 風險調整收益:{row['risk_adjusted_return']:6.2f} | "
                           f"MDD:{row['mdd']:8.2f} | 總P&L:{row['total_pnl']:8.2f} | LONG:{long_pnl:8.2f} | SHORT:{short_pnl:8.2f} | "
                           f"L1SL:{int(row['lot1_stop_loss']):2d}TP:{int(row['lot1_take_profit']):2d} "
                           f"L2SL:{int(row['lot2_stop_loss']):2d}TP:{int(row['lot2_take_profit']):2d} "
                           f"L3SL:{int(row['lot3_stop_loss']):2d}TP:{int(row['lot3_take_profit']):2d}")
            elif 'take_profit_mode' in row and row['take_profit_mode'] == 'range_boundary':
                logger.info(f"{len(top_risk_adj) - list(top_risk_adj.index).index(i):2.0f}. 風險調整收益:{row['risk_adjusted_return']:6.2f} | "
                           f"MDD:{row['mdd']:8.2f} | 總P&L:{row['total_pnl']:8.2f} | LONG:{long_pnl:8.2f} | SHORT:{short_pnl:8.2f} | "
                           f"L1SL:{int(row['lot1_stop_loss']):2d} L2SL:{int(row['lot2_stop_loss']):2d} L3SL:{int(row['lot3_stop_loss']):2d} | "
                           f"區間邊緣停利")
            else:
                take_profit_val = row.get('take_profit', 0)
                # 處理 NaN 值
                if pd.isna(take_profit_val):
                    take_profit_val = 0
                logger.info(f"{len(top_risk_adj) - list(top_risk_adj.index).index(i):2.0f}. 風險調整收益:{row['risk_adjusted_return']:6.2f} | "
                           f"MDD:{row['mdd']:8.2f} | 總P&L:{row['total_pnl']:8.2f} | LONG:{long_pnl:8.2f} | SHORT:{short_pnl:8.2f} | "
                           f"L1SL:{int(row['lot1_stop_loss']):2d} L2SL:{int(row['lot2_stop_loss']):2d} L3SL:{int(row['lot3_stop_loss']):2d} | "
                           f"TP:{int(take_profit_val):2d}")

        # 如果是時間區間分析模式，生成特殊報告
        if self.config.get('analysis_mode') == 'per_time_interval':
            self._generate_time_interval_analysis_report(df)

        logger.info("="*60)
        logger.info("🎊 增強版 MDD 優化完成！")

    def _generate_time_interval_analysis_report(self, df):
        """生成時間區間分析報告"""
        import pandas as pd

        logger.info("\n" + "="*80)
        logger.info("📊 時間區間 MDD 分析結果")
        logger.info("="*80)

        # 獲取所有時間區間
        time_intervals = df['time_interval'].unique()

        daily_recommendations = []

        for interval in sorted(time_intervals):
            logger.info(f"\n🕙 {interval} 最佳配置:")
            logger.info("-" * 60)

            # 篩選該時間區間的結果
            interval_df = df[df['time_interval'] == interval]

            # 分別找固定停利和區間邊緣停利的最佳結果
            # 檢查是否有 take_profit_mode 欄位
            if 'take_profit_mode' in interval_df.columns:
                fixed_tp_df = interval_df[interval_df['take_profit_mode'] != 'range_boundary']
                boundary_df = interval_df[interval_df['take_profit_mode'] == 'range_boundary']
            else:
                # 如果沒有 take_profit_mode 欄位，根據其他欄位判斷
                boundary_df = interval_df[interval_df['experiment_id'].str.contains('RangeBoundary', na=False)]
                fixed_tp_df = interval_df[~interval_df['experiment_id'].str.contains('RangeBoundary', na=False)]

            best_fixed = None
            best_boundary = None

            if not fixed_tp_df.empty:
                best_fixed = fixed_tp_df.loc[fixed_tp_df['mdd'].idxmax()]  # MDD最大(最小負值)
                # 檢查是統一停利還是各口獨立停利
                if 'take_profit' in best_fixed and pd.notna(best_fixed['take_profit']):
                    tp_info = f"TP:{int(best_fixed['take_profit']):2d}"
                elif 'lot1_take_profit' in best_fixed:
                    tp_info = f"L1TP:{int(best_fixed['lot1_take_profit']):2d} L2TP:{int(best_fixed['lot2_take_profit']):2d} L3TP:{int(best_fixed['lot3_take_profit']):2d}"
                else:
                    tp_info = "停利配置未知"

                logger.info(f"   固定停利: MDD:{best_fixed['mdd']:8.2f} | P&L:{best_fixed['total_pnl']:8.2f} | "
                           f"L1SL:{int(best_fixed['lot1_stop_loss']):2d} L2SL:{int(best_fixed['lot2_stop_loss']):2d} "
                           f"L3SL:{int(best_fixed['lot3_stop_loss']):2d} | {tp_info}")

            if not boundary_df.empty:
                best_boundary = boundary_df.loc[boundary_df['mdd'].idxmax()]  # MDD最大(最小負值)
                logger.info(f"   區間邊緣: MDD:{best_boundary['mdd']:8.2f} | P&L:{best_boundary['total_pnl']:8.2f} | "
                           f"L1SL:{int(best_boundary['lot1_stop_loss']):2d} L2SL:{int(best_boundary['lot2_stop_loss']):2d} "
                           f"L3SL:{int(best_boundary['lot3_stop_loss']):2d} | 區間邊緣停利")

            # 決定推薦配置
            if best_fixed is not None and best_boundary is not None:
                if best_boundary['mdd'] > best_fixed['mdd']:  # 區間邊緣MDD更小
                    recommended = best_boundary
                    mode = "區間邊緣停利"
                    logger.info(f"   ⭐ 推薦: 區間邊緣停利 (MDD更小: {best_boundary['mdd']:.2f} vs {best_fixed['mdd']:.2f})")
                else:
                    recommended = best_fixed
                    if 'take_profit' in best_fixed and pd.notna(best_fixed['take_profit']):
                        mode = f"固定停利 TP:{int(best_fixed['take_profit']):2d}"
                    else:
                        mode = "固定停利 (各口獨立)"
                    logger.info(f"   ⭐ 推薦: 固定停利 (MDD更小: {best_fixed['mdd']:.2f} vs {best_boundary['mdd']:.2f})")
            elif best_boundary is not None:
                recommended = best_boundary
                mode = "區間邊緣停利"
                logger.info(f"   ⭐ 推薦: 區間邊緣停利 (唯一選項)")
            elif best_fixed is not None:
                recommended = best_fixed
                if 'take_profit' in best_fixed and pd.notna(best_fixed['take_profit']):
                    mode = f"固定停利 TP:{int(best_fixed['take_profit']):2d}"
                else:
                    mode = "固定停利 (各口獨立)"
                logger.info(f"   ⭐ 推薦: 固定停利 (唯一選項)")
            else:
                logger.info(f"   ❌ 該時間區間無有效結果")
                continue

            # 添加到每日建議
            daily_recommendations.append({
                'time_interval': interval,
                'mode': mode,
                'lot1_sl': recommended['lot1_stop_loss'],
                'lot2_sl': recommended['lot2_stop_loss'],
                'lot3_sl': recommended['lot3_stop_loss'],
                'mdd': recommended['mdd'],
                'pnl': recommended['total_pnl']
            })

        # 生成每日交易配置建議
        logger.info(f"\n📋 一日交易配置建議:")
        logger.info("="*80)
        for rec in daily_recommendations:
            logger.info(f"{rec['time_interval']}: {rec['mode']}, "
                       f"L1SL:{rec['lot1_sl']:2d} L2SL:{rec['lot2_sl']:2d} L3SL:{rec['lot3_sl']:2d} "
                       f"(MDD:{rec['mdd']:6.2f}, P&L:{rec['pnl']:7.2f})")

        # 計算總體統計
        total_mdd = sum(rec['mdd'] for rec in daily_recommendations)
        total_pnl = sum(rec['pnl'] for rec in daily_recommendations)
        logger.info(f"\n📈 預期每日總計: MDD:{total_mdd:8.2f} | P&L:{total_pnl:8.2f}")

        # LONG 部位 PNL TOP 10
        if 'long_pnl' in df.columns:
            top_long_pnl = df.nlargest(10, 'long_pnl')
            logger.info("\n🟢 LONG 部位 PNL TOP 10:")
            logger.info("-" * 80)
            for i, row in top_long_pnl.iterrows():
                long_pnl = row.get('long_pnl', 0)
                short_pnl = row.get('short_pnl', 0)
                if 'take_profit_mode' in row and row['take_profit_mode'] == 'range_boundary':
                    logger.info(f"{len(top_long_pnl) - list(top_long_pnl.index).index(i):2.0f}. LONG:{long_pnl:8.2f} | "
                               f"總P&L:{row['total_pnl']:8.2f} | SHORT:{short_pnl:8.2f} | "
                               f"L1SL:{int(row['lot1_stop_loss']):2d} L2SL:{int(row['lot2_stop_loss']):2d} L3SL:{int(row['lot3_stop_loss']):2d} | "
                               f"區間邊緣停利 | {row['time_interval']}")
                else:
                    take_profit_val = row.get('take_profit', 0)
                    # 處理 NaN 值
                    if pd.isna(take_profit_val):
                        take_profit_val = 0
                    logger.info(f"{len(top_long_pnl) - list(top_long_pnl.index).index(i):2.0f}. LONG:{long_pnl:8.2f} | "
                               f"總P&L:{row['total_pnl']:8.2f} | SHORT:{short_pnl:8.2f} | "
                               f"L1SL:{int(row['lot1_stop_loss']):2d} L2SL:{int(row['lot2_stop_loss']):2d} L3SL:{int(row['lot3_stop_loss']):2d} | "
                               f"TP:{int(take_profit_val):2d} | {row['time_interval']}")

        # SHORT 部位 PNL TOP 10
        if 'short_pnl' in df.columns:
            top_short_pnl = df.nlargest(10, 'short_pnl')
            logger.info("\n🔴 SHORT 部位 PNL TOP 10:")
            logger.info("-" * 80)
            for i, row in top_short_pnl.iterrows():
                long_pnl = row.get('long_pnl', 0)
                short_pnl = row.get('short_pnl', 0)
                if 'take_profit_mode' in row and row['take_profit_mode'] == 'range_boundary':
                    logger.info(f"{len(top_short_pnl) - list(top_short_pnl.index).index(i):2.0f}. SHORT:{short_pnl:8.2f} | "
                               f"總P&L:{row['total_pnl']:8.2f} | LONG:{long_pnl:8.2f} | "
                               f"L1SL:{int(row['lot1_stop_loss']):2d} L2SL:{int(row['lot2_stop_loss']):2d} L3SL:{int(row['lot3_stop_loss']):2d} | "
                               f"區間邊緣停利 | {row['time_interval']}")
                else:
                    take_profit_val = row.get('take_profit', 0)
                    # 處理 NaN 值
                    if pd.isna(take_profit_val):
                        take_profit_val = 0
                    logger.info(f"{len(top_short_pnl) - list(top_short_pnl.index).index(i):2.0f}. SHORT:{short_pnl:8.2f} | "
                               f"總P&L:{row['total_pnl']:8.2f} | LONG:{long_pnl:8.2f} | "
                               f"L1SL:{int(row['lot1_stop_loss']):2d} L2SL:{int(row['lot2_stop_loss']):2d} L3SL:{int(row['lot3_stop_loss']):2d} | "
                               f"TP:{int(take_profit_val):2d} | {row['time_interval']}")

def main():
    """主函數"""
    import argparse

    parser = argparse.ArgumentParser(description='增強版 MDD 最小化參數優化器')
    parser.add_argument('--config', choices=['quick', 'detailed', 'focused', 'time_focus', 'user_custom', 'range_boundary', 'time_interval_analysis'],
                       default='quick', help='搜索配置類型')
    parser.add_argument('--sample-size', type=int, help='樣本數量 (用於快速測試)')
    parser.add_argument('--max-workers', type=int, default=2, help='並行進程數')
    parser.add_argument('--individual-tp', action='store_true', help='使用每口獨立停利設定')
    parser.add_argument('--show-configs', action='store_true', help='顯示所有配置摘要')

    args = parser.parse_args()

    if args.show_configs:
        MDDSearchConfig.print_config_summary()
        return

    optimizer = EnhancedMDDOptimizer(config_name=args.config)

    if args.sample_size:
        logger.info(f"⚡ 快速測試模式 - 樣本數: {args.sample_size}")
    else:
        logger.info("🎯 完整優化模式")

    results = optimizer.run_optimization(
        max_workers=args.max_workers,
        sample_size=args.sample_size,
        individual_tp=args.individual_tp
    )

if __name__ == "__main__":
    main()
