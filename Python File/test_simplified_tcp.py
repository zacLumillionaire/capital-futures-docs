#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
測試簡化TCP架構
驗證新的簡化TCP架構是否能避免GIL錯誤

🏷️ SIMPLIFIED_TCP_TEST_2025_07_01
✅ 測試簡化TCP伺服器
✅ 測試簡化TCP客戶端
✅ 測試GIL錯誤避免
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

import time
import threading
from datetime import datetime

def test_simplified_tcp_server():
    """測試簡化TCP伺服器"""
    print("🧪 測試簡化TCP伺服器")
    print("="*50)
    
    try:
        from tcp_price_server import start_price_server, stop_price_server, broadcast_price_tcp
        
        # 啟動伺服器
        print("📡 啟動簡化TCP伺服器...")
        if start_price_server():
            print("✅ 伺服器啟動成功")
            
            # 等待伺服器穩定
            time.sleep(1)
            
            # 測試廣播
            print("📤 測試價格廣播...")
            for i in range(5):
                test_data = {
                    'price': 22000 + i,
                    'bid': 21990 + i,
                    'ask': 22010 + i,
                    'volume': i + 1,
                    'timestamp': datetime.now().strftime('%H:%M:%S.%f')[:-3],
                    'source': 'simplified_test'
                }
                
                if broadcast_price_tcp(test_data):
                    print(f"✅ 廣播 {i+1}: 價格 {test_data['price']}")
                else:
                    print(f"❌ 廣播 {i+1}: 失敗")
                
                time.sleep(0.2)
            
            # 停止伺服器
            print("⏹️ 停止伺服器...")
            stop_price_server()
            print("✅ 伺服器已停止")
            
            return True
            
        else:
            print("❌ 伺服器啟動失敗")
            return False
            
    except Exception as e:
        print(f"❌ 測試失敗: {e}")
        return False

def test_simplified_tcp_client():
    """測試簡化TCP客戶端"""
    print("\n🧪 測試簡化TCP客戶端")
    print("="*50)
    
    try:
        from tcp_price_server import start_price_server, stop_price_server, broadcast_price_tcp, PriceClient
        
        # 啟動伺服器
        print("📡 啟動伺服器...")
        if not start_price_server():
            print("❌ 伺服器啟動失敗")
            return False
        
        time.sleep(1)
        
        # 建立客戶端
        print("🔗 建立簡化TCP客戶端...")
        client = PriceClient()
        
        # 設定回調
        received_data = []
        def callback(data):
            received_data.append(data)
            price = data.get('price', 0)
            timestamp = data.get('timestamp', '')
            print(f"📥 收到: 價格={price}, 時間={timestamp}")
        
        client.set_price_callback(callback)
        
        # 連接
        if client.connect():
            print("✅ 客戶端連接成功")
            
            # 等待連接穩定
            time.sleep(1)
            
            # 測試廣播接收
            print("📤 測試廣播接收...")
            for i in range(3):
                test_data = {
                    'price': 22100 + i * 5,
                    'bid': 22090 + i * 5,
                    'ask': 22110 + i * 5,
                    'volume': i + 1,
                    'timestamp': datetime.now().strftime('%H:%M:%S.%f')[:-3],
                    'source': 'client_test'
                }
                
                broadcast_price_tcp(test_data)
                time.sleep(0.5)
            
            # 等待接收完成
            time.sleep(2)
            
            print(f"📊 接收統計: {len(received_data)} 條訊息")
            
            # 斷開客戶端
            client.disconnect()
            print("🔌 客戶端已斷開")
            
            success = len(received_data) > 0
            
        else:
            print("❌ 客戶端連接失敗")
            success = False
        
        # 停止伺服器
        stop_price_server()
        
        return success
        
    except Exception as e:
        print(f"❌ 測試失敗: {e}")
        return False

def test_multiple_clients():
    """測試多客戶端連接"""
    print("\n🧪 測試多客戶端連接")
    print("="*50)
    
    try:
        from tcp_price_server import start_price_server, stop_price_server, broadcast_price_tcp, PriceClient
        
        # 啟動伺服器
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
            
            # 為每個客戶端設定獨立計數
            count = [0]
            received_counts.append(count)
            
            def make_callback(client_id, counter):
                def callback(data):
                    counter[0] += 1
                    price = data.get('price', 0)
                    print(f"📥 客戶端{client_id} 收到第{counter[0]}條: 價格={price}")
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
        
        # 廣播測試訊息
        print("📤 廣播測試訊息...")
        for i in range(5):
            test_data = {
                'price': 22200 + i * 10,
                'bid': 22190 + i * 10,
                'ask': 22210 + i * 10,
                'volume': i + 1,
                'timestamp': datetime.now().strftime('%H:%M:%S.%f')[:-3],
                'source': f'multi_test_{i+1}'
            }
            
            broadcast_price_tcp(test_data)
            time.sleep(0.3)
        
        # 等待接收完成
        time.sleep(3)
        
        # 檢查接收結果
        print("\n📊 接收結果:")
        total_received = 0
        for i, count in enumerate(received_counts):
            print(f"   客戶端 {i+1}: {count[0]} 條訊息")
            total_received += count[0]
        
        # 斷開所有客戶端
        for i, client in enumerate(clients):
            client.disconnect()
            print(f"🔌 客戶端 {i+1} 已斷開")
        
        # 停止伺服器
        stop_price_server()
        
        success = total_received > 0
        return success
        
    except Exception as e:
        print(f"❌ 測試失敗: {e}")
        return False

def test_gil_error_resistance():
    """測試GIL錯誤抵抗性"""
    print("\n🧪 測試GIL錯誤抵抗性")
    print("="*50)
    
    try:
        from tcp_price_server import start_price_server, stop_price_server, broadcast_price_tcp, PriceClient
        
        # 啟動伺服器
        if not start_price_server():
            print("❌ 伺服器啟動失敗")
            return False
        
        time.sleep(1)
        
        # 建立客戶端
        client = PriceClient()
        
        received_count = [0]
        def callback(data):
            received_count[0] += 1
            if received_count[0] % 10 == 0:
                print(f"📊 已接收 {received_count[0]} 條訊息")
        
        client.set_price_callback(callback)
        
        if client.connect():
            print("✅ 客戶端連接成功")
            
            # 高頻廣播測試 (模擬真實報價環境)
            print("🚀 開始高頻廣播測試...")
            
            for i in range(50):
                test_data = {
                    'price': 22000 + (i % 100),
                    'bid': 21990 + (i % 100),
                    'ask': 22010 + (i % 100),
                    'volume': (i % 10) + 1,
                    'timestamp': datetime.now().strftime('%H:%M:%S.%f')[:-3],
                    'source': 'gil_test'
                }
                
                broadcast_price_tcp(test_data)
                time.sleep(0.02)  # 50Hz頻率
            
            # 等待接收完成
            time.sleep(3)
            
            print(f"📊 高頻測試完成: 發送50條, 接收{received_count[0]}條")
            
            # 檢查是否有GIL錯誤
            if hasattr(client, 'gil_error_detected') and client.gil_error_detected:
                print("❌ 檢測到GIL錯誤")
                success = False
            else:
                print("✅ 未檢測到GIL錯誤")
                success = received_count[0] > 0
            
            client.disconnect()
            
        else:
            print("❌ 客戶端連接失敗")
            success = False
        
        stop_price_server()
        return success
        
    except Exception as e:
        print(f"❌ 測試失敗: {e}")
        return False

def main():
    """主測試流程"""
    print("🚀 簡化TCP架構測試")
    print("測試新的簡化TCP架構是否能避免GIL錯誤")
    print("="*60)
    
    try:
        results = []
        
        # 測試1: 簡化伺服器
        results.append(test_simplified_tcp_server())
        
        # 測試2: 簡化客戶端
        results.append(test_simplified_tcp_client())
        
        # 測試3: 多客戶端
        results.append(test_multiple_clients())
        
        # 測試4: GIL錯誤抵抗性
        results.append(test_gil_error_resistance())
        
        # 總結
        print("\n" + "="*60)
        print("📋 測試結果總結")
        print("="*60)
        
        test_names = [
            "簡化TCP伺服器",
            "簡化TCP客戶端", 
            "多客戶端連接",
            "GIL錯誤抵抗性"
        ]
        
        for i, (name, result) in enumerate(zip(test_names, results)):
            status = "✅ 通過" if result else "❌ 失敗"
            print(f"{i+1}. {name}: {status}")
        
        success_rate = sum(results) / len(results) * 100
        print(f"\n🎯 總體成功率: {success_rate:.1f}%")
        
        if success_rate >= 75:
            print("🎉 簡化TCP架構測試通過！")
            print("💡 新架構特色:")
            print("   - 單線程主循環，減少線程衝突")
            print("   - 非阻塞IO，避免線程阻塞")
            print("   - daemon線程，確保程式正常退出")
            print("   - GIL錯誤檢測，自動恢復機制")
        else:
            print("⚠️ 簡化TCP架構需要進一步改進")
        
    except Exception as e:
        print(f"❌ 測試過程發生錯誤: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
