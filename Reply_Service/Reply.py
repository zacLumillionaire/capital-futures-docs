# 先把API com元件初始化
import os
from ctypes import wintypes
# 第一種讓群益API元件可導入讓Python code使用的方法
#import win32com.client
#from ctypes import WinDLL,byref
#from ctypes.wintypes import MSG
#SKCenterLib = win32com.client.Dispatch("{AC30BAB5-194A-4515-A8D3-6260749F8577}")
#SKReplyLib = win32com.client.Dispatch("{72D98963-03E9-42AB-B997-BB2E5CCE78DD}")

# 第二種讓群益API元件可導入Python code內用的物件宣告
import comtypes.client
comtypes.client.GetModule(os.path.split(os.path.realpath(__file__))[0] + r"/SKCOM.dll")
import comtypes.gen.SKCOMLib as sk
skC = comtypes.client.CreateObject(sk.SKCenterLib,interface=sk.ISKCenterLib)
skOOQ = comtypes.client.CreateObject(sk.SKOOQuoteLib,interface=sk.ISKOOQuoteLib)
skO = comtypes.client.CreateObject(sk.SKOrderLib,interface=sk.ISKOrderLib)
skOSQ = comtypes.client.CreateObject(sk.SKOSQuoteLib,interface=sk.ISKOSQuoteLib)
skQ = comtypes.client.CreateObject(sk.SKQuoteLib,interface=sk.ISKQuoteLib)
skR = comtypes.client.CreateObject(sk.SKReplyLib,interface=sk.ISKReplyLib)

# 畫視窗用物件
from tkinter import *
from tkinter.ttk import *
from tkinter import messagebox,colorchooser,font,Button,Frame,Label

# 數學計算用物件
import math

# 🔧 GIL錯誤修復：導入Queue管理器
import sys
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'Python File'))
from queue_manager import (
    put_reply_message, put_order_message, register_message_handler, MainThreadProcessor
)
from message_handlers import (
    reply_handler, order_handler, set_ui_widget
)

# 顯示各功能狀態用的function
def WriteMessage(strMsg,listInformation):
    listInformation.insert('end', strMsg)
    listInformation.see('end')
def SendReturnMessage(strType, nCode, strMessage,listInformation):
    GetMessage(strType, nCode, strMessage,listInformation)
def GetMessage(strType,nCode,strMessage,listInformation):
    strInfo = ""
    if (nCode != 0):
        strInfo ="【"+ skC.SKCenterLib_GetLastLogInfo()+ "】"
    WriteMessage("【" + strType + "】【" + strMessage + "】【" + skC.SKCenterLib_GetReturnCodeMessage(nCode) + "】" + strInfo,listInformation)

#----------------------------------------------------------------------------------------------------------------------------------------------------
#上半部登入框
class FrameLogin(Frame):
    def __init__(self, master = None):
        Frame.__init__(self, master)
        self.grid()
        #self.pack()
        self.place()
        self.FrameLogin = Frame(self)
        self.master["background"] = "#F5F5F5"
        self.FrameLogin.master["background"] = "#F5F5F5"
        self.createWidgets()

    def createWidgets(self):
        #帳號
        self.labelID = Label(self)
        self.labelID["text"] = "帳號："
        self.labelID["background"] = "#F5F5F5"
        self.labelID["font"] = 20
        self.labelID.grid(column=0,row=0)
            #輸入框
        self.textID = Entry(self)
        self.textID["width"] = 50
        self.textID.grid(column = 1, row = 0)

        #密碼
        self.labelPassword = Label(self)
        self.labelPassword["text"] = "密碼："
        self.labelPassword["background"] = "#F5F5F5"
        self.labelPassword["font"] = 20
        self.labelPassword.grid(column = 2, row = 0)
            #輸入框
        self.textPassword = Entry(self)
        self.textPassword["width"] = 50
        self.textPassword['show'] = '*'
        self.textPassword.grid(column = 3, row = 0)

        #按鈕
        self.buttonLogin = Button(self)
        self.buttonLogin["text"] = "登入"
        self.buttonLogin["background"] = "#4169E1"
        self.buttonLogin["foreground"] = "#ffffff"
        self.buttonLogin["font"] = 20
        self.buttonLogin["command"] = self.buttonLogin_Click
        self.buttonLogin.grid(column = 4, row = 0)

        #ID
        self.labelID = Label(self)
        self.labelID["text"] = "<<ID>>"
        self.labelID["background"] = "#F5F5F5"
        self.labelID["font"] = 20
        self.labelID.grid(column = 5, row = 0)

        #訊息欄
        self.listInformation = Listbox(root, height=5)
        self.listInformation.grid(column = 0, row = 1, sticky = E + W)

        global GlobalListInformation,Global_ID
        GlobalListInformation = self.listInformation
        Global_ID = self.labelID

    def buttonLogin_Click(self):
        try:
            m_nCode = skC.SKCenterLib_SetLogPath(os.path.split(os.path.realpath(__file__))[0] + "\\CapitalLog_Reply")
            m_nCode = skC.SKCenterLib_Login(self.textID.get().replace(' ',''),self.textPassword.get().replace(' ',''))
            m_nCode = skC.SKCenterLib_Debug(os.path.split(os.path.realpath(__file__))[0] + "\\CapitalLog_Reply")
            if(m_nCode==0):
                Global_ID["text"] =  self.textID.get().replace(' ','')
                WriteMessage("登入成功",self.listInformation)
            elif m_nCode == 151:
                WriteMessage("密碼錯誤",self.listInformation)
            else:
                WriteMessage(m_nCode,self.listInformation)
        except Exception as e:
            messagebox.showerror("error！",e)

    def GetID(self):
        return self.textID.get().replace(' ','')

#下半部-回報
class FrameReply(Frame):
    def __init__(self, master = None):
        Frame.__init__(self, master)
        self.grid()
        self.FrameReply = Frame(self)
        self.FrameReply.master["background"] = "#F5F5F5"
        self.createWidgets()

    def createWidgets(self):
        #ID
        # self.labelID = Label(self)
        # self.labelID["text"] = "ID："
        # self.labelID.grid(column = 0, row = 0)

        #Connect
        self.btnConnect = Button(self)
        self.btnConnect["text"] = " 連線 "
        self.btnConnect["background"] = "#d0d0d0"
        self.btnConnect["font"] = "20"
        self.btnConnect.grid(column = 0, row = 1)
        self.btnConnect["command"] = self.btnConnect_Click

        #Disconnect
        self.btnDisconnect = Button(self)
        self.btnDisconnect["text"] = " 斷線 "
        self.btnDisconnect["background"] = "#d0d0d0"
        self.btnDisconnect["font"] = "20"
        self.btnDisconnect.grid(column = 1, row = 1)
        self.btnDisconnect["command"] = self.btnDisconnect_Click

        #ConnectStatus
        self.ConnectStatus = Button(self)
        self.ConnectStatus["text"] = "連線狀態"
        self.btnDisconnect["background"] = "#d0d0d0"
        self.ConnectStatus["font"] = "20"
        self.ConnectStatus.grid(column = 2, row = 1)
        self.ConnectStatus["command"] = self.ConnectStatus_Click

        #SolaceClose
        self.SolaceClose = Button(self)
        self.SolaceClose["text"] = "中斷Solace連線"
        self.SolaceClose["background"] = "#d0d0d0"
        self.SolaceClose["font"] = "20"
        self.SolaceClose.grid(column = 3, row = 1)
        self.SolaceClose["command"] = self.SolaceClose_Click

        #訊息欄
        self.listInformation = Listbox(self, height = 25, width = 100)
        self.listInformation.grid(column = 0, row = 2, sticky = E + W, columnspan = 4)

        sb = Scrollbar(self,orient='horizontal',command = self.listInformation.xview)
        sb.grid(row = 3, column = 0,columnspan = 4,sticky = 'ew')
        #self.listInformation.config(xscrollcommand = sb.set)


        global ReplyInformation
        ReplyInformation = self.listInformation

    def btnConnect_Click(self):
        try:
            nErrorCode = skR.SKReplyLib_ConnectByID(frLogin.GetID())
            SendReturnMessage("Reply", nErrorCode, "SKReplyLib_Connect",GlobalListInformation)
        except Exception as e:
            messagebox.showerror("error！",e)

    def btnDisconnect_Click(self):
        try:
            nErrorCode = skR.SKReplyLib_CloseByID(frLogin.GetID())
            SendReturnMessage("Reply", nErrorCode, "SKReplyLib_DisConnect",GlobalListInformation)
        except Exception as e:
            messagebox.showerror("error！",e)

    def ConnectStatus_Click(self):
        try:
            nErrorCode = skR.SKReplyLib_IsConnectedByID(frLogin.GetID())
            if nErrorCode == 1:
                strMsg = "SKReplyLib_ConnectStatus 連線成功"
            elif nErrorCode == 0:
                strMsg = "SKReplyLib_ConnectStatus 斷線中"
            WriteMessage(strMsg,GlobalListInformation)
        except Exception as e:
            messagebox.showerror("error！",e)

    def SolaceClose_Click(self):
        try:
            nErrorCode = skR.SKReplyLib_SolaceCloseByID(frLogin.GetID())
            SendReturnMessage("Reply", nErrorCode, "SKReplyLib_ConnectClose",GlobalListInformation)
        except Exception as e:
            messagebox.showerror("error！",e)

class SKReplyLibEvent:
    """回報事件類 - 🔧 GIL錯誤修復：改為Queue模式"""

    def OnConnect(self, btrUserID, nErrorCode):
        """連線事件 - 🔧 使用Queue避免GIL錯誤"""
        try:
            # 打包連線數據，放入Queue而不直接更新UI
            reply_data = {
                'type': 'connect',
                'user_id': btrUserID,
                'error_code': nErrorCode,
                'message': f"{btrUserID} {'Connected!' if nErrorCode == 0 else 'Connect Error!'}"
            }
            put_reply_message(reply_data)
        except Exception as e:
            # 即使發生錯誤也不能讓COM事件崩潰
            pass

    def OnDisconnect(self,btrUserID, nErrorCode):
        """斷線事件 - 🔧 使用Queue避免GIL錯誤"""
        try:
            # 打包斷線數據，放入Queue而不直接更新UI
            reply_data = {
                'type': 'disconnect',
                'user_id': btrUserID,
                'error_code': nErrorCode,
                'message': "OnDisconnect 您已經斷線囉~~~" if nErrorCode == 3002 else str(nErrorCode)
            }
            put_reply_message(reply_data)
        except Exception as e:
            # 即使發生錯誤也不能讓COM事件崩潰
            pass

    def OnComplete(self,btrUserID):
        """完成事件 - 🔧 使用Queue避免GIL錯誤"""
        try:
            # 打包完成數據，放入Queue而不直接更新UI
            reply_data = {
                'type': 'complete',
                'user_id': btrUserID,
                'message': "OnComplete"
            }
            put_reply_message(reply_data)
        except Exception as e:
            # 即使發生錯誤也不能讓COM事件崩潰
            pass

    def OnData(self,btrUserID,bstrData):
        """數據事件 - 🔧 使用Queue避免GIL錯誤"""
        try:
            # 打包數據，放入Queue而不直接更新UI
            reply_data = {
                'type': 'data',
                'user_id': btrUserID,
                'raw_data': bstrData,
                'message': f"OnData\n{bstrData}"
            }
            put_reply_message(reply_data)
        except Exception as e:
            # 即使發生錯誤也不能讓COM事件崩潰
            pass

    def OnNewData(self,btrUserID,bstrData):
        """新數據事件 - 🔧 使用Queue避免GIL錯誤 (最重要的委託回報)"""
        try:
            # 打包新數據，放入Queue而不直接更新UI
            cutData = bstrData.split(',')
            order_data = {
                'type': 'new_data',
                'user_id': btrUserID,
                'raw_data': bstrData,
                'parsed_data': cutData,
                'message': f"OnNewData\n{cutData}"
            }
            put_order_message(order_data)  # 使用order_message因為這是委託回報
        except Exception as e:
            # 即使發生錯誤也不能讓COM事件崩潰
            pass

    def OnReplyMessage(self,bstrUserID, bstrMessages):
        """回報訊息事件 - 🔧 使用Queue避免GIL錯誤"""
        try:
            sConfirmCode = -1
            # 打包回報訊息，放入Queue而不直接更新UI
            reply_data = {
                'type': 'reply_message',
                'user_id': bstrUserID,
                'message': bstrMessages
            }
            put_reply_message(reply_data)
            return sConfirmCode
        except Exception as e:
            # 即使發生錯誤也不能讓COM事件崩潰
            return -1

    def OnReplyClearMessage(self,bstrUserID):
        """清除訊息事件 - 🔧 使用Queue避免GIL錯誤"""
        try:
            # 打包清除訊息，放入Queue而不直接更新UI
            reply_data = {
                'type': 'clear_message',
                'user_id': bstrUserID,
                'message': "OnReplyClearMessage"
            }
            put_reply_message(reply_data)
        except Exception as e:
            # 即使發生錯誤也不能讓COM事件崩潰
            pass

    def OnSolaceReplyDisconnect(self,btrUserID, nErrorCode):
        """Solace斷線事件 - 🔧 使用Queue避免GIL錯誤"""
        try:
            # 打包Solace斷線數據，放入Queue而不直接更新UI
            reply_data = {
                'type': 'solace_disconnect',
                'user_id': btrUserID,
                'error_code': nErrorCode,
                'message': "OnSolaceReplyDisconnect SK_SUBJECT_CONNECTION_DISCONNECT" if nErrorCode == 3002 else str(nErrorCode)
            }
            put_reply_message(reply_data)
        except Exception as e:
            # 即使發生錯誤也不能讓COM事件崩潰
            pass

    def OnSmartData(self,btrUserID,bstrData):
        """智慧單數據事件 - 🔧 使用Queue避免GIL錯誤"""
        try:
            # 打包智慧單數據，放入Queue而不直接更新UI
            reply_data = {
                'type': 'smart_data',
                'user_id': btrUserID,
                'raw_data': bstrData,
                'message': f"OnSmartData\n{bstrData}"
            }
            put_reply_message(reply_data)
        except Exception as e:
            # 即使發生錯誤也不能讓COM事件崩潰
            pass

    def OnReplyClear(self,bstrMarket):
        """清除回報事件 - 🔧 使用Queue避免GIL錯誤"""
        try:
            # 打包清除回報數據，放入Queue而不直接更新UI
            reply_data = {
                'type': 'reply_clear',
                'market': bstrMarket,
                'message': f"Clear Market: {bstrMarket}"
            }
            put_reply_message(reply_data)
        except Exception as e:
            # 即使發生錯誤也不能讓COM事件崩潰
            pass

SKReplyEvent = SKReplyLibEvent()
SKReplyLibEventHandler = comtypes.client.GetEvents(skR, SKReplyEvent)

if __name__ == '__main__':
    root = Tk()
    root.title("PythonExampleReply - 🔧 GIL錯誤修復版本")
    root["background"] = "#ffdbdb"

    # 🔧 GIL錯誤修復：註冊訊息處理器
    register_message_handler('reply', reply_handler)
    register_message_handler('order', order_handler)

    frLogin = FrameLogin(master = root)

    #TabControl
    root.TabControl = Notebook(root)
    reply_frame = FrameReply(master = root)
    root.TabControl.add(reply_frame, text="Reply")
    root.TabControl.grid(column = 0, row = 2, sticky = E + W)

    # 🔧 GIL錯誤修復：設置UI控件引用
    set_ui_widget('reply_listbox', ReplyInformation)
    set_ui_widget('order_listbox', ReplyInformation)  # 委託回報也使用同一個listbox
    set_ui_widget('global_listbox', GlobalListInformation)

    # 🔧 GIL錯誤修復：啟動主線程Queue處理器
    processor = MainThreadProcessor(root, interval_ms=50)
    processor.start()

    root.mainloop()
