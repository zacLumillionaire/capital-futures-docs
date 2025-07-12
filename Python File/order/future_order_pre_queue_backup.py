#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
期貨下單模組 - 根據官方案例和文件
"""

import sys
import os
import time
import threading
from datetime import datetime
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import tkinter as tk
from tkinter import ttk, messagebox
import logging
from order.future_config import *

# 策略面板暫時移除，確保基礎功能穩定
# try:
#     from strategy.strategy_panel import StrategyControlPanel
#     STRATEGY_AVAILABLE = True
# except ImportError as e:
#     STRATEGY_AVAILABLE = False
#     print(f"策略模組未載入: {e}")
STRATEGY_AVAILABLE = False

# 設定日誌
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# 新增：下單執行器類別
class OrderExecutor:
    """下單執行器 - 核心邏輯層，支援手動/策略兩種下單模式"""

    def __init__(self, skcom_objects, message_callback=None):
        """
        初始化下單執行器

        Args:
            skcom_objects: SKCOM API物件字典
            message_callback: 訊息回調函數，用於記錄日誌
        """
        self.m_pSKOrder = skcom_objects.get('SKOrder')
        self.m_pSKCenter = skcom_objects.get('SKCenter')
        self.m_pSKQuote = skcom_objects.get('SKQuote')
        self.add_message = message_callback or self._default_message_callback

        # 預留：報價監控和委託追蹤
        self.quote_monitor = None
        self.order_tracker = None

        # 從LOG資料獲取報價資訊的預留接口
        self.log_quote_parser = None

        # 非同步下單回調處理
        self.strategy_callback = None  # 策略回調函數
        self.setup_async_order_handler()

    def _default_message_callback(self, message):
        """預設訊息回調"""
        print(f"[OrderExecutor] {message}")

    def _get_login_id(self):
        """取得登入ID"""
        # 暫時使用固定的登入ID，後續可以改為動態取得
        return "E123354882"

    def execute_order_core(self, order_params, require_confirmation=True):
        """
        核心下單邏輯

        Args:
            order_params: 下單參數字典
            require_confirmation: 是否需要確認對話框

        Returns:
            dict: 下單結果 {'success': bool, 'message': str, 'order_id': str}
        """
        try:
            # 檢查必要參數
            required_fields = ['account', 'product', 'direction', 'price', 'quantity']
            for field in required_fields:
                if field not in order_params:
                    return {'success': False, 'message': f'缺少必要參數: {field}', 'order_id': None}

            # 風險確認 (僅手動下單需要)
            if require_confirmation:
                risk_msg = self._build_confirmation_message(order_params)
                result = messagebox.askyesno("期貨下單確認", risk_msg)
                if not result:
                    self.add_message("【取消】使用者取消期貨下單")
                    return {'success': False, 'message': '使用者取消下單', 'order_id': None}

            # 執行實際下單
            return self._send_order_to_api(order_params)

        except Exception as e:
            error_msg = f"下單執行失敗: {str(e)}"
            self.add_message(f"【錯誤】{error_msg}")
            return {'success': False, 'message': error_msg, 'order_id': None}

    def strategy_order(self, direction, price, quantity=1, order_type="FOK", product="MTX00", new_close=0):
        """
        策略專用下單 - 無確認對話框

        Args:
            direction: 'BUY' 或 'SELL'
            price: 委託價格
            quantity: 委託數量
            order_type: 委託類型 ('ROD', 'IOC', 'FOK')
            product: 商品代碼
            new_close: 倉別 (0:新倉, 1:平倉, 2:自動)

        Returns:
            dict: 下單結果
        """
        # 策略交易參數
        order_params = {
            'account': 'F0200006363839',  # 策略固定帳號
            'product': product,
            'direction': direction,
            'price': price,
            'quantity': quantity,
            'order_type': order_type,
            'day_trade': 1,  # 當沖
            'new_close': new_close,  # 倉別：0=新倉, 1=平倉, 2=自動
            'reserved': 0    # 盤中
        }

        # 根據倉別顯示不同訊息
        close_type_text = {0: "新倉", 1: "平倉", 2: "自動"}[new_close]
        self.add_message(f"【策略下單】{direction} {quantity}口 @{price} ({order_type}) [{close_type_text}]")
        return self.execute_order_core(order_params, require_confirmation=False)

    def manual_order(self, order_params):
        """
        手動下單 - 保持原有確認機制

        Args:
            order_params: 完整的下單參數字典

        Returns:
            dict: 下單結果
        """
        return self.execute_order_core(order_params, require_confirmation=True)

    def _build_confirmation_message(self, order_params):
        """建立確認對話框訊息"""
        direction_text = "買進" if order_params['direction'] == 'BUY' else "賣出"
        order_type_text = order_params.get('order_type', 'ROD')

        return f"⚠️ 期貨交易風險確認 ⚠️\n\n" + \
               f"帳號: {order_params['account']}\n" + \
               f"商品: {order_params['product']}\n" + \
               f"價格: {order_params['price']}\n" + \
               f"數量: {order_params['quantity']}\n" + \
               f"買賣: {direction_text}\n" + \
               f"委託類型: {order_type_text}\n\n" + \
               "期貨具有高槓桿特性，可能產生巨大損失！\n" + \
               "確定要進行真實下單嗎？"

    def _send_order_to_api(self, order_params):
        """發送下單到API - 核心邏輯"""
        try:
            if not self.m_pSKOrder:
                return {'success': False, 'message': 'SKOrder物件未初始化', 'order_id': None}

            # 檢查並初始化SKOrderLib
            self.add_message("【初始化】檢查SKOrderLib初始化狀態...")
            nCode = self.m_pSKOrder.SKOrderLib_Initialize()
            if nCode != 0:
                if self.m_pSKCenter:
                    msg_text = self.m_pSKCenter.SKCenterLib_GetReturnCodeMessage(nCode)
                else:
                    msg_text = f"錯誤代碼: {nCode}"
                return {'success': False, 'message': f'SKOrderLib初始化失敗: {msg_text}', 'order_id': None}

            # 取得登入ID - 從父視窗或使用預設值
            login_id = self._get_login_id()
            self.add_message(f"【Token】使用登入ID: {login_id}")

            # 讀取憑證
            self.add_message(f"【憑證】使用登入ID讀取憑證: {login_id}")
            nCode = self.m_pSKOrder.ReadCertByID(login_id)

            if nCode != 0:
                if self.m_pSKCenter:
                    msg_text = self.m_pSKCenter.SKCenterLib_GetReturnCodeMessage(nCode)
                else:
                    msg_text = f"錯誤代碼: {nCode}"
                self.add_message(f"【警告】憑證讀取失敗: {msg_text}")

            # 建立下單物件
            import comtypes.gen.SKCOMLib as sk
            oOrder = sk.FUTUREORDER()

            # 填入下單參數
            oOrder.bstrFullAccount = order_params['account']
            oOrder.bstrStockNo = order_params['product']
            oOrder.sBuySell = 0 if order_params['direction'] == 'BUY' else 1

            # 委託類型轉換
            order_type_map = {'ROD': 0, 'IOC': 1, 'FOK': 2}
            oOrder.sTradeType = order_type_map.get(order_params.get('order_type', 'FOK'), 2)

            oOrder.sDayTrade = order_params.get('day_trade', 1)
            oOrder.bstrPrice = str(order_params['price'])
            oOrder.nQty = order_params['quantity']
            oOrder.sNewClose = order_params.get('new_close', 0)
            oOrder.sReserved = order_params.get('reserved', 0)

            # 執行下單 - 非同步下單
            self.add_message("【API】準備調用SendFutureOrderCLR (非同步模式)...")
            self.add_message(f"【API參數】Token: {login_id}, 非同步: True")
            result = self.m_pSKOrder.SendFutureOrderCLR(login_id, True, oOrder)  # True = 非同步下單

            if isinstance(result, tuple) and len(result) == 2:
                message, nCode = result
                self.add_message(f"【API返回】訊息: {message}, 代碼: {nCode}")

                if nCode == 0:
                    # 非同步下單請求已送出，實際結果將透過 OnAsyncOrder 事件回報
                    self.add_message(f"✅【下單請求】已送出，等待 OnAsyncOrder 確認...")
                    return {'success': True, 'message': '下單請求已送出', 'order_id': 'PENDING'}
                else:
                    if self.m_pSKCenter:
                        error_msg = self.m_pSKCenter.SKCenterLib_GetReturnCodeMessage(nCode)
                    else:
                        error_msg = f"錯誤代碼: {nCode}"
                    self.add_message(f"❌【下單失敗】{error_msg}")
                    return {'success': False, 'message': error_msg, 'order_id': None}
            else:
                self.add_message(f"【異常】API返回格式異常: {result}")
                return {'success': False, 'message': f'API返回格式異常: {result}', 'order_id': None}

        except Exception as e:
            error_msg = f"API調用失敗: {str(e)}"
            self.add_message(f"【錯誤】{error_msg}")
            return {'success': False, 'message': error_msg, 'order_id': None}

    # 預留：五檔報價和刪單追價功能
    def setup_quote_monitoring(self, product="MTX00"):
        """預留：設置五檔報價監控 - 從LOG資料解析"""
        # 未來可以從現有的報價LOG中解析五檔資料
        pass

    def setup_order_chasing(self):
        """預留：設置刪單追價機制"""
        # 未來整合委託查詢和刪單重下功能
        pass

    def setup_async_order_handler(self):
        """設置非同步下單事件處理"""
        try:
            if self.m_pSKOrder:
                # 創建事件處理器類別
                class AsyncOrderEventHandler:
                    def __init__(self, order_executor):
                        self.order_executor = order_executor

                    def OnAsyncOrder(self, nCode, bstrMessage):
                        """處理非同步下單結果事件"""
                        try:
                            if nCode == 0:
                                # 委託成功，bstrMessage 就是13碼委託序號
                                self.order_executor.add_message(f"✅【委託確認】委託序號: {bstrMessage}")

                                # 通知策略管理器
                                if self.order_executor.strategy_callback:
                                    self.order_executor.strategy_callback(bstrMessage, 'ORDER_SUCCESS')
                            else:
                                # 委託失敗
                                self.order_executor.add_message(f"❌【委託失敗】錯誤: {bstrMessage} (代碼: {nCode})")

                                # 通知策略管理器
                                if self.order_executor.strategy_callback:
                                    self.order_executor.strategy_callback(bstrMessage, 'ORDER_FAILED', nCode)

                        except Exception as e:
                            self.order_executor.add_message(f"【錯誤】OnAsyncOrder處理失敗: {e}")
                        return 0

                # 設置事件處理器
                self.async_order_handler = AsyncOrderEventHandler(self)

                # 連接事件 (如果API支援)
                try:
                    # 嘗試設置事件處理器
                    self.m_pSKOrder.OnAsyncOrder = self.async_order_handler.OnAsyncOrder
                    self.add_message("【初始化】OnAsyncOrder 事件處理器設置完成")
                except Exception as e:
                    self.add_message(f"【警告】OnAsyncOrder 事件設置失敗: {e}")

        except Exception as e:
            self.add_message(f"【錯誤】設置非同步事件處理器失敗: {e}")

class FutureOrderFrame(tk.Frame):
    """期貨下單框架"""
    
    def __init__(self, master=None, skcom_objects=None):
        super().__init__(master)
        self.master = master

        # 🔧 GIL錯誤修復：添加線程安全鎖
        self.quote_lock = threading.Lock()
        self.ui_lock = threading.Lock()
        self.data_lock = threading.Lock()

        # SKCOM物件
        self.m_pSKCenter = skcom_objects.get('SKCenter') if skcom_objects else None
        self.m_pSKOrder = skcom_objects.get('SKOrder') if skcom_objects else None
        self.m_pSKReply = skcom_objects.get('SKReply') if skcom_objects else None
        self.m_pSKQuote = skcom_objects.get('SKQuote') if skcom_objects else None

        # UI變數
        self.order_data = {}

        # 建立UI
        self.create_widgets()

        # 新增：初始化下單執行器 (在UI創建後)
        self.order_executor = OrderExecutor(skcom_objects, self.add_message)

        # 即時報價相關變數
        self.quote_monitoring = False
        self.current_product = "MTX00"  # 預設監控MTX00
        self.last_price = 0
        self.last_update_time = None
        self.quote_event_handler = None

        # 策略回調相關 - 階段1整合
        self.strategy_callback = None
        self.stocks_ready = False  # 商品資料是否準備完成

        # 策略面板暫時移除
        # self.strategy_panel = None

        # 載入預設值
        self.load_default_values()

        # 重新啟用事件註冊，使用更安全的方式
        self.register_quote_events()
    
    def create_widgets(self):
        """建立UI控件"""
        # 風險提醒
        risk_frame = tk.LabelFrame(self, text="⚠️ 期貨交易風險提醒", fg="red", padx=10, pady=5)
        risk_frame.grid(column=0, row=0, columnspan=6, sticky=tk.E + tk.W, padx=5, pady=5)
        
        risk_text = tk.Text(risk_frame, height=4, width=80, fg="red")
        risk_text.insert(tk.END, RISK_WARNING)
        risk_text.config(state=tk.DISABLED)
        risk_text.grid(column=0, row=0, sticky=tk.E + tk.W)
        
        # 主框架
        main_frame = tk.LabelFrame(self, text="期貨委託下單", padx=10, pady=10)
        main_frame.grid(column=0, row=1, columnspan=6, sticky=tk.E + tk.W, padx=5, pady=5)
        
        # 第一行：基本資訊
        row = 0
        
        # 帳號
        tk.Label(main_frame, text="期貨帳號:").grid(column=0, row=row, sticky=tk.W, padx=5, pady=2)
        self.entry_account = tk.Entry(main_frame, width=12)
        self.entry_account.grid(column=1, row=row, padx=5, pady=2)
        
        # 商品代碼
        tk.Label(main_frame, text="商品代碼:").grid(column=2, row=row, sticky=tk.W, padx=5, pady=2)
        self.combo_product = ttk.Combobox(main_frame, width=12, state='readonly')
        product_list = [f"{code} ({info['name']})" for code, info in FUTURE_PRODUCTS.items()]
        self.combo_product['values'] = product_list
        self.combo_product.grid(column=3, row=row, padx=5, pady=2)

        # 自動查詢近月合約按鈕
        self.btn_auto_query = tk.Button(main_frame, text="查詢近月",
                                       command=self.auto_query_near_month, bg="lightgreen")
        self.btn_auto_query.grid(column=4, row=row, padx=5, pady=2)

        # 手動輸入商品代碼欄位 (支援直接輸入「小台近」等API查詢結果)
        row += 1
        tk.Label(main_frame, text="或直接輸入:").grid(column=2, row=row, sticky=tk.W, padx=5, pady=2)
        self.entry_manual_product = tk.Entry(main_frame, width=15)
        self.entry_manual_product.grid(column=3, row=row, padx=5, pady=2)

        # 使用手動輸入按鈕
        self.btn_use_manual = tk.Button(main_frame, text="使用此代碼",
                                       command=self.use_manual_product, bg="orange")
        self.btn_use_manual.grid(column=4, row=row, padx=5, pady=2)

        # 預設選擇小台指近月合約 (MTX00)
        default_product = "MTX00 (小台指期貨(近月))"
        if default_product in product_list:
            self.combo_product.set(default_product)
        else:
            self.combo_product.current(0)  # 如果找不到就選第一個
        
        # 月份
        tk.Label(main_frame, text="月份:").grid(column=4, row=row, sticky=tk.W, padx=5, pady=2)
        self.combo_month = ttk.Combobox(main_frame, width=8, state='readonly')
        self.combo_month['values'] = FUTURE_MONTHS
        self.combo_month.grid(column=5, row=row, padx=5, pady=2)
        self.combo_month.current(0)  # 預設選擇最近月份
        
        # 第二行：交易參數
        row += 1
        
        # 買賣別
        tk.Label(main_frame, text="買賣別:").grid(column=0, row=row, sticky=tk.W, padx=5, pady=2)
        self.combo_buy_sell = ttk.Combobox(main_frame, width=8, state='readonly')
        self.combo_buy_sell['values'] = BUYSELLSET
        self.combo_buy_sell.grid(column=1, row=row, padx=5, pady=2)
        self.combo_buy_sell.current(0)  # 預設買進
        
        # 委託價
        tk.Label(main_frame, text="委託價:").grid(column=2, row=row, sticky=tk.W, padx=5, pady=2)
        self.entry_price = tk.Entry(main_frame, width=10)
        self.entry_price.grid(column=3, row=row, padx=5, pady=2)
        
        # 委託量
        tk.Label(main_frame, text="委託量:").grid(column=4, row=row, sticky=tk.W, padx=5, pady=2)
        self.entry_quantity = tk.Entry(main_frame, width=8)
        self.entry_quantity.grid(column=5, row=row, padx=5, pady=2)
        
        # 第三行：進階參數
        row += 1
        
        # 委託條件
        tk.Label(main_frame, text="委託條件:").grid(column=0, row=row, sticky=tk.W, padx=5, pady=2)
        self.combo_period = ttk.Combobox(main_frame, width=8, state='readonly')
        self.combo_period['values'] = PERIODSET['future']
        self.combo_period.grid(column=1, row=row, padx=5, pady=2)
        self.combo_period.current(0)  # 預設ROD
        
        # 當沖與否
        tk.Label(main_frame, text="當沖與否:").grid(column=2, row=row, sticky=tk.W, padx=5, pady=2)
        self.combo_day_trade = ttk.Combobox(main_frame, width=8, state='readonly')
        self.combo_day_trade['values'] = FLAGSET['future']
        self.combo_day_trade.grid(column=3, row=row, padx=5, pady=2)
        self.combo_day_trade.current(0)  # 預設非當沖
        
        # 倉別
        tk.Label(main_frame, text="倉別:").grid(column=4, row=row, sticky=tk.W, padx=5, pady=2)
        self.combo_new_close = ttk.Combobox(main_frame, width=8, state='readonly')
        self.combo_new_close['values'] = NEWCLOSESET['future']
        self.combo_new_close.grid(column=5, row=row, padx=5, pady=2)
        self.combo_new_close.current(0)  # 預設新倉
        
        # 第四行：盤別
        row += 1
        
        # 盤別
        tk.Label(main_frame, text="盤別:").grid(column=0, row=row, sticky=tk.W, padx=5, pady=2)
        self.combo_reserved = ttk.Combobox(main_frame, width=8, state='readonly')
        self.combo_reserved['values'] = RESERVEDSET
        self.combo_reserved.grid(column=1, row=row, padx=5, pady=2)
        self.combo_reserved.current(0)  # 預設盤中
        
        # 第五行：按鈕
        row += 1
        button_frame = tk.Frame(main_frame)
        button_frame.grid(column=0, row=row, columnspan=6, pady=10)
        
        # 測試下單按鈕
        self.btn_test_order = tk.Button(button_frame, text="測試期貨下單", 
                                       command=self.test_future_order,
                                       bg="#4169E1", fg="white", width=15)
        self.btn_test_order.grid(column=0, row=0, padx=5)
        
        # 查詢帳號按鈕
        self.btn_query_account = tk.Button(button_frame, text="查詢期貨帳號", 
                                          command=self.query_account,
                                          bg="#228B22", fg="white", width=15)
        self.btn_query_account.grid(column=1, row=0, padx=5)
        
        # 查詢部位按鈕
        self.btn_query_position = tk.Button(button_frame, text="查詢部位", 
                                           command=self.query_position,
                                           bg="#FF8C00", fg="white", width=12)
        self.btn_query_position.grid(column=2, row=0, padx=5)
        
        # 清除按鈕
        self.btn_clear = tk.Button(button_frame, text="清除", 
                                  command=self.clear_form,
                                  bg="#DC143C", fg="white", width=12)
        self.btn_clear.grid(column=3, row=0, padx=5)
        
        # 商品資訊顯示
        info_frame = tk.LabelFrame(self, text="商品資訊", padx=5, pady=5)
        info_frame.grid(column=0, row=2, columnspan=6, sticky=tk.E + tk.W, padx=5, pady=5)
        
        self.label_product_info = tk.Label(info_frame, text="請選擇商品", justify=tk.LEFT)
        self.label_product_info.grid(column=0, row=0, sticky=tk.W)
        
        # 綁定商品選擇事件
        self.combo_product.bind('<<ComboboxSelected>>', self.on_product_changed)
        
        # 即時報價顯示區域
        quote_frame = tk.LabelFrame(self, text="📊 MTX00 即時報價監控", padx=10, pady=5)
        quote_frame.grid(column=0, row=3, columnspan=6, sticky=tk.E + tk.W, padx=5, pady=5)

        # 報價控制按鈕
        quote_control_frame = tk.Frame(quote_frame)
        quote_control_frame.grid(column=0, row=0, columnspan=4, pady=5)

        self.btn_start_quote = tk.Button(quote_control_frame, text="開始監控報價",
                                        command=self.start_quote_monitoring, bg="lightgreen")
        self.btn_start_quote.grid(column=0, row=0, padx=5)

        self.btn_stop_quote = tk.Button(quote_control_frame, text="停止監控",
                                       command=self.stop_quote_monitoring, bg="lightcoral")
        self.btn_stop_quote.grid(column=1, row=0, padx=5)

        # 報價顯示標籤
        quote_info_frame = tk.Frame(quote_frame)
        quote_info_frame.grid(column=0, row=1, columnspan=4, pady=5)

        tk.Label(quote_info_frame, text="商品:", font=("Arial", 10)).grid(column=0, row=0, padx=5)
        self.label_product = tk.Label(quote_info_frame, text="MTX00", font=("Arial", 10, "bold"), fg="blue")
        self.label_product.grid(column=1, row=0, padx=5)

        tk.Label(quote_info_frame, text="最新價:", font=("Arial", 10)).grid(column=2, row=0, padx=5)
        self.label_price = tk.Label(quote_info_frame, text="--", font=("Arial", 12, "bold"), fg="red")
        self.label_price.grid(column=3, row=0, padx=5)

        tk.Label(quote_info_frame, text="更新時間:", font=("Arial", 10)).grid(column=4, row=0, padx=5)
        self.label_time = tk.Label(quote_info_frame, text="--", font=("Arial", 10))
        self.label_time.grid(column=5, row=0, padx=5)

        tk.Label(quote_info_frame, text="狀態:", font=("Arial", 10)).grid(column=6, row=0, padx=5)
        self.label_status = tk.Label(quote_info_frame, text="未連線", font=("Arial", 10), fg="gray")
        self.label_status.grid(column=7, row=0, padx=5)

        # 訊息顯示區域 (擴大到底部)
        msg_frame = tk.LabelFrame(self, text="下單訊息與報價LOG", padx=5, pady=5)
        msg_frame.grid(column=0, row=8, columnspan=6, sticky=tk.E + tk.W + tk.N + tk.S, padx=5, pady=5)

        # 設定msg_frame的權重，讓它可以擴展
        msg_frame.grid_rowconfigure(0, weight=1)
        msg_frame.grid_columnconfigure(0, weight=1)

        # 增大log區塊高度並設定為可擴展
        self.text_message = tk.Text(msg_frame, height=15, width=80)
        scrollbar = tk.Scrollbar(msg_frame, orient=tk.VERTICAL, command=self.text_message.yview)
        self.text_message.configure(yscrollcommand=scrollbar.set)

        self.text_message.grid(column=0, row=0, sticky=tk.E + tk.W + tk.N + tk.S)
        scrollbar.grid(column=1, row=0, sticky=tk.N + tk.S)

        # 委託單管理區域
        order_mgmt_frame = tk.LabelFrame(self, text="📋 盤中委託單管理", padx=10, pady=5)
        order_mgmt_frame.grid(column=0, row=5, columnspan=6, sticky=tk.E + tk.W, padx=5, pady=5)

        # 委託單管理按鈕
        mgmt_button_frame = tk.Frame(order_mgmt_frame)
        mgmt_button_frame.grid(column=0, row=0, columnspan=6, pady=5)

        self.btn_query_orders = tk.Button(mgmt_button_frame, text="查詢盤中委託",
                                         command=self.query_pending_orders, bg="lightblue")
        self.btn_query_orders.grid(column=0, row=0, padx=5)

        self.btn_cancel_order = tk.Button(mgmt_button_frame, text="刪除委託",
                                         command=self.cancel_selected_order, bg="lightcoral")
        self.btn_cancel_order.grid(column=1, row=0, padx=5)

        self.btn_modify_price = tk.Button(mgmt_button_frame, text="刪單重下",
                                         command=self.cancel_and_reorder, bg="lightyellow")
        self.btn_modify_price.grid(column=2, row=0, padx=5)

        # 新價格輸入
        tk.Label(mgmt_button_frame, text="新價格:").grid(column=3, row=0, padx=5)
        self.entry_new_price = tk.Entry(mgmt_button_frame, width=10)
        self.entry_new_price.grid(column=4, row=0, padx=5)

        # 版本檢查按鈕
        self.btn_check_version = tk.Button(mgmt_button_frame, text="檢查版本",
                                          command=self.check_skcom_version, bg="lightgray")
        self.btn_check_version.grid(column=5, row=0, padx=5)

        # 委託單列表
        order_list_frame = tk.Frame(order_mgmt_frame)
        order_list_frame.grid(column=0, row=1, columnspan=6, sticky=tk.E + tk.W + tk.N + tk.S, pady=5)

        # 委託單表格
        columns = ('序號', '書號', '商品', '買賣', '價格', '數量', '狀態', '時間')
        self.tree_orders = ttk.Treeview(order_list_frame, columns=columns, show='headings', height=6)

        for col in columns:
            self.tree_orders.heading(col, text=col)
            self.tree_orders.column(col, width=80)

        # 滾動條
        scrollbar_orders = ttk.Scrollbar(order_list_frame, orient=tk.VERTICAL, command=self.tree_orders.yview)
        self.tree_orders.configure(yscrollcommand=scrollbar_orders.set)

        self.tree_orders.grid(column=0, row=0, sticky=tk.E + tk.W + tk.N + tk.S)
        scrollbar_orders.grid(column=1, row=0, sticky=tk.N + tk.S)

        # 委託單資料存儲
        self.pending_orders = {}

        # 成交回報顯示區域
        trade_report_frame = tk.LabelFrame(self, text="📈 成交回報", padx=10, pady=5)
        trade_report_frame.grid(column=0, row=7, columnspan=6, sticky=tk.E + tk.W, padx=5, pady=5)

        # 成交回報文字區域
        trade_text_frame = tk.Frame(trade_report_frame)
        trade_text_frame.grid(column=0, row=0, sticky=tk.E + tk.W + tk.N + tk.S)

        self.text_trade_report = tk.Text(trade_text_frame, height=4, wrap=tk.WORD)
        scrollbar_trade = ttk.Scrollbar(trade_text_frame, orient=tk.VERTICAL, command=self.text_trade_report.yview)
        self.text_trade_report.configure(yscrollcommand=scrollbar_trade.set)

        self.text_trade_report.grid(column=0, row=0, sticky=tk.E + tk.W + tk.N + tk.S)
        scrollbar_trade.grid(column=1, row=0, sticky=tk.N + tk.S)

        trade_text_frame.grid_columnconfigure(0, weight=1)
        trade_text_frame.grid_rowconfigure(0, weight=1)

        # 清除成交回報按鈕
        self.btn_clear_trade = tk.Button(trade_report_frame, text="清除成交回報",
                                        command=self.clear_trade_report, bg="lightgray")
        self.btn_clear_trade.grid(column=0, row=1, pady=5)

        # 策略控制面板 (暫時移除，改為獨立分頁)
        # if STRATEGY_AVAILABLE:
        #     self.create_strategy_panel()

        # 設定主框架的權重，讓訊息區域可以擴展到底部
        self.grid_rowconfigure(8, weight=1)  # 修改為第8行（訊息區域）
        self.grid_columnconfigure(0, weight=1)

    def create_strategy_panel(self):
        """創建策略控制面板"""
        try:
            # 創建策略面板框架
            strategy_frame = tk.LabelFrame(self, text="🎯 開盤區間突破策略", fg="blue", font=("Arial", 12, "bold"))
            strategy_frame.grid(column=0, row=9, columnspan=6, sticky=tk.E + tk.W, padx=5, pady=5)

            # 創建策略控制面板
            self.strategy_panel = StrategyControlPanel(strategy_frame, quote_callback=self.on_strategy_price_update)
            self.strategy_panel.grid(column=0, row=0, sticky=tk.E + tk.W + tk.N + tk.S)

            # 設定策略面板的權重
            strategy_frame.grid_rowconfigure(0, weight=1)
            strategy_frame.grid_columnconfigure(0, weight=1)

            self.add_message("✅ 策略控制面板已載入")

        except Exception as e:
            self.add_message(f"❌ 策略面板載入失敗: {e}")
            logger.error(f"策略面板載入失敗: {e}")

    def on_strategy_price_update(self, price, timestamp=None):
        """策略面板的價格更新回調"""
        # 這個方法會被策略面板調用來獲取即時報價
        # 我們可以在這裡整合即時報價系統
        pass

    def load_default_values(self):
        """載入預設值"""
        # 載入測試用預設值
        self.entry_account.insert(0, TEST_FUTURE_CONFIG.get('ACCOUNT', ''))
        self.entry_price.insert(0, str(TEST_FUTURE_CONFIG.get('PRICE', 22000)))
        self.entry_quantity.insert(0, str(TEST_FUTURE_CONFIG.get('QUANTITY', 1)))
        
        # 觸發商品資訊更新
        self.on_product_changed(None)
    
    def on_product_changed(self, event):
        """商品選擇改變時的處理"""
        try:
            selected = self.combo_product.get()
            if selected:
                # 提取商品代碼
                product_code = selected.split(' ')[0]
                if product_code in FUTURE_PRODUCTS:
                    product_info = FUTURE_PRODUCTS[product_code]
                    info_text = f"商品: {product_info['name']} ({product_code})\n"
                    info_text += f"說明: {product_info['description']}\n"
                    info_text += f"最小跳動點: {product_info['tick_size']}\n"
                    info_text += f"契約規模: {product_info['contract_size']}"
                    self.label_product_info.config(text=info_text)
        except:
            pass

    def auto_query_near_month(self):
        """自動查詢小台指近月合約"""
        try:
            self.add_message("【自動查詢】開始查詢小台指近月合約...")

            # 嘗試從期貨報價查詢模組取得近月合約
            if hasattr(self.master, 'master') and hasattr(self.master.master, 'future_quote_frame'):
                quote_frame = self.master.master.future_quote_frame

                # 檢查是否已有查詢結果
                near_month = quote_frame.get_near_month_contract()
                if near_month:
                    self.add_message(f"【成功】找到近月合約: {near_month}")
                    self.update_product_with_near_month(near_month)
                else:
                    self.add_message("【提示】請先到「期貨報價查詢」頁籤查詢商品清單")
                    messagebox.showinfo("提示", "請先到「期貨報價查詢」頁籤查詢小台指近月合約")
            else:
                self.add_message("【錯誤】無法存取期貨報價查詢模組")
                messagebox.showerror("錯誤", "無法存取期貨報價查詢模組")

        except Exception as e:
            self.add_message(f"【錯誤】自動查詢近月合約失敗: {str(e)}")
            messagebox.showerror("錯誤", f"自動查詢失敗: {str(e)}")

    def update_product_with_near_month(self, near_month_code):
        """使用近月合約代碼更新商品選擇"""
        try:
            # 檢查近月合約代碼是否在現有選項中
            current_values = list(self.combo_product['values'])

            # 尋找匹配的選項
            for value in current_values:
                if near_month_code in value:
                    self.combo_product.set(value)
                    self.add_message(f"【更新】已選擇近月合約: {value}")
                    self.on_product_changed(None)  # 觸發選擇事件
                    return

            # 如果沒有找到匹配的選項，添加新選項
            new_option = f"{near_month_code} (API查詢近月)"
            current_values.append(new_option)
            self.combo_product['values'] = current_values
            self.combo_product.set(new_option)
            self.add_message(f"【新增】添加並選擇近月合約: {new_option}")
            self.on_product_changed(None)  # 觸發選擇事件

        except Exception as e:
            self.add_message(f"【錯誤】更新商品選擇失敗: {str(e)}")

    def use_manual_product(self):
        """使用手動輸入的商品代碼"""
        try:
            manual_code = self.entry_manual_product.get().strip()
            if not manual_code:
                messagebox.showwarning("警告", "請先輸入商品代碼")
                return

            self.add_message(f"【手動輸入】使用商品代碼: {manual_code}")

            # 添加到下拉選單選項中
            current_values = list(self.combo_product['values'])
            new_option = f"{manual_code} (手動輸入)"

            # 檢查是否已存在
            if new_option not in current_values:
                current_values.append(new_option)
                self.combo_product['values'] = current_values

            # 設定為當前選擇
            self.combo_product.set(new_option)
            self.add_message(f"【成功】已設定商品代碼為: {manual_code}")

            # 觸發選擇事件
            self.on_product_changed(None)

            # 清空輸入框
            self.entry_manual_product.delete(0, tk.END)

        except Exception as e:
            self.add_message(f"【錯誤】使用手動商品代碼失敗: {str(e)}")
            messagebox.showerror("錯誤", f"設定商品代碼失敗: {str(e)}")

    def add_message(self, message):
        """添加訊息到顯示區域"""
        self.text_message.insert(tk.END, message + "\n")
        self.text_message.see(tk.END)
        logger.info(message)
    
    def clear_form(self):
        """清除表單"""
        self.entry_account.delete(0, tk.END)
        self.entry_price.delete(0, tk.END)
        self.entry_quantity.delete(0, tk.END)
        self.text_message.delete(1.0, tk.END)
    
    def query_account(self):
        """查詢期貨帳號資訊"""
        if not self.m_pSKOrder:
            self.add_message("【錯誤】SKOrder物件未初始化")
            messagebox.showerror("錯誤", "SKOrder物件未初始化")
            return

        try:
            self.add_message("【查詢】開始查詢期貨帳號資訊...")

            # 根據官方文件，需要先初始化SKOrderLib
            self.add_message("【初始化】正在初始化SKOrderLib...")
            nCode = self.m_pSKOrder.SKOrderLib_Initialize()

            if self.m_pSKCenter:
                msg_text = self.m_pSKCenter.SKCenterLib_GetReturnCodeMessage(nCode)
            else:
                msg_text = f"結果代碼: {nCode}"

            self.add_message(f"【初始化結果】{msg_text} (代碼: {nCode})")

            if nCode != 0:
                self.add_message("【錯誤】SKOrderLib初始化失敗，無法進行下單操作")
                self.add_message("【提示】請確認已簽署期貨API下單聲明書")
                return

            # 初始化成功後，讀取憑證
            self.add_message("【憑證】SKOrderLib初始化成功，開始讀取憑證...")

            # 取得登入ID (從父視窗或全域變數)
            login_id = getattr(self, 'login_id', None)
            if not login_id:
                # 嘗試從父視窗取得
                try:
                    login_id = self.master.master.login_id if hasattr(self.master.master, 'login_id') else None
                except:
                    login_id = None

            if login_id:
                self.add_message(f"【憑證】使用登入ID讀取憑證: {login_id}")
                nCode = self.m_pSKOrder.ReadCertByID(login_id)

                if self.m_pSKCenter:
                    msg_text = self.m_pSKCenter.SKCenterLib_GetReturnCodeMessage(nCode)
                else:
                    msg_text = f"結果代碼: {nCode}"

                self.add_message(f"【讀取憑證】{msg_text} (代碼: {nCode})")

                if nCode == 0:
                    self.add_message("【成功】憑證讀取成功，開始查詢帳號...")

                    # 憑證讀取成功後，查詢帳號
                    nCode = self.m_pSKOrder.GetUserAccount()

                    if self.m_pSKCenter:
                        msg_text = self.m_pSKCenter.SKCenterLib_GetReturnCodeMessage(nCode)
                    else:
                        msg_text = f"結果代碼: {nCode}"

                    self.add_message(f"【查詢帳號】{msg_text} (代碼: {nCode})")

                    if nCode == 0:
                        self.add_message("【成功】期貨帳號查詢成功，請查看回報訊息")
                        self.add_message("【重要】請注意回報訊息中的帳號格式")
                        self.add_message("【提示】帳號格式可能是：分公司代碼-帳號 或其他格式")
                        self.add_message("【建議】請將回報中的完整帳號複製到帳號欄位")
                    else:
                        self.add_message(f"【失敗】期貨帳號查詢失敗: {msg_text}")
                else:
                    self.add_message(f"【失敗】憑證讀取失敗: {msg_text}")
                    self.add_message("【提示】請確認憑證是否正確安裝")
            else:
                self.add_message("【錯誤】無法取得登入ID，請確認已正確登入")
                self.add_message("【提示】請先在主程式登入後再查詢帳號")

        except Exception as e:
            error_msg = f"查詢期貨帳號時發生錯誤: {str(e)}"
            self.add_message(f"【錯誤】{error_msg}")
            messagebox.showerror("查詢錯誤", error_msg)
    
    def query_position(self):
        """查詢期貨部位"""
        account = self.entry_account.get().strip()
        if not account:
            messagebox.showerror("錯誤", "請先填入期貨帳號")
            return
        
        self.add_message(f"【查詢】查詢期貨部位 - 帳號: {account}")
        self.add_message("【提示】期貨部位查詢功能需要根據官方API文件實現")
    
    def test_future_order(self):
        """測試期貨下單 - 使用新的OrderExecutor架構"""
        if not self.m_pSKOrder:
            self.add_message("【錯誤】SKOrder物件未初始化")
            messagebox.showerror("錯誤", "SKOrder物件未初始化")
            return

        # 取得表單資料
        account_input = self.entry_account.get().strip()
        product_selected = self.combo_product.get()
        month = self.combo_month.get()
        price = self.entry_price.get().strip()
        quantity = self.entry_quantity.get().strip()

        # 檢查必填欄位
        if not all([account_input, product_selected, month, price, quantity]):
            messagebox.showerror("錯誤", "請填入所有必要欄位")
            return

        # 自動加上期貨帳號前綴 F020000
        if not account_input.startswith('F020000'):
            account = f"F020000{account_input}"
            self.add_message(f"【帳號格式】自動加上前綴: {account_input} -> {account}")
            # 同時更新界面顯示
            self.entry_account.delete(0, tk.END)
            self.entry_account.insert(0, account)
        else:
            account = account_input

        try:
            # 提取商品代碼
            product_code = product_selected.split(' ')[0]

            # 檢查是否為手動輸入的完整商品代碼 (不需要組合月份)
            manual_input_patterns = [
                "小台近", "大台近", "電子近", "金融近",  # 中文格式
                "MTX00", "TX00", "TE00", "TF00",        # 近月格式
                "MXFR1", "TXFR1", "TXER1",             # R1格式
            ]

            if any(pattern in product_code for pattern in manual_input_patterns) or \
               product_code.endswith("R1") or product_code.endswith("00") or len(product_code) >= 6:
                # 這是完整的商品代碼，直接使用，不組合月份
                full_product_code = product_code
                self.add_message(f"【商品代碼】使用完整代碼: {full_product_code}")
            else:
                # 傳統格式，需要組合月份
                full_product_code = f"{product_code}{month}"
                self.add_message(f"【商品代碼】組合代碼: {product_code} + {month} = {full_product_code}")

            # 轉換數值
            price_val = float(price)
            quantity_val = int(quantity)

            # 取得選擇的參數
            buy_sell = self.combo_buy_sell.current()  # 0:買進, 1:賣出
            period = self.combo_period.current()  # 0:ROD, 1:IOC, 2:FOK
            day_trade = self.combo_day_trade.current()  # 0:非當沖, 1:當沖
            new_close = self.combo_new_close.current()  # 0:新倉, 1:平倉, 2:自動
            reserved = self.combo_reserved.current()  # 0:盤中, 1:T盤預約

            self.add_message(f"【下單準備】帳號:{account}, 商品:{full_product_code}")
            self.add_message(f"【參數】價格:{price_val}, 數量:{quantity_val}, 買賣:{BUYSELLSET[buy_sell]}")
            self.add_message(f"【設定】委託條件:{PERIODSET['future'][period]}, 當沖:{FLAGSET['future'][day_trade]}")
            self.add_message(f"【倉別】{NEWCLOSESET['future'][new_close]}, 盤別:{RESERVEDSET[reserved]}")

            # 建立下單參數字典
            order_params = {
                'account': account,
                'product': full_product_code,
                'direction': 'BUY' if buy_sell == 0 else 'SELL',
                'price': price_val,
                'quantity': quantity_val,
                'order_type': ['ROD', 'IOC', 'FOK'][period],
                'day_trade': day_trade,
                'new_close': new_close,
                'reserved': reserved
            }

            # 使用新的OrderExecutor進行手動下單 (保持確認機制)
            self.add_message("【執行】使用OrderExecutor執行手動下單...")
            result = self.order_executor.manual_order(order_params)

            if result['success']:
                self.add_message(f"【成功】期貨下單指令已送出: {result['message']}")
                # 延遲查詢委託狀況
                self.after(2000, self.query_pending_orders)
            else:
                self.add_message(f"【失敗】期貨下單失敗: {result['message']}")

        except ValueError as e:
            error_msg = f"數值格式錯誤: {str(e)}"
            self.add_message(f"【錯誤】{error_msg}")
            messagebox.showerror("格式錯誤", error_msg)
        except Exception as e:
            error_msg = f"期貨下單時發生錯誤: {str(e)}"
            self.add_message(f"【錯誤】{error_msg}")
            messagebox.showerror("下單錯誤", error_msg)

    def send_future_order_clr(self, account, stock_no, buy_sell, trade_type, day_trade,
                             price, quantity, new_close, reserved):
        """發送期貨下單 - 根據官方API實現"""
        try:
            # 先檢查並初始化SKOrderLib
            self.add_message("【初始化】檢查SKOrderLib初始化狀態...")
            try:
                nCode = self.m_pSKOrder.SKOrderLib_Initialize()
                if nCode != 0:
                    if self.m_pSKCenter:
                        msg_text = self.m_pSKCenter.SKCenterLib_GetReturnCodeMessage(nCode)
                    else:
                        msg_text = f"錯誤代碼: {nCode}"
                    self.add_message(f"【錯誤】SKOrderLib初始化失敗: {msg_text}")
                    if nCode == 1001:
                        self.add_message("【提示】錯誤1001通常表示：")
                        self.add_message("1. 尚未簽署期貨API下單聲明書")
                        self.add_message("2. 帳號格式不正確 (應為完整帳號)")
                        self.add_message("3. 期貨帳號未開通")
                    return False
                else:
                    self.add_message("【成功】SKOrderLib初始化成功")
            except Exception as e:
                self.add_message(f"【錯誤】初始化檢查失敗: {str(e)}")
                return False

            # 讀取憑證 (解決1038錯誤的關鍵步驟)
            self.add_message("【憑證】讀取憑證以解決1038錯誤...")
            login_id = getattr(self, 'login_id', None)
            if not login_id:
                # 嘗試從父視窗取得登入ID
                try:
                    if hasattr(self.master, 'master') and hasattr(self.master.master, 'login_id'):
                        login_id = self.master.master.login_id
                    elif hasattr(self.master, 'login_id'):
                        login_id = self.master.login_id
                    else:
                        # 嘗試使用固定的登入ID (根據你提供的資訊)
                        login_id = "E123354882"
                        self.add_message(f"【憑證】使用預設登入ID: {login_id}")
                except:
                    login_id = "E123354882"
                    self.add_message(f"【憑證】使用預設登入ID: {login_id}")

            if login_id:
                try:
                    self.add_message(f"【憑證】使用登入ID讀取憑證: {login_id}")
                    nCode = self.m_pSKOrder.ReadCertByID(login_id)

                    if self.m_pSKCenter:
                        msg_text = self.m_pSKCenter.SKCenterLib_GetReturnCodeMessage(nCode)
                    else:
                        msg_text = f"結果代碼: {nCode}"

                    self.add_message(f"【讀取憑證】{msg_text} (代碼: {nCode})")

                    if nCode == 0:
                        self.add_message("【成功】憑證讀取成功，應該可以解決1038錯誤")
                    else:
                        self.add_message(f"【警告】憑證讀取失敗，可能導致1038錯誤: {msg_text}")
                        self.add_message("【提示】請確認憑證是否正確安裝")
                        # 繼續執行，但提醒用戶
                except Exception as e:
                    self.add_message(f"【錯誤】讀取憑證時發生例外: {str(e)}")
                    self.add_message("【提示】可能導致1038憑證驗證錯誤")
            else:
                self.add_message("【警告】無法取得登入ID，可能導致1038憑證錯誤")
                self.add_message("【建議】請確認已正確登入")

            # 導入SKCOMLib
            import comtypes.gen.SKCOMLib as sk

            # 建立下單用的參數(FUTUREORDER)物件
            try:
                oOrder = sk.FUTUREORDER()
                self.add_message("【成功】FUTUREORDER物件建立成功")
            except Exception as e:
                self.add_message(f"【錯誤】無法建立FUTUREORDER物件: {str(e)}")
                self.add_message("【提示】請確認SKCOMLib已正確註冊")
                return False

            # 填入完整帳號
            oOrder.bstrFullAccount = account

            # 填入期貨代號
            oOrder.bstrStockNo = stock_no

            # 買賣別 (0:買進, 1:賣出)
            oOrder.sBuySell = buy_sell

            # 委託條件 (0:ROD, 1:IOC, 2:FOK)
            oOrder.sTradeType = trade_type

            # 當沖與否 (0:非當沖, 1:當沖)
            oOrder.sDayTrade = day_trade

            # 委託價
            oOrder.bstrPrice = str(price)

            # 委託數量
            oOrder.nQty = quantity

            # 新倉、平倉、自動 (0:新倉, 1:平倉, 2:自動)
            oOrder.sNewClose = new_close

            # 盤中、T盤預約 (0:盤中, 1:T盤預約)
            oOrder.sReserved = reserved

            self.add_message("【API】準備調用SendFutureOrderCLR...")

            # 調用期貨下單API (非同步下單)
            # 根據官方案例：message, m_nCode = skO.SendFutureOrderCLR(Global.Global_IID, bAsyncOrder, oOrder)
            # 這裡使用非同步下單 (True)

            # 取得登入ID作為Token參數 (解決101 Token參數不足錯誤)
            login_id = getattr(self, 'login_id', None)
            if not login_id:
                # 嘗試從父視窗取得登入ID
                try:
                    if hasattr(self.master, 'master') and hasattr(self.master.master, 'login_id'):
                        login_id = self.master.master.login_id
                    elif hasattr(self.master, 'login_id'):
                        login_id = self.master.login_id
                    else:
                        # 使用預設的登入ID
                        login_id = "E123354882"
                        self.add_message(f"【Token】使用預設登入ID: {login_id}")
                except:
                    login_id = "E123354882"
                    self.add_message(f"【Token】使用預設登入ID: {login_id}")

            if login_id:
                token_id = login_id
                self.add_message(f"【Token】使用登入ID作為Token參數: {token_id}")
            else:
                token_id = ""
                self.add_message("【警告】無法取得登入ID，使用空字串作為Token")

            try:
                # 使用登入ID作為Token參數 (解決101錯誤)
                self.add_message(f"【API調用】SendFutureOrderCLR(Token: {token_id}, 非同步: True)")
                result = self.m_pSKOrder.SendFutureOrderCLR(token_id, True, oOrder)

                # 檢查返回值類型
                if isinstance(result, tuple) and len(result) == 2:
                    message, nCode = result
                    self.add_message(f"【API返回】訊息: {message}")
                else:
                    # 如果返回值不是元組，可能只是錯誤代碼
                    nCode = result if isinstance(result, int) else -1
                    message = "API調用完成"
                    self.add_message(f"【API返回】代碼: {nCode}")

            except Exception as api_error:
                self.add_message(f"【API錯誤】{api_error}")
                # 嘗試使用基本的SendFutureOrder方法
                try:
                    self.add_message("【嘗試】使用SendFutureOrder方法...")
                    self.add_message(f"【API調用】SendFutureOrder(Token: {token_id}, 非同步: True)")
                    result = self.m_pSKOrder.SendFutureOrder(token_id, True, oOrder)

                    if isinstance(result, tuple) and len(result) == 2:
                        message, nCode = result
                        self.add_message(f"【API返回】訊息: {message}")
                    else:
                        nCode = result if isinstance(result, int) else -1
                        message = "SendFutureOrder調用完成"
                        self.add_message(f"【API返回】代碼: {nCode}")

                except Exception as api_error2:
                    self.add_message(f"【API錯誤2】{api_error2}")
                    nCode = -1
                    message = "所有API調用都失敗"

            # 取得回傳訊息
            if self.m_pSKCenter:
                msg_text = self.m_pSKCenter.SKCenterLib_GetReturnCodeMessage(nCode)
            else:
                msg_text = f"結果代碼: {nCode}"

            self.add_message(f"【API回應】{msg_text} (代碼: {nCode})")

            if nCode == 0:
                self.add_message("【成功】期貨下單成功！")
                return True
            else:
                self.add_message(f"【失敗】期貨下單失敗: {msg_text}")
                return False

        except Exception as e:
            self.add_message(f"【錯誤】期貨下單API調用失敗: {str(e)}")
            return False

    def register_quote_events(self):
        """註冊報價事件處理 - 簡化版本避免GIL錯誤"""
        if not self.m_pSKQuote:
            self.add_message("【報價】SKQuote物件未初始化，無法註冊報價事件")
            return

        try:
            self.add_message("【報價】開始註冊報價事件處理...")

            # 使用最簡單的事件處理方式
            class SimpleQuoteEvent():
                def __init__(self, parent):
                    self.parent = parent

                def OnConnection(self, nKind, nCode):
                    """連線狀態事件 - 🔧 GIL錯誤修復版本"""
                    try:
                        # 🔧 使用線程鎖確保線程安全
                        with self.parent.data_lock:
                            if nKind == 3003:  # SK_SUBJECT_CONNECTION_STOCKS_READY
                                # 直接設定狀態，不更新UI (避免GIL錯誤)
                                self.parent.stocks_ready = True
                                # 如果有待訂閱的商品，直接訂閱
                                if hasattr(self.parent, 'pending_subscription') and self.parent.pending_subscription:
                                    # 使用簡單的方式觸發訂閱
                                    self.parent.after(100, self.parent.safe_subscribe_ticks)
                    except Exception as e:
                        # 🔧 GIL錯誤修復：記錄錯誤但絕不拋出異常
                        try:
                            import logging
                            logging.getLogger('order.future_order').debug(f"OnConnection錯誤: {e}")
                        except:
                            pass  # 連LOG都失敗就完全忽略
                    return 0

                def OnNotifyTicksLONG(self, sMarketNo, nStockidx, nPtr, lDate, lTimehms, lTimemillismicros, nBid, nAsk, nClose, nQty, nSimulate):
                    """即時Tick資料事件 - 🔧 GIL錯誤修復版本"""
                    try:
                        # 🔧 使用線程鎖確保線程安全
                        with self.parent.quote_lock:
                            # 簡化時間格式化
                            time_str = f"{lTimehms:06d}"
                            formatted_time = f"{time_str[:2]}:{time_str[2:4]}:{time_str[4:6]}"

                            # 直接更新價格顯示 (最小化UI操作)
                            try:
                                with self.parent.ui_lock:
                                    self.parent.label_price.config(text=str(nClose))
                                    self.parent.label_time.config(text=formatted_time)

                                # 🎯 策略數據更新：安全方式，不直接調用回調
                                try:
                                    with self.parent.data_lock:
                                        # 修正價格格式 (群益API價格通常需要除以100)
                                        corrected_price = nClose / 100.0 if nClose > 100000 else nClose

                                        # 只更新數據，不調用回調（避免GIL衝突）
                                        self.parent.last_price = corrected_price
                                        self.parent.last_update_time = formatted_time
                                except Exception as strategy_error:
                                    # 數據更新失敗不影響主要功能
                                    pass

                                # 🔧 GIL修復：移除價格橋接和TCP廣播功能
                                # 策略已整合，不再需要這些過渡功能

                            except Exception as ui_error:
                                # 價格橋接失敗不影響主要功能
                                pass

                            # 控制LOG頻率，使用最安全的方式
                            if hasattr(self.parent, '_last_log_time'):
                                current_time = time.time()
                                if current_time - self.parent._last_log_time > 1:  # 每1秒記錄一次
                                    self.parent._last_log_time = current_time
                                    tick_msg = f"【Tick】價格:{nClose} 買:{nBid} 賣:{nAsk} 量:{nQty} 時間:{formatted_time}"
                                    # 只輸出到控制台，避免GIL錯誤
                                    print(tick_msg)
                                    # 使用最簡單的方式添加到LOG (直接調用，不使用after_idle)
                                    try:
                                        import logging
                                        logging.getLogger('order.future_order').info(tick_msg)
                                    except:
                                        pass
                            else:
                                self.parent._last_log_time = time.time()
                                tick_msg = f"【Tick】價格:{nClose} 買:{nBid} 賣:{nAsk} 量:{nQty} 時間:{formatted_time}"
                                # 只輸出到控制台，避免GIL錯誤
                                print(tick_msg)
                                # 使用最簡單的方式添加到LOG
                                try:
                                    import logging
                                    logging.getLogger('order.future_order').info(tick_msg)
                                except:
                                    pass
                    except Exception as e:
                        # 🔧 GIL錯誤修復：記錄錯誤但絕不拋出異常
                        try:
                            import logging
                            logging.getLogger('order.future_order').debug(f"OnNotifyTicksLONG錯誤: {e}")
                        except:
                            pass  # 連LOG都失敗就完全忽略
                    return 0

                def OnNotifyBest5LONG(self, sMarketNo, nStockidx, nBestBid1, nBestBidQty1, nBestBid2, nBestBidQty2, nBestBid3, nBestBidQty3, nBestBid4, nBestBidQty4, nBestBid5, nBestBidQty5, nExtendBid, nExtendBidQty, nBestAsk1, nBestAskQty1, nBestAsk2, nBestAskQty2, nBestAsk3, nBestAskQty3, nBestAsk4, nBestAskQty4, nBestAsk5, nBestAskQty5, nExtendAsk, nExtendAskQty, nSimulate):
                    """五檔報價事件 - 🔧 GIL錯誤修復版本"""
                    try:
                        # 🔧 使用線程鎖確保線程安全
                        with self.parent.quote_lock:
                            # 控制五檔LOG頻率，使用最安全的方式
                            if hasattr(self.parent, '_last_best5_time'):
                                current_time = time.time()
                                if current_time - self.parent._last_best5_time > 3:  # 每3秒記錄一次
                                    self.parent._last_best5_time = current_time
                                    best5_msg = f"【五檔】買1:{nBestBid1}({nBestBidQty1}) 賣1:{nBestAsk1}({nBestAskQty1})"
                                    # 只輸出到控制台，避免GIL錯誤
                                    print(best5_msg)
                                    # 使用最簡單的方式添加到LOG
                                    try:
                                        import logging
                                        logging.getLogger('order.future_order').info(best5_msg)
                                    except:
                                        pass
                            else:
                                self.parent._last_best5_time = time.time()
                                best5_msg = f"【五檔】買1:{nBestBid1}({nBestBidQty1}) 賣1:{nBestAsk1}({nBestAskQty1})"
                                # 只輸出到控制台，避免GIL錯誤
                                print(best5_msg)
                                # 使用最簡單的方式添加到LOG
                                try:
                                    import logging
                                    logging.getLogger('order.future_order').info(best5_msg)
                                except:
                                    pass
                    except Exception as e:
                        # 🔧 GIL錯誤修復：記錄錯誤但絕不拋出異常
                        try:
                            import logging
                            logging.getLogger('order.future_order').debug(f"OnNotifyBest5LONG錯誤: {e}")
                        except:
                            pass  # 連LOG都失敗就完全忽略
                    return 0

            # 建立簡化的事件處理器
            self.quote_event = SimpleQuoteEvent(self)

            # 嘗試註冊事件
            try:
                import comtypes.client
                self.quote_event_handler = comtypes.client.GetEvents(self.m_pSKQuote, self.quote_event)
                self.add_message("【成功】報價事件處理註冊成功 (簡化版本)")
                return True
            except Exception as e:
                self.add_message(f"【錯誤】註冊報價事件失敗: {str(e)}")
                return False

        except Exception as e:
            self.add_message(f"【錯誤】建立報價事件處理器失敗: {str(e)}")
            return False

    def should_log_tick(self):
        """控制Tick LOG頻率，避免LOG過多"""
        current_time = time.time()
        if not hasattr(self, '_last_tick_log_time'):
            self._last_tick_log_time = 0

        # 每秒最多記錄一次Tick
        if current_time - self._last_tick_log_time > 1.0:
            self._last_tick_log_time = current_time
            return True
        return False

    def should_log_best5(self):
        """控制五檔LOG頻率"""
        current_time = time.time()
        if not hasattr(self, '_last_best5_log_time'):
            self._last_best5_log_time = 0

        # 每5秒最多記錄一次五檔
        if current_time - self._last_best5_log_time > 5.0:
            self._last_best5_log_time = current_time
            return True
        return False

    def start_quote_monitoring(self):
        """開始監控MTX00報價"""
        if not self.m_pSKQuote:
            self.add_message("【錯誤】SKQuote物件未初始化，無法監控報價")
            return

        try:
            self.add_message("【報價監控】開始啟動MTX00報價監控...")

            # 1. 先連線到報價伺服器
            self.add_message("【步驟1】連線到報價伺服器...")
            nCode = self.m_pSKQuote.SKQuoteLib_EnterMonitorLONG()

            if self.m_pSKCenter:
                msg_text = self.m_pSKCenter.SKCenterLib_GetReturnCodeMessage(nCode)
            else:
                msg_text = f"結果代碼: {nCode}"

            self.add_message(f"【連線結果】{msg_text} (代碼: {nCode})")

            if nCode != 0:
                self.add_message("【失敗】無法連線到報價伺服器")
                return

            # 2. 等待連線完成和商品資料準備
            self.add_message("【步驟2】等待商品資料載入完成...")
            self.add_message("【提示】請等待OnConnection事件回報3003狀態")

            # 設定標記，等待連線完成後再訂閱
            self.pending_subscription = True
            self.subscription_product = self.current_product.replace(' ', '')

            # 檢查是否已經連線完成
            if hasattr(self, 'stocks_ready') and self.stocks_ready:
                self.add_message("【提示】商品資料已準備完成，立即訂閱")
                self.subscribe_ticks()
            else:
                self.add_message("【提示】等待OnConnection事件3003後自動訂閱")

            if self.m_pSKCenter:
                msg_text = self.m_pSKCenter.SKCenterLib_GetReturnCodeMessage(nCode)
            else:
                msg_text = f"結果代碼: {nCode}"

            self.add_message(f"【訂閱結果】{msg_text} (代碼: {nCode})")

            if nCode == 0:
                self.quote_monitoring = True
                self.label_status.config(text="監控中", fg="green")
                self.btn_start_quote.config(state="disabled")
                self.btn_stop_quote.config(state="normal")
                self.add_message("【成功】MTX00報價監控已啟動，等待即時資料...")
                self.add_message("【說明】將以毫秒級精度接收即時Tick資料")
            else:
                self.add_message(f"【失敗】無法訂閱MTX00報價: {msg_text}")

        except Exception as e:
            self.add_message(f"【錯誤】啟動報價監控時發生錯誤: {str(e)}")

    def subscribe_ticks(self):
        """訂閱Tick資料 (在連線完成後調用)"""
        try:
            if not self.m_pSKQuote:
                self.add_message("【錯誤】SKQuote物件未初始化")
                return False

            # 3. 訂閱MTX00的Tick資料
            self.add_message("【步驟3】訂閱MTX00即時Tick資料...")

            # 使用Page 0訂閱MTX00 (完全參考官方Quote.py第440行的方式)
            pn = 0  # 使用官方案例的變數名
            product_code = getattr(self, 'subscription_product', self.current_product).replace(' ', '')

            self.add_message(f"【訂閱】商品: {product_code}, Page: {pn}")

            # 完全按照官方案例的方式調用 (Quote.py第440行)
            nCode = self.m_pSKQuote.SKQuoteLib_RequestTicks(pn, product_code)

            if self.m_pSKCenter:
                msg_text = self.m_pSKCenter.SKCenterLib_GetReturnCodeMessage(nCode)
            else:
                msg_text = f"結果代碼: {nCode}"

            self.add_message(f"【訂閱結果】{msg_text} (代碼: {nCode})")

            if nCode == 0:
                self.quote_monitoring = True
                self.label_status.config(text="監控中", fg="green")
                self.btn_start_quote.config(state="disabled")
                self.btn_stop_quote.config(state="normal")
                self.add_message("【成功】MTX00報價監控已啟動，等待即時資料...")
                self.add_message("【說明】將接收即時Tick資料並顯示在LOG中")

                # 清除待訂閱標記
                self.pending_subscription = False
                return True
            else:
                self.add_message(f"【失敗】無法訂閱MTX00報價: {msg_text}")
                return False

        except Exception as e:
            self.add_message(f"【錯誤】訂閱Tick資料時發生錯誤: {str(e)}")
            return False

    def stop_quote_monitoring(self):
        """停止監控報價"""
        try:
            self.add_message("【報價監控】停止MTX00報價監控...")

            if self.m_pSKQuote:
                # 停止訂閱 (使用正確的CancelRequestTicks API)
                product_code = self.current_product.replace(' ', '')  # 移除空格

                self.add_message(f"【停止訂閱】商品: {product_code}")

                # 使用正確的取消訂閱API (只需要商品代號參數)
                nCode = self.m_pSKQuote.SKQuoteLib_CancelRequestTicks(product_code)

                if self.m_pSKCenter:
                    msg_text = self.m_pSKCenter.SKCenterLib_GetReturnCodeMessage(nCode)
                else:
                    msg_text = f"結果代碼: {nCode}"

                self.add_message(f"【停止訂閱】{msg_text} (代碼: {nCode})")

            self.quote_monitoring = False
            self.label_status.config(text="已停止", fg="gray")
            self.btn_start_quote.config(state="normal")
            self.btn_stop_quote.config(state="disabled")
            self.add_message("【成功】報價監控已停止")

        except Exception as e:
            self.add_message(f"【錯誤】停止報價監控時發生錯誤: {str(e)}")

    def update_quote_display(self, price, time_str, bid, ask, qty):
        """更新報價顯示"""
        try:
            # 更新最新價
            self.label_price.config(text=str(price))

            # 更新時間
            self.label_time.config(text=time_str)

            # 更新商品代碼
            self.label_product.config(text=self.current_product)

            # 記錄最新價格和時間
            self.last_price = price
            self.last_update_time = time_str

            # 價格顏色變化 (簡單的漲跌顏色)
            if hasattr(self, '_previous_price'):
                if price > self._previous_price:
                    self.label_price.config(fg="red")  # 上漲紅色
                elif price < self._previous_price:
                    self.label_price.config(fg="green")  # 下跌綠色
                else:
                    self.label_price.config(fg="black")  # 平盤黑色

            self._previous_price = price

        except Exception as e:
            self.add_message(f"【錯誤】更新報價顯示時發生錯誤: {str(e)}")

    def safe_update_quote_display(self, price, time_str, bid, ask, qty):
        """線程安全的報價顯示更新"""
        try:
            # 更新最新價
            self.label_price.config(text=str(price))

            # 更新時間
            self.label_time.config(text=time_str)

            # 更新商品代碼
            self.label_product.config(text=self.current_product)

            # 記錄最新價格和時間
            self.last_price = price
            self.last_update_time = time_str

            # 價格顏色變化 (簡單的漲跌顏色)
            if hasattr(self, '_previous_price'):
                if price > self._previous_price:
                    self.label_price.config(fg="red")  # 上漲紅色
                elif price < self._previous_price:
                    self.label_price.config(fg="green")  # 下跌綠色
                else:
                    self.label_price.config(fg="black")  # 平盤黑色

            self._previous_price = price

        except Exception as e:
            # 錯誤處理也要線程安全
            self.after_idle(self.safe_add_message, f"【錯誤】安全更新報價顯示時發生錯誤: {str(e)}")

    def safe_add_message(self, message):
        """線程安全的訊息添加"""
        try:
            self.add_message(message)
        except Exception as e:
            # 如果連LOG都出錯，只能忽略了
            pass

    def safe_update_connection_status(self, status_text, color):
        """線程安全的連線狀態更新"""
        try:
            self.label_status.config(text=status_text, fg=color)
        except Exception as e:
            pass

    def safe_subscribe_ticks(self):
        """線程安全的Tick訂閱"""
        try:
            self.subscribe_ticks()
        except Exception as e:
            self.after_idle(self.safe_add_message, f"【錯誤】安全訂閱Tick時發生錯誤: {str(e)}")

    def query_pending_orders(self):
        """查詢盤中委託單"""
        if not self.m_pSKOrder:
            self.add_message("【錯誤】SKOrder物件未初始化")
            return

        try:
            self.add_message("【委託查詢】開始查詢盤中委託單...")

            # 清空現有資料
            self.pending_orders.clear()
            for item in self.tree_orders.get_children():
                self.tree_orders.delete(item)

            # 確保SKOrder已初始化
            try:
                nCode = self.m_pSKOrder.SKOrderLib_Initialize()
                if nCode != 0:
                    self.add_message(f"【初始化】SKOrder初始化結果: {nCode}")
            except:
                pass  # 可能已經初始化過

            # 取得登入ID和帳號
            login_id = "E123354882"
            account = "F0200006363839"  # 期貨帳號格式

            self.add_message(f"【參數】登入ID: {login_id}, 帳號: {account}")

            # 使用GetOrderReport查詢盤中委託 (format=1 表示全部委託)
            format_type = 1  # 1 = 全部委託 (包含盤中委託)

            try:
                # 調用API查詢盤中委託
                bstrResult = self.m_pSKOrder.GetOrderReport(login_id, account, format_type)

                self.add_message(f"【API調用】GetOrderReport({login_id}, {account}, {format_type}) - 盤中委託查詢")

                if bstrResult:
                    self.add_message("【成功】盤中委託查詢完成，處理結果...")
                    # 添加原始資料LOG以便調試
                    self.add_message(f"【原始資料】{bstrResult[:200]}...")  # 只顯示前200字符
                    self.parse_pending_orders_data(bstrResult)
                else:
                    self.add_message("【結果】目前無盤中委託")

            except Exception as api_error:
                self.add_message(f"【API錯誤】查詢盤中委託失敗: {str(api_error)}")

        except Exception as e:
            self.add_message(f"【錯誤】查詢盤中委託時發生錯誤: {str(e)}")

    def parse_pending_orders_data(self, data):
        """解析盤中委託資料"""
        try:
            self.add_message("【解析】開始解析盤中委託資料...")

            lines = data.split('\n')
            order_count = 0

            for line in lines:
                line = line.strip()
                if not line or line.startswith('##'):
                    continue

                # 解析逗號分隔的委託資料
                if ',' in line:
                    parts = line.split(',')
                    if len(parts) >= 15:  # 確保有足夠的欄位
                        try:
                            # 根據API文件解析關鍵欄位 - 修正數量欄位
                            seq_no = parts[8] if len(parts) > 8 else ""      # 委託序號 (13碼)
                            book_no = parts[9] if len(parts) > 9 else ""     # 委託書號 (5碼)
                            product = parts[15] if len(parts) > 15 else ""   # 商品代碼
                            buy_sell = parts[22] if len(parts) > 22 else ""  # 買賣別
                            price = parts[27] if len(parts) > 27 else ""     # 委託價格

                            # 根據API文件，期貨委託數量在欄位20 (索引19)
                            qty = parts[19] if len(parts) > 19 else ""       # 委託數量 (欄位20，索引19)
                            qty_old_26 = parts[26] if len(parts) > 26 else ""  # 錯誤的欄位26 (SubID)
                            qty_old_30 = parts[30] if len(parts) > 30 else ""  # 錯誤的欄位30 (MsgNo)
                            qty_old_31 = parts[31] if len(parts) > 31 else ""  # 錯誤的欄位31 (PreOrder)

                            status = parts[10] if len(parts) > 10 else ""    # 委託狀態
                            order_time = parts[12] if len(parts) > 12 else "" # 委託時間

                            # 調試資訊：顯示正確與錯誤欄位的對比
                            self.add_message(f"【數量修正】序號:{seq_no} 正確欄位20:{qty} 錯誤欄位26:{qty_old_26} 30:{qty_old_30} 31:{qty_old_31}")

                            # 格式化顯示
                            buy_sell_text = "買進" if buy_sell == "B" else "賣出" if buy_sell == "S" else buy_sell
                            status_text = self.get_order_status_text(status)

                            # 添加到表格
                            item_id = self.tree_orders.insert('', 'end', values=(
                                seq_no,           # 序號
                                book_no,          # 書號
                                product,          # 商品
                                buy_sell_text,    # 買賣
                                price,            # 價格
                                qty,              # 數量
                                status_text,      # 狀態
                                order_time        # 時間
                            ))

                            # 存儲完整的委託資料
                            self.pending_orders[item_id] = {
                                'seq_no': seq_no,
                                'book_no': book_no,
                                'product': product,
                                'buy_sell': buy_sell,
                                'price': price,
                                'qty': qty,
                                'status': status,
                                'order_time': order_time,
                                'raw_data': parts
                            }

                            order_count += 1
                            self.add_message(f"【委託】{seq_no} {product} {buy_sell_text} {qty}口 價格:{price} 狀態:{status_text}")

                        except (IndexError, ValueError) as e:
                            self.add_message(f"【警告】解析委託欄位時發生錯誤: {e}")

            self.add_message(f"【完成】共找到 {order_count} 筆盤中委託")

        except Exception as e:
            self.add_message(f"【錯誤】解析盤中委託資料時發生錯誤: {str(e)}")

    def get_order_status_text(self, status_code):
        """取得委託狀態文字"""
        status_map = {
            "0": "委託中",
            "1": "部分成交",
            "2": "全部成交",
            "3": "已取消",
            "4": "已失效",
            "5": "等待中",
            "6": "委託失敗",
            "7": "委託成功"
        }
        return status_map.get(status_code, f"狀態{status_code}")

    def cancel_selected_order(self):
        """刪除選中的委託單"""
        selected_items = self.tree_orders.selection()
        if not selected_items:
            self.add_message("【提示】請先選擇要刪除的委託單")
            return

        if not self.m_pSKOrder:
            self.add_message("【錯誤】SKOrder物件未初始化")
            return

        try:
            item_id = selected_items[0]
            order_data = self.pending_orders.get(item_id)

            if not order_data:
                self.add_message("【錯誤】找不到委託資料")
                return

            seq_no = order_data['seq_no']
            product = order_data['product']

            self.add_message(f"【刪單】準備刪除委託: {seq_no} {product}")

            # 使用CancelOrderBySeqNo API刪除委託
            login_id = "E123354882"
            account = "F0200006363839"
            async_order = False  # 使用同步模式

            try:
                # 調用刪單API
                message, nCode = self.m_pSKOrder.CancelOrderBySeqNo(login_id, async_order, account, seq_no)

                if self.m_pSKCenter:
                    result_msg = self.m_pSKCenter.SKCenterLib_GetReturnCodeMessage(nCode)
                else:
                    result_msg = f"結果代碼: {nCode}"

                self.add_message(f"【刪單結果】{result_msg} (代碼: {nCode})")
                self.add_message(f"【回應訊息】{message}")

                if nCode == 0:
                    self.add_message(f"【成功】委託 {seq_no} 刪除請求已送出")
                    # 重新查詢委託單列表
                    self.after(1000, self.query_pending_orders)  # 1秒後重新查詢
                else:
                    self.add_message(f"【失敗】刪除委託失敗: {result_msg}")

            except Exception as api_error:
                self.add_message(f"【API錯誤】刪單API調用失敗: {str(api_error)}")

        except Exception as e:
            self.add_message(f"【錯誤】刪除委託時發生錯誤: {str(e)}")

    def cancel_and_reorder(self):
        """刪單重下功能 - 替代改價"""
        selected_items = self.tree_orders.selection()
        if not selected_items:
            self.add_message("【提示】請先選擇要刪單重下的委託單")
            return

        new_price = self.entry_new_price.get().strip()
        if not new_price:
            self.add_message("【提示】請輸入新價格")
            return

        if not self.m_pSKOrder:
            self.add_message("【錯誤】SKOrder物件未初始化")
            return

        try:
            item_id = selected_items[0]
            order_data = self.pending_orders.get(item_id)

            if not order_data:
                self.add_message("【錯誤】找不到委託資料")
                return

            seq_no = order_data['seq_no']
            product = order_data['product']
            old_price = order_data['price']
            qty = order_data['qty']
            buy_sell = order_data['buy_sell']

            self.add_message(f"【刪單重下】準備刪除委託並重新下單: {seq_no}")
            self.add_message(f"【原委託】{product} {buy_sell} {qty}口 價格:{old_price}")
            self.add_message(f"【新委託】{product} {buy_sell} {qty}口 價格:{new_price}")

            # 步驟1: 先刪除原委託
            login_id = "E123354882"
            account = "F0200006363839"
            async_order = False  # 使用同步模式

            try:
                # 調用刪單API
                message, nCode = self.m_pSKOrder.CancelOrderBySeqNo(login_id, async_order, account, seq_no)

                if self.m_pSKCenter:
                    result_msg = self.m_pSKCenter.SKCenterLib_GetReturnCodeMessage(nCode)
                else:
                    result_msg = f"結果代碼: {nCode}"

                self.add_message(f"【刪單結果】{result_msg} (代碼: {nCode})")

                if nCode == 0:
                    self.add_message(f"【步驟1完成】委託 {seq_no} 刪除成功")

                    # 步驟2: 自動重新下單
                    self.add_message("【步驟2】自動重新下單...")

                    # 確保數量不為空
                    if not qty or qty == "":
                        qty = "1"  # 預設1口
                        self.add_message("【修正】數量為空，設定為1口")

                    # 設定新的下單參數 - 轉換為正確的商品代碼
                    correct_product = self.convert_to_correct_product_code(product)
                    self.combo_product.set(correct_product)  # 設定商品
                    self.entry_price.delete(0, tk.END)
                    self.entry_price.insert(0, new_price)  # 設定新價格
                    self.entry_quantity.delete(0, tk.END)
                    self.entry_quantity.insert(0, qty)  # 設定數量

                    # 設定買賣別
                    if buy_sell == "B":
                        self.combo_buy_sell.set("買進")
                    else:
                        self.combo_buy_sell.set("賣出")

                    self.add_message(f"【自動設定】原商品:{product} → 正確商品:{correct_product}")
                    self.add_message(f"【自動設定】買賣:{buy_sell} 數量:{qty} 新價格:{new_price}")

                    # 自動送出委託
                    self.add_message("【自動下單】開始自動送出新委託...")

                    # 延遲1秒後自動下單，確保參數設定完成
                    self.after(1000, self.auto_submit_order)

                    # 清空新價格輸入框
                    self.entry_new_price.delete(0, tk.END)

                else:
                    self.add_message(f"【失敗】刪單失敗，無法進行重新下單: {result_msg}")

            except Exception as api_error:
                self.add_message(f"【API錯誤】刪單API調用失敗: {str(api_error)}")

        except Exception as e:
            self.add_message(f"【錯誤】刪單重下時發生錯誤: {str(e)}")

    def auto_submit_order(self):
        """自動送出委託 - 用於刪單重下功能"""
        try:
            self.add_message("【自動下單】執行自動送出委託...")

            # 調用現有的下單功能
            self.test_future_order()

            # 延遲3秒後自動查詢委託狀況
            self.after(3000, self.query_pending_orders)

        except Exception as e:
            self.add_message(f"【錯誤】自動送出委託時發生錯誤: {str(e)}")

    def convert_to_correct_product_code(self, query_product_code):
        """將查詢結果的商品代碼轉換為下單用的正確代碼"""
        try:
            self.add_message(f"【代碼轉換】原始代碼: {query_product_code}")

            # 商品代碼對應表
            product_mapping = {
                'MXFG5': 'MTX00 (小台指期貨(近月))',  # 小台指期貨
                'MXFR1': 'MTX00 (小台指期貨(近月))',  # 小台指期貨R1格式
                'MTX00': 'MTX00 (小台指期貨(近月))',  # 小台指期貨近月
                'TXFG5': 'TX00 (台指期貨(近月))',    # 台指期貨
                'TXFR1': 'TX00 (台指期貨(近月))',    # 台指期貨R1格式
                'TX00': 'TX00 (台指期貨(近月))',     # 台指期貨近月
            }

            # 如果找到對應的代碼，使用對應的代碼
            if query_product_code in product_mapping:
                correct_code = product_mapping[query_product_code]
                self.add_message(f"【代碼轉換】{query_product_code} → {correct_code}")
                return correct_code

            # 如果是小台相關的代碼，預設使用MTX00
            if 'MX' in query_product_code or '小台' in query_product_code:
                correct_code = 'MTX00 (小台指期貨(近月))'
                self.add_message(f"【代碼轉換】小台相關代碼 {query_product_code} → {correct_code}")
                return correct_code

            # 如果是大台相關的代碼，使用TX00
            if 'TX' in query_product_code or '台指' in query_product_code:
                correct_code = 'TX00 (台指期貨(近月))'
                self.add_message(f"【代碼轉換】大台相關代碼 {query_product_code} → {correct_code}")
                return correct_code

            # 如果都不匹配，預設使用MTX00
            self.add_message(f"【代碼轉換】未知代碼，預設使用MTX00: {query_product_code}")
            return 'MTX00 (小台指期貨(近月))'

        except Exception as e:
            self.add_message(f"【錯誤】商品代碼轉換失敗: {str(e)}")
            # 發生錯誤時，預設使用MTX00
            return 'MTX00 (小台指期貨(近月))'

    def clear_trade_report(self):
        """清除成交回報"""
        try:
            self.text_trade_report.delete(1.0, tk.END)
            self.add_message("【成交回報】已清除成交回報區域")
        except Exception as e:
            self.add_message(f"【錯誤】清除成交回報時發生錯誤: {str(e)}")

    def add_trade_report(self, message):
        """添加成交回報訊息"""
        try:
            timestamp = datetime.now().strftime("%H:%M:%S")
            formatted_message = f"[{timestamp}] {message}\n"

            self.text_trade_report.insert(tk.END, formatted_message)
            self.text_trade_report.see(tk.END)  # 自動滾動到最新訊息

            # 同時添加到主LOG
            self.add_message(f"【成交回報】{message}")

        except Exception as e:
            self.add_message(f"【錯誤】添加成交回報時發生錯誤: {str(e)}")

    def on_trade_filled(self, seq_no, price, qty, trade_time, order_no):
        """處理成交回報 - 由回報模組調用"""
        try:
            # 在成交回報區域顯示
            self.add_trade_report("=" * 40)
            self.add_trade_report("🎉 成交確認")
            self.add_trade_report(f"📋 序號: {seq_no}")
            self.add_trade_report(f"💰 成交價: {price}")
            self.add_trade_report(f"📊 數量: {qty}口")
            self.add_trade_report(f"⏰ 時間: {trade_time}")

            # 計算成交金額
            try:
                if price and qty:
                    price_float = float(price)
                    qty_int = int(qty)
                    contract_value = price_float * qty_int * 50  # 小台每點50元
                    self.add_trade_report(f"💵 金額: {contract_value:,.0f}元")
            except:
                pass

            self.add_trade_report("=" * 40)

            # 自動查詢更新委託狀況
            self.after(2000, self.query_pending_orders)

        except Exception as e:
            self.add_message(f"【錯誤】處理成交回報時發生錯誤: {str(e)}")

    def on_order_status_update(self, seq_no, status):
        """接收委託狀態更新通知"""
        try:
            self.add_message(f"【狀態更新】委託序號:{seq_no} 狀態:{status}")

            # 如果是委託成功，延遲查詢委託列表
            if status == "委託成功":
                self.add_message("【提示】委託已進入市場，2秒後自動查詢委託列表...")
                self.after(2000, self.query_pending_orders)  # 2秒後查詢

            # 如果是其他狀態變化，也更新列表
            elif status in ["已取消", "改價成功", "部分成交"]:
                self.add_message("【提示】委託狀態已變化，1秒後自動查詢委託列表...")
                self.after(1000, self.query_pending_orders)  # 1秒後查詢

        except Exception as e:
            self.add_message(f"【錯誤】處理委託狀態更新時發生錯誤: {str(e)}")

    def check_skcom_version(self):
        """檢查SKCOM版本資訊"""
        try:
            self.add_message("【版本檢查】開始檢查SKCOM版本...")

            if self.m_pSKCenter:
                try:
                    # 使用正確的版本檢查函數
                    version_info = self.m_pSKCenter.SKCenterLib_GetSKAPIVersionAndBit()
                    self.add_message(f"【SKCOM版本】{version_info}")
                except Exception as e:
                    self.add_message(f"【版本檢查】無法取得版本資訊: {str(e)}")
                    # 嘗試其他可能的版本函數
                    try:
                        alt_version = self.m_pSKCenter.SKCenterLib_GetVersion()
                        self.add_message(f"【備用版本】{alt_version}")
                    except:
                        self.add_message("【版本檢查】所有版本檢查方法都失敗")

            # 檢查comtypes快取路徑
            try:
                import comtypes.client
                import os
                # 嘗試不同的方式取得快取路徑
                try:
                    cache_dir = comtypes.client._code_cache._get_cache_dir()
                    self.add_message(f"【comtypes快取】{cache_dir}")
                except:
                    # 替代方法：檢查常見的快取位置
                    import tempfile
                    temp_dir = tempfile.gettempdir()
                    possible_cache = os.path.join(temp_dir, "comtypes_cache")
                    self.add_message(f"【可能快取位置】{possible_cache}")

                    # 檢查用戶目錄下的comtypes快取
                    user_cache = os.path.expanduser("~/.comtypes_cache")
                    self.add_message(f"【用戶快取位置】{user_cache}")

            except Exception as e:
                self.add_message(f"【快取檢查】無法取得comtypes快取路徑: {str(e)}")

        except Exception as e:
            self.add_message(f"【錯誤】版本檢查時發生錯誤: {str(e)}")



    def simple_register_quote_events(self):
        """簡化的事件註冊方式 - 避免GIL錯誤"""
        if not self.m_pSKQuote:
            self.add_message("【報價】SKQuote物件未初始化，跳過事件註冊")
            return

        try:
            self.add_message("【報價】使用簡化方式註冊報價事件...")

            # 使用輪詢方式獲取報價資料，避免事件回調的GIL問題
            self.add_message("【提示】使用輪詢方式獲取報價資料，避免GIL錯誤")
            self.add_message("【提示】將定期查詢最新報價並顯示")

            # 初始化輪詢相關變數
            self.polling_active = False
            self.polling_interval = 1000  # 1秒輪詢一次

            return True

        except Exception as e:
            self.add_message(f"【錯誤】簡化事件註冊失敗: {str(e)}")
            return False

    def start_polling_quotes(self):
        """開始輪詢報價資料"""
        try:
            self.polling_active = True
            self.add_message("【輪詢】開始定期查詢MTX00報價資料...")
            self.poll_quote_data()
        except Exception as e:
            self.add_message(f"【錯誤】啟動輪詢時發生錯誤: {str(e)}")

    def stop_polling_quotes(self):
        """停止輪詢報價資料"""
        try:
            self.polling_active = False
            self.add_message("【輪詢】停止定期查詢報價資料")
        except Exception as e:
            self.add_message(f"【錯誤】停止輪詢時發生錯誤: {str(e)}")

    def poll_quote_data(self):
        """輪詢報價資料"""
        if not self.polling_active or not self.quote_monitoring:
            return

        try:
            # 使用SKQuoteLib_GetStockByNoLONG獲取即時報價
            if self.m_pSKQuote:
                product_code = self.current_product.replace(' ', '')

                # 嘗試獲取報價資料 (這個API通常用於獲取即時報價)
                # 注意：這裡可能需要根據實際API調整
                try:
                    # 模擬報價資料 (實際應該調用相應的查詢API)
                    current_time = time.strftime("%H:%M:%S")

                    # 這裡應該調用實際的報價查詢API
                    # 暫時顯示模擬資料，表示輪詢正在工作
                    if hasattr(self, '_poll_count'):
                        self._poll_count += 1
                    else:
                        self._poll_count = 1

                    # 每10次輪詢顯示一次狀態
                    if self._poll_count % 10 == 0:
                        self.add_message(f"【輪詢狀態】第{self._poll_count}次查詢 {product_code} 報價 - {current_time}")
                        self.label_time.config(text=current_time)
                        self.label_status.config(text=f"輪詢中({self._poll_count})", fg="blue")

                except Exception as api_error:
                    self.add_message(f"【輪詢錯誤】查詢報價API錯誤: {str(api_error)}")

            # 排程下一次輪詢
            if self.polling_active:
                self.after(self.polling_interval, self.poll_quote_data)

        except Exception as e:
            self.add_message(f"【錯誤】輪詢報價時發生錯誤: {str(e)}")
            # 即使出錯也要繼續輪詢
            if self.polling_active:
                self.after(self.polling_interval, self.poll_quote_data)

    def set_strategy_callback(self, callback_func):
        """設定策略回調函數 - 階段1整合"""
        try:
            self.strategy_callback = callback_func
            logger.info("✅ 策略回調函數已設定")
        except Exception as e:
            logger.error(f"❌ 設定策略回調函數失敗: {e}")

    def call_strategy_callback(self, price, time_str):
        """調用策略回調函數 - 線程安全版本"""
        try:
            if self.strategy_callback:
                # 使用after_idle確保在主線程中調用
                self.after_idle(self.strategy_callback, price, time_str)
        except Exception as e:
            logger.error(f"❌ 調用策略回調失敗: {e}")
