"""
檢查Queue控制面板是否存在
幫助用戶找到Queue控制面板的位置
"""

import tkinter as tk
from tkinter import ttk
import time

def create_demo_with_queue_panel():
    """創建一個演示視窗，顯示Queue控制面板應該在哪裡"""
    
    print("🔍 創建演示視窗，顯示Queue控制面板位置...")
    
    # 創建主視窗
    root = tk.Tk()
    root.title("Queue控制面板位置演示")
    root.geometry("800x600")
    
    # 創建說明
    info_frame = tk.Frame(root, bg="lightblue", height=80)
    info_frame.pack(fill="x", padx=10, pady=10)
    info_frame.pack_propagate(False)
    
    tk.Label(info_frame, text="📍 Queue控制面板位置演示", 
             bg="lightblue", font=("Arial", 16, "bold")).pack(pady=10)
    tk.Label(info_frame, text="在OrderTester.py的「期貨下單」分頁中，應該在成交回報區域下方", 
             bg="lightblue", font=("Arial", 10)).pack()
    
    # 模擬期貨下單頁面結構
    main_frame = tk.Frame(root)
    main_frame.pack(fill="both", expand=True, padx=10, pady=5)
    
    # 模擬下單區域
    order_frame = tk.LabelFrame(main_frame, text="📋 下單區域 (模擬)", fg="green")
    order_frame.pack(fill="x", pady=5)
    tk.Label(order_frame, text="這裡是下單控制項...").pack(pady=10)
    
    # 模擬即時報價區域
    quote_frame = tk.LabelFrame(main_frame, text="📊 即時報價 (模擬)", fg="orange")
    quote_frame.pack(fill="x", pady=5)
    tk.Label(quote_frame, text="這裡是報價顯示...").pack(pady=10)
    
    # 模擬成交回報區域
    trade_frame = tk.LabelFrame(main_frame, text="📈 成交回報 (模擬)", fg="purple")
    trade_frame.pack(fill="x", pady=5)
    tk.Label(trade_frame, text="這裡是成交回報...").pack(pady=10)
    
    # 🎯 這裡就是Queue控制面板應該出現的位置！
    queue_frame = tk.LabelFrame(main_frame, text="🚀 Queue架構控制", fg="blue", padx=10, pady=5)
    queue_frame.pack(fill="x", pady=5)
    
    # 狀態顯示
    status_row = tk.Frame(queue_frame)
    status_row.pack(fill="x", pady=5)
    
    tk.Label(status_row, text="Queue狀態:", font=("Arial", 10, "bold")).pack(side="left", padx=5)
    status_label = tk.Label(status_row, text="✅ 這就是Queue控制面板！", fg="green", font=("Arial", 10, "bold"))
    status_label.pack(side="left", padx=5)
    
    # 控制按鈕
    control_row = tk.Frame(queue_frame)
    control_row.pack(fill="x", pady=5)
    
    tk.Button(control_row, text="🚀 啟動Queue服務", bg="green", fg="white", font=("Arial", 9, "bold")).pack(side="left", padx=5)
    tk.Button(control_row, text="🛑 停止Queue服務", bg="red", fg="white", font=("Arial", 9, "bold")).pack(side="left", padx=5)
    tk.Button(control_row, text="📊 查看狀態", bg="orange", fg="white", font=("Arial", 9, "bold")).pack(side="left", padx=5)
    tk.Button(control_row, text="🔄 切換模式", bg="purple", fg="white", font=("Arial", 9, "bold")).pack(side="left", padx=5)
    
    # 說明文字
    explanation_frame = tk.Frame(main_frame, bg="lightyellow")
    explanation_frame.pack(fill="x", pady=10)
    
    explanation_text = """
📝 如果您在OrderTester.py中沒有看到上面的「🚀 Queue架構控制」面板：

1. 檢查控制台輸出是否顯示：
   ✅ Queue基礎設施載入成功
   
2. 如果顯示載入失敗，請確認：
   • queue_infrastructure 資料夾在 Python File 目錄中
   • 所有 .py 檔案都存在且沒有語法錯誤
   
3. 如果載入成功但面板不顯示，可能是：
   • 面板被其他控件遮蓋
   • 視窗需要向下滾動才能看到
   • 初始化過程中發生錯誤

4. 解決方案：
   • 重新啟動 OrderTester.py
   • 檢查控制台錯誤訊息
   • 嘗試調整視窗大小或滾動查看
    """
    
    tk.Label(explanation_frame, text=explanation_text, bg="lightyellow", 
             font=("Arial", 9), justify="left").pack(padx=10, pady=10)
    
    # 關閉按鈕
    tk.Button(main_frame, text="關閉演示", command=root.destroy, 
              bg="gray", fg="white", font=("Arial", 10, "bold")).pack(pady=10)
    
    print("✅ 演示視窗已開啟")
    print("💡 請對比這個演示視窗與您的OrderTester.py")
    
    root.mainloop()

def check_queue_infrastructure_files():
    """檢查Queue基礎設施檔案是否存在"""
    import os
    
    print("🔍 檢查Queue基礎設施檔案...")
    
    required_files = [
        "queue_infrastructure/__init__.py",
        "queue_infrastructure/queue_manager.py", 
        "queue_infrastructure/tick_processor.py",
        "queue_infrastructure/ui_updater.py"
    ]
    
    all_exist = True
    for file_path in required_files:
        if os.path.exists(file_path):
            print(f"✅ {file_path}")
        else:
            print(f"❌ {file_path} - 檔案不存在")
            all_exist = False
    
    if all_exist:
        print("✅ 所有Queue基礎設施檔案都存在")
        
        # 測試導入
        try:
            from queue_infrastructure import get_queue_manager
            print("✅ Queue基礎設施可以正常導入")
            return True
        except ImportError as e:
            print(f"❌ Queue基礎設施導入失敗: {e}")
            return False
    else:
        print("❌ 部分Queue基礎設施檔案缺失")
        return False

def main():
    """主函數"""
    print("🔍 Queue控制面板檢查工具")
    print("=" * 50)
    
    # 檢查檔案
    files_ok = check_queue_infrastructure_files()
    
    if not files_ok:
        print("\n❌ Queue基礎設施檔案有問題")
        print("🔧 請確認 queue_infrastructure 資料夾及其檔案都存在")
        return
    
    print("\n📍 開啟演示視窗，顯示Queue控制面板應該出現的位置...")
    print("💡 請對比演示視窗與您的OrderTester.py")
    
    # 創建演示
    create_demo_with_queue_panel()

if __name__ == "__main__":
    main()
