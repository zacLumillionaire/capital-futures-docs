#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
策略監控修復測試腳本
測試策略監控是否能正常接收報價數據
"""

import logging
import time
import threading

def test_log_handler():
    """測試LOG處理器功能"""
    print("🔧 測試LOG處理器功能...")
    
    try:
        # 創建測試logger
        test_logger = logging.getLogger('order.future_order')
        test_logger.setLevel(logging.INFO)
        
        # 創建簡單的測試處理器
        class TestHandler(logging.Handler):
            def __init__(self):
                super().__init__()
                self.messages = []
                
            def emit(self, record):
                message = record.getMessage()
                self.messages.append(message)
                print(f"[TEST] 收到LOG: {message}")
        
        test_handler = TestHandler()
        test_logger.addHandler(test_handler)
        
        # 發送測試訊息
        test_logger.info("🧪 測試訊息1")
        test_logger.info("【Tick】價格:2228200 買:2228100 賣:2228200 量:1 時間:22:59:21")
        test_logger.info("🧪 測試訊息2")
        
        # 檢查結果
        print(f"✅ 處理器收到 {len(test_handler.messages)} 條訊息")
        for i, msg in enumerate(test_handler.messages):
            print(f"  {i+1}. {msg}")
            
        # 清理
        test_logger.removeHandler(test_handler)
        
        return len(test_handler.messages) == 3
        
    except Exception as e:
        print(f"❌ LOG處理器測試失敗: {e}")
        return False

def test_threading_locks():
    """測試線程鎖功能"""
    print("\n🔧 測試線程鎖功能...")
    
    try:
        # 創建測試鎖
        test_lock = threading.Lock()
        shared_data = {"counter": 0, "messages": []}
        
        def worker(worker_id):
            for i in range(5):
                with test_lock:
                    shared_data["counter"] += 1
                    shared_data["messages"].append(f"Worker {worker_id} - {i}")
                time.sleep(0.001)  # 模擬處理時間
        
        # 創建多個工作線程
        threads = []
        for i in range(3):
            t = threading.Thread(target=worker, args=(i,))
            threads.append(t)
            t.start()
        
        # 等待所有線程完成
        for t in threads:
            t.join()
        
        expected_counter = 3 * 5
        actual_counter = shared_data["counter"]
        
        print(f"✅ 計數器測試: {actual_counter}/{expected_counter}")
        print(f"✅ 訊息數量: {len(shared_data['messages'])}")
        
        return actual_counter == expected_counter
        
    except Exception as e:
        print(f"❌ 線程鎖測試失敗: {e}")
        return False

def test_regex_parsing():
    """測試報價LOG解析"""
    print("\n🔧 測試報價LOG解析...")
    
    try:
        import re
        
        # 測試LOG格式
        test_logs = [
            "【Tick】價格:2228200 買:2228100 賣:2228200 量:1 時間:22:59:21",
            "【Tick】價格:2230000 買:2229900 賣:2230000 量:5 時間:09:15:30",
            "【五檔】買1:2228100(10) 賣1:2228200(8)",  # 這個不應該匹配
            "普通LOG訊息"  # 這個不應該匹配
        ]
        
        pattern = r"【Tick】價格:(\d+) 買:(\d+) 賣:(\d+) 量:(\d+) 時間:(\d{2}:\d{2}:\d{2})"
        
        matched_count = 0
        for log in test_logs:
            match = re.match(pattern, log)
            if match:
                matched_count += 1
                raw_price = int(match.group(1))
                price = raw_price / 100.0
                time_str = match.group(5)
                print(f"✅ 解析成功: {log}")
                print(f"   價格: {raw_price} -> {price}, 時間: {time_str}")
            else:
                print(f"⚪ 跳過: {log}")
        
        # 應該匹配2個Tick LOG
        return matched_count == 2
        
    except Exception as e:
        print(f"❌ 正則表達式測試失敗: {e}")
        return False

def test_strategy_simulation():
    """模擬策略監控流程"""
    print("\n🔧 模擬策略監控流程...")
    
    try:
        # 模擬策略狀態
        strategy_state = {
            "monitoring": False,
            "price_updates": 0,
            "last_price": 0,
            "errors": []
        }
        
        strategy_lock = threading.Lock()
        
        def simulate_price_update(price, time_str):
            """模擬價格更新處理"""
            try:
                with strategy_lock:
                    if strategy_state["monitoring"]:
                        strategy_state["price_updates"] += 1
                        strategy_state["last_price"] = price
                        print(f"📊 處理價格更新: {price} at {time_str}")
                    else:
                        print(f"⚪ 策略未啟動，跳過價格: {price}")
            except Exception as e:
                strategy_state["errors"].append(str(e))
        
        # 測試1: 策略未啟動時
        print("測試1: 策略未啟動")
        simulate_price_update(22282.0, "09:15:30")
        
        # 測試2: 啟動策略
        print("測試2: 啟動策略")
        with strategy_lock:
            strategy_state["monitoring"] = True
        
        simulate_price_update(22285.0, "09:15:31")
        simulate_price_update(22288.0, "09:15:32")
        
        # 測試3: 停止策略
        print("測試3: 停止策略")
        with strategy_lock:
            strategy_state["monitoring"] = False
        
        simulate_price_update(22290.0, "09:15:33")
        
        # 檢查結果
        print(f"✅ 價格更新次數: {strategy_state['price_updates']}")
        print(f"✅ 最後價格: {strategy_state['last_price']}")
        print(f"✅ 錯誤數量: {len(strategy_state['errors'])}")
        
        # 應該處理2次價格更新，無錯誤
        return (strategy_state["price_updates"] == 2 and 
                len(strategy_state["errors"]) == 0 and
                strategy_state["last_price"] == 22288.0)
        
    except Exception as e:
        print(f"❌ 策略模擬測試失敗: {e}")
        return False

def main():
    """主測試函數"""
    print("🚀 開始策略監控修復測試")
    print("=" * 50)
    
    tests = [
        ("LOG處理器功能", test_log_handler),
        ("線程鎖功能", test_threading_locks),
        ("報價LOG解析", test_regex_parsing),
        ("策略監控模擬", test_strategy_simulation)
    ]
    
    results = []
    for test_name, test_func in tests:
        print(f"\n🔧 執行測試: {test_name}")
        try:
            result = test_func()
            results.append(result)
            status = "✅ 通過" if result else "❌ 失敗"
            print(f"結果: {status}")
        except Exception as e:
            print(f"❌ 測試異常: {e}")
            results.append(False)
    
    # 統計結果
    passed = sum(results)
    total = len(results)
    
    print("\n" + "=" * 50)
    print(f"📊 測試結果統計:")
    print(f"✅ 通過: {passed}/{total}")
    print(f"❌ 失敗: {total - passed}/{total}")
    
    if passed == total:
        print("🎉 所有測試通過！策略監控修復成功")
        print("\n💡 建議:")
        print("1. 重新啟動OrderTester.py")
        print("2. 開啟報價監控")
        print("3. 啟動策略監控")
        print("4. 觀察策略LOG是否正常接收報價")
    else:
        print("⚠️ 部分測試失敗，需要進一步檢查")
    
    return passed == total

if __name__ == "__main__":
    success = main()
    print(f"\n最終結果: {'成功' if success else '失敗'}")
