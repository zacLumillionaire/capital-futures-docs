# 📋 改進版追價機制說明

## 🕐 **時間窗口機制**

### **時間窗口 = 5分鐘 (300秒)**
```python
# 只匹配5分鐘內創建的策略組
if current_time - group.submit_time <= 300:
    return group
```

**作用**:
- **防止歷史匹配**: 避免把舊的回報歸屬到新的策略組
- **自動過期**: 超過5分鐘的組不再接受新的回報匹配
- **避免混淆**: 確保回報只匹配到當前活躍的策略組

### **匹配條件組合**
1. **方向匹配**: LONG/SHORT
2. **商品匹配**: TM0000/MTX00
3. **價格容差**: ±5點範圍內
4. **時間窗口**: 5分鐘內
5. **組狀態**: 未完成

---

## 🔄 **改進版追價機制**

### **追價觸發條件**
```python
def needs_retry(self) -> bool:
    remaining_lots = self.total_lots - self.filled_lots
    return (remaining_lots > 0 and                    # 還有未成交口數
            self.retry_count < self.max_retries and   # 未達最大重試次數(5次)
            self.submitted_lots <= self.total_lots)   # 防止超量下單
```

### **精確追價控制**
```python
# 計算需要追價的口數
remaining_lots = group.total_lots - group.filled_lots
retry_lots = min(qty, remaining_lots)  # 不超過剩餘需求

if retry_lots > 0:
    group.is_retrying = True  # 標記為追價中
    group.pending_retry_lots = retry_lots
```

---

## 🚨 **多下單風險控制**

### **問題場景分析**
```
策略組: 3口目標
第1次: 3口FOK @22344 → 全部取消(C) → 觸發追價
第2次: 3口FOK @22345 → 1口成交(D), 2口取消(C) → 再次觸發追價?
第3次: 應該只下2口，不是3口
```

### **風險控制機制**

#### **1. 狀態鎖定機制**
```python
if group.needs_retry() and not group.is_retrying:
    group.is_retrying = True  # 防止重複觸發
```

#### **2. 精確口數計算**
```python
remaining_lots = group.total_lots - group.filled_lots
retry_lots = min(qty, remaining_lots)  # 只追價實際需要的口數
```

#### **3. 送出口數限制**
```python
self.submitted_lots <= self.total_lots  # 防止超量下單
```

#### **4. 狀態重置機制**
```python
# 新下單送出時重置追價狀態
if group.is_retrying:
    group.is_retrying = False
    group.pending_retry_lots = 0
```

---

## 📊 **追價流程示例**

### **正常追價流程**
```
1. 策略組註冊: 3口 @22344
2. 初始下單: 3口FOK @22344
3. 收到取消: 3口取消 → 觸發追價(第1次)
4. 追價下單: 3口FOK @22345
5. 收到成交: 1口成交, 2口取消 → 觸發追價(第2次)
6. 追價下單: 2口FOK @22346 (只下剩餘口數)
7. 收到成交: 2口成交 → 組完成
```

### **防止多下單的控制點**
```
✅ 第6步: 只下2口，不是3口 (remaining_lots控制)
✅ 狀態鎖定: 追價期間不重複觸發
✅ 口數限制: submitted_lots <= total_lots
✅ 時間控制: 至少間隔1秒
```

---

## ⚙️ **配置參數**

### **時間控制**
- **時間窗口**: 5分鐘 (300秒)
- **重試間隔**: 1秒
- **清理週期**: 1小時

### **追價控制**
- **最大重試**: 5次
- **價格容差**: ±5點
- **追價步長**: +1點 (多頭), -1點 (空頭)

### **風險控制**
- **超量保護**: submitted_lots <= total_lots
- **狀態鎖定**: is_retrying 標記
- **精確計算**: min(cancelled_qty, remaining_lots)

---

## 🎯 **預期效果**

### **解決的問題**
1. **✅ 序號不匹配**: 改用統計匹配
2. **✅ 成交無法識別**: 基於價格+方向+時間窗口
3. **✅ 追價機制失效**: 基於取消統計觸發
4. **✅ 多下單風險**: 精確口數控制

### **追價邏輯**
- **觸發條件**: 收到C(取消)回報
- **追價次數**: 最多5次
- **追價口數**: 精確計算剩餘需求
- **防重複**: 狀態鎖定機制

### **安全保障**
- **不會超量**: submitted_lots <= total_lots
- **不會重複**: is_retrying 狀態控制
- **不會混淆**: 時間窗口限制
- **不會卡死**: 最大重試次數限制

---

## 📝 **使用建議**

1. **監控日誌**: 關注 `[SIMPLIFIED_TRACKER]` 標籤
2. **檢查統計**: 定期查看 `get_statistics()` 結果
3. **狀態確認**: 使用 `get_group_status()` 檢查組狀態
4. **參數調整**: 可根據實際情況調整時間窗口和重試次數

這個改進版本應該能有效防止多下單問題，同時保持追價機制的有效性！
