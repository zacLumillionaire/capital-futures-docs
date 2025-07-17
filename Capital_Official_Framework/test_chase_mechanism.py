#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
追價機制測試腳本
測試虛擬報價機的追價功能運作
"""

import os
import sys
import time
import threading
from datetime import datetime

# 加入虛擬報價機路徑
virtual_quote_path = os.path.join(os.path.dirname(__file__), '虛擬報價機')
if virtual_quote_path not in sys.path:
    sys.path.insert(0, virtual_quote_path)

# 導入虛擬報價機模組
import Global
from config_manager import ConfigManager
from order_simulator import OrderInfo

class ChaseTestHandler:
    """追價測試處理器"""
    
    def __init__(self):
        self.quote_count = 0
        self.order_count = 0
        self.fill_count = 0
        self.cancel_count = 0
        self.orders = {}
        
    def OnNotifyTicksLONG(self, market_no, stock_idx, date, time_hms, time_ms, 
                         bid, ask, close, qty, volume, simulate):
        """處理報價事件"""
        self.quote_count += 1
        if self.quote_count % 10 == 0:  # 每10筆報價顯示一次
            print(f"📊 [報價] #{self.quote_count} - 買:{bid} 賣:{ask} 成交:{close}")
    
    def OnNotifyBest5LONG(self, market_no, stock_idx, date, time_hms, time_ms,
                         ask1, ask1_qty, ask2, ask2_qty, ask3, ask3_qty,
                         ask4, ask4_qty, ask5, ask5_qty,
                         bid1, bid1_qty, bid2, bid2_qty, bid3, bid3_qty,
                         bid4, bid4_qty, bid5, bid5_qty, simulate):
        """處理五檔報價事件"""
        print(f"📈 [五檔] ASK1:{ask1}({ask1_qty}) BID1:{bid1}({bid1_qty})")
    
    def OnNewData(self, user_id, reply_data):
        """處理回報事件"""
        fields = reply_data.split(',')
        if len(fields) >= 9:
            order_id = fields[0]
            status = fields[8]
            
            if status == "N":
                print(f"📤 [新單] {order_id}")
                self.order_count += 1
            elif status == "D":
                print(f"✅ [成交] {order_id}")
                self.fill_count += 1
            elif status == "C":
                print(f"❌ [取消] {order_id}")
                self.cancel_count += 1
    
    def get_statistics(self):
        """取得統計資訊"""
        return {
            "quotes": self.quote_count,
            "orders": self.order_count,
            "fills": self.fill_count,
            "cancels": self.cancel_count
        }

class MockFutureOrder:
    """模擬FUTUREORDER物件"""
    
    def __init__(self, direction="LONG", price=21500, quantity=1):
        self.bstrFullAccount = "F0200006363839"
        self.bstrStockNo = "MTX00"
        self.sBuySell = 0 if direction == "LONG" else 1
        self.sTradeType = 2  # FOK
        self.nQty = quantity
        self.bstrPrice = str(price)
        self.sNewClose = 0  # 新倉
        self.sDayTrade = 1  # 當沖

def test_chase_mechanism():
    """測試追價機制"""
    print("🚀 開始追價機制測試")
    print("=" * 60)
    
    # 1. 初始化虛擬報價機
    print("\n1. 初始化虛擬報價機")
    try:
        # 檢查配置
        config_manager = ConfigManager()
        scenario = config_manager.config.get('scenario', '')
        print(f"📋 當前配置: {scenario}")
        
        # 初始化Global模組
        Global.initialize_virtual_machine()
        print("✅ 虛擬報價機初始化完成")
        
    except Exception as e:
        print(f"❌ 虛擬報價機初始化失敗: {e}")
        return False
    
    # 2. 註冊事件處理器
    print("\n2. 註冊事件處理器")
    try:
        handler = ChaseTestHandler()
        Global.register_quote_handler(handler)
        Global.register_reply_handler(handler)
        print("✅ 事件處理器註冊完成")
    except Exception as e:
        print(f"❌ 事件處理器註冊失敗: {e}")
        return False
    
    # 3. 啟動報價
    print("\n3. 啟動報價推送")
    try:
        Global.skQ.SKQuoteLib_RequestTicks(0, "MTX00")
        Global.skQ.SKQuoteLib_RequestBest5LONG(0, "MTX00")
        print("✅ 報價推送已啟動")
        
        # 等待報價穩定
        time.sleep(2)
        
    except Exception as e:
        print(f"❌ 報價推送失敗: {e}")
        return False
    
    # 4. 測試追價下單
    print("\n4. 測試追價下單機制")
    print("🎯 測試邏輯: 前2次失敗，第3次成功")
    
    try:
        # 模擬同一部位的3次下單嘗試
        for attempt in range(1, 4):
            print(f"\n--- 第{attempt}次下單嘗試 ---")
            
            # 創建下單物件
            order_obj = MockFutureOrder(direction="LONG", price=21500, quantity=1)
            
            # 執行下單
            result = Global.skO.SendFutureOrderCLR("test_user", True, order_obj)
            order_id, status_code = result
            
            print(f"📋 下單結果: {order_id}, 狀態碼: {status_code}")
            
            # 等待回報
            time.sleep(1)
            
            # 顯示統計
            stats = handler.get_statistics()
            print(f"📊 統計: 下單{stats['orders']} 成交{stats['fills']} 取消{stats['cancels']}")
    
    except Exception as e:
        print(f"❌ 追價下單測試失敗: {e}")
        return False
    
    # 5. 等待所有回報完成
    print("\n5. 等待回報完成")
    time.sleep(3)
    
    # 6. 顯示最終結果
    print("\n6. 測試結果總結")
    print("=" * 60)
    
    final_stats = handler.get_statistics()
    print(f"📊 最終統計:")
    print(f"   - 報價數量: {final_stats['quotes']}")
    print(f"   - 下單數量: {final_stats['orders']}")
    print(f"   - 成交數量: {final_stats['fills']}")
    print(f"   - 取消數量: {final_stats['cancels']}")
    
    # 檢查追價邏輯是否正確
    if final_stats['cancels'] == 2 and final_stats['fills'] == 1:
        print("✅ 追價機制測試成功！前2次取消，第3次成交")
        return True
    else:
        print("⚠️ 追價機制可能需要調整")
        return False

if __name__ == "__main__":
    try:
        success = test_chase_mechanism()
        if success:
            print("\n🎉 追價機制測試完成！")
        else:
            print("\n⚠️ 追價機制測試需要檢查")
            
    except KeyboardInterrupt:
        print("\n⏹️ 測試被用戶中斷")
    except Exception as e:
        print(f"\n❌ 測試過程發生錯誤: {e}")
    finally:
        print("\n🔚 測試結束")
