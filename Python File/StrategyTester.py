#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
獨立策略測試程式
完全獨立於原有下單系統，專門用於測試策略功能

🎯 STRATEGY_TESTER_2025_06_30
✅ 完全獨立的策略開發環境
✅ 包含完整的策略邏輯測試
✅ 提供穩定版下單API整合示例
✅ 支援模擬和實盤交易切換
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

import tkinter as tk
from tkinter import ttk, messagebox
import threading
import time
import random
from datetime import datetime
import logging

# 設定日誌
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# 導入策略模組
try:
    from strategy.strategy_tab import StrategyTab
    STRATEGY_AVAILABLE = True
    logger.info("✅ 策略模組載入成功")
except ImportError as e:
    STRATEGY_AVAILABLE = False
    logger.error(f"❌ 策略模組載入失敗: {e}")

# 導入穩定版下單API
try:
    from stable_order_api import get_stable_order_api, strategy_place_order
    STABLE_API_AVAILABLE = True
    logger.info("✅ 穩定版下單API載入成功")
except ImportError as e:
    STABLE_API_AVAILABLE = False
    logger.warning(f"⚠️ 穩定版下單API未載入: {e}")
    logger.info("💡 如需實盤交易，請確保OrderTester.py正在運行")

class StrategyTesterApp:
    """獨立策略測試應用程式"""
    
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("🎯 策略交易系統測試 - 獨立版本")
        self.root.geometry("1400x900")
        
        # 價格模擬相關
        self.base_price = 22000
        self.price_running = False
        self.current_price = self.base_price
        
        # 建立UI
        self.create_widgets()
        
        # 顯示歡迎訊息
        self.show_welcome_message()
    
    def create_widgets(self):
        """建立UI控件"""
        # 主標題
        title_frame = tk.Frame(self.root, bg="navy", height=60)
        title_frame.pack(fill="x", padx=5, pady=5)
        title_frame.pack_propagate(False)
        
        title_label = tk.Label(title_frame, text="🎯 策略交易系統測試", 
                              fg="white", bg="navy", font=("Arial", 16, "bold"))
        title_label.pack(expand=True)
        
        subtitle_label = tk.Label(title_frame, text="獨立測試版本 - 不影響原有下單系統", 
                                 fg="lightblue", bg="navy", font=("Arial", 10))
        subtitle_label.pack()
        
        # 控制面板
        self.create_control_panel()
        
        # 策略面板
        if STRATEGY_AVAILABLE:
            self.create_strategy_panel()
        else:
            self.create_error_panel()
    
    def create_control_panel(self):
        """創建控制面板"""
        control_frame = tk.LabelFrame(self.root, text="🎮 測試控制面板", 
                                     fg="green", font=("Arial", 12, "bold"))
        control_frame.pack(fill="x", padx=10, pady=5)
        
        # 第一行 - 價格控制
        row1 = tk.Frame(control_frame)
        row1.pack(fill="x", padx=10, pady=5)
        
        tk.Label(row1, text="基準價格:", font=("Arial", 10)).pack(side="left", padx=5)
        self.entry_base_price = tk.Entry(row1, width=8, font=("Arial", 10))
        self.entry_base_price.insert(0, str(self.base_price))
        self.entry_base_price.pack(side="left", padx=5)
        
        tk.Button(row1, text="更新價格", command=self.update_base_price,
                 bg="lightblue", font=("Arial", 9)).pack(side="left", padx=5)
        
        tk.Label(row1, text="當前價格:", font=("Arial", 10)).pack(side="left", padx=(20, 5))
        self.label_current_price = tk.Label(row1, text=str(self.current_price), 
                                           fg="red", font=("Arial", 12, "bold"))
        self.label_current_price.pack(side="left", padx=5)
        
        # 第二行 - 模擬控制
        row2 = tk.Frame(control_frame)
        row2.pack(fill="x", padx=10, pady=5)
        
        self.btn_start_sim = tk.Button(row2, text="🎯 開始價格模擬", command=self.start_price_simulation,
                                      bg="green", fg="white", font=("Arial", 10, "bold"))
        self.btn_start_sim.pack(side="left", padx=5)
        
        self.btn_stop_sim = tk.Button(row2, text="⏹️ 停止價格模擬", command=self.stop_price_simulation,
                                     bg="red", fg="white", font=("Arial", 10, "bold"))
        self.btn_stop_sim.pack(side="left", padx=5)
        
        tk.Button(row2, text="📊 模擬開盤區間", command=self.simulate_opening_range,
                 bg="orange", font=("Arial", 10)).pack(side="left", padx=5)
        
        tk.Button(row2, text="🚀 模擬突破", command=self.simulate_breakout,
                 bg="purple", fg="white", font=("Arial", 10)).pack(side="left", padx=5)

        # 第三行 - 實盤交易測試
        row3 = tk.Frame(control_frame)
        row3.pack(fill="x", padx=10, pady=5)

        tk.Label(row3, text="實盤交易測試:", font=("Arial", 10, "bold"), fg="red").pack(side="left", padx=5)

        if STABLE_API_AVAILABLE:
            tk.Button(row3, text="📈 測試買進1口", command=self.test_buy_order,
                     bg="darkgreen", fg="white", font=("Arial", 9)).pack(side="left", padx=5)

            tk.Button(row3, text="📉 測試賣出1口", command=self.test_sell_order,
                     bg="darkred", fg="white", font=("Arial", 9)).pack(side="left", padx=5)

            tk.Label(row3, text="⚠️ 需要OrderTester.py運行", fg="orange", font=("Arial", 8)).pack(side="left", padx=10)
        else:
            tk.Label(row3, text="❌ 穩定版API未載入", fg="red", font=("Arial", 9)).pack(side="left", padx=5)

        # 狀態顯示
        tk.Label(row2, text="狀態:", font=("Arial", 10)).pack(side="left", padx=(20, 5))
        self.status_var = tk.StringVar(value="系統就緒")
        tk.Label(row2, textvariable=self.status_var, fg="blue", font=("Arial", 10)).pack(side="left", padx=5)
    
    def create_strategy_panel(self):
        """創建策略面板"""
        try:
            # 策略面板容器
            strategy_container = tk.LabelFrame(self.root, text="🎯 策略控制面板", 
                                             fg="blue", font=("Arial", 12, "bold"))
            strategy_container.pack(fill="both", expand=True, padx=10, pady=5)
            
            # 創建策略分頁
            self.strategy_tab = StrategyTab(strategy_container)
            self.strategy_tab.pack(fill="both", expand=True, padx=5, pady=5)
            
            logger.info("✅ 策略面板創建成功")
            
        except Exception as e:
            logger.error(f"❌ 策略面板創建失敗: {e}")
            self.create_error_panel()
    
    def create_error_panel(self):
        """創建錯誤面板"""
        error_frame = tk.LabelFrame(self.root, text="❌ 策略模組載入失敗", 
                                   fg="red", font=("Arial", 12, "bold"))
        error_frame.pack(fill="both", expand=True, padx=10, pady=5)
        
        error_text = """
策略模組載入失敗，可能的原因：

1. 策略模組檔案不存在或有錯誤
2. 相依模組未正確安裝
3. Python路徑設定問題

請檢查以下檔案是否存在：
- strategy/strategy_tab.py
- strategy/strategy_config.py
- strategy/signal_detector.py
- strategy/position_manager.py
- database/sqlite_manager.py
- utils/time_utils.py

建議：
1. 檢查所有策略模組檔案
2. 確認Python路徑設定
3. 重新啟動程式
"""
        
        text_widget = tk.Text(error_frame, wrap=tk.WORD, font=("Arial", 10))
        text_widget.pack(fill="both", expand=True, padx=10, pady=10)
        text_widget.insert("1.0", error_text)
        text_widget.config(state="disabled")
    
    def show_welcome_message(self):
        """顯示歡迎訊息"""
        if hasattr(self, 'strategy_tab'):
            welcome_msg = """
🎉 歡迎使用策略交易系統測試！

📋 測試流程：
1. 點擊「🎯 開始價格模擬」→ 開始即時價格更新
2. 在策略面板中點擊「測試用(當前時間)」→ 設定測試時段
3. 點擊「🚀 啟動策略」→ 開始監控開盤區間
4. 點擊「📊 模擬開盤區間」→ 模擬兩分鐘K線數據
5. 點擊「🚀 模擬突破」→ 測試突破信號和開倉

🎯 功能特色：
- 完全獨立測試，不影響原有下單系統
- 支援自定義時間段測試
- 即時價格模擬和策略執行
- 完整的多口移動停利測試
- 詳細的策略執行日誌

🧪 開始測試吧！
"""
            self.strategy_tab.log_message(welcome_msg)
    
    def update_base_price(self):
        """更新基準價格"""
        try:
            new_price = int(self.entry_base_price.get())
            self.base_price = new_price
            self.current_price = new_price
            self.label_current_price.config(text=str(new_price))
            
            if hasattr(self, 'strategy_tab'):
                self.strategy_tab.log_message(f"📊 基準價格已更新為: {new_price}")
            
            self.status_var.set(f"基準價格: {new_price}")
            
        except ValueError:
            messagebox.showerror("錯誤", "請輸入有效的價格數字")
    
    def start_price_simulation(self):
        """開始價格模擬"""
        if self.price_running:
            return
        
        self.price_running = True
        self.status_var.set("價格模擬中...")
        self.btn_start_sim.config(state="disabled")
        self.btn_stop_sim.config(state="normal")
        
        if hasattr(self, 'strategy_tab'):
            self.strategy_tab.log_message("🎯 開始模擬即時報價")
        
        def price_thread():
            while self.price_running:
                try:
                    # 生成隨機價格變動
                    change = random.randint(-3, 3)
                    self.current_price = self.base_price + change
                    
                    # 更新UI顯示
                    self.root.after(0, lambda: self.label_current_price.config(text=str(self.current_price)))
                    
                    # 更新策略面板
                    if hasattr(self, 'strategy_tab'):
                        timestamp = datetime.now()
                        self.root.after(0, lambda: self.strategy_tab.process_price_update(self.current_price, timestamp))
                    
                    time.sleep(0.5)  # 每0.5秒更新一次
                    
                except Exception as e:
                    logger.error(f"價格模擬錯誤: {e}")
                    break
        
        # 啟動價格模擬線程
        threading.Thread(target=price_thread, daemon=True).start()
    
    def stop_price_simulation(self):
        """停止價格模擬"""
        self.price_running = False
        self.status_var.set("價格模擬已停止")
        self.btn_start_sim.config(state="normal")
        self.btn_stop_sim.config(state="disabled")
        
        if hasattr(self, 'strategy_tab'):
            self.strategy_tab.log_message("⏹️ 停止模擬報價")
    
    def simulate_opening_range(self):
        """模擬開盤區間"""
        if not hasattr(self, 'strategy_tab'):
            messagebox.showwarning("警告", "策略面板未載入")
            return
        
        # 調用策略面板的模擬功能
        self.strategy_tab.simulate_opening_range()
    
    def simulate_breakout(self):
        """模擬突破"""
        if not hasattr(self, 'strategy_tab'):
            messagebox.showwarning("警告", "策略面板未載入")
            return

        # 調用策略面板的模擬功能
        self.strategy_tab.simulate_breakout()

    def test_buy_order(self):
        """測試買進下單"""
        if not STABLE_API_AVAILABLE:
            messagebox.showerror("錯誤", "穩定版下單API未載入")
            return

        try:
            # 調用穩定版下單API
            result = strategy_place_order(
                product='MTX00',
                direction='BUY',
                price=0.0,  # 市價
                quantity=1,
                order_type='ROD'
            )

            if result['success']:
                message = f"✅ 測試買進成功!\n委託編號: {result['order_id']}\n時間: {result['timestamp']}"
                messagebox.showinfo("下單成功", message)
                logger.info(f"測試買進成功: {result}")
            else:
                message = f"❌ 測試買進失敗!\n錯誤訊息: {result['message']}\n時間: {result['timestamp']}"
                messagebox.showerror("下單失敗", message)
                logger.error(f"測試買進失敗: {result}")

        except Exception as e:
            error_msg = f"測試買進異常: {str(e)}"
            messagebox.showerror("系統錯誤", error_msg)
            logger.error(error_msg)

    def test_sell_order(self):
        """測試賣出下單"""
        if not STABLE_API_AVAILABLE:
            messagebox.showerror("錯誤", "穩定版下單API未載入")
            return

        try:
            # 調用穩定版下單API
            result = strategy_place_order(
                product='MTX00',
                direction='SELL',
                price=0.0,  # 市價
                quantity=1,
                order_type='ROD'
            )

            if result['success']:
                message = f"✅ 測試賣出成功!\n委託編號: {result['order_id']}\n時間: {result['timestamp']}"
                messagebox.showinfo("下單成功", message)
                logger.info(f"測試賣出成功: {result}")
            else:
                message = f"❌ 測試賣出失敗!\n錯誤訊息: {result['message']}\n時間: {result['timestamp']}"
                messagebox.showerror("下單失敗", message)
                logger.error(f"測試賣出失敗: {result}")

        except Exception as e:
            error_msg = f"測試賣出異常: {str(e)}"
            messagebox.showerror("系統錯誤", error_msg)
            logger.error(error_msg)
    
    def run(self):
        """運行應用程式"""
        try:
            self.root.mainloop()
        except Exception as e:
            logger.error(f"應用程式運行錯誤: {e}")

def main():
    """主函數"""
    print("🚀 啟動獨立策略測試程式")
    print("=" * 50)
    
    if not STRATEGY_AVAILABLE:
        print("❌ 策略模組載入失敗")
        print("請檢查策略模組檔案是否存在")
        print("=" * 50)
    
    try:
        app = StrategyTesterApp()
        app.run()
    except Exception as e:
        print(f"❌ 程式啟動失敗: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
