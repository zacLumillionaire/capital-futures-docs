# 📊 出場機制價格選擇邏輯與追價機制開發計劃

**文件編號**: EXIT_MECHANISM_PRICE_AND_RETRY_DEVELOPMENT_PLAN  
**創建日期**: 2025-07-05  
**開發目標**: 完善出場機制的價格選擇邏輯和追價機制  
**預計完成**: 6個工作天  

---

## 🚨 **問題發現與分析**

### **當前系統狀況評估**

#### **✅ 已正確實現的功能**：
1. **出場方向轉換**：LONG→SELL, SHORT→BUY ✅
2. **出場委託設定**：FOK + 平倉 (new_close=1) ✅
3. **回報確認機制**：完整的OnNewData事件處理 ✅

#### **❌ 發現的關鍵問題**：

**1. 價格選擇邏輯問題**
- **進場邏輯**：只實現了 `get_best_ask_price()` 方法 ✅
- **出場邏輯**：**完全缺少** `get_best_bid_price()` 方法 ❌
- **價格選擇錯誤**：出場時可能錯誤使用ASK1價格 ❌

**2. 出場追價機制問題**
- **進場追價**：完整實現，包含ASK1+retry_count點邏輯 ✅
- **出場追價**：**完全缺失**，沒有任何出場追價機制 ❌

**3. 正確的出場價格邏輯應該是**：
- **多單出場 (SELL)**：應使用 BID1 價格 - 立即賣給買方
- **空單出場 (BUY)**：應使用 ASK1 價格 - 立即買回

---

## 🎯 **開發需求規格**

### **需求1: 實現BID1價格取得功能**

**開發目標**：為出場機制提供正確的BID1價格取得功能

**涉及文件**：
- `Capital_Official_Framework/real_time_quote_manager.py`
- `Capital_Official_Framework/virtual_real_order_manager.py`

**核心方法**：
```python
def get_best_bid_price(self, product_code: str) -> Optional[float]:
    """取得最佳買價 - 多單出場使用"""

def get_bid1_price(self, product: str) -> Optional[float]:
    """取得BID1價格 - 多單出場使用"""
```

### **需求2: 實現出場價格選擇邏輯**

**開發目標**：根據部位方向選擇正確的出場價格

**核心方法**：
```python
def get_exit_price(self, position_direction: str, product: str) -> Optional[float]:
    """取得出場價格 - 根據部位方向選擇BID1或ASK1"""

def execute_exit_order(self, position_direction: str, ...) -> OrderResult:
    """執行出場下單 - 新增方法"""
```

### **需求3: 實現出場追價機制**

**開發目標**：為出場FOK失敗提供追價重試機制

**涉及文件**：
- `Capital_Official_Framework/multi_group_position_manager.py`

**核心方法**：
```python
def calculate_exit_retry_price(self, position_info: Dict, retry_count: int) -> Optional[float]:
    """計算出場追價價格"""

def execute_exit_retry(self, position_id: int) -> bool:
    """執行出場追價"""
```

### **需求4: 整合出場追價到回報處理**

**開發目標**：在出場FOK取消時自動觸發追價機制

**核心方法**：
```python
def process_exit_order_reply(self, reply_data: str):
    """處理出場訂單回報"""

def _schedule_exit_retry(self, position_id: int):
    """排程出場追價"""
```

---

## 📋 **開發實施計劃**

### **階段1: BID1價格取得功能 (1天)** 🎯
- [ ] 在 `real_time_quote_manager.py` 中實現 `get_best_bid_price()`
- [ ] 在 `virtual_real_order_manager.py` 中實現 `get_bid1_price()`
- [ ] 測試BID1價格取得功能

### **階段2: 出場價格選擇邏輯 (1天)** 🎯
- [ ] 實現 `get_exit_price()` 方法
- [ ] 實現 `execute_exit_order()` 方法
- [ ] 整合到現有出場機制
- [ ] 測試多單用BID1、空單用ASK1邏輯

### **階段3: 出場追價機制 (2天)** 🎯
- [ ] 實現 `calculate_exit_retry_price()` 方法
- [ ] 實現 `execute_exit_retry()` 方法
- [ ] 實現 `_execute_exit_retry_order()` 方法
- [ ] 測試出場追價邏輯

### **階段4: 回報整合與測試 (1天)** 🎯
- [ ] 整合出場追價到回報處理
- [ ] 實現 `process_exit_order_reply()` 方法
- [ ] 端到端測試完整出場流程
- [ ] 驗證追價成功率

### **階段5: 文檔與優化 (1天)** 🎯
- [ ] 更新技術文檔
- [ ] 性能優化
- [ ] 錯誤處理完善
- [ ] 使用指南編寫

---

## 🎯 **預期成果**

### **功能完整性**：
- ✅ 多單出場使用BID1價格
- ✅ 空單出場使用ASK1價格  
- ✅ 出場FOK失敗自動追價
- ✅ 最多5次追價重試
- ✅ 滑價限制保護

### **性能指標**：
- 🎯 出場成功率：從當前的未知提升到85%+
- 🎯 追價延遲：2秒內觸發
- 🎯 價格精確性：即時BID1/ASK1價格

### **風險控制**：
- 🛡️ 最大滑價限制：5點
- 🛡️ 重試次數限制：5次
- 🛡️ 時間窗口控制：30秒內有效

---

## 📝 **開發進度追蹤**

### **階段1進度** (BID1價格取得功能)
- [x] **開始時間**: 2025-07-05
- [x] **完成時間**: 2025-07-05
- [x] **狀態**: 已完成
- [x] **備註**: 已實現 get_best_bid_price() 和 get_bid1_price() 方法

### **階段2進度** (出場價格選擇邏輯)
- [x] **開始時間**: 2025-07-05
- [x] **完成時間**: 2025-07-05
- [x] **狀態**: 已完成
- [x] **備註**: 已實現 get_exit_price() 和 execute_exit_order() 方法

### **階段3進度** (出場追價機制)
- [x] **開始時間**: 2025-07-05
- [x] **完成時間**: 2025-07-05
- [x] **狀態**: 已完成
- [x] **備註**: 已實現 calculate_exit_retry_price() 和 execute_exit_retry() 方法

### **階段4進度** (回報整合與測試)
- [x] **開始時間**: 2025-07-05
- [x] **完成時間**: 2025-07-05
- [x] **狀態**: 已完成
- [x] **備註**: 已整合出場追價到OnNewData回報處理

### **階段5進度** (文檔與優化)
- [x] **開始時間**: 2025-07-05
- [x] **完成時間**: 2025-07-05
- [x] **狀態**: 已完成
- [x] **備註**: 已完成技術文檔、使用指南和功能總結

---

## 🎉 **開發完成總結**

### **✅ 已實現的功能**

#### **1. BID1價格取得功能** ✅
- **文件**: `real_time_quote_manager.py`
  - 新增 `get_best_bid_price()` 方法
  - 支援數據新鮮度檢查
  - 完整的錯誤處理

- **文件**: `virtual_real_order_manager.py`
  - 新增 `get_bid1_price()` 方法
  - 整合報價管理器
  - Console日誌輸出

#### **2. 出場價格選擇邏輯** ✅
- **文件**: `virtual_real_order_manager.py`
  - 新增 `get_exit_price()` 方法
    - 多單出場 → 使用BID1價格
    - 空單出場 → 使用ASK1價格
  - 新增 `execute_exit_order()` 方法
    - 自動方向轉換 (LONG→SELL, SHORT→BUY)
    - FOK委託類型
    - 平倉設定 (new_close=1)
    - 完整的統計追蹤

#### **3. 出場追價機制** ✅
- **文件**: `multi_group_position_manager.py`
  - 新增 `calculate_exit_retry_price()` 方法
    - 多單出場：BID1 - retry_count點
    - 空單出場：ASK1 + retry_count點
    - 備用價格估算機制
  - 新增 `execute_exit_retry()` 方法
    - 重試次數限制檢查
    - 滑價限制保護 (5點)
    - 完整的資料庫更新
  - 新增 `_execute_exit_retry_order()` 方法
    - 整合訂單追蹤器
    - 部位訂單映射更新

#### **4. 回報整合機制** ✅
- **文件**: `simple_integrated.py`
  - 修改 `OnNewData()` 方法
    - 新增出場追價觸發邏輯
  - 新增 `process_exit_order_reply()` 方法
    - 識別出場訂單取消
    - 自動觸發追價機制
  - 新增 `_find_position_by_seq_no()` 方法
    - 委託序號與部位ID映射
  - 新增 `_schedule_exit_retry()` 方法
    - 延遲2秒執行追價
    - 多線程安全處理

### **🎯 功能特色**

#### **智能價格選擇**
```python
# 多單出場 - 使用BID1立即賣出
if position_direction == "LONG":
    exit_price = get_bid1_price(product)  # 賣給買方

# 空單出場 - 使用ASK1立即買回
if position_direction == "SHORT":
    exit_price = get_ask1_price(product)  # 從賣方買回
```

#### **動態追價機制**
```python
# 多單出場追價：更積極賣出
retry_price = current_bid1 - retry_count

# 空單出場追價：更積極買回
retry_price = current_ask1 + retry_count
```

#### **完整風險控制**
- ✅ 最大重試次數：5次
- ✅ 滑價限制：5點
- ✅ 時間窗口：30秒內有效
- ✅ FOK委託：避免部分成交

---

## � **使用指南**

### **1. 基本出場下單**
```python
# 多單出場
result = order_manager.execute_exit_order(
    position_direction="LONG",
    signal_source="stop_loss"
)

# 空單出場
result = order_manager.execute_exit_order(
    position_direction="SHORT",
    signal_source="trailing_stop"
)
```

### **2. 手動觸發出場追價**
```python
# 執行出場追價
success = position_manager.execute_exit_retry(position_id=123)
```

### **3. 價格查詢**
```python
# 查詢BID1價格 (多單出場用)
bid1 = order_manager.get_bid1_price("TM0000")

# 查詢ASK1價格 (空單出場用)
ask1 = order_manager.get_ask1_price("TM0000")

# 自動選擇出場價格
exit_price = order_manager.get_exit_price("LONG", "TM0000")  # 返回BID1
```

### **4. 監控Console輸出**
```
[EXIT_PRICE] 多單出場使用BID1: 22485
[EXIT_ORDER] 🔚 LONG出場實單下單成功 - TM0000 1口 @22485 (BID1)
[EXIT_RETRY] 📋 出場FOK取消，已排程追價: 部位123
[EXIT_RETRY] ⏰ 已排程部位123的延遲出場追價（2秒後執行）
多單出場追價: BID1(22485) - 1點 = 22484
✅ 部位123出場第1次追價成功: @22484
```

---

## 🔧 **技術細節**

### **價格選擇邏輯**
- **多單出場 (SELL)**：使用BID1價格，立即賣給市場買方
- **空單出場 (BUY)**：使用ASK1價格，立即從市場賣方買回
- **追價策略**：多單向下追價，空單向上追價，確保成交

### **追價觸發條件**
1. 出場訂單使用FOK委託
2. 收到取消回報 (order_type='C')
3. 部位狀態為'EXITING'
4. 重試次數未達上限
5. 滑價未超出限制

### **安全機制**
- 延遲2秒執行追價，避免過於頻繁
- 多線程處理，不阻塞主程序
- 完整的異常處理和日誌記錄
- 資料庫狀態同步更新

---

## 🎯 **預期效果**

### **出場成功率提升**
- **原本**：FOK失敗後無追價，成功率未知
- **現在**：自動追價機制，預期成功率85%+

### **價格執行精確度**
- **原本**：可能使用錯誤價格 (ASK1)
- **現在**：正確使用BID1/ASK1，立即成交

### **風險控制完善**
- **原本**：無滑價保護
- **現在**：5點滑價限制，5次重試上限

---

**🎉 出場機制價格選擇邏輯與追價機制開發完成！**
**�📞 如需進一步測試或調整，請隨時告知！**
