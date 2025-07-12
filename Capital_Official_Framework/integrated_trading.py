#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
群益整合交易程式
結合下單和報價功能，適合策略交易
基於群益官方架構
"""

import os
import sys
import time
import tkinter as tk
from tkinter import ttk, messagebox
import threading

# 加入order_service路徑
order_service_path = os.path.join(os.path.dirname(__file__), 'order_service')
if order_service_path not in sys.path:
    sys.path.insert(0, order_service_path)

# 導入群益官方模組
import Global
from user_config import get_user_config

class IntegratedTradingApp:
    """整合交易應用程式"""
    
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("群益整合交易系統 - 下單+報價+策略")
        self.root.geometry("1200x800")
        
        # 使用者配置
        self.config = get_user_config()
        
        # 交易狀態
        self.logged_in = False
        self.quote_connected = False
        self.order_initialized = False
        
        # 報價資料
        self.current_price = 0
        self.current_bid = 0
        self.current_ask = 0
        
        # 建立介面
        self.create_widgets()
        
        # 註冊報價事件
        self.setup_quote_events()
    
    def create_widgets(self):
        """建立使用者介面"""
        
        # 主框架
        main_frame = ttk.Frame(self.root)
        main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # 上方控制區
        control_frame = ttk.LabelFrame(main_frame, text="系統控制", padding=10)
        control_frame.pack(fill=tk.X, pady=(0, 10))
        
        # 登入區域
        login_frame = ttk.Frame(control_frame)
        login_frame.pack(fill=tk.X)
        
        ttk.Label(login_frame, text="身分證字號:").grid(row=0, column=0, padx=5)
        self.entry_id = ttk.Entry(login_frame, width=15)
        self.entry_id.insert(0, self.config['USER_ID'])
        self.entry_id.grid(row=0, column=1, padx=5)
        
        ttk.Label(login_frame, text="密碼:").grid(row=0, column=2, padx=5)
        self.entry_password = ttk.Entry(login_frame, show="*", width=15)
        self.entry_password.insert(0, self.config['PASSWORD'])
        self.entry_password.grid(row=0, column=3, padx=5)
        
        self.btn_login = ttk.Button(login_frame, text="登入", command=self.login)
        self.btn_login.grid(row=0, column=4, padx=10)
        
        self.btn_init_order = ttk.Button(login_frame, text="初始化下單", command=self.init_order, state="disabled")
        self.btn_init_order.grid(row=0, column=5, padx=5)
        
        self.btn_connect_quote = ttk.Button(login_frame, text="連線報價", command=self.connect_quote, state="disabled")
        self.btn_connect_quote.grid(row=0, column=6, padx=5)
        
        # 狀態顯示
        status_frame = ttk.Frame(control_frame)
        status_frame.pack(fill=tk.X, pady=(10, 0))
        
        self.label_status = ttk.Label(status_frame, text="狀態: 未登入", foreground="red")
        self.label_status.pack(side=tk.LEFT)
        
        # 主要內容區域
        content_frame = ttk.Frame(main_frame)
        content_frame.pack(fill=tk.BOTH, expand=True)
        
        # 左側 - 報價區域
        quote_frame = ttk.LabelFrame(content_frame, text="即時報價", padding=10)
        quote_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(0, 5))
        
        # 商品選擇
        product_frame = ttk.Frame(quote_frame)
        product_frame.pack(fill=tk.X, pady=(0, 10))
        
        ttk.Label(product_frame, text="商品:").pack(side=tk.LEFT)
        self.combo_product = ttk.Combobox(product_frame, values=["MTX00", "TX00", "TM0000"], width=10)
        self.combo_product.set(self.config['DEFAULT_PRODUCT'])
        self.combo_product.pack(side=tk.LEFT, padx=5)
        
        self.btn_subscribe = ttk.Button(product_frame, text="訂閱報價", command=self.subscribe_quote, state="disabled")
        self.btn_subscribe.pack(side=tk.LEFT, padx=5)
        
        # 報價顯示
        quote_display_frame = ttk.Frame(quote_frame)
        quote_display_frame.pack(fill=tk.X, pady=10)
        
        ttk.Label(quote_display_frame, text="成交價:").grid(row=0, column=0, sticky="w")
        self.label_price = ttk.Label(quote_display_frame, text="--", font=("Arial", 14, "bold"))
        self.label_price.grid(row=0, column=1, sticky="w", padx=10)
        
        ttk.Label(quote_display_frame, text="買價:").grid(row=1, column=0, sticky="w")
        self.label_bid = ttk.Label(quote_display_frame, text="--")
        self.label_bid.grid(row=1, column=1, sticky="w", padx=10)
        
        ttk.Label(quote_display_frame, text="賣價:").grid(row=2, column=0, sticky="w")
        self.label_ask = ttk.Label(quote_display_frame, text="--")
        self.label_ask.grid(row=2, column=1, sticky="w", padx=10)
        
        # 報價日誌
        self.text_quote_log = tk.Text(quote_frame, height=15, width=50)
        self.text_quote_log.pack(fill=tk.BOTH, expand=True, pady=(10, 0))
        
        # 右側 - 下單區域
        order_frame = ttk.LabelFrame(content_frame, text="期貨下單", padding=10)
        order_frame.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True, padx=(5, 0))
        
        # 下單參數
        order_params_frame = ttk.Frame(order_frame)
        order_params_frame.pack(fill=tk.X, pady=(0, 10))
        
        ttk.Label(order_params_frame, text="帳號:").grid(row=0, column=0, sticky="w")
        self.label_account = ttk.Label(order_params_frame, text=self.config['FUTURES_ACCOUNT'])
        self.label_account.grid(row=0, column=1, sticky="w", padx=10)
        
        ttk.Label(order_params_frame, text="商品:").grid(row=1, column=0, sticky="w")
        self.label_order_product = ttk.Label(order_params_frame, text=self.config['DEFAULT_PRODUCT'])
        self.label_order_product.grid(row=1, column=1, sticky="w", padx=10)
        
        ttk.Label(order_params_frame, text="價格:").grid(row=2, column=0, sticky="w")
        self.entry_price = ttk.Entry(order_params_frame, width=10)
        self.entry_price.grid(row=2, column=1, sticky="w", padx=10)
        
        ttk.Label(order_params_frame, text="數量:").grid(row=3, column=0, sticky="w")
        self.entry_quantity = ttk.Entry(order_params_frame, width=10)
        self.entry_quantity.insert(0, "1")
        self.entry_quantity.grid(row=3, column=1, sticky="w", padx=10)
        
        # 下單按鈕
        order_buttons_frame = ttk.Frame(order_frame)
        order_buttons_frame.pack(fill=tk.X, pady=10)
        
        self.btn_buy = ttk.Button(order_buttons_frame, text="買進", command=lambda: self.place_order("BUY"), state="disabled")
        self.btn_buy.pack(side=tk.LEFT, padx=5)
        
        self.btn_sell = ttk.Button(order_buttons_frame, text="賣出", command=lambda: self.place_order("SELL"), state="disabled")
        self.btn_sell.pack(side=tk.LEFT, padx=5)
        
        self.btn_market_buy = ttk.Button(order_buttons_frame, text="市價買", command=lambda: self.market_order("BUY"), state="disabled")
        self.btn_market_buy.pack(side=tk.LEFT, padx=5)
        
        self.btn_market_sell = ttk.Button(order_buttons_frame, text="市價賣", command=lambda: self.market_order("SELL"), state="disabled")
        self.btn_market_sell.pack(side=tk.LEFT, padx=5)
        
        # 交易日誌
        self.text_order_log = tk.Text(order_frame, height=15, width=50)
        self.text_order_log.pack(fill=tk.BOTH, expand=True, pady=(10, 0))
    
    def setup_quote_events(self):
        """設定報價事件處理"""
        try:
            # 使用群益官方的事件處理方式
            class QuoteEvents:
                def __init__(self, parent):
                    self.parent = parent
                
                def OnConnection(self, nKind, nCode):
                    """連線事件"""
                    if nKind == 3003:  # SK_SUBJECT_CONNECTION_STOCKS_READY
                        self.parent.root.after(0, self.parent.on_quote_connected)
                
                def OnNotifyTicksLONG(self, sMarketNo, nStockidx, nPtr, lDate, lTimehms, lTimemillismicros, nBid, nAsk, nClose, nQty, nSimulate):
                    """即時報價事件"""
                    try:
                        # 轉換價格 (群益API價格需要除以100)
                        price = nClose / 100.0
                        bid = nBid / 100.0
                        ask = nAsk / 100.0
                        
                        # 使用after確保在主線程更新UI
                        self.parent.root.after(0, self.parent.update_quote, price, bid, ask, nQty, lTimehms)
                    except Exception as e:
                        print(f"報價事件處理錯誤: {e}")
            
            self.quote_events = QuoteEvents(self)
            
        except Exception as e:
            self.add_quote_log(f"❌ 報價事件設定失敗: {e}")
    
    def login(self):
        """登入系統"""
        try:
            user_id = self.entry_id.get()
            password = self.entry_password.get()

            self.add_order_log("🔐 開始登入...")

            # 步驟1: 註冊OnReplyMessage事件 (解決2017警告)
            self.add_order_log("📋 步驟1: 註冊OnReplyMessage事件...")
            self.register_reply_events()

            # 步驟2: 設定LOG路徑
            log_path = os.path.join(os.path.dirname(__file__), "CapitalLog_Integrated")
            nCode = Global.skC.SKCenterLib_SetLogPath(log_path)
            self.add_order_log(f"📁 LOG路徑設定: {log_path}")

            # 步驟3: 執行登入
            nCode = Global.skC.SKCenterLib_Login(user_id, password)
            msg = Global.skC.SKCenterLib_GetReturnCodeMessage(nCode)

            if nCode == 0:
                self.logged_in = True
                Global.SetID(user_id)

                self.label_status.config(text="狀態: 已登入", foreground="green")
                self.btn_login.config(state="disabled")
                self.btn_init_order.config(state="normal")
                self.btn_connect_quote.config(state="normal")

                self.add_order_log(f"✅ 登入成功: {msg}")
            elif nCode == 2017:
                # 這個警告現在應該不會出現了
                self.logged_in = True
                Global.SetID(user_id)

                self.label_status.config(text="狀態: 已登入", foreground="green")
                self.btn_login.config(state="disabled")
                self.btn_init_order.config(state="normal")
                self.btn_connect_quote.config(state="normal")

                self.add_order_log(f"✅ 登入成功 (已處理事件註冊): {msg}")
            else:
                self.add_order_log(f"❌ 登入失敗: {msg}")

        except Exception as e:
            self.add_order_log(f"❌ 登入錯誤: {e}")

    def register_reply_events(self):
        """註冊OnReplyMessage事件 - 解決2017警告"""
        try:
            import comtypes.client

            # 建立事件處理類別
            class SKReplyLibEvent():
                def OnReplyMessage(self, bstrUserID, bstrMessages):
                    # 必須回傳-1
                    return -1

            # 註冊事件
            self.reply_event = SKReplyLibEvent()
            self.reply_handler = comtypes.client.GetEvents(Global.skR, self.reply_event)

            self.add_order_log("✅ OnReplyMessage事件註冊成功")

        except Exception as e:
            self.add_order_log(f"⚠️ OnReplyMessage事件註冊失敗: {e} (可能不影響登入)")
    
    def init_order(self):
        """初始化下單模組"""
        try:
            if not self.logged_in:
                self.add_order_log("❌ 請先登入系統")
                return

            self.add_order_log("🔧 初始化下單模組...")

            # 步驟1: 初始化SKOrderLib
            self.add_order_log("📋 步驟1: 初始化SKOrderLib...")
            nCode = Global.skO.SKOrderLib_Initialize()
            msg = Global.skC.SKCenterLib_GetReturnCodeMessage(nCode)
            self.add_order_log(f"📋 SKOrderLib初始化結果: {msg} (代碼: {nCode})")

            if nCode == 0 or nCode == 2003:  # 2003 = 已初始化
                # 步驟2: 讀取憑證
                self.add_order_log("📋 步驟2: 讀取憑證...")
                user_id = self.entry_id.get()
                nCode = Global.skO.ReadCertByID(user_id)
                msg = Global.skC.SKCenterLib_GetReturnCodeMessage(nCode)
                self.add_order_log(f"📋 憑證讀取結果: {msg} (代碼: {nCode})")

                if nCode == 0:
                    # 步驟3: 查詢帳號 (可選)
                    self.add_order_log("📋 步驟3: 查詢帳號...")
                    nCode = Global.skO.GetUserAccount()
                    msg = Global.skC.SKCenterLib_GetReturnCodeMessage(nCode)
                    self.add_order_log(f"📋 帳號查詢結果: {msg} (代碼: {nCode})")

                    # 無論帳號查詢是否成功，都認為初始化完成
                    self.order_initialized = True
                    self.btn_init_order.config(state="disabled")
                    self.enable_order_buttons()
                    self.add_order_log("✅ 下單模組初始化完成")
                else:
                    self.add_order_log(f"❌ 憑證讀取失敗: {msg}")
                    self.add_order_log("💡 提示: 可能需要向群益申請期貨API下單權限")
            else:
                self.add_order_log(f"❌ 下單初始化失敗: {msg}")
                if nCode == 1001:
                    self.add_order_log("💡 提示: 錯誤1001通常表示需要簽署期貨API下單聲明書")

        except Exception as e:
            self.add_order_log(f"❌ 下單初始化錯誤: {e}")
    
    def connect_quote(self):
        """連線報價服務"""
        try:
            if not self.logged_in:
                self.add_quote_log("❌ 請先登入系統")
                return

            self.add_quote_log("📡 連線報價服務...")

            # 步驟1: 註冊報價事件
            self.add_quote_log("📋 步驟1: 註冊報價事件...")
            self.register_quote_events()

            # 步驟2: 連線報價主機
            self.add_quote_log("📋 步驟2: 連線報價主機...")
            nCode = Global.skQ.SKQuoteLib_EnterMonitorLONG()
            msg = Global.skC.SKCenterLib_GetReturnCodeMessage(nCode)
            self.add_quote_log(f"📋 報價連線結果: {msg} (代碼: {nCode})")

            if nCode == 0:
                self.btn_connect_quote.config(state="disabled")
                self.btn_subscribe.config(state="normal")
                self.add_quote_log("✅ 報價服務連線成功")
            else:
                self.add_quote_log(f"❌ 報價連線失敗: {msg}")

        except Exception as e:
            self.add_quote_log(f"❌ 報價連線錯誤: {e}")

    def register_quote_events(self):
        """註冊報價事件"""
        try:
            import comtypes.client

            # 建立報價事件處理類別
            class SKQuoteLibEvent():
                def __init__(self, parent):
                    self.parent = parent

                def OnConnection(self, nKind, nCode):
                    """連線事件"""
                    if nKind == 3003:  # SK_SUBJECT_CONNECTION_STOCKS_READY
                        self.parent.root.after(0, self.parent.on_quote_connected)

                def OnNotifyTicksLONG(self, sMarketNo, nStockidx, nPtr, lDate, lTimehms, lTimemillismicros, nBid, nAsk, nClose, nQty, nSimulate):
                    """即時報價事件"""
                    try:
                        # 轉換價格 (群益API價格需要除以100)
                        price = nClose / 100.0
                        bid = nBid / 100.0
                        ask = nAsk / 100.0

                        # 使用after確保在主線程更新UI
                        self.parent.root.after(0, self.parent.update_quote, price, bid, ask, nQty, lTimehms)
                    except Exception as e:
                        print(f"報價事件處理錯誤: {e}")

            # 註冊事件
            self.quote_event = SKQuoteLibEvent(self)
            self.quote_handler = comtypes.client.GetEvents(Global.skQ, self.quote_event)

            self.add_quote_log("✅ 報價事件註冊成功")

        except Exception as e:
            self.add_quote_log(f"⚠️ 報價事件註冊失敗: {e} (可能不影響報價)")
    
    def subscribe_quote(self):
        """訂閱商品報價"""
        try:
            product = self.combo_product.get()
            self.add_quote_log(f"📊 訂閱 {product} 報價...")
            
            # 使用群益官方報價訂閱方式
            nCode = Global.skQ.SKQuoteLib_RequestTicks(0, product)
            msg = Global.skC.SKCenterLib_GetReturnCodeMessage(nCode)
            self.add_quote_log(f"📋 訂閱結果: {msg}")
            
            if nCode == 0:
                self.add_quote_log(f"✅ {product} 報價訂閱成功")
                self.label_order_product.config(text=product)
            else:
                self.add_quote_log(f"❌ 報價訂閱失敗: {msg}")
                
        except Exception as e:
            self.add_quote_log(f"❌ 報價訂閱錯誤: {e}")
    
    def on_quote_connected(self):
        """報價連線成功回調"""
        self.quote_connected = True
        self.add_quote_log("✅ 報價伺服器連線就緒")
    
    def update_quote(self, price, bid, ask, qty, time_hms):
        """更新報價顯示"""
        try:
            self.current_price = price
            self.current_bid = bid
            self.current_ask = ask
            
            # 更新顯示
            self.label_price.config(text=f"{price:.0f}")
            self.label_bid.config(text=f"{bid:.0f}")
            self.label_ask.config(text=f"{ask:.0f}")
            
            # 格式化時間
            time_str = f"{time_hms:06d}"
            formatted_time = f"{time_str[:2]}:{time_str[2:4]}:{time_str[4:6]}"
            
            # 記錄到報價日誌
            log_msg = f"{formatted_time} 成交:{price:.0f} 買:{bid:.0f} 賣:{ask:.0f} 量:{qty}"
            self.add_quote_log(log_msg)
            
        except Exception as e:
            self.add_quote_log(f"❌ 報價更新錯誤: {e}")
    
    def place_order(self, direction):
        """下限價單"""
        try:
            price = float(self.entry_price.get())
            quantity = int(self.entry_quantity.get())
            product = self.combo_product.get()
            account = self.config['FUTURES_ACCOUNT']
            
            self.add_order_log(f"📋 準備下單: {direction} {product} {quantity}口 @{price}")
            
            # 使用群益官方下單方式
            import comtypes.gen.SKCOMLib as sk
            oOrder = sk.FUTUREORDER()
            
            oOrder.bstrFullAccount = account
            oOrder.bstrStockNo = product
            oOrder.sBuySell = 0 if direction == "BUY" else 1
            oOrder.sTradeType = 2  # FOK
            oOrder.sDayTrade = 1   # 當沖
            oOrder.bstrPrice = str(int(price))
            oOrder.nQty = quantity
            oOrder.sNewClose = 0   # 新倉
            oOrder.sReserved = 0   # 盤中
            
            user_id = self.entry_id.get()
            result = Global.skO.SendFutureOrderCLR(user_id, True, oOrder)
            
            if isinstance(result, tuple):
                message, nCode = result
                msg = Global.skC.SKCenterLib_GetReturnCodeMessage(nCode)
                
                if nCode == 0:
                    self.add_order_log(f"✅ 下單成功: {msg}")
                else:
                    self.add_order_log(f"❌ 下單失敗: {msg}")
            else:
                self.add_order_log(f"📋 下單結果: {result}")
                
        except Exception as e:
            self.add_order_log(f"❌ 下單錯誤: {e}")
    
    def market_order(self, direction):
        """下市價單"""
        if direction == "BUY" and self.current_ask > 0:
            self.entry_price.delete(0, tk.END)
            self.entry_price.insert(0, str(int(self.current_ask)))
        elif direction == "SELL" and self.current_bid > 0:
            self.entry_price.delete(0, tk.END)
            self.entry_price.insert(0, str(int(self.current_bid)))
        
        self.place_order(direction)
    
    def enable_order_buttons(self):
        """啟用下單按鈕"""
        self.btn_buy.config(state="normal")
        self.btn_sell.config(state="normal")
        self.btn_market_buy.config(state="normal")
        self.btn_market_sell.config(state="normal")
    
    def add_order_log(self, message):
        """添加下單日誌"""
        timestamp = time.strftime("%H:%M:%S")
        self.text_order_log.insert(tk.END, f"[{timestamp}] {message}\n")
        self.text_order_log.see(tk.END)
    
    def add_quote_log(self, message):
        """添加報價日誌"""
        timestamp = time.strftime("%H:%M:%S")
        self.text_quote_log.insert(tk.END, f"[{timestamp}] {message}\n")
        self.text_quote_log.see(tk.END)
    
    def run(self):
        """執行應用程式"""
        self.root.mainloop()

if __name__ == "__main__":
    app = IntegratedTradingApp()
    app.run()
