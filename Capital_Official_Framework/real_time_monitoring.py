#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
實時報價監控與交易觀察系統
24小時運作，持續顯示報價和時間，支援區間監控和交易流程觀察
"""

import os
import sys
import time
import threading
from datetime import datetime
from collections import deque

print("🚀 啟動實時報價監控與交易觀察系統")
print("=" * 60)

# 設置虛擬報價機路徑
virtual_quote_path = os.path.join(os.path.dirname(__file__), '虛擬報價機')
sys.path.insert(0, virtual_quote_path)

# 導入虛擬報價機模組
import Global
from multi_group_database import MultiGroupDatabaseManager

class RealTimeMonitor:
    """實時監控系統"""
    def __init__(self):
        self.quotes = deque(maxlen=100)  # 保留最近100筆報價
        self.current_price = 0
        self.current_bid = 0
        self.current_ask = 0
        self.price_high = 0
        self.price_low = float('inf')
        self.quote_count = 0
        self.start_time = datetime.now()
        
        # 區間監控設定
        self.range_high = 21520  # 區間上緣
        self.range_low = 21480   # 區間下緣
        self.breakout_triggered = False
        
        # 交易狀態
        self.position_opened = False
        self.entry_price = 0
        self.entry_time = None
        
        # 顯示控制
        self.last_display_time = 0
        self.display_interval = 1  # 每秒顯示一次
        
    def OnNotifyTicksLONG(self, sMarketNo, nStockidx, nPtr, lDate, lTimehms, 
                         lTimemillismicros, nBid, nAsk, nClose, nQty, nSimulate):
        """報價處理"""
        # 轉換價格 (除以100)
        price = nClose / 100.0
        bid = nBid / 100.0
        ask = nAsk / 100.0
        
        # 更新當前價格
        self.current_price = price
        self.current_bid = bid
        self.current_ask = ask
        self.quote_count += 1
        
        # 更新價格區間
        if price > self.price_high:
            self.price_high = price
        if price < self.price_low:
            self.price_low = price
        
        # 記錄報價
        quote_data = {
            'time': datetime.now(),
            'price': price,
            'bid': bid,
            'ask': ask,
            'date': lDate,
            'time_hms': lTimehms
        }
        self.quotes.append(quote_data)
        
        # 檢查區間突破
        self.check_range_breakout(price)
        
        # 控制顯示頻率
        current_time = time.time()
        if current_time - self.last_display_time >= self.display_interval:
            self.display_real_time_info()
            self.last_display_time = current_time
    
    def OnNewData(self, user_id, reply_data):
        """回報處理"""
        fields = reply_data.split(',')
        order_id = fields[0]
        status = fields[8]
        
        current_time = datetime.now().strftime('%H:%M:%S')
        
        if status == 'N':  # 新單
            print(f"\n📋 [{current_time}] 新單回報: {order_id}")
        elif status == 'D':  # 成交
            if not self.position_opened:
                self.position_opened = True
                self.entry_price = self.current_price
                self.entry_time = datetime.now()
                print(f"\n🎉 [{current_time}] 建倉成交: {order_id} @ {self.entry_price}")
                print(f"    進場時間: {self.entry_time.strftime('%H:%M:%S')}")
            else:
                exit_price = self.current_price
                profit = exit_price - self.entry_price
                duration = datetime.now() - self.entry_time
                print(f"\n✅ [{current_time}] 平倉成交: {order_id} @ {exit_price}")
                print(f"    損益: {profit:.1f} 點")
                print(f"    持倉時間: {duration}")
                # 重置狀態
                self.position_opened = False
                self.entry_price = 0
                self.entry_time = None
        elif status == 'C':  # 取消
            print(f"\n❌ [{current_time}] 訂單取消: {order_id}")
    
    def check_range_breakout(self, price):
        """檢查區間突破"""
        if not self.breakout_triggered:
            if price > self.range_high:
                self.breakout_triggered = True
                print(f"\n🚨 向上突破！價格 {price} 突破區間上緣 {self.range_high}")
                print(f"    時間: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
                # 這裡可以觸發建倉邏輯
                self.trigger_entry_signal("LONG", price)
            elif price < self.range_low:
                self.breakout_triggered = True
                print(f"\n🚨 向下突破！價格 {price} 跌破區間下緣 {self.range_low}")
                print(f"    時間: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
                # 這裡可以觸發建倉邏輯
                self.trigger_entry_signal("SHORT", price)
    
    def trigger_entry_signal(self, direction, price):
        """觸發進場信號"""
        try:
            class EntryOrder:
                def __init__(self, direction, price):
                    self.bstrFullAccount = "F0200006363839"
                    self.bstrStockNo = "MTX00"
                    self.sBuySell = 0 if direction == "LONG" else 1
                    self.sTradeType = 2  # FOK
                    self.nQty = 1
                    # 追價策略：多單加2點，空單減2點
                    if direction == "LONG":
                        self.bstrPrice = str(int(price + 2))
                    else:
                        self.bstrPrice = str(int(price - 2))
            
            order = EntryOrder(direction, price)
            result = Global.skO.SendFutureOrderCLR("monitor_user", True, order)
            
            print(f"📤 發送{direction}進場單: {order.bstrPrice} (追價)")
            print(f"    訂單結果: {result}")
            
        except Exception as e:
            print(f"❌ 發送進場單失敗: {e}")
    
    def display_real_time_info(self):
        """顯示實時信息"""
        current_time = datetime.now()
        runtime = current_time - self.start_time
        
        # 清除上一行（在終端中）
        print(f"\r📊 [{current_time.strftime('%Y-%m-%d %H:%M:%S')}] "
              f"價格: {self.current_price:.1f} "
              f"(買:{self.current_bid:.1f} 賣:{self.current_ask:.1f}) "
              f"| 區間: {self.range_low}-{self.range_high} "
              f"| 高低: {self.price_high:.1f}/{self.price_low:.1f} "
              f"| 報價數: {self.quote_count} "
              f"| 運行: {str(runtime).split('.')[0]}", end="")
        
        # 如果有持倉，顯示持倉信息
        if self.position_opened:
            profit = self.current_price - self.entry_price
            hold_time = datetime.now() - self.entry_time
            print(f" | 🔥 持倉: {profit:+.1f}點 ({str(hold_time).split('.')[0]})", end="")
    
    def display_summary(self):
        """顯示統計摘要"""
        print(f"\n\n📈 監控統計摘要:")
        print(f"   總報價數: {self.quote_count}")
        print(f"   價格區間: {self.price_low:.1f} - {self.price_high:.1f}")
        print(f"   當前價格: {self.current_price:.1f}")
        print(f"   監控區間: {self.range_low} - {self.range_high}")
        print(f"   突破狀態: {'已觸發' if self.breakout_triggered else '未觸發'}")
        print(f"   持倉狀態: {'有持倉' if self.position_opened else '無持倉'}")

def main():
    """主程式"""
    print("🎯 系統功能:")
    print("   ✅ 24小時實時報價監控")
    print("   ✅ 區間突破自動偵測")
    print("   ✅ 自動建倉平倉流程")
    print("   ✅ 實時損益計算")
    print("   ✅ 完整時間戳記錄")
    print()
    
    # 初始化監控系統
    monitor = RealTimeMonitor()
    
    # 註冊事件處理器
    Global.register_quote_handler(monitor)
    Global.register_reply_handler(monitor)
    print("✅ 監控系統註冊完成")
    
    # 啟動虛擬報價機
    Global.skQ.SKQuoteLib_RequestTicks(0, "MTX00")
    Global.start_virtual_machine()
    print("✅ 虛擬報價機啟動完成")
    print()
    
    print("🔍 開始實時監控...")
    print("📋 監控區間: 21480 - 21520 (突破後自動建倉)")
    print("⏹️  按 Ctrl+C 停止監控")
    print("-" * 80)
    
    try:
        # 主監控循環
        while True:
            time.sleep(0.1)  # 短暫休眠，讓CPU不會100%
            
    except KeyboardInterrupt:
        print("\n\n🛑 用戶中斷監控")
        
    finally:
        # 停止虛擬報價機
        Global.stop_virtual_machine()
        print("\n✅ 虛擬報價機已停止")
        
        # 顯示最終統計
        monitor.display_summary()
        
        print("\n🎉 監控系統已安全關閉")

if __name__ == "__main__":
    main()
