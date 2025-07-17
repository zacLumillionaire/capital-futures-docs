#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
診斷虛擬機報價來源
檢查策略系統收到固定價格的原因
"""

import os
import sys
import time

# 加入虛擬報價機路徑
virtual_quote_path = os.path.join(os.path.dirname(__file__), '虛擬報價機')
if virtual_quote_path not in sys.path:
    sys.path.insert(0, virtual_quote_path)

import Global

class DiagnosticApp:
    """診斷應用程式"""
    
    def __init__(self):
        self.console_quote_enabled = False  # 關閉報價輸出，專注診斷
        self.strategy_enabled = True
        self.price_count = 0
        self.received_prices = []
        self.last_prices = []  # 記錄最近的價格
        
        # 創建主要的SKQuoteLibEvents
        self.quote_event = self.create_main_quote_event()
        
    def create_main_quote_event(self):
        """創建主要的SKQuoteLibEvents"""
        class SKQuoteLibEvents:
            def __init__(self, parent):
                self.parent = parent
                
            def OnNotifyTicksLONG(self, sMarketNo, nStockidx, nPtr, lDate, lTimehms, 
                                 lTimemillismicros, nBid, nAsk, nClose, nQty, nSimulate):
                """主要報價事件處理器"""
                corrected_price = nClose / 100.0
                time_str = f"{lTimehms:06d}"
                formatted_time = f"{time_str[:2]}:{time_str[2:4]}:{time_str[4:6]}"
                
                # 記錄原始報價數據
                self.parent.received_prices.append({
                    'price': corrected_price,
                    'time': formatted_time,
                    'raw_close': nClose,
                    'bid': nBid / 100.0,
                    'ask': nAsk / 100.0
                })
                
                # 保留最近10筆價格用於分析
                self.parent.last_prices.append(corrected_price)
                if len(self.parent.last_prices) > 10:
                    self.parent.last_prices.pop(0)
                
                # 每5筆顯示一次診斷信息
                if len(self.parent.received_prices) % 5 == 0:
                    print(f"🔍 [DIAG] 第{len(self.parent.received_prices)}筆報價: {corrected_price:.0f} @{formatted_time}")
                    print(f"🔍 [DIAG] 最近5筆價格: {self.parent.last_prices[-5:]}")
                
                # 策略邏輯處理
                if hasattr(self.parent, 'strategy_enabled') and self.parent.strategy_enabled:
                    self.parent.process_strategy_logic_safe(corrected_price, formatted_time)
                
                self.parent.price_count += 1
                
        return SKQuoteLibEvents(self)
    
    def process_strategy_logic_safe(self, price, time_str):
        """策略邏輯處理"""
        # 每10筆顯示一次策略接收信息
        if self.price_count % 10 == 0:
            print(f"📊 [STRATEGY] 策略收到第{self.price_count}筆: {price:.0f} @{time_str}")

def diagnose_quote_source():
    """診斷報價來源"""
    print("🔍 診斷虛擬機報價來源")
    print("=" * 50)
    
    # 1. 檢查虛擬報價機組件狀態
    print("\n1. 檢查虛擬報價機組件狀態")
    print(f"📋 進階組件可用: {hasattr(Global, 'ADVANCED_COMPONENTS_AVAILABLE')}")
    if hasattr(Global, 'ADVANCED_COMPONENTS_AVAILABLE'):
        print(f"📋 進階組件狀態: {Global.ADVANCED_COMPONENTS_AVAILABLE}")
    
    if hasattr(Global, '_quote_engine'):
        print(f"📋 進階報價引擎: {Global._quote_engine}")
    if hasattr(Global, '_virtual_quote'):
        print(f"📋 簡化報價機: {Global._virtual_quote}")
    
    # 2. 創建診斷應用
    app = DiagnosticApp()
    
    # 3. 創建VirtualQuoteWrapper
    class VirtualQuoteWrapper:
        def __init__(self, main_app):
            self.main_app = main_app
            
        def OnNotifyTicksLONG(self, sMarketNo, nStockidx, nPtr, lDate, lTimehms,
                             lTimemillismicros, nBid, nAsk, nClose, nQty, nSimulate):
            # 檢查主要的SKQuoteLibEvents
            if (hasattr(self.main_app, 'quote_event') and 
                self.main_app.quote_event and 
                hasattr(self.main_app.quote_event, 'OnNotifyTicksLONG') and
                type(self.main_app.quote_event).__name__ == 'SKQuoteLibEvents'):
                
                # 轉發到主要處理器
                self.main_app.quote_event.OnNotifyTicksLONG(
                    sMarketNo, nStockidx, nPtr, lDate, lTimehms,
                    lTimemillismicros, nBid, nAsk, nClose, nQty, nSimulate
                )
            else:
                print(f"⚠️ [DIAG] 主要處理器問題")
    
    # 4. 註冊並啟動
    wrapper = VirtualQuoteWrapper(app)
    Global.register_quote_handler(wrapper)
    
    print("\n2. 啟動報價推送診斷 (10秒)")
    Global.skQ.SKQuoteLib_RequestTicks(0, "MTX00")
    
    start_time = time.time()
    test_duration = 10
    
    while time.time() - start_time < test_duration:
        time.sleep(1)
        elapsed = int(time.time() - start_time)
        if elapsed % 3 == 0:  # 每3秒顯示一次狀態
            print(f"⏰ 診斷進行中... {elapsed}/{test_duration}秒 (已收到{len(app.received_prices)}筆)")
    
    # 5. 停止並分析
    Global.stop_virtual_machine()
    
    print("\n3. 診斷結果分析")
    print("=" * 50)
    
    if len(app.received_prices) > 0:
        prices = [item['price'] for item in app.received_prices]
        unique_prices = set(prices)
        
        print(f"📊 總報價數量: {len(app.received_prices)}")
        print(f"📊 不同價格數量: {len(unique_prices)}")
        print(f"📊 價格範圍: {min(prices):.0f} - {max(prices):.0f}")
        
        # 顯示前5筆和後5筆報價
        print(f"📊 前5筆報價:")
        for i, item in enumerate(app.received_prices[:5]):
            print(f"   {i+1}. {item['price']:.0f} @{item['time']}")
        
        print(f"📊 後5筆報價:")
        for i, item in enumerate(app.received_prices[-5:]):
            print(f"   {len(app.received_prices)-4+i}. {item['price']:.0f} @{item['time']}")
        
        # 診斷結論
        if len(unique_prices) == 1:
            print("\n❌ 診斷結果: 報價機產生固定價格")
            print(f"🔍 固定價格: {list(unique_prices)[0]:.0f}")
            print("💡 建議: 檢查報價引擎的價格生成邏輯")
            return False
        else:
            print("\n✅ 診斷結果: 報價機產生變化價格")
            print("💡 問題可能在策略系統的其他部分")
            return True
    else:
        print("\n❌ 診斷結果: 沒有收到任何報價")
        print("💡 建議: 檢查報價機啟動和事件註冊")
        return False

if __name__ == "__main__":
    try:
        success = diagnose_quote_source()
        if success:
            print("\n🎉 報價來源診斷完成 - 報價機正常")
        else:
            print("\n⚠️ 報價來源診斷發現問題")
    except Exception as e:
        print(f"\n❌ 診斷失敗: {e}")
        import traceback
        traceback.print_exc()
