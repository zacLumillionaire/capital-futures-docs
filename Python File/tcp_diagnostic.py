#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
TCP連接診斷工具
快速檢查TCP伺服器和客戶端的連接狀態

🏷️ TCP_DIAGNOSTIC_2025_07_01
✅ 檢查TCP伺服器狀態
✅ 測試TCP客戶端連接
✅ 診斷連接問題
"""

import socket
import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

def check_tcp_server(host='localhost', port=8888):
    """檢查TCP伺服器是否在運行"""
    print(f"🔍 檢查TCP伺服器 {host}:{port}")
    
    try:
        # 嘗試連接
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(3.0)
        result = sock.connect_ex((host, port))
        sock.close()
        
        if result == 0:
            print("✅ TCP伺服器正在運行")
            return True
        else:
            print("❌ TCP伺服器未運行或無法連接")
            print(f"   錯誤代碼: {result}")
            return False
            
    except Exception as e:
        print(f"❌ 檢查TCP伺服器時發生錯誤: {e}")
        return False

def test_tcp_client_connection():
    """測試TCP客戶端連接"""
    print("\n🔍 測試TCP客戶端連接")
    
    try:
        from tcp_price_server import PriceClient
        
        # 建立客戶端
        client = PriceClient()
        
        # 設定簡單回調
        received_data = []
        def callback(data):
            received_data.append(data)
            print(f"📥 收到數據: {data}")
        
        client.set_price_callback(callback)
        
        # 嘗試連接
        if client.connect():
            print("✅ TCP客戶端連接成功")
            
            # 等待一下看是否有數據
            import time
            print("⏳ 等待3秒檢查是否有數據...")
            time.sleep(3)
            
            if received_data:
                print(f"✅ 收到 {len(received_data)} 條數據")
            else:
                print("⚠️ 未收到任何數據 (可能伺服器沒有廣播)")
            
            # 斷開連接
            client.disconnect()
            print("🔌 客戶端已斷開")
            return True
        else:
            print("❌ TCP客戶端連接失敗")
            return False
            
    except ImportError as e:
        print(f"❌ 無法導入TCP模組: {e}")
        return False
    except Exception as e:
        print(f"❌ TCP客戶端測試失敗: {e}")
        return False

def check_ordertester_tcp_status():
    """檢查OrderTester的TCP狀態"""
    print("\n🔍 檢查OrderTester TCP狀態")
    
    try:
        from tcp_price_server import get_server_status
        
        status = get_server_status()
        if status:
            print("✅ 找到TCP伺服器狀態:")
            for key, value in status.items():
                print(f"   {key}: {value}")
            return True
        else:
            print("❌ 無法獲取TCP伺服器狀態 (可能未啟動)")
            return False
            
    except ImportError as e:
        print(f"❌ 無法導入TCP狀態模組: {e}")
        return False
    except Exception as e:
        print(f"❌ 檢查TCP狀態失敗: {e}")
        return False

def check_port_usage(port=8888):
    """檢查端口使用情況"""
    print(f"\n🔍 檢查端口 {port} 使用情況")
    
    try:
        import psutil
        
        # 查找使用該端口的進程
        for conn in psutil.net_connections():
            if conn.laddr.port == port:
                try:
                    process = psutil.Process(conn.pid)
                    print(f"✅ 端口 {port} 被進程使用:")
                    print(f"   PID: {conn.pid}")
                    print(f"   進程名: {process.name()}")
                    print(f"   狀態: {conn.status}")
                    return True
                except:
                    print(f"✅ 端口 {port} 被PID {conn.pid} 使用")
                    return True
        
        print(f"❌ 端口 {port} 未被使用")
        return False
        
    except ImportError:
        print("⚠️ 無法檢查端口使用情況 (需要psutil模組)")
        return None
    except Exception as e:
        print(f"❌ 檢查端口使用情況失敗: {e}")
        return False

def provide_solutions():
    """提供解決方案"""
    print("\n" + "="*60)
    print("🛠️ 解決方案建議")
    print("="*60)
    
    print("\n1️⃣ 如果TCP伺服器未運行:")
    print("   - 啟動 OrderTester.py")
    print("   - 勾選「☑️ 啟用TCP價格伺服器」")
    print("   - 確認狀態顯示「運行中」")
    
    print("\n2️⃣ 如果端口被占用:")
    print("   - 關閉其他使用8888端口的程式")
    print("   - 或重啟OrderTester.py")
    
    print("\n3️⃣ 如果連接成功但無數據:")
    print("   - 確認OrderTester已登入群益API")
    print("   - 確認已開啟報價監控")
    print("   - 檢查是否有實際的報價數據")
    
    print("\n4️⃣ 如果模組載入失敗:")
    print("   - 檢查 tcp_price_server.py 是否存在")
    print("   - 檢查Python路徑設定")
    
    print("\n5️⃣ 防火牆問題:")
    print("   - 檢查Windows防火牆設定")
    print("   - 允許Python程式使用localhost:8888")

def main():
    """主診斷流程"""
    print("🚀 TCP連接診斷工具")
    print("檢查OrderTester與策略端的TCP通信")
    print("="*60)
    
    # 檢查1: TCP伺服器狀態
    server_running = check_tcp_server()
    
    # 檢查2: 端口使用情況
    port_used = check_port_usage()
    
    # 檢查3: OrderTester TCP狀態
    ordertester_status = check_ordertester_tcp_status()
    
    # 檢查4: 客戶端連接測試
    client_test = test_tcp_client_connection()
    
    # 總結
    print("\n" + "="*60)
    print("📋 診斷結果總結")
    print("="*60)
    
    print(f"TCP伺服器運行: {'✅' if server_running else '❌'}")
    print(f"端口8888使用: {'✅' if port_used else '❌' if port_used is False else '⚠️'}")
    print(f"OrderTester狀態: {'✅' if ordertester_status else '❌'}")
    print(f"客戶端連接測試: {'✅' if client_test else '❌'}")
    
    # 判斷問題
    if not server_running:
        print("\n🎯 主要問題: TCP伺服器未運行")
        print("   解決方案: 啟動OrderTester並啟用TCP伺服器")
    elif not client_test:
        print("\n🎯 主要問題: 客戶端連接失敗")
        print("   解決方案: 檢查網路設定和防火牆")
    elif client_test and server_running:
        print("\n🎯 連接正常: TCP通信應該可以工作")
        print("   如果仍有問題，檢查報價數據源")
    
    # 提供解決方案
    provide_solutions()

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n⏹️ 診斷已取消")
    except Exception as e:
        print(f"\n❌ 診斷工具發生錯誤: {e}")
        import traceback
        traceback.print_exc()
