#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
策略配置模組
定義策略參數和配置結構，基於回測程式的設計
"""

from dataclasses import dataclass
from decimal import Decimal
from typing import List, Optional, Dict, Any
from enum import Enum
import json
import logging

logger = logging.getLogger(__name__)

class StopLossType(Enum):
    """停損類型"""
    RANGE_BOUNDARY = "RANGE_BOUNDARY"  # 區間邊界停損
    FIXED_POINTS = "FIXED_POINTS"      # 固定點數停損
    PERCENTAGE = "PERCENTAGE"          # 百分比停損

class PositionType(Enum):
    """部位類型"""
    LONG = "LONG"   # 多頭
    SHORT = "SHORT" # 空頭

@dataclass
class LotRule:
    """單口規則配置"""
    
    # 移動停利設定
    use_trailing_stop: bool = True
    trailing_activation: Optional[Decimal] = None      # 啟動移動停利的點數
    trailing_pullback: Optional[Decimal] = None        # 回檔比例 (0.20 = 20%)
    
    # 固定停利設定
    fixed_tp_points: Optional[Decimal] = None          # 固定停利點數
    
    # 保護性停損設定
    protective_stop_multiplier: Optional[Decimal] = None  # 保護停損倍數
    
    # 其他設定
    min_profit_to_protect: Decimal = Decimal('0')      # 最小保護獲利
    max_loss_points: Optional[Decimal] = None          # 最大虧損點數
    
    def __post_init__(self):
        """初始化後驗證"""
        if self.use_trailing_stop:
            if self.trailing_activation is None or self.trailing_pullback is None:
                raise ValueError("使用移動停利時必須設定 trailing_activation 和 trailing_pullback")
        
        if self.fixed_tp_points is not None and self.use_trailing_stop:
            logger.warning("同時設定固定停利和移動停利，將優先使用移動停利")

@dataclass
class StrategyConfig:
    """策略配置"""
    
    # 基本設定
    strategy_name: str = "開盤區間突破策略"
    trade_size_in_lots: int = 3                        # 交易口數 (預設3口)
    
    # 停損設定
    stop_loss_type: StopLossType = StopLossType.RANGE_BOUNDARY
    stop_loss_points: Optional[Decimal] = None         # 固定停損點數
    
    # 口數規則
    lot_rules: List[LotRule] = None
    
    # 風險控制
    max_daily_loss: Decimal = Decimal('5000')          # 每日最大虧損 (元)
    max_position_size: int = 4                         # 最大部位口數
    
    # 時間設定
    range_start_time: str = "08:46:00"                 # 開盤區間開始時間
    range_end_time: str = "08:47:59"                   # 開盤區間結束時間
    trading_start_time: str = "08:48:00"               # 交易開始時間
    trading_end_time: str = "13:45:00"                 # 交易結束時間
    
    # 進場設定
    breakout_buffer: Decimal = Decimal('0')            # 突破緩衝點數
    min_range_size: Decimal = Decimal('10')            # 最小區間大小
    max_range_size: Decimal = Decimal('100')           # 最大區間大小
    
    # 其他設定
    enable_short_trading: bool = True                  # 是否允許放空
    enable_night_trading: bool = False                 # 是否啟用夜盤
    
    def __post_init__(self):
        """初始化後處理"""
        # 如果沒有設定口數規則，創建預設規則
        if self.lot_rules is None:
            self.lot_rules = self._create_default_lot_rules()
        
        # 驗證口數規則數量
        if len(self.lot_rules) != self.trade_size_in_lots:
            raise ValueError(f"口數規則數量 ({len(self.lot_rules)}) 與交易口數 ({self.trade_size_in_lots}) 不符")
    
    def _create_default_lot_rules(self) -> List[LotRule]:
        """創建預設的口數規則"""
        rules = []
        
        if self.trade_size_in_lots == 1:
            # 單口策略
            rules.append(LotRule(
                use_trailing_stop=True,
                trailing_activation=Decimal('15'),
                trailing_pullback=Decimal('0.20')
            ))
        
        elif self.trade_size_in_lots == 2:
            # 雙口策略
            rules.extend([
                LotRule(
                    use_trailing_stop=True,
                    trailing_activation=Decimal('15'),
                    trailing_pullback=Decimal('0.20')
                ),
                LotRule(
                    use_trailing_stop=True,
                    trailing_activation=Decimal('40'),
                    trailing_pullback=Decimal('0.20'),
                    protective_stop_multiplier=Decimal('2.0')
                )
            ])
        
        elif self.trade_size_in_lots == 3:
            # 三口策略 (預設配置)
            rules.extend([
                LotRule(
                    use_trailing_stop=True,
                    trailing_activation=Decimal('15'),
                    trailing_pullback=Decimal('0.20')  # 20%回檔
                ),
                LotRule(
                    use_trailing_stop=True,
                    trailing_activation=Decimal('40'),
                    trailing_pullback=Decimal('0.20'),  # 20%回檔
                    protective_stop_multiplier=Decimal('2.0')
                ),
                LotRule(
                    use_trailing_stop=True,
                    trailing_activation=Decimal('65'),
                    trailing_pullback=Decimal('0.20'),  # 20%回檔
                    protective_stop_multiplier=Decimal('2.0')
                )
            ])
        
        elif self.trade_size_in_lots == 4:
            # 四口策略
            rules.extend([
                LotRule(
                    use_trailing_stop=True,
                    trailing_activation=Decimal('15'),
                    trailing_pullback=Decimal('0.20')
                ),
                LotRule(
                    use_trailing_stop=True,
                    trailing_activation=Decimal('40'),
                    trailing_pullback=Decimal('0.20'),
                    protective_stop_multiplier=Decimal('2.0')
                ),
                LotRule(
                    use_trailing_stop=True,
                    trailing_activation=Decimal('65'),
                    trailing_pullback=Decimal('0.20'),
                    protective_stop_multiplier=Decimal('2.0')
                ),
                LotRule(
                    use_trailing_stop=True,
                    trailing_activation=Decimal('80'),
                    trailing_pullback=Decimal('0.40'),
                    protective_stop_multiplier=Decimal('1.0')
                )
            ])
        
        else:
            # 其他口數，使用簡單規則
            for i in range(self.trade_size_in_lots):
                activation_points = Decimal('15') + Decimal('25') * i
                rules.append(LotRule(
                    use_trailing_stop=True,
                    trailing_activation=activation_points,
                    trailing_pullback=Decimal('0.20'),
                    protective_stop_multiplier=Decimal('2.0') if i > 0 else None
                ))
        
        return rules
    
    def to_dict(self) -> Dict[str, Any]:
        """轉換為字典格式"""
        return {
            'strategy_name': self.strategy_name,
            'trade_size_in_lots': self.trade_size_in_lots,
            'stop_loss_type': self.stop_loss_type.value,
            'stop_loss_points': float(self.stop_loss_points) if self.stop_loss_points else None,
            'lot_rules': [
                {
                    'use_trailing_stop': rule.use_trailing_stop,
                    'trailing_activation': float(rule.trailing_activation) if rule.trailing_activation else None,
                    'trailing_pullback': float(rule.trailing_pullback) if rule.trailing_pullback else None,
                    'fixed_tp_points': float(rule.fixed_tp_points) if rule.fixed_tp_points else None,
                    'protective_stop_multiplier': float(rule.protective_stop_multiplier) if rule.protective_stop_multiplier else None,
                }
                for rule in self.lot_rules
            ],
            'max_daily_loss': float(self.max_daily_loss),
            'max_position_size': self.max_position_size,
            'range_start_time': self.range_start_time,
            'range_end_time': self.range_end_time,
            'trading_start_time': self.trading_start_time,
            'trading_end_time': self.trading_end_time,
            'breakout_buffer': float(self.breakout_buffer),
            'min_range_size': float(self.min_range_size),
            'max_range_size': float(self.max_range_size),
            'enable_short_trading': self.enable_short_trading,
            'enable_night_trading': self.enable_night_trading,
        }
    
    def save_to_file(self, filename: str):
        """儲存配置到檔案"""
        try:
            with open(filename, 'w', encoding='utf-8') as f:
                json.dump(self.to_dict(), f, indent=2, ensure_ascii=False)
            logger.info(f"策略配置已儲存到: {filename}")
        except Exception as e:
            logger.error(f"儲存策略配置失敗: {e}")
    
    @classmethod
    def load_from_file(cls, filename: str) -> 'StrategyConfig':
        """從檔案載入配置"""
        try:
            with open(filename, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            # 重建LotRule物件
            lot_rules = []
            for rule_data in data.get('lot_rules', []):
                lot_rules.append(LotRule(
                    use_trailing_stop=rule_data.get('use_trailing_stop', True),
                    trailing_activation=Decimal(str(rule_data['trailing_activation'])) if rule_data.get('trailing_activation') else None,
                    trailing_pullback=Decimal(str(rule_data['trailing_pullback'])) if rule_data.get('trailing_pullback') else None,
                    fixed_tp_points=Decimal(str(rule_data['fixed_tp_points'])) if rule_data.get('fixed_tp_points') else None,
                    protective_stop_multiplier=Decimal(str(rule_data['protective_stop_multiplier'])) if rule_data.get('protective_stop_multiplier') else None,
                ))
            
            # 創建StrategyConfig物件
            config = cls(
                strategy_name=data.get('strategy_name', '開盤區間突破策略'),
                trade_size_in_lots=data.get('trade_size_in_lots', 1),
                stop_loss_type=StopLossType(data.get('stop_loss_type', 'RANGE_BOUNDARY')),
                stop_loss_points=Decimal(str(data['stop_loss_points'])) if data.get('stop_loss_points') else None,
                lot_rules=lot_rules,
                max_daily_loss=Decimal(str(data.get('max_daily_loss', '5000'))),
                max_position_size=data.get('max_position_size', 4),
                range_start_time=data.get('range_start_time', '08:46:00'),
                range_end_time=data.get('range_end_time', '08:47:59'),
                trading_start_time=data.get('trading_start_time', '08:48:00'),
                trading_end_time=data.get('trading_end_time', '13:45:00'),
                breakout_buffer=Decimal(str(data.get('breakout_buffer', '0'))),
                min_range_size=Decimal(str(data.get('min_range_size', '10'))),
                max_range_size=Decimal(str(data.get('max_range_size', '100'))),
                enable_short_trading=data.get('enable_short_trading', True),
                enable_night_trading=data.get('enable_night_trading', False),
            )
            
            logger.info(f"策略配置已從 {filename} 載入")
            return config
            
        except Exception as e:
            logger.error(f"載入策略配置失敗: {e}")
            raise

def create_preset_configs() -> Dict[str, StrategyConfig]:
    """創建預設策略配置"""
    configs = {}
    
    # 單口策略
    configs['single_lot'] = StrategyConfig(
        strategy_name="單口移動停利策略",
        trade_size_in_lots=1
    )
    
    # 雙口策略
    configs['double_lot'] = StrategyConfig(
        strategy_name="雙口移動停利策略",
        trade_size_in_lots=2
    )
    
    # 三口策略
    configs['triple_lot'] = StrategyConfig(
        strategy_name="三口移動停利策略",
        trade_size_in_lots=3
    )
    
    # 四口策略
    configs['quad_lot'] = StrategyConfig(
        strategy_name="四口移動停利策略",
        trade_size_in_lots=4
    )
    
    return configs

if __name__ == "__main__":
    # 測試策略配置
    print("🧪 測試策略配置模組")
    
    # 創建三口策略配置
    config = StrategyConfig(
        strategy_name="測試三口策略",
        trade_size_in_lots=3
    )
    
    print(f"策略名稱: {config.strategy_name}")
    print(f"交易口數: {config.trade_size_in_lots}")
    print(f"口數規則數量: {len(config.lot_rules)}")
    
    for i, rule in enumerate(config.lot_rules, 1):
        print(f"第{i}口: 啟動{rule.trailing_activation}點, 回檔{rule.trailing_pullback}")
    
    # 測試儲存和載入
    config.save_to_file("test_strategy_config.json")
    loaded_config = StrategyConfig.load_from_file("test_strategy_config.json")
    
    print(f"載入的策略: {loaded_config.strategy_name}")
    
    # 測試預設配置
    presets = create_preset_configs()
    print(f"預設配置數量: {len(presets)}")
    
    print("✅ 策略配置測試完成")

    # 清理測試檔案
    import os
    if os.path.exists("test_strategy_config.json"):
        os.remove("test_strategy_config.json")
