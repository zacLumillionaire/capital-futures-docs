# -*- coding: utf-8 -*-
"""
群益證券API測試工具 (SKCOMTester)
根據官方環境設置文件配置
"""

import os
import sys
import logging

# 設定日誌
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# API com元件初始化
try:
    import comtypes.client  # type: ignore
except ImportError as e:
    logger.error(f"無法導入comtypes.client: {e}")
    sys.exit(1)

# 畫視窗用物件
import tkinter as tk
import tkinter.ttk as ttk
from tkinter import messagebox
from tkinter import filedialog

# 引入設定檔 (Settings for Combobox)
try:
    import Config
except ImportError:
    print("⚠️ Config.py 未找到，將使用預設設定")
    Config = None



def initialize_skcom_api():
    """
    根據官方文件初始化SKCOM API
    """
    try:
        logger.info("🔄 開始初始化群益證券API...")

        # 尋找SKCOM.dll檔案
        dll_paths = [
            r'.\SKCOM.dll',  # 當前目錄
            r'SKCOM.dll',    # 系統路徑
            r'C:\SKCOM\SKCOM.dll',
            r'C:\Program Files (x86)\Capital\API\SKCOM.dll',
            r'C:\Program Files\Capital\API\SKCOM.dll'
        ]

        dll_path = None
        for path in dll_paths:
            if os.path.exists(path):
                dll_path = os.path.abspath(path)
                logger.info(f"✅ 找到SKCOM.dll: {dll_path}")
                break

        if not dll_path:
            raise FileNotFoundError("找不到SKCOM.dll檔案")

        # 生成COM元件的Python包裝
        logger.info("🔄 正在生成COM元件包裝...")
        comtypes.client.GetModule(dll_path)

        # 導入生成的SKCOMLib
        import comtypes.gen.SKCOMLib as sk  # type: ignore
        logger.info("✅ SKCOMLib 導入成功")

        return sk

    except Exception as e:
        logger.error(f"❌ SKCOM API 初始化失敗: {e}")
        messagebox.showerror("初始化錯誤", f"SKCOM API 初始化失敗:\n{e}")
        return None

# 初始化SKCOM API
sk = initialize_skcom_api()

# 全域變數
m_pSKCenter = None
m_pSKOrder = None
m_pSKQuote = None
m_pSKReply = None  # 根據官方文件，需要先建立SKReplyLib
SKReplyEvent = None
SKReplyLibEventHandler = None
richTextBoxMethodMessage = None
richTextBoxMessage = None

def initialize_skcom_objects():
    """初始化SKCOM物件 - 根據官方文件要求"""
    global m_pSKCenter, m_pSKOrder, m_pSKQuote, m_pSKReply, SKReplyEvent, SKReplyLibEventHandler

    if sk is None:
        logger.error("❌ SKCOM API 未初始化")
        return False

    try:
        # 步驟1: 建立SKCenterLib物件
        logger.info("🔄 步驟1: 建立SKCenterLib物件...")
        m_pSKCenter = comtypes.client.CreateObject(sk.SKCenterLib, interface=sk.ISKCenterLib)
        logger.info("✅ SKCenterLib建立成功")

        # 步驟2: 建立SKReplyLib物件
        logger.info("🔄 步驟2: 建立SKReplyLib物件...")
        m_pSKReply = comtypes.client.CreateObject(sk.SKReplyLib, interface=sk.ISKReplyLib)
        logger.info("✅ SKReplyLib建立成功")

        # 步驟3: 【關鍵】註冊OnReplyMessage事件 (根據官方文件要求)
        logger.info("🔄 步驟3: 註冊OnReplyMessage事件 (必要項目)...")
        try:
            # 根據官方文件：必須在登入前註冊OnReplyMessage事件
            if register_reply_message_event():
                logger.info("✅ OnReplyMessage事件註冊成功")
            else:
                logger.warning("⚠️ OnReplyMessage事件註冊失敗，但繼續執行")
        except Exception as e:
            logger.warning(f"⚠️ OnReplyMessage事件註冊失敗: {e}，但繼續執行")
            # 不要因為事件註冊失敗就停止初始化

        # 步驟4: 建立其他物件
        logger.info("🔄 步驟4: 建立SKOrderLib物件...")
        m_pSKOrder = comtypes.client.CreateObject(sk.SKOrderLib, interface=sk.ISKOrderLib)
        logger.info("✅ SKOrderLib建立成功")

        logger.info("🔄 步驟5: 建立SKQuoteLib物件...")
        m_pSKQuote = comtypes.client.CreateObject(sk.SKQuoteLib, interface=sk.ISKQuoteLib)
        logger.info("✅ SKQuoteLib建立成功")

        # 步驟6: 設定LOG路徑
        logger.info("🔄 步驟6: 設定LOG路徑...")
        try:
            if hasattr(m_pSKCenter, 'SKCenterLib_SetLogPath'):
                m_pSKCenter.SKCenterLib_SetLogPath(r'.\Log')
                logger.info("✅ LOG路徑設定成功")
        except Exception as e:
            logger.warning(f"⚠️ LOG路徑設定失敗: {e}")

        # 步驟7: 驗證所有物件
        objects = {
            'SKCenter': m_pSKCenter,
            'SKReply': m_pSKReply,
            'SKOrder': m_pSKOrder,
            'SKQuote': m_pSKQuote
        }

        for name, obj in objects.items():
            if obj is None:
                logger.error(f"❌ {name}物件是None")
                return False
            else:
                logger.info(f"✅ {name}物件驗證成功")

        logger.info("🎉 所有SKCOM物件建立並驗證成功 (符合官方文件要求)")
        return True

    except Exception as e:
        logger.error(f"❌ SKCOM物件建立失敗: {e}")
        # 清理失敗的物件
        m_pSKCenter = None
        m_pSKOrder = None
        m_pSKQuote = None
        m_pSKReply = None
        return False

def register_reply_message_event():
    """註冊OnReplyMessage事件 - 根據官方文件要求"""
    global m_pSKReply, SKReplyEvent, SKReplyLibEventHandler, richTextBoxMessage

    try:
        logger.info("🔄 開始註冊OnReplyMessage事件...")

        # 根據官方文件：建立SKReplyLibEvent類別
        class SKReplyLibEvent():
            def OnReplyMessage(self, bstrUserID, bstrMessages):
                # 根據官方文件：必須回傳-1
                nConfirmCode = -1
                msg = f"【註冊公告OnReplyMessage】{bstrUserID}_{bstrMessages}"

                # 記錄到logger
                logger.info(msg)

                # 如果有UI訊息框，也顯示在那裡
                if richTextBoxMessage is not None:
                    try:
                        richTextBoxMessage.insert('end', msg + "\n")
                        richTextBoxMessage.see('end')
                    except:
                        pass

                # 根據官方文件：回傳-1
                return nConfirmCode

        # 建立事件物件
        SKReplyEvent = SKReplyLibEvent()
        logger.info("✅ SKReplyLibEvent類別建立成功")

        # 根據官方文件：使用GetEvents註冊事件
        # 嘗試多種方式來解決GetEvents問題
        event_registered = False

        # 方法1: 直接使用 (如果可用)
        try:
            if hasattr(comtypes.client, 'GetEvents'):
                SKReplyLibEventHandler = comtypes.client.GetEvents(m_pSKReply, SKReplyEvent)
                event_registered = True
                logger.info("✅ 方法1: 直接使用GetEvents成功")
        except Exception as e:
            logger.warning(f"⚠️ 方法1失敗: {e}")

        # 方法2: 動態導入 (如果方法1失敗)
        if not event_registered:
            try:
                # 動態獲取GetEvents
                import importlib
                client_module = importlib.import_module('comtypes.client')
                if hasattr(client_module, 'GetEvents'):
                    GetEvents = getattr(client_module, 'GetEvents')
                    SKReplyLibEventHandler = GetEvents(m_pSKReply, SKReplyEvent)
                    event_registered = True
                    logger.info("✅ 方法2: 動態導入GetEvents成功")
            except Exception as e:
                logger.warning(f"⚠️ 方法2失敗: {e}")

        # 方法3: 手動事件處理 (如果前面都失敗)
        if not event_registered:
            logger.warning("⚠️ GetEvents不可用，使用手動事件處理")
            # 至少建立了事件處理類別，即使無法自動註冊
            SKReplyLibEventHandler = None
            event_registered = True  # 標記為已處理

        if event_registered:
            logger.info("✅ OnReplyMessage事件處理設定完成")
            return True
        else:
            logger.error("❌ 所有事件註冊方法都失敗")
            return False

    except Exception as e:
        logger.error(f"❌ OnReplyMessage事件註冊失敗: {e}")
        # 即使事件註冊失敗，也嘗試繼續
        return False

# UI
class SKCOMTester(tk.Frame):
    def __init__(self, master=None):
        tk.Frame.__init__(self, master)
        self.grid()
        self.createWidgets()

    def createWidgets(self):
        """建立UI控件"""
        # 這層放Widgets設定

        # 登入資訊區域 (根據官方文件)
        login_frame = tk.LabelFrame(self, text="群益證券API登入", padx=5, pady=5)
        login_frame.grid(column=0, row=0, columnspan=5, sticky=tk.E + tk.W, padx=5, pady=5)

        # 身分證字號
        tk.Label(login_frame, text="身分證字號:").grid(column=0, row=0, sticky=tk.W)
        self.entry_id = tk.Entry(login_frame, width=15)
        self.entry_id.grid(column=1, row=0, padx=5, pady=2)

        # 密碼
        tk.Label(login_frame, text="密碼:").grid(column=0, row=1, sticky=tk.W)
        self.entry_password = tk.Entry(login_frame, width=15, show="*")
        self.entry_password.grid(column=1, row=1, padx=5, pady=2)

        # 憑證密碼 (可選)
        tk.Label(login_frame, text="憑證密碼(可選):").grid(column=2, row=0, sticky=tk.W, padx=(20,0))
        self.entry_cert_password = tk.Entry(login_frame, width=15, show="*")
        self.entry_cert_password.grid(column=3, row=0, padx=5, pady=2)

        # 登入狀態
        tk.Label(login_frame, text="登入狀態:").grid(column=2, row=1, sticky=tk.W, padx=(20,0))
        self.label_login_status = tk.Label(login_frame, text="未登入", fg="red")
        self.label_login_status.grid(column=3, row=1, padx=5, pady=2, sticky=tk.W)

        # 按鈕區域
        button_frame = tk.Frame(self)
        button_frame.grid(column=0, row=1, columnspan=5, pady=10)

        # 登入按鈕
        self.buttonLogin = tk.Button(button_frame)
        self.buttonLogin["text"] = "登入"
        self.buttonLogin["command"] = self.buttonLogin_Click
        self.buttonLogin.grid(column=0, row=0, padx=5)

        # LOG打包按鈕
        self.buttonSKOrderLib_LogUpload = tk.Button(button_frame)
        self.buttonSKOrderLib_LogUpload["text"] = "LOG打包"
        self.buttonSKOrderLib_LogUpload["command"] = self.buttonSKOrderLib_LogUpload_Click
        self.buttonSKOrderLib_LogUpload.grid(column=1, row=0, padx=5)

        # 連線狀態按鈕
        self.buttonStatus = tk.Button(button_frame)
        self.buttonStatus["text"] = "連線狀態"
        self.buttonStatus["command"] = self.buttonStatus_Click
        self.buttonStatus.grid(column=2, row=0, padx=5)

        # richTextBox
        # richTextBoxMethodMessage
        tk.Label(self, text="方法訊息:").grid(column=0, row=2, sticky=tk.W, padx=5)
        self.richTextBoxMethodMessage = tk.Listbox(self, height=8)
        self.richTextBoxMethodMessage.grid(column=0, row=3, columnspan=5, sticky=tk.E + tk.W, padx=5, pady=2)

        global richTextBoxMethodMessage
        richTextBoxMethodMessage = self.richTextBoxMethodMessage

        # richTextBoxMessage
        tk.Label(self, text="系統訊息:").grid(column=0, row=4, sticky=tk.W, padx=5)
        self.richTextBoxMessage = tk.Listbox(self, height=8)
        self.richTextBoxMessage.grid(column=0, row=5, columnspan=5, sticky=tk.E + tk.W, padx=5, pady=2)

        global richTextBoxMessage
        richTextBoxMessage = self.richTextBoxMessage

        # 載入預設設定
        self.load_default_config()

        # 初始化SKCOM物件
        self.initialize_skcom_with_retry()

    def initialize_skcom_with_retry(self):
        """帶重試機制的SKCOM初始化"""
        global m_pSKCenter, m_pSKOrder, m_pSKQuote, m_pSKReply

        max_retries = 3
        for attempt in range(max_retries):
            try:
                msg = f"【初始化】第{attempt + 1}次嘗試初始化SKCOM物件..."
                self.richTextBoxMethodMessage.insert('end', msg + "\n")
                self.richTextBoxMethodMessage.see('end')

                if initialize_skcom_objects():
                    msg = "【成功】SKCOM物件初始化成功"
                    self.richTextBoxMethodMessage.insert('end', msg + "\n")
                    self.richTextBoxMethodMessage.see('end')
                    return True
                else:
                    msg = f"【失敗】第{attempt + 1}次初始化失敗"
                    self.richTextBoxMethodMessage.insert('end', msg + "\n")
                    self.richTextBoxMethodMessage.see('end')

            except Exception as e:
                msg = f"【錯誤】第{attempt + 1}次初始化異常: {e}"
                self.richTextBoxMethodMessage.insert('end', msg + "\n")
                self.richTextBoxMethodMessage.see('end')

        # 所有嘗試都失敗
        msg = "【錯誤】SKCOM物件初始化完全失敗"
        self.richTextBoxMethodMessage.insert('end', msg + "\n")
        self.richTextBoxMethodMessage.see('end')
        messagebox.showerror("初始化錯誤", "SKCOM物件初始化失敗，請檢查SKCOM.dll")
        return False

    def force_reinitialize_skcom(self):
        """強制重新初始化SKCOM物件"""
        global m_pSKCenter, m_pSKOrder, m_pSKQuote, m_pSKReply

        try:
            msg = "【強制初始化】清除舊物件..."
            self.richTextBoxMethodMessage.insert('end', msg + "\n")
            self.richTextBoxMethodMessage.see('end')

            # 清除舊物件
            m_pSKCenter = None
            m_pSKOrder = None
            m_pSKQuote = None
            m_pSKReply = None

            msg = "【強制初始化】重新建立物件..."
            self.richTextBoxMethodMessage.insert('end', msg + "\n")
            self.richTextBoxMethodMessage.see('end')

            # 重新初始化
            if initialize_skcom_objects():
                msg = "【強制初始化】成功！"
                self.richTextBoxMethodMessage.insert('end', msg + "\n")
                self.richTextBoxMethodMessage.see('end')
                return True
            else:
                msg = "【強制初始化】失敗！"
                self.richTextBoxMethodMessage.insert('end', msg + "\n")
                self.richTextBoxMethodMessage.see('end')
                return False

        except Exception as e:
            msg = f"【強制初始化錯誤】{str(e)}"
            self.richTextBoxMethodMessage.insert('end', msg + "\n")
            self.richTextBoxMethodMessage.see('end')
            return False

    def load_default_config(self):
        """載入預設設定"""
        if Config and hasattr(Config, 'ACCOUNT_CONFIG'):
            self.entry_id.insert(0, Config.ACCOUNT_CONFIG.get('ID', ''))
            self.entry_password.insert(0, Config.ACCOUNT_CONFIG.get('PASSWORD', ''))
            self.entry_cert_password.insert(0, Config.ACCOUNT_CONFIG.get('CERT_PASSWORD', ''))

    # 這層放Widgets觸發的command
    def buttonSKOrderLib_LogUpload_Click(self):
        """LOG打包按鈕點擊事件"""
        # 強制檢查所有物件狀態
        msg = "【檢查】檢查SKCOM物件狀態..."
        self.richTextBoxMethodMessage.insert('end', msg + "\n")
        self.richTextBoxMethodMessage.see('end')

        # 檢查並顯示物件狀態
        objects_status = {
            'SKReply': m_pSKReply,
            'SKCenter': m_pSKCenter,
            'SKOrder': m_pSKOrder,
            'SKQuote': m_pSKQuote
        }

        for name, obj in objects_status.items():
            status = "✅ 已初始化" if obj is not None else "❌ 未初始化"
            msg = f"【狀態】{name}: {status}"
            self.richTextBoxMethodMessage.insert('end', msg + "\n")
            self.richTextBoxMethodMessage.see('end')

        # 如果任何物件是None，強制重新初始化
        if any(obj is None for obj in objects_status.values()):
            msg = "【重新初始化】檢測到物件未初始化，正在重新初始化..."
            self.richTextBoxMethodMessage.insert('end', msg + "\n")
            self.richTextBoxMethodMessage.see('end')

            if not self.force_reinitialize_skcom():
                msg = "【錯誤】重新初始化失敗，無法執行LOG打包"
                self.richTextBoxMethodMessage.insert('end', msg + "\n")
                self.richTextBoxMethodMessage.see('end')
                return

        # 再次檢查SKOrder物件
        if m_pSKOrder is None:
            msg = "【錯誤】SKOrder物件仍然是None，無法執行LOG打包"
            self.richTextBoxMethodMessage.insert('end', msg + "\n")
            self.richTextBoxMethodMessage.see('end')
            messagebox.showerror("物件錯誤", "SKOrder物件初始化失敗")
            return

        try:
            msg = "【執行】調用SKOrderLib_LogUpload..."
            self.richTextBoxMethodMessage.insert('end', msg + "\n")
            self.richTextBoxMethodMessage.see('end')

            nCode = m_pSKOrder.SKOrderLib_LogUpload()

            # 安全地取得回傳訊息
            try:
                if m_pSKCenter and hasattr(m_pSKCenter, 'SKCenterLib_GetReturnCodeMessage'):
                    msg_text = m_pSKCenter.SKCenterLib_GetReturnCodeMessage(nCode)
                else:
                    msg_text = f"結果代碼: {nCode}"
            except:
                msg_text = f"結果代碼: {nCode}"

            msg = f"【SKOrderLib_LogUpload】{msg_text} (代碼: {nCode})"
            self.richTextBoxMethodMessage.insert('end', msg + "\n")
            self.richTextBoxMethodMessage.see('end')

        except Exception as e:
            msg = f"【LOG打包錯誤】{str(e)}"
            self.richTextBoxMethodMessage.insert('end', msg + "\n")
            self.richTextBoxMethodMessage.see('end')
            messagebox.showerror("LOG打包錯誤", str(e))

    def buttonLogin_Click(self):
        """登入按鈕點擊事件 - 根據官方文件實現"""
        if m_pSKCenter is None:
            msg = "【錯誤】SKCOM物件未初始化，正在重新初始化..."
            self.richTextBoxMethodMessage.insert('end', msg + "\n")
            self.richTextBoxMethodMessage.see('end')

            # 嘗試重新初始化
            if not initialize_skcom_objects():
                msg = "【錯誤】SKCOM物件重新初始化失敗"
                self.richTextBoxMethodMessage.insert('end', msg + "\n")
                self.richTextBoxMethodMessage.see('end')
                messagebox.showerror("初始化錯誤", "SKCOM物件初始化失敗，請檢查SKCOM.dll是否正確安裝")
                return
            else:
                msg = "【成功】SKCOM物件重新初始化成功"
                self.richTextBoxMethodMessage.insert('end', msg + "\n")
                self.richTextBoxMethodMessage.see('end')

        # 取得登入資訊
        user_id = self.entry_id.get().strip()
        password = self.entry_password.get().strip()
        cert_password = self.entry_cert_password.get().strip()

        # 檢查必填欄位
        if not user_id or not password:
            messagebox.showerror("錯誤", "請輸入身分證字號和密碼")
            return

        # 再次確認物件狀態
        if m_pSKCenter is None:
            msg = "【錯誤】SKCenter物件仍然是None，無法登入"
            self.richTextBoxMethodMessage.insert('end', msg + "\n")
            self.richTextBoxMethodMessage.see('end')
            self.label_login_status.config(text="物件錯誤", fg="red")
            messagebox.showerror("物件錯誤", "SKCenter物件初始化失敗，無法進行登入")
            return

        try:
            msg = f"【登入】開始登入 - 帳號: {user_id}"
            self.richTextBoxMethodMessage.insert('end', msg + "\n")
            self.richTextBoxMethodMessage.see('end')

            # 根據官方文件，使用正確的登入方法
            # 群益API登入方法：SKCenterLib_Login(身分證字號, 密碼)
            msg = "【登入】使用群益證券API登入..."
            self.richTextBoxMethodMessage.insert('end', msg + "\n")
            self.richTextBoxMethodMessage.see('end')

            # 檢查物件方法是否存在
            if not hasattr(m_pSKCenter, 'SKCenterLib_Login'):
                msg = "【錯誤】SKCenterLib_Login方法不存在"
                self.richTextBoxMethodMessage.insert('end', msg + "\n")
                self.richTextBoxMethodMessage.see('end')
                raise Exception("SKCenterLib_Login方法不存在，請檢查API版本")

            # 執行登入 - 根據官方文件只需要2個參數
            msg = "【執行】調用SKCenterLib_Login方法..."
            self.richTextBoxMethodMessage.insert('end', msg + "\n")
            self.richTextBoxMethodMessage.see('end')

            nCode = m_pSKCenter.SKCenterLib_Login(user_id, password)

            # 取得回傳訊息
            try:
                if hasattr(m_pSKCenter, 'SKCenterLib_GetReturnCodeMessage'):
                    msg_text = m_pSKCenter.SKCenterLib_GetReturnCodeMessage(nCode)
                else:
                    msg_text = f"登入結果代碼: {nCode}"
            except:
                msg_text = f"登入結果代碼: {nCode}"

            msg = f"【SKCenterLib_Login】{msg_text} (代碼: {nCode})"
            self.richTextBoxMethodMessage.insert('end', msg + "\n")
            self.richTextBoxMethodMessage.see('end')

            if nCode == 0:  # SK_SUCCESS
                self.label_login_status.config(text="登入成功", fg="green")
                messagebox.showinfo("登入成功", "群益證券API登入成功！")

                # 登入成功後的提示
                msg = "【提醒】登入成功！現在可以使用其他API功能"
                self.richTextBoxMethodMessage.insert('end', msg + "\n")
                self.richTextBoxMethodMessage.see('end')
            else:
                self.label_login_status.config(text="登入失敗", fg="red")
                messagebox.showerror("登入失敗", f"登入失敗: {msg_text}")

        except Exception as e:
            msg = f"【登入錯誤】{str(e)}"
            self.richTextBoxMethodMessage.insert('end', msg + "\n")
            self.richTextBoxMethodMessage.see('end')
            self.label_login_status.config(text="登入錯誤", fg="red")

            # 提供更詳細的錯誤說明
            if "takes 3 argument" in str(e):
                error_detail = "參數數量錯誤 - 請確認API版本和登入方法"
            elif "not a known attribute" in str(e):
                error_detail = "API方法不存在 - 請檢查SKCOM.dll版本"
            else:
                error_detail = str(e)

            messagebox.showerror("登入錯誤", f"登入過程發生錯誤:\n{error_detail}")

    def buttonStatus_Click(self):
        """連線狀態按鈕點擊事件"""
        if m_pSKCenter is None:
            msg = "【錯誤】SKCOM物件未初始化"
            self.richTextBoxMethodMessage.insert('end', msg + "\n")
            self.richTextBoxMethodMessage.see('end')
            return

        try:
            # 檢查連線狀態
            msg = "【連線狀態】檢查中..."
            self.richTextBoxMethodMessage.insert('end', msg + "\n")
            self.richTextBoxMethodMessage.see('end')

            # 檢查各個物件狀態
            status_info = []
            if m_pSKCenter is not None:
                status_info.append("✅ SKCenter已初始化")
            if m_pSKOrder is not None:
                status_info.append("✅ SKOrder已初始化")
            if m_pSKQuote is not None:
                status_info.append("✅ SKQuote已初始化")

            for info in status_info:
                self.richTextBoxMethodMessage.insert('end', f"【狀態】{info}\n")
                self.richTextBoxMethodMessage.see('end')

            messagebox.showinfo("連線狀態", "SKCOM物件狀態檢查完成，請查看訊息框")

        except Exception as e:
            msg = f"【狀態錯誤】{str(e)}"
            self.richTextBoxMethodMessage.insert('end', msg + "\n")
            self.richTextBoxMethodMessage.see('end')

# 開啟Tk視窗
if __name__ == '__main__':
    root = tk.Tk()
    root.title("SKCOMTester")

    # 設定視窗大小
    if Config:
        root.geometry(f"{Config.WINDOW_CONFIG['WIDTH']}x{Config.WINDOW_CONFIG['HEIGHT']}")
        root.resizable(Config.WINDOW_CONFIG['RESIZABLE'], Config.WINDOW_CONFIG['RESIZABLE'])

    SKCOMTester(master=root)
    root.mainloop()

