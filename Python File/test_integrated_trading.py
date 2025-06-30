#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
整合交易系統測試
測試下單機 + 策略面板的完整功能
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

import tkinter as tk
from tkinter import ttk
import threading
import time
import random
from datetime import datetime

# 導入下單機 (已整合策略面板)
from order.future_order import FutureOrderFrame

class IntegratedTradingTest:
    """整合交易系統測試"""
    
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("🚀 整合交易系統 - 下單機 + 策略面板")
        self.root.geometry("1200x900")
        
        # 創建下單機框架 (已包含策略面板)
        self.order_frame = FutureOrderFrame(self.root)
        self.order_frame.pack(fill="both", expand=True, padx=10, pady=10)
        
        # 模擬價格數據
        self.base_price = 22000
        self.price_running = False
        
        # 創建控制面板
        self.create_control_panel()
        
        # 顯示說明
        self.show_instructions()
    
    def create_control_panel(self):
        """創建測試控制面板"""
        control_frame = tk.LabelFrame(self.root, text="🧪 測試控制面板", fg="green", font=("Arial", 10, "bold"))
        control_frame.pack(fill="x", padx=10, pady=5)
        
        # 價格模擬控制
        tk.Label(control_frame, text="價格模擬:").grid(row=0, column=0, padx=5, pady=5)
        
        self.btn_start_price = tk.Button(control_frame, text="🎯 開始模擬報價", 
                                        command=self.start_price_simulation, bg="lightgreen")
        self.btn_start_price.grid(row=0, column=1, padx=5, pady=5)
        
        self.btn_stop_price = tk.Button(control_frame, text="⏹️ 停止模擬報價", 
                                       command=self.stop_price_simulation, bg="lightcoral")
        self.btn_stop_price.grid(row=0, column=2, padx=5, pady=5)
        
        # 基準價格設定
        tk.Label(control_frame, text="基準價格:").grid(row=0, column=3, padx=5, pady=5)
        self.entry_base_price = tk.Entry(control_frame, width=8)
        self.entry_base_price.insert(0, str(self.base_price))
        self.entry_base_price.grid(row=0, column=4, padx=5, pady=5)
        
        tk.Button(control_frame, text="更新", command=self.update_base_price).grid(row=0, column=5, padx=5, pady=5)
        
        # 策略測試按鈕
        tk.Label(control_frame, text="策略測試:").grid(row=1, column=0, padx=5, pady=5)
        
        tk.Button(control_frame, text="🎯 設定測試時間", command=self.set_test_time, 
                 bg="orange").grid(row=1, column=1, padx=5, pady=5)
        
        tk.Button(control_frame, text="📊 模擬開盤區間", command=self.simulate_opening_range, 
                 bg="lightblue").grid(row=1, column=2, padx=5, pady=5)
        
        tk.Button(control_frame, text="🚀 模擬突破", command=self.simulate_breakout, 
                 bg="yellow").grid(row=1, column=3, padx=5, pady=5)
        
        # 狀態顯示
        self.status_var = tk.StringVar(value="系統就緒")
        tk.Label(control_frame, text="狀態:").grid(row=1, column=4, padx=5, pady=5)
        tk.Label(control_frame, textvariable=self.status_var, fg="blue").grid(row=1, column=5, padx=5, pady=5)
    
    def show_instructions(self):
        """顯示使用說明"""
        instructions = """
🎯 整合交易系統使用說明:

1. 【策略面板功能】
   - 可設定交易口數 (1-4口)
   - 可自定義監控時段 (支援測試)
   - 即時顯示開盤區間和突破點位
   - 即時監控部位狀態和損益

2. 【測試流程】
   - 點擊「設定測試時間」→ 設定當前時間為監控時段
   - 點擊「開始模擬報價」→ 開始即時價格更新
   - 點擊「模擬開盤區間」→ 模擬08:46-08:47區間計算
   - 點擊「模擬突破」→ 模擬價格突破觸發策略

3. 【區間產出機制】
   - 即時監控指定時段的每個tick
   - 自動建立分鐘K線 (OHLC)
   - 時段結束立即計算區間高低點
   - 設定突破觸發點位

4. 【策略執行】
   - 價格突破區間自動開倉
   - 多口獨立移動停利管理
   - 保護性停損動態調整
   - 完整交易記錄和統計
"""
        
        # 在下單機中顯示說明
        if hasattr(self.order_frame, 'add_message'):
            for line in instructions.strip().split('\n'):
                if line.strip():
                    self.order_frame.add_message(line)
    
    def start_price_simulation(self):
        """開始價格模擬"""
        if self.price_running:
            return
        
        self.price_running = True
        self.status_var.set("價格模擬中...")
        
        def price_thread():
            while self.price_running:
                try:
                    # 生成隨機價格變動
                    change = random.randint(-5, 5)
                    new_price = self.base_price + change
                    
                    # 模擬tick數據 (簡化版)
                    if hasattr(self.order_frame, 'strategy_panel') and self.order_frame.strategy_panel:
                        timestamp = datetime.now()
                        self.order_frame.strategy_panel.process_price_update(new_price, timestamp)
                    
                    # 更新下單機的價格顯示
                    if hasattr(self.order_frame, 'label_price'):
                        self.root.after(0, lambda: self.order_frame.label_price.config(text=str(new_price)))
                    
                    # 更新時間顯示
                    current_time = datetime.now().strftime("%H:%M:%S")
                    if hasattr(self.order_frame, 'label_time'):
                        self.root.after(0, lambda: self.order_frame.label_time.config(text=current_time))
                    
                    time.sleep(0.5)  # 每0.5秒更新一次
                    
                except Exception as e:
                    print(f"價格模擬錯誤: {e}")
                    break
        
        # 啟動價格模擬線程
        threading.Thread(target=price_thread, daemon=True).start()
        self.order_frame.add_message("🎯 開始模擬即時報價")
    
    def stop_price_simulation(self):
        """停止價格模擬"""
        self.price_running = False
        self.status_var.set("價格模擬已停止")
        self.order_frame.add_message("⏹️ 停止模擬報價")
    
    def update_base_price(self):
        """更新基準價格"""
        try:
            new_price = int(self.entry_base_price.get())
            self.base_price = new_price
            self.order_frame.add_message(f"📊 基準價格已更新為: {new_price}")
        except ValueError:
            self.order_frame.add_message("❌ 價格格式錯誤")
    
    def set_test_time(self):
        """設定測試時間"""
        if hasattr(self.order_frame, 'strategy_panel') and self.order_frame.strategy_panel:
            # 調用策略面板的設定測試時間功能
            self.order_frame.strategy_panel.set_test_hours()
            self.order_frame.add_message("🧪 已設定測試時間為當前時間")
        else:
            self.order_frame.add_message("❌ 策略面板未載入")
    
    def simulate_opening_range(self):
        """模擬開盤區間計算"""
        if not hasattr(self.order_frame, 'strategy_panel') or not self.order_frame.strategy_panel:
            self.order_frame.add_message("❌ 策略面板未載入")
            return
        
        strategy_panel = self.order_frame.strategy_panel
        
        # 模擬兩分鐘的價格數據來建立開盤區間
        self.order_frame.add_message("📊 開始模擬開盤區間計算...")
        
        def simulate_range():
            base = self.base_price
            
            # 模擬第一分鐘 (08:46)
            prices_846 = [base, base+3, base+8, base+5, base+2, base-1, base+4, base+6, base+3, base+1]
            for i, price in enumerate(prices_846):
                timestamp = datetime.now().replace(minute=46, second=i*6)
                strategy_panel.process_price_update(price, timestamp)
                time.sleep(0.1)
            
            # 模擬第二分鐘 (08:47)
            prices_847 = [base+2, base+7, base+12, base+15, base+18, base+20, base+16, base+12, base+8, base+5]
            for i, price in enumerate(prices_847):
                timestamp = datetime.now().replace(minute=47, second=i*6)
                strategy_panel.process_price_update(price, timestamp)
                time.sleep(0.1)
            
            # 08:48:00 觸發區間計算
            timestamp = datetime.now().replace(minute=48, second=0)
            strategy_panel.process_price_update(base+6, timestamp)
            
            self.root.after(0, lambda: self.order_frame.add_message("✅ 開盤區間模擬完成"))
        
        # 在背景執行模擬
        threading.Thread(target=simulate_range, daemon=True).start()
    
    def simulate_breakout(self):
        """模擬突破"""
        if not hasattr(self.order_frame, 'strategy_panel') or not self.order_frame.strategy_panel:
            self.order_frame.add_message("❌ 策略面板未載入")
            return
        
        strategy_panel = self.order_frame.strategy_panel
        
        # 檢查是否有區間數據
        if not hasattr(strategy_panel, 'range_detector') or not strategy_panel.range_detector:
            self.order_frame.add_message("⚠️ 請先模擬開盤區間")
            return
        
        if not strategy_panel.range_detector.is_range_ready():
            self.order_frame.add_message("⚠️ 開盤區間尚未準備就緒")
            return
        
        # 獲取區間數據
        range_data = strategy_panel.range_detector.get_range_data()
        breakout_price = range_data['range_high'] + 5  # 突破高點+5
        
        # 模擬突破
        strategy_panel.process_price_update(breakout_price)
        self.order_frame.add_message(f"🚀 模擬突破: 價格{breakout_price} (突破高點+5)")
        
        # 繼續模擬價格變化
        def continue_simulation():
            prices = [
                breakout_price + 10,  # 繼續上漲
                breakout_price + 15,  # 第1口啟動移動停利
                breakout_price + 25,  # 更多獲利
                breakout_price + 40,  # 第2口啟動移動停利
                breakout_price + 30,  # 回檔測試移動停利
            ]
            
            for price in prices:
                time.sleep(1)
                self.root.after(0, lambda p=price: strategy_panel.process_price_update(p))
        
        threading.Thread(target=continue_simulation, daemon=True).start()
    
    def run(self):
        """運行測試程式"""
        self.root.mainloop()

def main():
    """主函數"""
    print("🚀 啟動整合交易系統測試")
    
    try:
        app = IntegratedTradingTest()
        app.run()
    except Exception as e:
        print(f"❌ 系統啟動失敗: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
