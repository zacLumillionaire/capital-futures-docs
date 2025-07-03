# 群益證券API官方框架

## 📋 概述

這是基於群益證券提供的官方案例代碼建立的完整交易框架，包含四個核心服務：

- **Login** - 登入服務
- **order_service** - 下單服務  
- **Quote_Service** - 報價服務
- **Reply_Service** - 回報服務

## 🏗️ 架構特點

✅ **完全基於群益官方案例** - 避免自行開發的相容性問題  
✅ **包含完整SKCOM.dll** - 所有必要的DLL檔案都已配置  
✅ **支援您的期貨帳號** - 預設配置F0200006363839帳號  
✅ **避免GIL問題** - 使用群益原生事件處理機制  

## 📁 檔案結構

```
Capital_Official_Framework/
├── SKCOM.dll                 # 群益API核心檔案
├── user_config.py           # 使用者帳號配置
├── main.py                  # 主程式入口
├── simple_test.py           # 基礎功能測試
├── login_test.py            # 登入功能測試
├── Login/                   # 登入服務
│   ├── LoginForm.py
│   └── SKCOM.dll
├── order_service/           # 下單服務
│   ├── Order.py
│   ├── FutureOrder.py
│   ├── Global.py
│   └── SKCOM.dll
├── Quote_Service/           # 報價服務
│   ├── Quote.py
│   └── SKCOM.dll
└── Reply_Service/           # 回報服務
    ├── Reply.py
    └── SKCOM.dll
```

## 🚀 快速開始

### 1. 設定使用者資訊

編輯 `user_config.py`：

```python
USER_CONFIG = {
    'USER_ID': 'A123456789',        # 請填入您的身分證字號
    'PASSWORD': 'kkd5ysUCC',        # 您的密碼
    'FUTURES_ACCOUNT': 'F0200006363839',  # 您的期貨帳號
    # ... 其他設定
}
```

### 2. 執行基礎測試

```bash
python simple_test.py
```

預期輸出：
```
✅ 基本API測試: 成功
✅ order_service測試: 成功
🎉 所有測試通過！群益官方框架可以使用
```

### 3. 執行登入測試

```bash
python login_test.py
```

### 4. 啟動完整服務

```bash
python main.py
```

## 🔧 各服務功能

### Login服務
- 身分證字號/密碼登入
- 憑證管理
- 連線狀態監控

### order_service (下單服務)
- 期貨下單 (MTX00小台指)
- 委託查詢
- 部位查詢
- 智慧單管理

### Quote_Service (報價服務)
- 即時報價訂閱
- 歷史資料查詢
- Tick資料接收

### Reply_Service (回報服務)
- 委託回報 (OnNewData)
- 成交回報
- 連線狀態監控

## 📋 您的帳號設定

根據記憶中的資訊：

- **期貨帳號**: F0200006363839
- **密碼**: kkd5ysUCC (用於測試)
- **預設商品**: MTX00 (小台指期貨)
- **替代商品**: TM0000 (微型台指期貨)

## ⚠️ 重要提醒

1. **真實交易環境** - 這是連接真實交易系統，請謹慎操作
2. **最小單位測試** - 建議先用1口進行測試
3. **保證金確認** - 確保帳戶有足夠保證金
4. **風險控制** - 期貨交易具有高風險

## 🔍 測試順序

1. **基礎測試**: `python simple_test.py`
2. **登入測試**: `python login_test.py`  
3. **下單測試**: 使用order_service
4. **報價測試**: 使用Quote_Service
5. **回報測試**: 使用Reply_Service

## 💡 下一步計畫

1. ✅ 環境準備與SKCOM.dll配置
2. ✅ 基礎API物件初始化測試
3. 🔄 登入流程實作與測試
4. ⏳ 期貨下單功能整合
5. ⏳ 回報事件處理機制
6. ⏳ 即時報價訂閱功能
7. ⏳ 完整功能測試與驗證

## 🆘 常見問題

### Q: 登入失敗怎麼辦？
A: 檢查user_config.py中的USER_ID和PASSWORD是否正確

### Q: 找不到SKCOM.dll？
A: 確認每個服務資料夾都有SKCOM.dll檔案

### Q: API物件創建失敗？
A: 執行simple_test.py檢查基礎環境

## 📞 支援

如果遇到問題，請檢查：
1. SKCOM.dll是否存在
2. 使用者配置是否正確
3. 網路連線是否正常
4. 群益API服務是否正常
