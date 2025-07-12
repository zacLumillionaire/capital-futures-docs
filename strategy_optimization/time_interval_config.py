#!/usr/bin/env python3
"""
時間區間配置管理器
專門管理多時間區間的實驗配置
"""

from datetime import time
from typing import List, Dict, Tuple, Any
import logging

logger = logging.getLogger(__name__)

class TimeIntervalConfig:
    """時間區間配置管理器"""
    
    def __init__(self):
        self.default_configs = self._initialize_default_configs()
    
    def _initialize_default_configs(self) -> Dict[str, Dict]:
        """初始化預設配置"""
        return {
            'quick_test': {
                'name': '快速測試',
                'description': '少量時間區間，適合快速驗證',
                'time_intervals': [
                    ("08:46", "08:47"),
                    ("12:30", "12:32")
                ],
                'stop_loss_ranges': {
                    'lot1': [15, 20],
                    'lot2': [20, 25],
                    'lot3': [25, 30]
                },
                'take_profit_ranges': {
                    'unified': [50, 60],
                    'individual': [40, 50, 60]
                },
                'optimization_target': 'mdd_minimization',
                'estimated_experiments': 48  # 2區間 × 2×2×2停損 × 3停利模式
            },
            
            'standard_analysis': {
                'name': '標準分析',
                'description': '涵蓋主要交易時段的標準配置',
                'time_intervals': [
                    ("10:00", "10:02"),  # 早盤
                    ("10:30", "10:32"),  # 早盤活躍
                    ("11:30", "11:32"),  # 中午震盪
                    ("12:30", "12:32"),  # 午後開始
                    ("13:30", "13:32")   # 尾盤
                ],
                'stop_loss_ranges': {
                    'lot1': [15, 20, 25],
                    'lot2': [20, 25, 30],
                    'lot3': [25, 30, 35]
                },
                'take_profit_ranges': {
                    'unified': [50, 60, 70],
                    'individual': [40, 50, 60, 70]
                },
                'optimization_target': 'mdd_minimization',
                'estimated_experiments': 1080  # 5區間 × 6停損組合 × 3統一停利 + 64各口獨立 + 1區間邊緣
            },
            
            'comprehensive_analysis': {
                'name': '綜合分析',
                'description': '全面的時間區間分析，涵蓋所有主要時段',
                'time_intervals': [
                    ("09:00", "09:02"),  # 開盤
                    ("09:30", "09:32"),  # 開盤後
                    ("10:00", "10:02"),  # 早盤
                    ("10:30", "10:32"),  # 早盤活躍
                    ("11:00", "11:02"),  # 中午前
                    ("11:30", "11:32"),  # 中午震盪
                    ("12:00", "12:02"),  # 午休前
                    ("12:30", "12:32"),  # 午後開始
                    ("13:00", "13:02"),  # 下午時段
                    ("13:30", "13:32")   # 尾盤
                ],
                'stop_loss_ranges': {
                    'lot1': [10, 15, 20, 25],
                    'lot2': [15, 20, 25, 30],
                    'lot3': [20, 25, 30, 35]
                },
                'take_profit_ranges': {
                    'unified': [40, 50, 60, 70, 80],
                    'individual': [30, 40, 50, 60, 70, 80]
                },
                'optimization_target': 'mdd_minimization',
                'estimated_experiments': 6800  # 10區間 × 20停損組合 × 多種停利模式
            },
            
            'focused_mdd': {
                'name': 'MDD專注分析 - 基於驗證配置',
                'description': '使用web_trading_gui.py驗證過的基礎配置，只調整時間區間和停利停損參數',
                'analysis_mode': 'per_time_interval',
                'date_range': {
                    'start_date': '2024-11-04',
                    'end_date': '2025-06-28'
                },
                'time_intervals': [
                    ("08:46", "08:47"),  # 您驗證的基礎時間
                    ("10:30", "10:32"),
                    ("11:30", "11:32"),
                    ("12:30", "12:32"),
                    ("13:00", "13:02")
                ],
                'stop_loss_ranges': {
                    'lot1': [15, 20, 25, 30],  # 基於15點做調整
                    'lot2': [15, 20, 25, 30],  # 基於40點做調整
                    'lot3': [15, 20, 25, 30]   # 基於41點做調整
                },
                'take_profit_ranges': {
                    'unified': [55],  # 統一停利選項
                    'individual': [15, 40, 41]  # 各口獨立停利選項
                },
                'take_profit_settings': [
                    {
                        'mode': 'trailing_stop',
                        'trailing_config': {
                            'lot1': {'trigger': 15, 'pullback': 10},  # 您的驗證配置
                            'lot2': {'trigger': 40, 'pullback': 10},
                            'lot3': {'trigger': 41, 'pullback': 20}
                        }
                    }
                ],
                'stop_loss_mode': 'range_boundary',  # 區間邊緣停損
                'filters_disabled': True,  # 所有濾網停用
                'optimization_target': 'mdd_minimization',
                'estimated_experiments': 100  # 5區間 × 4停損組合 × 1停利模式
            },
            
            'custom_intervals': {
                'name': '自定義區間',
                'description': '用戶可自定義的時間區間配置',
                'time_intervals': [],  # 用戶自定義
                'stop_loss_ranges': {
                    'lot1': [15],
                    'lot2': [25],
                    'lot3': [35]
                },
                'take_profit_ranges': {
                    'unified': [60],
                    'individual': [60]
                },
                'optimization_target': 'mdd_minimization',
                'estimated_experiments': 0  # 取決於用戶設定
            }
        }
    
    def get_config(self, config_name: str) -> Dict[str, Any]:
        """獲取指定配置"""
        if config_name not in self.default_configs:
            logger.warning(f"配置 '{config_name}' 不存在，使用預設配置 'standard_analysis'")
            config_name = 'standard_analysis'
        
        return self.default_configs[config_name].copy()
    
    def list_available_configs(self) -> Dict[str, Dict[str, Any]]:
        """列出所有可用配置"""
        return {
            name: {
                'name': config.get('name', name),
                'description': config.get('description', ''),
                'time_intervals': config.get('time_intervals', []),
                'estimated_experiments': config.get('estimated_experiments', 0)
            }
            for name, config in self.default_configs.items()
        }
    
    def create_custom_config(self, 
                           name: str,
                           time_intervals: List[Tuple[str, str]],
                           stop_loss_ranges: Dict[str, List[int]] = None,
                           take_profit_ranges: Dict[str, List[int]] = None,
                           optimization_target: str = 'mdd_minimization') -> Dict[str, Any]:
        """創建自定義配置"""
        
        # 使用預設值如果未提供
        if stop_loss_ranges is None:
            stop_loss_ranges = {
                'lot1': [15, 20],
                'lot2': [20, 25],
                'lot3': [25, 30]
            }
        
        if take_profit_ranges is None:
            take_profit_ranges = {
                'unified': [50, 60, 70],
                'individual': [40, 50, 60, 70]
            }
        
        # 驗證時間區間格式
        validated_intervals = self._validate_time_intervals(time_intervals)
        
        # 估算實驗數量
        estimated_experiments = self._estimate_experiments(
            len(validated_intervals),
            stop_loss_ranges,
            take_profit_ranges
        )
        
        custom_config = {
            'name': name,
            'description': f'自定義配置: {name}',
            'time_intervals': validated_intervals,
            'stop_loss_ranges': stop_loss_ranges,
            'take_profit_ranges': take_profit_ranges,
            'optimization_target': optimization_target,
            'estimated_experiments': estimated_experiments
        }
        
        logger.info(f"✅ 創建自定義配置 '{name}': {len(validated_intervals)} 個時間區間, "
                   f"預估 {estimated_experiments} 個實驗")
        
        return custom_config
    
    def _validate_time_intervals(self, intervals: List[Tuple[str, str]]) -> List[Tuple[str, str]]:
        """驗證時間區間格式"""
        validated = []
        
        for start_time, end_time in intervals:
            try:
                # 驗證時間格式
                start = time.fromisoformat(start_time)
                end = time.fromisoformat(end_time)
                
                # 檢查時間邏輯
                if start >= end:
                    logger.warning(f"時間區間 {start_time}-{end_time} 無效: 開始時間應早於結束時間")
                    continue
                
                # 檢查是否在交易時間內 (09:00-13:30)
                trading_start = time(9, 0)
                trading_end = time(13, 30)
                
                if start < trading_start or end > trading_end:
                    logger.warning(f"時間區間 {start_time}-{end_time} 超出交易時間 (09:00-13:30)")
                    continue
                
                validated.append((start_time, end_time))
                
            except ValueError as e:
                logger.error(f"時間格式錯誤 {start_time}-{end_time}: {e}")
                continue
        
        return validated
    
    def _estimate_experiments(self, 
                            interval_count: int,
                            stop_loss_ranges: Dict[str, List[int]],
                            take_profit_ranges: Dict[str, List[int]]) -> int:
        """估算實驗數量"""
        
        # 計算停損組合數 (考慮遞增約束)
        lot1_count = len(stop_loss_ranges['lot1'])
        lot2_count = len(stop_loss_ranges['lot2'])
        lot3_count = len(stop_loss_ranges['lot3'])
        
        # 簡化估算: 假設約50%的組合滿足遞增約束
        stop_loss_combinations = int(lot1_count * lot2_count * lot3_count * 0.5)
        
        # 計算停利模式數
        unified_count = len(take_profit_ranges['unified'])
        individual_count = len(take_profit_ranges['individual']) ** 3  # 每口獨立
        boundary_count = 1  # 區間邊緣停利
        
        take_profit_modes = unified_count + individual_count + boundary_count
        
        total_experiments = interval_count * stop_loss_combinations * take_profit_modes
        
        return total_experiments
    
    def get_optimization_targets(self) -> Dict[str, str]:
        """獲取可用的優化目標"""
        return {
            'mdd_minimization': 'MDD最小化 - 專注於降低最大回撤',
            'profit_maximization': '收益最大化 - 專注於提高總收益',
            'sharpe_optimization': '夏普比率優化 - 平衡收益與風險',
            'win_rate_optimization': '勝率優化 - 提高交易成功率',
            'risk_adjusted_return': '風險調整收益 - 綜合考慮收益與風險'
        }
    
    def validate_config(self, config: Dict[str, Any]) -> Tuple[bool, List[str]]:
        """驗證配置的有效性"""
        errors = []
        
        # 檢查必要欄位
        required_fields = ['time_intervals', 'stop_loss_ranges', 'take_profit_ranges']
        for field in required_fields:
            if field not in config:
                errors.append(f"缺少必要欄位: {field}")
        
        # 檢查時間區間
        if 'time_intervals' in config:
            if not config['time_intervals']:
                errors.append("時間區間不能為空")
            else:
                validated_intervals = self._validate_time_intervals(config['time_intervals'])
                if len(validated_intervals) != len(config['time_intervals']):
                    errors.append("部分時間區間格式無效")
        
        # 檢查停損範圍
        if 'stop_loss_ranges' in config:
            for lot in ['lot1', 'lot2', 'lot3']:
                if lot not in config['stop_loss_ranges']:
                    errors.append(f"缺少 {lot} 停損範圍")
                elif not config['stop_loss_ranges'][lot]:
                    errors.append(f"{lot} 停損範圍不能為空")
        
        # 檢查停利範圍
        if 'take_profit_ranges' in config:
            if 'unified' not in config['take_profit_ranges']:
                errors.append("缺少統一停利範圍")
            if 'individual' not in config['take_profit_ranges']:
                errors.append("缺少各口獨立停利範圍")
        
        is_valid = len(errors) == 0
        return is_valid, errors
    
    def get_config_summary(self, config: Dict[str, Any]) -> str:
        """獲取配置摘要"""
        summary = f"""
配置摘要:
  名稱: {config.get('name', '未命名')}
  描述: {config.get('description', '無描述')}
  時間區間數量: {len(config.get('time_intervals', []))}
  停損參數組合: {len(config.get('stop_loss_ranges', {}).get('lot1', []))} × {len(config.get('stop_loss_ranges', {}).get('lot2', []))} × {len(config.get('stop_loss_ranges', {}).get('lot3', []))}
  統一停利選項: {len(config.get('take_profit_ranges', {}).get('unified', []))}
  各口獨立停利選項: {len(config.get('take_profit_ranges', {}).get('individual', []))}
  優化目標: {config.get('optimization_target', 'mdd_minimization')}
  預估實驗數: {config.get('estimated_experiments', 0):,}
        """.strip()
        
        return summary
