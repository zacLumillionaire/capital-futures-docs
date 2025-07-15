# Task 4: 停利機制優化設計

## 📋 任務概述

分析現有移動停利機制，設計支援移動停利或固定點數停利的靈活配置，包括各口獨立設定功能。

## 🔍 現有移動停利機制分析

### 4.1 單一策略移動停利機制

#### 固定移動停利邏輯
```python
def enter_position_safe(self, direction, price, time_str):
    """建倉時固定移動停利參數"""
    self.current_position = {
        'direction': direction,
        'entry_price': price,
        'peak_price': price,
        'trailing_activated': False,
        'trailing_activation_points': 15,    # 固定15點啟動
        'trailing_pullback_percent': 0.20    # 固定20%回撤
    }

def check_trailing_stop_logic(self, price, time_str):
    """固定移動停利檢查邏輯"""
    activation_points = self.current_position['trailing_activation_points']  # 固定15點
    pullback_percent = self.current_position['trailing_pullback_percent']    # 固定20%
    
    # 檢查啟動條件（固定15點）
    if not trailing_activated:
        if direction == "LONG":
            activation_triggered = price >= entry_price + activation_points
    
    # 檢查回撤觸發（固定20%）
    if trailing_activated:
        pullback_amount = (peak_price - entry_price) * pullback_percent
        trigger_price = peak_price - pullback_amount
        if price <= trigger_price:
            self.exit_position_safe(trigger_price, time_str, "移動停利")
```

### 4.2 多組策略移動停利機制

#### 分層移動停利配置
```python
# exit_mechanism_config.py 中的配置
@dataclass
class LotExitRule:
    lot_number: int
    trailing_activation_points: float = 15.0    # 固定啟動點數
    trailing_pullback_percent: float = 0.20     # 固定回撤百分比
    protective_stop_multiplier: Optional[float] = None

# 預設配置範例
lot_rules = [
    LotExitRule(1, 15.0, 0.20, None),    # 第1口：15點啟動，20%回撤
    LotExitRule(2, 40.0, 0.20, 2.0),     # 第2口：40點啟動，20%回撤
    LotExitRule(3, 65.0, 0.20, 2.0)      # 第3口：65點啟動，20%回撤
]
```

#### 分散式組件架構
```python
# 移動停利系統組件
self.trailing_stop_activator    # 啟動器：檢查15/40/65點啟動
self.peak_price_tracker         # 峰值追蹤器：更新峰值價格
self.drawdown_monitor          # 回撤監控器：檢查20%回撤觸發
```

### 4.3 現有機制限制

1. **停利方式固定**：只能使用移動停利，無法指定固定點數停利
2. **參數固定**：啟動點數和回撤百分比固定，無法靈活調整
3. **各口相似**：雖然啟動點數不同，但回撤邏輯相同
4. **無固定停利**：無法設定簡單的固定點數停利

## 🎯 靈活停利配置設計

### 5.1 核心設計原則

1. **停利方式可選**：支援移動停利或固定點數停利
2. **各口獨立配置**：每口可有不同的停利設定
3. **參數可調**：移動停利的啟動點數和回撤比例可調
4. **混合策略**：同一時段不同口數可使用不同停利方式

### 5.2 停利配置結構設計

#### 停利類型枚舉
```python
from enum import Enum

class TakeProfitType(Enum):
    TRAILING_STOP = "trailing_stop"      # 移動停利
    FIXED_POINTS = "fixed_points"        # 固定點數停利
    PERCENTAGE_GAIN = "percentage_gain"  # 百分比獲利停利
    DISABLED = "disabled"                # 停用停利

class TakeProfitMode(Enum):
    UNIFIED = "unified"                  # 統一停利（所有口相同）
    INDIVIDUAL = "individual"            # 各口獨立停利
```

#### 停利配置結構
```python
@dataclass
class TakeProfitConfig:
    """停利配置"""
    take_profit_type: TakeProfitType
    take_profit_mode: TakeProfitMode
    
    # 統一停利配置
    unified_config: Optional[Dict] = None
    
    # 各口獨立配置
    individual_configs: Dict[int, Dict] = field(default_factory=dict)
    
    # 是否啟用
    enabled: bool = True
    
    def to_dict(self) -> Dict:
        return {
            'take_profit_type': self.take_profit_type.value,
            'take_profit_mode': self.take_profit_mode.value,
            'unified_config': self.unified_config,
            'individual_configs': self.individual_configs,
            'enabled': self.enabled
        }

# 各口獨立配置範例
individual_take_profit_example = {
    1: {  # 第1口：移動停利
        'type': TakeProfitType.TRAILING_STOP,
        'activation_points': 15,
        'pullback_percent': 0.10,
        'enabled': True
    },
    2: {  # 第2口：固定點數停利
        'type': TakeProfitType.FIXED_POINTS,
        'points': 30,
        'enabled': True
    },
    3: {  # 第3口：移動停利（不同參數）
        'type': TakeProfitType.TRAILING_STOP,
        'activation_points': 50,
        'pullback_percent': 0.20,
        'enabled': True
    }
}
```

#### 整合到時段配置
```python
# 整合到多時段配置中
time_interval_config = {
    'id': 'morning_1',
    'start_time': '08:46',
    'end_time': '08:48',
    'direction_config': {
        # ... 方向配置
    },
    'stop_loss_config': {
        # ... 停損配置
    },
    'take_profit_config': {
        'take_profit_type': TakeProfitType.INDIVIDUAL,
        'take_profit_mode': TakeProfitMode.INDIVIDUAL,
        'individual_configs': {
            1: {
                'type': 'trailing_stop',
                'activation_points': 15,
                'pullback_percent': 0.10
            },
            2: {
                'type': 'fixed_points',
                'points': 30
            },
            3: {
                'type': 'trailing_stop',
                'activation_points': 50,
                'pullback_percent': 0.20
            }
        }
    }
}
```

### 5.3 核心函數重構

#### 統一停利計算函數
```python
class FlexibleTakeProfitCalculator:
    """靈活停利計算器"""
    
    def __init__(self, take_profit_config: TakeProfitConfig):
        self.config = take_profit_config
        self.position_states = {}  # 存儲各部位的停利狀態
    
    def initialize_position(self, position_id: int, lot_number: int, direction: str,
                          entry_price: float, entry_time: str):
        """初始化部位停利狀態"""
        
        if self.config.take_profit_mode == TakeProfitMode.UNIFIED:
            lot_config = self.config.unified_config
        else:
            lot_config = self.config.individual_configs.get(lot_number, {})
        
        take_profit_type = TakeProfitType(lot_config.get('type', 'trailing_stop'))
        
        if take_profit_type == TakeProfitType.TRAILING_STOP:
            self.position_states[position_id] = {
                'type': 'trailing_stop',
                'direction': direction,
                'entry_price': entry_price,
                'peak_price': entry_price,
                'activation_points': lot_config.get('activation_points', 15),
                'pullback_percent': lot_config.get('pullback_percent', 0.20),
                'activated': False,
                'target_price': None
            }
        
        elif take_profit_type == TakeProfitType.FIXED_POINTS:
            points = lot_config.get('points', 30)
            if direction == "LONG":
                target_price = entry_price + points
            else:
                target_price = entry_price - points
            
            self.position_states[position_id] = {
                'type': 'fixed_points',
                'direction': direction,
                'entry_price': entry_price,
                'target_price': target_price,
                'points': points
            }
        
        elif take_profit_type == TakeProfitType.PERCENTAGE_GAIN:
            percentage = lot_config.get('percentage', 0.05)  # 5%
            if direction == "LONG":
                target_price = entry_price * (1 + percentage)
            else:
                target_price = entry_price * (1 - percentage)
            
            self.position_states[position_id] = {
                'type': 'percentage_gain',
                'direction': direction,
                'entry_price': entry_price,
                'target_price': target_price,
                'percentage': percentage
            }
    
    def check_take_profit_trigger(self, position_id: int, current_price: float,
                                current_time: str) -> Optional[Dict]:
        """檢查停利觸發"""
        
        if position_id not in self.position_states:
            return None
        
        state = self.position_states[position_id]
        
        if state['type'] == 'trailing_stop':
            return self._check_trailing_stop_trigger(position_id, current_price, current_time)
        
        elif state['type'] == 'fixed_points':
            return self._check_fixed_points_trigger(position_id, current_price, current_time)
        
        elif state['type'] == 'percentage_gain':
            return self._check_percentage_gain_trigger(position_id, current_price, current_time)
        
        return None
    
    def _check_trailing_stop_trigger(self, position_id: int, current_price: float,
                                   current_time: str) -> Optional[Dict]:
        """檢查移動停利觸發"""
        state = self.position_states[position_id]
        direction = state['direction']
        entry_price = state['entry_price']
        peak_price = state['peak_price']
        activation_points = state['activation_points']
        pullback_percent = state['pullback_percent']
        activated = state['activated']
        
        # 更新峰值價格
        if direction == "LONG":
            if current_price > peak_price:
                state['peak_price'] = current_price
                peak_price = current_price
        else:
            if current_price < peak_price:
                state['peak_price'] = current_price
                peak_price = current_price
        
        # 檢查啟動條件
        if not activated:
            if direction == "LONG":
                activation_triggered = current_price >= entry_price + activation_points
            else:
                activation_triggered = current_price <= entry_price - activation_points
            
            if activation_triggered:
                state['activated'] = True
                return {
                    'type': 'activation',
                    'position_id': position_id,
                    'activation_price': current_price,
                    'activation_time': current_time
                }
        
        # 檢查回撤觸發
        if activated:
            if direction == "LONG":
                total_gain = peak_price - entry_price
                pullback_amount = total_gain * pullback_percent
                trigger_price = peak_price - pullback_amount
                
                if current_price <= trigger_price:
                    return {
                        'type': 'exit',
                        'position_id': position_id,
                        'exit_price': trigger_price,
                        'exit_time': current_time,
                        'reason': f'移動停利 (峰值:{peak_price:.0f} 回撤:{pullback_amount:.1f}點)'
                    }
            
            else:  # SHORT
                total_gain = entry_price - peak_price
                pullback_amount = total_gain * pullback_percent
                trigger_price = peak_price + pullback_amount
                
                if current_price >= trigger_price:
                    return {
                        'type': 'exit',
                        'position_id': position_id,
                        'exit_price': trigger_price,
                        'exit_time': current_time,
                        'reason': f'移動停利 (峰值:{peak_price:.0f} 回撤:{pullback_amount:.1f}點)'
                    }
        
        return None
    
    def _check_fixed_points_trigger(self, position_id: int, current_price: float,
                                  current_time: str) -> Optional[Dict]:
        """檢查固定點數停利觸發"""
        state = self.position_states[position_id]
        direction = state['direction']
        target_price = state['target_price']
        
        triggered = False
        if direction == "LONG":
            triggered = current_price >= target_price
        else:
            triggered = current_price <= target_price
        
        if triggered:
            return {
                'type': 'exit',
                'position_id': position_id,
                'exit_price': target_price,
                'exit_time': current_time,
                'reason': f'固定點數停利 {state["points"]}點'
            }
        
        return None
    
    def _check_percentage_gain_trigger(self, position_id: int, current_price: float,
                                     current_time: str) -> Optional[Dict]:
        """檢查百分比獲利停利觸發"""
        state = self.position_states[position_id]
        direction = state['direction']
        target_price = state['target_price']
        
        triggered = False
        if direction == "LONG":
            triggered = current_price >= target_price
        else:
            triggered = current_price <= target_price
        
        if triggered:
            return {
                'type': 'exit',
                'position_id': position_id,
                'exit_price': target_price,
                'exit_time': current_time,
                'reason': f'百分比停利 {state["percentage"]*100:.1f}%'
            }
        
        return None
```

### 5.4 配置模板系統

#### 預設配置模板
```python
class TakeProfitConfigTemplates:
    """停利配置模板"""
    
    @staticmethod
    def get_trailing_stop_template(activation_points: float = 15, pullback_percent: float = 0.20):
        """移動停利模板（原有邏輯）"""
        return TakeProfitConfig(
            take_profit_type=TakeProfitType.TRAILING_STOP,
            take_profit_mode=TakeProfitMode.UNIFIED,
            unified_config={
                'activation_points': activation_points,
                'pullback_percent': pullback_percent
            },
            enabled=True
        )
    
    @staticmethod
    def get_fixed_points_template(points: float = 30):
        """固定點數停利模板"""
        return TakeProfitConfig(
            take_profit_type=TakeProfitType.FIXED_POINTS,
            take_profit_mode=TakeProfitMode.UNIFIED,
            unified_config={
                'points': points
            },
            enabled=True
        )
    
    @staticmethod
    def get_mixed_strategy_template():
        """混合策略模板"""
        return TakeProfitConfig(
            take_profit_type=TakeProfitType.TRAILING_STOP,
            take_profit_mode=TakeProfitMode.INDIVIDUAL,
            individual_configs={
                1: {
                    'type': 'trailing_stop',
                    'activation_points': 15,
                    'pullback_percent': 0.10
                },
                2: {
                    'type': 'fixed_points',
                    'points': 30
                },
                3: {
                    'type': 'trailing_stop',
                    'activation_points': 50,
                    'pullback_percent': 0.20
                }
            },
            enabled=True
        )
    
    @staticmethod
    def get_progressive_fixed_template():
        """遞增固定點數停利模板"""
        return TakeProfitConfig(
            take_profit_type=TakeProfitType.FIXED_POINTS,
            take_profit_mode=TakeProfitMode.INDIVIDUAL,
            individual_configs={
                1: {'type': 'fixed_points', 'points': 15},
                2: {'type': 'fixed_points', 'points': 30},
                3: {'type': 'fixed_points', 'points': 50}
            },
            enabled=True
        )
```

## 🔄 實施優勢

### 6.1 技術優勢

1. **向後相容**：保持與現有移動停利邏輯的完全相容
2. **模組化設計**：停利邏輯與其他邏輯解耦
3. **配置驅動**：通過配置控制停利行為
4. **性能優化**：支援內存計算和批次更新

### 6.2 交易優勢

1. **策略多樣化**：支援移動停利、固定停利、混合策略
2. **風險控制精確**：可根據不同口數設定不同獲利目標
3. **適應性強**：可根據市場狀況調整停利策略
4. **回測一致性**：與回測系統的停利邏輯保持一致

## 🚀 下一步實施

1. **GUI 配置介面**：建立停利配置的圖形化設定介面
2. **配置驗證**：實現停利配置的有效性驗證
3. **回測整合**：將靈活停利整合到回測系統
4. **性能測試**：在高頻報價環境中測試性能

---

**此設計實現了完全靈活的停利配置機制，為多樣化獲利策略提供了強大的技術基礎。**
