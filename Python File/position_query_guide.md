# 📊 部位查詢與預約單查詢功能指南

## 🎯 **新增功能概述**

我已經實現了完整的部位查詢功能，可以查詢：
1. **未平倉部位** - 查看目前持有的期貨/選擇權部位
2. **預約單/智慧單** - 查看設定的條件單和預約委託

## 📋 **功能特色**

### ✅ **未平倉部位查詢**
- **API函式**: `GetOpenInterestGW`
- **回報事件**: `OnOpenInterest`
- **查詢範圍**: 國內期貨/選擇權未平倉部位
- **顯示資訊**: 市場別、帳號、商品、買賣、數量、平均成本等

### ✅ **預約單/智慧單查詢**
- **API函式**: `GetStopLossReport`
- **回報事件**: `OnStopLossReport`
- **查詢範圍**: 各種智慧單 (STP停損、MIT觸價、OCO二擇一等)
- **顯示資訊**: 智慧單號、策略別、狀態、觸發價、委託價等

### ✅ **即時狀態更新**
- **狀態異動事件**: `OnStrategyData`
- **即時通知**: 智慧單狀態變化主動推送

## 🧪 **使用步驟**

### 步驟1: 啟動程式並登入
```bash
cd "Python File"
python OrderTester.py
```

1. **登入**: `E123354882` / `kkd5ysUCC`
2. **等待自動連線完成**

### 步驟2: 查詢未平倉部位
1. **切換到「部位查詢」頁籤**
2. **點擊「查詢未平倉部位」按鈕** (藍色)
3. **觀察查詢結果**

#### 預期看到的訊息：
```
【查詢】開始查詢未平倉部位...
【參數】登入ID: E123354882, 帳號: IB6363839
【API調用】GetOpenInterestGW(E123354882, IB6363839, 1) - SK_SUCCESS (代碼: 0)
【成功】未平倉部位查詢請求已送出，等待回報...
【回報】收到未平倉部位回報: E123354882
```

#### 可能的結果：
- **有部位**: 顯示在「未平倉部位」表格中
- **無部位**: 顯示「目前無未平倉部位」

### 步驟3: 查詢預約單/智慧單
1. **點擊「查詢預約單/智慧單」按鈕** (綠色)
2. **觀察查詢結果**

#### 預期看到的訊息：
```
【查詢】開始查詢預約單/智慧單...
【參數】登入ID: E123354882
【API調用】GetStopLossReport(E123354882) - SK_SUCCESS (代碼: 0)
【成功】預約單/智慧單查詢請求已送出，等待回報...
【回報】收到預約單/智慧單回報: E123354882
```

## 📊 **查詢你的測試委託**

### 根據你的委託回報
```
委託回報: 【非同步委託】ThreadID: 1152, Code: 0, Message: 2315544158849
```

這個委託編號 `2315544158849` 的部位狀態可以通過以下方式查詢：

#### 1. **如果是已成交的委託**
- 會在「未平倉部位」中顯示
- 顯示商品、買賣方向、數量、平均成本等

#### 2. **如果是預約單或條件單**
- 會在「預約單/智慧單」中顯示
- 顯示智慧單號、狀態、觸發條件等

## 🔍 **資料格式說明**

### 未平倉部位表格欄位
| 欄位 | 說明 | 範例 |
|------|------|------|
| 市場 | 市場別 | TF (國內期選) |
| 帳號 | 委託帳號 | IB6363839 |
| 商品 | 商品代碼 | MTX00 |
| 買賣 | 買賣方向 | B (買進) / S (賣出) |
| 數量 | 未平倉數量 | 1 |
| 當沖數量 | 當沖未平倉 | 0 |
| 平均成本 | 平均成本價 | 22000.0 |
| 手續費 | 單口手續費 | 35.0 |
| 交易稅 | 交易稅 | 10.0 |

### 預約單/智慧單表格欄位
| 欄位 | 說明 | 範例 |
|------|------|------|
| 智慧單號 | 智慧單編號 | 2315544158849 |
| 策略別 | 單別類型 | 3:OCO, 5:STP, 8:MIT |
| 狀態 | 委託狀態 | 32:收單成功, 34:洗價中 |
| 商品 | 商品代碼 | MTX00 |
| 買賣 | 買賣方向 | B / S |
| 觸發價 | 觸發價格 | 22100.0 |
| 委託價 | 委託價格 | 22000.0 |
| 數量 | 委託數量 | 1 |
| 建立時間 | 下單時間 | 2025-06-29 14:30:00 |

## 🎯 **智慧單狀態代碼**

### 常見狀態代碼
- **32**: 中台收單成功
- **34**: 洗價中 (監控觸發條件)
- **37**: 洗價觸發 (條件已滿足)
- **38**: 觸發下單 (已送出委託)
- **39**: 下單失敗
- **40**: 使用者刪單

### 策略別代碼
- **3**: OCO (二擇一委託)
- **5**: STP (停損單)
- **8**: MIT (觸價單)
- **9**: MST (移動停損)

## 🔧 **技術實現細節**

### API調用參數
```python
# 未平倉部位查詢
GetOpenInterestGW(
    bstrLogInID="E123354882",    # 登入ID
    bstrAccount="IB6363839",     # 帳號格式：IB + 期貨帳號
    nFormat=1                    # 回傳格式
)

# 預約單/智慧單查詢
GetStopLossReport(
    bstrLogInID="E123354882"     # 登入ID
)
```

### 事件處理
```python
def OnOpenInterest(self, bstrLogInID, bstrData):
    """未平倉部位回報"""
    # 解析逗號分隔的資料
    # 格式：市場別,帳號,商品,買賣別,數量,當沖數量,平均成本,手續費,交易稅,LOGIN_ID

def OnStopLossReport(self, bstrLogInID, bstrData):
    """預約單/智慧單回報"""
    # 解析智慧單資料
    # 包含智慧單號、策略別、狀態、商品、價格等資訊
```

## 🚀 **立即測試**

### 測試你的委託狀態
1. **重新啟動程式並登入**
2. **切換到「部位查詢」頁籤**
3. **點擊「查詢未平倉部位」**
   - 查看是否有 MTX00 的部位
   - 確認數量和平均成本
4. **點擊「查詢預約單/智慧單」**
   - 查看是否有相關的智慧單
   - 確認委託狀態

### 預期結果
根據你的委託編號 `2315544158849`：
- **如果已成交**: 會在未平倉部位中看到 MTX00 的部位
- **如果是條件單**: 會在智慧單列表中看到相關記錄
- **如果已平倉**: 可能不會顯示在未平倉部位中

## 📋 **測試檢查清單**

### 功能測試
- [ ] 程式啟動並登入成功
- [ ] 切換到「部位查詢」頁籤
- [ ] 點擊「查詢未平倉部位」
- [ ] 觀察API調用結果
- [ ] 檢查部位表格顯示
- [ ] 點擊「查詢預約單/智慧單」
- [ ] 觀察智慧單查詢結果

### 資料驗證
- [ ] 確認帳號格式 (IB6363839)
- [ ] 確認登入ID (E123354882)
- [ ] 檢查回報資料格式
- [ ] 驗證表格顯示正確

### 委託追蹤
- [ ] 查詢委託編號 2315544158849 的狀態
- [ ] 確認 MTX00 商品的部位
- [ ] 檢查委託是否已成交
- [ ] 驗證部位數量和成本

**🎯 目標：成功查詢到你的測試委託狀態和當前部位！**

## 💡 **使用建議**

### 最佳實踐
1. **定期查詢**: 交易前後都查詢部位狀態
2. **監控智慧單**: 關注條件單的觸發狀態
3. **核對資料**: 確認部位數量和成本正確

### 注意事項
- **帳號格式**: 期貨帳號需要 IB 前綴
- **即時性**: 部位資料可能有延遲
- **狀態變化**: 智慧單狀態會即時更新

**🎉 現在可以完整追蹤你的期貨交易狀態了！**

---
*部位查詢與預約單查詢功能指南*
*時間: 2025-06-29*
*狀態: 完整實現部位查詢功能*
