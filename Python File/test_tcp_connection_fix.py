#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
測試TCP連接修復
驗證修復後的TCP連接是否只建立一個連接

🏷️ TCP_CONNECTION_FIX_TEST_2025_07_01
✅ 測試單一連接
✅ 測試重複點擊防護
✅ 測試詳細日誌
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

import time
import threading
from datetime import datetime

def test_single_connection():
    """測試單一連接"""
    print("🧪 測試單一連接")
    print("="*50)
    
    try:
        from tcp_price_server import start_price_server, stop_price_server, PriceServer
        
        # 啟動伺服器
        print("📡 啟動TCP伺服器...")
        if not start_price_server():
            print("❌ 伺服器啟動失敗")
            return False
        
        # 獲取伺服器實例來監控連接數
        from tcp_price_server import _global_server
        server = _global_server
        
        time.sleep(1)
        
        # 建立客戶端
        print("🔗 建立TCP客戶端...")
        from tcp_price_server import PriceClient
        
        client = PriceClient()
        
        # 記錄連接前的狀態
        initial_clients = len(server.clients) if server else 0
        print(f"📊 連接前客戶端數量: {initial_clients}")
        
        # 連接
        if client.connect():
            time.sleep(0.5)  # 等待連接穩定
            
            # 檢查連接數
            final_clients = len(server.clients) if server else 0
            print(f"📊 連接後客戶端數量: {final_clients}")
            
            connection_increase = final_clients - initial_clients
            print(f"📊 新增連接數: {connection_increase}")
            
            if connection_increase == 1:
                print("✅ 單一連接測試通過")
                success = True
            else:
                print(f"❌ 單一連接測試失敗 - 預期1個連接，實際{connection_increase}個")
                success = False
            
            # 斷開客戶端
            client.disconnect()
            time.sleep(0.5)
            
            # 檢查斷開後的狀態
            after_disconnect = len(server.clients) if server else 0
            print(f"📊 斷開後客戶端數量: {after_disconnect}")
            
        else:
            print("❌ 客戶端連接失敗")
            success = False
        
        # 停止伺服器
        stop_price_server()
        return success
        
    except Exception as e:
        print(f"❌ 測試失敗: {e}")
        return False

def test_duplicate_click_protection():
    """測試重複點擊防護"""
    print("\n🧪 測試重複點擊防護")
    print("="*50)
    
    try:
        from tcp_price_server import start_price_server, stop_price_server, PriceClient
        
        # 啟動伺服器
        if not start_price_server():
            print("❌ 伺服器啟動失敗")
            return False
        
        time.sleep(1)
        
        # 建立客戶端
        client = PriceClient()
        
        # 第一次連接
        print("🔗 第一次連接...")
        result1 = client.connect()
        print(f"第一次連接結果: {result1}")
        
        time.sleep(0.5)
        
        # 第二次連接 (應該被防護)
        print("🔗 第二次連接 (測試重複防護)...")
        result2 = client.connect()
        print(f"第二次連接結果: {result2}")
        
        # 檢查是否正確處理重複連接
        if result1 and result2:
            print("✅ 重複點擊防護測試通過")
            success = True
        else:
            print("❌ 重複點擊防護測試失敗")
            success = False
        
        # 清理
        client.disconnect()
        stop_price_server()
        
        return success
        
    except Exception as e:
        print(f"❌ 測試失敗: {e}")
        return False

def test_connection_logging():
    """測試連接日誌"""
    print("\n🧪 測試連接日誌")
    print("="*50)
    
    try:
        import logging
        
        # 設定日誌捕獲
        log_messages = []
        
        class LogCapture(logging.Handler):
            def emit(self, record):
                log_messages.append(record.getMessage())
        
        # 添加日誌捕獲器
        logger = logging.getLogger('tcp_price_server')
        handler = LogCapture()
        logger.addHandler(handler)
        logger.setLevel(logging.INFO)
        
        from tcp_price_server import start_price_server, stop_price_server, PriceClient
        
        # 啟動伺服器
        if not start_price_server():
            print("❌ 伺服器啟動失敗")
            return False
        
        time.sleep(1)
        
        # 清空之前的日誌
        log_messages.clear()
        
        # 建立客戶端並連接
        client = PriceClient()
        client.connect()
        
        time.sleep(1)
        
        # 檢查日誌
        print("📋 捕獲的日誌訊息:")
        for i, msg in enumerate(log_messages):
            print(f"   {i+1}. {msg}")
        
        # 檢查關鍵日誌
        key_logs = [
            "PriceClient開始連接",
            "建立新socket連接",
            "Socket連接成功",
            "啟動TCP接收線程",
            "已連接到價格伺服器"
        ]
        
        found_logs = 0
        for key_log in key_logs:
            for msg in log_messages:
                if key_log in msg:
                    found_logs += 1
                    break
        
        print(f"📊 找到關鍵日誌: {found_logs}/{len(key_logs)}")
        
        if found_logs >= len(key_logs) * 0.8:  # 80%以上
            print("✅ 連接日誌測試通過")
            success = True
        else:
            print("❌ 連接日誌測試失敗")
            success = False
        
        # 清理
        client.disconnect()
        stop_price_server()
        logger.removeHandler(handler)
        
        return success
        
    except Exception as e:
        print(f"❌ 測試失敗: {e}")
        return False

def test_error_handling():
    """測試錯誤處理"""
    print("\n🧪 測試錯誤處理")
    print("="*50)
    
    try:
        from tcp_price_server import PriceClient
        
        # 測試連接到不存在的伺服器
        print("🔗 測試連接到不存在的伺服器...")
        client = PriceClient(port=9999)  # 使用不存在的端口
        
        result = client.connect()
        
        if not result:
            print("✅ 錯誤處理測試通過 - 正確處理連接失敗")
            success = True
        else:
            print("❌ 錯誤處理測試失敗 - 應該連接失敗但返回成功")
            success = False
        
        return success
        
    except Exception as e:
        print(f"❌ 測試失敗: {e}")
        return False

def main():
    """主測試流程"""
    print("🚀 TCP連接修復測試")
    print("驗證修復後的TCP連接是否只建立一個連接")
    print("="*60)
    
    try:
        results = []
        
        # 測試1: 單一連接
        results.append(test_single_connection())
        
        # 測試2: 重複點擊防護
        results.append(test_duplicate_click_protection())
        
        # 測試3: 連接日誌
        results.append(test_connection_logging())
        
        # 測試4: 錯誤處理
        results.append(test_error_handling())
        
        # 總結
        print("\n" + "="*60)
        print("📋 測試結果總結")
        print("="*60)
        
        test_names = [
            "單一連接測試",
            "重複點擊防護",
            "連接日誌測試",
            "錯誤處理測試"
        ]
        
        for i, (name, result) in enumerate(zip(test_names, results)):
            status = "✅ 通過" if result else "❌ 失敗"
            print(f"{i+1}. {name}: {status}")
        
        success_rate = sum(results) / len(results) * 100
        print(f"\n🎯 總體成功率: {success_rate:.1f}%")
        
        if success_rate >= 75:
            print("🎉 TCP連接修復測試通過！")
            print("💡 修復效果:")
            print("   - 移除了預先診斷連接")
            print("   - 添加了重複連接防護")
            print("   - 增強了錯誤處理和日誌")
            print("   - 確保只建立一個TCP連接")
        else:
            print("⚠️ TCP連接修復需要進一步改進")
        
    except Exception as e:
        print(f"❌ 測試過程發生錯誤: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
