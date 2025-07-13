# simple_integrated.py 程式碼結構與職責劃分分析

## 概覽
本文檔詳細分析 `simple_integrated.py` 的程式碼結構，包括主要類別、函式及其職責劃分。

## 1. 主要類別與函式 (Key Classes & Functions)

### 🏗️ **主要類別 (Main Classes)**

#### `SimpleIntegratedApp` (主應用程式類別)
- **職責**: 整合交易系統的主控制器
- **功能**: GUI管理、系統初始化、事件協調、策略執行
- **重要屬性**:
  - `logged_in`: 登入狀態
  - `strategy_enabled`: 策略啟用狀態
  - `current_position`: 當前部位信息
  - `range_high/range_low`: 交易區間上下軌
  - `multi_group_*`: 多組策略相關狀態
  - `virtual_real_order_manager`: 虛實單管理器
  - `multi_group_position_manager`: 多組部位管理器

#### `SimpleQuoteThrottler` (報價頻率控制器)
- **職責**: 控制報價處理頻率，避免系統過載
- **功能**: 報價節流、統計監控
- **關鍵方法**:
  - `should_process()`: 檢查是否應該處理此次報價
  - `get_stats()`: 獲取統計信息

#### `SKReplyLibEvent` (內部事件處理類別)
- **職責**: 處理券商API回報事件
- **功能**: 委託回報、連線狀態、錯誤處理
- **關鍵方法**:
  - `OnNewData()`: 處理委託狀態回報
  - `OnConnect()`: 連線事件處理
  - `OnDisconnect()`: 斷線事件處理
  - `OnReplyMessage()`: 回報訊息處理
  - `OnSmartData()`: 智慧單回報處理

#### `SKQuoteLibEvents` (內部報價事件類別)
- **職責**: 處理即時報價事件
- **功能**: TICK數據處理、五檔報價更新、策略觸發
- **關鍵方法**:
  - `OnNotifyTicksLONG()`: 處理即時報價
  - `OnNotifyBest5LONG()`: 處理五檔報價

### 🔧 **核心功能函式 (Core Functions)**

#### 系統初始化類
- `__init__()`: 系統主初始化，設定所有組件
- `init_optimized_risk_manager()`: 初始化優化風險管理器
- `init_real_order_system()`: 實際下單系統初始化
- `init_virtual_real_order_system()`: 虛實單整合系統初始化
- `init_multi_group_system()`: 多組策略系統初始化
- `_update_multi_group_order_components()`: 更新多組策略下單組件

#### 連線與認證類
- `login()`: 系統登入，處理群益API認證
- `init_order()`: 下單模組初始化
- `init_reply_connection()`: 初始化回報連線
- `connect_quote()`: 報價服務連線
- `subscribe_quote()`: 報價訂閱
- `register_reply_events()`: 註冊回報事件
- `register_order_reply_events()`: 註冊下單回報事件
- `register_quote_events()`: 註冊報價事件

#### 策略邏輯類
- `process_strategy_logic_safe()`: 主策略邏輯處理
- `update_range_calculation_safe()`: 區間計算
- `is_in_range_time_safe()`: 時間檢查
- `update_minute_candle_safe()`: 更新分鐘K線數據
- `check_immediate_short_entry_safe()`: 即時空單進場檢測
- `check_minute_candle_breakout_safe()`: 突破信號檢測
- `check_breakout_signals_safe()`: 進場信號處理

#### 部位管理類
- `enter_position_safe()`: 建倉處理
- `exit_position_safe()`: 平倉處理
- `check_exit_conditions_safe()`: 出場條件檢查
- `check_trailing_stop_logic()`: 移動停利邏輯
- `execute_multi_group_entry()`: 執行多組策略進場
- `create_multi_group_strategy_with_direction()`: 根據突破方向創建策略組

#### 下單執行類
- `place_future_order()`: 期貨下單執行
- `test_order()`: 測試下單功能
- `_calculate_exit_retry_price()`: 計算平倉追價價格

#### 風險控制類
- `check_multi_group_exit_conditions()`: 檢查多組策略出場條件
- `_is_new_order_reply()`: 判斷是否為新的訂單回報
- `enable_order_reply_processing()`: 啟用訂單回報處理
- `disable_order_reply_processing()`: 停用訂單回報處理

#### 策略控制類
- `start_strategy()`: 啟動策略監控
- `stop_strategy()`: 停止策略監控
- `prepare_multi_group_strategy()`: 準備多組策略
- `start_multi_group_strategy()`: 啟動多組策略
- `stop_multi_group_strategy()`: 停止多組策略

#### GUI與介面類
- `create_widgets()`: 建立使用者介面
- `create_main_page()`: 建立主要功能頁面
- `create_strategy_page()`: 建立策略監控頁面
- `create_strategy_panel()`: 創建策略監控面板
- `create_multi_group_strategy_page()`: 創建多組策略配置頁面

#### 日誌與監控類
- `add_log()`: 添加系統日誌
- `add_strategy_log()`: 添加策略日誌
- `start_status_monitor()`: 啟動狀態監控
- `monitor_strategy_status()`: 監控策略狀態

## 2. 職責對應 (Responsibility Mapping)

### 🎯 **交易訊號生成 (Signal Generation)**

**主要負責函式**:
- `process_strategy_logic_safe()`: 主策略邏輯處理入口
- `update_range_calculation_safe()`: 開盤區間計算 (08:46-08:48)
- `is_in_range_time_safe()`: 精確時間檢查
- `update_minute_candle_safe()`: 分鐘K線數據更新
- `check_immediate_short_entry_safe()`: 即時空單進場檢測
- `check_minute_candle_breakout_safe()`: 1分K多單突破檢測

**觸發機制**:
```
OnNotifyTicksLONG() → process_strategy_logic_safe()
├── update_range_calculation_safe() (區間時間內)
├── check_immediate_short_entry_safe() (空單即時檢測)
└── check_minute_candle_breakout_safe() (多單1分K檢測)
```

**訊號類型**:
- **多單訊號**: 1分K收盤價突破區間上軌
- **空單訊號**: 任何報價跌破區間下軌 (即時觸發)

### 🚀 **部位建立 (Position Entry / 建倉)**

**主要負責函式**:
- `check_breakout_signals_safe()`: 進場信號確認
- `enter_position_safe()`: 單一策略建倉處理
- `execute_multi_group_entry()`: 多組策略建倉處理
- `create_multi_group_strategy_with_direction()`: 根據突破方向創建策略組

**建倉流程**:
```
突破信號檢測 → waiting_for_entry = True
↓
下一個報價觸發 → check_breakout_signals_safe()
├── 單一策略: enter_position_safe()
└── 多組策略: execute_multi_group_entry()
    └── create_multi_group_strategy_with_direction()
```

**下單執行**:
- 使用 `VirtualRealOrderManager` 執行多筆1口FOK下單
- 註冊到 `UnifiedOrderTracker` 進行回報追蹤
- 支援虛擬/實際下單模式切換

### 🛡️ **初始停損設定 (Initial Stop-Loss Setup)**

**主要負責函式**:
- `enter_position_safe()`: 建倉時設定初始停損
- `check_exit_conditions_safe()`: 檢查初始停損觸發

**停損邏輯**:
```python
# 在 enter_position_safe() 中設定
self.current_position = {
    'direction': direction,
    'entry_price': price,
    # ... 其他屬性
}

# 在 check_exit_conditions_safe() 中檢查
if direction == "LONG" and price <= self.range_low:
    self.exit_position_safe(price, time_str, f"初始停損 {self.range_low:.0f}")
elif direction == "SHORT" and price >= self.range_high:
    self.exit_position_safe(price, time_str, f"初始停損 {self.range_high:.0f}")
```

**停損設定**:
- **多單停損**: 區間下軌 (`range_low`)
- **空單停損**: 區間上軌 (`range_high`)

### 📊 **部位狀態追蹤 (Position Tracking)**

**主要負責組件**:
- `current_position`: 單一策略部位狀態
- `MultiGroupPositionManager`: 多組策略部位管理
- `UnifiedOrderTracker`: 統一回報追蹤
- `SimplifiedOrderTracker`: 簡化FIFO追蹤

**追蹤機制**:
```
OnNewData() (回報事件)
├── SimplifiedOrderTracker.process_order_reply()
├── UnifiedOrderTracker.process_real_order_reply()
└── MultiGroupPositionManager 狀態更新
```

**狀態管理**:
- 委託狀態: 新單(N)、成交(D)、取消(C)、錯誤(R)
- 部位狀態: PENDING → FILLED → EXITED
- 資料庫同步: SQLite本地儲存

### 🎯 **移動停利/停損 (Trailing Stop / 移動停利)**

**主要負責函式**:
- `check_trailing_stop_logic()`: 移動停利邏輯檢查
- `check_exit_conditions_safe()`: 出場條件整合檢查

**移動停利邏輯**:
```python
# 啟動條件: 獲利15點
if direction == "LONG":
    activation_triggered = price >= entry_price + 15
else:  # SHORT
    activation_triggered = price <= entry_price - 15

# 回撤出場: 20%回撤
if trailing_activated:
    if direction == "LONG":
        total_gain = peak_price - entry_price
        pullback_amount = total_gain * 0.20
        trailing_stop_price = peak_price - pullback_amount
        if price <= trailing_stop_price:
            exit_position_safe(...)
```

**進階風險管理**:
- `OptimizedRiskManager`: 優化風險管理器
- `RiskManagementEngine`: 統一風險控制
- `UnifiedExitManager`: 統一出場管理

### 🔚 **部位平倉 (Position Closing / 平倉)**

**主要負責函式**:
- `exit_position_safe()`: 安全平倉處理
- `check_exit_conditions_safe()`: 出場條件檢查
- `check_multi_group_exit_conditions()`: 多組策略出場檢查

**平倉觸發條件**:
1. **初始停損**: 價格觸及區間邊界
2. **移動停利**: 20%回撤觸發
3. **收盤平倉**: 13:30強制平倉 (可選)
4. **手動平倉**: 使用者手動觸發

**平倉執行流程**:
```
出場條件觸發 → exit_position_safe()
├── 計算損益 (pnl = price差 × 50元/點)
├── 記錄交易日誌
├── 清除部位狀態
└── 更新UI顯示 (Console模式)
```

**追價機制**:
- `_calculate_exit_retry_price()`: 計算平倉追價價格
- 多單平倉: BID1 - retry_count點
- 空單平倉: ASK1 + retry_count點
- 最大重試5次，滑價限制5點

## 3. 組件關係圖 (Component Relationship)

### 🔄 **系統啟動流程**
```
SimpleIntegratedApp.__init__()
├── 載入使用者配置
├── 初始化GUI介面
├── init_multi_group_system()
├── init_optimized_risk_manager()
├── init_real_order_system()
├── init_virtual_real_order_system()
└── create_widgets()
```

### 🔐 **登入與連線流程**
```
login() → init_order() → connect_quote() → subscribe_quote()
├── SKCenterLib_Login() (群益API登入)
├── SKOrderLib_Initialize() (下單模組初始化)
├── register_reply_events() (註冊回報事件)
├── register_quote_events() (註冊報價事件)
└── 啟用測試下單功能
```

### 📊 **報價處理流程**
```
OnNotifyTicksLONG() (報價事件)
├── SimpleQuoteThrottler.should_process() (頻率控制)
├── 價格解析與格式化
├── 停損監控整合
│   ├── OptimizedRiskManager.update_price()
│   ├── ExitMechanismManager.process_price_update()
│   └── TrailingStopSystem 各組件更新
├── MultiGroupPositionManager.update_current_price()
├── process_strategy_logic_safe() (策略邏輯)
└── Console輸出與統計更新
```

### 🎯 **策略執行流程**
```
process_strategy_logic_safe()
├── update_range_calculation_safe() (區間計算)
├── update_minute_candle_safe() (K線更新)
├── check_immediate_short_entry_safe() (空單即時檢測)
├── check_minute_candle_breakout_safe() (多單1分K檢測)
├── check_breakout_signals_safe() (進場信號處理)
│   ├── enter_position_safe() (單一策略)
│   └── execute_multi_group_entry() (多組策略)
└── check_exit_conditions_safe() (出場檢查)
    ├── 初始停損檢查
    ├── check_trailing_stop_logic() (移動停利)
    ├── 收盤平倉檢查
    └── exit_position_safe() (執行平倉)
```

### 🚀 **下單執行流程**
```
enter_position_safe() / execute_multi_group_entry()
├── VirtualRealOrderManager.execute_strategy_order()
│   ├── 虛擬模式: 模擬下單
│   └── 實際模式: place_future_order()
│       └── Global.skO.SendFutureOrderCLR()
├── UnifiedOrderTracker.register_order()
└── 等待回報: OnNewData()
    ├── SimplifiedOrderTracker.process_order_reply()
    ├── UnifiedOrderTracker.process_real_order_reply()
    └── 狀態更新與追價處理
```

### 🔧 **回報處理流程**
```
OnNewData() (回報事件)
├── _is_new_order_reply() (過濾歷史回報)
├── 回報數據解析 (序號、類型、價格、數量等)
├── Console詳細輸出
├── SimplifiedOrderTracker.process_order_reply() (主要FIFO邏輯)
├── UnifiedOrderTracker.process_real_order_reply() (向後相容)
└── 追價機制觸發 (如需要)
    └── _calculate_exit_retry_price()
```

### 🏗️ **模組間依賴關係**
```
SimpleIntegratedApp (主控制器)
├── 依賴 → Global (群益API模組)
├── 依賴 → MultiGroupPositionManager (多組策略管理)
│   ├── 包含 → MultiGroupDatabaseManager
│   ├── 包含 → SimplifiedOrderTracker
│   └── 包含 → TotalLotManager
├── 依賴 → VirtualRealOrderManager (虛實單管理)
├── 依賴 → UnifiedOrderTracker (統一追蹤)
├── 依賴 → RiskManagementEngine (風險管理)
├── 依賴 → UnifiedExitManager (統一出場)
├── 依賴 → OptimizedRiskManager (優化風險管理)
└── 依賴 → RealTimeQuoteManager (即時報價)
```

### 🎮 **事件驅動架構**
```
群益API事件
├── SKReplyLibEvent (回報事件)
│   ├── OnConnect() → 自動切換實單模式
│   ├── OnDisconnect() → 連線狀態更新
│   ├── OnNewData() → 回報處理與追蹤
│   └── OnReplyMessage() → 一般訊息處理
└── SKQuoteLibEvents (報價事件)
    ├── OnNotifyTicksLONG() → 策略邏輯觸發
    └── OnNotifyBest5LONG() → 五檔報價更新
```

### 🛡️ **安全性設計特點**
- **Console模式優先**: 避免GUI更新造成GIL問題
- **回報過濾機制**: 防止歷史回報干擾當前交易
- **異常處理**: 所有關鍵方法都包含try-catch
- **頻率控制**: SimpleQuoteThrottler避免系統過載
- **模組化設計**: 可選模組載入，向後相容
- **多重風險控制**: 初始停損+移動停利+收盤平倉

## 4. 總結

`simple_integrated.py` 採用事件驅動的模組化架構，整合了完整的自動化交易功能：

1. **核心架構**: 以 `SimpleIntegratedApp` 為主控制器，整合多個專業模組
2. **事件處理**: 透過 `SKReplyLibEvent` 和 `SKQuoteLibEvents` 處理API事件
3. **策略邏輯**: 實現開盤區間突破策略，支援多組策略並行
4. **風險管理**: 多層次風險控制，包含停損、停利、收盤平倉
5. **下單系統**: 虛實單整合，支援模擬和實際交易
6. **安全設計**: Console模式、回報過濾、異常處理確保系統穩定

這個系統代表了專業級自動化交易平台的完整實現，適合在生產環境中進行期貨自動交易。

### 🎯 **交易訊號生成 (Signal Generation)**
**主要負責**: `check_minute_candle_breakout_safe()`
- **輔助函式**: 
  - `update_range_calculation_safe()`: 計算交易區間
  - `is_in_range_time_safe()`: 時間範圍檢查
  - `update_minute_candle_safe()`: 分鐘K線更新
- **觸發條件**: 分鐘K線收盤價突破區間上下軌

### 🏗️ **部位建立 (Position Entry)**
**主要負責**: `enter_position_safe()`
- **輔助函式**:
  - `check_breakout_signals_safe()`: 進場信號確認
  - `execute_multi_group_entry()`: 多組策略進場
  - `place_future_order()`: 實際下單執行
- **流程**: 信號確認 → 風險檢查 → 下單執行 → 部位記錄

### 🛡️ **初始停損設定 (Initial Stop-Loss Setup)**
**主要負責**: `enter_position_safe()` 內的停損邏輯
- **設定方式**: 
  - 多頭: 區間下軌作為停損
  - 空頭: 區間上軌作為停損
- **整合**: 與多組策略系統的風險管理引擎整合

### 📊 **部位狀態追蹤 (Position Tracking)**
**主要負責**: 
- `current_position` 屬性維護
- `SKReplyLibEvent.OnNewData()`: 委託回報處理
- `UnifiedOrderTracker`: 統一回報追蹤 (外部模組)
- `TotalLotManager`: 總量追蹤管理 (外部模組)

### 📈 **移動停利/停損 (Trailing Stop)**
**主要負責**: `check_trailing_stop_logic()`
- **觸發條件**: 
  - 獲利達到觸發點數
  - 價格回撤達到設定百分比
- **整合**: 與多組策略的個別停利設定整合

### 🚪 **部位平倉 (Position Closing)**
**主要負責**: `exit_position_safe()`
- **觸發來源**:
  - `check_exit_conditions_safe()`: 一般出場條件
  - `check_trailing_stop_logic()`: 移動停利觸發
  - `check_multi_group_exit_conditions()`: 多組策略風險管理
- **執行**: 透過 `place_future_order()` 執行平倉單

## 3. 組件關係圖 (Component Relationship)

### 🔄 **主要呼叫流程**
```
SimpleIntegratedApp.__init__()
├── init_real_order_system()
├── init_virtual_real_order_system()
├── init_multi_group_system()
└── create_widgets()
    ├── create_main_page()
    └── create_strategy_page()

登入流程:
login() → init_order() → connect_quote() → subscribe_quote()

策略執行流程:
OnNotifyTicksLONG() → process_strategy_logic_safe()
├── update_range_calculation_safe()
├── check_minute_candle_breakout_safe()
├── check_breakout_signals_safe() → enter_position_safe()
└── check_exit_conditions_safe() → exit_position_safe()

下單流程:
enter_position_safe() → place_future_order() → OnNewData()
```

### 🔗 **模組間依賴關係**
```
SimpleIntegratedApp
├── 依賴 → Global (群益API模組)
├── 依賴 → MultiGroupPositionManager (多組策略管理)
├── 依賴 → VirtualRealOrderManager (虛實單管理)
├── 依賴 → RiskManagementEngine (風險管理)
├── 依賴 → UnifiedOrderTracker (統一追蹤)
└── 依賴 → RealTimeQuoteManager (即時報價)

事件處理:
SKQuoteLibEvents → SimpleIntegratedApp.process_strategy_logic_safe()
SKReplyLibEvent → UnifiedOrderTracker.process_real_order_reply()
```

### 📡 **數據流向**
```
市場數據流:
券商API → SKQuoteLibEvents → process_strategy_logic_safe() → 策略邏輯

委託回報流:
券商API → SKReplyLibEvent → UnifiedOrderTracker → 部位更新

策略信號流:
區間計算 → 突破檢測 → 信號確認 → 下單執行 → 部位管理
```

## 4. 關鍵設計特點

### 🛡️ **安全性設計**
- 所有策略函式都有 `_safe` 後綴，包含異常處理
- Console模式避免UI更新造成的GIL問題
- 虛實單切換機制防止誤操作

### 🎯 **模組化架構**
- 清楚分離GUI、策略邏輯、下單執行
- 外部模組負責專業功能（風險管理、部位追蹤）
- 事件驅動的鬆耦合設計

### 📊 **多組策略支援**
- 支援同時運行多個策略配置
- 統一的風險管理和部位追蹤
- 靈活的參數配置和監控機制

## 5. 詳細函式分析

### 🎯 **策略核心函式詳解**

#### `process_strategy_logic_safe(price, time_str)`
- **職責**: 主策略邏輯協調器
- **輸入**: 即時價格、時間字串
- **流程**:
  1. 價格數據驗證和統計更新
  2. 區間計算邏輯調用
  3. 分鐘K線數據更新
  4. 突破信號檢測
  5. 進場信號處理
  6. 出場條件檢查
  7. 多組策略風險管理
- **特點**: 包含完整異常處理，避免UI更新防止GIL問題

#### `update_range_calculation_safe(price, time_str)`
- **職責**: 開盤區間計算
- **邏輯**:
  - 檢查是否在指定時間範圍內（預設08:46-08:47）
  - 收集區間內的所有價格數據
  - 計算最高價和最低價作為交易邊界
- **輸出**: 設定 `range_high` 和 `range_low` 屬性

#### `check_minute_candle_breakout_safe()`
- **職責**: 突破信號檢測
- **條件**:
  - 區間已計算完成
  - 尚未檢測到首次突破
  - 有完整的分鐘K線數據
- **邏輯**:
  - 多頭信號：K線收盤價 > 區間上軌
  - 空頭信號：K線最低價 < 區間下軌
- **輸出**: 設定突破方向和等待進場狀態

### 🏗️ **部位管理函式詳解**

#### `enter_position_safe(direction, price, time_str)`
- **職責**: 安全建倉處理
- **參數**:
  - `direction`: "LONG" 或 "SHORT"
  - `price`: 進場價格
  - `time_str`: 進場時間
- **流程**:
  1. 檢查是否已有部位
  2. 創建部位記錄
  3. 設定初始停損
  4. 執行下單
  5. 更新UI狀態
- **停損設定**:
  - 多頭：區間下軌
  - 空頭：區間上軌

#### `exit_position_safe(price, time_str, reason)`
- **職責**: 安全平倉處理
- **參數**:
  - `price`: 出場價格
  - `time_str`: 出場時間
  - `reason`: 出場原因
- **流程**:
  1. 驗證部位存在
  2. 計算損益
  3. 執行平倉單
  4. 清除部位記錄
  5. 記錄交易日誌
- **損益計算**: 考慮方向、數量、手續費

#### `check_trailing_stop_logic(price, time_str)`
- **職責**: 移動停利邏輯
- **觸發條件**:
  - 獲利達到設定觸發點數
  - 價格回撤超過設定百分比
- **支援**: 多層次觸發點和不同回撤比例

### 🔧 **系統管理函式詳解**

#### `place_future_order(order_params)`
- **職責**: 期貨下單執行
- **參數**: 包含完整下單資訊的字典
- **流程**:
  1. 參數驗證
  2. 創建群益下單物件
  3. 設定交易參數
  4. 執行下單API
  5. 處理回傳結果
- **整合**: 與虛實單管理器整合

#### `init_multi_group_system()`
- **職責**: 多組策略系統初始化
- **組件**:
  - MultiGroupDatabaseManager: 數據庫管理
  - MultiGroupPositionManager: 部位管理
  - RiskManagementEngine: 風險控制
  - MultiGroupConfigPanel: 配置介面
- **狀態**: 設定多組策略相關狀態變數

## 6. 安全性與穩定性設計

### 🛡️ **異常處理策略**
- 所有策略函式使用 `try-except` 包裝
- 靜默處理非關鍵錯誤，避免中斷報價處理
- Console輸出詳細錯誤信息供調試

### 🔒 **GIL問題解決**
- 避免在背景線程中更新UI
- 使用Console輸出替代動態UI更新
- 移除複雜時間操作，減少線程競爭

### 🎯 **模組化設計優勢**
- 清楚的職責分離
- 鬆耦合的組件關係
- 易於測試和維護
- 支援功能擴展

---
*本文檔基於 simple_integrated.py 版本分析，共3135行程式碼*
*最後更新: 2025-01-12*
