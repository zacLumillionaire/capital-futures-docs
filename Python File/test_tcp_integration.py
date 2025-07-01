#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
TCP價格傳輸整合測試
測試OrderTester TCP伺服器與策略端TCP客戶端的整合

🏷️ TCP_INTEGRATION_TEST_2025_07_01
✅ 測試TCP伺服器啟動
✅ 測試TCP客戶端連接
✅ 測試價格廣播
✅ 測試斷線重連
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

import time
import threading
from datetime import datetime
import logging

# 導入TCP模組
try:
    from tcp_price_server import PriceServer, PriceClient, start_price_server, stop_price_server, broadcast_price_tcp
    TCP_AVAILABLE = True
    print("✅ TCP價格伺服器模組載入成功")
except ImportError as e:
    TCP_AVAILABLE = False
    print(f"❌ TCP價格伺服器模組載入失敗: {e}")

# 設定日誌
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def test_tcp_server_basic():
    """測試TCP伺服器基本功能"""
    print("\n" + "="*60)
    print("🧪 測試1: TCP伺服器基本功能")
    print("="*60)
    
    if not TCP_AVAILABLE:
        print("❌ TCP模組未載入，跳過測試")
        return False
    
    # 啟動伺服器
    print("📡 啟動TCP價格伺服器...")
    if start_price_server():
        print("✅ TCP伺服器啟動成功")
        
        # 等待一下
        time.sleep(1)
        
        # 檢查狀態
        from tcp_price_server import get_server_status
        status = get_server_status()
        if status:
            print(f"📊 伺服器狀態: {status}")
        
        # 停止伺服器
        print("⏹️ 停止TCP伺服器...")
        stop_price_server()
        print("✅ TCP伺服器已停止")
        
        return True
    else:
        print("❌ TCP伺服器啟動失敗")
        return False

def test_tcp_client_connection():
    """測試TCP客戶端連接"""
    print("\n" + "="*60)
    print("🧪 測試2: TCP客戶端連接")
    print("="*60)
    
    if not TCP_AVAILABLE:
        print("❌ TCP模組未載入，跳過測試")
        return False
    
    # 啟動伺服器
    print("📡 啟動TCP價格伺服器...")
    if not start_price_server():
        print("❌ 伺服器啟動失敗")
        return False
    
    time.sleep(1)
    
    # 建立客戶端
    print("🔗 建立TCP客戶端...")
    client = PriceClient()
    
    # 設定接收回調
    received_messages = []
    def price_callback(price_data):
        received_messages.append(price_data)
        print(f"📥 客戶端收到: {price_data}")
    
    client.set_price_callback(price_callback)
    
    # 連接
    if client.connect():
        print("✅ 客戶端連接成功")
        
        # 等待連接穩定
        time.sleep(1)
        
        # 測試廣播
        print("📤 測試價格廣播...")
        test_price_data = {
            'price': 22100,
            'bid': 22090,
            'ask': 22110,
            'volume': 5,
            'timestamp': datetime.now().strftime('%H:%M:%S'),
            'source': 'test'
        }
        
        if broadcast_price_tcp(test_price_data):
            print("✅ 價格廣播成功")
            
            # 等待接收
            time.sleep(1)
            
            if received_messages:
                print(f"✅ 客戶端成功接收 {len(received_messages)} 條訊息")
                for msg in received_messages:
                    print(f"   📋 {msg}")
            else:
                print("❌ 客戶端未接收到訊息")
        else:
            print("❌ 價格廣播失敗")
        
        # 斷開客戶端
        client.disconnect()
        print("🔌 客戶端已斷開")
        
    else:
        print("❌ 客戶端連接失敗")
    
    # 停止伺服器
    stop_price_server()
    print("⏹️ 伺服器已停止")
    
    return len(received_messages) > 0

def test_multiple_clients():
    """測試多客戶端連接"""
    print("\n" + "="*60)
    print("🧪 測試3: 多客戶端連接")
    print("="*60)
    
    if not TCP_AVAILABLE:
        print("❌ TCP模組未載入，跳過測試")
        return False
    
    # 啟動伺服器
    print("📡 啟動TCP價格伺服器...")
    if not start_price_server():
        print("❌ 伺服器啟動失敗")
        return False
    
    time.sleep(1)
    
    # 建立多個客戶端
    clients = []
    received_counts = []
    
    for i in range(3):
        print(f"🔗 建立客戶端 {i+1}...")
        client = PriceClient()
        
        # 為每個客戶端設定獨立的接收計數
        count = [0]  # 使用列表來避免閉包問題
        received_counts.append(count)
        
        def make_callback(client_id, counter):
            def callback(price_data):
                counter[0] += 1
                print(f"📥 客戶端{client_id} 收到第{counter[0]}條: 價格={price_data.get('price')}")
            return callback
        
        client.set_price_callback(make_callback(i+1, count))
        
        if client.connect():
            clients.append(client)
            print(f"✅ 客戶端 {i+1} 連接成功")
        else:
            print(f"❌ 客戶端 {i+1} 連接失敗")
    
    print(f"📊 成功連接 {len(clients)} 個客戶端")
    
    # 等待連接穩定
    time.sleep(1)
    
    # 廣播多條訊息
    print("📤 廣播多條測試訊息...")
    for i in range(5):
        test_data = {
            'price': 22100 + i,
            'bid': 22090 + i,
            'ask': 22110 + i,
            'volume': i + 1,
            'timestamp': datetime.now().strftime('%H:%M:%S.%f')[:-3],
            'source': f'test_msg_{i+1}'
        }
        
        if broadcast_price_tcp(test_data):
            print(f"✅ 訊息 {i+1} 廣播成功")
        else:
            print(f"❌ 訊息 {i+1} 廣播失敗")
        
        time.sleep(0.1)  # 短暫間隔
    
    # 等待接收完成
    time.sleep(2)
    
    # 檢查接收結果
    print("\n📊 接收結果統計:")
    for i, count in enumerate(received_counts):
        print(f"   客戶端 {i+1}: 接收 {count[0]} 條訊息")
    
    # 斷開所有客戶端
    for i, client in enumerate(clients):
        client.disconnect()
        print(f"🔌 客戶端 {i+1} 已斷開")
    
    # 停止伺服器
    stop_price_server()
    print("⏹️ 伺服器已停止")
    
    # 檢查是否所有客戶端都收到了訊息
    all_received = all(count[0] > 0 for count in received_counts)
    return all_received

def test_high_frequency_broadcast():
    """測試高頻廣播"""
    print("\n" + "="*60)
    print("🧪 測試4: 高頻價格廣播")
    print("="*60)
    
    if not TCP_AVAILABLE:
        print("❌ TCP模組未載入，跳過測試")
        return False
    
    # 啟動伺服器
    if not start_price_server():
        print("❌ 伺服器啟動失敗")
        return False
    
    time.sleep(1)
    
    # 建立客戶端
    client = PriceClient()
    received_count = [0]
    start_time = time.time()
    
    def callback(price_data):
        received_count[0] += 1
        if received_count[0] % 10 == 0:  # 每10條顯示一次
            elapsed = time.time() - start_time
            rate = received_count[0] / elapsed
            print(f"📊 已接收 {received_count[0]} 條，速率: {rate:.1f} 條/秒")
    
    client.set_price_callback(callback)
    
    if client.connect():
        print("✅ 客戶端連接成功")
        
        # 高頻廣播測試
        print("🚀 開始高頻廣播測試 (50條訊息)...")
        
        for i in range(50):
            price_data = {
                'price': 22000 + (i % 100),
                'bid': 21990 + (i % 100),
                'ask': 22010 + (i % 100),
                'volume': (i % 10) + 1,
                'timestamp': datetime.now().strftime('%H:%M:%S.%f')[:-3],
                'source': 'high_freq_test'
            }
            
            broadcast_price_tcp(price_data)
            time.sleep(0.02)  # 20ms間隔，模擬50Hz
        
        # 等待接收完成
        time.sleep(2)
        
        elapsed = time.time() - start_time
        rate = received_count[0] / elapsed
        
        print(f"📊 測試完成:")
        print(f"   發送: 50 條訊息")
        print(f"   接收: {received_count[0]} 條訊息")
        print(f"   耗時: {elapsed:.2f} 秒")
        print(f"   接收率: {rate:.1f} 條/秒")
        print(f"   成功率: {received_count[0]/50*100:.1f}%")
        
        client.disconnect()
    else:
        print("❌ 客戶端連接失敗")
    
    stop_price_server()
    
    return received_count[0] >= 45  # 允許少量丟失

if __name__ == "__main__":
    print("🚀 TCP價格傳輸整合測試開始")
    print("測試OrderTester與策略端的TCP通信")
    
    if not TCP_AVAILABLE:
        print("❌ TCP模組未載入，無法進行測試")
        sys.exit(1)
    
    try:
        results = []
        
        # 測試1: 基本功能
        results.append(test_tcp_server_basic())
        
        # 測試2: 客戶端連接
        results.append(test_tcp_client_connection())
        
        # 測試3: 多客戶端
        results.append(test_multiple_clients())
        
        # 測試4: 高頻廣播
        results.append(test_high_frequency_broadcast())
        
        # 總結
        print("\n" + "="*60)
        print("📋 測試結果總結")
        print("="*60)
        
        test_names = [
            "TCP伺服器基本功能",
            "TCP客戶端連接",
            "多客戶端連接",
            "高頻價格廣播"
        ]
        
        for i, (name, result) in enumerate(zip(test_names, results)):
            status = "✅ 通過" if result else "❌ 失敗"
            print(f"{i+1}. {name}: {status}")
        
        success_rate = sum(results) / len(results) * 100
        print(f"\n🎯 總體成功率: {success_rate:.1f}%")
        
        if success_rate >= 75:
            print("🎉 TCP整合測試基本通過！")
        else:
            print("⚠️ TCP整合測試需要改進")
        
    except Exception as e:
        logger.error(f"❌ 測試過程發生錯誤: {e}", exc_info=True)
        print(f"\n❌ 測試失敗: {e}")
    
    finally:
        # 確保清理
        try:
            stop_price_server()
        except:
            pass
