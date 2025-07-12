#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
交易策略回測GUI面板
提供圖形化界面來配置和執行回測
"""

import tkinter as tk
from tkinter import messagebox, filedialog
try:
    from tkinter import ttk
except ImportError:
    # 如果ttk不可用，使用基本tkinter
    ttk = None
from datetime import datetime, date
import threading
import subprocess
import sys
import os
from decimal import Decimal
import json

class TradingStrategyGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("台指期貨交易策略回測系統")
        self.root.geometry("800x700")
        
        # 設定基本風格
        try:
            # 嘗試設定現代風格
            self.root.tk.call("source", "/System/Library/Tcl/8.5/ttk/aqua.tcl")
        except:
            # 如果失敗，使用基本設定
            pass
        
        # 初始化變數
        self.init_variables()
        
        # 創建界面
        self.create_widgets()
        
        # 載入預設配置
        self.load_default_config()
    
    def init_variables(self):
        """初始化界面變數"""
        # 基本策略設定
        self.trade_lots = tk.IntVar(value=3)
        self.start_date = tk.StringVar(value="2024-11-01")
        self.end_date = tk.StringVar(value="2024-11-30")
        
        # 移動停利設定 (第1口)
        self.lot1_trigger = tk.StringVar(value="15")
        self.lot1_trailing = tk.StringVar(value="20")
        
        # 移動停利設定 (第2口)
        self.lot2_trigger = tk.StringVar(value="40")
        self.lot2_trailing = tk.StringVar(value="20")
        self.lot2_protection = tk.StringVar(value="2.0")
        
        # 移動停利設定 (第3口)
        self.lot3_trigger = tk.StringVar(value="65")
        self.lot3_trailing = tk.StringVar(value="20")
        self.lot3_protection = tk.StringVar(value="2.0")
        
        # 濾網設定
        self.range_filter_enabled = tk.BooleanVar(value=False)
        self.max_range_points = tk.StringVar(value="50")
        
        self.risk_filter_enabled = tk.BooleanVar(value=False)
        self.daily_loss_limit = tk.StringVar(value="150")
        self.profit_target = tk.StringVar(value="200")
        
        self.stop_loss_filter_enabled = tk.BooleanVar(value=False)
        self.fixed_stop_loss = tk.StringVar(value="15")
        self.use_range_midpoint = tk.BooleanVar(value=False)
        
        # 狀態變數
        self.status_text = tk.StringVar(value="就緒")
        self.is_running = False
    
    def create_widgets(self):
        """創建界面元件"""
        # 主容器
        main_frame = ttk.Frame(self.root, padding="10")
        main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # 配置網格權重
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(0, weight=1)
        main_frame.columnconfigure(1, weight=1)
        
        row = 0
        
        # 標題
        title_label = ttk.Label(main_frame, text="台指期貨交易策略回測系統", 
                               font=('Arial', 16, 'bold'))
        title_label.grid(row=row, column=0, columnspan=2, pady=(0, 20))
        row += 1
        
        # 基本設定區
        self.create_basic_settings(main_frame, row)
        row += 1
        
        # 移動停利設定區
        self.create_trailing_stop_settings(main_frame, row)
        row += 1
        
        # 濾網設定區
        self.create_filter_settings(main_frame, row)
        row += 1
        
        # 控制按鈕區
        self.create_control_buttons(main_frame, row)
        row += 1
        
        # 狀態顯示區
        self.create_status_area(main_frame, row)
    
    def create_basic_settings(self, parent, row):
        """創建基本設定區"""
        frame = ttk.LabelFrame(parent, text="基本設定", padding="10")
        frame.grid(row=row, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=5)
        frame.columnconfigure(1, weight=1)
        frame.columnconfigure(3, weight=1)
        
        # 交易口數
        ttk.Label(frame, text="交易口數:").grid(row=0, column=0, sticky=tk.W, padx=(0, 5))
        lots_combo = ttk.Combobox(frame, textvariable=self.trade_lots, values=[1, 2, 3], 
                                 state="readonly", width=10)
        lots_combo.grid(row=0, column=1, sticky=tk.W, padx=(0, 20))
        
        # 回測日期範圍
        ttk.Label(frame, text="開始日期:").grid(row=0, column=2, sticky=tk.W, padx=(0, 5))
        start_entry = ttk.Entry(frame, textvariable=self.start_date, width=12)
        start_entry.grid(row=0, column=3, sticky=tk.W, padx=(0, 10))
        
        ttk.Label(frame, text="結束日期:").grid(row=1, column=2, sticky=tk.W, padx=(0, 5))
        end_entry = ttk.Entry(frame, textvariable=self.end_date, width=12)
        end_entry.grid(row=1, column=3, sticky=tk.W, padx=(0, 10))
        
        # 日期格式說明
        ttk.Label(frame, text="(格式: YYYY-MM-DD)", font=('Arial', 9)).grid(
            row=2, column=2, columnspan=2, sticky=tk.W, pady=(5, 0))
    
    def create_trailing_stop_settings(self, parent, row):
        """創建移動停利設定區"""
        frame = ttk.LabelFrame(parent, text="移動停利設定", padding="10")
        frame.grid(row=row, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=5)
        frame.columnconfigure(1, weight=1)
        frame.columnconfigure(3, weight=1)
        frame.columnconfigure(5, weight=1)
        
        # 表頭
        ttk.Label(frame, text="口數", font=('Arial', 10, 'bold')).grid(
            row=0, column=0, padx=5, pady=5)
        ttk.Label(frame, text="觸發點數", font=('Arial', 10, 'bold')).grid(
            row=0, column=1, padx=5, pady=5)
        ttk.Label(frame, text="回檔比例(%)", font=('Arial', 10, 'bold')).grid(
            row=0, column=2, padx=5, pady=5)
        ttk.Label(frame, text="保護係數", font=('Arial', 10, 'bold')).grid(
            row=0, column=3, padx=5, pady=5)
        
        # 第1口設定
        ttk.Label(frame, text="第1口").grid(row=1, column=0, padx=5, pady=2)
        ttk.Entry(frame, textvariable=self.lot1_trigger, width=8).grid(
            row=1, column=1, padx=5, pady=2)
        ttk.Entry(frame, textvariable=self.lot1_trailing, width=8).grid(
            row=1, column=2, padx=5, pady=2)
        ttk.Label(frame, text="N/A").grid(row=1, column=3, padx=5, pady=2)
        
        # 第2口設定
        ttk.Label(frame, text="第2口").grid(row=2, column=0, padx=5, pady=2)
        ttk.Entry(frame, textvariable=self.lot2_trigger, width=8).grid(
            row=2, column=1, padx=5, pady=2)
        ttk.Entry(frame, textvariable=self.lot2_trailing, width=8).grid(
            row=2, column=2, padx=5, pady=2)
        ttk.Entry(frame, textvariable=self.lot2_protection, width=8).grid(
            row=2, column=3, padx=5, pady=2)
        
        # 第3口設定
        ttk.Label(frame, text="第3口").grid(row=3, column=0, padx=5, pady=2)
        ttk.Entry(frame, textvariable=self.lot3_trigger, width=8).grid(
            row=3, column=1, padx=5, pady=2)
        ttk.Entry(frame, textvariable=self.lot3_trailing, width=8).grid(
            row=3, column=2, padx=5, pady=2)
        ttk.Entry(frame, textvariable=self.lot3_protection, width=8).grid(
            row=3, column=3, padx=5, pady=2)
    
    def create_filter_settings(self, parent, row):
        """創建濾網設定區"""
        frame = ttk.LabelFrame(parent, text="濾網設定", padding="10")
        frame.grid(row=row, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=5)
        frame.columnconfigure(2, weight=1)
        
        # 區間大小濾網
        ttk.Checkbutton(frame, text="區間大小濾網", variable=self.range_filter_enabled).grid(
            row=0, column=0, sticky=tk.W, pady=2)
        ttk.Label(frame, text="最大區間點數:").grid(row=0, column=1, sticky=tk.W, padx=(20, 5))
        ttk.Entry(frame, textvariable=self.max_range_points, width=8).grid(
            row=0, column=2, sticky=tk.W)
        
        # 風險管理濾網
        ttk.Checkbutton(frame, text="風險管理濾網", variable=self.risk_filter_enabled).grid(
            row=1, column=0, sticky=tk.W, pady=2)
        ttk.Label(frame, text="每日虧損限制:").grid(row=1, column=1, sticky=tk.W, padx=(20, 5))
        ttk.Entry(frame, textvariable=self.daily_loss_limit, width=8).grid(
            row=1, column=2, sticky=tk.W)
        
        ttk.Label(frame, text="每日獲利目標:").grid(row=2, column=1, sticky=tk.W, padx=(20, 5))
        ttk.Entry(frame, textvariable=self.profit_target, width=8).grid(
            row=2, column=2, sticky=tk.W)
        
        # 停損設定濾網
        ttk.Checkbutton(frame, text="停損設定濾網", variable=self.stop_loss_filter_enabled).grid(
            row=3, column=0, sticky=tk.W, pady=2)
        ttk.Label(frame, text="固定停損點數:").grid(row=3, column=1, sticky=tk.W, padx=(20, 5))
        ttk.Entry(frame, textvariable=self.fixed_stop_loss, width=8).grid(
            row=3, column=2, sticky=tk.W)
        
        ttk.Checkbutton(frame, text="使用區間中點", variable=self.use_range_midpoint).grid(
            row=4, column=1, columnspan=2, sticky=tk.W, padx=(20, 0), pady=2)
    
    def create_control_buttons(self, parent, row):
        """創建控制按鈕區"""
        frame = ttk.Frame(parent)
        frame.grid(row=row, column=0, columnspan=2, pady=20)
        
        # 執行回測按鈕
        self.run_button = ttk.Button(frame, text="執行回測", command=self.run_backtest)
        self.run_button.pack(side=tk.LEFT, padx=5)
        
        # 載入配置按鈕
        ttk.Button(frame, text="載入配置", command=self.load_config).pack(side=tk.LEFT, padx=5)
        
        # 儲存配置按鈕
        ttk.Button(frame, text="儲存配置", command=self.save_config).pack(side=tk.LEFT, padx=5)
        
        # 查看報告按鈕
        self.report_button = ttk.Button(frame, text="查看報告", command=self.view_report,
                                       state=tk.DISABLED)
        self.report_button.pack(side=tk.LEFT, padx=5)
        
        # 凱利分析按鈕
        self.kelly_button = ttk.Button(frame, text="凱利分析", command=self.kelly_analysis,
                                      state=tk.DISABLED)
        self.kelly_button.pack(side=tk.LEFT, padx=5)
    
    def create_status_area(self, parent, row):
        """創建狀態顯示區"""
        frame = ttk.LabelFrame(parent, text="狀態", padding="10")
        frame.grid(row=row, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=5)
        frame.columnconfigure(0, weight=1)
        
        # 狀態標籤
        status_label = ttk.Label(frame, textvariable=self.status_text, font=('Arial', 10))
        status_label.grid(row=0, column=0, sticky=tk.W)
        
        # 進度條
        self.progress = ttk.Progressbar(frame, mode='indeterminate')
        self.progress.grid(row=1, column=0, sticky=(tk.W, tk.E), pady=(10, 0))
    
    def load_default_config(self):
        """載入預設配置"""
        # 這裡可以從文件載入預設配置
        pass
    
    def run_backtest(self):
        """執行回測"""
        if self.is_running:
            return
        
        try:
            # 驗證輸入
            self.validate_inputs()
            
            # 設定執行狀態
            self.is_running = True
            self.run_button.config(state=tk.DISABLED)
            self.status_text.set("正在執行回測...")
            self.progress.start()
            
            # 在新線程中執行回測
            thread = threading.Thread(target=self._run_backtest_thread)
            thread.daemon = True
            thread.start()
            
        except ValueError as e:
            messagebox.showerror("輸入錯誤", str(e))
    
    def _run_backtest_thread(self):
        """在背景線程執行回測"""
        try:
            # 生成配置文件
            config_data = self.generate_config()
            
            # 執行回測腳本
            result = self.execute_backtest(config_data)
            
            # 更新UI (需要在主線程中執行)
            self.root.after(0, self._backtest_completed, result)
            
        except Exception as e:
            self.root.after(0, self._backtest_error, str(e))
    
    def _backtest_completed(self, result):
        """回測完成後的UI更新"""
        self.is_running = False
        self.run_button.config(state=tk.NORMAL)
        self.progress.stop()
        self.status_text.set("回測完成")
        
        # 啟用報告按鈕
        self.report_button.config(state=tk.NORMAL)
        self.kelly_button.config(state=tk.NORMAL)
        
        messagebox.showinfo("完成", "回測執行完成！")
    
    def _backtest_error(self, error_msg):
        """回測錯誤後的UI更新"""
        self.is_running = False
        self.run_button.config(state=tk.NORMAL)
        self.progress.stop()
        self.status_text.set("執行失敗")
        
        messagebox.showerror("錯誤", f"回測執行失敗：{error_msg}")
    
    def validate_inputs(self):
        """驗證輸入參數"""
        # 驗證日期格式
        try:
            datetime.strptime(self.start_date.get(), "%Y-%m-%d")
            datetime.strptime(self.end_date.get(), "%Y-%m-%d")
        except ValueError:
            raise ValueError("日期格式錯誤，請使用 YYYY-MM-DD 格式")
        
        # 驗證數值參數
        try:
            float(self.lot1_trigger.get())
            float(self.lot1_trailing.get())
            if self.trade_lots.get() >= 2:
                float(self.lot2_trigger.get())
                float(self.lot2_trailing.get())
                float(self.lot2_protection.get())
            if self.trade_lots.get() >= 3:
                float(self.lot3_trigger.get())
                float(self.lot3_trailing.get())
                float(self.lot3_protection.get())
        except ValueError:
            raise ValueError("移動停利參數必須為數值")
    
    def generate_config(self):
        """生成配置數據"""
        config = {
            "trade_lots": self.trade_lots.get(),
            "start_date": self.start_date.get(),
            "end_date": self.end_date.get(),
            "lot_settings": {
                "lot1": {
                    "trigger": float(self.lot1_trigger.get()),
                    "trailing": float(self.lot1_trailing.get())
                },
                "lot2": {
                    "trigger": float(self.lot2_trigger.get()),
                    "trailing": float(self.lot2_trailing.get()),
                    "protection": float(self.lot2_protection.get())
                },
                "lot3": {
                    "trigger": float(self.lot3_trigger.get()),
                    "trailing": float(self.lot3_trailing.get()),
                    "protection": float(self.lot3_protection.get())
                }
            },
            "filters": {
                "range_filter": {
                    "enabled": self.range_filter_enabled.get(),
                    "max_range_points": float(self.max_range_points.get())
                },
                "risk_filter": {
                    "enabled": self.risk_filter_enabled.get(),
                    "daily_loss_limit": float(self.daily_loss_limit.get()),
                    "profit_target": float(self.profit_target.get())
                },
                "stop_loss_filter": {
                    "enabled": self.stop_loss_filter_enabled.get(),
                    "fixed_stop_loss": float(self.fixed_stop_loss.get()),
                    "use_range_midpoint": self.use_range_midpoint.get()
                }
            }
        }
        return config

    def execute_backtest(self, config_data):
        """執行回測腳本"""
        try:
            # 構建命令行參數
            cmd = [
                sys.executable,
                "multi_Profit-Funded Risk_多口.py",
                "--start-date", config_data["start_date"],
                "--end-date", config_data["end_date"],
                "--gui-mode",  # 添加GUI模式標記
                "--config", json.dumps(config_data)  # 傳遞配置
            ]

            # 執行回測
            result = subprocess.run(
                cmd,
                cwd=os.path.dirname(os.path.abspath(__file__)),
                capture_output=True,
                text=True,
                encoding='utf-8'
            )

            if result.returncode != 0:
                raise Exception(f"回測執行失敗：{result.stderr}")

            return result.stdout

        except Exception as e:
            raise Exception(f"執行回測時發生錯誤：{e}")
    
    def view_report(self):
        """查看回測報告"""
        messagebox.showinfo("報告", "報告功能將在下一步實現")
    
    def kelly_analysis(self):
        """凱利公式分析"""
        messagebox.showinfo("分析", "凱利分析功能將在下一步實現")
    
    def load_config(self):
        """載入配置文件"""
        filename = filedialog.askopenfilename(
            title="載入配置",
            filetypes=[("JSON files", "*.json"), ("All files", "*.*")]
        )
        if filename:
            try:
                with open(filename, 'r', encoding='utf-8') as f:
                    config = json.load(f)
                self.apply_config(config)
                messagebox.showinfo("成功", "配置載入成功")
            except Exception as e:
                messagebox.showerror("錯誤", f"載入配置失敗：{e}")
    
    def save_config(self):
        """儲存配置文件"""
        filename = filedialog.asksaveasfilename(
            title="儲存配置",
            defaultextension=".json",
            filetypes=[("JSON files", "*.json"), ("All files", "*.*")]
        )
        if filename:
            try:
                config = self.get_current_config()
                with open(filename, 'w', encoding='utf-8') as f:
                    json.dump(config, f, indent=2, ensure_ascii=False)
                messagebox.showinfo("成功", "配置儲存成功")
            except Exception as e:
                messagebox.showerror("錯誤", f"儲存配置失敗：{e}")
    
    def get_current_config(self):
        """獲取當前配置"""
        return {
            "trade_lots": self.trade_lots.get(),
            "start_date": self.start_date.get(),
            "end_date": self.end_date.get(),
            "lot1_trigger": self.lot1_trigger.get(),
            "lot1_trailing": self.lot1_trailing.get(),
            "lot2_trigger": self.lot2_trigger.get(),
            "lot2_trailing": self.lot2_trailing.get(),
            "lot2_protection": self.lot2_protection.get(),
            "lot3_trigger": self.lot3_trigger.get(),
            "lot3_trailing": self.lot3_trailing.get(),
            "lot3_protection": self.lot3_protection.get(),
            "range_filter_enabled": self.range_filter_enabled.get(),
            "max_range_points": self.max_range_points.get(),
            "risk_filter_enabled": self.risk_filter_enabled.get(),
            "daily_loss_limit": self.daily_loss_limit.get(),
            "profit_target": self.profit_target.get(),
            "stop_loss_filter_enabled": self.stop_loss_filter_enabled.get(),
            "fixed_stop_loss": self.fixed_stop_loss.get(),
            "use_range_midpoint": self.use_range_midpoint.get()
        }

    def apply_config(self, config):
        """應用配置到界面"""
        try:
            self.trade_lots.set(config.get("trade_lots", 3))
            self.start_date.set(config.get("start_date", "2024-11-01"))
            self.end_date.set(config.get("end_date", "2024-11-30"))

            self.lot1_trigger.set(config.get("lot1_trigger", "15"))
            self.lot1_trailing.set(config.get("lot1_trailing", "20"))
            self.lot2_trigger.set(config.get("lot2_trigger", "40"))
            self.lot2_trailing.set(config.get("lot2_trailing", "20"))
            self.lot2_protection.set(config.get("lot2_protection", "2.0"))
            self.lot3_trigger.set(config.get("lot3_trigger", "65"))
            self.lot3_trailing.set(config.get("lot3_trailing", "20"))
            self.lot3_protection.set(config.get("lot3_protection", "2.0"))

            self.range_filter_enabled.set(config.get("range_filter_enabled", False))
            self.max_range_points.set(config.get("max_range_points", "50"))
            self.risk_filter_enabled.set(config.get("risk_filter_enabled", False))
            self.daily_loss_limit.set(config.get("daily_loss_limit", "150"))
            self.profit_target.set(config.get("profit_target", "200"))
            self.stop_loss_filter_enabled.set(config.get("stop_loss_filter_enabled", False))
            self.fixed_stop_loss.set(config.get("fixed_stop_loss", "15"))
            self.use_range_midpoint.set(config.get("use_range_midpoint", False))

        except Exception as e:
            raise Exception(f"應用配置時發生錯誤：{e}")

def main():
    root = tk.Tk()
    app = TradingStrategyGUI(root)
    root.mainloop()

if __name__ == "__main__":
    main()
