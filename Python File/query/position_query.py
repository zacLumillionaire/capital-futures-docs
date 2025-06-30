#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
部位查詢模組 - 查詢未平倉部位和預約單
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import tkinter as tk
from tkinter import ttk
import logging
import comtypes.client
from datetime import datetime
import re

# 設定日誌
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class PositionQueryFrame(tk.Frame):
    """部位查詢框架"""
    
    def __init__(self, master=None, skcom_objects=None):
        super().__init__(master)
        self.master = master
        
        # SKCOM物件
        self.m_pSKCenter = skcom_objects.get('SKCenter') if skcom_objects else None
        self.m_pSKOrder = skcom_objects.get('SKOrder') if skcom_objects else None
        
        # 查詢資料
        self.positions = []  # 未平倉部位
        self.smart_orders = []  # 預約單/智慧單
        
        # 事件處理器
        self.order_event_handler = None
        
        # 建立UI
        self.create_widgets()
        
        # 註冊事件處理
        self.register_order_events()
    
    def create_widgets(self):
        """建立UI控件"""
        # 主框架
        main_frame = tk.LabelFrame(self, text="部位與預約單查詢", padx=10, pady=10)
        main_frame.grid(column=0, row=0, columnspan=4, sticky=tk.E + tk.W, padx=5, pady=5)
        
        # 控制按鈕
        button_frame = tk.Frame(main_frame)
        button_frame.grid(column=0, row=0, columnspan=4, pady=5)
        
        # 查詢未平倉部位按鈕
        self.btn_query_positions = tk.Button(button_frame, text="查詢未平倉部位", 
                                           command=self.query_open_interest, bg="lightblue")
        self.btn_query_positions.grid(column=0, row=0, padx=5)
        
        # 查詢預約單按鈕 (主要方法 - 使用有效的GetOrderReport)
        self.btn_query_scheduled_orders = tk.Button(button_frame, text="查詢預約單",
                                                   command=self.query_scheduled_orders, bg="lightgreen")
        self.btn_query_scheduled_orders.grid(column=1, row=0, padx=5)

        # 查詢智慧單按鈕 (備用方法 - GetStopLossReport)
        self.btn_query_smart_orders = tk.Button(button_frame, text="查詢智慧單(備用)",
                                              command=self.query_smart_orders, bg="lightyellow")
        self.btn_query_smart_orders.grid(column=2, row=0, padx=5)

        # 查詢最近委託回報按鈕 (新增功能)
        self.btn_query_recent_orders = tk.Button(button_frame, text="查詢最近委託(20筆)",
                                               command=self.query_recent_orders, bg="lightcoral")
        self.btn_query_recent_orders.grid(column=3, row=0, padx=5)

        # 狀態顯示
        self.label_status = tk.Label(main_frame, text="準備查詢", fg="blue")
        self.label_status.grid(column=0, row=1, columnspan=4, pady=5)
        
        # 未平倉部位顯示
        position_frame = tk.LabelFrame(main_frame, text="未平倉部位", padx=5, pady=5)
        position_frame.grid(column=0, row=2, columnspan=4, sticky=tk.E + tk.W, pady=5)
        
        # 建立部位表格
        pos_columns = ('市場', '帳號', '商品', '買賣', '數量', '當沖數量', '平均成本', '手續費', '交易稅')
        self.tree_positions = ttk.Treeview(position_frame, columns=pos_columns, show='headings', height=6)
        
        # 設定部位表格欄位
        for col in pos_columns:
            self.tree_positions.heading(col, text=col)
            self.tree_positions.column(col, width=80)
        
        # 部位表格滾動條
        pos_scrollbar = ttk.Scrollbar(position_frame, orient=tk.VERTICAL, command=self.tree_positions.yview)
        self.tree_positions.configure(yscrollcommand=pos_scrollbar.set)
        
        self.tree_positions.grid(column=0, row=0, sticky=tk.E + tk.W + tk.N + tk.S)
        pos_scrollbar.grid(column=1, row=0, sticky=tk.N + tk.S)
        
        # 預約單/智慧單顯示
        smart_frame = tk.LabelFrame(main_frame, text="預約單/智慧單", padx=5, pady=5)
        smart_frame.grid(column=0, row=3, columnspan=4, sticky=tk.E + tk.W, pady=5)
        
        # 建立智慧單表格
        smart_columns = ('智慧單號', '策略別', '狀態', '商品', '買賣', '觸發價', '委託價', '數量', '建立時間')
        self.tree_smart_orders = ttk.Treeview(smart_frame, columns=smart_columns, show='headings', height=6)
        
        # 設定智慧單表格欄位
        for col in smart_columns:
            self.tree_smart_orders.heading(col, text=col)
            self.tree_smart_orders.column(col, width=90)
        
        # 智慧單表格滾動條
        smart_scrollbar = ttk.Scrollbar(smart_frame, orient=tk.VERTICAL, command=self.tree_smart_orders.yview)
        self.tree_smart_orders.configure(yscrollcommand=smart_scrollbar.set)
        
        self.tree_smart_orders.grid(column=0, row=0, sticky=tk.E + tk.W + tk.N + tk.S)
        smart_scrollbar.grid(column=1, row=0, sticky=tk.N + tk.S)
        
        # 訊息顯示區域
        msg_frame = tk.LabelFrame(main_frame, text="查詢訊息", padx=5, pady=5)
        msg_frame.grid(column=0, row=4, columnspan=4, sticky=tk.E + tk.W + tk.N + tk.S, pady=5)
        
        # 設定權重讓訊息區域可以擴展
        msg_frame.grid_rowconfigure(0, weight=1)
        msg_frame.grid_columnconfigure(0, weight=1)
        
        self.text_messages = tk.Text(msg_frame, height=10, width=80)
        msg_scrollbar = tk.Scrollbar(msg_frame, orient=tk.VERTICAL, command=self.text_messages.yview)
        self.text_messages.configure(yscrollcommand=msg_scrollbar.set)
        
        self.text_messages.grid(column=0, row=0, sticky=tk.E + tk.W + tk.N + tk.S)
        msg_scrollbar.grid(column=1, row=0, sticky=tk.N + tk.S)
        
        # 設定主框架權重
        self.grid_rowconfigure(0, weight=1)
        self.grid_columnconfigure(0, weight=1)
        main_frame.grid_rowconfigure(4, weight=1)
        main_frame.grid_columnconfigure(0, weight=1)
        
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
    
    def register_order_events(self):
        """註冊下單事件處理"""
        if not self.m_pSKOrder:
            self.add_message("【錯誤】SKOrder物件未初始化，無法註冊事件")
            return
        
        try:
            self.add_message("【初始化】開始註冊部位查詢事件處理...")
            
            # 建立事件處理類別
            class SKOrderLibEvent():
                def __init__(self, parent):
                    self.parent = parent
                
                def OnOpenInterest(self, bstrData):
                    """未平倉部位回報事件"""
                    self.parent.on_open_interest_received(bstrData)
                    return 0

                def OnStopLossReport(self, bstrData):
                    """預約單/智慧單回報事件"""
                    self.parent.on_smart_order_received(bstrData)
                    return 0
                
                def OnStrategyData(self, bstrData):
                    """智慧單狀態異動事件"""
                    self.parent.on_strategy_data_received(bstrData)
                    return 0
            
            # 建立事件處理器
            self.order_event = SKOrderLibEvent(self)
            
            # 註冊事件 (如果還沒有註冊過)
            try:
                if not hasattr(self, '_events_registered'):
                    self.order_event_handler = comtypes.client.GetEvents(self.m_pSKOrder, self.order_event)
                    self._events_registered = True
                    self.add_message("【成功】部位查詢事件處理註冊成功")
                else:
                    self.add_message("【提示】事件處理已註冊，跳過重複註冊")
                return True
            except Exception as e:
                self.add_message(f"【錯誤】註冊部位查詢事件失敗: {str(e)}")
                return False
                
        except Exception as e:
            self.add_message(f"【錯誤】建立部位查詢事件處理器失敗: {str(e)}")
            return False
    
    def query_open_interest(self):
        """查詢未平倉部位"""
        if not self.m_pSKOrder:
            self.add_message("【錯誤】SKOrder物件未初始化")
            return
        
        try:
            self.add_message("【查詢】開始查詢未平倉部位...")
            self.label_status.config(text="查詢未平倉部位中...", fg="orange")

            # 檢查SKOrder初始化狀態
            try:
                init_code = self.m_pSKOrder.SKOrderLib_Initialize()
                if init_code == 0:
                    self.add_message("【初始化】SKOrderLib初始化成功")
                elif init_code == 2003:  # SK_WARNING_INITIALIZE_ALREADY
                    self.add_message("【初始化】SKOrderLib已初始化")
                else:
                    self.add_message(f"【警告】SKOrderLib初始化狀態: {init_code}")
            except Exception as e:
                self.add_message(f"【錯誤】檢查初始化狀態失敗: {str(e)}")

            # 清空之前的資料
            self.positions.clear()
            for item in self.tree_positions.get_children():
                self.tree_positions.delete(item)
            
            # 取得登入ID和帳號 (修正為正確的期貨帳號格式)
            login_id = "E123354882"  # 使用登入ID
            account = "F0200006363839"  # 期貨帳號 (需要F020000前綴)

            self.add_message(f"【參數】登入ID: {login_id}, 帳號: {account}")

            # 調用API查詢未平倉部位 (根據官方案例使用GetOpenInterestWithFormat)
            # 參考官方: GetOpenInterestWithFormat(Global.Global_IID, self.__dOrder['boxAccount'], nFormat)
            nFormat = 1  # 1=完整格式
            nCode = self.m_pSKOrder.GetOpenInterestWithFormat(login_id, account, nFormat)
            
            if self.m_pSKCenter:
                msg_text = self.m_pSKCenter.SKCenterLib_GetReturnCodeMessage(nCode)
            else:
                msg_text = f"結果代碼: {nCode}"
            
            self.add_message(f"【API調用】GetOpenInterestWithFormat({login_id}, {account}, {nFormat}) - {msg_text} (代碼: {nCode})")
            
            if nCode == 0:
                self.add_message("【成功】未平倉部位查詢請求已送出，等待回報...")
                self.label_status.config(text="等待未平倉部位回報...", fg="blue")
            else:
                self.add_message(f"【失敗】未平倉部位查詢失敗: {msg_text}")
                self.label_status.config(text="查詢失敗", fg="red")
                
        except Exception as e:
            error_msg = f"查詢未平倉部位時發生錯誤: {str(e)}"
            self.add_message(f"【錯誤】{error_msg}")
            self.label_status.config(text="查詢錯誤", fg="red")
    
    def query_smart_orders(self):
        """查詢預約單/智慧單"""
        if not self.m_pSKOrder:
            self.add_message("【錯誤】SKOrder物件未初始化")
            return
        
        try:
            self.add_message("【查詢】開始查詢預約單/智慧單...")
            self.label_status.config(text="查詢預約單/智慧單中...", fg="orange")

            # 檢查SKOrder初始化狀態
            try:
                init_code = self.m_pSKOrder.SKOrderLib_Initialize()
                if init_code == 0:
                    self.add_message("【初始化】SKOrderLib初始化成功")
                elif init_code == 2003:  # SK_WARNING_INITIALIZE_ALREADY
                    self.add_message("【初始化】SKOrderLib已初始化")
                else:
                    self.add_message(f"【警告】SKOrderLib初始化狀態: {init_code}")
            except Exception as e:
                self.add_message(f"【錯誤】檢查初始化狀態失敗: {str(e)}")

            # 清空之前的資料
            self.smart_orders.clear()
            for item in self.tree_smart_orders.get_children():
                self.tree_smart_orders.delete(item)
            
            # 取得登入ID和帳號 (嘗試不同的帳號格式)
            login_id = "E123354882"
            # 嘗試多種帳號格式 (根據官方案例和錯誤分析)
            account_formats = [
                "6363839",           # 原始帳號
                "F0200006363839",    # 完整期貨帳號格式
                "TF6363839",         # TF + 帳號 (參考官方OnAccount邏輯)
                "F0206363839"        # F020 + 帳號
            ]

            # 使用與未平倉部位查詢相同的帳號格式 (F020000前綴)
            account = "F0200006363839"  # 與未平倉部位查詢保持一致
            nReportStatus = 0        # 0=全部的委託單
            trade_kind = ""          # 空字串=全部類型
            date = ""                # 空字串=不限日期

            self.add_message(f"【參數】登入ID: {login_id}, 帳號: {account} (格式1/4)")

            # 調用API查詢智慧單 (根據官方案例添加完整參數)
            # 參考官方: GetStopLossReport(Global.Global_IID, self.__dOrder["boxAccount"], nReportStatus, self.boxTradeKind.get(), self.txtDate.get())
            nCode = self.m_pSKOrder.GetStopLossReport(login_id, account, nReportStatus, trade_kind, date)
            
            if self.m_pSKCenter:
                msg_text = self.m_pSKCenter.SKCenterLib_GetReturnCodeMessage(nCode)
            else:
                msg_text = f"結果代碼: {nCode}"
            
            self.add_message(f"【API調用】GetStopLossReport({login_id}, {account}, {nReportStatus}, {trade_kind}, {date}) - {msg_text} (代碼: {nCode})")
            
            if nCode == 0:
                self.add_message("【成功】預約單/智慧單查詢請求已送出，等待回報...")
                self.label_status.config(text="等待預約單/智慧單回報...", fg="blue")
            else:
                self.add_message(f"【失敗】預約單/智慧單查詢失敗: {msg_text}")
                self.label_status.config(text="查詢失敗", fg="red")
                
        except Exception as e:
            error_msg = f"查詢預約單/智慧單時發生錯誤: {str(e)}"
            self.add_message(f"【錯誤】{error_msg}")
            self.label_status.config(text="查詢錯誤", fg="red")

    def query_scheduled_orders(self):
        """查詢預約單 (使用GetOrderReport備用方法)"""
        if not self.m_pSKOrder:
            self.add_message("【錯誤】SKOrder物件未初始化")
            return

        try:
            self.add_message("【查詢】開始查詢預約單 (備用方法)...")
            self.label_status.config(text="查詢預約單中 (備用方法)...", fg="orange")

            # 檢查SKOrder初始化狀態
            try:
                init_code = self.m_pSKOrder.SKOrderLib_Initialize()
                if init_code == 0:
                    self.add_message("【初始化】SKOrderLib初始化成功")
                elif init_code == 2003:  # SK_WARNING_INITIALIZE_ALREADY
                    self.add_message("【初始化】SKOrderLib已初始化")
                else:
                    self.add_message(f"【警告】SKOrderLib初始化狀態: {init_code}")
            except Exception as e:
                self.add_message(f"【錯誤】檢查初始化狀態失敗: {str(e)}")

            # 清空之前的資料
            self.smart_orders.clear()
            for item in self.tree_smart_orders.get_children():
                self.tree_smart_orders.delete(item)

            # 取得登入ID和帳號
            login_id = "E123354882"
            account = "F0200006363839"  # 使用完整期貨帳號格式 (與未平倉部位查詢一致)
            format_type = 9      # 9 = 預約單查詢

            self.add_message(f"【參數】登入ID: {login_id}, 帳號: {account}, 格式: {format_type} (預約單)")

            # 調用API查詢預約單 (參考官方LoginForm.py)
            # bstrResult = m_pSKOrder.GetOrderReport(comboBoxUserID.get(), comboBoxAccount.get(), format)
            bstrResult = self.m_pSKOrder.GetOrderReport(login_id, account, format_type)

            self.add_message(f"【API調用】GetOrderReport({login_id}, {account}, {format_type}) - 直接返回結果")

            if bstrResult:
                self.add_message("【成功】預約單查詢完成，處理結果...")
                self.add_message(f"【結果】{bstrResult[:200]}...")  # 顯示前200字元
                self.parse_order_report_data(bstrResult)
                self.label_status.config(text="預約單查詢完成 (備用方法)", fg="green")
            else:
                self.add_message("【結果】查無預約單資料")
                self.label_status.config(text="無預約單資料", fg="green")

        except Exception as e:
            error_msg = f"查詢預約單時發生錯誤: {str(e)}"
            self.add_message(f"【錯誤】{error_msg}")
            self.label_status.config(text="查詢錯誤", fg="red")

    def parse_order_report_data(self, data):
        """解析GetOrderReport返回的預約單資料"""
        try:
            self.add_message("【解析】開始解析預約單資料...")

            # GetOrderReport返回的資料格式可能與GetStopLossReport不同
            # 需要根據實際返回格式進行解析
            lines = data.split('\n')

            for line in lines:
                line = line.strip()
                if not line:
                    continue

                # 簡單顯示原始資料，後續可根據實際格式優化
                self.add_message(f"【預約單資料】{line}")

                # 解析GetOrderReport返回的預約單資料
                if ',' in line and line.startswith('TF,'):
                    parts = line.split(',')
                    if len(parts) >= 30:  # 確保有足夠的欄位
                        try:
                            # 根據實際資料格式解析關鍵欄位
                            order_no = parts[8]      # 委託編號 (索引8)
                            status_code = parts[10]  # 委託狀態 (索引10)
                            product = parts[15]      # 商品代碼 (索引15)
                            buy_sell = parts[22]     # 買賣別 (索引22)
                            price = parts[27]        # 委託價格 (索引27)

                            # 嘗試多個可能的數量欄位
                            qty_candidates = [
                                parts[29] if len(parts) > 29 else "",  # 索引29
                                parts[30] if len(parts) > 30 else "",  # 索引30
                                parts[28] if len(parts) > 28 else "",  # 索引28
                                parts[26] if len(parts) > 26 else "",  # 索引26 (原來的)
                            ]

                            # 選擇第一個看起來像數量的值 (通常是1)
                            qty = "1"  # 預設為1口
                            for candidate in qty_candidates:
                                if candidate and candidate.isdigit() and candidate != "0":
                                    if int(candidate) <= 10:  # 合理的數量範圍
                                        qty = candidate
                                        break

                            order_date = parts[11]   # 委託日期 (索引11)
                            order_time = parts[12]   # 委託時間 (索引12)

                            # 解析委託狀態
                            status_map = {
                                "0": "有效",
                                "1": "部分成交",
                                "2": "全部成交",
                                "3": "已取消",
                                "4": "失效",
                                "5": "等待中"
                            }
                            status_text = status_map.get(status_code, f"狀態{status_code}")

                            # 格式化顯示
                            buy_sell_text = "買進" if buy_sell == "B" else "賣出" if buy_sell == "S" else buy_sell
                            datetime_str = f"{order_date} {order_time}"

                            # 除錯資訊：顯示關鍵欄位
                            self.add_message(f"【除錯】委託:{order_no}, 狀態碼:{status_code}({status_text}), 數量候選:{qty_candidates}, 選擇:{qty}")

                            # 添加到表格
                            self.tree_smart_orders.insert('', 'end', values=(
                                order_no,           # 智慧單號
                                "預約單",           # 策略別
                                status_text,        # 狀態 (使用解析後的狀態)
                                product,            # 商品
                                buy_sell_text,      # 買賣
                                "",                 # 觸發價
                                price,              # 委託價
                                qty,                # 數量
                                datetime_str        # 建立時間
                            ))

                            self.add_message(f"【預約單】{order_no} {product} {buy_sell_text} {qty}口 價格:{price} 狀態:{status_text}")

                        except (IndexError, ValueError) as e:
                            self.add_message(f"【警告】解析預約單欄位時發生錯誤: {e}")
                            # 如果解析失敗，顯示原始資料的前幾個欄位
                            self.tree_smart_orders.insert('', 'end', values=(
                                parts[8] if len(parts) > 8 else "",   # 委託編號
                                "預約單",                              # 類型
                                "未知",                                # 狀態
                                parts[15] if len(parts) > 15 else "", # 商品
                                parts[22] if len(parts) > 22 else "", # 買賣
                                "",                                    # 觸發價
                                parts[27] if len(parts) > 27 else "", # 委託價
                                parts[26] if len(parts) > 26 else "", # 數量
                                ""                                     # 時間
                            ))

        except Exception as e:
            self.add_message(f"【錯誤】解析預約單資料時發生錯誤: {str(e)}")

    def on_open_interest_received(self, data):
        """處理未平倉部位回報"""
        try:
            self.add_message(f"【回報】收到未平倉部位回報")
            self.add_message(f"【原始資料】{data[:100]}...")  # 只顯示前100字元
            
            # 檢查是否為結束標記
            if data.startswith("##"):
                self.add_message("【完成】未平倉部位查詢完成")
                self.label_status.config(text="未平倉部位查詢完成", fg="green")
                return
            
            # 檢查是否為無資料
            if "M003,NO DATA" in data:
                self.add_message("【結果】目前無未平倉部位")
                self.label_status.config(text="無未平倉部位", fg="green")
                return
            
            # 解析部位資料
            self.parse_position_data(data)
            
        except Exception as e:
            self.add_message(f"【錯誤】處理未平倉部位回報時發生錯誤: {str(e)}")
    
    def parse_position_data(self, data):
        """解析未平倉部位資料"""
        try:
            # 資料格式：市場別,帳號,商品,買賣別,未平倉部位,當沖未平倉部位,平均成本,單口手續費,交易稅,LOGIN_ID
            lines = data.split('\n')
            
            for line in lines:
                line = line.strip()
                if not line or line.startswith("##") or "M003,NO DATA" in line:
                    continue
                
                parts = line.split(',')
                if len(parts) >= 9:
                    market_type = parts[0]  # 市場別 (TF=國內期選)
                    account = parts[1]      # 帳號
                    product = parts[2]      # 商品
                    buy_sell = parts[3]     # 買賣別
                    qty = parts[4]          # 未平倉部位
                    day_trade_qty = parts[5] # 當沖未平倉部位
                    avg_cost = parts[6]     # 平均成本
                    fee = parts[7]          # 單口手續費
                    tax = parts[8]          # 交易稅
                    
                    # 添加到表格
                    self.tree_positions.insert('', 'end', values=(
                        market_type, account, product, buy_sell, qty, 
                        day_trade_qty, avg_cost, fee, tax
                    ))
                    
                    self.add_message(f"【部位】{product} {buy_sell} {qty}口 平均成本:{avg_cost}")
            
        except Exception as e:
            self.add_message(f"【錯誤】解析未平倉部位資料時發生錯誤: {str(e)}")
    
    def on_smart_order_received(self, data):
        """處理預約單/智慧單回報"""
        try:
            self.add_message(f"【回報】收到預約單/智慧單回報")
            self.add_message(f"【原始資料】{data[:100]}...")  # 只顯示前100字元

            # 檢查是否為錯誤訊息
            if "M999" in data and "找不到資料表" in data:
                self.add_message("【錯誤】M999錯誤 - 可能是帳號格式問題，嘗試其他格式...")
                self.label_status.config(text="嘗試其他帳號格式...", fg="orange")
                # 可以在這裡觸發重試邏輯
                return

            # 檢查是否為結束標記
            if data.startswith("##"):
                self.add_message("【完成】預約單/智慧單查詢完成")
                self.label_status.config(text="預約單/智慧單查詢完成", fg="green")
                return

            # 檢查是否為無資料
            if "查無資料" in data or "NO DATA" in data:
                self.add_message("【結果】目前無預約單/智慧單")
                self.label_status.config(text="無預約單/智慧單", fg="green")
                return

            # 解析智慧單資料
            self.parse_smart_order_data(data)

        except Exception as e:
            self.add_message(f"【錯誤】處理預約單/智慧單回報時發生錯誤: {str(e)}")
    
    def parse_smart_order_data(self, data):
        """解析預約單/智慧單資料"""
        try:
            # 智慧單資料格式較複雜，包含多種欄位
            lines = data.split('\n')
            
            for line in lines:
                line = line.strip()
                if not line or line.startswith("##"):
                    continue
                
                parts = line.split(',')
                if len(parts) >= 10:
                    # 提取主要欄位 (根據實際回報格式調整)
                    smart_key_no = parts[0] if len(parts) > 0 else ""     # 智慧單號
                    trade_kind = parts[1] if len(parts) > 1 else ""       # 策略別
                    status = parts[2] if len(parts) > 2 else ""           # 狀態
                    stock_no = parts[3] if len(parts) > 3 else ""         # 商品代碼
                    buy_sell = parts[4] if len(parts) > 4 else ""         # 買賣別
                    trigger_price = parts[5] if len(parts) > 5 else ""    # 觸發價格
                    order_price = parts[6] if len(parts) > 6 else ""      # 委託價格
                    qty = parts[7] if len(parts) > 7 else ""              # 委託數量
                    create_time = parts[8] if len(parts) > 8 else ""      # 建立時間
                    
                    # 添加到表格
                    self.tree_smart_orders.insert('', 'end', values=(
                        smart_key_no, trade_kind, status, stock_no, buy_sell,
                        trigger_price, order_price, qty, create_time
                    ))
                    
                    self.add_message(f"【智慧單】{smart_key_no} {stock_no} {buy_sell} 狀態:{status}")
            
        except Exception as e:
            self.add_message(f"【錯誤】解析預約單/智慧單資料時發生錯誤: {str(e)}")
    
    def on_strategy_data_received(self, data):
        """處理智慧單狀態異動事件"""
        try:
            self.add_message(f"【狀態異動】智慧單狀態更新")
            self.add_message(f"【異動資料】{data}")

        except Exception as e:
            self.add_message(f"【錯誤】處理智慧單狀態異動時發生錯誤: {str(e)}")

    def query_recent_orders(self):
        """查詢最近委託回報 (限制20筆) - 解決大量回報問題"""
        if not self.m_pSKOrder:
            self.add_message("【錯誤】SKOrder物件未初始化")
            return

        try:
            self.add_message("【查詢】開始查詢最近委託回報 (限制20筆)...")

            # 清除之前的查詢結果
            for item in self.tree_smart_orders.get_children():
                self.tree_smart_orders.delete(item)

            # 取得登入ID和帳號
            login_id = "E123354882"
            account = "F0200006363839"  # 使用完整期貨帳號格式
            format_type = 1  # 1 = 全部委託

            self.add_message(f"【參數】登入ID: {login_id}, 帳號: {account}, 格式: {format_type}")

            # 調用API查詢委託回報
            bstrResult = self.m_pSKOrder.GetOrderReport(login_id, account, format_type)

            self.add_message(f"【API調用】GetOrderReport({login_id}, {account}, {format_type}) - 委託回報查詢")

            if bstrResult:
                self.add_message("【成功】委託回報查詢完成，處理結果...")
                # 限制顯示筆數，只處理最近20筆
                self.parse_recent_order_data(bstrResult, max_records=20)
                self.label_status.config(text="最近委託查詢完成 (限制20筆)", fg="green")
            else:
                self.add_message("【結果】查無委託回報資料")
                self.label_status.config(text="無委託回報資料", fg="green")

        except Exception as e:
            error_msg = f"查詢最近委託回報時發生錯誤: {str(e)}"
            self.add_message(f"【錯誤】{error_msg}")
            self.label_status.config(text="查詢錯誤", fg="red")

    def parse_recent_order_data(self, data, max_records=20):
        """解析最近委託回報資料 (限制筆數)"""
        try:
            self.add_message(f"【解析】開始解析委託回報資料 (限制{max_records}筆)...")

            # 分割資料行
            lines = data.split('\n')
            processed_count = 0

            # 反向處理，取得最新的記錄
            valid_lines = []
            for line in reversed(lines):
                line = line.strip()
                if not line:
                    continue

                # 只處理期貨相關的委託 (TF開頭)
                if line.startswith('TF,') and ',' in line:
                    valid_lines.append(line)
                    if len(valid_lines) >= max_records:
                        break

            # 再次反向，讓最新的在上面
            for line in reversed(valid_lines):
                parts = line.split(',')
                if len(parts) >= 30:  # 確保有足夠的欄位
                    try:
                        # 解析關鍵欄位
                        order_no = parts[8] if len(parts) > 8 else ""        # 委託編號
                        status_code = parts[10] if len(parts) > 10 else ""   # 委託狀態
                        order_date = parts[11] if len(parts) > 11 else ""    # 委託日期
                        order_time = parts[12] if len(parts) > 12 else ""    # 委託時間
                        product = parts[15] if len(parts) > 15 else ""       # 商品代碼
                        buy_sell = parts[22] if len(parts) > 22 else ""      # 買賣別
                        price = parts[27] if len(parts) > 27 else ""         # 委託價格
                        qty = parts[20] if len(parts) > 20 else "1"          # 委託數量

                        # 解析委託狀態
                        status_map = {
                            "0": "有效",
                            "1": "部分成交",
                            "2": "全部成交",
                            "3": "已取消",
                            "4": "失效",
                            "5": "等待中",
                            "6": "失敗",
                            "7": "成功"
                        }
                        status_text = status_map.get(status_code, f"狀態{status_code}")

                        # 格式化顯示
                        buy_sell_text = "買進" if buy_sell == "B" else "賣出" if buy_sell == "S" else buy_sell
                        datetime_str = f"{order_date} {order_time}"

                        # 添加到表格
                        self.tree_smart_orders.insert('', 'end', values=(
                            order_no,           # 委託編號
                            "委託單",           # 類型
                            status_text,        # 狀態
                            product,            # 商品
                            buy_sell_text,      # 買賣
                            "",                 # 觸發價
                            price,              # 委託價
                            qty,                # 數量
                            datetime_str        # 時間
                        ))

                        processed_count += 1
                        self.add_message(f"【委託{processed_count}】{order_no} {product} {buy_sell_text} {qty}口 價格:{price} 狀態:{status_text}")

                    except (IndexError, ValueError) as e:
                        self.add_message(f"【警告】解析委託欄位時發生錯誤: {e}")

            self.add_message(f"【完成】已處理 {processed_count} 筆最近委託記錄")

        except Exception as e:
            self.add_message(f"【錯誤】解析最近委託資料時發生錯誤: {str(e)}")
