# 📋 OnNewData事件欄位完整指南

## 🎯 **當沖交易關鍵欄位**

根據群益API官方文件，OnNewData事件的bstrData包含49個欄位（索引0-48），以逗號分隔。

### ⭐ **核心欄位對照表**

| 索引 | 欄位名稱 | 說明 | 當沖重要性 | 範例值 | 備註 |
|------|---------|------|-----------|--------|------|
| **0** | **KeyNo** | **13碼委託序號** | ⭐⭐⭐⭐⭐ | 2315544224514 | 追蹤委託的唯一識別 |
| **1** | MarketType | 市場類型 | ⭐⭐ | TF | TF=期貨, TO=選擇權 |
| **2** | **Type** | **委託狀態** | ⭐⭐⭐⭐⭐ | N/C/D/P/U/B/S | 最重要的狀態欄位 |
| **3** | **OrderErr** | **委託結果** | ⭐⭐⭐⭐⭐ | N/Y/T | 成功與否的判斷 |
| **4** | BrokerID | 券商代號 | ⭐ | F020000 | 固定值 |
| **5** | Account | 帳號 | ⭐ | 6363839 | 交易帳號 |
| **6** | UserDefine | 自定義欄位 | ⭐ | BNF20 | 使用者定義 |
| **7** | ExchangeNo | 交易所代號 | ⭐ | TW | TW=台灣 |
| **8** | StockNo | 商品代號 | ⭐⭐⭐ | MTX00 | 交易商品 |
| **9** | OrderNo | 委託編號 | ⭐⭐ | | 券商內部編號 |
| **10** | Price2 | 價格2 | ⭐ | | 特殊用途 |
| **11** | **Price** | **主要價格** | ⭐⭐⭐⭐⭐ | 22000.0000 | 委託價/成交價 |
| **12** | Numerator | 價格分子 | ⭐ | | 海外期貨用 |
| **13** | Denominator | 價格分母 | ⭐ | | 海外期貨用 |
| **14-19** | 保留欄位 | 保留使用 | ⭐ | | |
| **20** | **Qty** | **數量(口數)** | ⭐⭐⭐⭐⭐ | 1 | 委託量/成交量 |
| **21** | Before | 修改前數量 | ⭐⭐ | | 改量時使用 |
| **22** | After | 修改後數量 | ⭐⭐ | | 改量時使用 |
| **23** | Date | 日期 | ⭐⭐ | 20250630 | YYYYMMDD |
| **24** | Time | 時間 | ⭐⭐⭐ | 14:30:15 | HH:MM:SS |
| **25-43** | 其他欄位 | 各種資訊 | ⭐ | | 依需求使用 |
| **44** | **ErrorMsg** | **錯誤訊息** | ⭐⭐⭐ | | 失敗時的原因 |
| **45** | 保留 | 保留使用 | ⭐ | | |
| **46** | **ExchangeTandemMsg** | **交易所訊息** | ⭐⭐⭐ | | 退單原因 |
| **47** | **SeqNo** | **新序號欄位** | ⭐⭐⭐⭐ | | 期選市場專用 |
| **48** | 保留 | 保留使用 | ⭐ | | |

## 🔍 **委託狀態詳解 (Type欄位)**

### **Type欄位值對照**
```python
TYPE_MAP = {
    "N": "委託",      # 新委託進入市場
    "C": "取消",      # 委託被取消
    "U": "改量",      # 修改委託數量
    "P": "改價",      # 修改委託價格
    "D": "成交",      # 委託成交 ⭐⭐⭐⭐⭐
    "B": "改價改量",   # 同時修改價格和數量
    "S": "動態退單"    # 系統自動退單
}
```

### **OrderErr欄位值對照**
```python
ORDER_ERR_MAP = {
    "N": "正常",      # 委託正常處理 ✅
    "Y": "失敗",      # 委託失敗 ❌
    "T": "逾時"       # 委託逾時 ⏰
}
```

## 💰 **當沖交易關鍵組合**

### 🎉 **成交確認 (最重要)**
```python
if Type == "D" and OrderErr == "N":
    委託序號 = KeyNo (索引0) 或 SeqNo (索引47)
    成交價格 = Price (索引11)
    成交口數 = Qty (索引20)
    成交時間 = Time (索引24)
    
    # 小台指期貨每點50元
    成交金額 = 成交價格 * 成交口數 * 50
    
    print(f"🎉 成交確認: {成交價格} x {成交口數}口 = {成交金額:,.0f}元")
```

### ✅ **委託成功**
```python
if Type == "N" and OrderErr == "N":
    委託序號 = KeyNo (索引0)
    委託價格 = Price (索引11)
    委託口數 = Qty (索引20)
    
    print(f"✅ 委託成功: 序號{委託序號} 價格{委託價格} 數量{委託口數}口")
```

### 🗑️ **委託取消**
```python
if Type == "C" and OrderErr == "N":
    委託序號 = KeyNo (索引0)
    原價格 = Price (索引11)
    剩餘口數 = Qty (索引20)
    
    print(f"🗑️ 委託取消: 序號{委託序號} 剩餘{剩餘口數}口")
```

### ❌ **委託失敗**
```python
if Type == "N" and OrderErr == "Y":
    委託序號 = KeyNo (索引0)
    錯誤訊息 = ErrorMsg (索引44)
    
    print(f"❌ 委託失敗: 序號{委託序號} 原因:{錯誤訊息}")
```

## 📊 **當沖損益計算範例**

### **基本計算公式**
```python
def calculate_trade_pnl(entry_price, exit_price, qty, direction):
    """
    計算當沖損益
    
    Args:
        entry_price: 進場價格
        exit_price: 出場價格  
        qty: 交易口數
        direction: 方向 ("買進"/"賣出")
    
    Returns:
        損益金額 (元)
    """
    if direction == "買進":
        # 做多: (出場價 - 進場價) * 口數 * 每點價值
        pnl = (exit_price - entry_price) * qty * 50
    else:
        # 做空: (進場價 - 出場價) * 口數 * 每點價值
        pnl = (entry_price - exit_price) * qty * 50
    
    return pnl

# 範例
entry_price = 22000  # 進場價格
exit_price = 22050   # 出場價格
qty = 1              # 1口
direction = "買進"   # 做多

pnl = calculate_trade_pnl(entry_price, exit_price, qty, direction)
print(f"損益: {pnl:+.0f}元")  # +2500元 (50點 x 1口 x 50元)
```

## 🎯 **實戰應用建議**

### **1. 即時監控重點**
- **成交回報 (Type=D)**: 立即計算損益
- **委託確認 (Type=N, OrderErr=N)**: 確認進場
- **委託失敗 (Type=N, OrderErr=Y)**: 檢查原因

### **2. 風險控制**
- **動態退單 (Type=S)**: 注意市場異常
- **委託取消 (Type=C)**: 確認是否為主動取消

### **3. 策略執行**
- **使用KeyNo或SeqNo追蹤委託**
- **記錄每筆成交的價格和數量**
- **即時計算浮動損益**

## 📋 **程式實作範例**

```python
def parse_onnewdata_for_trading(bstr_data):
    """解析OnNewData用於當沖交易"""
    try:
        fields = bstr_data.split(',')
        
        if len(fields) < 25:
            return None
        
        # 解析關鍵欄位
        result = {
            'key_no': fields[0],           # 委託序號
            'market_type': fields[1],      # 市場類型
            'type': fields[2],             # 委託狀態
            'order_err': fields[3],        # 委託結果
            'stock_no': fields[8],         # 商品代號
            'price': float(fields[11]) if fields[11] else 0,  # 價格
            'qty': int(fields[20]) if fields[20] else 0,      # 數量
            'date': fields[23],            # 日期
            'time': fields[24],            # 時間
            'error_msg': fields[44] if len(fields) > 44 else "",  # 錯誤訊息
            'seq_no': fields[47] if len(fields) > 47 else fields[0]  # 序號
        }
        
        return result
        
    except Exception as e:
        print(f"解析失敗: {e}")
        return None
```

---

**🎯 這份指南涵蓋了當沖交易所需的所有關鍵欄位資訊**

*更新時間: 2025-06-30*  
*版本: v1.0 - OnNewData完整欄位指南*  
*用途: 當沖交易點位計算與策略開發*
