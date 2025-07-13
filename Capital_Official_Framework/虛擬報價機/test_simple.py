# 簡化版虛擬報價機測試
import time
import simple_virtual_quote as Global

class TestQuoteHandler:
    def __init__(self):
        self.count = 0
    
    def OnNotifyTicksLONG(self, sMarketNo, nStockidx, nPtr, lDate, lTimehms, 
                         lTimemillismicros, nBid, nAsk, nClose, nQty, nSimulate):
        self.count += 1
        price = nClose / 100.0
        bid = nBid / 100.0
        ask = nAsk / 100.0
        print(f"📊 報價 #{self.count}: {price} (買:{bid} 賣:{ask})")

class TestReplyHandler:
    def __init__(self):
        self.count = 0
    
    def OnNewData(self, user_id, reply_data):
        self.count += 1
        fields = reply_data.split(',')
        order_id = fields[0]
        status = fields[8]
        print(f"📋 回報 #{self.count}: {order_id} 狀態:{status}")

class MockOrder:
    def __init__(self):
        self.bstrFullAccount = "F0200006363839"
        self.bstrStockNo = "MTX00"
        self.sBuySell = 0  # 買進
        self.sTradeType = 2  # FOK
        self.nQty = 1
        self.bstrPrice = "21500"

def main():
    print("🚀 簡化版虛擬報價機測試")
    
    # 註冊事件處理器
    quote_handler = TestQuoteHandler()
    reply_handler = TestReplyHandler()
    
    Global.register_quote_handler(quote_handler)
    Global.register_reply_handler(reply_handler)
    
    # 測試API
    print("\n1. 測試登入")
    result = Global.skC.SKCenterLib_Login("test", "test")
    print(f"登入結果: {result}")
    
    print("\n2. 測試下單初始化")
    result = Global.skO.SKOrderLib_Initialize()
    print(f"初始化結果: {result}")
    
    print("\n3. 開始報價")
    result = Global.skQ.SKQuoteLib_RequestTicks(0, "MTX00")
    print(f"報價訂閱結果: {result}")
    
    print("\n4. 等待報價...")
    time.sleep(3)
    
    print(f"\n5. 測試下單")
    order = MockOrder()
    result = Global.skO.SendFutureOrderCLR("test", True, order)
    print(f"下單結果: {result}")
    
    print("\n6. 等待回報...")
    time.sleep(2)
    
    print(f"\n✅ 測試完成 - 收到 {quote_handler.count} 筆報價, {reply_handler.count} 筆回報")
    
    Global.stop_virtual_machine()

if __name__ == "__main__":
    main()
