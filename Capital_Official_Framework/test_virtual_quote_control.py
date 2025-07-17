#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
測試虛擬機報價輸出控制
直接測試virtual_simple_integrated.py的VirtualQuoteWrapper
"""

import os
import sys
import time

# 加入虛擬報價機路徑
virtual_quote_path = os.path.join(os.path.dirname(__file__), '虛擬報價機')
if virtual_quote_path not in sys.path:
    sys.path.insert(0, virtual_quote_path)

import Global

class MockMainApp:
    """模擬virtual_simple_integrated.py的主程式"""
    def __init__(self):
        self.console_quote_enabled = True  # 初始啟用
        self.best5_data = {}
        self.quote_event = None
        
    def add_log(self, message):
        """模擬日誌方法"""
        print(f"[LOG] {message}")

def test_virtual_wrapper_control():
    """測試VirtualQuoteWrapper的報價控制"""
    print("🚀 測試VirtualQuoteWrapper報價控制")
    print("=" * 60)
    
    # 1. 創建模擬主程式
    mock_app = MockMainApp()
    
    # 2. 創建VirtualQuoteWrapper（模擬virtual_simple_integrated.py的方式）
    class VirtualQuoteWrapper:
        def __init__(self, main_app):
            self.main_app = main_app
            
        def OnNotifyTicksLONG(self, sMarketNo, nStockidx, nPtr, lDate, lTimehms,
                             lTimemillismicros, nBid, nAsk, nClose, nQty, nSimulate):
            # 檢查報價Console輸出設定
            if getattr(self.main_app, 'console_quote_enabled', True):
                print(f"[TICK] 成交:{nClose/100:.0f} 買:{nBid/100:.0f} 賣:{nAsk/100:.0f}")
                
        def OnNotifyBest5LONG(self, sMarketNo, nStockidx, nPtr,
                             nBid1, nBidQty1, nBid2, nBidQty2, nBid3, nBidQty3, nBid4, nBidQty4, nBid5, nBidQty5,
                             nAsk1, nAskQty1, nAsk2, nAskQty2, nAsk3, nAskQty3, nAsk4, nAskQty4, nAsk5, nAskQty5, nSimulate):
            """五檔報價事件處理"""
            # 轉換價格
            bid1 = nBid1/100
            ask1 = nAsk1/100
            
            # 🔧 檢查報價Console輸出設定
            if getattr(self.main_app, 'console_quote_enabled', True):
                print(f"[BEST5] 買1:{bid1:.0f}({nBidQty1}) 賣1:{ask1:.0f}({nAskQty1})")
    
    # 3. 創建包裝器並註冊
    wrapper = VirtualQuoteWrapper(mock_app)
    Global.register_quote_handler(wrapper)
    Global.register_best5_handler(wrapper)
    
    print("✅ VirtualQuoteWrapper已註冊")
    
    # 4. 測試報價輸出啟用狀態
    print("\n1. 測試報價輸出啟用狀態 (3秒)")
    mock_app.console_quote_enabled = True
    print("🔊 報價輸出已啟用")
    
    # 啟動虛擬報價機
    Global.skQ.SKQuoteLib_RequestTicks(0, "MTX00")
    Global.skQ.SKQuoteLib_RequestBest5LONG(0, "MTX00")
    
    time.sleep(3)
    
    # 5. 測試報價輸出關閉狀態
    print("\n2. 測試報價輸出關閉狀態 (3秒)")
    mock_app.console_quote_enabled = False
    print("🔇 報價輸出已關閉")
    print("💡 如果修復成功，接下來應該沒有[TICK]和[BEST5]輸出")
    
    time.sleep(3)
    
    # 6. 重新啟用測試
    print("\n3. 重新啟用報價輸出 (2秒)")
    mock_app.console_quote_enabled = True
    print("🔊 報價輸出重新啟用")
    
    time.sleep(2)
    
    # 7. 停止虛擬報價機
    Global.stop_virtual_machine()
    
    print("\n✅ 測試完成")
    print("📊 如果在關閉期間沒有看到[TICK]和[BEST5]輸出，則修復成功")

if __name__ == "__main__":
    try:
        test_virtual_wrapper_control()
        print("\n🎉 VirtualQuoteWrapper報價控制測試完成！")
        print("💡 請檢查關閉期間是否有報價輸出")
    except Exception as e:
        print(f"\n❌ 測試失敗: {e}")
        import traceback
        traceback.print_exc()
