# 🔧 實際下單功能技術規格書

## 📋 **技術架構概述**

### **系統架構圖**
```
┌─────────────────────────────────────────────────────────────────┐
│                     實際下單功能架構                              │
├─────────────────────────────────────────────────────────────────┤
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐ │
│  │ 報價管理器  │  │ FOK執行器   │  │ 追蹤系統    │  │ 重試管理器  │ │
│  │ (五檔ASK)   │→ │ (買ASK下單) │→ │ (回報監控)  │→ │ (失敗重試)  │ │
│  └─────────────┘  └─────────────┘  └─────────────┘  └─────────────┘ │
│         │                 │                 │                 │    │
│         ▼                 ▼                 ▼                 ▼    │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐ │
│  │ 多口管理器  │  │ 平倉整合器  │  │ 部位同步器  │  │ 資料記錄器  │ │
│  │ (批次下單)  │  │ (FIFO平倉)  │  │ (狀態同步)  │  │ (交易記錄)  │ │
│  └─────────────┘  └─────────────┘  └─────────────┘  └─────────────┘ │
│                                │                                   │
│                                ▼                                   │
│                    ┌─────────────────────┐                        │
│                    │   多組策略系統      │                        │
│                    │ (核心業務邏輯整合)  │                        │
│                    └─────────────────────┘                        │
└─────────────────────────────────────────────────────────────────┘
```

## 🎯 **核心組件技術規格**

### **1. 即時報價管理器 (RealTimeQuoteManager)**

#### **數據結構**
```python
class QuoteData:
    """報價數據結構"""
    ask_prices: List[float]     # [ask1, ask2, ask3, ask4, ask5]
    ask_quantities: List[int]   # [qty1, qty2, qty3, qty4, qty5]
    bid_prices: List[float]     # [bid1, bid2, bid3, bid4, bid5]
    bid_quantities: List[int]   # [qty1, qty2, qty3, qty4, qty5]
    last_price: float           # 最新成交價
    last_update: datetime       # 最後更新時間
    product_code: str           # 商品代碼
```

#### **核心API**
```python
class RealTimeQuoteManager:
    def update_best5_data(self, market_no, stock_idx, 
                          ask1, ask1_qty, ask2, ask2_qty, ask3, ask3_qty,
                          ask4, ask4_qty, ask5, ask5_qty,
                          bid1, bid1_qty, bid2, bid2_qty, bid3, bid3_qty,
                          bid4, bid4_qty, bid5, bid5_qty) -> bool:
        """更新五檔數據 - 從OnNotifyBest5LONG調用"""
        
    def get_best_ask_price(self, product_code: str) -> Optional[float]:
        """取得最佳賣價 - 策略進場使用"""
        
    def get_ask_depth(self, product_code: str, levels: int = 5) -> List[Tuple[float, int]]:
        """取得ASK深度 - 大量下單參考"""
        
    def is_quote_fresh(self, product_code: str, max_age_seconds: int = 5) -> bool:
        """檢查報價新鮮度"""
```

#### **整合點**
- **simple_integrated.py**: 修改`OnNotifyBest5LONG`事件
- **multi_group_position_manager.py**: 進場時查詢ASK價格

### **2. FOK買ASK執行器 (FOKOrderExecutor)**

#### **下單參數結構**
```python
class FOKOrderParams:
    """FOK下單參數"""
    product_code: str           # 商品代碼 (MTX00/TM0000)
    direction: str              # 方向 (BUY/SELL)
    quantity: int               # 數量
    ask_price: float            # ASK價格
    account: str                # 帳號
    new_close: int              # 新倉/平倉 (0/1)
    max_retry: int              # 最大重試次數
```

#### **核心API**
```python
class FOKOrderExecutor:
    def place_fok_buy_ask_order(self, params: FOKOrderParams) -> OrderResult:
        """FOK買ASK下單執行"""
        # 1. 驗證ASK價格有效性
        # 2. 構建下單物件
        # 3. 調用群益API下單
        # 4. 返回下單結果
        
    def validate_ask_price(self, ask_price: float, last_price: float) -> bool:
        """驗證ASK價格合理性"""
        # 檢查價格偏離度不超過合理範圍
        
    def build_order_object(self, params: FOKOrderParams) -> FUTUREORDER:
        """構建群益API下單物件"""
```

#### **整合點**
- **order/future_order.py**: 使用現有下單API
- **multi_lot_order_manager.py**: 被多口管理器調用

### **3. 訂單追蹤系統 (OrderTrackingSystem)**

#### **訂單狀態枚舉**
```python
class OrderStatus(Enum):
    PENDING = "PENDING"         # 等待確認
    CONFIRMED = "CONFIRMED"     # 已確認
    FILLED = "FILLED"           # 已成交
    PARTIAL_FILLED = "PARTIAL"  # 部分成交
    CANCELLED = "CANCELLED"     # 已取消
    FAILED = "FAILED"           # 失敗
    TIMEOUT = "TIMEOUT"         # 超時
```

#### **追蹤記錄結構**
```python
class OrderTrackingRecord:
    """訂單追蹤記錄"""
    order_id: str               # 訂單ID
    seq_no: str                 # 委託序號 (13碼)
    status: OrderStatus         # 訂單狀態
    submit_time: datetime       # 送單時間
    confirm_time: datetime      # 確認時間
    fill_time: datetime         # 成交時間
    fill_price: float           # 成交價格
    fill_quantity: int          # 成交數量
    callback_func: Callable     # 回調函數
    retry_count: int            # 重試次數
```

#### **核心API**
```python
class OrderTrackingSystem:
    def register_order(self, order_info: dict, callback_func: Callable) -> str:
        """註冊訂單追蹤"""
        
    def process_order_report(self, seq_no: str, order_type: str, 
                           order_err: str, order_data: str) -> bool:
        """處理OnNewData回報"""
        # 解析回報數據格式:
        # Type: 'N'=新單, 'D'=成交, 'C'=取消, 'U'=更新
        
    def get_order_status(self, order_id: str) -> Optional[OrderTrackingRecord]:
        """查詢訂單狀態"""
        
    def cleanup_expired_orders(self, max_age_hours: int = 24) -> int:
        """清理過期訂單記錄"""
```

#### **整合點**
- **simple_integrated.py**: 修改`OnNewData`事件處理
- **intelligent_retry_manager.py**: 失敗訂單重試

### **4. 多口訂單管理器 (MultiLotOrderManager)**

#### **批次下單策略**
```python
class BatchOrderStrategy(Enum):
    SEQUENTIAL = "SEQUENTIAL"   # 順序下單
    PARALLEL = "PARALLEL"       # 並行下單
    ADAPTIVE = "ADAPTIVE"       # 自適應下單
```

#### **核心API**
```python
class MultiLotOrderManager:
    def place_multiple_lots(self, direction: str, total_lots: int, 
                           strategy_config: dict) -> BatchOrderResult:
        """執行多口批次下單"""
        # 1. 分割總口數
        # 2. 依策略執行下單
        # 3. 協調訂單狀態
        # 4. 處理部分成交
        
    def handle_partial_fill(self, filled_orders: List[OrderResult], 
                           remaining_lots: int) -> bool:
        """處理部分成交情況"""
        
    def coordinate_order_status(self, batch_id: str) -> BatchStatus:
        """協調批次訂單狀態"""
```

### **5. 智能重試管理器 (IntelligentRetryManager)**

#### **重試策略配置**
```python
class RetryConfig:
    """重試配置"""
    max_retries: int = 3                    # 最大重試次數
    max_retry_time: int = 30                # 最大重試時間(秒)
    price_update_threshold: int = 5         # 價格更新閾值(點)
    retry_delays: List[int] = [1, 3, 5]     # 重試延遲(秒)
    use_last_price_on_retry: bool = False   # 重試時使用成交價
```

#### **失敗原因分析**
```python
class FailureReason(Enum):
    PRICE_DEVIATION = "PRICE_DEVIATION"     # 價格偏離
    INSUFFICIENT_QUANTITY = "INSUFFICIENT"  # 數量不足
    SYSTEM_BUSY = "SYSTEM_BUSY"            # 系統忙碌
    ACCOUNT_ERROR = "ACCOUNT_ERROR"        # 帳戶錯誤
    NETWORK_ERROR = "NETWORK_ERROR"        # 網路錯誤
    UNKNOWN_ERROR = "UNKNOWN_ERROR"        # 未知錯誤
```

#### **核心API**
```python
class IntelligentRetryManager:
    def analyze_failure(self, error_code: int, error_message: str) -> FailureReason:
        """分析失敗原因"""
        
    def determine_retry_strategy(self, failure_reason: FailureReason, 
                               retry_count: int) -> RetryStrategy:
        """決定重試策略"""
        
    def execute_retry(self, failed_order: OrderTrackingRecord) -> OrderResult:
        """執行重試下單"""
```

### **6. 平倉整合器 (MultiGroupCloseIntegrator)**

#### **平倉參數計算**
```python
class CloseOrderParams:
    """平倉參數"""
    position_id: int            # 部位ID
    group_id: int               # 策略組ID
    lot_id: int                 # 口數ID
    original_direction: str     # 原始方向 (LONG/SHORT)
    close_direction: str        # 平倉方向 (SELL/BUY)
    close_price: float          # 平倉價格
    close_quantity: int         # 平倉數量
    close_reason: str           # 平倉原因
```

#### **核心API**
```python
class MultiGroupCloseIntegrator:
    def execute_position_close(self, close_params: CloseOrderParams) -> CloseResult:
        """執行部位平倉"""
        # 1. 驗證部位存在性
        # 2. 計算平倉參數
        # 3. 執行平倉下單 (sNewClose=1)
        # 4. 更新資料庫記錄
        
    def validate_close_order(self, position_record: dict, 
                           close_params: CloseOrderParams) -> bool:
        """驗證平倉訂單合法性"""
        
    def update_position_status(self, position_id: int, 
                             close_result: CloseResult) -> bool:
        """更新部位狀態"""
```

## 🔗 **系統整合規格**

### **simple_integrated.py 修改規格**

#### **新增導入**
```python
# 實際下單功能導入
from real_time_quote_manager import RealTimeQuoteManager
from fok_order_executor import FOKOrderExecutor
from multi_lot_order_manager import MultiLotOrderManager
from order_tracking_system import OrderTrackingSystem
from intelligent_retry_manager import IntelligentRetryManager
from multi_group_close_integrator import MultiGroupCloseIntegrator
```

#### **初始化修改**
```python
def init_real_order_system(self):
    """初始化實際下單系統"""
    # 1. 初始化報價管理器
    self.real_time_quote_manager = RealTimeQuoteManager()
    
    # 2. 初始化下單組件
    self.fok_order_executor = FOKOrderExecutor(
        quote_manager=self.real_time_quote_manager,
        order_api=self.order_api
    )
    
    # 3. 初始化追蹤系統
    self.order_tracking_system = OrderTrackingSystem(
        db_manager=self.multi_group_db_manager
    )
    
    # 4. 初始化重試管理器
    self.retry_manager = IntelligentRetryManager(
        quote_manager=self.real_time_quote_manager,
        order_executor=self.fok_order_executor,
        tracking_system=self.order_tracking_system
    )
    
    # 5. 初始化多口管理器
    self.multi_lot_manager = MultiLotOrderManager(
        fok_executor=self.fok_order_executor,
        tracking_system=self.order_tracking_system,
        retry_manager=self.retry_manager
    )
    
    # 6. 初始化平倉整合器
    self.close_integrator = MultiGroupCloseIntegrator(
        position_manager=self.multi_group_position_manager,
        order_executor=self.fok_order_executor,
        db_manager=self.multi_group_db_manager
    )
```

#### **事件處理修改**
```python
def OnNotifyBest5LONG(self, sMarketNo, nStockidx, nBestBid1, nBestBidQty1, ...):
    """五檔報價事件 - 整合實際下單"""
    try:
        # 原有邏輯...
        
        # 新增: 更新即時報價管理器
        if hasattr(self, 'real_time_quote_manager'):
            self.real_time_quote_manager.update_best5_data(
                market_no=sMarketNo,
                stock_idx=nStockidx,
                ask1=nBestAsk1, ask1_qty=nBestAskQty1,
                ask2=nBestAsk2, ask2_qty=nBestAskQty2,
                ask3=nBestAsk3, ask3_qty=nBestAskQty3,
                ask4=nBestAsk4, ask4_qty=nBestAskQty4,
                ask5=nBestAsk5, ask5_qty=nBestAskQty5,
                bid1=nBestBid1, bid1_qty=nBestBidQty1,
                bid2=nBestBid2, bid2_qty=nBestBidQty2,
                bid3=nBestBid3, bid3_qty=nBestBidQty3,
                bid4=nBestBid4, bid4_qty=nBestBidQty4,
                bid5=nBestBid5, bid5_qty=nBestBidQty5
            )
            
    except Exception as e:
        # 錯誤處理...
        pass

def OnNewData(self, bstrLogInID, bstrData):
    """委託回報事件 - 整合訂單追蹤"""
    try:
        # 原有邏輯...
        
        # 新增: 訂單追蹤處理
        if hasattr(self, 'order_tracking_system'):
            # 解析回報數據
            data_fields = bstrData.split(',')
            if len(data_fields) >= 48:
                seq_no = data_fields[47]        # SeqNo
                order_type = data_fields[2]     # Type
                order_err = data_fields[3]      # OrderErr
                
                # 處理訂單回報
                self.order_tracking_system.process_order_report(
                    seq_no=seq_no,
                    order_type=order_type,
                    order_err=order_err,
                    order_data=bstrData
                )
                
    except Exception as e:
        # 錯誤處理...
        pass
```

## 📊 **性能與可靠性規格**

### **性能指標**
- **報價更新延遲**: < 10ms
- **下單執行時間**: < 100ms
- **訂單追蹤響應**: < 50ms
- **重試決策時間**: < 200ms
- **平倉執行時間**: < 150ms

### **可靠性指標**
- **下單成功率**: > 95%
- **重試成功率**: > 80%
- **數據同步準確率**: 100%
- **系統可用性**: > 99%
- **錯誤恢復時間**: < 5秒

### **容錯機制**
- **網路中斷恢復**: 自動重連機制
- **API錯誤處理**: 分類錯誤處理
- **數據不一致**: 自動同步修正
- **系統異常**: 緊急停止保護

---

**📝 文檔版本**: v1.0  
**🎯 狀態**: 技術規格完成  
**📅 更新時間**: 2025-07-04
