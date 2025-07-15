# 虛擬報價機測試腳本 (含五檔功能)
import time
import Global

class TestQuoteHandler:
    def __init__(self):
        self.tick_count = 0
        self.best5_count = 0
    
    def OnNotifyTicksLONG(self, sMarketNo, nStockidx, nPtr, lDate, lTimehms, 
                         lTimemillismicros, nBid, nAsk, nClose, nQty, nSimulate):
        """處理即時報價事件"""
        self.tick_count += 1
        price = nClose / 100.0
        bid = nBid / 100.0
        ask = nAsk / 100.0
        
        print(f"📊 [Test] 即時報價 #{self.tick_count}: {price} (買:{bid} 賣:{ask}) 量:{nQty}")
    
    def OnNotifyBest5LONG(self, sMarketNo, nStockidx, nPtr, lDate, lTimehms,
                         lTimemillismicros, nBestBid1, nBestBidQty1, nBestBid2, 
                         nBestBidQty2, nBestBid3, nBestBidQty3, nBestBid4, 
                         nBestBidQty4, nBestBid5, nBestBidQty5, nBestAsk1, 
                         nBestAskQty1, nBestAsk2, nBestAskQty2, nBestAsk3, 
                         nBestAskQty3, nBestAsk4, nBestAskQty4, nBestAsk5, 
                         nBestAskQty5, nSimulate):
        """處理五檔報價事件"""
        self.best5_count += 1
        
        # 顯示買賣一到三檔
        bid1 = nBestBid1 / 100.0
        bid2 = nBestBid2 / 100.0
        bid3 = nBestBid3 / 100.0
        ask1 = nBestAsk1 / 100.0
        ask2 = nBestAsk2 / 100.0
        ask3 = nBestAsk3 / 100.0
        
        print(f"📈 [Test] 五檔 #{self.best5_count}:")
        print(f"    買三: {bid3}({nBestBidQty3})  賣三: {ask3}({nBestAskQty3})")
        print(f"    買二: {bid2}({nBestBidQty2})  賣二: {ask2}({nBestAskQty2})")
        print(f"    買一: {bid1}({nBestBidQty1})  賣一: {ask1}({nBestAskQty1})")

class TestReplyHandler:
    def __init__(self):
        self.reply_count = 0
    
    def OnNewData(self, user_id, reply_data):
        """處理回報事件"""
        self.reply_count += 1
        fields = reply_data.split(',')
        
        if len(fields) >= 9:
            order_id = fields[0]
            status = fields[8]
            status_text = {"N": "新單", "D": "成交", "C": "取消"}.get(status, status)
            print(f"📋 [Test] 回報 #{self.reply_count}: 訂單:{order_id} 狀態:{status_text}")

class MockOrder:
    def __init__(self):
        self.bstrFullAccount = "F0200006363839"
        self.bstrStockNo = "MTX00"
        self.sBuySell = 0  # 買進
        self.sTradeType = 2  # FOK
        self.nQty = 1
        self.bstrPrice = "21500"

def main():
    print("🚀 虛擬報價機測試 (含五檔功能)")
    print("=" * 50)
    
    # 註冊事件處理器
    quote_handler = TestQuoteHandler()
    reply_handler = TestReplyHandler()
    
    Global.register_quote_handler(quote_handler)
    Global.register_reply_handler(reply_handler)
    
    print("\n1. 測試基本API")
    result = Global.skC.SKCenterLib_Login("test_user", "test_password")
    print(f"登入結果: {result}")
    
    result = Global.skO.SKOrderLib_Initialize()
    print(f"下單初始化: {result}")
    
    print("\n2. 開始即時報價")
    result = Global.skQ.SKQuoteLib_RequestTicks(0, "MTX00")
    print(f"即時報價訂閱: {result}")
    
    print("\n3. 等待即時報價...")
    time.sleep(2)
    
    print(f"\n4. 開始五檔報價")
    result = Global.skQ.SKQuoteLib_RequestBest5LONG(0, "MTX00")
    print(f"五檔報價訂閱: {result}")
    
    print("\n5. 等待五檔報價...")
    time.sleep(3)
    
    print(f"\n6. 測試下單")
    order = MockOrder()
    result = Global.skO.SendFutureOrderCLR("test_user", True, order)
    print(f"下單結果: {result}")
    
    print("\n7. 等待回報...")
    time.sleep(2)
    
    print(f"\n✅ 測試完成")
    print(f"📊 收到即時報價: {quote_handler.tick_count} 筆")
    print(f"📈 收到五檔報價: {quote_handler.best5_count} 筆")
    print(f"📋 收到委託回報: {reply_handler.reply_count} 筆")
    
    Global.stop_virtual_machine()
    print("\n🛑 虛擬報價機已停止")

if __name__ == "__main__":
    main()
