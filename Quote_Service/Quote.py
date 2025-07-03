# 先把API com元件初始化
import os
import tkinter as tk

# 第一種讓群益API元件可導入讓Python code使用的方法
#import win32com.client 
#from ctypes import WinDLL,byref
#from ctypes.wintypes import MSG
#SKCenterLib = win32com.client.Dispatch("{AC30BAB5-194A-4515-A8D3-6260749F8577}")
#SKQuoteLib = win32com.client.Dispatch("{E7BCB8BB-E1F0-4F6F-A944-2679195E5807}")

# 第二種讓群益API元件可導入Python code內用的物件宣告
import comtypes.client
comtypes.client.GetModule(os.path.split(os.path.realpath(__file__))[0] + r'\SKCOM.dll') #加此行需將API放與py同目錄
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
from tkinter import ttk

# 數學計算用物件
import math

# 其它物件
import Config

# 🔧 GIL錯誤修復：導入Queue管理器
import sys
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'Python File'))
from queue_manager import (
    put_quote_message, put_tick_message, put_connection_message,
    put_reply_message, register_message_handler, MainThreadProcessor
)
from message_handlers import (
    quote_handler, tick_handler, connection_handler, reply_handler,
    set_ui_widget
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
    # 這裡是登入按鈕,使用群益API不管要幹嘛你都要先登入才行
    def buttonLogin_Click(self):
        try:
            m_nCode = skC.SKCenterLib_SetLogPath(os.path.split(os.path.realpath(__file__))[0] + "\\CapitalLog_Quote")
            m_nCode = skC.SKCenterLib_Login(self.textID.get().replace(' ',''),self.textPassword.get().replace(' ',''))
            if(m_nCode==0):
                Global_ID["text"] =  self.textID.get().replace(' ','')
                WriteMessage("登入成功",self.listInformation)
            else:
                WriteMessage(m_nCode,self.listInformation)
        except Exception as e:
            messagebox.showerror("error！",e)

# 報價連線的按鈕
class FrameQuote(Frame):
    def __init__(self, master = None):
        Frame.__init__(self, master)
        self.grid()
        self.FrameQuote = Frame(self)
        self.FrameQuote.master["background"] = "#F5F5F5"
        self.createWidgets()
        
    def createWidgets(self):
        #ID
        # self.labelID = Label(self)
        # self.labelID["text"] = "ID："
        # self.labelID.grid(column = 0, row = 0)

        #Connect
        self.btnConnect = Button(self)
        self.btnConnect["text"] = "報價連線"
        self.btnConnect["background"] = "#d0d0d0"
        self.btnConnect["font"] = 20
        self.btnConnect["command"] = self.btnConnect_Click
        self.btnConnect.grid(column = 0, row = 1)

        #Disconnect
        self.btnDisconnect = Button(self)
        self.btnDisconnect["text"] = "報價斷線"
        self.btnDisconnect["background"] = "#d0d0d0"
        self.btnDisconnect["font"] = 20
        self.btnDisconnect["command"] = self.btnDisconnect_Click
        self.btnDisconnect.grid(column = 1, row = 1)

        #ServerTime
        self.btnTime = Button(self)
        self.btnTime["text"] = "主機時間"
        self.btnTime["background"] = "#d0d0d0"
        self.btnTime["font"] = 20
        self.btnTime["command"] = self.btnTime_Click
        self.btnTime.grid(column = 2, row = 1,sticky=E)

        self.timeshower = Label(self)
        self.timeshower["text"] = "00:00:00"
        self.timeshower["background"] = "#F5F5F5"
        self.timeshower["font"] = 20
        self.timeshower.grid(column = 3, row = 1,sticky= W)

        global Gobal_ServerTime_Information
        Gobal_ServerTime_Information = self.timeshower

        #TabControl
        self.TabControl = Notebook(self)
        self.TabControl.add(Quote(master = self),text="行情_報價")
        self.TabControl.add(TickandBest5(master = self),text="Tick&Best5")
        self.TabControl.add(KLine(master = self),text="KLine")
        self.TabControl.add(MarketInfo(master = self),text="MarketInfo")
        self.TabControl.add(MACDandBOOL(master = self),text="MACD, Boolen, FutureTradeInfo")
        self.TabControl.add(StrikePrices(master = self),text="OptionStrikePrices")
        self.TabControl.add(StockList(master = self),text="StockList")
        self.TabControl.grid(column = 0, row = 2, sticky = E + W, columnspan = 4)

    def btnConnect_Click(self):
        try:
           m_nCode = skQ.SKQuoteLib_EnterMonitorLONG()
           SendReturnMessage("Quote", m_nCode, "SKQuoteLib_EnterMonitorLONG",GlobalListInformation)
        except Exception as e:
            messagebox.showerror("error！",e)
    
    def btnDisconnect_Click(self):
        try:
            m_nCode = skQ.SKQuoteLib_LeaveMonitor()
            if (m_nCode != 0):
                strMsg = "SKQuoteLib_LeaveMonitor failed!", skC.SKCenterLib_GetReturnCodeMessage(m_nCode)
                WriteMessage(strMsg,GlobalListInformation)
            else:
                SendReturnMessage("Quote", m_nCode, "SKQuoteLib_LeaveMonitor",GlobalListInformation)
        except Exception as e:
            messagebox.showerror("error！",e)

    def btnTime_Click(self):
        try:
           m_nCode = skQ.SKQuoteLib_RequestServerTime()
           SendReturnMessage("Quote", m_nCode, "SKQuoteLib_RequestServerTime",GlobalListInformation)
        except Exception as e:
            messagebox.showerror("error！",e)
    
                 
#下半部-報價-Quote項目
class Quote(Frame):
    def __init__(self, master = None):
        Frame.__init__(self, master)
        self.grid()
        self.Quote = Frame(self)
        self.Quote.master["background"] = "#F5F5F5"
        self.createWidgets()
        
    def createWidgets(self):
        #PageNo
        self.LabelPageNo = Label(self)
        self.LabelPageNo["text"] = "PageNo"
        self.LabelPageNo["background"] = "#F5F5F5"
        self.LabelPageNo["font"] = 20
        self.LabelPageNo.grid(column=0,row=0)
        #輸入框
        self.strPageNo = StringVar()
        self.txtPageNo = Entry(self, textvariable = self.strPageNo)
        self.strPageNo.set("0")
        self.txtPageNo.grid(column=1,row=0)

        #商品代碼
        self.LabelStocks = Label(self)
        self.LabelStocks["text"] = "商品代碼"
        self.LabelStocks["background"] = "#F5F5F5"
        self.LabelStocks["font"] = 20
        self.LabelStocks.grid(column=2,row=0)
        #輸入框
        self.strStocks = StringVar()
        self.txtStocks = Entry(self, textvariable = self.strStocks)
        self.strStocks.set("TX00")
        self.txtStocks.grid(column=3,row=0)
        
        #提示
        self.LabelP = Label(self)
        self.LabelP["text"] = "( 多筆以逗號{,}區隔 )"
        self.LabelP["background"] = "#F5F5F5"
        self.LabelP["font"] = 20
        self.LabelP.grid(column=2,row=1, columnspan=2)

        #按鈕
        self.btnQueryStocks = Button(self)
        self.btnQueryStocks["text"] = "查詢"
        self.btnQueryStocks["background"] = "#d0d0d0"
        self.btnQueryStocks["foreground"] = "#000000"
        self.btnQueryStocks["font"] = 20
        self.btnQueryStocks["command"] = self.btnQueryStocks_Click
        self.btnQueryStocks.grid(column = 4, row = 0)

        #訊息欄
        self.listInformation = Listbox(self, height = 25, width = 100)
        self.listInformation.grid(column = 0, row = 2, sticky = E + W, columnspan = 6)

        global Gobal_Quote_ListInformation
        Gobal_Quote_ListInformation = self.listInformation

    def btnQueryStocks_Click(self):
        try:
            if(self.txtPageNo.get().replace(' ','') == ''):
                pn = 0
            else:
                pn = int(self.txtPageNo.get())
            m_nCode = skQ.SKQuoteLib_RequestStocks(pn,self.txtStocks.get().replace(' ',''))
        except Exception as e:
            messagebox.showerror("error！",e)

#下半部-報價-TickandBest5項目
class TickandBest5(Frame):
    def __init__(self, master = None):
        Frame.__init__(self, master)
        self.grid()
        self.Quote = Frame(self)
        self.Quote.master["background"] = "#F5F5F5"
        self.createWidgets()
        
    def createWidgets(self):
        #PageNo
        self.LabelPageNo = Label(self)
        self.LabelPageNo["text"] = "PageNo"
        self.LabelPageNo["background"] = "#F5F5F5"
        self.LabelPageNo["font"] = 20
        self.LabelPageNo.grid(column=0,row=0)
        #輸入框
        self.strPageNo = StringVar()
        self.txtPageNo = Entry(self, textvariable = self.strPageNo)
        self.strPageNo.set("0")
        self.txtPageNo.grid(column=1,row=0)

        #商品代碼
        self.LabelStocks = Label(self)
        self.LabelStocks["text"] = "商品代碼"
        self.LabelStocks["background"] = "#F5F5F5"
        self.LabelStocks["font"] = 20
        self.LabelStocks.grid(column=2,row=0)
        #輸入框
        self.strStocks = StringVar()
        self.txtStocks = Entry(self, textvariable = self.strStocks)
        self.strStocks.set("TX00")
        self.txtStocks.grid(column=3,row=0)
        
        #按鈕
        self.btnQueryStocks = Button(self)
        self.btnQueryStocks.config
        self.btnQueryStocks.config(text="查詢完整",fg="black",font="20",command=self.btnTick_Click)
        self.btnQueryStocks["background"] = "#d0d0d0"
        self.btnQueryStocks.grid(column = 4, row = 0)

        #LiveTick查詢按鈕
        self.btnQueryStocks = Button(self)
        self.btnQueryStocks.config(text="查詢即時",fg="black",font="20",command=self.btnLiveTick_Click)
        self.btnQueryStocks["background"] = "#d0d0d0"
        #self.btnQueryStocks.grid(column = 5, row = 0)


        #StopTick and StopLive按鈕
        self.btnQueryStocks = Button(self)
        self.btnQueryStocks.config(text="stop",fg="black",font="20",command=self.btnStop_Click)
        self.btnQueryStocks["background"] = "#d0d0d0"
        self.btnQueryStocks.grid(column = 6, row = 0)

        self.btnQueryStocks = Button(self)
        self.btnQueryStocks.config(text="stopLive",fg="black",font="20",command=self.btnLiveStop_Click)
        self.btnQueryStocks["background"] = "#d0d0d0"
        #self.btnQueryStocks.grid(column = 7, row = 0)

        #訊息欄
        self.listInformation = Listbox(self, height = 25, width = 100)
        self.listInformation.grid(column = 0, row = 1, sticky = E + W, columnspan = 6,rowspan =7)

        #最佳五檔表格
        columns = ("張數", "買價")
        self.treeview = ttk.Treeview(self, height=5, show="headings", columns=columns)  
        self.treeview.column("張數", width=60, anchor='center')
        self.treeview.column("買價", width=60, anchor='center')
        self.treeview.heading("張數", text="張數")
        self.treeview.heading("買價", text="買價")
        self.treeview.grid(column = 6, row = 1, sticky=N)

        self.Quantity = ["0","0","0","0","0"]
        self.Price = ["0","0","0","0","0"]
        for i in range(min(len(self.Quantity),len(self.Price))):
            self.treeview.insert('', i, values=(self.Quantity[i], self.Price[i]))

        columns2 = ("張數", "賣價")
        self.treeview2 = ttk.Treeview(self, height=5, show="headings", columns=columns2)  
        self.treeview2.column("張數", width=60, anchor='center')
        self.treeview2.column("賣價", width=60, anchor='center')
        self.treeview2.heading("張數", text="張數")
        self.treeview2.heading("賣價", text="賣價")
        self.treeview2.grid(column = 7, row = 1, sticky=N)

        self.Quantity2 = ["0","0","0","0","0"]
        self.Price2 = ["0","0","0","0","0"]
        for i in range(min(len(self.Quantity2),len(self.Price2))):
            self.treeview2.insert('', i, values=(self.Quantity2[i], self.Price2[i]))
        
         #GetTick按鈕
        self.btnQueryStocks = Button(self)
        self.btnQueryStocks.config(text="GetTick",fg="black",font="20",command=self.btnGetTick_Click)
        self.btnQueryStocks["background"] = "#d0d0d0"
        self.btnQueryStocks.grid(column = 7, row = 2,rowspan= 3,sticky=N)

        self.gettickInfo = Label(self)
        self.gettickInfo["text"] = "市場別"
        self.gettickInfo["font"] = 22
        self.gettickInfo.grid(column=6,row=1,rowspan= 3,sticky = S)

        self.gettickInfo = Label(self)
        self.gettickInfo["text"] = "系統之股票代碼"
        self.gettickInfo["font"] = 22
        self.gettickInfo.grid(column=7,row=1,rowspan= 3,sticky = S)

        self.gettickInfo = Label(self)
        self.gettickInfo["text"] = "第N筆資料"
        self.gettickInfo["font"] = 22
        self.gettickInfo.grid(column=8,row=1,rowspan= 3,sticky = S)


        self.tickMarketNo = Combobox(self,state='readonly')
        self.tickMarketNo['values'] = Config.MARKETNO
        self.tickMarketNo.grid(column=6,row=4,rowspan= 3,sticky=N)

        self.strStocks3= StringVar(self)
        self.txtStocks3 = Entry(self, textvariable = self.strStocks3)
        self.txtStocks3.grid(column=7,row=4,rowspan= 3,sticky=N)

        self.strStocks4 = StringVar(self)
        self.txtStocks4 = Entry(self, textvariable = self.strStocks4)
        self.txtStocks4.grid(column=8,row=4,rowspan= 3,sticky=N)

        self.gettickInfo = Label(self)
        self.gettickInfo["text"] = "Tick Info"
        self.gettickInfo["background"] = "#C4C4C4"
        self.gettickInfo["font"] = 22
        self.gettickInfo.grid(column=6,row=5,sticky = N+W)

        self.gettickclass = Label(self)
        self.gettickclass["text"] = "揭示類型: "
        self.gettickclass["background"] = "#F5F5F5"
        self.gettickclass["font"] = 16
        self.gettickclass.grid(column=7,row=5,sticky = N+W)

        self.gettickshower = Label(self)
        self.gettickshower["text"] = "日期:YYYYMMDD 買價:__ 賣價:__ 成交量:__ 成交價:__ "
        self.gettickshower["background"] = "#F5F5F5"
        self.gettickshower["font"] = 16
        self.gettickshower.grid(column=6,row=6,sticky = N+W,columnspan =4)

        self.getticktime = Label(self)
        self.getticktime["text"] = "時間: 時 分 秒 毫秒 微秒"
        self.getticktime["background"] = "#F5F5F5"
        self.getticktime["font"] = 16
        self.getticktime.grid(column=6,row=7,sticky = N+W,columnspan =4)


        global Gobal_tickclass,Gobal_tickInfo,Gobal_ticktime
        Gobal_tickclass = self.gettickclass
        Gobal_tickInfo = self.gettickshower
        Gobal_ticktime = self.getticktime

        global Gobal_Tick_ListInformation, Gobal_Best5TreeViewQ_Information,Gobal_Best5TreeViewP_Information,Gobal_Best5TreeViewQ_Information2,Gobal_Best5TreeViewP_Information2,Gobal_Best5TXTInfo
        global Gobal_Best5TreeView, Gobal_Best5TreeView2
        Gobal_Tick_ListInformation = self.listInformation
        Gobal_Best5TreeViewQ_Information = self.Quantity
        Gobal_Best5TreeViewP_Information = self.Price
        Gobal_Best5TreeViewQ_Information2 = self.Quantity2
        Gobal_Best5TreeViewP_Information2 = self.Price2
        Gobal_Best5TreeView = self.treeview
        Gobal_Best5TreeView2 = self.treeview2
        
    def btnTick_Click(self):
        try:
            pn = 0
            if(self.txtPageNo.get().replace(' ','') != ''):
                pn = int(self.txtPageNo.get())
            m_nCode = skQ.SKQuoteLib_RequestTicks(pn,self.txtStocks.get().replace(' ',''))
            if (m_nCode ==0):
                SendReturnMessage("Tick&Best5", m_nCode[1], "SKQuoteLib_RequestTicks", GlobalListInformation)
        except Exception as e:
            messagebox.showerror("error！",e)

    def btnLiveTick_Click(self):
        try:
            if(self.txtPageNo.get().replace(' ','') != ''):
                pn = int(self.txtPageNo.get())
            m_nCode = skQ.SKQuoteLib_RequestLiveTick(pn,self.txtStocks.get().replace(' ',''))
        except Exception as e:
            messagebox.showerror("error！",e)

    def btnStop_Click(self):    
        try:
            pn = 0
            if(self.txtPageNo.get().replace(' ','') != ''):
                pn = 50
            m_nCode = skQ.SKQuoteLib_RequestTicks(pn,self.txtStocks.get().replace(' ',''))
        except Exception as e:
            messagebox.showerror("error！",e)

    def btnLiveStop_Click(self):
        try:
            pn=2
            if(self.txtPageNo.get().replace(' ','') != ''):
                pn = 50
            m_nCode = skQ.SKQuoteLib_RequestLiveTick(pn,self.txtStocks.get().replace(' ',''))
        except Exception as e:
            messagebox.showerror("error！",e)
   
    def btnGetTick_Click(self):
        try:
            if(self.tickMarketNo.get() == "0 = 上市"):
                sMarketNo=0
            elif(self.tickMarketNo.get() == "1 = 上櫃"):
                sMarketNo=1
            elif(self.tickMarketNo.get() == "2 = 期貨"):
                sMarketNo=2
            elif(self.tickMarketNo.get() == "3 = 選擇權"):
                sMarketNo=3
            else:
                sMarketNo=4

            pStock = sk.SKTICK()
            m_nCode = skQ.SKQuoteLib_GetTickLONG(sMarketNo,int( self.txtStocks3.get()),int(self.txtStocks4.get()) ,pStock)
            SendReturnMessage("Quote", m_nCode[1], "SKQuoteLib_GetTickLONG",GlobalListInformation)

            #處理時間顯示
            time=int(pStock.nTimehms)
            hour=time//10000
            b=time-hour*10000
            min=b//100
            sec = b-min*100
            millisec = pStock.nTimemillismicros//1000
            microsec = pStock.nTimemillismicros-millisec*1000

            #判斷揭示類型
            if pStock.nSimulate ==0:
                tick_class= "一般揭示"
            elif pStock.nSimulate == 1:
                tick_class = "試算揭示"
            else:
                tick_class = "Error"

            #輸出
            Gobal_tickclass["text"] = "揭示類型: %s" % tick_class
            Gobal_tickInfo["text"] = "日期:%d 買價:%d 賣價:%d 成交量:%d 成交價:%d" % (pStock.nDate, pStock.nBid, pStock.nAsk, pStock.nQty, pStock.nClose)
            Gobal_ticktime["text"] = "時間: %02d點 %02d分 %02d秒 %03d毫秒 %03d微秒" %(hour, min, sec, millisec, microsec)

        except Exception as e:
                messagebox.showerror("error！",e)

    def btnBest5_Click(self):
        try:
            if(self.boxMarketNo.get() == "0 = 上市"):
                sMarketNo=0x00
            elif(self.boxMarketNo.get() == "1 = 上櫃"):
                sMarketNo=0x01
            elif(self.boxMarketNo.get() == "2 = 期貨"):
                sMarketNo=0x02
            elif(self.boxMarketNo.get() == "3 = 選擇權"):
                sMarketNo=0x03
            else:
                sMarketNo=0x04
            pStock = sk.SKBEST5()
            m_nCode = skQ.SKQuoteLib_GetBest5LONG(sMarketNo,int(self.txtBest5.get()), pStock)
            SendReturnMessage("Quote", m_nCode[1], "SKQuoteLib_GetBest5LONG",GlobalListInformation)

        except Exception as e:
            messagebox.showerror("error！",e)

#下半部-報價-KLine項目
class KLine(Frame):
    
    def __init__(self, master = None):
        Frame.__init__(self, master)
        self.grid()
        self.KLine = Frame(self)
        self.KLine.master["background"] = "#F5F5F5"
        self.createWidgets()
        
    def createWidgets(self):
        #商品代碼
        self.LabelKLine = Label(self)
        self.LabelKLine["text"] = "商品代碼"
        self.LabelKLine["background"] = "#F5F5F5"
        self.LabelKLine["font"] = 20
        self.LabelKLine.grid(column=0,row=0)
        #輸入框
        self.txtKLine = Entry(self)
        self.txtKLine.grid(column=1,row=0)

        #提示
        # self.LabelP = Label(self)
        # self.LabelP["text"] = "( 多筆以逗號{,}區隔 )"
        # self.LabelP.grid(column=0,row=1, columnspan=2)

        #K線種類
        self.boxKLine = Combobox(self,state='readonly')
        self.boxKLine['values'] = Config.KLINETYPESET
        self.boxKLine.grid(column=2,row=0)

        #K線輸出格式
        self.boxOutType = Combobox(self,state='readonly')
        self.boxOutType['values'] = Config.KLINEOUTTYPESET
        self.boxOutType.grid(column=3,row=0)

        #K線盤別
        self.boxTradeSessin = Combobox(self,state='readonly')
        self.boxTradeSessin['values'] = Config.TRADESESSIONSET
        self.boxTradeSessin.grid(column=4,row=0)

        #按鈕
        self.btnKLine = Button(self)
        self.btnKLine["text"] = "查詢"
        self.btnKLine["background"] = "#d0d0d0"
        self.btnKLine["foreground"] = "#000000"
        self.btnKLine["font"] = 20
        self.btnKLine["command"] = self.btnKLine_Click
        self.btnKLine.grid(column = 5, row = 0)


        #訊息欄
        self.listInformation = Listbox(self, height = 25, width = 100)
        self.listInformation.grid(column = 0, row = 2, sticky = E + W, columnspan = 6)

        #雖然上面有設定global了,但是這邊還是要再宣告一次,不然不會過
        global Gobal_KLine_ListInformation
        Gobal_KLine_ListInformation = self.listInformation
    
    def btnKLine_Click(self):
        try:
            if(self.boxKLine.get() == "0 = 1分鐘線"):
                sKLineType=0
            elif(self.boxKLine.get() == "4 = 完整日線"):
                sKLineType=4
            elif(self.boxKLine.get() == "5 = 週線"):
                sKLineType=5
            else:
                sKLineType=6

            if(self.boxOutType.get() == "0 = 舊版輸出格式"):
                sOutType=0
            else:
                sOutType=1

            if(self.boxTradeSessin.get() == "0 = 全盤K線(國內期選用)"):
                sTradeSession=0
            else:
                sTradeSession=1
            m_nCode = skQ.SKQuoteLib_RequestKLineAM(self.txtKLine.get().replace(' ','') , sKLineType , sOutType, sTradeSession)
            SendReturnMessage("Quote", m_nCode, "SKQuoteLib_RequestKLineAM",GlobalListInformation)
        except Exception as e:
            messagebox.showerror("error！",e)

#下半部-報價-MarketInfo項目
class MarketInfo(Frame):
    def __init__(self, master = None):
        Frame.__init__(self, master)
        self.grid()
        self.MarketInfo = Frame(self)
        self.MarketInfo.master["background"] = "#F5F5F5"
        self.createWidgets()
        
    def createWidgets(self):
       
        #按鈕
        self.btnMarketInfo = Button(self)
        self.btnMarketInfo["text"] = "查詢"
        self.btnMarketInfo["background"] = "#d0d0d0"
        self.btnMarketInfo["foreground"] = "#000000"
        self.btnMarketInfo["font"] = 20
        self.btnMarketInfo["command"] = self.btnMarketInfo_Click
        self.btnMarketInfo.grid(column = 4, row = 0)
        
        #上市上櫃標籤
        self.Label1 = Label(self)
        self.Label1["text"] = "上市"
        self.Label1["background"] = "#F5F5F5"
        self.Label1["font"] = 20
        self.Label1.grid(column=2,row=1, sticky = E+W)

        self.Label2 = Label(self)
        self.Label2["text"] = "上櫃"
        self.Label2["background"] = "#F5F5F5"
        self.Label2["font"] = 20
        self.Label2.grid(column=9,row=1, sticky = E+W)

        self.Label3 = Label(self)
        self.Label3["text"] = "大盤張筆"
        self.Label3["background"] = "#F5F5F5"
        self.Label3["font"] = 20
        self.Label3.grid(column=0,row=4, sticky = E+W)

        

        self.Label4 = Label(self)
        self.Label4["text"] = "成交金額"
        self.Label4["background"] = "#F5F5F5"
        self.Label4["font"] = 20
        self.Label4.grid(column=1,row=5, sticky = E+W)

        self.Label4 = Label(self)
        self.Label4["text"] = "成交張數"
        self.Label4["background"] = "#F5F5F5"
        self.Label4["font"] = 20
        self.Label4.grid(column=2,row=5, sticky = E+W)

        self.Label4 = Label(self)
        self.Label4["text"] = "成交筆數"
        self.Label4["background"] = "#F5F5F5"
        self.Label4["font"] = 20
        self.Label4.grid(column=3,row=5, sticky = E+W)

        self.Label5 = Label(self)
        self.Label5["text"] = "成交金額"
        self.Label5["background"] = "#F5F5F5"
        self.Label5["font"] = 20
        self.Label5.grid(column=8,row=5, sticky = E+W)

        self.Label5 = Label(self)
        self.Label5["text"] = "成交張數"
        self.Label5["background"] = "#F5F5F5"
        self.Label5["font"] = 20
        self.Label5.grid(column=9,row=5, sticky = E+W)

        self.Label5 = Label(self)
        self.Label5["text"] = "成交筆數"
        self.Label5["background"] = "#F5F5F5"
        self.Label5["font"] = 20
        self.Label5.grid(column=10,row=5, sticky = E+W)


        #上市
        self.listInformation = Listbox(self, height = 10, width = 80)
        self.listInformation.grid(column = 0, row = 2, sticky = E+W, columnspan = 6)

        #上櫃
        self.listInformation2 = Listbox(self, height = 10, width = 80)
        self.listInformation2.grid(column =7, row = 2, sticky = E+W, columnspan = 6)

        
        self.Label3 = Label(self)
        self.Label3["text"] = "上市"
        self.Label3["background"] = "#F5F5F5"
        self.Label3["font"] = 20
        self.Label3.grid(column=0,row=7)
        #成交金額(上市)
        self.listInformation3 = Listbox(self, height = 1, width = 12)
        self.listInformation3.grid(column = 1, row = 7)
        
        #成交張數(上市)
        self.listInformation4 = Listbox(self, height = 1, width = 12)
        self.listInformation4.grid(column = 2, row = 7)

        #成交筆數(上市)
        self.listInformation5 = Listbox(self, height = 1, width = 12)
        self.listInformation5.grid(column = 3, row = 7)

        self.Label3 = Label(self)
        self.Label3["text"] = "上櫃"
        self.Label3["background"] = "#F5F5F5"
        self.Label3["font"] = 20
        self.Label3.grid(column=7,row=7)

        #成交金額(上櫃)
        self.listInformation6 = Listbox(self, height = 1, width = 12)
        self.listInformation6.grid(column = 8, row = 7)
        
        #成交張數(上櫃)
        self.listInformation7 = Listbox(self, height = 1, width = 12)
        self.listInformation7.grid(column = 9, row = 7)

        #成交筆數(上櫃)
        self.listInformation8 = Listbox(self, height = 1, width = 12)
        self.listInformation8.grid(column = 10, row = 7)

        #上市
        self.listInformationA = Listbox(self, height = 8, width = 80)
        self.listInformationA.grid(column = 0, row = 9, sticky = E+W, columnspan = 6)
        
        
        #上櫃
        self.listInformationB = Listbox(self, height = 8, width = 80)
        self.listInformationB.grid(column =7, row = 9, sticky = E+W, columnspan = 6)


        global Gobal_MarketInfo_ListInformation,Gobal_MarketInfo_ListInformation2,Gobal_MarketInfo_ListInformation3,Gobal_MarketInfo_ListInformation4,Gobal_MarketInfo_ListInformation5,Gobal_MarketInfo_ListInformation6,Gobal_MarketInfo_ListInformation7,Gobal_MarketInfo_ListInformation8
        Gobal_MarketInfo_ListInformation = self.listInformation      
        Gobal_MarketInfo_ListInformation2 = self.listInformation2
        Gobal_MarketInfo_ListInformation3 = self.listInformation3
        Gobal_MarketInfo_ListInformation4 = self.listInformation4
        Gobal_MarketInfo_ListInformation5 = self.listInformation5
        Gobal_MarketInfo_ListInformation6 = self.listInformation6
        Gobal_MarketInfo_ListInformation7 = self.listInformation7
        Gobal_MarketInfo_ListInformation8 = self.listInformation8

        global Gobal_OnNotifyUDHLC_ListInformation1,Gobal_OnNotifyUDHLC_ListInformation2
        Gobal_OnNotifyUDHLC_ListInformation1 = self.listInformationA
        Gobal_OnNotifyUDHLC_ListInformation2 = self.listInformationB

    def btnMarketInfo_Click(self):
        try:
            m_nCode = skQ.SKQuoteLib_GetMarketBuySellUpDown()
            SendReturnMessage("Quote", m_nCode, "SKQuoteLib_GetMarketBuySellUpDown",GlobalListInformation)
            SendReturnMessage("Quote", m_nCode, "SKQuoteLib_GetMarketTot",GlobalListInformation)
            SendReturnMessage("Quote",m_nCode,"SKQuoteLib_GetMarketHighLowNoChange",GlobalListInformation)

        except Exception as e:
            messagebox.showerror("error！",e)
            
class MACDandBOOL(Frame):

    def __init__(self, master = None):
        Frame.__init__(self, master)
        self.grid()
        self.macd = Frame(self)
        self.macd.master["background"] = "#F5F5F5"
        self.createWidgets()
  
  
    def createWidgets(self):
        self.LabelBoolenTunel = Label(self)
        self.LabelBoolenTunel["text"] = "技術分析__時間單位(日線)"
        self.LabelBoolenTunel["background"] = "#F5F5F5"
        self.LabelBoolenTunel["font"] = 20
        self.LabelBoolenTunel.grid(column=0,row=0,sticky ="w",columnspan=8)


        self.LabelBoolenTunel = Label(self)
        self.LabelBoolenTunel["text"] = " "
        self.LabelBoolenTunel["background"] = "#F5F5F5"
        self.LabelBoolenTunel["font"] = 20
        self.LabelBoolenTunel.grid(column=0,row=1,ipadx = 20)

        self.Labelmacd = Label(self)
        self.Labelmacd["text"] = "商品代碼"
        self.Labelmacd["background"] = "#F5F5F5"
        self.Labelmacd["font"] = 20
        self.Labelmacd.grid(column=1,row=1,sticky = E+W)

        self.Labelmacd = Label(self)
        self.Labelmacd["text"] = "1. MACD"
        self.Labelmacd.config(anchor=NW)
        self.Labelmacd["background"] = "#F5F5F5"
        self.Labelmacd["font"] = 20
        self.Labelmacd.grid(column=1,row=2 ,sticky = E+W)


        #輸入框
        #商品代碼
        self.strStocks = StringVar()
        self.txtStocks = Entry(self, textvariable = self.strStocks)
        self.txtStocks.grid(column=2,row=1)

        #按鈕
        self.Labelmacd = Label(self)
        self.Labelmacd["text"] = " "
        self.Labelmacd["background"] = "#F5F5F5"
        self.Labelmacd["font"] = 20
        self.Labelmacd.grid(column=3,row=2)  

        self.btnAll = Button(self)
        self.btnAll["text"] = "Get ALL Info"
        self.btnAll["background"] = "#d0d0d0"
        self.btnAll["foreground"] = "#000000"
        self.btnAll["command"] =self.btnGetALLInfo_Click
        self.btnAll.grid(column = 4, row = 1,sticky=E,columnspan=2)

        #按鈕
        self.btnCancel = Button(self)
        self.btnCancel["text"] = "Cancel"
        self.btnCancel["background"] = "#d0d0d0"
        self.btnCancel["foreground"] = "#000000"  
        self.btnCancel["command"] =self.btnCancel_Click
        self.btnCancel.grid(column = 6, row = 1,sticky=W,columnspan=2)
        
        #MACD 顯示
        self.MACDLabel = Label(self)
        self.MACDLabel["text"] = "MACD: "
        self.MACDLabel["background"] = "#F5F5F5"
        self.MACDLabel["font"] = 20
        self.MACDLabel.grid(column = 1, row = 3,sticky= E)

        self.MACDshower = Label(self)
        self.MACDshower["text"] = "MACD"
        self.MACDshower.config(anchor=NW)
        self.MACDshower["background"] = "#F5F5F5"
        self.MACDshower["font"] = 20
        self.MACDshower.grid(column = 2, row = 3,sticky= E+W)


        self.DIFLabel = Label(self)
        self.DIFLabel["text"] = "DIF : "
        self.DIFLabel["background"] = "#F5F5F5"
        self.DIFLabel["font"] = 20
        self.DIFLabel.grid(column = 1, row = 4,sticky= E)

        self.DIFshower = Label(self)
        self.DIFshower["text"] = "DIF"
        self.DIFshower.config(anchor=NW)
        self.DIFshower["background"] = "#F5F5F5"
        self.DIFshower["font"] = 20
        self.DIFshower.grid(column = 2, row = 4,sticky= E+W)

        self.OSCLabel = Label(self)
        self.OSCLabel["text"] = "OSC : "
        self.OSCLabel["background"] = "#F5F5F5"
        self.OSCLabel["font"] = 20
        self.OSCLabel.grid(column = 1, row = 5,sticky= E)

        self.OSCshower = Label(self)
        self.OSCshower["text"] = "OSC"
        self.OSCshower.config(anchor=NW)
        self.OSCshower["background"] = "#F5F5F5"
        self.OSCshower["font"] = 20
        self.OSCshower.grid(column = 2, row = 5,sticky= E+W)
        
        global Gobal_MACD_Inf, Gobal_DIF_Inf, Gobal_OSC_Inf
        Gobal_MACD_Inf = self.MACDshower
        Gobal_DIF_Inf = self.DIFshower
        Gobal_OSC_Inf = self.OSCshower

        #BOOLEN
        self.LabelBoolenTunel = Label(self)
        self.LabelBoolenTunel["text"] = " "
        self.LabelBoolenTunel["background"] = "#F5F5F5"
        self.LabelBoolenTunel["font"] = 20
        self.LabelBoolenTunel.grid(column=9,row=1,ipadx = 30)

        self.LabelBoolenTunel = Label(self)
        self.LabelBoolenTunel["text"] = "2. 布林"
        self.LabelBoolenTunel.config(anchor=NW)
        self.LabelBoolenTunel["background"] = "#F5F5F5"
        self.LabelBoolenTunel["font"] = 20  
        self.LabelBoolenTunel.grid(column=10,row=2)

        #BOOLEN 顯示
        self.AVGLabel = Label(self)
        self.AVGLabel["text"] = "AVG :"
        self.AVGLabel["background"] = "#F5F5F5"
        self.AVGLabel["font"] = 20
        self.AVGLabel.grid(column = 10, row = 3, sticky = E)

        self.AVGshower = Label(self)
        self.AVGshower["text"] = "均線"
        self.AVGshower.config(anchor=NW)
        self.AVGshower["background"] = "#F5F5F5"
        self.AVGshower["font"] = 20
        self.AVGshower.grid(column = 11, row = 3, sticky = W)

        self.UBTLabel = Label(self)
        self.UBTLabel["text"] = "UBT :"
        self.UBTLabel["background"] = "#F5F5F5"
        self.UBTLabel["font"] = 20
        self.UBTLabel.grid(column = 10, row = 4, sticky = E)

        self.UBTshower = Label(self)
        self.UBTshower["text"] = "上通道"
        self.UBTshower.config(anchor=NW)
        self.UBTshower["background"] = "#F5F5F5"
        self.UBTshower["font"] = 20
        self.UBTshower.grid(column = 11, row = 4, sticky = W)

        self.LBTLabel = Label(self)
        self.LBTLabel["text"] = "LBT :"
        self.LBTLabel["background"] = "#F5F5F5"
        self.LBTLabel["font"] = 20
        self.LBTLabel.grid(column = 10, row = 5, sticky = E)

        self.LBTshower = Label(self)
        self.LBTshower["text"] = "下通道"
        self.LBTshower.config(anchor=NW)
        self.LBTshower["background"] = "#F5F5F5"
        self.LBTshower["font"] = 20
        self.LBTshower.grid(column = 11, row = 5, sticky = W)

        global Gobal_BoolenAVG_Info, Gobal_BoolenUBT_Info, Gobal_BoolenLBT_Info
        Gobal_BoolenAVG_Info = self.AVGshower
        Gobal_BoolenUBT_Info = self.UBTshower
        Gobal_BoolenLBT_Info = self.LBTshower

        #3.FutureTradeInfo
        self.GoodLookLabel = Label(self)
        self.GoodLookLabel["text"] = ""
        self.GoodLookLabel["background"] = "#F5F5F5"
        self.GoodLookLabel["font"] = 20
        self.GoodLookLabel.grid(column=1,row=7)
        self.GoodLookLabel = Label(self)
        self.GoodLookLabel["text"] = ""
        self.GoodLookLabel["background"] = "#F5F5F5"
        self.GoodLookLabel["font"] = 20
        self.GoodLookLabel.grid(column=1,row=8)  #排版美觀用 無意義

        self.FTInfoLabel = Label(self)
        self.FTInfoLabel["text"] = "3. FutureTradeInfo"
        self.FTInfoLabel.config(anchor=NW)
        self.FTInfoLabel["background"] = "#F5F5F5"
        self.FTInfoLabel["font"] = 20
        self.FTInfoLabel.grid(column=1,row=9 ,sticky = E+W)

        self.MarketNoLabel = Label(self)
        self.MarketNoLabel["text"] = "MarketNo: "
        self.MarketNoLabel["background"] = "#F5F5F5"
        self.MarketNoLabel["font"] = 20
        self.MarketNoLabel.grid(column = 1, row = 10,sticky= E)

        self.MarketNoshower = Label(self)
        self.MarketNoshower["text"] = "MarketNo"
        self.MarketNoshower.config(anchor=NW)
        self.MarketNoshower["background"] = "#F5F5F5"
        self.MarketNoshower["font"] = 20
        self.MarketNoshower.grid(column = 2, row = 10,sticky= E+W)

        self.TotalBuyLabel = Label(self)
        self.TotalBuyLabel["text"] = "總買筆數 :"
        self.TotalBuyLabel["background"] = "#F5F5F5"
        self.TotalBuyLabel["font"] = 20
        self.TotalBuyLabel.grid(column = 1, row = 11,sticky= E)

        self.TotalBuyshower = Label(self)
        self.TotalBuyshower["text"] = "買筆"
        self.TotalBuyshower.config(anchor=NW)
        self.TotalBuyshower["background"] = "#F5F5F5"
        self.TotalBuyshower["font"] = 20
        self.TotalBuyshower.grid(column = 2, row = 11,sticky= E+W)

        self.TotalBuyPLabel = Label(self)
        self.TotalBuyPLabel["text"] = "總買口數 :"
        self.TotalBuyPLabel["background"] = "#F5F5F5"
        self.TotalBuyPLabel["font"] = 20
        self.TotalBuyPLabel.grid(column = 1, row = 12,sticky= E)

        self.TotalBuyPshower = Label(self)
        self.TotalBuyPshower["text"] = "口數"
        self.TotalBuyPshower.config(anchor=NW)
        self.TotalBuyPshower["background"] = "#F5F5F5"
        self.TotalBuyPshower["font"] = 20
        self.TotalBuyPshower.grid(column = 2, row = 12,sticky= E+W)

        self.TotalSucessBLabel = Label(self)
        self.TotalSucessBLabel["text"] = "總成交買筆 :"
        self.TotalSucessBLabel["background"] = "#F5F5F5"
        self.TotalSucessBLabel["font"] = 20
        self.TotalSucessBLabel.grid(column = 1, row = 13,sticky= E)

        self.TotalSucessBshower = Label(self)
        self.TotalSucessBshower["text"] = "總成交買"
        self.TotalSucessBshower.config(anchor=NW)
        self.TotalSucessBshower["background"] = "#F5F5F5"
        self.TotalSucessBshower["font"] = 20
        self.TotalSucessBshower.grid(column = 2, row = 13,sticky= E+W)


        self.StockIdxLabel = Label(self)
        self.StockIdxLabel["text"] = "StockIdx: "
        self.StockIdxLabel["background"] = "#F5F5F5"
        self.StockIdxLabel["font"] = 20
        self.StockIdxLabel.grid(column = 4, row = 10,sticky= E)

        self.StockIdxshower = Label(self)
        self.StockIdxshower["text"] = "StockIdx"
        self.StockIdxshower.config(anchor=NW)
        self.StockIdxshower["background"] = "#F5F5F5"
        self.StockIdxshower["font"] = 20
        self.StockIdxshower.grid(column = 5, row = 10,sticky= E+W)

        self.TotalSellLabel = Label(self)
        self.TotalSellLabel["text"] = "總賣筆數 :"
        self.TotalSellLabel["background"] = "#F5F5F5"
        self.TotalSellLabel["font"] = 20
        self.TotalSellLabel.grid(column = 4, row = 11,sticky= E)

        self.TotalSellshower = Label(self)
        self.TotalSellshower["text"] = "賣筆"
        self.TotalSellshower.config(anchor=NW)
        self.TotalSellshower["background"] = "#F5F5F5"
        self.TotalSellshower["font"] = 20
        self.TotalSellshower.grid(column = 5, row = 11,sticky= E+W)

        self.TotalSellPLabel = Label(self)
        self.TotalSellPLabel["text"] = "總賣口數 :"
        self.TotalSellPLabel["background"] = "#F5F5F5"
        self.TotalSellPLabel["font"] = 20
        self.TotalSellPLabel.grid(column = 4, row = 12,sticky= E)

        self.TotalSellPshower = Label(self)
        self.TotalSellPshower["text"] = "口數"
        self.TotalSellPshower.config(anchor=NW)
        self.TotalSellPshower["background"] = "#F5F5F5"
        self.TotalSellPshower["font"] = 20
        self.TotalSellPshower.grid(column = 5, row = 12,sticky= E+W)

        self.TotalSucessSLabel = Label(self)
        self.TotalSucessSLabel["text"] = "總成交賣筆 :"
        self.TotalSucessSLabel["background"] = "#F5F5F5"
        self.TotalSucessSLabel["font"] = 20
        self.TotalSucessSLabel.grid(column = 4, row = 13,sticky= E)

        self.TotalSucessSshower = Label(self)
        self.TotalSucessSshower["text"] = "總成交賣"
        self.TotalSucessSshower.config(anchor=NW)
        self.TotalSucessSshower["background"] = "#F5F5F5"
        self.TotalSucessSshower["font"] = 20
        self.TotalSucessSshower.grid(column = 5, row = 13,sticky= E+W)
        
        global Gobal_MarketNo_Inf, Gobal_TotalBuy_Inf, Gobal_TotalBuyP_Inf, Gobal_TotalSucessB_Inf, Gobal_StockIdx_Inf, Gobal_TotalSell_Inf, Gobal_TotalSellP_Inf, Gobal_TotalSucessS_Inf
        Gobal_MarketNo_Inf = self.MarketNoshower
        Gobal_TotalBuy_Inf = self.TotalBuyshower
        Gobal_TotalBuyP_Inf = self.TotalBuyPshower
        Gobal_TotalSucessB_Inf = self.TotalSucessBshower
        Gobal_StockIdx_Inf = self.StockIdxshower
        Gobal_TotalSell_Inf = self.TotalSellshower
        Gobal_TotalSellP_Inf = self.TotalSellPshower
        Gobal_TotalSucessS_Inf = self.TotalSucessSshower
        
        
    def btnGetALLInfo_Click(self):
        try:
            m_nCode = skQ.SKQuoteLib_RequestMACD(0, self.txtStocks.get())
            SendReturnMessage("Quote", m_nCode[1], "SKQuoteLib_RequestMACD", GlobalListInformation)
             
        except Exception as e:
            messagebox.showerror("error！",e)

        try:
            m_nCode = skQ.SKQuoteLib_RequestBoolTunel(0, self.txtStocks.get())
            SendReturnMessage("Quote", m_nCode[1],"SKQuoteLib_RequestBoolTunel", GlobalListInformation)
             
        except Exception as e:
            messagebox.showerror("error！",e)

        try:
            page = 0
            m_nCode = skQ.SKQuoteLib_RequestFutureTradeInfo(comtypes.automation.c_short(0),self.txtStocks.get()) 
            SendReturnMessage("Quote", m_nCode, "SKQuoteLib_RequestFutureTradeInfo",GlobalListInformation)

        except Exception as e:
            messagebox.showerror("error！",e)
        
    def btnCancel_Click(self):
        try:
            m_nCode = skQ.SKQuoteLib_RequestMACD(50, self.txtStocks.get())
            SendReturnMessage("Cancel", m_nCode[1], "CancelSKQuoteLib_RequestMACD", GlobalListInformation)
             
        except Exception as e:
            messagebox.showerror("error！",e)

        try:
            m_nCode = skQ.SKQuoteLib_RequestBoolTunel(50, self.txtStocks.get())
            SendReturnMessage("Cancel", m_nCode[1],"CancelSKQuoteLib_RequestBoolTunel", GlobalListInformation)
             
        except Exception as e:
            messagebox.showerror("error！",e)

        try:
            page = 50
            m_nCode = skQ.SKQuoteLib_RequestFutureTradeInfo(comtypes.automation.c_short(0),self.txtStocks.get()) 
            SendReturnMessage("Cancel", m_nCode, "CancelSKQuoteLib_RequestFutureTradeInfo",GlobalListInformation)

        except Exception as e:
            messagebox.showerror("error！",e)


class StrikePrices(Frame):
    def __init__(self, master = None):
        Frame.__init__(self, master)
        self.grid()
        self.StrikePrices = Frame(self)
        self.StrikePrices.master["background"] = "#F5F5F5"
        self.createWidgets()
  
    def createWidgets(self):
        #PageNo
        self.LabelStrikePrices = Label(self)
        self.LabelStrikePrices["text"] = "選擇權商品"
        self.LabelStrikePrices["background"] = "#F5F5F5"
        self.LabelStrikePrices["font"] = 20
        self.LabelStrikePrices.grid(column=0,row=0)
        self.btnGetStrikePrices = Button(self)
        self.btnGetStrikePrices["text"] = "GetStrikePrices"
        self.btnGetStrikePrices["background"] = "#d0d0d0"
        self.btnGetStrikePrices["foreground"] = "#000000"
        self.btnGetStrikePrices["font"] = 20
     
        self.btnGetStrikePrices["command"] = self.btnGetStrikePrices_Click
        self.btnGetStrikePrices.grid(column = 0, row = 1)
    

       
        self.listInformation = Listbox(self,height = 25, width = 100)
        self.listInformation.grid(column = 0, row = 3, sticky = E + W, columnspan = 6)
        
        global Gobal_StrikePrices_ListInformation
        Gobal_StrikePrices_ListInformation = self.listInformation
    def btnGetStrikePrices_Click(self):
         try:
             m_nCode = skQ.SKQuoteLib_GetStrikePrices()
             SendReturnMessage("Quote", m_nCode, "SKQuoteLib_GetStrikePrices",GlobalListInformation)
         except Exception as e:
             messagebox.showerror("error！",e)




#下半部-報價-StockList項目
class StockList(Frame):
    def __init__(self, master = None):
        Frame.__init__(self, master)
        self.grid()
        self.StockList = Frame(self)
        self.StockList.master["background"] = "#F5F5F5"
        self.createWidgets()
        
    def createWidgets(self):
        #市場別代碼
        self.LabelStockList = Label(self)
        self.LabelStockList["text"] = "市場編碼"
        self.LabelStockList["background"] = "#F5F5F5"
        self.LabelStockList["font"] = 20
        self.LabelStockList.grid(column=0,row=0)

        #選擇框
        self.boxMarketNo = Combobox(self,state='readonly')
        self.boxMarketNo['values'] = Config.MARKETNO
        self.boxMarketNo.grid(column=1,row=0)
        
        #按鈕
        self.btnStockList = Button(self)
        self.btnStockList["text"] = "查詢"
        self.btnStockList["background"] = "#d0d0d0"
        self.btnStockList["foreground"] = "#000000"
        self.btnStockList["font"] = 20
        self.btnStockList["command"] = self.btnStockList_Click
        self.btnStockList.grid(column = 4, row = 0)
        
        #訊息欄
        self.listInformation = Listbox(self, height = 25, width = 100)
        self.listInformation.grid(column = 0, row = 2, sticky = E + W, columnspan = 6)
        
        global Gobal_StockList_ListInformation
        Gobal_StockList_ListInformation = self.listInformation
        
    def btnStockList_Click(self):
        try:
            if(self.boxMarketNo.get() == "0 = 上市"):
                sMarketNo=0
            elif(self.boxMarketNo.get() == "1 = 上櫃"):
                sMarketNo=1
            elif(self.boxMarketNo.get() == "2 = 期貨"):
                sMarketNo=2
            elif(self.boxMarketNo.get() == "3 = 選擇權"):
                sMarketNo=3
            elif(self.boxMarketNo.get() == "4 = 興櫃"):
                sMarketNo=4
            else:
                return

            m_nCode = skQ.SKQuoteLib_RequestStockList(sMarketNo)
            SendReturnMessage("Quote", m_nCode, "SKQuoteLib_RequestStockList",GlobalListInformation)
            m_nCode = skQ.SKQuoteLib_RequestStockList(sMarketNo)
            
        except Exception as e:
            messagebox.showerror("error！",e)

#事件 - 🔧 GIL錯誤修復：改為Queue模式
class SKQuoteLibEvents:

    def OnConnection(self, nKind, nCode):
        """連線事件 - 🔧 使用Queue避免GIL錯誤"""
        try:
            # 打包連線數據，放入Queue而不直接更新UI
            connection_data = {
                'kind': nKind,
                'code': nCode
            }
            put_connection_message(connection_data)
        except Exception as e:
            # 即使發生錯誤也不能讓COM事件崩潰
            pass

    def OnNotifyQuoteLONG(self, sMarketNo, nStockidx):
        """報價事件 - 🔧 使用Queue避免GIL錯誤"""
        try:
            pStock = sk.SKSTOCKLONG()
            m_nCode = skQ.SKQuoteLib_GetStockByIndexLONG(sMarketNo, nStockidx, pStock)

            # 打包報價數據，放入Queue而不直接更新UI
            quote_data = {
                'stock_no': pStock.bstrStockNo,
                'stock_name': pStock.bstrStockName,
                'open_price': pStock.nOpen/math.pow(10,pStock.sDecimal),
                'high_price': pStock.nHigh/math.pow(10,pStock.sDecimal),
                'low_price': pStock.nLow/math.pow(10,pStock.sDecimal),
                'close_price': pStock.nClose/math.pow(10,pStock.sDecimal),
                'total_qty': pStock.nTQty
            }
            put_quote_message(quote_data)
        except Exception as e:
            # 即使發生錯誤也不能讓COM事件崩潰
            pass

    def OnNotifyHistoryTicksLONG(self, sMarketNo, nStockidx, nPtr, lDate, lTimehms, lTimemillismicros, nBid, nAsk, nClose, nQty, nSimulate):
        """歷史Tick事件 - 🔧 使用Queue避免GIL錯誤"""
        try:
            # 打包歷史Tick數據，放入Queue而不直接更新UI
            tick_data = {
                'type': 'history',
                'market_no': sMarketNo,
                'stock_idx': nStockidx,
                'ptr': nPtr,
                'date': lDate,
                'time_hms': lTimehms,
                'time_millis': lTimemillismicros,
                'bid': nBid,
                'ask': nAsk,
                'close': nClose,
                'qty': nQty,
                'simulate': nSimulate
            }
            put_tick_message(tick_data)
        except Exception as e:
            # 即使發生錯誤也不能讓COM事件崩潰
            pass

    def OnNotifyTicksLONG(self,sMarketNo, nStockidx, nPtr, lDate, lTimehms, lTimemillismicros, nBid, nAsk, nClose, nQty, nSimulate):
        """即時Tick事件 - 🔧 使用Queue避免GIL錯誤"""
        try:
            # 打包即時Tick數據，放入Queue而不直接更新UI
            tick_data = {
                'type': 'live',
                'market_no': sMarketNo,
                'stock_idx': nStockidx,
                'ptr': nPtr,
                'date': lDate,
                'time_hms': lTimehms,
                'time_millis': lTimemillismicros,
                'bid': nBid,
                'ask': nAsk,
                'close': nClose,
                'qty': nQty,
                'simulate': nSimulate
            }
            put_tick_message(tick_data)
        except Exception as e:
            # 即使發生錯誤也不能讓COM事件崩潰
            pass

    def OnNotifyBest5LONG(self,sMarketNo,nStockidx,nBestBid1,nBestBidQty1,nBestBid2,nBestBidQty2,nBestBid3,nBestBidQty3,nBestBid4,nBestBidQty4,nBestBid5,nBestBidQty5,nExtendBid,nExtendBidQty,nBestAsk1,nBestAskQty1,nBestAsk2,nBestAskQty2,nBestAsk3,nBestAskQty3,nBestAsk4,nBestAskQty4,nBestAsk5,nBestAskQty5,nExtendAsk,nExtendAskQty,nSimulate):
        """五檔報價事件 - 🔧 使用Queue避免GIL錯誤"""
        try:
            # 🔧 GIL錯誤修復：絕不直接操作TreeView控件！

            # 打包五檔報價數據，放入Queue而不直接更新UI
            best5_data = {
                'type': 'best5',
                'market_no': sMarketNo,
                'stock_idx': nStockidx,
                'bid_prices': [nBestBid1, nBestBid2, nBestBid3, nBestBid4, nBestBid5],
                'bid_qtys': [nBestBidQty1, nBestBidQty2, nBestBidQty3, nBestBidQty4, nBestBidQty5],
                'ask_prices': [nBestAsk1, nBestAsk2, nBestAsk3, nBestAsk4, nBestAsk5],
                'ask_qtys': [nBestAskQty1, nBestAskQty2, nBestAskQty3, nBestAskQty4, nBestAskQty5],
                'extend_bid': nExtendBid,
                'extend_bid_qty': nExtendBidQty,
                'extend_ask': nExtendAsk,
                'extend_ask_qty': nExtendAskQty,
                'simulate': nSimulate
            }

            # 使用Queue安全傳遞數據
            put_quote_message(best5_data)

        except Exception as e:
            # 即使發生錯誤也不能讓COM事件崩潰
            pass

    def OnNotifyKLineData(self,bstrStockNo,bstrData):
        """K線數據事件 - 🔧 使用Queue避免GIL錯誤"""
        try:
            # 打包K線數據，放入Queue而不直接更新UI
            kline_data = {
                'type': 'kline',
                'stock_no': bstrStockNo,
                'data': bstrData
            }
            put_quote_message(kline_data)
        except Exception as e:
            # 即使發生錯誤也不能讓COM事件崩潰
            pass

    def OnNotifyMarketTot(self,sMarketNo,sPrt,nTime,nTotv,nTots,nTotc):
        """市場總計事件 - 🔧 使用Queue避免GIL錯誤"""
        try:
            # 打包市場總計數據，放入Queue而不直接更新UI
            market_data = {
                'type': 'market_total',
                'market_no': sMarketNo,
                'prt': sPrt,
                'time': nTime,
                'total_value': nTotv/100,
                'total_shares': nTots,
                'total_count': nTotc
            }
            put_quote_message(market_data)
        except Exception as e:
            # 即使發生錯誤也不能讓COM事件崩潰
            pass

    def OnNotifyMarketHighLow(self,sMarketNo,sPrt,nTime,sUp,sDown,sHigh,sLow,sNoChange):
        """市場漲跌事件 - 🔧 使用Queue避免GIL錯誤"""
        try:
            # 打包市場漲跌數據，放入Queue而不直接更新UI
            market_data = {
                'type': 'market_highlow',
                'market_no': sMarketNo,
                'prt': sPrt,
                'time': nTime,
                'up': sUp,
                'down': sDown,
                'high': sHigh,
                'low': sLow,
                'no_change': sNoChange
            }
            put_quote_message(market_data)
        except Exception as e:
            # 即使發生錯誤也不能讓COM事件崩潰
            pass

    def OnNotifyStockList(self,sMarketNo,bstrStockData):
        """股票清單事件 - 🔧 使用Queue避免GIL錯誤"""
        try:
            # 打包股票清單數據，放入Queue而不直接更新UI
            stock_data = {
                'type': 'stock_list',
                'market_no': sMarketNo,
                'stock_data': bstrStockData
            }
            put_quote_message(stock_data)
        except Exception as e:
            # 即使發生錯誤也不能讓COM事件崩潰
            pass

    def OnNotifyMarketBuySell(self,sMarketNo,sPrt,nTime,nBc,nSc,nBs,nSs):
        """市場買賣事件 - 🔧 使用Queue避免GIL錯誤"""
        try:
            # 打包市場買賣數據，放入Queue而不直接更新UI
            market_data = {
                'type': 'market_buysell',
                'market_no': sMarketNo,
                'prt': sPrt,
                'time': nTime,
                'buy_count': nBc,
                'sell_count': nSc,
                'buy_shares': nBs,
                'sell_shares': nSs
            }
            put_quote_message(market_data)
        except Exception as e:
            # 即使發生錯誤也不能讓COM事件崩潰
            pass

    def OnNotifyServerTime(self,sHour,sMinute,sSecond,nTotal):
        """伺服器時間事件 - 🔧 使用Queue避免GIL錯誤"""
        try:
            # 打包時間數據，放入Queue而不直接更新UI
            time_data = {
                'type': 'server_time',
                'hour': sHour,
                'minute': sMinute,
                'second': sSecond,
                'total': nTotal
            }
            put_connection_message(time_data)
        except Exception as e:
            # 即使發生錯誤也不能讓COM事件崩潰
            pass

    def OnNotifyBoolTunelLONG(self,  sMarketNo, nStockIdx, bstrAVG, bstrUBT, bstrLBT):
        """布林通道事件 - 🔧 使用Queue避免GIL錯誤"""
        try:
            # 打包布林通道數據，放入Queue而不直接更新UI
            bool_data = {
                'type': 'bool_tunnel',
                'market_no': sMarketNo,
                'stock_idx': nStockIdx,
                'avg': bstrAVG,
                'ubt': bstrUBT,
                'lbt': bstrLBT
            }
            put_quote_message(bool_data)
        except Exception as e:
            # 即使發生錯誤也不能讓COM事件崩潰
            pass

    def OnNotifyMACDLONG(self, sMarketNo, nStockidx, bstrMACD, bstrDIF ,bstrOSC):
        """MACD事件 - 🔧 使用Queue避免GIL錯誤"""
        try:
            # 打包MACD數據，放入Queue而不直接更新UI
            macd_data = {
                'type': 'macd',
                'market_no': sMarketNo,
                'stock_idx': nStockidx,
                'macd': bstrMACD,
                'dif': bstrDIF,
                'osc': bstrOSC
            }
            put_quote_message(macd_data)
        except Exception as e:
            # 即使發生錯誤也不能讓COM事件崩潰
            pass

    def  OnNotifyFutureTradeInfoLONG(self, bstrStockNo, sMarketNo, nStockidx, nBuyTotalCount, nSellTotalCount, nBuyTotalQty, nSellTotalQty, nBuyDealTotalCount, nSellDealTotalCount):
        """期貨交易資訊事件 - 🔧 使用Queue避免GIL錯誤"""
        try:
            # 打包期貨交易資訊，放入Queue而不直接更新UI
            trade_data = {
                'type': 'future_trade_info',
                'stock_no': bstrStockNo,
                'market_no': sMarketNo,
                'stock_idx': nStockidx,
                'buy_total_count': nBuyTotalCount,
                'sell_total_count': nSellTotalCount,
                'buy_total_qty': nBuyTotalQty,
                'sell_total_qty': nSellTotalQty,
                'buy_deal_total_count': nBuyDealTotalCount,
                'sell_deal_total_count': nSellDealTotalCount
            }
            put_quote_message(trade_data)
        except Exception as e:
            # 即使發生錯誤也不能讓COM事件崩潰
            pass

    def OnNotifyStrikePrices(self,bstrOptionData):
        """履約價事件 - 🔧 使用Queue避免GIL錯誤"""
        try:
            # 打包履約價數據，放入Queue而不直接更新UI
            strike_data = {
                'type': 'strike_prices',
                'option_data': bstrOptionData
            }
            put_quote_message(strike_data)
        except Exception as e:
            # 即使發生錯誤也不能讓COM事件崩潰
            pass

#SKQuoteLibEventHandler = win32com.client.WithEvents(SKQuoteLib, SKQuoteLibEvents)
SKQuoteEvent=SKQuoteLibEvents()
SKQuoteLibEventHandler = comtypes.client.GetEvents(skQ, SKQuoteEvent)

class SKReplyLibEvent():
    """回報事件類 - 🔧 使用Queue避免GIL錯誤"""

    def OnReplyMessage(self,bstrUserID, bstrMessages):
        """回報訊息事件 - 🔧 使用Queue避免GIL錯誤"""
        try:
            sConfirmCode = -1
            # 打包回報數據，放入Queue而不直接更新UI
            reply_data = {
                'user_id': bstrUserID,
                'message': bstrMessages
            }
            put_reply_message(reply_data)
            return sConfirmCode
        except Exception as e:
            # 即使發生錯誤也不能讓COM事件崩潰
            return -1

# comtypes使用此方式註冊callback
SKReplyEvent = SKReplyLibEvent()
SKReplyLibEventHandler = comtypes.client.GetEvents(skR, SKReplyEvent)


if __name__ == '__main__':
    #Globals.initialize()
    root = Tk()
    root.title("PythonExampleQuote - 🔧 GIL錯誤修復版本")

    # 🔧 GIL錯誤修復：註冊訊息處理器
    register_message_handler('quote', quote_handler)
    register_message_handler('tick', tick_handler)
    register_message_handler('connection', connection_handler)
    register_message_handler('reply', reply_handler)

    # Center
    FrameLogin(master = root)

    #TabControl
    root.TabControl = Notebook(root)
    quote_frame = FrameQuote(master = root)
    root.TabControl.add(quote_frame, text="報價功能")
    root.TabControl.grid(column = 0, row = 2, sticky = 'ew', padx = 10, pady = 10)

    # 🔧 GIL錯誤修復：設置UI控件引用
    set_ui_widget('global_listbox', GlobalListInformation)
    set_ui_widget('quote_listbox', Gobal_Quote_ListInformation)
    set_ui_widget('tick_listbox', Gobal_Tick_ListInformation)
    set_ui_widget('reply_listbox', GlobalListInformation)  # 回報使用全域listbox

    # 🔧 GIL錯誤修復：啟動主線程Queue處理器
    processor = MainThreadProcessor(root, interval_ms=50)
    processor.start()

    root.mainloop()
