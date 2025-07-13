# simple_integrated.py 最小修改整合方案

## 📋 概述

本文檔分析simple_integrated.py串接虛擬報價機所需的最小修改方案，確保在不破壞現有功能的前提下實現虛擬測試。

## 🎯 1. 整合策略

### 1.1 設計原則
- **最小侵入**: 僅修改必要的導入和配置
- **功能保持**: 所有策略邏輯保持不變
- **可切換**: 支持虛擬/真實API模式切換
- **向後兼容**: 不影響現有的真實交易功能

### 1.2 整合方式
- **模組替換**: 替換Global模組導入
- **配置開關**: 增加虛擬模式配置選項
- **環境隔離**: 虛擬模式使用獨立配置

## 🔧 2. 具體修改方案

### 2.1 Global模組導入修改

#### **原有代碼 (第24行)**
```python
# 原有導入
import order_service.Global as Global
```

#### **修改後代碼**
```python
# 🔧 虛擬報價機整合 - 支持模式切換
VIRTUAL_QUOTE_MODE = True  # 設為False使用真實API

if VIRTUAL_QUOTE_MODE:
    try:
        import virtual_quote_machine.Global as Global
        print("✅ 虛擬報價機模式啟用")
    except ImportError:
        import order_service.Global as Global
        print("⚠️ 虛擬報價機不可用，使用真實API")
        VIRTUAL_QUOTE_MODE = False
else:
    import order_service.Global as Global
    print("✅ 真實API模式啟用")
```

### 2.2 配置文件修改

#### **新增虛擬模式配置 (config.json)**
```json
{
    "VIRTUAL_QUOTE_MODE": true,
    "VIRTUAL_QUOTE_CONFIG": {
        "base_price": 21500,
        "price_range": 50,
        "spread": 5,
        "quote_interval": 0.5,
        "fill_probability": 0.95,
        "fill_delay_ms": 200
    },
    "DEFAULT_PRODUCT": "MTX00",
    "FUTURES_ACCOUNT": "F0200006363839"
}
```

#### **配置讀取修改**
```python
def load_config(self):
    """載入配置 - 支持虛擬模式"""
    try:
        with open('config.json', 'r', encoding='utf-8') as f:
            self.config = json.load(f)
        
        # 🔧 虛擬模式配置
        global VIRTUAL_QUOTE_MODE
        VIRTUAL_QUOTE_MODE = self.config.get('VIRTUAL_QUOTE_MODE', False)
        
        if VIRTUAL_QUOTE_MODE:
            self.virtual_config = self.config.get('VIRTUAL_QUOTE_CONFIG', {})
            print(f"🎯 虛擬報價機配置: {self.virtual_config}")
            
    except Exception as e:
        print(f"❌ 配置載入失敗: {e}")
        self.config = self.get_default_config()
```

### 2.3 登入流程修改

#### **login()函數修改 (第1057行)**
```python
def login(self):
    """登入系統 - 支持虛擬模式"""
    try:
        user_id = self.entry_id.get().strip()
        password = self.entry_password.get().strip()
        
        if not user_id or not password:
            self.add_log("❌ 請輸入身分證字號和密碼")
            return
        
        # 🔧 虛擬模式處理
        if VIRTUAL_QUOTE_MODE:
            self.add_log("🎯 虛擬報價機模式登入...")
            
            # 虛擬模式直接設為登入成功
            self.logged_in = True
            self.btn_login.config(state="disabled")
            self.btn_init_order.config(state="normal")
            self.add_log("✅ 虛擬模式登入成功")
            
            # 初始化虛擬報價機
            if hasattr(Global, 'init_virtual_quote_machine'):
                Global.init_virtual_quote_machine(self.virtual_config)
                
            return
        
        # 原有真實API登入邏輯保持不變
        self.add_log("🔐 開始登入...")
        # ... 原有登入代碼 ...
```

### 2.4 下單模組初始化修改

#### **init_order()函數修改 (第1121行)**
```python
def init_order(self):
    """初始化下單模組 - 支持虛擬模式"""
    try:
        if not self.logged_in:
            self.add_log("❌ 請先登入系統")
            return
        
        # 🔧 虛擬模式處理
        if VIRTUAL_QUOTE_MODE:
            self.add_log("🎯 虛擬下單模組初始化...")
            
            # 虛擬模式直接設為初始化成功
            self.btn_init_order.config(state="disabled")
            self.btn_test_order.config(state="normal")
            self.btn_connect_quote.config(state="normal")
            
            # 初始化虛擬回報連線
            self.init_reply_connection()
            
            self.add_log("✅ 虛擬下單模組初始化完成")
            return
        
        # 原有真實API初始化邏輯保持不變
        print("🔧 [INIT] 初始化下單模組...")
        # ... 原有初始化代碼 ...
```

### 2.5 報價連線修改

#### **connect_quote()函數修改 (第1211行)**
```python
def connect_quote(self):
    """連線報價服務 - 支持虛擬模式"""
    try:
        if not self.logged_in:
            self.add_log("❌ 請先登入系統")
            return
        
        # 🔧 虛擬模式處理
        if VIRTUAL_QUOTE_MODE:
            self.add_log("🎯 虛擬報價服務連線...")
            
            # 虛擬模式直接設為連線成功
            self.btn_connect_quote.config(state="disabled")
            self.btn_subscribe_quote.config(state="normal")
            
            self.add_log("✅ 虛擬報價服務連線成功")
            return
        
        # 原有真實API連線邏輯保持不變
        self.add_log("📡 連線報價服務...")
        # ... 原有連線代碼 ...
```

### 2.6 報價訂閱修改

#### **subscribe_quote()函數修改 (第1235行)**
```python
def subscribe_quote(self):
    """訂閱MTX00報價 - 支持虛擬模式"""
    try:
        product = self.config['DEFAULT_PRODUCT']
        
        # 🔧 虛擬模式處理
        if VIRTUAL_QUOTE_MODE:
            self.add_log(f"🎯 虛擬報價訂閱 {product}...")
            
            # 註冊報價事件
            self.register_quote_events()
            
            # 啟動虛擬報價推送
            if hasattr(Global, 'start_quote_feed'):
                Global.start_quote_feed(product, self.virtual_config)
            
            self.btn_subscribe_quote.config(state="disabled")
            self.btn_start_strategy.config(state="normal")
            
            self.add_log(f"✅ 虛擬 {product} 報價訂閱成功")
            return
        
        # 原有真實API訂閱邏輯保持不變
        self.add_log(f"📊 訂閱 {product} 報價...")
        # ... 原有訂閱代碼 ...
```

## 🔄 3. 虛擬報價機介面設計

### 3.1 Global模組介面

#### **virtual_quote_machine/Global.py**
```python
# 虛擬報價機Global模組
import threading
import time
from virtual_quote_engine import VirtualQuoteEngine

# 模擬群益API物件
class MockSKCenterLib:
    def SKCenterLib_Login(self, user_id, password):
        return 0  # 成功
    
    def SKCenterLib_GetReturnCodeMessage(self, code):
        return "成功" if code == 0 else f"錯誤代碼: {code}"

class MockSKOrderLib:
    def SKOrderLib_Initialize(self):
        return 0
    
    def ReadCertByID(self, user_id):
        return 0
    
    def SendFutureOrderCLR(self, user_id, async_flag, order):
        return virtual_engine.process_order(order)

class MockSKQuoteLib:
    def SKQuoteLib_EnterMonitorLONG(self):
        return 0
    
    def SKQuoteLib_RequestTicks(self, page, product):
        return 0

class MockSKReplyLib:
    def SKReplyLib_ConnectByID(self, user_id):
        return 0

# 全域物件
skC = MockSKCenterLib()
skO = MockSKOrderLib()
skQ = MockSKQuoteLib()
skR = MockSKReplyLib()

# 虛擬報價引擎
virtual_engine = None

def init_virtual_quote_machine(config):
    """初始化虛擬報價機"""
    global virtual_engine
    virtual_engine = VirtualQuoteEngine(config)

def start_quote_feed(product, config):
    """啟動報價推送"""
    if virtual_engine:
        virtual_engine.start_quote_feed(product)
```

### 3.2 事件處理保持

#### **事件註冊機制不變**
- `register_quote_events()` 函數保持不變
- `register_order_reply_events()` 函數保持不變
- 事件處理器類別結構保持不變
- 只是事件來源從真實API改為虛擬引擎

## 🧪 4. 測試驗證方案

### 4.1 功能測試
1. **登入測試**: 驗證虛擬模式登入流程
2. **報價測試**: 確認報價事件正常推送
3. **下單測試**: 驗證下單和回報流程
4. **策略測試**: 確認策略邏輯正常運作

### 4.2 切換測試
1. **模式切換**: 測試虛擬/真實模式切換
2. **配置載入**: 驗證配置正確讀取
3. **錯誤處理**: 測試異常情況處理

## 📊 5. 修改影響評估

### 5.1 程式碼修改量
- **新增代碼**: ~50行 (配置和模式判斷)
- **修改函數**: 5個函數 (login, init_order, connect_quote, subscribe_quote, load_config)
- **新增檔案**: 虛擬報價機模組 (~500行)

### 5.2 風險評估
- **低風險**: 原有邏輯完全保留
- **可回退**: 設定VIRTUAL_QUOTE_MODE=False即可回到原狀
- **隔離性**: 虛擬模式不影響真實API功能

### 5.3 維護成本
- **配置管理**: 需要維護虛擬模式配置
- **同步更新**: 虛擬API需要跟隨真實API介面變化
- **測試覆蓋**: 需要測試兩種模式的功能

## 🎯 6. 實施步驟

### 6.1 開發階段
1. **開發虛擬報價機引擎**
2. **實現Global模組替換**
3. **修改simple_integrated.py**
4. **配置文件調整**

### 6.2 測試階段
1. **單元測試**: 各模組獨立測試
2. **整合測試**: 完整流程測試
3. **壓力測試**: 長時間運行測試
4. **切換測試**: 模式切換驗證

### 6.3 部署階段
1. **備份原始代碼**
2. **部署虛擬報價機**
3. **配置虛擬模式**
4. **驗證功能正常**

---
*整合方案版本: v1.0*  
*最後更新: 2025-01-13*
