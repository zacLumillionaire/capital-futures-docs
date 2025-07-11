# 報價接收機制分析報告

## 📡 **當前報價接收機制**

### **🔍 您的系統使用的是被動接收Full Tick模式**

根據代碼分析，您的系統運作方式：

```python
# simple_integrated.py 第1110行
result = Global.skQ.SKQuoteLib_RequestTicks(0, str(product))
```

### **📊 群益API報價機制說明**

#### **1. 訂閱方式 (一次性設定)**
```python
# 🔧 一次性訂閱設定
SKQuoteLib_RequestTicks(0, "MTX00")
# 參數說明:
# - 0 = 即時逐筆模式
# - "MTX00" = 商品代碼
```

#### **2. 接收方式 (被動回調)**
```python
# 🔔 系統自動回調，無法控制頻率
def OnNotifyTicksLONG(self, sMarketNo, nStockidx, nPtr, lDate, lTimehms, 
                     lTimemillismicros, nBid, nAsk, nClose, nQty, nSimulate):
    # 每筆成交都會自動觸發此函數
    # 無法在API層面控制接收頻率
```

## 🚨 **關鍵發現：無法在API層面控制頻率**

### **群益API的特性**
1. **Full Tick推送**: 每筆成交都會推送
2. **無頻率控制**: API不提供頻率限制功能
3. **被動接收**: 只能被動接收，無法主動拉取
4. **即時性**: 交易所有成交就立即推送

### **您看到的高頻報價是正常的**
```
[TICK] 09:17:25 成交:22470 買:22469 賣:22470 量:4
[TICK] 09:17:25 成交:22470 買:22469 賣:22470 量:4  
[TICK] 09:17:25 成交:22470 買:22469 賣:22470 量:4
[TICK] 09:17:25 成交:22470 買:22469 賣:22470 量:4
```
**這表示09:17:25這一秒內確實有4筆相同價格的成交**

## 🔧 **如何實現500ms頻率控制**

### **方法1：在OnNotifyTicksLONG內部控制** (推薦)

```python
class QuoteThrottler:
    def __init__(self, interval_ms=500):
        self.interval = interval_ms / 1000.0  # 轉換為秒
        self.last_process_time = 0
        self.pending_quote = None
    
    def should_process(self, quote_data):
        current_time = time.time()
        
        # 🔄 總是更新最新報價
        self.pending_quote = quote_data
        
        # 🕐 檢查是否到達處理時間
        if current_time - self.last_process_time >= self.interval:
            self.last_process_time = current_time
            return True, self.pending_quote
        
        return False, None

# 在OnNotifyTicksLONG中使用
def OnNotifyTicksLONG(self, sMarketNo, nStockidx, nPtr, lDate, lTimehms, 
                     lTimemillismicros, nBid, nAsk, nClose, nQty, nSimulate):
    quote_start_time = time.time()
    
    # 🔧 頻率控制
    quote_data = {
        'price': nClose / 100.0,
        'bid': nBid / 100.0,
        'ask': nAsk / 100.0,
        'time': lTimehms,
        'qty': nQty
    }
    
    should_process, data = self.quote_throttler.should_process(quote_data)
    
    if not should_process:
        return  # 🚀 跳過此次處理，等待下次間隔
    
    # 📊 處理最新的報價數據
    corrected_price = data['price']
    # ... 原有處理邏輯 ...
```

### **方法2：使用定時器模式**

```python
class TimerBasedQuoteProcessor:
    def __init__(self, interval_ms=500):
        self.interval = interval_ms / 1000.0
        self.latest_quote = None
        self.timer = None
        self.processing = False
    
    def update_quote(self, quote_data):
        # 🔄 總是更新最新報價
        self.latest_quote = quote_data
        
        # 🕐 如果沒有定時器在運行，啟動一個
        if self.timer is None and not self.processing:
            self.timer = threading.Timer(self.interval, self._process_latest_quote)
            self.timer.start()
    
    def _process_latest_quote(self):
        if self.latest_quote:
            self.processing = True
            try:
                # 📊 處理最新報價
                self._do_quote_processing(self.latest_quote)
            finally:
                self.processing = False
                self.timer = None

# 在OnNotifyTicksLONG中使用
def OnNotifyTicksLONG(self, ...):
    quote_data = {...}
    self.timer_processor.update_quote(quote_data)
    return  # 立即返回，不阻塞
```

### **方法3：批量處理模式**

```python
class BatchQuoteProcessor:
    def __init__(self, batch_interval=0.5):
        self.batch_interval = batch_interval
        self.quote_buffer = []
        self.last_batch_time = time.time()
    
    def add_quote(self, quote_data):
        self.quote_buffer.append(quote_data)
        
        current_time = time.time()
        if current_time - self.last_batch_time >= self.batch_interval:
            self._process_batch()
            self.last_batch_time = current_time
    
    def _process_batch(self):
        if not self.quote_buffer:
            return
        
        # 📊 只處理最新的報價
        latest_quote = self.quote_buffer[-1]
        self.quote_buffer.clear()
        
        # 處理邏輯...
```

## 📊 **三種方法比較**

| 方法 | 優點 | 缺點 | 推薦度 |
|------|------|------|--------|
| **內部控制** | 簡單、可靠、同步 | 仍會接收所有報價 | ⭐⭐⭐⭐⭐ |
| **定時器模式** | 完全異步、不阻塞 | 複雜度較高 | ⭐⭐⭐⭐ |
| **批量處理** | 高效、可統計 | 邏輯較複雜 | ⭐⭐⭐ |

## 🎯 **推薦實施方案**

### **立即實施：方法1 (內部控制)**

```python
# 🔧 在simple_integrated.py中添加
class SimpleQuoteThrottler:
    def __init__(self):
        self.last_process_time = 0
        self.interval = 0.5  # 500ms
    
    def should_process(self):
        current_time = time.time()
        if current_time - self.last_process_time >= self.interval:
            self.last_process_time = current_time
            return True
        return False

# 在OnNotifyTicksLONG開頭添加
def OnNotifyTicksLONG(self, ...):
    # 🚀 500ms頻率控制
    if not hasattr(self, 'quote_throttler'):
        self.quote_throttler = SimpleQuoteThrottler()
    
    if not self.quote_throttler.should_process():
        return  # 跳過此次處理
    
    # 原有處理邏輯...
    quote_start_time = time.time()
    # ...
```

## 📝 **總結**

### **您的系統特性**
1. **被動接收Full Tick**: 無法在API層面控制
2. **高頻是正常的**: 反映真實的市場成交
3. **必須在應用層控制**: 在OnNotifyTicksLONG內部實現頻率控制

### **500ms控制的實現**
- **不是減少接收**: 仍會接收所有報價
- **是減少處理**: 只處理間隔內的最新報價
- **保持即時性**: 總是使用最新的價格數據

**建議立即實施方法1的內部控制，這是最簡單有效的解決方案。** 🚀

您希望我提供具體的代碼修改嗎？


