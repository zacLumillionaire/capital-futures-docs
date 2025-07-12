#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Queue機制基礎測試
"""

import sys
import os
import time

def test_queue_import():
    """測試Queue相關導入"""
    print("🔍 測試Queue相關導入...")
    
    try:
        import queue
        import threading
        print("✅ queue模組導入成功")
        print("✅ threading模組導入成功")
        return True
    except ImportError as e:
        print(f"❌ 導入失敗: {e}")
        return False

def test_queue_creation():
    """測試Queue創建"""
    print("\n🔍 測試Queue創建...")
    
    try:
        import queue
        
        # 創建測試Queue
        tick_queue = queue.Queue(maxsize=1000)
        strategy_queue = queue.Queue(maxsize=100)
        log_queue = queue.Queue(maxsize=500)
        
        print("✅ tick_data_queue 創建成功")
        print("✅ strategy_queue 創建成功")
        print("✅ log_queue 創建成功")
        
        # 測試基本操作
        test_data = {'test': 'data'}
        tick_queue.put_nowait(test_data)
        retrieved_data = tick_queue.get_nowait()
        
        if retrieved_data == test_data:
            print("✅ Queue基本操作測試通過")
            return True
        else:
            print("❌ Queue基本操作測試失敗")
            return False
            
    except Exception as e:
        print(f"❌ Queue創建測試失敗: {e}")
        return False

def test_ordertester_import():
    """測試OrderTester導入"""
    print("\n🔍 測試OrderTester導入...")
    
    try:
        import OrderTester
        print("✅ OrderTester模組導入成功")
        
        # 檢查是否有Queue相關屬性
        app_class = OrderTester.OrderTesterApp
        
        # 創建一個測試實例來檢查__init__
        print("✅ OrderTesterApp類存在")
        return True
        
    except ImportError as e:
        print(f"❌ OrderTester導入失敗: {e}")
        return False
    except Exception as e:
        print(f"❌ OrderTester測試失敗: {e}")
        return False

def test_future_order_import():
    """測試future_order導入"""
    print("\n🔍 測試future_order導入...")
    
    try:
        from order import future_order
        print("✅ future_order模組導入成功")
        return True
        
    except ImportError as e:
        print(f"❌ future_order導入失敗: {e}")
        return False
    except Exception as e:
        print(f"❌ future_order測試失敗: {e}")
        return False

def main():
    """主測試函數"""
    print("🚀 Queue機制基礎測試")
    print("=" * 50)
    
    tests = [
        ("Queue導入測試", test_queue_import),
        ("Queue創建測試", test_queue_creation),
        ("OrderTester導入測試", test_ordertester_import),
        ("future_order導入測試", test_future_order_import)
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
        print("🎉 所有基礎測試通過！")
        print("📝 建議：現在可以嘗試啟動OrderTester.py")
        print("📝 檢查控制台是否顯示 '✅ Queue機制已初始化'")
    else:
        print("⚠️ 部分測試失敗，請檢查並修正問題")
    
    return all_passed

if __name__ == "__main__":
    main()
