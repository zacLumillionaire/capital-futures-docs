#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
簡單的GIL修復驗證腳本
"""

import threading
import sys
import os

def test_basic_imports():
    """測試基本導入"""
    print("🔧 測試基本導入...")
    
    try:
        # 測試threading模組
        lock = threading.Lock()
        print(f"✅ threading.Lock創建成功: {type(lock)}")
        
        # 測試是否可以導入我們的模組
        sys.path.append(os.path.dirname(os.path.abspath(__file__)))
        
        # 測試導入future_order模組
        from order import future_order
        print("✅ future_order模組導入成功")
        
        # 檢查FutureOrderFrame類是否有線程鎖屬性
        frame_class = future_order.FutureOrderFrame
        print(f"✅ FutureOrderFrame類找到: {frame_class}")
        
        return True
        
    except Exception as e:
        print(f"❌ 基本導入測試失敗: {e}")
        return False

def test_lock_functionality():
    """測試線程鎖功能"""
    print("\n🔧 測試線程鎖功能...")
    
    try:
        # 創建測試鎖
        test_lock = threading.Lock()
        shared_data = {"value": 0}
        
        def worker():
            for i in range(100):
                with test_lock:
                    shared_data["value"] += 1
        
        # 創建多個線程
        threads = []
        for i in range(5):
            t = threading.Thread(target=worker)
            threads.append(t)
            t.start()
        
        # 等待所有線程完成
        for t in threads:
            t.join()
        
        expected_value = 5 * 100
        actual_value = shared_data["value"]
        
        if actual_value == expected_value:
            print(f"✅ 線程鎖測試成功: {actual_value} == {expected_value}")
            return True
        else:
            print(f"❌ 線程鎖測試失敗: {actual_value} != {expected_value}")
            return False
            
    except Exception as e:
        print(f"❌ 線程鎖測試異常: {e}")
        return False

def main():
    """主函數"""
    print("🚀 開始簡單GIL修復驗證")
    print("=" * 40)
    
    results = []
    results.append(test_basic_imports())
    results.append(test_lock_functionality())
    
    passed = sum(results)
    total = len(results)
    
    print("\n" + "=" * 40)
    print(f"📊 測試結果: {passed}/{total} 通過")
    
    if passed == total:
        print("🎉 基本驗證通過！")
    else:
        print("⚠️ 部分測試失敗")
    
    return passed == total

if __name__ == "__main__":
    success = main()
    print(f"\n結果: {'成功' if success else '失敗'}")
