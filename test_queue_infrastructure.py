"""
Queue基礎設施測試程式
驗證新的Queue架構是否正常運作

測試項目：
1. QueueManager基本功能
2. TickDataProcessor處理能力
3. UIUpdateManager安全性
4. 整體架構整合測試
"""

import tkinter as tk
import threading
import time
import random
from datetime import datetime
from queue_infrastructure import (
    QueueInfrastructure, 
    TickData, 
    get_queue_infrastructure,
    quick_setup
)

class QueueInfrastructureTest:
    """Queue基礎設施測試類別"""
    
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("Queue基礎設施測試")
        self.root.geometry("800x600")
        
        # Queue基礎設施
        self.infrastructure = None
        
        # 測試控制
        self.test_running = False
        self.test_thread = None
        
        # 統計資料
        self.test_stats = {
            'ticks_sent': 0,
            'logs_received': 0,
            'errors': 0,
            'start_time': None
        }
        
        self.create_widgets()
        
    def create_widgets(self):
        """建立測試UI"""
        # 標題
        title_frame = tk.Frame(self.root, bg="navy", height=50)
        title_frame.pack(fill="x", padx=5, pady=5)
        title_frame.pack_propagate(False)
        
        title_label = tk.Label(title_frame, text="🧪 Queue基礎設施測試", 
                              fg="white", bg="navy", font=("Arial", 16, "bold"))
        title_label.pack(expand=True)
        
        # 控制面板
        control_frame = tk.LabelFrame(self.root, text="測試控制", font=("Arial", 12, "bold"))
        control_frame.pack(fill="x", padx=10, pady=5)
        
        button_frame = tk.Frame(control_frame)
        button_frame.pack(fill="x", padx=5, pady=5)
        
        self.btn_init = tk.Button(button_frame, text="🔧 初始化基礎設施", 
                                 command=self.init_infrastructure,
                                 bg="blue", fg="white", font=("Arial", 10, "bold"))
        self.btn_init.pack(side="left", padx=5)
        
        self.btn_start = tk.Button(button_frame, text="🚀 開始測試", 
                                  command=self.start_test,
                                  bg="green", fg="white", font=("Arial", 10, "bold"),
                                  state="disabled")
        self.btn_start.pack(side="left", padx=5)
        
        self.btn_stop = tk.Button(button_frame, text="🛑 停止測試", 
                                 command=self.stop_test,
                                 bg="red", fg="white", font=("Arial", 10, "bold"),
                                 state="disabled")
        self.btn_stop.pack(side="left", padx=5)
        
        self.btn_status = tk.Button(button_frame, text="📊 查看狀態", 
                                   command=self.show_status,
                                   bg="orange", fg="white", font=("Arial", 10, "bold"))
        self.btn_status.pack(side="left", padx=5)
        
        # 統計面板
        stats_frame = tk.LabelFrame(self.root, text="測試統計", font=("Arial", 12, "bold"))
        stats_frame.pack(fill="x", padx=10, pady=5)
        
        self.stats_text = tk.Text(stats_frame, height=4, font=("Consolas", 10))
        self.stats_text.pack(fill="x", padx=5, pady=5)
        
        # 日誌面板
        log_frame = tk.LabelFrame(self.root, text="系統日誌", font=("Arial", 12, "bold"))
        log_frame.pack(fill="both", expand=True, padx=10, pady=5)
        
        # 日誌文字區域
        log_text_frame = tk.Frame(log_frame)
        log_text_frame.pack(fill="both", expand=True, padx=5, pady=5)
        
        self.log_text = tk.Text(log_text_frame, font=("Consolas", 9))
        log_scrollbar = tk.Scrollbar(log_text_frame, orient="vertical", command=self.log_text.yview)
        self.log_text.configure(yscrollcommand=log_scrollbar.set)
        
        self.log_text.pack(side="left", fill="both", expand=True)
        log_scrollbar.pack(side="right", fill="y")
        
        # 清除日誌按鈕
        clear_frame = tk.Frame(log_frame)
        clear_frame.pack(fill="x", padx=5, pady=2)
        
        tk.Button(clear_frame, text="🗑️ 清除日誌", command=self.clear_log,
                 font=("Arial", 9)).pack(side="right")
        
        # 啟動統計更新
        self.update_stats()
    
    def init_infrastructure(self):
        """初始化Queue基礎設施"""
        try:
            self.log_message("🔧 正在初始化Queue基礎設施...")
            
            # 使用快速設定
            self.infrastructure = quick_setup(self.root)
            
            if self.infrastructure:
                # 添加日誌回調
                self.infrastructure.add_log_callback(self.on_log_message)
                
                # 添加策略回調 (測試用)
                self.infrastructure.add_strategy_callback(self.on_strategy_data)
                
                self.log_message("✅ Queue基礎設施初始化成功")
                self.btn_init.config(state="disabled")
                self.btn_start.config(state="normal")
                
            else:
                self.log_message("❌ Queue基礎設施初始化失敗")
                
        except Exception as e:
            self.log_message(f"❌ 初始化錯誤: {str(e)}")
    
    def start_test(self):
        """開始測試"""
        if not self.infrastructure:
            self.log_message("❌ 請先初始化基礎設施")
            return
        
        self.test_running = True
        self.test_stats['start_time'] = datetime.now()
        self.test_stats['ticks_sent'] = 0
        self.test_stats['logs_received'] = 0
        self.test_stats['errors'] = 0
        
        # 啟動測試線程
        self.test_thread = threading.Thread(target=self.test_loop, daemon=True)
        self.test_thread.start()
        
        self.log_message("🚀 測試已開始")
        self.btn_start.config(state="disabled")
        self.btn_stop.config(state="normal")
    
    def stop_test(self):
        """停止測試"""
        self.test_running = False
        
        if self.test_thread and self.test_thread.is_alive():
            self.test_thread.join(timeout=2.0)
        
        self.log_message("🛑 測試已停止")
        self.btn_start.config(state="normal")
        self.btn_stop.config(state="disabled")
    
    def test_loop(self):
        """測試循環 (在背景線程中運行)"""
        base_price = 22000
        
        while self.test_running:
            try:
                # 生成模擬Tick資料
                price_change = random.randint(-10, 10)
                current_price = base_price + price_change
                
                bid = current_price - random.randint(1, 3)
                ask = current_price + random.randint(1, 3)
                qty = random.randint(1, 10)
                
                current_time = datetime.now()
                time_hms = int(current_time.strftime("%H%M%S"))
                
                # 發送Tick資料到Queue
                success = self.infrastructure.put_tick_data(
                    market_no="TW",
                    stock_idx=1,
                    date=int(current_time.strftime("%Y%m%d")),
                    time_hms=time_hms,
                    time_millis=current_time.microsecond // 1000,
                    bid=bid,
                    ask=ask,
                    close=current_price,
                    qty=qty,
                    timestamp=current_time
                )
                
                if success:
                    self.test_stats['ticks_sent'] += 1
                else:
                    self.test_stats['errors'] += 1
                
                # 隨機發送系統訊息
                if random.randint(1, 10) == 1:
                    test_msg = f"測試訊息 #{self.test_stats['ticks_sent']}"
                    self.infrastructure.put_log_message(test_msg, "INFO", "TEST")
                
                time.sleep(0.1)  # 每100ms發送一次
                
            except Exception as e:
                self.test_stats['errors'] += 1
                print(f"測試循環錯誤: {e}")
    
    def on_log_message(self, message, level, source):
        """處理來自Queue的日誌訊息"""
        try:
            self.test_stats['logs_received'] += 1
            
            # 在主線程中更新UI
            timestamp = datetime.now().strftime("%H:%M:%S")
            log_entry = f"[{timestamp}] [{source}] {message}\n"
            
            self.log_text.insert(tk.END, log_entry)
            self.log_text.see(tk.END)
            
        except Exception as e:
            print(f"日誌回調錯誤: {e}")
    
    def on_strategy_data(self, tick_dict):
        """處理策略資料 (測試回調)"""
        try:
            # 這裡可以添加策略邏輯測試
            price = tick_dict.get('corrected_price', 0)
            
            # 每100個tick發送一次策略訊息
            if self.test_stats['ticks_sent'] % 100 == 0:
                strategy_msg = f"策略處理: 價格 {price}, 已處理 {self.test_stats['ticks_sent']} 個tick"
                self.infrastructure.put_log_message(strategy_msg, "INFO", "STRATEGY")
                
        except Exception as e:
            print(f"策略回調錯誤: {e}")
    
    def show_status(self):
        """顯示系統狀態"""
        if not self.infrastructure:
            self.log_message("❌ 基礎設施未初始化")
            return
        
        try:
            status = self.infrastructure.get_status()
            
            status_msg = f"""
📊 Queue基礎設施狀態報告:

🔧 初始化狀態: {'✅ 已初始化' if status['initialized'] else '❌ 未初始化'}
🚀 運行狀態: {'✅ 運行中' if status['running'] else '❌ 已停止'}

📦 Queue狀態:
  • Tick佇列: {status['queue_manager']['tick_queue_size']}/{status['queue_manager']['tick_queue_maxsize']}
  • 日誌佇列: {status['queue_manager']['log_queue_size']}/{status['queue_manager']['log_queue_maxsize']}
  • 已接收Tick: {status['queue_manager']['stats']['tick_received']}
  • 已處理Tick: {status['queue_manager']['stats']['tick_processed']}

🔄 處理器狀態:
  • 處理線程: {'✅ 運行中' if status['tick_processor']['running'] else '❌ 已停止'}
  • 回調函數: {status['tick_processor']['callback_count']} 個
  • 處理計數: {status['tick_processor']['stats']['processed_count']}
  • 錯誤計數: {status['tick_processor']['stats']['error_count']}

🖥️ UI更新器:
  • 更新循環: {'✅ 運行中' if status['ui_updater']['running'] else '❌ 已停止'}
  • 更新間隔: {status['ui_updater']['update_interval']}ms
  • UI更新次數: {status['ui_updater']['stats']['ui_updates']}
  • 日誌更新次數: {status['ui_updater']['stats']['log_updates']}
            """
            
            self.log_message(status_msg)
            
        except Exception as e:
            self.log_message(f"❌ 取得狀態失敗: {str(e)}")
    
    def update_stats(self):
        """更新統計顯示"""
        try:
            if self.test_stats['start_time']:
                elapsed = datetime.now() - self.test_stats['start_time']
                elapsed_str = str(elapsed).split('.')[0]  # 移除微秒
            else:
                elapsed_str = "未開始"
            
            stats_text = f"""測試統計:
運行時間: {elapsed_str}
發送Tick: {self.test_stats['ticks_sent']}
接收日誌: {self.test_stats['logs_received']}
錯誤計數: {self.test_stats['errors']}"""
            
            self.stats_text.delete(1.0, tk.END)
            self.stats_text.insert(1.0, stats_text)
            
        except Exception as e:
            print(f"統計更新錯誤: {e}")
        
        # 每秒更新一次
        self.root.after(1000, self.update_stats)
    
    def log_message(self, message):
        """記錄本地日誌"""
        timestamp = datetime.now().strftime("%H:%M:%S")
        log_entry = f"[{timestamp}] [LOCAL] {message}\n"
        
        self.log_text.insert(tk.END, log_entry)
        self.log_text.see(tk.END)
    
    def clear_log(self):
        """清除日誌"""
        self.log_text.delete(1.0, tk.END)
    
    def on_closing(self):
        """關閉程式時的清理"""
        try:
            if self.test_running:
                self.stop_test()
            
            if self.infrastructure:
                self.infrastructure.stop_all()
            
        except Exception as e:
            print(f"清理錯誤: {e}")
        
        self.root.destroy()
    
    def run(self):
        """運行測試程式"""
        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)
        self.root.mainloop()

if __name__ == "__main__":
    print("🧪 啟動Queue基礎設施測試程式...")
    test_app = QueueInfrastructureTest()
    test_app.run()
