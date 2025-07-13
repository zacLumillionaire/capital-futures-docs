# 虛擬報價機 Global 模組
# 提供與群益API相同介面的模擬器
# 
# 此模組替換 order_service.Global，提供完全相同的API介面
# 讓 simple_integrated.py 無需修改即可使用虛擬報價機

import time
import threading
import random
from datetime import datetime

class SimpleVirtualQuote:
    """簡化版虛擬報價機 - 只做核心功能"""
    
    def __init__(self):
        # 報價參數
        self.base_price = 21500
        self.current_price = self.base_price
        self.spread = 5  # 買賣價差
        self.running = False
        self.quote_thread = None
        
        # 事件處理器
        self.quote_handlers = []
        self.reply_handlers = []
        
        # 下單計數器
        self.order_counter = 0
        
        print("✅ [Virtual] 簡化版虛擬報價機初始化完成")
    
    def register_quote_handler(self, handler):
        """註冊報價事件處理器"""
        self.quote_handlers.append(handler)
        print(f"📝 [Virtual] 註冊報價處理器: {type(handler).__name__}")
    
    def register_reply_handler(self, handler):
        """註冊回報事件處理器"""
        self.reply_handlers.append(handler)
        print(f"📝 [Virtual] 註冊回報處理器: {type(handler).__name__}")
    
    def start_quote_feed(self):
        """開始報價推送"""
        if self.running:
            return
        
        self.running = True
        self.quote_thread = threading.Thread(target=self._quote_loop, daemon=True)
        self.quote_thread.start()
        print("🚀 [Virtual] 報價推送已啟動")
    
    def stop_quote_feed(self):
        """停止報價推送"""
        self.running = False
        print("🛑 [Virtual] 報價推送已停止")
    
    def _quote_loop(self):
        """報價推送主循環"""
        while self.running:
            try:
                # 生成新價格 (隨機波動)
                change = random.randint(-20, 20)
                self.current_price = max(21400, min(21600, self.current_price + change))
                
                # 計算買賣價
                bid_price = self.current_price - self.spread // 2
                ask_price = self.current_price + self.spread // 2
                
                # 生成時間戳
                now = datetime.now()
                date = int(now.strftime('%Y%m%d'))
                time_hms = int(now.strftime('%H%M%S'))
                time_ms = now.microsecond // 1000
                
                # 推送報價事件
                for handler in self.quote_handlers:
                    if hasattr(handler, 'OnNotifyTicksLONG'):
                        handler.OnNotifyTicksLONG(
                            1,  # sMarketNo
                            0,  # nStockidx
                            0,  # nPtr
                            date,  # lDate
                            time_hms,  # lTimehms
                            time_ms,  # lTimemillismicros
                            bid_price * 100,  # nBid (*100)
                            ask_price * 100,  # nAsk (*100)
                            self.current_price * 100,  # nClose (*100)
                            random.randint(1, 5),  # nQty
                            0  # nSimulate
                        )
                
                # 等待0.5秒
                time.sleep(0.5)
                
            except Exception as e:
                print(f"❌ [Virtual] 報價循環錯誤: {e}")
                time.sleep(0.1)
    
    def process_order(self, user_id, async_flag, order_obj):
        """處理下單請求"""
        try:
            # 生成委託序號
            self.order_counter += 1
            order_id = f"VQ{self.order_counter:08d}"
            
            # 解析下單參數
            account = getattr(order_obj, 'bstrFullAccount', 'F0200006363839')
            product = getattr(order_obj, 'bstrStockNo', 'MTX00')
            buy_sell = getattr(order_obj, 'sBuySell', 0)
            price = int(getattr(order_obj, 'bstrPrice', '21500'))
            quantity = getattr(order_obj, 'nQty', 1)
            
            print(f"📋 [Virtual] 收到下單: {order_id} - {'買進' if buy_sell == 0 else '賣出'} {product} {quantity}口 @{price}")
            
            # 異步處理成交
            threading.Thread(target=self._process_fill, args=(order_id, account, product, buy_sell, price, quantity), daemon=True).start()
            
            return (order_id, 0)  # 立即返回成功
            
        except Exception as e:
            print(f"❌ [Virtual] 下單處理失敗: {e}")
            return ("", -1)
    
    def _process_fill(self, order_id, account, product, buy_sell, price, quantity):
        """處理成交"""
        try:
            # 1. 發送新單回報
            time.sleep(0.05)  # 50ms後
            self._send_reply(order_id, account, product, buy_sell, price, quantity, "N", 0, 0)
            
            # 2. 決定是否成交 (95%成交率)
            if random.random() < 0.95:
                # 成交
                time.sleep(0.15)  # 再等150ms
                fill_price = price  # 簡化：使用委託價成交
                self._send_reply(order_id, account, product, buy_sell, price, quantity, "D", fill_price, quantity)
                print(f"✅ [Virtual] 訂單成交: {order_id} @ {fill_price}")
            else:
                # 取消
                time.sleep(0.15)
                self._send_reply(order_id, account, product, buy_sell, price, quantity, "C", 0, 0)
                print(f"❌ [Virtual] 訂單取消: {order_id}")
                
        except Exception as e:
            print(f"❌ [Virtual] 成交處理錯誤: {e}")
    
    def _send_reply(self, order_id, account, product, buy_sell, price, quantity, status, fill_price, fill_qty):
        """發送回報"""
        now = datetime.now()
        
        # 生成回報數據 (逗號分隔格式)
        reply_data = ",".join([
            order_id,                    # [0] 委託序號
            account,                     # [1] 帳號
            product,                     # [2] 商品代碼
            str(buy_sell),               # [3] 買賣別
            str(price),                  # [4] 委託價格
            str(quantity),               # [5] 委託數量
            str(fill_price),             # [6] 成交價格
            str(fill_qty),               # [7] 成交數量
            status,                      # [8] 委託狀態 (N=新單, D=成交, C=取消)
            now.strftime('%H%M%S'),      # [9] 委託時間
            "0",                         # [10] 錯誤代碼
            "",                          # [11] 錯誤訊息
            "2",                         # [12] 委託類型 (FOK)
            "0",                         # [13] 新平倉
            "1",                         # [14] 當沖
            "Virtual"                    # [15] 來源
        ])
        
        # 推送回報事件
        for handler in self.reply_handlers:
            if hasattr(handler, 'OnNewData'):
                handler.OnNewData("virtual_user", reply_data)

# 全域實例
_virtual_quote = SimpleVirtualQuote()

# 模擬群益API物件
class MockSKCenterLib:
    def SKCenterLib_Login(self, user_id, password):
        print(f"🎯 [Virtual] 模擬登入: {user_id}")
        return 0
    
    def SKCenterLib_GetReturnCodeMessage(self, code):
        return "成功" if code == 0 else f"錯誤代碼: {code}"
    
    def SKCenterLib_SetLogPath(self, path):
        return 0

class MockSKOrderLib:
    def SKOrderLib_Initialize(self):
        print("🎯 [Virtual] 模擬下單初始化")
        return 0
    
    def ReadCertByID(self, user_id):
        print(f"🎯 [Virtual] 模擬憑證讀取: {user_id}")
        return 0
    
    def SendFutureOrderCLR(self, user_id, async_flag, order_obj):
        return _virtual_quote.process_order(user_id, async_flag, order_obj)

class MockSKQuoteLib:
    def SKQuoteLib_EnterMonitorLONG(self):
        print("🎯 [Virtual] 模擬報價連線")
        return 0
    
    def SKQuoteLib_RequestTicks(self, page, product):
        print(f"🎯 [Virtual] 開始報價推送: {product}")
        _virtual_quote.start_quote_feed()
        return 0
    
    def SKQuoteLib_RequestBest5LONG(self, page, product):
        print(f"🎯 [Virtual] 模擬五檔訂閱: {product}")
        return 0

class MockSKReplyLib:
    def SKReplyLib_ConnectByID(self, user_id):
        print(f"🎯 [Virtual] 模擬回報連線: {user_id}")
        return 0

# 全域API物件 (與原始Global模組保持一致)
skC = MockSKCenterLib()
skO = MockSKOrderLib()
skQ = MockSKQuoteLib()
skR = MockSKReplyLib()

# 額外的模擬物件 (保持兼容性)
skOSQ = None  # 海期報價 (暫不實現)
skOOQ = None  # 海選報價 (暫不實現)

# 全域ID變數 (與原始Global模組保持一致)
Global_IID = None

def SetID(id):
    """設定全域ID (與原始API保持一致)"""
    global Global_IID
    Global_IID = id
    print(f"🎯 [Virtual] SetID: {Global_IID}")

# 事件處理器註冊函數
def register_quote_handler(handler):
    """註冊報價事件處理器"""
    _virtual_quote.register_quote_handler(handler)

def register_reply_handler(handler):
    """註冊回報事件處理器"""
    _virtual_quote.register_reply_handler(handler)

def start_virtual_machine():
    """啟動虛擬報價機"""
    _virtual_quote.start_quote_feed()
    print("🚀 [Virtual] 虛擬報價機已啟動")

def stop_virtual_machine():
    """停止虛擬報價機"""
    _virtual_quote.stop_quote_feed()
    print("🛑 [Virtual] 虛擬報價機已停止")

# 模組初始化
print("📦 [Virtual] Global 模組載入完成")
print("🎯 [Virtual] 虛擬報價機 API 模擬器就緒")
print("💡 [Virtual] 核心功能: 報價推送 + 下單成交模擬")
