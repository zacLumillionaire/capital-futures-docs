#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
簡化版策略控制面板
用於OrderTester整合，避免複雜依賴問題
"""

import tkinter as tk
from tkinter import ttk, messagebox
from datetime import datetime
import logging

logger = logging.getLogger(__name__)

class StrategyControlPanel(tk.Frame):
    """簡化版策略控制面板"""
    
    def __init__(self, master=None):
        super().__init__(master)
        self.master = master
        
        # 基本狀態
        self.strategy_active = False
        self.monitoring_active = False
        self.current_price = 0.0
        self.range_high = 0.0
        self.range_low = 0.0
        
        # 創建界面
        self.create_widgets()
        
        # 初始化日誌
        self.log_message("✅ 策略面板初始化完成")
        self.log_message("ℹ️ 簡化版策略面板，基本功能可用")
    
    def create_widgets(self):
        """創建界面組件"""
        # 主框架
        main_frame = ttk.Frame(self)
        main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # 標題
        title_label = ttk.Label(main_frame, text="策略交易控制面板", 
                               font=("Arial", 14, "bold"))
        title_label.pack(pady=(0, 10))
        
        # 狀態顯示區域
        self.create_status_section(main_frame)
        
        # 控制按鈕區域
        self.create_control_section(main_frame)
        
        # 日誌區域
        self.create_log_section(main_frame)
    
    def create_status_section(self, parent):
        """創建狀態顯示區域"""
        status_frame = ttk.LabelFrame(parent, text="策略狀態", padding=10)
        status_frame.pack(fill=tk.X, pady=(0, 10))
        
        # 狀態標籤
        self.status_label = ttk.Label(status_frame, text="策略狀態: 停止", 
                                     font=("Arial", 10, "bold"))
        self.status_label.pack(anchor=tk.W)
        
        # 價格顯示
        self.price_label = ttk.Label(status_frame, text="當前價格: --")
        self.price_label.pack(anchor=tk.W)
        
        # 區間顯示
        self.range_label = ttk.Label(status_frame, text="開盤區間: --")
        self.range_label.pack(anchor=tk.W)
    
    def create_control_section(self, parent):
        """創建控制按鈕區域"""
        control_frame = ttk.LabelFrame(parent, text="策略控制", padding=10)
        control_frame.pack(fill=tk.X, pady=(0, 10))
        
        # 按鈕框架
        button_frame = ttk.Frame(control_frame)
        button_frame.pack(fill=tk.X)
        
        # 開始/停止按鈕
        self.start_button = ttk.Button(button_frame, text="開始策略", 
                                      command=self.start_strategy)
        self.start_button.pack(side=tk.LEFT, padx=(0, 5))
        
        self.stop_button = ttk.Button(button_frame, text="停止策略", 
                                     command=self.stop_strategy, state=tk.DISABLED)
        self.stop_button.pack(side=tk.LEFT, padx=(0, 5))
        
        # 統計按鈕
        self.stats_button = ttk.Button(button_frame, text="顯示統計", 
                                      command=self.show_statistics)
        self.stats_button.pack(side=tk.LEFT, padx=(0, 5))
    
    def create_log_section(self, parent):
        """創建日誌區域"""
        log_frame = ttk.LabelFrame(parent, text="策略日誌", padding=10)
        log_frame.pack(fill=tk.BOTH, expand=True)
        
        # 日誌文本框
        self.log_text = tk.Text(log_frame, height=15, wrap=tk.WORD)
        self.log_text.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        
        # 滾動條
        scrollbar = ttk.Scrollbar(log_frame, orient=tk.VERTICAL, 
                                 command=self.log_text.yview)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.log_text.config(yscrollcommand=scrollbar.set)
    
    def start_strategy(self):
        """開始策略"""
        try:
            self.strategy_active = True
            self.monitoring_active = True
            
            # 更新界面
            self.status_label.config(text="策略狀態: 運行中", foreground="green")
            self.start_button.config(state=tk.DISABLED)
            self.stop_button.config(state=tk.NORMAL)
            
            self.log_message("🚀 策略已啟動")
            self.log_message("📊 開始監控價格變化")
            
        except Exception as e:
            self.log_message(f"❌ 策略啟動失敗: {e}")
            logger.error(f"策略啟動失敗: {e}")
    
    def stop_strategy(self):
        """停止策略"""
        try:
            self.strategy_active = False
            self.monitoring_active = False
            
            # 更新界面
            self.status_label.config(text="策略狀態: 停止", foreground="red")
            self.start_button.config(state=tk.NORMAL)
            self.stop_button.config(state=tk.DISABLED)
            
            self.log_message("⏹️ 策略已停止")
            
        except Exception as e:
            self.log_message(f"❌ 策略停止失敗: {e}")
            logger.error(f"策略停止失敗: {e}")
    
    def process_price_update(self, price, timestamp=None):
        """處理價格更新"""
        try:
            self.current_price = float(price)
            
            # 更新價格顯示
            self.price_label.config(text=f"當前價格: {self.current_price}")
            
            # 如果策略運行中，處理價格邏輯
            if self.strategy_active:
                self.check_signals()
            
        except Exception as e:
            self.log_message(f"❌ 價格更新失敗: {e}")
            logger.error(f"價格更新失敗: {e}")
    
    def check_signals(self):
        """檢查交易信號（簡化版）"""
        try:
            # 簡化的信號檢測邏輯
            if self.current_price > 0:
                # 這裡可以添加簡單的信號檢測邏輯
                pass
                
        except Exception as e:
            self.log_message(f"❌ 信號檢測失敗: {e}")
            logger.error(f"信號檢測失敗: {e}")
    
    def show_statistics(self):
        """顯示統計資訊"""
        try:
            stats_info = f"""
策略統計資訊

當前狀態: {'運行中' if self.strategy_active else '停止'}
當前價格: {self.current_price}
開盤區間: {self.range_low} - {self.range_high}

注意: 這是簡化版策略面板
完整功能需要修復模組依賴問題
            """
            
            messagebox.showinfo("策略統計", stats_info.strip())
            self.log_message("📊 顯示統計資訊")
            
        except Exception as e:
            self.log_message(f"❌ 顯示統計失敗: {e}")
            logger.error(f"顯示統計失敗: {e}")
    
    def log_message(self, message):
        """添加日誌訊息"""
        try:
            timestamp = datetime.now().strftime("%H:%M:%S.%f")[:-3]
            log_entry = f"📊 策略日誌: [{timestamp}] {message}\n"
            
            self.log_text.insert(tk.END, log_entry)
            self.log_text.see(tk.END)
            
            # 限制日誌行數
            lines = self.log_text.get("1.0", tk.END).split('\n')
            if len(lines) > 100:
                self.log_text.delete("1.0", "10.0")
            
        except Exception as e:
            logger.error(f"日誌記錄失敗: {e}")

# 為了兼容性，創建一個別名
StrategyPanel = StrategyControlPanel

if __name__ == "__main__":
    # 測試界面
    root = tk.Tk()
    root.title("策略控制面板測試")
    root.geometry("800x600")
    
    panel = StrategyControlPanel(root)
    panel.pack(fill=tk.BOTH, expand=True)
    
    # 測試價格更新
    def test_price_update():
        import random
        price = 22000 + random.randint(-100, 100)
        panel.process_price_update(price)
        root.after(1000, test_price_update)
    
    test_price_update()
    
    root.mainloop()
