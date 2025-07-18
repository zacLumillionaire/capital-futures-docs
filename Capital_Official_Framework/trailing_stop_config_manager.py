#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
各口移動停利自訂功能配置管理器
實現移動停利參數的配置、驗證、保存和載入功能
"""

import os
import json
from dataclasses import dataclass, field, asdict
from typing import Dict, List, Optional, Tuple
from decimal import Decimal


@dataclass
class LotTrailingStopConfig:
    """單口移動停利配置"""
    lot_id: int
    enabled: bool = True
    activation_points: float = 25.0      # 啟動點數
    pullback_percent: float = 20.0       # 回撤百分比
    min_activation: float = 5.0          # 最小啟動點數
    max_activation: float = 200.0        # 最大啟動點數
    min_pullback: float = 5.0            # 最小回撤百分比
    max_pullback: float = 80.0           # 最大回撤百分比
    
    def validate(self) -> Tuple[bool, str]:
        """驗證配置參數"""
        if not self.min_activation <= self.activation_points <= self.max_activation:
            return False, f"啟動點數必須在{self.min_activation}-{self.max_activation}之間"
        
        if not self.min_pullback <= self.pullback_percent <= self.max_pullback:
            return False, f"回撤百分比必須在{self.min_pullback}-{self.max_pullback}%之間"
            
        return True, "配置有效"
    
    def to_dict(self) -> dict:
        """轉換為字典格式"""
        return {
            'lot_id': self.lot_id,
            'enabled': self.enabled,
            'activation_points': self.activation_points,
            'pullback_percent': self.pullback_percent
        }


@dataclass  
class MultiLotTrailingStopConfig:
    """多口移動停利配置管理器"""
    lot_configs: Dict[int, LotTrailingStopConfig] = field(default_factory=dict)
    global_enabled: bool = True
    max_lots: int = 3
    
    def add_lot_config(self, lot_id: int, config: LotTrailingStopConfig):
        """添加口數配置"""
        self.lot_configs[lot_id] = config
        
    def get_lot_config(self, lot_id: int) -> Optional[LotTrailingStopConfig]:
        """取得指定口數配置"""
        return self.lot_configs.get(lot_id)
        
    def validate_all(self) -> Tuple[bool, List[str]]:
        """驗證所有配置"""
        errors = []
        for lot_id, config in self.lot_configs.items():
            valid, message = config.validate()
            if not valid:
                errors.append(f"第{lot_id}口: {message}")
        
        return len(errors) == 0, errors
    
    def to_dict(self) -> dict:
        """轉換為字典格式"""
        return {
            'global_enabled': self.global_enabled,
            'max_lots': self.max_lots,
            'lot_configs': {
                str(lot_id): config.to_dict() 
                for lot_id, config in self.lot_configs.items()
            }
        }


class TrailingStopConfigManager:
    """移動停利配置管理器"""
    
    def __init__(self, config_file="trailing_stop_config.json"):
        self.config_file = config_file
        self.current_config = MultiLotTrailingStopConfig()
        self.console_enabled = True
        
    def save_config(self, config: MultiLotTrailingStopConfig) -> bool:
        """保存配置到文件"""
        try:
            config_dict = config.to_dict()
            
            with open(self.config_file, 'w', encoding='utf-8') as f:
                json.dump(config_dict, f, indent=2, ensure_ascii=False)
                
            if self.console_enabled:
                print(f"[TRAILING_CONFIG] ✅ 配置已保存到 {self.config_file}")
            return True
        except Exception as e:
            if self.console_enabled:
                print(f"[TRAILING_CONFIG] ❌ 保存配置失敗: {e}")
            return False
            
    def load_config(self) -> MultiLotTrailingStopConfig:
        """從文件載入配置"""
        try:
            if not os.path.exists(self.config_file):
                if self.console_enabled:
                    print(f"[TRAILING_CONFIG] 💡 配置文件不存在，使用預設配置")
                return self.get_default_config()
                
            with open(self.config_file, 'r', encoding='utf-8') as f:
                config_dict = json.load(f)
                
            config = MultiLotTrailingStopConfig()
            config.global_enabled = config_dict.get('global_enabled', True)
            config.max_lots = config_dict.get('max_lots', 3)
            
            for lot_id_str, lot_data in config_dict.get('lot_configs', {}).items():
                lot_id = int(lot_id_str)
                lot_config = LotTrailingStopConfig(
                    lot_id=lot_id,
                    enabled=lot_data.get('enabled', True),
                    activation_points=lot_data.get('activation_points', 25.0),
                    pullback_percent=lot_data.get('pullback_percent', 20.0)
                )
                config.add_lot_config(lot_id, lot_config)
                
            if self.console_enabled:
                print(f"[TRAILING_CONFIG] ✅ 配置已從 {self.config_file} 載入")
            return config
        except Exception as e:
            if self.console_enabled:
                print(f"[TRAILING_CONFIG] ❌ 載入配置失敗: {e}")
            return self.get_default_config()
    
    def get_default_config(self) -> MultiLotTrailingStopConfig:
        """取得預設配置"""
        config = MultiLotTrailingStopConfig()
        
        # 預設配置：基於實施計畫中的平衡配置
        default_configs = [
            LotTrailingStopConfig(1, True, 20.0, 10.0),  # 第1口：20點啟動，10%回撤
            LotTrailingStopConfig(2, True, 35.0, 10.0),  # 第2口：35點啟動，10%回撤
            LotTrailingStopConfig(3, True, 40.0, 20.0),  # 第3口：40點啟動，20%回撤
        ]
        
        for lot_config in default_configs:
            config.add_lot_config(lot_config.lot_id, lot_config)
            
        if self.console_enabled:
            print("[TRAILING_CONFIG] 💡 使用預設配置")
            
        return config
    
    def get_preset_configs(self) -> Dict[str, MultiLotTrailingStopConfig]:
        """取得預設配置選項"""
        presets = {}
        
        # 保守配置
        conservative = MultiLotTrailingStopConfig()
        conservative.add_lot_config(1, LotTrailingStopConfig(1, True, 20.0, 10.0))
        conservative.add_lot_config(2, LotTrailingStopConfig(2, True, 40.0, 10.0))
        conservative.add_lot_config(3, LotTrailingStopConfig(3, True, 50.0, 20.0))
        presets["保守配置 (10:15-10:30)"] = conservative
        
        # 積極配置
        aggressive = MultiLotTrailingStopConfig()
        aggressive.add_lot_config(1, LotTrailingStopConfig(1, True, 15.0, 10.0))
        aggressive.add_lot_config(2, LotTrailingStopConfig(2, True, 35.0, 10.0))
        aggressive.add_lot_config(3, LotTrailingStopConfig(3, True, 45.0, 20.0))
        presets["積極配置 (11:00-11:02)"] = aggressive
        
        # 平衡配置（預設）
        balanced = self.get_default_config()
        presets["平衡配置 (08:58-09:02)"] = balanced
        
        return presets
    
    def apply_preset(self, preset_name: str) -> bool:
        """應用預設配置"""
        try:
            presets = self.get_preset_configs()
            if preset_name in presets:
                self.current_config = presets[preset_name]
                success = self.save_config(self.current_config)
                if success and self.console_enabled:
                    print(f"[TRAILING_CONFIG] ✅ 已應用預設配置: {preset_name}")
                return success
            else:
                if self.console_enabled:
                    print(f"[TRAILING_CONFIG] ❌ 未找到預設配置: {preset_name}")
                return False
        except Exception as e:
            if self.console_enabled:
                print(f"[TRAILING_CONFIG] ❌ 應用預設配置失敗: {e}")
            return False
    
    def get_lot_trailing_params(self, lot_id: int) -> dict:
        """取得指定口數的移動停利參數（供交易邏輯使用）"""
        lot_config = self.current_config.get_lot_config(lot_id)
        if lot_config and lot_config.enabled and self.current_config.global_enabled:
            return {
                'trailing_activation_points': lot_config.activation_points,
                'trailing_pullback_percent': lot_config.pullback_percent / 100.0,  # 轉換為小數
                'enabled': True
            }
        else:
            # 返回預設值（向後相容）
            return {
                'trailing_activation_points': 15.0,
                'trailing_pullback_percent': 0.20,
                'enabled': False
            }
