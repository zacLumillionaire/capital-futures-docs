#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
簡化版交易策略回測GUI面板
使用基本tkinter，避免版本兼容問題
"""

import tkinter as tk
from tkinter import messagebox, filedialog
from datetime import datetime
import threading
import subprocess
import sys
import os
import json

class SimpleTradingGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("台指期貨交易策略回測系統")
        self.root.geometry("700x600")
        
        # 初始化變數
        self.init_variables()
        
        # 創建界面
        self.create_widgets()
    
    def init_variables(self):
        """初始化界面變數"""
        # 基本策略設定
        self.trade_lots = tk.IntVar(value=3)
        self.start_date = tk.StringVar(value="2024-11-01")
        self.end_date = tk.StringVar(value="2024-11-30")
        
        # 移動停利設定
        self.lot1_trigger = tk.StringVar(value="15")
        self.lot1_trailing = tk.StringVar(value="20")
        self.lot2_trigger = tk.StringVar(value="40")
        self.lot2_trailing = tk.StringVar(value="20")
        self.lot2_protection = tk.StringVar(value="2.0")
        self.lot3_trigger = tk.StringVar(value="65")
        self.lot3_trailing = tk.StringVar(value="20")
        self.lot3_protection = tk.StringVar(value="2.0")
        
        # 濾網設定
        self.range_filter_enabled = tk.BooleanVar(value=False)
        self.max_range_points = tk.StringVar(value="50")
        self.risk_filter_enabled = tk.BooleanVar(value=False)
        self.daily_loss_limit = tk.StringVar(value="150")
        self.profit_target = tk.StringVar(value="200")
        
        # 狀態變數
        self.status_text = tk.StringVar(value="就緒")
        self.is_running = False
    
    def create_widgets(self):
        """創建界面元件"""
        # 主框架
        main_frame = tk.Frame(self.root, padx=20, pady=20)
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # 標題
        title_label = tk.Label(main_frame, text="台指期貨交易策略回測系統", 
                              font=('Arial', 16, 'bold'))
        title_label.pack(pady=(0, 20))
        
        # 基本設定區
        self.create_basic_settings(main_frame)
        
        # 移動停利設定區
        self.create_trailing_stop_settings(main_frame)
        
        # 濾網設定區
        self.create_filter_settings(main_frame)
        
        # 控制按鈕區
        self.create_control_buttons(main_frame)
        
        # 狀態顯示區
        self.create_status_area(main_frame)
    
    def create_basic_settings(self, parent):
        """創建基本設定區"""
        frame = tk.LabelFrame(parent, text="基本設定", padx=10, pady=10)
        frame.pack(fill=tk.X, pady=5)
        
        # 第一行：交易口數和開始日期
        row1 = tk.Frame(frame)
        row1.pack(fill=tk.X, pady=2)
        
        tk.Label(row1, text="交易口數:").pack(side=tk.LEFT)
        lots_frame = tk.Frame(row1)
        lots_frame.pack(side=tk.LEFT, padx=(5, 20))
        
        for i in [1, 2, 3]:
            tk.Radiobutton(lots_frame, text=str(i), variable=self.trade_lots, 
                          value=i).pack(side=tk.LEFT)
        
        tk.Label(row1, text="開始日期:").pack(side=tk.LEFT)
        tk.Entry(row1, textvariable=self.start_date, width=12).pack(side=tk.LEFT, padx=5)
        
        # 第二行：結束日期
        row2 = tk.Frame(frame)
        row2.pack(fill=tk.X, pady=2)
        
        tk.Label(row2, text="結束日期:").pack(side=tk.LEFT)
        tk.Entry(row2, textvariable=self.end_date, width=12).pack(side=tk.LEFT, padx=5)
        tk.Label(row2, text="(格式: YYYY-MM-DD)", font=('Arial', 9)).pack(side=tk.LEFT, padx=10)
    
    def create_trailing_stop_settings(self, parent):
        """創建移動停利設定區"""
        frame = tk.LabelFrame(parent, text="移動停利設定", padx=10, pady=10)
        frame.pack(fill=tk.X, pady=5)
        
        # 表頭
        header = tk.Frame(frame)
        header.pack(fill=tk.X, pady=2)
        tk.Label(header, text="口數", width=8, font=('Arial', 10, 'bold')).pack(side=tk.LEFT)
        tk.Label(header, text="觸發點數", width=10, font=('Arial', 10, 'bold')).pack(side=tk.LEFT)
        tk.Label(header, text="回檔比例(%)", width=12, font=('Arial', 10, 'bold')).pack(side=tk.LEFT)
        tk.Label(header, text="保護係數", width=10, font=('Arial', 10, 'bold')).pack(side=tk.LEFT)
        
        # 第1口
        row1 = tk.Frame(frame)
        row1.pack(fill=tk.X, pady=2)
        tk.Label(row1, text="第1口", width=8).pack(side=tk.LEFT)
        tk.Entry(row1, textvariable=self.lot1_trigger, width=10).pack(side=tk.LEFT)
        tk.Entry(row1, textvariable=self.lot1_trailing, width=12).pack(side=tk.LEFT)
        tk.Label(row1, text="N/A", width=10).pack(side=tk.LEFT)
        
        # 第2口
        row2 = tk.Frame(frame)
        row2.pack(fill=tk.X, pady=2)
        tk.Label(row2, text="第2口", width=8).pack(side=tk.LEFT)
        tk.Entry(row2, textvariable=self.lot2_trigger, width=10).pack(side=tk.LEFT)
        tk.Entry(row2, textvariable=self.lot2_trailing, width=12).pack(side=tk.LEFT)
        tk.Entry(row2, textvariable=self.lot2_protection, width=10).pack(side=tk.LEFT)
        
        # 第3口
        row3 = tk.Frame(frame)
        row3.pack(fill=tk.X, pady=2)
        tk.Label(row3, text="第3口", width=8).pack(side=tk.LEFT)
        tk.Entry(row3, textvariable=self.lot3_trigger, width=10).pack(side=tk.LEFT)
        tk.Entry(row3, textvariable=self.lot3_trailing, width=12).pack(side=tk.LEFT)
        tk.Entry(row3, textvariable=self.lot3_protection, width=10).pack(side=tk.LEFT)
    
    def create_filter_settings(self, parent):
        """創建濾網設定區"""
        frame = tk.LabelFrame(parent, text="濾網設定", padx=10, pady=10)
        frame.pack(fill=tk.X, pady=5)
        
        # 區間大小濾網
        row1 = tk.Frame(frame)
        row1.pack(fill=tk.X, pady=2)
        tk.Checkbutton(row1, text="區間大小濾網", variable=self.range_filter_enabled).pack(side=tk.LEFT)
        tk.Label(row1, text="最大區間點數:").pack(side=tk.LEFT, padx=(20, 5))
        tk.Entry(row1, textvariable=self.max_range_points, width=8).pack(side=tk.LEFT)
        
        # 風險管理濾網
        row2 = tk.Frame(frame)
        row2.pack(fill=tk.X, pady=2)
        tk.Checkbutton(row2, text="風險管理濾網", variable=self.risk_filter_enabled).pack(side=tk.LEFT)
        tk.Label(row2, text="每日虧損限制:").pack(side=tk.LEFT, padx=(20, 5))
        tk.Entry(row2, textvariable=self.daily_loss_limit, width=8).pack(side=tk.LEFT)
        
        row3 = tk.Frame(frame)
        row3.pack(fill=tk.X, pady=2)
        tk.Label(row3, text="每日獲利目標:").pack(side=tk.LEFT, padx=(140, 5))
        tk.Entry(row3, textvariable=self.profit_target, width=8).pack(side=tk.LEFT)
    
    def create_control_buttons(self, parent):
        """創建控制按鈕區"""
        frame = tk.Frame(parent)
        frame.pack(pady=20)
        
        # 執行回測按鈕
        self.run_button = tk.Button(frame, text="執行回測", command=self.run_backtest,
                                   bg='#4CAF50', fg='white', font=('Arial', 12, 'bold'),
                                   padx=20, pady=5)
        self.run_button.pack(side=tk.LEFT, padx=5)
        
        # 載入配置按鈕
        tk.Button(frame, text="載入配置", command=self.load_config,
                 padx=15, pady=5).pack(side=tk.LEFT, padx=5)
        
        # 儲存配置按鈕
        tk.Button(frame, text="儲存配置", command=self.save_config,
                 padx=15, pady=5).pack(side=tk.LEFT, padx=5)
        
        # 查看報告按鈕
        self.report_button = tk.Button(frame, text="查看報告", command=self.view_report,
                                      state=tk.DISABLED, padx=15, pady=5)
        self.report_button.pack(side=tk.LEFT, padx=5)
        
        # 凱利分析按鈕
        self.kelly_button = tk.Button(frame, text="凱利分析", command=self.kelly_analysis,
                                     state=tk.DISABLED, padx=15, pady=5)
        self.kelly_button.pack(side=tk.LEFT, padx=5)
    
    def create_status_area(self, parent):
        """創建狀態顯示區"""
        frame = tk.LabelFrame(parent, text="狀態", padx=10, pady=10)
        frame.pack(fill=tk.X, pady=5)
        
        # 狀態標籤
        status_label = tk.Label(frame, textvariable=self.status_text, font=('Arial', 10))
        status_label.pack()
    
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
        self.status_text.set("回測完成")
        
        # 啟用報告按鈕
        self.report_button.config(state=tk.NORMAL)
        self.kelly_button.config(state=tk.NORMAL)
        
        messagebox.showinfo("完成", "回測執行完成！")
    
    def _backtest_error(self, error_msg):
        """回測錯誤後的UI更新"""
        self.is_running = False
        self.run_button.config(state=tk.NORMAL)
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
                    "enabled": False,
                    "fixed_stop_loss": 15.0,
                    "use_range_midpoint": False
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
        messagebox.showinfo("報告", "報告功能：請查看VS Code終端中的詳細回測結果")
    
    def kelly_analysis(self):
        """凱利公式分析"""
        try:
            # 執行凱利分析
            result = subprocess.run(
                [sys.executable, "kelly_formula_analyzer.py"],
                cwd=os.path.dirname(os.path.abspath(__file__)),
                capture_output=True,
                text=True,
                encoding='utf-8'
            )
            
            if result.returncode == 0:
                messagebox.showinfo("凱利分析", "凱利分析完成！請查看VS Code終端中的詳細分析結果")
            else:
                messagebox.showerror("錯誤", f"凱利分析失敗：{result.stderr}")
                
        except Exception as e:
            messagebox.showerror("錯誤", f"執行凱利分析時發生錯誤：{e}")
    
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
            "profit_target": self.profit_target.get()
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
            
        except Exception as e:
            raise Exception(f"應用配置時發生錯誤：{e}")

def main():
    root = tk.Tk()
    app = SimpleTradingGUI(root)
    root.mainloop()

if __name__ == "__main__":
    main()
