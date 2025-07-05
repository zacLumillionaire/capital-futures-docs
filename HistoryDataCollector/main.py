#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
群益期貨歷史資料收集器主程式
整合所有模組，提供GUI和命令列介面
"""

import os
import sys
import logging
import argparse
import time
import tkinter as tk
from tkinter import ttk, messagebox, filedialog
from datetime import datetime, timedelta
import threading

# 添加專案路徑
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# 導入專案模組
from history_config import *
from utils.skcom_manager import SKCOMManager
from utils.logger import setup_logger, get_logger
from database.db_manager import DatabaseManager
from collectors.tick_collector import TickCollector
from collectors.best5_collector import Best5Collector
from collectors.kline_collector import KLineCollector
from database.postgres_importer import PostgreSQLImporter

# 設定日誌
setup_logger()
logger = get_logger(__name__)

class HistoryDataCollectorGUI:
    """歷史資料收集器GUI介面"""

    def __init__(self, root):
        """
        初始化GUI介面
        
        Args:
            root: tkinter根視窗
        """
        self.root = root
        self.root.title(WINDOW_TITLE)
        self.root.geometry(WINDOW_SIZE)
        
        # 核心元件
        self.skcom_manager = None
        self.db_manager = None
        self.tick_collector = None
        self.best5_collector = None
        self.kline_collector = None
        
        # 狀態變數
        self.is_logged_in = False
        self.is_collecting = False
        self.collection_thread = None
        
        # 建立GUI元件
        self.create_widgets()
        
        # 初始化元件
        self.initialize_components()

    def create_widgets(self):
        """建立GUI元件"""
        # 主框架
        main_frame = ttk.Frame(self.root, padding="10")
        main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # 登入區域
        login_frame = ttk.LabelFrame(main_frame, text="登入設定", padding="5")
        login_frame.grid(row=0, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=(0, 10))
        
        ttk.Label(login_frame, text="身分證字號:").grid(row=0, column=0, sticky=tk.W)
        self.user_id_var = tk.StringVar(value=DEFAULT_USER_ID)
        ttk.Entry(login_frame, textvariable=self.user_id_var, width=15).grid(row=0, column=1, padx=(5, 10))
        
        ttk.Label(login_frame, text="密碼:").grid(row=0, column=2, sticky=tk.W)
        self.password_var = tk.StringVar(value=DEFAULT_PASSWORD)
        ttk.Entry(login_frame, textvariable=self.password_var, show="*", width=15).grid(row=0, column=3, padx=(5, 10))
        
        self.login_btn = ttk.Button(login_frame, text="登入", command=self.login)
        self.login_btn.grid(row=0, column=4, padx=(10, 0))
        
        self.logout_btn = ttk.Button(login_frame, text="登出", command=self.logout, state=tk.DISABLED)
        self.logout_btn.grid(row=0, column=5, padx=(5, 0))
        
        # 收集設定區域
        collect_frame = ttk.LabelFrame(main_frame, text="收集設定", padding="5")
        collect_frame.grid(row=1, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=(0, 10))
        
        # 商品代碼
        ttk.Label(collect_frame, text="商品代碼:").grid(row=0, column=0, sticky=tk.W)
        self.symbol_var = tk.StringVar(value=DEFAULT_SYMBOL)
        symbol_combo = ttk.Combobox(collect_frame, textvariable=self.symbol_var, width=12)
        symbol_combo['values'] = list(PRODUCT_CODES.keys())
        symbol_combo.grid(row=0, column=1, padx=(5, 10))
        
        # K線類型
        ttk.Label(collect_frame, text="K線類型:").grid(row=0, column=2, sticky=tk.W)
        self.kline_type_var = tk.StringVar(value='MINUTE')
        kline_combo = ttk.Combobox(collect_frame, textvariable=self.kline_type_var, width=10)
        kline_combo['values'] = list(KLINE_TYPES.keys())
        kline_combo.grid(row=0, column=3, padx=(5, 10))
        
        # 交易時段
        ttk.Label(collect_frame, text="交易時段:").grid(row=0, column=4, sticky=tk.W)
        self.session_var = tk.StringVar(value='ALL')
        session_combo = ttk.Combobox(collect_frame, textvariable=self.session_var, width=12)
        session_combo['values'] = list(TRADING_SESSION_NAMES.keys())
        session_combo.grid(row=0, column=5, padx=(5, 0))
        
        # 日期設定
        date_frame = ttk.Frame(collect_frame)
        date_frame.grid(row=1, column=0, columnspan=6, sticky=(tk.W, tk.E), pady=(10, 0))
        
        ttk.Label(date_frame, text="起始日期:").grid(row=0, column=0, sticky=tk.W)
        self.start_date_var = tk.StringVar(value=(datetime.now() - timedelta(days=30)).strftime('%Y%m%d'))
        ttk.Entry(date_frame, textvariable=self.start_date_var, width=10).grid(row=0, column=1, padx=(5, 10))
        
        ttk.Label(date_frame, text="結束日期:").grid(row=0, column=2, sticky=tk.W)
        self.end_date_var = tk.StringVar(value=datetime.now().strftime('%Y%m%d'))
        ttk.Entry(date_frame, textvariable=self.end_date_var, width=10).grid(row=0, column=3, padx=(5, 10))
        
        # 收集類型選擇
        type_frame = ttk.Frame(collect_frame)
        type_frame.grid(row=2, column=0, columnspan=6, sticky=(tk.W, tk.E), pady=(10, 0))
        
        self.collect_tick_var = tk.BooleanVar(value=True)
        ttk.Checkbutton(type_frame, text="逐筆資料", variable=self.collect_tick_var).grid(row=0, column=0, padx=(0, 10))
        
        self.collect_best5_var = tk.BooleanVar(value=True)
        ttk.Checkbutton(type_frame, text="五檔資料", variable=self.collect_best5_var).grid(row=0, column=1, padx=(0, 10))
        
        self.collect_kline_var = tk.BooleanVar(value=True)
        ttk.Checkbutton(type_frame, text="K線資料", variable=self.collect_kline_var).grid(row=0, column=2, padx=(0, 10))
        
        # 控制按鈕
        control_frame = ttk.Frame(main_frame)
        control_frame.grid(row=2, column=0, columnspan=2, pady=(0, 10))
        
        self.start_btn = ttk.Button(control_frame, text="開始收集", command=self.start_collection, state=tk.DISABLED)
        self.start_btn.grid(row=0, column=0, padx=(0, 10))
        
        self.stop_btn = ttk.Button(control_frame, text="停止收集", command=self.stop_collection, state=tk.DISABLED)
        self.stop_btn.grid(row=0, column=1, padx=(0, 10))
        
        self.stats_btn = ttk.Button(control_frame, text="查看統計", command=self.show_statistics)
        self.stats_btn.grid(row=0, column=2, padx=(0, 10))

        self.import_btn = ttk.Button(control_frame, text="匯入K線", command=self.import_to_postgres)
        self.import_btn.grid(row=0, column=3, padx=(0, 5))

        # 新增逐筆和五檔匯入按鈕
        self.import_tick_btn = ttk.Button(control_frame, text="匯入逐筆", command=self.import_tick_to_postgres)
        self.import_tick_btn.grid(row=0, column=4, padx=(0, 5))

        self.import_best5_btn = ttk.Button(control_frame, text="匯入五檔", command=self.import_best5_to_postgres)
        self.import_best5_btn.grid(row=0, column=5, padx=(0, 5))

        self.import_all_btn = ttk.Button(control_frame, text="匯入全部", command=self.import_all_to_postgres)
        self.import_all_btn.grid(row=0, column=6, padx=(0, 10))

        # 第二行按鈕
        control_frame2 = ttk.Frame(main_frame)
        control_frame2.grid(row=3, column=0, columnspan=2, pady=(5, 10))

        # 自動匯入選項
        self.auto_import_var = tk.BooleanVar()
        self.auto_import_check = ttk.Checkbutton(
            control_frame2,
            text="收集完成後自動匯入PostgreSQL",
            variable=self.auto_import_var
        )
        self.auto_import_check.grid(row=0, column=0, padx=(0, 10))

        # 資料管理按鈕
        self.manage_data_btn = ttk.Button(control_frame2, text="管理資料", command=self.manage_collected_data)
        self.manage_data_btn.grid(row=0, column=1, padx=(0, 10))

        # PostgreSQL統計按鈕
        self.pg_stats_btn = ttk.Button(control_frame2, text="PostgreSQL統計", command=self.show_postgres_statistics)
        self.pg_stats_btn.grid(row=0, column=2, padx=(0, 10))

        # 狀態顯示區域
        status_frame = ttk.LabelFrame(main_frame, text="狀態資訊", padding="5")
        status_frame.grid(row=4, column=0, columnspan=2, sticky=(tk.W, tk.E, tk.N, tk.S), pady=(0, 10))
        
        # 建立文字顯示區域
        self.status_text = tk.Text(status_frame, height=15, width=80)
        scrollbar = ttk.Scrollbar(status_frame, orient=tk.VERTICAL, command=self.status_text.yview)
        self.status_text.configure(yscrollcommand=scrollbar.set)
        
        self.status_text.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        scrollbar.grid(row=0, column=1, sticky=(tk.N, tk.S))
        
        # 設定網格權重
        main_frame.columnconfigure(0, weight=1)
        main_frame.rowconfigure(3, weight=1)
        status_frame.columnconfigure(0, weight=1)
        status_frame.rowconfigure(0, weight=1)

    def initialize_components(self):
        """初始化核心元件"""
        try:
            self.log_message("🚀 初始化歷史資料收集器...")
            
            # 初始化資料庫管理器
            self.db_manager = DatabaseManager()
            self.log_message("✅ 資料庫管理器初始化完成")
            
            # 初始化SKCOM管理器
            self.skcom_manager = SKCOMManager()
            
            if not self.skcom_manager.initialize_skcom():
                raise Exception("SKCOM API初始化失敗")
            
            if not self.skcom_manager.initialize_skcom_objects():
                raise Exception("SKCOM物件初始化失敗")
            
            self.log_message("✅ SKCOM API初始化完成")
            
            # 初始化收集器
            self.tick_collector = TickCollector(self.skcom_manager, self.db_manager)
            self.best5_collector = Best5Collector(self.skcom_manager, self.db_manager)
            self.kline_collector = KLineCollector(self.skcom_manager, self.db_manager)
            
            self.log_message("✅ 所有元件初始化完成")
            
        except Exception as e:
            self.log_message(f"❌ 初始化失敗: {e}")
            messagebox.showerror("初始化錯誤", f"初始化失敗: {e}")

    def log_message(self, message):
        """在狀態區域顯示訊息"""
        timestamp = datetime.now().strftime("%H:%M:%S")
        full_message = f"[{timestamp}] {message}\n"
        
        # 在GUI中顯示
        self.status_text.insert(tk.END, full_message)
        self.status_text.see(tk.END)
        self.root.update_idletasks()
        
        # 同時記錄到日誌
        logger.info(message)

    def login(self):
        """登入群益API"""
        try:
            user_id = self.user_id_var.get().strip()
            password = self.password_var.get().strip()

            if not user_id or not password:
                messagebox.showerror("登入錯誤", "請輸入身分證字號和密碼")
                return

            self.log_message("🔐 開始登入群益API...")

            # 執行登入
            if self.skcom_manager.login(user_id, password):
                self.log_message("✅ 登入成功")

                # 連線報價主機
                self.log_message("📡 連線報價主機...")
                if self.skcom_manager.connect_quote_server():
                    self.log_message("⏳ 等待商品資料準備完成...")

                    # 在背景等待商品資料準備完成
                    self.wait_for_stocks_ready()
                else:
                    self.log_message("❌ 連線報價主機失敗")
                    return
            else:
                self.log_message("❌ 登入失敗")
                return

        except Exception as e:
            self.log_message(f"❌ 登入時發生錯誤: {e}")
            messagebox.showerror("登入錯誤", f"登入失敗: {e}")

    def wait_for_stocks_ready(self):
        """等待商品資料準備完成"""
        def check_ready():
            timeout = 30  # 30秒超時
            start_time = time.time()

            while not self.skcom_manager.stocks_ready:
                if time.time() - start_time > timeout:
                    self.log_message("❌ 等待商品資料準備完成超時")
                    return
                time.sleep(1)

            # 商品資料準備完成
            self.log_message("✅ 商品資料已準備完成，可以開始收集資料")
            self.is_logged_in = True

            # 更新UI狀態
            self.root.after(0, self.update_login_ui)

        # 在背景執行
        threading.Thread(target=check_ready, daemon=True).start()

    def update_login_ui(self):
        """更新登入相關UI狀態"""
        if self.is_logged_in:
            self.login_btn.config(state=tk.DISABLED)
            self.logout_btn.config(state=tk.NORMAL)
            self.start_btn.config(state=tk.NORMAL)
        else:
            self.login_btn.config(state=tk.NORMAL)
            self.logout_btn.config(state=tk.DISABLED)
            self.start_btn.config(state=tk.DISABLED)

    def logout(self):
        """登出API"""
        try:
            if self.is_collecting:
                self.stop_collection()

            if self.skcom_manager:
                self.skcom_manager.logout()

            self.is_logged_in = False
            self.update_login_ui()
            self.log_message("✅ 已登出")

        except Exception as e:
            self.log_message(f"❌ 登出時發生錯誤: {e}")

    def start_collection(self):
        """開始收集資料"""
        if not self.is_logged_in:
            messagebox.showerror("錯誤", "請先登入")
            return

        if self.is_collecting:
            messagebox.showwarning("警告", "資料收集正在進行中")
            return

        try:
            # 取得設定參數
            symbol = self.symbol_var.get()
            kline_type = self.kline_type_var.get()
            trading_session = self.session_var.get()
            start_date = self.start_date_var.get()
            end_date = self.end_date_var.get()

            collect_tick = self.collect_tick_var.get()
            collect_best5 = self.collect_best5_var.get()
            collect_kline = self.collect_kline_var.get()

            if not any([collect_tick, collect_best5, collect_kline]):
                messagebox.showerror("錯誤", "請至少選擇一種資料類型")
                return

            self.log_message(f"🚀 開始收集 {symbol} 資料...")
            self.log_message(f"📊 設定: {kline_type}K線, {start_date}~{end_date}, {TRADING_SESSION_NAMES[trading_session]}")

            self.is_collecting = True
            self.start_btn.config(state=tk.DISABLED)
            self.stop_btn.config(state=tk.NORMAL)

            # 在背景執行收集
            self.collection_thread = threading.Thread(
                target=self.run_collection,
                args=(symbol, kline_type, trading_session, start_date, end_date,
                     collect_tick, collect_best5, collect_kline),
                daemon=True
            )
            self.collection_thread.start()

        except Exception as e:
            self.log_message(f"❌ 開始收集時發生錯誤: {e}")
            messagebox.showerror("錯誤", f"開始收集失敗: {e}")

    def run_collection(self, symbol, kline_type, trading_session, start_date, end_date,
                      collect_tick, collect_best5, collect_kline):
        """在背景執行資料收集"""
        try:
            # 開始收集逐筆資料
            if collect_tick:
                self.log_message("📊 開始收集逐筆資料...")
                self.tick_collector.start_collection(symbol)
                time.sleep(2)  # 等待一下讓資料開始回傳

            # 開始收集五檔資料
            if collect_best5:
                self.log_message("📊 開始收集五檔資料...")
                self.best5_collector.start_collection(symbol)
                time.sleep(2)

            # 開始收集K線資料
            if collect_kline:
                self.log_message("📊 開始收集K線資料...")
                self.kline_collector.start_collection(
                    symbol, kline_type, start_date, end_date, trading_session
                )

            # 監控收集狀態
            self.monitor_collection()

        except Exception as e:
            self.log_message(f"❌ 收集過程中發生錯誤: {e}")
            self.root.after(0, self.collection_finished)

    def monitor_collection(self):
        """監控收集狀態"""
        while self.is_collecting:
            try:
                # 檢查K線收集是否完成
                if (self.collect_kline_var.get() and
                    hasattr(self.kline_collector, 'is_complete') and
                    self.kline_collector.is_complete):
                    self.log_message("✅ K線資料收集完成")
                    break

                # 顯示進度
                stats = self.get_collection_stats()
                if stats['total_count'] > 0:
                    self.log_message(f"📊 收集進度: 共 {stats['total_count']:,} 筆資料")

                time.sleep(5)  # 每5秒檢查一次

            except Exception as e:
                self.log_message(f"❌ 監控收集狀態時發生錯誤: {e}")
                break

        # 收集完成
        self.root.after(0, self.collection_finished)

    def stop_collection(self):
        """停止收集資料"""
        try:
            self.log_message("🛑 停止資料收集...")
            self.is_collecting = False

            if self.tick_collector:
                self.tick_collector.stop_collection()
            if self.best5_collector:
                self.best5_collector.stop_collection()
            if self.kline_collector:
                self.kline_collector.stop_collection()

            self.collection_finished()

        except Exception as e:
            self.log_message(f"❌ 停止收集時發生錯誤: {e}")

    def collection_finished(self):
        """收集完成後的處理"""
        self.is_collecting = False
        self.start_btn.config(state=tk.NORMAL if self.is_logged_in else tk.DISABLED)
        self.stop_btn.config(state=tk.DISABLED)

        # 顯示最終統計
        stats = self.get_collection_stats()
        self.log_message(f"✅ 收集完成 - 總計: {stats['total_count']:,} 筆資料")
        self.log_message(f"   逐筆: {stats['tick_count']:,} 筆")
        self.log_message(f"   五檔: {stats['best5_count']:,} 筆")
        self.log_message(f"   K線: {stats['kline_count']:,} 筆")

        # 檢查是否需要自動匯入PostgreSQL
        if self.auto_import_var.get() and stats['kline_count'] > 0:
            self.log_message("🚀 開始自動匯入PostgreSQL...")
            self.auto_import_to_postgres()

    def get_collection_stats(self):
        """取得收集統計"""
        try:
            if self.db_manager:
                return self.db_manager.get_data_statistics()
            return {'tick_count': 0, 'best5_count': 0, 'kline_count': 0, 'total_count': 0}
        except:
            return {'tick_count': 0, 'best5_count': 0, 'kline_count': 0, 'total_count': 0}

    def show_statistics(self):
        """顯示資料統計"""
        try:
            stats = self.db_manager.get_data_statistics() if self.db_manager else None
            if not stats:
                messagebox.showinfo("統計資訊", "無法取得統計資料")
                return

            # 建立統計視窗
            stats_window = tk.Toplevel(self.root)
            stats_window.title("資料統計")
            stats_window.geometry("400x300")

            # 統計內容
            stats_frame = ttk.Frame(stats_window, padding="10")
            stats_frame.pack(fill=tk.BOTH, expand=True)

            ttk.Label(stats_frame, text="資料庫統計資訊", font=("Arial", 12, "bold")).pack(pady=(0, 10))

            ttk.Label(stats_frame, text=f"逐筆資料: {stats['tick_count']:,} 筆").pack(anchor=tk.W)
            ttk.Label(stats_frame, text=f"五檔資料: {stats['best5_count']:,} 筆").pack(anchor=tk.W)
            ttk.Label(stats_frame, text=f"K線資料: {stats['kline_count']:,} 筆").pack(anchor=tk.W)
            ttk.Label(stats_frame, text=f"總計: {stats['total_count']:,} 筆").pack(anchor=tk.W, pady=(5, 0))

            if stats.get('latest_tick_time'):
                ttk.Label(stats_frame, text=f"最新資料時間: {stats['latest_tick_time']}").pack(anchor=tk.W, pady=(10, 0))

            if stats.get('date_range'):
                date_range = stats['date_range']
                if date_range['min_date'] and date_range['max_date']:
                    ttk.Label(stats_frame, text=f"資料日期範圍: {date_range['min_date']} ~ {date_range['max_date']}").pack(anchor=tk.W)

            # 關閉按鈕
            ttk.Button(stats_frame, text="關閉", command=stats_window.destroy).pack(pady=(20, 0))

        except Exception as e:
            self.log_message(f"❌ 顯示統計時發生錯誤: {e}")
            messagebox.showerror("錯誤", f"顯示統計失敗: {e}")

    def import_to_postgres(self):
        """匯入資料到PostgreSQL"""
        try:
            # 檢查是否有資料可匯入
            if not self.db_manager:
                messagebox.showerror("錯誤", "資料庫管理器未初始化")
                return

            stats = self.db_manager.get_data_statistics()
            if not stats or stats['kline_count'] == 0:
                messagebox.showwarning("警告", "沒有K線資料可匯入")
                return

            # 確認匯入
            result = messagebox.askyesno(
                "確認匯入",
                f"即將匯入 {stats['kline_count']} 筆K線資料到PostgreSQL\n\n"
                "請確認：\n"
                "1. PostgreSQL資料庫已啟動\n"
                "2. app_setup.py和shared.py在正確路徑\n"
                "3. stock_price表已建立\n\n"
                "確定要繼續嗎？"
            )

            if not result:
                return

            self.log_message("🚀 開始匯入資料到PostgreSQL...")

            # 在背景執行匯入
            def run_import():
                try:
                    importer = PostgreSQLImporter()

                    if not importer.postgres_initialized:
                        self.root.after(0, lambda: self.log_message("❌ PostgreSQL連接失敗"))
                        return

                    # 執行匯入 - 使用優化參數
                    success = importer.import_kline_to_postgres(
                        symbol='MTX00',  # 可以從GUI取得
                        kline_type='MINUTE',
                        batch_size=5000,  # 增加批次大小
                        optimize_performance=True,  # 啟用性能優化
                        exclude_anomalies=True  # 排除異常資料
                    )

                    if success:
                        self.root.after(0, lambda: self.log_message("✅ PostgreSQL匯入完成！"))
                        self.root.after(0, lambda: messagebox.showinfo("成功", "資料匯入完成！"))
                    else:
                        self.root.after(0, lambda: self.log_message("❌ PostgreSQL匯入失敗"))
                        self.root.after(0, lambda: messagebox.showerror("失敗", "資料匯入失敗，請檢查日誌"))

                except Exception as e:
                    error_msg = f"匯入過程中發生錯誤: {e}"
                    self.root.after(0, lambda: self.log_message(f"❌ {error_msg}"))
                    self.root.after(0, lambda: messagebox.showerror("錯誤", error_msg))

            # 在背景執行
            threading.Thread(target=run_import, daemon=True).start()

        except Exception as e:
            self.log_message(f"❌ 匯入功能錯誤: {e}")
            messagebox.showerror("錯誤", f"匯入功能失敗: {e}")

    def auto_import_to_postgres(self):
        """自動匯入資料到PostgreSQL（收集完成後）"""
        try:
            # 檢查是否有資料可匯入
            if not self.db_manager:
                self.log_message("❌ 自動匯入失敗：資料庫管理器未初始化")
                return

            stats = self.db_manager.get_data_statistics()
            if not stats or stats['kline_count'] == 0:
                self.log_message("⚠️ 沒有K線資料可自動匯入")
                return

            self.log_message(f"📊 準備自動匯入 {stats['kline_count']} 筆K線資料...")

            # 在背景執行匯入
            def run_auto_import():
                try:
                    importer = PostgreSQLImporter()

                    if not importer.postgres_initialized:
                        self.root.after(0, lambda: self.log_message("❌ 自動匯入失敗：PostgreSQL連接失敗"))
                        return

                    # 獲取當前收集的商品代碼和K線類型
                    symbol = self.symbol_var.get()
                    kline_type = self.kline_type_var.get()  # 直接使用GUI中選擇的值

                    # 執行匯入 - 使用優化參數
                    success = importer.import_kline_to_postgres(
                        symbol=symbol,
                        kline_type=kline_type,
                        batch_size=5000,  # 增加批次大小
                        optimize_performance=True,  # 啟用性能優化
                        exclude_anomalies=True  # 排除異常資料
                    )

                    if success:
                        self.root.after(0, lambda: self.log_message("✅ 自動匯入PostgreSQL完成！"))
                    else:
                        self.root.after(0, lambda: self.log_message("❌ 自動匯入PostgreSQL失敗"))

                except Exception as e:
                    error_msg = f"自動匯入過程中發生錯誤: {e}"
                    self.root.after(0, lambda: self.log_message(f"❌ {error_msg}"))

            # 在背景執行
            threading.Thread(target=run_auto_import, daemon=True).start()

        except Exception as e:
            self.log_message(f"❌ 自動匯入功能錯誤: {e}")

    def manage_collected_data(self):
        """管理收集到的資料"""
        try:
            # 檢查是否有資料
            if not self.db_manager:
                messagebox.showerror("錯誤", "資料庫管理器未初始化")
                return

            stats = self.db_manager.get_data_statistics()
            total_data = stats['kline_count'] + stats['tick_count'] + stats['best5_count']

            if total_data == 0:
                messagebox.showinfo("資訊", "目前沒有收集到的資料")
                return

            # 建立資料管理視窗
            manage_window = tk.Toplevel(self.root)
            manage_window.title("資料管理")
            manage_window.geometry("500x400")
            manage_window.transient(self.root)
            manage_window.grab_set()

            # 資料摘要
            summary_frame = ttk.LabelFrame(manage_window, text="資料摘要", padding="10")
            summary_frame.pack(fill=tk.X, padx=10, pady=5)

            summary_text = f"""📊 收集資料統計：
• K線資料：{stats['kline_count']:,} 筆
• 逐筆資料：{stats['tick_count']:,} 筆
• 五檔資料：{stats['best5_count']:,} 筆
• 總計：{total_data:,} 筆"""

            ttk.Label(summary_frame, text=summary_text, justify=tk.LEFT).pack(anchor=tk.W)

            # 操作按鈕
            button_frame = ttk.Frame(manage_window)
            button_frame.pack(fill=tk.X, padx=10, pady=10)

            def clear_all_data():
                result = messagebox.askyesno(
                    "確認清空",
                    f"⚠️ 即將清空所有收集到的資料：\n\n"
                    f"• K線資料：{stats['kline_count']:,} 筆\n"
                    f"• 逐筆資料：{stats['tick_count']:,} 筆\n"
                    f"• 五檔資料：{stats['best5_count']:,} 筆\n\n"
                    f"這個操作無法復原！確定要繼續嗎？"
                )

                if result:
                    try:
                        # 清空資料
                        import sqlite3
                        conn = sqlite3.connect(self.db_manager.db_path)
                        cursor = conn.cursor()

                        cursor.execute("DELETE FROM kline_data")
                        cursor.execute("DELETE FROM tick_data")
                        cursor.execute("DELETE FROM best5_data")
                        cursor.execute("DELETE FROM collection_log")
                        cursor.execute("DELETE FROM sqlite_sequence")

                        conn.commit()
                        conn.close()

                        self.log_message("✅ 所有收集資料已清空")
                        messagebox.showinfo("成功", "所有資料已清空")
                        manage_window.destroy()

                    except Exception as e:
                        self.log_message(f"❌ 清空資料失敗: {e}")
                        messagebox.showerror("錯誤", f"清空資料失敗：{e}")

            def open_external_tool():
                """開啟外部管理工具"""
                import subprocess
                import sys
                try:
                    subprocess.Popen([sys.executable, "manage_collected_data.py"],
                                   cwd=os.path.dirname(os.path.abspath(__file__)))
                    manage_window.destroy()
                except Exception as e:
                    messagebox.showerror("錯誤", f"無法開啟管理工具：{e}")

            ttk.Button(button_frame, text="清空所有資料", command=clear_all_data).pack(side=tk.LEFT, padx=5)
            ttk.Button(button_frame, text="進階管理", command=open_external_tool).pack(side=tk.LEFT, padx=5)
            ttk.Button(button_frame, text="關閉", command=manage_window.destroy).pack(side=tk.RIGHT, padx=5)

        except Exception as e:
            self.log_message(f"❌ 資料管理功能錯誤: {e}")
            messagebox.showerror("錯誤", f"資料管理功能失敗: {e}")

    def import_tick_to_postgres(self):
        """匯入逐筆資料到PostgreSQL"""
        try:
            self.log_message("🚀 開始匯入逐筆資料到PostgreSQL...")

            def run_import():
                try:
                    from database.postgres_importer import PostgreSQLImporter
                    importer = PostgreSQLImporter()

                    if not importer.postgres_initialized:
                        self.root.after(0, lambda: self.log_message("❌ PostgreSQL未初始化，無法匯入"))
                        self.root.after(0, lambda: messagebox.showerror("失敗", "PostgreSQL連接失敗"))
                        return

                    # 執行逐筆資料匯入
                    success = importer.import_tick_to_postgres(
                        symbol='MTX00',
                        batch_size=5000,
                        optimize_performance=True
                    )

                    if success:
                        self.root.after(0, lambda: self.log_message("✅ 逐筆資料匯入完成"))
                        self.root.after(0, lambda: messagebox.showinfo("成功", "逐筆資料匯入完成"))
                    else:
                        self.root.after(0, lambda: self.log_message("❌ 逐筆資料匯入失敗"))
                        self.root.after(0, lambda: messagebox.showerror("失敗", "逐筆資料匯入失敗"))

                except Exception as e:
                    error_msg = f"逐筆資料匯入過程中發生錯誤: {e}"
                    self.root.after(0, lambda: self.log_message(f"❌ {error_msg}"))
                    self.root.after(0, lambda: messagebox.showerror("錯誤", error_msg))

            # 在背景執行
            threading.Thread(target=run_import, daemon=True).start()

        except Exception as e:
            self.log_message(f"❌ 逐筆資料匯入功能錯誤: {e}")
            messagebox.showerror("錯誤", f"逐筆資料匯入功能失敗: {e}")

    def import_best5_to_postgres(self):
        """匯入五檔資料到PostgreSQL"""
        try:
            self.log_message("🚀 開始匯入五檔資料到PostgreSQL...")

            def run_import():
                try:
                    from database.postgres_importer import PostgreSQLImporter
                    importer = PostgreSQLImporter()

                    if not importer.postgres_initialized:
                        self.root.after(0, lambda: self.log_message("❌ PostgreSQL未初始化，無法匯入"))
                        self.root.after(0, lambda: messagebox.showerror("失敗", "PostgreSQL連接失敗"))
                        return

                    # 執行五檔資料匯入
                    success = importer.import_best5_to_postgres(
                        symbol='MTX00',
                        batch_size=5000,
                        optimize_performance=True
                    )

                    if success:
                        self.root.after(0, lambda: self.log_message("✅ 五檔資料匯入完成"))
                        self.root.after(0, lambda: messagebox.showinfo("成功", "五檔資料匯入完成"))
                    else:
                        self.root.after(0, lambda: self.log_message("❌ 五檔資料匯入失敗"))
                        self.root.after(0, lambda: messagebox.showerror("失敗", "五檔資料匯入失敗"))

                except Exception as e:
                    error_msg = f"五檔資料匯入過程中發生錯誤: {e}"
                    self.root.after(0, lambda: self.log_message(f"❌ {error_msg}"))
                    self.root.after(0, lambda: messagebox.showerror("錯誤", error_msg))

            # 在背景執行
            threading.Thread(target=run_import, daemon=True).start()

        except Exception as e:
            self.log_message(f"❌ 五檔資料匯入功能錯誤: {e}")
            messagebox.showerror("錯誤", f"五檔資料匯入功能失敗: {e}")

    def import_all_to_postgres(self):
        """匯入所有資料到PostgreSQL"""
        try:
            self.log_message("🚀 開始匯入所有資料到PostgreSQL...")

            def run_import():
                try:
                    from database.postgres_importer import PostgreSQLImporter
                    importer = PostgreSQLImporter()

                    if not importer.postgres_initialized:
                        self.root.after(0, lambda: self.log_message("❌ PostgreSQL未初始化，無法匯入"))
                        self.root.after(0, lambda: messagebox.showerror("失敗", "PostgreSQL連接失敗"))
                        return

                    # 執行全部資料匯入
                    success = importer.import_all_data_to_postgres(
                        symbol='MTX00',
                        batch_size=5000,
                        optimize_performance=True
                    )

                    if success:
                        self.root.after(0, lambda: self.log_message("✅ 所有資料匯入完成"))
                        self.root.after(0, lambda: messagebox.showinfo("成功", "所有資料匯入完成"))
                    else:
                        self.root.after(0, lambda: self.log_message("❌ 部分資料匯入失敗"))
                        self.root.after(0, lambda: messagebox.showwarning("部分成功", "部分資料匯入失敗，請檢查日誌"))

                except Exception as e:
                    error_msg = f"全部資料匯入過程中發生錯誤: {e}"
                    self.root.after(0, lambda: self.log_message(f"❌ {error_msg}"))
                    self.root.after(0, lambda: messagebox.showerror("錯誤", error_msg))

            # 在背景執行
            threading.Thread(target=run_import, daemon=True).start()

        except Exception as e:
            self.log_message(f"❌ 全部資料匯入功能錯誤: {e}")
            messagebox.showerror("錯誤", f"全部資料匯入功能失敗: {e}")

    def show_postgres_statistics(self):
        """顯示PostgreSQL資料統計"""
        try:
            from database.postgres_importer import PostgreSQLImporter
            importer = PostgreSQLImporter()

            if not importer.postgres_initialized:
                self.log_message("❌ PostgreSQL未初始化")
                messagebox.showerror("錯誤", "PostgreSQL連接失敗")
                return

            stats = importer.get_postgres_data_statistics()
            if not stats:
                messagebox.showwarning("警告", "無法取得PostgreSQL統計資料")
                return

            # 創建統計視窗
            stats_window = tk.Toplevel(self.root)
            stats_window.title("PostgreSQL資料統計")
            stats_window.geometry("400x300")
            stats_window.resizable(False, False)

            # 統計資訊框架
            stats_frame = ttk.Frame(stats_window, padding="20")
            stats_frame.pack(fill=tk.BOTH, expand=True)

            ttk.Label(stats_frame, text="PostgreSQL資料統計", font=("Arial", 14, "bold")).pack(pady=(0, 20))

            # 顯示統計資料
            ttk.Label(stats_frame, text=f"K線資料: {stats['kline_count']:,} 筆").pack(anchor=tk.W, pady=2)
            ttk.Label(stats_frame, text=f"逐筆資料: {stats['tick_count']:,} 筆").pack(anchor=tk.W, pady=2)
            ttk.Label(stats_frame, text=f"五檔資料: {stats['best5_count']:,} 筆").pack(anchor=tk.W, pady=2)
            ttk.Label(stats_frame, text=f"總計: {stats['total_count']:,} 筆").pack(anchor=tk.W, pady=(10, 20))

            # 關閉按鈕
            ttk.Button(stats_frame, text="關閉", command=stats_window.destroy).pack(pady=(20, 0))

        except Exception as e:
            self.log_message(f"❌ 顯示PostgreSQL統計時發生錯誤: {e}")
            messagebox.showerror("錯誤", f"顯示統計失敗: {e}")

    def on_closing(self):
        """視窗關閉事件處理"""
        try:
            if self.is_collecting:
                if messagebox.askokcancel("確認", "資料收集正在進行中，確定要關閉嗎？"):
                    self.stop_collection()
                else:
                    return

            if self.skcom_manager:
                self.skcom_manager.cleanup()

            self.root.destroy()

        except Exception as e:
            logger.error(f"關閉程式時發生錯誤: {e}")
            self.root.destroy()

class HistoryDataCollectorCLI:
    """歷史資料收集器命令列介面"""

    def __init__(self):
        """初始化CLI介面"""
        self.skcom_manager = None
        self.db_manager = None
        self.tick_collector = None
        self.best5_collector = None
        self.kline_collector = None

    def initialize(self):
        """初始化所有元件"""
        try:
            logger.info("🚀 初始化歷史資料收集器...")

            # 初始化資料庫管理器
            self.db_manager = DatabaseManager()
            logger.info("✅ 資料庫管理器初始化完成")

            # 初始化SKCOM管理器
            self.skcom_manager = SKCOMManager()

            if not self.skcom_manager.initialize_skcom():
                raise Exception("SKCOM API初始化失敗")

            if not self.skcom_manager.initialize_skcom_objects():
                raise Exception("SKCOM物件初始化失敗")

            logger.info("✅ SKCOM API初始化完成")

            # 初始化收集器
            self.tick_collector = TickCollector(self.skcom_manager, self.db_manager)
            self.best5_collector = Best5Collector(self.skcom_manager, self.db_manager)
            self.kline_collector = KLineCollector(self.skcom_manager, self.db_manager)

            logger.info("✅ 所有元件初始化完成")
            return True

        except Exception as e:
            logger.error(f"❌ 初始化失敗: {e}")
            return False

    def login(self, user_id=None, password=None):
        """登入群益API"""
        try:
            if not user_id:
                user_id = DEFAULT_USER_ID
            if not password:
                password = DEFAULT_PASSWORD

            logger.info("🔐 開始登入群益API...")

            if not self.skcom_manager.login(user_id, password):
                logger.error("❌ 登入失敗")
                return False

            logger.info("✅ 登入成功")

            # 連線報價主機
            logger.info("📡 連線報價主機...")
            if not self.skcom_manager.connect_quote_server():
                logger.error("❌ 連線報價主機失敗")
                return False

            # 等待商品資料準備完成
            logger.info("⏳ 等待商品資料準備完成...")
            timeout = 30
            start_time = time.time()

            while not self.skcom_manager.stocks_ready:
                if time.time() - start_time > timeout:
                    logger.error("❌ 等待商品資料準備完成超時")
                    return False
                time.sleep(1)

            logger.info("✅ 商品資料已準備完成")
            return True

        except Exception as e:
            logger.error(f"❌ 登入時發生錯誤: {e}")
            return False

    def collect_data(self, symbol=DEFAULT_SYMBOL, kline_type='MINUTE',
                    start_date=None, end_date=None, trading_session='ALL',
                    collect_tick=True, collect_best5=True, collect_kline=True,
                    duration=60):
        """收集資料"""
        try:
            logger.info(f"🚀 開始收集 {symbol} 資料...")

            # 設定預設日期
            if not start_date:
                start_date = (datetime.now() - timedelta(days=DEFAULT_DATE_RANGE)).strftime('%Y%m%d')
            if not end_date:
                end_date = datetime.now().strftime('%Y%m%d')

            logger.info(f"📊 設定: {kline_type}K線, {start_date}~{end_date}, {TRADING_SESSION_NAMES[trading_session]}")

            # 開始收集
            if collect_tick:
                logger.info("📊 開始收集逐筆資料...")
                self.tick_collector.start_collection(symbol)

            if collect_best5:
                logger.info("📊 開始收集五檔資料...")
                self.best5_collector.start_collection(symbol)

            if collect_kline:
                logger.info("📊 開始收集K線資料...")
                self.kline_collector.start_collection(
                    symbol, kline_type, start_date, end_date, trading_session
                )

            # 等待收集完成或超時
            logger.info(f"⏳ 收集中，將持續 {duration} 秒...")
            time.sleep(duration)

            # 停止收集
            self.stop_collection()

            # 顯示統計
            self.show_statistics()

            return True

        except Exception as e:
            logger.error(f"❌ 收集資料時發生錯誤: {e}")
            return False

    def stop_collection(self):
        """停止收集"""
        try:
            logger.info("🛑 停止資料收集...")

            if self.tick_collector:
                self.tick_collector.stop_collection()
            if self.best5_collector:
                self.best5_collector.stop_collection()
            if self.kline_collector:
                self.kline_collector.stop_collection()

            logger.info("✅ 收集已停止")

        except Exception as e:
            logger.error(f"❌ 停止收集時發生錯誤: {e}")

    def show_statistics(self):
        """顯示統計"""
        try:
            stats = self.db_manager.get_data_statistics()
            if stats:
                logger.info("📊 資料庫統計:")
                logger.info(f"   逐筆資料: {stats['tick_count']:,} 筆")
                logger.info(f"   五檔資料: {stats['best5_count']:,} 筆")
                logger.info(f"   K線資料: {stats['kline_count']:,} 筆")
                logger.info(f"   總計: {stats['total_count']:,} 筆")
                if stats.get('latest_tick_time'):
                    logger.info(f"   最新資料時間: {stats['latest_tick_time']}")
            else:
                logger.error("❌ 無法取得資料統計")

        except Exception as e:
            logger.error(f"❌ 顯示統計時發生錯誤: {e}")

    def cleanup(self):
        """清理資源"""
        try:
            if self.skcom_manager:
                self.skcom_manager.cleanup()
            logger.info("✅ 資源清理完成")
        except Exception as e:
            logger.error(f"❌ 清理資源時發生錯誤: {e}")

def main():
    """主函數"""
    parser = argparse.ArgumentParser(description='群益期貨歷史資料收集器')
    parser.add_argument('--mode', choices=['gui', 'cli'], default='gui', help='執行模式')
    parser.add_argument('--user-id', help='身分證字號')
    parser.add_argument('--password', help='密碼')
    parser.add_argument('--symbol', default=DEFAULT_SYMBOL, help='商品代碼')
    parser.add_argument('--kline-type', choices=['MINUTE', 'DAILY', 'WEEKLY', 'MONTHLY'],
                       default='MINUTE', help='K線類型')
    parser.add_argument('--trading-session', choices=['ALL', 'AM_ONLY'],
                       default='ALL', help='交易時段')
    parser.add_argument('--start-date', help='開始日期 (YYYYMMDD)')
    parser.add_argument('--end-date', help='結束日期 (YYYYMMDD)')
    parser.add_argument('--duration', type=int, default=60, help='收集持續時間(秒)')
    parser.add_argument('--collect-tick', action='store_true', default=True, help='收集逐筆資料')
    parser.add_argument('--collect-best5', action='store_true', default=True, help='收集五檔資料')
    parser.add_argument('--collect-kline', action='store_true', default=True, help='收集K線資料')
    parser.add_argument('--no-tick', action='store_true', help='不收集逐筆資料')
    parser.add_argument('--no-best5', action='store_true', help='不收集五檔資料')
    parser.add_argument('--no-kline', action='store_true', help='不收集K線資料')

    args = parser.parse_args()

    # 處理收集類型參數
    collect_tick = args.collect_tick and not args.no_tick
    collect_best5 = args.collect_best5 and not args.no_best5
    collect_kline = args.collect_kline and not args.no_kline

    if args.mode == 'gui':
        # GUI模式
        try:
            root = tk.Tk()
            app = HistoryDataCollectorGUI(root)

            # 設定關閉事件
            root.protocol("WM_DELETE_WINDOW", app.on_closing)

            # 啟動GUI
            root.mainloop()

        except Exception as e:
            logger.error(f"❌ GUI模式啟動失敗: {e}")
            return 1

    else:
        # CLI模式
        try:
            cli = HistoryDataCollectorCLI()

            # 初始化
            if not cli.initialize():
                logger.error("❌ 初始化失敗")
                return 1

            # 登入
            if not cli.login(args.user_id, args.password):
                logger.error("❌ 登入失敗")
                return 1

            # 收集資料
            success = cli.collect_data(
                symbol=args.symbol,
                kline_type=args.kline_type,
                start_date=args.start_date,
                end_date=args.end_date,
                trading_session=args.trading_session,
                collect_tick=collect_tick,
                collect_best5=collect_best5,
                collect_kline=collect_kline,
                duration=args.duration
            )

            # 清理資源
            cli.cleanup()

            return 0 if success else 1

        except KeyboardInterrupt:
            logger.info("❌ 使用者中斷程式")
            if 'cli' in locals():
                cli.cleanup()
            return 1
        except Exception as e:
            logger.error(f"❌ CLI模式執行失敗: {e}")
            if 'cli' in locals():
                cli.cleanup()
            return 1

if __name__ == "__main__":
    try:
        exit_code = main()
        sys.exit(exit_code)
    except Exception as e:
        logger.error(f"❌ 程式執行失敗: {e}")
        sys.exit(1)
