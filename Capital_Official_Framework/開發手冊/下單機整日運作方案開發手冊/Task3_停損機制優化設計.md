# Task 3: 停損機制優化設計

## 📋 任務概述

分析現有區間邊緣停損機制，設計支援區間邊緣或指定點數的靈活停損配置，包括各口獨立設定功能。

## 🔍 現有停損機制分析

### 3.1 單一策略停損機制

#### 固定區間邊緣停損
```python
def check_exit_conditions_safe(self, price, time_str):
    """單一策略固定停損邏輯"""
    direction = self.current_position['direction']
    
    # 🛡️ 固定使用區間邊界作為停損點
    if direction == "LONG" and price <= self.range_low:
        self.exit_position_safe(price, time_str, f"初始停損 {self.range_low:.0f}")
        return
    elif direction == "SHORT" and price >= self.range_high:
        self.exit_position_safe(price, time_str, f"初始停損 {self.range_high:.0f}")
        return
```

#### 停損點設定邏輯
```python
def enter_position_safe(self, direction, price, time_str):
    """建倉時隱含停損設定"""
    # 停損點隱含在區間邊界中：
    # 多單停損：self.range_low (區間下軌)
    # 空單停損：self.range_high (區間上軌)
    # 無法自定義停損點數
```

### 3.2 多組策略停損機制

#### 區間邊緣停損配置
```python
# exit_mechanism_config.py 中的配置
@dataclass
class GroupExitConfig:
    group_id: str
    total_lots: int = 3
    stop_loss_type: str = "RANGE_BOUNDARY"  # 固定為區間邊緣
    lot_rules: List[LotExitRule] = field(default_factory=list)

# initial_stop_loss_manager.py 中的計算
def _calculate_initial_stop_loss_price(self, direction: str, range_data: Dict[str, float]) -> float:
    """固定使用區間邊緣計算停損"""
    if direction == "LONG":
        stop_loss_price = range_data['range_low']  # 固定區間低點
    elif direction == "SHORT":
        stop_loss_price = range_data['range_high']  # 固定區間高點
    return stop_loss_price
```

### 3.3 現有機制限制

1. **停損方式固定**：只能使用區間邊緣，無法指定點數
2. **各口相同**：所有口數使用相同的停損邏輯
3. **無法獨立配置**：無法為不同口數設定不同停損點
4. **缺乏靈活性**：無法根據市場狀況調整停損策略

## 🎯 靈活停損配置設計

### 4.1 核心設計原則

1. **停損方式可選**：支援區間邊緣或固定點數停損
2. **各口獨立配置**：每口可有不同的停損設定
3. **動態計算**：根據配置動態計算停損點
4. **向後相容**：保持與現有系統的相容性

### 4.2 停損配置結構設計

#### 停損類型枚舉
```python
from enum import Enum

class StopLossType(Enum):
    RANGE_BOUNDARY = "range_boundary"    # 區間邊緣停損
    FIXED_POINTS = "fixed_points"        # 固定點數停損
    CUSTOM_PRICE = "custom_price"        # 自定義價格停損

class StopLossMode(Enum):
    UNIFIED = "unified"                  # 統一停損（所有口相同）
    INDIVIDUAL = "individual"            # 各口獨立停損
```

#### 停損配置結構
```python
@dataclass
class StopLossConfig:
    """停損配置"""
    stop_loss_type: StopLossType
    stop_loss_mode: StopLossMode
    
    # 統一停損配置
    unified_points: Optional[float] = None
    unified_price: Optional[float] = None
    
    # 各口獨立配置
    individual_configs: Dict[int, Dict] = field(default_factory=dict)
    
    # 是否啟用
    enabled: bool = True
    
    def to_dict(self) -> Dict:
        return {
            'stop_loss_type': self.stop_loss_type.value,
            'stop_loss_mode': self.stop_loss_mode.value,
            'unified_points': self.unified_points,
            'unified_price': self.unified_price,
            'individual_configs': self.individual_configs,
            'enabled': self.enabled
        }

# 各口獨立配置範例
individual_stop_loss_example = {
    1: {  # 第1口
        'type': StopLossType.FIXED_POINTS,
        'points': 15,
        'enabled': True
    },
    2: {  # 第2口
        'type': StopLossType.FIXED_POINTS,
        'points': 25,
        'enabled': True
    },
    3: {  # 第3口
        'type': StopLossType.RANGE_BOUNDARY,
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
        'stop_loss_type': StopLossType.INDIVIDUAL,
        'stop_loss_mode': StopLossMode.INDIVIDUAL,
        'individual_configs': {
            1: {'type': 'fixed_points', 'points': 15},
            2: {'type': 'fixed_points', 'points': 25},
            3: {'type': 'range_boundary'}
        }
    }
}
```

### 4.3 核心函數重構

#### 統一停損計算函數
```python
class FlexibleStopLossCalculator:
    """靈活停損計算器"""
    
    def __init__(self, stop_loss_config: StopLossConfig):
        self.config = stop_loss_config
    
    def calculate_stop_loss_price(self, lot_number: int, direction: str, 
                                entry_price: float, range_data: Dict[str, float]) -> float:
        """計算停損價格"""
        
        if self.config.stop_loss_mode == StopLossMode.UNIFIED:
            return self._calculate_unified_stop_loss(direction, entry_price, range_data)
        else:
            return self._calculate_individual_stop_loss(
                lot_number, direction, entry_price, range_data
            )
    
    def _calculate_unified_stop_loss(self, direction: str, entry_price: float, 
                                   range_data: Dict[str, float]) -> float:
        """計算統一停損價格"""
        
        if self.config.stop_loss_type == StopLossType.RANGE_BOUNDARY:
            return self._calculate_range_boundary_stop_loss(direction, range_data)
        
        elif self.config.stop_loss_type == StopLossType.FIXED_POINTS:
            return self._calculate_fixed_points_stop_loss(
                direction, entry_price, self.config.unified_points
            )
        
        elif self.config.stop_loss_type == StopLossType.CUSTOM_PRICE:
            return self.config.unified_price
        
        else:
            raise ValueError(f"不支援的停損類型: {self.config.stop_loss_type}")
    
    def _calculate_individual_stop_loss(self, lot_number: int, direction: str,
                                      entry_price: float, range_data: Dict[str, float]) -> float:
        """計算各口獨立停損價格"""
        
        lot_config = self.config.individual_configs.get(lot_number)
        if not lot_config or not lot_config.get('enabled', True):
            # 如果沒有配置或停用，使用區間邊緣作為預設
            return self._calculate_range_boundary_stop_loss(direction, range_data)
        
        stop_type = StopLossType(lot_config.get('type', 'range_boundary'))
        
        if stop_type == StopLossType.RANGE_BOUNDARY:
            return self._calculate_range_boundary_stop_loss(direction, range_data)
        
        elif stop_type == StopLossType.FIXED_POINTS:
            points = lot_config.get('points', 15)
            return self._calculate_fixed_points_stop_loss(direction, entry_price, points)
        
        elif stop_type == StopLossType.CUSTOM_PRICE:
            return lot_config.get('price', entry_price)
        
        else:
            raise ValueError(f"不支援的停損類型: {stop_type}")
    
    def _calculate_range_boundary_stop_loss(self, direction: str, 
                                          range_data: Dict[str, float]) -> float:
        """計算區間邊緣停損"""
        if direction == "LONG":
            return range_data['range_low']
        elif direction == "SHORT":
            return range_data['range_high']
        else:
            raise ValueError(f"不支援的交易方向: {direction}")
    
    def _calculate_fixed_points_stop_loss(self, direction: str, entry_price: float, 
                                        points: float) -> float:
        """計算固定點數停損"""
        if direction == "LONG":
            return entry_price - points
        elif direction == "SHORT":
            return entry_price + points
        else:
            raise ValueError(f"不支援的交易方向: {direction}")
```

#### 重構停損管理器
```python
class EnhancedStopLossManager:
    """增強型停損管理器"""
    
    def __init__(self, db_manager, console_enabled: bool = True):
        self.db_manager = db_manager
        self.console_enabled = console_enabled
        self.stop_loss_calculators = {}  # 存儲各組的停損計算器
    
    def setup_group_stop_loss(self, group_id: int, stop_loss_config: StopLossConfig, 
                            range_data: Dict[str, float]) -> bool:
        """為策略組設定停損"""
        try:
            # 創建停損計算器
            calculator = FlexibleStopLossCalculator(stop_loss_config)
            self.stop_loss_calculators[group_id] = calculator
            
            # 取得該組的所有活躍部位
            positions = self.db_manager.get_active_positions_by_group(group_id)
            
            if not positions:
                if self.console_enabled:
                    print(f"[STOP_LOSS] ⚠️ 策略組 {group_id} 沒有活躍部位")
                return False
            
            success_count = 0
            for position in positions:
                if self._setup_position_flexible_stop_loss(position, calculator, range_data):
                    success_count += 1
            
            if self.console_enabled:
                print(f"[STOP_LOSS] ✅ 靈活停損設定完成: {success_count}/{len(positions)} 個部位")
            
            return success_count == len(positions)
            
        except Exception as e:
            if self.console_enabled:
                print(f"[STOP_LOSS] ❌ 設定靈活停損失敗: {e}")
            return False
    
    def _setup_position_flexible_stop_loss(self, position: Dict, calculator: FlexibleStopLossCalculator,
                                         range_data: Dict[str, float]) -> bool:
        """為單一部位設定靈活停損"""
        try:
            position_id = position['id']
            lot_number = position['lot_id']
            direction = position['direction']
            entry_price = position['entry_price']
            
            # 使用靈活計算器計算停損價格
            stop_loss_price = calculator.calculate_stop_loss_price(
                lot_number, direction, entry_price, range_data
            )
            
            # 更新資料庫
            success = self._update_position_stop_loss_in_db(
                position_id, stop_loss_price, range_data, entry_price
            )
            
            if success and self.console_enabled:
                stop_type = calculator.config.individual_configs.get(lot_number, {}).get('type', 'range_boundary')
                print(f"[STOP_LOSS] ✅ 第{lot_number}口停損: {stop_loss_price:.0f} (類型: {stop_type})")
            
            return success
            
        except Exception as e:
            if self.console_enabled:
                print(f"[STOP_LOSS] ❌ 部位 {position.get('id')} 停損設定失敗: {e}")
            return False
```

### 4.4 配置模板系統

#### 預設配置模板
```python
class StopLossConfigTemplates:
    """停損配置模板"""
    
    @staticmethod
    def get_range_boundary_template():
        """區間邊緣停損模板（原有邏輯）"""
        return StopLossConfig(
            stop_loss_type=StopLossType.RANGE_BOUNDARY,
            stop_loss_mode=StopLossMode.UNIFIED,
            enabled=True
        )
    
    @staticmethod
    def get_unified_fixed_points_template(points: float = 15):
        """統一固定點數停損模板"""
        return StopLossConfig(
            stop_loss_type=StopLossType.FIXED_POINTS,
            stop_loss_mode=StopLossMode.UNIFIED,
            unified_points=points,
            enabled=True
        )
    
    @staticmethod
    def get_individual_mixed_template():
        """各口獨立混合停損模板"""
        return StopLossConfig(
            stop_loss_type=StopLossType.FIXED_POINTS,
            stop_loss_mode=StopLossMode.INDIVIDUAL,
            individual_configs={
                1: {'type': 'fixed_points', 'points': 15, 'enabled': True},
                2: {'type': 'fixed_points', 'points': 25, 'enabled': True},
                3: {'type': 'range_boundary', 'enabled': True}
            },
            enabled=True
        )
    
    @staticmethod
    def get_progressive_points_template():
        """遞增點數停損模板"""
        return StopLossConfig(
            stop_loss_type=StopLossType.FIXED_POINTS,
            stop_loss_mode=StopLossMode.INDIVIDUAL,
            individual_configs={
                1: {'type': 'fixed_points', 'points': 15, 'enabled': True},
                2: {'type': 'fixed_points', 'points': 30, 'enabled': True},
                3: {'type': 'fixed_points', 'points': 50, 'enabled': True}
            },
            enabled=True
        )
```

## 🔄 實施優勢

### 5.1 技術優勢

1. **向後相容**：保持與現有區間邊緣邏輯的完全相容
2. **模組化設計**：停損邏輯與其他邏輯解耦
3. **配置驅動**：通過配置控制停損行為
4. **易於擴展**：可輕鬆添加新的停損類型

### 5.2 交易優勢

1. **風險控制精確**：可根據不同口數設定不同風險水平
2. **策略多樣化**：支援保守、激進等多種停損策略
3. **適應性強**：可根據市場狀況調整停損配置
4. **回測一致性**：與回測系統的停損邏輯保持一致

## 🚀 下一步實施

1. **GUI 配置介面**：建立停損配置的圖形化設定介面
2. **配置驗證**：實現停損配置的有效性驗證
3. **回測整合**：將靈活停損整合到回測系統
4. **實盤測試**：在模擬環境中測試不同停損配置

---

**此設計實現了完全靈活的停損配置機制，為精確風險控制提供了強大的技術基礎。**
