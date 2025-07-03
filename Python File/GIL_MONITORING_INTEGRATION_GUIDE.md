# GIL監控集成指南 - 開發階段調試工具

## 🎯 目標

在開發階段為現有的群益API代碼添加GIL監控，幫助快速定位可能導致GIL錯誤的代碼位置，避免程式崩潰。

## 📁 監控工具文件

- `gil_monitor.py` - 核心監控系統
- `gil_decorators.py` - 裝飾器工具集
- `gil_monitoring_example.py` - 實際應用示例
- `gil_monitor.log` - 監控日誌文件（自動生成）

## 🚀 快速集成步驟

### 步驟1: 導入監控工具

在需要監控的文件頂部添加：

```python
# 導入GIL監控工具
from gil_monitor import log_ui_operation, log_com_event
from gil_decorators import com_event_monitor, ui_function_monitor, log_dangerous_operation
```

### 步驟2: 為COM事件添加監控

**方法A: 使用裝飾器（推薦）**

```python
@com_event_monitor
def OnNotifyTicksLONG(self, sMarketNo, nStockidx, nPtr, lDate, lTimehms, 
                     lTimemillismicros, nBid, nAsk, nClose, nQty, nSimulate):
    """Tick事件 - 帶有完整GIL監控"""
    try:
        # 原有的處理邏輯
        # ...
    except Exception as e:
        # COM事件絕不能拋出異常
        return 0
```

**方法B: 手動添加監控**

```python
def OnNotifyTicksLONG(self, ...):
    try:
        # 記錄COM事件
        log_com_event("OnNotifyTicksLONG", f"價格:{nClose}", has_ui_operations=True)
        
        # 檢查是否有危險操作
        if not threading.current_thread() == threading.main_thread():
            log_dangerous_operation("COM事件中的UI操作", "OnNotifyTicksLONG")
        
        # 原有邏輯...
        
    except Exception as e:
        log_dangerous_operation(f"COM事件異常: {e}", "OnNotifyTicksLONG")
        return 0
```

### 步驟3: 為UI操作添加監控

**方法A: 使用裝飾器**

```python
@ui_function_monitor
def update_price_display(self, price, time_str):
    """更新價格顯示 - 帶有UI監控"""
    self.price_label.config(text=str(price))
    self.time_label.config(text=time_str)
```

**方法B: 手動添加監控**

```python
def update_price_display(self, price, time_str):
    # 記錄UI操作
    log_ui_operation("price_label_update", f"價格:{price}", "Label")
    
    # 檢查線程安全
    if not threading.current_thread() == threading.main_thread():
        log_dangerous_operation("在背景線程中更新UI", "update_price_display")
    
    # 執行UI操作
    self.price_label.config(text=str(price))
    self.time_label.config(text=time_str)
```

### 步驟4: 監控關鍵位置

**在可能有問題的地方添加檢查點：**

```python
# 在任何UI操作前檢查
from gil_decorators import check_thread_safety
if not check_thread_safety("critical_ui_update"):
    # 記錄警告並使用安全方式
    self.after_idle(self.safe_ui_update, data)
    return

# 在COM事件中記錄危險操作
if hasattr(self, 'some_ui_widget'):
    log_dangerous_operation("直接UI操作", "OnSomeEvent")
```

## 📋 具體集成示例

### 1. 修改 future_order.py

**在文件頂部添加：**
```python
from gil_monitor import log_ui_operation, log_com_event
from gil_decorators import com_event_monitor, log_dangerous_operation
```

**修改COM事件處理：**
```python
@com_event_monitor
def OnNotifyTicksLONG(self, sMarketNo, nStockidx, nPtr, lDate, lTimehms, 
                     lTimemillismicros, nBid, nAsk, nClose, nQty, nSimulate):
    """Tick事件 - 🔧 GIL錯誤修復 + 監控版本"""
    try:
        # 記錄事件詳情
        log_com_event("OnNotifyTicksLONG", f"價格:{nClose} 量:{nQty}", has_ui_operations=True)
        
        # 檢查危險操作
        if hasattr(self.parent, 'label_price'):
            log_dangerous_operation("COM事件中可能的UI操作", "OnNotifyTicksLONG")
        
        # 安全的數據更新
        with self.parent.data_lock:
            self.parent.last_price = nClose
            self.parent.last_update_time = lTimehms
        
        # 安全的UI更新
        self.parent.after_idle(
            self.parent.safe_update_quote_display,
            nClose, lTimehms, nBid, nAsk, nQty
        )
        
    except Exception as e:
        log_dangerous_operation(f"COM事件異常: {e}", "OnNotifyTicksLONG")
        return 0
```

**修改UI更新方法：**
```python
@ui_function_monitor
def safe_update_quote_display(self, price, time_hms, bid, ask, qty):
    """安全的報價顯示更新 - 帶監控"""
    try:
        log_ui_operation("quote_display_update", f"價格:{price}", "Label")
        
        # 更新UI
        if hasattr(self, 'label_price'):
            self.label_price.config(text=str(price))
        if hasattr(self, 'label_time'):
            formatted_time = f"{time_hms:06d}"
            self.label_time.config(text=f"{formatted_time[:2]}:{formatted_time[2:4]}:{formatted_time[4:6]}")
        
    except Exception as e:
        log_dangerous_operation(f"UI更新失敗: {e}", "safe_update_quote_display")
```

### 2. 修改 Quote.py

**在SKQuoteLibEvents類中添加監控：**
```python
@com_event_monitor
def OnNotifyQuoteLONG(self, sMarketNo, nStockidx):
    """報價事件 - 帶監控版本"""
    try:
        log_com_event("OnNotifyQuoteLONG", f"市場:{sMarketNo} 指數:{nStockidx}")
        
        # 原有的Queue處理邏輯
        pStock = sk.SKSTOCKLONG()
        m_nCode = skQ.SKQuoteLib_GetStockByIndexLONG(sMarketNo, nStockidx, pStock)
        
        quote_data = {
            'stock_no': pStock.bstrStockNo,
            'stock_name': pStock.bstrStockName,
            'close_price': pStock.nClose/math.pow(10,pStock.sDecimal),
            # ...
        }
        put_quote_message(quote_data)
        
    except Exception as e:
        log_dangerous_operation(f"報價事件異常: {e}", "OnNotifyQuoteLONG")
```

## 🔍 監控檢查清單

### 必須監控的位置

1. **所有COM事件處理函數**
   - `OnNotify*` 系列
   - `OnAsync*` 系列  
   - `OnConnection*` 系列
   - `OnReply*` 系列

2. **所有UI更新操作**
   - `widget.config()`
   - `widget.insert()`
   - `widget.delete()`
   - `widget["text"] = ...`

3. **關鍵的線程交互點**
   - 數據鎖操作
   - `after_idle` 調用
   - Queue操作

### 監控級別

**ERROR級別（會導致崩潰）：**
- COM事件中直接UI操作
- 背景線程中的tkinter操作
- COM事件拋出異常

**WARNING級別（可能有問題）：**
- 背景線程中的可疑操作
- 未預期的線程切換
- 長時間的COM事件處理

**DEBUG級別（正常記錄）：**
- 所有COM事件調用
- 所有UI操作
- 線程狀態變化

## 📊 監控報告查看

### 實時監控

```python
from gil_monitor import print_gil_report, get_gil_stats

# 顯示實時報告
print_gil_report()

# 獲取統計數據
stats = get_gil_stats()
print(f"不安全操作: {stats['unsafe_ui_operations']}")
print(f"警告數量: {stats['warnings_count']}")
```

### 日誌文件分析

監控日誌會自動保存到 `gil_monitor.log`，包含：

- 詳細的操作記錄
- 線程信息
- 堆棧追蹤
- 時間戳

**查看危險操作：**
```bash
grep "危險\|WARNING\|ERROR" gil_monitor.log
```

**查看COM事件：**
```bash
grep "COM事件" gil_monitor.log
```

## 🚨 緊急調試

當發生GIL錯誤時，立即檢查：

1. **最近的日誌記錄**
   ```bash
   tail -50 gil_monitor.log
   ```

2. **查找ERROR級別記錄**
   ```bash
   grep "ERROR\|❌\|🚨" gil_monitor.log
   ```

3. **檢查最後的COM事件**
   ```bash
   grep "COM事件" gil_monitor.log | tail -10
   ```

4. **查看線程警告**
   ```bash
   grep "背景線程\|危險操作" gil_monitor.log
   ```

## 🎯 最佳實踐

1. **開發階段全程啟用監控**
2. **定期檢查監控報告**
3. **重點關注ERROR和WARNING級別**
4. **在測試時故意觸發危險操作**
5. **發布前移除或降低監控級別**

---

**🔍 記住**: 監控工具是開發階段的調試助手，幫助您快速定位GIL錯誤的根源，確保程式穩定運行！
