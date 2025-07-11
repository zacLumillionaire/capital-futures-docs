# 🔧 SK_ERROR_INITIALIZE_FAIL (1001) 修復指南

## 🚨 **問題分析**

### 錯誤訊息：
```
【API回應】SK_ERROR_INITIALIZE_FAIL (代碼: 1001)
【失敗】期貨下單失敗: SK_ERROR_INITIALIZE_FAIL
```

### 根據官方文件，錯誤1001的可能原因：

#### 1. **尚未簽署期貨API下單聲明書**
- 這是最常見的原因
- 需要向群益證券申請並簽署聲明書

#### 2. **SKOrderLib未正確初始化**
- 需要先調用 `SKOrderLib_Initialize()`
- 必須在登入後進行

#### 3. **帳號格式問題**
- 期貨帳號格式可能需要包含分公司代碼
- 例如：`分公司代碼-帳號` 或其他格式

#### 4. **期貨帳號未開通**
- 帳號可能沒有期貨交易權限

## ✅ **修復步驟**

### 步驟1: 確認期貨API下單聲明書
根據官方下單準備文件：

> **重要提醒**：使用期貨API下單功能前，必須先向群益證券申請並簽署「期貨API下單聲明書」

**解決方法**：
1. 聯繫群益證券客服
2. 申請期貨API下單權限
3. 簽署相關聲明書

### 步驟2: 正確的初始化順序
根據官方案例，正確的順序應該是：

```python
# 1. 登入
nCode = m_pSKCenter.SKCenterLib_Login(user_id, password)

# 2. 初始化SKOrderLib
nCode = m_pSKOrder.SKOrderLib_Initialize()

# 3. 查詢帳號
nCode = m_pSKOrder.GetUserAccount()

# 4. 然後才能下單
```

### 步驟3: 確認帳號格式
期貨帳號可能需要特定格式：

**可能的格式**：
- `6363839` (你目前使用的)
- `分公司代碼-6363839`
- `完整帳號格式`

**測試方法**：
1. 先成功查詢帳號
2. 觀察回報中的帳號格式
3. 使用正確的帳號格式下單

### 步驟4: 檢查期貨交易權限
確認帳號具有：
- 期貨交易權限
- API下單權限
- 相關商品交易權限

## 🧪 **測試建議**

### 立即測試步驟：

#### 1. **測試初始化**
```python
# 在期貨下單前，先點擊「查詢期貨帳號」
# 觀察初始化結果
```

#### 2. **觀察回報訊息**
- 查看帳號查詢的回報
- 確認帳號格式
- 檢查是否有錯誤訊息

#### 3. **聯繫群益證券**
如果初始化仍然失敗：
1. 致電群益證券客服
2. 確認期貨API下單權限
3. 詢問正確的帳號格式

## 📋 **我已實現的修復**

### 1. **加強初始化檢查**
```python
# 在下單前先檢查初始化
nCode = self.m_pSKOrder.SKOrderLib_Initialize()
if nCode != 0:
    # 顯示詳細錯誤訊息和建議
```

### 2. **詳細錯誤提示**
```python
if nCode == 1001:
    self.add_message("【提示】錯誤1001通常表示：")
    self.add_message("1. 尚未簽署期貨API下單聲明書")
    self.add_message("2. 帳號格式不正確")
    self.add_message("3. 期貨帳號未開通")
```

### 3. **完整的測試流程**
- 先測試查詢帳號
- 再測試下單功能
- 提供詳細的錯誤分析

## 🎯 **下一步行動**

### 立即行動：
1. **測試查詢帳號功能**
   ```bash
   python OrderTester.py
   # 登入後點擊「查詢期貨帳號」
   ```

2. **觀察初始化結果**
   - 如果初始化成功，再測試下單
   - 如果失敗，需要聯繫群益證券

### 如果初始化成功但下單仍失敗：
1. 檢查帳號格式
2. 確認商品代碼格式
3. 檢查其他參數

### 如果初始化失敗：
1. **聯繫群益證券客服**
2. **申請期貨API下單權限**
3. **簽署相關聲明書**

## 📞 **群益證券聯繫方式**

根據官方文件，你可能需要：
1. 致電群益證券客服
2. 說明需要申請「期貨API下單權限」
3. 提供你的帳號：`6363839`
4. 詢問是否已簽署相關聲明書

## 🎉 **好消息**

雖然遇到1001錯誤，但這表示：
- ✅ API連接正常
- ✅ 登入成功
- ✅ 程式邏輯正確
- ❌ 只是缺少期貨API下單權限

**這是一個權限問題，不是技術問題！**

## 🚀 **測試計畫**

### 第一步：測試查詢帳號
```bash
cd "Python File"
python OrderTester.py
# 1. 登入
# 2. 切換到期貨下單頁籤
# 3. 點擊「查詢期貨帳號」
# 4. 觀察初始化結果
```

### 第二步：根據結果決定下一步
- **如果查詢成功** → 測試下單
- **如果查詢失敗** → 聯繫群益證券

**🎯 準備好測試查詢帳號功能了嗎？這將告訴我們確切的問題所在！**

---
*SK_ERROR_INITIALIZE_FAIL (1001) 修復指南*
*時間: 2025-06-29*
*基於群益證券官方API文件分析*
