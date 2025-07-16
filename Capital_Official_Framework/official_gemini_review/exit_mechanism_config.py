#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
平倉機制配置模組
基於回測程式邏輯，定義平倉機制的配置結構和預設規則
"""

from dataclasses import dataclass, field
from typing import List, Dict, Optional, Union
from decimal import Decimal
import json
import logging

logger = logging.getLogger(__name__)

@dataclass
class LotExitRule:
    """
    口數平倉規則配置
    對應回測程式的 LotRule 結構
    """
    lot_number: int                                    # 口數編號 (1, 2, 3)
    trailing_activation_points: int                   # 移動停利啟動點位 (15, 40, 65)
    trailing_pullback_ratio: float = 0.20            # 回撤比例 (20%)
    protective_stop_multiplier: Optional[float] = None # 保護倍數 (2.0)
    description: str = ""                             # 規則描述
    
    def __post_init__(self):
        """初始化後驗證"""
        if self.lot_number not in [1, 2, 3]:
            raise ValueError(f"口數編號必須為 1, 2, 3，當前: {self.lot_number}")
        
        if self.trailing_activation_points <= 0:
            raise ValueError(f"啟動點位必須大於0，當前: {self.trailing_activation_points}")
        
        if not 0.1 <= self.trailing_pullback_ratio <= 0.5:
            raise ValueError(f"回撤比例必須在 0.1-0.5 之間，當前: {self.trailing_pullback_ratio}")
        
        if self.protective_stop_multiplier is not None and self.protective_stop_multiplier <= 0:
            raise ValueError(f"保護倍數必須大於0，當前: {self.protective_stop_multiplier}")
        
        # 設定預設描述
        if not self.description:
            protection_text = f", {self.protective_stop_multiplier}倍保護" if self.protective_stop_multiplier else ""
            self.description = f"第{self.lot_number}口: {self.trailing_activation_points}點啟動{protection_text}"
    
    def to_dict(self) -> Dict:
        """轉換為字典格式"""
        return {
            'lot_number': self.lot_number,
            'trailing_activation_points': self.trailing_activation_points,
            'trailing_pullback_ratio': self.trailing_pullback_ratio,
            'protective_stop_multiplier': self.protective_stop_multiplier,
            'description': self.description
        }
    
    def to_json(self) -> str:
        """轉換為JSON字串"""
        return json.dumps(self.to_dict(), ensure_ascii=False)
    
    @classmethod
    def from_dict(cls, data: Dict) -> 'LotExitRule':
        """從字典創建實例"""
        return cls(
            lot_number=data['lot_number'],
            trailing_activation_points=data['trailing_activation_points'],
            trailing_pullback_ratio=data.get('trailing_pullback_ratio', 0.20),
            protective_stop_multiplier=data.get('protective_stop_multiplier'),
            description=data.get('description', "")
        )
    
    @classmethod
    def from_json(cls, json_str: str) -> 'LotExitRule':
        """從JSON字串創建實例"""
        return cls.from_dict(json.loads(json_str))


@dataclass
class GroupExitConfig:
    """
    組別平倉配置
    對應回測程式的 StrategyConfig
    """
    group_id: str                                     # 組別ID
    total_lots: int = 3                              # 總口數 (預設3口)
    stop_loss_type: str = "RANGE_BOUNDARY"           # 停損類型 (區間邊緣)
    lot_rules: List[LotExitRule] = field(default_factory=list)  # 口數規則列表
    enabled: bool = True                             # 是否啟用平倉機制
    console_logging: bool = True                     # 是否啟用Console日誌
    
    def __post_init__(self):
        """初始化後處理"""
        if not self.lot_rules:
            self.lot_rules = self._create_default_lot_rules()
        
        # 驗證規則數量與總口數一致
        if len(self.lot_rules) != self.total_lots:
            raise ValueError(f"規則數量 ({len(self.lot_rules)}) 與總口數 ({self.total_lots}) 不一致")
        
        # 驗證口數編號連續性
        lot_numbers = [rule.lot_number for rule in self.lot_rules]
        expected_numbers = list(range(1, self.total_lots + 1))
        if sorted(lot_numbers) != expected_numbers:
            raise ValueError(f"口數編號不連續: {lot_numbers}, 期望: {expected_numbers}")
    
    def _create_default_lot_rules(self) -> List[LotExitRule]:
        """
        創建預設口數規則
        對應回測程式的標準配置
        """
        default_rules = [
            LotExitRule(
                lot_number=1, 
                trailing_activation_points=15, 
                trailing_pullback_ratio=0.20,
                protective_stop_multiplier=None,
                description="第1口: 15點啟動移動停利"
            ),
            LotExitRule(
                lot_number=2, 
                trailing_activation_points=40, 
                trailing_pullback_ratio=0.20,
                protective_stop_multiplier=2.0,
                description="第2口: 40點啟動移動停利, 2倍保護"
            ),
            LotExitRule(
                lot_number=3, 
                trailing_activation_points=65, 
                trailing_pullback_ratio=0.20,
                protective_stop_multiplier=2.0,
                description="第3口: 65點啟動移動停利, 2倍保護"
            )
        ]
        
        # 根據總口數返回對應數量的規則
        return default_rules[:self.total_lots]
    
    def get_lot_rule(self, lot_number: int) -> Optional[LotExitRule]:
        """取得指定口數的規則"""
        for rule in self.lot_rules:
            if rule.lot_number == lot_number:
                return rule
        return None
    
    def to_dict(self) -> Dict:
        """轉換為字典格式"""
        return {
            'group_id': self.group_id,
            'total_lots': self.total_lots,
            'stop_loss_type': self.stop_loss_type,
            'lot_rules': [rule.to_dict() for rule in self.lot_rules],
            'enabled': self.enabled,
            'console_logging': self.console_logging
        }
    
    def to_json(self) -> str:
        """轉換為JSON字串"""
        return json.dumps(self.to_dict(), ensure_ascii=False, indent=2)
    
    @classmethod
    def from_dict(cls, data: Dict) -> 'GroupExitConfig':
        """從字典創建實例"""
        lot_rules = [LotExitRule.from_dict(rule_data) for rule_data in data.get('lot_rules', [])]
        
        return cls(
            group_id=data['group_id'],
            total_lots=data.get('total_lots', 3),
            stop_loss_type=data.get('stop_loss_type', "RANGE_BOUNDARY"),
            lot_rules=lot_rules,
            enabled=data.get('enabled', True),
            console_logging=data.get('console_logging', True)
        )
    
    @classmethod
    def from_json(cls, json_str: str) -> 'GroupExitConfig':
        """從JSON字串創建實例"""
        return cls.from_dict(json.loads(json_str))


class ExitMechanismConfigManager:
    """平倉機制配置管理器"""
    
    def __init__(self, console_enabled: bool = True):
        self.console_enabled = console_enabled
        self.preset_configs = self._create_preset_configs()
    
    def _create_preset_configs(self) -> Dict[str, GroupExitConfig]:
        """創建預設配置"""
        presets = {
            "回測標準配置 (3口)": GroupExitConfig(
                group_id="backtest_standard_3lots",
                total_lots=3,
                stop_loss_type="RANGE_BOUNDARY",
                lot_rules=[
                    LotExitRule(1, 15, 0.20, None),
                    LotExitRule(2, 40, 0.20, 2.0),
                    LotExitRule(3, 65, 0.20, 2.0)
                ]
            ),
            
            "保守配置 (2口)": GroupExitConfig(
                group_id="conservative_2lots",
                total_lots=2,
                stop_loss_type="RANGE_BOUNDARY",
                lot_rules=[
                    LotExitRule(1, 15, 0.20, None),
                    LotExitRule(2, 30, 0.20, 1.5)
                ]
            ),
            
            "單口測試配置": GroupExitConfig(
                group_id="single_lot_test",
                total_lots=1,
                stop_loss_type="RANGE_BOUNDARY",
                lot_rules=[
                    LotExitRule(1, 15, 0.20, None)
                ]
            )
        }
        
        if self.console_enabled:
            print("[EXIT_CONFIG] ⚙️ 創建預設平倉配置:")
            for name, config in presets.items():
                print(f"[EXIT_CONFIG]   📋 {name}: {config.total_lots}口")
                for rule in config.lot_rules:
                    protection = f", {rule.protective_stop_multiplier}倍保護" if rule.protective_stop_multiplier else ""
                    print(f"[EXIT_CONFIG]     - 第{rule.lot_number}口: {rule.trailing_activation_points}點啟動{protection}")
        
        return presets
    
    def get_preset_config(self, preset_name: str) -> Optional[GroupExitConfig]:
        """取得預設配置"""
        config = self.preset_configs.get(preset_name)
        if config and self.console_enabled:
            print(f"[EXIT_CONFIG] 📋 載入預設配置: {preset_name}")
        return config
    
    def get_default_config_for_lots(self, total_lots: int) -> GroupExitConfig:
        """根據口數取得預設配置"""
        if total_lots == 1:
            return self.get_preset_config("單口測試配置")
        elif total_lots == 2:
            return self.get_preset_config("保守配置 (2口)")
        else:
            return self.get_preset_config("回測標準配置 (3口)")
    
    def create_custom_config(self, group_id: str, total_lots: int, 
                           custom_rules: Optional[List[Dict]] = None) -> GroupExitConfig:
        """創建自訂配置"""
        if custom_rules:
            lot_rules = [LotExitRule.from_dict(rule_data) for rule_data in custom_rules]
        else:
            # 使用預設規則
            lot_rules = None
        
        config = GroupExitConfig(
            group_id=group_id,
            total_lots=total_lots,
            lot_rules=lot_rules or []
        )
        
        if self.console_enabled:
            print(f"[EXIT_CONFIG] 🔧 創建自訂配置: {group_id} ({total_lots}口)")
        
        return config
    
    def validate_config(self, config: GroupExitConfig) -> bool:
        """驗證配置有效性"""
        try:
            # 基本驗證已在 __post_init__ 中完成
            
            # 額外業務邏輯驗證
            if config.total_lots > 3:
                if self.console_enabled:
                    print(f"[EXIT_CONFIG] ⚠️ 警告: 口數超過建議上限 ({config.total_lots} > 3)")
            
            # 檢查啟動點位是否合理遞增
            activation_points = [rule.trailing_activation_points for rule in config.lot_rules]
            if activation_points != sorted(activation_points):
                if self.console_enabled:
                    print(f"[EXIT_CONFIG] ⚠️ 警告: 啟動點位未遞增排序: {activation_points}")
            
            if self.console_enabled:
                print(f"[EXIT_CONFIG] ✅ 配置驗證通過: {config.group_id}")
            
            return True
            
        except Exception as e:
            if self.console_enabled:
                print(f"[EXIT_CONFIG] ❌ 配置驗證失敗: {e}")
            logger.error(f"配置驗證失敗: {e}")
            return False


# 全域配置管理器實例
exit_config_manager = ExitMechanismConfigManager()


def get_default_exit_config_for_multi_group() -> GroupExitConfig:
    """
    取得多組策略系統的預設平倉配置
    配置為1組3口模式，對應回測程式邏輯
    """
    return exit_config_manager.get_preset_config("回測標準配置 (3口)")


if __name__ == "__main__":
    # 測試配置
    print("=== 平倉機制配置測試 ===")
    
    # 測試預設配置
    config = get_default_exit_config_for_multi_group()
    print(f"預設配置: {config.group_id}")
    print(f"JSON: {config.to_json()}")
    
    # 測試自訂配置
    custom_config = exit_config_manager.create_custom_config("test_group", 2)
    print(f"自訂配置: {custom_config.group_id}")
