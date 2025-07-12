#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
多組多口策略配置數據類
定義策略配置的數據結構和預設值
"""

import json
from dataclasses import dataclass, field
from decimal import Decimal
from typing import List, Optional
from enum import Enum, auto

class StopLossType(Enum):
    """停損類型枚舉"""
    RANGE_BOUNDARY = auto()    # 區間邊界停損
    FIXED_POINTS = auto()      # 固定點數停損

class PositionStatus(Enum):
    """部位狀態枚舉"""
    ACTIVE = "ACTIVE"
    EXITED = "EXITED"

class GroupStatus(Enum):
    """策略組狀態枚舉"""
    WAITING = "WAITING"        # 等待進場
    ACTIVE = "ACTIVE"          # 有活躍部位
    COMPLETED = "COMPLETED"    # 全部出場
    CANCELLED = "CANCELLED"    # 已取消

@dataclass
class LotRule:
    """單口風險管理規則"""
    lot_id: int                                    # 口數編號 (1,2,3)
    use_trailing_stop: bool = True                 # 使用移動停利
    trailing_activation: Optional[Decimal] = None  # 啟動點數
    trailing_pullback: Optional[Decimal] = None    # 回撤比例 (0.20 = 20%)
    protective_stop_multiplier: Optional[Decimal] = None  # 保護倍數
    fixed_tp_points: Optional[Decimal] = None      # 固定停利點數
    
    def to_json(self) -> str:
        """轉換為JSON字符串"""
        return json.dumps({
            'lot_id': self.lot_id,
            'use_trailing_stop': self.use_trailing_stop,
            'trailing_activation': float(self.trailing_activation) if self.trailing_activation else None,
            'trailing_pullback': float(self.trailing_pullback) if self.trailing_pullback else None,
            'protective_stop_multiplier': float(self.protective_stop_multiplier) if self.protective_stop_multiplier else None,
            'fixed_tp_points': float(self.fixed_tp_points) if self.fixed_tp_points else None
        })
    
    @classmethod
    def from_json(cls, json_str: str) -> 'LotRule':
        """從JSON字符串創建"""
        data = json.loads(json_str)
        return cls(
            lot_id=data['lot_id'],
            use_trailing_stop=data['use_trailing_stop'],
            trailing_activation=Decimal(str(data['trailing_activation'])) if data['trailing_activation'] else None,
            trailing_pullback=Decimal(str(data['trailing_pullback'])) if data['trailing_pullback'] else None,
            protective_stop_multiplier=Decimal(str(data['protective_stop_multiplier'])) if data['protective_stop_multiplier'] else None,
            fixed_tp_points=Decimal(str(data['fixed_tp_points'])) if data['fixed_tp_points'] else None
        )

@dataclass
class StrategyGroupConfig:
    """策略組配置"""
    group_id: int                                  # 組別ID (1,2,3...)
    lots_per_group: int                           # 每組口數 (1-3)
    lot_rules: List[LotRule]                      # 每口規則列表
    is_active: bool = True                        # 是否啟用
    entry_price: Optional[Decimal] = None         # 實際進場價格
    entry_time: Optional[str] = None              # 進場時間
    status: GroupStatus = GroupStatus.WAITING     # 組狀態

@dataclass
class MultiGroupStrategyConfig:
    """多組策略總配置"""
    total_groups: int                              # 總組數 (1-5)
    lots_per_group: int                           # 每組口數 (1-3)
    stop_loss_type: StopLossType = StopLossType.RANGE_BOUNDARY
    groups: List[StrategyGroupConfig] = field(default_factory=list)
    max_daily_entries: int = 1                    # 每日最大進場次數
    
    def __post_init__(self):
        """初始化後處理"""
        if not self.groups:
            self.groups = self._create_default_groups()
    
    def _create_default_groups(self) -> List[StrategyGroupConfig]:
        """創建預設組配置"""
        groups = []
        for group_id in range(1, self.total_groups + 1):
            lot_rules = self._create_default_lot_rules()
            groups.append(StrategyGroupConfig(
                group_id=group_id,
                lots_per_group=self.lots_per_group,
                lot_rules=lot_rules
            ))
        return groups
    
    def _create_default_lot_rules(self) -> List[LotRule]:
        """創建預設口數規則 - 🔧 用戶自定義配置"""
        default_rules = [
            # 第1口：快速移動停利 (15點啟動, 10%回撤)
            LotRule(
                lot_id=1,
                use_trailing_stop=True,
                trailing_activation=Decimal('15'),
                trailing_pullback=Decimal('0.10')  # 🔧 修改：20% → 10%
            ),
            # 第2口：中等移動停利 + 保護 (40點啟動, 10%回撤, 2倍保護)
            LotRule(
                lot_id=2,
                use_trailing_stop=True,
                trailing_activation=Decimal('40'),
                trailing_pullback=Decimal('0.10'),  # 🔧 修改：20% → 10%
                protective_stop_multiplier=Decimal('2.0')
            ),
            # 第3口：較大移動停利 + 保護 (41點啟動, 20%回撤, 2倍保護)
            LotRule(
                lot_id=3,
                use_trailing_stop=True,
                trailing_activation=Decimal('41'),  # 🔧 修改：65點 → 41點
                trailing_pullback=Decimal('0.20'),  # 🔧 保持：20%回撤
                protective_stop_multiplier=Decimal('2.0')
            )
        ]
        
        return default_rules[:self.lots_per_group]
    
    def get_total_positions(self) -> int:
        """取得總部位數"""
        return self.total_groups * self.lots_per_group
    
    def get_active_groups(self) -> List[StrategyGroupConfig]:
        """取得啟用的組"""
        return [group for group in self.groups if group.is_active]
    
    def get_group_by_id(self, group_id: int) -> Optional[StrategyGroupConfig]:
        """根據ID取得組配置"""
        for group in self.groups:
            if group.group_id == group_id:
                return group
        return None
    
    def to_summary_string(self) -> str:
        """轉換為摘要字符串"""
        active_groups = len(self.get_active_groups())
        total_positions = self.get_total_positions()
        
        return f"""多組策略配置摘要:
📊 總組數: {self.total_groups} (啟用: {active_groups})
📊 每組口數: {self.lots_per_group}
📊 總部位數: {total_positions}
📊 停損類型: {'區間邊界' if self.stop_loss_type == StopLossType.RANGE_BOUNDARY else '固定點數'}
📊 每日進場限制: {self.max_daily_entries}次

組別詳情:"""

def create_preset_configs() -> dict:
    """創建預設配置選項"""
    return {
        "保守配置 (1口×2組)": MultiGroupStrategyConfig(
            total_groups=2,
            lots_per_group=1
        ),
        "平衡配置 (2口×2組)": MultiGroupStrategyConfig(
            total_groups=2,
            lots_per_group=2
        ),
        "標準配置 (3口×1組)": MultiGroupStrategyConfig(
            total_groups=1,
            lots_per_group=3
        ),
        "積極配置 (3口×3組)": MultiGroupStrategyConfig(
            total_groups=3,
            lots_per_group=3
        ),
        "測試配置 (1口×1組)": MultiGroupStrategyConfig(
            total_groups=1,
            lots_per_group=1
        )
    }

def validate_config(config: MultiGroupStrategyConfig) -> List[str]:
    """驗證配置有效性"""
    errors = []
    
    # 檢查基本範圍
    if not (1 <= config.total_groups <= 5):
        errors.append("總組數必須在1-5之間")
    
    if not (1 <= config.lots_per_group <= 3):
        errors.append("每組口數必須在1-3之間")
    
    # 檢查組配置
    if len(config.groups) != config.total_groups:
        errors.append("組配置數量與總組數不符")
    
    # 檢查每組的口數規則
    for group in config.groups:
        if len(group.lot_rules) != config.lots_per_group:
            errors.append(f"組{group.group_id}的口數規則數量不正確")
        
        # 檢查口數編號連續性
        lot_ids = [rule.lot_id for rule in group.lot_rules]
        expected_ids = list(range(1, config.lots_per_group + 1))
        if sorted(lot_ids) != expected_ids:
            errors.append(f"組{group.group_id}的口數編號不連續")
    
    return errors

if __name__ == "__main__":
    # 測試配置類
    print("🧪 測試多組策略配置類")
    print("=" * 50)
    
    # 測試預設配置
    presets = create_preset_configs()
    
    for name, config in presets.items():
        print(f"\n📋 {name}:")
        print(config.to_summary_string())
        
        # 驗證配置
        errors = validate_config(config)
        if errors:
            print("❌ 配置錯誤:")
            for error in errors:
                print(f"   - {error}")
        else:
            print("✅ 配置有效")
        
        print(f"📊 總部位數: {config.get_total_positions()}")
    
    # 測試JSON序列化
    print(f"\n🧪 測試JSON序列化:")
    test_rule = LotRule(
        lot_id=1,
        use_trailing_stop=True,
        trailing_activation=Decimal('15'),
        trailing_pullback=Decimal('0.20')
    )
    
    json_str = test_rule.to_json()
    print(f"JSON: {json_str}")
    
    restored_rule = LotRule.from_json(json_str)
    print(f"還原: lot_id={restored_rule.lot_id}, activation={restored_rule.trailing_activation}")
    
    print("\n✅ 配置類測試完成")
