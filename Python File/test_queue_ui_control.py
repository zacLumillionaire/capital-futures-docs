"""
測試Queue UI控制面板
驗證新增的Queue控制功能
"""

import tkinter as tk
from tkinter import ttk
import time
import threading
from datetime import datetime

# 導入Queue基礎設施
try:
    from queue_infrastructure import (
        get_queue_infrastructure,
        TickData,
        get_queue_manager,
        reset_queue_infrastructure
    )
    print("✅ Queue基礎設施導入成功")
except ImportError as e:
    print(f"❌ Queue基礎設施導入失敗: {e}")
    exit(1)

class QueueUITestApp:
    """Queue UI控制面板測試應用"""
    
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("Queue UI控制面板測試")
        self.root.geometry("800x600")
        
        # Queue基礎設施
        self.queue_infrastructure = None
        self.queue_mode_enabled = False
        
        # 測試控制
        self.test_running = False
        self.test_thread = None
        
        self.create_widgets()
        self.init_queue_infrastructure()
        
    def create_widgets(self):
        """創建UI控件"""
        # 標題
        title_frame = tk.Frame(self.root, bg="navy", height=50)
        title_frame.pack(fill="x", padx=5, pady=5)
        title_frame.pack_propagate(False)
        
        title_label = tk.Label(title_frame, text="🧪 Queue UI控制面板測試", 
                              fg="white", bg="navy", font=("Arial", 16, "bold"))
        title_label.pack(expand=True)
        
        # Queue控制面板 (模擬future_order.py中的面板)
        self.create_queue_control_panel()
        
        # 測試控制面板
        test_frame = tk.LabelFrame(self.root, text="測試控制", font=("Arial", 12, "bold"))
        test_frame.pack(fill="x", padx=10, pady=5)
        
        button_frame = tk.Frame(test_frame)
        button_frame.pack(fill="x", padx=5, pady=5)
        
        tk.Button(button_frame, text="🚀 開始模擬Tick", 
                 command=self.start_tick_simulation,
                 bg="green", fg="white", font=("Arial", 10, "bold")).pack(side="left", padx=5)
        
        tk.Button(button_frame, text="🛑 停止模擬", 
                 command=self.stop_tick_simulation,
                 bg="red", fg="white", font=("Arial", 10, "bold")).pack(side="left", padx=5)
        
        # 日誌顯示
        log_frame = tk.LabelFrame(self.root, text="系統日誌", font=("Arial", 12, "bold"))
        log_frame.pack(fill="both", expand=True, padx=10, pady=5)
        
        self.log_text = tk.Text(log_frame, font=("Consolas", 9))
        log_scrollbar = tk.Scrollbar(log_frame, orient="vertical", command=self.log_text.yview)
        self.log_text.configure(yscrollcommand=log_scrollbar.set)
        
        self.log_text.pack(side="left", fill="both", expand=True)
        log_scrollbar.pack(side="right", fill="y")
        
    def create_queue_control_panel(self):
        """創建Queue控制面板 (模擬future_order.py中的實現)"""
        # Queue控制面板
        queue_frame = tk.LabelFrame(self.root, text="🚀 Queue架構控制", fg="blue", padx=10, pady=5)
        queue_frame.pack(fill="x", padx=10, pady=5)

        # 第一行：狀態顯示
        status_row = tk.Frame(queue_frame)
        status_row.pack(fill="x", pady=5)

        tk.Label(status_row, text="Queue狀態:", font=("Arial", 10, "bold")).pack(side="left", padx=5)
        
        self.queue_status_label = tk.Label(status_row, text="未初始化", fg="gray", font=("Arial", 10))
        self.queue_status_label.pack(side="left", padx=5)

        # 第二行：控制按鈕
        control_row = tk.Frame(queue_frame)
        control_row.pack(fill="x", pady=5)

        # 啟動Queue服務按鈕
        self.btn_start_queue = tk.Button(control_row, text="🚀 啟動Queue服務",
                                        command=self.on_start_queue_services,
                                        bg="green", fg="white", font=("Arial", 9, "bold"))
        self.btn_start_queue.pack(side="left", padx=5)

        # 停止Queue服務按鈕
        self.btn_stop_queue = tk.Button(control_row, text="🛑 停止Queue服務",
                                       command=self.on_stop_queue_services,
                                       bg="red", fg="white", font=("Arial", 9, "bold"))
        self.btn_stop_queue.pack(side="left", padx=5)

        # 查看Queue狀態按鈕
        self.btn_queue_status = tk.Button(control_row, text="📊 查看狀態",
                                         command=self.on_show_queue_status,
                                         bg="orange", fg="white", font=("Arial", 9, "bold"))
        self.btn_queue_status.pack(side="left", padx=5)

        # 切換模式按鈕
        self.btn_toggle_mode = tk.Button(control_row, text="🔄 切換模式",
                                        command=self.on_toggle_queue_mode,
                                        bg="purple", fg="white", font=("Arial", 9, "bold"))
        self.btn_toggle_mode.pack(side="left", padx=5)

    def init_queue_infrastructure(self):
        """初始化Queue基礎設施"""
        try:
            self.add_message("🔧 正在初始化Queue基礎設施...")
            
            # 重置之前的實例
            reset_queue_infrastructure()
            
            # 創建新的基礎設施
            self.queue_infrastructure = get_queue_infrastructure(self.root)
            
            if self.queue_infrastructure.initialize():
                self.add_message("✅ Queue基礎設施初始化成功")
                
                # 添加日誌回調
                self.queue_infrastructure.add_log_callback(self.on_queue_log_message)
                
                self.queue_mode_enabled = True
                self.update_queue_control_buttons()
            else:
                self.add_message("❌ Queue基礎設施初始化失敗")
                
        except Exception as e:
            self.add_message(f"❌ Queue基礎設施初始化錯誤: {str(e)}")
    
    def on_queue_log_message(self, message, level, source):
        """處理來自Queue的日誌訊息"""
        try:
            # 根據來源決定顯示格式
            if source == "TICK":
                # 控制Tick日誌頻率
                if not hasattr(self, '_last_queue_tick_time'):
                    self._last_queue_tick_time = 0
                
                current_time = time.time()
                if current_time - self._last_queue_tick_time > 1:  # 每1秒顯示一次
                    self._last_queue_tick_time = current_time
                    self.add_message(f"[Queue-Tick] {message}")
            else:
                self.add_message(f"[Queue-{source}] {message}")
                
        except Exception as e:
            pass  # 忽略日誌處理錯誤
    
    def update_queue_control_buttons(self):
        """更新Queue控制按鈕狀態"""
        try:
            if self.queue_mode_enabled and self.queue_infrastructure:
                status = self.queue_infrastructure.get_status()
                if status.get('running', False):
                    self.queue_status_label.config(text="✅ 運行中", fg="green")
                    self.btn_start_queue.config(state="disabled")
                    self.btn_stop_queue.config(state="normal")
                else:
                    self.queue_status_label.config(text="⏸️ 已初始化", fg="orange")
                    self.btn_start_queue.config(state="normal")
                    self.btn_stop_queue.config(state="disabled")
                
                self.btn_toggle_mode.config(text="🔄 切換到傳統模式")
            else:
                self.queue_status_label.config(text="🔄 傳統模式", fg="blue")
                self.btn_start_queue.config(state="disabled")
                self.btn_stop_queue.config(state="disabled")
                self.btn_toggle_mode.config(text="🚀 切換到Queue模式")

        except Exception as e:
            self.queue_status_label.config(text=f"錯誤: {str(e)}", fg="red")
    
    def on_start_queue_services(self):
        """啟動Queue服務"""
        if self.queue_infrastructure and self.queue_infrastructure.start_all():
            self.add_message("🚀 Queue服務已全部啟動")
            self.update_queue_control_buttons()
        else:
            self.add_message("❌ Queue服務啟動失敗")
    
    def on_stop_queue_services(self):
        """停止Queue服務"""
        if self.queue_infrastructure:
            self.queue_infrastructure.stop_all()
            self.add_message("🛑 Queue服務已全部停止")
            self.update_queue_control_buttons()
    
    def on_show_queue_status(self):
        """顯示Queue狀態"""
        if not self.queue_infrastructure:
            self.add_message("❌ Queue基礎設施未初始化")
            return
        
        status = self.queue_infrastructure.get_status()
        status_msg = f"""
📊 Queue基礎設施狀態:
🔧 初始化: {'✅' if status.get('initialized') else '❌'}
🚀 運行狀態: {'✅' if status.get('running') else '❌'}
📦 Tick佇列: {status.get('queue_manager', {}).get('tick_queue_size', 0)}/{status.get('queue_manager', {}).get('tick_queue_maxsize', 0)}
📝 日誌佇列: {status.get('queue_manager', {}).get('log_queue_size', 0)}/{status.get('queue_manager', {}).get('log_queue_maxsize', 0)}
📈 已處理Tick: {status.get('queue_manager', {}).get('stats', {}).get('tick_processed', 0)}
        """
        self.add_message(status_msg)
    
    def on_toggle_queue_mode(self):
        """切換Queue模式"""
        try:
            if self.queue_mode_enabled:
                # 切換到傳統模式
                if self.queue_infrastructure:
                    self.queue_infrastructure.stop_all()
                self.queue_mode_enabled = False
                self.add_message("🔄 已切換到傳統模式")
            else:
                # 切換到Queue模式
                if self.queue_infrastructure and self.queue_infrastructure.initialized:
                    self.queue_mode_enabled = True
                    self.add_message("🚀 已切換到Queue模式")
                else:
                    self.add_message("❌ Queue基礎設施未初始化")
                    return

            self.update_queue_control_buttons()

        except Exception as e:
            self.add_message(f"❌ 切換模式錯誤: {str(e)}")
    
    def start_tick_simulation(self):
        """開始Tick模擬"""
        if not self.queue_infrastructure or not self.queue_mode_enabled:
            self.add_message("❌ 請先啟用Queue模式")
            return
        
        self.test_running = True
        self.test_thread = threading.Thread(target=self.tick_simulation_loop, daemon=True)
        self.test_thread.start()
        self.add_message("🚀 Tick模擬已開始")
    
    def stop_tick_simulation(self):
        """停止Tick模擬"""
        self.test_running = False
        self.add_message("🛑 Tick模擬已停止")
    
    def tick_simulation_loop(self):
        """Tick模擬循環"""
        base_price = 22461
        counter = 0
        
        while self.test_running:
            try:
                # 生成模擬Tick
                price_change = counter % 10 - 5  # -5到+4的變化
                current_price = base_price + price_change
                
                tick_data = TickData(
                    market_no="TW",
                    stock_idx=1,
                    date=20250703,
                    time_hms=143000 + counter,
                    time_millis=(counter * 100) % 1000,
                    bid=current_price - 1,
                    ask=current_price + 1,
                    close=current_price,
                    qty=1 + (counter % 5),
                    timestamp=datetime.now()
                )
                
                # 發送到Queue
                if self.queue_infrastructure:
                    self.queue_infrastructure.put_tick_data(
                        tick_data.market_no,
                        tick_data.stock_idx,
                        tick_data.date,
                        tick_data.time_hms,
                        tick_data.time_millis,
                        tick_data.bid,
                        tick_data.ask,
                        tick_data.close,
                        tick_data.qty,
                        tick_data.timestamp
                    )
                
                counter += 1
                time.sleep(0.5)  # 每500ms一個Tick
                
            except Exception as e:
                self.add_message(f"❌ Tick模擬錯誤: {e}")
                break
    
    def add_message(self, message):
        """添加日誌訊息"""
        timestamp = datetime.now().strftime("%H:%M:%S")
        log_entry = f"[{timestamp}] {message}\n"
        
        self.log_text.insert(tk.END, log_entry)
        self.log_text.see(tk.END)
    
    def on_closing(self):
        """關閉程式時的清理"""
        try:
            self.test_running = False
            if self.queue_infrastructure:
                self.queue_infrastructure.stop_all()
            reset_queue_infrastructure()
        except Exception as e:
            print(f"清理錯誤: {e}")
        
        self.root.destroy()
    
    def run(self):
        """運行測試程式"""
        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)
        self.root.mainloop()

if __name__ == "__main__":
    print("🧪 啟動Queue UI控制面板測試...")
    app = QueueUITestApp()
    app.run()
