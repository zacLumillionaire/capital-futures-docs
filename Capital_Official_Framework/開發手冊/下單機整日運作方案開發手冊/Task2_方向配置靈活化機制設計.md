# Task 2: 方向配置靈活化機制設計

## 📋 任務概述

分析現有固定方向邏輯（low做空、close突破做多），設計可配置的方向選擇機制，讓用戶自定義突破方向和進場策略。

## 🔍 現有固定方向機制分析

### 2.1 當前固定方向邏輯

#### 空單進場邏輯（即時檢測）
```python
def check_immediate_short_entry_safe(self, price, time_str):
    """即時空單進場檢測 - 固定做空邏輯"""
    # 🚀 固定邏輯：任何報價跌破區間下緣就立即觸發空單
    if price < self.range_low:
        self.first_breakout_detected = True
        self.breakout_direction = 'SHORT'  # 固定做空
        self.waiting_for_entry = True
```

#### 多單進場邏輯（1分K檢測）
```python
def check_minute_candle_breakout_safe(self):
    """1分K線收盤價突破檢測 - 固定做多邏輯"""
    close_price = self.current_minute_candle['close']
    
    # 🔧 固定邏輯：收盤價突破區間上緣就做多單
    if close_price > self.range_high:
        self.first_breakout_detected = True
        self.breakout_direction = 'LONG'  # 固定做多
        self.waiting_for_entry = True
```

### 2.2 現有機制限制

1. **方向固定**：無法改變突破方向的交易邏輯
2. **檢測方式固定**：空單用即時檢測，多單用1分K檢測
3. **無反向策略**：無法實現反轉策略（突破做反向）
4. **配置缺乏**：無法根據市場狀況調整進場方向

## 🎯 靈活方向配置設計

### 3.1 核心設計原則

1. **方向可配置**：每個突破點可獨立設定做多或做空
2. **檢測方式可選**：可選擇即時檢測或1分K檢測
3. **反向策略支援**：支援突破做反向的逆勢策略
4. **時段獨立配置**：每個時段可有不同的方向配置

### 3.2 方向配置結構設計

#### 基礎配置結構
```python
# 方向配置枚舉
class BreakoutDirection(Enum):
    LONG = "LONG"           # 做多
    SHORT = "SHORT"         # 做空
    DISABLED = "DISABLED"   # 停用

class DetectionMode(Enum):
    IMMEDIATE = "immediate"  # 即時檢測
    CANDLE_CLOSE = "candle_close"  # 1分K收盤檢測

# 方向配置結構
direction_config = {
    'high_breakout': {
        'direction': BreakoutDirection.LONG,     # 突破上緣做多
        'detection_mode': DetectionMode.CANDLE_CLOSE,
        'enabled': True
    },
    'low_breakout': {
        'direction': BreakoutDirection.SHORT,    # 突破下緣做空
        'detection_mode': DetectionMode.IMMEDIATE,
        'enabled': True
    }
}
```

#### 完整時段配置
```python
# 整合到時段配置中
time_interval_config = {
    'id': 'morning_1',
    'start_time': '08:46',
    'end_time': '08:48',
    'direction_config': {
        'high_breakout': {
            'direction': BreakoutDirection.LONG,
            'detection_mode': DetectionMode.CANDLE_CLOSE,
            'enabled': True,
            'description': '突破上緣做多單'
        },
        'low_breakout': {
            'direction': BreakoutDirection.SHORT,
            'detection_mode': DetectionMode.IMMEDIATE,
            'enabled': True,
            'description': '突破下緣做空單'
        }
    }
}

# 反向策略範例
reverse_strategy_config = {
    'id': 'reverse_morning',
    'start_time': '09:30',
    'end_time': '09:32',
    'direction_config': {
        'high_breakout': {
            'direction': BreakoutDirection.SHORT,  # 突破上緣做空（反向）
            'detection_mode': DetectionMode.IMMEDIATE,
            'enabled': True,
            'description': '突破上緣做空單（反向策略）'
        },
        'low_breakout': {
            'direction': BreakoutDirection.LONG,   # 突破下緣做多（反向）
            'detection_mode': DetectionMode.CANDLE_CLOSE,
            'enabled': True,
            'description': '突破下緣做多單（反向策略）'
        }
    }
}
```

### 3.3 核心函數重構

#### 統一突破檢測函數
```python
def check_breakout_signals_unified(self, price, time_str):
    """統一的突破檢測邏輯 - 支援靈活方向配置"""
    if not self.current_interval or not self.range_calculated:
        return
    
    interval_config = self.current_interval
    direction_config = interval_config.get('direction_config', {})
    
    # 檢查上緣突破
    if self._should_check_high_breakout(direction_config):
        self._check_high_breakout(price, time_str, direction_config['high_breakout'])
    
    # 檢查下緣突破
    if self._should_check_low_breakout(direction_config):
        self._check_low_breakout(price, time_str, direction_config['low_breakout'])

def _should_check_high_breakout(self, direction_config):
    """檢查是否應該檢測上緣突破"""
    high_config = direction_config.get('high_breakout', {})
    return (high_config.get('enabled', False) and 
            not self.first_breakout_detected and
            high_config.get('direction') != BreakoutDirection.DISABLED)

def _should_check_low_breakout(self, direction_config):
    """檢查是否應該檢測下緣突破"""
    low_config = direction_config.get('low_breakout', {})
    return (low_config.get('enabled', False) and 
            not self.first_breakout_detected and
            low_config.get('direction') != BreakoutDirection.DISABLED)
```

#### 上緣突破檢測
```python
def _check_high_breakout(self, price, time_str, high_config):
    """檢查上緣突破"""
    detection_mode = high_config.get('detection_mode', DetectionMode.CANDLE_CLOSE)
    direction = high_config.get('direction', BreakoutDirection.LONG)
    
    if detection_mode == DetectionMode.IMMEDIATE:
        # 即時檢測
        if price > self.range_high:
            self._trigger_breakout_signal(direction.value, price, time_str, 
                                        f"即時突破上緣 {self.range_high:.0f}")
    
    elif detection_mode == DetectionMode.CANDLE_CLOSE:
        # 1分K收盤檢測
        if (self.current_minute_candle and 
            self.current_minute_candle['close'] > self.range_high):
            close_price = self.current_minute_candle['close']
            self._trigger_breakout_signal(direction.value, close_price, time_str,
                                        f"1分K收盤突破上緣 {self.range_high:.0f}")

def _check_low_breakout(self, price, time_str, low_config):
    """檢查下緣突破"""
    detection_mode = low_config.get('detection_mode', DetectionMode.IMMEDIATE)
    direction = low_config.get('direction', BreakoutDirection.SHORT)
    
    if detection_mode == DetectionMode.IMMEDIATE:
        # 即時檢測
        if price < self.range_low:
            self._trigger_breakout_signal(direction.value, price, time_str,
                                        f"即時突破下緣 {self.range_low:.0f}")
    
    elif detection_mode == DetectionMode.CANDLE_CLOSE:
        # 1分K收盤檢測
        if (self.current_minute_candle and 
            self.current_minute_candle['close'] < self.range_low):
            close_price = self.current_minute_candle['close']
            self._trigger_breakout_signal(direction.value, close_price, time_str,
                                        f"1分K收盤突破下緣 {self.range_low:.0f}")

def _trigger_breakout_signal(self, direction, price, time_str, description):
    """觸發突破信號"""
    self.first_breakout_detected = True
    self.breakout_direction = direction
    self.waiting_for_entry = True
    
    # 記錄突破事件
    self.add_strategy_log(f"🔥 {description} → {direction}信號")
    self.add_strategy_log(f"⏳ 等待下一個報價進場...")
    
    print(f"🔥 [STRATEGY] {direction}突破信號已觸發")
```

### 3.4 配置管理系統

#### 預設配置模板
```python
class DirectionConfigTemplates:
    """方向配置模板"""
    
    @staticmethod
    def get_standard_template():
        """標準配置：突破上緣做多，突破下緣做空"""
        return {
            'high_breakout': {
                'direction': BreakoutDirection.LONG,
                'detection_mode': DetectionMode.CANDLE_CLOSE,
                'enabled': True,
                'description': '突破上緣做多單'
            },
            'low_breakout': {
                'direction': BreakoutDirection.SHORT,
                'detection_mode': DetectionMode.IMMEDIATE,
                'enabled': True,
                'description': '突破下緣做空單'
            }
        }
    
    @staticmethod
    def get_reverse_template():
        """反向配置：突破上緣做空，突破下緣做多"""
        return {
            'high_breakout': {
                'direction': BreakoutDirection.SHORT,
                'detection_mode': DetectionMode.IMMEDIATE,
                'enabled': True,
                'description': '突破上緣做空單（反向）'
            },
            'low_breakout': {
                'direction': BreakoutDirection.LONG,
                'detection_mode': DetectionMode.CANDLE_CLOSE,
                'enabled': True,
                'description': '突破下緣做多單（反向）'
            }
        }
    
    @staticmethod
    def get_long_only_template():
        """只做多配置：只在突破時做多"""
        return {
            'high_breakout': {
                'direction': BreakoutDirection.LONG,
                'detection_mode': DetectionMode.CANDLE_CLOSE,
                'enabled': True,
                'description': '突破上緣做多單'
            },
            'low_breakout': {
                'direction': BreakoutDirection.LONG,
                'detection_mode': DetectionMode.CANDLE_CLOSE,
                'enabled': True,
                'description': '突破下緣做多單'
            }
        }
    
    @staticmethod
    def get_short_only_template():
        """只做空配置：只在突破時做空"""
        return {
            'high_breakout': {
                'direction': BreakoutDirection.SHORT,
                'detection_mode': DetectionMode.IMMEDIATE,
                'enabled': True,
                'description': '突破上緣做空單'
            },
            'low_breakout': {
                'direction': BreakoutDirection.SHORT,
                'detection_mode': DetectionMode.IMMEDIATE,
                'enabled': True,
                'description': '突破下緣做空單'
            }
        }
```

#### 配置驗證函數
```python
def validate_direction_config(self, direction_config):
    """驗證方向配置的有效性"""
    required_keys = ['high_breakout', 'low_breakout']
    
    for key in required_keys:
        if key not in direction_config:
            raise ValueError(f"缺少必要配置: {key}")
        
        breakout_config = direction_config[key]
        
        # 檢查必要欄位
        if 'direction' not in breakout_config:
            raise ValueError(f"{key} 缺少 direction 設定")
        
        if 'detection_mode' not in breakout_config:
            raise ValueError(f"{key} 缺少 detection_mode 設定")
        
        # 檢查枚舉值有效性
        try:
            BreakoutDirection(breakout_config['direction'])
            DetectionMode(breakout_config['detection_mode'])
        except ValueError as e:
            raise ValueError(f"{key} 配置值無效: {e}")
    
    return True
```

## 🔄 實施優勢

### 4.1 策略靈活性

1. **多樣化策略**：支援順勢、逆勢、單向等多種策略
2. **時段差異化**：不同時段可採用不同的方向邏輯
3. **檢測方式選擇**：可根據市場特性選擇檢測方式
4. **動態調整**：可根據回測結果調整方向配置

### 4.2 技術優勢

1. **向後相容**：保持與現有代碼的相容性
2. **模組化設計**：方向邏輯與其他邏輯解耦
3. **配置驅動**：通過配置文件控制策略行為
4. **易於測試**：可獨立測試不同方向配置

## 🚀 下一步實施

1. **GUI 介面**：建立方向配置的圖形化設定介面
2. **配置存儲**：實現配置的保存和載入功能
3. **回測整合**：將方向配置整合到回測系統
4. **實盤驗證**：在模擬環境中驗證不同配置效果

---

**此設計實現了完全靈活的方向配置機制，為多樣化交易策略提供了強大的技術基礎。**
