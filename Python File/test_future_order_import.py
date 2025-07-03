"""
測試future_order.py中的Queue基礎設施導入
"""

import sys
import os

print("🧪 測試future_order.py中的Queue基礎設施導入...")

try:
    # 模擬從order目錄導入
    from order.future_order import QUEUE_INFRASTRUCTURE_AVAILABLE
    
    print(f"📊 QUEUE_INFRASTRUCTURE_AVAILABLE = {QUEUE_INFRASTRUCTURE_AVAILABLE}")
    
    if QUEUE_INFRASTRUCTURE_AVAILABLE:
        print("✅ future_order.py中Queue基礎設施導入成功")
        
        # 測試創建FutureOrderFrame
        import tkinter as tk
        root = tk.Tk()
        root.withdraw()  # 隱藏主視窗
        
        # 創建測試框架
        test_frame = tk.Frame(root)
        
        # 模擬skcom_objects
        skcom_objects = {
            'SKCenter': None,
            'SKOrder': None,
            'SKQuote': None,
            'SKReply': None
        }
        
        from order.future_order import FutureOrderFrame
        future_frame = FutureOrderFrame(test_frame, skcom_objects)
        
        # 檢查是否有Queue控制面板相關屬性
        has_queue_panel = hasattr(future_frame, 'queue_infrastructure')
        has_queue_buttons = hasattr(future_frame, 'btn_start_queue')
        
        print(f"📊 Queue基礎設施屬性: {has_queue_panel}")
        print(f"📊 Queue控制按鈕: {has_queue_buttons}")
        
        if has_queue_panel and has_queue_buttons:
            print("🎉 Queue控制面板應該已正確創建！")
        else:
            print("⚠️ Queue控制面板可能未正確創建")
        
        root.destroy()
        
    else:
        print("❌ future_order.py中Queue基礎設施導入失敗")
        print("🔧 請檢查queue_infrastructure目錄和檔案")
        
except Exception as e:
    print(f"❌ 測試過程中發生錯誤: {e}")
    import traceback
    traceback.print_exc()

print("\n💡 如果測試成功，重新啟動OrderTester.py應該就能看到Queue控制面板了")
