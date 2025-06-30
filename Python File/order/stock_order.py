#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
股票下單模組 - 根據官方案例和文件
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import tkinter as tk
from tkinter import ttk, messagebox
import logging
from order.order_config import *

# 設定日誌
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class StockOrderFrame(tk.Frame):
    """股票下單框架"""
    
    def __init__(self, master=None, skcom_objects=None):
        super().__init__(master)
        self.master = master
        
        # SKCOM物件
        self.m_pSKCenter = skcom_objects.get('SKCenter') if skcom_objects else None
        self.m_pSKOrder = skcom_objects.get('SKOrder') if skcom_objects else None
        self.m_pSKReply = skcom_objects.get('SKReply') if skcom_objects else None
        
        # UI變數
        self.order_data = {}
        
        # 建立UI
        self.create_widgets()
        
        # 載入預設值
        self.load_default_values()
    
    def create_widgets(self):
        """建立UI控件"""
        # 主框架
        main_frame = tk.LabelFrame(self, text="股票委託下單", padx=10, pady=10)
        main_frame.grid(column=0, row=0, columnspan=6, sticky=tk.E + tk.W, padx=5, pady=5)
        
        # 第一行：基本資訊
        row = 0
        
        # 帳號
        tk.Label(main_frame, text="帳號:").grid(column=0, row=row, sticky=tk.W, padx=5, pady=2)
        self.entry_account = tk.Entry(main_frame, width=12)
        self.entry_account.grid(column=1, row=row, padx=5, pady=2)
        
        # 股票代碼
        tk.Label(main_frame, text="股票代碼:").grid(column=2, row=row, sticky=tk.W, padx=5, pady=2)
        self.entry_stock_no = tk.Entry(main_frame, width=10)
        self.entry_stock_no.grid(column=3, row=row, padx=5, pady=2)
        
        # 上市櫃
        tk.Label(main_frame, text="上市櫃:").grid(column=4, row=row, sticky=tk.W, padx=5, pady=2)
        self.combo_prime = ttk.Combobox(main_frame, width=8, state='readonly')
        self.combo_prime['values'] = PRIMESET
        self.combo_prime.grid(column=5, row=row, padx=5, pady=2)
        self.combo_prime.current(0)  # 預設選擇上市
        
        # 第二行：交易參數
        row += 1
        
        # 買賣別
        tk.Label(main_frame, text="買賣別:").grid(column=0, row=row, sticky=tk.W, padx=5, pady=2)
        self.combo_buy_sell = ttk.Combobox(main_frame, width=8, state='readonly')
        self.combo_buy_sell['values'] = BUYSELLSET
        self.combo_buy_sell.grid(column=1, row=row, padx=5, pady=2)
        self.combo_buy_sell.current(0)  # 預設買進
        
        # 委託價
        tk.Label(main_frame, text="委託價:").grid(column=2, row=row, sticky=tk.W, padx=5, pady=2)
        self.entry_price = tk.Entry(main_frame, width=10)
        self.entry_price.grid(column=3, row=row, padx=5, pady=2)
        
        # 委託量
        tk.Label(main_frame, text="委託量:").grid(column=4, row=row, sticky=tk.W, padx=5, pady=2)
        self.entry_quantity = tk.Entry(main_frame, width=8)
        self.entry_quantity.grid(column=5, row=row, padx=5, pady=2)
        
        # 第三行：進階參數
        row += 1
        
        # 委託條件
        tk.Label(main_frame, text="委託條件:").grid(column=0, row=row, sticky=tk.W, padx=5, pady=2)
        self.combo_period = ttk.Combobox(main_frame, width=8, state='readonly')
        self.combo_period['values'] = PERIODSET['stock']
        self.combo_period.grid(column=1, row=row, padx=5, pady=2)
        self.combo_period.current(0)  # 預設ROD
        
        # 限市價
        tk.Label(main_frame, text="限市價:").grid(column=2, row=row, sticky=tk.W, padx=5, pady=2)
        self.combo_order_type = ttk.Combobox(main_frame, width=8, state='readonly')
        self.combo_order_type['values'] = STRADETYPE['stock']
        self.combo_order_type.grid(column=3, row=row, padx=5, pady=2)
        self.combo_order_type.current(1)  # 預設限價
        
        # 當沖與否
        tk.Label(main_frame, text="當沖與否:").grid(column=4, row=row, sticky=tk.W, padx=5, pady=2)
        self.combo_day_trade = ttk.Combobox(main_frame, width=8, state='readonly')
        self.combo_day_trade['values'] = FLAGSET['stock']
        self.combo_day_trade.grid(column=5, row=row, padx=5, pady=2)
        self.combo_day_trade.current(0)  # 預設非當沖
        
        # 第四行：按鈕
        row += 1
        button_frame = tk.Frame(main_frame)
        button_frame.grid(column=0, row=row, columnspan=6, pady=10)
        
        # 測試下單按鈕
        self.btn_test_order = tk.Button(button_frame, text="測試下單", 
                                       command=self.test_stock_order,
                                       bg="#4169E1", fg="white", width=12)
        self.btn_test_order.grid(column=0, row=0, padx=5)
        
        # 查詢帳號按鈕
        self.btn_query_account = tk.Button(button_frame, text="查詢帳號", 
                                          command=self.query_account,
                                          bg="#228B22", fg="white", width=12)
        self.btn_query_account.grid(column=1, row=0, padx=5)
        
        # 清除按鈕
        self.btn_clear = tk.Button(button_frame, text="清除", 
                                  command=self.clear_form,
                                  bg="#DC143C", fg="white", width=12)
        self.btn_clear.grid(column=2, row=0, padx=5)
        
        # 訊息顯示區域
        msg_frame = tk.LabelFrame(self, text="下單訊息", padx=5, pady=5)
        msg_frame.grid(column=0, row=1, columnspan=6, sticky=tk.E + tk.W, padx=5, pady=5)
        
        self.text_message = tk.Text(msg_frame, height=8, width=80)
        scrollbar = tk.Scrollbar(msg_frame, orient=tk.VERTICAL, command=self.text_message.yview)
        self.text_message.configure(yscrollcommand=scrollbar.set)
        
        self.text_message.grid(column=0, row=0, sticky=tk.E + tk.W + tk.N + tk.S)
        scrollbar.grid(column=1, row=0, sticky=tk.N + tk.S)
    
    def load_default_values(self):
        """載入預設值"""
        # 載入測試用預設值
        self.entry_account.insert(0, TEST_ACCOUNT_CONFIG.get('ACCOUNT', ''))
        self.entry_stock_no.insert(0, TEST_ACCOUNT_CONFIG.get('STOCK_NO', '2330'))
        self.entry_price.insert(0, str(TEST_ACCOUNT_CONFIG.get('PRICE', 500.0)))
        self.entry_quantity.insert(0, str(TEST_ACCOUNT_CONFIG.get('QUANTITY', 1)))
    
    def add_message(self, message):
        """添加訊息到顯示區域"""
        self.text_message.insert(tk.END, message + "\n")
        self.text_message.see(tk.END)
        logger.info(message)
    
    def clear_form(self):
        """清除表單"""
        self.entry_account.delete(0, tk.END)
        self.entry_stock_no.delete(0, tk.END)
        self.entry_price.delete(0, tk.END)
        self.entry_quantity.delete(0, tk.END)
        self.text_message.delete(1.0, tk.END)
    
    def query_account(self):
        """查詢帳號資訊"""
        if not self.m_pSKOrder:
            self.add_message("【錯誤】SKOrder物件未初始化")
            messagebox.showerror("錯誤", "SKOrder物件未初始化")
            return
        
        try:
            self.add_message("【查詢】開始查詢帳號資訊...")
            
            # 根據官方文件，查詢帳號
            nCode = self.m_pSKOrder.GetUserAccount()
            
            if self.m_pSKCenter:
                msg_text = self.m_pSKCenter.SKCenterLib_GetReturnCodeMessage(nCode)
            else:
                msg_text = f"結果代碼: {nCode}"
            
            self.add_message(f"【查詢帳號】{msg_text} (代碼: {nCode})")
            
            if nCode == 0:
                self.add_message("【成功】帳號查詢成功，請查看回報訊息")
            else:
                self.add_message(f"【失敗】帳號查詢失敗: {msg_text}")
                
        except Exception as e:
            error_msg = f"查詢帳號時發生錯誤: {str(e)}"
            self.add_message(f"【錯誤】{error_msg}")
            messagebox.showerror("查詢錯誤", error_msg)
    
    def test_stock_order(self):
        """測試股票下單"""
        if not self.m_pSKOrder:
            self.add_message("【錯誤】SKOrder物件未初始化")
            messagebox.showerror("錯誤", "SKOrder物件未初始化")
            return
        
        # 取得表單資料
        account = self.entry_account.get().strip()
        stock_no = self.entry_stock_no.get().strip()
        price = self.entry_price.get().strip()
        quantity = self.entry_quantity.get().strip()
        
        # 檢查必填欄位
        if not all([account, stock_no, price, quantity]):
            messagebox.showerror("錯誤", "請填入所有必要欄位")
            return
        
        try:
            # 轉換數值
            price_val = float(price)
            quantity_val = int(quantity)
            
            # 取得選擇的參數
            prime = self.combo_prime.current()  # 0:上市, 1:上櫃, 2:興櫃
            buy_sell = self.combo_buy_sell.current()  # 0:買進, 1:賣出
            period = self.combo_period.current()  # 0:ROD, 1:IOC, 2:FOK
            order_type = self.combo_order_type.current()  # 0:市價, 1:限價, 2:範圍市價
            day_trade = self.combo_day_trade.current()  # 0:非當沖, 1:當沖
            
            self.add_message(f"【下單準備】帳號:{account}, 股票:{stock_no}, 價格:{price_val}, 數量:{quantity_val}")
            self.add_message(f"【參數】上市櫃:{prime}, 買賣:{buy_sell}, 委託條件:{period}, 限市價:{order_type}, 當沖:{day_trade}")
            
            # 根據官方文件，進行股票下單
            # 這裡先做參數檢查，實際下單需要更謹慎
            
            # 警告訊息
            result = messagebox.askyesno("確認下單", 
                f"確定要進行測試下單嗎？\n\n" +
                f"帳號: {account}\n" +
                f"股票: {stock_no}\n" +
                f"價格: {price_val}\n" +
                f"數量: {quantity_val}\n" +
                f"買賣: {BUYSELLSET[buy_sell]}\n\n" +
                "注意：這是真實的下單測試！")
            
            if not result:
                self.add_message("【取消】使用者取消下單")
                return
            
            # 實際下單 (根據官方API)
            # 注意：這裡需要根據實際的API參數進行調整
            self.add_message("【警告】實際下單功能需要根據官方API文件完整實現")
            self.add_message("【建議】請先使用模擬環境測試")
            
            # TODO: 實現實際的下單API調用
            # nCode = self.m_pSKOrder.SendStockOrder(...)
            
        except ValueError as e:
            error_msg = f"數值格式錯誤: {str(e)}"
            self.add_message(f"【錯誤】{error_msg}")
            messagebox.showerror("格式錯誤", error_msg)
        except Exception as e:
            error_msg = f"下單時發生錯誤: {str(e)}"
            self.add_message(f"【錯誤】{error_msg}")
            messagebox.showerror("下單錯誤", error_msg)
