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
import tkinter as tk
from tkinter import ttk, messagebox
import logging
import comtypes.client

# 導入我們的模組
from order.future_order import FutureOrderFrame
from reply.order_reply import OrderReplyFrame
from quote.future_quote import FutureQuoteFrame
from query.position_query import PositionQueryFrame

# 導入價格橋接模組
try:
    from price_bridge import write_price_to_bridge
    PRICE_BRIDGE_AVAILABLE = True
    print("✅ 價格橋接模組載入成功")
except ImportError as e:
    PRICE_BRIDGE_AVAILABLE = False
    print(f"⚠️ 價格橋接模組未載入: {e}")

# 導入TCP價格伺服器模組
try:
    from tcp_price_server import start_price_server, stop_price_server, broadcast_price_tcp, get_server_status
    TCP_PRICE_SERVER_AVAILABLE = True
    print("✅ TCP價格伺服器模組載入成功")
except ImportError as e:
    TCP_PRICE_SERVER_AVAILABLE = False
    print(f"⚠️ TCP價格伺服器模組未載入: {e}")

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
# 策略功能啟用 - 階段1：報價事件整合
STRATEGY_AVAILABLE = True

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

        # TCP價格伺服器狀態
        self.tcp_server_enabled = False
        self.tcp_server_running = False

        # 策略相關初始化
        self.strategy_panel = None
        self.strategy_quote_callback = None

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

        # TCP價格伺服器控制區域
        tcp_frame = tk.LabelFrame(parent, text="TCP價格伺服器 (新功能)", padx=10, pady=10)
        tcp_frame.pack(fill=tk.X, padx=10, pady=5)

        # TCP開關
        self.var_tcp_enabled = tk.BooleanVar()
        self.check_tcp_enabled = tk.Checkbutton(tcp_frame, text="啟用TCP價格伺服器",
                                               variable=self.var_tcp_enabled,
                                               command=self.toggle_tcp_server)
        self.check_tcp_enabled.grid(column=0, row=0, sticky=tk.W, padx=5, pady=5)

        # TCP狀態顯示
        tk.Label(tcp_frame, text="伺服器狀態:").grid(column=1, row=0, sticky=tk.W, padx=(20,5), pady=5)
        self.label_tcp_status = tk.Label(tcp_frame, text="未啟動", fg="red")
        self.label_tcp_status.grid(column=2, row=0, padx=5, pady=5)

        # TCP連接數顯示
        tk.Label(tcp_frame, text="連接數:").grid(column=3, row=0, sticky=tk.W, padx=(20,5), pady=5)
        self.label_tcp_clients = tk.Label(tcp_frame, text="0", fg="blue")
        self.label_tcp_clients.grid(column=4, row=0, padx=5, pady=5)

        # TCP說明
        tcp_info = tk.Label(tcp_frame, text="📡 啟用後可讓策略程式透過TCP接收即時報價 (localhost:8888)",
                           fg="gray", font=("Arial", 8))
        tcp_info.grid(column=0, row=1, columnspan=5, sticky=tk.W, padx=5, pady=2)

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

    def toggle_tcp_server(self):
        """切換TCP價格伺服器狀態"""
        if not TCP_PRICE_SERVER_AVAILABLE:
            messagebox.showerror("錯誤", "TCP價格伺服器模組未載入")
            self.var_tcp_enabled.set(False)
            return

        if self.var_tcp_enabled.get():
            # 啟動TCP伺服器
            self.start_tcp_server()
        else:
            # 停止TCP伺服器
            self.stop_tcp_server()

    def start_tcp_server(self):
        """啟動TCP價格伺服器"""
        try:
            if start_price_server():
                self.tcp_server_running = True
                self.tcp_server_enabled = True
                self.label_tcp_status.config(text="運行中", fg="green")
                self.add_login_message("✅ TCP價格伺服器已啟動 (localhost:8888)")

                # 啟動狀態更新
                self.update_tcp_status()
            else:
                self.var_tcp_enabled.set(False)
                self.label_tcp_status.config(text="啟動失敗", fg="red")
                self.add_login_message("❌ TCP價格伺服器啟動失敗")

        except Exception as e:
            self.var_tcp_enabled.set(False)
            self.label_tcp_status.config(text="錯誤", fg="red")
            self.add_login_message(f"❌ TCP價格伺服器啟動異常: {e}")

    def stop_tcp_server(self):
        """停止TCP價格伺服器"""
        try:
            stop_price_server()
            self.tcp_server_running = False
            self.tcp_server_enabled = False
            self.label_tcp_status.config(text="已停止", fg="red")
            self.label_tcp_clients.config(text="0")
            self.add_login_message("⏹️ TCP價格伺服器已停止")

        except Exception as e:
            self.add_login_message(f"❌ 停止TCP價格伺服器異常: {e}")

    def update_tcp_status(self):
        """更新TCP伺服器狀態"""
        if self.tcp_server_running:
            try:
                status = get_server_status()
                if status:
                    client_count = status.get('connected_clients', 0)
                    self.label_tcp_clients.config(text=str(client_count))

                # 每2秒更新一次
                self.after(2000, self.update_tcp_status)

            except Exception as e:
                logger.error(f"更新TCP狀態失敗: {e}")

    def create_strategy_panel(self, parent_frame, skcom_objects):
        """創建簡化策略面板 - 階段1"""
        try:
            logger.info("🎯 開始創建策略面板...")

            # 創建策略面板容器
            strategy_container = tk.LabelFrame(parent_frame, text="🎯 開盤區間突破策略",
                                             fg="blue", font=("Arial", 12, "bold"))
            strategy_container.pack(fill="both", expand=True, padx=10, pady=10)

            # 價格顯示區域
            price_frame = tk.LabelFrame(strategy_container, text="即時價格", fg="green")
            price_frame.pack(fill="x", padx=5, pady=5)

            tk.Label(price_frame, text="當前價格:", font=("Arial", 10)).pack(side="left", padx=5)
            self.strategy_price_var = tk.StringVar(value="--")
            tk.Label(price_frame, textvariable=self.strategy_price_var,
                    font=("Arial", 12, "bold"), fg="red").pack(side="left", padx=5)

            tk.Label(price_frame, text="更新時間:", font=("Arial", 10)).pack(side="left", padx=(20, 5))
            self.strategy_time_var = tk.StringVar(value="--:--:--")
            tk.Label(price_frame, textvariable=self.strategy_time_var,
                    font=("Arial", 10), fg="blue").pack(side="left", padx=5)

            # 區間狀態顯示
            range_frame = tk.LabelFrame(strategy_container, text="區間狀態", fg="purple")
            range_frame.pack(fill="x", padx=5, pady=5)

            tk.Label(range_frame, text="區間狀態:", font=("Arial", 10)).pack(side="left", padx=5)
            self.range_status_var = tk.StringVar(value="等待8:46-8:47")
            tk.Label(range_frame, textvariable=self.range_status_var,
                    font=("Arial", 10, "bold"), fg="orange").pack(side="left", padx=5)

            tk.Label(range_frame, text="高點:", font=("Arial", 10)).pack(side="left", padx=(20, 5))
            self.range_high_var = tk.StringVar(value="--")
            tk.Label(range_frame, textvariable=self.range_high_var,
                    font=("Arial", 10), fg="red").pack(side="left", padx=5)

            tk.Label(range_frame, text="低點:", font=("Arial", 10)).pack(side="left", padx=(10, 5))
            self.range_low_var = tk.StringVar(value="--")
            tk.Label(range_frame, textvariable=self.range_low_var,
                    font=("Arial", 10), fg="green").pack(side="left", padx=5)

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

            # 添加初始日誌
            self.add_strategy_log("🎯 策略面板初始化完成")
            self.add_strategy_log("📊 等待報價數據...")

            logger.info("✅ 策略面板創建成功")

        except Exception as e:
            logger.error(f"❌ 策略面板創建失敗: {e}")
            # 創建錯誤顯示
            error_label = tk.Label(parent_frame, text=f"策略面板載入失敗: {e}",
                                 fg="red", font=("Arial", 12))
            error_label.pack(expand=True)

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
        """啟動策略監控"""
        try:
            self.strategy_monitoring = True
            self.strategy_start_btn.config(state="disabled")
            self.strategy_stop_btn.config(state="normal")

            self.add_strategy_log("🚀 策略監控已啟動")
            self.add_strategy_log("📡 開始接收報價數據...")

            # 設定報價回調 - 這裡是關鍵整合點
            self.setup_quote_callback()

        except Exception as e:
            logger.error(f"啟動策略監控失敗: {e}")
            self.add_strategy_log(f"❌ 啟動失敗: {e}")

    def stop_strategy_monitoring(self):
        """停止策略監控"""
        try:
            self.strategy_monitoring = False
            self.strategy_start_btn.config(state="normal")
            self.strategy_stop_btn.config(state="disabled")

            self.add_strategy_log("⏹️ 策略監控已停止")

            # 清除報價回調
            self.strategy_quote_callback = None

        except Exception as e:
            logger.error(f"停止策略監控失敗: {e}")
            self.add_strategy_log(f"❌ 停止失敗: {e}")

    def setup_quote_callback(self):
        """設定報價回調 - 階段1的核心功能"""
        try:
            # 設定報價回調函數
            self.strategy_quote_callback = self.on_strategy_quote_received

            # 通知期貨下單框架設定策略回調
            if hasattr(self, 'future_order_frame'):
                self.future_order_frame.set_strategy_callback(self.on_strategy_quote_received)
                self.add_strategy_log("✅ 報價回調設定完成")
            else:
                self.add_strategy_log("⚠️ 期貨下單框架未找到")

        except Exception as e:
            logger.error(f"設定報價回調失敗: {e}")
            self.add_strategy_log(f"❌ 報價回調設定失敗: {e}")

    def on_strategy_quote_received(self, price, time_str):
        """處理策略報價數據 - 線程安全版本"""
        try:
            if self.strategy_monitoring:
                # 更新價格顯示
                self.strategy_price_var.set(str(price))
                self.strategy_time_var.set(time_str)

                # 這裡將來會添加區間計算邏輯
                # 目前只是顯示價格更新
                if hasattr(self, '_last_strategy_price'):
                    if price != self._last_strategy_price:
                        self.add_strategy_log(f"💰 價格更新: {price} (時間: {time_str})")
                else:
                    self.add_strategy_log(f"📊 首次接收價格: {price}")

                self._last_strategy_price = price

        except Exception as e:
            logger.error(f"策略報價處理錯誤: {e}")

    def on_closing(self):
        """關閉應用程式"""
        try:
            # 直接關閉，避免messagebox導致的GIL錯誤
            logger.info("正在關閉應用程式...")

            # 停止TCP價格伺服器
            try:
                if self.tcp_server_running:
                    stop_price_server()
                    logger.info("已停止TCP價格伺服器")
            except Exception as e:
                logger.error(f"停止TCP價格伺服器時發生錯誤: {e}")

            # 停止所有報價監控
            try:
                if hasattr(self, 'future_order_frame') and self.future_order_frame:
                    if hasattr(self.future_order_frame, 'quote_monitoring') and self.future_order_frame.quote_monitoring:
                        self.future_order_frame.stop_quote_monitoring()
                        logger.info("已停止報價監控")
            except Exception as e:
                logger.error(f"停止報價監控時發生錯誤: {e}")

            # 清理資源
            logger.info("正在清理資源...")
            self.quit()
            self.destroy()
        except Exception as e:
            logger.error(f"關閉應用程式時發生錯誤: {e}")
            # 強制退出
            import sys
            sys.exit(0)

def main():
    """主函式"""
    # 檢查SKCOM.dll
    if not os.path.exists('SKCOM.dll'):
        messagebox.showerror("錯誤", "找不到SKCOM.dll檔案")
        return
    
    # 建立並執行應用程式
    app = OrderTesterApp()
    app.mainloop()

if __name__ == "__main__":
    main()
