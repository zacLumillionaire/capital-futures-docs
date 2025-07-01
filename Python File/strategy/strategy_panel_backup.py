#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
策略控制面板
整合到下單機中的策略監控和設定界面
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import tkinter as tk
from tkinter import ttk, messagebox
from datetime import datetime, time
import threading
import logging

from strategy.strategy_config import StrategyConfig
from strategy.signal_detector import OpeningRangeDetector, BreakoutSignalDetector
from strategy.position_manager import MultiLotPositionManager
from database.sqlite_manager import SQLiteManager
from utils.time_utils import TradingTimeManager

logger = logging.getLogger(__name__)

class StrategyControlPanel(tk.Frame):
    """策略控制面板"""
    
    def __init__(self, master=None, quote_callback=None):
        super().__init__(master)
        self.master = master
        self.quote_callback = quote_callback  # 接收即時報價的回調函數
        
        # 策略組件
        self.config = None
        self.range_detector = None
        self.breakout_detector = None
        self.position_manager = None
        self.time_manager = TradingTimeManager()
        self.db_manager = SQLiteManager("strategy_trading.db")
        
        # 狀態變數
        self.strategy_active = False
        self.monitoring_active = False
        self.current_price = 0
        self.last_update_time = None
        
        # UI變數
        self.status_vars = {}
        self.data_vars = {}
        
        # 建立UI
        self.create_widgets()
        
        # 載入預設配置
        self.load_default_config()
        
        # 啟動狀態更新
        self.start_status_update()
    
    def create_widgets(self):
        """建立UI控件"""
        # 主標題
        title_frame = tk.LabelFrame(self, text="🎯 開盤區間突破策略", fg="blue", font=("Arial", 12, "bold"))
        title_frame.grid(row=0, column=0, columnspan=2, sticky="ew", padx=5, pady=5)
        
        # 策略設定區域
        self.create_config_section(title_frame)
        
        # 時間設定區域
        self.create_time_section()
        
        # 區間監控區域
        self.create_range_section()
        
        # 部位狀態區域
        self.create_position_section()
        
        # 控制按鈕區域
        self.create_control_section()
        
        # 日誌顯示區域
        self.create_log_section()
    
    def create_config_section(self, parent):
        """創建策略設定區域"""
        config_frame = tk.Frame(parent)
        config_frame.grid(row=0, column=0, columnspan=2, sticky="ew", padx=5, pady=5)
        
        # 交易口數設定
        tk.Label(config_frame, text="交易口數:").grid(row=0, column=0, sticky="w", padx=5)
        self.combo_lots = ttk.Combobox(config_frame, width=8, state='readonly')
        self.combo_lots['values'] = ['1口', '2口', '3口', '4口']
        self.combo_lots.set('3口')  # 預設3口
        self.combo_lots.grid(row=0, column=1, padx=5)
        self.combo_lots.bind('<<ComboboxSelected>>', self.on_lots_changed)
        
        # 策略狀態
        tk.Label(config_frame, text="策略狀態:").grid(row=0, column=2, sticky="w", padx=5)
        self.status_vars['strategy'] = tk.StringVar(value="🔴 未啟動")
        tk.Label(config_frame, textvariable=self.status_vars['strategy'], fg="red").grid(row=0, column=3, sticky="w", padx=5)
        
        # 當前時段
        tk.Label(config_frame, text="當前時段:").grid(row=0, column=4, sticky="w", padx=5)
        self.status_vars['session'] = tk.StringVar(value="等待中...")
        tk.Label(config_frame, textvariable=self.status_vars['session']).grid(row=0, column=5, sticky="w", padx=5)
    
    def create_time_section(self):
        """創建時間設定區域"""
        time_frame = tk.LabelFrame(self, text="⏰ 時間設定 (可自定義測試時段)", fg="green")
        time_frame.grid(row=1, column=0, columnspan=2, sticky="ew", padx=5, pady=5)
        
        # 監控時段設定
        tk.Label(time_frame, text="監控時段:").grid(row=0, column=0, sticky="w", padx=5)
        
        # 開始時間
        self.time_start_hour = ttk.Combobox(time_frame, width=4, state='readonly')
        self.time_start_hour['values'] = [f"{i:02d}" for i in range(24)]
        self.time_start_hour.set('08')
        self.time_start_hour.grid(row=0, column=1, padx=2)
        
        tk.Label(time_frame, text=":").grid(row=0, column=2)
        
        self.time_start_min = ttk.Combobox(time_frame, width=4, state='readonly')
        self.time_start_min['values'] = [f"{i:02d}" for i in range(60)]
        self.time_start_min.set('46')
        self.time_start_min.grid(row=0, column=3, padx=2)
        
        tk.Label(time_frame, text="~").grid(row=0, column=4, padx=5)
        
        # 結束時間
        self.time_end_hour = ttk.Combobox(time_frame, width=4, state='readonly')
        self.time_end_hour['values'] = [f"{i:02d}" for i in range(24)]
        self.time_end_hour.set('08')
        self.time_end_hour.grid(row=0, column=5, padx=2)
        
        tk.Label(time_frame, text=":").grid(row=0, column=6)
        
        self.time_end_min = ttk.Combobox(time_frame, width=4, state='readonly')
        self.time_end_min['values'] = [f"{i:02d}" for i in range(60)]
        self.time_end_min.set('47')
        self.time_end_min.grid(row=0, column=7, padx=2)
        
        # 應用時間設定按鈕
        tk.Button(time_frame, text="應用設定", command=self.apply_time_settings, 
                 bg="lightblue").grid(row=0, column=8, padx=10)
        
        # 預設時段按鈕
        tk.Button(time_frame, text="正常盤(08:46-08:47)", command=self.set_normal_hours,
                 bg="lightgreen").grid(row=0, column=9, padx=5)
        
        tk.Button(time_frame, text="測試用(3分鐘後)", command=self.set_test_hours,
                 bg="orange").grid(row=0, column=10, padx=5)

        tk.Button(time_frame, text="手動設定未來時間", command=self.set_future_time,
                 bg="yellow").grid(row=0, column=11, padx=5)
    
    def create_range_section(self):
        """創建區間監控區域"""
        range_frame = tk.LabelFrame(self, text="📊 開盤區間監控", fg="purple")
        range_frame.grid(row=2, column=0, columnspan=2, sticky="ew", padx=5, pady=5)
        
        # 第一行：區間資料
        tk.Label(range_frame, text="區間高點:").grid(row=0, column=0, sticky="w", padx=5)
        self.data_vars['range_high'] = tk.StringVar(value="--")
        tk.Label(range_frame, textvariable=self.data_vars['range_high'], fg="red", font=("Arial", 10, "bold")).grid(row=0, column=1, sticky="w", padx=5)
        
        tk.Label(range_frame, text="區間低點:").grid(row=0, column=2, sticky="w", padx=5)
        self.data_vars['range_low'] = tk.StringVar(value="--")
        tk.Label(range_frame, textvariable=self.data_vars['range_low'], fg="blue", font=("Arial", 10, "bold")).grid(row=0, column=3, sticky="w", padx=5)
        
        tk.Label(range_frame, text="區間大小:").grid(row=0, column=4, sticky="w", padx=5)
        self.data_vars['range_size'] = tk.StringVar(value="--")
        tk.Label(range_frame, textvariable=self.data_vars['range_size'], fg="green", font=("Arial", 10, "bold")).grid(row=0, column=5, sticky="w", padx=5)
        
        # 第二行：突破點位
        tk.Label(range_frame, text="做多觸發:").grid(row=1, column=0, sticky="w", padx=5)
        self.data_vars['long_trigger'] = tk.StringVar(value="--")
        tk.Label(range_frame, textvariable=self.data_vars['long_trigger'], fg="red").grid(row=1, column=1, sticky="w", padx=5)
        
        tk.Label(range_frame, text="做空觸發:").grid(row=1, column=2, sticky="w", padx=5)
        self.data_vars['short_trigger'] = tk.StringVar(value="--")
        tk.Label(range_frame, textvariable=self.data_vars['short_trigger'], fg="blue").grid(row=1, column=3, sticky="w", padx=5)
        
        tk.Label(range_frame, text="當前價格:").grid(row=1, column=4, sticky="w", padx=5)
        self.data_vars['current_price'] = tk.StringVar(value="--")
        tk.Label(range_frame, textvariable=self.data_vars['current_price'], fg="black", font=("Arial", 10, "bold")).grid(row=1, column=5, sticky="w", padx=5)
    
    def create_position_section(self):
        """創建部位狀態區域"""
        pos_frame = tk.LabelFrame(self, text="📈 部位狀態", fg="brown")
        pos_frame.grid(row=3, column=0, columnspan=2, sticky="ew", padx=5, pady=5)
        
        # 第一行：基本資訊
        tk.Label(pos_frame, text="部位方向:").grid(row=0, column=0, sticky="w", padx=5)
        self.data_vars['position_type'] = tk.StringVar(value="無部位")
        tk.Label(pos_frame, textvariable=self.data_vars['position_type'], font=("Arial", 10, "bold")).grid(row=0, column=1, sticky="w", padx=5)
        
        tk.Label(pos_frame, text="活躍口數:").grid(row=0, column=2, sticky="w", padx=5)
        self.data_vars['active_lots'] = tk.StringVar(value="0")
        tk.Label(pos_frame, textvariable=self.data_vars['active_lots'], font=("Arial", 10, "bold")).grid(row=0, column=3, sticky="w", padx=5)
        
        tk.Label(pos_frame, text="總損益:").grid(row=0, column=4, sticky="w", padx=5)
        self.data_vars['total_pnl'] = tk.StringVar(value="0元")
        self.label_pnl = tk.Label(pos_frame, textvariable=self.data_vars['total_pnl'], font=("Arial", 10, "bold"))
        self.label_pnl.grid(row=0, column=5, sticky="w", padx=5)
        
        # 第二行：各口狀態
        tk.Label(pos_frame, text="各口狀態:").grid(row=1, column=0, sticky="w", padx=5)
        self.data_vars['lots_status'] = tk.StringVar(value="等待開倉...")
        tk.Label(pos_frame, textvariable=self.data_vars['lots_status'], wraplength=400).grid(row=1, column=1, columnspan=5, sticky="w", padx=5)
    
    def create_control_section(self):
        """創建控制按鈕區域"""
        control_frame = tk.LabelFrame(self, text="🎮 策略控制", fg="navy")
        control_frame.grid(row=4, column=0, columnspan=2, sticky="ew", padx=5, pady=5)
        
        # 主要控制按鈕
        self.btn_start = tk.Button(control_frame, text="🚀 啟動策略", command=self.start_strategy,
                                  bg="green", fg="white", font=("Arial", 10, "bold"))
        self.btn_start.grid(row=0, column=0, padx=5, pady=5)
        
        self.btn_stop = tk.Button(control_frame, text="🛑 停止策略", command=self.stop_strategy,
                                 bg="red", fg="white", font=("Arial", 10, "bold"), state="disabled")
        self.btn_stop.grid(row=0, column=1, padx=5, pady=5)
        
        self.btn_emergency = tk.Button(control_frame, text="🚨 緊急平倉", command=self.emergency_close,
                                      bg="darkred", fg="white", font=("Arial", 10, "bold"))
        self.btn_emergency.grid(row=0, column=2, padx=5, pady=5)
    
    def create_log_section(self):
        """創建日誌顯示區域"""
        log_frame = tk.LabelFrame(self, text="📝 策略日誌 (同步顯示於VS CODE)", fg="gray")
        log_frame.grid(row=5, column=0, columnspan=2, sticky="ew", padx=5, pady=5)

        # 日誌文字框 - 增加高度到15行
        self.log_text = tk.Text(log_frame, height=15, width=80, wrap=tk.WORD,
                               font=("Consolas", 9))  # 使用等寬字體便於閱讀
        self.log_text.grid(row=0, column=0, sticky="ew", padx=5, pady=5)

        # 滾動條
        scrollbar = tk.Scrollbar(log_frame, orient="vertical", command=self.log_text.yview)
        scrollbar.grid(row=0, column=1, sticky="ns")
        self.log_text.configure(yscrollcommand=scrollbar.set)

        # 清除日誌按鈕
        clear_btn = tk.Button(log_frame, text="🗑️ 清除日誌", command=self.clear_log,
                             bg="lightgray", font=("Arial", 8))
        clear_btn.grid(row=1, column=0, sticky="w", padx=5, pady=2)
    
    def load_default_config(self):
        """載入預設配置"""
        self.config = StrategyConfig(trade_size_in_lots=3)
        self.log_message("✅ 載入預設策略配置 (3口)")
    
    def on_lots_changed(self, event=None):
        """口數改變事件"""
        lots_text = self.combo_lots.get()
        lots_num = int(lots_text[0])  # 取第一個字符轉為數字
        
        # 重新創建配置
        self.config = StrategyConfig(trade_size_in_lots=lots_num)
        self.log_message(f"🔄 更新策略配置: {lots_num}口")
        
        # 顯示口數規則
        rules_text = []
        for i, rule in enumerate(self.config.lot_rules, 1):
            rules_text.append(f"第{i}口: {rule.trailing_activation}點啟動, {rule.trailing_pullback}回檔")
        
        self.log_message(f"📋 口數規則: {'; '.join(rules_text)}")
    
    def apply_time_settings(self):
        """應用時間設定"""
        start_hour = int(self.time_start_hour.get())
        start_min = int(self.time_start_min.get())
        end_hour = int(self.time_end_hour.get())
        end_min = int(self.time_end_min.get())
        
        # 更新時間管理器的時間設定
        self.time_manager.RANGE_START_TIME = time(start_hour, start_min, 0)
        self.time_manager.RANGE_END_TIME = time(end_hour, end_min, 59)
        
        self.log_message(f"⏰ 時間設定已更新: {start_hour:02d}:{start_min:02d} ~ {end_hour:02d}:{end_min:02d}")
    
    def set_normal_hours(self):
        """設定正常盤時間"""
        self.time_start_hour.set('08')
        self.time_start_min.set('46')
        self.time_end_hour.set('08')
        self.time_end_min.set('47')
        self.apply_time_settings()
    
    def set_test_hours(self):
        """設定測試時間 (未來3分鐘開始的2分鐘區間)"""
        now = datetime.now()
        # 設定為3分鐘後開始，持續2分鐘
        start_time = now.replace(minute=now.minute + 3, second=0)
        end_time = start_time.replace(minute=start_time.minute + 1)  # 2分鐘區間

        # 處理分鐘數超過59的情況
        if start_time.minute >= 60:
            start_time = start_time.replace(hour=start_time.hour + 1, minute=start_time.minute - 60)
        if end_time.minute >= 60:
            end_time = end_time.replace(hour=end_time.hour + 1, minute=end_time.minute - 60)

        self.time_start_hour.set(f"{start_time.hour:02d}")
        self.time_start_min.set(f"{start_time.minute:02d}")
        self.time_end_hour.set(f"{end_time.hour:02d}")
        self.time_end_min.set(f"{end_time.minute:02d}")
        self.apply_time_settings()

        self.log_message(f"🧪 測試時間已設定: {start_time.strftime('%H:%M')} ~ {end_time.strftime('%H:%M')} (3分鐘後開始)")

    def set_future_time(self):
        """手動設定未來時間"""
        import tkinter.simpledialog as simpledialog

        now = datetime.now()
        current_time_str = now.strftime('%H:%M')

        # 詢問用戶要設定的開始時間
        start_time_str = simpledialog.askstring(
            "設定測試時間",
            f"請輸入開始時間 (格式: HH:MM)\n當前時間: {current_time_str}\n建議設定為未來3-5分鐘:",
            initialvalue=f"{now.hour:02d}:{now.minute+3:02d}"
        )

        if not start_time_str:
            return

        try:
            # 解析時間
            start_hour, start_min = map(int, start_time_str.split(':'))

            # 設定結束時間為開始時間+2分鐘
            end_min = start_min + 2
            end_hour = start_hour

            # 處理分鐘數超過59的情況
            if end_min >= 60:
                end_hour += 1
                end_min -= 60

            # 更新UI
            self.time_start_hour.set(f"{start_hour:02d}")
            self.time_start_min.set(f"{start_min:02d}")
            self.time_end_hour.set(f"{end_hour:02d}")
            self.time_end_min.set(f"{end_min:02d}")
            self.apply_time_settings()

            self.log_message(f"🕐 手動設定時間: {start_hour:02d}:{start_min:02d} ~ {end_hour:02d}:{end_min:02d}")

        except ValueError:
            self.log_message("❌ 時間格式錯誤，請使用 HH:MM 格式")

    def start_strategy(self):
        """啟動策略"""
        if self.strategy_active:
            return
        
        try:
            # 取得當前時間設定
            start_hour = int(self.time_start_hour.get())
            start_min = int(self.time_start_min.get())
            end_hour = int(self.time_end_hour.get())
            end_min = int(self.time_end_min.get())

            start_time = time(start_hour, start_min, 0)
            end_time = time(end_hour, end_min, 59)

            # 初始化策略組件
            self.range_detector = OpeningRangeDetector(start_time, end_time)
            if self.config:
                self.position_manager = MultiLotPositionManager(self.config)
            else:
                self.log_message("⚠️ 策略配置未載入，使用預設設定")
                return
            
            # 啟動監控
            self.range_detector.start_monitoring()
            self.strategy_active = True
            self.monitoring_active = True
            
            # 更新UI
            self.status_vars['strategy'].set("🟢 運行中")
            self.btn_start.config(state="disabled")
            self.btn_stop.config(state="normal")
            
            self.log_message("🚀 策略已啟動，開始監控開盤區間")
            
        except Exception as e:
            self.log_message(f"❌ 策略啟動失敗: {e}")
    
    def stop_strategy(self):
        """停止策略"""
        self.strategy_active = False
        self.monitoring_active = False
        
        if self.range_detector:
            self.range_detector.stop_monitoring()
        
        # 更新UI
        self.status_vars['strategy'].set("🔴 已停止")
        self.btn_start.config(state="normal")
        self.btn_stop.config(state="disabled")
        
        self.log_message("🛑 策略已停止")
    
    def emergency_close(self):
        """緊急平倉"""
        if self.position_manager and self.position_manager.has_position():
            closed_count = self.position_manager.close_all_positions(self.current_price)
            self.log_message(f"🚨 緊急平倉完成: {closed_count}口")
        else:
            self.log_message("ℹ️ 目前無部位需要平倉")
    
    def simulate_breakout(self):
        """模擬突破測試"""
        try:
            if not self.range_detector or not self.range_detector.is_range_ready():
                self.log_message("⚠️ 開盤區間尚未準備就緒，無法模擬突破")
                return

            # 模擬突破高點
            range_data = self.range_detector.get_range_data()
            if range_data and 'range_high' in range_data:
                breakout_price = range_data['range_high'] + 5
                self.process_price_update(breakout_price)
                self.log_message(f"🧪 模擬突破測試: 價格{breakout_price} (突破高點+5)")
            else:
                self.log_message("❌ 無法取得區間資料，模擬突破失敗")
        except Exception as e:
            self.log_message(f"❌ 模擬突破錯誤: {str(e)}")
    
    def show_statistics(self):
        """顯示統計資料"""
        summary = self.db_manager.get_trading_summary()
        
        if summary.get('total_trades', 0) > 0:
            stats_text = f"""
📊 交易統計:
總交易次數: {summary['total_trades']}
獲利次數: {summary['winning_trades']}
虧損次數: {summary['losing_trades']}
勝率: {summary['win_rate']:.1f}%
總損益: {summary['total_pnl']:.0f}元
平均損益: {summary['avg_pnl']:.0f}元
最大獲利: {summary['max_profit']:.0f}元
最大虧損: {summary['max_loss']:.0f}元
"""
        else:
            stats_text = "📊 尚無交易記錄"
        
        messagebox.showinfo("交易統計", stats_text)
    
    def process_price_update(self, price, timestamp=None):
        """處理價格更新 (供外部調用)"""
        if not self.strategy_active:
            return
        
        self.current_price = price
        self.last_update_time = timestamp or datetime.now()
        
        # 更新顯示
        self.data_vars['current_price'].set(f"{price}")
        
        # 處理開盤區間監控
        if self.range_detector and self.monitoring_active:
            updated = self.range_detector.process_tick(price, 0, self.last_update_time)

            # 定時檢查區間完成狀態 (即使沒有更新也要檢查)
            if not self.range_detector.is_range_ready():
                if self.range_detector.force_check_completion():
                    self.log_message("🎯 定時檢查觸發區間完成")
                    updated = True

            if updated and self.range_detector.is_range_ready():
                self.update_range_display()

                # 創建突破偵測器
                if not self.breakout_detector:
                    range_data = self.range_detector.get_range_data()
                    self.breakout_detector = BreakoutSignalDetector(
                        range_data['range_high'], range_data['range_low']
                    )
                    self.log_message("🎯 突破偵測器已啟動")
        
        # 處理突破信號
        if self.breakout_detector:
            signal = self.breakout_detector.check_breakout(price, self.last_update_time)
            if signal:
                self.handle_breakout_signal(signal, price)
        
        # 更新部位
        if self.position_manager and self.position_manager.has_position():
            exited_lots = self.position_manager.update_position(price)
            if exited_lots:
                self.log_message(f"🔚 第{exited_lots}口出場")
            self.update_position_display()
    
    def update_range_display(self):
        """更新區間顯示"""
        if not self.range_detector or not self.range_detector.is_range_ready():
            return
        
        range_data = self.range_detector.get_range_data()
        
        self.data_vars['range_high'].set(f"{range_data['range_high']}")
        self.data_vars['range_low'].set(f"{range_data['range_low']}")
        self.data_vars['range_size'].set(f"{range_data['range_size']:.0f}點")
        
        if self.breakout_detector:
            self.data_vars['long_trigger'].set(f"{self.breakout_detector.long_trigger}")
            self.data_vars['short_trigger'].set(f"{self.breakout_detector.short_trigger}")
    
    def handle_breakout_signal(self, signal, price):
        """處理突破信號"""
        if self.position_manager.has_position():
            return  # 已有部位，不重複開倉
        
        range_data = self.range_detector.get_range_data()
        success = self.position_manager.open_position(
            signal, price, range_data['range_high'], range_data['range_low']
        )
        
        if success:
            self.log_message(f"🚀 突破開倉: {signal} {self.config.trade_size_in_lots}口 @{price}")
            
            # 記錄到資料庫
            self.db_manager.insert_strategy_signal(
                datetime.now().date().isoformat(),
                range_data['range_high'], range_data['range_low'],
                signal, self.last_update_time.strftime('%H:%M:%S'), price
            )
    
    def update_position_display(self):
        """更新部位顯示"""
        if not self.position_manager:
            return
        
        summary = self.position_manager.get_position_summary()
        
        # 更新基本資訊
        if summary['position_type']:
            self.data_vars['position_type'].set(summary['position_type'])
        else:
            self.data_vars['position_type'].set("無部位")
        
        self.data_vars['active_lots'].set(f"{summary['active_lots']}")
        
        # 更新損益顯示
        total_pnl = summary['total_pnl']
        self.data_vars['total_pnl'].set(f"{total_pnl:+.0f}元")
        
        # 根據損益設定顏色
        if total_pnl > 0:
            self.label_pnl.config(fg="red")  # 獲利紅色
        elif total_pnl < 0:
            self.label_pnl.config(fg="green")  # 虧損綠色
        else:
            self.label_pnl.config(fg="black")
        
        # 更新各口狀態
        lots_status = []
        for lot_detail in summary['lots_detail']:
            if lot_detail['status'] == 'ACTIVE':
                trailing = "✅" if lot_detail['trailing_activated'] else "❌"
                lots_status.append(f"第{lot_detail['lot_id']}口:移動停利{trailing}")
            else:
                lots_status.append(f"第{lot_detail['lot_id']}口:已出場({lot_detail['exit_reason']})")
        
        if lots_status:
            self.data_vars['lots_status'].set(" | ".join(lots_status))
        else:
            self.data_vars['lots_status'].set("等待開倉...")
    
    def start_status_update(self):
        """啟動狀態更新"""
        def update_status():
            session_info = self.time_manager.get_trading_session_info()
            session_text = f"{session_info['session']} ({session_info['current_time'].strftime('%H:%M:%S')})"
            self.status_vars['session'].set(session_text)
            
            # 每秒更新一次
            self.after(1000, update_status)
        
        update_status()
    
    def log_message(self, message):
        """記錄日誌訊息 - 同時輸出到UI和VS CODE"""
        timestamp = datetime.now().strftime("%H:%M:%S.%f")[:-3]  # 包含毫秒
        log_entry = f"[{timestamp}] {message}"

        # 輸出到VS CODE終端 (print會顯示在VS CODE的輸出面板)
        print(f"📊 策略日誌: {log_entry}")

        # 同時使用logging模組輸出 (更詳細的開發日誌)
        import logging
        logger = logging.getLogger('StrategyPanel')
        if not logger.handlers:
            # 設定logging格式，輸出到VS CODE
            logging.basicConfig(
                level=logging.DEBUG,
                format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                handlers=[
                    logging.StreamHandler(),  # 輸出到控制台
                ]
            )
        logger.info(message)

        # 添加到UI
        self.log_text.insert(tk.END, log_entry + "\n")
        self.log_text.see(tk.END)  # 自動滾動到最新

        # 限制日誌行數到300行 (增加容量)
        lines = self.log_text.get("1.0", tk.END).split('\n')
        if len(lines) > 300:
            # 刪除最舊的100行
            for _ in range(100):
                self.log_text.delete("1.0", "2.0")

    def clear_log(self):
        """清除日誌"""
        self.log_text.delete(1.0, tk.END)
        self.log_message("🗑️ 日誌已清除")

if __name__ == "__main__":
    # 測試策略面板
    root = tk.Tk()
    root.title("策略控制面板測試")
    
    panel = StrategyControlPanel(root)
    panel.pack(fill="both", expand=True)
    
    # 模擬價格更新
    def simulate_prices():
        import random
        base_price = 22000
        for i in range(100):
            price = base_price + random.randint(-20, 20)
            panel.process_price_update(price)
            root.after(1000, lambda: None)  # 等待1秒
    
    root.after(2000, simulate_prices)  # 2秒後開始模擬
    root.mainloop()
