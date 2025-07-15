#!/usr/bin/env python3
"""
調試風險管理配置的測試腳本
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# 直接定義需要的類別來避免執行主程式
from dataclasses import dataclass, field
from decimal import Decimal
from enum import Enum

class StopLossType(Enum):
    RANGE_BOUNDARY = "range_boundary"

@dataclass
class LotRule:
    use_trailing_stop: bool = False
    trailing_activation: Decimal = Decimal(0)
    trailing_pullback: Decimal = Decimal('0.20')
    protective_stop_multiplier: Decimal = Decimal('0.0')

@dataclass
class RangeFilter:
    use_range_size_filter: bool = False
    max_range_points: Decimal = Decimal(50)

@dataclass
class RiskConfig:
    use_risk_filter: bool = False
    daily_loss_limit: Decimal = Decimal(150)
    profit_target: Decimal = Decimal(200)

@dataclass
class StopLossConfig:
    stop_loss_type: StopLossType = StopLossType.RANGE_BOUNDARY

@dataclass
class StrategyConfig:
    trade_size_in_lots: int = 1
    stop_loss_type: StopLossType = StopLossType.RANGE_BOUNDARY
    lot_rules: list[LotRule] = field(default_factory=list)
    range_filter: RangeFilter = field(default_factory=RangeFilter)
    risk_config: RiskConfig = field(default_factory=RiskConfig)
    stop_loss_config: StopLossConfig = field(default_factory=StopLossConfig)
from decimal import Decimal

def test_risk_config():
    """測試風險管理配置的邏輯"""
    
    print("🔍 測試風險管理配置邏輯...")
    
    # 測試1：默認配置（無風險管理）
    config_default = StrategyConfig(
        trade_size_in_lots=3,
        stop_loss_type=StopLossType.RANGE_BOUNDARY,
        lot_rules=[
            LotRule(use_trailing_stop=True, trailing_activation=Decimal(15), trailing_pullback=Decimal('0.20')),
            LotRule(use_trailing_stop=True, trailing_activation=Decimal(40), trailing_pullback=Decimal('0.20')),
            LotRule(use_trailing_stop=True, trailing_activation=Decimal(65), trailing_pullback=Decimal('0.20'))
        ]
    )
    
    print(f"\n📋 測試1：默認配置")
    print(f"  - hasattr(config, 'risk_config'): {hasattr(config_default, 'risk_config')}")
    if hasattr(config_default, 'risk_config'):
        print(f"  - config.risk_config.use_risk_filter: {config_default.risk_config.use_risk_filter}")
        print(f"  - config.risk_config.profit_target: {config_default.risk_config.profit_target}")
        print(f"  - profit_target > 0: {config_default.risk_config.profit_target > 0}")
        
        condition = (hasattr(config_default, 'risk_config') and 
                    config_default.risk_config.use_risk_filter and
                    config_default.risk_config.profit_target > 0)
        print(f"  - 完整條件結果: {condition}")
    
    # 測試2：明確禁用風險管理
    config_disabled = StrategyConfig(
        trade_size_in_lots=3,
        stop_loss_type=StopLossType.RANGE_BOUNDARY,
        lot_rules=[
            LotRule(use_trailing_stop=True, trailing_activation=Decimal(15), trailing_pullback=Decimal('0.20')),
            LotRule(use_trailing_stop=True, trailing_activation=Decimal(40), trailing_pullback=Decimal('0.20')),
            LotRule(use_trailing_stop=True, trailing_activation=Decimal(65), trailing_pullback=Decimal('0.20'))
        ],
        risk_config=RiskConfig(use_risk_filter=False, daily_loss_limit=Decimal(150), profit_target=Decimal(200))
    )
    
    print(f"\n📋 測試2：明確禁用風險管理")
    print(f"  - hasattr(config, 'risk_config'): {hasattr(config_disabled, 'risk_config')}")
    print(f"  - config.risk_config.use_risk_filter: {config_disabled.risk_config.use_risk_filter}")
    print(f"  - config.risk_config.profit_target: {config_disabled.risk_config.profit_target}")
    print(f"  - profit_target > 0: {config_disabled.risk_config.profit_target > 0}")
    
    condition = (hasattr(config_disabled, 'risk_config') and 
                config_disabled.risk_config.use_risk_filter and
                config_disabled.risk_config.profit_target > 0)
    print(f"  - 完整條件結果: {condition}")
    
    # 測試3：啟用風險管理
    config_enabled = StrategyConfig(
        trade_size_in_lots=3,
        stop_loss_type=StopLossType.RANGE_BOUNDARY,
        lot_rules=[
            LotRule(use_trailing_stop=True, trailing_activation=Decimal(15), trailing_pullback=Decimal('0.20')),
            LotRule(use_trailing_stop=True, trailing_activation=Decimal(40), trailing_pullback=Decimal('0.20')),
            LotRule(use_trailing_stop=True, trailing_activation=Decimal(65), trailing_pullback=Decimal('0.20'))
        ],
        risk_config=RiskConfig(use_risk_filter=True, daily_loss_limit=Decimal(150), profit_target=Decimal(200))
    )
    
    print(f"\n📋 測試3：啟用風險管理")
    print(f"  - hasattr(config, 'risk_config'): {hasattr(config_enabled, 'risk_config')}")
    print(f"  - config.risk_config.use_risk_filter: {config_enabled.risk_config.use_risk_filter}")
    print(f"  - config.risk_config.profit_target: {config_enabled.risk_config.profit_target}")
    print(f"  - profit_target > 0: {config_enabled.risk_config.profit_target > 0}")
    
    condition = (hasattr(config_enabled, 'risk_config') and 
                config_enabled.risk_config.use_risk_filter and
                config_enabled.risk_config.profit_target > 0)
    print(f"  - 完整條件結果: {condition}")

if __name__ == "__main__":
    test_risk_config()
