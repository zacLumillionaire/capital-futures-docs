# 🔧 部位查詢功能修復指南

## 🔍 **問題分析**

根據你的錯誤日誌，我發現了兩個關鍵問題：

### 問題1: 初始化失敗 (1001錯誤)
```
SK_ERROR_INITIALIZE_FAIL (代碼: 1001)
```

### 問題2: 缺少帳號參數
```
required argument 'bstrAccount' missing
```

## ✅ **已實施的修復**

### 修復1: 使用正確的API函式
根據群益官方案例，我發現了API調用的差異：

#### 修復前 (錯誤)
```python
# 使用了錯誤的API
nCode = self.m_pSKOrder.GetOpenInterestGW(login_id, account, 1)
```

#### 修復後 (正確)
```python
# 使用官方案例的API
nCode = self.m_pSKOrder.GetOpenInterestWithFormat(login_id, account, nFormat)
```

### 修復2: 智慧單查詢參數完整化
根據官方案例，`GetStopLossReport` 需要更多參數：

#### 修復前 (缺少參數)
```python
nCode = self.m_pSKOrder.GetStopLossReport(login_id)
```

#### 修復後 (完整參數)
```python
nCode = self.m_pSKOrder.GetStopLossReport(login_id, account, nReportStatus, trade_kind, date)
```

### 修復3: 帳號格式調整
根據官方案例，期貨帳號不需要IB前綴：

#### 修復前
```python
account = "IB6363839"    # 錯誤格式
```

#### 修復後
```python
account = "6363839"      # 正確格式
```

### 修復4: 添加初始化檢查
在查詢前確保SKOrder已正確初始化：

```python
# 檢查SKOrder初始化狀態
init_code = self.m_pSKOrder.SKOrderLib_Initialize()
if init_code == 0:
    self.add_message("【初始化】SKOrderLib初始化成功")
elif init_code == 2003:  # SK_WARNING_INITIALIZE_ALREADY
    self.add_message("【初始化】SKOrderLib已初始化")
```

## 📋 **修復後的API調用**

### 未平倉部位查詢
```python
# 參數設定
login_id = "E123354882"  # 登入ID
account = "6363839"      # 期貨帳號 (不需要IB前綴)
nFormat = 1              # 1=完整格式

# API調用
nCode = self.m_pSKOrder.GetOpenInterestWithFormat(login_id, account, nFormat)
```

### 智慧單查詢
```python
# 參數設定
login_id = "E123354882"
account = "6363839"      # 期貨帳號
nReportStatus = 0        # 0=全部的委託單
trade_kind = ""          # 空字串=全部類型
date = ""                # 空字串=不限日期

# API調用
nCode = self.m_pSKOrder.GetStopLossReport(login_id, account, nReportStatus, trade_kind, date)
```

## 🧪 **測試修復效果**

### 測試步驟
1. **重新啟動程式**
   ```bash
   cd "Python File"
   python OrderTester.py
   ```

2. **登入並等待自動連線完成**
   - 登入: `E123354882` / `kkd5ysUCC`
   - 等待自動連線報價主機

3. **測試未平倉部位查詢**
   - 切換到「部位查詢」頁籤
   - 點擊「查詢未平倉部位」
   - 觀察是否還有1001錯誤

4. **測試智慧單查詢**
   - 點擊「查詢預約單/智慧單」
   - 觀察是否還有參數缺失錯誤

### 預期成功結果

#### 未平倉部位查詢
```
【查詢】開始查詢未平倉部位...
【初始化】SKOrderLib已初始化
【參數】登入ID: E123354882, 帳號: 6363839
【API調用】GetOpenInterestWithFormat(E123354882, 6363839, 1) - SK_SUCCESS (代碼: 0)
【成功】未平倉部位查詢請求已送出，等待回報...
【回報】收到未平倉部位回報: E123354882
```

#### 智慧單查詢
```
【查詢】開始查詢預約單/智慧單...
【初始化】SKOrderLib已初始化
【參數】登入ID: E123354882, 帳號: 6363839
【API調用】GetStopLossReport(E123354882, 6363839, 0, , ) - SK_SUCCESS (代碼: 0)
【成功】預約單/智慧單查詢請求已送出，等待回報...
【回報】收到預約單/智慧單回報: E123354882
```

## 🎯 **查詢你的委託狀態**

### 委託編號追蹤
根據你的委託回報：
```
委託編號: 2315544158849
```

修復後應該能夠查詢到：

#### 如果已成交
- **未平倉部位表格**會顯示 MTX00 的部位
- 包含數量、平均成本等資訊

#### 如果是條件單
- **智慧單表格**會顯示相關的智慧單記錄
- 包含智慧單號、狀態等資訊

## 🔧 **技術改進總結**

### 參考官方案例的改進
1. **API函式**: 使用 `GetOpenInterestWithFormat` 而非 `GetOpenInterestGW`
2. **參數完整性**: 智慧單查詢提供所有必要參數
3. **帳號格式**: 使用正確的期貨帳號格式
4. **初始化檢查**: 確保SKOrder正確初始化

### 針對國內商品優化
- **專注國內期貨**: 針對台指期貨等國內商品
- **正確市場代碼**: TF (國內期選)
- **適當的參數設定**: 符合國內期貨交易規範

## 🚀 **立即測試**

### 現在可以測試修復效果：

1. **重新啟動程式並登入**
2. **切換到「部位查詢」頁籤**
3. **測試未平倉部位查詢**
   - 應該不再有1001錯誤
   - 能正常查詢部位資料
4. **測試智慧單查詢**
   - 應該不再有參數缺失錯誤
   - 能正常查詢智慧單資料

### 成功指標
- [ ] 不再出現 SK_ERROR_INITIALIZE_FAIL (1001)
- [ ] 不再出現 required argument 'bstrAccount' missing
- [ ] API調用返回 SK_SUCCESS (代碼: 0)
- [ ] 能收到查詢回報資料
- [ ] 表格正常顯示查詢結果

## 💡 **重要發現**

### 官方案例的關鍵差異
1. **API命名**: 官方使用 `GetOpenInterestWithFormat` 而非 `GetOpenInterestGW`
2. **參數數量**: 智慧單查詢需要5個參數，不是1個
3. **帳號格式**: 期貨帳號直接使用數字，不需要前綴

### 國內商品特性
- **市場代碼**: TF (國內期選)
- **帳號格式**: 7位數字期貨帳號
- **查詢範圍**: 專注國內期貨和選擇權

**🎯 目標：成功查詢到你的委託編號 2315544158849 的狀態和部位資訊！**

## 📋 **測試檢查清單**

### API修復驗證
- [ ] 未平倉查詢使用 GetOpenInterestWithFormat
- [ ] 智慧單查詢提供完整參數
- [ ] 帳號格式為 6363839 (無前綴)
- [ ] 初始化檢查正常

### 功能測試
- [ ] 程式重新啟動
- [ ] 登入成功
- [ ] 部位查詢頁籤正常
- [ ] 兩個查詢按鈕都能正常工作

### 結果驗證
- [ ] 查詢API調用成功
- [ ] 收到回報資料
- [ ] 表格正常顯示
- [ ] 找到委託相關資訊

**🎉 修復完成！現在應該能夠正常查詢部位和智慧單了！**

---
*部位查詢功能修復指南*
*時間: 2025-06-29*
*狀態: 根據官方案例完成修復*
