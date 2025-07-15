# Task 1: 多時段區間繪製機制分析與設計

## 📋 任務概述

分析現有 simple_integrated.py 的單一時段機制（08:45~08:47），設計支援多時段運作的架構，包括時間管理、區間計算、狀態切換等核心邏輯。

## 🔍 現有機制分析

### 1.1 當前單一時段架構

#### 核心變數結構
```python
# 區間計算相關
self.range_high = 0                    # 區間最高價
self.range_low = 0                     # 區間最低價
self.range_calculated = False          # 區間是否已計算完成
self.in_range_period = False           # 是否在區間收集期間
self.range_prices = []                 # 區間內價格數據
self.range_start_hour = 8              # 預設08:46開始
self.range_start_minute = 46
self._range_start_time = ""            # 區間開始時間記錄
```

#### 時間檢查邏輯
```python
def is_in_range_time_safe(self, time_str):
    """精確2分鐘區間檢查"""
    hour, minute, second = map(int, time_str.split(':'))
    current_total_seconds = hour * 3600 + minute * 60 + second
    start_total_seconds = self.range_start_hour * 3600 + self.range_start_minute * 60
    end_total_seconds = start_total_seconds + 120  # 固定2分鐘
    
    return start_total_seconds <= current_total_seconds < end_total_seconds
```

#### 區間計算流程
```python
def update_range_calculation_safe(self, price, time_str):
    """區間計算主邏輯"""
    if self.is_in_range_time_safe(time_str):
        if not self.in_range_period:
            # 開始收集區間數據
            self.in_range_period = True
            self.range_prices = []
        self.range_prices.append(price)
    
    elif self.in_range_period and not self.range_calculated:
        # 區間結束，計算高低點
        self.range_high = max(self.range_prices)
        self.range_low = min(self.range_prices)
        self.range_calculated = True
        self.in_range_period = False
```

### 1.2 現有機制限制

1. **單一時段限制**：只能處理一個固定時間區間
2. **狀態重置問題**：無法處理多個區間的狀態切換
3. **數據覆蓋問題**：新區間會覆蓋前一個區間的數據
4. **進場邏輯衝突**：多時段可能產生重複進場信號

## 🎯 多時段架構設計

### 2.1 核心設計原則

1. **時段隔離**：每個時段獨立計算區間，互不干擾
2. **狀態管理**：清楚的時段狀態切換和追蹤
3. **數據保存**：保留所有時段的區間數據供後續使用
4. **進場控制**：避免多時段重複進場的衝突

### 2.2 新架構變數設計

#### 多時段配置結構
```python
# 多時段配置
self.time_intervals = [
    {
        'id': 'morning_1',
        'start_time': '08:46',
        'end_time': '08:48',
        'duration': 120,  # 秒
        'direction_config': {
            'long_on_high_break': True,
            'short_on_low_break': True
        },
        'stop_loss_config': {
            'mode': 'range_boundary',  # 或 'fixed_points'
            'lot1': 15, 'lot2': 25, 'lot3': 35
        },
        'take_profit_config': {
            'mode': 'trailing',  # 或 'fixed_points'
            'lot1': {'trigger': 15, 'pullback': 10},
            'lot2': {'trigger': 40, 'pullback': 10},
            'lot3': {'trigger': 41, 'pullback': 20}
        }
    },
    {
        'id': 'morning_2',
        'start_time': '09:30',
        'end_time': '09:32',
        'duration': 120,
        'direction_config': {
            'long_on_high_break': False,
            'short_on_low_break': True  # 只做空單
        },
        # ... 其他配置
    }
]
```

#### 時段狀態管理
```python
# 當前活躍時段
self.current_interval = None
self.current_interval_id = None

# 時段狀態追蹤
self.interval_states = {
    'morning_1': {
        'status': 'waiting',  # waiting/collecting/completed/trading
        'range_high': 0,
        'range_low': 0,
        'range_prices': [],
        'start_time': None,
        'end_time': None,
        'position_entered': False
    }
}

# 全局交易狀態
self.daily_position_count = 0
self.max_daily_positions = 3  # 每日最大進場次數
```

### 2.3 核心函數重構

#### 時間檢查函數
```python
def get_current_active_interval(self, time_str):
    """獲取當前應該活躍的時段"""
    current_seconds = self._time_to_seconds(time_str)
    
    for interval in self.time_intervals:
        start_seconds = self._time_to_seconds(interval['start_time'])
        end_seconds = start_seconds + interval['duration']
        
        if start_seconds <= current_seconds < end_seconds:
            return interval
    
    return None

def _time_to_seconds(self, time_str):
    """時間字串轉換為秒數"""
    if ':' in time_str:
        hour, minute = map(int, time_str.split(':'))
        return hour * 3600 + minute * 60
    return 0
```

#### 多時段區間計算
```python
def update_multi_interval_calculation(self, price, time_str):
    """多時段區間計算主邏輯"""
    # 1. 檢查當前應該活躍的時段
    active_interval = self.get_current_active_interval(time_str)
    
    if active_interval:
        interval_id = active_interval['id']
        
        # 2. 時段切換處理
        if self.current_interval_id != interval_id:
            self._switch_to_interval(active_interval, time_str)
        
        # 3. 收集當前時段數據
        self._collect_interval_data(interval_id, price, time_str)
    
    else:
        # 4. 非活躍時段，檢查是否需要結束當前時段
        if self.current_interval_id:
            self._finalize_current_interval(time_str)

def _switch_to_interval(self, interval, time_str):
    """切換到新時段"""
    # 結束前一個時段
    if self.current_interval_id:
        self._finalize_current_interval(time_str)
    
    # 啟動新時段
    interval_id = interval['id']
    self.current_interval = interval
    self.current_interval_id = interval_id
    
    # 初始化時段狀態
    self.interval_states[interval_id] = {
        'status': 'collecting',
        'range_high': 0,
        'range_low': 0,
        'range_prices': [],
        'start_time': time_str,
        'end_time': None,
        'position_entered': False
    }
    
    self.add_strategy_log(f"📊 切換到時段 {interval_id}: {time_str}")

def _collect_interval_data(self, interval_id, price, time_str):
    """收集時段數據"""
    state = self.interval_states[interval_id]
    
    if state['status'] == 'collecting':
        state['range_prices'].append(price)

def _finalize_current_interval(self, time_str):
    """結束當前時段計算"""
    if not self.current_interval_id:
        return
    
    state = self.interval_states[self.current_interval_id]
    
    if state['range_prices']:
        state['range_high'] = max(state['range_prices'])
        state['range_low'] = min(state['range_prices'])
        state['status'] = 'completed'
        state['end_time'] = time_str
        
        self.add_strategy_log(
            f"✅ 時段 {self.current_interval_id} 完成: "
            f"高{state['range_high']:.0f} 低{state['range_low']:.0f}"
        )
    
    self.current_interval = None
    self.current_interval_id = None
```

## 🔄 狀態切換邏輯

### 3.1 時段生命週期

```
waiting → collecting → completed → trading → finished
   ↓         ↓           ↓          ↓         ↓
 等待開始   收集數據    計算完成    交易中    結束
```

### 3.2 狀態轉換條件

1. **waiting → collecting**：進入時段時間範圍
2. **collecting → completed**：離開時段時間範圍且有數據
3. **completed → trading**：檢測到突破信號且允許進場
4. **trading → finished**：部位平倉或達到每日限制

## 📊 實施優勢

### 4.1 技術優勢

1. **模組化設計**：每個時段獨立配置和管理
2. **狀態清晰**：明確的時段狀態追蹤
3. **數據保存**：完整保留所有時段數據
4. **擴展性強**：易於添加新時段或修改配置

### 4.2 交易優勢

1. **多機會捕捉**：可在多個時段尋找交易機會
2. **風險分散**：不同時段可有不同的風險配置
3. **策略靈活**：每個時段可有獨立的交易邏輯
4. **進場控制**：避免過度交易的風險管理

## 🚀 下一步實施

1. **配置系統**：建立時段配置的 GUI 介面
2. **狀態顯示**：在 UI 中顯示各時段狀態
3. **測試驗證**：多時段邏輯的完整測試
4. **整合其他任務**：與方向配置、停損停利機制整合

---

**此設計為多時段交易系統奠定了堅實的架構基礎，為後續任務的實施提供了清晰的技術路線。**
