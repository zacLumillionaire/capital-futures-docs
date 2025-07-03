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
from tkinter import ttk, messagebox

# 加入order_service路徑
order_service_path = os.path.join(os.path.dirname(__file__), 'order_service')
if order_service_path not in sys.path:
    sys.path.insert(0, order_service_path)

# 導入群益官方模組
import Global
from user_config import get_user_config

class SimpleIntegratedApp:
    """簡化版整合交易應用程式"""
    
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("群益簡化整合交易系統")
        self.root.geometry("1000x700")
        
        # 使用者配置
        self.config = get_user_config()
        
        # 狀態變數
        self.logged_in = False
        
        # 建立介面
        self.create_widgets()
        
        # 註冊OnReplyMessage事件 (解決2017警告)
        self.register_reply_events()

        # 註冊回報事件 (接收下單狀態)
        self.register_order_reply_events()
    
    def create_widgets(self):
        """建立使用者介面"""
        
        # 主框架
        main_frame = ttk.Frame(self.root)
        main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
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
        
        self.btn_subscribe_quote = ttk.Button(btn_frame, text="訂閱MTX00", command=self.subscribe_quote, state="disabled")
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
                    """即時委託狀態回報 - 完全按照群益官方方式"""
                    try:
                        cutData = bstrData.split(',')
                        # 完全按照群益官方的方式處理
                        self.parent.add_log(f"📋 OnNewData: {cutData}")

                        # 解析重要欄位 (基於群益官方註解)
                        if len(cutData) > 24:
                            order_no = cutData[0]      # 委託序號
                            order_type = cutData[2]    # 委託種類
                            order_status = cutData[3]  # 委託狀態
                            product = cutData[8]       # 商品代碼
                            book_no = cutData[10]      # 委託書號
                            price = cutData[11]        # 價格
                            quantity = cutData[20]     # 數量
                            date_time = f"{cutData[23]} {cutData[24]}"  # 日期&時間

                            # 顯示解析後的資訊
                            self.parent.add_log(f"✅ 委託回報: 序號={order_no}, 狀態={order_status}, {product} {price}@{quantity}")

                    except Exception as e:
                        self.parent.add_log(f"❌ OnNewData處理錯誤: {e}")

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
                messagebox.showerror("錯誤", "請輸入身分證字號和密碼")
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
                
                self.label_status.config(text="狀態: 已登入", foreground="green")
                self.btn_login.config(state="disabled")
                self.btn_init_order.config(state="normal")
                self.btn_connect_quote.config(state="normal")
                
                self.add_log("✅ 登入成功 (已處理警告)！")
                
            else:
                self.add_log(f"❌ 登入失敗: {msg}")
                messagebox.showerror("登入失敗", f"登入失敗: {msg}")
                
        except Exception as e:
            self.add_log(f"❌ 登入錯誤: {e}")
            messagebox.showerror("錯誤", f"登入錯誤: {e}")
    
    def init_order(self):
        """初始化下單模組"""
        try:
            if not self.logged_in:
                self.add_log("❌ 請先登入系統")
                return
            
            self.add_log("🔧 初始化下單模組...")
            
            # 步驟1: 初始化SKOrderLib
            nCode = Global.skO.SKOrderLib_Initialize()
            msg = Global.skC.SKCenterLib_GetReturnCodeMessage(nCode)
            self.add_log(f"📋 SKOrderLib初始化: {msg} (代碼: {nCode})")
            
            if nCode == 0 or nCode == 2003:  # 2003 = 已初始化
                # 步驟2: 讀取憑證
                user_id = self.entry_id.get().strip()
                nCode = Global.skO.ReadCertByID(user_id)
                msg = Global.skC.SKCenterLib_GetReturnCodeMessage(nCode)
                self.add_log(f"📋 憑證讀取: {msg} (代碼: {nCode})")
                
                if nCode == 0:
                    self.btn_init_order.config(state="disabled")
                    self.btn_test_order.config(state="normal")  # 啟用下單測試按鈕

                    # 初始化回報連線 (群益官方方式)
                    self.init_reply_connection()

                    self.add_log("✅ 下單模組初始化完成")
                    self.add_log("💡 現在可以測試下單功能")
                else:
                    self.add_log(f"❌ 憑證讀取失敗: {msg}")
                    if nCode == 1001:
                        self.add_log("💡 提示: 可能需要向群益申請期貨API下單權限")
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

            # 使用群益官方的方式 - RequestTicks返回tuple
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
                    """即時報價事件 - 完全按照群益官方方式處理"""
                    try:
                        # 完全按照群益官方的方式格式化訊息
                        strMsg = f"[OnNotifyTicksLONG] {nStockidx} {nPtr} {lDate} {lTimehms} {lTimemillismicros} {nBid} {nAsk} {nClose} {nQty} {nSimulate}"

                        # 完全按照群益官方的方式直接更新UI (不使用after)
                        self.parent.write_message_direct(strMsg)

                        # 同時解析價格資訊
                        price = nClose / 100.0
                        bid = nBid / 100.0
                        ask = nAsk / 100.0

                        # 格式化時間
                        time_str = f"{lTimehms:06d}"
                        formatted_time = f"{time_str[:2]}:{time_str[2:4]}:{time_str[4:6]}"

                        # 顯示解析後的價格資訊
                        price_msg = f"📊 {formatted_time} 成交:{price:.0f} 買:{bid:.0f} 賣:{ask:.0f} 量:{nQty}"
                        self.parent.write_message_direct(price_msg)

                    except Exception as e:
                        # 如果出錯，也按照群益方式直接寫入
                        self.parent.write_message_direct(f"❌ 報價處理錯誤: {e}")

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
                self.add_log("❌ 請填入完整的下單參數")
                return

            self.add_log(f"🧪 準備測試下單...")
            self.add_log(f"📋 帳號: {account}")
            self.add_log(f"📋 商品: {product}")
            self.add_log(f"📋 買賣: {buysell}")
            self.add_log(f"📋 價格: {price}")
            self.add_log(f"📋 數量: {quantity}口")
            self.add_log(f"📋 委託類型: {trade_type}")
            self.add_log(f"📋 當沖: {day_trade}")
            self.add_log(f"📋 新平倉: {new_close}")
            self.add_log(f"📋 盤別: {reserved}")

            # 確認下單
            result = messagebox.askyesno("確認下單",
                f"確定要下單嗎？\n\n"
                f"帳號: {account}\n"
                f"商品: {product}\n"
                f"買賣: {buysell}\n"
                f"價格: {price}\n"
                f"數量: {quantity}口\n"
                f"委託類型: {trade_type}\n"
                f"當沖: {day_trade}\n"
                f"新平倉: {new_close}\n"
                f"盤別: {reserved}\n\n"
                f"⚠️ 這是真實下單，會產生實際交易！")

            if not result:
                self.add_log("❌ 使用者取消下單")
                return

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
            self.add_log(f"🚀 執行{buysell}下單...")

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

                self.add_log(f"📋 下單物件設定完成")

                # 執行下單
                result = Global.skO.SendFutureOrderCLR(user_id, True, oOrder)

                # 處理下單結果
                if isinstance(result, tuple) and len(result) >= 2:
                    message, nCode = result[0], result[1]
                    msg = Global.skC.SKCenterLib_GetReturnCodeMessage(nCode)

                    if nCode == 0:
                        self.add_log(f"✅ 下單成功: {msg}")
                        self.add_log(f"📋 委託序號: {message}")
                    else:
                        self.add_log(f"❌ 下單失敗: {msg} (代碼: {nCode})")
                else:
                    self.add_log(f"📋 下單結果: {result}")

            else:
                self.add_log("❌ 下單物件未初始化")

        except Exception as e:
            self.add_log(f"❌ 下單執行錯誤: {e}")
            import traceback
            self.add_log(f"📋 錯誤詳情: {traceback.format_exc()}")
    
    def add_log(self, message):
        """添加日誌"""
        timestamp = time.strftime("%H:%M:%S")
        self.text_log.insert(tk.END, f"[{timestamp}] {message}\n")
        self.text_log.see(tk.END)
        self.root.update_idletasks()
    
    def run(self):
        """執行應用程式"""
        self.add_log("🚀 群益簡化整合交易系統啟動")
        self.add_log(f"📋 期貨帳號: {self.config['FUTURES_ACCOUNT']}")
        self.add_log(f"📋 預設商品: {self.config['DEFAULT_PRODUCT']}")
        self.add_log("💡 請點擊「登入」開始使用")
        
        self.root.mainloop()

if __name__ == "__main__":
    app = SimpleIntegratedApp()
    app.run()
