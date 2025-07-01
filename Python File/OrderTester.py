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
# 策略功能啟用 - 使用安全的數據讀取方式
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

            # 客製化區間設定
            range_config_frame = tk.LabelFrame(strategy_container, text="區間設定", fg="purple")
            range_config_frame.pack(fill="x", padx=5, pady=5)

            # 第一行：區間模式選擇
            mode_row = tk.Frame(range_config_frame)
            mode_row.pack(fill="x", padx=5, pady=2)

            tk.Label(mode_row, text="模式:", font=("Arial", 10)).pack(side="left", padx=5)
            self.range_mode_var = tk.StringVar(value="正常模式")
            mode_combo = ttk.Combobox(mode_row, textvariable=self.range_mode_var, width=12, state='readonly')
            mode_combo['values'] = ['正常模式', '測試模式']
            mode_combo.pack(side="left", padx=5)
            mode_combo.bind('<<ComboboxSelected>>', self.on_range_mode_changed)

            # 第二行：時間設定
            time_row = tk.Frame(range_config_frame)
            time_row.pack(fill="x", padx=5, pady=2)

            tk.Label(time_row, text="開始時間:", font=("Arial", 10)).pack(side="left", padx=5)
            self.range_start_time_var = tk.StringVar(value="08:46")
            self.range_time_entry = tk.Entry(time_row, textvariable=self.range_start_time_var, width=8, font=("Arial", 10))
            self.range_time_entry.pack(side="left", padx=5)

            tk.Button(time_row, text="套用", command=self.apply_range_time,
                     bg="lightblue", fg="black", font=("Arial", 9)).pack(side="left", padx=5)

            tk.Button(time_row, text="測試用(3分鐘後)", command=self.set_test_time,
                     bg="orange", fg="white", font=("Arial", 9)).pack(side="left", padx=5)

            # 區間狀態顯示
            range_status_frame = tk.LabelFrame(strategy_container, text="區間狀態", fg="blue")
            range_status_frame.pack(fill="x", padx=5, pady=5)

            # 第一行：當前區間和狀態
            status_row1 = tk.Frame(range_status_frame)
            status_row1.pack(fill="x", padx=5, pady=2)

            tk.Label(status_row1, text="目標區間:", font=("Arial", 10)).pack(side="left", padx=5)
            self.target_range_var = tk.StringVar(value="08:46-08:48")
            tk.Label(status_row1, textvariable=self.target_range_var,
                    font=("Arial", 10, "bold"), fg="purple").pack(side="left", padx=5)

            tk.Label(status_row1, text="狀態:", font=("Arial", 10)).pack(side="left", padx=(20, 5))
            self.range_status_var = tk.StringVar(value="等待區間開始")
            tk.Label(status_row1, textvariable=self.range_status_var,
                    font=("Arial", 10, "bold"), fg="orange").pack(side="left", padx=5)

            # 第二行：高低點數據
            status_row2 = tk.Frame(range_status_frame)
            status_row2.pack(fill="x", padx=5, pady=2)

            tk.Label(status_row2, text="高點:", font=("Arial", 10)).pack(side="left", padx=5)
            self.range_high_var = tk.StringVar(value="--")
            tk.Label(status_row2, textvariable=self.range_high_var,
                    font=("Arial", 10, "bold"), fg="red").pack(side="left", padx=5)

            tk.Label(status_row2, text="低點:", font=("Arial", 10)).pack(side="left", padx=(20, 5))
            self.range_low_var = tk.StringVar(value="--")
            tk.Label(status_row2, textvariable=self.range_low_var,
                    font=("Arial", 10, "bold"), fg="green").pack(side="left", padx=5)

            tk.Label(status_row2, text="區間大小:", font=("Arial", 10)).pack(side="left", padx=(20, 5))
            self.range_size_var = tk.StringVar(value="--")
            tk.Label(status_row2, textvariable=self.range_size_var,
                    font=("Arial", 10, "bold"), fg="blue").pack(side="left", padx=5)

            # 進場信號顯示
            signal_frame = tk.LabelFrame(strategy_container, text="進場信號", fg="red")
            signal_frame.pack(fill="x", padx=5, pady=5)

            # 第一行：信號狀態
            signal_row1 = tk.Frame(signal_frame)
            signal_row1.pack(fill="x", padx=5, pady=2)

            tk.Label(signal_row1, text="信號狀態:", font=("Arial", 10)).pack(side="left", padx=5)
            self.signal_status_var = tk.StringVar(value="等待突破信號")
            tk.Label(signal_row1, textvariable=self.signal_status_var,
                    font=("Arial", 10, "bold"), fg="orange").pack(side="left", padx=5)

            tk.Label(signal_row1, text="方向:", font=("Arial", 10)).pack(side="left", padx=(20, 5))
            self.signal_direction_var = tk.StringVar(value="--")
            tk.Label(signal_row1, textvariable=self.signal_direction_var,
                    font=("Arial", 10, "bold"), fg="purple").pack(side="left", padx=5)

            # 第二行：進場資訊
            signal_row2 = tk.Frame(signal_frame)
            signal_row2.pack(fill="x", padx=5, pady=2)

            tk.Label(signal_row2, text="進場價:", font=("Arial", 10)).pack(side="left", padx=5)
            self.entry_price_var = tk.StringVar(value="--")
            tk.Label(signal_row2, textvariable=self.entry_price_var,
                    font=("Arial", 10, "bold"), fg="red").pack(side="left", padx=5)

            tk.Label(signal_row2, text="進場時間:", font=("Arial", 10)).pack(side="left", padx=(20, 5))
            self.entry_time_var = tk.StringVar(value="--:--:--")
            tk.Label(signal_row2, textvariable=self.entry_time_var,
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
            future_order_logger.addHandler(self.strategy_log_handler)

            # 調試：確認logger設定
            print(f"[DEBUG] Logger名稱: order.future_order")
            print(f"[DEBUG] Logger級別: {future_order_logger.level}")
            print(f"[DEBUG] Handler數量: {len(future_order_logger.handlers)}")
            print(f"[DEBUG] 策略Handler已添加: {self.strategy_log_handler in future_order_logger.handlers}")

        except Exception as e:
            logger.error(f"設定策略LOG處理器失敗: {e}")

    def process_tick_log(self, log_message):
        """處理Tick報價LOG - 包含區間計算邏輯"""
        try:
            self.add_strategy_log(f"🔍 收到LOG: {log_message}")

            # 解析LOG訊息：【Tick】價格:2228200 買:2228100 賣:2228200 量:1 時間:22:59:21
            import re
            pattern = r"【Tick】價格:(\d+) 買:(\d+) 賣:(\d+) 量:(\d+) 時間:(\d{2}:\d{2}:\d{2})"
            match = re.match(pattern, log_message)

            if match:
                raw_price = int(match.group(1))
                price = raw_price / 100.0  # 轉換為正確價格
                time_str = match.group(5)

                self.add_strategy_log(f"📊 解析成功: 原始價格={raw_price}, 轉換價格={price}, 時間={time_str}")

                # 更新基本顯示
                self.add_strategy_log(f"🔄 開始更新顯示...")
                self.update_strategy_display_simple(price, time_str)

                # 區間計算邏輯
                self.add_strategy_log(f"📈 開始區間計算...")
                self.process_range_calculation(price, time_str)

            else:
                self.add_strategy_log(f"❌ LOG格式不匹配: {log_message}")

        except Exception as e:
            self.add_strategy_log(f"❌ process_tick_log錯誤: {e}")
            # 靜默處理錯誤，不影響主程式
            pass

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
            if self.range_calculated and not self.daily_entry_completed:
                self.process_entry_logic(price, time_str, hour, minute, second)

        except Exception as e:
            pass

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

            # 標記當天進場已完成
            self.daily_entry_completed = True

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
        """建立部位 - 簡化版多口建倉"""
        try:
            self.position = direction
            self.entry_price = price
            self.entry_time = time_str

            # 簡化版：預設3口建倉
            trade_size = 3
            self.lots = []

            for i in range(trade_size):
                lot_info = {
                    'id': i + 1,
                    'status': 'active',
                    'pnl': 0,
                    'entry_price': price,
                    'order_id': f"SIM{time_str.replace(':', '')}{i+1:02d}"
                }
                self.lots.append(lot_info)

                # 模擬下單記錄
                print(f"[策略] 📋 模擬下單: 第{i+1}口 {direction} @{float(price):.1f} (ID: {lot_info['order_id']})")

            # 更新UI顯示
            self.position_status_var.set(f"{direction} {trade_size}口")
            self.active_lots_var.set(str(trade_size))
            self.entry_price_var.set(f"{float(price):.1f}")
            self.entry_time_var.set(time_str)

            # 記錄到資料庫（簡化版）
            self.record_entry_to_database(direction, price, time_str, trade_size)

        except Exception as e:
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
        """最簡單的策略顯示更新 - 只更新變數，不觸發事件"""
        try:
            self.add_strategy_log(f"🔄 update_strategy_display_simple 被調用: price={price}, time={time_str}")
            self.add_strategy_log(f"📊 strategy_monitoring狀態: {getattr(self, 'strategy_monitoring', 'undefined')}")

            if self.strategy_monitoring:
                self.add_strategy_log(f"✅ 策略監控中，開始更新UI...")

                # 檢查UI變數是否存在
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
            self.add_strategy_log(f"❌ update_strategy_display_simple錯誤: {e}")
            pass

    def stop_strategy_log_handler(self):
        """停止LOG監聽"""
        try:
            if hasattr(self, 'strategy_log_handler'):
                future_order_logger = logging.getLogger('order.future_order')
                future_order_logger.removeHandler(self.strategy_log_handler)
                print("[策略] ⏹️ LOG監聽已停止")
        except Exception as e:
            pass

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
