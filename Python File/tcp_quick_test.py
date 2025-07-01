#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
TCP快速測試工具
快速測試TCP伺服器和客戶端功能

🏷️ TCP_QUICK_TEST_2025_07_01
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

import time
import threading
from datetime import datetime

def test_tcp_basic():
    """基本TCP測試"""
    print("🚀 TCP快速測試開始")
    
    try:
        # 導入模組
        from tcp_price_server import start_price_server, stop_price_server, broadcast_price_tcp, PriceClient
        print("✅ TCP模組載入成功")
        
        # 啟動伺服器
        print("📡 啟動TCP伺服器...")
        if start_price_server():
            print("✅ TCP伺服器啟動成功")
            
            # 等待伺服器穩定
            time.sleep(1)
            
            # 建立客戶端
            print("🔗 建立TCP客戶端...")
            client = PriceClient()
            
            # 設定回調
            received_data = []
            def callback(data):
                received_data.append(data)
                print(f"📥 收到: {data}")
            
            client.set_price_callback(callback)
            
            # 連接
            print("🔗 嘗試連接...")
            if client.connect():
                print("✅ 客戶端連接成功")
                
                # 等待連接穩定
                time.sleep(1)
                
                # 測試廣播
                print("📤 測試廣播...")
                test_data = {
                    'price': 22100,
                    'bid': 22090,
                    'ask': 22110,
                    'volume': 5,
                    'timestamp': datetime.now().strftime('%H:%M:%S'),
                    'source': 'quick_test'
                }
                
                if broadcast_price_tcp(test_data):
                    print("✅ 廣播成功")
                    
                    # 等待接收
                    time.sleep(2)
                    
                    if received_data:
                        print(f"✅ 測試成功！收到 {len(received_data)} 條數據")
                        return True
                    else:
                        print("❌ 未收到數據")
                        return False
                else:
                    print("❌ 廣播失敗")
                    return False
            else:
                print("❌ 客戶端連接失敗")
                return False
                
        else:
            print("❌ TCP伺服器啟動失敗")
            return False
            
    except ImportError as e:
        print(f"❌ 模組載入失敗: {e}")
        return False
    except Exception as e:
        print(f"❌ 測試失敗: {e}")
        return False
    finally:
        # 清理
        try:
            if 'client' in locals():
                client.disconnect()
            stop_price_server()
            print("🧹 清理完成")
        except:
            pass

def check_port_8888():
    """檢查8888端口"""
    print("\n🔍 檢查端口8888...")
    
    import socket
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(2.0)
        result = sock.connect_ex(('localhost', 8888))
        sock.close()
        
        if result == 0:
            print("✅ 端口8888有服務運行")
            return True
        else:
            print("❌ 端口8888無服務")
            return False
    except Exception as e:
        print(f"❌ 檢查端口失敗: {e}")
        return False

if __name__ == "__main__":
    print("🧪 TCP快速診斷工具")
    print("="*40)
    
    # 檢查端口
    port_ok = check_port_8888()
    
    if not port_ok:
        print("\n💡 建議:")
        print("1. 啟動OrderTester.py")
        print("2. 勾選「☑️ 啟用TCP價格伺服器」")
        print("3. 確認狀態顯示「運行中」")
    
    # 基本測試
    print("\n" + "="*40)
    test_result = test_tcp_basic()
    
    print("\n" + "="*40)
    if test_result:
        print("🎉 TCP功能正常！")
    else:
        print("❌ TCP功能有問題")
        print("\n💡 可能原因:")
        print("- OrderTester未啟動TCP伺服器")
        print("- 防火牆阻擋localhost:8888")
        print("- 端口被其他程式占用")
