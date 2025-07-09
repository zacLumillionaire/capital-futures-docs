#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
簡化版群益整合交易程式
基於群益官方架構，解決登入和初始化問題
"""

import os
import sys
import time
import tkinter as tk
from tkinter import ttk
from typing import Optional
from datetime import datetime

# 加入order_service路徑
order_service_path = os.path.join(os.path.dirname(__file__), 'order_service')
if order_service_path not in sys.path:
    sys.path.insert(0, order_service_path)

# 導入群益官方模組
import Global
from user_config import get_user_config

# 🚀 Queue基礎設施導入 (GIL問題解決方案)
# 🚨 Console模式：完全禁用Queue架構
QUEUE_INFRASTRUCTURE_AVAILABLE = False
print("💡 使用Console模式，所有信息將在VS Code中顯示")
print("🎯 這將大幅降低GIL錯誤風險，提升系統穩定性")

# 🎯 多組策略系統導入
try:
    from multi_group_database import MultiGroupDatabaseManager
    from multi_group_config import MultiGroupStrategyConfig, create_preset_configs
    from multi_group_position_manager import MultiGroupPositionManager
    from unified_exit_manager import UnifiedExitManager
    from risk_management_engine import RiskManagementEngine
    from multi_group_ui_panel import MultiGroupConfigPanel
    from multi_group_console_logger import get_logger, LogCategory

    MULTI_GROUP_AVAILABLE = True
    print("✅ 多組策略系統模組載入成功")
except ImportError as e:
    MULTI_GROUP_AVAILABLE = False
    print(f"⚠️ 多組策略系統模組載入失敗: {e}")
    print("💡 將使用原有的單組策略系統")

# 🚀 實際下單功能模組導入
try:
    from real_time_quote_manager import RealTimeQuoteManager
    REAL_ORDER_MODULES_AVAILABLE = True
    print("✅ 實際下單模組載入成功")
except ImportError as e:
    REAL_ORDER_MODULES_AVAILABLE = False
    print(f"⚠️ 實際下單模組載入失敗: {e}")
    print("💡 系統將以模擬模式運行")

# 🚀 Stage2 虛實單整合系統模組導入
try:
    from virtual_real_order_manager import VirtualRealOrderManager
    from unified_order_tracker import UnifiedOrderTracker
    from order_mode_ui_controller import OrderModeUIController
    VIRTUAL_REAL_ORDER_AVAILABLE = True
    print("✅ Stage2 虛實單整合系統模組載入成功")
except ImportError as e:
    VIRTUAL_REAL_ORDER_AVAILABLE = False
    print(f"⚠️ Stage2 虛實單整合系統模組載入失敗: {e}")
    print("💡 將使用原有的下單系統")

# 🗄️ 建倉紀錄資料庫模組導入
try:
    import sys
    import os
    # 添加 Python File 目錄到路徑
    python_file_path = os.path.join(os.path.dirname(__file__), '..', 'Python File')
    if python_file_path not in sys.path:
        sys.path.append(python_file_path)

    from database.sqlite_manager import SQLiteManager
    DATABASE_AVAILABLE = True
    print("✅ 建倉紀錄資料庫模組載入成功")
except ImportError as e:
    DATABASE_AVAILABLE = False
    print(f"⚠️ 建倉紀錄資料庫模組載入失敗: {e}")
    print("💡 建倉紀錄將只保存在記憶體中")

class SimpleIntegratedApp:
    """簡化版整合交易應用程式"""
    
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("群益簡化整合交易系統")
        self.root.geometry("1200x800")  # 增加寬度以容納策略面板

        # 使用者配置
        self.config = get_user_config()

        # 狀態變數
        self.logged_in = False

        # 🎯 策略相關變數初始化
        self.strategy_enabled = False
        self.strategy_monitoring = False

        # 區間計算相關
        self.range_high = 0
        self.range_low = 0
        self.range_calculated = False
        self.in_range_period = False
        self.range_prices = []
        self.range_start_hour = 8    # 預設08:46開始
        self.range_start_minute = 46
        self._last_range_minute = None
        self._range_start_time = ""

        # 部位管理相關
        self.current_position = None
        self.first_breakout_detected = False
        self.waiting_for_entry = False
        self.breakout_signal = None
        self.breakout_direction = None

        # 價格追蹤（不即時更新UI，只記錄）
        self.latest_price = 0
        self.latest_time = ""
        self.price_count = 0  # 接收到的報價數量
        self.best5_count = 0  # 接收到的五檔報價數量
        # self.last_quote_time = time.time()  # 已移除，避免GIL風險

        # LOG控制變數
        self.strategy_log_count = 0

        # 🎯 狀態監聽器相關變數
        self.monitoring_stats = {
            'last_quote_count': 0,
            'last_tick_count': 0,
            'last_best5_count': 0,
            'last_quote_time': None,
            'quote_status': '未知',
            'strategy_status': '未啟動',
            'last_strategy_activity': 0,
            'strategy_activity_count': 0
        }

        # 🎯 多組策略系統初始化
        self.multi_group_enabled = False
        self.multi_group_db_manager = None
        self.multi_group_position_manager = None
        self.multi_group_risk_engine = None
        self.multi_group_config_panel = None
        self.multi_group_logger = None

        # 🎯 多組策略狀態管理
        self.multi_group_prepared = False  # 策略是否已準備
        self.multi_group_auto_start = False  # 是否自動啟動
        self.multi_group_running = False  # 策略是否運行中
        self.multi_group_monitoring_ready = False  # 監控準備狀態（等待突破信號）
        self._auto_start_triggered = False  # 防止重複觸發自動啟動

        if MULTI_GROUP_AVAILABLE:
            self.init_multi_group_system()

        # 🚀 實際下單系統初始化
        self.real_order_enabled = False
        self.real_time_quote_manager = None
        if REAL_ORDER_MODULES_AVAILABLE:
            self.init_real_order_system()

        # 🚀 Stage2 虛實單整合系統初始化
        self.virtual_real_order_manager = None
        self.unified_order_tracker = None
        self.order_mode_ui_controller = None
        self.virtual_real_system_enabled = False
        if VIRTUAL_REAL_ORDER_AVAILABLE:
            self.init_virtual_real_order_system()

        # Console輸出控制
        self.console_quote_enabled = True
        self.console_strategy_enabled = True  # 策略Console輸出控制

        # 🔧 監控系統總開關 (開發階段可關閉)
        self.monitoring_enabled = False  # 預設關閉，避免GIL風險

        # 五檔數據存儲
        self.best5_data = None

        # 🚨 Console模式：禁用Queue架構
        # self.queue_infrastructure = None
        # self.queue_mode_enabled = False

        # 分鐘K線數據追蹤（新增）
        self.current_minute_candle = None
        self.minute_prices = []  # 當前分鐘內的價格
        self.last_minute = None
        self._last_range_minute = None

        # 建立介面
        self.create_widgets()

        # 註冊OnReplyMessage事件 (解決2017警告)
        self.register_reply_events()

        # 註冊回報事件 (接收下單狀態)
        self.register_order_reply_events()

    def init_real_order_system(self):
        """初始化實際下單系統"""
        try:
            if not REAL_ORDER_MODULES_AVAILABLE:
                print("[REAL_ORDER] ⚠️ 實際下單模組不可用，跳過初始化")
                return

            # 初始化即時報價管理器
            self.real_time_quote_manager = RealTimeQuoteManager(console_enabled=True)

            # 設定實際下單系統狀態
            self.real_order_enabled = True

            print("[REAL_ORDER] ✅ 實際下單系統初始化完成")
            print("[REAL_ORDER] 📊 五檔ASK價格提取系統已就緒")

        except Exception as e:
            print(f"[REAL_ORDER] ❌ 實際下單系統初始化失敗: {e}")
            self.real_order_enabled = False
            self.real_time_quote_manager = None

    def init_virtual_real_order_system(self):
        """初始化Stage2虛實單整合系統"""
        try:
            if not VIRTUAL_REAL_ORDER_AVAILABLE:
                print("[VIRTUAL_REAL] ⚠️ 虛實單整合系統模組不可用，跳過初始化")
                return

            # 1. 初始化虛實單切換管理器
            self.virtual_real_order_manager = VirtualRealOrderManager(
                quote_manager=self.real_time_quote_manager,
                strategy_config=getattr(self, 'strategy_config', None),
                console_enabled=True,
                default_account=self.config.get('FUTURES_ACCOUNT', 'F0200006363839')
            )

            # 2. 初始化統一回報追蹤器
            self.unified_order_tracker = UnifiedOrderTracker(
                strategy_manager=self,
                console_enabled=True
            )

            # 3. 設定系統狀態
            self.virtual_real_system_enabled = True

            print("[VIRTUAL_REAL] ✅ Stage2虛實單整合系統初始化完成")
            print("[VIRTUAL_REAL] 🔄 預設模式: 虛擬模式 (安全)")
            print("[VIRTUAL_REAL] 📊 統一回報追蹤系統已就緒")

            # 🔧 更新多組策略管理器的下單組件
            self._update_multi_group_order_components()

        except Exception as e:
            print(f"[VIRTUAL_REAL] ❌ 虛實單整合系統初始化失敗: {e}")
            self.virtual_real_system_enabled = False
            self.virtual_real_order_manager = None
            self.unified_order_tracker = None

    def _update_multi_group_order_components(self):
        """更新多組策略管理器的下單組件"""
        try:
            if (self.multi_group_enabled and
                self.multi_group_position_manager and
                self.virtual_real_order_manager and
                self.unified_order_tracker):

                # 設置下單組件
                self.multi_group_position_manager.order_manager = self.virtual_real_order_manager
                self.multi_group_position_manager.order_tracker = self.unified_order_tracker

                # 🔧 新增：連接平倉機制管理器到部位管理器
                if hasattr(self, 'exit_mechanism_manager') and self.exit_mechanism_manager:
                    self.multi_group_position_manager.exit_mechanism_manager = self.exit_mechanism_manager
                    print("[MULTI_GROUP] 🔗 平倉機制管理器已連接到部位管理器")

                # 🔧 新增：初始化統一出場管理器
                if not self.unified_exit_manager:
                    self.unified_exit_manager = UnifiedExitManager(
                        order_manager=self.virtual_real_order_manager,
                        position_manager=self.multi_group_position_manager,
                        db_manager=self.multi_group_db_manager,
                        console_enabled=True
                    )
                    # 將統一出場管理器設置到部位管理器
                    self.multi_group_position_manager.unified_exit_manager = self.unified_exit_manager

                    # 將統一出場管理器設置到風險管理引擎
                    if hasattr(self, 'multi_group_risk_engine') and self.multi_group_risk_engine:
                        self.multi_group_risk_engine.set_unified_exit_manager(self.unified_exit_manager)

                    print("[MULTI_GROUP] ✅ 統一出場管理器初始化完成")

                # 🔧 新增：確保總量追蹤管理器已初始化
                if not hasattr(self.multi_group_position_manager, 'total_lot_manager') or \
                   not self.multi_group_position_manager.total_lot_manager:
                    from total_lot_manager import TotalLotManager
                    self.multi_group_position_manager.total_lot_manager = TotalLotManager()
                    print("[MULTI_GROUP] ✅ 總量追蹤管理器初始化完成")

                # 🔧 保留：確保簡化追蹤器已初始化 (向後相容)
                if not hasattr(self.multi_group_position_manager, 'simplified_tracker') or \
                   not self.multi_group_position_manager.simplified_tracker:
                    from simplified_order_tracker import SimplifiedOrderTracker
                    self.multi_group_position_manager.simplified_tracker = SimplifiedOrderTracker()
                    print("[MULTI_GROUP] ✅ 簡化追蹤器初始化完成")

                # 🔍 DEBUG: 設定簡化追蹤器的console開關
                if hasattr(self.multi_group_position_manager, 'simplified_tracker') and \
                   self.multi_group_position_manager.simplified_tracker:
                    if hasattr(self.multi_group_position_manager.simplified_tracker, 'console_enabled'):
                        # 確保console_enabled屬性存在
                        if not hasattr(self, 'console_enabled'):
                            self.console_enabled = True  # 預設啟用console模式

                        self.multi_group_position_manager.simplified_tracker.console_enabled = self.console_enabled
                        if self.console_enabled:
                            print("[MULTI_GROUP] 🔍 簡化追蹤器DEBUG模式已啟用")

                    # 🔧 註冊平倉追價回調
                    if hasattr(self, 'stop_loss_executor') and self.stop_loss_executor:
                        def on_exit_retry(exit_order: dict):
                            """平倉追價回調函數"""
                            try:
                                position_id = exit_order.get('position_id')
                                retry_count = getattr(exit_order, 'retry_count', 1)

                                if self.console_enabled:
                                    print(f"[MAIN] 🔄 收到平倉追價回調: 部位{position_id}")

                                # 執行平倉追價
                                success = self.stop_loss_executor.execute_exit_retry(
                                    position_id, exit_order, retry_count
                                )

                                if self.console_enabled:
                                    if success:
                                        print(f"[MAIN] ✅ 平倉追價執行成功")
                                    else:
                                        print(f"[MAIN] ❌ 平倉追價執行失敗")

                            except Exception as e:
                                if self.console_enabled:
                                    print(f"[MAIN] ❌ 平倉追價回調異常: {e}")

                        # 註冊回調到簡化追蹤器
                        self.multi_group_position_manager.simplified_tracker.exit_retry_callbacks.append(on_exit_retry)

                        if self.console_enabled:
                            print("[MULTI_GROUP] 🔧 平倉追價回調已註冊")

                    # 🔧 新增：註冊平倉成交回調
                    def on_exit_fill(exit_order: dict, price: float, qty: int):
                        """平倉成交回調函數 - 更新部位狀態為EXITED"""
                        try:
                            position_id = exit_order.get('position_id')
                            exit_reason = exit_order.get('exit_reason', '平倉')

                            if self.console_enabled:
                                print(f"[MAIN] 🎯 收到平倉成交回調: 部位{position_id} @{price:.0f}")

                            # 更新部位狀態為EXITED
                            if hasattr(self, 'multi_group_db_manager') and self.multi_group_db_manager:
                                success = self.multi_group_db_manager.update_position_exit(
                                    position_id=position_id,
                                    exit_price=price,
                                    exit_time=datetime.now().strftime('%H:%M:%S'),
                                    exit_reason=exit_reason,
                                    pnl=0.0  # 暫時設為0，後續可以計算實際損益
                                )

                                if success:
                                    if self.console_enabled:
                                        print(f"[MAIN] ✅ 部位{position_id}狀態已更新為EXITED")
                                else:
                                    if self.console_enabled:
                                        print(f"[MAIN] ❌ 部位{position_id}狀態更新失敗")

                        except Exception as e:
                            if self.console_enabled:
                                print(f"[MAIN] ❌ 平倉成交回調異常: {e}")

                    # 註冊平倉成交回調到簡化追蹤器
                    if hasattr(self.multi_group_position_manager, 'simplified_tracker') and \
                       self.multi_group_position_manager.simplified_tracker:
                        self.multi_group_position_manager.simplified_tracker.exit_fill_callbacks.append(on_exit_fill)

                        if self.console_enabled:
                            print("[MULTI_GROUP] 🎯 平倉成交回調已註冊")

                    # 🔧 新增：註冊平倉追價回調
                    def on_exit_retry(exit_order: dict, retry_count: int):
                        """平倉追價回調函數 - 執行平倉FOK追價"""
                        try:
                            position_id = exit_order.get('position_id')
                            original_direction = exit_order.get('original_direction')  # 原始部位方向
                            exit_reason = exit_order.get('exit_reason', '平倉追價')

                            if self.console_enabled:
                                print(f"[MAIN] 🔄 收到平倉追價回調: 部位{position_id} 第{retry_count}次")

                            # 檢查追價限制
                            max_retries = 5
                            if retry_count > max_retries:
                                if self.console_enabled:
                                    print(f"[MAIN] ❌ 部位{position_id}追價次數超限({retry_count}>{max_retries})")
                                return

                            # 計算平倉追價價格
                            retry_price = self._calculate_exit_retry_price(original_direction, retry_count)
                            if not retry_price:
                                if self.console_enabled:
                                    print(f"[MAIN] ❌ 部位{position_id}無法計算追價價格")
                                return

                            # 檢查滑價限制
                            original_price = exit_order.get('original_price', 0)
                            max_slippage = 5
                            if original_price and abs(retry_price - original_price) > max_slippage:
                                if self.console_enabled:
                                    print(f"[MAIN] ❌ 部位{position_id}追價滑價超限: {abs(retry_price - original_price):.0f}點")
                                return

                            # 執行平倉追價下單
                            exit_direction = "SELL" if original_direction == "LONG" else "BUY"

                            if self.console_enabled:
                                print(f"[MAIN] 🔄 執行平倉追價: 部位{position_id} {exit_direction} @{retry_price:.0f} (第{retry_count}次)")

                            # 使用虛實單管理器執行追價下單
                            if hasattr(self, 'virtual_real_order_manager') and self.virtual_real_order_manager:
                                order_result = self.virtual_real_order_manager.execute_strategy_order(
                                    direction=exit_direction,
                                    signal_source=f"exit_retry_{position_id}_{retry_count}",
                                    product="TM0000",
                                    price=retry_price,
                                    quantity=1,
                                    new_close=1  # 平倉
                                )
                                success = order_result.success if order_result else False

                                if success:
                                    if self.console_enabled:
                                        print(f"[MAIN] ✅ 部位{position_id}第{retry_count}次追價下單成功")
                                else:
                                    if self.console_enabled:
                                        print(f"[MAIN] ❌ 部位{position_id}第{retry_count}次追價下單失敗")

                        except Exception as e:
                            if self.console_enabled:
                                print(f"[MAIN] ❌ 平倉追價回調異常: {e}")

                    # 註冊平倉追價回調到簡化追蹤器
                    if hasattr(self.multi_group_position_manager, 'simplified_tracker') and \
                       self.multi_group_position_manager.simplified_tracker:
                        self.multi_group_position_manager.simplified_tracker.exit_retry_callbacks.append(on_exit_retry)

                        if self.console_enabled:
                            print("[MULTI_GROUP] 🔄 平倉追價回調已註冊")

                        # 🔧 設定停損執行器的簡化追蹤器引用
                        if hasattr(self, 'stop_loss_executor') and self.stop_loss_executor:
                            self.stop_loss_executor.simplified_tracker = self.multi_group_position_manager.simplified_tracker
                            if self.console_enabled:
                                print("[MULTI_GROUP] 🔗 停損執行器已連接簡化追蹤器")

                # 重新設置回調機制
                if hasattr(self.multi_group_position_manager, '_setup_order_callbacks'):
                    self.multi_group_position_manager._setup_order_callbacks()
                if hasattr(self.multi_group_position_manager, '_setup_total_lot_manager_callbacks'):
                    self.multi_group_position_manager._setup_total_lot_manager_callbacks()
                if hasattr(self.multi_group_position_manager, '_setup_simplified_tracker_callbacks'):
                    self.multi_group_position_manager._setup_simplified_tracker_callbacks()

                print("[MULTI_GROUP] ✅ 下單組件整合完成")

        except Exception as e:
            print(f"[MULTI_GROUP] ❌ 下單組件整合失敗: {e}")

    def create_widgets(self):
        """建立使用者介面"""

        # 建立筆記本控件（分頁結構）
        notebook = ttk.Notebook(self.root)
        notebook.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        # 主要功能頁面
        main_frame = ttk.Frame(notebook)
        notebook.add(main_frame, text="主要功能")

        # 策略監控頁面
        strategy_frame = ttk.Frame(notebook)
        notebook.add(strategy_frame, text="策略監控")

        # 建立主要功能頁面內容
        self.create_main_page(main_frame)

        # 建立策略監控頁面內容
        self.create_strategy_page(strategy_frame)

        # 🎯 啟動狀態監聽器
        self.start_status_monitor()

    def create_main_page(self, main_frame):
        """建立主要功能頁面"""
        
        # 登入區域
        login_frame = ttk.LabelFrame(main_frame, text="系統登入", padding=10)
        login_frame.pack(fill=tk.X, pady=(0, 10))
        
        # 登入控制
        control_frame = ttk.Frame(login_frame)
        control_frame.pack(fill=tk.X)
        
        ttk.Label(control_frame, text="身分證字號:").grid(row=0, column=0, padx=5)
        self.entry_id = ttk.Entry(control_frame, width=15)
        self.entry_id.insert(0, self.config['USER_ID'])
        self.entry_id.grid(row=0, column=1, padx=5)
        
        ttk.Label(control_frame, text="密碼:").grid(row=0, column=2, padx=5)
        self.entry_password = ttk.Entry(control_frame, show="*", width=15)
        self.entry_password.insert(0, self.config['PASSWORD'])
        self.entry_password.grid(row=0, column=3, padx=5)
        
        self.btn_login = ttk.Button(control_frame, text="登入", command=self.login)
        self.btn_login.grid(row=0, column=4, padx=10)
        
        # 狀態顯示
        self.label_status = ttk.Label(control_frame, text="狀態: 未登入", foreground="red")
        self.label_status.grid(row=0, column=5, padx=10)
        
        # 功能按鈕區域
        function_frame = ttk.LabelFrame(main_frame, text="功能操作", padding=10)
        function_frame.pack(fill=tk.X, pady=(0, 10))
        
        btn_frame = ttk.Frame(function_frame)
        btn_frame.pack(fill=tk.X)
        
        self.btn_init_order = ttk.Button(btn_frame, text="初始化下單", command=self.init_order, state="disabled")
        self.btn_init_order.pack(side=tk.LEFT, padx=5)
        
        self.btn_connect_quote = ttk.Button(btn_frame, text="連線報價", command=self.connect_quote, state="disabled")
        self.btn_connect_quote.pack(side=tk.LEFT, padx=5)
        
        self.btn_subscribe_quote = ttk.Button(btn_frame, text="訂閱報價", command=self.subscribe_quote, state="disabled")
        self.btn_subscribe_quote.pack(side=tk.LEFT, padx=5)

        # 停止報價按鈕 (永遠可用)
        self.btn_stop_quote = ttk.Button(btn_frame, text="停止報價", command=self.stop_quote, state="normal")
        self.btn_stop_quote.pack(side=tk.LEFT, padx=5)



        # 下單測試按鈕
        self.btn_test_order = ttk.Button(btn_frame, text="測試下單", command=self.test_order, state="disabled")
        self.btn_test_order.pack(side=tk.LEFT, padx=5)

        # 重新連接回報按鈕
        self.btn_reconnect_reply = ttk.Button(btn_frame, text="重新連接回報", command=self.reconnect_reply)
        self.btn_reconnect_reply.pack(side=tk.LEFT, padx=5)

        # 🚨 Console模式：隱藏Queue控制面板
        # self.create_queue_control_panel(main_frame)

        # 📊 商品選擇面板
        self.create_product_selection_panel(main_frame)

        # 📊 狀態監控面板
        self.create_status_display_panel(main_frame)

        # 日誌區域
        log_frame = ttk.LabelFrame(main_frame, text="系統日誌", padding=10)
        log_frame.pack(fill=tk.BOTH, expand=True)
        
        # 建立滾動條
        scrollbar = ttk.Scrollbar(log_frame)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        self.text_log = tk.Text(log_frame, height=20, yscrollcommand=scrollbar.set)
        self.text_log.pack(fill=tk.BOTH, expand=True)
        scrollbar.config(command=self.text_log.yview)
        
        # 下單參數設定區域
        order_frame = ttk.LabelFrame(function_frame, text="下單參數", padding=5)
        order_frame.pack(fill=tk.X, pady=(10, 0))

        # 第一行：基本參數
        params_frame1 = ttk.Frame(order_frame)
        params_frame1.pack(fill=tk.X, pady=2)

        ttk.Label(params_frame1, text="帳號:").grid(row=0, column=0, sticky="w", padx=5)
        ttk.Label(params_frame1, text=self.config['FUTURES_ACCOUNT']).grid(row=0, column=1, sticky="w", padx=5)

        ttk.Label(params_frame1, text="商品:").grid(row=0, column=2, sticky="w", padx=5)
        self.entry_product = ttk.Entry(params_frame1, width=8)
        self.entry_product.insert(0, self.config['DEFAULT_PRODUCT'])
        self.entry_product.grid(row=0, column=3, sticky="w", padx=5)

        ttk.Label(params_frame1, text="價格:").grid(row=0, column=4, sticky="w", padx=5)
        self.entry_price = ttk.Entry(params_frame1, width=8)
        self.entry_price.insert(0, "22000")
        self.entry_price.grid(row=0, column=5, sticky="w", padx=5)

        ttk.Label(params_frame1, text="數量:").grid(row=0, column=6, sticky="w", padx=5)
        self.entry_quantity = ttk.Entry(params_frame1, width=5)
        self.entry_quantity.insert(0, "1")
        self.entry_quantity.grid(row=0, column=7, sticky="w", padx=5)

        # 第二行：交易參數
        params_frame2 = ttk.Frame(order_frame)
        params_frame2.pack(fill=tk.X, pady=2)

        ttk.Label(params_frame2, text="買賣:").grid(row=0, column=0, sticky="w", padx=5)
        self.combo_buysell = ttk.Combobox(params_frame2, values=["買進", "賣出"], width=6, state="readonly")
        self.combo_buysell.set("買進")
        self.combo_buysell.grid(row=0, column=1, sticky="w", padx=5)

        ttk.Label(params_frame2, text="委託類型:").grid(row=0, column=2, sticky="w", padx=5)
        self.combo_trade_type = ttk.Combobox(params_frame2, values=["ROD", "IOC", "FOK"], width=6, state="readonly")
        self.combo_trade_type.set("ROD")
        self.combo_trade_type.grid(row=0, column=3, sticky="w", padx=5)

        ttk.Label(params_frame2, text="當沖:").grid(row=0, column=4, sticky="w", padx=5)
        self.combo_day_trade = ttk.Combobox(params_frame2, values=["否", "是"], width=6, state="readonly")
        self.combo_day_trade.set("否")
        self.combo_day_trade.grid(row=0, column=5, sticky="w", padx=5)

        ttk.Label(params_frame2, text="新平倉:").grid(row=0, column=6, sticky="w", padx=5)
        self.combo_new_close = ttk.Combobox(params_frame2, values=["新倉", "平倉", "自動"], width=6, state="readonly")
        self.combo_new_close.set("新倉")
        self.combo_new_close.grid(row=0, column=7, sticky="w", padx=5)

        # 第三行：盤別參數
        params_frame3 = ttk.Frame(order_frame)
        params_frame3.pack(fill=tk.X, pady=2)

        ttk.Label(params_frame3, text="盤別:").grid(row=0, column=0, sticky="w", padx=5)
        self.combo_reserved = ttk.Combobox(params_frame3, values=["盤中", "T盤預約"], width=8, state="readonly")
        self.combo_reserved.set("盤中")
        self.combo_reserved.grid(row=0, column=1, sticky="w", padx=5)

        # 參數說明
        ttk.Label(params_frame3, text="💡 ROD=整日有效 IOC=立即成交否則取消 FOK=全部成交否則取消",
                 foreground="gray").grid(row=0, column=2, columnspan=6, sticky="w", padx=10)


    
    def register_reply_events(self):
        """註冊OnReplyMessage事件 - 解決2017警告"""
        try:
            import comtypes.client
            
            # 建立事件處理類別 (基於群益官方範例)
            class SKReplyLibEvent():
                def OnReplyMessage(self, bstrUserID, bstrMessages):
                    # 根據群益官方文件，必須回傳-1
                    return -1
            
            # 註冊事件 (使用群益官方方式)
            self.reply_event = SKReplyLibEvent()
            self.reply_handler = comtypes.client.GetEvents(Global.skR, self.reply_event)
            
            self.add_log("✅ OnReplyMessage事件註冊成功 (解決2017警告)")
            
        except Exception as e:
            self.add_log(f"⚠️ OnReplyMessage事件註冊失敗: {e}")

    def register_order_reply_events(self):
        """註冊下單回報事件 - 基於群益官方Reply.py"""
        try:
            import comtypes.client

            # 建立回報事件處理類別 (完全按照群益官方Reply.py)
            class SKReplyLibEvent():
                def __init__(self, parent):
                    self.parent = parent

                def OnConnect(self, btrUserID, nErrorCode):
                    """連線事件"""
                    if nErrorCode == 0:
                        msg = f"OnConnect: {btrUserID} Connected!"
                    else:
                        msg = f"OnConnect: {btrUserID} Connect Error!"
                    self.parent.add_log(msg)

                def OnDisconnect(self, btrUserID, nErrorCode):
                    """斷線事件"""
                    if nErrorCode == 3002:
                        msg = "OnDisconnect: 您已經斷線囉~~~"
                    else:
                        msg = f"OnDisconnect: {nErrorCode}"
                    self.parent.add_log(msg)

                def OnNewData(self, btrUserID, bstrData):
                    """即時委託狀態回報 - Console詳細版本"""
                    try:
                        cutData = bstrData.split(',')

                        # 🔧 強力過濾歷史回報：檢查是否為啟動後的新回報
                        if not self.parent._is_new_order_reply(bstrData):
                            # 靜默跳過，避免大量日誌
                            return

                        # 🚨 原始數據轉移到Console
                        print(f"📋 [REPLY] OnNewData: {cutData}")

                        # 解析重要欄位 (基於您提供的詳細解析)
                        if len(cutData) > 33:
                            # 基本信息
                            seq_no = cutData[0]           # 委託序號
                            market = cutData[1]           # 市場別 (TF=期貨)
                            order_type = cutData[2]       # 委託種類 (N=新單, C=成交, X=取消, R=錯誤)
                            status = cutData[3]           # 委託狀態

                            # 帳號信息
                            branch_code = cutData[4]      # 分公司代碼
                            account = cutData[5]          # 期貨帳號
                            buy_sell = cutData[6] if len(cutData) > 6 else ""  # 🔧 新增：買賣別/新平倉標識

                            # 商品信息
                            product = cutData[8]          # 商品代碼
                            book_no = cutData[10]         # 委託書號
                            price = cutData[11]           # 委託/成交價格
                            quantity = cutData[20]        # 委託/未成交數量

                            # 時間信息
                            date = cutData[23]            # 委託日期
                            time = cutData[24]            # 委託時間

                            # 成交信息 (修正欄位索引)
                            match_no = cutData[38] if len(cutData) > 38 else ""  # 成交序號 (正確欄位)
                            contract_month = cutData[33] if len(cutData) > 33 else ""  # 合約月份 (如202507)

                            # 錯誤信息
                            err_code = cutData[-4] if len(cutData) > 4 else ""   # 錯誤代碼
                            err_msg = cutData[-3] if len(cutData) > 3 else ""    # 錯誤訊息
                            original_seq = cutData[-1] if len(cutData) > 1 else ""  # 原始委託序號

                            # 🎯 Console詳細輸出 (完整委託類型對照表)
                            type_map = {
                                'N': '新單 (New)',
                                'D': '成交 (Deal/Done)',
                                'C': '取消 (Cancel)',
                                'U': '改量 (Update)',
                                'P': '改價 (Price)',
                                'B': '改價改量 (Both)',
                                'S': '動態退單 (System)',
                                'X': '刪除 (Delete)',
                                'R': '錯誤 (Reject)'
                            }
                            type_desc = type_map.get(order_type, f'未知({order_type})')

                            print(f"✅ [REPLY] 委託回報解析:")
                            print(f"   📋 序號: {seq_no} (原始: {original_seq})")
                            print(f"   📊 類型: {order_type} ({type_desc})")
                            print(f"   🏷️ 商品: {product}")
                            print(f"   💰 價格: {price}")
                            print(f"   📦 數量: {quantity}")
                            print(f"   ⏰ 時間: {date} {time}")
                            if buy_sell:
                                print(f"   🔄 買賣別: {buy_sell}")
                            if contract_month:
                                print(f"   📅 合約月份: {contract_month}")
                            if match_no:
                                print(f"   🎯 成交序號: {match_no}")
                            if err_code:
                                print(f"   ❌ 錯誤: {err_code} - {err_msg}")

                            # 🚨 UI日誌只顯示簡要信息 (完整類型支援)
                            if order_type == 'N':
                                self.parent.add_log(f"✅ 新單: {product} {price}@{quantity}")
                            elif order_type == 'D':
                                self.parent.add_log(f"🎯 成交: {product} {price}@{quantity}")
                            elif order_type == 'C':
                                self.parent.add_log(f"❌ 取消: {product} {price}@{quantity}")
                            elif order_type == 'U':
                                self.parent.add_log(f"📝 改量: {product} {price}@{quantity}")
                            elif order_type == 'P':
                                self.parent.add_log(f"💰 改價: {product} {price}@{quantity}")
                            elif order_type == 'B':
                                self.parent.add_log(f"🔄 改價改量: {product} {price}@{quantity}")
                            elif order_type == 'S':
                                self.parent.add_log(f"⚠️ 動態退單: {product}")
                            elif order_type == 'X':
                                self.parent.add_log(f"🗑️ 刪除: {product}")
                            elif order_type == 'R':
                                self.parent.add_log(f"❌ 錯誤: {err_msg}")
                            else:
                                self.parent.add_log(f"📋 回報: {order_type} - {type_desc}")

                            # 🔧 統一回報處理：避免重複處理，按優先級處理
                            processed = False

                            # 優先級1: 簡化追蹤器（最新的FIFO邏輯）
                            if hasattr(self.parent, 'multi_group_position_manager') and self.parent.multi_group_position_manager:
                                try:
                                    if hasattr(self.parent.multi_group_position_manager, 'simplified_tracker') and \
                                       self.parent.multi_group_position_manager.simplified_tracker:
                                        processed = self.parent.multi_group_position_manager.simplified_tracker.process_order_reply(bstrData)
                                        if processed:
                                            print(f"✅ [REPLY] 簡化追蹤器處理成功")
                                except Exception as tracker_error:
                                    print(f"❌ [REPLY] 簡化追蹤器處理失敗: {tracker_error}")

                            # 優先級2: 總量追蹤管理器（如果簡化追蹤器沒有處理）
                            if not processed and hasattr(self.parent, 'multi_group_position_manager') and self.parent.multi_group_position_manager:
                                try:
                                    if hasattr(self.parent.multi_group_position_manager, 'total_lot_manager') and \
                                       self.parent.multi_group_position_manager.total_lot_manager:
                                        processed = self.parent.multi_group_position_manager.total_lot_manager.process_order_reply(bstrData)
                                        if processed:
                                            print(f"✅ [REPLY] 總量追蹤管理器處理成功")
                                except Exception as tracker_error:
                                    print(f"❌ [REPLY] 總量追蹤管理器處理失敗: {tracker_error}")

                            # 優先級3: 統一追蹤器（向後相容）
                            if not processed and hasattr(self.parent, 'unified_order_tracker') and self.parent.unified_order_tracker:
                                try:
                                    self.parent.unified_order_tracker.process_real_order_reply(bstrData)
                                    print(f"✅ [REPLY] 統一追蹤器處理成功")
                                except Exception as tracker_error:
                                    print(f"❌ [REPLY] 統一追蹤器處理失敗: {tracker_error}")

                            # 🔧 移除：出場追價機制整合（已整合到簡化追蹤器）
                            # 所有回報處理現在統一由簡化追蹤器處理，包括進場和出場

                    except Exception as e:
                        print(f"❌ [REPLY] OnNewData處理錯誤: {e}")
                        self.parent.add_log(f"❌ 回報處理錯誤: {e}")

                def OnReplyMessage(self, bstrUserID, bstrMessages):
                    """回報訊息 - 必須回傳-1"""
                    self.parent.add_log(f"📋 OnReplyMessage: {bstrMessages}")
                    return -1

                def OnSmartData(self, btrUserID, bstrData):
                    """智慧單回報"""
                    cutData = bstrData.split(',')
                    self.parent.add_log(f"📋 OnSmartData: {cutData}")

            # 註冊事件 (使用群益官方方式)
            self.order_reply_event = SKReplyLibEvent(self)
            self.order_reply_handler = comtypes.client.GetEvents(Global.skR, self.order_reply_event)

            self.add_log("✅ 下單回報事件註冊成功 (群益官方方式)")

        except Exception as e:
            self.add_log(f"⚠️ 下單回報事件註冊失敗: {e}")

    def login(self):
        """登入系統"""
        try:
            user_id = self.entry_id.get().strip()
            password = self.entry_password.get().strip()
            
            if not user_id or not password:
                print("❌ [LOGIN] 請輸入身分證字號和密碼")
                self.add_log("❌ 請輸入身分證字號和密碼")
                return
            
            self.add_log("🔐 開始登入...")
            
            # 設定LOG路徑
            log_path = os.path.join(os.path.dirname(__file__), "CapitalLog_Simple")
            nCode = Global.skC.SKCenterLib_SetLogPath(log_path)
            self.add_log(f"📁 LOG路徑設定: {log_path}")
            
            # 執行登入 (使用群益官方方式)
            nCode = Global.skC.SKCenterLib_Login(user_id, password)
            msg = Global.skC.SKCenterLib_GetReturnCodeMessage(nCode)
            
            self.add_log(f"📋 登入結果: {msg} (代碼: {nCode})")
            
            if nCode == 0:
                # 登入成功
                self.logged_in = True
                Global.SetID(user_id)

                # 🔧 確保Global_IID已設定 (修復實單模式切換問題)
                if hasattr(Global, 'Global_IID'):
                    print(f"✅ [LOGIN] Global_IID已設定: {Global.Global_IID}")
                else:
                    print(f"⚠️ [LOGIN] Global_IID未設定，手動設定...")
                    Global.Global_IID = user_id
                    print(f"✅ [LOGIN] Global_IID已手動設定: {Global.Global_IID}")

                self.label_status.config(text="狀態: 已登入", foreground="green")
                self.btn_login.config(state="disabled")
                self.btn_init_order.config(state="normal")
                self.btn_connect_quote.config(state="normal")

                self.add_log("✅ 登入成功！")
                
            elif nCode == 2017:
                # 這個警告現在應該不會出現了
                self.add_log("⚠️ 收到2017警告，但OnReplyMessage已註冊，繼續執行...")

                self.logged_in = True
                Global.SetID(user_id)

                # 🔧 確保Global_IID已設定 (修復實單模式切換問題)
                if hasattr(Global, 'Global_IID'):
                    print(f"✅ [LOGIN] Global_IID已設定: {Global.Global_IID}")
                else:
                    print(f"⚠️ [LOGIN] Global_IID未設定，手動設定...")
                    Global.Global_IID = user_id
                    print(f"✅ [LOGIN] Global_IID已手動設定: {Global.Global_IID}")

                self.label_status.config(text="狀態: 已登入", foreground="green")
                self.btn_login.config(state="disabled")
                self.btn_init_order.config(state="normal")
                self.btn_connect_quote.config(state="normal")

                self.add_log("✅ 登入成功 (已處理警告)！")
                
            else:
                print(f"❌ [LOGIN] 登入失敗: {msg}")
                self.add_log(f"❌ 登入失敗: {msg}")

        except Exception as e:
            print(f"❌ [LOGIN] 登入錯誤: {e}")
            self.add_log(f"❌ 登入錯誤: {e}")
    
    def init_order(self):
        """初始化下單模組"""
        try:
            if not self.logged_in:
                self.add_log("❌ 請先登入系統")
                return
            
            # 🚨 詳細初始化信息轉移到Console
            print("🔧 [INIT] 初始化下單模組...")

            # 步驟1: 初始化SKOrderLib
            nCode = Global.skO.SKOrderLib_Initialize()
            msg = Global.skC.SKCenterLib_GetReturnCodeMessage(nCode)
            print(f"📋 [INIT] SKOrderLib初始化: {msg} (代碼: {nCode})")

            if nCode == 0 or nCode == 2003:  # 2003 = 已初始化
                # 步驟2: 讀取憑證
                user_id = self.entry_id.get().strip()
                nCode = Global.skO.ReadCertByID(user_id)
                msg = Global.skC.SKCenterLib_GetReturnCodeMessage(nCode)
                print(f"📋 [INIT] 憑證讀取: {msg} (代碼: {nCode})")

                if nCode == 0:
                    self.btn_init_order.config(state="disabled")
                    self.btn_test_order.config(state="normal")  # 啟用下單測試按鈕

                    # 初始化回報連線 (群益官方方式)
                    self.init_reply_connection()

                    # UI日誌只顯示簡要成功信息
                    self.add_log("✅ 下單模組初始化完成")
                    print("💡 [INIT] 現在可以測試下單功能")
                else:
                    print(f"❌ [INIT] 憑證讀取失敗: {msg}")
                    self.add_log(f"❌ 憑證讀取失敗: {msg}")
                    if nCode == 1001:
                        print("💡 [INIT] 提示: 可能需要向群益申請期貨API下單權限")
            else:
                self.add_log(f"❌ SKOrderLib初始化失敗: {msg}")
                
        except Exception as e:
            self.add_log(f"❌ 下單初始化錯誤: {e}")

    def init_reply_connection(self):
        """初始化回報連線 - 基於群益官方Reply.py"""
        try:
            self.add_log("🔗 初始化回報連線...")

            # 使用群益官方的回報連線方式
            user_id = self.entry_id.get().strip()
            nCode = Global.skR.SKReplyLib_ConnectByID(user_id)
            msg = Global.skC.SKCenterLib_GetReturnCodeMessage(nCode)
            self.add_log(f"📋 回報連線結果: {msg} (代碼: {nCode})")

            if nCode == 0:
                self.add_log("✅ 回報連線成功，可以接收委託回報")
            else:
                self.add_log(f"❌ 回報連線失敗: {msg}")

        except Exception as e:
            self.add_log(f"❌ 回報連線錯誤: {e}")

    def reconnect_reply(self):
        """重新連接回報 - 解決回報訊息消失問題"""
        try:
            self.add_log("🔄 重新連接回報...")

            # 重新初始化回報連線
            user_id = self.entry_id.get().strip()

            # 先斷開現有連線
            try:
                nCode = Global.skR.SKReplyLib_CloseByID(user_id)
                self.add_log(f"📋 關閉舊回報連線: {nCode}")
            except:
                pass

            # 重新連接
            nCode = Global.skR.SKReplyLib_ConnectByID(user_id)
            msg = Global.skC.SKCenterLib_GetReturnCodeMessage(nCode)
            self.add_log(f"📋 重新連接結果: {msg} (代碼: {nCode})")

            if nCode == 0:
                self.add_log("✅ 回報重新連接成功，現在可以接收委託回報")
            else:
                self.add_log(f"❌ 回報重新連接失敗: {msg}")

        except Exception as e:
            self.add_log(f"❌ 重新連接回報錯誤: {e}")

    def connect_quote(self):
        """連線報價服務"""
        try:
            if not self.logged_in:
                self.add_log("❌ 請先登入系統")
                return
            
            self.add_log("📡 連線報價服務...")
            
            # 使用群益官方報價連線方式
            nCode = Global.skQ.SKQuoteLib_EnterMonitorLONG()
            msg = Global.skC.SKCenterLib_GetReturnCodeMessage(nCode)
            self.add_log(f"📋 報價連線: {msg} (代碼: {nCode})")
            
            if nCode == 0:
                self.btn_connect_quote.config(state="disabled")
                self.btn_subscribe_quote.config(state="normal")
                self.add_log("✅ 報價服務連線成功")
            else:
                self.add_log(f"❌ 報價連線失敗: {msg}")
                
        except Exception as e:
            self.add_log(f"❌ 報價連線錯誤: {e}")
    
    def subscribe_quote(self):
        """訂閱MTX00報價"""
        try:
            product = self.config['DEFAULT_PRODUCT']
            self.add_log(f"📊 訂閱 {product} 報價...")

            # 註冊報價事件 (使用群益官方方式)
            self.register_quote_events()

            # 🔧 修復TypeError: 確保參數類型正確
            try:
                # 嘗試不同的參數類型
                result = Global.skQ.SKQuoteLib_RequestTicks(0, str(product))
            except Exception as e1:
                self.add_log(f"⚠️ 第一次嘗試失敗: {e1}")
                try:
                    # 嘗試整數參數
                    result = Global.skQ.SKQuoteLib_RequestTicks(0, 0)
                except Exception as e2:
                    self.add_log(f"⚠️ 第二次嘗試失敗: {e2}")
                    # 使用原始方式
                    result = Global.skQ.SKQuoteLib_RequestTicks(0, product)

            # 處理返回結果 (可能是tuple或單一值)
            if isinstance(result, tuple):
                nCode = result[0] if len(result) > 0 else -1
            else:
                nCode = result

            msg = Global.skC.SKCenterLib_GetReturnCodeMessage(nCode)
            self.add_log(f"📋 訂閱結果: {msg} (代碼: {nCode})")

            if nCode == 0:
                self.btn_subscribe_quote.config(state="disabled")
                self.add_log(f"✅ {product} 報價訂閱成功")
                self.add_log("💡 報價資料將顯示在下方日誌中")
                self.add_log("💡 可隨時點擊停止報價按鈕")
            else:
                self.add_log(f"❌ 報價訂閱失敗: {msg}")

        except Exception as e:
            self.add_log(f"❌ 報價訂閱錯誤: {e}")

    def stop_quote(self):
        """停止報價訂閱 - 使用OrderTester.py中成功的方法"""
        try:
            self.add_log("🛑 停止報價訂閱...")

            # 使用OrderTester.py中成功的停止方法：CancelRequestTicks
            product = self.config['DEFAULT_PRODUCT']
            self.add_log(f"📋 使用CancelRequestTicks停止{product}訂閱...")

            # 使用正確的取消訂閱API (只需要商品代號參數)
            nCode = Global.skQ.SKQuoteLib_CancelRequestTicks(product)
            msg = Global.skC.SKCenterLib_GetReturnCodeMessage(nCode)
            self.add_log(f"📋 CancelRequestTicks結果: {msg} (代碼: {nCode})")

            # 只更新訂閱按鈕狀態，停止按鈕保持可用
            self.btn_subscribe_quote.config(state="normal")  # 重新啟用訂閱按鈕

            if nCode == 0:
                self.add_log("✅ 報價訂閱已停止")
                self.add_log("💡 可重新訂閱報價或再次點擊停止確認")
            else:
                self.add_log("⚠️ 停止指令已發送，如報價仍更新可再次點擊停止")

        except Exception as e:
            self.add_log(f"❌ 停止報價錯誤: {e}")
            # 確保訂閱按鈕可用
            try:
                self.btn_subscribe_quote.config(state="normal")
                self.add_log("💡 可重新訂閱報價")
            except:
                pass



    def register_quote_events(self):
        """註冊報價事件 - 使用群益官方方式"""
        try:
            import comtypes.client

            # 建立事件處理類別 (完全按照群益官方方式)
            class SKQuoteLibEvents():
                def __init__(self, parent):
                    self.parent = parent

                def OnNotifyTicksLONG(self, sMarketNo, nStockidx, nPtr, lDate, lTimehms, lTimemillismicros, nBid, nAsk, nClose, nQty, nSimulate):
                    """簡化版報價事件 - Console輸出為主 + 停損監控整合"""
                    try:
                        # 解析價格資訊
                        corrected_price = nClose / 100.0
                        bid = nBid / 100.0
                        ask = nAsk / 100.0

                        # 格式化時間
                        time_str = f"{lTimehms:06d}"
                        formatted_time = f"{time_str[:2]}:{time_str[2:4]}:{time_str[4:6]}"

                        # 🛡️ 停損監控整合 - 在價格更新時檢查停損觸發
                        if hasattr(self.parent, 'stop_loss_monitor') and self.parent.stop_loss_monitor:
                            try:
                                triggered_stops = self.parent.stop_loss_monitor.monitor_stop_loss_breach(
                                    corrected_price, formatted_time
                                )
                                # 觸發的停損會自動通過回調函數處理
                            except Exception as e:
                                # 靜默處理停損監控錯誤，不影響報價流程
                                if hasattr(self.parent, 'console_enabled') and self.parent.console_enabled:
                                    print(f"[PRICE_UPDATE] ⚠️ 停損監控錯誤: {e}")

                        # 🎯 平倉機制系統整合 - 使用統一管理器處理所有平倉邏輯
                        if hasattr(self.parent, 'exit_mechanism_manager') and self.parent.exit_mechanism_manager:
                            try:
                                # 使用統一管理器處理價格更新
                                results = self.parent.exit_mechanism_manager.process_price_update(
                                    corrected_price, formatted_time
                                )

                                # 可選：記錄處理結果 (靜默模式，避免過多輸出)
                                if results and 'error' not in results:
                                    total_events = sum(results.values())
                                    if total_events > 0 and hasattr(self.parent, 'console_enabled') and self.parent.console_enabled:
                                        print(f"[PRICE_UPDATE] 📊 平倉事件: {total_events} 個")

                            except Exception as e:
                                # 靜默處理平倉機制錯誤，不影響報價流程
                                if hasattr(self.parent, 'console_enabled') and self.parent.console_enabled:
                                    print(f"[PRICE_UPDATE] ⚠️ 平倉機制系統錯誤: {e}")

                        # 🔄 回退模式 - 如果統一管理器不可用，使用分散組件
                        elif hasattr(self.parent, 'trailing_stop_system_enabled') and self.parent.trailing_stop_system_enabled:
                            try:
                                # 檢查移動停利啟動
                                if hasattr(self.parent, 'trailing_stop_activator') and self.parent.trailing_stop_activator:
                                    self.parent.trailing_stop_activator.check_trailing_stop_activation(
                                        corrected_price, formatted_time
                                    )

                                # 更新峰值價格
                                if hasattr(self.parent, 'peak_price_tracker') and self.parent.peak_price_tracker:
                                    self.parent.peak_price_tracker.update_peak_prices(
                                        corrected_price, formatted_time
                                    )

                                # 監控回撤觸發
                                if hasattr(self.parent, 'drawdown_monitor') and self.parent.drawdown_monitor:
                                    self.parent.drawdown_monitor.monitor_drawdown_triggers(
                                        corrected_price, formatted_time
                                    )

                            except Exception as e:
                                # 靜默處理移動停利錯誤，不影響報價流程
                                if hasattr(self.parent, 'console_enabled') and self.parent.console_enabled:
                                    print(f"[PRICE_UPDATE] ⚠️ 移動停利系統錯誤: {e}")

                        # 🎯 多組策略價格更新整合
                        if hasattr(self.parent, 'multi_group_position_manager') and self.parent.multi_group_position_manager:
                            try:
                                # 通知多組策略系統價格更新
                                self.parent.multi_group_position_manager.update_current_price(corrected_price, formatted_time)
                            except Exception as e:
                                # 靜默處理多組策略錯誤
                                if hasattr(self.parent, 'console_enabled') and self.parent.console_enabled:
                                    print(f"[PRICE_UPDATE] ⚠️ 多組策略價格更新錯誤: {e}")

                        # ✅ 可控制的Console輸出 - 增強版包含五檔信息
                        if getattr(self.parent, 'console_quote_enabled', True):
                            # 基本TICK信息
                            tick_msg = f"[TICK] {formatted_time} 成交:{corrected_price:.0f} 買:{bid:.0f} 賣:{ask:.0f} 量:{nQty}"

                            # 如果有五檔數據，添加最佳買賣價
                            if hasattr(self.parent, 'best5_data') and self.parent.best5_data:
                                best5 = self.parent.best5_data
                                tick_msg += f" | 最佳買:{best5['bid1']:.0f}({best5['bid1_qty']}) 最佳賣:{best5['ask1']:.0f}({best5['ask1_qty']})"

                            print(tick_msg)

                        # 🚨 移除UI日誌輸出，完全使用Console模式
                        # self.parent.write_message_direct(strMsg)
                        # self.parent.write_message_direct(price_msg)

                        # 🎯 策略邏輯整合
                        if hasattr(self.parent, 'strategy_enabled') and self.parent.strategy_enabled:
                            self.parent.process_strategy_logic_safe(corrected_price, formatted_time)

                        # ✅ 更新內部數據變數（Monitor依賴這些）
                        self.parent.last_price = corrected_price
                        self.parent.last_update_time = formatted_time

                        # ✅ 更新報價計數器（Monitor檢測用）
                        if hasattr(self.parent, 'price_count'):
                            self.parent.price_count += 1

                        # 🔧 移除時間操作，避免GIL風險
                        # self.parent.last_quote_time = time.time()  # 已移除

                    except Exception as e:
                        # Console錯誤輸出
                        print(f"❌ [ERROR] 報價處理錯誤: {e}")

                    return 0

                def OnNotifyBest5LONG(self, sMarketNo, nStockidx, nBestBid1, nBestBidQty1, nBestBid2, nBestBidQty2, nBestBid3, nBestBidQty3, nBestBid4, nBestBidQty4, nBestBid5, nBestBidQty5, nExtendBid, nExtendBidQty, nBestAsk1, nBestAskQty1, nBestAsk2, nBestAskQty2, nBestAsk3, nBestAskQty3, nBestAsk4, nBestAskQty4, nBestAsk5, nBestAskQty5, nExtendAsk, nExtendAskQty, nSimulate):
                    """五檔報價事件 - Console版本"""
                    try:
                        # 控制五檔輸出頻率，避免過多信息
                        if not hasattr(self.parent, '_last_best5_time'):
                            self.parent._last_best5_time = 0

                        current_time = time.time()
                        if current_time - self.parent._last_best5_time > 2:  # 每2秒輸出一次
                            self.parent._last_best5_time = current_time

                            # 可控制的Console輸出
                            if getattr(self.parent, 'console_quote_enabled', True):
                                # 轉換價格 (群益API價格需要除以100)
                                bid1 = nBestBid1 / 100.0 if nBestBid1 > 0 else 0
                                bid2 = nBestBid2 / 100.0 if nBestBid2 > 0 else 0
                                bid3 = nBestBid3 / 100.0 if nBestBid3 > 0 else 0
                                bid4 = nBestBid4 / 100.0 if nBestBid4 > 0 else 0
                                bid5 = nBestBid5 / 100.0 if nBestBid5 > 0 else 0

                                ask1 = nBestAsk1 / 100.0 if nBestAsk1 > 0 else 0
                                ask2 = nBestAsk2 / 100.0 if nBestAsk2 > 0 else 0
                                ask3 = nBestAsk3 / 100.0 if nBestAsk3 > 0 else 0
                                ask4 = nBestAsk4 / 100.0 if nBestAsk4 > 0 else 0
                                ask5 = nBestAsk5 / 100.0 if nBestAsk5 > 0 else 0

                                print(f"📊 [BEST5] 五檔報價:")
                                print(f"   賣5: {ask5:.0f}({nBestAskQty5})  賣4: {ask4:.0f}({nBestAskQty4})  賣3: {ask3:.0f}({nBestAskQty3})  賣2: {ask2:.0f}({nBestAskQty2})  賣1: {ask1:.0f}({nBestAskQty1})")
                                print(f"   買1: {bid1:.0f}({nBestBidQty1})  買2: {bid2:.0f}({nBestBidQty2})  買3: {bid3:.0f}({nBestBidQty3})  買4: {bid4:.0f}({nBestBidQty4})  買5: {bid5:.0f}({nBestBidQty5})")

                            # ✅ 更新五檔報價計數器（Monitor檢測用）
                            if hasattr(self.parent, 'best5_count'):
                                self.parent.best5_count += 1

                            # 🔧 移除時間操作，避免GIL風險
                            # self.parent.last_quote_time = current_time  # 已移除

                            # 🎯 為策略保存五檔數據
                            self.parent.best5_data = {
                                'bid1': nBestBid1 / 100.0 if nBestBid1 > 0 else 0,
                                'bid1_qty': nBestBidQty1,
                                'ask1': nBestAsk1 / 100.0 if nBestAsk1 > 0 else 0,
                                'ask1_qty': nBestAskQty1,
                                'bid_prices': [nBestBid1/100.0, nBestBid2/100.0, nBestBid3/100.0, nBestBid4/100.0, nBestBid5/100.0],
                                'bid_qtys': [nBestBidQty1, nBestBidQty2, nBestBidQty3, nBestBidQty4, nBestBidQty5],
                                'ask_prices': [nBestAsk1/100.0, nBestAsk2/100.0, nBestAsk3/100.0, nBestAsk4/100.0, nBestAsk5/100.0],
                                'ask_qtys': [nBestAskQty1, nBestAskQty2, nBestAskQty3, nBestAskQty4, nBestAskQty5],
                                'timestamp': current_time
                            }

                            # 🚀 實際下單系統：更新即時報價管理器
                            if hasattr(self.parent, 'real_time_quote_manager') and self.parent.real_time_quote_manager:
                                try:
                                    # 🎯 Stage2 商品監控整合：自動識別當前監控商品
                                    product_code = self.parent.get_current_monitoring_product()

                                    # 更新五檔數據到實際下單系統
                                    self.parent.real_time_quote_manager.update_best5_data(
                                        market_no=sMarketNo,
                                        stock_idx=nStockidx,
                                        ask1=nBestAsk1/100.0, ask1_qty=nBestAskQty1,
                                        ask2=nBestAsk2/100.0, ask2_qty=nBestAskQty2,
                                        ask3=nBestAsk3/100.0, ask3_qty=nBestAskQty3,
                                        ask4=nBestAsk4/100.0, ask4_qty=nBestAskQty4,
                                        ask5=nBestAsk5/100.0, ask5_qty=nBestAskQty5,
                                        bid1=nBestBid1/100.0, bid1_qty=nBestBidQty1,
                                        bid2=nBestBid2/100.0, bid2_qty=nBestBidQty2,
                                        bid3=nBestBid3/100.0, bid3_qty=nBestBidQty3,
                                        bid4=nBestBid4/100.0, bid4_qty=nBestBidQty4,
                                        bid5=nBestBid5/100.0, bid5_qty=nBestBidQty5,
                                        product_code=product_code
                                    )

                                    # 🔄 移除UI更新，避免GIL問題
                                    # UI更新會在背景線程中引起GIL錯誤，已移除

                                except Exception as e:
                                    # 靜默處理，不影響原有功能
                                    pass

                    except Exception as e:
                        print(f"❌ [BEST5] 五檔處理錯誤: {e}")

                    return 0

            # 註冊事件 (使用群益官方方式)
            self.quote_event = SKQuoteLibEvents(self)
            self.quote_handler = comtypes.client.GetEvents(Global.skQ, self.quote_event)

            self.add_log("✅ 報價事件註冊成功 (群益官方方式)")

        except Exception as e:
            self.add_log(f"⚠️ 報價事件註冊失敗: {e}")

    def write_message_direct(self, message):
        """直接寫入訊息 - 完全按照群益官方方式"""
        try:
            # 完全按照群益官方的WriteMessage方式
            self.text_log.insert('end', message + '\n')
            self.text_log.see('end')
        except Exception as e:
            # 如果連這個都失敗，就忽略 (群益官方沒有錯誤處理)
            pass

    def test_order(self):
        """測試下單功能"""
        try:
            # 取得下單參數
            product = self.entry_product.get().strip()
            price = self.entry_price.get().strip()
            quantity = self.entry_quantity.get().strip()
            account = self.config['FUTURES_ACCOUNT']

            # 取得交易參數
            buysell = self.combo_buysell.get()
            trade_type = self.combo_trade_type.get()
            day_trade = self.combo_day_trade.get()
            new_close = self.combo_new_close.get()
            reserved = self.combo_reserved.get()

            if not product or not price or not quantity:
                print("❌ [ORDER] 請填入完整的下單參數")
                self.add_log("❌ 請填入完整的下單參數")
                return

            # 🚨 詳細下單信息轉移到Console
            print(f"🧪 [ORDER] 準備測試下單...")
            print(f"📋 [ORDER] 帳號: {account}")
            print(f"📋 [ORDER] 商品: {product}")
            print(f"📋 [ORDER] 買賣: {buysell}")
            print(f"📋 [ORDER] 價格: {price}")
            print(f"📋 [ORDER] 數量: {quantity}口")
            print(f"📋 [ORDER] 委託類型: {trade_type}")
            print(f"📋 [ORDER] 當沖: {day_trade}")
            print(f"📋 [ORDER] 新平倉: {new_close}")
            print(f"📋 [ORDER] 盤別: {reserved}")

            # Console輸出下單資訊
            print("🧪 [ORDER] 準備執行測試下單")
            print(f"📊 [ORDER] 帳號: {account}")
            print(f"📊 [ORDER] 商品: {product}")
            print(f"📊 [ORDER] 買賣: {buysell}")
            print(f"📊 [ORDER] 價格: {price}")
            print(f"📊 [ORDER] 數量: {quantity}口")
            print(f"📊 [ORDER] 委託類型: {trade_type}")
            print(f"📊 [ORDER] 當沖: {day_trade}")
            print(f"📊 [ORDER] 新平倉: {new_close}")
            print(f"⚡ [ORDER] 執行真實下單...")

            # UI日誌只顯示簡要信息
            self.add_log(f"🧪 執行下單: {buysell} {product} {price}@{quantity}口")

            # 執行下單 (使用群益官方方式)
            order_params = {
                'product': product,
                'price': price,
                'quantity': quantity,
                'account': account,
                'buysell': buysell,
                'trade_type': trade_type,
                'day_trade': day_trade,
                'new_close': new_close,
                'reserved': reserved
            }
            self.place_future_order(order_params)

        except Exception as e:
            self.add_log(f"❌ 下單測試錯誤: {e}")

    def place_future_order(self, order_params):
        """執行期貨下單 - 基於群益官方方式"""
        try:
            buysell = order_params['buysell']
            print(f"🚀 [ORDER] 執行{buysell}下單...")

            # 檢查Global模組中的期貨下單功能
            if hasattr(Global, 'skO') and Global.skO:
                # 使用群益官方的下單方式
                user_id = self.entry_id.get().strip()

                # 建立下單物件 (參考群益官方FutureOrder.py)
                import comtypes.gen.SKCOMLib as sk
                oOrder = sk.FUTUREORDER()

                # 設定基本參數
                oOrder.bstrFullAccount = order_params['account']
                oOrder.bstrStockNo = order_params['product']
                oOrder.sBuySell = 0 if order_params['buysell'] == "買進" else 1
                oOrder.bstrPrice = order_params['price']
                oOrder.nQty = int(order_params['quantity'])

                # 設定委託類型
                trade_type_map = {"ROD": 0, "IOC": 1, "FOK": 2}
                oOrder.sTradeType = trade_type_map.get(order_params['trade_type'], 0)

                # 設定當沖
                oOrder.sDayTrade = 1 if order_params['day_trade'] == "是" else 0

                # 設定新平倉
                new_close_map = {"新倉": 0, "平倉": 1, "自動": 2}
                oOrder.sNewClose = new_close_map.get(order_params['new_close'], 0)

                # 設定盤別
                oOrder.sReserved = 1 if order_params['reserved'] == "T盤預約" else 0

                print(f"📋 [ORDER] 下單物件設定完成")

                # 執行下單
                result = Global.skO.SendFutureOrderCLR(user_id, True, oOrder)

                # 處理下單結果
                if isinstance(result, tuple) and len(result) >= 2:
                    message, nCode = result[0], result[1]
                    msg = Global.skC.SKCenterLib_GetReturnCodeMessage(nCode)

                    if nCode == 0:
                        print(f"✅ [ORDER] 下單成功: {msg}")
                        print(f"📋 [ORDER] 委託序號: {message}")
                        # UI日誌只顯示簡要成功信息
                        self.add_log(f"✅ 下單成功，序號: {message}")
                    else:
                        print(f"❌ [ORDER] 下單失敗: {msg} (代碼: {nCode})")
                        # UI日誌顯示失敗信息
                        self.add_log(f"❌ 下單失敗: {msg}")
                else:
                    print(f"📋 [ORDER] 下單結果: {result}")
                    self.add_log(f"📋 下單結果: {result}")

            else:
                print("❌ [ORDER] 下單物件未初始化")
                self.add_log("❌ 下單物件未初始化")

        except Exception as e:
            self.add_log(f"❌ 下單執行錯誤: {e}")
            import traceback
            self.add_log(f"📋 錯誤詳情: {traceback.format_exc()}")
    


    def create_strategy_page(self, strategy_frame):
        """建立策略監控頁面"""
        # 創建策略頁面的Notebook
        strategy_notebook = ttk.Notebook(strategy_frame)
        strategy_notebook.pack(fill="both", expand=True, padx=5, pady=5)

        # 原有策略監控頁面
        original_strategy_frame = ttk.Frame(strategy_notebook)
        strategy_notebook.add(original_strategy_frame, text="📊 原有策略監控")

        # 策略監控面板
        self.create_strategy_panel(original_strategy_frame)
        # 策略日誌區域
        self.create_strategy_log_area(original_strategy_frame)

        # 多組策略配置頁面
        if self.multi_group_enabled:
            multi_group_frame = ttk.Frame(strategy_notebook)
            strategy_notebook.add(multi_group_frame, text="🎯 多組策略配置")
            self.create_multi_group_strategy_page(multi_group_frame)

    def create_strategy_panel(self, parent_frame):
        """創建策略監控面板 - 簡化版，避免頻繁UI更新"""
        try:
            # 策略控制框架
            strategy_frame = ttk.LabelFrame(parent_frame, text="🎯 開盤區間突破策略監控", padding=10)
            strategy_frame.pack(fill="x", pady=(10, 0))

            # 第一行：策略控制按鈕
            control_row = ttk.Frame(strategy_frame)
            control_row.pack(fill="x", pady=(0, 5))

            self.btn_start_strategy = ttk.Button(control_row, text="🚀 啟動策略監控",
                                              command=self.start_strategy)
            self.btn_start_strategy.pack(side="left", padx=5)

            self.btn_stop_strategy = ttk.Button(control_row, text="🛑 停止策略監控",
                                             command=self.stop_strategy, state="disabled")
            self.btn_stop_strategy.pack(side="left", padx=5)

            # 策略狀態顯示（靜態，不頻繁更新）
            ttk.Label(control_row, text="狀態:").pack(side="left", padx=(20, 5))
            self.strategy_status_var = tk.StringVar(value="策略未啟動")
            ttk.Label(control_row, textvariable=self.strategy_status_var, foreground="blue").pack(side="left", padx=5)

            # 收盤平倉控制
            self.single_strategy_eod_close_var = tk.BooleanVar(value=False)  # 預設關閉
            eod_check = tk.Checkbutton(
                control_row,
                text="🕐 收盤平倉 (13:30)",
                variable=self.single_strategy_eod_close_var,
                command=self.toggle_single_strategy_eod_close
            )
            eod_check.pack(side="left", padx=(20, 5))

            # 第二行：區間設定
            range_row = ttk.Frame(strategy_frame)
            range_row.pack(fill="x", pady=5)

            # 區間時間設定
            ttk.Label(range_row, text="監控區間:").pack(side="left", padx=5)
            self.range_time_var = tk.StringVar(value="08:46-08:48")
            ttk.Label(range_row, textvariable=self.range_time_var,
                     font=("Arial", 10, "bold"), foreground="purple").pack(side="left", padx=5)

            # 手動設定區間時間
            ttk.Label(range_row, text="設定開始時間:").pack(side="left", padx=(20, 2))
            self.entry_range_time = ttk.Entry(range_row, width=8)
            self.entry_range_time.insert(0, "08:46")
            self.entry_range_time.pack(side="left", padx=2)

            ttk.Button(range_row, text="套用", command=self.apply_range_time).pack(side="left", padx=2)

            # 第三行：區間結果顯示（只在計算完成時更新）
            result_row = ttk.Frame(strategy_frame)
            result_row.pack(fill="x", pady=5)

            ttk.Label(result_row, text="區間結果:").pack(side="left", padx=5)
            self.range_result_var = tk.StringVar(value="等待計算")
            ttk.Label(result_row, textvariable=self.range_result_var, foreground="green").pack(side="left", padx=5)

            # 第四行：突破和部位狀態（只在狀態變化時更新）
            status_row = ttk.Frame(strategy_frame)
            status_row.pack(fill="x", pady=5)

            ttk.Label(status_row, text="突破狀態:").pack(side="left", padx=5)
            self.breakout_status_var = tk.StringVar(value="等待突破")
            ttk.Label(status_row, textvariable=self.breakout_status_var, foreground="orange").pack(side="left", padx=5)

            ttk.Label(status_row, text="部位:").pack(side="left", padx=(20, 5))
            self.position_status_var = tk.StringVar(value="無部位")
            ttk.Label(status_row, textvariable=self.position_status_var, foreground="purple").pack(side="left", padx=5)

            # 第五行：統計資訊（不頻繁更新）
            stats_row = ttk.Frame(strategy_frame)
            stats_row.pack(fill="x", pady=5)

            ttk.Label(stats_row, text="接收報價:").pack(side="left", padx=5)
            self.price_count_var = tk.StringVar(value="0")
            ttk.Label(stats_row, textvariable=self.price_count_var, foreground="gray").pack(side="left", padx=5)

            ttk.Button(stats_row, text="📊 查看策略狀態", command=self.show_strategy_status).pack(side="left", padx=(20, 5))

            # 🚀 Stage2 虛實單切換控制整合
            if hasattr(self, 'virtual_real_system_enabled') and self.virtual_real_system_enabled:
                try:
                    # 初始化UI控制器 (如果還沒有的話)
                    if not hasattr(self, 'order_mode_ui_controller') or not self.order_mode_ui_controller:
                        self.order_mode_ui_controller = OrderModeUIController(
                            parent_frame=strategy_frame,
                            order_manager=self.virtual_real_order_manager
                        )

                        # 添加模式變更回調
                        self.order_mode_ui_controller.add_mode_change_callback(self.on_order_mode_changed)

                        print("[UI_CONTROLLER] ✅ 虛實單切換UI控制器已整合到策略面板")

                except Exception as ui_error:
                    print(f"[UI_CONTROLLER] ❌ UI控制器整合失敗: {ui_error}")

            self.add_log("✅ 策略監控面板創建完成（安全模式）")

        except Exception as e:
            self.add_log(f"❌ 策略面板創建失敗: {e}")

    def on_order_mode_changed(self, is_real_mode: bool):
        """虛實單模式變更回調"""
        try:
            mode_desc = "實單" if is_real_mode else "虛擬"
            print(f"[ORDER_MODE] 🔄 策略系統收到模式變更通知: {mode_desc}模式")

            # 更新策略日誌
            self.add_strategy_log(f"🔄 下單模式切換: {mode_desc}模式")

            # 如果有報價管理器，刷新商品資訊
            if hasattr(self, 'order_mode_ui_controller') and self.order_mode_ui_controller:
                self.order_mode_ui_controller.refresh_product_info()

        except Exception as e:
            print(f"[ORDER_MODE] ❌ 模式變更回調失敗: {e}")

    def get_current_monitoring_product(self) -> str:
        """
        取得當前監控商品代碼

        Returns:
            str: 商品代碼 (MTX00/TM0000)
        """
        try:
            # 從商品選擇下拉選單取得
            if hasattr(self, 'product_var') and self.product_var:
                selected_product = self.product_var.get()
                if selected_product in ['MTX00', 'TM0000']:
                    return selected_product

            # 從配置取得
            if hasattr(self, 'config') and self.config:
                config_product = self.config.get('DEFAULT_PRODUCT', 'MTX00')
                if config_product in ['MTX00', 'TM0000']:
                    return config_product

            # 預設返回MTX00
            return "MTX00"

        except Exception as e:
            print(f"[PRODUCT] ❌ 取得當前監控商品失敗: {e}")
            return "MTX00"

    def create_multi_group_strategy_page(self, parent_frame):
        """創建多組策略配置頁面"""
        try:
            # 多組策略配置面板
            def on_config_change(config):
                """配置變更回調"""
                if self.multi_group_position_manager:
                    self.multi_group_position_manager.strategy_config = config
                    if self.multi_group_logger:
                        self.multi_group_logger.config_change(
                            f"配置更新: {config.total_groups}組×{config.lots_per_group}口"
                        )

            self.multi_group_config_panel = MultiGroupConfigPanel(
                parent_frame,
                on_config_change=on_config_change
            )

            # 多組策略控制區域
            control_frame = ttk.LabelFrame(parent_frame, text="🎮 多組策略控制")
            control_frame.pack(fill="x", padx=5, pady=5)

            # 控制按鈕行
            button_row = tk.Frame(control_frame)
            button_row.pack(fill="x", padx=5, pady=5)

            # 多組策略準備按鈕
            self.btn_prepare_multi_group = ttk.Button(
                button_row,
                text="📋 準備多組策略",
                command=self.prepare_multi_group_strategy
            )
            self.btn_prepare_multi_group.pack(side="left", padx=5)

            # 多組策略手動啟動按鈕
            self.btn_start_multi_group = ttk.Button(
                button_row,
                text="🚀 手動啟動",
                command=self.manual_start_multi_group_strategy,
                state="disabled"
            )
            self.btn_start_multi_group.pack(side="left", padx=5)

            # 多組策略停止按鈕
            self.btn_stop_multi_group = ttk.Button(
                button_row,
                text="🛑 停止策略",
                command=self.stop_multi_group_strategy,
                state="disabled"
            )
            self.btn_stop_multi_group.pack(side="left", padx=5)

            # 自動啟動選項
            self.auto_start_var = tk.BooleanVar(value=True)
            auto_start_check = tk.Checkbutton(
                button_row,
                text="🤖 區間完成後自動啟動",
                variable=self.auto_start_var,
                command=self.toggle_auto_start
            )
            auto_start_check.pack(side="left", padx=10)

            # 執行頻率控制
            freq_frame = tk.Frame(button_row)
            freq_frame.pack(side="left", padx=20)

            tk.Label(freq_frame, text="執行頻率:", font=("Arial", 9)).pack(side="left", padx=5)
            self.multi_group_frequency_var = tk.StringVar(value="一天一次")
            freq_combo = ttk.Combobox(
                freq_frame,
                textvariable=self.multi_group_frequency_var,
                values=["一天一次", "可重複執行", "測試模式"],
                state="readonly",
                width=10,
                font=("Arial", 9)
            )
            freq_combo.pack(side="left", padx=5)
            freq_combo.bind("<<ComboboxSelected>>", self.on_multi_group_frequency_changed)

            # 收盤平倉控制
            eod_frame = tk.Frame(button_row)
            eod_frame.pack(side="left", padx=20)

            self.multi_group_eod_close_var = tk.BooleanVar(value=False)  # 預設關閉
            eod_check = tk.Checkbutton(
                eod_frame,
                text="🕐 收盤平倉 (13:30)",
                variable=self.multi_group_eod_close_var,
                command=self.toggle_multi_group_eod_close
            )
            eod_check.pack(side="left", padx=5)

            # 狀態顯示行
            status_row = tk.Frame(control_frame)
            status_row.pack(fill="x", padx=5, pady=5)

            tk.Label(status_row, text="策略狀態:", font=("Arial", 9, "bold")).pack(side="left")

            self.multi_group_status_label = tk.Label(
                status_row,
                text="⏸️ 未準備",
                fg="gray"
            )
            self.multi_group_status_label.pack(side="left", padx=10)

            # 詳細狀態顯示
            self.multi_group_detail_label = tk.Label(
                status_row,
                text="請先配置策略參數",
                fg="blue",
                font=("Arial", 8)
            )
            self.multi_group_detail_label.pack(side="left", padx=10)

            # Console控制區域
            console_frame = ttk.LabelFrame(parent_frame, text="🎛️ Console輸出控制")
            console_frame.pack(fill="x", padx=5, pady=5)

            console_row = tk.Frame(console_frame)
            console_row.pack(fill="x", padx=5, pady=5)

            # Console控制按鈕
            categories = [
                ("策略", LogCategory.STRATEGY),
                ("部位", LogCategory.POSITION),
                ("風險", LogCategory.RISK),
                ("配置", LogCategory.CONFIG),
                ("系統", LogCategory.SYSTEM)
            ]

            for name, category in categories:
                btn = ttk.Button(
                    console_row,
                    text=f"🔇 關閉{name}",
                    command=lambda cat=category, n=name: self.toggle_multi_group_console(cat, n)
                )
                btn.pack(side="left", padx=2)

            print("✅ 多組策略配置頁面創建完成")

        except Exception as e:
            print(f"❌ 多組策略頁面創建失敗: {e}")
            if self.multi_group_logger:
                self.multi_group_logger.system_error(f"頁面創建失敗: {e}")

    def create_strategy_log_area(self, parent_frame):
        """創建策略日誌區域"""
        try:
            # 策略日誌框架
            log_frame = ttk.LabelFrame(parent_frame, text="📋 策略監控日誌", padding=5)
            log_frame.pack(fill="both", expand=True, pady=(10, 0))

            # 策略日誌文字框
            self.text_strategy_log = tk.Text(log_frame, height=12, wrap=tk.WORD,
                                           font=("Consolas", 9), bg="#f8f9fa")

            # 滾動條
            scrollbar_strategy = ttk.Scrollbar(log_frame, orient="vertical",
                                             command=self.text_strategy_log.yview)
            self.text_strategy_log.configure(yscrollcommand=scrollbar_strategy.set)

            # 佈局
            self.text_strategy_log.pack(side="left", fill="both", expand=True)
            scrollbar_strategy.pack(side="right", fill="y")

            # 初始化訊息
            self.add_strategy_log("📋 策略監控日誌系統已初始化")

        except Exception as e:
            self.add_log(f"❌ 策略日誌區域創建失敗: {e}")

    def add_strategy_log(self, message):
        """策略日誌 - Console化版本，避免UI更新造成GIL問題"""
        try:
            # 添加時間戳
            timestamp = time.strftime("%H:%M:%S")
            formatted_message = f"[{timestamp}] {message}"

            # 🎯 可控制的策略Console輸出（主要）
            if getattr(self, 'console_strategy_enabled', True):
                print(f"[STRATEGY] {formatted_message}")

            # 🚨 完全移除UI更新，避免GIL風險
            # 策略日誌完全使用Console模式

        except Exception as e:
            # 靜默處理，不影響策略邏輯
            pass

    def process_strategy_logic_safe(self, price, time_str):
        """安全的策略邏輯處理 - 避免頻繁UI更新"""
        try:
            # 🔍 可控制的策略Console輸出 - 增強版包含時間對比
            if getattr(self, 'console_strategy_enabled', True):
                if price == 0:
                    print(f"⚠️ 策略收到0價格數據，時間: {time_str}")
                elif self.price_count % 50 == 0:  # 每50筆報價顯示一次
                    # 🕐 添加系統時間對比
                    import datetime
                    current_time = datetime.datetime.now().strftime("%H:%M:%S")

                    # 計算時間差異（簡化版）
                    try:
                        api_hour, api_min, api_sec = map(int, time_str.split(':'))
                        sys_hour, sys_min, sys_sec = map(int, current_time.split(':'))

                        api_total_sec = api_hour * 3600 + api_min * 60 + api_sec
                        sys_total_sec = sys_hour * 3600 + sys_min * 60 + sys_sec
                        time_diff = sys_total_sec - api_total_sec

                        # 處理跨日情況（簡化處理）
                        if time_diff > 43200:  # 12小時以上，可能是跨日
                            time_diff -= 86400
                        elif time_diff < -43200:
                            time_diff += 86400

                        print(f"🔍 策略收到: price={price}, api_time={time_str}, sys_time={current_time}, diff={time_diff}s, count={self.price_count}")

                        # 🚨 延遲警告
                        if abs(time_diff) > 30:  # 超過30秒
                            print(f"⚠️ 時間差異警告: {time_diff}秒 (API時間 vs 系統時間)")

                    except Exception as e:
                        # 時間計算錯誤時回退到原始格式
                        print(f"🔍 策略收到: price={price}, api_time={time_str}, sys_time={current_time}, count={self.price_count}")
                        print(f"⚠️ 時間差異計算錯誤: {e}")

            # 🔧 簡化統計更新，避免複雜時間操作 (僅在監控啟用時)
            if getattr(self, 'monitoring_enabled', True):
                self.monitoring_stats['strategy_activity_count'] += 1
                # self.monitoring_stats['last_strategy_activity'] = time.time()  # 已移除

            # 只更新內部變數，不更新UI
            self.latest_price = price
            self.latest_time = time_str
            self.price_count += 1

            # 移除UI更新，避免GIL問題
            # UI更新會在背景線程中引起GIL錯誤，改用Console輸出
            if self.price_count % 1000 == 0:  # 每1000筆報價輸出一次統計
                print(f"📊 [STRATEGY] 報價統計: {self.price_count}筆")

            # 解析時間
            hour, minute, second = map(int, time_str.split(':'))

            # 區間計算邏輯
            self.update_range_calculation_safe(price, time_str)

            # 更新分鐘K線數據（用於突破檢測）
            if self.range_calculated:
                self.update_minute_candle_safe(price, hour, minute, second)

            # 🔧 修正：空單即時檢測 + 多單1分K檢測
            if self.range_calculated and not self.first_breakout_detected:
                # 🚀 新增：即時空單進場檢測（不等1分K收盤）
                self.check_immediate_short_entry_safe(price, time_str)

                # 原有：1分K多單檢測（只檢測多單）
                if not self.first_breakout_detected:  # 確保空單沒有先觸發
                    self.check_minute_candle_breakout_safe()

            # 執行進場（檢測到突破信號後的下一個報價）
            if self.range_calculated and self.waiting_for_entry:
                self.check_breakout_signals_safe(price, time_str)

            # 出場條件檢查（有部位時）
            if self.current_position:
                self.check_exit_conditions_safe(price, time_str)

            # 🎯 多組策略風險管理檢查
            if self.multi_group_enabled and self.multi_group_risk_engine:
                self.check_multi_group_exit_conditions(price, time_str)
            elif self.console_enabled:
                # 🔍 DEBUG: 風險管理引擎狀態檢查 (每100次輸出一次)
                if not hasattr(self, '_risk_engine_debug_count'):
                    self._risk_engine_debug_count = 0
                self._risk_engine_debug_count += 1

                if self._risk_engine_debug_count % 100 == 0:
                    print(f"[RISK_DEBUG] 風險管理引擎狀態檢查:")
                    print(f"[RISK_DEBUG]   multi_group_enabled: {getattr(self, 'multi_group_enabled', 'None')}")
                    print(f"[RISK_DEBUG]   multi_group_risk_engine: {getattr(self, 'multi_group_risk_engine', 'None')}")
                    print(f"[RISK_DEBUG]   檢查次數: {self._risk_engine_debug_count}")

        except Exception as e:
            # 靜默處理錯誤，避免影響報價處理
            pass

    def update_range_calculation_safe(self, price, time_str):
        """安全的區間計算 - 只在關鍵時刻更新UI"""
        try:
            # 檢查是否在區間時間內
            if self.is_in_range_time_safe(time_str):
                if not self.in_range_period:
                    # 開始收集區間數據
                    self.in_range_period = True
                    self.range_prices = []
                    self._range_start_time = time_str
                    # 重要事件：記錄到策略日誌
                    self.add_strategy_log(f"📊 開始收集區間數據: {time_str}")

                # 收集價格數據
                self.range_prices.append(price)

            elif self.in_range_period and not self.range_calculated:
                # 區間結束，計算高低點
                if self.range_prices:
                    self.range_high = max(self.range_prices)
                    self.range_low = min(self.range_prices)
                    self.range_calculated = True
                    self.in_range_period = False

                    # 移除UI更新，改用Console輸出
                    range_text = f"高:{self.range_high:.0f} 低:{self.range_low:.0f} 大小:{self.range_high-self.range_low:.0f}"
                    print(f"✅ [STRATEGY] 區間計算完成: {range_text}")
                    # UI更新會在背景線程中引起GIL錯誤，已移除

                    # 重要事件：記錄到策略日誌
                    self.add_strategy_log(f"✅ 區間計算完成: {range_text}")
                    self.add_strategy_log(f"📊 收集數據點數: {len(self.range_prices)} 筆，開始監測突破")

                    # 🎯 檢查是否需要自動啟動多組策略（防重複觸發）
                    if not self._auto_start_triggered:
                        self.check_auto_start_multi_group_strategy()

        except Exception as e:
            pass

    def is_in_range_time_safe(self, time_str):
        """安全的時間檢查 - 精確2分鐘區間"""
        try:
            hour, minute, second = map(int, time_str.split(':'))
            current_total_seconds = hour * 3600 + minute * 60 + second
            start_total_seconds = self.range_start_hour * 3600 + self.range_start_minute * 60
            end_total_seconds = start_total_seconds + 120  # 精確2分鐘

            return start_total_seconds <= current_total_seconds < end_total_seconds
        except:
            return False

    def update_minute_candle_safe(self, price, hour, minute, second):
        """更新分鐘K線數據 - 參考OrderTester.py邏輯"""
        try:
            current_minute = minute

            # 如果是新的分鐘，處理上一分鐘的K線
            if self.last_minute is not None and current_minute != self.last_minute:
                if self.minute_prices:
                    # 計算上一分鐘的K線
                    open_price = self.minute_prices[0]
                    close_price = self.minute_prices[-1]
                    high_price = max(self.minute_prices)
                    low_price = min(self.minute_prices)

                    self.current_minute_candle = {
                        'minute': self.last_minute,
                        'open': open_price,
                        'high': high_price,
                        'low': low_price,
                        'close': close_price,
                        'start_time': f"{hour:02d}:{self.last_minute:02d}:00"
                    }

                # 重置當前分鐘的價格數據
                self.minute_prices = []

            # 添加當前價格到分鐘數據
            self.minute_prices.append(price)
            self.last_minute = current_minute

        except Exception as e:
            pass

    def check_immediate_short_entry_safe(self, price, time_str):
        """
        即時空單進場檢測 - 不等1分K收盤
        空單在下跌過程中只要碰到區間就立即進場
        """
        try:
            if not self.range_high or not self.range_low:
                return

            # 如果已經檢測到第一次突破，就不再檢測
            if self.first_breakout_detected:
                return

            # 🚀 空單即時檢測：任何報價跌破區間下緣就立即觸發
            if price < self.range_low:
                # 記錄第一次突破
                self.first_breakout_detected = True
                self.breakout_direction = 'SHORT'
                self.waiting_for_entry = True

                # 重要事件：記錄到策略日誌
                self.add_strategy_log(f"🔥 即時空單觸發！報價:{price:.0f} < 下緣:{self.range_low:.0f}")
                self.add_strategy_log(f"⚡ 立即進場做空（不等1分K收盤）...")

                # Console輸出
                print(f"🔥 [STRATEGY] SHORT突破信號已觸發（即時）")

        except Exception as e:
            pass

    def check_minute_candle_breakout_safe(self):
        """
        檢查分鐘K線收盤價是否突破區間 - 修正版本
        🔧 現在只檢測多單（空單已改為即時檢測）
        """
        try:
            if not self.current_minute_candle or not self.range_high or not self.range_low:
                return

            # 如果已經檢測到第一次突破，就不再檢測
            if self.first_breakout_detected:
                return

            close_price = self.current_minute_candle['close']
            minute = self.current_minute_candle['minute']

            # 🔧 修正：只檢查多單突破（空單已改為即時檢測）
            if close_price > self.range_high:
                # 記錄第一次突破
                self.first_breakout_detected = True
                self.breakout_direction = 'LONG'
                self.waiting_for_entry = True

                # 重要事件：記錄到策略日誌
                self.add_strategy_log(f"🔥 {minute:02d}分K線收盤突破上緣！收盤:{close_price:.0f} > 上緣:{self.range_high:.0f}")
                self.add_strategy_log(f"⏳ 等待下一個報價進場做多...")

                # Console輸出
                print(f"🔥 [STRATEGY] LONG突破信號已觸發")

            # 🚀 移除空單檢測邏輯（已改為即時檢測）
            # elif close_price < self.range_low: 已移除

        except Exception as e:
            pass

    def check_breakout_signals_safe(self, price, time_str):
        """執行進場 - 在檢測到突破信號後的下一個報價進場"""
        try:
            # 如果等待進場且有突破方向
            if self.waiting_for_entry and self.breakout_direction and not self.current_position:
                direction = self.breakout_direction
                self.waiting_for_entry = False  # 重置等待狀態

                # 🎯 多組策略進場邏輯
                if self.multi_group_enabled and self.multi_group_running and self.multi_group_position_manager:
                    self.execute_multi_group_entry(direction, price, time_str)
                else:
                    # 單一策略進場邏輯
                    self.enter_position_safe(direction, price, time_str)

        except Exception as e:
            pass

    def execute_multi_group_entry(self, direction, price, time_str):
        """執行多組策略進場"""
        try:
            # 🎯 檢查是否為監控準備狀態（需要先創建策略組）
            if hasattr(self, 'multi_group_monitoring_ready') and self.multi_group_monitoring_ready:
                # 根據實際突破方向創建策略組
                self.create_multi_group_strategy_with_direction(direction, time_str)
                self.multi_group_monitoring_ready = False  # 重置監控準備狀態

            # 獲取所有等待中的策略組
            active_groups = self.multi_group_position_manager.strategy_config.get_active_groups()
            from multi_group_config import GroupStatus
            waiting_groups = [g for g in active_groups if g.status == GroupStatus.WAITING]

            if not waiting_groups:
                print("⚠️ [MULTI_GROUP] 沒有等待中的策略組")
                return

            print(f"🎯 [MULTI_GROUP] 開始執行 {len(waiting_groups)} 組進場")

            # 逐組執行進場
            success_count = 0
            for group_config in waiting_groups:
                # 查找對應的資料庫組ID
                group_db_id = self._find_group_db_id(group_config.group_id)
                if group_db_id:
                    success = self.multi_group_position_manager.execute_group_entry(
                        group_db_id=group_db_id,
                        actual_price=price,
                        actual_time=time_str
                    )

                    if success:
                        success_count += 1
                        print(f"✅ [MULTI_GROUP] 組別 {group_config.group_id} 進場成功")

                        # 🔧 新增：下單成功後立即啟用回報處理
                        if hasattr(self, 'enable_order_reply_processing'):
                            self.enable_order_reply_processing()

                        # 🔧 修復：execute_group_entry() 已經執行了下單，不需要重複執行
                        # self._execute_multi_group_orders(group_config, direction, price)  # ← 移除重複下單
                    else:
                        print(f"❌ [MULTI_GROUP] 組別 {group_config.group_id} 進場失敗")
                else:
                    print(f"❌ [MULTI_GROUP] 找不到組別 {group_config.group_id} 的資料庫ID")

            print(f"🎯 [MULTI_GROUP] 進場完成: {success_count}/{len(waiting_groups)} 組成功")

            if self.multi_group_logger:
                self.multi_group_logger.strategy_info(f"多組進場執行: {success_count}/{len(waiting_groups)} 組成功")

        except Exception as e:
            print(f"❌ [MULTI_GROUP] 多組進場執行失敗: {e}")
            if self.multi_group_logger:
                self.multi_group_logger.system_error(f"多組進場執行失敗: {e}")

    def _find_group_db_id(self, group_id):
        """查找組別的資料庫ID"""
        try:
            # 獲取今日策略組
            today_groups = self.multi_group_position_manager.db_manager.get_today_strategy_groups()
            for group in today_groups:
                if group['group_id'] == group_id:
                    return group['id']
            return None
        except Exception as e:
            print(f"❌ [MULTI_GROUP] 查找組別DB ID失敗: {e}")
            return None

    def _execute_multi_group_orders(self, group_config, direction, price):
        """執行多組策略的實際下單"""
        try:
            # 為該組的每口執行下單
            for lot_rule in group_config.lot_rules:
                if hasattr(self, 'virtual_real_order_manager') and self.virtual_real_order_manager:
                    # 🎯 執行下單 - 明確指定1口，避免數量混亂
                    order_result = self.virtual_real_order_manager.execute_strategy_order(
                        direction=direction,
                        quantity=1,  # 🔧 強制每筆1口FOK
                        signal_source=f"multi_group_lot_{lot_rule.lot_id}"
                    )

                    if order_result.success:
                        mode_desc = "實單" if order_result.mode == "real" else "虛擬"
                        print(f"🚀 [MULTI_GROUP] 組別{group_config.group_id} 第{lot_rule.lot_id}口 {mode_desc}下單成功 - ID:{order_result.order_id}")

                        # 註冊到統一回報追蹤器
                        if hasattr(self, 'unified_order_tracker') and self.unified_order_tracker:
                            current_product = self.virtual_real_order_manager.get_current_product()
                            if current_product:
                                ask1_price = self.virtual_real_order_manager.get_ask1_price(current_product)

                                # 處理API序號
                                api_seq_no = None
                                if order_result.mode == "real" and order_result.api_result:
                                    if isinstance(order_result.api_result, tuple) and len(order_result.api_result) >= 1:
                                        api_seq_no = str(order_result.api_result[0])  # 只取第一個元素
                                    else:
                                        api_seq_no = str(order_result.api_result)

                                self.unified_order_tracker.register_order(
                                    order_id=order_result.order_id,
                                    product=current_product,
                                    direction=direction,
                                    quantity=1,  # 🔧 多組策略每筆都是1口
                                    price=ask1_price or price,
                                    is_virtual=(order_result.mode == "virtual"),
                                    signal_source=f"multi_group_G{group_config.group_id}_L{lot_rule.lot_id}",
                                    api_seq_no=api_seq_no
                                )
                    else:
                        print(f"❌ [MULTI_GROUP] 組別{group_config.group_id} 第{lot_rule.lot_id}口下單失敗: {order_result.error}")
                else:
                    print(f"💡 [MULTI_GROUP] 組別{group_config.group_id} 第{lot_rule.lot_id}口策略信號 (未啟用下單系統)")

        except Exception as e:
            print(f"❌ [MULTI_GROUP] 多組下單執行失敗: {e}")

    def create_multi_group_strategy_with_direction(self, direction, time_str):
        """根據實際突破方向創建策略組"""
        try:
            print(f"🎯 [MULTI_GROUP] 根據突破方向創建策略組: {direction}")

            # 創建進場信號
            group_ids = self.multi_group_position_manager.create_entry_signal(
                direction=direction,  # 🎯 使用實際突破方向
                signal_time=time_str,
                range_high=self.range_high,
                range_low=self.range_low
            )

            if group_ids:
                # 移除動態UI更新，改為Console輸出
                # self.multi_group_status_label.config(text="🎯 運行中", fg="green")
                # self.multi_group_detail_label.config(text=f"已創建{len(group_ids)}個{direction}策略組", fg="green")

                if self.multi_group_logger:
                    self.multi_group_logger.strategy_info(
                        f"多組策略啟動: {len(group_ids)}組 {direction}, 區間{self.range_low}-{self.range_high}"
                    )

                print(f"✅ [MULTI_GROUP] 已創建 {len(group_ids)} 個{direction}策略組")
                self.add_log(f"✅ 多組策略已啟動: {len(group_ids)}組 {direction}")

                return True
            else:
                print("❌ [MULTI_GROUP] 創建策略組失敗")
                return False

        except Exception as e:
            print(f"❌ [MULTI_GROUP] 創建策略組失敗: {e}")
            if self.multi_group_logger:
                self.multi_group_logger.system_error(f"創建策略組失敗: {e}")
            return False

    def enter_position_safe(self, direction, price, time_str):
        """安全的建倉處理 - 只在建倉時更新UI"""
        try:
            # 重要事件：記錄到策略日誌
            self.add_strategy_log(f"🚀 {direction} 突破進場 @{price:.0f} 時間:{time_str}")

            # 記錄部位資訊
            self.current_position = {
                'direction': direction,
                'entry_price': price,
                'entry_time': time_str,
                'quantity': 1,
                'peak_price': price,  # 峰值價格追蹤
                'trailing_activated': False,  # 移動停利是否啟動
                'trailing_activation_points': 15,  # 15點啟動移動停利
                'trailing_pullback_percent': 0.20  # 20%回撤
            }

            # 標記已檢測到第一次突破
            self.first_breakout_detected = True

            # 移除UI更新，避免GIL問題
            print(f"✅ [STRATEGY] {direction}突破進場 @{price:.0f}")
            # UI更新會在背景線程中引起GIL錯誤，已移除

            # 🚀 Stage2 虛實單整合下單邏輯 - 多筆1口策略
            if hasattr(self, 'virtual_real_order_manager') and self.virtual_real_order_manager:
                try:
                    # 🎯 取得策略配置的總口數
                    total_lots = self.virtual_real_order_manager.get_strategy_quantity()

                    # 🔧 執行多筆1口下單（統一採用多筆1口策略）
                    success_count = 0
                    for lot_id in range(1, total_lots + 1):
                        order_result = self.virtual_real_order_manager.execute_strategy_order(
                            direction=direction,
                            quantity=1,  # 🎯 強制每筆1口FOK
                            signal_source=f"single_strategy_lot_{lot_id}"
                        )

                        if order_result.success:
                            success_count += 1
                            mode_desc = "實單" if order_result.mode == "real" else "虛擬"
                            print(f"🚀 [STRATEGY] 第{lot_id}口 {mode_desc}下單成功 - ID:{order_result.order_id}")

                            # 註冊到統一回報追蹤器
                            if hasattr(self, 'unified_order_tracker') and self.unified_order_tracker:
                                current_product = self.virtual_real_order_manager.get_current_product()
                                if current_product:
                                    ask1_price = self.virtual_real_order_manager.get_ask1_price(current_product)

                                    # 處理API序號
                                    api_seq_no = None
                                    if order_result.mode == "real" and order_result.api_result:
                                        api_seq_no = str(order_result.api_result)

                                    self.unified_order_tracker.register_order(
                                        order_id=order_result.order_id,
                                        product=current_product,
                                        direction=direction,
                                        quantity=1,  # 🎯 每筆都是1口
                                        price=ask1_price or price,
                                        is_virtual=(order_result.mode == "virtual"),
                                        signal_source=f"single_strategy_lot_{lot_id}",
                                        api_seq_no=api_seq_no
                                    )
                        else:
                            print(f"❌ [STRATEGY] 第{lot_id}口下單失敗: {order_result.error}")

                    # 更新策略日誌
                    if success_count > 0:
                        self.add_strategy_log(f"🚀 {direction} 下單完成: {success_count}/{total_lots} 口成功")

                        # 🔧 新增：下單成功後立即啟用回報處理
                        if hasattr(self, 'enable_order_reply_processing'):
                            self.enable_order_reply_processing()
                    else:
                        self.add_strategy_log(f"❌ {direction} 下單失敗: 所有口數都失敗")

                except Exception as order_error:
                    self.add_strategy_log(f"❌ 下單系統錯誤: {order_error}")
            else:
                # 原有邏輯：僅記錄，不實際下單
                self.add_strategy_log(f"💡 {direction} 策略信號 (未啟用下單系統)")

        except Exception as e:
            self.add_strategy_log(f"❌ 建倉失敗: {e}")

    def check_exit_conditions_safe(self, price, time_str):
        """安全的出場檢查 - 包含移動停利和收盤平倉"""
        try:
            if not self.current_position:
                return

            direction = self.current_position['direction']
            entry_price = self.current_position['entry_price']

            # 🕐 檢查收盤平倉 (13:30) - 受控制開關影響
            if hasattr(self, 'single_strategy_eod_close_var') and self.single_strategy_eod_close_var.get():
                hour, minute, second = map(int, time_str.split(':'))
                if hour >= 13 and minute >= 30:
                    self.exit_position_safe(price, time_str, "收盤平倉")
                    return

            # 🛡️ 檢查初始停損 (區間邊界)
            if direction == "LONG" and price <= self.range_low:
                self.exit_position_safe(price, time_str, f"初始停損 {self.range_low:.0f}")
                return
            elif direction == "SHORT" and price >= self.range_high:
                self.exit_position_safe(price, time_str, f"初始停損 {self.range_high:.0f}")
                return

            # 🎯 移動停利邏輯
            self.check_trailing_stop_logic(price, time_str)

        except Exception as e:
            pass

    def check_trailing_stop_logic(self, price, time_str):
        """移動停利邏輯檢查"""
        try:
            if not self.current_position:
                return

            direction = self.current_position['direction']
            entry_price = self.current_position['entry_price']
            peak_price = self.current_position['peak_price']
            trailing_activated = self.current_position['trailing_activated']
            activation_points = self.current_position['trailing_activation_points']
            pullback_percent = self.current_position['trailing_pullback_percent']

            # 更新峰值價格
            if direction == "LONG":
                if price > peak_price:
                    self.current_position['peak_price'] = price
                    peak_price = price
            else:  # SHORT
                if price < peak_price:
                    self.current_position['peak_price'] = price
                    peak_price = price

            # 檢查移動停利啟動條件
            if not trailing_activated:
                activation_triggered = False

                if direction == "LONG":
                    activation_triggered = price >= entry_price + activation_points
                else:  # SHORT
                    activation_triggered = price <= entry_price - activation_points

                if activation_triggered:
                    self.current_position['trailing_activated'] = True
                    self.add_strategy_log(f"🔔 移動停利已啟動！峰值價格: {peak_price:.0f}")
                    return

            # 如果移動停利已啟動，檢查回撤出場條件
            if trailing_activated:
                if direction == "LONG":
                    total_gain = peak_price - entry_price
                    pullback_amount = total_gain * pullback_percent
                    trailing_stop_price = peak_price - pullback_amount

                    if price <= trailing_stop_price:
                        pnl = trailing_stop_price - entry_price
                        self.exit_position_safe(trailing_stop_price, time_str,
                                              f"移動停利 (峰值:{peak_price:.0f} 回撤:{pullback_amount:.1f}點)")
                        return

                else:  # SHORT
                    total_gain = entry_price - peak_price
                    pullback_amount = total_gain * pullback_percent
                    trailing_stop_price = peak_price + pullback_amount

                    if price >= trailing_stop_price:
                        pnl = entry_price - trailing_stop_price
                        self.exit_position_safe(trailing_stop_price, time_str,
                                              f"移動停利 (峰值:{peak_price:.0f} 回撤:{pullback_amount:.1f}點)")
                        return

        except Exception as e:
            pass

    def exit_position_safe(self, price, time_str, reason):
        """安全的出場處理 - 包含完整損益計算"""
        try:
            if not self.current_position:
                return

            direction = self.current_position['direction']
            entry_price = self.current_position['entry_price']
            entry_time = self.current_position['entry_time']

            # 計算損益
            pnl = (price - entry_price) if direction == "LONG" else (entry_price - price)
            pnl_money = pnl * 50  # 每點50元

            # 計算持倉時間
            try:
                entry_h, entry_m, entry_s = map(int, entry_time.split(':'))
                exit_h, exit_m, exit_s = map(int, time_str.split(':'))
                entry_seconds = entry_h * 3600 + entry_m * 60 + entry_s
                exit_seconds = exit_h * 3600 + exit_m * 60 + exit_s
                hold_seconds = exit_seconds - entry_seconds
                hold_minutes = hold_seconds // 60
            except:
                hold_minutes = 0

            # 重要事件：記錄到策略日誌
            self.add_strategy_log(f"🔚 {direction} 出場 @{price:.0f} 原因:{reason}")
            self.add_strategy_log(f"📊 損益:{pnl:+.0f}點 ({pnl_money:+.0f}元) 持倉:{hold_minutes}分鐘")

            # 清除部位
            self.current_position = None

            # 移除UI更新，避免GIL問題
            print(f"📊 [STRATEGY] 部位狀態: 無部位")
            # UI更新會在背景線程中引起GIL錯誤，已移除

        except Exception as e:
            self.add_strategy_log(f"❌ 出場處理錯誤: {e}")

    def start_strategy(self):
        """啟動策略監控"""
        try:
            self.strategy_enabled = True
            self.strategy_monitoring = True

            # 🚀 自動啟用多組策略的單組模式 (啟用動態追價)
            if self.multi_group_enabled and not self.multi_group_running:
                print("[STRATEGY] 🎯 自動啟用多組策略單組模式 (含動態追價)")
                self.multi_group_running = True
                self.multi_group_monitoring_ready = True

            # 重置策略狀態
            self.range_calculated = False
            self.first_breakout_detected = False
            self.current_position = None
            self.price_count = 0

            # 更新UI
            self.btn_start_strategy.config(state="disabled")
            self.btn_stop_strategy.config(state="normal")
            self.strategy_status_var.set("✅ 監控中")
            self.range_result_var.set("等待區間")
            self.breakout_status_var.set("等待突破")
            self.position_status_var.set("無部位")
            self.price_count_var.set("0")

            # 初始化策略監控統計 (僅在監控啟用時)
            if getattr(self, 'monitoring_enabled', True):
                self.monitoring_stats['strategy_activity_count'] = 0
                self.monitoring_stats['last_strategy_activity'] = time.time()
                self.monitoring_stats['strategy_status'] = '策略運行中'

            # 重要事件：記錄到策略日誌
            self.add_strategy_log("🚀 策略監控已啟動（Console模式）")
            self.add_strategy_log(f"📊 監控區間: {self.range_time_var.get()}")
            self.add_strategy_log("💡 策略監控已完全Console化，避免GIL問題")

        except Exception as e:
            self.add_strategy_log(f"❌ 策略啟動失敗: {e}")

    def stop_strategy(self):
        """停止策略監控"""
        try:
            self.strategy_enabled = False
            self.strategy_monitoring = False

            # 🚀 同時停止多組策略
            if self.multi_group_running:
                print("[STRATEGY] 🛑 同時停止多組策略")
                self.multi_group_running = False
                self.multi_group_monitoring_ready = False

            # 更新UI
            self.btn_start_strategy.config(state="normal")
            self.btn_stop_strategy.config(state="disabled")
            self.strategy_status_var.set("⏹️ 已停止")

            # 更新策略監控統計 (僅在監控啟用時)
            if getattr(self, 'monitoring_enabled', True):
                self.monitoring_stats['strategy_status'] = '已停止'

            # 重要事件：記錄到策略日誌
            self.add_strategy_log("🛑 策略監控已停止")

        except Exception as e:
            self.add_strategy_log(f"❌ 策略停止失敗: {e}")

    def apply_range_time(self):
        """套用區間時間設定"""
        try:
            time_input = self.entry_range_time.get().strip()

            # 解析時間格式 HH:MM
            if ':' in time_input:
                hour, minute = map(int, time_input.split(':'))
            else:
                self.add_log("❌ 時間格式錯誤，請使用 HH:MM 格式")
                return

            # 設定區間開始時間
            self.range_start_hour = hour
            self.range_start_minute = minute

            # 計算結束時間（+2分鐘）
            end_minute = minute + 2
            end_hour = hour
            if end_minute >= 60:
                end_minute -= 60
                end_hour += 1

            # 更新顯示
            range_display = f"{hour:02d}:{minute:02d}-{end_hour:02d}:{end_minute:02d}"
            self.range_time_var.set(range_display)

            # 重置區間數據
            self.range_calculated = False
            self.in_range_period = False
            self.range_prices = []

            # 重要事件：記錄到策略日誌
            self.add_strategy_log(f"✅ 區間時間已設定: {range_display}")

        except ValueError:
            self.add_strategy_log("❌ 時間格式錯誤，請使用 HH:MM 格式")
        except Exception as e:
            self.add_strategy_log(f"❌ 套用區間時間失敗: {e}")

    def show_strategy_status(self):
        """顯示詳細策略狀態"""
        try:
            status_info = f"""
策略監控狀態報告
==================
監控狀態: {'啟動' if self.strategy_enabled else '停止'}
接收報價: {self.price_count} 筆
最新價格: {self.latest_price:.0f} ({self.latest_time})

區間計算:
- 監控時間: {self.range_time_var.get()}
- 計算狀態: {'已完成' if self.range_calculated else '等待中'}
- 區間高點: {self.range_high:.0f if self.range_calculated else '--'}
- 區間低點: {self.range_low:.0f if self.range_calculated else '--'}
- 數據點數: {len(self.range_prices)}

突破狀態:
- 突破檢測: {'已觸發' if self.first_breakout_detected else '等待中'}
- 當前部位: {self.current_position['direction'] + ' @' + str(self.current_position['entry_price']) if self.current_position else '無部位'}
            """

            # 改用Console輸出策略狀態
            print("📊 [STRATEGY] 策略狀態報告:")
            print(status_info)
            self.add_log("📊 策略狀態已輸出到Console")

        except Exception as e:
            self.add_strategy_log(f"❌ 顯示狀態失敗: {e}")

    def add_log(self, message):
        """添加日誌"""
        timestamp = time.strftime("%H:%M:%S")
        self.text_log.insert(tk.END, f"[{timestamp}] {message}\n")
        self.text_log.see(tk.END)
        self.root.update_idletasks()

    def create_queue_control_panel(self, parent_frame):
        """創建Queue架構控制面板"""
        if not QUEUE_INFRASTRUCTURE_AVAILABLE:
            return

        # Queue控制框架
        queue_frame = ttk.LabelFrame(parent_frame, text="🚀 Queue架構控制", padding=5)
        queue_frame.pack(fill="x", pady=5)

        # 狀態顯示
        self.queue_status_var = tk.StringVar(value="⏸️ 已初始化")
        ttk.Label(queue_frame, text="狀態:").pack(side="left")
        ttk.Label(queue_frame, textvariable=self.queue_status_var).pack(side="left", padx=5)

        # 控制按鈕
        ttk.Button(queue_frame, text="🚀 啟動Queue服務",
                  command=self.start_queue_services).pack(side="left", padx=2)
        ttk.Button(queue_frame, text="🛑 停止Queue服務",
                  command=self.stop_queue_services).pack(side="left", padx=2)
        ttk.Button(queue_frame, text="📊 查看狀態",
                  command=self.show_queue_status).pack(side="left", padx=2)
        ttk.Button(queue_frame, text="🔄 切換模式",
                  command=self.toggle_queue_mode).pack(side="left", padx=2)

    def start_queue_services(self):
        """啟動Queue基礎設施服務"""
        if not self.queue_infrastructure:
            self.add_log("❌ Queue基礎設施未初始化")
            return

        try:
            # 初始化並啟動
            if self.queue_infrastructure.initialize():
                if self.queue_infrastructure.start_all():
                    # 🔧 修復後重新啟用策略回調 (已解決線程安全問題)
                    self.queue_infrastructure.add_strategy_callback(
                        self.process_queue_strategy_data
                    )

                    self.queue_mode_enabled = True
                    self.queue_status_var.set("✅ 運行中")
                    self.add_log("🚀 Queue服務啟動成功")
                    self.add_log("✅ 策略回調已啟用 (線程安全版本)")
                else:
                    self.add_log("❌ Queue服務啟動失敗")
            else:
                self.add_log("❌ Queue基礎設施初始化失敗")
        except Exception as e:
            self.add_log(f"❌ 啟動Queue服務錯誤: {e}")

    def stop_queue_services(self):
        """停止Queue基礎設施服務"""
        try:
            if self.queue_infrastructure:
                self.queue_infrastructure.stop_all()

            self.queue_mode_enabled = False
            self.queue_status_var.set("⏸️ 已停止")
            self.add_log("🛑 Queue服務已停止")
        except Exception as e:
            self.add_log(f"❌ 停止Queue服務錯誤: {e}")

    def toggle_queue_mode(self):
        """切換Queue模式"""
        if self.queue_mode_enabled:
            self.queue_mode_enabled = False
            self.queue_status_var.set("🔄 傳統模式")
            self.add_log("🔄 已切換到傳統模式")
        else:
            if self.queue_infrastructure and self.queue_infrastructure.running:
                self.queue_mode_enabled = True
                self.queue_status_var.set("✅ Queue模式")
                self.add_log("🚀 已切換到Queue模式")
            else:
                self.add_log("⚠️ 請先啟動Queue服務")

    def show_queue_status(self):
        """顯示Queue狀態"""
        if not self.queue_infrastructure:
            self.add_log("❌ Queue基礎設施未初始化")
            return

        try:
            # 顯示基本狀態
            self.add_log("📊 Queue狀態:")
            self.add_log(f"   - 初始化狀態: {'✅' if self.queue_infrastructure.initialized else '❌'}")
            self.add_log(f"   - 運行狀態: {'✅' if self.queue_infrastructure.running else '❌'}")
            self.add_log(f"   - Queue模式: {'✅' if self.queue_mode_enabled else '❌'}")

            # 嘗試獲取Queue管理器統計
            if hasattr(self.queue_infrastructure, 'queue_manager') and self.queue_infrastructure.queue_manager:
                stats = self.queue_infrastructure.queue_manager.stats
                self.add_log(f"   - Tick接收: {stats.get('tick_received', 0)}")
                self.add_log(f"   - Tick處理: {stats.get('tick_processed', 0)}")
                self.add_log(f"   - 佇列錯誤: {stats.get('queue_full_errors', 0)}")
                self.add_log(f"   - 處理錯誤: {stats.get('processing_errors', 0)}")
        except Exception as e:
            self.add_log(f"❌ 獲取Queue狀態錯誤: {e}")

    def process_queue_strategy_data(self, tick_data_dict):
        """處理來自Queue的策略數據"""
        try:
            # 從Queue數據中提取價格和時間
            price = tick_data_dict.get('corrected_close', 0)
            formatted_time = tick_data_dict.get('formatted_time', '')

            # 調用現有的策略邏輯 (格式完全相同)
            if hasattr(self, 'strategy_enabled') and self.strategy_enabled:
                self.process_strategy_logic_safe(price, formatted_time)

        except Exception as e:
            # 靜默處理錯誤，不影響Queue處理
            pass

    def create_status_display_panel(self, parent_frame):
        """創建狀態顯示面板 - Console版本，避免動態UI更新"""
        status_frame = ttk.LabelFrame(parent_frame, text="📊 Console控制面板", padding=5)
        status_frame.pack(fill="x", pady=5)

        # 控制按鈕行
        control_row = ttk.Frame(status_frame)
        control_row.pack(fill="x", pady=2)

        # Console控制按鈕
        self.btn_toggle_console = ttk.Button(control_row, text="🔇 關閉報價Console",
                                           command=self.toggle_console_quote)
        self.btn_toggle_console.pack(side="left", padx=5)

        # 策略Console控制按鈕
        self.btn_toggle_strategy_console = ttk.Button(control_row, text="🔇 關閉策略Console",
                                                    command=self.toggle_console_strategy)
        self.btn_toggle_strategy_console.pack(side="left", padx=5)

        # 🔧 監控系統總開關按鈕
        self.btn_toggle_monitoring = ttk.Button(control_row, text="🔊 啟用監控",
                                               command=self.toggle_monitoring)
        self.btn_toggle_monitoring.pack(side="left", padx=5)

        # 開發模式說明
        ttk.Label(control_row, text="(開發模式)", foreground="orange").pack(side="left", padx=2)

        # 說明文字
        ttk.Label(control_row, text="📊 狀態監控和報價信息請查看VS Code Console輸出",
                 foreground="blue").pack(side="left", padx=20)

        # 🚨 移除動態更新的UI元素，避免GIL錯誤
        # self.label_quote_status = ...
        # self.label_last_update = ...

    def start_status_monitor(self):
        """啟動狀態監控 - 智能提醒版本（可調整間隔）"""
        # 🔧 檢查監控開關
        if not getattr(self, 'monitoring_enabled', True):
            print("🔇 [MONITOR] 狀態監控已停用 (開發模式)")
            print("💡 [MONITOR] 如需啟用監控，請點擊 '啟用監控' 按鈕")
            return

        # 初始化狀態追蹤
        self.last_status = None
        self.status_unchanged_count = 0

        # 🔧 監控參數配置 (針對期貨市場優化)
        self.monitor_interval = 8000  # 監控間隔（毫秒）- 改為8秒
        self.quote_timeout_threshold = 4  # 報價中斷判定閾值（檢查次數）- 32秒無報價才判定中斷

        def monitor_loop():
            try:
                # 🔧 檢查監控開關 (動態檢查，可隨時切換)
                if not getattr(self, 'monitoring_enabled', True):
                    # 監控已停用，跳過本次檢查，但繼續排程下次檢查
                    self.root.after(self.monitor_interval, monitor_loop)
                    return

                # 🔧 簡化的報價狀態檢查 - 避免複雜時間操作
                current_tick_count = getattr(self, 'price_count', 0)
                current_best5_count = getattr(self, 'best5_count', 0)
                previous_status = self.monitoring_stats['quote_status']

                # 檢查是否有新的報價數據（成交或五檔）
                has_new_tick = current_tick_count > self.monitoring_stats.get('last_tick_count', 0)
                has_new_best5 = current_best5_count > self.monitoring_stats.get('last_best5_count', 0)

                if has_new_tick or has_new_best5:
                    # 有新報價
                    self.monitoring_stats['quote_status'] = "報價中"
                    self.monitoring_stats['last_tick_count'] = current_tick_count
                    self.monitoring_stats['last_best5_count'] = current_best5_count
                    new_status = "報價中"
                    self.status_unchanged_count = 0
                else:
                    # 沒有新報價，累計計數
                    self.status_unchanged_count += 1

                    # 🎯 只有超過閾值才判定為中斷
                    if self.status_unchanged_count >= self.quote_timeout_threshold:
                        self.monitoring_stats['quote_status'] = "報價中斷"
                        new_status = "報價中斷"
                    else:
                        # 還在容忍範圍內，保持原狀態
                        new_status = self.monitoring_stats['quote_status']

                # 🎯 智能提醒邏輯
                should_notify = False

                if previous_status != new_status:
                    # 狀態變化時一定提醒
                    should_notify = True
                    if new_status == "報價中":
                        status_msg = "✅ [MONITOR] 報價恢復正常"
                    else:
                        interval_seconds = (self.monitor_interval / 1000) * self.quote_timeout_threshold
                        status_msg = f"❌ [MONITOR] 報價中斷 (超過{interval_seconds:.0f}秒無報價)"
                elif new_status == "報價中斷":
                    # 報價中斷時，每6次檢查提醒一次 (6次 × 5秒 = 30秒)
                    if self.status_unchanged_count % 6 == 0:
                        should_notify = True
                        total_seconds = self.status_unchanged_count * (self.monitor_interval / 1000)
                        status_msg = f"⚠️ [MONITOR] 報價持續中斷 ({total_seconds:.0f}秒)"

                # 只在需要時輸出
                if should_notify:
                    timestamp = time.strftime("%H:%M:%S")
                    print(f"{status_msg} (檢查時間: {timestamp})")

                # 🎯 策略狀態監控
                self.monitor_strategy_status()

            except Exception as e:
                print(f"❌ [MONITOR] 狀態監控錯誤: {e}")

            # 排程下一次檢查（使用可配置間隔）
            self.root.after(self.monitor_interval, monitor_loop)

        # 啟動監控
        interval_sec = self.monitor_interval / 1000
        timeout_sec = interval_sec * self.quote_timeout_threshold
        print(f"🎯 [MONITOR] 狀態監聽器啟動")
        print(f"📊 [MONITOR] 檢查間隔: {interval_sec}秒, 中斷判定: {timeout_sec}秒無報價")
        monitor_loop()

    def toggle_console_quote(self):
        """切換報價Console輸出"""
        try:
            self.console_quote_enabled = not self.console_quote_enabled

            if self.console_quote_enabled:
                self.btn_toggle_console.config(text="🔇 關閉報價Console")
                print("✅ [CONSOLE] 報價Console輸出已啟用")
                print("💡 [CONSOLE] 報價數據將顯示在Console中")
            else:
                self.btn_toggle_console.config(text="🔊 開啟報價Console")
                print("🔇 [CONSOLE] 報價Console輸出已關閉")
                print("💡 [CONSOLE] 報價仍在處理，但不顯示在Console中")
                print("📊 [CONSOLE] 狀態監聽器仍會檢測報價狀態")

        except Exception as e:
            print(f"❌ [CONSOLE] 切換Console輸出錯誤: {e}")

    def toggle_console_strategy(self):
        """切換策略Console輸出"""
        try:
            self.console_strategy_enabled = not self.console_strategy_enabled

            if self.console_strategy_enabled:
                self.btn_toggle_strategy_console.config(text="🔇 關閉策略Console")
                print("✅ [CONSOLE] 策略Console輸出已啟用")
                print("💡 [CONSOLE] 策略監控數據將顯示在Console中")
            else:
                self.btn_toggle_strategy_console.config(text="🔊 開啟策略Console")
                print("🔇 [CONSOLE] 策略Console輸出已關閉")
                print("💡 [CONSOLE] 策略仍在運行，但不顯示在Console中")
                print("📊 [CONSOLE] 狀態監聽器仍會檢測策略狀態")

        except Exception as e:
            print(f"❌ [CONSOLE] 切換策略Console輸出錯誤: {e}")

    def toggle_monitoring(self):
        """切換監控系統總開關"""
        try:
            self.monitoring_enabled = not self.monitoring_enabled

            if self.monitoring_enabled:
                self.btn_toggle_monitoring.config(text="🔇 停用監控")
                print("✅ [MONITOR] 狀態監控系統已啟用")
                print("📊 [MONITOR] 將開始監控報價和策略狀態")
                # 重新啟動監控
                self.start_status_monitor()
            else:
                self.btn_toggle_monitoring.config(text="🔊 啟用監控")
                print("🔇 [MONITOR] 狀態監控系統已停用")
                print("💡 [MONITOR] 核心功能不受影響，僅停止狀態監控")
                print("🎯 [MONITOR] 開發模式：避免GIL風險")

        except Exception as e:
            print(f"❌ [MONITOR] 切換監控系統錯誤: {e}")

    def init_multi_group_system(self):
        """初始化多組策略系統"""
        try:
            # 初始化Console日誌器
            self.multi_group_logger = get_logger()
            self.multi_group_logger.system_info("多組策略系統初始化開始")

            # 🔧 初始化回報過濾機制
            self._init_reply_filter()

            # 初始化資料庫管理器
            self.multi_group_db_manager = MultiGroupDatabaseManager("multi_group_strategy.db")

            # 🚀 擴展資料庫以支援平倉機制
            self._extend_database_for_exit_mechanism()

            # 初始化風險管理引擎
            self.multi_group_risk_engine = RiskManagementEngine(self.multi_group_db_manager)

            # 🔍 DEBUG: 設定console開關給風險管理引擎
            if hasattr(self.multi_group_risk_engine, 'console_enabled'):
                # 確保console_enabled屬性存在
                if not hasattr(self, 'console_enabled'):
                    self.console_enabled = True  # 預設啟用console模式

                self.multi_group_risk_engine.console_enabled = self.console_enabled
                if self.console_enabled:
                    print("[MULTI_GROUP] 🔍 風險管理引擎DEBUG模式已啟用")

                    # 🔍 立即測試風險管理引擎
                    try:
                        test_price = 22300.0
                        test_time = "16:00:00"
                        print(f"[MULTI_GROUP] 🧪 測試風險管理引擎: {test_price} @{test_time}")

                        exit_actions = self.multi_group_risk_engine.check_all_exit_conditions(test_price, test_time)
                        print(f"[MULTI_GROUP] ✅ 風險管理引擎測試成功: {len(exit_actions)}個出場動作")

                    except Exception as test_error:
                        print(f"[MULTI_GROUP] ❌ 風險管理引擎測試失敗: {test_error}")
                        import traceback
                        traceback.print_exc()

            # 🎯 設定預設配置 - 改用1組3口模式 (對應回測程式)
            presets = create_preset_configs()
            default_config = presets["標準配置 (3口×1組)"]  # 🚀 改用1組3口配置，對應回測程式邏輯

            print("[MULTI_GROUP] 📊 使用配置: 標準配置 (3口×1組)")
            print("[MULTI_GROUP] 🎯 對應回測程式的3口策略邏輯")
            print("[MULTI_GROUP] 📋 規則: 第1口15點啟動, 第2口40點啟動, 第3口65點啟動")

            # 🔧 初始化平倉機制配置
            self._init_exit_mechanism_config()

            # 🛡️ 初始化完整平倉機制系統
            self._init_complete_exit_mechanism()

            # 初始化部位管理器（暫時不設置下單組件，稍後設置）
            self.multi_group_position_manager = MultiGroupPositionManager(
                self.multi_group_db_manager,
                default_config
            )

            # 🔧 新增：設置父引用，讓部位管理器能訪問報價數據
            import weakref
            self.multi_group_position_manager._parent_ref = weakref.ref(self)

            # 🔧 新增：初始化統一出場管理器
            self.unified_exit_manager = None  # 稍後在設置下單組件時初始化

            self.multi_group_enabled = True
            self.multi_group_logger.system_info("多組策略系統初始化完成")
            print("✅ 多組策略系統初始化成功")
            print("✅ 平倉機制配置完成")

        except Exception as e:
            self.multi_group_enabled = False
            print(f"❌ 多組策略系統初始化失敗: {e}")
            if hasattr(self, 'multi_group_logger') and self.multi_group_logger:
                self.multi_group_logger.system_error(f"初始化失敗: {e}")

    def _extend_database_for_exit_mechanism(self):
        """擴展資料庫以支援平倉機制"""
        try:
            from exit_mechanism_database_extension import extend_database_for_exit_mechanism

            print("[EXIT_DB] 🚀 開始擴展資料庫以支援平倉機制...")
            success = extend_database_for_exit_mechanism(self.multi_group_db_manager)

            if success:
                print("[EXIT_DB] ✅ 資料庫擴展成功")
            else:
                print("[EXIT_DB] ❌ 資料庫擴展失敗")

        except ImportError as e:
            print(f"[EXIT_DB] ⚠️ 平倉機制資料庫擴展模組載入失敗: {e}")
        except Exception as e:
            print(f"[EXIT_DB] ❌ 資料庫擴展過程發生錯誤: {e}")

    def _init_exit_mechanism_config(self):
        """初始化平倉機制配置"""
        try:
            from exit_mechanism_config import get_default_exit_config_for_multi_group

            # 取得預設平倉配置 (1組3口模式)
            self.exit_config = get_default_exit_config_for_multi_group()

            print("[EXIT_CONFIG] ⚙️ 平倉機制配置載入:")
            print(f"[EXIT_CONFIG]   📋 配置ID: {self.exit_config.group_id}")
            print(f"[EXIT_CONFIG]   📊 總口數: {self.exit_config.total_lots}")
            print(f"[EXIT_CONFIG]   🛡️ 停損類型: {self.exit_config.stop_loss_type}")

            for rule in self.exit_config.lot_rules:
                protection_text = f", {rule.protective_stop_multiplier}倍保護" if rule.protective_stop_multiplier else ""
                print(f"[EXIT_CONFIG]   🎯 第{rule.lot_number}口: {rule.trailing_activation_points}點啟動{protection_text}")

        except ImportError as e:
            print(f"[EXIT_CONFIG] ⚠️ 平倉機制配置模組載入失敗: {e}")
            self.exit_config = None
        except Exception as e:
            print(f"[EXIT_CONFIG] ❌ 平倉機制配置初始化失敗: {e}")
            self.exit_config = None

    def _init_stop_loss_system(self):
        """初始化停損系統"""
        try:
            from initial_stop_loss_manager import create_initial_stop_loss_manager
            from stop_loss_monitor import create_stop_loss_monitor
            from stop_loss_executor import create_stop_loss_executor

            print("[STOP_LOSS] 🛡️ 初始化停損系統...")

            # 創建停損管理器
            self.initial_stop_loss_manager = create_initial_stop_loss_manager(
                self.multi_group_db_manager, console_enabled=True
            )

            # 創建停損監控器
            self.stop_loss_monitor = create_stop_loss_monitor(
                self.multi_group_db_manager, console_enabled=True
            )

            # 創建停損執行器 (暫時不連接虛實單管理器)
            self.stop_loss_executor = create_stop_loss_executor(
                self.multi_group_db_manager,
                virtual_real_order_manager=None,  # 稍後連接
                console_enabled=self.console_enabled  # 🔍 使用統一的console開關
            )

            # 🔍 DEBUG: 確保停損執行器的console設定
            if hasattr(self.stop_loss_executor, 'console_enabled'):
                self.stop_loss_executor.console_enabled = self.console_enabled
                if self.console_enabled:
                    print("[STOP_LOSS] 🔍 停損執行器DEBUG模式已啟用")

            # 🔧 設定停損執行器的簡化追蹤器引用 (稍後連接)
            # 這將在多組部位管理器初始化後設定

            # 🔧 新增：設定停損執行器的FIFO追蹤器
            if hasattr(self, 'multi_group_position_manager'):
                self.stop_loss_executor.set_trackers(
                    order_tracker=getattr(self.multi_group_position_manager, 'order_tracker', None),
                    simplified_tracker=getattr(self.multi_group_position_manager, 'simplified_tracker', None)
                )

            # 設定停損觸發回調
            def on_stop_loss_triggered(trigger_info):
                """停損觸發回調函數"""
                try:
                    print(f"[STOP_LOSS] 🚨 停損觸發回調: 部位 {trigger_info.position_id}")
                    # 執行停損平倉
                    execution_result = self.stop_loss_executor.execute_stop_loss(trigger_info)

                    if execution_result.success:
                        print(f"[STOP_LOSS] ✅ 停損執行成功: {execution_result.order_id}")
                    else:
                        print(f"[STOP_LOSS] ❌ 停損執行失敗: {execution_result.error_message}")

                except Exception as e:
                    print(f"[STOP_LOSS] ❌ 停損回調處理失敗: {e}")

            # 註冊回調函數
            self.stop_loss_monitor.add_stop_loss_callback(on_stop_loss_triggered)

            # 🎯 初始化移動停利系統
            self._init_trailing_stop_system()

            # 🛡️ 初始化累積獲利保護系統
            self._init_protection_system()

            print("[STOP_LOSS] ✅ 停損系統初始化完成")
            print("[STOP_LOSS] 📋 組件: 管理器、監控器、執行器")
            print("[STOP_LOSS] 🔗 回調函數已註冊")

        except ImportError as e:
            print(f"[STOP_LOSS] ⚠️ 停損系統模組載入失敗: {e}")
            self.initial_stop_loss_manager = None
            self.stop_loss_monitor = None
            self.stop_loss_executor = None
        except Exception as e:
            print(f"[STOP_LOSS] ❌ 停損系統初始化失敗: {e}")
            self.initial_stop_loss_manager = None
            self.stop_loss_monitor = None
            self.stop_loss_executor = None

    def _init_trailing_stop_system(self):
        """初始化移動停利系統"""
        try:
            from trailing_stop_activator import create_trailing_stop_activator
            from peak_price_tracker import create_peak_price_tracker
            from drawdown_monitor import create_drawdown_monitor

            print("[TRAILING] 🎯 初始化移動停利系統...")

            # 創建移動停利啟動器
            self.trailing_stop_activator = create_trailing_stop_activator(
                self.multi_group_db_manager, console_enabled=True
            )

            # 創建峰值價格追蹤器
            self.peak_price_tracker = create_peak_price_tracker(
                self.multi_group_db_manager, console_enabled=True
            )

            # 創建回撤監控器
            self.drawdown_monitor = create_drawdown_monitor(
                self.multi_group_db_manager, console_enabled=True
            )

            # 設定移動停利啟動回調
            def on_trailing_stop_activated(activation_info):
                """移動停利啟動回調函數"""
                try:
                    print(f"[TRAILING] 🎯 移動停利啟動回調: 部位 {activation_info.position_id}")
                    print(f"[TRAILING] 📊 啟動條件: {activation_info.activation_points}點獲利")
                    print(f"[TRAILING] 💰 當前獲利: {activation_info.profit_points:.1f}點")
                except Exception as e:
                    print(f"[TRAILING] ❌ 啟動回調處理失敗: {e}")

            # 設定峰值更新回調
            def on_peak_price_updated(update_info):
                """峰值價格更新回調函數"""
                try:
                    print(f"[TRAILING] 📈 峰值更新回調: 部位 {update_info.position_id}")
                    print(f"[TRAILING] 🔄 峰值變化: {update_info.old_peak} → {update_info.new_peak}")
                    print(f"[TRAILING] 📊 改善幅度: {update_info.improvement:.1f}點")
                except Exception as e:
                    print(f"[TRAILING] ❌ 峰值更新回調處理失敗: {e}")

            # 設定回撤觸發回調
            def on_drawdown_triggered(trigger_info):
                """回撤觸發回調函數"""
                try:
                    print(f"[TRAILING] 🚨 回撤觸發回調: 部位 {trigger_info.position_id}")
                    print(f"[TRAILING] 📉 回撤比例: {trigger_info.drawdown_ratio:.1%}")
                    print(f"[TRAILING] 💔 回撤點數: {trigger_info.drawdown_points:.1f}點")

                    # 執行移動停利平倉
                    if hasattr(self, 'stop_loss_executor') and self.stop_loss_executor:
                        # 創建類似停損觸發的結構來執行平倉
                        from stop_loss_monitor import StopLossTrigger

                        trailing_trigger = StopLossTrigger(
                            position_id=trigger_info.position_id,
                            group_id=trigger_info.group_id,
                            direction=trigger_info.direction,
                            current_price=trigger_info.current_price,
                            stop_loss_price=trigger_info.current_price,  # 使用當前價格作為平倉價
                            trigger_time=trigger_info.trigger_time,
                            trigger_reason=f"移動停利: {trigger_info.trigger_reason}",
                            breach_amount=trigger_info.drawdown_points
                        )

                        execution_result = self.stop_loss_executor.execute_stop_loss(trailing_trigger)

                        if execution_result.success:
                            print(f"[TRAILING] ✅ 移動停利平倉成功: {execution_result.order_id}")
                        else:
                            print(f"[TRAILING] ❌ 移動停利平倉失敗: {execution_result.error_message}")

                except Exception as e:
                    print(f"[TRAILING] ❌ 回撤觸發回調處理失敗: {e}")

            # 註冊回調函數
            self.trailing_stop_activator.add_activation_callback(on_trailing_stop_activated)
            self.peak_price_tracker.add_update_callback(on_peak_price_updated)
            self.drawdown_monitor.add_drawdown_callback(on_drawdown_triggered)

            # 啟用移動停利系統
            self.trailing_stop_system_enabled = True

            print("[TRAILING] ✅ 移動停利系統初始化完成")
            print("[TRAILING] 📋 組件: 啟動器、峰值追蹤器、回撤監控器")
            print("[TRAILING] 🔗 所有回調函數已註冊")
            print("[TRAILING] 🎯 分層啟動: 15/40/65點, 20%回撤")

        except ImportError as e:
            print(f"[TRAILING] ⚠️ 移動停利系統模組載入失敗: {e}")
            self.trailing_stop_activator = None
            self.peak_price_tracker = None
            self.drawdown_monitor = None
            self.trailing_stop_system_enabled = False
        except Exception as e:
            print(f"[TRAILING] ❌ 移動停利系統初始化失敗: {e}")
            self.trailing_stop_activator = None
            self.peak_price_tracker = None
            self.drawdown_monitor = None
            self.trailing_stop_system_enabled = False

    def _init_protection_system(self):
        """初始化累積獲利保護系統"""
        try:
            from cumulative_profit_protection_manager import create_cumulative_profit_protection_manager
            from stop_loss_state_manager import create_stop_loss_state_manager

            print("[PROTECTION] 🛡️ 初始化累積獲利保護系統...")

            # 創建累積獲利保護管理器
            self.protection_manager = create_cumulative_profit_protection_manager(
                self.multi_group_db_manager, console_enabled=True
            )

            # 創建停損狀態管理器
            self.stop_loss_state_manager = create_stop_loss_state_manager(
                self.multi_group_db_manager, console_enabled=True
            )

            # 設定保護更新回調
            def on_protection_updated(update_info):
                """保護性停損更新回調函數"""
                try:
                    print(f"[PROTECTION] 🛡️ 保護更新回調: 部位 {update_info.position_id}")
                    print(f"[PROTECTION] 📊 停損提升: {update_info.old_stop_loss} → {update_info.new_stop_loss}")
                    print(f"[PROTECTION] 💰 累積獲利: {update_info.cumulative_profit:.1f}點")
                    print(f"[PROTECTION] 🔢 保護倍數: {update_info.protection_multiplier}倍")

                    # 更新停損狀態
                    if hasattr(self, 'stop_loss_state_manager') and self.stop_loss_state_manager:
                        self.stop_loss_state_manager.transition_to_protective_stop(
                            update_info.position_id,
                            update_info.new_stop_loss,
                            update_info.update_reason
                        )

                except Exception as e:
                    print(f"[PROTECTION] ❌ 保護更新回調處理失敗: {e}")

            # 設定狀態轉換回調
            def on_state_transition(transition_info):
                """停損狀態轉換回調函數"""
                try:
                    print(f"[PROTECTION] 🔄 狀態轉換回調: 部位 {transition_info.position_id}")
                    print(f"[PROTECTION] 📋 轉換類型: {transition_info.from_type.value} → {transition_info.to_type.value}")
                    print(f"[PROTECTION] 🎯 轉換原因: {transition_info.transition_reason}")
                except Exception as e:
                    print(f"[PROTECTION] ❌ 狀態轉換回調處理失敗: {e}")

            # 註冊回調函數
            self.protection_manager.add_protection_callback(on_protection_updated)
            self.stop_loss_state_manager.add_transition_callback(on_state_transition)

            # 🔗 將保護管理器連接到停損執行器
            if hasattr(self, 'stop_loss_executor') and self.stop_loss_executor:
                self.stop_loss_executor.set_protection_manager(self.protection_manager)
                print("[PROTECTION] 🔗 保護管理器已連接到停損執行器")

            print("[PROTECTION] ✅ 累積獲利保護系統初始化完成")
            print("[PROTECTION] 📋 組件: 保護管理器、狀態管理器")
            print("[PROTECTION] 🔗 所有回調函數已註冊")
            print("[PROTECTION] 🛡️ 保護邏輯: 累積獲利 × 2.0倍保護")

        except ImportError as e:
            print(f"[PROTECTION] ⚠️ 累積獲利保護系統模組載入失敗: {e}")
            self.protection_manager = None
            self.stop_loss_state_manager = None
        except Exception as e:
            print(f"[PROTECTION] ❌ 累積獲利保護系統初始化失敗: {e}")
            self.protection_manager = None
            self.stop_loss_state_manager = None

    def _init_complete_exit_mechanism(self):
        """初始化完整平倉機制系統 (統一管理器版本)"""
        try:
            from exit_mechanism_manager import create_exit_mechanism_manager

            print("[EXIT_SYSTEM] 🚀 初始化完整平倉機制系統...")

            # 創建平倉機制統一管理器
            self.exit_mechanism_manager = create_exit_mechanism_manager(
                self.multi_group_db_manager, console_enabled=True
            )

            # 🔧 新增：設定平倉機制管理器的FIFO追蹤器
            if hasattr(self, 'multi_group_position_manager'):
                self.exit_mechanism_manager.set_trackers(
                    order_tracker=getattr(self.multi_group_position_manager, 'order_tracker', None),
                    simplified_tracker=getattr(self.multi_group_position_manager, 'simplified_tracker', None)
                )

            # 初始化所有平倉機制組件
            success = self.exit_mechanism_manager.initialize_all_components()

            if success:
                # 設定便捷訪問屬性 (向後兼容)
                self.initial_stop_loss_manager = self.exit_mechanism_manager.initial_stop_loss_manager
                self.stop_loss_monitor = self.exit_mechanism_manager.stop_loss_monitor
                self.stop_loss_executor = self.exit_mechanism_manager.stop_loss_executor
                self.trailing_stop_activator = self.exit_mechanism_manager.trailing_stop_activator
                self.peak_price_tracker = self.exit_mechanism_manager.peak_price_tracker
                self.drawdown_monitor = self.exit_mechanism_manager.drawdown_monitor
                self.protection_manager = self.exit_mechanism_manager.protection_manager
                self.stop_loss_state_manager = self.exit_mechanism_manager.stop_loss_state_manager

                # 啟用系統
                self.trailing_stop_system_enabled = True

                print("[EXIT_SYSTEM] ✅ 完整平倉機制系統初始化成功")
                print("[EXIT_SYSTEM] 📋 包含所有組件: 停損、移動停利、保護機制")
                print("[EXIT_SYSTEM] 🔗 統一管理器已啟用")
                print("[EXIT_SYSTEM] 🎯 對應回測程式邏輯: 15/40/65點啟動, 2倍保護, 20%回撤")

                # 列印系統狀態
                self.exit_mechanism_manager.print_exit_mechanism_status()

            else:
                print("[EXIT_SYSTEM] ❌ 平倉機制系統初始化失敗")
                self.exit_mechanism_manager = None
                self.trailing_stop_system_enabled = False
                # 回退到分散初始化
                self._init_stop_loss_system()

        except ImportError as e:
            print(f"[EXIT_SYSTEM] ⚠️ 平倉機制系統模組載入失敗: {e}")
            print("[EXIT_SYSTEM] 🔄 回退到分散初始化模式...")
            self.exit_mechanism_manager = None
            self.trailing_stop_system_enabled = False
            # 回退到分散初始化
            self._init_stop_loss_system()
        except Exception as e:
            print(f"[EXIT_SYSTEM] ❌ 平倉機制系統初始化失敗: {e}")
            print("[EXIT_SYSTEM] 🔄 回退到分散初始化模式...")
            self.exit_mechanism_manager = None
            self.trailing_stop_system_enabled = False
            # 回退到分散初始化
            self._init_stop_loss_system()

    def toggle_auto_start(self):
        """切換自動啟動選項"""
        self.multi_group_auto_start = self.auto_start_var.get()
        status = "開啟" if self.multi_group_auto_start else "關閉"
        if self.multi_group_logger:
            self.multi_group_logger.config_change(f"自動啟動已{status}")
        print(f"🤖 [CONFIG] 區間完成後自動啟動: {status}")

    def toggle_multi_group_eod_close(self):
        """切換多組策略收盤平倉選項"""
        try:
            enable_eod_close = self.multi_group_eod_close_var.get()

            # 更新風險管理引擎設定
            if self.multi_group_risk_engine:
                self.multi_group_risk_engine.set_eod_close_settings(enable_eod_close, 13, 30)

            status = "啟用" if enable_eod_close else "停用"
            if self.multi_group_logger:
                self.multi_group_logger.config_change(f"收盤平倉已{status}")
            print(f"🕐 [CONFIG] 多組策略收盤平倉 (13:30): {status}")

            if enable_eod_close:
                print("⚠️ [CONFIG] 啟用收盤平倉後，所有部位將在13:30強制平倉")
            else:
                print("💡 [CONFIG] 收盤平倉已停用，適合測試階段使用")

        except Exception as e:
            print(f"❌ [CONFIG] 收盤平倉設定失敗: {e}")

    def toggle_single_strategy_eod_close(self):
        """切換單一策略收盤平倉選項"""
        try:
            enable_eod_close = self.single_strategy_eod_close_var.get()

            status = "啟用" if enable_eod_close else "停用"
            print(f"🕐 [CONFIG] 單一策略收盤平倉 (13:30): {status}")

            if enable_eod_close:
                print("⚠️ [CONFIG] 啟用收盤平倉後，所有部位將在13:30強制平倉")
            else:
                print("💡 [CONFIG] 收盤平倉已停用，適合測試階段使用")

        except Exception as e:
            print(f"❌ [CONFIG] 單一策略收盤平倉設定失敗: {e}")

    def prepare_multi_group_strategy(self):
        """準備多組策略"""
        try:
            if not self.multi_group_enabled:
                print("⚠️ [STRATEGY] 多組策略系統未啟用")
                self.add_log("⚠️ 多組策略系統未啟用")
                return

            if not self.logged_in:
                print("⚠️ [STRATEGY] 請先登入系統")
                self.add_log("⚠️ 請先登入系統")
                return

            # 檢查配置是否有效
            if not self.multi_group_config_panel:
                print("❌ [STRATEGY] 配置面板未初始化")
                self.add_log("❌ 配置面板未初始化")
                return

            current_config = self.multi_group_config_panel.get_current_config()
            if not current_config:
                print("⚠️ [STRATEGY] 請先選擇策略配置")
                self.add_log("⚠️ 請先選擇策略配置")
                return

            # 驗證配置
            from multi_group_config import validate_config
            errors = validate_config(current_config)
            if errors:
                error_msg = "配置驗證失敗: " + ", ".join(errors)
                print(f"❌ [STRATEGY] {error_msg}")
                self.add_log(f"❌ {error_msg}")
                return

            # 設定策略為準備狀態
            self.multi_group_prepared = True
            self.multi_group_auto_start = self.auto_start_var.get()

            # 更新UI狀態
            self.btn_prepare_multi_group.config(state="disabled")
            self.btn_start_multi_group.config(state="normal")
            self.multi_group_status_label.config(text="📋 已準備", fg="blue")

            if self.multi_group_auto_start:
                self.multi_group_detail_label.config(
                    text="等待區間計算完成後自動啟動",
                    fg="orange"
                )
            else:
                self.multi_group_detail_label.config(
                    text="準備完成，可手動啟動",
                    fg="green"
                )

            # 記錄日誌
            if self.multi_group_logger:
                self.multi_group_logger.strategy_info(
                    f"策略已準備: {current_config.total_groups}組×{current_config.lots_per_group}口, "
                    f"自動啟動: {'是' if self.multi_group_auto_start else '否'}"
                )

            # Console輸出替代對話框
            print("✅ [STRATEGY] 多組策略已準備完成！")
            print(f"📊 [STRATEGY] 配置: {current_config.total_groups}組×{current_config.lots_per_group}口")
            print(f"📊 [STRATEGY] 總部位數: {current_config.get_total_positions()}")
            print(f"📊 [STRATEGY] 自動啟動: {'是' if self.multi_group_auto_start else '否'}")
            if self.multi_group_auto_start:
                print("🤖 [STRATEGY] 系統將在區間計算完成後自動啟動策略")
            else:
                print("👆 [STRATEGY] 請在區間計算完成後手動啟動策略")

            # UI日誌
            self.add_log(f"✅ 多組策略已準備: {current_config.total_groups}組×{current_config.lots_per_group}口")

        except Exception as e:
            print(f"❌ [STRATEGY] 準備策略失敗: {e}")
            self.add_log(f"❌ 準備策略失敗: {e}")
            if self.multi_group_logger:
                self.multi_group_logger.strategy_error(f"準備失敗: {e}")

    def manual_start_multi_group_strategy(self):
        """手動啟動多組策略"""
        try:
            if not self.multi_group_prepared:
                print("⚠️ [STRATEGY] 請先準備策略")
                self.add_log("⚠️ 請先準備策略")
                return

            self.start_multi_group_strategy()

        except Exception as e:
            print(f"❌ [STRATEGY] 手動啟動失敗: {e}")
            self.add_log(f"❌ 手動啟動失敗: {e}")

    def start_multi_group_strategy(self):
        """啟動多組策略"""
        try:
            if not self.multi_group_enabled:
                print("⚠️ [STRATEGY] 多組策略系統未啟用")
                self.add_log("⚠️ 多組策略系統未啟用")
                return

            if not self.logged_in:
                print("⚠️ [STRATEGY] 請先登入系統")
                self.add_log("⚠️ 請先登入系統")
                return

            # 檢查是否有區間數據
            if not self.range_calculated:
                print("⚠️ [STRATEGY] 請先計算開盤區間")
                self.add_log("⚠️ 請先計算開盤區間")
                return

            # 檢查是否已經在運行中（防重複啟動）
            if self.multi_group_running:
                print("⚠️ [STRATEGY] 多組策略已在運行中")
                self.add_log("⚠️ 多組策略已在運行中")
                return

            # 🎯 手動啟動時使用預設方向，等待實際突破時動態調整
            # 設定為監控準備狀態，不立即創建策略組
            self.multi_group_monitoring_ready = True

            # 更新運行狀態（監控狀態）
            self.multi_group_running = True

            # 模擬創建成功的group_ids（實際創建將在突破時進行）
            group_ids = [1]  # 假設會創建組別，實際數量在突破時確定

            if group_ids:
                # 更新UI狀態 (只修改按鈕狀態，避免GIL風險)
                self.btn_prepare_multi_group.config(state="disabled")
                self.btn_start_multi_group.config(state="disabled")
                self.btn_stop_multi_group.config(state="normal")
                # 移除動態標籤更新，改為Console輸出

                if self.multi_group_logger:
                    self.multi_group_logger.strategy_info(
                        f"多組策略監控啟動, 區間{self.range_low}-{self.range_high}"
                    )

                # Console輸出啟動結果
                print(f"🎯 [STRATEGY] 多組策略監控已啟動，等待突破信號")
                self.add_log(f"🎯 多組策略監控已啟動")

                # 標記為自動啟動
                if self.multi_group_auto_start:
                    self._auto_started = True
            else:
                print("❌ [STRATEGY] 創建策略組失敗")
                self.add_log("❌ 創建策略組失敗")

        except Exception as e:
            print(f"❌ [STRATEGY] 啟動多組策略失敗: {e}")
            self.add_log(f"❌ 啟動多組策略失敗: {e}")
            if self.multi_group_logger:
                self.multi_group_logger.strategy_error(f"啟動失敗: {e}")

    def stop_multi_group_strategy(self):
        """停止多組策略"""
        try:
            if not self.multi_group_enabled:
                return

            # 重置每日狀態
            if self.multi_group_position_manager:
                self.multi_group_position_manager.reset_daily_state()

            # 重置狀態變數
            self.multi_group_running = False
            self.multi_group_prepared = False
            self.multi_group_monitoring_ready = False  # 重置監控準備狀態
            self._auto_start_triggered = False  # 重置觸發標記
            if hasattr(self, '_auto_started'):
                delattr(self, '_auto_started')

            # 更新UI狀態
            self.btn_prepare_multi_group.config(state="normal")
            self.btn_start_multi_group.config(state="disabled")
            self.btn_stop_multi_group.config(state="disabled")
            self.multi_group_status_label.config(text="⏸️ 已停止", fg="gray")
            self.multi_group_detail_label.config(text="請重新配置策略", fg="blue")

            if self.multi_group_logger:
                self.multi_group_logger.strategy_info("多組策略已停止")

            print("✅ [STRATEGY] 多組策略已停止")
            self.add_log("✅ 多組策略已停止")

        except Exception as e:
            print(f"❌ [STRATEGY] 停止多組策略失敗: {e}")
            self.add_log(f"❌ 停止多組策略失敗: {e}")
            if self.multi_group_logger:
                self.multi_group_logger.strategy_error(f"停止失敗: {e}")

    def toggle_multi_group_console(self, category, name):
        """切換多組策略Console輸出"""
        try:
            if not self.multi_group_logger:
                return

            new_state = self.multi_group_logger.toggle_category_console(category)

            # 更新按鈕文字（這裡需要找到對應的按鈕，簡化處理）
            state_text = "關閉" if new_state else "開啟"
            print(f"🎛️ [CONSOLE] {name}Console輸出已{state_text}")

        except Exception as e:
            print(f"❌ [CONSOLE] 切換{name}Console失敗: {e}")

    def check_auto_start_multi_group_strategy(self):
        """檢查是否需要自動啟動多組策略"""
        try:
            # 🆕 檢查執行頻率設定
            frequency = getattr(self, 'multi_group_frequency_var', None)
            freq_setting = frequency.get() if frequency else "一天一次"

            # 🆕 根據頻率設定檢查是否允許執行
            if freq_setting == "一天一次":
                # 檢查今天是否已有策略組
                if hasattr(self, 'multi_group_position_manager') and self.multi_group_position_manager:
                    today_groups = self.multi_group_position_manager.db_manager.get_today_strategy_groups()
                    if today_groups:
                        print("📅 [STRATEGY] 一天一次模式：今日已執行過，跳過自動啟動")
                        if self.multi_group_logger:
                            self.multi_group_logger.strategy_info("一天一次模式：今日已執行過，跳過")
                        return

            # 檢查條件：已準備 + 自動啟動 + 未運行 + 區間已計算 + 未觸發過
            if (self.multi_group_prepared and
                self.multi_group_auto_start and
                not self.multi_group_running and
                self.range_calculated and
                not self._auto_start_triggered):

                # 立即設定觸發標記，防止重複調用
                self._auto_start_triggered = True

                if self.multi_group_logger:
                    self.multi_group_logger.strategy_info(
                        f"區間計算完成，準備多組策略監控: 區間{self.range_low}-{self.range_high} (頻率:{freq_setting})"
                    )

                # 🎯 新邏輯：準備多組策略監控，但不立即創建策略組
                self.prepare_multi_group_monitoring()

                # 移除動態UI更新，改為Console輸出
                # self.multi_group_detail_label.config(text="等待突破信號...", fg="orange")

                print(f"🤖 [AUTO] 區間計算完成，準備多組策略監控 (頻率:{freq_setting})")

        except Exception as e:
            # 如果啟動失敗，重置觸發標記
            self._auto_start_triggered = False
            if self.multi_group_logger:
                self.multi_group_logger.system_error(f"自動啟動檢查失敗: {e}")
            print(f"❌ [AUTO] 自動啟動檢查失敗: {e}")

    def prepare_multi_group_monitoring(self):
        """準備多組策略監控（不立即創建策略組）"""
        try:
            # 設定多組策略為監控狀態
            self.multi_group_running = True
            self.multi_group_monitoring_ready = True  # 新增監控準備狀態

            # 更新UI狀態 (只修改按鈕狀態，避免GIL風險)
            self.btn_prepare_multi_group.config(state="disabled")
            self.btn_start_multi_group.config(state="disabled")
            self.btn_stop_multi_group.config(state="normal")
            # 移除動態標籤更新，改為Console輸出

            if self.multi_group_logger:
                self.multi_group_logger.strategy_info("多組策略監控已準備，等待突破信號")

            print("🎯 [STRATEGY] 多組策略監控已準備，等待突破信號")
            self.add_log("🎯 多組策略監控已準備")

        except Exception as e:
            print(f"❌ [STRATEGY] 準備多組策略監控失敗: {e}")
            if self.multi_group_logger:
                self.multi_group_logger.system_error(f"準備監控失敗: {e}")

    def on_multi_group_frequency_changed(self, event=None):
        """多組策略執行頻率變更事件"""
        try:
            frequency = self.multi_group_frequency_var.get()

            if frequency == "一天一次":
                self.add_log("📅 多組策略設定為一天一次執行")
                print("📅 [STRATEGY] 多組策略設定為一天一次執行")

            elif frequency == "可重複執行":
                self.add_log("🔄 多組策略設定為可重複執行")
                print("🔄 [STRATEGY] 多組策略設定為可重複執行")
                print("💡 [STRATEGY] 每次區間計算完成都可以執行新的策略組")

            elif frequency == "測試模式":
                self.add_log("🧪 多組策略設定為測試模式")
                print("🧪 [STRATEGY] 多組策略設定為測試模式 - 忽略所有執行限制")
                # 重置觸發標記，允許立即重新執行
                self._auto_start_triggered = False

            # 記錄到多組策略日誌
            if self.multi_group_logger:
                self.multi_group_logger.system_info(f"執行頻率變更為: {frequency}")

        except Exception as e:
            self.add_log(f"❌ 執行頻率設定失敗: {e}")
            print(f"❌ [STRATEGY] 執行頻率設定失敗: {e}")

    def _init_reply_filter(self):
        """初始化回報過濾機制"""
        import time
        self._order_system_start_time = time.time()
        self._known_order_ids = set()  # 記錄我們下的訂單ID

        # 初始化手動啟動標記
        self._manual_order_started = False

        # 確保console_enabled屬性存在
        console_enabled = getattr(self, 'console_enabled', True)
        if console_enabled:
            print(f"[REPLY_FILTER] 🔧 回報過濾機制已初始化")
            print(f"[REPLY_FILTER] ⏰ 系統啟動時間: {time.strftime('%H:%M:%S', time.localtime(self._order_system_start_time))}")
            print(f"[REPLY_FILTER] 🛡️ 手動啟動模式: 需要手動啟用回報處理")

    def _is_new_order_reply(self, reply_data: str) -> bool:
        """
        判斷是否為新的訂單回報（非歷史回報）

        Args:
            reply_data: 回報數據字符串

        Returns:
            bool: True=新回報, False=歷史回報
        """
        try:
            import time
            from datetime import datetime

            cutData = reply_data.split(',')
            if len(cutData) < 25:
                return False  # 數據不完整，拒絕

            # 🔧 多重過濾策略
            current_time = time.time()
            startup_elapsed = current_time - self._order_system_start_time

            # 策略1: 啟動後60秒內，拒絕所有回報（延長過濾時間）
            if startup_elapsed < 60:
                return False

            # 策略2: 檢查是否有手動啟動標記
            if hasattr(self, '_manual_order_started') and not self._manual_order_started:
                return False

            # 策略3: 檢查回報時間是否太舊
            reply_time_str = cutData[24] if len(cutData) > 24 else ""
            if reply_time_str:
                try:
                    now = datetime.now()
                    reply_hour, reply_min, reply_sec = map(int, reply_time_str.split(':'))
                    current_seconds = now.hour * 3600 + now.minute * 60 + now.second
                    reply_seconds = reply_hour * 3600 + reply_min * 60 + reply_sec

                    # 如果回報時間與當前時間差距超過120秒，視為歷史回報
                    time_diff = abs(current_seconds - reply_seconds)
                    if time_diff > 120:
                        return False
                except:
                    pass

            # 通過所有過濾條件，接受回報
            return True

        except Exception as e:
            # 出錯時拒絕，更安全
            return False

    def register_order_id(self, order_id: str):
        """註冊我們下的訂單ID"""
        if hasattr(self, '_known_order_ids'):
            self._known_order_ids.add(order_id)
            console_enabled = getattr(self, 'console_enabled', True)
            if console_enabled:
                print(f"[REPLY_FILTER] 📝 註冊訂單ID: {order_id}")

    def enable_order_reply_processing(self):
        """手動啟用訂單回報處理"""
        self._manual_order_started = True
        console_enabled = getattr(self, 'console_enabled', True)
        if console_enabled:
            print(f"[REPLY_FILTER] ✅ 手動啟用回報處理 - 開始接受新的訂單回報")

    def disable_order_reply_processing(self):
        """手動停用訂單回報處理"""
        self._manual_order_started = False
        console_enabled = getattr(self, 'console_enabled', True)
        if console_enabled:
            print(f"[REPLY_FILTER] 🛑 手動停用回報處理 - 拒絕所有訂單回報")

    def check_multi_group_exit_conditions(self, price, time_str):
        """檢查多組策略出場條件 - 使用統一出場管理器"""
        try:
            if not self.multi_group_risk_engine:
                if self.console_enabled:
                    print(f"[RISK_DEBUG] ❌ 風險管理引擎未初始化")
                return

            # 🔍 DEBUG: 風險管理引擎調用追蹤 (每50次輸出一次)
            if not hasattr(self, '_risk_call_count'):
                self._risk_call_count = 0
            self._risk_call_count += 1

            if self.console_enabled and self._risk_call_count % 50 == 0:
                print(f"[RISK_DEBUG] 🔍 風險管理引擎調用: 第{self._risk_call_count}次 @{price:.0f}")

                # 🔍 DEBUG: 檢查活躍部位數量
                try:
                    active_positions = self.multi_group_db_manager.get_all_active_positions()
                    print(f"[RISK_DEBUG] 📊 活躍部位數量: {len(active_positions)}")

                    for pos in active_positions[:3]:  # 只顯示前3個
                        print(f"[RISK_DEBUG]   部位{pos.get('id')}: {pos.get('direction')} "
                              f"@{pos.get('entry_price', 'N/A')} 狀態:{pos.get('order_status', 'N/A')}")
                except Exception as debug_error:
                    print(f"[RISK_DEBUG] ❌ 檢查活躍部位失敗: {debug_error}")

            # 檢查所有活躍部位的出場條件
            exit_actions = self.multi_group_risk_engine.check_all_exit_conditions(price, time_str)

            # 🔧 修正：使用統一出場管理器執行出場動作
            if exit_actions and hasattr(self.multi_group_risk_engine, 'execute_exit_actions'):
                success_count = self.multi_group_risk_engine.execute_exit_actions(exit_actions)

                if success_count > 0:
                    print(f"[MULTI_EXIT] ✅ 成功執行 {success_count}/{len(exit_actions)} 個出場動作")
                elif len(exit_actions) > 0:
                    print(f"[MULTI_EXIT] ❌ 出場動作執行失敗: {len(exit_actions)} 個動作")

            # 🔧 保留：舊版本相容性處理 (如果統一出場管理器不可用)
            elif exit_actions:
                print(f"[MULTI_EXIT] ⚠️ 統一出場管理器不可用，使用舊版出場邏輯")
                for action in exit_actions:
                    success = self.multi_group_position_manager.update_position_exit(
                        position_id=action['position_id'],
                        exit_price=action['exit_price'],
                        exit_time=action['exit_time'],
                        exit_reason=action['exit_reason'],
                        pnl=action['pnl']
                    )

                if success and self.multi_group_logger:
                    self.multi_group_logger.position_exit(
                        f"{action['exit_reason']} @ {action['exit_price']}",
                        group_id=action.get('group_id', 0),
                        position_id=action['position_id'],
                        pnl=action['pnl']
                    )

                    # 更新保護性停損
                    if action['exit_reason'] == '移動停利':
                        self.multi_group_risk_engine.update_protective_stop_loss(
                            action['position_id'],
                            action.get('group_id', 0)
                        )

        except Exception as e:
            if self.multi_group_logger:
                self.multi_group_logger.system_error(f"多組風險管理檢查失敗: {e}")

    def configure_monitor_settings(self, interval_seconds=5, timeout_seconds=10):
        """配置監控設定

        Args:
            interval_seconds: 檢查間隔（秒）
            timeout_seconds: 報價中斷判定時間（秒）
        """
        try:
            self.monitor_interval = interval_seconds * 1000  # 轉換為毫秒
            self.quote_timeout_threshold = max(1, timeout_seconds // interval_seconds)

            print(f"🔧 [MONITOR] 監控設定已更新:")
            print(f"   檢查間隔: {interval_seconds}秒")
            print(f"   中斷判定: {timeout_seconds}秒無報價")
            print(f"   檢查次數閾值: {self.quote_timeout_threshold}")

        except Exception as e:
            print(f"❌ [MONITOR] 監控設定更新失敗: {e}")

    def monitor_strategy_status(self):
        """監控策略狀態 - 仿照報價監控的智能提醒機制"""
        try:
            # 🔧 檢查監控開關
            if not getattr(self, 'monitoring_enabled', True):
                return

            # 檢查策略是否啟動
            if not getattr(self, 'strategy_enabled', False):
                # 策略未啟動，不需要監控
                return

            # 獲取當前策略活動統計
            current_activity = self.monitoring_stats.get('strategy_activity_count', 0)
            last_activity = self.monitoring_stats.get('last_strategy_activity', 0)
            current_time = time.time()

            # 檢查策略是否有活動（最近10秒內有活動）
            if current_time - last_activity < 10:
                new_strategy_status = "策略運行中"
            else:
                new_strategy_status = "策略中斷"

            # 獲取之前的狀態
            previous_strategy_status = self.monitoring_stats.get('strategy_status', '未知')

            # 更新狀態
            self.monitoring_stats['strategy_status'] = new_strategy_status

            # 🔧 簡化提醒邏輯，避免複雜字符串操作
            if previous_strategy_status != new_strategy_status:
                if new_strategy_status == "策略運行中":
                    print("✅ [MONITOR] 策略恢復正常")
                else:
                    print("❌ [MONITOR] 策略中斷")

        except Exception as e:
            # 靜默處理，不影響主監控邏輯
            pass

    def create_product_selection_panel(self, parent_frame):
        """創建商品選擇面板 - 最低風險實施"""
        try:
            # 商品選項定義
            self.PRODUCT_OPTIONS = {
                "MTX00": "小台指當月",
                "TM0000": "微型台指當月",
                "MXF00": "小台指次月",
                "TMF00": "微型台指次月"
            }

            # 創建面板
            product_frame = ttk.LabelFrame(parent_frame, text="📊 報價商品選擇", padding=5)
            product_frame.pack(fill="x", pady=5)

            # 商品選擇行
            product_row = ttk.Frame(product_frame)
            product_row.pack(fill="x", pady=2)

            # 商品選擇標籤
            ttk.Label(product_row, text="商品:").pack(side="left")

            # 商品下拉選單 - 初始化為當前配置值
            current_product = self.config.get('DEFAULT_PRODUCT', 'MTX00')
            self.product_var = tk.StringVar(value=current_product)
            self.product_combo = ttk.Combobox(product_row, textvariable=self.product_var,
                                             values=list(self.PRODUCT_OPTIONS.keys()),
                                             state="readonly", width=10)
            self.product_combo.pack(side="left", padx=5)

            # 商品說明標籤
            desc = self.PRODUCT_OPTIONS.get(current_product, "未知商品")
            self.product_desc = ttk.Label(product_row, text=desc, foreground="blue")
            self.product_desc.pack(side="left", padx=10)

            # 狀態顯示
            self.product_status = ttk.Label(product_row, text="(未訂閱)", foreground="gray")
            self.product_status.pack(side="left", padx=5)

            # 綁定選擇變更事件
            self.product_combo.bind('<<ComboboxSelected>>', self.on_product_selection_changed)

            # 初始化時更新訂閱按鈕文字
            if hasattr(self, 'btn_subscribe_quote'):
                self.btn_subscribe_quote.config(text=f"訂閱{current_product}")

            print(f"✅ [PRODUCT] 商品選擇面板初始化完成，當前商品: {current_product}")

        except Exception as e:
            print(f"❌ [PRODUCT] 商品選擇面板創建錯誤: {e}")

    def on_product_selection_changed(self, event=None):
        """商品選擇變更事件 - 只更新顯示，不影響現有功能"""
        try:
            selected_product = self.product_var.get()

            # 更新商品說明
            desc = self.PRODUCT_OPTIONS.get(selected_product, "未知商品")
            self.product_desc.config(text=desc)

            # 更新配置變數（不影響當前運行）
            self.config['DEFAULT_PRODUCT'] = selected_product

            # 更新訂閱按鈕文字（如果按鈕存在）
            if hasattr(self, 'btn_subscribe_quote'):
                self.btn_subscribe_quote.config(text=f"訂閱{selected_product}")

            # Console提示
            print(f"📊 [PRODUCT] 商品選擇變更為: {selected_product} ({desc})")
            print("💡 [PRODUCT] 新商品將在下次報價訂閱時生效")

        except Exception as e:
            print(f"❌ [PRODUCT] 商品選擇變更錯誤: {e}")

    def run(self):
        """執行應用程式"""
        self.add_log("🚀 群益簡化整合交易系統啟動")
        self.add_log(f"📋 期貨帳號: {self.config['FUTURES_ACCOUNT']}")
        self.add_log(f"📋 預設商品: {self.config['DEFAULT_PRODUCT']}")
        self.add_log("💡 請點擊「登入」開始使用")

        # 顯示Queue架構狀態
        if QUEUE_INFRASTRUCTURE_AVAILABLE:
            self.add_log("✅ Queue基礎設施可用，可使用Queue模式避免GIL錯誤")
        else:
            self.add_log("⚠️ Queue基礎設施不可用，將使用傳統模式")

        # 啟動主事件循環
        self.root.mainloop()

    # 🔧 移除：process_exit_order_reply 方法
    # 出場回報處理已整合到簡化追蹤器的FIFO邏輯中

    # 🔧 移除：_find_position_by_seq_no 方法
    # 🔧 移除：_schedule_exit_retry 方法
    # 出場追價已整合到簡化追蹤器的FIFO邏輯中，不再依賴序號查找

    def _calculate_exit_retry_price(self, original_direction: str, retry_count: int) -> Optional[float]:
        """
        計算平倉追價價格

        Args:
            original_direction: 原始部位方向 (LONG/SHORT)
            retry_count: 重試次數

        Returns:
            float: 追價價格，失敗返回None

        平倉追價邏輯：
        - 多單平倉(SELL): 使用BID1 - retry_count點 (向下追價，更容易成交)
        - 空單平倉(BUY): 使用ASK1 + retry_count點 (向上追價，更容易成交)
        """
        try:
            product = "TM0000"  # 預設使用微型台指

            if not original_direction:
                if self.console_enabled:
                    print(f"[MAIN] ❌ 無法取得原始部位方向")
                return None

            # 取得當前報價
            current_ask1 = None
            current_bid1 = None

            # 方法1: 從下單管理器取得報價
            if hasattr(self, 'virtual_real_order_manager') and self.virtual_real_order_manager:
                try:
                    if hasattr(self.virtual_real_order_manager, 'get_ask1_price'):
                        current_ask1 = self.virtual_real_order_manager.get_ask1_price(product)
                    if hasattr(self.virtual_real_order_manager, 'get_bid1_price'):
                        current_bid1 = self.virtual_real_order_manager.get_bid1_price(product)
                except:
                    pass

            # 方法2: 從報價管理器取得報價
            if (not current_ask1 or not current_bid1) and hasattr(self, 'quote_manager') and self.quote_manager:
                try:
                    quote_data = self.quote_manager.get_current_quote(product)
                    if quote_data:
                        current_ask1 = quote_data.get('ask1', 0)
                        current_bid1 = quote_data.get('bid1', 0)
                except:
                    pass

            # 檢查是否成功獲取市價
            if current_ask1 > 0 and current_bid1 > 0:
                if original_direction.upper() == "LONG":
                    # 🔧 多單平倉：使用BID1 - retry_count點 (向下追價)
                    retry_price = current_bid1 - retry_count
                    if self.console_enabled:
                        print(f"[MAIN] 🔄 多單平倉追價計算: BID1({current_bid1}) - {retry_count} = {retry_price}")
                    return retry_price
                elif original_direction.upper() == "SHORT":
                    # 🔧 空單平倉：使用ASK1 + retry_count點 (向上追價)
                    retry_price = current_ask1 + retry_count
                    if self.console_enabled:
                        print(f"[MAIN] 🔄 空單平倉追價計算: ASK1({current_ask1}) + {retry_count} = {retry_price}")
                    return retry_price
            else:
                if self.console_enabled:
                    print(f"[MAIN] ❌ 無法獲取有效市價: ASK1={current_ask1}, BID1={current_bid1}")

            if self.console_enabled:
                print(f"[MAIN] ❌ 無法計算平倉追價，使用預設邏輯")
            return None

        except Exception as e:
            if self.console_enabled:
                print(f"[MAIN] ❌ 計算平倉追價失敗: {e}")
            return None


if __name__ == "__main__":
    app = SimpleIntegratedApp()
    app.run()
