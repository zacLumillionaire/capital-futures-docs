# 🔧 訂單匹配FIFO機制重新設計方案

## 📊 **問題分析**

### **🔴 當前問題現象**
```
下單記錄: API序號 ['3748', '6632']
回報序號: KeyNo=2315544965069, SeqNo=2315544965069
結果: ⚠️ 序號都不在追蹤列表中 → 找不到匹配
```

### **🔍 根本原因分析**

#### **1. 序號系統不匹配**
- **API返回序號**: `3748`, `6632` (短序號)
- **回報序號**: `2315544965069`, `2315544965070` (長序號)
- **問題**: 這是兩個完全不同的編號系統！

#### **2. 現有匹配邏輯仍依賴序號**
雖然我們說要改用FIFO，但實際上：
```python
# ORDER_TRACKER 仍在用序號匹配
[ORDER_TRACKER] 🔍 已追蹤序號: ['3748', '6632']
[ORDER_TRACKER] ⚠️ 序號KeyNo=2315544965069都不在追蹤列表中
```

#### **3. 多層追蹤器混亂**
- `ORDER_TRACKER` (統一追蹤器)
- `TOTAL_MANAGER` (總量追蹤器)  
- `SIMPLIFIED_TRACKER` (簡化追蹤器)

每個都有自己的匹配邏輯，造成混亂。

---

## 🎯 **解決方案：純FIFO匹配機制**

### **核心理念**
**完全放棄序號匹配，改用時間+價格+商品+數量的FIFO匹配**

### **設計原則**
1. **先進先出**: 時間優先：最早下單的訂單優先匹配同時使用下單點數跟回報點數比對 


---

## 🔧 **修改計畫**

### **階段1: 統一追蹤器改造**

#### **目標文件**: `unified_order_tracker.py`

**修改前**:
```python
# ❌ 依賴序號匹配
def process_real_order_reply(self, reply_data: str):
    key_no = fields[0]
    seq_no = fields[47]
    primary_id = key_no if key_no else seq_no
    
    # 查找追蹤的訂單
    for order_id, order_info in self.tracked_orders.items():
        if order_info.api_sequence == primary_id:  # 序號匹配
            # 處理回報
```

**修改後**:
```python
# ✅ FIFO匹配
def process_real_order_reply(self, reply_data: str):
    # 解析回報
    order_type = fields[2]
    price = float(fields[11])
    qty = int(fields[20])
    product = fields[8]
    
    # FIFO匹配
    matched_order = self._find_fifo_match(price, qty, product, order_type)
    if matched_order:
        # 處理回報
```

#### **新增FIFO匹配方法**:
```python
def _find_fifo_match(self, price: float, qty: int, product: str, order_type: str):
    """純FIFO匹配邏輯"""
    current_time = time.time()
    candidates = []
    
    # 標準化商品代碼
    normalized_product = self._normalize_product(product)
    
    for order_id, order_info in self.tracked_orders.items():
        if (order_info.status == OrderStatus.PENDING and
            self._normalize_product(order_info.product) == normalized_product and
            order_info.quantity == qty and
            current_time - order_info.submit_time <= 30):  # 30秒窗口
            
            # 價格匹配 (±5點容差)
            if abs(price - order_info.price) <= 5:
                candidates.append((order_info, order_info.submit_time))
    
    # FIFO: 返回最早的訂單
    if candidates:
        return min(candidates, key=lambda x: x[1])[0]
    return None
```

### **階段2: 簡化追蹤器改造**

#### **目標文件**: `simplified_order_tracker.py`

**關鍵修改**:
```python
def process_order_reply(self, reply_data: str) -> bool:
    """處理訂單回報 - 純FIFO版本"""
    fields = reply_data.split(',')
    
    order_type = fields[2]
    price = float(fields[11]) if fields[11] else 0
    qty = int(fields[20]) if fields[20] else 0
    product = fields[8]
    
    if order_type == "D":  # 成交
        return self._handle_fill_fifo(price, qty, product)
    elif order_type == "C":  # 取消
        return self._handle_cancel_fifo(price, qty, product)

def _handle_fill_fifo(self, price: float, qty: int, product: str):
    """FIFO成交處理"""
    # 找到最早的未完成策略組
    group = self._find_earliest_pending_group(product)
    if group:
        group.filled_lots += qty
        # 觸發成交回調
        return True
    return False
```

### **階段3: 總量追蹤器改造**

#### **目標文件**: `total_lot_manager.py`

**移除方向依賴**:
```python
def _find_matching_tracker(self, price: float, qty: int, product: str):
    """純FIFO匹配 - 不依賴方向"""
    current_time = time.time()
    normalized_product = self._normalize_product(product)
    
    candidates = []
    for tracker in self.active_trackers.values():
        if (self._normalize_product(tracker.product) == normalized_product and
            not tracker.is_complete() and
            current_time - tracker.start_time <= 30):
            candidates.append((tracker, tracker.start_time))
    
    # 返回最早的追蹤器
    if candidates:
        return min(candidates, key=lambda x: x[1])[0]
    return None
```

---

## 🎯 **實施步驟**

### **Step 1: 修改統一追蹤器**
1. 移除所有序號匹配邏輯
2. 實現純FIFO匹配方法
3. 添加商品代碼標準化

### **Step 2: 修改簡化追蹤器**
1. 重寫 `process_order_reply()` 方法
2. 實現基於時間的FIFO匹配
3. 移除方向檢測依賴

### **Step 3: 修改總量追蹤器**
1. 簡化匹配邏輯
2. 移除方向判斷
3. 純粹基於時間順序

### **Step 4: 測試驗證**
1. 測試成交匹配
2. 測試取消匹配
3. 測試追價觸發

---

## 📋 **預期效果**

### **修改前**:
```
❌ [ORDER_TRACKER] ⚠️ 序號KeyNo=2315544965069都不在追蹤列表中
❌ [TOTAL_MANAGER] ⚠️ 找不到匹配的追蹤器
❌ [SIMPLIFIED_TRACKER] ⚠️ 找不到匹配的策略組
```

### **修改後**:
```
✅ [ORDER_TRACKER] 🎯 FIFO匹配成功: 價格22334, 商品TM2507 → TM0000
✅ [TOTAL_MANAGER] 📊 匹配追蹤器: strategy_4_1751855447
✅ [SIMPLIFIED_TRACKER] 🎉 策略組4成交: 1口 @22334
```

---

## 🚀 **關鍵優勢**

### **1. 簡化邏輯**
- 不再依賴複雜的序號對應
- 純粹基於業務邏輯匹配

### **2. 提高可靠性**
- 避免序號系統差異問題
- FIFO原則符合期貨交易特性

### **3. 易於維護**
- 邏輯清晰，容易調試
- 減少多層追蹤器的複雜性

### **4. 容錯性強**
- 允許價格滑價
- 時間窗口保護

---

## ⚠️ **注意事項**

### **1. 時間同步**
確保所有追蹤器使用相同的時間基準

### **2. 價格精度**
注意浮點數比較的精度問題

### **3. 商品映射**
確保TM0000與TM2507的映射正確

### **4. 併發安全**
多線程環境下的數據一致性

---

## 🎯 **下一步行動**

1. **先修改統一追蹤器** - 這是核心組件
2. **測試基本匹配** - 確保FIFO邏輯正確
3. **逐步修改其他追蹤器** - 保持系統穩定
4. **全面測試** - 驗證所有場景

這個方案將徹底解決序號匹配問題，實現真正的FIFO訂單追蹤機制。

---

## 💻 **具體代碼實現**

### **核心FIFO匹配邏輯**

```python
class FIFOOrderMatcher:
    """純FIFO訂單匹配器"""

    def __init__(self):
        self.pending_orders = []  # [(submit_time, order_info), ...]

    def add_pending_order(self, order_info):
        """添加待匹配訂單"""
        submit_time = time.time()
        self.pending_orders.append((submit_time, order_info))
        # 按時間排序，確保FIFO
        self.pending_orders.sort(key=lambda x: x[0])

    def find_match(self, price: float, qty: int, product: str) -> Optional[OrderInfo]:
        """FIFO匹配邏輯"""
        current_time = time.time()
        normalized_product = self._normalize_product(product)

        for i, (submit_time, order_info) in enumerate(self.pending_orders):
            # 檢查時間窗口 (30秒)
            if current_time - submit_time > 30:
                continue

            # 檢查商品匹配
            if self._normalize_product(order_info.product) != normalized_product:
                continue

            # 檢查數量匹配
            if order_info.quantity != qty:
                continue

            # 檢查價格匹配 (±5點容差)
            if abs(order_info.price - price) <= 5:
                # 找到匹配，移除並返回
                matched_order = self.pending_orders.pop(i)[1]
                return matched_order

        return None

    def _normalize_product(self, product: str) -> str:
        """標準化商品代碼"""
        if product.startswith("TM") and len(product) == 6:
            return "TM0000"
        elif product.startswith("MTX") and len(product) == 5:
            return "MTX00"
        return product
```

### **統一追蹤器修改示例**

```python
# unified_order_tracker.py 修改
class UnifiedOrderTracker:
    def __init__(self):
        self.fifo_matcher = FIFOOrderMatcher()
        # 移除 self.tracked_orders = {} (序號追蹤)

    def register_order(self, order_info: OrderInfo):
        """註冊訂單到FIFO匹配器"""
        self.fifo_matcher.add_pending_order(order_info)
        print(f"[FIFO] 📝 註冊訂單: {order_info.product} {order_info.quantity}口 @{order_info.price}")

    def process_real_order_reply(self, reply_data: str):
        """處理回報 - FIFO版本"""
        try:
            fields = reply_data.split(',')

            order_type = fields[2]
            price = float(fields[11]) if fields[11] else 0
            qty = int(fields[20]) if fields[20] else 0
            product = fields[8]

            if order_type == "D":  # 成交
                matched_order = self.fifo_matcher.find_match(price, qty, product)
                if matched_order:
                    self._process_fill_reply(matched_order, price, qty)
                    print(f"[FIFO] ✅ 成交匹配: {product} {qty}口 @{price}")
                else:
                    print(f"[FIFO] ⚠️ 找不到匹配: {product} {qty}口 @{price}")

            elif order_type == "C":  # 取消
                matched_order = self.fifo_matcher.find_match(price, qty, product)
                if matched_order:
                    self._process_cancel_reply(matched_order)
                    print(f"[FIFO] 🗑️ 取消匹配: {product} {qty}口 @{price}")
                else:
                    print(f"[FIFO] ⚠️ 找不到取消匹配: {product} {qty}口 @{price}")

        except Exception as e:
            print(f"[FIFO] ❌ 處理回報失敗: {e}")
```

---

## 🔄 **追價機制整合**

### **FIFO追價邏輯**

```python
def _process_cancel_reply(self, matched_order: OrderInfo):
    """處理取消回報 - 觸發追價"""
    try:
        # 標記訂單取消
        matched_order.status = OrderStatus.CANCELLED

        # 觸發取消回調 (包含追價邏輯)
        for callback in self.cancel_callbacks:
            callback(matched_order)

        print(f"[FIFO] 🔄 訂單取消，觸發追價: {matched_order.order_id}")

    except Exception as e:
        print(f"[FIFO] ❌ 處理取消失敗: {e}")
```

### **追價價格計算**

```python
def calculate_retry_price(self, original_order: OrderInfo, retry_count: int) -> float:
    """計算追價價格 - FIFO版本"""
    try:
        if original_order.direction == "LONG":
            # 多單: ASK1 + retry_count
            ask1 = self.get_ask1_price(original_order.product)
            return ask1 + retry_count if ask1 else original_order.price + retry_count

        elif original_order.direction == "SHORT":
            # 空單: BID1 - retry_count
            bid1 = self.get_bid1_price(original_order.product)
            return bid1 - retry_count if bid1 else original_order.price - retry_count

    except Exception as e:
        print(f"[FIFO] ❌ 計算追價失敗: {e}")
        return original_order.price
```

---

## 📊 **測試驗證方案**

### **測試場景1: 正常成交**

```python
def test_normal_fill():
    """測試正常成交匹配"""
    matcher = FIFOOrderMatcher()

    # 1. 添加待匹配訂單
    order = OrderInfo(
        product="TM0000",
        price=22334,
        quantity=1,
        direction="SHORT"
    )
    matcher.add_pending_order(order)

    # 2. 模擬成交回報
    matched = matcher.find_match(
        price=22334,  # 原價成交
        qty=1,
        product="TM2507"  # 回報中的商品代碼
    )

    assert matched is not None
    assert matched.product == "TM0000"
    print("✅ 正常成交測試通過")
```

### **測試場景2: 滑價成交**

```python
def test_slippage_fill():
    """測試滑價成交匹配"""
    matcher = FIFOOrderMatcher()

    # 1. 添加訂單 @22334
    order = OrderInfo(product="TM0000", price=22334, quantity=1)
    matcher.add_pending_order(order)

    # 2. 模擬滑價成交 @22337 (+3點)
    matched = matcher.find_match(price=22337, qty=1, product="TM2507")

    assert matched is not None  # 應該匹配成功
    print("✅ 滑價成交測試通過")
```

### **測試場景3: FIFO順序**

```python
def test_fifo_order():
    """測試FIFO順序正確性"""
    matcher = FIFOOrderMatcher()

    # 1. 按順序添加3個訂單
    order1 = OrderInfo(product="TM0000", price=22334, quantity=1, order_id="first")
    order2 = OrderInfo(product="TM0000", price=22335, quantity=1, order_id="second")
    order3 = OrderInfo(product="TM0000", price=22336, quantity=1, order_id="third")

    matcher.add_pending_order(order1)
    time.sleep(0.1)  # 確保時間差
    matcher.add_pending_order(order2)
    time.sleep(0.1)
    matcher.add_pending_order(order3)

    # 2. 匹配應該返回最早的訂單
    matched = matcher.find_match(price=22334, qty=1, product="TM2507")

    assert matched.order_id == "first"
    print("✅ FIFO順序測試通過")
```

---

## 🎯 **實施優先級**

### **Phase 1: 核心修改 (高優先級)**
1. ✅ 修改 `unified_order_tracker.py`
2. ✅ 實現 `FIFOOrderMatcher` 類
3. ✅ 測試基本匹配功能

### **Phase 2: 追蹤器整合 (中優先級)**
1. ✅ 修改 `simplified_order_tracker.py`
2. ✅ 修改 `total_lot_manager.py`
3. ✅ 統一FIFO邏輯

### **Phase 3: 追價機制 (中優先級)**
1. ✅ 整合追價觸發
2. ✅ 測試追價流程
3. ✅ 驗證價格計算

### **Phase 4: 全面測試 (高優先級)**
1. ✅ 單元測試
2. ✅ 整合測試
3. ✅ 實盤驗證

這個重新設計將徹底解決序號匹配問題，實現真正可靠的FIFO訂單追蹤機制！
