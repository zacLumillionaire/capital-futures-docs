#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
測試虛擬機報價與策略系統整合
驗證報價是否正確傳遞給策略監控系統
"""

import os
import sys
import time
import threading

# 加入虛擬報價機路徑
virtual_quote_path = os.path.join(os.path.dirname(__file__), '虛擬報價機')
if virtual_quote_path not in sys.path:
    sys.path.insert(0, virtual_quote_path)

import Global

class MockStrategyApp:
    """模擬策略應用程式"""
    
    def __init__(self):
        self.strategy_enabled = True
        self.console_quote_enabled = True
        self.console_strategy_enabled = True
        self.price_count = 0
        self.last_price = 0
        self.last_update_time = ""
        self.strategy_prices = []  # 記錄策略收到的價格
        
        # 創建主要的SKQuoteLibEvents
        self.quote_event = self.create_main_quote_event()
        
    def create_main_quote_event(self):
        """創建主要的SKQuoteLibEvents（模擬virtual_simple_integrated.py的方式）"""
        class SKQuoteLibEvents:
            def __init__(self, parent):
                self.parent = parent
                
            def OnNotifyTicksLONG(self, sMarketNo, nStockidx, nPtr, lDate, lTimehms, 
                                 lTimemillismicros, nBid, nAsk, nClose, nQty, nSimulate):
                """主要報價事件處理器（包含策略邏輯）"""
                # 解析價格資訊
                corrected_price = nClose / 100.0
                bid = nBid / 100.0
                ask = nAsk / 100.0
                
                # 格式化時間
                time_str = f"{lTimehms:06d}"
                formatted_time = f"{time_str[:2]}:{time_str[2:4]}:{time_str[4:6]}"
                
                # 顯示報價
                if getattr(self.parent, 'console_quote_enabled', True):
                    print(f"[MAIN] {formatted_time} 成交:{corrected_price:.0f} 買:{bid:.0f} 賣:{ask:.0f}")
                
                # 🎯 策略邏輯整合（關鍵部分）
                if hasattr(self.parent, 'strategy_enabled') and self.parent.strategy_enabled:
                    self.parent.process_strategy_logic_safe(corrected_price, formatted_time)
                
                # 更新內部數據
                self.parent.last_price = corrected_price
                self.parent.last_update_time = formatted_time
                self.parent.price_count += 1
                
        return SKQuoteLibEvents(self)
    
    def process_strategy_logic_safe(self, price, time_str):
        """策略邏輯處理（模擬virtual_simple_integrated.py的方式）"""
        try:
            # 記錄策略收到的價格
            self.strategy_prices.append(price)
            
            # 顯示策略處理
            if getattr(self, 'console_strategy_enabled', True):
                if len(self.strategy_prices) % 5 == 0:  # 每5筆顯示一次
                    print(f"📊 [STRATEGY] 策略收到價格: {price:.0f} (第{len(self.strategy_prices)}筆)")
                    
        except Exception as e:
            print(f"❌ [STRATEGY] 策略處理錯誤: {e}")

def test_virtual_quote_strategy():
    """測試虛擬機報價與策略整合"""
    print("🚀 測試虛擬機報價與策略系統整合")
    print("=" * 60)
    
    # 1. 創建模擬策略應用
    mock_app = MockStrategyApp()
    print(f"✅ 模擬策略應用已創建")
    print(f"📋 主要報價處理器類型: {type(mock_app.quote_event).__name__}")
    
    # 2. 創建VirtualQuoteWrapper（模擬virtual_simple_integrated.py的方式）
    class VirtualQuoteWrapper:
        def __init__(self, main_app):
            self.main_app = main_app
            
        def OnNotifyTicksLONG(self, sMarketNo, nStockidx, nPtr, lDate, lTimehms,
                             lTimemillismicros, nBid, nAsk, nClose, nQty, nSimulate):
            # 檢查主要的SKQuoteLibEvents是否存在且為正確類型
            if (hasattr(self.main_app, 'quote_event') and 
                self.main_app.quote_event and 
                hasattr(self.main_app.quote_event, 'OnNotifyTicksLONG') and
                type(self.main_app.quote_event).__name__ == 'SKQuoteLibEvents'):
                
                # 使用主要的SKQuoteLibEvents處理器
                print(f"🎯 [Virtual] 使用主要SKQuoteLibEvents處理報價")
                self.main_app.quote_event.OnNotifyTicksLONG(
                    sMarketNo, nStockidx, nPtr, lDate, lTimehms,
                    lTimemillismicros, nBid, nAsk, nClose, nQty, nSimulate
                )
            else:
                print(f"⚠️ [Virtual] 主要SKQuoteLibEvents未就緒")
    
    # 3. 註冊VirtualQuoteWrapper
    wrapper = VirtualQuoteWrapper(mock_app)
    Global.register_quote_handler(wrapper)
    print("✅ VirtualQuoteWrapper已註冊")
    
    # 4. 啟動虛擬報價機
    print("\n📊 啟動虛擬報價推送 (10秒)")
    Global.skQ.SKQuoteLib_RequestTicks(0, "MTX00")
    
    start_time = time.time()
    test_duration = 10
    
    while time.time() - start_time < test_duration:
        time.sleep(1)
        elapsed = int(time.time() - start_time)
        print(f"⏰ 測試進行中... {elapsed}/{test_duration}秒")
    
    # 5. 停止虛擬報價機
    Global.stop_virtual_machine()
    
    # 6. 分析結果
    print("\n📊 測試結果分析")
    print("=" * 60)
    
    print(f"📋 總報價數量: {mock_app.price_count}")
    print(f"📋 策略收到價格數量: {len(mock_app.strategy_prices)}")
    print(f"📋 最後價格: {mock_app.last_price:.0f}")
    
    if len(mock_app.strategy_prices) > 0:
        print(f"📋 策略價格範圍: {min(mock_app.strategy_prices):.0f} - {max(mock_app.strategy_prices):.0f}")
        
        # 檢查價格是否有變化
        unique_prices = set(mock_app.strategy_prices)
        if len(unique_prices) > 1:
            print("✅ 策略系統收到變化的價格數據")
            print(f"📊 不同價格數量: {len(unique_prices)}")
            return True
        else:
            print("❌ 策略系統收到固定價格數據")
            print(f"📊 固定價格: {list(unique_prices)[0]:.0f}")
            return False
    else:
        print("❌ 策略系統沒有收到任何價格數據")
        return False

if __name__ == "__main__":
    try:
        success = test_virtual_quote_strategy()
        if success:
            print("\n🎉 虛擬機報價與策略整合測試成功！")
            print("💡 策略監控系統正確接收到變化的報價數據")
        else:
            print("\n⚠️ 虛擬機報價與策略整合需要檢查")
            print("💡 策略監控系統可能沒有正確接收報價")
    except Exception as e:
        print(f"\n❌ 測試失敗: {e}")
        import traceback
        traceback.print_exc()
