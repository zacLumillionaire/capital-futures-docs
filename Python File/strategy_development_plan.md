# 🚀 當沖策略交易系統開發計劃

## 📋 **策略概念總結**

### 🎯 **核心策略邏輯**
1. **開盤區間設定** - 監聽08:46-08:47兩根K棒，記錄最高點和最低點
2. **突破進場** - 08:48開始等待突破，突破高點做多，跌破低點做空
3. **多口管理** - 同時進場1-4口，每口有不同的出場規則
4. **移動停利** - 每口有不同的啟動點(15/40/65/80點)和回檔比例(20%/40%)
5. **保護性停損** - 後續口數使用前面口數的獲利來設定保護停損
6. **收盤平倉** - 13:45強制平倉所有剩餘部位

### 📊 **策略參數範例**
```python
# 三口策略範例
第1口: 15點啟動移動停利，回檔20%
第2口: 40點啟動移動停利，回檔20%，用累積獲利2倍保護
第3口: 65點啟動移動停利，回檔20%，用累積獲利2倍保護
```

## 🏗️ **系統架構設計**

### 📁 **新增模組結構**
```
Python File/
├── strategy/                    # 策略模組 (新增)
│   ├── __init__.py
│   ├── strategy_engine.py       # 策略引擎核心
│   ├── position_manager.py      # 部位管理
│   ├── risk_manager.py          # 風險控制
│   ├── signal_detector.py       # 信號偵測
│   └── strategy_config.py       # 策略配置
├── database/                    # 資料庫模組 (新增)
│   ├── __init__.py
│   ├── sqlite_manager.py        # SQLite管理
│   ├── market_data.py           # 市場資料
│   └── trade_records.py         # 交易記錄
├── utils/                       # 工具模組 (新增)
│   ├── __init__.py
│   ├── time_utils.py            # 時間工具
│   └── calculation_utils.py     # 計算工具
└── 現有模組保持不變...
```

### 🔗 **模組間關係**
```
策略引擎 ←→ 部位管理 ←→ 下單模組 (現有)
    ↓           ↓
信號偵測 ←→ 風險控制 ←→ 回報模組 (現有)
    ↓           ↓
市場資料 ←→ 交易記錄 ←→ 報價模組 (現有)
```

## 📅 **分階段開發步驟**

### 🎯 **第一階段: 基礎架構 (1-2天)**

#### **步驟1.1: SQLite資料庫設計**
```sql
-- 市場資料表
CREATE TABLE market_data (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    datetime TEXT NOT NULL,
    open_price REAL,
    high_price REAL,
    low_price REAL,
    close_price REAL,
    volume INTEGER,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 策略信號表
CREATE TABLE strategy_signals (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    date TEXT NOT NULL,
    range_high REAL,
    range_low REAL,
    signal_type TEXT,  -- 'LONG', 'SHORT', 'NONE'
    signal_time TEXT,
    signal_price REAL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 交易記錄表
CREATE TABLE trade_records (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    date TEXT NOT NULL,
    strategy_name TEXT,
    lot_id INTEGER,
    entry_time TEXT,
    entry_price REAL,
    exit_time TEXT,
    exit_price REAL,
    position_type TEXT,  -- 'LONG', 'SHORT'
    pnl REAL,
    exit_reason TEXT,    -- 'TRAILING_STOP', 'PROTECTIVE_STOP', 'EOD'
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 策略狀態表
CREATE TABLE strategy_status (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    date TEXT NOT NULL,
    status TEXT,         -- 'WAITING', 'MONITORING', 'TRADING', 'CLOSED'
    current_position TEXT,
    active_lots INTEGER,
    total_pnl REAL,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

#### **步驟1.2: 基礎模組創建**
- ✅ SQLite管理器
- ✅ 時間工具 (交易時間判斷)
- ✅ 策略配置管理
- ✅ 日誌系統整合

### 🎯 **第二階段: 信號偵測 (2-3天)**

#### **步驟2.1: 開盤區間監控**
```python
class OpeningRangeDetector:
    def __init__(self):
        self.range_high = None
        self.range_low = None
        self.candles_846_847 = []
    
    def process_tick(self, price, timestamp):
        """處理即時報價，建立開盤區間"""
        if self.is_range_time(timestamp):  # 08:46-08:47
            self.update_range(price, timestamp)
    
    def is_range_complete(self):
        """檢查是否已收集完整的開盤區間"""
        return len(self.candles_846_847) >= 2
```

#### **步驟2.2: 突破信號偵測**
```python
class BreakoutSignalDetector:
    def __init__(self, range_high, range_low):
        self.range_high = range_high
        self.range_low = range_low
        self.signal_generated = False
    
    def check_breakout(self, current_price, timestamp):
        """檢查突破信號"""
        if current_price > self.range_high:
            return 'LONG'
        elif current_price < self.range_low:
            return 'SHORT'
        return None
```

### 🎯 **第三階段: 部位管理 (3-4天)**

#### **步驟3.1: 多口部位管理器**
```python
class MultiLotPositionManager:
    def __init__(self, strategy_config):
        self.config = strategy_config
        self.lots = []
        self.entry_price = None
        self.position_type = None
    
    def open_position(self, signal_type, entry_price):
        """開倉多口部位"""
        for i in range(self.config.trade_size_in_lots):
            lot = self.create_lot(i, entry_price)
            self.lots.append(lot)
            # 調用下單模組進行實際下單
            self.place_order(lot)
    
    def update_lots(self, current_price):
        """更新所有口數的狀態"""
        for lot in self.lots:
            if lot['status'] == 'active':
                self.check_exit_conditions(lot, current_price)
```

#### **步驟3.2: 移動停利邏輯**
```python
class TrailingStopManager:
    def update_trailing_stop(self, lot, current_price):
        """更新移動停利"""
        rule = lot['rule']
        if rule.use_trailing_stop:
            # 更新峰值價格
            self.update_peak_price(lot, current_price)
            
            # 檢查是否啟動移動停利
            if self.should_activate_trailing(lot):
                lot['trailing_on'] = True
            
            # 計算移動停利價格
            if lot['trailing_on']:
                stop_price = self.calculate_trailing_stop(lot)
                if self.should_exit_at_trailing_stop(current_price, stop_price):
                    self.exit_lot(lot, stop_price)
```

### 🎯 **第四階段: 風險控制 (2-3天)**

#### **步驟4.1: 保護性停損**
```python
class ProtectiveStopManager:
    def update_protective_stops(self, lots, exited_lot):
        """當某口出場時，更新後續口數的保護停損"""
        cumulative_pnl = self.calculate_cumulative_pnl(lots)
        
        for lot in lots:
            if lot['id'] > exited_lot['id'] and lot['status'] == 'active':
                if lot['rule'].protective_stop_multiplier:
                    new_stop = self.calculate_protective_stop(
                        cumulative_pnl, 
                        lot['rule'].protective_stop_multiplier
                    )
                    lot['stop_loss'] = new_stop
                    lot['is_initial_stop'] = False
```

#### **步驟4.2: 風險限制**
```python
class RiskManager:
    def __init__(self, max_daily_loss, max_position_size):
        self.max_daily_loss = max_daily_loss
        self.max_position_size = max_position_size
        self.daily_pnl = 0
    
    def can_open_position(self, position_size):
        """檢查是否可以開倉"""
        if self.daily_pnl <= -self.max_daily_loss:
            return False, "達到每日最大虧損限制"
        if position_size > self.max_position_size:
            return False, "超過最大部位限制"
        return True, "可以開倉"
```

### 🎯 **第五階段: 策略引擎整合 (3-4天)**

#### **步驟5.1: 主策略引擎**
```python
class StrategyEngine:
    def __init__(self, config):
        self.config = config
        self.range_detector = OpeningRangeDetector()
        self.signal_detector = None
        self.position_manager = MultiLotPositionManager(config)
        self.risk_manager = RiskManager()
        self.status = 'WAITING'
    
    def process_market_data(self, price, timestamp):
        """處理即時市場資料"""
        current_time = timestamp.time()
        
        if self.is_range_monitoring_time(current_time):
            self.range_detector.process_tick(price, timestamp)
            
        elif self.is_trading_time(current_time):
            if not self.signal_detector and self.range_detector.is_range_complete():
                self.initialize_signal_detector()
            
            if self.signal_detector and not self.position_manager.has_position():
                signal = self.signal_detector.check_breakout(price, timestamp)
                if signal:
                    self.open_position(signal, price, timestamp)
            
            if self.position_manager.has_position():
                self.position_manager.update_lots(price)
        
        elif self.is_closing_time(current_time):
            self.close_all_positions()
```

#### **步驟5.2: 與現有系統整合**
```python
# 在回報模組中添加策略引擎通知
def OnNewData(self, bstrUserID, bstrData):
    # 現有的回報處理...
    
    # 通知策略引擎
    if hasattr(self, 'strategy_engine'):
        parsed_data = parse_onnewdata_for_daytrading(bstrData)
        if parsed_data and parsed_data.get('type') == 'D':  # 成交
            self.strategy_engine.on_trade_filled(parsed_data)

# 在報價模組中添加策略引擎通知
def OnNotifyTicksLONG(self, sMarketNo, sStockIdx, sPtr):
    # 現有的報價處理...
    
    # 通知策略引擎
    if hasattr(self, 'strategy_engine'):
        self.strategy_engine.process_market_data(
            current_price, 
            datetime.now()
        )
```

### 🎯 **第六階段: 用戶界面 (2-3天)**

#### **步驟6.1: 策略控制面板**
```python
class StrategyControlPanel(tk.Frame):
    def __init__(self, master=None):
        super().__init__(master)
        self.strategy_engine = None
        self.create_widgets()
    
    def create_widgets(self):
        # 策略狀態顯示
        # 開盤區間顯示
        # 當前部位顯示
        # 損益統計
        # 控制按鈕 (啟動/停止/緊急平倉)
```

#### **步驟6.2: 即時監控界面**
- 📊 開盤區間圖表
- 📈 即時損益曲線
- 📋 部位明細表格
- 🎯 策略狀態指示器

### 🎯 **第七階段: 測試與優化 (3-5天)**

#### **步驟7.1: 模擬測試**
- 🧪 使用歷史資料進行模擬
- 📊 驗證策略邏輯正確性
- 🔍 測試風險控制機制

#### **步驟7.2: 紙上交易**
- 📝 連接即時報價但不實際下單
- 📊 記錄模擬交易結果
- 🔧 調整參數和邏輯

#### **步驟7.3: 小額實盤測試**
- 💰 使用最小口數進行實盤測試
- 📈 監控實際執行效果
- 🛠️ 修正執行問題

## 🔧 **技術實作重點**

### 📊 **資料流設計**
```
即時報價 → 策略引擎 → 信號偵測 → 部位管理 → 下單模組
    ↓           ↓           ↓           ↓
SQLite ← 資料記錄 ← 交易記錄 ← 回報處理 ← 回報模組
```

### 🛡️ **錯誤處理**
- ✅ 網路斷線重連機制
- ✅ 資料庫錯誤恢復
- ✅ 策略狀態持久化
- ✅ 緊急平倉機制

### ⚡ **性能優化**
- ✅ 異步資料處理
- ✅ 記憶體使用優化
- ✅ 資料庫查詢優化
- ✅ UI響應性保證

## 📋 **開發時程估算**

| 階段 | 功能 | 預估時間 | 累計時間 |
|------|------|----------|----------|
| 1 | 基礎架構 | 2天 | 2天 |
| 2 | 信號偵測 | 3天 | 5天 |
| 3 | 部位管理 | 4天 | 9天 |
| 4 | 風險控制 | 3天 | 12天 |
| 5 | 策略引擎 | 4天 | 16天 |
| 6 | 用戶界面 | 3天 | 19天 |
| 7 | 測試優化 | 5天 | 24天 |

**總計: 約3-4週完成**

## 🎯 **成功標準**

### ✅ **功能完整性**
- 能正確識別開盤區間
- 能準確偵測突破信號
- 能同時管理多口部位
- 能執行移動停利邏輯
- 能實施保護性停損

### 📊 **性能指標**
- 信號延遲 < 100ms
- 下單執行 < 500ms
- 系統穩定運行 > 8小時
- 資料準確率 > 99.9%

### 🛡️ **風險控制**
- 最大回撤控制
- 緊急停止機制
- 異常狀況處理
- 資料備份恢復

---

**🚀 這個開發計劃將把您的回測策略轉化為完整的實盤交易系統！**

*計劃制定: 2025-06-30*  
*預估完成: 2025-07-24*  
*目標: 全自動當沖策略交易系統*
