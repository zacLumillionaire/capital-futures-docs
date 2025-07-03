"""
GIL監控實際應用示例
==================

展示如何在現有的群益API代碼中添加GIL監控，
幫助開發階段快速定位可能的GIL錯誤問題。

這個示例展示：
1. 如何為COM事件添加監控
2. 如何為UI操作添加監控
3. 如何使用裝飾器進行自動監控
4. 如何手動記錄危險操作

作者: 開發階段GIL錯誤調試工具
日期: 2025-07-03
"""

import tkinter as tk
import threading
import time
import random
from datetime import datetime

# 導入GIL監控工具
from gil_monitor import log_ui_operation, log_com_event, print_gil_report
from gil_decorators import (
    com_event_monitor, ui_function_monitor, 
    log_dangerous_operation, check_thread_safety
)

class MonitoredQuoteEvents:
    """
    帶有GIL監控的報價事件處理類
    
    展示如何在COM事件處理中添加監控
    """
    
    def __init__(self, parent):
        self.parent = parent
    
    @com_event_monitor
    def OnNotifyTicksLONG(self, sMarketNo, nStockidx, nPtr, lDate, lTimehms, 
                         lTimemillismicros, nBid, nAsk, nClose, nQty, nSimulate):
        """
        Tick事件處理 - 帶有完整GIL監控
        
        這個函數展示如何正確監控COM事件
        """
        try:
            # 🔍 記錄COM事件詳情
            log_com_event(
                "OnNotifyTicksLONG",
                f"價格:{nClose} 買:{nBid} 賣:{nAsk} 量:{nQty}",
                has_ui_operations=True  # 標記有UI操作
            )
            
            # ⚠️ 檢查線程安全性
            if not check_thread_safety("OnNotifyTicksLONG"):
                log_dangerous_operation(
                    "COM事件中的UI操作", 
                    "OnNotifyTicksLONG"
                )
            
            # 🔧 安全的數據更新（不直接操作UI）
            with self.parent.data_lock:
                self.parent.last_price = nClose
                self.parent.last_time = lTimehms
            
            # 🔧 使用after_idle安全地安排UI更新
            self.parent.after_idle(
                self.parent.safe_update_price_display,
                nClose, lTimehms, nBid, nAsk, nQty
            )
            
        except Exception as e:
            # 🛡️ COM事件絕不能拋出異常
            log_dangerous_operation(f"COM事件異常: {e}", "OnNotifyTicksLONG")
            return 0
    
    @com_event_monitor
    def OnNotifyQuoteLONG(self, sMarketNo, nStockidx):
        """
        報價事件處理 - 帶有GIL監控
        """
        try:
            log_com_event("OnNotifyQuoteLONG", f"市場:{sMarketNo} 指數:{nStockidx}")
            
            # 模擬獲取報價數據
            price_data = {
                'market_no': sMarketNo,
                'stock_idx': nStockidx,
                'timestamp': datetime.now()
            }
            
            # 安全地通知主線程
            self.parent.after_idle(
                self.parent.safe_update_quote_display,
                price_data
            )
            
        except Exception as e:
            log_dangerous_operation(f"報價事件異常: {e}", "OnNotifyQuoteLONG")
            return 0
    
    @com_event_monitor
    def OnConnection(self, nKind, nCode):
        """
        連線事件處理 - 帶有GIL監控
        """
        try:
            connection_status = {
                3001: "已連線",
                3002: "已斷線", 
                3003: "商品資料準備完成",
                3021: "連線錯誤"
            }.get(nKind, f"未知狀態({nKind})")
            
            log_com_event("OnConnection", f"狀態:{connection_status} 代碼:{nCode}")
            
            # 安全地更新連線狀態
            self.parent.after_idle(
                self.parent.safe_update_connection_status,
                nKind, nCode, connection_status
            )
            
        except Exception as e:
            log_dangerous_operation(f"連線事件異常: {e}", "OnConnection")
            return 0

class MonitoredUIFrame(tk.Frame):
    """
    帶有GIL監控的UI框架
    
    展示如何在UI操作中添加監控
    """
    
    def __init__(self, master):
        super().__init__(master)
        
        # 數據鎖
        self.data_lock = threading.Lock()
        self.last_price = 0
        self.last_time = 0
        
        # 創建UI
        self.create_ui()
        
        # 創建事件處理器
        self.quote_events = MonitoredQuoteEvents(self)
    
    def create_ui(self):
        """創建UI控件"""
        # 價格顯示
        tk.Label(self, text="當前價格:").pack()
        self.price_label = tk.Label(self, text="--", font=("Arial", 16))
        self.price_label.pack()
        
        # 時間顯示
        tk.Label(self, text="更新時間:").pack()
        self.time_label = tk.Label(self, text="--")
        self.time_label.pack()
        
        # 連線狀態
        tk.Label(self, text="連線狀態:").pack()
        self.status_label = tk.Label(self, text="未連線", fg="red")
        self.status_label.pack()
        
        # 測試按鈕
        tk.Button(self, text="模擬Tick事件", 
                 command=self.simulate_tick_event).pack(pady=5)
        tk.Button(self, text="模擬報價事件", 
                 command=self.simulate_quote_event).pack(pady=5)
        tk.Button(self, text="模擬連線事件", 
                 command=self.simulate_connection_event).pack(pady=5)
        tk.Button(self, text="危險操作測試", 
                 command=self.test_dangerous_operation).pack(pady=5)
        tk.Button(self, text="顯示監控報告", 
                 command=self.show_monitoring_report).pack(pady=5)
        
        # 日誌顯示
        tk.Label(self, text="操作日誌:").pack()
        self.log_text = tk.Text(self, height=10, width=60)
        self.log_text.pack(fill="both", expand=True)
    
    @ui_function_monitor
    def safe_update_price_display(self, price, time_hms, bid, ask, qty):
        """
        安全的價格顯示更新 - 帶有UI監控
        
        這個函數應該只在主線程中調用
        """
        try:
            # 🔍 記錄UI操作
            log_ui_operation(
                "price_display_update",
                f"價格:{price} 時間:{time_hms}",
                "Label"
            )
            
            # 格式化時間
            time_str = f"{time_hms:06d}"
            formatted_time = f"{time_str[:2]}:{time_str[2:4]}:{time_str[4:6]}"
            
            # 更新UI控件
            self.price_label.config(text=str(price))
            self.time_label.config(text=formatted_time)
            
            # 添加到日誌
            log_msg = f"[{formatted_time}] 價格更新: {price} (買:{bid} 賣:{ask} 量:{qty})"
            self.add_log_message(log_msg)
            
        except Exception as e:
            log_dangerous_operation(f"價格顯示更新失敗: {e}", "safe_update_price_display")
    
    @ui_function_monitor
    def safe_update_quote_display(self, quote_data):
        """安全的報價顯示更新"""
        try:
            log_ui_operation("quote_display_update", str(quote_data), "Label")
            
            log_msg = f"[報價] 市場:{quote_data['market_no']} 指數:{quote_data['stock_idx']}"
            self.add_log_message(log_msg)
            
        except Exception as e:
            log_dangerous_operation(f"報價顯示更新失敗: {e}", "safe_update_quote_display")
    
    @ui_function_monitor
    def safe_update_connection_status(self, kind, code, status_text):
        """安全的連線狀態更新"""
        try:
            log_ui_operation("connection_status_update", status_text, "Label")
            
            # 更新狀態標籤
            color = "green" if kind == 3001 else "red"
            self.status_label.config(text=status_text, fg=color)
            
            log_msg = f"[連線] {status_text} (代碼:{code})"
            self.add_log_message(log_msg)
            
        except Exception as e:
            log_dangerous_operation(f"連線狀態更新失敗: {e}", "safe_update_connection_status")
    
    def add_log_message(self, message):
        """添加日誌訊息"""
        try:
            # 🔍 檢查是否在主線程中
            if not check_thread_safety("add_log_message"):
                log_dangerous_operation("在背景線程中更新日誌", "add_log_message")
                return
            
            # 記錄UI操作
            log_ui_operation("text_insert", message, "Text")
            
            # 更新日誌顯示
            self.log_text.insert(tk.END, message + "\n")
            self.log_text.see(tk.END)
            
            # 限制日誌行數
            lines = self.log_text.get("1.0", tk.END).split("\n")
            if len(lines) > 100:
                self.log_text.delete("1.0", "10.0")
            
        except Exception as e:
            print(f"日誌更新失敗: {e}")
    
    def simulate_tick_event(self):
        """模擬Tick事件（在主線程中）"""
        # 模擬Tick數據
        price = random.randint(21900, 22100)
        bid = price - 1
        ask = price + 1
        qty = random.randint(1, 10)
        time_hms = int(datetime.now().strftime("%H%M%S"))
        
        # 調用事件處理器
        self.quote_events.OnNotifyTicksLONG(
            2, 1, 1, 20250703, time_hms, 0, bid, ask, price, qty, 0
        )
    
    def simulate_quote_event(self):
        """模擬報價事件"""
        self.quote_events.OnNotifyQuoteLONG(2, random.randint(1, 100))
    
    def simulate_connection_event(self):
        """模擬連線事件"""
        kinds = [3001, 3002, 3003, 3021]
        kind = random.choice(kinds)
        self.quote_events.OnConnection(kind, 0)
    
    def test_dangerous_operation(self):
        """測試危險操作（在背景線程中執行UI操作）"""
        def dangerous_ui_operation():
            """在背景線程中執行危險的UI操作"""
            try:
                # 🚨 這是危險的操作！在背景線程中直接操作UI
                log_dangerous_operation("背景線程直接UI操作", "test_dangerous_operation")
                
                # 模擬直接UI操作（會被監控器捕獲）
                log_ui_operation("dangerous_label_config", "危險操作測試", "Label")
                
                # 實際的危險操作（註釋掉避免真的崩潰）
                # self.price_label.config(text="危險操作！")
                
                print("⚠️ 危險操作已執行（已被監控器記錄）")
                
            except Exception as e:
                print(f"危險操作失敗: {e}")
        
        # 在背景線程中執行
        thread = threading.Thread(target=dangerous_ui_operation, name="DangerousThread")
        thread.start()
    
    def show_monitoring_report(self):
        """顯示監控報告"""
        print_gil_report()
        self.add_log_message("監控報告已輸出到控制台")

class MonitoringTestApp:
    """GIL監控測試應用程式"""
    
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("GIL監控測試應用程式")
        self.root.geometry("800x600")
        
        # 創建監控框架
        self.frame = MonitoredUIFrame(self.root)
        self.frame.pack(fill="both", expand=True, padx=10, pady=10)
        
        # 添加說明
        info_text = """
🔍 GIL監控測試說明：
1. 點擊「模擬事件」按鈕測試正常操作
2. 點擊「危險操作測試」模擬GIL錯誤情況
3. 點擊「顯示監控報告」查看監控統計
4. 查看控制台輸出了解詳細監控信息
5. 檢查 gil_monitor.log 文件查看完整日誌
        """
        
        info_label = tk.Label(self.root, text=info_text, justify="left", 
                             font=("Arial", 9), fg="blue")
        info_label.pack(pady=5)
    
    def run(self):
        """運行測試應用程式"""
        print("🚀 GIL監控測試應用程式啟動")
        print("📋 監控功能已啟用，所有操作都會被記錄")
        print("📄 詳細日誌請查看 gil_monitor.log 文件")
        
        try:
            self.root.mainloop()
        except Exception as e:
            print(f"應用程式錯誤: {e}")
        finally:
            print("📊 最終監控報告:")
            print_gil_report()

if __name__ == "__main__":
    app = MonitoringTestApp()
    app.run()
