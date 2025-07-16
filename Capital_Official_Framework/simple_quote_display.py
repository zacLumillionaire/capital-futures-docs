#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
簡單報價顯示測試
確保報價持續跳動和時間顯示正常
"""

import os
import sys
import time
from datetime import datetime

print("🚀 簡單報價顯示測試")
print("=" * 50)

# 設置虛擬報價機路徑
virtual_quote_path = os.path.join(os.path.dirname(__file__), '虛擬報價機')
sys.path.insert(0, virtual_quote_path)

# 導入虛擬報價機模組
import Global

class SimpleQuoteDisplay:
    """簡單報價顯示器"""
    def __init__(self):
        self.quote_count = 0
        self.current_price = 0
        self.current_bid = 0
        self.current_ask = 0
        self.start_time = datetime.now()
        
    def OnNotifyTicksLONG(self, sMarketNo, nStockidx, nPtr, lDate, lTimehms, 
                         lTimemillismicros, nBid, nAsk, nClose, nQty, nSimulate):
        """報價處理"""
        # 轉換價格
        price = nClose / 100.0
        bid = nBid / 100.0
        ask = nAsk / 100.0
        
        self.current_price = price
        self.current_bid = bid
        self.current_ask = ask
        self.quote_count += 1
        
        # 顯示報價
        current_time = datetime.now()
        runtime = current_time - self.start_time
        
        print(f"📊 [{current_time.strftime('%Y-%m-%d %H:%M:%S')}] "
              f"報價#{self.quote_count}: {price:.1f} "
              f"(買:{bid:.1f} 賣:{ask:.1f}) "
              f"運行時間: {str(runtime).split('.')[0]}")

def main():
    """主程式"""
    print("🎯 測試目標:")
    print("   ✅ 確認報價持續跳動")
    print("   ✅ 確認實時時間顯示")
    print("   ✅ 確認24小時運作")
    print()
    
    # 初始化顯示器
    display = SimpleQuoteDisplay()
    
    # 註冊事件處理器
    Global.register_quote_handler(display)
    print("✅ 報價處理器註冊完成")
    
    # 啟動虛擬報價機
    print("🚀 啟動虛擬報價機...")
    Global.skQ.SKQuoteLib_RequestTicks(0, "MTX00")
    Global.start_virtual_machine()
    print("✅ 虛擬報價機啟動完成")
    
    print("\n🔍 開始報價顯示測試...")
    print("⏹️  按 Ctrl+C 停止測試")
    print("-" * 60)
    
    try:
        # 主循環
        while True:
            time.sleep(0.1)
            
    except KeyboardInterrupt:
        print("\n\n🛑 用戶中斷測試")
        
    finally:
        # 停止虛擬報價機
        Global.stop_virtual_machine()
        print("\n✅ 虛擬報價機已停止")
        print(f"📊 總計接收報價: {display.quote_count} 筆")
        print(f"📊 最後價格: {display.current_price:.1f}")
        print("\n🎉 報價顯示測試完成")

if __name__ == "__main__":
    main()
