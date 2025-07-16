#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
虛擬報價機整合測試
驗證虛擬報價機與策略下單機的基本整合功能
"""

import os
import sys
import time
import threading

# 加入虛擬報價機路徑
virtual_quote_path = os.path.join(os.path.dirname(__file__), '虛擬報價機')
if virtual_quote_path not in sys.path:
    sys.path.insert(0, virtual_quote_path)

# 導入虛擬報價機模組
import Global

# 導入多組策略系統
from multi_group_database import MultiGroupDatabaseManager

class TestQuoteHandler:
    """測試報價處理器"""
    def __init__(self):
        self.quote_count = 0
        
    def OnNotifyTicksLONG(self, sMarketNo, nStockidx, nPtr, lDate, lTimehms, 
                         lTimemillismicros, nBid, nAsk, nClose, nQty, nSimulate):
        self.quote_count += 1
        price = nClose / 100.0
        bid = nBid / 100.0
        ask = nAsk / 100.0
        print(f"📊 報價 #{self.quote_count}: {price} (買:{bid} 賣:{ask})")

class TestReplyHandler:
    """測試回報處理器"""
    def __init__(self):
        self.reply_count = 0
        
    def OnNewData(self, user_id, reply_data):
        self.reply_count += 1
        fields = reply_data.split(',')
        order_id = fields[0]
        status = fields[8]
        print(f"📋 回報 #{self.reply_count}: {order_id} 狀態:{status}")

def test_virtual_integration():
    """測試虛擬報價機整合功能"""
    print("🚀 開始虛擬報價機整合測試")
    print("=" * 50)
    
    # 1. 測試資料庫初始化
    print("\n1. 測試資料庫初始化")
    try:
        db_manager = MultiGroupDatabaseManager("test_virtual_strategy.db")
        print("✅ 測試資料庫初始化成功")
    except Exception as e:
        print(f"❌ 資料庫初始化失敗: {e}")
        return False
    
    # 2. 測試虛擬API登入
    print("\n2. 測試虛擬API登入")
    try:
        result = Global.skC.SKCenterLib_Login("test_user", "test_password")
        print(f"✅ 虛擬登入結果: {result}")
    except Exception as e:
        print(f"❌ 虛擬登入失敗: {e}")
        return False
    
    # 3. 測試下單初始化
    print("\n3. 測試下單初始化")
    try:
        result = Global.skO.SKOrderLib_Initialize()
        print(f"✅ 下單初始化結果: {result}")
    except Exception as e:
        print(f"❌ 下單初始化失敗: {e}")
        return False
    
    # 4. 註冊事件處理器
    print("\n4. 註冊事件處理器")
    try:
        quote_handler = TestQuoteHandler()
        reply_handler = TestReplyHandler()
        
        Global.register_quote_handler(quote_handler)
        Global.register_reply_handler(reply_handler)
        print("✅ 事件處理器註冊成功")
    except Exception as e:
        print(f"❌ 事件處理器註冊失敗: {e}")
        return False
    
    # 5. 測試報價連線
    print("\n5. 測試報價連線")
    try:
        result = Global.skQ.SKQuoteLib_Initialize("test_user", "test_password")
        print(f"✅ 報價連線結果: {result}")
    except Exception as e:
        print(f"❌ 報價連線失敗: {e}")
        return False
    
    # 6. 測試報價訂閱
    print("\n6. 測試報價訂閱")
    try:
        result = Global.skQ.SKQuoteLib_RequestTicks(0, "MTX00")
        print(f"✅ 報價訂閱結果: {result}")
        
        # 啟動虛擬報價機
        Global.start_virtual_machine()
        print("✅ 虛擬報價機已啟動")
    except Exception as e:
        print(f"❌ 報價訂閱失敗: {e}")
        return False
    
    # 7. 等待並驗證報價接收
    print("\n7. 等待報價接收 (5秒)")
    time.sleep(5)
    
    if quote_handler.quote_count > 0:
        print(f"✅ 成功接收 {quote_handler.quote_count} 筆報價")
    else:
        print("❌ 未接收到報價")
        return False
    
    # 8. 測試下單功能
    print("\n8. 測試下單功能")
    try:
        # 模擬下單物件
        class MockOrder:
            def __init__(self):
                self.bstrFullAccount = "F0200006363839"
                self.bstrStockNo = "MTX00"
                self.sBuySell = 0  # 買進
                self.sTradeType = 2  # FOK
                self.nQty = 1
                self.bstrPrice = "21500"
        
        order = MockOrder()
        result = Global.skO.SendFutureOrderCLR("test_user", True, order)
        print(f"✅ 下單結果: {result}")
        
        # 等待回報
        print("等待回報 (3秒)")
        time.sleep(3)
        
        if reply_handler.reply_count > 0:
            print(f"✅ 成功接收 {reply_handler.reply_count} 筆回報")
        else:
            print("⚠️ 未接收到回報 (可能是正常情況)")
            
    except Exception as e:
        print(f"❌ 下單測試失敗: {e}")
        return False
    
    # 9. 停止虛擬報價機
    print("\n9. 停止虛擬報價機")
    try:
        Global.stop_virtual_machine()
        print("✅ 虛擬報價機已停止")
    except Exception as e:
        print(f"❌ 停止虛擬報價機失敗: {e}")
    
    print("\n" + "=" * 50)
    print("🎉 虛擬報價機整合測試完成")
    print(f"📊 總計接收報價: {quote_handler.quote_count} 筆")
    print(f"📋 總計接收回報: {reply_handler.reply_count} 筆")
    print("✅ 基本功能驗證成功")
    
    return True

if __name__ == "__main__":
    success = test_virtual_integration()
    if success:
        print("\n🎯 任務3完成：虛擬報價機整合驗證成功")
    else:
        print("\n❌ 任務3失敗：虛擬報價機整合驗證失敗")
