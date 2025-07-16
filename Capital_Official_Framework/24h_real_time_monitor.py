#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
24小時實時報價監控系統
解決問題：
1. 報價持續跳動顯示
2. 顯示實時電腦時間
3. 24小時運作
4. 區間監控和交易流程觀察
5. 建倉平倉完整流程
"""

import os
import sys
import time
import threading
from datetime import datetime
from collections import deque

print("🚀 啟動24小時實時報價監控系統")
print("🎯 解決報價持續顯示、實時時間、區間監控、交易流程問題")
print("=" * 70)

# 設置虛擬報價機路徑
virtual_quote_path = os.path.join(os.path.dirname(__file__), '虛擬報價機')
sys.path.insert(0, virtual_quote_path)

# 導入虛擬報價機模組
import Global

class ContinuousQuoteMonitor:
    """持續報價監控器"""
    def __init__(self):
        self.quotes = deque(maxlen=1000)  # 保留最近1000筆報價
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
        self.positions = []  # 持倉記錄
        self.orders = []     # 訂單記錄
        
        # 顯示控制
        self.running = True
        self.display_thread = None
        
        print(f"✅ 監控器初始化完成")
        print(f"📊 監控區間: {self.range_low} - {self.range_high}")
        print(f"⏰ 啟動時間: {self.start_time.strftime('%Y-%m-%d %H:%M:%S')}")
        
    def OnNotifyTicksLONG(self, sMarketNo, nStockidx, nPtr, lDate, lTimehms, 
                         lTimemillismicros, nBid, nAsk, nClose, nQty, nSimulate):
        """報價處理 - 每次報價都會調用"""
        # 轉換價格
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
        
        # 記錄報價（帶時間戳）
        quote_data = {
            'time': datetime.now(),
            'price': price,
            'bid': bid,
            'ask': ask,
            'count': self.quote_count
        }
        self.quotes.append(quote_data)
        
        # 檢查區間突破
        self.check_range_breakout(price)
    
    def OnNewData(self, user_id, reply_data):
        """回報處理"""
        fields = reply_data.split(',')
        order_id = fields[0]
        status = fields[8]
        
        order_info = {
            'time': datetime.now(),
            'order_id': order_id,
            'status': status,
            'price': self.current_price,
            'data': reply_data
        }
        self.orders.append(order_info)
        
        # 處理不同狀態
        if status == 'N':  # 新單
            print(f"\n📋 [{datetime.now().strftime('%H:%M:%S')}] 新單: {order_id}")
        elif status == 'D':  # 成交
            self.handle_fill(order_id, order_info)
        elif status == 'C':  # 取消
            print(f"\n❌ [{datetime.now().strftime('%H:%M:%S')}] 取消: {order_id}")
    
    def handle_fill(self, order_id, order_info):
        """處理成交"""
        current_time = datetime.now().strftime('%H:%M:%S')
        
        # 檢查是否是新建倉
        open_positions = [p for p in self.positions if p['status'] == 'OPEN']
        
        if not open_positions:
            # 新建倉
            position = {
                'id': len(self.positions) + 1,
                'entry_time': datetime.now(),
                'entry_price': self.current_price,
                'entry_order_id': order_id,
                'status': 'OPEN',
                'direction': 'LONG'  # 假設都是多單
            }
            self.positions.append(position)
            
            print(f"\n🎉 [{current_time}] 建倉成交!")
            print(f"    訂單ID: {order_id}")
            print(f"    進場價格: {self.current_price}")
            print(f"    進場時間: {position['entry_time'].strftime('%H:%M:%S')}")
            print(f"    部位編號: {position['id']}")
            
        else:
            # 平倉
            position = open_positions[0]  # 取第一個開倉部位
            position['exit_time'] = datetime.now()
            position['exit_price'] = self.current_price
            position['exit_order_id'] = order_id
            position['status'] = 'CLOSED'
            
            # 計算損益
            profit = position['exit_price'] - position['entry_price']
            duration = position['exit_time'] - position['entry_time']
            
            print(f"\n✅ [{current_time}] 平倉成交!")
            print(f"    訂單ID: {order_id}")
            print(f"    出場價格: {self.current_price}")
            print(f"    出場時間: {position['exit_time'].strftime('%H:%M:%S')}")
            print(f"    損益: {profit:+.1f} 點")
            print(f"    持倉時間: {str(duration).split('.')[0]}")
            print(f"    部位編號: {position['id']}")
    
    def check_range_breakout(self, price):
        """檢查區間突破"""
        if not self.breakout_triggered:
            if price > self.range_high:
                self.breakout_triggered = True
                self.trigger_entry_signal("LONG", price, "向上突破")
            elif price < self.range_low:
                self.breakout_triggered = True
                self.trigger_entry_signal("SHORT", price, "向下突破")
    
    def trigger_entry_signal(self, direction, price, reason):
        """觸發進場信號"""
        print(f"\n🚨 {reason}！價格 {price} {'突破' if direction == 'LONG' else '跌破'}區間")
        print(f"    時間: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        
        try:
            class EntryOrder:
                def __init__(self, direction, price):
                    self.bstrFullAccount = "F0200006363839"
                    self.bstrStockNo = "MTX00"
                    self.sBuySell = 0 if direction == "LONG" else 1
                    self.sTradeType = 2  # FOK
                    self.nQty = 1
                    # 追價策略
                    if direction == "LONG":
                        self.bstrPrice = str(int(price + 2))
                    else:
                        self.bstrPrice = str(int(price - 2))
            
            order = EntryOrder(direction, price)
            result = Global.skO.SendFutureOrderCLR("monitor_user", True, order)
            
            print(f"📤 發送{direction}進場單: {order.bstrPrice} (追價+2點)")
            print(f"    訂單結果: {result}")
            
        except Exception as e:
            print(f"❌ 發送進場單失敗: {e}")
    
    def start_continuous_display(self):
        """啟動持續顯示"""
        def display_loop():
            while self.running:
                self.display_real_time_info()
                time.sleep(1)  # 每秒更新一次
        
        self.display_thread = threading.Thread(target=display_loop, daemon=True)
        self.display_thread.start()
        print("✅ 持續顯示線程已啟動")
    
    def display_real_time_info(self):
        """顯示實時信息"""
        current_time = datetime.now()
        runtime = current_time - self.start_time
        
        # 計算持倉狀態
        open_positions = len([p for p in self.positions if p['status'] == 'OPEN'])
        closed_positions = len([p for p in self.positions if p['status'] == 'CLOSED'])
        
        # 計算當前損益
        current_pnl = 0
        if open_positions > 0:
            for pos in self.positions:
                if pos['status'] == 'OPEN':
                    current_pnl += self.current_price - pos['entry_price']
        
        # 清除當前行並顯示新信息
        info = (f"\r📊 [{current_time.strftime('%Y-%m-%d %H:%M:%S')}] "
                f"價格: {self.current_price:.1f} "
                f"(買:{self.current_bid:.1f} 賣:{self.current_ask:.1f}) "
                f"| 區間: {self.range_low}-{self.range_high} "
                f"| 高低: {self.price_high:.1f}/{self.price_low:.1f} "
                f"| 報價: {self.quote_count} "
                f"| 運行: {str(runtime).split('.')[0]} "
                f"| 持倉: {open_positions} "
                f"| 已平: {closed_positions}")
        
        if current_pnl != 0:
            info += f" | 損益: {current_pnl:+.1f}點"
        
        print(info, end="", flush=True)
    
    def stop(self):
        """停止監控"""
        self.running = False
        if self.display_thread:
            self.display_thread.join(timeout=1)

def main():
    """主程式"""
    print("🎯 系統功能:")
    print("   ✅ 24小時持續報價顯示")
    print("   ✅ 實時電腦時間顯示")
    print("   ✅ 區間突破自動偵測")
    print("   ✅ 自動建倉平倉流程")
    print("   ✅ 實時損益計算")
    print("   ✅ 完整交易記錄")
    print()
    
    # 初始化監控系統
    monitor = ContinuousQuoteMonitor()
    
    # 註冊事件處理器
    Global.register_quote_handler(monitor)
    Global.register_reply_handler(monitor)
    print("✅ 事件處理器註冊完成")
    
    # 啟動虛擬報價機
    print("🚀 啟動虛擬報價機...")
    Global.skQ.SKQuoteLib_RequestTicks(0, "MTX00")
    Global.start_virtual_machine()
    print("✅ 虛擬報價機啟動完成")
    
    # 啟動持續顯示
    monitor.start_continuous_display()
    
    print("\n🔍 開始24小時實時監控...")
    print("📋 監控區間: 21480 - 21520 (突破後自動建倉)")
    print("⏰ 顯示實時電腦時間")
    print("📊 每秒更新報價和狀態")
    print("⏹️  按 Ctrl+C 停止監控")
    print("-" * 80)
    
    try:
        # 主監控循環
        while True:
            time.sleep(0.1)  # 短暫休眠
            
    except KeyboardInterrupt:
        print("\n\n🛑 用戶中斷監控")
        
    finally:
        # 停止系統
        monitor.stop()
        Global.stop_virtual_machine()
        print("\n✅ 虛擬報價機已停止")
        
        # 顯示最終統計
        print(f"\n📈 監控統計摘要:")
        print(f"   總報價數: {monitor.quote_count}")
        print(f"   價格區間: {monitor.price_low:.1f} - {monitor.price_high:.1f}")
        print(f"   當前價格: {monitor.current_price:.1f}")
        print(f"   總訂單數: {len(monitor.orders)}")
        print(f"   總部位數: {len(monitor.positions)}")
        print(f"   開倉部位: {len([p for p in monitor.positions if p['status'] == 'OPEN'])}")
        print(f"   已平部位: {len([p for p in monitor.positions if p['status'] == 'CLOSED'])}")
        
        # 顯示交易記錄
        if monitor.positions:
            print(f"\n📋 交易記錄:")
            for pos in monitor.positions:
                if pos['status'] == 'CLOSED':
                    profit = pos['exit_price'] - pos['entry_price']
                    duration = pos['exit_time'] - pos['entry_time']
                    print(f"   部位{pos['id']}: {pos['entry_price']:.1f} → {pos['exit_price']:.1f} "
                          f"({profit:+.1f}點) 時間:{str(duration).split('.')[0]}")
                else:
                    print(f"   部位{pos['id']}: {pos['entry_price']:.1f} (持倉中)")
        
        print("\n🎉 24小時監控系統已安全關閉")

if __name__ == "__main__":
    main()
