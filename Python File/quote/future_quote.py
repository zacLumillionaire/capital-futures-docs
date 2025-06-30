#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
期貨報價查詢模組 - 動態查詢小台指近月合約
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import tkinter as tk
from tkinter import ttk, messagebox
import logging
import comtypes.client
from datetime import datetime, timedelta
import re

# 設定日誌
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class FutureQuoteFrame(tk.Frame):
    """期貨報價查詢框架"""
    
    def __init__(self, master=None, skcom_objects=None):
        super().__init__(master)
        self.master = master
        
        # SKCOM物件
        self.m_pSKCenter = skcom_objects.get('SKCenter') if skcom_objects else None
        self.m_pSKQuote = skcom_objects.get('SKQuote') if skcom_objects else None
        
        # 商品清單資料
        self.future_products = {}
        self.mtx_contracts = []  # 小台指合約清單
        self.current_near_month = None  # 當前近月合約

        # 連線狀態
        self.is_connected = False
        self.stocks_ready = False

        # 事件處理器
        self.quote_event_handler = None
        
        # 建立UI
        self.create_widgets()
        
        # 註冊事件處理
        self.register_quote_events()
    
    def create_widgets(self):
        """建立UI控件"""
        # 主框架
        main_frame = tk.LabelFrame(self, text="期貨商品查詢", padx=10, pady=10)
        main_frame.grid(column=0, row=0, columnspan=4, sticky=tk.E + tk.W, padx=5, pady=5)
        
        # 控制按鈕
        button_frame = tk.Frame(main_frame)
        button_frame.grid(column=0, row=0, columnspan=4, pady=5)

        # 連線報價主機按鈕
        self.btn_connect = tk.Button(button_frame, text="連線報價主機",
                                    command=self.connect_quote_server, bg="lightblue")
        self.btn_connect.grid(column=0, row=0, padx=5)

        # 查詢期貨商品清單按鈕
        self.btn_query_futures = tk.Button(button_frame, text="查詢期貨商品清單",
                                          command=self.query_future_products, state=tk.DISABLED)
        self.btn_query_futures.grid(column=1, row=0, padx=5)

        # 查詢小台指近月按鈕
        self.btn_query_mtx = tk.Button(button_frame, text="查詢小台指近月合約",
                                      command=self.find_mtx_near_month, state=tk.DISABLED)
        self.btn_query_mtx.grid(column=2, row=0, padx=5)
        
        # 狀態顯示
        self.label_status = tk.Label(main_frame, text="準備查詢", fg="blue")
        self.label_status.grid(column=0, row=1, columnspan=4, pady=5)
        
        # 小台指合約資訊顯示
        info_frame = tk.LabelFrame(main_frame, text="小台指合約資訊", padx=5, pady=5)
        info_frame.grid(column=0, row=2, columnspan=4, sticky=tk.E + tk.W, pady=5)
        
        # 近月合約顯示
        tk.Label(info_frame, text="近月合約:").grid(column=0, row=0, sticky=tk.W, padx=5)
        self.label_near_month = tk.Label(info_frame, text="未查詢", fg="red", font=("Arial", 12, "bold"))
        self.label_near_month.grid(column=1, row=0, sticky=tk.W, padx=5)
        
        # 複製按鈕
        self.btn_copy_code = tk.Button(info_frame, text="複製代碼", 
                                      command=self.copy_near_month_code, state=tk.DISABLED)
        self.btn_copy_code.grid(column=2, row=0, padx=5)
        
        # 合約清單
        list_frame = tk.LabelFrame(main_frame, text="小台指合約清單", padx=5, pady=5)
        list_frame.grid(column=0, row=3, columnspan=4, sticky=tk.E + tk.W, pady=5)
        
        # 建立表格
        columns = ('代碼', '名稱', '最後交易日', '狀態')
        self.tree_contracts = ttk.Treeview(list_frame, columns=columns, show='headings', height=8)
        
        # 設定欄位標題
        for col in columns:
            self.tree_contracts.heading(col, text=col)
            self.tree_contracts.column(col, width=120)
        
        # 滾動條
        scrollbar = ttk.Scrollbar(list_frame, orient=tk.VERTICAL, command=self.tree_contracts.yview)
        self.tree_contracts.configure(yscrollcommand=scrollbar.set)
        
        # 放置表格和滾動條
        self.tree_contracts.grid(column=0, row=0, sticky=tk.E + tk.W + tk.N + tk.S)
        scrollbar.grid(column=1, row=0, sticky=tk.N + tk.S)
        
        # 訊息顯示區域
        msg_frame = tk.LabelFrame(main_frame, text="查詢訊息", padx=5, pady=5)
        msg_frame.grid(column=0, row=4, columnspan=4, sticky=tk.E + tk.W, pady=5)
        
        self.text_messages = tk.Text(msg_frame, height=8, width=80)
        msg_scrollbar = tk.Scrollbar(msg_frame, orient=tk.VERTICAL, command=self.text_messages.yview)
        self.text_messages.configure(yscrollcommand=msg_scrollbar.set)
        
        self.text_messages.grid(column=0, row=0, sticky=tk.E + tk.W + tk.N + tk.S)
        msg_scrollbar.grid(column=1, row=0, sticky=tk.N + tk.S)
        
        # 清除訊息按鈕
        tk.Button(msg_frame, text="清除訊息", command=self.clear_messages).grid(column=0, row=1, pady=5)
    
    def add_message(self, message):
        """添加訊息到顯示區域"""
        timestamp = datetime.now().strftime("%H:%M:%S")
        full_message = f"[{timestamp}] {message}\n"
        self.text_messages.insert(tk.END, full_message)
        self.text_messages.see(tk.END)
        logger.info(message)
    
    def clear_messages(self):
        """清除所有訊息"""
        self.text_messages.delete(1.0, tk.END)

    def connect_quote_server(self):
        """連線報價主機 - 根據官方案例實現"""
        if not self.m_pSKQuote:
            self.add_message("【錯誤】SKQuote物件未初始化")
            # 移除messagebox避免多線程衝突
            # messagebox.showerror("錯誤", "SKQuote物件未初始化")
            return

        try:
            self.add_message("【連線】開始連線報價主機...")
            self.label_status.config(text="連線中...", fg="orange")

            # 重置連線狀態
            self.is_connected = False
            self.stocks_ready = False

            # 調用API連線報價主機 (根據官方案例)
            nCode = self.m_pSKQuote.SKQuoteLib_EnterMonitorLONG()

            if self.m_pSKCenter:
                msg_text = self.m_pSKCenter.SKCenterLib_GetReturnCodeMessage(nCode)
            else:
                msg_text = f"結果代碼: {nCode}"

            self.add_message(f"【API調用】SKQuoteLib_EnterMonitorLONG() - {msg_text} (代碼: {nCode})")

            if nCode == 0:
                self.add_message("【成功】連線請求已送出，等待連線完成...")
                self.add_message("【提示】請等待 'Stocks ready!' 訊息後再查詢商品清單")
                self.btn_connect.config(state=tk.DISABLED)
            else:
                self.add_message(f"【失敗】連線報價主機失敗: {msg_text}")
                self.label_status.config(text="連線失敗", fg="red")

        except Exception as e:
            error_msg = f"連線報價主機時發生錯誤: {str(e)}"
            self.add_message(f"【錯誤】{error_msg}")
            self.label_status.config(text="連線錯誤", fg="red")
            # 移除messagebox避免多線程衝突
            # messagebox.showerror("連線錯誤", error_msg)

    def on_stocks_ready(self):
        """商品資料準備完成事件處理"""
        try:
            self.add_message("【準備完成】商品資料已下載完成，可以開始查詢商品清單")
            self.label_status.config(text="已連線 - 商品資料準備完成", fg="green")

            # 啟用查詢按鈕
            self.btn_query_futures.config(state=tk.NORMAL)
            self.btn_query_mtx.config(state=tk.NORMAL)

            # 自動查詢期貨商品清單
            self.add_message("【自動查詢】開始自動查詢期貨商品清單...")
            self.query_future_products()

        except Exception as e:
            self.add_message(f"【錯誤】處理商品資料準備完成事件時發生錯誤: {str(e)}")
    
    def register_quote_events(self):
        """註冊報價事件處理"""
        if not self.m_pSKQuote:
            self.add_message("【錯誤】SKQuote物件未初始化，無法註冊事件")
            return
        
        try:
            self.add_message("【初始化】開始註冊報價事件處理...")
            
            # 根據官方案例建立事件處理類別
            class SKQuoteLibEvent():
                def __init__(self, parent):
                    self.parent = parent
                
                def OnNotifyStockList(self, sMarketNo, bstrStockData):
                    """商品清單回報事件"""
                    self.parent.on_stock_list_received(sMarketNo, bstrStockData)
                    return 0
                
                def OnConnection(self, nKind, nCode):
                    """連線狀態事件 - 根據官方案例實現"""
                    if nKind == 3001:
                        msg = "【連線狀態】Connected! 已連線到報價主機"
                        self.parent.is_connected = True
                    elif nKind == 3002:
                        msg = "【連線狀態】DisConnected! 已斷線"
                        self.parent.is_connected = False
                        self.parent.stocks_ready = False
                    elif nKind == 3003:
                        msg = "【連線狀態】Stocks ready! 商品資料已準備完成"
                        self.parent.stocks_ready = True
                        self.parent.on_stocks_ready()  # 觸發商品資料準備完成事件
                    elif nKind == 3021:
                        msg = "【連線狀態】Connect Error! 連線錯誤"
                        self.parent.is_connected = False
                    else:
                        msg = f"【連線狀態】Unknown Kind: {nKind}, Code: {nCode}"

                    self.parent.add_message(msg)
                    return 0
            
            # 建立事件處理器
            self.quote_event = SKQuoteLibEvent(self)
            
            # 嘗試註冊事件
            try:
                self.quote_event_handler = comtypes.client.GetEvents(self.m_pSKQuote, self.quote_event)
                self.add_message("【成功】報價事件處理註冊成功")
                return True
            except Exception as e:
                self.add_message(f"【錯誤】註冊報價事件失敗: {str(e)}")
                return False
                
        except Exception as e:
            self.add_message(f"【錯誤】建立報價事件處理器失敗: {str(e)}")
            return False
    
    def query_future_products(self):
        """查詢期貨商品清單"""
        if not self.m_pSKQuote:
            self.add_message("【錯誤】SKQuote物件未初始化")
            # 移除messagebox避免多線程衝突
            # messagebox.showerror("錯誤", "SKQuote物件未初始化")
            return

        # 檢查連線狀態
        if not self.is_connected:
            self.add_message("【錯誤】報價主機尚未連線，請先點擊「連線報價主機」")
            # 移除messagebox避免多線程衝突
            # messagebox.showerror("錯誤", "請先連線報價主機")
            return

        if not self.stocks_ready:
            self.add_message("【錯誤】商品資料尚未準備完成，請等待 'Stocks ready!' 訊息")
            # 移除messagebox避免多線程衝突
            # messagebox.showwarning("警告", "商品資料尚未準備完成，請稍候")
            return

        try:
            self.add_message("【查詢】開始查詢期貨商品清單...")
            self.label_status.config(text="查詢中...", fg="orange")
            
            # 清空之前的資料
            self.future_products.clear()
            self.mtx_contracts.clear()
            
            # 清空表格
            for item in self.tree_contracts.get_children():
                self.tree_contracts.delete(item)
            
            # 調用API查詢期貨商品清單 (市場代碼 2 = 期貨)
            nCode = self.m_pSKQuote.SKQuoteLib_RequestStockList(2)
            
            if self.m_pSKCenter:
                msg_text = self.m_pSKCenter.SKCenterLib_GetReturnCodeMessage(nCode)
            else:
                msg_text = f"結果代碼: {nCode}"
            
            self.add_message(f"【API調用】SKQuoteLib_RequestStockList(2) - {msg_text} (代碼: {nCode})")
            
            if nCode == 0:
                self.add_message("【成功】期貨商品清單查詢請求已送出，等待回報...")
                self.label_status.config(text="等待回報中...", fg="blue")
            else:
                self.add_message(f"【失敗】期貨商品清單查詢失敗: {msg_text}")
                self.label_status.config(text="查詢失敗", fg="red")
                
        except Exception as e:
            error_msg = f"查詢期貨商品清單時發生錯誤: {str(e)}"
            self.add_message(f"【錯誤】{error_msg}")
            self.label_status.config(text="查詢錯誤", fg="red")
            # 移除messagebox避免多線程衝突
            # messagebox.showerror("查詢錯誤", error_msg)
    
    def on_stock_list_received(self, sMarketNo, bstrStockData):
        """處理商品清單回報"""
        try:
            self.add_message(f"【回報】收到市場 {sMarketNo} 的商品清單回報")
            
            if sMarketNo == 2:  # 期貨市場
                self.parse_future_products(bstrStockData)
            
        except Exception as e:
            self.add_message(f"【錯誤】處理商品清單回報時發生錯誤: {str(e)}")
    
    def parse_future_products(self, stock_data):
        """解析期貨商品資料"""
        try:
            self.add_message("【解析】開始解析期貨商品資料...")
            
            # 解析商品資料 (格式可能是以分隔符分隔的字串)
            # 根據官方文件，資料格式可能包含：商品代碼,商品名稱,最後交易日等
            
            # 先記錄原始資料
            self.add_message(f"【原始資料】{stock_data[:200]}...")  # 只顯示前200字元
            
            # 嘗試解析資料 (可能需要根據實際格式調整)
            products = stock_data.split(',') if stock_data else []
            
            mtx_count = 0
            for product in products:
                product = product.strip()
                if product:
                    # 檢查是否為小台指相關合約
                    if self.is_mtx_contract(product):
                        self.mtx_contracts.append(product)
                        mtx_count += 1
                        self.add_message(f"【發現】小台指合約: {product}")
            
            self.add_message(f"【統計】共找到 {len(products)} 個期貨商品，其中 {mtx_count} 個小台指合約")
            
            # 更新UI
            self.update_contract_list()
            self.label_status.config(text="查詢完成", fg="green")
            
        except Exception as e:
            self.add_message(f"【錯誤】解析期貨商品資料時發生錯誤: {str(e)}")
            self.label_status.config(text="解析錯誤", fg="red")
    
    def is_mtx_contract(self, product_code):
        """判斷是否為小台指合約"""
        # 小台指合約的可能格式：
        # MTX, MXF, MXFR1, MXF202501, 等
        mtx_patterns = [
            r'^MTX',      # 以MTX開頭
            r'^MXF',      # 以MXF開頭  
            r'小台',       # 包含"小台"
            r'Mini',      # 包含"Mini"
        ]
        
        for pattern in mtx_patterns:
            if re.search(pattern, product_code, re.IGNORECASE):
                return True
        return False
    
    def update_contract_list(self):
        """更新合約清單顯示"""
        # 清空表格
        for item in self.tree_contracts.get_children():
            self.tree_contracts.delete(item)
        
        # 添加小台指合約到表格
        for contract in self.mtx_contracts:
            # 這裡需要根據實際資料格式解析
            # 暫時使用簡單的顯示方式
            self.tree_contracts.insert('', 'end', values=(contract, '小台指期貨', '待查詢', '可交易'))
    
    def find_mtx_near_month(self):
        """查找小台指近月合約"""
        if not self.mtx_contracts:
            self.add_message("【提示】請先查詢期貨商品清單")
            # 移除messagebox避免多線程衝突
            # messagebox.showwarning("提示", "請先查詢期貨商品清單")
            return
        
        try:
            self.add_message("【分析】開始分析小台指近月合約...")
            
            # 簡單的近月合約判斷邏輯
            # 實際應用中需要根據最後交易日來判斷
            near_month_candidates = []
            
            for contract in self.mtx_contracts:
                # 尋找可能的近月合約格式
                if 'R1' in contract or 'MXFR1' in contract:
                    near_month_candidates.append(contract)
            
            if near_month_candidates:
                # 選擇第一個作為近月合約
                self.current_near_month = near_month_candidates[0]
                self.label_near_month.config(text=self.current_near_month, fg="green")
                self.btn_copy_code.config(state=tk.NORMAL)
                self.add_message(f"【成功】找到小台指近月合約: {self.current_near_month}")
            else:
                # 如果沒有找到R1格式，使用第一個小台指合約
                if self.mtx_contracts:
                    self.current_near_month = self.mtx_contracts[0]
                    self.label_near_month.config(text=self.current_near_month, fg="orange")
                    self.btn_copy_code.config(state=tk.NORMAL)
                    self.add_message(f"【建議】使用第一個小台指合約: {self.current_near_month}")
                else:
                    self.add_message("【失敗】未找到小台指合約")
                    
        except Exception as e:
            self.add_message(f"【錯誤】分析近月合約時發生錯誤: {str(e)}")
    
    def copy_near_month_code(self):
        """複製近月合約代碼到剪貼簿"""
        if self.current_near_month:
            try:
                self.master.clipboard_clear()
                self.master.clipboard_append(self.current_near_month)
                self.add_message(f"【成功】已複製合約代碼到剪貼簿: {self.current_near_month}")
                # 移除messagebox避免多線程衝突
                # messagebox.showinfo("成功", f"已複製合約代碼: {self.current_near_month}")
            except Exception as e:
                self.add_message(f"【錯誤】複製到剪貼簿失敗: {str(e)}")
    
    def get_near_month_contract(self):
        """取得當前近月合約代碼"""
        return self.current_near_month
