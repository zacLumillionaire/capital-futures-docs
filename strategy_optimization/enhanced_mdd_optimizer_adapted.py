#!/usr/bin/env python3
"""
增強版 MDD 優化器 - 適配版本
專為 strategy_optimization 項目使用
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
from mdd_search_config_adapted import MDDSearchConfig
from time_interval_config import TimeIntervalConfig

# 設定日誌
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('data/processed/enhanced_mdd_optimization.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class EnhancedMDDOptimizer:
    """增強版 MDD 優化器 - 適配版本"""
    
    def __init__(self, config_name='quick'):
        self.results_dir = Path("data/processed")
        self.results_dir.mkdir(exist_ok=True)
        
        # 載入搜索配置 - 優先使用 TimeIntervalConfig
        try:
            time_config = TimeIntervalConfig()
            self.config = time_config.get_config(config_name)
            self.config_name = config_name
            logger.info(f"✅ 使用 TimeIntervalConfig 載入配置: {config_name}")
        except:
            # 回退到原始配置
            self.config = MDDSearchConfig.get_config_by_name(config_name)
            self.config_name = config_name
            logger.info(f"⚠️ 回退到 MDDSearchConfig 載入配置: {config_name}")
        
        # 回測期間 - 可以通過參數調整
        self.start_date = "2024-11-04"
        self.end_date = "2025-06-27"
        
        logger.info(f"🎯 增強版 MDD 優化器初始化完成 - 配置: {config_name.upper()}")
        self._log_config_summary()
    
    def set_date_range(self, start_date: str, end_date: str):
        """設定回測日期範圍"""
        self.start_date = start_date
        self.end_date = end_date
        logger.info(f"📅 設定回測期間: {start_date} 到 {end_date}")
    
    def _log_config_summary(self):
        """記錄配置摘要"""
        config = self.config
        logger.info(f"   第1口停損範圍: {config['stop_loss_ranges']['lot1']}")
        logger.info(f"   第2口停損範圍: {config['stop_loss_ranges']['lot2']}")
        logger.info(f"   第3口停損範圍: {config['stop_loss_ranges']['lot3']}")
        
        if 'time_intervals' in config:
            logger.info(f"   時間區間數量: {len(config['time_intervals'])}")
            for i, interval in enumerate(config['time_intervals'][:3]):  # 只顯示前3個
                logger.info(f"     區間{i+1}: {interval[0]}-{interval[1]}")
            if len(config['time_intervals']) > 3:
                logger.info(f"     ... 還有 {len(config['time_intervals'])-3} 個區間")
        
        if 'estimated_combinations' in config:
            total_combinations = 0
            for mode, count in config['estimated_combinations'].items():
                if isinstance(count, int):
                    total_combinations += count
                    logger.info(f"   {mode} 模式預估組合: {count:,}")
            if total_combinations > 0:
                logger.info(f"   總預估組合數: {total_combinations:,}")
    
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
                                # 獲取停損模式設定
                                stop_loss_modes = config.get('stop_loss_modes', {'fixed_points': True})

                                # 為每種停損模式生成組合
                                for stop_loss_mode in ['range_boundary', 'fixed_points']:
                                    if stop_loss_modes.get(stop_loss_mode, False):
                                        # 1. 移動停利模式（使用預設觸發點配置）
                                        if config.get('trailing_stop_config'):
                                            combination_trailing = {
                                                'time_interval': f"{time_interval[0]}-{time_interval[1]}",
                                                'lot1_stop_loss': lot1_sl,
                                                'lot2_stop_loss': lot2_sl,
                                                'lot3_stop_loss': lot3_sl,
                                                'take_profit_mode': 'trailing_stop',
                                                'stop_loss_mode': stop_loss_mode,
                                                'trailing_config': config['trailing_stop_config'],
                                                'experiment_id': f"{time_interval[0]}{time_interval[1]}_L1SL{lot1_sl}_L2SL{lot2_sl}_L3SL{lot3_sl}_Trailing_{stop_loss_mode}"
                                            }
                                            combinations.append(combination_trailing)

                                        # 2. 統一停利設定
                                        for take_profit in config['take_profit_ranges']['unified']:
                                            combination_unified = {
                                                'time_interval': f"{time_interval[0]}-{time_interval[1]}",
                                                'lot1_stop_loss': lot1_sl,
                                                'lot2_stop_loss': lot2_sl,
                                                'lot3_stop_loss': lot3_sl,
                                                'take_profit': take_profit,
                                                'stop_loss_mode': stop_loss_mode,
                                                'experiment_id': f"{time_interval[0]}{time_interval[1]}_L1SL{lot1_sl}_L2SL{lot2_sl}_L3SL{lot3_sl}_TP{take_profit}_{stop_loss_mode}"
                                            }
                                            combinations.append(combination_unified)

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
                                                        'stop_loss_mode': stop_loss_mode,
                                                        'experiment_id': f"{time_interval[0]}{time_interval[1]}_L1SL{lot1_sl}TP{lot1_tp}_L2SL{lot2_sl}TP{lot2_tp}_L3SL{lot3_sl}TP{lot3_tp}_{stop_loss_mode}"
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
            # 各口獨立停利設定
            for time_interval in config['time_intervals']:
                for lot1_sl in config['stop_loss_ranges']['lot1']:
                    for lot2_sl in config['stop_loss_ranges']['lot2']:
                        for lot3_sl in config['stop_loss_ranges']['lot3']:
                            for lot1_tp in config['take_profit_ranges']['individual']['lot1']:
                                for lot2_tp in config['take_profit_ranges']['individual']['lot2']:
                                    for lot3_tp in config['take_profit_ranges']['individual']['lot3']:
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
        """創建實驗配置 - 支援移動停利功能和停損模式"""
        config = {
            'start_date': self.start_date,
            'end_date': self.end_date,
            'range_start_time': params['time_interval'].split('-')[0],
            'range_end_time': params['time_interval'].split('-')[1],
            'trade_lots': 3,
            'lot_settings': {},
            'filters': {
                'range_filter': {'enabled': False},
                'risk_filter': {'enabled': False},
                'stop_loss_filter': {'enabled': True}  # 啟用停損濾網來設定停損模式
            }
        }

        # 設定停損模式
        stop_loss_mode = params.get('stop_loss_mode', 'fixed_points')
        if stop_loss_mode == 'range_boundary':
            config['filters']['stop_loss_filter'].update({
                'stop_loss_type': 'range_boundary'
            })
        else:
            config['filters']['stop_loss_filter'].update({
                'stop_loss_type': 'fixed_points',
                'fixed_stop_loss_points': params['lot1_stop_loss']  # 使用第1口停損作為基準
            })

        # 設定停損（初始停損點）
        config['lot_settings']['lot1'] = {'stop_loss': params['lot1_stop_loss']}
        config['lot_settings']['lot2'] = {'stop_loss': params['lot2_stop_loss']}
        config['lot_settings']['lot3'] = {'stop_loss': params['lot3_stop_loss']}

        # 設定停利 - 根據模式決定使用移動停利或固定停利
        if 'take_profit_mode' in params and params['take_profit_mode'] == 'trailing_stop':
            # 移動停利模式 - 使用配置的觸發點和回撤%
            config['take_profit_mode'] = 'trailing_stop'
            trailing_config = params.get('trailing_config', {})

            # 設置移動停利參數（使用您驗證的配置）
            config['lot_settings']['lot1'].update({
                'trigger': trailing_config.get('lot1', {}).get('trigger', 15),      # 觸發點位
                'trailing': trailing_config.get('lot1', {}).get('pullback', 10),    # 回撤百分比
                'protection': 1.0   # 保護倍數
            })
            config['lot_settings']['lot2'].update({
                'trigger': trailing_config.get('lot2', {}).get('trigger', 40),      # 觸發點位
                'trailing': trailing_config.get('lot2', {}).get('pullback', 10),    # 回撤百分比
                'protection': 2.0   # 保護倍數 (您的驗證配置)
            })
            config['lot_settings']['lot3'].update({
                'trigger': trailing_config.get('lot3', {}).get('trigger', 41),      # 觸發點位
                'trailing': trailing_config.get('lot3', {}).get('pullback', 20),    # 回撤百分比
                'protection': 2.0   # 保護倍數 (您的驗證配置)
            })
        elif 'lot1_take_profit' in params:
            # 各口獨立停利 - 使用移動停利，但以停利點位作為觸發點
            config['lot_settings']['lot1'].update({
                'trigger': params['lot1_take_profit'],  # 使用停利點位作為觸發點
                'trailing': 20,     # 固定20%回撤
                'protection': 1.0
            })
            config['lot_settings']['lot2'].update({
                'trigger': params['lot2_take_profit'],
                'trailing': 20,
                'protection': 2.0
            })
            config['lot_settings']['lot3'].update({
                'trigger': params['lot3_take_profit'],
                'trailing': 20,
                'protection': 2.0
            })
        elif 'take_profit' in params:
            # 統一停利 - 使用移動停利，但各口使用不同觸發點
            unified_tp = params['take_profit']
            config['lot_settings']['lot1'].update({
                'trigger': max(15, unified_tp - 20),  # 第1口較早觸發
                'trailing': 20,
                'protection': 1.0
            })
            config['lot_settings']['lot2'].update({
                'trigger': unified_tp,                # 第2口標準觸發
                'trailing': 20,
                'protection': 2.0
            })
            config['lot_settings']['lot3'].update({
                'trigger': unified_tp + 15,           # 第3口較晚觸發
                'trailing': 20,
                'protection': 2.0
            })

        return config

    def _convert_to_gui_config(self, config):
        """將實驗配置轉換為GUI配置格式"""
        gui_config = {
            'start_date': config['start_date'],
            'end_date': config['end_date'],
            'range_start_time': config['range_start_time'],
            'range_end_time': config['range_end_time'],
            'trade_lots': config['trade_lots'],
            'lot_settings': config['lot_settings'],
            'filters': config['filters']
        }

        # 添加停利模式
        if 'take_profit_mode' in config:
            gui_config['take_profit_mode'] = config['take_profit_mode']
        if 'unified_take_profit' in config:
            gui_config['unified_take_profit'] = config['unified_take_profit']

        return gui_config

    def _parse_backtest_output(self, stdout):
        """解析回測輸出結果"""
        # 這是一個簡化的解析器，實際需要根據回測輸出格式調整
        # 暫時返回模擬結果
        import re

        # 嘗試從輸出中提取統計數據
        total_pnl = 0
        mdd = 0
        win_rate = 0
        total_trades = 0

        # 使用正則表達式提取關鍵數據 - 修復格式匹配
        pnl_match = re.search(r'總損益\([^)]+\)[：:]\s*([+-]?\d+\.?\d*)', stdout)
        if pnl_match:
            total_pnl = float(pnl_match.group(1))

        mdd_match = re.search(r'最大回撤[：:]\s*([+-]?\d+\.?\d*)', stdout)
        if mdd_match:
            mdd = float(mdd_match.group(1))

        win_rate_match = re.search(r'勝率[：:]\s*(\d+\.?\d*)%?', stdout)
        if win_rate_match:
            win_rate = float(win_rate_match.group(1))

        trades_match = re.search(r'總交易次數[：:]\s*(\d+)', stdout)
        if trades_match:
            total_trades = int(trades_match.group(1))

        return {
            'statistics': {
                'total_pnl': total_pnl,
                'max_drawdown': mdd,
                'win_rate': win_rate,
                'total_trades': total_trades,
                'sharpe_ratio': 0,  # 需要從輸出中提取
                'profit_factor': 0,  # 需要從輸出中提取
                'avg_win': 0,
                'avg_loss': 0,
                'max_consecutive_losses': 0
            }
        }

    def run_single_experiment(self, params):
        """執行單一實驗"""
        try:
            # 創建實驗配置
            config = self.create_experiment_config(params)

            # 調用策略回測 - 使用GUI模式來支援移動停利功能
            import subprocess
            import json
            import tempfile
            import os

            # 將配置轉換為GUI格式
            gui_config = self._convert_to_gui_config(config)

            # 創建臨時文件來傳遞配置
            with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
                json.dump(gui_config, f, ensure_ascii=False, indent=2)
                config_file = f.name

            try:
                # 使用GUI模式執行回測
                cmd = [
                    'python', 'multi_Profit-Funded Risk_多口.py',
                    '--gui-mode',
                    '--config', json.dumps(gui_config, ensure_ascii=False)
                ]

                result = subprocess.run(cmd, capture_output=True, text=True, cwd=os.getcwd())

                if result.returncode == 0:
                    # 解析回測結果 - 策略輸出在stderr中（因為使用了日志記錄器）
                    output_to_parse = result.stderr if result.stderr else result.stdout
                    parsed_result = self._parse_backtest_output(output_to_parse)
                    if parsed_result and 'statistics' in parsed_result:
                        stats = parsed_result['statistics']
                        return {
                            'experiment_id': params['experiment_id'],
                            'time_interval': params['time_interval'],
                            'lot1_stop_loss': params['lot1_stop_loss'],
                            'lot2_stop_loss': params['lot2_stop_loss'],
                            'lot3_stop_loss': params['lot3_stop_loss'],
                            'take_profit': params.get('take_profit'),
                            'lot1_take_profit': params.get('lot1_take_profit'),
                            'lot2_take_profit': params.get('lot2_take_profit'),
                            'lot3_take_profit': params.get('lot3_take_profit'),
                            'take_profit_mode': params.get('take_profit_mode'),
                            'total_pnl': stats.get('total_pnl', 0),
                            'mdd': stats.get('max_drawdown', 0),
                            'win_rate': stats.get('win_rate', 0),
                            'total_trades': stats.get('total_trades', 0),
                            'sharpe_ratio': stats.get('sharpe_ratio', 0),
                            'profit_factor': stats.get('profit_factor', 0),
                            'avg_win': stats.get('avg_win', 0),
                            'avg_loss': stats.get('avg_loss', 0),
                            'max_consecutive_losses': stats.get('max_consecutive_losses', 0),
                            'status': 'success'
                        }
                    else:
                        logger.error(f"無法解析回測結果 - 實驗: {params['experiment_id']}")
                        logger.error(f"stdout 前500字符: {result.stdout[:500]}")
                        # 返回失敗結果而不是None
                        return {
                            'experiment_id': params['experiment_id'],
                            'time_interval': params['time_interval'],
                            'lot1_stop_loss': params['lot1_stop_loss'],
                            'lot2_stop_loss': params['lot2_stop_loss'],
                            'lot3_stop_loss': params['lot3_stop_loss'],
                            'take_profit': params.get('take_profit'),
                            'lot1_take_profit': params.get('lot1_take_profit'),
                            'lot2_take_profit': params.get('lot2_take_profit'),
                            'lot3_take_profit': params.get('lot3_take_profit'),
                            'take_profit_mode': params.get('take_profit_mode'),
                            'total_pnl': 0,
                            'mdd': 0,
                            'win_rate': 0,
                            'total_trades': 0,
                            'sharpe_ratio': 0,
                            'profit_factor': 0,
                            'avg_win': 0,
                            'avg_loss': 0,
                            'max_consecutive_losses': 0,
                            'status': 'parse_failed'
                        }
                else:
                    logger.error(f"回測執行失敗 - 實驗: {params['experiment_id']}")
                    logger.error(f"返回碼: {result.returncode}")
                    logger.error(f"stderr: {result.stderr}")
                    # 返回失敗結果而不是None
                    return {
                        'experiment_id': params['experiment_id'],
                        'time_interval': params['time_interval'],
                        'lot1_stop_loss': params['lot1_stop_loss'],
                        'lot2_stop_loss': params['lot2_stop_loss'],
                        'lot3_stop_loss': params['lot3_stop_loss'],
                        'take_profit': params.get('take_profit'),
                        'lot1_take_profit': params.get('lot1_take_profit'),
                        'lot2_take_profit': params.get('lot2_take_profit'),
                        'lot3_take_profit': params.get('lot3_take_profit'),
                        'take_profit_mode': params.get('take_profit_mode'),
                        'total_pnl': 0,
                        'mdd': 0,
                        'win_rate': 0,
                        'total_trades': 0,
                        'sharpe_ratio': 0,
                        'profit_factor': 0,
                        'avg_win': 0,
                        'avg_loss': 0,
                        'max_consecutive_losses': 0,
                        'status': 'execution_failed'
                    }

            finally:
                # 清理臨時文件
                if os.path.exists(config_file):
                    os.unlink(config_file)

        except Exception as e:
            logger.error(f"❌ 實驗 {params['experiment_id']} 失敗: {e}")
            return {
                'experiment_id': params['experiment_id'],
                'status': 'failed',
                'error': str(e)
            }

    def run_optimization(self, max_workers=2, sample_size=None, individual_tp=False):
        """執行 MDD 優化"""
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

        logger.info(f"📊 總共將執行 {len(combinations)} 個實驗")
        logger.info(f"⚙️  使用 {max_workers} 個並行進程")

        # 執行實驗
        results = []
        start_time = datetime.now()

        if max_workers == 1:
            # 單進程執行
            for i, params in enumerate(combinations):
                logger.info(f"🔄 執行實驗 {i+1}/{len(combinations)}: {params['experiment_id']}")
                result = self.run_single_experiment(params)
                results.append(result)
        else:
            # 多進程執行
            with ProcessPoolExecutor(max_workers=max_workers) as executor:
                future_to_params = {executor.submit(self.run_single_experiment, params): params
                                  for params in combinations}

                for i, future in enumerate(future_to_params):
                    try:
                        result = future.result(timeout=300)  # 5分鐘超時
                        results.append(result)
                        if (i + 1) % 10 == 0:
                            logger.info(f"✅ 完成 {i+1}/{len(combinations)} 個實驗")
                    except Exception as e:
                        params = future_to_params[future]
                        logger.error(f"❌ 實驗 {params['experiment_id']} 失敗: {e}")
                        results.append({
                            'experiment_id': params['experiment_id'],
                            'status': 'failed',
                            'error': str(e)
                        })

        execution_time = (datetime.now() - start_time).total_seconds()
        logger.info(f"⏱️  總執行時間: {execution_time:.1f} 秒")

        # 處理結果
        self._process_results(results)

        return results

    def _process_results(self, results):
        """處理實驗結果"""
        logger.info("📊 開始處理實驗結果...")

        # 過濾成功的結果
        successful_results = [r for r in results if r.get('status') == 'success']
        failed_count = len(results) - len(successful_results)

        if failed_count > 0:
            logger.warning(f"⚠️  {failed_count} 個實驗失敗")

        if not successful_results:
            logger.error("❌ 沒有成功的實驗結果")
            return

        # 轉換為 DataFrame
        df = pd.DataFrame(successful_results)

        # 保存詳細結果
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        results_file = self.results_dir / f"mdd_optimization_results_{timestamp}.csv"
        df.to_csv(results_file, index=False, encoding='utf-8-sig')
        logger.info(f"💾 詳細結果已保存: {results_file}")

        # 分析結果
        self._analyze_results(df)

        # 如果是時間區間分析模式，生成特殊報告
        if self.config.get('analysis_mode') == 'per_time_interval':
            self._generate_time_interval_analysis_report(df)

        logger.info("="*60)
        logger.info("🎊 增強版 MDD 優化完成！")

    def _analyze_results(self, df):
        """分析實驗結果"""
        logger.info("\n" + "="*60)
        logger.info("📈 MDD 優化結果分析")
        logger.info("="*60)

        # 基本統計
        logger.info(f"✅ 成功實驗數量: {len(df)}")
        logger.info(f"📊 平均 MDD: {df['mdd'].mean():.2f}")
        logger.info(f"📊 平均總損益: {df['total_pnl'].mean():.2f}")
        logger.info(f"📊 平均勝率: {df['win_rate'].mean():.2%}")

        # 找出最佳 MDD 結果
        best_mdd_idx = df['mdd'].idxmax()  # MDD 最大值（最小負值）
        best_mdd = df.loc[best_mdd_idx]

        logger.info(f"\n🏆 最佳 MDD 配置:")
        logger.info(f"   實驗ID: {best_mdd['experiment_id']}")
        logger.info(f"   時間區間: {best_mdd['time_interval']}")
        logger.info(f"   MDD: {best_mdd['mdd']:.2f}")
        logger.info(f"   總損益: {best_mdd['total_pnl']:.2f}")
        logger.info(f"   勝率: {best_mdd['win_rate']:.2%}")
        logger.info(f"   停損設定: L1={best_mdd['lot1_stop_loss']}, L2={best_mdd['lot2_stop_loss']}, L3={best_mdd['lot3_stop_loss']}")

        if 'take_profit' in best_mdd and pd.notna(best_mdd['take_profit']):
            logger.info(f"   停利設定: {best_mdd['take_profit']}")
        elif 'take_profit_mode' in best_mdd and best_mdd['take_profit_mode'] == 'range_boundary':
            logger.info(f"   停利設定: 區間邊緣停利")
        elif 'lot1_take_profit' in best_mdd:
            logger.info(f"   停利設定: L1={best_mdd['lot1_take_profit']}, L2={best_mdd['lot2_take_profit']}, L3={best_mdd['lot3_take_profit']}")

        # 風險調整收益排名
        df['risk_adjusted_return'] = df['total_pnl'] / (abs(df['mdd']) + 1)  # 避免除零
        top_risk_adjusted = df.nlargest(5, 'risk_adjusted_return')

        logger.info(f"\n🎯 風險調整收益 TOP 5:")
        for i, (_, row) in enumerate(top_risk_adjusted.iterrows(), 1):
            take_profit_val = row.get('take_profit', 'N/A')
            if pd.isna(take_profit_val) and row.get('take_profit_mode') == 'range_boundary':
                take_profit_val = '區間邊緣'
            elif pd.isna(take_profit_val) and 'lot1_take_profit' in row:
                take_profit_val = f"L1:{row['lot1_take_profit']},L2:{row['lot2_take_profit']},L3:{row['lot3_take_profit']}"

            logger.info(f"   {i}. {row['time_interval']} | MDD:{row['mdd']:8.2f} | P&L:{row['total_pnl']:8.2f} | "
                       f"L1SL:{int(row['lot1_stop_loss']):2d} L2SL:{int(row['lot2_stop_loss']):2d} L3SL:{int(row['lot3_stop_loss']):2d} | "
                       f"TP:{take_profit_val}")

    def _generate_time_interval_analysis_report(self, df):
        """生成時間區間分析報告"""
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

        return daily_recommendations
