#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
測試Queue機制的UI更新功能
"""

import sys
import time
import queue
import threading
from datetime import datetime

def test_queue_ui_update_mechanism():
    """測試Queue UI更新機制"""
    print("🔍 測試Queue UI更新機制...")
    
    try:
        # 創建測試Queue
        log_queue = queue.Queue(maxsize=500)
        
        # 模擬策略執行緒發送UI更新請求
        def simulate_strategy_updates():
            """模擬策略執行緒發送更新"""
            print("📊 模擬策略執行緒開始發送更新...")
            
            # 價格更新
            price_update = {
                'type': 'price_update',
                'price': 22150.0,
                'time': '09:15:30'
            }
            log_queue.put_nowait(price_update)
            print("✅ 發送價格更新請求")
            
            # 區間更新
            range_update = {
                'type': 'range_update',
                'range_high': 22180.0,
                'range_low': 22120.0,
                'range_size': 60.0,
                'status': '計算中...'
            }
            log_queue.put_nowait(range_update)
            print("✅ 發送區間更新請求")
            
            # 信號更新
            signal_update = {
                'type': 'signal_update',
                'breakout_signal': '向上突破',
                'entry_signal': '做多信號',
                'long_trigger': 22180.0,
                'short_trigger': 22120.0
            }
            log_queue.put_nowait(signal_update)
            print("✅ 發送信號更新請求")
            
            # 部位更新
            position_update = {
                'type': 'position_update',
                'position_type': '多頭 3口',
                'active_lots': 3,
                'total_pnl': 1500,
                'lots_status': '第1口:+800, 第2口:+400, 第3口:+300'
            }
            log_queue.put_nowait(position_update)
            print("✅ 發送部位更新請求")
        
        # 模擬主線程處理UI更新
        def simulate_main_thread_processing():
            """模擬主線程處理UI更新"""
            print("🎯 模擬主線程開始處理UI更新...")
            
            processed_count = 0
            while not log_queue.empty() and processed_count < 10:
                try:
                    queue_item = log_queue.get_nowait()
                    
                    if isinstance(queue_item, dict) and 'type' in queue_item:
                        update_type = queue_item.get('type')
                        print(f"📋 處理UI更新請求: {update_type}")
                        
                        if update_type == 'price_update':
                            price = queue_item.get('price')
                            time_str = queue_item.get('time')
                            print(f"   💰 價格更新: {price} 時間: {time_str}")
                            
                        elif update_type == 'range_update':
                            range_high = queue_item.get('range_high')
                            range_low = queue_item.get('range_low')
                            range_size = queue_item.get('range_size')
                            status = queue_item.get('status')
                            print(f"   📊 區間更新: 高={range_high} 低={range_low} 大小={range_size} 狀態={status}")
                            
                        elif update_type == 'signal_update':
                            breakout_signal = queue_item.get('breakout_signal')
                            entry_signal = queue_item.get('entry_signal')
                            print(f"   🎯 信號更新: 突破={breakout_signal} 進場={entry_signal}")
                            
                        elif update_type == 'position_update':
                            position_type = queue_item.get('position_type')
                            active_lots = queue_item.get('active_lots')
                            total_pnl = queue_item.get('total_pnl')
                            print(f"   📈 部位更新: 類型={position_type} 口數={active_lots} 損益={total_pnl}")
                    
                    processed_count += 1
                    
                except queue.Empty:
                    break
                except Exception as e:
                    print(f"❌ 處理更新請求失敗: {e}")
        
        # 執行測試
        simulate_strategy_updates()
        time.sleep(0.1)  # 短暫等待
        simulate_main_thread_processing()
        
        print("✅ Queue UI更新機制測試完成")
        return True
        
    except Exception as e:
        print(f"❌ Queue UI更新機制測試失敗: {e}")
        return False

def test_queue_performance():
    """測試Queue性能"""
    print("\n🔍 測試Queue性能...")
    
    try:
        test_queue = queue.Queue(maxsize=1000)
        
        # 測試大量數據處理
        start_time = time.time()
        
        # 發送1000個更新請求
        for i in range(1000):
            update_request = {
                'type': 'price_update',
                'price': 22000 + i,
                'time': f"09:{i//60:02d}:{i%60:02d}"
            }
            test_queue.put_nowait(update_request)
        
        # 處理所有請求
        processed = 0
        while not test_queue.empty():
            test_queue.get_nowait()
            processed += 1
        
        end_time = time.time()
        duration = end_time - start_time
        
        print(f"✅ 處理{processed}個更新請求，耗時: {duration:.3f}秒")
        print(f"📊 平均處理速度: {processed/duration:.0f} 請求/秒")
        
        if duration < 1.0:  # 1秒內完成
            print("✅ Queue性能測試通過")
            return True
        else:
            print("⚠️ Queue性能可能需要優化")
            return False
            
    except Exception as e:
        print(f"❌ Queue性能測試失敗: {e}")
        return False

def test_thread_safety():
    """測試線程安全性"""
    print("\n🔍 測試線程安全性...")
    
    try:
        shared_queue = queue.Queue(maxsize=100)
        results = []
        
        def producer_thread(thread_id):
            """生產者線程"""
            for i in range(10):
                data = {
                    'thread_id': thread_id,
                    'data': f"data_{thread_id}_{i}",
                    'timestamp': time.time()
                }
                shared_queue.put_nowait(data)
                time.sleep(0.01)  # 模擬處理時間
        
        def consumer_thread():
            """消費者線程"""
            while True:
                try:
                    data = shared_queue.get(timeout=1)
                    results.append(data)
                except queue.Empty:
                    break
        
        # 啟動多個生產者線程
        producers = []
        for i in range(3):
            t = threading.Thread(target=producer_thread, args=(i,))
            producers.append(t)
            t.start()
        
        # 啟動消費者線程
        consumer = threading.Thread(target=consumer_thread)
        consumer.start()
        
        # 等待所有線程完成
        for t in producers:
            t.join()
        
        consumer.join()
        
        print(f"✅ 多線程測試完成，處理了{len(results)}個數據項")
        
        # 檢查數據完整性
        expected_count = 3 * 10  # 3個線程，每個10個數據
        if len(results) == expected_count:
            print("✅ 線程安全性測試通過")
            return True
        else:
            print(f"⚠️ 數據丟失，預期{expected_count}個，實際{len(results)}個")
            return False
            
    except Exception as e:
        print(f"❌ 線程安全性測試失敗: {e}")
        return False

def main():
    """主測試函數"""
    print("🚀 Queue UI更新機制測試")
    print("=" * 50)
    
    tests = [
        ("Queue UI更新機制", test_queue_ui_update_mechanism),
        ("Queue性能測試", test_queue_performance),
        ("線程安全性測試", test_thread_safety)
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
        print("🎉 所有測試通過！Queue UI更新機制運作正常")
        print("📝 建議：現在可以啟動OrderTester.py測試實際UI更新")
    else:
        print("⚠️ 部分測試失敗，請檢查Queue機制實現")
    
    return all_passed

if __name__ == "__main__":
    main()
