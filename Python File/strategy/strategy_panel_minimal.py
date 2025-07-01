#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
最簡化策略控制面板
專為OrderTester整合設計，無外部依賴
"""

import tkinter as tk
from tkinter import ttk, messagebox
from datetime import datetime
import logging

logger = logging.getLogger(__name__)

class StrategyControlPanel(tk.Frame):
    """最簡化策略控制面板"""
    
    def __init__(self, master=None):
        super().__init__(master)
        self.master = master
        
        # 基本狀態變數
        self.strategy_active = False
        self.monitoring_active = False
        self.current_price = 0.0
        self.range_high = 0.0
        self.range_low = 0.0
        
        # 創建界面
        self.create_widgets()
        
        # 初始化完成
        self.log_message("✅ 最簡化策略面板初始化完成")
        self.log_message("ℹ️ 基本策略功能可用，無複雜依賴")
    
    def create_widgets(self):
        """創建界面組件"""
        # 主容器
        main_frame = ttk.Frame(self)
        main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # 標題
        title_label = ttk.Label(main_frame, text="🎯 策略交易控制面板", 
                               font=("Arial", 16, "bold"))
        title_label.pack(pady=(0, 15))
        
        # 狀態區域
        self.create_status_area(main_frame)
        
        # 控制區域
        self.create_control_area(main_frame)
        
        # 日誌區域
        self.create_log_area(main_frame)
    
    def create_status_area(self, parent):
        """創建狀態顯示區域"""
        status_frame = ttk.LabelFrame(parent, text="📊 策略狀態", padding=15)
        status_frame.pack(fill=tk.X, pady=(0, 10))
        
        # 狀態網格
        status_grid = ttk.Frame(status_frame)
        status_grid.pack(fill=tk.X)
        
        # 策略狀態
        ttk.Label(status_grid, text="策略狀態:", font=("Arial", 10, "bold")).grid(row=0, column=0, sticky=tk.W, padx=(0, 10))
        self.status_label = ttk.Label(status_grid, text="🔴 停止", foreground="red")
        self.status_label.grid(row=0, column=1, sticky=tk.W)
        
        # 當前價格
        ttk.Label(status_grid, text="當前價格:", font=("Arial", 10, "bold")).grid(row=1, column=0, sticky=tk.W, padx=(0, 10), pady=(5, 0))
        self.price_label = ttk.Label(status_grid, text="📈 --")
        self.price_label.grid(row=1, column=1, sticky=tk.W, pady=(5, 0))
        
        # 開盤區間
        ttk.Label(status_grid, text="開盤區間:", font=("Arial", 10, "bold")).grid(row=2, column=0, sticky=tk.W, padx=(0, 10), pady=(5, 0))
        self.range_label = ttk.Label(status_grid, text="📊 未檢測")
        self.range_label.grid(row=2, column=1, sticky=tk.W, pady=(5, 0))
    
    def create_control_area(self, parent):
        """創建控制按鈕區域"""
        control_frame = ttk.LabelFrame(parent, text="🎮 策略控制", padding=15)
        control_frame.pack(fill=tk.X, pady=(0, 10))
        
        # 按鈕容器
        button_container = ttk.Frame(control_frame)
        button_container.pack()
        
        # 開始按鈕
        self.start_button = ttk.Button(button_container, text="🚀 開始策略", 
                                      command=self.start_strategy, width=12)
        self.start_button.pack(side=tk.LEFT, padx=(0, 10))
        
        # 停止按鈕
        self.stop_button = ttk.Button(button_container, text="⏹️ 停止策略", 
                                     command=self.stop_strategy, state=tk.DISABLED, width=12)
        self.stop_button.pack(side=tk.LEFT, padx=(0, 10))
        
        # 統計按鈕
        self.stats_button = ttk.Button(button_container, text="📊 顯示統計", 
                                      command=self.show_statistics, width=12)
        self.stats_button.pack(side=tk.LEFT)
    
    def create_log_area(self, parent):
        """創建日誌顯示區域"""
        log_frame = ttk.LabelFrame(parent, text="📝 策略日誌", padding=10)
        log_frame.pack(fill=tk.BOTH, expand=True)
        
        # 日誌文本框和滾動條
        log_container = ttk.Frame(log_frame)
        log_container.pack(fill=tk.BOTH, expand=True)
        
        self.log_text = tk.Text(log_container, height=12, wrap=tk.WORD, 
                               font=("Consolas", 9))
        self.log_text.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        
        log_scrollbar = ttk.Scrollbar(log_container, orient=tk.VERTICAL, 
                                     command=self.log_text.yview)
        log_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.log_text.config(yscrollcommand=log_scrollbar.set)
    
    def start_strategy(self):
        """開始策略"""
        try:
            self.strategy_active = True
            self.monitoring_active = True
            
            # 更新界面
            self.status_label.config(text="🟢 運行中", foreground="green")
            self.start_button.config(state=tk.DISABLED)
            self.stop_button.config(state=tk.NORMAL)
            
            self.log_message("🚀 策略已啟動")
            self.log_message("📊 開始監控MTX00期貨價格")
            self.log_message("⏰ 等待開盤區間檢測...")
            
        except Exception as e:
            self.log_message(f"❌ 策略啟動失敗: {e}")
    
    def stop_strategy(self):
        """停止策略"""
        try:
            self.strategy_active = False
            self.monitoring_active = False
            
            # 更新界面
            self.status_label.config(text="🔴 停止", foreground="red")
            self.start_button.config(state=tk.NORMAL)
            self.stop_button.config(state=tk.DISABLED)
            
            self.log_message("⏹️ 策略已停止")
            
        except Exception as e:
            self.log_message(f"❌ 策略停止失敗: {e}")
    
    def process_price_update(self, price, timestamp=None):
        """處理價格更新"""
        try:
            self.current_price = float(price)
            
            # 更新價格顯示
            self.price_label.config(text=f"📈 {self.current_price}")
            
            # 如果策略運行中，進行簡單的邏輯處理
            if self.strategy_active:
                self.process_strategy_logic()
            
        except Exception as e:
            self.log_message(f"❌ 價格更新失敗: {e}")
    
    def process_strategy_logic(self):
        """處理策略邏輯（簡化版）"""
        try:
            # 簡單的區間檢測邏輯
            current_time = datetime.now().strftime("%H:%M:%S")
            
            # 模擬區間檢測
            if self.range_high == 0 and self.range_low == 0:
                # 設定模擬區間
                self.range_high = self.current_price + 20
                self.range_low = self.current_price - 20
                self.range_label.config(text=f"📊 {self.range_low:.0f} - {self.range_high:.0f}")
                self.log_message(f"📊 檢測到開盤區間: {self.range_low:.0f} - {self.range_high:.0f}")
            
            # 簡單的突破檢測
            if self.current_price > self.range_high:
                self.log_message(f"🔥 價格突破上軌 {self.current_price} > {self.range_high}")
            elif self.current_price < self.range_low:
                self.log_message(f"🔥 價格突破下軌 {self.current_price} < {self.range_low}")
                
        except Exception as e:
            self.log_message(f"❌ 策略邏輯處理失敗: {e}")
    
    def show_statistics(self):
        """顯示統計資訊"""
        try:
            stats_text = f"""
🎯 策略統計資訊

📊 當前狀態: {'🟢 運行中' if self.strategy_active else '🔴 停止'}
📈 當前價格: {self.current_price}
📊 開盤區間: {self.range_low:.0f} - {self.range_high:.0f}

ℹ️ 這是最簡化版策略面板
✅ 基本功能正常運作
⚠️ 完整功能需要修復模組依賴

💡 建議: 先測試基本功能，確認整合正常
            """
            
            messagebox.showinfo("策略統計", stats_text.strip())
            self.log_message("📊 顯示統計資訊")
            
        except Exception as e:
            self.log_message(f"❌ 顯示統計失敗: {e}")
    
    def log_message(self, message):
        """添加日誌訊息"""
        try:
            timestamp = datetime.now().strftime("%H:%M:%S")
            log_entry = f"[{timestamp}] {message}\n"
            
            self.log_text.insert(tk.END, log_entry)
            self.log_text.see(tk.END)
            
            # 限制日誌行數，避免記憶體問題
            lines = self.log_text.get("1.0", tk.END).split('\n')
            if len(lines) > 50:
                self.log_text.delete("1.0", "10.0")
            
        except Exception as e:
            print(f"日誌記錄失敗: {e}")

if __name__ == "__main__":
    # 獨立測試
    root = tk.Tk()
    root.title("最簡化策略面板測試")
    root.geometry("700x500")
    
    panel = StrategyControlPanel(root)
    panel.pack(fill=tk.BOTH, expand=True)
    
    # 模擬價格更新
    def simulate_price():
        import random
        price = 22000 + random.randint(-50, 50)
        panel.process_price_update(price)
        root.after(2000, simulate_price)
    
    simulate_price()
    root.mainloop()
