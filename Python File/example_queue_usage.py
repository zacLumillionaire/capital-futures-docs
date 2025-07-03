"""
Queue方案使用示例 - 實際應用範例
===============================

這個示例展示如何在實際的群益API項目中使用Queue方案來避免GIL錯誤。
包含完整的報價、委託、回報處理流程。

特點：
- 完整的COM事件處理
- 安全的UI更新機制
- 錯誤處理和日誌記錄
- 易於理解和擴展

作者: 根據GIL_ERROR_SOLUTION_PLAN.md制定
日期: 2025-07-03
"""

import tkinter as tk
from tkinter import ttk, messagebox
import threading
import time
import logging
from datetime import datetime

# 設置日誌
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# 導入Queue方案模組
from queue_manager import (
    put_quote_message, put_tick_message, put_order_message, 
    put_reply_message, put_connection_message
)
from queue_setup import setup_comprehensive_processing

class CapitalFuturesApp:
    """群益期貨應用程式 - 使用Queue方案避免GIL錯誤"""
    
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("群益期貨交易系統 - Queue方案版本")
        self.root.geometry("1200x800")
        
        # 模擬連線狀態
        self.connected = False
        
        # 創建UI
        self.create_ui()
        
        # 設置Queue處理
        self.setup_queue_processing()
        
        logger.info("🚀 群益期貨應用程式初始化完成")
    
    def create_ui(self):
        """創建用戶界面"""
        # 主框架
        main_frame = ttk.Frame(self.root)
        main_frame.pack(fill="both", expand=True, padx=10, pady=10)
        
        # 頂部控制面板
        self.create_control_panel(main_frame)
        
        # 中間標籤頁
        self.create_notebook(main_frame)
        
        # 底部狀態欄
        self.create_status_bar(main_frame)
    
    def create_control_panel(self, parent):
        """創建控制面板"""
        control_frame = ttk.LabelFrame(parent, text="🎮 連線控制")
        control_frame.pack(fill="x", pady=(0, 10))
        
        button_frame = ttk.Frame(control_frame)
        button_frame.pack(fill="x", padx=10, pady=10)
        
        # 連線按鈕
        self.connect_btn = ttk.Button(button_frame, text="🔗 連線報價", 
                                     command=self.connect_quote)
        self.connect_btn.pack(side="left", padx=5)
        
        # 斷線按鈕
        self.disconnect_btn = ttk.Button(button_frame, text="❌ 斷線", 
                                        command=self.disconnect_quote, state="disabled")
        self.disconnect_btn.pack(side="left", padx=5)
        
        # 模擬數據按鈕
        self.simulate_btn = ttk.Button(button_frame, text="🎲 模擬數據", 
                                      command=self.start_simulation)
        self.simulate_btn.pack(side="left", padx=5)
        
        # 停止模擬按鈕
        self.stop_btn = ttk.Button(button_frame, text="⏹️ 停止模擬", 
                                  command=self.stop_simulation, state="disabled")
        self.stop_btn.pack(side="left", padx=5)
        
        # 清除按鈕
        ttk.Button(button_frame, text="🗑️ 清除日誌", 
                  command=self.clear_all_logs).pack(side="left", padx=5)
    
    def create_notebook(self, parent):
        """創建標籤頁"""
        self.notebook = ttk.Notebook(parent)
        self.notebook.pack(fill="both", expand=True, pady=(0, 10))
        
        # 報價頁面
        self.create_quote_tab()
        
        # Tick頁面
        self.create_tick_tab()
        
        # 委託頁面
        self.create_order_tab()
        
        # 回報頁面
        self.create_reply_tab()
        
        # 系統頁面
        self.create_system_tab()
    
    def create_quote_tab(self):
        """創建報價頁面"""
        quote_frame = ttk.Frame(self.notebook)
        self.notebook.add(quote_frame, text="📊 即時報價")
        
        # 報價控制
        control_frame = ttk.Frame(quote_frame)
        control_frame.pack(fill="x", padx=10, pady=5)
        
        ttk.Label(control_frame, text="商品代號:").pack(side="left")
        self.stock_entry = ttk.Entry(control_frame, width=10)
        self.stock_entry.insert(0, "MTX00")
        self.stock_entry.pack(side="left", padx=5)
        
        ttk.Button(control_frame, text="訂閱報價", 
                  command=self.subscribe_quote).pack(side="left", padx=5)
        
        # 報價顯示
        self.quote_listbox = tk.Listbox(quote_frame)
        quote_scroll = ttk.Scrollbar(quote_frame, orient="vertical", 
                                    command=self.quote_listbox.yview)
        self.quote_listbox.configure(yscrollcommand=quote_scroll.set)
        self.quote_listbox.pack(side="left", fill="both", expand=True, padx=(10, 0), pady=5)
        quote_scroll.pack(side="right", fill="y", padx=(0, 10), pady=5)
    
    def create_tick_tab(self):
        """創建Tick頁面"""
        tick_frame = ttk.Frame(self.notebook)
        self.notebook.add(tick_frame, text="📈 Tick數據")
        
        self.tick_listbox = tk.Listbox(tick_frame)
        tick_scroll = ttk.Scrollbar(tick_frame, orient="vertical", 
                                   command=self.tick_listbox.yview)
        self.tick_listbox.configure(yscrollcommand=tick_scroll.set)
        self.tick_listbox.pack(side="left", fill="both", expand=True, padx=(10, 0), pady=10)
        tick_scroll.pack(side="right", fill="y", padx=(0, 10), pady=10)
    
    def create_order_tab(self):
        """創建委託頁面"""
        order_frame = ttk.Frame(self.notebook)
        self.notebook.add(order_frame, text="📝 委託管理")
        
        # 委託控制
        control_frame = ttk.Frame(order_frame)
        control_frame.pack(fill="x", padx=10, pady=5)
        
        ttk.Label(control_frame, text="價格:").pack(side="left")
        self.price_entry = ttk.Entry(control_frame, width=8)
        self.price_entry.insert(0, "22000")
        self.price_entry.pack(side="left", padx=5)
        
        ttk.Label(control_frame, text="數量:").pack(side="left")
        self.qty_entry = ttk.Entry(control_frame, width=5)
        self.qty_entry.insert(0, "1")
        self.qty_entry.pack(side="left", padx=5)
        
        ttk.Button(control_frame, text="買進", 
                  command=lambda: self.send_order("B")).pack(side="left", padx=5)
        ttk.Button(control_frame, text="賣出", 
                  command=lambda: self.send_order("S")).pack(side="left", padx=5)
        
        # 委託顯示
        self.order_listbox = tk.Listbox(order_frame)
        order_scroll = ttk.Scrollbar(order_frame, orient="vertical", 
                                    command=self.order_listbox.yview)
        self.order_listbox.configure(yscrollcommand=order_scroll.set)
        self.order_listbox.pack(side="left", fill="both", expand=True, padx=(10, 0), pady=5)
        order_scroll.pack(side="right", fill="y", padx=(0, 10), pady=5)
    
    def create_reply_tab(self):
        """創建回報頁面"""
        reply_frame = ttk.Frame(self.notebook)
        self.notebook.add(reply_frame, text="📢 即時回報")
        
        self.reply_listbox = tk.Listbox(reply_frame)
        reply_scroll = ttk.Scrollbar(reply_frame, orient="vertical", 
                                    command=self.reply_listbox.yview)
        self.reply_listbox.configure(yscrollcommand=reply_scroll.set)
        self.reply_listbox.pack(side="left", fill="both", expand=True, padx=(10, 0), pady=10)
        reply_scroll.pack(side="right", fill="y", padx=(0, 10), pady=10)
    
    def create_system_tab(self):
        """創建系統頁面"""
        system_frame = ttk.Frame(self.notebook)
        self.notebook.add(system_frame, text="🌐 系統訊息")
        
        self.system_listbox = tk.Listbox(system_frame)
        system_scroll = ttk.Scrollbar(system_frame, orient="vertical", 
                                     command=self.system_listbox.yview)
        self.system_listbox.configure(yscrollcommand=system_scroll.set)
        self.system_listbox.pack(side="left", fill="both", expand=True, padx=(10, 0), pady=10)
        system_scroll.pack(side="right", fill="y", padx=(0, 10), pady=10)
    
    def create_status_bar(self, parent):
        """創建狀態欄"""
        status_frame = ttk.Frame(parent)
        status_frame.pack(fill="x")
        
        self.status_label = ttk.Label(status_frame, text="狀態: 未連線", foreground="red")
        self.status_label.pack(side="left")
        
        self.time_label = ttk.Label(status_frame, text="")
        self.time_label.pack(side="right")
        
        # 更新時間
        self.update_time()
    
    def setup_queue_processing(self):
        """設置Queue處理"""
        try:
            # 使用綜合設置函數
            self.processor = setup_comprehensive_processing(
                self.root,
                global_listbox=self.system_listbox,
                quote_listbox=self.quote_listbox,
                tick_listbox=self.tick_listbox,
                reply_listbox=self.reply_listbox,
                order_listbox=self.order_listbox
            )
            
            logger.info("✅ Queue處理設置完成")
            
        except Exception as e:
            logger.error(f"❌ Queue處理設置失敗: {e}")
            messagebox.showerror("錯誤", f"Queue處理設置失敗: {e}")
    
    def connect_quote(self):
        """連線報價"""
        try:
            self.connected = True
            self.status_label.config(text="狀態: 已連線", foreground="green")
            self.connect_btn.config(state="disabled")
            self.disconnect_btn.config(state="normal")
            
            # 模擬連線事件
            connection_data = {'kind': 3001, 'code': 0}  # Connected
            put_connection_message(connection_data)
            
            logger.info("📡 報價連線成功")
            
        except Exception as e:
            logger.error(f"❌ 連線失敗: {e}")
            messagebox.showerror("錯誤", f"連線失敗: {e}")
    
    def disconnect_quote(self):
        """斷線報價"""
        try:
            self.connected = False
            self.status_label.config(text="狀態: 未連線", foreground="red")
            self.connect_btn.config(state="normal")
            self.disconnect_btn.config(state="disabled")
            
            # 停止模擬
            self.stop_simulation()
            
            # 模擬斷線事件
            connection_data = {'kind': 3002, 'code': 0}  # Disconnected
            put_connection_message(connection_data)
            
            logger.info("📡 報價已斷線")
            
        except Exception as e:
            logger.error(f"❌ 斷線失敗: {e}")
            messagebox.showerror("錯誤", f"斷線失敗: {e}")
    
    def subscribe_quote(self):
        """訂閱報價"""
        if not self.connected:
            messagebox.showwarning("警告", "請先連線報價服務器")
            return
        
        stock_no = self.stock_entry.get().strip()
        if not stock_no:
            messagebox.showwarning("警告", "請輸入商品代號")
            return
        
        # 模擬訂閱成功
        reply_data = {
            'type': 'reply_message',
            'user_id': 'User',
            'message': f'已訂閱 {stock_no} 報價'
        }
        put_reply_message(reply_data)
        
        logger.info(f"📊 已訂閱 {stock_no} 報價")
    
    def send_order(self, direction):
        """送出委託"""
        if not self.connected:
            messagebox.showwarning("警告", "請先連線")
            return
        
        try:
            price = float(self.price_entry.get())
            qty = int(self.qty_entry.get())
            
            # 模擬委託數據
            order_data = {
                'type': 'new_data',
                'user_id': 'User',
                'message': f'[委託] {direction} MTX00 價格:{price} 數量:{qty} 時間:{datetime.now().strftime("%H:%M:%S")}'
            }
            put_order_message(order_data)
            
            logger.info(f"📝 送出委託: {direction} {qty}口 @ {price}")
            
        except ValueError:
            messagebox.showerror("錯誤", "請輸入有效的價格和數量")
    
    def start_simulation(self):
        """開始模擬數據"""
        if not self.connected:
            messagebox.showwarning("警告", "請先連線")
            return
        
        self.simulating = True
        self.simulate_btn.config(state="disabled")
        self.stop_btn.config(state="normal")
        
        # 啟動模擬線程
        self.sim_thread = threading.Thread(target=self.simulation_worker, daemon=True)
        self.sim_thread.start()
        
        logger.info("🎲 開始模擬數據")
    
    def stop_simulation(self):
        """停止模擬數據"""
        self.simulating = False
        self.simulate_btn.config(state="normal")
        self.stop_btn.config(state="disabled")
        
        logger.info("⏹️ 停止模擬數據")
    
    def simulation_worker(self):
        """模擬數據工作線程"""
        import random
        
        base_price = 22000
        
        while self.simulating and self.connected:
            try:
                # 模擬報價
                quote_data = {
                    'stock_no': 'MTX00',
                    'stock_name': '小台指',
                    'open_price': base_price + random.randint(-20, 20),
                    'high_price': base_price + random.randint(-10, 30),
                    'low_price': base_price + random.randint(-30, 10),
                    'close_price': base_price + random.randint(-15, 15),
                    'total_qty': random.randint(1000, 9999)
                }
                put_quote_message(quote_data)
                
                # 模擬Tick
                tick_data = {
                    'type': 'live',
                    'stock_idx': 1,
                    'close': base_price + random.randint(-10, 10),
                    'qty': random.randint(1, 50),
                    'time_hms': int(time.strftime("%H%M%S"))
                }
                put_tick_message(tick_data)
                
                time.sleep(0.5)  # 500ms間隔
                
            except Exception as e:
                logger.error(f"❌ 模擬數據錯誤: {e}")
                break
    
    def clear_all_logs(self):
        """清除所有日誌"""
        for listbox in [self.quote_listbox, self.tick_listbox, self.order_listbox, 
                       self.reply_listbox, self.system_listbox]:
            listbox.delete(0, "end")
        
        logger.info("🗑️ 所有日誌已清除")
    
    def update_time(self):
        """更新時間顯示"""
        current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        self.time_label.config(text=current_time)
        self.root.after(1000, self.update_time)
    
    def run(self):
        """運行應用程式"""
        try:
            logger.info("🎯 群益期貨應用程式啟動")
            self.root.protocol("WM_DELETE_WINDOW", self.on_closing)
            self.root.mainloop()
        except Exception as e:
            logger.error(f"❌ 應用程式運行失敗: {e}")
        finally:
            logger.info("🏁 群益期貨應用程式結束")
    
    def on_closing(self):
        """關閉應用程式"""
        try:
            # 停止模擬
            self.simulating = False
            
            # 停止處理器
            if hasattr(self, 'processor'):
                self.processor.stop()
            
            # 關閉窗口
            self.root.destroy()
            
        except Exception as e:
            logger.error(f"❌ 關閉應用程式失敗: {e}")

if __name__ == "__main__":
    app = CapitalFuturesApp()
    app.run()
