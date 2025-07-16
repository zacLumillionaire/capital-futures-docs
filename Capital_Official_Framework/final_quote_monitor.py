#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
最終版報價監控系統
解決所有報價顯示問題，確保24小時運作
"""

import os
import sys
import time
from datetime import datetime

print("🚀 最終版24小時報價監控系統")
print("🎯 解決報價持續顯示問題")
print("=" * 60)

# 設置虛擬報價機路徑
virtual_quote_path = os.path.join(os.path.dirname(__file__), '虛擬報價機')
sys.path.insert(0, virtual_quote_path)

# 導入虛擬報價機模組
import Global

class FinalQuoteMonitor:
    """最終版報價監控器"""
    def __init__(self):
        self.quote_count = 0
        self.current_price = 0
        self.current_bid = 0
        self.current_ask = 0
        self.start_time = datetime.now()
        self.range_high = 21520
        self.range_low = 21480
        self.breakout_triggered = False
        
        print(f"✅ 監控器初始化完成")
        print(f"📊 監控區間: {self.range_low} - {self.range_high}")
        print(f"⏰ 啟動時間: {self.start_time.strftime('%Y-%m-%d %H:%M:%S')}")
        
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
        
        # 立即顯示報價
        current_time = datetime.now()
        runtime = current_time - self.start_time
        
        # 檢查區間突破
        status = ""
        if price > self.range_high and not self.breakout_triggered:
            status = " 🚨向上突破!"
            self.breakout_triggered = True
        elif price < self.range_low and not self.breakout_triggered:
            status = " 🚨向下突破!"
            self.breakout_triggered = True
        
        print(f"📊 [{current_time.strftime('%H:%M:%S')}] "
              f"#{self.quote_count:03d} 價格:{price:.1f} "
              f"買:{bid:.1f} 賣:{ask:.1f} "
              f"區間:{self.range_low}-{self.range_high} "
              f"運行:{str(runtime).split('.')[0]}{status}")
        
        # 強制刷新輸出
        sys.stdout.flush()

def main():
    """主程式"""
    print("🎯 功能說明:")
    print("   ✅ 每秒顯示實時報價和時間")
    print("   ✅ 24小時持續運作")
    print("   ✅ 自動偵測區間突破")
    print("   ✅ 顯示運行時間統計")
    print()
    
    # 初始化監控器
    monitor = FinalQuoteMonitor()
    
    # 註冊事件處理器
    Global.register_quote_handler(monitor)
    print("✅ 報價處理器註冊完成")
    
    # 啟動虛擬報價機
    print("🚀 啟動虛擬報價機...")
    Global.skQ.SKQuoteLib_RequestTicks(0, "MTX00")
    Global.start_virtual_machine()
    print("✅ 虛擬報價機啟動完成")
    
    print("\n🔍 開始24小時報價監控...")
    print("📋 監控區間: 21480 - 21520")
    print("⏰ 報價時間使用電腦實時時間")
    print("⏹️  按 Ctrl+C 停止監控")
    print("-" * 70)
    
    try:
        # 主循環 - 保持程式運行
        while True:
            time.sleep(0.1)
            
    except KeyboardInterrupt:
        print("\n\n🛑 用戶中斷監控")
        
    finally:
        # 停止虛擬報價機
        Global.stop_virtual_machine()
        print("\n✅ 虛擬報價機已停止")
        
        # 顯示統計
        runtime = datetime.now() - monitor.start_time
        print(f"\n📈 監控統計:")
        print(f"   總報價數: {monitor.quote_count}")
        print(f"   最後價格: {monitor.current_price:.1f}")
        print(f"   總運行時間: {str(runtime).split('.')[0]}")
        print(f"   平均報價頻率: {monitor.quote_count / runtime.total_seconds():.1f} 次/秒")
        
        print("\n🎉 24小時監控系統已安全關閉")

if __name__ == "__main__":
    main()
