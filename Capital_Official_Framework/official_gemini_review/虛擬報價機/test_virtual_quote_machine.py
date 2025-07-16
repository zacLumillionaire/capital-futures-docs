# 虛擬報價機測試腳本
# Test Script for Virtual Quote Machine

import sys
import os
import time
import threading

# 添加虛擬報價機到路徑
sys.path.insert(0, os.path.dirname(__file__))

# 導入虛擬報價機模組
import Global
from config_manager import ConfigManager
from quote_engine import VirtualQuoteEngine
from event_dispatcher import EventDispatcher
from order_simulator import OrderSimulator

class TestQuoteHandler:
    """測試報價事件處理器"""
    
    def __init__(self):
        self.quote_count = 0
        self.best5_count = 0
    
    def OnNotifyTicksLONG(self, sMarketNo, nStockidx, nPtr, lDate, lTimehms, 
                         lTimemillismicros, nBid, nAsk, nClose, nQty, nSimulate):
        """處理報價事件"""
        self.quote_count += 1
        price = nClose / 100.0
        bid = nBid / 100.0
        ask = nAsk / 100.0
        
        print(f"📊 [Test] 報價 #{self.quote_count}: {price} (買:{bid} 賣:{ask}) 量:{nQty}")
    
    def OnNotifyBest5LONG(self, sMarketNo, nStockidx, nPtr, lDate, lTimehms,
                         lTimemillismicros, nBestBid1, nBestBidQty1, nBestBid2, 
                         nBestBidQty2, nBestBid3, nBestBidQty3, nBestBid4, 
                         nBestBidQty4, nBestBid5, nBestBidQty5, nBestAsk1, 
                         nBestAskQty1, nBestAsk2, nBestAskQty2, nBestAsk3, 
                         nBestAskQty3, nBestAsk4, nBestAskQty4, nBestAsk5, 
                         nBestAskQty5, nSimulate):
        """處理五檔事件"""
        self.best5_count += 1
        bid1 = nBestBid1 / 100.0
        ask1 = nBestAsk1 / 100.0
        
        print(f"📈 [Test] 五檔 #{self.best5_count}: 買一:{bid1}({nBestBidQty1}) 賣一:{ask1}({nBestAskQty1})")

class TestReplyHandler:
    """測試回報事件處理器"""
    
    def __init__(self):
        self.reply_count = 0
    
    def OnConnect(self, user_id, error_code):
        """處理連線事件"""
        print(f"🔗 [Test] 連線事件: {user_id}, 錯誤碼: {error_code}")
    
    def OnNewData(self, user_id, reply_data):
        """處理回報事件"""
        self.reply_count += 1
        fields = reply_data.split(',')
        
        if len(fields) >= 9:
            order_id = fields[0]
            status = fields[8]
            print(f"📋 [Test] 回報 #{self.reply_count}: 訂單:{order_id} 狀態:{status}")

class MockFutureOrder:
    """模擬FUTUREORDER物件"""
    
    def __init__(self):
        self.bstrFullAccount = "F0200006363839"
        self.bstrStockNo = "MTX00"
        self.sBuySell = 0  # 買進
        self.sTradeType = 2  # FOK
        self.nQty = 1
        self.bstrPrice = "21500"
        self.sNewClose = 0  # 新倉
        self.sDayTrade = 1  # 當沖

def test_api_compatibility():
    """測試API兼容性"""
    print("🧪 [Test] 開始API兼容性測試")
    
    # 測試SKCenterLib
    result = Global.skC.SKCenterLib_Login("test_user", "test_password")
    print(f"✅ [Test] 登入結果: {result}")
    
    msg = Global.skC.SKCenterLib_GetReturnCodeMessage(result)
    print(f"✅ [Test] 錯誤訊息: {msg}")
    
    # 測試SKOrderLib
    result = Global.skO.SKOrderLib_Initialize()
    print(f"✅ [Test] 下單初始化: {result}")
    
    result = Global.skO.ReadCertByID("test_user")
    print(f"✅ [Test] 憑證讀取: {result}")
    
    # 測試SKQuoteLib
    result = Global.skQ.SKQuoteLib_EnterMonitorLONG()
    print(f"✅ [Test] 報價連線: {result}")
    
    # 測試SKReplyLib
    result = Global.skR.SKReplyLib_ConnectByID("test_user")
    print(f"✅ [Test] 回報連線: {result}")

def test_quote_engine():
    """測試報價引擎"""
    print("🧪 [Test] 開始報價引擎測試")
    
    # 創建測試處理器
    quote_handler = TestQuoteHandler()
    
    # 註冊事件處理器
    Global.register_quote_handler(quote_handler)
    
    # 啟動報價推送
    result = Global.skQ.SKQuoteLib_RequestTicks(0, "MTX00")
    print(f"✅ [Test] 報價訂閱: {result}")
    
    # 等待報價
    print("⏳ [Test] 等待報價推送...")
    time.sleep(3)
    
    print(f"📊 [Test] 收到報價: {quote_handler.quote_count} 筆")
    print(f"📈 [Test] 收到五檔: {quote_handler.best5_count} 筆")

def test_order_simulator():
    """測試下單模擬器"""
    print("🧪 [Test] 開始下單模擬器測試")
    
    # 創建測試處理器
    reply_handler = TestReplyHandler()
    
    # 註冊事件處理器
    Global.register_reply_handler(reply_handler)
    
    # 測試下單
    order = MockFutureOrder()
    result = Global.skO.SendFutureOrderCLR("test_user", True, order)
    print(f"✅ [Test] 下單結果: {result}")
    
    # 等待回報
    print("⏳ [Test] 等待回報...")
    time.sleep(2)
    
    print(f"📋 [Test] 收到回報: {reply_handler.reply_count} 筆")

def test_statistics():
    """測試統計資訊"""
    print("🧪 [Test] 統計資訊測試")
    
    # 取得各模組統計
    quote_engine = Global.get_quote_engine()
    if quote_engine:
        stats = quote_engine.get_statistics()
        print(f"📊 [Test] 報價引擎統計: {stats}")
    
    order_simulator = Global.get_order_simulator()
    if order_simulator:
        stats = order_simulator.get_statistics()
        print(f"📋 [Test] 下單模擬器統計: {stats}")
    
    event_dispatcher = Global.get_event_dispatcher()
    if event_dispatcher:
        stats = event_dispatcher.get_statistics()
        print(f"📡 [Test] 事件分發器統計: {stats}")

def main():
    """主測試函數"""
    print("🚀 [Test] 虛擬報價機測試開始")
    print("=" * 50)
    
    try:
        # 1. API兼容性測試
        test_api_compatibility()
        print()
        
        # 2. 報價引擎測試
        test_quote_engine()
        print()
        
        # 3. 下單模擬器測試
        test_order_simulator()
        print()
        
        # 4. 統計資訊測試
        test_statistics()
        print()
        
        print("✅ [Test] 所有測試完成")
        
    except Exception as e:
        print(f"❌ [Test] 測試失敗: {e}")
        import traceback
        traceback.print_exc()
    
    finally:
        # 停止虛擬報價機
        Global.stop_virtual_machine()
        print("🛑 [Test] 虛擬報價機已停止")

if __name__ == "__main__":
    main()
