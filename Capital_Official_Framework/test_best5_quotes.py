#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
五檔報價功能測試
驗證虛擬報價機的五檔報價功能
"""

import os
import sys
import time
from datetime import datetime

print("🚀 五檔報價功能測試")
print("=" * 50)

# 設置虛擬報價機路徑
virtual_quote_path = os.path.join(os.path.dirname(__file__), '虛擬報價機')
sys.path.insert(0, virtual_quote_path)

# 導入虛擬報價機模組
import Global

class Best5QuoteHandler:
    """五檔報價處理器"""
    def __init__(self):
        self.tick_count = 0
        self.best5_count = 0
        self.start_time = datetime.now()
        
    def OnNotifyTicksLONG(self, sMarketNo, nStockidx, nPtr, lDate, lTimehms, 
                         lTimemillismicros, nBid, nAsk, nClose, nQty, nSimulate):
        """一般報價處理"""
        self.tick_count += 1
        price = nClose / 100.0
        bid = nBid / 100.0
        ask = nAsk / 100.0
        
        current_time = datetime.now()
        print(f"📊 [{current_time.strftime('%H:%M:%S')}] "
              f"#{self.tick_count:03d} 成交:{price:.0f} 買:{bid:.0f} 賣:{ask:.0f}")
    
    def OnNotifyBest5LONG(self, sMarketNo, nStockidx, nPtr, 
                         nBid1, nBidQty1, nBid2, nBidQty2, nBid3, nBidQty3, nBid4, nBidQty4, nBid5, nBidQty5,
                         nAsk1, nAskQty1, nAsk2, nAskQty2, nAsk3, nAskQty3, nAsk4, nAskQty4, nAsk5, nAskQty5, nSimulate):
        """五檔報價處理"""
        self.best5_count += 1
        
        # 轉換價格
        bid1, bid2, bid3, bid4, bid5 = nBid1/100, nBid2/100, nBid3/100, nBid4/100, nBid5/100
        ask1, ask2, ask3, ask4, ask5 = nAsk1/100, nAsk2/100, nAsk3/100, nAsk4/100, nAsk5/100
        
        current_time = datetime.now()
        print(f"\n🏆 [{current_time.strftime('%H:%M:%S')}] 五檔報價 #{self.best5_count:03d}")
        print(f"📈 買盤: {bid5:.0f}({nBidQty5}) {bid4:.0f}({nBidQty4}) {bid3:.0f}({nBidQty3}) {bid2:.0f}({nBidQty2}) {bid1:.0f}({nBidQty1})")
        print(f"📉 賣盤: {ask1:.0f}({nAskQty1}) {ask2:.0f}({nAskQty2}) {ask3:.0f}({nAskQty3}) {ask4:.0f}({nAskQty4}) {ask5:.0f}({nAskQty5})")
        
        # 計算買賣價差
        spread = ask1 - bid1
        print(f"💰 最佳買賣價差: {spread:.0f} 點")
        print("-" * 60)

def main():
    """主程式"""
    print("🎯 測試目標:")
    print("   ✅ 驗證五檔報價功能")
    print("   ✅ 測試追價所需的五檔數據")
    print("   ✅ 確認20秒區間監控")
    print()
    
    # 初始化處理器
    handler = Best5QuoteHandler()
    
    # 註冊事件處理器
    Global.register_quote_handler(handler)
    Global.register_best5_handler(handler)
    print("✅ 報價和五檔處理器註冊完成")
    
    # 啟動虛擬報價機
    print("🚀 啟動虛擬報價機...")
    
    # 訂閱一般報價
    Global.skQ.SKQuoteLib_RequestTicks(0, "MTX00")
    
    # 訂閱五檔報價
    Global.skQ.SKQuoteLib_RequestBest5LONG(0, "MTX00")
    
    Global.start_virtual_machine()
    print("✅ 虛擬報價機啟動完成")
    print("✅ 一般報價和五檔報價已訂閱")
    
    print("\n🔍 開始五檔報價測試...")
    print("📋 測試時間: 30秒")
    print("📊 觀察五檔報價數據，用於追價測試")
    print("⏹️  按 Ctrl+C 提前停止測試")
    print("=" * 60)
    
    try:
        # 測試30秒
        test_duration = 30
        start_time = time.time()
        
        while time.time() - start_time < test_duration:
            time.sleep(0.1)
            
        print(f"\n⏰ 測試時間到 ({test_duration}秒)")
        
    except KeyboardInterrupt:
        print("\n\n🛑 用戶中斷測試")
        
    finally:
        # 停止虛擬報價機
        Global.stop_virtual_machine()
        print("\n✅ 虛擬報價機已停止")
        
        # 顯示統計
        runtime = datetime.now() - handler.start_time
        print(f"\n📈 測試統計:")
        print(f"   一般報價: {handler.tick_count} 筆")
        print(f"   五檔報價: {handler.best5_count} 筆")
        print(f"   測試時間: {str(runtime).split('.')[0]}")
        
        if handler.best5_count > 0:
            print(f"   五檔頻率: {handler.best5_count / runtime.total_seconds():.1f} 次/秒")
            print("✅ 五檔報價功能正常")
        else:
            print("❌ 未接收到五檔報價")
        
        if handler.tick_count > 0:
            print(f"   報價頻率: {handler.tick_count / runtime.total_seconds():.1f} 次/秒")
            print("✅ 一般報價功能正常")
        else:
            print("❌ 未接收到一般報價")
        
        print("\n🎉 五檔報價功能測試完成")
        print("💡 現在您可以使用五檔數據進行追價測試")

if __name__ == "__main__":
    main()
