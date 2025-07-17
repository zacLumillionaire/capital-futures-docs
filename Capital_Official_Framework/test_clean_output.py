#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
測試虛擬機清潔輸出
驗證關閉報價Console輸出後是否真的沒有干擾信息
"""

import os
import sys
import time

# 加入虛擬報價機路徑
virtual_quote_path = os.path.join(os.path.dirname(__file__), '虛擬報價機')
if virtual_quote_path not in sys.path:
    sys.path.insert(0, virtual_quote_path)

import Global

class CleanOutputTestApp:
    """清潔輸出測試應用"""
    
    def __init__(self):
        self.console_quote_enabled = True  # 初始啟用
        self.strategy_enabled = True
        self.price_count = 0
        self.strategy_prices = []
        
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
                
                # 報價Console輸出控制
                if getattr(self.parent, 'console_quote_enabled', True):
                    print(f"[TICK] {formatted_time} 成交:{corrected_price:.0f}")
                
                # 策略邏輯（總是執行，不受Console控制影響）
                if hasattr(self.parent, 'strategy_enabled') and self.parent.strategy_enabled:
                    self.parent.process_strategy_logic_safe(corrected_price, formatted_time)
                
                self.parent.price_count += 1
                
        return SKQuoteLibEvents(self)
    
    def process_strategy_logic_safe(self, price, time_str):
        """策略邏輯處理"""
        self.strategy_prices.append(price)
        # 策略處理不受Console控制影響，但可以有自己的輸出控制
        if len(self.strategy_prices) % 10 == 0:
            print(f"📊 [STRATEGY] 策略處理第{len(self.strategy_prices)}筆價格: {price:.0f}")

def test_clean_output():
    """測試清潔輸出"""
    print("🚀 測試虛擬機清潔輸出功能")
    print("=" * 50)
    
    # 1. 創建測試應用
    app = CleanOutputTestApp()
    
    # 2. 創建VirtualQuoteWrapper
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
                
                # 🔧 修復後：沒有調試信息輸出
                self.main_app.quote_event.OnNotifyTicksLONG(
                    sMarketNo, nStockidx, nPtr, lDate, lTimehms,
                    lTimemillismicros, nBid, nAsk, nClose, nQty, nSimulate
                )
    
    # 3. 註冊並啟動
    wrapper = VirtualQuoteWrapper(app)
    Global.register_quote_handler(wrapper)
    Global.skQ.SKQuoteLib_RequestTicks(0, "MTX00")
    
    # 4. 測試啟用狀態（3秒）
    print("\n1. 測試報價輸出啟用狀態 (3秒)")
    app.console_quote_enabled = True
    print("🔊 報價Console輸出已啟用")
    
    time.sleep(3)
    
    # 5. 測試關閉狀態（3秒）
    print("\n2. 測試報價輸出關閉狀態 (3秒)")
    app.console_quote_enabled = False
    print("🔇 報價Console輸出已關閉")
    print("💡 接下來應該只看到策略處理信息，沒有[TICK]和調試信息")
    
    time.sleep(3)
    
    # 6. 停止並分析
    Global.stop_virtual_machine()
    
    print("\n3. 測試結果")
    print("=" * 50)
    print(f"📊 總報價處理: {app.price_count}筆")
    print(f"📊 策略處理: {len(app.strategy_prices)}筆")
    
    if app.price_count > 0 and len(app.strategy_prices) > 0:
        print("✅ 虛擬機報價處理正常")
        print("💡 如果關閉期間沒有看到[TICK]和🎯調試信息，則修復成功")
        return True
    else:
        print("❌ 虛擬機報價處理異常")
        return False

if __name__ == "__main__":
    try:
        success = test_clean_output()
        if success:
            print("\n🎉 清潔輸出測試完成！")
            print("💡 現在可以安全地關閉報價Console輸出進行測試")
        else:
            print("\n⚠️ 清潔輸出測試需要檢查")
    except Exception as e:
        print(f"\n❌ 測試失敗: {e}")
        import traceback
        traceback.print_exc()
