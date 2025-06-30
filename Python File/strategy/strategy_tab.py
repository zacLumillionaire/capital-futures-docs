#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
策略分頁 - 獨立的策略控制分頁
設計為與下單、查詢部位同等級的分頁
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

class StrategyTab(tk.Frame):
    """策略控制分頁"""

    def __init__(self, master=None, skcom_objects=None):
        super().__init__(master)
        self.master = master

        # SKCOM物件 (用於獲取即時報價)
        self.m_pSKQuote = skcom_objects.get('SKQuote') if skcom_objects else None

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
        self.price_simulation_running = False

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
        title_frame = tk.LabelFrame(self, text="🎯 開盤區間突破策略", fg="blue", font=("Arial", 14, "bold"))
        title_frame.pack(fill="x", padx=10, pady=5)

        title_label = tk.Label(title_frame, text="當沖策略交易系統", font=("Arial", 12))
        title_label.pack(pady=5)

        # 策略設定區域
        self.create_config_section()

        # 時間設定區域
        self.create_time_section()

        # 區間監控區域
        self.create_range_section()

        # 部位狀態區域
        self.create_position_section()

        # 控制按鈕區域
        self.create_control_section()

        # 測試功能區域
        self.create_test_section()

        # 日誌顯示區域
        self.create_log_section()

    def create_config_section(self):
        """創建策略設定區域"""
        config_frame = tk.LabelFrame(self, text="📋 策略設定", fg="green", font=("Arial", 12, "bold"))
        config_frame.pack(fill="x", padx=10, pady=5)

        # 第一行
        row1_frame = tk.Frame(config_frame)
        row1_frame.pack(fill="x", padx=5, pady=5)

        # 交易口數設定
        tk.Label(row1_frame, text="交易口數:", font=("Arial", 10)).pack(side="left", padx=5)
        self.combo_lots = ttk.Combobox(row1_frame, width=8, state='readonly')
        self.combo_lots['values'] = ['1口', '2口', '3口', '4口']
        self.combo_lots.set('3口')  # 預設3口
        self.combo_lots.pack(side="left", padx=5)
        self.combo_lots.bind('<<ComboboxSelected>>', self.on_lots_changed)

        # 策略狀態
        tk.Label(row1_frame, text="策略狀態:", font=("Arial", 10)).pack(side="left", padx=(20, 5))
        self.status_vars['strategy'] = tk.StringVar(value="🔴 未啟動")
        tk.Label(row1_frame, textvariable=self.status_vars['strategy'], fg="red", font=("Arial", 10, "bold")).pack(side="left", padx=5)

        # 當前時段
        tk.Label(row1_frame, text="當前時段:", font=("Arial", 10)).pack(side="left", padx=(20, 5))
        self.status_vars['session'] = tk.StringVar(value="等待中...")
        tk.Label(row1_frame, textvariable=self.status_vars['session'], font=("Arial", 10)).pack(side="left", padx=5)

        # 第二行 - 口數規則顯示
        row2_frame = tk.Frame(config_frame)
        row2_frame.pack(fill="x", padx=5, pady=5)

        tk.Label(row2_frame, text="口數規則:", font=("Arial", 10)).pack(side="left", padx=5)
        self.status_vars['lot_rules'] = tk.StringVar(value="載入中...")
        tk.Label(row2_frame, textvariable=self.status_vars['lot_rules'], font=("Arial", 9), wraplength=600).pack(side="left", padx=5)

    def create_time_section(self):
        """創建時間設定區域"""
        time_frame = tk.LabelFrame(self, text="⏰ 時間設定 (可自定義測試時段)", fg="purple", font=("Arial", 12, "bold"))
        time_frame.pack(fill="x", padx=10, pady=5)

        # 時間設定行
        time_row = tk.Frame(time_frame)
        time_row.pack(fill="x", padx=5, pady=5)

        tk.Label(time_row, text="監控時段:", font=("Arial", 10)).pack(side="left", padx=5)

        # 開始時間
        self.time_start_hour = ttk.Combobox(time_row, width=4, state='readonly')
        self.time_start_hour['values'] = [f"{i:02d}" for i in range(24)]
        self.time_start_hour.set('08')
        self.time_start_hour.pack(side="left", padx=2)

        tk.Label(time_row, text=":").pack(side="left")

        self.time_start_min = ttk.Combobox(time_row, width=4, state='readonly')
        self.time_start_min['values'] = [f"{i:02d}" for i in range(60)]
        self.time_start_min.set('46')
        self.time_start_min.pack(side="left", padx=2)

        tk.Label(time_row, text="~", font=("Arial", 12)).pack(side="left", padx=5)

        # 結束時間
        self.time_end_hour = ttk.Combobox(time_row, width=4, state='readonly')
        self.time_end_hour['values'] = [f"{i:02d}" for i in range(24)]
        self.time_end_hour.set('08')
        self.time_end_hour.pack(side="left", padx=2)

        tk.Label(time_row, text=":").pack(side="left")

        self.time_end_min = ttk.Combobox(time_row, width=4, state='readonly')
        self.time_end_min['values'] = [f"{i:02d}" for i in range(60)]
        self.time_end_min.set('47')
        self.time_end_min.pack(side="left", padx=2)

        # 按鈕
        tk.Button(time_row, text="應用設定", command=self.apply_time_settings,
                 bg="lightblue", font=("Arial", 9)).pack(side="left", padx=10)

        tk.Button(time_row, text="正常盤(08:46-08:47)", command=self.set_normal_hours,
                 bg="lightgreen", font=("Arial", 9)).pack(side="left", padx=5)

        tk.Button(time_row, text="測試用(當前時間)", command=self.set_test_hours,
                 bg="orange", font=("Arial", 9)).pack(side="left", padx=5)

    def create_range_section(self):
        """創建區間監控區域"""
        range_frame = tk.LabelFrame(self, text="📊 開盤區間監控", fg="brown", font=("Arial", 12, "bold"))
        range_frame.pack(fill="x", padx=10, pady=5)

        # 第一行：區間資料
        row1 = tk.Frame(range_frame)
        row1.pack(fill="x", padx=5, pady=5)

        tk.Label(row1, text="區間高點:", font=("Arial", 10)).pack(side="left", padx=5)
        self.data_vars['range_high'] = tk.StringVar(value="--")
        tk.Label(row1, textvariable=self.data_vars['range_high'], fg="red", font=("Arial", 12, "bold")).pack(side="left", padx=5)

        tk.Label(row1, text="區間低點:", font=("Arial", 10)).pack(side="left", padx=(20, 5))
        self.data_vars['range_low'] = tk.StringVar(value="--")
        tk.Label(row1, textvariable=self.data_vars['range_low'], fg="blue", font=("Arial", 12, "bold")).pack(side="left", padx=5)

        tk.Label(row1, text="區間大小:", font=("Arial", 10)).pack(side="left", padx=(20, 5))
        self.data_vars['range_size'] = tk.StringVar(value="--")
        tk.Label(row1, textvariable=self.data_vars['range_size'], fg="green", font=("Arial", 12, "bold")).pack(side="left", padx=5)

        # 第二行：突破點位
        row2 = tk.Frame(range_frame)
        row2.pack(fill="x", padx=5, pady=5)

        tk.Label(row2, text="做多觸發:", font=("Arial", 10)).pack(side="left", padx=5)
        self.data_vars['long_trigger'] = tk.StringVar(value="--")
        tk.Label(row2, textvariable=self.data_vars['long_trigger'], fg="red", font=("Arial", 11, "bold")).pack(side="left", padx=5)

        tk.Label(row2, text="做空觸發:", font=("Arial", 10)).pack(side="left", padx=(20, 5))
        self.data_vars['short_trigger'] = tk.StringVar(value="--")
        tk.Label(row2, textvariable=self.data_vars['short_trigger'], fg="blue", font=("Arial", 11, "bold")).pack(side="left", padx=5)

        tk.Label(row2, text="當前價格:", font=("Arial", 10)).pack(side="left", padx=(20, 5))
        self.data_vars['current_price'] = tk.StringVar(value="--")
        tk.Label(row2, textvariable=self.data_vars['current_price'], fg="black", font=("Arial", 12, "bold")).pack(side="left", padx=5)

    def create_position_section(self):
        """創建部位狀態區域"""
        pos_frame = tk.LabelFrame(self, text="📈 部位狀態", fg="navy", font=("Arial", 12, "bold"))
        pos_frame.pack(fill="x", padx=10, pady=5)

        # 第一行：基本資訊
        row1 = tk.Frame(pos_frame)
        row1.pack(fill="x", padx=5, pady=5)

        tk.Label(row1, text="部位方向:", font=("Arial", 10)).pack(side="left", padx=5)
        self.data_vars['position_type'] = tk.StringVar(value="無部位")
        tk.Label(row1, textvariable=self.data_vars['position_type'], font=("Arial", 11, "bold")).pack(side="left", padx=5)

        tk.Label(row1, text="活躍口數:", font=("Arial", 10)).pack(side="left", padx=(20, 5))
        self.data_vars['active_lots'] = tk.StringVar(value="0")
        tk.Label(row1, textvariable=self.data_vars['active_lots'], font=("Arial", 11, "bold")).pack(side="left", padx=5)

        tk.Label(row1, text="總損益:", font=("Arial", 10)).pack(side="left", padx=(20, 5))
        self.data_vars['total_pnl'] = tk.StringVar(value="0元")
        self.label_pnl = tk.Label(row1, textvariable=self.data_vars['total_pnl'], font=("Arial", 12, "bold"))
        self.label_pnl.pack(side="left", padx=5)

        # 第二行：各口狀態
        row2 = tk.Frame(pos_frame)
        row2.pack(fill="x", padx=5, pady=5)

        tk.Label(row2, text="各口狀態:", font=("Arial", 10)).pack(side="left", padx=5)
        self.data_vars['lots_status'] = tk.StringVar(value="等待開倉...")
        tk.Label(row2, textvariable=self.data_vars['lots_status'], wraplength=600, font=("Arial", 9)).pack(side="left", padx=5)

    def create_control_section(self):
        """創建控制按鈕區域"""
        control_frame = tk.LabelFrame(self, text="🎮 策略控制", fg="darkgreen", font=("Arial", 12, "bold"))
        control_frame.pack(fill="x", padx=10, pady=5)

        # 按鈕行
        button_row = tk.Frame(control_frame)
        button_row.pack(fill="x", padx=5, pady=10)

        # 主要控制按鈕
        self.btn_start = tk.Button(button_row, text="🚀 啟動策略", command=self.start_strategy,
                                  bg="green", fg="white", font=("Arial", 11, "bold"), width=12)
        self.btn_start.pack(side="left", padx=5)

        self.btn_stop = tk.Button(button_row, text="🛑 停止策略", command=self.stop_strategy,
                                 bg="red", fg="white", font=("Arial", 11, "bold"), width=12, state="disabled")
        self.btn_stop.pack(side="left", padx=5)

        self.btn_emergency = tk.Button(button_row, text="🚨 緊急平倉", command=self.emergency_close,
                                      bg="darkred", fg="white", font=("Arial", 11, "bold"), width=12)
        self.btn_emergency.pack(side="left", padx=5)

        tk.Button(button_row, text="📊 查看統計", command=self.show_statistics,
                 bg="lightblue", font=("Arial", 10), width=12).pack(side="left", padx=5)

    def create_test_section(self):
        """創建測試功能區域"""
        test_frame = tk.LabelFrame(self, text="🧪 測試功能", fg="orange", font=("Arial", 12, "bold"))
        test_frame.pack(fill="x", padx=10, pady=5)

        # 測試按鈕行
        test_row = tk.Frame(test_frame)
        test_row.pack(fill="x", padx=5, pady=5)

        tk.Button(test_row, text="🎯 開始模擬報價", command=self.start_price_simulation,
                 bg="lightgreen", font=("Arial", 10), width=15).pack(side="left", padx=5)

        tk.Button(test_row, text="⏹️ 停止模擬報價", command=self.stop_price_simulation,
                 bg="lightcoral", font=("Arial", 10), width=15).pack(side="left", padx=5)

        tk.Button(test_row, text="📊 模擬開盤區間", command=self.simulate_opening_range,
                 bg="lightyellow", font=("Arial", 10), width=15).pack(side="left", padx=5)

        tk.Button(test_row, text="🚀 模擬突破", command=self.simulate_breakout,
                 bg="lightpink", font=("Arial", 10), width=15).pack(side="left", padx=5)

    def create_log_section(self):
        """創建日誌顯示區域"""
        log_frame = tk.LabelFrame(self, text="📝 策略日誌", fg="gray", font=("Arial", 12, "bold"))
        log_frame.pack(fill="both", expand=True, padx=10, pady=5)

        # 日誌文字框
        log_container = tk.Frame(log_frame)
        log_container.pack(fill="both", expand=True, padx=5, pady=5)

        self.log_text = tk.Text(log_container, height=12, width=100, wrap=tk.WORD, font=("Consolas", 9))
        scrollbar = tk.Scrollbar(log_container, orient="vertical", command=self.log_text.yview)
        self.log_text.configure(yscrollcommand=scrollbar.set)

        self.log_text.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")

        # 清除按鈕
        tk.Button(log_frame, text="清除日誌", command=self.clear_log,
                 bg="lightgray", font=("Arial", 9)).pack(pady=5)

    def load_default_config(self):
        """載入預設配置"""
        self.config = StrategyConfig(trade_size_in_lots=3)
        self.log_message("✅ 載入預設策略配置 (3口)")
        self.update_lot_rules_display()

    def update_lot_rules_display(self):
        """更新口數規則顯示"""
        if not self.config:
            return

        rules_text = []
        for i, rule in enumerate(self.config.lot_rules, 1):
            rules_text.append(f"第{i}口:{rule.trailing_activation}點啟動,{rule.trailing_pullback}回檔")

        self.status_vars['lot_rules'].set(" | ".join(rules_text))

    def on_lots_changed(self, event=None):
        """口數改變事件"""
        lots_text = self.combo_lots.get()
        lots_num = int(lots_text[0])  # 取第一個字符轉為數字

        # 重新創建配置
        self.config = StrategyConfig(trade_size_in_lots=lots_num)
        self.log_message(f"🔄 更新策略配置: {lots_num}口")
        self.update_lot_rules_display()

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
        """設定測試時間 (當前時間開始的2分鐘)"""
        now = datetime.now()
        start_time = now
        end_time = now.replace(minute=now.minute + 1)  # 1分鐘後結束

        self.time_start_hour.set(f"{start_time.hour:02d}")
        self.time_start_min.set(f"{start_time.minute:02d}")
        self.time_end_hour.set(f"{end_time.hour:02d}")
        self.time_end_min.set(f"{end_time.minute:02d}")
        self.apply_time_settings()

        self.log_message(f"🧪 測試時間已設定: {start_time.strftime('%H:%M')} ~ {end_time.strftime('%H:%M')}")

    def start_strategy(self):
        """啟動策略"""
        if self.strategy_active:
            return

        if not self.config:
            self.log_message("❌ 策略配置未載入")
            return

        try:
            # 初始化策略組件
            self.range_detector = OpeningRangeDetector()
            self.position_manager = MultiLotPositionManager(self.config)

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

    def show_statistics(self):
        """顯示統計資料"""
        summary = self.db_manager.get_trading_summary()

        if summary.get('total_trades', 0) > 0:
            stats_text = f"""📊 交易統計:
總交易次數: {summary['total_trades']}
獲利次數: {summary['winning_trades']}
虧損次數: {summary['losing_trades']}
勝率: {summary['win_rate']:.1f}%
總損益: {summary['total_pnl']:.0f}元
平均損益: {summary['avg_pnl']:.0f}元
最大獲利: {summary['max_profit']:.0f}元
最大虧損: {summary['max_loss']:.0f}元"""
        else:
            stats_text = "📊 尚無交易記錄"

        messagebox.showinfo("交易統計", stats_text)

    def start_price_simulation(self):
        """開始價格模擬"""
        if self.price_simulation_running:
            return

        self.price_simulation_running = True
        self.log_message("🎯 開始模擬即時報價")

        def price_thread():
            import random
            base_price = 22000

            while self.price_simulation_running:
                try:
                    # 生成隨機價格變動
                    change = random.randint(-5, 5)
                    new_price = base_price + change

                    # 更新價格
                    timestamp = datetime.now()
                    self.process_price_update(new_price, timestamp)

                    import time
                    time.sleep(0.5)  # 每0.5秒更新一次

                except Exception as e:
                    self.log_message(f"價格模擬錯誤: {e}")
                    break

        # 啟動價格模擬線程
        threading.Thread(target=price_thread, daemon=True).start()

    def stop_price_simulation(self):
        """停止價格模擬"""
        self.price_simulation_running = False
        self.log_message("⏹️ 停止模擬報價")

    def simulate_opening_range(self):
        """模擬開盤區間計算"""
        if not self.range_detector:
            self.log_message("⚠️ 請先啟動策略")
            return

        self.log_message("📊 開始模擬開盤區間計算...")

        def simulate_range():
            import time
            base = 22000

            # 模擬第一分鐘 (08:46)
            prices_846 = [base, base+3, base+8, base+5, base+2, base-1, base+4, base+6, base+3, base+1]
            for i, price in enumerate(prices_846):
                timestamp = datetime.now().replace(minute=46, second=i*6)
                self.range_detector.process_tick(price, 100, timestamp)
                time.sleep(0.1)

            # 模擬第二分鐘 (08:47)
            prices_847 = [base+2, base+7, base+12, base+15, base+18, base+20, base+16, base+12, base+8, base+5]
            for i, price in enumerate(prices_847):
                timestamp = datetime.now().replace(minute=47, second=i*6)
                self.range_detector.process_tick(price, 100, timestamp)
                time.sleep(0.1)

            # 08:48:00 觸發區間計算
            timestamp = datetime.now().replace(minute=48, second=0)
            self.range_detector.process_tick(base+6, 100, timestamp)

            # 更新顯示
            self.after(0, self.update_range_display)
            self.after(0, lambda: self.log_message("✅ 開盤區間模擬完成"))

        # 在背景執行模擬
        threading.Thread(target=simulate_range, daemon=True).start()

    def simulate_breakout(self):
        """模擬突破"""
        if not self.range_detector or not self.range_detector.is_range_ready():
            self.log_message("⚠️ 請先模擬開盤區間")
            return

        # 獲取區間數據
        range_data = self.range_detector.get_range_data()
        breakout_price = range_data['range_high'] + 5  # 突破高點+5

        # 模擬突破
        self.process_price_update(breakout_price)
        self.log_message(f"🚀 模擬突破: 價格{breakout_price} (突破高點+5)")

    def process_price_update(self, price, timestamp=None):
        """處理價格更新"""
        if not self.strategy_active:
            return

        self.current_price = price
        self.last_update_time = timestamp or datetime.now()

        # 更新顯示
        self.data_vars['current_price'].set(f"{price}")

        # 處理開盤區間監控
        if self.range_detector and self.monitoring_active:
            updated = self.range_detector.process_tick(price, 0, self.last_update_time)

            if updated and self.range_detector.is_range_ready():
                self.update_range_display()

                # 創建突破偵測器
                if not self.breakout_detector:
                    range_data = self.range_detector.get_range_data()
                    if range_data:
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
        if not range_data:
            return

        self.data_vars['range_high'].set(f"{range_data['range_high']}")
        self.data_vars['range_low'].set(f"{range_data['range_low']}")
        self.data_vars['range_size'].set(f"{range_data['range_size']:.0f}點")

        if self.breakout_detector:
            self.data_vars['long_trigger'].set(f"{self.breakout_detector.long_trigger}")
            self.data_vars['short_trigger'].set(f"{self.breakout_detector.short_trigger}")

    def handle_breakout_signal(self, signal, price):
        """處理突破信號"""
        if not self.position_manager or not self.range_detector or not self.config:
            return

        if self.position_manager.has_position():
            return  # 已有部位，不重複開倉

        range_data = self.range_detector.get_range_data()
        if not range_data:
            return

        success = self.position_manager.open_position(
            signal, price, range_data['range_high'], range_data['range_low']
        )

        if success:
            self.log_message(f"🚀 突破開倉: {signal} {self.config.trade_size_in_lots}口 @{price}")

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
                lots_status.append(f"第{lot_detail['lot_id']}口:已出場")

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
        """記錄日誌訊息"""
        timestamp = datetime.now().strftime("%H:%M:%S")
        log_entry = f"[{timestamp}] {message}\n"

        self.log_text.insert(tk.END, log_entry)
        self.log_text.see(tk.END)  # 自動滾動到最新

    def clear_log(self):
        """清除日誌"""
        self.log_text.delete(1.0, tk.END)