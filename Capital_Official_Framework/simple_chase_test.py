#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
簡化版追價機制測試
直接測試order_simulator的追價邏輯
"""

import os
import sys
import time

# 加入虛擬報價機路徑
virtual_quote_path = os.path.join(os.path.dirname(__file__), '虛擬報價機')
if virtual_quote_path not in sys.path:
    sys.path.insert(0, virtual_quote_path)

from config_manager import ConfigManager
from order_simulator import OrderSimulator, OrderInfo
from event_dispatcher import EventDispatcher

class MockOrderObj:
    """模擬下單物件"""
    def __init__(self, direction="LONG", price=21500):
        self.bstrFullAccount = "F0200006363839"
        self.bstrStockNo = "MTX00"
        self.sBuySell = 0 if direction == "LONG" else 1
        self.sTradeType = 2  # FOK
        self.nQty = 1
        self.bstrPrice = str(price)
        self.sNewClose = 0
        self.sDayTrade = 1

class TestReplyHandler:
    """測試回報處理器"""
    def __init__(self):
        self.replies = []
    
    def OnNewData(self, user_id, reply_data):
        """處理回報"""
        fields = reply_data.split(',')
        if len(fields) >= 9:
            order_id = fields[0]
            status = fields[8]
            self.replies.append((order_id, status))
            print(f"📋 回報: {order_id} - {status}")

def test_chase_logic():
    """測試追價邏輯"""
    print("🚀 開始簡化版追價測試")
    print("=" * 50)
    
    # 1. 初始化組件
    print("\n1. 初始化組件")
    config_manager = ConfigManager()
    event_dispatcher = EventDispatcher()
    order_simulator = OrderSimulator(config_manager, event_dispatcher)
    
    # 檢查追價模式
    print(f"🎯 追價測試模式: {order_simulator.chase_test_mode}")
    
    # 2. 註冊回報處理器
    reply_handler = TestReplyHandler()
    event_dispatcher.register_reply_handler(reply_handler)
    
    # 3. 啟動組件
    event_dispatcher.start()
    order_simulator.start()
    
    print("✅ 組件初始化完成")
    
    # 4. 測試同一部位的多次下單
    print("\n2. 測試追價邏輯")
    print("🎯 預期: 前2次失敗，第3次成功")
    
    results = []
    
    for attempt in range(1, 4):
        print(f"\n--- 第{attempt}次下單 ---")
        
        # 創建下單物件
        order_obj = MockOrderObj(direction="LONG", price=21500)
        
        # 執行下單
        order_id, status_code = order_simulator.process_order("test_user", True, order_obj)
        
        print(f"📋 下單結果: {order_id}, 狀態: {status_code}")
        
        # 等待處理完成
        time.sleep(1)
        
        # 檢查訂單狀態
        order_info = order_simulator.get_order_info(order_id)
        if order_info:
            print(f"📊 訂單狀態: {order_info.status}")
            results.append((attempt, order_info.status))
        
        # 顯示追價測試狀態
        chase_status = order_simulator.get_chase_test_status()
        print(f"🎯 追價狀態: {chase_status}")
    
    # 5. 等待所有回報
    print("\n3. 等待回報完成")
    time.sleep(2)
    
    # 6. 分析結果
    print("\n4. 結果分析")
    print("=" * 50)
    
    print("📊 下單結果:")
    for attempt, status in results:
        print(f"   第{attempt}次: {status}")
    
    print(f"\n📋 回報數量: {len(reply_handler.replies)}")
    for order_id, status in reply_handler.replies:
        print(f"   {order_id}: {status}")
    
    # 檢查追價邏輯是否正確
    if len(results) >= 3:
        if (results[0][1] == "CANCELLED" and 
            results[1][1] == "CANCELLED" and 
            results[2][1] == "FILLED"):
            print("\n✅ 追價邏輯測試成功！")
            print("   前2次取消，第3次成交")
            return True
        else:
            print("\n⚠️ 追價邏輯需要檢查")
            return False
    else:
        print("\n❌ 測試數據不足")
        return False

if __name__ == "__main__":
    try:
        success = test_chase_logic()
        if success:
            print("\n🎉 追價機制驗證成功！")
        else:
            print("\n⚠️ 追價機制需要調整")
    except Exception as e:
        print(f"\n❌ 測試失敗: {e}")
        import traceback
        traceback.print_exc()
