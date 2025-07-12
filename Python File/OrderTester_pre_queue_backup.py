#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
群益證券API下單測試程式 - 策略整合版本
整合登入、下單、回報、策略功能

🏷️ STRATEGY_INTEGRATION_VERSION_2025_07_01
✅ 基於穩定版本進行策略整合
✅ 包含：下單、回報、報價、查詢、策略功能
✅ 基於群益官方案例，確保穩定性
🎯 新增策略整合功能，直接使用報價事件

📋 版本特性:
- 穩定的MTX00期貨下單功能
- 即時OnNewData事件回報
- 即時OnNotifyTicksLONG報價
- GetOpenInterestGW部位查詢
- GetOrderReport智慧單查詢
- 🆕 策略面板整合
- 🆕 開盤區間計算
- 🆕 直接報價事件處理
- 零GIL錯誤目標，可長時間運行
"""

import os
import sys
import time
import threading
import re
import tkinter as tk
from tkinter import ttk, messagebox
import logging
import comtypes.client
from enum import Enum, auto
from dataclasses import dataclass, field
from decimal import Decimal
from datetime import datetime

# 導入我們的模組
from order.future_order import FutureOrderFrame
from reply.order_reply import OrderReplyFrame
from quote.future_quote import FutureQuoteFrame
from query.position_query import PositionQueryFrame

# 🔧 GIL修復：移除過渡期功能 - 價格橋接和TCP伺服器
# 策略已整合，不再需要這些過渡功能

# 設定日誌
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# 策略分頁暫時移除，確保基礎功能穩定
# try:
#     from strategy.strategy_tab import StrategyTab
#     STRATEGY_AVAILABLE = True
# except ImportError as e:
#     STRATEGY_AVAILABLE = False
#     logger.warning(f"策略模組未載入: {e}")
# 策略功能啟用 - 使用安全的數據讀取方式
STRATEGY_AVAILABLE = True

# ==================== 策略下單管理類別 ====================

# 新增：交易模式枚舉
class TradingMode(Enum):
    SIMULATION = "模擬"
    LIVE = "實單"

# 新增：策略下單管理器
class StrategyOrderManager:
    """策略下單管理器 - 橋接策略邏輯和實際下單"""

    def __init__(self, future_order_frame, trading_mode=TradingMode.SIMULATION):
        """
        初始化策略下單管理器

        Args:
            future_order_frame: 期貨下單框架實例
            trading_mode: 交易模式 (模擬/實單)
        """
        self.future_order_frame = future_order_frame
        self.trading_mode = trading_mode
        self.order_executor = future_order_frame.order_executor if future_order_frame else None

        # 商品設定
        self.current_product = "MTX00"  # 預設小台指

        # 非同步下單追蹤
        self.pending_orders = {}      # 暫存下單請求，等待 OnAsyncOrder 確認
        self.strategy_orders = {}     # 已確認的策略委託 (key: 委託序號)

        # 設置回調函數
        if self.order_executor:
            self.order_executor.strategy_callback = self.on_order_result

        # 設置回報監聽
        self.setup_reply_log_monitoring()

        # 預留：報價監控和委託追蹤 (從LOG資料獲取)
        self.quote_monitor = None
        self.order_tracker = None
        self.log_quote_parser = None

    def set_trading_mode(self, mode):
        """設定交易模式"""
        print(f"[策略下單DEBUG] set_trading_mode 被調用，舊模式: {self.trading_mode}, 新模式: {mode}")
        self.trading_mode = mode
        print(f"[策略下單] 交易模式切換為: {mode.value}")
        print(f"[策略下單DEBUG] 確認當前模式: {self.trading_mode}")

    def on_order_result(self, order_seq_no, result_type, error_code=None):
        """接收非同步下單結果"""
        try:
            if result_type == 'ORDER_SUCCESS':
                # 委託成功，將暫存的下單資訊轉移到正式追蹤
                print(f"[策略下單] ✅ 委託確認成功，序號: {order_seq_no}")

                # 查找對應的暫存委託
                pending_key = None
                for key, order_info in self.pending_orders.items():
                    if order_info['status'] == 'WAITING_CONFIRM':
                        # 找到第一個等待確認的委託
                        pending_key = key
                        break

                if pending_key:
                    # 轉移到正式追蹤
                    order_info = self.pending_orders.pop(pending_key)
                    order_info['order_seq_no'] = order_seq_no
                    order_info['status'] = 'CONFIRMED'
                    self.strategy_orders[order_seq_no] = order_info

                    print(f"[策略下單] 📋 委託追蹤: {order_info['direction']} {order_info['quantity']}口 @{order_info['price']}")

            elif result_type == 'ORDER_FAILED':
                # 委託失敗
                print(f"[策略下單] ❌ 委託失敗: {order_seq_no} (錯誤代碼: {error_code})")

                # 清理暫存的失敗委託
                failed_keys = []
                for key, order_info in self.pending_orders.items():
                    if order_info['status'] == 'WAITING_CONFIRM':
                        failed_keys.append(key)

                # 移除失敗的委託 (簡化處理，移除第一個等待確認的)
                if failed_keys:
                    self.pending_orders.pop(failed_keys[0])

        except Exception as e:
            print(f"[策略下單] ❌ 處理下單結果失敗: {e}")

    def place_entry_order(self, direction, price, quantity=1, order_type="FOK"):
        """
        建倉下單 - 支援非同步追蹤

        Args:
            direction: 'LONG' 或 'SHORT'
            price: 委託價格
            quantity: 委託數量
            order_type: 委託類型

        Returns:
            dict: 下單結果
        """
        print(f"[策略下單DEBUG] place_entry_order 被調用")
        print(f"[策略下單DEBUG] 參數: direction={direction}, price={price}, quantity={quantity}, order_type={order_type}")
        print(f"[策略下單DEBUG] 交易模式: {self.trading_mode}")
        print(f"[策略下單DEBUG] order_executor: {self.order_executor}")

        if self.trading_mode == TradingMode.SIMULATION:
            # 模擬模式 - 直接返回成功
            print(f"[策略下單] 模擬建倉: {direction} {quantity}口 @{price}")
            return {
                'success': True,
                'message': f'模擬建倉成功: {direction} {quantity}口 @{price}',
                'order_id': f'SIM_{direction}_{int(price)}_{quantity}',
                'mode': 'SIMULATION'
            }
        else:
            # 實單模式 - 調用實際下單 (非同步)
            print(f"[策略下單DEBUG] 進入實單模式分支")
            if not self.order_executor:
                print(f"[策略下單DEBUG] order_executor 為 None，返回失敗")
                return {
                    'success': False,
                    'message': '下單執行器未初始化',
                    'order_id': None,
                    'mode': 'LIVE'
                }

            api_direction = 'BUY' if direction == 'LONG' else 'SELL'
            print(f"[策略下單] 實單建倉: {direction} {quantity}口 @{price}")

            # 先暫存下單資訊
            pending_key = f"{direction}_{price}_{quantity}_{len(self.pending_orders)}"
            self.pending_orders[pending_key] = {
                'direction': direction,
                'price': price,
                'quantity': quantity,
                'order_type': order_type,
                'status': 'WAITING_CONFIRM',
                'timestamp': time.time()
            }

            # 執行非同步下單 - 建倉使用新倉
            result = self.order_executor.strategy_order(
                direction=api_direction,
                price=price,
                quantity=quantity,
                order_type=order_type,
                product=self.current_product,
                new_close=0  # 建倉 = 新倉
            )
            result['mode'] = 'LIVE'
            return result

    def place_exit_order(self, direction, price, quantity=1, order_type="FOK"):
        """
        出場下單

        Args:
            direction: 'LONG' 或 'SHORT' (原部位方向)
            price: 委託價格
            quantity: 委託數量
            order_type: 委託類型

        Returns:
            dict: 下單結果
        """
        # 出場方向與建倉方向相反
        exit_direction = 'SHORT' if direction == 'LONG' else 'LONG'

        if self.trading_mode == TradingMode.SIMULATION:
            # 模擬模式 - 直接返回成功
            print(f"[策略下單] 模擬出場: {exit_direction} {quantity}口 @{price}")
            return {
                'success': True,
                'message': f'模擬出場成功: {exit_direction} {quantity}口 @{price}',
                'order_id': f'SIM_EXIT_{exit_direction}_{int(price)}_{quantity}',
                'mode': 'SIMULATION'
            }
        else:
            # 實單模式 - 調用實際下單
            if not self.order_executor:
                return {
                    'success': False,
                    'message': '下單執行器未初始化',
                    'order_id': None,
                    'mode': 'LIVE'
                }

            api_direction = 'BUY' if exit_direction == 'LONG' else 'SELL'
            print(f"[策略下單] 實單出場: {exit_direction} {quantity}口 @{price}")

            # 執行非同步下單 - 出場使用平倉
            result = self.order_executor.strategy_order(
                direction=api_direction,
                price=price,
                quantity=quantity,
                order_type=order_type,
                product=self.current_product,
                new_close=1  # 出場 = 平倉
            )
            result['mode'] = 'LIVE'
            return result

    # 預留：五檔報價和刪單追價功能 (從LOG資料獲取)
    def setup_quote_monitoring_from_log(self):
        """預留：從LOG資料設置五檔報價監控"""
        # 未來可以解析現有的報價LOG來獲取五檔資料
        pass

    def setup_order_chasing_from_log(self):
        """預留：從LOG資料設置刪單追價機制"""
        # 未來整合委託查詢和刪單重下功能，並從LOG監控價格變化
        pass

    def setup_reply_log_monitoring(self):
        """設置回報LOG監聽 - 監聽委託成功和成交回報"""
        try:
            # 添加到 reply.order_reply 的logger
            reply_logger = logging.getLogger('reply.order_reply')

            # 檢查是否已有策略回報處理器
            if not hasattr(self, 'reply_log_handler'):
                self.reply_log_handler = StrategyReplyLogHandler(self)
                reply_logger.addHandler(self.reply_log_handler)

            print("[策略下單] ✅ 回報LOG監聽設置完成")
        except Exception as e:
            print(f"[策略下單] ❌ 回報LOG監聽設置失敗: {e}")

    def process_reply_log(self, log_message):
        """處理回報LOG - 解析委託序號並更新策略追蹤"""
        try:
            # 解析委託成功回報
            if "✅【委託成功】序號:" in log_message:
                # 提取序號
                match = re.search(r'序號:(\d+)', log_message)
                if match:
                    seq_no = match.group(1)

                    # 檢查是否有等待確認的策略委託
                    if self.pending_orders:
                        # 找到第一個等待確認的委託
                        for key, order_info in list(self.pending_orders.items()):
                            if order_info['status'] == 'WAITING_CONFIRM':
                                # 轉移到正式追蹤
                                order_info = self.pending_orders.pop(key)
                                order_info['order_seq_no'] = seq_no
                                order_info['status'] = 'CONFIRMED'
                                self.strategy_orders[seq_no] = order_info

                                print(f"[策略下單] 📋 委託確認: {order_info['direction']} {order_info['quantity']}口 @{order_info['price']} (序號:{seq_no})")
                                break

            # 解析成交回報
            elif "🎉【成交】序號:" in log_message:
                match = re.search(r'序號:(\d+)', log_message)
                if match:
                    seq_no = match.group(1)

                    # 檢查是否為策略委託的成交
                    if seq_no in self.strategy_orders:
                        order_info = self.strategy_orders[seq_no]
                        order_info['status'] = 'FILLED'

                        print(f"[策略下單] 🎉 成交確認: {order_info['direction']} {order_info['quantity']}口 (序號:{seq_no})")

                        # 如果是建倉成交，開始追蹤停損停利
                        if order_info.get('new_close', 0) == 0:  # 新倉
                            print(f"[策略下單] 🎯 建倉成交，開始追蹤停損停利")

            # 解析取消回報
            elif "🗑️【委託取消】序號:" in log_message or "🗑️【取消】序號:" in log_message:
                match = re.search(r'序號:(\d+)', log_message)
                if match:
                    seq_no = match.group(1)

                    # 檢查是否為策略委託的取消
                    if seq_no in self.strategy_orders:
                        order_info = self.strategy_orders[seq_no]
                        order_info['status'] = 'CANCELLED'

                        print(f"[策略下單] 🗑️ 委託取消: {order_info['direction']} {order_info['quantity']}口 (序號:{seq_no})")

        except Exception as e:
            print(f"[策略下單] ❌ 回報LOG處理失敗: {e}")

    def get_strategy_orders_status(self):
        """獲取策略委託狀態 - 用於查看追蹤情況"""
        print(f"\n📊 策略委託狀態:")
        print(f"等待確認: {len(self.pending_orders)} 筆")
        print(f"已確認: {len([o for o in self.strategy_orders.values() if o['status'] == 'CONFIRMED'])} 筆")
        print(f"已成交: {len([o for o in self.strategy_orders.values() if o['status'] == 'FILLED'])} 筆")
        print(f"已取消: {len([o for o in self.strategy_orders.values() if o['status'] == 'CANCELLED'])} 筆")

        if self.strategy_orders:
            print(f"\n📋 詳細記錄:")
            for seq_no, order_info in self.strategy_orders.items():
                print(f"  序號:{seq_no} | {order_info['direction']} {order_info['quantity']}口 @{order_info['price']} | {order_info['status']}")

        return {
            'pending': len(self.pending_orders),
            'confirmed': len([o for o in self.strategy_orders.values() if o['status'] == 'CONFIRMED']),
            'filled': len([o for o in self.strategy_orders.values() if o['status'] == 'FILLED']),
            'cancelled': len([o for o in self.strategy_orders.values() if o['status'] == 'CANCELLED'])
        }

# 新增：策略回報LOG處理器
class StrategyReplyLogHandler(logging.Handler):
    """策略回報LOG處理器 - 監聽委託和成交回報"""

    def __init__(self, strategy_order_manager):
        super().__init__()
        self.strategy_order_manager = strategy_order_manager

    def emit(self, record):
        try:
            message = record.getMessage()

            # 監聽回報相關LOG
            if any(keyword in message for keyword in ["【委託成功】", "【成交】", "【委託取消】", "【取消】"]):
                self.strategy_order_manager.process_reply_log(message)

        except Exception as e:
            pass  # 忽略錯誤，避免影響LOG系統

# ==================== 停損管理核心類別 ====================

class StopLossType(Enum):
    """停損類型枚舉"""
    RANGE_BOUNDARY = auto()  # 區間邊界停損
    OPENING_PRICE = auto()   # 開盤價停損
    FIXED_POINTS = auto()    # 固定點數停損

@dataclass
class LotRule:
    """單一口部位的出場規則配置"""
    use_trailing_stop: bool = True                          # 是否使用移動停利
    fixed_tp_points: Decimal | None = None                  # 固定停利點數
    trailing_activation: Decimal | None = None              # 移動停利啟動點數
    trailing_pullback: Decimal | None = None                # 移動停利回撤比例
    protective_stop_multiplier: Decimal | None = None       # 保護性停損倍數

@dataclass
class StrategyConfig:
    """策略配置的中央控制面板"""
    trade_size_in_lots: int = 3                            # 交易口數
    stop_loss_type: StopLossType = StopLossType.RANGE_BOUNDARY  # 停損類型
    fixed_stop_loss_points: Decimal = Decimal(15)          # 固定停損點數
    lot_rules: list[LotRule] = field(default_factory=list) # 各口停損規則

# 全域變數
sk = None
m_pSKCenter = None
m_pSKOrder = None
m_pSKQuote = None
m_pSKReply = None
SKReplyEvent = None
SKReplyLibEventHandler = None

def initialize_skcom():
    """初始化SKCOM API"""
    global sk
    
    try:
        logger.info("🔄 初始化SKCOM API...")
        
        # 生成COM元件的Python包裝
        comtypes.client.GetModule(r'.\SKCOM.dll')
        
        # 導入生成的SKCOMLib
        import comtypes.gen.SKCOMLib as sk_module
        sk = sk_module
        
        logger.info("✅ SKCOM API初始化成功")
        return True
        
    except Exception as e:
        logger.error(f"❌ SKCOM API初始化失敗: {e}")
        return False

def initialize_skcom_objects():
    """初始化SKCOM物件"""
    global m_pSKCenter, m_pSKOrder, m_pSKQuote, m_pSKReply, SKReplyEvent, SKReplyLibEventHandler
    
    if sk is None:
        logger.error("❌ SKCOM API 未初始化")
        return False
    
    try:
        # 建立物件
        logger.info("🔄 建立SKCenterLib物件...")
        m_pSKCenter = comtypes.client.CreateObject(sk.SKCenterLib, interface=sk.ISKCenterLib)
        
        logger.info("🔄 建立SKReplyLib物件...")
        m_pSKReply = comtypes.client.CreateObject(sk.SKReplyLib, interface=sk.ISKReplyLib)
        
        logger.info("🔄 建立SKOrderLib物件...")
        m_pSKOrder = comtypes.client.CreateObject(sk.SKOrderLib, interface=sk.ISKOrderLib)
        
        logger.info("🔄 建立SKQuoteLib物件...")
        m_pSKQuote = comtypes.client.CreateObject(sk.SKQuoteLib, interface=sk.ISKQuoteLib)
        
        # 註冊OnReplyMessage事件
        logger.info("🔄 註冊OnReplyMessage事件...")
        register_reply_message_event()
        
        logger.info("✅ 所有SKCOM物件建立成功")
        return True
        
    except Exception as e:
        logger.error(f"❌ SKCOM物件建立失敗: {e}")
        return False

def register_reply_message_event():
    """註冊OnReplyMessage事件 - 使用線程安全處理"""
    global SKReplyEvent, SKReplyLibEventHandler

    try:
        # 建立事件處理類別
        class SKReplyLibEvent():
            def OnReplyMessage(self, bstrUserID, bstrMessages):
                try:
                    # 使用線程安全的方式處理，避免GIL錯誤
                    # 不直接調用logger，因為可能在不同線程中
                    nConfirmCode = -1
                    # 簡化處理，避免複雜的字符串操作
                    return nConfirmCode
                except:
                    # 如果發生任何錯誤，安全返回避免崩潰
                    return -1

        # 建立事件物件並註冊
        SKReplyEvent = SKReplyLibEvent()
        SKReplyLibEventHandler = comtypes.client.GetEvents(m_pSKReply, SKReplyEvent)

        logger.info("✅ OnReplyMessage事件註冊成功 (線程安全版)")
        return True

    except Exception as e:
        logger.warning(f"⚠️ OnReplyMessage事件註冊失敗: {e}")
        return False

class OrderTesterApp(tk.Tk):
    """下單測試主應用程式"""

    def __init__(self):
        super().__init__()

        self.title("群益證券API期貨下單測試程式")
        self.geometry("1000x800")

        # 🔧 GIL錯誤修復：添加線程安全鎖
        self.quote_lock = threading.Lock()
        self.strategy_lock = threading.Lock()
        self.ui_lock = threading.Lock()
        self.order_lock = threading.Lock()

        # TCP價格伺服器狀態
        self.tcp_server_enabled = False
        self.tcp_server_running = False

        # 策略相關初始化
        self.strategy_panel = None
        self.strategy_quote_callback = None

        # 停損管理配置初始化
        self.strategy_config = self.create_default_strategy_config()

        # 交易記錄系統初始化
        self.trading_logger = TradingLogger()

        # 🎯 關鍵：在程式啟動時就設定LOG處理器
        self.setup_strategy_log_handler()

        # 初始化SKCOM
        self.initialize_skcom()

        # 建立UI
        self.create_widgets()

        # 設定關閉事件
        self.protocol("WM_DELETE_WINDOW", self.on_closing)
    
    def initialize_skcom(self):
        """初始化SKCOM環境"""
        if not initialize_skcom():
            messagebox.showerror("初始化錯誤", "SKCOM API初始化失敗")
            self.quit()
            return
        
        if not initialize_skcom_objects():
            messagebox.showerror("初始化錯誤", "SKCOM物件初始化失敗")
            self.quit()
            return
    
    def create_widgets(self):
        """建立UI控件"""
        # 建立筆記本控件
        notebook = ttk.Notebook(self)
        notebook.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # 登入頁面
        login_frame = tk.Frame(notebook)
        notebook.add(login_frame, text="登入")
        self.create_login_page(login_frame)
        
        # 下單頁面
        order_frame = tk.Frame(notebook)
        notebook.add(order_frame, text="期貨下單")

        # 建立SKCOM物件字典
        skcom_objects = {
            'SKCenter': m_pSKCenter,
            'SKOrder': m_pSKOrder,
            'SKQuote': m_pSKQuote,
            'SKReply': m_pSKReply
        }

        # 建立期貨下單框架
        self.future_order_frame = FutureOrderFrame(order_frame, skcom_objects)
        self.future_order_frame.pack(fill=tk.BOTH, expand=True)

        # 期貨報價查詢頁面
        quote_frame = tk.Frame(notebook)
        notebook.add(quote_frame, text="期貨報價查詢")

        # 建立期貨報價查詢框架
        self.future_quote_frame = FutureQuoteFrame(quote_frame, skcom_objects)
        self.future_quote_frame.pack(fill=tk.BOTH, expand=True)

        # 部位查詢頁面
        position_frame = tk.Frame(notebook)
        notebook.add(position_frame, text="部位查詢")

        # 建立部位查詢框架
        self.position_query_frame = PositionQueryFrame(position_frame, skcom_objects)
        self.position_query_frame.pack(fill=tk.BOTH, expand=True)

        # 回報頁面
        reply_frame = tk.Frame(notebook)
        notebook.add(reply_frame, text="下單回報")

        # 建立回報框架
        self.order_reply_frame = OrderReplyFrame(reply_frame, skcom_objects)
        self.order_reply_frame.pack(fill=tk.BOTH, expand=True)

        # 策略分頁 - 階段1：基礎策略面板
        if STRATEGY_AVAILABLE:
            strategy_frame = tk.Frame(notebook)
            notebook.add(strategy_frame, text="🎯 策略交易")

            # 建立簡化策略面板
            self.create_strategy_panel(strategy_frame, skcom_objects)

            logger.info("✅ 策略交易分頁已載入")
        else:
            logger.warning("⚠️ 策略交易分頁未載入")
    
    def create_login_page(self, parent):
        """建立登入頁面"""
        # 登入框架
        login_frame = tk.LabelFrame(parent, text="群益證券API登入", padx=10, pady=10)
        login_frame.pack(fill=tk.X, padx=10, pady=10)
        
        # 身分證字號
        tk.Label(login_frame, text="身分證字號:").grid(column=0, row=0, sticky=tk.W, padx=5, pady=5)
        self.entry_user_id = tk.Entry(login_frame, width=15)
        self.entry_user_id.grid(column=1, row=0, padx=5, pady=5)

        # 記住身分證字號選項
        self.var_remember_id = tk.BooleanVar()
        self.check_remember = tk.Checkbutton(login_frame, text="記住身分證字號",
                                           variable=self.var_remember_id)
        self.check_remember.grid(column=2, row=0, padx=5, pady=5)

        # 載入記住的身分證字號 (稍後在UI創建完成後調用)
        
        # 密碼
        tk.Label(login_frame, text="密碼:").grid(column=0, row=1, sticky=tk.W, padx=5, pady=5)
        self.entry_password = tk.Entry(login_frame, width=15, show="*")
        self.entry_password.grid(column=1, row=1, padx=5, pady=5)

        # 測試階段自動填入密碼
        self.entry_password.insert(0, "kkd5ysUCC")
        
        # 登入狀態
        tk.Label(login_frame, text="登入狀態:").grid(column=2, row=0, sticky=tk.W, padx=(20,5), pady=5)
        self.label_login_status = tk.Label(login_frame, text="未登入", fg="red")
        self.label_login_status.grid(column=3, row=0, padx=5, pady=5)
        
        # 登入按鈕
        self.btn_login = tk.Button(login_frame, text="登入", command=self.login,
                                  bg="#4169E1", fg="white", width=10)
        self.btn_login.grid(column=2, row=1, padx=(20,5), pady=5)
        
        # 登出按鈕
        self.btn_logout = tk.Button(login_frame, text="登出", command=self.logout,
                                   bg="#DC143C", fg="white", width=10, state="disabled")
        self.btn_logout.grid(column=3, row=1, padx=5, pady=5)

        # 🔧 GIL修復：移除TCP價格伺服器UI區域
        # 策略已整合，不再需要TCP價格廣播功能

        # 訊息顯示
        msg_frame = tk.LabelFrame(parent, text="登入訊息", padx=5, pady=5)
        msg_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        self.text_login_message = tk.Text(msg_frame, height=15)
        scrollbar = tk.Scrollbar(msg_frame, orient=tk.VERTICAL, command=self.text_login_message.yview)
        self.text_login_message.configure(yscrollcommand=scrollbar.set)
        
        self.text_login_message.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        # 現在UI已創建完成，可以載入記住的身分證字號
        self.load_saved_user_id()
    
    def add_login_message(self, message):
        """添加登入訊息"""
        self.text_login_message.insert(tk.END, message + "\n")
        self.text_login_message.see(tk.END)
        logger.info(message)

    def load_saved_user_id(self):
        """載入記住的身分證字號"""
        try:
            # 嘗試讀取記住的身分證字號
            with open('saved_user_id.txt', 'r', encoding='utf-8') as f:
                saved_id = f.read().strip()
                if saved_id:
                    self.entry_user_id.insert(0, saved_id)
                    self.var_remember_id.set(True)
                    # 安全地添加訊息
                    if hasattr(self, 'text_login_message'):
                        self.add_login_message(f"【載入】已載入記住的身分證字號: {saved_id}")
                    else:
                        logger.info(f"【載入】已載入記住的身分證字號: {saved_id}")
        except FileNotFoundError:
            # 檔案不存在，使用預設值
            pass
        except Exception as e:
            # 安全地添加錯誤訊息
            if hasattr(self, 'text_login_message'):
                self.add_login_message(f"【錯誤】載入身分證字號失敗: {e}")
            else:
                logger.error(f"【錯誤】載入身分證字號失敗: {e}")

    def save_user_id(self, user_id):
        """儲存身分證字號"""
        try:
            if self.var_remember_id.get():
                with open('saved_user_id.txt', 'w', encoding='utf-8') as f:
                    f.write(user_id)
                self.add_login_message(f"【儲存】已記住身分證字號: {user_id}")
            else:
                # 如果不記住，刪除檔案
                try:
                    import os
                    os.remove('saved_user_id.txt')
                    self.add_login_message("【清除】已清除記住的身分證字號")
                except FileNotFoundError:
                    pass
        except Exception as e:
            self.add_login_message(f"【錯誤】儲存身分證字號失敗: {e}")

    def auto_fill_account(self, user_id):
        """根據身分證字號自動填入帳號"""
        # 根據你的身分證字號自動填入期貨帳號
        if user_id:  # 你可以在這裡加上你的身分證字號判斷
            account = "6363839"  # 你的期貨帳號

            # 自動填入期貨下單頁面的帳號
            try:
                if hasattr(self, 'future_order_frame'):
                    self.future_order_frame.entry_account.delete(0, tk.END)
                    self.future_order_frame.entry_account.insert(0, account)
                    self.add_login_message(f"【自動填入】期貨帳號: {account}")
            except Exception as e:
                self.add_login_message(f"【錯誤】自動填入帳號失敗: {e}")
    
    def login(self):
        """登入功能"""
        user_id = self.entry_user_id.get().strip()
        password = self.entry_password.get().strip()
        
        if not user_id or not password:
            messagebox.showerror("錯誤", "請輸入身分證字號和密碼")
            return
        
        if not m_pSKCenter:
            self.add_login_message("【錯誤】SKCenter物件未初始化")
            return
        
        try:
            self.add_login_message(f"【登入】開始登入 - 帳號: {user_id}")
            
            # 執行登入
            nCode = m_pSKCenter.SKCenterLib_Login(user_id, password)
            
            # 取得回傳訊息
            msg_text = m_pSKCenter.SKCenterLib_GetReturnCodeMessage(nCode)
            self.add_login_message(f"【SKCenterLib_Login】{msg_text} (代碼: {nCode})")
            
            if nCode == 0:  # 登入成功
                self.label_login_status.config(text="登入成功", fg="green")
                self.btn_login.config(state="disabled")
                self.btn_logout.config(state="normal")
                self.add_login_message("【成功】群益證券API登入成功！")

                # 儲存身分證字號 (如果勾選記住)
                self.save_user_id(user_id)

                # 自動填入期貨帳號
                self.auto_fill_account(user_id)

                # 自動連線報價主機
                self.auto_connect_quote_server()

                # 不自動連線回報主機，避免GIL錯誤
                # self.auto_connect_reply_server()

                # 移除messagebox避免多線程衝突
                # messagebox.showinfo("登入成功", "群益證券API登入成功！")
                self.add_login_message("【提示】登入成功！已自動開始連線報價主機")
                self.add_login_message("【提示】請手動點擊「連線回報」按鈕啟動即時回報")
            else:
                self.label_login_status.config(text="登入失敗", fg="red")
                self.add_login_message(f"【失敗】登入失敗: {msg_text}")
                messagebox.showerror("登入失敗", f"登入失敗: {msg_text}")
                
        except Exception as e:
            error_msg = f"登入時發生錯誤: {str(e)}"
            self.add_login_message(f"【錯誤】{error_msg}")
            self.label_login_status.config(text="登入錯誤", fg="red")
            messagebox.showerror("登入錯誤", error_msg)
    
    def logout(self):
        """登出功能"""
        try:
            self.add_login_message("【登出】執行登出...")
            
            # 這裡可以加入登出的API調用
            # nCode = m_pSKCenter.SKCenterLib_Logout()
            
            self.label_login_status.config(text="未登入", fg="red")
            self.btn_login.config(state="normal")
            self.btn_logout.config(state="disabled")
            self.add_login_message("【成功】已登出")
            
        except Exception as e:
            self.add_login_message(f"【錯誤】登出時發生錯誤: {str(e)}")

    def auto_connect_quote_server(self):
        """登入成功後自動連線報價主機"""
        try:
            self.add_login_message("【自動連線】開始連線報價主機...")

            # 檢查期貨報價查詢模組是否存在
            if hasattr(self, 'future_quote_frame'):
                # 自動觸發連線報價主機
                self.future_quote_frame.connect_quote_server()
                self.add_login_message("【成功】已自動觸發報價主機連線")
            else:
                self.add_login_message("【跳過】期貨報價查詢模組未初始化")

        except Exception as e:
            self.add_login_message(f"【錯誤】自動連線報價主機失敗: {str(e)}")

    def auto_connect_reply_server(self):
        """登入成功後自動連線回報主機"""
        try:
            self.add_login_message("【自動連線】開始連線回報主機...")

            # 檢查回報模組是否存在
            if hasattr(self, 'order_reply_frame'):
                reply_frame = self.order_reply_frame
                if hasattr(reply_frame, 'connect_reply_server'):
                    # 調用回報模組的連線函數
                    success = reply_frame.connect_reply_server()
                    if success:
                        self.add_login_message("【成功】回報主機連線成功")
                    else:
                        self.add_login_message("【失敗】回報主機連線失敗")
                else:
                    self.add_login_message("【警告】回報模組沒有連線函數")
            else:
                self.add_login_message("【警告】找不到回報模組")

        except Exception as e:
            self.add_login_message(f"【錯誤】自動連線回報主機時發生錯誤: {str(e)}")

    # 🔧 GIL修復：移除TCP伺服器功能 - toggle_tcp_server
    pass

    # 🔧 GIL修復：移除TCP伺服器功能 - start_tcp_server, stop_tcp_server, update_tcp_status
    pass

    def create_strategy_panel(self, parent_frame, skcom_objects):
        """創建簡化策略面板 - 階段1 + 實單功能整合"""
        try:
            logger.info("🎯 開始創建策略面板...")

            # 初始化策略下單管理器
            print(f"[策略DEBUG] 準備初始化策略下單管理器")
            print(f"[策略DEBUG] future_order_frame: {getattr(self, 'future_order_frame', None)}")
            if hasattr(self, 'future_order_frame') and self.future_order_frame:
                print(f"[策略DEBUG] future_order_frame.order_executor: {getattr(self.future_order_frame, 'order_executor', None)}")

            self.strategy_order_manager = StrategyOrderManager(
                future_order_frame=self.future_order_frame,
                trading_mode=TradingMode.SIMULATION  # 預設為模擬模式
            )

            print(f"[策略DEBUG] 策略下單管理器初始化完成")
            print(f"[策略DEBUG] strategy_order_manager.order_executor: {self.strategy_order_manager.order_executor}")
            logger.info("✅ 策略下單管理器初始化完成")

            # 創建策略面板容器
            strategy_container = tk.LabelFrame(parent_frame, text="🎯 開盤區間突破策略",
                                             fg="blue", font=("Arial", 12, "bold"))
            strategy_container.pack(fill="both", expand=True, padx=10, pady=10)

            # 新增：交易模式控制區域
            mode_frame = tk.LabelFrame(strategy_container, text="⚙️ 交易模式", fg="red", font=("Arial", 10, "bold"))
            mode_frame.pack(fill="x", padx=5, pady=5)

            # 模式選擇
            tk.Label(mode_frame, text="當前模式:", font=("Arial", 10)).pack(side="left", padx=5)
            self.trading_mode_var = tk.StringVar(value=TradingMode.SIMULATION.value)
            mode_combo = ttk.Combobox(mode_frame, textvariable=self.trading_mode_var,
                                    values=[TradingMode.SIMULATION.value, TradingMode.LIVE.value],
                                    state="readonly", width=8, font=("Arial", 10))
            mode_combo.pack(side="left", padx=5)
            mode_combo.bind("<<ComboboxSelected>>", self.on_trading_mode_changed)

            # 模式狀態顯示
            self.mode_status_var = tk.StringVar(value="✅ 模擬模式 (安全)")
            tk.Label(mode_frame, textvariable=self.mode_status_var,
                    font=("Arial", 10, "bold"), fg="green").pack(side="left", padx=10)

            # 商品選擇區域
            product_frame = tk.Frame(mode_frame)
            product_frame.pack(side="left", padx=10)

            tk.Label(product_frame, text="商品:", font=("Arial", 10)).pack(side="left", padx=5)
            self.strategy_product_var = tk.StringVar(value="MTX00")
            product_combo = ttk.Combobox(product_frame, textvariable=self.strategy_product_var,
                                       values=["MTX00", "TM0000"],
                                       state="readonly", width=8, font=("Arial", 10))
            product_combo.pack(side="left", padx=5)
            product_combo.bind("<<ComboboxSelected>>", self.on_strategy_product_changed)

            # 商品說明
            tk.Label(product_frame, text="(MTX00:小台指, TM0000:微型台指)",
                    font=("Arial", 8), fg="gray").pack(side="left", padx=5)

            # 進場頻率控制區域
            entry_freq_frame = tk.Frame(mode_frame)
            entry_freq_frame.pack(side="left", padx=10)

            tk.Label(entry_freq_frame, text="進場頻率:", font=("Arial", 10)).pack(side="left", padx=5)
            self.entry_frequency_var = tk.StringVar(value="一天一次")
            freq_combo = ttk.Combobox(entry_freq_frame, textvariable=self.entry_frequency_var,
                                    values=["一天一次", "可重複進場", "測試模式"],
                                    state="readonly", width=10, font=("Arial", 10))
            freq_combo.pack(side="left", padx=5)
            freq_combo.bind("<<ComboboxSelected>>", self.on_entry_frequency_changed)

            # 策略委託狀態查看按鈕
            status_btn = tk.Button(mode_frame, text="📊 查看委託狀態",
                                 command=self.show_strategy_orders_status,
                                 font=("Arial", 9), bg="lightblue")
            status_btn.pack(side="right", padx=5)

            # 重置進場狀態按鈕
            reset_btn = tk.Button(mode_frame, text="🔄 重置進場狀態",
                                command=self.reset_entry_status,
                                font=("Arial", 9), bg="lightyellow")
            reset_btn.pack(side="right", padx=5)

            # 風險警告
            tk.Label(mode_frame, text="⚠️ 實單模式將執行真實交易！",
                    font=("Arial", 9), fg="red").pack(side="right", padx=5)



            # 客製化區間設定 (包含即時價格)
            range_config_frame = tk.LabelFrame(strategy_container, text="📊 即時價格 & 區間設定", fg="purple", font=("Arial", 10, "bold"))
            range_config_frame.pack(fill="x", padx=5, pady=5)

            # 即時價格區域 (最重要，放在最左邊)
            price_area = tk.Frame(range_config_frame)
            price_area.pack(side="left", padx=5, pady=2)

            tk.Label(price_area, text="當前價格:", font=("Arial", 10, "bold")).pack(side="left", padx=5)
            self.strategy_price_var = tk.StringVar(value="--")
            tk.Label(price_area, textvariable=self.strategy_price_var,
                    font=("Arial", 12, "bold"), fg="red").pack(side="left", padx=5)

            tk.Label(price_area, text="更新時間:", font=("Arial", 10)).pack(side="left", padx=(10, 5))
            self.strategy_time_var = tk.StringVar(value="--:--:--")
            tk.Label(price_area, textvariable=self.strategy_time_var,
                    font=("Arial", 10), fg="blue").pack(side="left", padx=5)

            # 區間模式選擇區域
            mode_area = tk.Frame(range_config_frame)
            mode_area.pack(side="left", padx=15, pady=2)

            tk.Label(mode_area, text="模式:", font=("Arial", 10)).pack(side="left", padx=5)
            self.range_mode_var = tk.StringVar(value="正常模式")
            mode_combo = ttk.Combobox(mode_area, textvariable=self.range_mode_var, width=12, state='readonly')
            mode_combo['values'] = ['正常模式', '測試模式']
            mode_combo.pack(side="left", padx=5)
            mode_combo.bind('<<ComboboxSelected>>', self.on_range_mode_changed)

            # 時間設定區域
            time_area = tk.Frame(range_config_frame)
            time_area.pack(side="left", padx=15, pady=2)

            tk.Label(time_area, text="開始時間:", font=("Arial", 10)).pack(side="left", padx=5)
            self.range_start_time_var = tk.StringVar(value="08:46")
            self.range_time_entry = tk.Entry(time_area, textvariable=self.range_start_time_var, width=8, font=("Arial", 10))
            self.range_time_entry.pack(side="left", padx=5)

            tk.Button(time_area, text="套用", command=self.apply_range_time,
                     bg="lightblue", fg="black", font=("Arial", 9)).pack(side="left", padx=5)

            tk.Button(time_area, text="測試用(3分鐘後)", command=self.set_test_time,
                     bg="orange", fg="white", font=("Arial", 9)).pack(side="left", padx=5)

            # 區間狀態與進場信號合併顯示 (類似交易模式框的水平布局)
            range_signal_frame = tk.LabelFrame(strategy_container, text="📊 區間狀態 & 進場信號", fg="blue", font=("Arial", 10, "bold"))
            range_signal_frame.pack(fill="x", padx=5, pady=5)

            # 區間狀態區域
            range_area = tk.Frame(range_signal_frame)
            range_area.pack(side="left", padx=5, pady=2)

            tk.Label(range_area, text="目標區間:", font=("Arial", 10)).pack(side="left", padx=5)
            self.target_range_var = tk.StringVar(value="08:46-08:48")
            tk.Label(range_area, textvariable=self.target_range_var,
                    font=("Arial", 10, "bold"), fg="purple").pack(side="left", padx=5)

            tk.Label(range_area, text="狀態:", font=("Arial", 10)).pack(side="left", padx=(10, 5))
            self.range_status_var = tk.StringVar(value="等待區間開始")
            tk.Label(range_area, textvariable=self.range_status_var,
                    font=("Arial", 10, "bold"), fg="orange").pack(side="left", padx=5)

            # 高低點區域
            range_data_area = tk.Frame(range_signal_frame)
            range_data_area.pack(side="left", padx=10, pady=2)

            tk.Label(range_data_area, text="高點:", font=("Arial", 10)).pack(side="left", padx=5)
            self.range_high_var = tk.StringVar(value="--")
            tk.Label(range_data_area, textvariable=self.range_high_var,
                    font=("Arial", 10, "bold"), fg="red").pack(side="left", padx=5)

            tk.Label(range_data_area, text="低點:", font=("Arial", 10)).pack(side="left", padx=(10, 5))
            self.range_low_var = tk.StringVar(value="--")
            tk.Label(range_data_area, textvariable=self.range_low_var,
                    font=("Arial", 10, "bold"), fg="green").pack(side="left", padx=5)

            tk.Label(range_data_area, text="區間大小:", font=("Arial", 10)).pack(side="left", padx=(10, 5))
            self.range_size_var = tk.StringVar(value="--")
            tk.Label(range_data_area, textvariable=self.range_size_var,
                    font=("Arial", 10, "bold"), fg="blue").pack(side="left", padx=5)

            # 進場信號區域
            signal_area = tk.Frame(range_signal_frame)
            signal_area.pack(side="left", padx=10, pady=2)

            tk.Label(signal_area, text="信號狀態:", font=("Arial", 10)).pack(side="left", padx=5)
            self.signal_status_var = tk.StringVar(value="等待突破信號")
            tk.Label(signal_area, textvariable=self.signal_status_var,
                    font=("Arial", 10, "bold"), fg="orange").pack(side="left", padx=5)

            tk.Label(signal_area, text="方向:", font=("Arial", 10)).pack(side="left", padx=(10, 5))
            self.signal_direction_var = tk.StringVar(value="--")
            tk.Label(signal_area, textvariable=self.signal_direction_var,
                    font=("Arial", 10, "bold"), fg="purple").pack(side="left", padx=5)

            # 進場資訊區域
            entry_info_area = tk.Frame(range_signal_frame)
            entry_info_area.pack(side="left", padx=10, pady=2)

            tk.Label(entry_info_area, text="進場價:", font=("Arial", 10)).pack(side="left", padx=5)
            self.entry_price_var = tk.StringVar(value="--")
            tk.Label(entry_info_area, textvariable=self.entry_price_var,
                    font=("Arial", 10, "bold"), fg="red").pack(side="left", padx=5)

            tk.Label(entry_info_area, text="進場時間:", font=("Arial", 10)).pack(side="left", padx=(10, 5))
            self.entry_time_var = tk.StringVar(value="--:--:--")
            tk.Label(entry_info_area, textvariable=self.entry_time_var,
                    font=("Arial", 10, "bold"), fg="blue").pack(side="left", padx=5)

            # 部位狀態顯示
            position_frame = tk.LabelFrame(strategy_container, text="部位狀態", fg="green")
            position_frame.pack(fill="x", padx=5, pady=5)

            # 第一行：部位資訊
            position_row1 = tk.Frame(position_frame)
            position_row1.pack(fill="x", padx=5, pady=2)

            tk.Label(position_row1, text="當前部位:", font=("Arial", 10)).pack(side="left", padx=5)
            self.position_status_var = tk.StringVar(value="無部位")
            tk.Label(position_row1, textvariable=self.position_status_var,
                    font=("Arial", 10, "bold"), fg="green").pack(side="left", padx=5)

            tk.Label(position_row1, text="活躍口數:", font=("Arial", 10)).pack(side="left", padx=(20, 5))
            self.active_lots_var = tk.StringVar(value="0")
            tk.Label(position_row1, textvariable=self.active_lots_var,
                    font=("Arial", 10, "bold"), fg="blue").pack(side="left", padx=5)

            # 第二行：損益資訊
            position_row2 = tk.Frame(position_frame)
            position_row2.pack(fill="x", padx=5, pady=2)

            tk.Label(position_row2, text="總損益:", font=("Arial", 10)).pack(side="left", padx=5)
            self.total_pnl_var = tk.StringVar(value="0")
            tk.Label(position_row2, textvariable=self.total_pnl_var,
                    font=("Arial", 10, "bold"), fg="red").pack(side="left", padx=5)

            tk.Label(position_row2, text="今日狀態:", font=("Arial", 10)).pack(side="left", padx=(20, 5))
            self.daily_status_var = tk.StringVar(value="等待進場")
            tk.Label(position_row2, textvariable=self.daily_status_var,
                    font=("Arial", 10, "bold"), fg="orange").pack(side="left", padx=5)

            # 停損狀態顯示
            stop_loss_frame = tk.LabelFrame(strategy_container, text="停損狀態", fg="red")
            stop_loss_frame.pack(fill="x", padx=5, pady=5)

            # 第一行：停損類型和狀態
            stop_row1 = tk.Frame(stop_loss_frame)
            stop_row1.pack(fill="x", padx=5, pady=2)

            tk.Label(stop_row1, text="停損類型:", font=("Arial", 10)).pack(side="left", padx=5)
            self.stop_loss_type_var = tk.StringVar(value="區間邊界")
            tk.Label(stop_row1, textvariable=self.stop_loss_type_var,
                    font=("Arial", 10, "bold"), fg="red").pack(side="left", padx=5)

            tk.Label(stop_row1, text="移動停利:", font=("Arial", 10)).pack(side="left", padx=(20, 5))
            self.trailing_stop_var = tk.StringVar(value="--")
            tk.Label(stop_row1, textvariable=self.trailing_stop_var,
                    font=("Arial", 10, "bold"), fg="blue").pack(side="left", padx=5)

            # 第二行：各口停損狀態
            stop_row2 = tk.Frame(stop_loss_frame)
            stop_row2.pack(fill="x", padx=5, pady=2)

            tk.Label(stop_row2, text="各口狀態:", font=("Arial", 10)).pack(side="left", padx=5)
            self.lots_status_var = tk.StringVar(value="--")
            tk.Label(stop_row2, textvariable=self.lots_status_var,
                    font=("Arial", 9), fg="purple").pack(side="left", padx=5)

            # 即時統計顯示
            stats_frame = tk.LabelFrame(strategy_container, text="即時統計", fg="purple")
            stats_frame.pack(fill="x", padx=5, pady=5)

            # 第一行：當日績效
            stats_row1 = tk.Frame(stats_frame)
            stats_row1.pack(fill="x", padx=5, pady=2)

            tk.Label(stats_row1, text="當日交易:", font=("Arial", 10)).pack(side="left", padx=5)
            self.daily_trades_var = tk.StringVar(value="0次")
            tk.Label(stats_row1, textvariable=self.daily_trades_var,
                    font=("Arial", 10, "bold"), fg="blue").pack(side="left", padx=5)

            tk.Label(stats_row1, text="總損益:", font=("Arial", 10)).pack(side="left", padx=(20, 5))
            self.daily_pnl_var = tk.StringVar(value="0點")
            tk.Label(stats_row1, textvariable=self.daily_pnl_var,
                    font=("Arial", 10, "bold"), fg="green").pack(side="left", padx=5)

            # 第二行：各口表現
            stats_row2 = tk.Frame(stats_frame)
            stats_row2.pack(fill="x", padx=5, pady=2)

            tk.Label(stats_row2, text="各口表現:", font=("Arial", 9)).pack(side="left", padx=5)
            self.lot1_performance_var = tk.StringVar(value="--")
            tk.Label(stats_row2, text="1口:", font=("Arial", 9)).pack(side="left", padx=(10, 2))
            tk.Label(stats_row2, textvariable=self.lot1_performance_var,
                    font=("Arial", 9), fg="blue").pack(side="left", padx=2)

            self.lot2_performance_var = tk.StringVar(value="--")
            tk.Label(stats_row2, text="2口:", font=("Arial", 9)).pack(side="left", padx=(10, 2))
            tk.Label(stats_row2, textvariable=self.lot2_performance_var,
                    font=("Arial", 9), fg="blue").pack(side="left", padx=2)

            self.lot3_performance_var = tk.StringVar(value="--")
            tk.Label(stats_row2, text="3口:", font=("Arial", 9)).pack(side="left", padx=(10, 2))
            tk.Label(stats_row2, textvariable=self.lot3_performance_var,
                    font=("Arial", 9), fg="blue").pack(side="left", padx=2)

            # 第三行：出場原因統計
            stats_row3 = tk.Frame(stats_frame)
            stats_row3.pack(fill="x", padx=5, pady=2)

            tk.Label(stats_row3, text="出場統計:", font=("Arial", 9)).pack(side="left", padx=5)

            self.trailing_stats_var = tk.StringVar(value="--")
            tk.Label(stats_row3, text="移動:", font=("Arial", 9)).pack(side="left", padx=(10, 2))
            tk.Label(stats_row3, textvariable=self.trailing_stats_var,
                    font=("Arial", 9), fg="green").pack(side="left", padx=2)

            self.protection_stats_var = tk.StringVar(value="--")
            tk.Label(stats_row3, text="保護:", font=("Arial", 9)).pack(side="left", padx=(10, 2))
            tk.Label(stats_row3, textvariable=self.protection_stats_var,
                    font=("Arial", 9), fg="orange").pack(side="left", padx=2)

            self.initial_stop_stats_var = tk.StringVar(value="--")
            tk.Label(stats_row3, text="停損:", font=("Arial", 9)).pack(side="left", padx=(10, 2))
            tk.Label(stats_row3, textvariable=self.initial_stop_stats_var,
                    font=("Arial", 9), fg="red").pack(side="left", padx=2)

            # 控制按鈕
            control_frame = tk.Frame(strategy_container)
            control_frame.pack(fill="x", padx=5, pady=5)

            self.strategy_start_btn = tk.Button(control_frame, text="啟動策略監控",
                                              command=self.start_strategy_monitoring,
                                              bg="green", fg="white", font=("Arial", 10))
            self.strategy_start_btn.pack(side="left", padx=5)

            self.strategy_stop_btn = tk.Button(control_frame, text="停止策略監控",
                                             command=self.stop_strategy_monitoring,
                                             bg="red", fg="white", font=("Arial", 10), state="disabled")
            self.strategy_stop_btn.pack(side="left", padx=5)

            # 日誌顯示區域
            log_frame = tk.LabelFrame(strategy_container, text="策略日誌", fg="gray")
            log_frame.pack(fill="both", expand=True, padx=5, pady=5)

            # 創建日誌文本框和滾動條
            log_text_frame = tk.Frame(log_frame)
            log_text_frame.pack(fill="both", expand=True, padx=5, pady=5)

            self.strategy_log_text = tk.Text(log_text_frame, height=8, font=("Consolas", 9))
            log_scrollbar = tk.Scrollbar(log_text_frame, orient="vertical", command=self.strategy_log_text.yview)
            self.strategy_log_text.configure(yscrollcommand=log_scrollbar.set)

            self.strategy_log_text.pack(side="left", fill="both", expand=True)
            log_scrollbar.pack(side="right", fill="y")

            # 儲存SKCOM物件引用
            self.strategy_skcom_objects = skcom_objects

            # 初始化策略狀態
            self.strategy_monitoring = False

            # 初始化區間計算相關變數
            self.range_start_hour = 8
            self.range_start_minute = 46
            self.range_end_hour = 8
            self.range_end_minute = 48
            self.range_mode = "正常模式"

            # 區間數據
            self.range_prices = []  # 存儲區間內的價格
            self.range_high = None
            self.range_low = None
            self.range_calculated = False
            self.in_range_period = False

            # 進場機制相關變數
            self.first_breakout_detected = False
            self.breakout_direction = None
            self.breakout_signal = None
            self.waiting_for_entry = False
            self.daily_entry_completed = False
            self.entry_signal_time = None

            # 部位管理
            self.position = None  # 'LONG' or 'SHORT' or None
            self.entry_price = None
            self.entry_time = None
            self.lots = []  # 多口管理

            # 分鐘K線數據
            self.current_minute_candle = None
            self.minute_prices = []  # 當前分鐘內的價格
            self.last_minute = None

            # 添加初始日誌
            self.add_strategy_log("🎯 策略面板初始化完成")
            self.add_strategy_log("📊 等待報價數據...")
            self.add_strategy_log("⏰ 預設區間: 08:46-08:48")

            logger.info("✅ 策略面板創建成功")

        except Exception as e:
            logger.error(f"❌ 策略面板創建失敗: {e}")
            # 創建錯誤顯示
            error_label = tk.Label(parent_frame, text=f"策略面板載入失敗: {e}",
                                 fg="red", font=("Arial", 12))
            error_label.pack(expand=True)

    def create_default_strategy_config(self):
        """創建預設策略配置"""
        return StrategyConfig(
            trade_size_in_lots=3,
            stop_loss_type=StopLossType.RANGE_BOUNDARY,
            lot_rules=[
                # 第1口：快速移動停利
                LotRule(
                    use_trailing_stop=True,
                    trailing_activation=Decimal(15),
                    trailing_pullback=Decimal('0.20')
                ),
                # 第2口：中等移動停利 + 保護性停損
                LotRule(
                    use_trailing_stop=True,
                    trailing_activation=Decimal(40),
                    trailing_pullback=Decimal('0.20'),
                    protective_stop_multiplier=Decimal('2.0')
                ),
                # 第3口：較大移動停利 + 保護性停損
                LotRule(
                    use_trailing_stop=True,
                    trailing_activation=Decimal(65),
                    trailing_pullback=Decimal('0.20'),
                    protective_stop_multiplier=Decimal('2.0')
                )
            ]
        )

    def add_strategy_log(self, message):
        """添加策略日誌"""
        try:
            if hasattr(self, 'strategy_log_text'):
                from datetime import datetime
                timestamp = datetime.now().strftime("%H:%M:%S")
                log_message = f"[{timestamp}] {message}\n"

                self.strategy_log_text.insert(tk.END, log_message)
                self.strategy_log_text.see(tk.END)

                # 同時輸出到控制台
                logger.info(f"[策略] {message}")
        except Exception as e:
            logger.error(f"添加策略日誌失敗: {e}")

    def start_strategy_monitoring(self):
        """啟動策略監控 - 🔧 GIL錯誤修復版本"""
        try:
            # 🔧 使用線程鎖保護狀態變更
            with self.strategy_lock:
                self.strategy_monitoring = True

            # UI更新使用UI鎖
            with self.ui_lock:
                self.strategy_start_btn.config(state="disabled")
                self.strategy_stop_btn.config(state="normal")

            self.add_strategy_log("🚀 策略監控已啟動")
            self.add_strategy_log("📡 開始接收報價數據...")
            self.add_strategy_log(f"🔧 GIL修復：使用線程安全機制")

            # 設定報價回調 - 這裡是關鍵整合點
            self.setup_quote_callback()

            # 🔧 調試：檢查LOG處理器狀態
            future_order_logger = logging.getLogger('order.future_order')
            self.add_strategy_log(f"📊 LOG處理器狀態: {len(future_order_logger.handlers)} 個處理器")
            self.add_strategy_log(f"📊 策略監控狀態: {self.strategy_monitoring}")

        except Exception as e:
            logger.error(f"啟動策略監控失敗: {e}")
            self.add_strategy_log(f"❌ 啟動失敗: {e}")
            # 恢復狀態
            self.strategy_monitoring = False

    def stop_strategy_monitoring(self):
        """停止策略監控"""
        try:
            self.strategy_monitoring = False
            self.strategy_start_btn.config(state="normal")
            self.strategy_stop_btn.config(state="disabled")

            # 停止LOG監聽
            self.stop_strategy_log_handler()

            self.add_strategy_log("⏹️ 策略監控已停止")

        except Exception as e:
            logger.error(f"停止策略監控失敗: {e}")
            self.add_strategy_log(f"❌ 停止失敗: {e}")

    def setup_quote_callback(self):
        """確認LOG監聽策略 - 里程碑方案"""
        try:
            # LOG處理器已在程式啟動時設定，這裡只是確認
            self.add_strategy_log("✅ LOG監聽策略已啟動")
            self.add_strategy_log("📡 直接監聽報價LOG，零GIL錯誤")
            self.add_strategy_log("🎯 里程碑方案：報價事件→LOG輸出→策略處理")

        except Exception as e:
            logger.error(f"確認LOG監聽失敗: {e}")
            self.add_strategy_log(f"❌ LOG監聽確認失敗: {e}")

    def setup_strategy_log_handler(self):
        """設定策略LOG處理器"""
        try:
            # 創建自定義LOG處理器
            class StrategyLogHandler(logging.Handler):
                def __init__(self, strategy_app):
                    super().__init__()
                    self.strategy_app = strategy_app

                def emit(self, record):
                    try:
                        message = record.getMessage()

                        # 總是顯示接收到的LOG (不管策略是否啟動)
                        print(f"[DEBUG] LOG處理器收到: {message}")

                        # 檢查策略監控狀態
                        monitoring = getattr(self.strategy_app, 'strategy_monitoring', False)
                        print(f"[DEBUG] 策略監控狀態: {monitoring}")

                        # 監聽Tick報價LOG
                        if "【Tick】價格:" in message:
                            print(f"[DEBUG] 發現Tick報價LOG")
                            if monitoring:
                                print(f"[DEBUG] 策略監控中，開始處理...")
                                self.strategy_app.process_tick_log(message)
                            else:
                                print(f"[DEBUG] 策略監控未啟動，跳過處理")
                        else:
                            print(f"[DEBUG] 非Tick報價LOG，跳過")

                    except Exception as e:
                        print(f"[DEBUG] LOG處理器錯誤: {e}")
                        import traceback
                        traceback.print_exc()
                        pass  # 忽略所有錯誤，避免影響LOG系統

            # 添加到order.future_order的logger
            future_order_logger = logging.getLogger('order.future_order')
            self.strategy_log_handler = StrategyLogHandler(self)

            # 🔧 GIL修復：確保LOG級別正確設置
            future_order_logger.setLevel(logging.INFO)  # 確保INFO級別的LOG可以通過
            self.strategy_log_handler.setLevel(logging.INFO)

            future_order_logger.addHandler(self.strategy_log_handler)

            # 調試：確認logger設定
            print(f"[DEBUG] Logger名稱: order.future_order")
            print(f"[DEBUG] Logger級別: {future_order_logger.level}")
            print(f"[DEBUG] Handler級別: {self.strategy_log_handler.level}")
            print(f"[DEBUG] Handler數量: {len(future_order_logger.handlers)}")
            print(f"[DEBUG] 策略Handler已添加: {self.strategy_log_handler in future_order_logger.handlers}")

            # 測試LOG輸出
            future_order_logger.info("🧪 測試LOG輸出 - 策略LOG處理器")
            print("[DEBUG] 測試LOG已發送")

        except Exception as e:
            logger.error(f"設定策略LOG處理器失敗: {e}")

    def process_tick_log(self, log_message):
        """處理Tick報價LOG - 包含區間計算邏輯 - 🔧 GIL錯誤修復版本"""
        try:
            # 🔧 避免嵌套鎖定，只在必要時使用鎖
            self.add_strategy_log(f"🔍 收到LOG: {log_message}")

            # 解析LOG訊息：【Tick】價格:2228200 買:2228100 賣:2228200 量:1 時間:22:59:21
            pattern = r"【Tick】價格:(\d+) 買:(\d+) 賣:(\d+) 量:(\d+) 時間:(\d{2}:\d{2}:\d{2})"
            match = re.match(pattern, log_message)

            if match:
                raw_price = int(match.group(1))
                price = raw_price / 100.0  # 轉換為正確價格
                time_str = match.group(5)

                self.add_strategy_log(f"📊 解析成功: 原始價格={raw_price}, 轉換價格={price}, 時間={time_str}")

                # 更新基本顯示 - 這個函數內部有自己的鎖
                self.add_strategy_log(f"🔄 開始更新顯示...")
                self.update_strategy_display_simple(price, time_str)

                # 區間計算邏輯 - 使用策略鎖保護
                with self.strategy_lock:
                    self.add_strategy_log(f"📈 開始區間計算...")
                    self.process_range_calculation(price, time_str)

                    # 出場條件檢查 - 如果已有部位，檢查出場條件
                    if hasattr(self, 'position') and self.position and hasattr(self, 'lots') and self.lots:
                        self.add_strategy_log(f"🔍 檢查出場條件...")
                        # 創建時間戳對象
                        timestamp = datetime.strptime(time_str, "%H:%M:%S").replace(
                            year=datetime.now().year,
                            month=datetime.now().month,
                            day=datetime.now().day
                        )
                        self.check_exit_conditions(Decimal(str(price)), timestamp)

            else:
                self.add_strategy_log(f"❌ LOG格式不匹配: {log_message}")

        except Exception as e:
            # 🔧 GIL錯誤修復：記錄錯誤但絕不拋出異常
            try:
                self.add_strategy_log(f"❌ process_tick_log錯誤: {e}")
            except:
                pass  # 連LOG都失敗就完全忽略

    def process_range_calculation(self, price, time_str):
        """處理區間計算邏輯 + 進場機制 - 使用報價時間戳精確控制"""
        try:
            # 解析當前時間
            hour, minute, second = map(int, time_str.split(':'))

            # 檢查是否在精確2分鐘區間內 (使用報價時間戳)
            is_in_range = self.is_time_in_range_precise(time_str)

            # 檢測分鐘變化 (用於觸發區間結束)
            current_minute = minute
            minute_changed = (hasattr(self, '_last_range_minute') and
                            self._last_range_minute is not None and
                            current_minute != self._last_range_minute)

            if is_in_range and not self.in_range_period:
                # 剛進入區間 - 開始收集數據
                self.in_range_period = True
                self.range_calculated = False
                self.range_prices = []
                self.range_status_var.set("🔄 收集區間數據中...")
                self._range_start_time = time_str
                print(f"[策略] 📊 開始收集區間數據: {time_str} (精確2分鐘)")

            elif is_in_range and self.in_range_period:
                # 在區間內，收集價格數據
                self.range_prices.append(price)

            elif not is_in_range and self.in_range_period and minute_changed:
                # 分鐘變化且離開區間 - 觸發計算 (上一分K收盤)
                self.in_range_period = False
                print(f"[策略] ⏰ 檢測到分鐘變化: {self._last_range_minute:02d} → {current_minute:02d}")
                print(f"[策略] 📊 第2根1分K收盤，開始計算區間...")
                self.calculate_range_result()

            # 更新分鐘記錄
            self._last_range_minute = current_minute

            # 區間計算完成後的進場邏輯
            if self.range_calculated and self.can_enter_position():
                self.process_entry_logic(price, time_str, hour, minute, second)

        except Exception as e:
            pass

    def can_enter_position(self):
        """檢查是否可以進場 - 根據進場頻率設定"""
        try:
            # 獲取進場頻率設定
            frequency = getattr(self, 'entry_frequency_var', None)
            if frequency:
                freq_setting = frequency.get()
            else:
                freq_setting = "一天一次"  # 預設值

            if freq_setting == "一天一次":
                # 一天一次模式：檢查是否已經進場
                return not self.daily_entry_completed

            elif freq_setting == "可重複進場":
                # 可重複進場模式：只檢查是否已有部位
                return not (hasattr(self, 'position') and self.position is not None)

            elif freq_setting == "測試模式":
                # 測試模式：忽略所有限制
                return True

            else:
                # 預設為一天一次
                return not self.daily_entry_completed

        except Exception as e:
            # 發生錯誤時使用保守策略
            return not self.daily_entry_completed

    def process_entry_logic(self, price, time_str, hour, minute, second):
        """處理進場邏輯"""
        try:
            # 更新分鐘K線數據
            self.update_minute_candle(price, hour, minute, second)

            # 如果正在等待進場，下一個報價就是進場時機
            if self.waiting_for_entry and self.breakout_signal:
                self.execute_entry_on_next_tick(price, time_str)
            elif not self.first_breakout_detected:
                # 只有在未檢測到第一次突破時才監控
                self.monitor_minute_candle_breakout()

        except Exception as e:
            pass

    def update_minute_candle(self, price, hour, minute, second):
        """更新分鐘K線數據"""
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

                    # 檢查突破
                    self.check_minute_candle_breakout()

                # 重置當前分鐘的價格數據
                self.minute_prices = []

            # 添加當前價格到分鐘數據
            self.minute_prices.append(price)
            self.last_minute = current_minute

        except Exception as e:
            pass

    def monitor_minute_candle_breakout(self):
        """監控分鐘K線突破 - 調用檢查方法"""
        try:
            if self.current_minute_candle:
                self.check_minute_candle_breakout()
        except Exception as e:
            pass

    def check_minute_candle_breakout(self):
        """檢查分鐘K線收盤價是否突破區間 - 只檢測第一次突破"""
        try:
            if not self.current_minute_candle or not self.range_high or not self.range_low:
                return

            # 如果已經檢測到第一次突破，就不再檢測
            if self.first_breakout_detected:
                return

            close_price = self.current_minute_candle['close']
            minute = self.current_minute_candle['minute']

            # 檢查第一次突破
            if close_price > self.range_high:
                # 記錄第一次突破
                self.first_breakout_detected = True
                self.breakout_direction = 'LONG'
                self.breakout_signal = 'LONG_SIGNAL'
                self.waiting_for_entry = True
                self.entry_signal_time = self.current_minute_candle['start_time']

                # 更新UI顯示
                self.signal_status_var.set("🔥 突破信號！")
                self.signal_direction_var.set("做多")

                print(f"[策略] 🔥 第一次突破！{minute:02d}分K線收盤價突破上緣!")
                print(f"[策略]    收盤價: {float(close_price):.1f}, 區間上緣: {float(self.range_high):.1f}")
                print(f"[策略] ⏳ 等待下一個報價進場做多...")

            elif close_price < self.range_low:
                # 記錄第一次突破
                self.first_breakout_detected = True
                self.breakout_direction = 'SHORT'
                self.breakout_signal = 'SHORT_SIGNAL'
                self.waiting_for_entry = True
                self.entry_signal_time = self.current_minute_candle['start_time']

                # 更新UI顯示
                self.signal_status_var.set("🔥 突破信號！")
                self.signal_direction_var.set("做空")

                print(f"[策略] 🔥 第一次突破！{minute:02d}分K線收盤價突破下緣!")
                print(f"[策略]    收盤價: {float(close_price):.1f}, 區間下緣: {float(self.range_low):.1f}")
                print(f"[策略] ⏳ 等待下一個報價進場做空...")

        except Exception as e:
            pass

    def execute_entry_on_next_tick(self, price, time_str):
        """在下一個報價執行進場"""
        try:
            if not self.waiting_for_entry or not self.breakout_signal:
                return

            direction = 'LONG' if self.breakout_signal == 'LONG_SIGNAL' else 'SHORT'

            print(f"[策略] 🎯 執行進場! 方向: {direction}, 進場價: {float(price):.1f}")

            # 執行建倉
            self.enter_position(direction, price, time_str)

            # 根據進場頻率設定決定是否標記當天進場完成
            frequency = getattr(self, 'entry_frequency_var', None)
            freq_setting = frequency.get() if frequency else "一天一次"

            if freq_setting == "一天一次":
                # 一天一次模式：標記當天進場已完成
                self.daily_entry_completed = True
                print(f"[策略] 📅 一天一次模式：標記當天進場已完成")
            elif freq_setting == "可重複進場":
                # 可重複進場模式：不標記完成，但重置突破檢測
                self.first_breakout_detected = False
                print(f"[策略] 🔄 可重複進場模式：重置突破檢測，等待下次機會")
            elif freq_setting == "測試模式":
                # 測試模式：重置所有狀態，立即可再次進場
                self.daily_entry_completed = False
                self.first_breakout_detected = False
                print(f"[策略] 🧪 測試模式：重置所有狀態，可立即再次進場")

            # 重置信號狀態
            self.breakout_signal = None
            self.waiting_for_entry = False
            self.entry_signal_time = None

            # 更新UI顯示
            self.signal_status_var.set("✅ 已進場")
            self.daily_status_var.set("已完成進場")

            print(f"[策略] ✅ 當天進場已完成，後續只執行停利/停損機制")

        except Exception as e:
            pass

    def enter_position(self, direction, price, time_str):
        """建立部位 - 完整版多口建倉含停損配置"""
        try:
            self.position = direction
            self.entry_price = Decimal(str(price))
            self.entry_time = time_str

            # 使用策略配置的交易口數
            trade_size = self.strategy_config.trade_size_in_lots
            self.lots = []

            # 計算初始停損價位
            initial_sl = self.range_low if direction == 'LONG' else self.range_high
            if initial_sl is None:
                # 如果沒有區間數據，使用固定點數停損
                if direction == 'LONG':
                    initial_sl = self.entry_price - self.strategy_config.fixed_stop_loss_points
                else:
                    initial_sl = self.entry_price + self.strategy_config.fixed_stop_loss_points

            for i in range(trade_size):
                # 取得對應的停損規則
                rule = (self.strategy_config.lot_rules[i]
                       if i < len(self.strategy_config.lot_rules)
                       else self.strategy_config.lot_rules[-1])

                lot_info = {
                    'id': i + 1,
                    'rule': rule,                           # 新增：停損規則
                    'status': 'active',
                    'pnl': Decimal(0),
                    'peak_price': self.entry_price,         # 新增：峰值價格追蹤
                    'trailing_on': False,                   # 新增：移動停利狀態
                    'stop_loss': initial_sl,                # 新增：停損價位
                    'is_initial_stop': True,                # 新增：是否為初始停損
                    'entry_price': self.entry_price,
                    'order_id': f"SIM{time_str.replace(':', '')}{i+1:02d}"
                }
                self.lots.append(lot_info)

                # 新增：使用策略下單管理器執行建倉下單
                print(f"[策略DEBUG] 檢查策略下單管理器: hasattr={hasattr(self, 'strategy_order_manager')}, manager={getattr(self, 'strategy_order_manager', None)}")

                if hasattr(self, 'strategy_order_manager') and self.strategy_order_manager:
                    print(f"[策略DEBUG] 策略下單管理器存在，準備下單...")
                    print(f"[策略DEBUG] 交易模式: {self.strategy_order_manager.trading_mode}")
                    print(f"[策略DEBUG] order_executor: {self.strategy_order_manager.order_executor}")

                    result = self.strategy_order_manager.place_entry_order(
                        direction=direction,
                        price=float(price),
                        quantity=1,
                        order_type="FOK"
                    )

                    print(f"[策略DEBUG] 下單結果: {result}")

                    if result['success']:
                        mode_text = result.get('mode', 'UNKNOWN')
                        if mode_text == 'LIVE':
                            print(f"[策略] 🔴 實單建倉: 第{i+1}口 {direction} @{float(price):.1f} (ID: {result['order_id']})")
                            self.add_strategy_log(f"🔴 實單建倉: 第{i+1}口 {direction} @{float(price):.1f}")
                            # 更新order_id為實際委託編號
                            lot_info['order_id'] = result['order_id']
                        else:
                            print(f"[策略] 📋 模擬建倉: 第{i+1}口 {direction} @{float(price):.1f} (ID: {lot_info['order_id']})")
                            self.add_strategy_log(f"📋 模擬建倉: 第{i+1}口 {direction} @{float(price):.1f}")
                    else:
                        print(f"[策略] ❌ 建倉下單失敗: 第{i+1}口 - {result['message']}")
                        self.add_strategy_log(f"❌ 建倉下單失敗: 第{i+1}口 - {result['message']}")
                else:
                    # 備用：純模擬模式
                    print(f"[策略DEBUG] 策略下單管理器不存在，使用備用模式")
                    print(f"[策略] 📋 模擬建倉: 第{i+1}口 {direction} @{float(price):.1f} (ID: {lot_info['order_id']})")
                    self.add_strategy_log(f"📋 模擬建倉: 第{i+1}口 {direction} @{float(price):.1f}")

                print(f"[策略]    停損規則: 移動停利={rule.use_trailing_stop}, 啟動點={rule.trailing_activation}, 回撤={rule.trailing_pullback}")

            # 更新UI顯示
            self.position_status_var.set(f"{direction} {trade_size}口")
            self.active_lots_var.set(str(trade_size))
            self.entry_price_var.set(f"{float(price):.1f}")
            self.entry_time_var.set(time_str)

            # 初始化停損狀態顯示
            stop_type_map = {
                StopLossType.RANGE_BOUNDARY: "區間邊界",
                StopLossType.OPENING_PRICE: "開盤價",
                StopLossType.FIXED_POINTS: "固定點數"
            }
            self.stop_loss_type_var.set(stop_type_map.get(self.strategy_config.stop_loss_type, "區間邊界"))
            self.trailing_stop_var.set("未啟動")

            # 更新各口狀態顯示
            self.update_stop_loss_display(self.lots)

            # 記錄到資料庫（簡化版）
            self.record_entry_to_database(direction, price, time_str, trade_size)

            # 新增：開始交易記錄
            range_data = {
                'high': float(self.range_high) if self.range_high else None,
                'low': float(self.range_low) if self.range_low else None,
                'size': float(self.range_high - self.range_low) if self.range_high and self.range_low else None
            }
            self.trading_logger.log_trade_start(direction, price, time_str, self.lots, range_data)

            print(f"[策略] ✅ 建倉完成 - {direction} {trade_size}口 @ {float(price):.1f}")
            print(f"[策略] 🛡️ 初始停損: {float(initial_sl):.1f}")

        except Exception as e:
            logger.error(f"建立部位失敗: {e}")
            pass

    def record_entry_to_database(self, direction, price, time_str, trade_size):
        """記錄進場到資料庫 - 簡化版"""
        try:
            # 這裡可以添加資料庫記錄邏輯
            # 目前只是控制台輸出
            from datetime import datetime
            date_str = datetime.now().strftime("%Y-%m-%d")

            print(f"[策略] 💾 記錄進場資料:")
            print(f"[策略]    日期: {date_str}")
            print(f"[策略]    方向: {direction}")
            print(f"[策略]    價格: {float(price):.1f}")
            print(f"[策略]    時間: {time_str}")
            print(f"[策略]    口數: {trade_size}")

        except Exception as e:
            pass

    def check_exit_conditions(self, price, timestamp):
        """檢查出場條件 - 從test_ui_improvements.py移植"""
        if not self.lots:
            return

        current_time = timestamp.time()

        # 檢查初始停損
        active_lots_with_initial_stop = [lot for lot in self.lots if lot['status'] == 'active' and lot['is_initial_stop']]

        if active_lots_with_initial_stop:
            initial_sl = self.range_low if self.position == 'LONG' else self.range_high

            if initial_sl and ((self.position == 'LONG' and price < initial_sl) or (self.position == 'SHORT' and price > initial_sl)):
                # 觸及初始停損，全部出場
                loss = (price - self.entry_price) if self.position == 'LONG' else (self.entry_price - price)

                for lot in active_lots_with_initial_stop:
                    lot['pnl'] = loss
                    lot['status'] = 'exited'
                    self.execute_exit_order(lot, price, "初始停損")

                print(f"[策略] ❌ 初始停損觸發 | 時間: {current_time.strftime('%H:%M:%S')}, 價格: {int(float(price))}, 單口虧損: {int(float(loss))}")
                self.add_strategy_log(f"❌ 初始停損觸發 @ {int(float(price))}")
                return

        # 檢查各口單的個別出場條件
        for lot in self.lots:
            if lot['status'] != 'active':
                continue

            # 檢查保護性停損
            if not lot['is_initial_stop']:
                if (self.position == 'LONG' and price <= lot['stop_loss']) or \
                   (self.position == 'SHORT' and price >= lot['stop_loss']):
                    lot['pnl'] = lot['stop_loss'] - self.entry_price if self.position == 'LONG' else self.entry_price - lot['stop_loss']
                    lot['status'] = 'exited'
                    self.execute_exit_order(lot, lot['stop_loss'], "保護性停損")
                    continue

            # 檢查移動停利和固定停利
            self.check_take_profit_conditions(lot, price, timestamp)

    def check_take_profit_conditions(self, lot, price, timestamp):
        """檢查停利條件 - 從test_ui_improvements.py移植"""
        rule = lot['rule']
        current_time = timestamp.time()

        # 移動停利邏輯
        if rule.use_trailing_stop and rule.trailing_activation and rule.trailing_pullback:
            if self.position == 'LONG':
                lot['peak_price'] = max(lot['peak_price'], price)

                # 檢查是否啟動移動停利
                if not lot['trailing_on'] and lot['peak_price'] >= self.entry_price + rule.trailing_activation:
                    lot['trailing_on'] = True
                    print(f"[策略] 🔔 第{lot['id']}口移動停利啟動 | 時間: {current_time.strftime('%H:%M:%S')}")
                    self.add_strategy_log(f"🔔 第{lot['id']}口移動停利啟動")

                # 檢查移動停利出場
                if lot['trailing_on']:
                    stop_price = lot['peak_price'] - (lot['peak_price'] - self.entry_price) * rule.trailing_pullback
                    if price <= stop_price:
                        lot['pnl'] = stop_price - self.entry_price
                        lot['status'] = 'exited'
                        self.execute_exit_order(lot, stop_price, "移動停利")
                        self.update_next_lot_protection(lot)
                        return

            elif self.position == 'SHORT':
                lot['peak_price'] = min(lot['peak_price'], price)

                if not lot['trailing_on'] and lot['peak_price'] <= self.entry_price - rule.trailing_activation:
                    lot['trailing_on'] = True
                    print(f"[策略] 🔔 第{lot['id']}口移動停利啟動 | 時間: {current_time.strftime('%H:%M:%S')}")
                    self.add_strategy_log(f"🔔 第{lot['id']}口移動停利啟動")

                if lot['trailing_on']:
                    stop_price = lot['peak_price'] + (self.entry_price - lot['peak_price']) * rule.trailing_pullback
                    if price >= stop_price:
                        lot['pnl'] = self.entry_price - stop_price
                        lot['status'] = 'exited'
                        self.execute_exit_order(lot, stop_price, "移動停利")
                        self.update_next_lot_protection(lot)
                        return

        # 固定停利邏輯
        elif rule.fixed_tp_points:
            if (self.position == 'LONG' and price >= self.entry_price + rule.fixed_tp_points) or \
               (self.position == 'SHORT' and price <= self.entry_price - rule.fixed_tp_points):
                lot['pnl'] = rule.fixed_tp_points
                lot['status'] = 'exited'
                exit_price = self.entry_price + rule.fixed_tp_points if self.position == 'LONG' else self.entry_price - rule.fixed_tp_points
                self.execute_exit_order(lot, exit_price, "固定停利")
                self.update_next_lot_protection(lot)

    def check_all_previous_lots_profitable(self, target_lot_id):
        """檢查目標口單之前的所有口單是否都獲利"""
        try:
            for lot in self.lots:
                if lot['id'] < target_lot_id and lot['status'] == 'exited':
                    if lot['pnl'] <= 0:  # 如果有虧損或平手
                        return False
            return True
        except Exception as e:
            print(f"[策略] ❌ 檢查前面口單獲利狀況失敗: {e}")
            return False

    def update_next_lot_protection(self, exited_lot):
        """更新下一口單的保護性停損 - 修正版：只有前面全部獲利才更新"""
        next_lot = next((l for l in self.lots if l['id'] == exited_lot['id'] + 1), None)

        if not next_lot or next_lot['status'] != 'active' or not next_lot['rule'].protective_stop_multiplier:
            return

        # 新增：檢查前面所有口單是否都獲利
        all_previous_profitable = self.check_all_previous_lots_profitable(next_lot['id'])

        # 收集前面口單的獲利資訊用於日誌
        previous_lots_info = []
        for lot in self.lots:
            if lot['id'] < next_lot['id'] and lot['status'] == 'exited':
                previous_lots_info.append(f"第{lot['id']}口:{lot['pnl']:+.0f}點")

        if not all_previous_profitable:
            print(f"[策略] ⚠️ 前面有口單虧損({', '.join(previous_lots_info)})，第{next_lot['id']}口維持原始停損")
            self.add_strategy_log(f"⚠️ 第{next_lot['id']}口維持原始停損(前面有虧損)")
            return

        # 計算累積獲利
        cumulative_pnl = sum(l['pnl'] for l in self.lots if l['status'] == 'exited')
        total_profit = cumulative_pnl + exited_lot['pnl']

        # 只有在總獲利為正時才設定保護性停損
        if total_profit <= 0:
            print(f"[策略] ⚠️ 累積獲利不足({total_profit:+.0f}點)，第{next_lot['id']}口維持原始停損")
            self.add_strategy_log(f"⚠️ 第{next_lot['id']}口維持原始停損(獲利不足)")
            return

        # 設定保護性停損
        stop_loss_amount = total_profit * next_lot['rule'].protective_stop_multiplier
        new_sl = self.entry_price - stop_loss_amount if self.position == 'LONG' else self.entry_price + stop_loss_amount

        next_lot['stop_loss'] = new_sl
        next_lot['is_initial_stop'] = False

        print(f"[策略] 🛡️ 第{next_lot['id']}口保護性停損更新: {int(float(new_sl))} (基於累積獲利 {int(float(total_profit))})")
        print(f"[策略] 📊 前面口單狀況: {', '.join(previous_lots_info)}")
        self.add_strategy_log(f"🛡️ 第{next_lot['id']}口保護性停損更新: {int(float(new_sl))}")
        self.add_strategy_log(f"📊 前面全部獲利: {', '.join(previous_lots_info)}")

    def execute_exit_order(self, lot, price, reason):
        """執行出場下單 - 從test_ui_improvements.py移植並整合到OrderTester"""
        # 模擬模式記錄
        print(f"[策略] ✅ 第{lot['id']}口{reason} | 模擬出場價: {int(float(price))}, 損益: {int(float(lot['pnl']))}")
        self.add_strategy_log(f"✅ 第{lot['id']}口{reason} @ {int(float(price))}, 損益: {int(float(lot['pnl']))}")

        # 新增：記錄出場到交易記錄
        from datetime import datetime
        current_time = datetime.now().strftime("%H:%M:%S")
        self.trading_logger.log_lot_exit(lot, price, current_time, reason)

        # 更新UI顯示
        self.update_position_display()

        # 檢查是否全部出場，如果是則完成交易記錄
        if hasattr(self, 'lots') and self.lots:
            if all(lot['status'] == 'exited' for lot in self.lots):
                self.trading_logger.log_trade_complete()
                self.trading_logger.update_daily_summary()
                print(f"[交易記錄] 🎯 交易循環完成，已更新統計")

        # 新增：使用策略下單管理器執行出場下單
        try:
            if hasattr(self, 'strategy_order_manager') and self.strategy_order_manager:
                result = self.strategy_order_manager.place_exit_order(
                    direction=self.position,  # 原部位方向
                    price=float(price),
                    quantity=1,
                    order_type="FOK"
                )

                if result['success']:
                    mode_text = result.get('mode', 'UNKNOWN')
                    if mode_text == 'LIVE':
                        self.add_strategy_log(f"🔴 實單出場: {result['message']}")
                        print(f"[策略] 🔴 實單出場成功: {result['message']}")
                    else:
                        self.add_strategy_log(f"✅ 模擬出場: {result['message']}")
                        print(f"[策略] ✅ 模擬出場: {result['message']}")
                else:
                    self.add_strategy_log(f"❌ 出場下單失敗: {result['message']}")
                    print(f"[策略] ❌ 出場下單失敗: {result['message']}")
            else:
                # 備用：純模擬模式
                self.add_strategy_log(f"✅ 模擬出場 (備用模式)")
                print(f"[策略] ✅ 模擬出場 (備用模式)")

        except Exception as e:
            logger.error(f"❌ 執行出場下單失敗: {e}")
            self.add_strategy_log(f"❌ 出場下單異常: {str(e)}")
            print(f"[策略] ❌ 出場下單異常: {e}")

    def update_position_display(self):
        """更新部位顯示 - 包含停損狀態"""
        try:
            if hasattr(self, 'lots') and self.lots:
                active_lots = [lot for lot in self.lots if lot['status'] == 'active']
                total_pnl = sum(lot['pnl'] for lot in self.lots if lot['status'] == 'exited')

                self.active_lots_var.set(str(len(active_lots)))
                self.total_pnl_var.set(f"{int(float(total_pnl))}")

                # 更新停損狀態顯示
                self.update_stop_loss_display(active_lots)

                # 更新即時統計顯示
                self.update_trading_stats_display()

                if len(active_lots) == 0:
                    self.position_status_var.set("已全部出場")
                    self.daily_status_var.set("交易完成")
                    self.lots_status_var.set("全部出場")
        except Exception as e:
            pass

    def update_stop_loss_display(self, active_lots):
        """更新停損狀態顯示"""
        try:
            if not active_lots:
                self.trailing_stop_var.set("--")
                self.lots_status_var.set("--")
                return

            # 統計移動停利狀態
            trailing_count = sum(1 for lot in active_lots if lot.get('trailing_on', False))
            if trailing_count > 0:
                self.trailing_stop_var.set(f"{trailing_count}口啟動")
            else:
                self.trailing_stop_var.set("未啟動")

            # 顯示各口狀態
            status_parts = []
            for lot in active_lots:
                lot_id = lot['id']
                if lot.get('trailing_on', False):
                    status_parts.append(f"第{lot_id}口:移動中")
                elif lot.get('is_initial_stop', True):
                    status_parts.append(f"第{lot_id}口:初始停損")
                else:
                    status_parts.append(f"第{lot_id}口:保護停損")

            status_text = " | ".join(status_parts)
            # 限制顯示長度
            if len(status_text) > 50:
                status_text = status_text[:47] + "..."
            self.lots_status_var.set(status_text)

        except Exception as e:
            pass

    def update_trading_stats_display(self):
        """更新即時統計顯示"""
        try:
            # 獲取當前統計數據
            stats = self.trading_logger.get_current_stats()

            # 更新當日績效
            self.daily_trades_var.set(f"{stats.get('trades_count', 0)}次")
            pnl = stats.get('total_pnl', 0)
            pnl_sign = "+" if pnl >= 0 else ""
            self.daily_pnl_var.set(f"{pnl_sign}{pnl:.0f}點")

            # 更新各口表現
            self.lot1_performance_var.set(stats.get('lot1_performance', '--'))
            self.lot2_performance_var.set(stats.get('lot2_performance', '--'))
            self.lot3_performance_var.set(stats.get('lot3_performance', '--'))

            # 更新出場原因統計
            self.trailing_stats_var.set(stats.get('trailing_stats', '--'))
            self.protection_stats_var.set(stats.get('protection_stats', '--'))
            self.initial_stop_stats_var.set(stats.get('initial_stop_stats', '--'))

        except Exception as e:
            print(f"[統計顯示] 更新統計顯示失敗: {e}")

    def is_time_in_range_precise(self, time_str):
        """精確的2分鐘區間判斷 - 使用報價時間戳"""
        try:
            # 解析報價時間：14:30:15
            hour, minute, second = map(int, time_str.split(':'))

            # 計算當前時間的總秒數
            current_total_seconds = hour * 3600 + minute * 60 + second

            # 計算區間開始的總秒數
            start_total_seconds = self.range_start_hour * 3600 + self.range_start_minute * 60

            # 精確2分鐘 = 120秒 (2根1分K)
            end_total_seconds = start_total_seconds + 120

            # 精確判斷：開始時間 <= 當前時間 < 結束時間
            # 例如：14:30:00 <= 時間 < 14:32:00
            in_range = start_total_seconds <= current_total_seconds < end_total_seconds

            # 調試輸出 (只在狀態變化時輸出)
            if not hasattr(self, '_last_range_status'):
                self._last_range_status = False

            if in_range != self._last_range_status:
                start_time = f"{self.range_start_hour:02d}:{self.range_start_minute:02d}:00"
                end_time = f"{(start_total_seconds + 120) // 3600:02d}:{((start_total_seconds + 120) % 3600) // 60:02d}:00"
                status = "進入" if in_range else "離開"
                print(f"[策略] ⏰ {status}區間: {start_time}-{end_time} (當前: {time_str})")
                self._last_range_status = in_range

            return in_range

        except Exception as e:
            return False

    def is_time_in_range(self, hour, minute):
        """檢查時間是否在設定的區間內 - 舊版本保留"""
        try:
            # 轉換為分鐘數便於比較
            current_minutes = hour * 60 + minute
            start_minutes = self.range_start_hour * 60 + self.range_start_minute
            end_minutes = self.range_end_hour * 60 + self.range_end_minute

            # 處理跨日情況
            if end_minutes < start_minutes:
                # 跨日區間
                return current_minutes >= start_minutes or current_minutes <= end_minutes
            else:
                # 同日區間
                return start_minutes <= current_minutes <= end_minutes

        except Exception as e:
            return False

    def calculate_range_result(self):
        """計算區間結果 - 基於2根1分K線的高低點"""
        try:
            if len(self.range_prices) > 0:
                self.range_high = max(self.range_prices)
                self.range_low = min(self.range_prices)
                range_size = self.range_high - self.range_low

                # 更新顯示
                self.range_high_var.set(f"{self.range_high:.1f}")
                self.range_low_var.set(f"{self.range_low:.1f}")
                self.range_size_var.set(f"{range_size:.1f}")
                self.range_status_var.set("✅ 區間計算完成")

                # 計算時間範圍
                start_time = f"{self.range_start_hour:02d}:{self.range_start_minute:02d}"
                end_minute = self.range_start_minute + 2
                end_hour = self.range_start_hour
                if end_minute >= 60:
                    end_minute -= 60
                    end_hour += 1
                end_time = f"{end_hour:02d}:{end_minute:02d}"

                # 記錄結果 - 強調是2根1分K
                print(f"[策略] ✅ 2根1分K線區間計算完成:")
                print(f"[策略] ⏰ 時間範圍: {start_time}-{end_time} (精確2分鐘)")
                print(f"[策略] 📈 區間高點: {self.range_high:.1f}")
                print(f"[策略] 📉 區間低點: {self.range_low:.1f}")
                print(f"[策略] 📏 區間大小: {range_size:.1f}")
                print(f"[策略] 📊 數據點數: {len(self.range_prices)}")
                print(f"[策略] 🎯 等待第3分鐘開始監控突破信號...")

                self.range_calculated = True
            else:
                self.range_status_var.set("❌ 無數據")
                print(f"[策略] ❌ 2分鐘區間內無價格數據")

        except Exception as e:
            pass

    def update_strategy_display_simple(self, price, time_str):
        """最簡單的策略顯示更新 - 只更新變數，不觸發事件 - 🔧 GIL錯誤修復版本"""
        try:
            # 🔧 使用線程鎖確保線程安全
            with self.strategy_lock:
                self.add_strategy_log(f"🔄 update_strategy_display_simple 被調用: price={price}, time={time_str}")
                self.add_strategy_log(f"📊 strategy_monitoring狀態: {getattr(self, 'strategy_monitoring', 'undefined')}")

                if self.strategy_monitoring:
                    self.add_strategy_log(f"✅ 策略監控中，開始更新UI...")

                    # 檢查UI變數是否存在
                    with self.ui_lock:
                        if hasattr(self, 'strategy_price_var'):
                            self.add_strategy_log(f"📊 找到strategy_price_var，設定價格: {price}")
                            self.strategy_price_var.set(str(price))
                        else:
                            self.add_strategy_log(f"❌ 找不到strategy_price_var")

                        if hasattr(self, 'strategy_time_var'):
                            self.add_strategy_log(f"⏰ 找到strategy_time_var，設定時間: {time_str}")
                            self.strategy_time_var.set(time_str)
                        else:
                            self.add_strategy_log(f"❌ 找不到strategy_time_var")

                    # 記錄價格變化
                    if not hasattr(self, '_last_strategy_price') or price != self._last_strategy_price:
                        self.add_strategy_log(f"💰 價格更新: {price} 時間: {time_str}")
                        self._last_strategy_price = price
                    else:
                        self.add_strategy_log(f"📊 價格無變化: {price}")

                    self.add_strategy_log(f"✅ UI更新完成")
                else:
                    self.add_strategy_log(f"⚠️ 策略監控未啟動，跳過UI更新")

        except Exception as e:
            # 🔧 GIL錯誤修復：記錄錯誤但絕不拋出異常
            try:
                self.add_strategy_log(f"❌ update_strategy_display_simple錯誤: {e}")
            except:
                pass  # 連LOG都失敗就完全忽略

    def stop_strategy_log_handler(self):
        """停止LOG監聽"""
        try:
            if hasattr(self, 'strategy_log_handler'):
                future_order_logger = logging.getLogger('order.future_order')
                future_order_logger.removeHandler(self.strategy_log_handler)
                print("[策略] ⏹️ LOG監聽已停止")
        except Exception as e:
            pass

    def on_trading_mode_changed(self, event=None):
        """交易模式變更事件"""
        try:
            mode_text = self.trading_mode_var.get()

            if mode_text == TradingMode.LIVE.value:
                # 切換到實單模式 - 需要額外確認
                confirm_msg = "⚠️ 實單模式風險確認 ⚠️\n\n" + \
                             "您即將切換到實單交易模式！\n" + \
                             "策略觸發時將執行真實的期貨下單。\n\n" + \
                             "期貨交易具有高風險，可能造成重大損失！\n" + \
                             "確定要切換到實單模式嗎？"

                result = messagebox.askyesno("實單模式確認", confirm_msg)

                if result:
                    # 確認切換到實單模式
                    mode = TradingMode.LIVE
                    self.strategy_order_manager.set_trading_mode(mode)
                    self.mode_status_var.set("🔴 實單模式 (風險)")
                    self.add_strategy_log("🔴 已切換到實單模式 - 策略將執行真實交易！")
                    logger.warning("策略交易模式切換為實單模式")
                else:
                    # 取消切換，恢復模擬模式
                    self.trading_mode_var.set(TradingMode.SIMULATION.value)
                    self.add_strategy_log("✅ 保持模擬模式")
            else:
                # 切換到模擬模式
                mode = TradingMode.SIMULATION
                self.strategy_order_manager.set_trading_mode(mode)
                self.mode_status_var.set("✅ 模擬模式 (安全)")
                self.add_strategy_log("✅ 已切換到模擬模式")
                logger.info("策略交易模式切換為模擬模式")

        except Exception as e:
            logger.error(f"交易模式切換失敗: {e}")
            # 發生錯誤時恢復到模擬模式
            self.trading_mode_var.set(TradingMode.SIMULATION.value)
            self.mode_status_var.set("✅ 模擬模式 (安全)")

    def on_strategy_product_changed(self, event=None):
        """策略商品變更事件"""
        try:
            product = self.strategy_product_var.get()

            # 更新策略下單管理器的商品設定
            if hasattr(self, 'strategy_order_manager'):
                self.strategy_order_manager.current_product = product

            # 記錄變更
            if product == "MTX00":
                self.add_strategy_log("📊 切換到小台指期貨 (MTX00)")
                logger.info("策略商品切換為小台指期貨 (MTX00)")
            elif product == "TM0000":
                self.add_strategy_log("📊 切換到微型台指期貨 (TM0000)")
                logger.info("策略商品切換為微型台指期貨 (TM0000)")

        except Exception as e:
            logger.error(f"策略商品切換失敗: {e}")
            # 發生錯誤時恢復到預設商品
            self.strategy_product_var.set("MTX00")

    def on_entry_frequency_changed(self, event=None):
        """進場頻率變更事件"""
        try:
            frequency = self.entry_frequency_var.get()

            if frequency == "一天一次":
                self.add_strategy_log("📅 設定為一天一次進場模式")
                logger.info("策略進場頻率設定為一天一次")

            elif frequency == "可重複進場":
                self.add_strategy_log("🔄 設定為可重複進場模式")
                logger.info("策略進場頻率設定為可重複進場")

                # 重置今日進場標記，允許重新進場
                if hasattr(self, 'daily_entry_completed'):
                    self.daily_entry_completed = False
                    self.add_strategy_log("✅ 已重置今日進場標記，可重新進場")

            elif frequency == "測試模式":
                self.add_strategy_log("🧪 設定為測試模式 - 忽略所有進場限制")
                logger.info("策略進場頻率設定為測試模式")

                # 重置所有限制
                if hasattr(self, 'daily_entry_completed'):
                    self.daily_entry_completed = False
                if hasattr(self, 'first_breakout_detected'):
                    self.first_breakout_detected = False

                self.add_strategy_log("✅ 已重置所有進場限制")

        except Exception as e:
            logger.error(f"進場頻率變更失敗: {e}")
            # 發生錯誤時恢復到預設
            self.entry_frequency_var.set("一天一次")

    def show_strategy_orders_status(self):
        """顯示策略委託狀態"""
        try:
            if hasattr(self, 'strategy_order_manager'):
                status = self.strategy_order_manager.get_strategy_orders_status()
                self.add_strategy_log(f"📊 委託狀態 - 等待:{status['pending']} 確認:{status['confirmed']} 成交:{status['filled']} 取消:{status['cancelled']}")
            else:
                self.add_strategy_log("❌ 策略下單管理器未初始化")
        except Exception as e:
            self.add_strategy_log(f"❌ 查看委託狀態失敗: {e}")

    def reset_entry_status(self):
        """重置進場狀態 - 手動重置功能"""
        try:
            # 重置進場相關狀態
            self.daily_entry_completed = False
            self.first_breakout_detected = False
            self.breakout_signal = None
            self.waiting_for_entry = False
            self.entry_signal_time = None

            # 更新UI顯示
            self.signal_status_var.set("⏳ 等待信號")
            self.signal_direction_var.set("無")
            self.daily_status_var.set("等待進場")

            self.add_strategy_log("🔄 已重置進場狀態 - 可重新檢測突破信號")
            logger.info("手動重置策略進場狀態")

        except Exception as e:
            self.add_strategy_log(f"❌ 重置進場狀態失敗: {e}")
            logger.error(f"重置進場狀態失敗: {e}")

    def on_range_mode_changed(self, event=None):
        """區間模式變更事件"""
        try:
            mode = self.range_mode_var.get()
            self.range_mode = mode

            if mode == "測試模式":
                self.range_time_entry.config(state="normal")
                self.add_strategy_log("🧪 已切換到測試模式 - 可自訂區間時間")
            else:
                self.range_time_entry.config(state="disabled")
                # 恢復預設時間
                self.range_start_time_var.set("08:46")
                self.apply_range_time()
                self.add_strategy_log("📈 已切換到正常模式 - 使用08:46-08:48區間")

        except Exception as e:
            logger.error(f"區間模式變更失敗: {e}")

    def apply_range_time(self):
        """套用區間時間設定"""
        try:
            time_str = self.range_start_time_var.get().strip()

            # 驗證時間格式
            if ':' not in time_str:
                raise ValueError("時間格式錯誤，請使用 HH:MM 格式")

            hour_str, minute_str = time_str.split(':')
            hour = int(hour_str)
            minute = int(minute_str)

            # 驗證時間範圍
            if not (0 <= hour <= 23) or not (0 <= minute <= 59):
                raise ValueError("時間範圍錯誤")

            # 更新區間設定
            self.range_start_hour = hour
            self.range_start_minute = minute

            # 計算結束時間（+2分鐘）
            end_minute = minute + 2
            end_hour = hour
            if end_minute >= 60:
                end_minute -= 60
                end_hour += 1
                if end_hour >= 24:
                    end_hour = 0

            self.range_end_hour = end_hour
            self.range_end_minute = end_minute

            # 更新顯示
            range_display = f"{hour:02d}:{minute:02d}-{end_hour:02d}:{end_minute:02d}"
            self.target_range_var.set(range_display)
            self.range_status_var.set("等待區間開始")

            # 重置區間數據
            self.reset_range_data()

            self.add_strategy_log(f"✅ 區間時間已設定: {range_display}")

        except ValueError as e:
            self.add_strategy_log(f"❌ 時間格式錯誤: {e}")
        except Exception as e:
            self.add_strategy_log(f"❌ 套用區間時間失敗: {e}")

    def set_test_time(self):
        """設定測試時間（當前時間+3分鐘）"""
        try:
            from datetime import datetime, timedelta

            # 計算3分鐘後的時間
            future_time = datetime.now() + timedelta(minutes=3)
            time_str = future_time.strftime("%H:%M")

            # 更新時間設定
            self.range_start_time_var.set(time_str)
            self.apply_range_time()

            self.add_strategy_log(f"🕐 測試時間已設定: {time_str} (3分鐘後開始)")

        except Exception as e:
            self.add_strategy_log(f"❌ 設定測試時間失敗: {e}")

    def reset_range_data(self):
        """重置區間數據和進場機制狀態"""
        try:
            # 重置區間數據
            self.range_prices = []
            self.range_high = None
            self.range_low = None
            self.range_calculated = False
            self.in_range_period = False

            # 重置進場機制狀態
            self.first_breakout_detected = False
            self.breakout_direction = None
            self.breakout_signal = None
            self.waiting_for_entry = False
            self.daily_entry_completed = False
            self.entry_signal_time = None

            # 重置部位狀態
            self.position = None
            self.entry_price = None
            self.entry_time = None
            self.lots = []

            # 重置分鐘K線數據
            self.current_minute_candle = None
            self.minute_prices = []
            self.last_minute = None

            # 清空區間顯示
            self.range_high_var.set("--")
            self.range_low_var.set("--")
            self.range_size_var.set("--")

            # 清空進場信號顯示
            self.signal_status_var.set("等待突破信號")
            self.signal_direction_var.set("--")
            self.entry_price_var.set("--")
            self.entry_time_var.set("--:--:--")

            # 清空部位顯示
            self.position_status_var.set("無部位")
            self.active_lots_var.set("0")
            self.total_pnl_var.set("0")
            self.daily_status_var.set("等待進場")

        except Exception as e:
            pass

    def on_closing(self):
        """關閉應用程式"""
        try:
            # 直接關閉，避免messagebox導致的GIL錯誤
            logger.info("正在關閉應用程式...")

            # 🔧 GIL修復：移除TCP價格伺服器相關代碼

            # 停止所有報價監控
            try:
                if hasattr(self, 'future_order_frame') and self.future_order_frame:
                    if hasattr(self.future_order_frame, 'quote_monitoring') and self.future_order_frame.quote_monitoring:
                        self.future_order_frame.stop_quote_monitoring()
                        logger.info("已停止報價監控")
            except Exception as e:
                logger.error(f"停止報價監控時發生錯誤: {e}")

            # 關閉主視窗
            self.destroy()
            logger.info("應用程式已關閉")

        except Exception as e:
            logger.error(f"關閉應用程式時發生錯誤: {e}")
            # 強制關閉
            try:
                self.destroy()
            except:
                pass

# ==================== 交易記錄系統 ====================

class TradingLogger:
    """交易記錄器 - 專注於TXT檔案記錄和即時統計"""

    def __init__(self):
        self.records_folder = "Trading_Records"
        self.current_date = datetime.now().strftime("%Y-%m-%d")
        self.trade_counter = 0
        self.current_trade = None
        self.daily_trades = []  # 當日交易記錄

        # 確保資料夾存在
        self.ensure_folder_exists()

    def ensure_folder_exists(self):
        """確保Trading_Records資料夾存在"""
        try:
            if not os.path.exists(self.records_folder):
                os.makedirs(self.records_folder)
                print(f"[交易記錄] 創建資料夾: {self.records_folder}")
        except Exception as e:
            print(f"[交易記錄] 創建資料夾失敗: {e}")

    def log_trade_start(self, direction, entry_price, entry_time, lots_info, range_data=None):
        """記錄交易開始"""
        try:
            self.trade_counter += 1
            self.current_trade = {
                'trade_id': self.trade_counter,
                'direction': direction,
                'entry_price': float(entry_price),
                'entry_time': entry_time,
                'total_lots': len(lots_info),
                'lots_detail': [],
                'range_data': range_data or {},
                'start_timestamp': datetime.now()
            }

            print(f"[交易記錄] 開始記錄交易 #{self.trade_counter}: {direction} @{float(entry_price)}")

        except Exception as e:
            print(f"[交易記錄] 記錄交易開始失敗: {e}")

    def log_lot_exit(self, lot_info, exit_price, exit_time, exit_reason):
        """記錄單口出場"""
        try:
            if not self.current_trade:
                return

            lot_record = {
                'lot_id': lot_info['id'],
                'exit_time': exit_time,
                'exit_price': float(exit_price),
                'exit_reason': exit_reason,
                'pnl': float(lot_info['pnl']),
                'rule': {
                    'trailing_activation': float(lot_info['rule'].trailing_activation) if lot_info['rule'].trailing_activation else None,
                    'trailing_pullback': float(lot_info['rule'].trailing_pullback) if lot_info['rule'].trailing_pullback else None,
                    'protective_stop_multiplier': float(lot_info['rule'].protective_stop_multiplier) if lot_info['rule'].protective_stop_multiplier else None
                }
            }

            self.current_trade['lots_detail'].append(lot_record)
            print(f"[交易記錄] 記錄第{lot_info['id']}口出場: {exit_reason} @{float(exit_price)}")

        except Exception as e:
            print(f"[交易記錄] 記錄出場失敗: {e}")

    def log_trade_complete(self):
        """完成交易記錄並保存到TXT檔案"""
        try:
            if not self.current_trade or not self.current_trade['lots_detail']:
                return

            # 計算交易總結
            total_pnl = sum(lot['pnl'] for lot in self.current_trade['lots_detail'])
            end_timestamp = datetime.now()
            duration = end_timestamp - self.current_trade['start_timestamp']

            self.current_trade['total_pnl'] = total_pnl
            self.current_trade['duration'] = str(duration).split('.')[0]  # 移除微秒
            self.current_trade['end_time'] = self.current_trade['lots_detail'][-1]['exit_time']

            # 添加到每日交易列表
            self.daily_trades.append(self.current_trade.copy())

            # 寫入詳細記錄檔案
            self.write_trade_detail()

            print(f"[交易記錄] 完成交易記錄 #{self.current_trade['trade_id']}: 總損益 {total_pnl:.1f}點")

            # 重置當前交易
            self.current_trade = None

        except Exception as e:
            print(f"[交易記錄] 完成交易記錄失敗: {e}")

    def write_trade_detail(self):
        """寫入交易詳細記錄到TXT檔案"""
        try:
            if not self.current_trade:
                return

            filename = f"{self.current_date}_trading_log.txt"
            filepath = os.path.join(self.records_folder, filename)

            # 準備交易記錄內容
            trade = self.current_trade
            content = []

            # 如果是第一筆交易，添加標題
            if not os.path.exists(filepath):
                content.append(f"=== {self.current_date} 台指期貨交易記錄 ===\n")

            # 交易標題
            content.append(f"[交易 #{trade['trade_id']:03d}] {trade['entry_time']} - {trade['end_time']}")
            content.append(f"方向: {trade['direction']} | 進場價: {trade['entry_price']:.0f} | 總口數: {trade['total_lots']}")

            # 區間資訊（如果有）
            if trade['range_data']:
                range_info = trade['range_data']
                content.append(f"區間: {range_info.get('low', '--'):.0f}-{range_info.get('high', '--'):.0f} ({range_info.get('size', '--'):.0f}點)")

            content.append("")  # 空行

            # 各口出場詳情
            for lot in trade['lots_detail']:
                duration_parts = trade['duration'].split(':')
                if len(duration_parts) >= 2:
                    duration_display = f"{duration_parts[1]}:{duration_parts[2]}" if len(duration_parts) > 2 else f"{duration_parts[0]}:{duration_parts[1]}"
                else:
                    duration_display = trade['duration']

                pnl_sign = "+" if lot['pnl'] >= 0 else ""
                content.append(f"第{lot['lot_id']}口: {lot['exit_time']} {lot['exit_reason']}出場 @{lot['exit_price']:.0f} | 損益: {pnl_sign}{lot['pnl']:.0f}點")

            content.append("")  # 空行

            # 交易總結
            total_pnl_sign = "+" if trade['total_pnl'] >= 0 else ""
            win_lots = sum(1 for lot in trade['lots_detail'] if lot['pnl'] > 0)
            win_rate = (win_lots / len(trade['lots_detail']) * 100) if trade['lots_detail'] else 0

            content.append(f"交易總結: {total_pnl_sign}{trade['total_pnl']:.0f}點 | 持倉時間: {duration_display} | 勝率: {win_rate:.0f}%")
            content.append("")
            content.append("---")
            content.append("")

            # 寫入檔案
            with open(filepath, 'a', encoding='utf-8') as f:
                f.write('\n'.join(content))

            print(f"[交易記錄] 寫入詳細記錄: {filename}")

        except Exception as e:
            print(f"[交易記錄] 寫入詳細記錄失敗: {e}")

    def update_daily_summary(self):
        """更新每日統計摘要"""
        try:
            if not self.daily_trades:
                return

            filename = f"{self.current_date}_summary.txt"
            filepath = os.path.join(self.records_folder, filename)

            # 計算統計數據
            stats = self.calculate_daily_stats()

            # 準備摘要內容
            content = []
            content.append(f"=== {self.current_date} 交易統計摘要 ===")
            content.append("")

            # 總體績效
            content.append("【總體績效】")
            content.append(f"交易次數: {stats['total_trades']}次")
            content.append(f"總損益: {stats['total_pnl']:+.0f}點")
            content.append(f"勝率: {stats['win_rate']:.0f}% ({stats['winning_trades']}勝{stats['losing_trades']}負)")
            content.append(f"平均每筆: {stats['avg_pnl']:+.1f}點")
            content.append(f"最大獲利: {stats['max_profit']:+.0f}點")
            content.append(f"最大虧損: {stats['max_loss']:+.0f}點")
            content.append("")

            # 各口單表現
            content.append("【各口單表現】")
            for i in range(1, 4):  # 假設最多3口
                lot_stats = stats['lot_performance'].get(f'lot_{i}')
                if lot_stats:
                    content.append(f"第{i}口: {lot_stats['trades']}筆交易 | 平均: {lot_stats['avg_pnl']:+.1f}點 | 勝率: {lot_stats['win_rate']:.0f}%")
            content.append("")

            # 出場原因分析
            content.append("【出場原因分析】")
            for reason, reason_stats in stats['exit_analysis'].items():
                content.append(f"{reason}: {reason_stats['count']}次 | 平均: {reason_stats['avg_pnl']:+.1f}點 | 勝率: {reason_stats['win_rate']:.0f}%")
            content.append("")

            # 更新時間
            content.append(f"更新時間: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

            # 寫入檔案
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write('\n'.join(content))

            print(f"[交易記錄] 更新統計摘要: {filename}")

        except Exception as e:
            print(f"[交易記錄] 更新統計摘要失敗: {e}")

    def calculate_daily_stats(self):
        """計算每日統計數據"""
        try:
            if not self.daily_trades:
                return {}

            # 基本統計
            total_trades = len(self.daily_trades)
            total_pnl = sum(trade['total_pnl'] for trade in self.daily_trades)
            winning_trades = sum(1 for trade in self.daily_trades if trade['total_pnl'] > 0)
            losing_trades = total_trades - winning_trades
            win_rate = (winning_trades / total_trades * 100) if total_trades > 0 else 0
            avg_pnl = total_pnl / total_trades if total_trades > 0 else 0

            trade_pnls = [trade['total_pnl'] for trade in self.daily_trades]
            max_profit = max(trade_pnls) if trade_pnls else 0
            max_loss = min(trade_pnls) if trade_pnls else 0

            # 各口單表現統計
            lot_performance = {}
            for lot_num in range(1, 4):  # 假設最多3口
                lot_key = f'lot_{lot_num}'
                lot_pnls = []
                lot_wins = 0
                lot_trades = 0

                for trade in self.daily_trades:
                    for lot in trade['lots_detail']:
                        if lot['lot_id'] == lot_num:
                            lot_pnls.append(lot['pnl'])
                            lot_trades += 1
                            if lot['pnl'] > 0:
                                lot_wins += 1

                if lot_trades > 0:
                    lot_performance[lot_key] = {
                        'trades': lot_trades,
                        'avg_pnl': sum(lot_pnls) / lot_trades,
                        'win_rate': (lot_wins / lot_trades * 100)
                    }

            # 出場原因分析
            exit_analysis = {}
            for trade in self.daily_trades:
                for lot in trade['lots_detail']:
                    reason = lot['exit_reason']
                    if reason not in exit_analysis:
                        exit_analysis[reason] = {'pnls': [], 'wins': 0}

                    exit_analysis[reason]['pnls'].append(lot['pnl'])
                    if lot['pnl'] > 0:
                        exit_analysis[reason]['wins'] += 1

            # 計算出場原因統計
            for reason, data in exit_analysis.items():
                count = len(data['pnls'])
                avg_pnl = sum(data['pnls']) / count if count > 0 else 0
                win_rate = (data['wins'] / count * 100) if count > 0 else 0
                exit_analysis[reason] = {
                    'count': count,
                    'avg_pnl': avg_pnl,
                    'win_rate': win_rate
                }

            return {
                'total_trades': total_trades,
                'total_pnl': total_pnl,
                'winning_trades': winning_trades,
                'losing_trades': losing_trades,
                'win_rate': win_rate,
                'avg_pnl': avg_pnl,
                'max_profit': max_profit,
                'max_loss': max_loss,
                'lot_performance': lot_performance,
                'exit_analysis': exit_analysis
            }

        except Exception as e:
            print(f"[交易記錄] 計算統計數據失敗: {e}")
            return {}

    def get_current_stats(self):
        """獲取當前統計數據供UI顯示"""
        try:
            if not self.daily_trades:
                return {
                    'trades_count': 0,
                    'total_pnl': 0,
                    'lot1_performance': '--',
                    'lot2_performance': '--',
                    'lot3_performance': '--',
                    'trailing_stats': '--',
                    'protection_stats': '--',
                    'initial_stop_stats': '--'
                }

            stats = self.calculate_daily_stats()

            # 格式化各口表現
            lot_performances = {}
            for i in range(1, 4):
                lot_key = f'lot_{i}'
                if lot_key in stats['lot_performance']:
                    perf = stats['lot_performance'][lot_key]
                    lot_performances[f'lot{i}_performance'] = f"{perf['avg_pnl']:+.0f}點({perf['win_rate']:.0f}%)"
                else:
                    lot_performances[f'lot{i}_performance'] = '--'

            # 格式化出場原因統計
            exit_stats = {}
            for reason in ['移動停利', '保護性停損', '初始停損']:
                if reason in stats['exit_analysis']:
                    data = stats['exit_analysis'][reason]
                    exit_stats[f'{reason}_stats'] = f"{data['count']}次({data['avg_pnl']:+.0f}點)"
                else:
                    exit_stats[f'{reason}_stats'] = '--'

            return {
                'trades_count': stats['total_trades'],
                'total_pnl': stats['total_pnl'],
                **lot_performances,
                'trailing_stats': exit_stats.get('移動停利_stats', '--'),
                'protection_stats': exit_stats.get('保護性停損_stats', '--'),
                'initial_stop_stats': exit_stats.get('初始停損_stats', '--')
            }

        except Exception as e:
            print(f"[交易記錄] 獲取統計數據失敗: {e}")
            return {}

if __name__ == "__main__":
    try:
        app = OrderTesterApp()
        app.mainloop()
    except Exception as e:
        logger.error(f"應用程式啟動失敗: {e}")
        print(f"應用程式啟動失敗: {e}")
        input("按Enter鍵退出...")
