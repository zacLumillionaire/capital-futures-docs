#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
測試純Queue機制，確認沒有LOG處理器干擾
"""

import sys
import time
import logging

def test_log_handler_removal():
    """測試LOG處理器是否已移除"""
    print("🔍 檢查LOG處理器狀態...")
    
    try:
        # 檢查order.future_order的logger
        future_order_logger = logging.getLogger('order.future_order')
        
        print(f"📊 Logger名稱: {future_order_logger.name}")
        print(f"📊 Logger級別: {future_order_logger.level}")
        print(f"📊 Handler數量: {len(future_order_logger.handlers)}")
        
        # 列出所有handlers
        for i, handler in enumerate(future_order_logger.handlers):
            print(f"   Handler {i}: {type(handler).__name__}")
            if hasattr(handler, 'strategy_app'):
                print(f"   ⚠️ 發現StrategyLogHandler - 舊機制仍存在")
                return False
        
        if len(future_order_logger.handlers) == 0:
            print("✅ 沒有發現LOG處理器 - 舊機制已移除")
            return True
        else:
            print("ℹ️ 發現其他LOG處理器，但非StrategyLogHandler")
            return True
            
    except Exception as e:
        print(f"❌ 檢查LOG處理器失敗: {e}")
        return False

def test_queue_mechanism():
    """測試Queue機制是否正常"""
    print("\n🔍 測試Queue機制...")
    
    try:
        import OrderTester
        
        # 檢查OrderTesterApp是否有Queue相關屬性
        app_class = OrderTester.OrderTesterApp
        
        # 創建一個測試實例（不啟動UI）
        print("📊 檢查Queue相關屬性...")
        
        # 檢查類定義中是否有Queue初始化
        import inspect
        source = inspect.getsource(app_class.__init__)
        
        queue_checks = [
            ('tick_data_queue', 'tick_data_queue' in source),
            ('strategy_queue', 'strategy_queue' in source),
            ('log_queue', 'log_queue' in source),
            ('process_tick_queue', 'process_tick_queue' in source),
            ('process_log_queue', 'process_log_queue' in source),
            ('strategy_logic_thread', 'strategy_logic_thread' in source)
        ]
        
        all_good = True
        for check_name, found in queue_checks:
            status = "✅" if found else "❌"
            print(f"   {status} {check_name}")
            if not found:
                all_good = False
        
        if all_good:
            print("✅ Queue機制檢查通過")
            return True
        else:
            print("❌ Queue機制檢查失敗")
            return False
            
    except Exception as e:
        print(f"❌ Queue機制測試失敗: {e}")
        return False

def test_com_event_modification():
    """測試COM事件是否已修改"""
    print("\n🔍 檢查COM事件修改...")
    
    try:
        from order import future_order
        
        # 檢查OnNotifyTicksLONG是否已修改
        import inspect
        
        # 獲取OnNotifyTicksLONG的源碼
        source_lines = inspect.getsourcelines(future_order.SKQuoteLibEvents.OnNotifyTicksLONG)
        source = ''.join(source_lines[0])
        
        # 檢查關鍵修改點
        checks = [
            ('tick_data打包', 'tick_data' in source),
            ('put_nowait操作', 'put_nowait' in source),
            ('移除UI操作', '.config(' not in source),
            ('移除LOG輸出', 'logging.getLogger' not in source),
            ('return 0', 'return 0' in source)
        ]
        
        all_good = True
        for check_name, passed in checks:
            status = "✅" if passed else "❌"
            print(f"   {status} {check_name}")
            if not passed:
                all_good = False
        
        if all_good:
            print("✅ COM事件修改檢查通過")
            return True
        else:
            print("❌ COM事件修改檢查失敗")
            return False
            
    except Exception as e:
        print(f"❌ COM事件檢查失敗: {e}")
        return False

def simulate_pure_queue_flow():
    """模擬純Queue數據流"""
    print("\n🔍 模擬純Queue數據流...")
    
    try:
        import queue
        import threading
        import time
        
        # 創建Queue
        tick_queue = queue.Queue(maxsize=1000)
        strategy_queue = queue.Queue(maxsize=100)
        log_queue = queue.Queue(maxsize=500)
        
        # 模擬COM事件數據
        def simulate_com_event():
            """模擬COM事件發送數據"""
            for i in range(5):
                tick_data = {
                    'type': 'tick',
                    'close': 22000 + i * 10,
                    'time': 91500 + i,
                    'timestamp': time.time()
                }
                tick_queue.put_nowait(tick_data)
                time.sleep(0.1)
        
        # 模擬主線程處理
        def simulate_main_thread():
            """模擬主線程處理Tick"""
            processed = 0
            while processed < 5:
                try:
                    data = tick_queue.get(timeout=1)
                    print(f"   📊 主線程處理: 價格={data['close']}")
                    
                    # 轉發給策略
                    strategy_data = {
                        'price': data['close'] / 100.0,
                        'time': f"{data['time']:06d}"[:6],
                        'timestamp': data['timestamp']
                    }
                    strategy_queue.put_nowait(strategy_data)
                    processed += 1
                    
                except queue.Empty:
                    break
        
        # 模擬策略執行緒
        def simulate_strategy_thread():
            """模擬策略執行緒"""
            processed = 0
            while processed < 5:
                try:
                    data = strategy_queue.get(timeout=1)
                    print(f"   🎯 策略處理: 價格={data['price']}")
                    
                    # 生成UI更新
                    ui_update = {
                        'type': 'price_update',
                        'price': data['price'],
                        'time': data['time']
                    }
                    log_queue.put_nowait(ui_update)
                    processed += 1
                    
                except queue.Empty:
                    break
        
        # 執行模擬
        print("   🚀 開始模擬...")
        
        # 啟動線程
        com_thread = threading.Thread(target=simulate_com_event)
        main_thread = threading.Thread(target=simulate_main_thread)
        strategy_thread = threading.Thread(target=simulate_strategy_thread)
        
        com_thread.start()
        main_thread.start()
        strategy_thread.start()
        
        # 等待完成
        com_thread.join()
        main_thread.join()
        strategy_thread.join()
        
        # 檢查結果
        ui_updates = []
        while not log_queue.empty():
            ui_updates.append(log_queue.get_nowait())
        
        print(f"   📊 生成了{len(ui_updates)}個UI更新請求")
        
        if len(ui_updates) == 5:
            print("✅ 純Queue數據流模擬成功")
            return True
        else:
            print("❌ 純Queue數據流模擬失敗")
            return False
            
    except Exception as e:
        print(f"❌ 純Queue數據流模擬失敗: {e}")
        return False

def main():
    """主測試函數"""
    print("🚀 純Queue機制測試")
    print("=" * 50)
    
    tests = [
        ("LOG處理器移除檢查", test_log_handler_removal),
        ("Queue機制檢查", test_queue_mechanism),
        ("COM事件修改檢查", test_com_event_modification),
        ("純Queue數據流模擬", simulate_pure_queue_flow)
    ]
    
    results = []
    for test_name, test_func in tests:
        try:
            result = test_func()
            results.append((test_name, result))
        except Exception as e:
            print(f"❌ {test_name} 異常: {e}")
            results.append((test_name, False))
    
    # 總結報告
    print("\n" + "=" * 50)
    print("📊 測試結果總結:")
    
    all_passed = True
    for test_name, passed in results:
        status = "✅ 通過" if passed else "❌ 失敗"
        print(f"  {status} {test_name}")
        if not passed:
            all_passed = False
    
    print("\n" + "=" * 50)
    if all_passed:
        print("🎉 純Queue機制測試通過！")
        print("📝 現在應該只有Queue機制在運行，沒有LOG處理器干擾")
        print("📝 您應該不會再看到 '[DEBUG] LOG處理器收到' 的訊息")
    else:
        print("⚠️ 部分測試失敗，可能仍有舊機制殘留")
    
    return all_passed

if __name__ == "__main__":
    main()
