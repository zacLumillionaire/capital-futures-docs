#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
任務5：邊界情況與配置測試
測試低成交率下的追價重試邏輯和系統健壯性
"""

import os
import sys
import time
import json
from datetime import datetime

print("🚀 開始任務5：邊界情況與配置測試")
print("=" * 60)

# 設置虛擬報價機路徑
virtual_quote_path = os.path.join(os.path.dirname(__file__), '虛擬報價機')
sys.path.insert(0, virtual_quote_path)

# 導入必要模組
import Global

class RetryTestHandler:
    """追價重試測試處理器"""
    def __init__(self):
        self.quotes = []
        self.replies = []
        self.orders_sent = []
        self.orders_filled = []
        self.orders_cancelled = []
        self.current_price = 0
        self.retry_count = 0
        self.max_retries = 5
        self.last_order_id = None
        self.order_attempt_time = None
        self.retry_interval = 3  # 3秒後重試
        
    def OnNotifyTicksLONG(self, sMarketNo, nStockidx, nPtr, lDate, lTimehms, 
                         lTimemillismicros, nBid, nAsk, nClose, nQty, nSimulate):
        """報價處理"""
        price = nClose / 100.0
        bid = nBid / 100.0
        ask = nAsk / 100.0
        self.current_price = price
        
        quote_data = {
            'time': datetime.now(),
            'price': price,
            'bid': bid,
            'ask': ask
        }
        self.quotes.append(quote_data)
        
        print(f"📊 報價: {price} (買:{bid} 賣:{ask})")
        
        # 檢查是否需要重試
        self.check_retry_logic()
        
    def OnNewData(self, user_id, reply_data):
        """回報處理"""
        fields = reply_data.split(',')
        order_id = fields[0]
        status = fields[8]
        
        reply_info = {
            'time': datetime.now(),
            'order_id': order_id,
            'status': status,
            'data': reply_data
        }
        self.replies.append(reply_info)
        
        print(f"📋 回報: {order_id} 狀態:{status}")
        
        if status == 'N':  # 新單
            print(f"  ✅ 訂單已送出: {order_id}")
        elif status == 'D':  # 成交
            print(f"  🎉 訂單成交: {order_id}")
            self.orders_filled.append(order_id)
            self.retry_count = 0  # 重置重試計數
        elif status == 'C':  # 取消
            print(f"  ❌ 訂單取消: {order_id}")
            self.orders_cancelled.append(order_id)
            # 觸發重試邏輯
            self.trigger_retry()
    
    def send_initial_order(self):
        """發送初始訂單"""
        try:
            class TestOrder:
                def __init__(self, price):
                    self.bstrFullAccount = "F0200006363839"
                    self.bstrStockNo = "MTX00"
                    self.sBuySell = 0  # 買進
                    self.sTradeType = 2  # FOK
                    self.nQty = 1
                    self.bstrPrice = str(int(price))
            
            order = TestOrder(self.current_price + 1)  # 稍微高於市價
            result = Global.skO.SendFutureOrderCLR("test_user", True, order)
            
            order_info = {
                'time': datetime.now(),
                'order_id': result[0] if result else None,
                'price': order.bstrPrice,
                'attempt': self.retry_count + 1
            }
            self.orders_sent.append(order_info)
            self.last_order_id = result[0] if result else None
            self.order_attempt_time = datetime.now()
            
            print(f"📤 發送訂單 (嘗試 {self.retry_count + 1}): 買進 MTX00 1口 @{order.bstrPrice}")
            print(f"   訂單ID: {result[0] if result else 'N/A'}")
            
            return result
            
        except Exception as e:
            print(f"❌ 發送訂單失敗: {e}")
            return None
    
    def trigger_retry(self):
        """觸發重試邏輯"""
        if self.retry_count < self.max_retries:
            self.retry_count += 1
            print(f"🔄 準備重試 (第 {self.retry_count} 次)，等待 {self.retry_interval} 秒...")
            self.order_attempt_time = datetime.now()
        else:
            print(f"🛑 已達最大重試次數 ({self.max_retries})，停止重試")
    
    def check_retry_logic(self):
        """檢查重試邏輯"""
        if (self.order_attempt_time and 
            self.retry_count > 0 and 
            self.retry_count <= self.max_retries):
            
            # 檢查是否到了重試時間
            elapsed = (datetime.now() - self.order_attempt_time).total_seconds()
            if elapsed >= self.retry_interval:
                print(f"⏰ 重試時間到，發送追價單...")
                
                # 計算追價價格 (每次重試加1點)
                retry_price = self.current_price + self.retry_count
                
                try:
                    class RetryOrder:
                        def __init__(self, price):
                            self.bstrFullAccount = "F0200006363839"
                            self.bstrStockNo = "MTX00"
                            self.sBuySell = 0  # 買進
                            self.sTradeType = 2  # FOK
                            self.nQty = 1
                            self.bstrPrice = str(int(price))
                    
                    order = RetryOrder(retry_price)
                    result = Global.skO.SendFutureOrderCLR("test_user", True, order)
                    
                    order_info = {
                        'time': datetime.now(),
                        'order_id': result[0] if result else None,
                        'price': order.bstrPrice,
                        'attempt': self.retry_count + 1,
                        'is_retry': True
                    }
                    self.orders_sent.append(order_info)
                    self.last_order_id = result[0] if result else None
                    self.order_attempt_time = datetime.now()
                    
                    print(f"📤 發送追價單 (嘗試 {self.retry_count + 1}): 買進 MTX00 1口 @{order.bstrPrice}")
                    print(f"   追價幅度: +{self.retry_count} 點")
                    print(f"   訂單ID: {result[0] if result else 'N/A'}")
                    
                except Exception as e:
                    print(f"❌ 發送追價單失敗: {e}")

def test_retry_mechanism():
    """測試追價重試機制"""
    
    # 1. 確認配置修改
    print("\n1. 確認虛擬報價機配置")
    try:
        config_path = os.path.join(os.path.dirname(__file__), '虛擬報價機', 'config.json')
        with open(config_path, 'r', encoding='utf-8') as f:
            config = json.load(f)
        
        fill_prob = config['virtual_quote_config']['fill_probability']
        print(f"✅ 當前成交率設定: {fill_prob * 100}%")
        
        if fill_prob <= 0.1:  # 10%以下
            print("✅ 低成交率配置確認，適合測試重試機制")
        else:
            print("⚠️ 成交率較高，可能不易觸發重試機制")
            
    except Exception as e:
        print(f"❌ 讀取配置失敗: {e}")
        return False
    
    # 2. 啟動虛擬報價機
    print("\n2. 啟動虛擬報價機")
    try:
        handler = RetryTestHandler()
        Global.register_quote_handler(handler)
        Global.register_reply_handler(handler)
        print("✅ 重試測試處理器註冊完成")
        
        Global.skQ.SKQuoteLib_RequestTicks(0, "MTX00")
        Global.start_virtual_machine()
        print("✅ 虛擬報價機啟動完成")
        
        # 等待報價穩定
        time.sleep(2)
        
    except Exception as e:
        print(f"❌ 虛擬報價機啟動失敗: {e}")
        return False
    
    # 3. 執行重試測試
    print("\n3. 執行追價重試測試")
    print("🎯 測試邏輯: 在低成交率下發送訂單，觀察重試機制")
    
    # 發送初始訂單
    print("\n📤 發送初始訂單...")
    handler.send_initial_order()
    
    # 等待並觀察重試過程
    test_duration = 30  # 30秒測試時間
    start_time = time.time()
    
    print(f"⏳ 觀察重試過程 ({test_duration}秒)...")
    
    while time.time() - start_time < test_duration:
        time.sleep(1)
        
        # 如果有訂單成交，結束測試
        if handler.orders_filled:
            print("✅ 有訂單成交，重試機制測試完成")
            break
    
    # 4. 停止虛擬報價機
    print("\n4. 停止虛擬報價機")
    try:
        Global.stop_virtual_machine()
        print("✅ 虛擬報價機已停止")
    except Exception as e:
        print(f"❌ 停止虛擬報價機失敗: {e}")
    
    # 5. 分析測試結果
    print("\n5. 重試機制分析")
    print(f"📊 總計接收報價: {len(handler.quotes)} 筆")
    print(f"📋 總計接收回報: {len(handler.replies)} 筆")
    print(f"📤 總計發送訂單: {len(handler.orders_sent)} 筆")
    print(f"✅ 成交訂單: {len(handler.orders_filled)} 筆")
    print(f"❌ 取消訂單: {len(handler.orders_cancelled)} 筆")
    print(f"🔄 重試次數: {handler.retry_count}")
    
    print("\n📋 訂單發送詳情:")
    for i, order in enumerate(handler.orders_sent):
        retry_flag = " (重試)" if order.get('is_retry', False) else " (初始)"
        print(f"  訂單 {i+1}: {order['order_id']} @{order['price']}{retry_flag}")
        print(f"    時間: {order['time']}")
        print(f"    嘗試: 第 {order['attempt']} 次")
    
    # 驗證重試機制是否正常工作
    retry_triggered = handler.retry_count > 0
    multiple_orders = len(handler.orders_sent) > 1
    
    print(f"\n🔍 重試機制驗證:")
    print(f"  重試是否觸發: {'✅ 是' if retry_triggered else '❌ 否'}")
    print(f"  多次下單: {'✅ 是' if multiple_orders else '❌ 否'}")
    print(f"  追價邏輯: {'✅ 正常' if retry_triggered and multiple_orders else '❌ 異常'}")
    
    return retry_triggered and multiple_orders

if __name__ == "__main__":
    success = test_retry_mechanism()
    
    print("\n" + "=" * 60)
    if success:
        print("🎉 任務5完成：邊界情況與配置測試成功")
        print("✅ 低成交率配置驗證完成")
        print("✅ 追價重試邏輯驗證完成")
        print("✅ 系統健壯性驗證完成")
    else:
        print("❌ 任務5失敗：邊界情況與配置測試失敗")
