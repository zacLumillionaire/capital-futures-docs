"""
Queue方案測試程式 - 驗證GIL錯誤修復
===================================

這個測試程式用來驗證Queue方案是否能正確解決GIL錯誤問題。
測試包括：
1. 模擬COM事件的多線程環境
2. 驗證Queue訊息傳遞
3. 確認UI更新在主線程中執行
4. 壓力測試高頻率訊息處理

使用方法：
python test_queue_solution.py

作者: 根據GIL_ERROR_SOLUTION_PLAN.md制定
日期: 2025-07-03
"""

import tkinter as tk
from tkinter import ttk
import threading
import time
import random
import logging
from datetime import datetime

# 設置日誌
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# 導入Queue管理器
from queue_manager import (
    put_quote_message, put_tick_message, put_order_message, 
    put_reply_message, put_connection_message, get_queue_stats
)
from queue_setup import setup_comprehensive_processing
from message_handlers import get_handler_stats

class QueueTestApp:
    """Queue方案測試應用程式"""
    
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("🧪 Queue方案GIL錯誤修復測試")
        self.root.geometry("1000x700")
        
        # 測試控制變數
        self.test_running = False
        self.test_threads = []
        
        # 創建UI
        self.create_ui()
        
        # 設置Queue處理
        self.setup_queue_processing()
        
        logger.info("🚀 Queue測試應用程式初始化完成")
    
    def create_ui(self):
        """創建測試UI"""
        # 主框架
        main_frame = ttk.Frame(self.root)
        main_frame.pack(fill="both", expand=True, padx=10, pady=10)
        
        # 控制面板
        control_frame = ttk.LabelFrame(main_frame, text="🎮 測試控制面板")
        control_frame.pack(fill="x", pady=(0, 10))
        
        # 測試按鈕
        button_frame = ttk.Frame(control_frame)
        button_frame.pack(fill="x", padx=10, pady=10)
        
        ttk.Button(button_frame, text="🚀 開始壓力測試", 
                  command=self.start_stress_test).pack(side="left", padx=5)
        ttk.Button(button_frame, text="⏹️ 停止測試", 
                  command=self.stop_test).pack(side="left", padx=5)
        ttk.Button(button_frame, text="📊 顯示統計", 
                  command=self.show_stats).pack(side="left", padx=5)
        ttk.Button(button_frame, text="🗑️ 清除日誌", 
                  command=self.clear_logs).pack(side="left", padx=5)
        
        # 狀態標籤
        self.status_label = ttk.Label(control_frame, text="狀態: 就緒", foreground="green")
        self.status_label.pack(pady=5)
        
        # 訊息顯示區域
        notebook = ttk.Notebook(main_frame)
        notebook.pack(fill="both", expand=True)
        
        # 報價頁面
        quote_frame = ttk.Frame(notebook)
        notebook.add(quote_frame, text="📊 報價訊息")
        self.quote_listbox = tk.Listbox(quote_frame)
        quote_scroll = ttk.Scrollbar(quote_frame, orient="vertical", command=self.quote_listbox.yview)
        self.quote_listbox.configure(yscrollcommand=quote_scroll.set)
        self.quote_listbox.pack(side="left", fill="both", expand=True)
        quote_scroll.pack(side="right", fill="y")
        
        # Tick頁面
        tick_frame = ttk.Frame(notebook)
        notebook.add(tick_frame, text="📈 Tick數據")
        self.tick_listbox = tk.Listbox(tick_frame)
        tick_scroll = ttk.Scrollbar(tick_frame, orient="vertical", command=self.tick_listbox.yview)
        self.tick_listbox.configure(yscrollcommand=tick_scroll.set)
        self.tick_listbox.pack(side="left", fill="both", expand=True)
        tick_scroll.pack(side="right", fill="y")
        
        # 委託頁面
        order_frame = ttk.Frame(notebook)
        notebook.add(order_frame, text="📝 委託回報")
        self.order_listbox = tk.Listbox(order_frame)
        order_scroll = ttk.Scrollbar(order_frame, orient="vertical", command=self.order_listbox.yview)
        self.order_listbox.configure(yscrollcommand=order_scroll.set)
        self.order_listbox.pack(side="left", fill="both", expand=True)
        order_scroll.pack(side="right", fill="y")
        
        # 回報頁面
        reply_frame = ttk.Frame(notebook)
        notebook.add(reply_frame, text="📢 系統回報")
        self.reply_listbox = tk.Listbox(reply_frame)
        reply_scroll = ttk.Scrollbar(reply_frame, orient="vertical", command=self.reply_listbox.yview)
        self.reply_listbox.configure(yscrollcommand=reply_scroll.set)
        self.reply_listbox.pack(side="left", fill="both", expand=True)
        reply_scroll.pack(side="right", fill="y")
        
        # 全域訊息頁面
        global_frame = ttk.Frame(notebook)
        notebook.add(global_frame, text="🌐 全域訊息")
        self.global_listbox = tk.Listbox(global_frame)
        global_scroll = ttk.Scrollbar(global_frame, orient="vertical", command=self.global_listbox.yview)
        self.global_listbox.configure(yscrollcommand=global_scroll.set)
        self.global_listbox.pack(side="left", fill="both", expand=True)
        global_scroll.pack(side="right", fill="y")
    
    def setup_queue_processing(self):
        """設置Queue處理"""
        try:
            # 使用綜合設置函數
            self.processor = setup_comprehensive_processing(
                self.root,
                global_listbox=self.global_listbox,
                quote_listbox=self.quote_listbox,
                tick_listbox=self.tick_listbox,
                reply_listbox=self.reply_listbox,
                order_listbox=self.order_listbox
            )
            
            logger.info("✅ Queue處理設置完成")
            
        except Exception as e:
            logger.error(f"❌ Queue處理設置失敗: {e}")
            raise
    
    def start_stress_test(self):
        """開始壓力測試"""
        if self.test_running:
            return
        
        self.test_running = True
        self.status_label.config(text="狀態: 壓力測試進行中...", foreground="orange")
        
        # 啟動多個測試線程
        test_configs = [
            ("報價測試", self.quote_test_thread, 0.1),
            ("Tick測試", self.tick_test_thread, 0.05),
            ("委託測試", self.order_test_thread, 0.2),
            ("回報測試", self.reply_test_thread, 0.15),
            ("連線測試", self.connection_test_thread, 1.0)
        ]
        
        for name, target, interval in test_configs:
            thread = threading.Thread(target=target, args=(interval,), name=name, daemon=True)
            thread.start()
            self.test_threads.append(thread)
            logger.info(f"🧵 啟動測試線程: {name}")
        
        logger.info("🚀 壓力測試已開始")
    
    def stop_test(self):
        """停止測試"""
        self.test_running = False
        self.status_label.config(text="狀態: 測試已停止", foreground="red")
        logger.info("⏹️ 壓力測試已停止")
    
    def quote_test_thread(self, interval):
        """報價測試線程"""
        while self.test_running:
            try:
                # 模擬報價數據
                quote_data = {
                    'stock_no': f'MTX{random.randint(10, 99)}',
                    'stock_name': '小台指',
                    'open_price': 22000 + random.randint(-50, 50),
                    'high_price': 22000 + random.randint(-30, 80),
                    'low_price': 22000 + random.randint(-80, 30),
                    'close_price': 22000 + random.randint(-40, 40),
                    'total_qty': random.randint(1000, 9999)
                }
                
                put_quote_message(quote_data)
                time.sleep(interval)
                
            except Exception as e:
                logger.error(f"❌ 報價測試線程錯誤: {e}")
                break
    
    def tick_test_thread(self, interval):
        """Tick測試線程"""
        while self.test_running:
            try:
                # 模擬Tick數據
                tick_data = {
                    'type': 'live',
                    'market_no': 2,
                    'stock_idx': random.randint(1, 100),
                    'ptr': random.randint(1, 1000),
                    'date': 20250703,
                    'time_hms': int(time.strftime("%H%M%S")),
                    'time_millis': random.randint(0, 999),
                    'bid': 22000 + random.randint(-20, 20),
                    'ask': 22000 + random.randint(-20, 20),
                    'close': 22000 + random.randint(-20, 20),
                    'qty': random.randint(1, 100),
                    'simulate': 0
                }
                
                put_tick_message(tick_data)
                time.sleep(interval)
                
            except Exception as e:
                logger.error(f"❌ Tick測試線程錯誤: {e}")
                break
    
    def order_test_thread(self, interval):
        """委託測試線程"""
        while self.test_running:
            try:
                # 模擬委託數據
                order_data = {
                    'type': 'new_data',
                    'user_id': 'TestUser',
                    'raw_data': f'12345,TF,D,N,F020000,6363839,BNF20,TW,MTX00,,{22000 + random.randint(-10, 10)}.0000,0.000000,,,,,,,,,{random.randint(1, 5)},,,20250703,{time.strftime("%H:%M:%S")},,0000000,{random.randint(1000000000, 9999999999)},y',
                    'message': f'[委託] 序號:12345 商品:MTX00 價格:{22000 + random.randint(-10, 10)} 數量:{random.randint(1, 5)}'
                }
                
                put_order_message(order_data)
                time.sleep(interval)
                
            except Exception as e:
                logger.error(f"❌ 委託測試線程錯誤: {e}")
                break
    
    def reply_test_thread(self, interval):
        """回報測試線程"""
        while self.test_running:
            try:
                # 模擬回報數據
                reply_types = ['connect', 'disconnect', 'reply_message', 'smart_data']
                reply_type = random.choice(reply_types)
                
                reply_data = {
                    'type': reply_type,
                    'user_id': 'TestUser',
                    'message': f'測試{reply_type}訊息 - {datetime.now().strftime("%H:%M:%S")}'
                }
                
                put_reply_message(reply_data)
                time.sleep(interval)
                
            except Exception as e:
                logger.error(f"❌ 回報測試線程錯誤: {e}")
                break
    
    def connection_test_thread(self, interval):
        """連線測試線程"""
        while self.test_running:
            try:
                # 模擬連線數據
                kinds = [3001, 3002, 3003, 3021]
                kind = random.choice(kinds)
                
                connection_data = {
                    'kind': kind,
                    'code': 0
                }
                
                put_connection_message(connection_data)
                time.sleep(interval)
                
            except Exception as e:
                logger.error(f"❌ 連線測試線程錯誤: {e}")
                break
    
    def show_stats(self):
        """顯示統計信息"""
        queue_stats = get_queue_stats()
        handler_stats = get_handler_stats()
        
        stats_window = tk.Toplevel(self.root)
        stats_window.title("📊 Queue統計信息")
        stats_window.geometry("500x400")
        
        text_widget = tk.Text(stats_window, wrap="word")
        text_widget.pack(fill="both", expand=True, padx=10, pady=10)
        
        stats_text = "📊 Queue管理器統計:\n"
        stats_text += "=" * 30 + "\n"
        for key, value in queue_stats.items():
            stats_text += f"{key}: {value}\n"
        
        stats_text += "\n📋 訊息處理器統計:\n"
        stats_text += "=" * 30 + "\n"
        for key, value in handler_stats.items():
            stats_text += f"{key}: {value}\n"
        
        text_widget.insert("1.0", stats_text)
        text_widget.config(state="disabled")
        
        logger.info("📊 統計信息已顯示")
    
    def clear_logs(self):
        """清除所有日誌"""
        for listbox in [self.quote_listbox, self.tick_listbox, self.order_listbox, 
                       self.reply_listbox, self.global_listbox]:
            listbox.delete(0, "end")
        
        logger.info("🗑️ 所有日誌已清除")
    
    def run(self):
        """運行測試應用程式"""
        try:
            logger.info("🎯 Queue方案測試開始")
            self.root.mainloop()
        except Exception as e:
            logger.error(f"❌ 測試應用程式運行失敗: {e}")
        finally:
            self.stop_test()
            if hasattr(self, 'processor'):
                self.processor.stop()
            logger.info("🏁 Queue方案測試結束")

if __name__ == "__main__":
    app = QueueTestApp()
    app.run()
