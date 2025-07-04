# 🔧 UNIQUE constraint failed 錯誤修復方案

## 📋 **問題描述**

**錯誤訊息**:
```
ERROR:multi_group_database:資料庫操作錯誤: UNIQUE constraint failed: strategy_groups.date, strategy_groups.group_id
ERROR:multi_group_database:創建策略組失敗: UNIQUE constraint failed: strategy_groups.date, strategy_groups.group_id
ERROR:multi_group_position_manager.MultiGroupPositionManager:創建進場信號失敗: UNIQUE constraint failed: strategy_groups.date, strategy_groups.group_id
❌ [STRATEGY] 創建策略組失敗
```

**發生時機**: 區間計算完成後，自動啟動多組策略時

## 🔍 **根本原因分析**

### **問題根源**
1. **重複觸發機制**: `update_range_calculation_safe()` 在每次報價處理時都會被調用
2. **狀態檢查時間差**: 在資料庫操作和狀態更新之間存在時間差
3. **缺乏防重複機制**: 沒有防止同一個區間計算觸發多次策略組創建

### **觸發流程**
```
報價處理 → update_range_calculation_safe() → check_auto_start_multi_group_strategy()
    ↓
start_multi_group_strategy() → create_entry_signal() → 資料庫創建策略組
    ↓
如果在狀態更新前再次觸發 → 重複創建 → UNIQUE constraint failed
```

### **資料庫約束**
```sql
CREATE TABLE strategy_groups (
    ...
    date TEXT NOT NULL,
    group_id INTEGER NOT NULL,
    ...
    UNIQUE(date, group_id)  -- 同一天不能有相同的group_id
);
```

## ✅ **修復方案**

### **雙重防護機制**

#### **1. 應用層防護** - 防止重複觸發
在 `simple_integrated.py` 中添加觸發標記：

```python
# 初始化時添加狀態變數
self._auto_start_triggered = False  # 防止重複觸發自動啟動

# 區間計算完成時檢查
if not self._auto_start_triggered:
    self.check_auto_start_multi_group_strategy()

# 自動啟動檢查時立即設定標記
def check_auto_start_multi_group_strategy(self):
    if (self.multi_group_prepared and
        self.multi_group_auto_start and
        not self.multi_group_running and
        self.range_calculated and
        not self._auto_start_triggered):  # 新增檢查
        
        # 立即設定觸發標記，防止重複調用
        self._auto_start_triggered = True
        
        # 執行啟動邏輯...
```

#### **2. 狀態檢查防護** - 防止重複啟動
在 `start_multi_group_strategy()` 中添加運行狀態檢查：

```python
def start_multi_group_strategy(self):
    # 檢查是否已經在運行中（防重複啟動）
    if self.multi_group_running:
        print("⚠️ [STRATEGY] 多組策略已在運行中")
        return
    
    # 執行創建邏輯...
```

#### **3. 狀態重置機制** - 確保下次正常運行
在停止策略時重置觸發標記：

```python
def stop_multi_group_strategy(self):
    # 重置狀態變數
    self.multi_group_running = False
    self.multi_group_prepared = False
    self._auto_start_triggered = False  # 重置觸發標記
```

## 🧪 **修復驗證**

### **測試結果**
```
🔧 重複創建策略組防護機制測試
================================================================================

🧪 測試1: 第一次創建策略組
✅ 第一次創建成功: 1 個策略組

🧪 測試2: 重複創建策略組（預期失敗）
✅ 重複創建觸發異常（預期結果）: UNIQUE constraint failed

📊 檢查資料庫狀態:
✅ 防護機制有效：只創建了1個策略組

🧪 測試simple_integrated.py防護機制
📊 調用結果統計:
   總調用次數: 5
   成功觸發次數: 1
✅ 防護機制有效：只觸發了1次

🎯 測試總結:
資料庫層防護: ✅ 通過
應用層防護: ✅ 通過
🎉 所有測試通過！防護機制有效
```

## 📝 **修改文件清單**

### **主要修改**
- **文件**: `Capital_Official_Framework/simple_integrated.py`
- **修改內容**:
  1. 添加 `_auto_start_triggered` 狀態變數
  2. 修改 `update_range_calculation_safe()` 添加觸發檢查
  3. 修改 `check_auto_start_multi_group_strategy()` 添加防重複邏輯
  4. 修改 `start_multi_group_strategy()` 添加運行狀態檢查
  5. 修改 `stop_multi_group_strategy()` 添加狀態重置

### **測試文件**
- **新增**: `Capital_Official_Framework/test_duplicate_prevention.py`
- **新增**: `Capital_Official_Framework/check_database_status.py`

## 🚀 **使用建議**

### **正常使用流程**
1. **盤前準備**: 配置策略 → 點擊"📋 準備多組策略" → 勾選"🤖 區間完成後自動啟動"
2. **盤中運行**: 區間計算完成 → 系統自動啟動策略（只觸發一次）
3. **策略監控**: 系統正常運行，不會重複創建策略組

### **異常處理**
如果仍然遇到問題：
1. 檢查資料庫狀態：`python check_database_status.py`
2. 清理今天記錄：選擇選項2（謹慎使用）
3. 重新啟動程式

## 🎯 **修復效果**

### **解決的問題**
- ✅ 消除 UNIQUE constraint failed 錯誤
- ✅ 防止重複創建策略組
- ✅ 確保自動啟動只觸發一次
- ✅ 保持系統穩定性

### **保持的功能**
- ✅ 所有現有功能完全保留
- ✅ 自動啟動機制正常工作
- ✅ 多組策略系統正常運行
- ✅ 向後兼容性100%

## 📊 **技術細節**

### **防護機制層次**
1. **第一層**: 觸發標記防護（應用層）
2. **第二層**: 運行狀態檢查（邏輯層）
3. **第三層**: 資料庫UNIQUE約束（資料層）

### **狀態管理**
```python
# 狀態變數
self.multi_group_prepared = False      # 策略是否已準備
self.multi_group_auto_start = False    # 是否自動啟動
self.multi_group_running = False       # 策略是否運行中
self._auto_start_triggered = False     # 防止重複觸發（新增）
```

---

**📝 修復完成時間**: 2025-07-04  
**🎯 狀態**: ✅ **修復完成並驗證通過**  
**📊 測試結果**: 雙重防護機制有效，問題已解決
