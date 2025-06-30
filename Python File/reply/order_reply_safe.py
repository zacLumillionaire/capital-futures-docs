#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
安全版本的回報處理模組 - 完全避免GIL錯誤
不使用任何COM事件處理，改用查詢方式
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import tkinter as tk
from tkinter import ttk
import logging
import threading
import time

# 設定日誌
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class OrderReplyFrame(tk.Frame):
    """安全版本的下單回報框架 - 無COM事件"""
    
    def __init__(self, master=None, skcom_objects=None):
        super().__init__(master)
        self.master = master
        
        # SKCOM物件
        self.m_pSKCenter = skcom_objects.get('SKCenter') if skcom_objects else None
        self.m_pSKOrder = skcom_objects.get('SKOrder') if skcom_objects else None
        self.m_pSKReply = skcom_objects.get('SKReply') if skcom_objects else None
        
        # 輪詢控制
        self.polling_active = False
        self.polling_thread = None
        
        # 建立UI
        self.create_widgets()
        
        # 顯示安全模式訊息
        self.add_order_message("【安全模式】已啟用無事件版本，避免GIL錯誤")
        self.add_order_message("【說明】使用輪詢方式查詢委託狀態，每5秒更新一次")
        self.add_order_message("【提示】點擊「開始監控」啟動輪詢查詢")
    
    def create_widgets(self):
        """建立UI控件"""
        # 主框架
        main_frame = tk.LabelFrame(self, text="下單回報監控 (安全模式 - 無事件)", padx=10, pady=10)
        main_frame.grid(column=0, row=0, columnspan=4, sticky=tk.E + tk.W, padx=5, pady=5)
        
        # 控制按鈕
        button_frame = tk.Frame(main_frame)
        button_frame.grid(column=0, row=0, columnspan=4, pady=5)
        
        # 開始輪詢監控按鈕
        self.btn_start_monitor = tk.Button(button_frame, text="開始監控", 
                                          command=self.start_polling,
                                          bg="#228B22", fg="white", width=12)
        self.btn_start_monitor.grid(column=0, row=0, padx=5)
        
        # 停止輪詢監控按鈕
        self.btn_stop_monitor = tk.Button(button_frame, text="停止監控", 
                                         command=self.stop_polling,
                                         bg="#DC143C", fg="white", width=12)
        self.btn_stop_monitor.grid(column=1, row=0, padx=5)
        
        # 手動查詢按鈕
        self.btn_manual_query = tk.Button(button_frame, text="手動查詢",
                                         command=self.manual_query,
                                         bg="#FF8C00", fg="white", width=12)
        self.btn_manual_query.grid(column=2, row=0, padx=5)
        
        # 清除訊息按鈕
        self.btn_clear = tk.Button(button_frame, text="清除訊息",
                                  command=self.clear_messages,
                                  bg="#4169E1", fg="white", width=12)
        self.btn_clear.grid(column=3, row=0, padx=5)
        
        # 狀態標籤
        self.label_status = tk.Label(button_frame, text="狀態: 安全模式 (未監控)", fg="red")
        self.label_status.grid(column=0, row=1, columnspan=4, pady=5)
        
        # 回報訊息顯示區域
        msg_frame = tk.LabelFrame(main_frame, text="委託狀態 (輪詢查詢)", padx=5, pady=5)
        msg_frame.grid(column=0, row=1, columnspan=4, sticky=tk.E + tk.W, padx=5, pady=5)
        
        # 委託回報顯示
        self.text_order_reply = tk.Text(msg_frame, height=12, width=80)
        scrollbar1 = tk.Scrollbar(msg_frame, orient=tk.VERTICAL, command=self.text_order_reply.yview)
        self.text_order_reply.configure(yscrollcommand=scrollbar1.set)
        self.text_order_reply.grid(column=0, row=0, sticky=tk.E + tk.W + tk.N + tk.S)
        scrollbar1.grid(column=1, row=0, sticky=tk.N + tk.S)
    
    def add_order_message(self, message):
        """添加委託回報訊息 - 線程安全"""
        def _add_message():
            self.text_order_reply.insert(tk.END, message + "\n")
            self.text_order_reply.see(tk.END)
            logger.info(f"委託回報: {message}")
        
        # 確保在主線程中執行
        if threading.current_thread() == threading.main_thread():
            _add_message()
        else:
            self.master.after(0, _add_message)
    
    def clear_messages(self):
        """清除所有訊息"""
        self.text_order_reply.delete(1.0, tk.END)
        self.add_order_message("【清除】訊息已清除")
    
    def start_polling(self):
        """開始輪詢監控"""
        if self.polling_active:
            self.add_order_message("【警告】監控已在運行中")
            return
        
        self.polling_active = True
        self.label_status.config(text="狀態: 輪詢監控中", fg="green")
        self.btn_start_monitor.config(state="disabled")
        self.btn_stop_monitor.config(state="normal")
        
        self.add_order_message("【啟動】開始輪詢監控委託狀態")
        self.add_order_message("【設定】每5秒查詢一次最新委託狀態")
        
        # 啟動輪詢線程
        self.polling_thread = threading.Thread(target=self._polling_worker, daemon=True)
        self.polling_thread.start()
    
    def stop_polling(self):
        """停止輪詢監控"""
        self.polling_active = False
        self.label_status.config(text="狀態: 安全模式 (未監控)", fg="red")
        self.btn_start_monitor.config(state="normal")
        self.btn_stop_monitor.config(state="disabled")
        
        self.add_order_message("【停止】輪詢監控已停止")
    
    def _polling_worker(self):
        """輪詢工作線程"""
        while self.polling_active:
            try:
                # 每5秒查詢一次
                time.sleep(5)
                if not self.polling_active:
                    break
                
                # 查詢委託狀態
                self._query_order_status()
                
            except Exception as e:
                self.add_order_message(f"【錯誤】輪詢查詢失敗: {str(e)}")
                time.sleep(10)  # 錯誤時等待更久
    
    def manual_query(self):
        """手動查詢委託狀態"""
        self.add_order_message("【手動】執行委託狀態查詢...")
        self._query_order_status()
    
    def _query_order_status(self):
        """查詢委託狀態 (核心方法)"""
        if not self.m_pSKOrder:
            self.add_order_message("【錯誤】SKOrder物件未初始化")
            return
        
        try:
            # 查詢最近委託
            login_id = "E123354882"
            account = "F0200006363839"
            format_type = 1  # 全部委託
            
            bstrResult = self.m_pSKOrder.GetOrderReport(login_id, account, format_type)
            
            if bstrResult:
                # 解析最近的委託記錄
                lines = bstrResult.split('\n')
                recent_orders = []
                
                for line in lines:
                    line = line.strip()
                    if line and line.startswith('TF,'):
                        parts = line.split(',')
                        if len(parts) >= 30:
                            try:
                                order_no = parts[8] if len(parts) > 8 else ""
                                status_code = parts[10] if len(parts) > 10 else ""
                                product = parts[15] if len(parts) > 15 else ""
                                buy_sell = parts[22] if len(parts) > 22 else ""
                                price = parts[27] if len(parts) > 27 else ""
                                qty = parts[20] if len(parts) > 20 else ""
                                
                                # 狀態對照
                                status_map = {
                                    "0": "有效", "1": "部分成交", "2": "全部成交",
                                    "3": "已取消", "4": "失效", "5": "等待中"
                                }
                                status_text = status_map.get(status_code, f"狀態{status_code}")
                                
                                recent_orders.append({
                                    'order_no': order_no,
                                    'status': status_text,
                                    'product': product,
                                    'buy_sell': buy_sell,
                                    'price': price,
                                    'qty': qty
                                })
                            except:
                                continue
                
                # 顯示最近5筆
                if recent_orders:
                    self.add_order_message(f"【查詢】找到 {len(recent_orders)} 筆委託，顯示最近5筆:")
                    for i, order in enumerate(recent_orders[-5:], 1):
                        buy_sell_text = "買進" if order['buy_sell'] == "B" else "賣出"
                        self.add_order_message(
                            f"  {i}. {order['order_no']} {order['product']} "
                            f"{buy_sell_text} {order['qty']}口 價格:{order['price']} "
                            f"狀態:{order['status']}"
                        )
                else:
                    self.add_order_message("【結果】查無委託記錄")
            else:
                self.add_order_message("【結果】查無委託資料")
                
        except Exception as e:
            self.add_order_message(f"【錯誤】查詢委託狀態失敗: {str(e)}")
    
    # 兼容性方法 (保持與原版本的接口一致)
    def add_fill_message(self, message):
        """添加成交回報訊息 (兼容性方法)"""
        self.add_order_message(f"【成交】{message}")
    
    def connect_reply_server(self):
        """連線回報主機 (兼容性方法)"""
        self.add_order_message("【安全模式】不使用回報主機連線，改用輪詢查詢")
        return True
