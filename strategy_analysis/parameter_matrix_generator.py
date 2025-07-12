#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
參數矩陣生成器
基於 web_trading_gui.py 的架構，生成大量參數組合用於批次實驗
支援各口停利啟動點、時間區段等參數的組合生成
"""

import itertools
from dataclasses import dataclass, field
from typing import List, Dict, Any, Tuple
from decimal import Decimal
import json
from datetime import datetime, time

@dataclass
class ParameterRange:
    """參數範圍定義"""
    min_value: float
    max_value: float
    step: float
    
    def generate_values(self) -> List[float]:
        """生成參數值列表"""
        values = []
        current = self.min_value
        while current <= self.max_value:
            values.append(round(current, 1))
            current += self.step
        return values

@dataclass
class TimeRange:
    """時間區段範圍定義"""
    start_times: List[str]  # 格式: ["08:45", "08:46", "08:47"]
    end_times: List[str]    # 格式: ["08:46", "08:47", "08:48"]
    
    def generate_combinations(self) -> List[Tuple[str, str]]:
        """生成時間區段組合"""
        combinations = []
        for start_time in self.start_times:
            for end_time in self.end_times:
                # 確保結束時間晚於開始時間
                start_hour, start_min = map(int, start_time.split(':'))
                end_hour, end_min = map(int, end_time.split(':'))
                
                start_minutes = start_hour * 60 + start_min
                end_minutes = end_hour * 60 + end_min
                
                if end_minutes > start_minutes:
                    combinations.append((start_time, end_time))
        return combinations

@dataclass
class LotParameterConfig:
    """單口參數配置"""
    trigger_range: ParameterRange
    trailing_range: ParameterRange
    protection_range: ParameterRange = None  # 第1口不需要保護係數

@dataclass
class ExperimentConfig:
    """實驗配置"""
    # 基本設定
    trade_lots: int = 3
    date_ranges: List[Tuple[str, str]] = field(default_factory=lambda: [("2024-11-01", "2024-11-30")])
    
    # 時間區段設定
    time_ranges: TimeRange = field(default_factory=lambda: TimeRange(
        start_times=["08:45", "08:46", "08:47"],
        end_times=["08:46", "08:47", "08:48"]
    ))
    
    # 各口參數設定
    lot1_config: LotParameterConfig = field(default_factory=lambda: LotParameterConfig(
        trigger_range=ParameterRange(10, 25, 5),
        trailing_range=ParameterRange(10, 30, 10)
    ))
    
    lot2_config: LotParameterConfig = field(default_factory=lambda: LotParameterConfig(
        trigger_range=ParameterRange(30, 50, 5),
        trailing_range=ParameterRange(10, 30, 10),
        protection_range=ParameterRange(1.5, 3.0, 0.5)
    ))
    
    lot3_config: LotParameterConfig = field(default_factory=lambda: LotParameterConfig(
        trigger_range=ParameterRange(50, 80, 5),
        trailing_range=ParameterRange(10, 30, 10),
        protection_range=ParameterRange(1.5, 3.0, 0.5)
    ))
    
    # 濾網設定
    enable_range_filter: bool = False
    range_filter_values: List[float] = field(default_factory=lambda: [50, 100, 150, 200])
    
    enable_risk_filter: bool = False
    daily_loss_limits: List[float] = field(default_factory=lambda: [100, 150, 200])
    profit_targets: List[float] = field(default_factory=lambda: [150, 200, 250])
    
    # 約束條件
    enforce_lot_progression: bool = True  # lot1_trigger <= lot2_trigger <= lot3_trigger

class ParameterMatrixGenerator:
    """參數矩陣生成器"""
    
    def __init__(self, config: ExperimentConfig):
        self.config = config
        
    def generate_lot_parameter_combinations(self) -> List[Dict[str, Any]]:
        """生成各口參數組合"""
        # 生成各口的參數值
        lot1_triggers = self.config.lot1_config.trigger_range.generate_values()
        lot1_trailings = self.config.lot1_config.trailing_range.generate_values()
        
        lot2_triggers = self.config.lot2_config.trigger_range.generate_values()
        lot2_trailings = self.config.lot2_config.trailing_range.generate_values()
        lot2_protections = self.config.lot2_config.protection_range.generate_values() if self.config.lot2_config.protection_range else [2.0]
        
        lot3_triggers = self.config.lot3_config.trigger_range.generate_values()
        lot3_trailings = self.config.lot3_config.trailing_range.generate_values()
        lot3_protections = self.config.lot3_config.protection_range.generate_values() if self.config.lot3_config.protection_range else [2.0]
        
        combinations = []
        
        # 生成所有可能的組合
        for lot1_trigger in lot1_triggers:
            for lot1_trailing in lot1_trailings:
                for lot2_trigger in lot2_triggers:
                    for lot2_trailing in lot2_trailings:
                        for lot2_protection in lot2_protections:
                            for lot3_trigger in lot3_triggers:
                                for lot3_trailing in lot3_trailings:
                                    for lot3_protection in lot3_protections:
                                        
                                        # 檢查約束條件
                                        if self.config.enforce_lot_progression:
                                            if not (lot1_trigger <= lot2_trigger <= lot3_trigger):
                                                continue
                                        
                                        combination = {
                                            "lot1_trigger": lot1_trigger,
                                            "lot1_trailing": lot1_trailing,
                                            "lot2_trigger": lot2_trigger,
                                            "lot2_trailing": lot2_trailing,
                                            "lot2_protection": lot2_protection,
                                            "lot3_trigger": lot3_trigger,
                                            "lot3_trailing": lot3_trailing,
                                            "lot3_protection": lot3_protection
                                        }
                                        combinations.append(combination)
        
        return combinations
    
    def generate_filter_combinations(self) -> List[Dict[str, Any]]:
        """生成濾網參數組合"""
        filter_combinations = []
        
        # 基本組合：無濾網
        base_filter = {
            "range_filter_enabled": False,
            "risk_filter_enabled": False,
            "stop_loss_filter_enabled": False
        }
        filter_combinations.append(base_filter)
        
        # 區間濾網組合
        if self.config.enable_range_filter:
            for range_value in self.config.range_filter_values:
                filter_combo = base_filter.copy()
                filter_combo.update({
                    "range_filter_enabled": True,
                    "max_range_points": range_value
                })
                filter_combinations.append(filter_combo)
        
        # 風險管理濾網組合
        if self.config.enable_risk_filter:
            for loss_limit in self.config.daily_loss_limits:
                for profit_target in self.config.profit_targets:
                    filter_combo = base_filter.copy()
                    filter_combo.update({
                        "risk_filter_enabled": True,
                        "daily_loss_limit": loss_limit,
                        "profit_target": profit_target
                    })
                    filter_combinations.append(filter_combo)
        
        return filter_combinations
    
    def generate_full_parameter_matrix(self) -> List[Dict[str, Any]]:
        """生成完整的參數矩陣"""
        lot_combinations = self.generate_lot_parameter_combinations()
        filter_combinations = self.generate_filter_combinations()
        time_combinations = self.config.time_ranges.generate_combinations()
        
        full_matrix = []
        experiment_id = 1
        
        for date_range in self.config.date_ranges:
            for time_combo in time_combinations:
                for lot_combo in lot_combinations:
                    for filter_combo in filter_combinations:
                        
                        experiment = {
                            "experiment_id": experiment_id,
                            "trade_lots": self.config.trade_lots,
                            "start_date": date_range[0],
                            "end_date": date_range[1],
                            "range_start_time": time_combo[0],
                            "range_end_time": time_combo[1],
                            **lot_combo,
                            **filter_combo
                        }
                        
                        full_matrix.append(experiment)
                        experiment_id += 1
        
        return full_matrix
    
    def get_matrix_statistics(self) -> Dict[str, int]:
        """獲取矩陣統計資訊"""
        lot_combinations = len(self.generate_lot_parameter_combinations())
        filter_combinations = len(self.generate_filter_combinations())
        time_combinations = len(self.config.time_ranges.generate_combinations())
        date_ranges = len(self.config.date_ranges)
        
        total_experiments = lot_combinations * filter_combinations * time_combinations * date_ranges
        
        return {
            "lot_combinations": lot_combinations,
            "filter_combinations": filter_combinations,
            "time_combinations": time_combinations,
            "date_ranges": date_ranges,
            "total_experiments": total_experiments
        }
    
    def save_matrix_to_file(self, filename: str = None) -> str:
        """將參數矩陣儲存到檔案"""
        if filename is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"parameter_matrix_{timestamp}.json"
        
        matrix = self.generate_full_parameter_matrix()
        statistics = self.get_matrix_statistics()
        
        output_data = {
            "metadata": {
                "generated_at": datetime.now().isoformat(),
                "statistics": statistics,
                "config": {
                    "trade_lots": self.config.trade_lots,
                    "enforce_lot_progression": self.config.enforce_lot_progression,
                    "enable_range_filter": self.config.enable_range_filter,
                    "enable_risk_filter": self.config.enable_risk_filter
                }
            },
            "experiments": matrix
        }
        
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(output_data, f, ensure_ascii=False, indent=2)
        
        return filename

def create_default_experiment_config() -> ExperimentConfig:
    """創建預設實驗配置"""
    return ExperimentConfig(
        trade_lots=3,
        date_ranges=[("2024-11-04", "2025-06-28")],  # 使用用戶偏好的日期範圍
        time_ranges=TimeRange(
            start_times=["08:46"],  # 使用用戶偏好的開盤區間
            end_times=["08:47"]
        ),
        # 基於用戶記憶中的MDD優化範圍
        lot1_config=LotParameterConfig(
            trigger_range=ParameterRange(15, 25, 5),  # 15-25點
            trailing_range=ParameterRange(10, 20, 10)  # 10%, 20%
        ),
        lot2_config=LotParameterConfig(
            trigger_range=ParameterRange(35, 45, 5),  # 35-45點
            trailing_range=ParameterRange(10, 20, 10),
            protection_range=ParameterRange(2.0, 2.0, 1.0)  # 固定2x保護
        ),
        lot3_config=LotParameterConfig(
            trigger_range=ParameterRange(40, 50, 5),  # 40-50點
            trailing_range=ParameterRange(20, 20, 1),  # 固定20%
            protection_range=ParameterRange(2.0, 2.0, 1.0)  # 固定2x保護
        ),
        enforce_lot_progression=True
    )

if __name__ == "__main__":
    # 示例使用
    config = create_default_experiment_config()
    generator = ParameterMatrixGenerator(config)
    
    # 顯示統計資訊
    stats = generator.get_matrix_statistics()
    print("📊 參數矩陣統計:")
    for key, value in stats.items():
        print(f"  - {key}: {value}")
    
    # 生成並儲存矩陣
    filename = generator.save_matrix_to_file()
    print(f"\n✅ 參數矩陣已儲存到: {filename}")
