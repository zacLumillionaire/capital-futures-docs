#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
即時回報處理模組 - 基於官方案例的正確實作
避免GIL錯誤，保持即時性
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import tkinter as tk
from tkinter import ttk
import logging
import comtypes.client
import queue
import threading

# 設定日誌
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class OrderReplyFrame(tk.Frame):
    """即時回報框架 - 基於官方案例的正確實作"""
    
    def __init__(self, master=None, skcom_objects=None):
        super().__init__(master)
        self.master = master
        
        # SKCOM物件
        self.m_pSKCenter = skcom_objects.get('SKCenter') if skcom_objects else None
        self.m_pSKOrder = skcom_objects.get('SKOrder') if skcom_objects else None
        self.m_pSKReply = skcom_objects.get('SKReply') if skcom_objects else None
        
        # 使用隊列進行線程安全的訊息傳遞
        self.message_queue = queue.Queue()
        self.processing_messages = False
        
        # 事件處理器
        self.order_event_handler = None
        self.reply_event_handler = None
        
        # 建立UI
        self.create_widgets()
        
        # 啟動訊息處理
        self.start_message_processing()
        
        # 註冊事件處理 (基於官方案例)
        self.register_events()
    
    def create_widgets(self):
        """建立UI控件"""
        # 主框架
        main_frame = tk.LabelFrame(self, text="即時回報監控 (官方案例版)", padx=10, pady=10)
        main_frame.grid(column=0, row=0, columnspan=4, sticky=tk.E + tk.W, padx=5, pady=5)
        
        # 控制按鈕
        button_frame = tk.Frame(main_frame)
        button_frame.grid(column=0, row=0, columnspan=4, pady=5)
        
        # 開始監控按鈕
        self.btn_start_monitor = tk.Button(button_frame, text="開始監控", 
                                          command=self.start_monitoring,
                                          bg="#228B22", fg="white", width=12)
        self.btn_start_monitor.grid(column=0, row=0, padx=5)
        
        # 停止監控按鈕
        self.btn_stop_monitor = tk.Button(button_frame, text="停止監控", 
                                         command=self.stop_monitoring,
                                         bg="#DC143C", fg="white", width=12)
        self.btn_stop_monitor.grid(column=1, row=0, padx=5)
        
        # 連線回報按鈕
        self.btn_connect_reply = tk.Button(button_frame, text="連線回報",
                                          command=self.connect_reply_server,
                                          bg="#FF8C00", fg="white", width=12)
        self.btn_connect_reply.grid(column=2, row=0, padx=5)
        
        # 清除訊息按鈕
        self.btn_clear = tk.Button(button_frame, text="清除訊息",
                                  command=self.clear_messages,
                                  bg="#4169E1", fg="white", width=12)
        self.btn_clear.grid(column=3, row=0, padx=5)
        
        # 狀態標籤
        self.label_status = tk.Label(button_frame, text="狀態: 未監控", fg="red")
        self.label_status.grid(column=0, row=1, columnspan=4, pady=5)
        
        # 回報訊息顯示區域
        msg_frame = tk.LabelFrame(main_frame, text="即時回報訊息", padx=5, pady=5)
        msg_frame.grid(column=0, row=1, columnspan=4, sticky=tk.E + tk.W, padx=5, pady=5)
        
        # 即時回報顯示
        self.text_reply = tk.Text(msg_frame, height=15, width=80)
        scrollbar = tk.Scrollbar(msg_frame, orient=tk.VERTICAL, command=self.text_reply.yview)
        self.text_reply.configure(yscrollcommand=scrollbar.set)
        self.text_reply.grid(column=0, row=0, sticky=tk.E + tk.W + tk.N + tk.S)
        scrollbar.grid(column=1, row=0, sticky=tk.N + tk.S)
    
    def start_message_processing(self):
        """啟動訊息處理 (在主線程中)"""
        if not self.processing_messages:
            self.processing_messages = True
            self.process_message_queue()
    
    def process_message_queue(self):
        """處理訊息隊列 (在主線程中執行)"""
        try:
            while not self.message_queue.empty():
                message = self.message_queue.get_nowait()
                self.text_reply.insert(tk.END, message + "\n")
                self.text_reply.see(tk.END)
        except queue.Empty:
            pass
        
        # 每100ms檢查一次隊列
        if self.processing_messages:
            self.master.after(100, self.process_message_queue)
    
    def add_message(self, message):
        """添加訊息到隊列 (線程安全)"""
        try:
            self.message_queue.put(message)
            logger.info(f"即時回報: {message}")
        except:
            pass  # 避免隊列滿時的錯誤
    
    def clear_messages(self):
        """清除所有訊息"""
        self.text_reply.delete(1.0, tk.END)
        self.add_message("【清除】訊息已清除")
    
    def register_events(self):
        """註冊事件處理 - 基於官方案例"""
        try:
            self.add_message("【初始化】註冊即時回報事件...")
            
            # 註冊SKOrder事件 (基於官方案例)
            if self.m_pSKOrder:
                self.register_order_events()
            
            # 註冊SKReply事件 (基於官方案例)
            if self.m_pSKReply:
                self.register_reply_events()
                
        except Exception as e:
            self.add_message(f"【錯誤】事件註冊失敗: {str(e)}")
    
    def register_order_events(self):
        """註冊SKOrder事件 - 簡化版本"""
        try:
            # 基於官方案例的簡化事件處理
            class SKOrderEvent:
                def __init__(self, parent):
                    self.parent = parent
                
                def OnAsyncOrder(self, nThreadID, nCode, bstrMessage):
                    """非同步委託回報 - 簡化處理"""
                    try:
                        msg = f"【非同步委託】Code: {nCode}, Message: {bstrMessage}"
                        self.parent.add_message(msg)
                    except:
                        pass
                    return 0
                
                def OnAccount(self, bstrLogInID, bstrAccountData):
                    """帳號回報 - 簡化處理"""
                    try:
                        msg = f"【帳號回報】ID: {bstrLogInID}"
                        self.parent.add_message(msg)
                    except:
                        pass
                    return 0
            
            # 註冊事件
            self.order_event = SKOrderEvent(self)
            self.order_event_handler = comtypes.client.GetEvents(self.m_pSKOrder, self.order_event)
            self.add_message("【成功】SKOrder事件註冊成功")
            
        except Exception as e:
            self.add_message(f"【警告】SKOrder事件註冊失敗: {str(e)}")
    
    def register_reply_events(self):
        """註冊SKReply事件 - 基於官方案例"""
        try:
            # 完全基於官方案例的事件處理
            class SKReplyEvent:
                def __init__(self, parent):
                    self.parent = parent
                
                def OnConnect(self, bstrUserID, nErrorCode):
                    """連線事件 - 官方案例風格"""
                    try:
                        if nErrorCode == 0:
                            msg = f"【OnConnect】{bstrUserID} Connected!"
                        else:
                            msg = f"【OnConnect】{bstrUserID} Connect Error!"
                        self.parent.add_message(msg)
                    except:
                        pass
                    return 0
                
                def OnDisconnect(self, bstrUserID, nErrorCode):
                    """斷線事件 - 官方案例風格"""
                    try:
                        if nErrorCode == 3002:
                            msg = "【OnDisconnect】您已經斷線囉~~~"
                        else:
                            msg = f"【OnDisconnect】{nErrorCode}"
                        self.parent.add_message(msg)
                    except:
                        pass
                    return 0
                
                def OnComplete(self, bstrUserID):
                    """完成事件 - 官方案例風格"""
                    try:
                        self.parent.add_message("【OnComplete】回報資料載入完成")
                    except:
                        pass
                    return 0
                
                def OnNewData(self, bstrUserID, bstrData):
                    """即時回報事件 - 完全基於官方案例"""
                    try:
                        # 完全按照官方案例的處理方式
                        cutData = bstrData.split(',')
                        
                        # 解析關鍵欄位 (基於API文件)
                        if len(cutData) >= 25:
                            data_type = cutData[2] if len(cutData) > 2 else ""
                            order_err = cutData[3] if len(cutData) > 3 else ""
                            price = cutData[11] if len(cutData) > 11 else ""
                            qty = cutData[20] if len(cutData) > 20 else ""
                            
                            # 簡化顯示 (當沖需要快速)
                            type_map = {"N": "委託", "C": "取消", "D": "成交", "P": "改價"}
                            type_text = type_map.get(data_type, data_type)
                            
                            if data_type == "D":  # 成交最重要
                                msg = f"🎉【成交】價格:{price} 數量:{qty}口"
                            elif data_type == "N" and order_err == "N":
                                msg = f"✅【委託成功】價格:{price} 數量:{qty}口"
                            elif data_type == "C":
                                msg = f"🗑️【取消】價格:{price} 數量:{qty}口"
                            else:
                                msg = f"【{type_text}】價格:{price} 數量:{qty}口 狀態:{order_err}"
                            
                            self.parent.add_message(msg)
                        else:
                            # 如果欄位不足，顯示原始資料
                            self.parent.add_message(f"【OnNewData】{bstrData[:100]}...")
                            
                    except:
                        pass  # 絕對不能讓事件處理崩潰
                    return 0
                
                def OnData(self, bstrUserID, bstrData):
                    """一般回報事件 - 官方案例風格"""
                    try:
                        # 按照官方案例，OnData主要用於查詢結果
                        self.parent.add_message("【OnData】收到查詢結果")
                    except:
                        pass
                    return 0
                
                def OnReplyMessage(self, bstrUserID, bstrMessages):
                    """回報訊息事件 - 官方案例風格"""
                    try:
                        # 過濾HTML內容，避免複雜處理
                        if "<" not in bstrMessages and ">" not in bstrMessages:
                            self.parent.add_message(f"【系統訊息】{bstrMessages}")
                    except:
                        pass
                    return -1  # 官方案例返回-1
            
            # 註冊事件
            self.reply_event = SKReplyEvent(self)
            self.reply_event_handler = comtypes.client.GetEvents(self.m_pSKReply, self.reply_event)
            self.add_message("【成功】SKReply事件註冊成功")
            
        except Exception as e:
            self.add_message(f"【警告】SKReply事件註冊失敗: {str(e)}")
    
    def start_monitoring(self):
        """開始監控"""
        try:
            self.add_message("【監控】開始即時回報監控...")
            
            # 查詢帳號啟動監控
            if self.m_pSKOrder:
                nCode = self.m_pSKOrder.GetUserAccount()
                if nCode == 0:
                    self.label_status.config(text="狀態: 監控中", fg="green")
                    self.btn_start_monitor.config(state="disabled")
                    self.btn_stop_monitor.config(state="normal")
                    self.add_message("【成功】即時監控已啟動")
                else:
                    self.add_message(f"【失敗】監控啟動失敗: {nCode}")
            
        except Exception as e:
            self.add_message(f"【錯誤】啟動監控失敗: {str(e)}")
    
    def stop_monitoring(self):
        """停止監控"""
        try:
            self.label_status.config(text="狀態: 未監控", fg="red")
            self.btn_start_monitor.config(state="normal")
            self.btn_stop_monitor.config(state="disabled")
            self.add_message("【停止】監控已停止")
        except Exception as e:
            self.add_message(f"【錯誤】停止監控失敗: {str(e)}")
    
    def connect_reply_server(self):
        """連線回報主機"""
        try:
            if self.m_pSKReply:
                login_id = "E123354882"
                nCode = self.m_pSKReply.SKReplyLib_ConnectByID(login_id)
                if nCode == 0:
                    self.add_message("【成功】回報主機連線成功")
                else:
                    self.add_message(f"【失敗】回報主機連線失敗: {nCode}")
        except Exception as e:
            self.add_message(f"【錯誤】連線回報主機失敗: {str(e)}")
    
    # 兼容性方法
    def add_order_message(self, message):
        """兼容性方法"""
        self.add_message(message)
    
    def add_fill_message(self, message):
        """兼容性方法"""
        self.add_message(f"【成交】{message}")
