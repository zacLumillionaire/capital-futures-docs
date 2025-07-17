#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
測試五檔報價修復
"""

import os
import sys
import time

# 加入虛擬報價機路徑
virtual_quote_path = os.path.join(os.path.dirname(__file__), '虛擬報價機')
if virtual_quote_path not in sys.path:
    sys.path.insert(0, virtual_quote_path)

from config_manager import ConfigManager
from quote_engine import VirtualQuoteEngine
from event_dispatcher import EventDispatcher

class TestBest5Handler:
    """測試五檔報價處理器"""
    
    def __init__(self):
        self.best5_count = 0
        
    def OnNotifyBest5LONG(self, sMarketNo, nStockidx, 
                         nBestBid1, nBestBidQty1, nBestBid2, nBestBidQty2, 
                         nBestBid3, nBestBidQty3, nBestBid4, nBestBidQty4, 
                         nBestBid5, nBestBidQty5, nExtendBid, nExtendBidQty, 
                         nBestAsk1, nBestAskQty1, nBestAsk2, nBestAskQty2, 
                         nBestAsk3, nBestAskQty3, nBestAsk4, nBestAskQty4, 
                         nBestAsk5, nBestAskQty5, nExtendAsk, nExtendAskQty, 
                         nSimulate):
        """處理五檔報價事件"""
        self.best5_count += 1
        
        # 轉換價格 (除以100)
        bid1 = nBestBid1 / 100
        ask1 = nBestAsk1 / 100
        
        print(f"📈 [五檔] #{self.best5_count} - BID1:{bid1}({nBestBidQty1}) ASK1:{ask1}({nBestAskQty1})")
        
        # 每5次顯示完整五檔
        if self.best5_count % 5 == 0:
            print(f"📊 [完整五檔] 買方: {nBestBid1/100}({nBestBidQty1}) {nBestBid2/100}({nBestBidQty2}) {nBestBid3/100}({nBestBidQty3})")
            print(f"📊 [完整五檔] 賣方: {nBestAsk1/100}({nBestAskQty1}) {nBestAsk2/100}({nBestAskQty2}) {nBestAsk3/100}({nBestAskQty3})")

def test_best5_fix():
    """測試五檔報價修復"""
    print("🚀 開始五檔報價修復測試")
    print("=" * 50)
    
    # 1. 初始化組件
    print("\n1. 初始化組件")
    config_manager = ConfigManager()
    event_dispatcher = EventDispatcher()
    quote_engine = VirtualQuoteEngine(config_manager, event_dispatcher)
    
    # 2. 註冊五檔處理器
    best5_handler = TestBest5Handler()
    event_dispatcher.register_quote_handler(best5_handler)
    
    # 3. 啟動組件
    event_dispatcher.start()
    
    print("✅ 組件初始化完成")
    
    # 4. 啟動報價推送
    print("\n2. 啟動報價推送")
    quote_engine.start_quote_feed("MTX00")
    
    print("✅ 報價推送已啟動")
    
    # 5. 運行測試
    print("\n3. 運行五檔報價測試 (10秒)")
    print("🎯 檢查是否還有參數錯誤")
    
    start_time = time.time()
    test_duration = 10
    
    while time.time() - start_time < test_duration:
        time.sleep(1)
        elapsed = int(time.time() - start_time)
        print(f"⏰ 測試進行中... {elapsed}/{test_duration}秒")
    
    # 6. 停止報價
    quote_engine.stop()
    
    # 7. 顯示結果
    print("\n4. 測試結果")
    print("=" * 50)
    print(f"📊 五檔報價接收數量: {best5_handler.best5_count}")
    
    if best5_handler.best5_count > 0:
        print("✅ 五檔報價修復成功！")
        print("   沒有參數錯誤，事件正常處理")
        return True
    else:
        print("⚠️ 五檔報價沒有接收到")
        return False

if __name__ == "__main__":
    try:
        success = test_best5_fix()
        if success:
            print("\n🎉 五檔報價修復驗證成功！")
        else:
            print("\n⚠️ 五檔報價需要進一步檢查")
    except Exception as e:
        print(f"\n❌ 測試失敗: {e}")
        import traceback
        traceback.print_exc()
