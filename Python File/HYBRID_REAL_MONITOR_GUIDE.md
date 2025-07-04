# 📡 混合模式實盤監控使用指南

## 🎯 **解決方案說明**

✅ **API初始化問題已解決！**

經過修復，test_ui_improvements.py現在可以直接初始化群益API，無需依賴OrderTester.py。

**兩種使用方式：**
1. **直接模式** - test_ui_improvements.py直接初始化API（推薦）
2. **混合模式** - 仍可配合OrderTester.py使用（備用）

---

## 🚀 **使用步驟**

### **方式1: 直接模式（推薦）**

#### **步驟1: 直接啟動test_ui_improvements.py**
```bash
cd "Python File"
python test_ui_improvements.py
```

#### **步驟2: 開始實盤監控**
1. 點擊 **「📡 開始實盤監控」** 按鈕
2. 系統會自動初始化群益API
3. 自動登入群益證券
4. 顯示 **「📡 實盤監控中...」**
5. 開始接收實盤報價並運行策略

### **方式2: 混合模式（備用）**

#### **步驟1: 啟動OrderTester.py**
```bash
cd "Python File"
python OrderTester.py
```

1. **登入群益證券**
   - 帳號: `E123354882`
   - 密碼: `kkd5ysUCC`
   - 確認登入狀態顯示為 **綠色**

#### **步驟2: 啟動test_ui_improvements.py**
```bash
# 在另一個終端視窗
python test_ui_improvements.py
```

#### **步驟3: 開始實盤監控**
1. 點擊 **「📡 開始實盤監控」** 按鈕
2. 系統會檢查OrderTester狀態或直接初始化API
3. 顯示 **「📡 實盤監控中...」**
4. 開始接收實盤報價並運行策略

---

## 🔍 **狀態檢查機制**

### **自動檢查項目**
當點擊「開始實盤監控」時，系統會檢查：

1. **OrderTester運行狀態**
   - 檢查程序是否在運行
   - 檢查API物件是否已初始化

2. **登入狀態驗證**
   - 確認已成功登入群益證券
   - 驗證API物件可用性

3. **報價服務狀態**
   - 檢查報價連接是否正常
   - 確認可以接收報價資料

### **錯誤處理**
如果檢查失敗，系統會：
- 顯示詳細的錯誤說明
- 提供解決建議
- 允許用戶重新嘗試

---

## 📋 **常見問題解決**

### **Q1: 點擊「開始實盤監控」後顯示需要OrderTester支援？**
**解決方案：**
1. 確認OrderTester.py正在運行
2. 確認已成功登入（狀態為綠色）
3. 重新點擊「開始實盤監控」

### **Q2: OrderTester已登入但仍然連接失敗？**
**解決方案：**
1. 重新啟動OrderTester.py
2. 確認登入過程沒有錯誤
3. 檢查網路連接
4. 重新啟動test_ui_improvements.py

### **Q3: 如何確認實盤監控正常運作？**
**檢查指標：**
- 狀態顯示「📡 實盤監控中...」
- 當前價格有實時更新
- 日誌顯示「✅ 實盤監控已啟動」

---

## 🔄 **備用方案**

如果混合模式遇到問題，可以使用以下備用方案：

### **方案1: 橋接模式**
1. 確保OrderTester.py正在運行
2. 點擊「🌉 橋接模式」
3. 使用檔案橋接方式接收報價

### **方案2: TCP模式**
1. 確保OrderTester.py正在運行
2. 點擊「🚀 TCP模式」
3. 使用TCP連接接收報價（注意GIL風險）

### **方案3: 模擬模式**
1. 點擊「🎮 模擬報價」
2. 使用模擬價格進行策略測試

---

## 🎯 **優勢說明**

### **混合模式的優點**
- ✅ **穩定可靠** - 重用OrderTester的穩定初始化邏輯
- ✅ **簡化操作** - 一鍵啟動實盤監控
- ✅ **風險控制** - 避免複雜的API初始化問題
- ✅ **向後相容** - 保留所有現有功能

### **技術架構**
```
OrderTester.py (API初始化和登入)
    ↓ 提供已初始化的API物件
test_ui_improvements.py (策略和UI)
    ↓ 重用API物件
實盤報價監控 (穩定運行)
```

---

## 📝 **使用流程總結**

1. **🚀 啟動OrderTester.py** → 登入群益證券
2. **🎯 啟動test_ui_improvements.py** → 載入策略系統
3. **📡 點擊開始實盤監控** → 自動檢查並連接
4. **✅ 確認監控狀態** → 開始策略交易
5. **🛑 需要時停止監控** → 安全停止並清理

這個流程確保了最大的穩定性和可靠性，同時保持了操作的簡便性。

---

📚 **混合模式使用指南**  
📅 **建立日期**: 2025-01-01  
🔄 **版本**: 1.0  

*這個解決方案平衡了穩定性和便利性，是目前最可靠的實盤監控方案。*
