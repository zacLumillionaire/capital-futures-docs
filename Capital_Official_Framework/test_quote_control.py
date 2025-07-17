#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
測試報價輸出控制功能
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

class MockMainApp:
    """模擬主程式"""
    def __init__(self):
        self.console_quote_enabled = True  # 初始啟用
        self._last_best5_time = 0

class TestQuoteControlHandler:
    """測試報價控制處理器"""
    
    def __init__(self, main_app):
        self.main_app = main_app
        self.quote_count = 0
        self.best5_count = 0
        
    def OnNotifyTicksLONG(self, sMarketNo, nStockidx, nPtr, lDate, lTimehms,
                         lTimemillismicros, nBid, nAsk, nClose, nQty, nSimulate):
        """處理報價事件"""
        self.quote_count += 1
        
        # 檢查報價Console輸出設定
        if getattr(self.main_app, 'console_quote_enabled', True):
            print(f"[TICK] #{self.quote_count} 成交:{nClose/100:.0f} 買:{nBid/100:.0f} 賣:{nAsk/100:.0f}")
        
    def OnNotifyBest5LONG(self, sMarketNo, nStockidx, nPtr,
                         nBid1, nBidQty1, nBid2, nBidQty2, nBid3, nBidQty3, nBid4, nBidQty4, nBid5, nBidQty5,
                         nAsk1, nAskQty1, nAsk2, nAskQty2, nAsk3, nAskQty3, nAsk4, nAskQty4, nAsk5, nAskQty5, nSimulate):
        """處理五檔報價事件"""
        self.best5_count += 1
        
        # 轉換價格
        bid1 = nBid1/100
        ask1 = nAsk1/100
        
        # 🔧 檢查報價Console輸出設定
        if getattr(self.main_app, 'console_quote_enabled', True):
            print(f"[BEST5] #{self.best5_count} 買1:{bid1:.0f}({nBidQty1}) 賣1:{ask1:.0f}({nAskQty1})")

def test_quote_control():
    """測試報價輸出控制"""
    print("🚀 測試報價輸出控制功能")
    print("=" * 60)
    
    # 1. 初始化組件
    print("\n1. 初始化組件")
    config_manager = ConfigManager()
    event_dispatcher = EventDispatcher()
    quote_engine = VirtualQuoteEngine(config_manager, event_dispatcher)
    
    # 創建模擬主程式
    mock_app = MockMainApp()
    
    # 創建測試處理器
    handler = TestQuoteControlHandler(mock_app)
    
    # 註冊處理器
    event_dispatcher.register_quote_handler(handler)
    
    # 啟動組件
    event_dispatcher.start()
    
    print("✅ 組件初始化完成")
    
    # 2. 測試報價輸出啟用狀態
    print("\n2. 測試報價輸出啟用狀態 (5秒)")
    mock_app.console_quote_enabled = True
    print("🔊 報價輸出已啟用")
    
    quote_engine.start_quote_feed("MTX00")
    time.sleep(5)
    
    enabled_quotes = handler.quote_count
    enabled_best5 = handler.best5_count
    
    print(f"📊 啟用狀態統計: TICK={enabled_quotes}, BEST5={enabled_best5}")
    
    # 3. 測試報價輸出關閉狀態
    print("\n3. 測試報價輸出關閉狀態 (5秒)")
    mock_app.console_quote_enabled = False
    print("🔇 報價輸出已關閉")
    
    # 重置計數器
    start_quotes = handler.quote_count
    start_best5 = handler.best5_count
    
    time.sleep(5)
    
    disabled_quotes = handler.quote_count - start_quotes
    disabled_best5 = handler.best5_count - start_best5
    
    print(f"📊 關閉狀態統計: TICK={disabled_quotes}, BEST5={disabled_best5}")
    
    # 4. 停止報價
    quote_engine.stop()
    
    # 5. 分析結果
    print("\n4. 測試結果分析")
    print("=" * 60)
    
    print(f"📊 總體統計:")
    print(f"   - 啟用時: TICK={enabled_quotes}, BEST5={enabled_best5}")
    print(f"   - 關閉時: TICK={disabled_quotes}, BEST5={disabled_best5}")
    
    # 檢查控制是否有效
    if disabled_quotes > 0 or disabled_best5 > 0:
        print("\n⚠️ 警告：關閉報價輸出時仍有輸出")
        print("   這表示報價控制機制可能沒有完全生效")
        return False
    else:
        print("\n✅ 報價輸出控制測試成功！")
        print("   關閉時沒有任何報價輸出")
        return True

if __name__ == "__main__":
    try:
        success = test_quote_control()
        if success:
            print("\n🎉 報價輸出控制功能正常！")
            print("💡 現在GUI介面的報價開關應該能正確控制虛擬機輸出")
        else:
            print("\n⚠️ 報價輸出控制需要進一步檢查")
    except Exception as e:
        print(f"\n❌ 測試失敗: {e}")
        import traceback
        traceback.print_exc()
