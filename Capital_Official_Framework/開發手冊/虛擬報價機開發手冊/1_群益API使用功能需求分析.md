# simple_integrated.py 群益API使用功能需求分析

## 📋 概述

本文檔從simple_integrated.py下單機的角度，反向分析其使用的群益API功能，為開發虛擬報價機提供需求基礎。

## 🔍 1. 群益API使用功能清單

### 1.1 即時報價功能 (SKQuoteLib)

#### **核心API調用**
```python
# 報價連線
Global.skQ.SKQuoteLib_EnterMonitorLONG()

# 報價訂閱
Global.skQ.SKQuoteLib_RequestTicks(0, product)  # product = "MTX00"

# 五檔報價訂閱
Global.skQ.SKQuoteLib_RequestBest5LONG(0, product)
```

#### **事件處理**
```python
class SKQuoteLibEvents:
    def OnNotifyTicksLONG(self, sMarketNo, nStockidx, nPtr, lDate, lTimehms, 
                         lTimemillismicros, nBid, nAsk, nClose, nQty, nSimulate):
        """即時報價事件 - 策略邏輯的核心觸發點"""
        
    def OnNotifyBest5LONG(self, sMarketNo, nStockidx, nPtr, lDate, lTimehms,
                         lTimemillismicros, nBestBid1, nBestBidQty1, nBestBid2, 
                         nBestBidQty2, nBestBid3, nBestBidQty3, nBestBid4, 
                         nBestBidQty4, nBestBid5, nBestBidQty5, nBestAsk1, 
                         nBestAskQty1, nBestAsk2, nBestAskQty2, nBestAsk3, 
                         nBestAskQty3, nBestAsk4, nBestAskQty4, nBestAsk5, 
                         nBestAskQty5, nSimulate):
        """五檔報價事件 - 提供買賣五檔資訊"""
```

#### **報價數據使用方式**
- **成交價 (nClose)**: 策略邏輯判斷、區間計算、突破檢測
- **買一價 (nBid)**: 空單進場價格參考、平倉追價
- **賣一價 (nAsk)**: 多單進場價格參考、平倉追價
- **成交量 (nQty)**: 市場活躍度判斷
- **時間戳 (lTimehms)**: 策略時間控制、K線計算

### 1.2 下單功能 (SKOrderLib)

#### **核心API調用**
```python
# 下單模組初始化
Global.skO.SKOrderLib_Initialize()

# 憑證讀取
Global.skO.ReadCertByID(user_id)

# 期貨下單
Global.skO.SendFutureOrderCLR(user_id, True, oOrder)
```

#### **下單參數結構 (FUTUREORDER)**
```python
oOrder = sk.FUTUREORDER()
oOrder.bstrFullAccount = "F0200006363839"  # 期貨帳號
oOrder.bstrStockNo = "MTX00"               # 商品代碼
oOrder.sBuySell = 0/1                      # 0=買進, 1=賣出
oOrder.sTradeType = 2                      # 0=ROD, 1=IOC, 2=FOK
oOrder.nQty = 1                            # 數量
oOrder.bstrPrice = "21500"                 # 價格(整數字串)
oOrder.sNewClose = 0/1                     # 0=新倉, 1=平倉
oOrder.sDayTrade = 1                       # 0=否, 1=當沖
oOrder.sReserved = 0                       # 0=盤中, 1=T盤預約
```

### 1.3 回報處理功能 (SKReplyLib)

#### **核心API調用**
```python
# 回報連線
Global.skR.SKReplyLib_ConnectByID(user_id)
```

#### **事件處理**
```python
class SKReplyLibEvent:
    def OnConnect(self, btrUserID, nErrorCode):
        """連線事件 - 自動切換實單模式"""
        
    def OnDisconnect(self, btrUserID, nErrorCode):
        """斷線事件 - 連線狀態更新"""
        
    def OnNewData(self, btrUserID, bstrData):
        """委託回報事件 - 核心回報處理"""
        
    def OnReplyMessage(self, bstrUserID, bstrMessages):
        """一般訊息事件"""
```

#### **回報數據格式**
```python
# bstrData格式 (逗號分隔)
cutData = bstrData.split(',')
# [0]=序號, [1]=帳號, [2]=商品, [3]=買賣別, [4]=委託價, [5]=委託量,
# [6]=成交價, [7]=成交量, [8]=委託狀態, [9]=委託時間, ...
```

### 1.4 系統管理功能 (SKCenterLib)

#### **核心API調用**
```python
# 登入
Global.skC.SKCenterLib_Login(user_id, password)

# 設定LOG路徑
Global.skC.SKCenterLib_SetLogPath(log_path)

# 錯誤訊息取得
Global.skC.SKCenterLib_GetReturnCodeMessage(nCode)
```

## 🎯 2. 下單機對API的依賴分析

### 2.1 策略邏輯依賴

#### **報價頻率需求**
- **頻率**: 每0.5秒一次報價更新
- **用途**: 
  - 區間計算 (08:46-08:47)
  - 即時突破檢測
  - 移動停利監控
  - 平倉條件判斷

#### **報價數據完整性**
- **必要欄位**: 成交價、買一價、賣一價、時間戳
- **可選欄位**: 成交量、五檔深度
- **精度要求**: 價格精確到整數點位

### 2.2 下單執行依賴

#### **下單回應需求**
- **即時回應**: SendFutureOrderCLR需要立即返回結果
- **回應格式**: (message, nCode) tuple
- **成功標準**: nCode = 0

#### **回報處理需求**
- **回報時效**: 下單後0.5秒內收到回報
- **回報完整性**: 包含委託序號、狀態、成交資訊
- **狀態追蹤**: 新單(N)、成交(D)、取消(C)、錯誤(R)

### 2.3 連線穩定性依賴

#### **連線監控**
- **連線狀態**: OnConnect/OnDisconnect事件
- **自動重連**: 斷線後自動重新連線
- **狀態同步**: 連線狀態影響下單模式切換

## 🔧 3. 虛擬報價機需要模擬的功能

### 3.1 必須模擬的API

#### **SKQuoteLib (報價)**
- `SKQuoteLib_EnterMonitorLONG()` - 報價連線
- `SKQuoteLib_RequestTicks()` - 報價訂閱
- `OnNotifyTicksLONG()` - 即時報價事件

#### **SKOrderLib (下單)**
- `SKOrderLib_Initialize()` - 下單初始化
- `ReadCertByID()` - 憑證讀取
- `SendFutureOrderCLR()` - 期貨下單

#### **SKReplyLib (回報)**
- `SKReplyLib_ConnectByID()` - 回報連線
- `OnConnect()` - 連線事件
- `OnNewData()` - 委託回報事件

#### **SKCenterLib (系統)**
- `SKCenterLib_Login()` - 登入
- `SKCenterLib_GetReturnCodeMessage()` - 錯誤訊息

### 3.2 可選模擬的API

#### **進階報價功能**
- `OnNotifyBest5LONG()` - 五檔報價 (用於追價)
- `SKQuoteLib_RequestBest5LONG()` - 五檔訂閱

#### **系統管理功能**
- `SKCenterLib_SetLogPath()` - LOG設定
- `OnReplyMessage()` - 一般訊息

## 📊 4. 總結

### 4.1 核心需求
1. **即時報價推送**: 每0.5秒提供成交價、買賣一價
2. **下單介面模擬**: 接收下單請求並返回結果
3. **回報事件推送**: 模擬委託狀態變化
4. **連線狀態管理**: 提供連線/斷線事件

### 4.2 簡化策略
- **重點模擬**: 報價推送、下單回應、回報處理
- **簡化處理**: 五檔深度、複雜錯誤處理
- **測試導向**: 確保下單機正常運作即可

### 4.3 開發優先級
1. **高優先級**: OnNotifyTicksLONG、SendFutureOrderCLR、OnNewData
2. **中優先級**: 連線事件、錯誤處理
3. **低優先級**: 五檔報價、LOG管理

---
*分析基於 simple_integrated.py v3135行*  
*最後更新: 2025-01-13*
