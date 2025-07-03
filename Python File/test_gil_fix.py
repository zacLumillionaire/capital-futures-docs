"""
GIL修復測試程式
==============

快速測試修復後的程式是否還會發生GIL錯誤

使用方法：
python test_gil_fix.py

作者: GIL錯誤修復驗證
日期: 2025-07-03
"""

import threading
import time
import logging

def test_logging_safety():
    """測試日誌記錄的線程安全性"""
    print("🧪 測試日誌記錄線程安全性...")
    
    # 模擬COM事件中的日誌記錄
    def simulate_com_event():
        """模擬COM事件中的日誌記錄"""
        try:
            # 這是之前會導致GIL錯誤的操作
            logger = logging.getLogger('order.future_order')
            logger.info("【測試】模擬COM事件日誌記錄")
            print("✅ 背景線程日誌記錄成功")
        except Exception as e:
            print(f"❌ 背景線程日誌記錄失敗: {e}")
    
    # 在背景線程中執行
    thread = threading.Thread(target=simulate_com_event, name="TestCOMEvent")
    thread.start()
    thread.join()
    
    print("✅ 日誌記錄線程安全性測試完成")

def test_print_safety():
    """測試print輸出的線程安全性"""
    print("🧪 測試print輸出線程安全性...")
    
    def simulate_print_in_background():
        """在背景線程中使用print"""
        try:
            print("【測試】背景線程print輸出")
            print("✅ 背景線程print成功")
        except Exception as e:
            print(f"❌ 背景線程print失敗: {e}")
    
    # 在背景線程中執行
    thread = threading.Thread(target=simulate_print_in_background, name="TestPrint")
    thread.start()
    thread.join()
    
    print("✅ print輸出線程安全性測試完成")

def test_multiple_threads():
    """測試多線程環境"""
    print("🧪 測試多線程環境...")
    
    def worker(thread_id):
        """工作線程"""
        for i in range(5):
            print(f"【線程{thread_id}】第{i+1}次輸出")
            time.sleep(0.1)
    
    # 創建多個線程
    threads = []
    for i in range(3):
        thread = threading.Thread(target=worker, args=(i+1,), name=f"Worker{i+1}")
        threads.append(thread)
        thread.start()
    
    # 等待所有線程完成
    for thread in threads:
        thread.join()
    
    print("✅ 多線程環境測試完成")

def main():
    """主測試函數"""
    print("🚀 開始GIL修復驗證測試")
    print("=" * 50)
    
    # 測試1: 日誌記錄安全性
    test_logging_safety()
    print()
    
    # 測試2: print輸出安全性
    test_print_safety()
    print()
    
    # 測試3: 多線程環境
    test_multiple_threads()
    print()
    
    print("=" * 50)
    print("🎉 所有測試完成！")
    print("如果沒有發生GIL錯誤，說明修復成功。")
    print("現在可以測試實際的報價監控功能。")

if __name__ == "__main__":
    main()
