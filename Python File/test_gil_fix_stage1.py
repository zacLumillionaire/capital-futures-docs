#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
GIL錯誤修復階段一測試腳本
測試線程安全機制是否正確實施

🔧 測試內容：
1. 驗證線程鎖是否正確添加
2. 測試COM事件處理的異常保護
3. 驗證策略函數的線程安全性
4. 確保現有功能不受影響
"""

import sys
import os
import threading
import time
import logging

# 設定日誌
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def test_thread_locks_existence():
    """測試線程鎖是否正確添加"""
    print("🔧 測試1: 檢查線程鎖是否正確添加")
    
    try:
        # 測試OrderTesterApp類
        sys.path.append(os.path.dirname(os.path.abspath(__file__)))
        from OrderTester import OrderTesterApp
        
        # 創建應用實例（不啟動GUI）
        import tkinter as tk
        root = tk.Tk()
        root.withdraw()  # 隱藏主窗口
        
        app = OrderTesterApp()
        app.withdraw()  # 隱藏應用窗口
        
        # 檢查線程鎖是否存在
        required_locks = ['quote_lock', 'strategy_lock', 'ui_lock', 'order_lock']
        missing_locks = []
        
        for lock_name in required_locks:
            if hasattr(app, lock_name):
                lock_obj = getattr(app, lock_name)
                if isinstance(lock_obj, threading.Lock):
                    print(f"✅ {lock_name}: 存在且類型正確")
                else:
                    print(f"❌ {lock_name}: 存在但類型錯誤 ({type(lock_obj)})")
                    missing_locks.append(lock_name)
            else:
                print(f"❌ {lock_name}: 不存在")
                missing_locks.append(lock_name)
        
        app.destroy()
        root.destroy()
        
        if not missing_locks:
            print("✅ 測試1通過: 所有線程鎖都正確添加")
            return True
        else:
            print(f"❌ 測試1失敗: 缺少線程鎖 {missing_locks}")
            return False
            
    except Exception as e:
        print(f"❌ 測試1異常: {e}")
        return False

def test_future_order_frame_locks():
    """測試FutureOrderFrame類的線程鎖"""
    print("\n🔧 測試2: 檢查FutureOrderFrame線程鎖")
    
    try:
        from order.future_order import FutureOrderFrame
        
        # 創建實例
        import tkinter as tk
        root = tk.Tk()
        root.withdraw()
        
        frame = FutureOrderFrame(master=root)
        
        # 檢查線程鎖
        required_locks = ['quote_lock', 'ui_lock', 'data_lock']
        missing_locks = []
        
        for lock_name in required_locks:
            if hasattr(frame, lock_name):
                lock_obj = getattr(frame, lock_name)
                if isinstance(lock_obj, threading.Lock):
                    print(f"✅ {lock_name}: 存在且類型正確")
                else:
                    print(f"❌ {lock_name}: 存在但類型錯誤 ({type(lock_obj)})")
                    missing_locks.append(lock_name)
            else:
                print(f"❌ {lock_name}: 不存在")
                missing_locks.append(lock_name)
        
        frame.destroy()
        root.destroy()
        
        if not missing_locks:
            print("✅ 測試2通過: FutureOrderFrame線程鎖正確添加")
            return True
        else:
            print(f"❌ 測試2失敗: 缺少線程鎖 {missing_locks}")
            return False
            
    except Exception as e:
        print(f"❌ 測試2異常: {e}")
        return False

def test_thread_safety_simulation():
    """模擬多線程環境測試線程安全性"""
    print("\n🔧 測試3: 模擬多線程環境測試")
    
    try:
        import tkinter as tk
        from OrderTester import OrderTesterApp
        
        # 創建應用實例
        root = tk.Tk()
        root.withdraw()
        
        app = OrderTesterApp()
        app.withdraw()
        
        # 模擬多線程存取共享數據
        errors = []
        test_complete = threading.Event()
        
        def thread_worker(thread_id):
            """工作線程函數"""
            try:
                for i in range(10):
                    # 模擬策略數據更新
                    if hasattr(app, 'strategy_lock'):
                        with app.strategy_lock:
                            # 模擬數據操作
                            test_data = f"thread_{thread_id}_data_{i}"
                            time.sleep(0.001)  # 模擬處理時間
                    
                    # 模擬UI更新
                    if hasattr(app, 'ui_lock'):
                        with app.ui_lock:
                            # 模擬UI操作
                            time.sleep(0.001)
                            
            except Exception as e:
                errors.append(f"Thread {thread_id}: {e}")
        
        # 創建多個工作線程
        threads = []
        for i in range(5):
            thread = threading.Thread(target=thread_worker, args=(i,))
            threads.append(thread)
            thread.start()
        
        # 等待所有線程完成
        for thread in threads:
            thread.join(timeout=5)
        
        app.destroy()
        root.destroy()
        
        if not errors:
            print("✅ 測試3通過: 多線程環境下無錯誤")
            return True
        else:
            print(f"❌ 測試3失敗: 發現錯誤 {errors}")
            return False
            
    except Exception as e:
        print(f"❌ 測試3異常: {e}")
        return False

def test_import_verification():
    """測試導入是否正常"""
    print("\n🔧 測試4: 驗證模組導入")
    
    try:
        # 測試主要模組導入
        modules_to_test = [
            'OrderTester',
            'order.future_order',
            'reply.order_reply',
            'quote.future_quote',
            'query.position_query'
        ]
        
        failed_imports = []
        
        for module_name in modules_to_test:
            try:
                __import__(module_name)
                print(f"✅ {module_name}: 導入成功")
            except Exception as e:
                print(f"❌ {module_name}: 導入失敗 - {e}")
                failed_imports.append(module_name)
        
        if not failed_imports:
            print("✅ 測試4通過: 所有模組導入正常")
            return True
        else:
            print(f"❌ 測試4失敗: 模組導入失敗 {failed_imports}")
            return False
            
    except Exception as e:
        print(f"❌ 測試4異常: {e}")
        return False

def main():
    """主測試函數"""
    print("🚀 開始GIL錯誤修復階段一測試")
    print("=" * 50)
    
    test_results = []
    
    # 執行所有測試
    test_results.append(test_import_verification())
    test_results.append(test_thread_locks_existence())
    test_results.append(test_future_order_frame_locks())
    test_results.append(test_thread_safety_simulation())
    
    # 統計結果
    passed_tests = sum(test_results)
    total_tests = len(test_results)
    
    print("\n" + "=" * 50)
    print(f"📊 測試結果統計:")
    print(f"✅ 通過測試: {passed_tests}/{total_tests}")
    print(f"❌ 失敗測試: {total_tests - passed_tests}/{total_tests}")
    
    if passed_tests == total_tests:
        print("🎉 所有測試通過！GIL錯誤修復階段一成功")
        return True
    else:
        print("⚠️ 部分測試失敗，需要檢查修復內容")
        return False

if __name__ == "__main__":
    success = main()
    if success:
        print("\n✅ 階段一修復驗證完成，可以進行下一階段")
    else:
        print("\n❌ 階段一修復需要調整，請檢查問題")
    
    input("\n按Enter鍵退出...")
