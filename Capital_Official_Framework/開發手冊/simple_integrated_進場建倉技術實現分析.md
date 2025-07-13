# simple_integrated.py 進場建倉技術實現詳細分析

## 📋 概述

本文檔詳細分析 `simple_integrated.py` 策略下單機的進場建倉技術實現方式，包括訊號確認、建倉模組、資料庫操作、回報處理、部位狀態更新、失敗處理、追價機制和 async 優化等核心技術細節。

## 🎯 1. 訊號確認機制

### 1.1 突破訊號檢測流程

**主要函數**: `check_breakout_signals_safe(price, time_str)`

```python
def check_breakout_signals_safe(self, price, time_str):
    """執行進場 - 在檢測到突破信號後的下一個報價進場"""
    try:
        # 如果等待進場且有突破方向
        if self.waiting_for_entry and self.breakout_direction and not self.current_position:
            direction = self.breakout_direction
            self.waiting_for_entry = False  # 重置等待狀態
            
            # 🎯 多組策略進場邏輯
            if self.multi_group_enabled and self.multi_group_running and self.multi_group_position_manager:
                self.execute_multi_group_entry(direction, price, time_str)
            else:
                # 單一策略進場邏輯
                self.enter_position_safe(direction, price, time_str)
```

**訊號確認步驟**:
1. **區間計算**: `update_range_calculation_safe()` - 計算開盤區間高低點
2. **即時空單檢測**: `check_immediate_short_entry_safe()` - 價格跌破區間下緣立即觸發
3. **多單1分K檢測**: `check_minute_candle_breakout_safe()` - 1分K收盤價突破區間上緣
4. **進場信號處理**: `check_breakout_signals_safe()` - 在下一個報價執行進場

### 1.2 訊號觸發條件

**空單即時觸發**:
```python
def check_immediate_short_entry_safe(self, price, time_str):
    # 🚀 空單即時檢測：任何報價跌破區間下緣就立即觸發
    if price < self.range_low:
        self.first_breakout_detected = True
        self.breakout_direction = 'SHORT'
        self.waiting_for_entry = True
```

**多單1分K觸發**:
```python
def check_minute_candle_breakout_safe(self):
    # 多單檢測：1分K收盤價突破區間上緣
    if close_price > self.range_high:
        self.first_breakout_detected = True
        self.breakout_direction = 'LONG'
        self.waiting_for_entry = True
```

## 🏗️ 2. 建倉模組架構

### 2.1 主要建倉函數

**核心函數**: `enter_position_safe(direction, price, time_str)`

**職責分工**:
- **訊號處理**: 確認突破方向和進場價格
- **部位記錄**: 創建 `current_position` 字典記錄部位資訊
- **下單執行**: 調用 `VirtualRealOrderManager` 執行實際下單
- **追蹤註冊**: 註冊到 `UnifiedOrderTracker` 進行回報追蹤

### 2.2 虛實單管理器 (VirtualRealOrderManager)

**模組位置**: `virtual_real_order_manager.py`

**核心功能**:
```python
def execute_strategy_order(self, direction, signal_source, product, price, quantity, new_close=0):
    """執行策略下單 - 統一入口"""
    
    # 1. 生成唯一訂單ID
    order_id = f"{signal_source}_{int(time.time() * 1000)}"
    
    # 2. 建立下單參數
    order_params = OrderParams(
        account=self.default_account,
        product=product,
        direction=direction,
        quantity=quantity,
        price=price,
        order_type="FOK",
        new_close=new_close,
        signal_source=signal_source
    )
    
    # 3. 根據模式分流處理
    if self.is_real_mode:
        result = self.execute_real_order(order_params)
    else:
        result = self.execute_virtual_order(order_params)
```

**實際下單執行**:
```python
def execute_real_order(self, order_params):
    """執行實際下單 - 使用群益API"""
    
    # 調用群益API下單
    api_result = self.parent.place_future_order_direct(order_params)
    
    # 記錄待追蹤訂單
    self.pending_orders[order_params.order_id] = order_params
    
    return OrderResult(success=True, mode="real", order_id=order_params.order_id, api_result=api_result)
```

## 🗄️ 3. 資料庫建倉操作

### 3.1 多組策略資料庫管理

**模組**: `MultiGroupDatabaseManager`

**建倉記錄結構**:
```sql
CREATE TABLE strategy_groups (
    group_id INTEGER PRIMARY KEY,
    direction TEXT NOT NULL,
    entry_price REAL,
    entry_time TEXT,
    total_lots INTEGER,
    filled_lots INTEGER DEFAULT 0,
    status TEXT DEFAULT 'PENDING'
);

CREATE TABLE positions (
    position_id INTEGER PRIMARY KEY AUTOINCREMENT,
    group_id INTEGER,
    lot_number INTEGER,
    entry_price REAL,
    entry_time TEXT,
    status TEXT DEFAULT 'PENDING'
);
```

**建倉資料庫操作**:
```python
def create_strategy_group(self, direction, entry_price, entry_time, total_lots):
    """創建策略組記錄"""
    
    group_id = self.get_next_group_id()
    
    # 插入策略組記錄
    self.execute_query("""
        INSERT INTO strategy_groups 
        (group_id, direction, entry_price, entry_time, total_lots, status)
        VALUES (?, ?, ?, ?, ?, 'PENDING')
    """, (group_id, direction, entry_price, entry_time, total_lots))
    
    # 創建個別部位記錄
    for lot_num in range(1, total_lots + 1):
        self.execute_query("""
            INSERT INTO positions 
            (group_id, lot_number, entry_price, entry_time, status)
            VALUES (?, ?, ?, ?, 'PENDING')
        """, (group_id, lot_num, entry_price, entry_time))
```

### 3.2 SQLite 本地儲存

**模組**: `sqlite_manager.py`

**優勢**:
- **高性能**: 本地資料庫，無網路延遲
- **事務安全**: 支援 ACID 特性
- **併發處理**: 支援多線程安全操作
- **資料持久化**: 系統重啟後資料不丟失

## 📡 4. 回報接收處理機制 (0.5秒窗口)

### 4.1 回報頻率控制器

**類別**: `SimpleQuoteThrottler`

```python
class SimpleQuoteThrottler:
    """簡單的報價頻率控制器 - 零風險設計"""
    def __init__(self, interval_ms=500):
        self.interval = interval_ms / 1000.0  # 轉換為秒 (0.5秒)
        self.last_process_time = 0
        
    def should_process(self):
        """檢查是否應該處理此次報價"""
        current_time = time.time()
        if current_time - self.last_process_time >= self.interval:
            self.last_process_time = current_time
            return True
        return False
```

**0.5秒窗口設定**:
- **預設間隔**: 500毫秒 (0.5秒)
- **控制機制**: 限制報價處理頻率，避免過度頻繁的回報處理
- **性能優化**: 大幅降低 CPU 使用率和 GIL 競爭

### 4.2 OnNewData 回報事件處理

**主要處理器**: `OnNewData(self, btrUserID, bstrData)`

```python
def OnNewData(self, btrUserID, bstrData):
    """即時委託狀態回報 - Console詳細版本"""
    try:
        cutData = bstrData.split(',')
        
        # 🔧 強力過濾歷史回報：檢查是否為啟動後的新回報
        if not self.parent._is_new_order_reply(bstrData):
            return  # 靜默跳過歷史回報
            
        # 🚨 原始數據轉移到Console
        print(f"📋 [REPLY] OnNewData: {cutData}")
        
        # 🔧 並行回報處理，讓兩個追蹤器同時接收回報
        simplified_processed = False
        total_processed = False
        
        # 處理1: 簡化追蹤器（主要FIFO邏輯）
        if hasattr(self.parent.multi_group_position_manager, 'simplified_tracker'):
            simplified_processed = self.parent.multi_group_position_manager.simplified_tracker.process_order_reply(bstrData)
            
        # 處理2: 統一追蹤器（向後相容）
        if hasattr(self.parent, 'unified_order_tracker'):
            self.parent.unified_order_tracker.process_real_order_reply(bstrData)
```

### 4.3 回報過濾機制

**初始化**: `_init_reply_filter()`

```python
def _init_reply_filter(self):
    """初始化回報過濾機制"""
    import time
    self._order_system_start_time = time.time()
    self._known_order_ids = set()  # 記錄我們下的訂單ID
    self._manual_order_started = False  # 手動啟動標記
```

**過濾邏輯**: `_is_new_order_reply(reply_data)`

```python
def _is_new_order_reply(self, reply_data: str) -> bool:
    """判斷是否為新的訂單回報（非歷史回報）"""
    
    current_time = time.time()
    startup_elapsed = current_time - self._order_system_start_time
    
    # 策略1: 啟動後60秒內，拒絕所有回報
    if startup_elapsed < 60:
        return False
        
    # 策略2: 檢查是否有手動啟動標記
    if not self._manual_order_started:
        return False
        
    return True
```

## 🔄 5. 部位狀態確認與資料庫更新

### 5.1 SimplifiedOrderTracker FIFO 處理

**核心函數**: `process_order_reply(reply_data)`

```python
def process_order_reply(self, reply_data: str) -> bool:
    """統一處理進場和平倉回報 - 避免重複處理"""
    
    try:
        cutData = reply_data.split(',')
        order_type = cutData[16]  # 委託狀態
        price = float(cutData[9])  # 成交價格
        qty = int(cutData[10])    # 成交數量
        product = cutData[1]      # 商品代碼
        
        if order_type == "D":  # 成交
            # 🔧 優先處理進場成交 (更常見的情況)
            processed = self._handle_fill_report_fifo(price, qty, product)
            if processed:
                return True
                
            # 再嘗試平倉成交處理
            processed = self._handle_exit_fill_report(price, qty, product)
            return processed
            
        elif order_type == "C":  # 取消
            # 處理取消回報
            processed = self._handle_cancel_report_fifo(price, qty, product)
            return processed
            
    except Exception as e:
        print(f"[SIMPLIFIED_TRACKER] ❌ 處理回報失敗: {e}")
        return False
```

### 5.2 部位狀態更新流程

**FIFO 匹配邏輯**:
```python
def _find_matching_group_fifo(self, price: float, qty: int, product: str):
    """使用純FIFO匹配找到策略組"""
    
    # 按組ID順序查找第一個未完成的策略組
    for group_id in sorted(self.strategy_groups.keys()):
        group = self.strategy_groups[group_id]
        
        if not group.is_complete() and group.product == product:
            return group
            
    return None
```

**狀態更新**:
```python
def _update_group_fill_status(self, group, fill_qty: int, fill_price: float):
    """更新策略組成交狀態"""
    
    group.filled_lots += fill_qty
    group.avg_fill_price = ((group.avg_fill_price * (group.filled_lots - fill_qty)) + 
                           (fill_price * fill_qty)) / group.filled_lots
    
    # 檢查是否完全成交
    if group.filled_lots >= group.total_lots:
        group.status = "FILLED"
        
    # 更新資料庫
    self._update_database_status(group)
```

## ❌ 6. 建倉失敗處理方式

### 6.1 下單失敗處理

**VirtualRealOrderManager 錯誤處理**:
```python
def execute_real_order(self, order_params):
    """執行實際下單 - 使用群益API"""
    try:
        api_result = self.parent.place_future_order_direct(order_params)
        
        if api_result and api_result.get('success', False):
            return OrderResult(success=True, mode="real", order_id=order_params.order_id)
        else:
            error_msg = api_result.get('error', '未知錯誤') if api_result else 'API調用失敗'
            return OrderResult(success=False, mode="real", error=error_msg)
            
    except Exception as e:
        error_msg = f"實際下單失敗: {e}"
        return OrderResult(success=False, mode="real", error=error_msg)
```

**策略層失敗處理**:
```python
def enter_position_safe(self, direction, price, time_str):
    """安全的建倉處理"""
    try:
        # 執行下單
        for lot_id in range(1, total_lots + 1):
            order_result = self.virtual_real_order_manager.execute_strategy_order(...)
            
            if order_result.success:
                success_count += 1
                # 註冊到統一回報追蹤器
                self.unified_order_tracker.register_order(...)
            else:
                print(f"❌ [STRATEGY] 第{lot_id}口下單失敗: {order_result.error}")
                
        # 檢查整體成功率
        if success_count == 0:
            self.add_strategy_log(f"❌ {direction} 下單失敗: 所有口數都失敗")
            # 清理部位記錄
            self.current_position = None
            
    except Exception as e:
        self.add_strategy_log(f"❌ 建倉失敗: {e}")
        self.current_position = None
```

### 6.2 回報超時處理

**超時檢測機制**:
```python
def check_order_timeout(self):
    """檢查訂單超時"""
    
    current_time = time.time()
    timeout_threshold = 30  # 30秒超時
    
    for order_id, order_params in self.pending_orders.items():
        if current_time - order_params.timestamp > timeout_threshold:
            # 標記為超時失敗
            self.handle_order_timeout(order_id, order_params)
```

## 🔄 7. 追價機制與部位確認

### 7.1 追價觸發條件

**取消回報觸發追價**:
```python
def _handle_cancel_report_fifo(self, price: float, qty: int, product: str) -> bool:
    """處理取消回報 - 觸發追價機制"""
    
    # 找到被取消的策略組
    group = self._find_matching_group_fifo(price, qty, product)
    if group and not group.is_complete():
        
        # 標記為需要追價
        group.is_retrying = True
        group.pending_retry_lots = qty
        
        # 觸發追價回調
        for callback in self.retry_callbacks:
            callback(group.group_id, qty)
            
        return True
    return False
```

### 7.2 追價價格計算

**核心函數**: `_calculate_exit_retry_price(original_direction, retry_count)`

```python
def _calculate_exit_retry_price(self, original_direction: str, retry_count: int) -> float:
    """計算平倉追價價格"""
    
    # 獲取當前市價
    current_ask1 = self.virtual_real_order_manager.get_ask1_price("TM0000")
    current_bid1 = self.virtual_real_order_manager.get_bid1_price("TM0000")
    
    if original_direction.upper() == "LONG":
        # 🔧 多單平倉：使用BID1 - retry_count點 (向下追價)
        retry_price = current_bid1 - retry_count
        return retry_price
    elif original_direction.upper() == "SHORT":
        # 🔧 空單平倉：使用ASK1 + retry_count點 (向上追價)
        retry_price = current_ask1 + retry_count
        return retry_price
```

**追價限制**:
- **最大重試次數**: 5次
- **滑價限制**: 最大5點滑價保護
- **時間限制**: 30秒內必須完成

## 🚀 8. Async 優化與內存計算

### 8.1 異步峰值更新系統

**啟用機制**:
```python
def toggle_async_peak_update(self):
    """切換異步峰值更新狀態"""
    
    self.enable_async_peak_update = not self.enable_async_peak_update
    
    if self.enable_async_peak_update:
        # 啟用異步峰值更新
        success = self.multi_group_risk_engine.enable_async_peak_updates(True)
        if success:
            self.add_log("🚀 異步峰值更新已啟用")
            self.add_log("💡 峰值更新將使用異步處理，大幅降低延遲")
```

**異步處理優勢**:
- **降低延遲**: 避免同步計算阻塞主線程
- **提高吞吐量**: 並行處理多個部位的峰值更新
- **減少 GIL 競爭**: 使用異步 I/O 避免 Python GIL 限制

### 8.2 內存計算批次更新

**統一移動停利計算器**:
```python
# 🚀 優先模式：統一移動停利計算器（內存計算，無資料庫查詢）
if hasattr(self.parent, 'unified_trailing_enabled') and self.parent.unified_trailing_enabled:
    # 🚀 純內存計算，獲取所有活躍部位
    active_positions = self.parent.trailing_calculator.get_active_positions()
    
    # 為每個活躍部位更新價格（純內存操作）
    for position_id in active_positions:
        trigger_info = self.parent.trailing_calculator.update_price(
            position_id, corrected_price
        )
```

**批次更新機制**:
- **內存優先**: 所有計算在內存中完成，避免頻繁資料庫查詢
- **批次同步**: 定期批次更新資料庫，減少 I/O 操作
- **事件驅動**: 只在觸發條件時才執行資料庫寫入

### 8.3 一口與多口處理差異

**一口處理**:
```python
# 單口下單 - 簡化邏輯
order_result = self.virtual_real_order_manager.execute_strategy_order(
    direction=direction,
    signal_source=f"single_strategy_lot_1",
    product="TM0000",
    price=price,
    quantity=1
)
```

**多口處理**:
```python
# 多口下單 - 循環處理
total_lots = 3
success_count = 0

for lot_id in range(1, total_lots + 1):
    order_result = self.virtual_real_order_manager.execute_strategy_order(
        direction=direction,
        signal_source=f"multi_strategy_lot_{lot_id}",
        product="TM0000",
        price=ask1_price or price,
        quantity=1  # 🎯 每筆都是1口
    )
    
    if order_result.success:
        success_count += 1
        # 註冊到統一回報追蹤器
        self.unified_order_tracker.register_order(...)
```

**差異化處理**:
- **一口**: 直接下單，簡化追蹤
- **多口**: 循環下單，分別追蹤每口的成交狀態
- **FIFO 追蹤**: 使用先進先出邏輯匹配回報與訂單
- **批次管理**: 多口訂單作為一個策略組統一管理

## 📊 總結

simple_integrated.py 的進場建倉技術實現採用了多層次的架構設計：

1. **訊號層**: 精確的突破檢測和確認機制
2. **執行層**: 虛實單管理器提供統一的下單介面
3. **追蹤層**: FIFO 回報追蹤和狀態管理
4. **儲存層**: SQLite 本地資料庫提供高性能資料持久化
5. **優化層**: 異步處理和內存計算提升系統性能

整個系統通過 0.5 秒回報窗口控制、追價機制、失敗處理和 async 優化，確保了高效穩定的實單交易執行能力。
