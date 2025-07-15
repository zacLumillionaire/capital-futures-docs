#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
批次回測執行引擎
基於 web_trading_gui.py 的架構，自動執行大量參數組合的回測實驗
"""

import subprocess
import sys
import os
import json
import threading
import time
import sqlite3
from datetime import datetime
from typing import List, Dict, Any, Optional, Callable
from dataclasses import dataclass
import logging
from pathlib import Path
import re
from concurrent.futures import ThreadPoolExecutor, as_completed

# 設定日誌
logging.basicConfig(level=logging.INFO, format='[%(asctime)s] %(levelname)s [%(name)s:%(lineno)d] %(message)s')
logger = logging.getLogger(__name__)

@dataclass
class ExperimentResult:
    """實驗結果數據結構"""
    experiment_id: int
    parameters: Dict[str, Any]
    success: bool
    execution_time: float
    
    # 回測結果指標
    total_trades: int = 0
    winning_trades: int = 0
    losing_trades: int = 0
    win_rate: float = 0.0
    total_pnl: float = 0.0
    max_drawdown: float = 0.0
    
    # 多空分析
    long_trades: int = 0
    short_trades: int = 0
    long_pnl: float = 0.0
    short_pnl: float = 0.0
    
    # 錯誤信息
    error_message: str = ""
    stdout_log: str = ""
    stderr_log: str = ""

class ResultDatabase:
    """實驗結果資料庫管理"""
    
    def __init__(self, db_path: str = "batch_experiments.db"):
        self.db_path = db_path
        self.init_database()
    
    def init_database(self):
        """初始化資料庫表格"""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS experiments (
                    experiment_id INTEGER PRIMARY KEY,
                    parameters TEXT NOT NULL,
                    success BOOLEAN NOT NULL,
                    execution_time REAL NOT NULL,
                    total_trades INTEGER DEFAULT 0,
                    winning_trades INTEGER DEFAULT 0,
                    losing_trades INTEGER DEFAULT 0,
                    win_rate REAL DEFAULT 0.0,
                    total_pnl REAL DEFAULT 0.0,
                    max_drawdown REAL DEFAULT 0.0,
                    long_trades INTEGER DEFAULT 0,
                    short_trades INTEGER DEFAULT 0,
                    long_pnl REAL DEFAULT 0.0,
                    short_pnl REAL DEFAULT 0.0,
                    error_message TEXT DEFAULT '',
                    stdout_log TEXT DEFAULT '',
                    stderr_log TEXT DEFAULT '',
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_experiment_success ON experiments(success)
            """)
            
            conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_experiment_pnl ON experiments(total_pnl)
            """)
            
            conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_experiment_mdd ON experiments(max_drawdown)
            """)
    
    def save_result(self, result: ExperimentResult):
        """儲存實驗結果"""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                INSERT OR REPLACE INTO experiments (
                    experiment_id, parameters, success, execution_time,
                    total_trades, winning_trades, losing_trades, win_rate,
                    total_pnl, max_drawdown, long_trades, short_trades,
                    long_pnl, short_pnl, error_message, stdout_log, stderr_log
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                result.experiment_id, json.dumps(result.parameters), result.success, result.execution_time,
                result.total_trades, result.winning_trades, result.losing_trades, result.win_rate,
                result.total_pnl, result.max_drawdown, result.long_trades, result.short_trades,
                result.long_pnl, result.short_pnl, result.error_message, result.stdout_log, result.stderr_log
            ))
    
    def get_all_results(self) -> List[Dict]:
        """獲取所有實驗結果"""
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.execute("SELECT * FROM experiments ORDER BY created_at DESC")
            return [dict(row) for row in cursor.fetchall()]

    def get_best_results(self, metric: str = "total_pnl", limit: int = 10, ascending: bool = False) -> List[Dict]:
        """獲取最佳結果"""
        if ascending:
            order_direction = "ASC"
        else:
            # 預設降序排列，除了 max_drawdown (回撤越小越好)
            order_direction = "ASC" if metric == "max_drawdown" else "DESC"

        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.execute(f"""
                SELECT * FROM experiments
                WHERE success = 1
                ORDER BY {metric} {order_direction}
                LIMIT ?
            """, (limit,))
            return [dict(row) for row in cursor.fetchall()]

    def get_best_results_with_direction_filter(self, metric: str = "total_pnl", limit: int = 10, ascending: bool = False, trading_direction: str = None) -> List[Dict]:
        """🚀 新增：獲取指定交易方向的最佳結果"""
        if ascending:
            order_direction = "ASC"
        else:
            # 預設降序排列，除了 max_drawdown (回撤越小越好)
            order_direction = "ASC" if metric == "max_drawdown" else "DESC"

        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row

            # 🚀 添加交易方向過濾條件
            if trading_direction:
                cursor = conn.execute(f"""
                    SELECT * FROM experiments
                    WHERE success = 1
                    AND json_extract(parameters, '$.trading_direction') = ?
                    ORDER BY {metric} {order_direction}
                    LIMIT ?
                """, (trading_direction, limit))
            else:
                cursor = conn.execute(f"""
                    SELECT * FROM experiments
                    WHERE success = 1
                    ORDER BY {metric} {order_direction}
                    LIMIT ?
                """, (limit,))

            return [dict(row) for row in cursor.fetchall()]

    def clear_all_results(self):
        """清理所有實驗結果"""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("DELETE FROM experiments")
            logger.info("🗑️ 已清理所有實驗數據")

class BatchBacktestEngine:
    """批次回測執行引擎"""
    
    def __init__(self, 
                 backtest_script: str = "multi_Profit-Funded Risk_多口.py",
                 max_parallel: int = 1,
                 result_db: Optional[ResultDatabase] = None):
        self.backtest_script = backtest_script
        self.max_parallel = max_parallel
        self.result_db = result_db or ResultDatabase()
        
        # 執行狀態
        self.running = False
        self.completed_count = 0
        self.total_count = 0
        self.current_experiment = None
        self.start_time = None
        
        # 回調函數
        self.progress_callback: Optional[Callable] = None
        self.result_callback: Optional[Callable] = None
    
    def set_progress_callback(self, callback: Callable[[int, int, Dict], None]):
        """設定進度回調函數"""
        self.progress_callback = callback
    
    def set_result_callback(self, callback: Callable[[ExperimentResult], None]):
        """設定結果回調函數"""
        self.result_callback = callback
    
    def parse_backtest_output(self, stdout: str, stderr: str) -> Dict[str, Any]:
        """解析回測輸出，提取關鍵指標"""
        metrics = {
            'total_trades': 0,
            'winning_trades': 0,
            'losing_trades': 0,
            'win_rate': 0.0,
            'total_pnl': 0.0,
            'max_drawdown': 0.0,
            'long_trades': 0,
            'short_trades': 0,
            'long_pnl': 0.0,
            'short_pnl': 0.0
        }

        # 合併 stdout 和 stderr 進行解析
        full_output = stdout + "\n" + stderr
        lines = full_output.split('\n')

        # 首先嘗試從結構化輸出中解析（如果有的話）
        import re
        import json

        # 查找 JSON 格式的結果輸出
        # 首先查找新的標準格式：BACKTEST_RESULT_JSON: {...}
        backtest_result_pattern = r'BACKTEST_RESULT_JSON:\s*(\{.*\})'
        backtest_matches = re.findall(backtest_result_pattern, full_output)

        if backtest_matches:
            try:
                # 解析標準格式的 JSON 結果
                result_data = json.loads(backtest_matches[-1])
                if isinstance(result_data, dict):
                    metrics.update({
                        'total_trades': result_data.get('total_trades', 0),
                        'winning_trades': result_data.get('winning_trades', 0),
                        'losing_trades': result_data.get('losing_trades', 0),
                        'win_rate': result_data.get('win_rate', 0.0) * 100,  # 轉換為百分比
                        'total_pnl': result_data.get('total_pnl', 0.0),
                        'long_trades': result_data.get('long_trades', 0),
                        'short_trades': result_data.get('short_trades', 0),
                        'long_pnl': result_data.get('long_pnl', 0.0),
                        'short_pnl': result_data.get('short_pnl', 0.0)
                    })

                    # 計算最大回撤（如果沒有提供的話）
                    if 'max_drawdown' not in result_data:
                        # 使用更準確的MDD計算方法
                        # 從交易日誌中提取每筆交易的損益
                        trades_pnl = []
                        for line in full_output.split('\n'):
                            if '損益:' in line:
                                try:
                                    pnl_str = line.split('損益:')[1].strip().split()[0]
                                    trades_pnl.append(float(pnl_str))
                                except:
                                    pass

                        # 計算最大回撤
                        if trades_pnl:
                            peak = 0
                            max_dd = 0
                            current_pnl = 0

                            for pnl in trades_pnl:
                                current_pnl += pnl

                                # 更新峰值
                                if current_pnl > peak:
                                    peak = current_pnl

                                # 計算回撤
                                drawdown = peak - current_pnl
                                if drawdown > max_dd:
                                    max_dd = drawdown

                            metrics['max_drawdown'] = max_dd
                        else:
                            # 如果沒有交易記錄，使用簡單估算
                            if metrics['total_pnl'] < 0:
                                metrics['max_drawdown'] = abs(metrics['total_pnl'])
                            else:
                                metrics['max_drawdown'] = 0.0
                    else:
                        metrics['max_drawdown'] = result_data.get('max_drawdown', 0.0)

                    return metrics
            except (json.JSONDecodeError, KeyError):
                pass

        # 如果沒有找到標準格式，嘗試查找舊的 JSON 格式
        json_pattern = r'\{[^{}]*"total_pnl"[^{}]*\}'
        json_matches = re.findall(json_pattern, full_output)

        if json_matches:
            try:
                # 嘗試解析最後一個 JSON 結果
                result_data = json.loads(json_matches[-1])
                if isinstance(result_data, dict):
                    metrics.update({
                        'total_trades': result_data.get('total_trades', 0),
                        'winning_trades': result_data.get('winning_trades', 0),
                        'losing_trades': result_data.get('losing_trades', 0),
                        'win_rate': result_data.get('win_rate', 0.0) * 100,  # 轉換為百分比
                        'total_pnl': result_data.get('total_pnl', 0.0),
                        'long_trades': result_data.get('long_trades', 0),
                        'short_trades': result_data.get('short_trades', 0),
                        'long_pnl': result_data.get('long_pnl', 0.0),
                        'short_pnl': result_data.get('short_pnl', 0.0)
                    })

                    # 計算最大回撤（如果沒有提供的話）
                    if 'max_drawdown' not in result_data:
                        # 簡單估算：假設最大回撤為總損益的負值（如果是虧損）
                        if metrics['total_pnl'] < 0:
                            metrics['max_drawdown'] = abs(metrics['total_pnl'])
                    else:
                        metrics['max_drawdown'] = result_data.get('max_drawdown', 0.0)

                    return metrics
            except (json.JSONDecodeError, KeyError):
                pass

        # 如果沒有找到 JSON 格式，則使用傳統的文本解析
        for line in lines:
            # 清理日誌格式
            clean_line = line.strip()
            if '] INFO [' in line:
                parts = line.split('] ')
                if len(parts) >= 3:
                    clean_line = parts[2].strip()

            # 提取統計數據
            try:
                if '總交易次數:' in clean_line:
                    value = clean_line.split('總交易次數:')[1].strip()
                    metrics['total_trades'] = int(value)
                elif '獲利次數:' in clean_line:
                    value = clean_line.split('獲利次數:')[1].strip()
                    metrics['winning_trades'] = int(value)
                elif '虧損次數:' in clean_line:
                    value = clean_line.split('虧損次數:')[1].strip()
                    metrics['losing_trades'] = int(value)
                elif '勝率:' in clean_line:
                    value = clean_line.split('勝率:')[1].strip().replace('%', '')
                    metrics['win_rate'] = float(value)
                elif '總損益(' in clean_line and '口):' in clean_line:
                    # 匹配格式：總損益(3口): 1234.56
                    value = clean_line.split('):')[1].strip()
                    metrics['total_pnl'] = float(value)
                elif '最大回撤:' in clean_line:
                    value = clean_line.split('最大回撤:')[1].strip()
                    metrics['max_drawdown'] = float(value)
                elif '多頭交易次數:' in clean_line:
                    value = clean_line.split('多頭交易次數:')[1].strip()
                    metrics['long_trades'] = int(value)
                elif '空頭交易次數:' in clean_line:
                    value = clean_line.split('空頭交易次數:')[1].strip()
                    metrics['short_trades'] = int(value)
                elif '多頭損益:' in clean_line:
                    value = clean_line.split('多頭損益:')[1].strip()
                    metrics['long_pnl'] = float(value)
                elif '空頭損益:' in clean_line:
                    value = clean_line.split('空頭損益:')[1].strip()
                    metrics['short_pnl'] = float(value)
            except (ValueError, IndexError):
                continue

        # 如果沒有解析到多空數據，嘗試從總交易數據中估算
        if metrics['long_trades'] == 0 and metrics['short_trades'] == 0 and metrics['total_trades'] > 0:
            # 假設多空各佔一半
            metrics['long_trades'] = metrics['total_trades'] // 2
            metrics['short_trades'] = metrics['total_trades'] - metrics['long_trades']

            # 假設多空損益各佔一半
            metrics['long_pnl'] = metrics['total_pnl'] / 2
            metrics['short_pnl'] = metrics['total_pnl'] / 2

        return metrics
    
    def execute_single_experiment(self, experiment: Dict[str, Any]) -> ExperimentResult:
        """執行單個實驗"""
        experiment_id = experiment['experiment_id']
        start_time = time.time()

        # 計算進度百分比
        progress_percent = (self.completed_count / self.total_count * 100) if self.total_count > 0 else 0
        logger.info(f"🚀 開始執行實驗 {experiment_id}/{self.total_count} - {progress_percent:.1f}%")
        
        try:
            # 轉換為 GUI 配置格式
            gui_config = {
                "trade_lots": experiment["trade_lots"],
                "start_date": experiment["start_date"],
                "end_date": experiment["end_date"],
                "range_start_time": experiment["range_start_time"],
                "range_end_time": experiment["range_end_time"],
                "trading_direction": experiment.get("trading_direction", "BOTH"),  # 🚀 新增交易方向
                "lot_settings": {
                    "lot1": {
                        "trigger": experiment["lot1_trigger"],
                        "trailing": experiment["lot1_trailing"]
                    },
                    "lot2": {
                        "trigger": experiment["lot2_trigger"],
                        "trailing": experiment["lot2_trailing"],
                        "protection": experiment["lot2_protection"]
                    },
                    "lot3": {
                        "trigger": experiment["lot3_trigger"],
                        "trailing": experiment["lot3_trailing"],
                        "protection": experiment["lot3_protection"]
                    }
                },
                "filters": {
                    "range_filter": {
                        "enabled": experiment.get("range_filter_enabled", False),
                        "max_range_points": experiment.get("max_range_points", 50)
                    },
                    "risk_filter": {
                        "enabled": experiment.get("risk_filter_enabled", False),
                        "daily_loss_limit": experiment.get("daily_loss_limit", 150),
                        "profit_target": experiment.get("profit_target", 200)
                    },
                    "stop_loss_filter": {
                        "enabled": experiment.get("stop_loss_filter_enabled", False),
                        "stop_loss_type": experiment.get("stop_loss_type", "range_boundary"),
                        "fixed_stop_loss_points": experiment.get("fixed_stop_loss_points", 15.0)
                    }
                }
            }
            
            # 構建命令
            cmd = [
                sys.executable,
                self.backtest_script,
                "--start-date", gui_config["start_date"],
                "--end-date", gui_config["end_date"],
                "--gui-mode",
                "--config", json.dumps(gui_config, ensure_ascii=False)
            ]
            
            # 執行回測
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                encoding='utf-8',
                errors='replace',
                timeout=300  # 5分鐘超時
            )
            
            execution_time = time.time() - start_time
            
            # 解析結果
            if result.returncode == 0:
                metrics = self.parse_backtest_output(result.stdout, result.stderr)
                
                experiment_result = ExperimentResult(
                    experiment_id=experiment_id,
                    parameters=experiment,
                    success=True,
                    execution_time=execution_time,
                    **metrics,
                    stdout_log=result.stdout,
                    stderr_log=result.stderr
                )
                
                logger.info(f"✅ 實驗 {experiment_id} 完成 - 總損益: {metrics['total_pnl']}, 勝率: {metrics['win_rate']}%")
            else:
                experiment_result = ExperimentResult(
                    experiment_id=experiment_id,
                    parameters=experiment,
                    success=False,
                    execution_time=execution_time,
                    error_message=f"回測執行失敗 (返回碼: {result.returncode})",
                    stdout_log=result.stdout,
                    stderr_log=result.stderr
                )
                
                logger.error(f"❌ 實驗 {experiment_id} 失敗 - {experiment_result.error_message}")
            
            return experiment_result
            
        except subprocess.TimeoutExpired:
            execution_time = time.time() - start_time
            experiment_result = ExperimentResult(
                experiment_id=experiment_id,
                parameters=experiment,
                success=False,
                execution_time=execution_time,
                error_message="執行超時"
            )
            logger.error(f"⏰ 實驗 {experiment_id} 超時")
            return experiment_result
            
        except Exception as e:
            execution_time = time.time() - start_time
            experiment_result = ExperimentResult(
                experiment_id=experiment_id,
                parameters=experiment,
                success=False,
                execution_time=execution_time,
                error_message=str(e)
            )
            logger.error(f"💥 實驗 {experiment_id} 異常: {e}")
            return experiment_result
    
    def run_batch_experiments(self, experiments: List[Dict[str, Any]]):
        """執行批次實驗"""
        self.running = True
        self.completed_count = 0
        self.total_count = len(experiments)
        self.start_time = time.time()

        logger.info(f"🎯 開始批次實驗 - 總共 {self.total_count} 個實驗，並行數: {self.max_parallel}")

        try:
            if self.max_parallel == 1:
                # 串行執行
                self._run_sequential(experiments)
            else:
                # 並行執行
                self._run_parallel(experiments)

            total_time = time.time() - self.start_time
            logger.info(f"🏁 批次實驗完成 - 耗時: {total_time:.2f}秒, 完成: {self.completed_count}/{self.total_count}")

        except Exception as e:
            logger.error(f"💥 批次實驗異常: {e}")
        finally:
            self.running = False

    def _run_sequential(self, experiments: List[Dict[str, Any]]):
        """串行執行實驗"""
        for i, experiment in enumerate(experiments):
            if not self.running:
                break

            self.current_experiment = experiment
            result = self.execute_single_experiment(experiment)
            self._process_result(result, experiment)
            time.sleep(0.1)

    def _run_parallel(self, experiments: List[Dict[str, Any]]):
        """並行執行實驗"""
        with ThreadPoolExecutor(max_workers=self.max_parallel) as executor:
            # 提交所有任務
            future_to_experiment = {
                executor.submit(self.execute_single_experiment, exp): exp
                for exp in experiments
            }

            # 處理完成的任務
            for future in as_completed(future_to_experiment):
                if not self.running:
                    break

                experiment = future_to_experiment[future]
                try:
                    result = future.result()
                    self._process_result(result, experiment)
                except Exception as e:
                    logger.error(f"實驗 {experiment['experiment_id']} 執行異常: {e}")

    def _process_result(self, result: ExperimentResult, experiment: Dict[str, Any]):
        """處理實驗結果"""
        # 儲存結果
        self.result_db.save_result(result)

        # 更新進度
        self.completed_count += 1
        self.current_experiment = experiment

        # 調用回調函數
        if self.progress_callback:
            self.progress_callback(self.completed_count, self.total_count, experiment)

        if self.result_callback:
            self.result_callback(result)
    
    def stop_experiments(self):
        """停止實驗執行"""
        self.running = False
        logger.info("🛑 批次實驗已停止")
    
    def get_progress_info(self) -> Dict[str, Any]:
        """獲取進度信息"""
        if not self.start_time:
            return {"status": "not_started"}
        
        elapsed_time = time.time() - self.start_time
        progress_percent = (self.completed_count / self.total_count * 100) if self.total_count > 0 else 0
        
        eta = 0
        if self.completed_count > 0:
            avg_time_per_experiment = elapsed_time / self.completed_count
            remaining_experiments = self.total_count - self.completed_count
            eta = avg_time_per_experiment * remaining_experiments
        
        return {
            "status": "running" if self.running else "completed",
            "completed": self.completed_count,
            "total": self.total_count,
            "progress_percent": progress_percent,
            "elapsed_time": elapsed_time,
            "eta": eta,
            "current_experiment": self.current_experiment
        }

def load_experiments_from_file(filename: str) -> List[Dict[str, Any]]:
    """從檔案載入實驗配置"""
    with open(filename, 'r', encoding='utf-8') as f:
        data = json.load(f)
    return data['experiments']

if __name__ == "__main__":
    # 示例使用
    engine = BatchBacktestEngine()
    
    # 載入實驗配置
    experiments = load_experiments_from_file("parameter_matrix_20250710_102309.json")
    
    # 設定進度回調
    def progress_callback(completed, total, current_exp):
        print(f"進度: {completed}/{total} ({completed/total*100:.1f}%) - 當前實驗: {current_exp['experiment_id']}")
    
    engine.set_progress_callback(progress_callback)
    
    # 執行批次實驗
    print("🚀 開始執行批次實驗...")
    engine.run_batch_experiments(experiments[:5])  # 先測試前5個實驗
    
    # 查看最佳結果
    best_results = engine.result_db.get_best_results("total_pnl", 3)
    print("\n🏆 最佳結果 (總損益):")
    for i, result in enumerate(best_results, 1):
        print(f"  {i}. 實驗 {result['experiment_id']}: {result['total_pnl']} 點")
