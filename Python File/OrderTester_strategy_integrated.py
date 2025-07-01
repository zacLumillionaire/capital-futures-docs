#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
群益證券API下單測試程式 - 穩定版本
整合登入、下單、回報功能

[TAG] STABLE_VERSION_2025_06_30_FINAL
[OK] 此版本已確認穩定運作，無GIL錯誤
[OK] 包含：下單、回報、報價、查詢功能
[OK] 基於群益官方案例，確保穩定性
[OK] 提供策略整合API接口
[WARN] 策略功能已移除，使用獨立StrategyTester.py測試

[LIST] 版本特性:
- 穩定的MTX00期貨下單功能
- 即時OnNewData事件回報
- 即時OnNotifyTicksLONG報價
- GetOpenInterestGW部位查詢
- GetOrderReport智慧單查詢
- 零GIL錯誤，可長時間運行
- 為策略系統提供下單API接口
"""

import os
import sys
import time
import tkinter as tk
from tkinter import ttk, messagebox
import logging
import comtypes.client

# 導入我們的模組
from order.future_order import FutureOrderFrame
from reply.order_reply import OrderReplyFrame
from quote.future_quote import FutureQuoteFrame
from query.position_query import PositionQueryFrame

# 導入策略模組 - 三層容錯機制
try:
    # 第一層：嘗試完整版策略面板
    from strategy.strategy_panel import StrategyControlPanel
    STRATEGY_AVAILABLE = True
    STRATEGY_VERSION = "完整版"
    print("[OK] 完整版策略模組載入成功")
except ImportError as e:
    try:
        # 第二層：如果完整版失敗，使用簡化版
        from strategy.strategy_panel_simple import StrategyControlPanel
        STRATEGY_AVAILABLE = True
        STRATEGY_VERSION = "簡化版"
        print("[OK] 簡化版策略模組載入成功")
    except ImportError as e2:
        try:
            # 第三層：如果簡化版也失敗，使用最簡化版
            from strategy.strategy_panel_minimal import StrategyControlPanel
            STRATEGY_AVAILABLE = True
            STRATEGY_VERSION = "最簡化版"
            print("[OK] 最簡化版策略模組載入成功")
        except ImportError as e3:
            STRATEGY_AVAILABLE = False
            STRATEGY_VERSION = "無"
            print(f"[ERROR] 所有策略模組載入失敗: {e3}")

# 導入價格橋接模組
try:
    from price_bridge import write_price_to_bridge
    PRICE_BRIDGE_AVAILABLE = True
    print("[OK] 價格橋接模組載入成功")
except ImportError as e:
    PRICE_BRIDGE_AVAILABLE = False
    print(f"[WARN] 價格橋接模組未載入: {e}")

# 導入TCP價格伺服器模組
try:
    from tcp_price_server import start_price_server, stop_price_server, broadcast_price_tcp, get_server_status
    TCP_PRICE_SERVER_AVAILABLE = True
    print("[OK] TCP價格伺服器模組載入成功")
except ImportError as e:
    TCP_PRICE_SERVER_AVAILABLE = False
    print(f"[WARN] TCP價格伺服器模組未載入: {e}")

# 設定日誌
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# 策略分頁已整合到主程式中
# 舊的策略分頁代碼已移除，現在使用新的策略面板
# STRATEGY_AVAILABLE 由上方的策略模組導入邏輯決定

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
        logger.info("[LOADING] 初始化SKCOM API...")
        
        # 生成COM元件的Python包裝
        comtypes.client.GetModule(r'.\SKCOM.dll')
        
        # 導入生成的SKCOMLib
        import comtypes.gen.SKCOMLib as sk_module
        sk = sk_module
        
        logger.info("[OK] SKCOM API初始化成功")
        return True
        
    except Exception as e:
        logger.error(f"[ERROR] SKCOM API初始化失敗: {e}")
        return False

def initialize_skcom_objects():
    """初始化SKCOM物件"""
    global m_pSKCenter, m_pSKOrder, m_pSKQuote, m_pSKReply, SKReplyEvent, SKReplyLibEventHandler
    
    if sk is None:
        logger.error("[ERROR] SKCOM API 未初始化")
        return False
    
    try:
        # 建立物件
        logger.info("[LOADING] 建立SKCenterLib物件...")
        m_pSKCenter = comtypes.client.CreateObject(sk.SKCenterLib, interface=sk.ISKCenterLib)
        
        logger.info("[LOADING] 建立SKReplyLib物件...")
        m_pSKReply = comtypes.client.CreateObject(sk.SKReplyLib, interface=sk.ISKReplyLib)
        
        logger.info("[LOADING] 建立SKOrderLib物件...")
        m_pSKOrder = comtypes.client.CreateObject(sk.SKOrderLib, interface=sk.ISKOrderLib)
        
        logger.info("[LOADING] 建立SKQuoteLib物件...")
        m_pSKQuote = comtypes.client.CreateObject(sk.SKQuoteLib, interface=sk.ISKQuoteLib)
        
        # 註冊OnReplyMessage事件
        logger.info("[LOADING] 註冊OnReplyMessage事件...")
        register_reply_message_event()
        
        logger.info("[OK] 所有SKCOM物件建立成功")
        return True
        
    except Exception as e:
        logger.error(f"[ERROR] SKCOM物件建立失敗: {e}")
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

        logger.info("[OK] OnReplyMessage事件註冊成功 (線程安全版)")
        return True

    except Exception as e:
        logger.warning(f"[WARN] OnReplyMessage事件註冊失敗: {e}")
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

        # 策略交易頁面
        logger.info("[DEBUG] 準備創建策略交易標籤頁...")
        logger.info(f"[DEBUG] STRATEGY_AVAILABLE = {STRATEGY_AVAILABLE}")
        logger.info(f"[DEBUG] STRATEGY_VERSION = {STRATEGY_VERSION}")

        if STRATEGY_AVAILABLE:
            logger.info("[DEBUG] 策略可用，創建策略標籤頁...")
            strategy_frame = tk.Frame(notebook)
            notebook.add(strategy_frame, text="策略交易")
            logger.info("[DEBUG] 策略標籤頁框架已創建，開始創建策略頁面...")
            self.create_strategy_page(strategy_frame, skcom_objects)
        else:
            logger.warning("[DEBUG] 策略不可用，創建錯誤頁面...")
            # 如果策略模組不可用，顯示錯誤頁面
            error_frame = tk.Frame(notebook)
            notebook.add(error_frame, text="策略交易")
            self.create_strategy_error_page(error_frame)

        # 策略分頁暫時移除，確保基礎功能穩定
        # if STRATEGY_AVAILABLE:
        #     strategy_frame = tk.Frame(notebook)
        #     notebook.add(strategy_frame, text="🎯 策略交易")
        #
        #     # 建立策略分頁框架
        #     self.strategy_tab = StrategyTab(strategy_frame, skcom_objects)
        #     self.strategy_tab.pack(fill=tk.BOTH, expand=True)
        #
        #     logger.info("[OK] 策略交易分頁已載入")
        # else:
        #     logger.warning("[WARN] 策略交易分頁未載入")
    
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
        tcp_info = tk.Label(tcp_frame, text="[TCP] 啟用後可讓策略程式透過TCP接收即時報價 (localhost:8888)",
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
                self.add_login_message("[OK] TCP價格伺服器已啟動 (localhost:8888)")

                # 啟動狀態更新
                self.update_tcp_status()
            else:
                self.var_tcp_enabled.set(False)
                self.label_tcp_status.config(text="啟動失敗", fg="red")
                self.add_login_message("[ERROR] TCP價格伺服器啟動失敗")

        except Exception as e:
            self.var_tcp_enabled.set(False)
            self.label_tcp_status.config(text="錯誤", fg="red")
            self.add_login_message(f"[ERROR] TCP價格伺服器啟動異常: {e}")

    def stop_tcp_server(self):
        """停止TCP價格伺服器"""
        try:
            stop_price_server()
            self.tcp_server_running = False
            self.tcp_server_enabled = False
            self.label_tcp_status.config(text="已停止", fg="red")
            self.label_tcp_clients.config(text="0")
            self.add_login_message("[STOP] TCP價格伺服器已停止")

        except Exception as e:
            self.add_login_message(f"[ERROR] 停止TCP價格伺服器異常: {e}")

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

    def create_strategy_page(self, parent_frame, skcom_objects):
        """創建策略交易頁面"""
        logger.info("[DEBUG] 開始創建策略交易頁面...")

        try:
            logger.info("[DEBUG] 步驟1: 準備創建策略控制面板...")
            logger.info(f"[DEBUG] 使用策略版本: {STRATEGY_VERSION}")
            logger.info(f"[DEBUG] StrategyControlPanel類: {StrategyControlPanel}")

            # 創建策略控制面板
            logger.info("[DEBUG] 步驟2: 實例化StrategyControlPanel...")
            self.strategy_panel = StrategyControlPanel(parent_frame)
            logger.info("[DEBUG] 步驟2完成: StrategyControlPanel實例化成功")

            logger.info("[DEBUG] 步驟3: 設定面板佈局...")
            self.strategy_panel.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
            logger.info("[DEBUG] 步驟3完成: 面板佈局設定成功")

            # 儲存SKCOM物件引用，用於下單
            logger.info("[DEBUG] 步驟4: 儲存SKCOM物件引用...")
            self.strategy_skcom_objects = skcom_objects
            logger.info("[DEBUG] 步驟4完成: SKCOM物件引用已儲存")

            # 設定下單API接口
            logger.info("[DEBUG] 步驟5: 設定下單API接口...")
            self.setup_strategy_order_api()
            logger.info("[DEBUG] 步驟5完成: 下單API接口設定完成")

            # 連接報價數據流
            logger.info("[DEBUG] 步驟6: 連接報價數據流...")
            self.setup_strategy_quote_bridge()
            logger.info("[DEBUG] 步驟6完成: 報價數據流連接完成")

            logger.info(f"[OK] 策略交易頁面創建成功 ({STRATEGY_VERSION})")

            # 在策略面板中顯示版本資訊
            logger.info("[DEBUG] 步驟7: 顯示版本資訊...")
            if hasattr(self.strategy_panel, 'log_message'):
                self.strategy_panel.log_message(f"[INFO] 使用{STRATEGY_VERSION}策略面板")
                logger.info("[DEBUG] 步驟7完成: 版本資訊已顯示")
            else:
                logger.warning("[DEBUG] 步驟7警告: strategy_panel沒有log_message方法")

            logger.info("[SUCCESS] 策略交易頁面創建完全成功！")

        except Exception as e:
            import traceback
            error_details = traceback.format_exc()
            logger.error(f"[ERROR] 策略交易頁面創建失敗: {e}")
            logger.error(f"[ERROR] 詳細錯誤堆疊: {error_details}")
            logger.info("[DEBUG] 轉向創建錯誤頁面...")
            self.create_strategy_error_page(parent_frame)

    def create_strategy_error_page(self, parent_frame):
        """創建策略錯誤頁面"""
        # 主框架
        main_frame = tk.Frame(parent_frame)
        main_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=20)

        # 錯誤標題
        error_label = tk.Label(main_frame,
                              text="策略模組載入失敗",
                              fg="red", font=("Arial", 14, "bold"))
        error_label.pack(pady=(0, 10))

        # 說明文字
        info_label = tk.Label(main_frame,
                             text="請點擊下方診斷按鈕來查看詳細錯誤資訊",
                             font=("Arial", 10))
        info_label.pack(pady=(0, 20))

        # 診斷按鈕
        diagnose_button = tk.Button(main_frame,
                                   text="[SEARCH] 開始診斷策略模組問題",
                                   command=self.diagnose_strategy_problem,
                                   bg="#4CAF50", fg="white",
                                   font=("Arial", 12, "bold"),
                                   padx=20, pady=10)
        diagnose_button.pack(pady=(0, 20))

        # 日誌顯示區域
        log_frame = tk.LabelFrame(main_frame, text="診斷日誌", font=("Arial", 10, "bold"))
        log_frame.pack(fill=tk.BOTH, expand=True)

        # 日誌文本框
        self.error_log_text = tk.Text(log_frame, height=15, wrap=tk.WORD,
                                     font=("Consolas", 9))
        self.error_log_text.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=5, pady=5)

        # 滾動條
        error_scrollbar = tk.Scrollbar(log_frame, orient=tk.VERTICAL,
                                      command=self.error_log_text.yview)
        error_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.error_log_text.config(yscrollcommand=error_scrollbar.set)

        # 初始訊息
        self.add_error_log("策略模組診斷系統已準備就緒")
        self.add_error_log("點擊診斷按鈕開始詳細檢查...")

    def add_error_log(self, message):
        """添加錯誤日誌"""
        try:
            from datetime import datetime
            timestamp = datetime.now().strftime("%H:%M:%S.%f")[:-3]
            log_entry = f"[{timestamp}] {message}\n"

            if hasattr(self, 'error_log_text'):
                self.error_log_text.insert(tk.END, log_entry)
                self.error_log_text.see(tk.END)

            # 同時輸出到VS Code終端
            logger.info(f"策略診斷: {message}")

        except Exception as e:
            logger.error(f"錯誤日誌記錄失敗: {e}")

    def diagnose_strategy_problem(self):
        """診斷策略模組問題"""
        self.add_error_log("=" * 50)
        self.add_error_log("開始策略模組診斷...")
        self.add_error_log("=" * 50)

        try:
            import sys
            import os

            # 1. 檢查基本環境
            self.add_error_log("1. 檢查基本環境:")
            self.add_error_log(f"   Python版本: {sys.version}")
            self.add_error_log(f"   當前目錄: {os.getcwd()}")
            self.add_error_log(f"   Python路徑: {sys.executable}")

            # 2. 檢查strategy資料夾
            self.add_error_log("\n2. 檢查strategy資料夾:")
            strategy_path = "strategy"
            if os.path.exists(strategy_path):
                self.add_error_log(f"   ✓ strategy資料夾存在: {os.path.abspath(strategy_path)}")

                # 列出strategy資料夾內容
                try:
                    files = os.listdir(strategy_path)
                    self.add_error_log(f"   strategy資料夾內容: {files}")
                except Exception as e:
                    self.add_error_log(f"   ✗ 無法讀取strategy資料夾: {e}")
            else:
                self.add_error_log(f"   ✗ strategy資料夾不存在")
                return

            # 3. 測試各個策略模組導入
            self.add_error_log("\n3. 測試策略模組導入:")

            # 測試完整版
            self.add_error_log("   測試完整版策略面板...")
            try:
                from strategy.strategy_panel import StrategyControlPanel as FullPanel
                self.add_error_log("   ✓ 完整版策略面板導入成功")
                full_success = True
            except Exception as e:
                self.add_error_log(f"   ✗ 完整版策略面板導入失敗: {e}")
                self.add_error_log(f"   詳細錯誤: {type(e).__name__}: {str(e)}")
                full_success = False

            # 測試簡化版
            self.add_error_log("   測試簡化版策略面板...")
            try:
                from strategy.strategy_panel_simple import StrategyControlPanel as SimplePanel
                self.add_error_log("   ✓ 簡化版策略面板導入成功")
                simple_success = True
            except Exception as e:
                self.add_error_log(f"   ✗ 簡化版策略面板導入失敗: {e}")
                self.add_error_log(f"   詳細錯誤: {type(e).__name__}: {str(e)}")
                simple_success = False

            # 測試最簡化版
            self.add_error_log("   測試最簡化版策略面板...")
            try:
                from strategy.strategy_panel_minimal import StrategyControlPanel as MinimalPanel
                self.add_error_log("   ✓ 最簡化版策略面板導入成功")
                minimal_success = True
            except Exception as e:
                self.add_error_log(f"   ✗ 最簡化版策略面板導入失敗: {e}")
                self.add_error_log(f"   詳細錯誤: {type(e).__name__}: {str(e)}")
                minimal_success = False

            # 4. 檢查依賴模組
            self.add_error_log("\n4. 檢查依賴模組:")

            dependencies = [
                ("tkinter", "tkinter"),
                ("資料庫管理", "database.sqlite_manager"),
                ("時間工具", "utils.time_utils"),
                ("策略配置", "strategy.strategy_config"),
                ("信號檢測", "strategy.signal_detector"),
            ]

            for name, module in dependencies:
                try:
                    __import__(module)
                    self.add_error_log(f"   ✓ {name} ({module}): 可用")
                except Exception as e:
                    self.add_error_log(f"   ✗ {name} ({module}): 失敗 - {e}")

            # 5. 總結和建議
            self.add_error_log("\n5. 診斷總結:")
            if full_success:
                self.add_error_log("   ✓ 完整版策略面板可用 - 應該能正常工作")
                self.add_error_log("   建議: 重新啟動OrderTester.py")
            elif simple_success:
                self.add_error_log("   ✓ 簡化版策略面板可用 - 基本功能可用")
                self.add_error_log("   建議: 使用簡化版，或修復完整版依賴問題")
            elif minimal_success:
                self.add_error_log("   ✓ 最簡化版策略面板可用 - 最基本功能可用")
                self.add_error_log("   建議: 使用最簡化版，或修復其他版本問題")
            else:
                self.add_error_log("   ✗ 所有策略面板都無法導入")
                self.add_error_log("   建議: 檢查Python環境和模組安裝")

            self.add_error_log("\n診斷完成！請查看上述詳細資訊。")

        except Exception as e:
            self.add_error_log(f"診斷過程發生錯誤: {e}")
            logger.error(f"策略診斷失敗: {e}")

    def setup_strategy_order_api(self):
        """設定策略下單API接口"""
        try:
            # 導入穩定版下單API
            from stable_order_api import get_stable_order_api

            # 取得API實例並設定OrderTester引用
            api = get_stable_order_api()
            api.set_order_tester(self)

            # 為策略面板設定下單回調函數
            # 由於StrategyControlPanel沒有內建的下單回調機制，
            # 我們將在需要時直接調用self.strategy_place_order

            logger.info("[OK] 策略下單API接口設定成功")

        except ImportError as e:
            logger.error(f"[ERROR] 穩定版下單API導入失敗: {e}")
        except Exception as e:
            logger.error(f"[ERROR] 策略下單API接口設定失敗: {e}")

    def strategy_place_order(self, product="MTX00", direction="BUY", price=0.0, quantity=1, order_type="ROD"):
        """策略下單接口"""
        try:
            from stable_order_api import strategy_place_order

            result = strategy_place_order(
                product=product,
                direction=direction,
                price=price,
                quantity=quantity,
                order_type=order_type
            )

            # 記錄下單結果
            if result['success']:
                logger.info(f"[OK] 策略下單成功: {product} {direction} {quantity}口 @{price}")
            else:
                logger.error(f"[ERROR] 策略下單失敗: {result['message']}")

            return result

        except Exception as e:
            error_msg = f"策略下單異常: {str(e)}"
            logger.error(error_msg)
            return {
                'success': False,
                'order_id': None,
                'message': error_msg,
                'timestamp': time.strftime('%H:%M:%S')
            }

    def setup_strategy_quote_bridge(self):
        """設定策略報價數據橋接"""
        try:
            # 由於FutureQuoteFrame沒有set_quote_callback方法，
            # 我們使用其他方式來橋接報價數據
            # 可以通過修改報價事件處理或使用定時器來獲取報價數據

            # 啟動定時器來檢查報價數據
            self.start_quote_bridge_timer()
            logger.info("[OK] 策略報價數據橋接設定成功")
        except Exception as e:
            logger.error(f"[ERROR] 策略報價數據橋接設定失敗: {e}")

    def start_quote_bridge_timer(self):
        """啟動報價橋接定時器"""
        try:
            # 檢查期貨下單框架的報價數據（它有報價監控功能）
            if hasattr(self, 'future_order_frame') and hasattr(self.future_order_frame, 'last_price'):
                if self.future_order_frame.last_price > 0:
                    # 將報價數據傳遞給策略
                    self.on_quote_data_for_strategy(self.future_order_frame.last_price)

            # 繼續定時檢查
            self.after(1000, self.start_quote_bridge_timer)
        except Exception as e:
            logger.error(f"[ERROR] 報價橋接定時器錯誤: {e}")
            # 繼續定時檢查，即使出錯也不停止
            self.after(1000, self.start_quote_bridge_timer)

    def on_quote_data_for_strategy(self, quote_data):
        """處理報價數據並傳遞給策略"""
        try:
            if hasattr(self, 'strategy_panel') and self.strategy_panel:
                # 提取價格數據並傳遞給策略面板
                if isinstance(quote_data, dict) and 'price' in quote_data:
                    price = quote_data['price']
                    timestamp = quote_data.get('timestamp')
                    self.strategy_panel.process_price_update(price, timestamp)
                elif isinstance(quote_data, (int, float)):
                    # 如果直接傳入價格數字
                    self.strategy_panel.process_price_update(quote_data)
        except Exception as e:
            logger.error(f"[ERROR] 策略報價數據處理失敗: {e}")

    def on_closing(self):
        """關閉應用程式"""
        try:
            # 直接關閉，避免messagebox導致的GIL錯誤
            logger.info("正在關閉應用程式...")

            # 停止策略
            try:
                if hasattr(self, 'strategy_panel') and self.strategy_panel:
                    if hasattr(self.strategy_panel, 'stop_strategy'):
                        self.strategy_panel.stop_strategy()
                        logger.info("已停止策略")
            except Exception as e:
                logger.error(f"停止策略時發生錯誤: {e}")

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
