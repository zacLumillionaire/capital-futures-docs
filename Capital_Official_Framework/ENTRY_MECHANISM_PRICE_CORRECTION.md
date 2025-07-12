# 🔧 進場機制價格選擇邏輯修正記錄

**文件編號**: ENTRY_MECHANISM_PRICE_CORRECTION  
**修正日期**: 2025-07-05  
**修正原因**: 發現空單進場機制價格選擇錯誤  
**修正狀態**: 已完成 ✅  

---

## 🚨 **發現的問題**

### **原始進場機制問題**：
在比對進場與出場機制時，發現進場機制存在**重大問題**：

- **多單進場**：使用ASK1價格 ✅ (正確)
- **空單進場**：使用ASK1價格 ❌ (錯誤，應該用BID1)
- **多單追價**：ASK1 + retry_count點 ✅ (正確)  
- **空單追價**：ASK1 + retry_count點 ❌ (錯誤，應該BID1 - retry_count點)

### **問題影響**：
1. **空單進場困難**：使用ASK1價格會比市價高，成交困難
2. **空單追價錯誤**：向上追價會越追越貴，更難成交
3. **實單測試誤導**：如果只測試多單，不會發現空單問題

---

## ✅ **修正內容**

### **1. 修正 execute_strategy_order() 價格選擇**

**文件**: `Capital_Official_Framework/virtual_real_order_manager.py`

**修正前**：
```python
# 3. 取得ASK1價格
if not price:
    price = self.get_ask1_price(product)  # ❌ 統一使用ASK1
    if not price:
        return OrderResult(False, self.get_current_mode(),
                         error=f"無法取得{product}的ASK1價格")
```

**修正後**：
```python
# 3. 根據方向取得正確價格
if not price:
    if direction == 'BUY':  # 多單進場
        price = self.get_ask1_price(product)
        price_type = "ASK1"
    elif direction == 'SELL':  # 空單進場
        price = self.get_bid1_price(product)
        price_type = "BID1"
    else:
        return OrderResult(False, self.get_current_mode(),
                         error=f"無效的方向: {direction}")
    
    if not price:
        return OrderResult(False, self.get_current_mode(),
                         error=f"無法取得{product}的{price_type}價格")
    
    if self.console_enabled:
        print(f"[ENTRY_PRICE] {direction}進場使用{price_type}: {price}")
```

### **2. 修正 calculate_retry_price() 追價邏輯**

**文件**: `Capital_Official_Framework/multi_group_position_manager.py`

**修正前**：
```python
def calculate_retry_price(self, position_info: Dict, retry_count: int) -> Optional[float]:
    """計算追價價格（當前ASK1 + retry_count點）"""  # ❌ 統一ASK1
    
    # 方法1：嘗試從下單管理器取得
    if self.order_manager and hasattr(self.order_manager, 'get_ask1_price'):
        try:
            current_ask1 = self.order_manager.get_ask1_price(product)  # ❌ 統一ASK1
        except:
            pass
    
    # 計算追價：ASK1 + retry_count點
    retry_price = current_ask1 + retry_count  # ❌ 統一向上追價
```

**修正後**：
```python
def calculate_retry_price(self, position_info: Dict, retry_count: int) -> Optional[float]:
    """計算進場追價價格 - 根據方向選擇正確價格"""
    
    position_direction = position_info.get('direction')
    
    if position_direction.upper() == "LONG":
        # 多單進場：使用ASK1 + retry_count點 (向上追價)
        current_ask1 = self.order_manager.get_ask1_price(product)
        if current_ask1:
            current_price = current_ask1 + retry_count
            self.logger.info(f"多單進場追價: ASK1({current_ask1}) + {retry_count}點 = {current_price}")
            
    elif position_direction.upper() == "SHORT":
        # 空單進場：使用BID1 - retry_count點 (向下追價)
        current_bid1 = self.order_manager.get_bid1_price(product)
        if current_bid1:
            current_price = current_bid1 - retry_count
            self.logger.info(f"空單進場追價: BID1({current_bid1}) - {retry_count}點 = {current_price}")
```

### **3. 修正追價記錄描述**

**修正前**：
```python
retry_reason = f"ASK1+{retry_count}點追價"  # ❌ 統一描述
```

**修正後**：
```python
position_direction = position_info.get('direction', 'UNKNOWN')
if position_direction.upper() == "LONG":
    retry_reason = f"多單進場ASK1+{retry_count}點追價"
elif position_direction.upper() == "SHORT":
    retry_reason = f"空單進場BID1-{retry_count}點追價"
else:
    retry_reason = f"進場追價第{retry_count}次"
```

---

## 🎯 **修正後的完整邏輯**

### **進場機制** ✅：
- **多單進場 (BUY)**：使用ASK1價格，向上追價
- **空單進場 (SELL)**：使用BID1價格，向下追價

### **出場機制** ✅：
- **多單出場 (SELL)**：使用BID1價格，向下追價
- **空單出場 (BUY)**：使用ASK1價格，向上追價

### **邏輯一致性** ✅：
```
進場：多單用ASK1(買進) → 空單用BID1(賣出)
出場：多單用BID1(賣出) → 空單用ASK1(買進)
追價：多單向上追價 → 空單向下追價
```

---

## 💡 **為什麼之前實單測試成功**

1. **測試範圍限制**：如果測試的都是**多單進場**，ASK1邏輯是正確的
2. **多單邏輯正確**：多單使用ASK1價格和向上追價都是正確的
3. **問題隱藏**：空單的問題只有在實際空單交易時才會暴露

---

## 📋 **測試建議**

### **建議測試項目**：
1. **多單進場測試**：確認ASK1價格選擇和向上追價
2. **空單進場測試**：確認BID1價格選擇和向下追價  
3. **多單出場測試**：確認BID1價格選擇和向下追價
4. **空單出場測試**：確認ASK1價格選擇和向上追價

### **Console監控輸出**：
```
[ENTRY_PRICE] BUY進場使用ASK1: 22485
[ENTRY_PRICE] SELL進場使用BID1: 22483
多單進場追價: ASK1(22485) + 1點 = 22486
空單進場追價: BID1(22483) - 1點 = 22482
```

---

**🎉 進場機制價格選擇邏輯修正完成！**  
**📞 現在多單和空單的進場、出場、追價邏輯都已正確實現！**
