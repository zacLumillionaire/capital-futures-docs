#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
下單回報處理模組 - 根據官方案例
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import tkinter as tk
from tkinter import ttk
import logging
import comtypes.client

# 設定日誌
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class OrderReplyFrame(tk.Frame):
    """下單回報框架"""
    
    def __init__(self, master=None, skcom_objects=None):
        super().__init__(master)
        self.master = master
        
        # SKCOM物件
        self.m_pSKCenter = skcom_objects.get('SKCenter') if skcom_objects else None
        self.m_pSKOrder = skcom_objects.get('SKOrder') if skcom_objects else None
        self.m_pSKReply = skcom_objects.get('SKReply') if skcom_objects else None
        
        # 事件處理器
        self.order_event_handler = None
        
        # 建立UI
        self.create_widgets()
        
        # 註冊事件處理
        self.register_order_events()
    
    def create_widgets(self):
        """建立UI控件"""
        # 主框架
        main_frame = tk.LabelFrame(self, text="下單回報監控", padx=10, pady=10)
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
        
        # 清除訊息按鈕
        self.btn_clear = tk.Button(button_frame, text="清除訊息",
                                  command=self.clear_messages,
                                  bg="#4169E1", fg="white", width=12)
        self.btn_clear.grid(column=2, row=0, padx=5)

        # 重新連線回報按鈕
        self.btn_reconnect = tk.Button(button_frame, text="重新連線回報",
                                      command=self.connect_reply_server,
                                      bg="#FF8C00", fg="white", width=12)
        self.btn_reconnect.grid(column=3, row=0, padx=5)
        
        # 狀態標籤
        self.label_status = tk.Label(button_frame, text="狀態: 未監控", fg="red")
        self.label_status.grid(column=3, row=0, padx=20)
        
        # 回報訊息顯示區域
        msg_frame = tk.LabelFrame(main_frame, text="回報訊息", padx=5, pady=5)
        msg_frame.grid(column=0, row=1, columnspan=4, sticky=tk.E + tk.W, padx=5, pady=5)
        
        # 委託回報
        tk.Label(msg_frame, text="委託回報:").grid(column=0, row=0, sticky=tk.W)
        self.text_order_reply = tk.Text(msg_frame, height=6, width=80)
        scrollbar1 = tk.Scrollbar(msg_frame, orient=tk.VERTICAL, command=self.text_order_reply.yview)
        self.text_order_reply.configure(yscrollcommand=scrollbar1.set)
        self.text_order_reply.grid(column=0, row=1, sticky=tk.E + tk.W + tk.N + tk.S)
        scrollbar1.grid(column=1, row=1, sticky=tk.N + tk.S)
        
        # 成交回報
        tk.Label(msg_frame, text="成交回報:").grid(column=0, row=2, sticky=tk.W, pady=(10,0))
        self.text_fill_reply = tk.Text(msg_frame, height=6, width=80)
        scrollbar2 = tk.Scrollbar(msg_frame, orient=tk.VERTICAL, command=self.text_fill_reply.yview)
        self.text_fill_reply.configure(yscrollcommand=scrollbar2.set)
        self.text_fill_reply.grid(column=0, row=3, sticky=tk.E + tk.W + tk.N + tk.S)
        scrollbar2.grid(column=1, row=3, sticky=tk.N + tk.S)
    
    def add_order_message(self, message):
        """添加委託回報訊息"""
        self.text_order_reply.insert(tk.END, message + "\n")
        self.text_order_reply.see(tk.END)
        logger.info(f"委託回報: {message}")
    
    def add_fill_message(self, message):
        """添加成交回報訊息"""
        self.text_fill_reply.insert(tk.END, message + "\n")
        self.text_fill_reply.see(tk.END)
        logger.info(f"成交回報: {message}")
    
    def clear_messages(self):
        """清除所有訊息"""
        self.text_order_reply.delete(1.0, tk.END)
        self.text_fill_reply.delete(1.0, tk.END)
    
    def register_order_events(self):
        """註冊下單事件處理"""
        if not self.m_pSKOrder:
            self.add_order_message("【錯誤】SKOrder物件未初始化，無法註冊事件")
            return
        
        try:
            self.add_order_message("【初始化】開始註冊下單事件處理...")
            
            # 根據官方案例建立事件處理類別
            class SKOrderLibEvent():
                def __init__(self, parent):
                    self.parent = parent
                
                def OnAccount(self, bstrLogInID, bstrAccountData):
                    """帳號回報事件 - 線程安全處理"""
                    try:
                        msg = f"【帳號回報】登入ID: {bstrLogInID}, 帳號資料: {bstrAccountData}"
                        self.parent.master.after(0, self.parent.add_order_message, msg)
                    except:
                        pass  # 避免崩潰
                    return 0

                def OnAsyncOrder(self, nThreadID, nCode, bstrMessage):
                    """非同步委託回報事件 - 線程安全處理"""
                    try:
                        msg = f"【非同步委託】ThreadID: {nThreadID}, Code: {nCode}, Message: {bstrMessage}"
                        self.parent.master.after(0, self.parent.add_order_message, msg)
                    except:
                        pass  # 避免崩潰
                    return 0

                def OnRealBalanceReport(self, bstrData):
                    """即時庫存回報事件 - 線程安全處理"""
                    try:
                        msg = f"【即時庫存】{bstrData}"
                        self.parent.master.after(0, self.parent.add_order_message, msg)
                    except:
                        pass  # 避免崩潰
                    return 0

                def OnOrderReply(self, bstrData):
                    """委託回報事件 - 線程安全處理"""
                    try:
                        msg = f"【委託回報】{bstrData}"
                        self.parent.master.after(0, self.parent.add_order_message, msg)
                    except:
                        pass  # 避免崩潰
                    return 0

                def OnFillReport(self, bstrData):
                    """成交回報事件 - 線程安全處理"""
                    try:
                        msg = f"【成交回報】{bstrData}"
                        self.parent.master.after(0, self.parent.add_fill_message, msg)
                    except:
                        pass  # 避免崩潰
                    return 0

                def OnNewData(self, bstrUserID, bstrData):
                    """即時委託狀態回報事件 - 使用線程安全處理避免GIL錯誤"""
                    try:
                        # 使用after方法將處理推遲到主線程，避免GIL衝突
                        self.parent.master.after(0, self.parent.safe_parse_new_data, bstrUserID, bstrData)
                    except Exception as e:
                        # 即使發生錯誤也要安全返回，避免崩潰
                        try:
                            self.parent.master.after(0, self.parent.add_order_message, f"【錯誤】OnNewData處理失敗: {str(e)}")
                        except:
                            pass  # 如果連錯誤處理都失敗，就忽略以避免崩潰
                    return 0
            
            # 建立事件處理器
            self.order_event = SKOrderLibEvent(self)
            
            # 嘗試註冊事件
            try:
                self.order_event_handler = comtypes.client.GetEvents(self.m_pSKOrder, self.order_event)
                self.add_order_message("【成功】下單事件處理註冊成功")

                # 註冊成功後，註冊SKReply事件 (但不立即連線，等登入後再連線)
                self.register_reply_events()
                self.add_order_message("【提示】回報事件已註冊，等待登入後連線回報主機")
                return True
            except Exception as e:
                self.add_order_message(f"【警告】事件註冊失敗: {e}")
                self.add_order_message("【提示】事件處理功能可能不可用，但基本功能仍可使用")
                return False
                
        except Exception as e:
            self.add_order_message(f"【錯誤】註冊事件處理時發生錯誤: {e}")
            return False
    
    def start_monitoring(self):
        """開始監控即時回報"""
        if not self.m_pSKOrder:
            self.add_order_message("【錯誤】SKOrder物件未初始化")
            return

        try:
            self.add_order_message("【監控】開始監控即時回報...")
            self.add_order_message("【說明】OnNewData = 即時推送 | OnData = 查詢結果")

            # 根據官方文件，開始接收回報
            # 通常需要先查詢帳號
            nCode = self.m_pSKOrder.GetUserAccount()

            if self.m_pSKCenter:
                msg_text = self.m_pSKCenter.SKCenterLib_GetReturnCodeMessage(nCode)
            else:
                msg_text = f"結果代碼: {nCode}"

            self.add_order_message(f"【帳號查詢】{msg_text} (代碼: {nCode})")

            if nCode == 0:
                self.label_status.config(text="狀態: 監控中", fg="green")
                self.btn_start_monitor.config(state="disabled")
                self.btn_stop_monitor.config(state="normal")
                self.add_order_message("【成功】即時回報監控已啟動")
                self.add_order_message("【提示】即時委託/成交狀態將透過OnNewData推送")
                self.add_order_message("【提示】歷史資料請使用「部位查詢」頁籤的查詢功能")
            else:
                self.add_order_message(f"【失敗】監控啟動失敗: {msg_text}")

        except Exception as e:
            self.add_order_message(f"【錯誤】啟動監控時發生錯誤: {e}")
    
    def stop_monitoring(self):
        """停止監控"""
        try:
            self.add_order_message("【監控】停止監控下單回報...")
            
            self.label_status.config(text="狀態: 未監控", fg="red")
            self.btn_start_monitor.config(state="normal")
            self.btn_stop_monitor.config(state="disabled")
            
            self.add_order_message("【成功】監控已停止")
            
        except Exception as e:
            self.add_order_message(f"【錯誤】停止監控時發生錯誤: {e}")

    def safe_parse_new_data(self, user_id, data):
        """線程安全的OnNewData解析方法 - 避免GIL錯誤"""
        try:
            self.parse_new_data(user_id, data)
        except Exception as e:
            self.add_order_message(f"【錯誤】線程安全解析失敗: {str(e)}")

    def parse_new_data(self, user_id, data):
        """解析OnNewData回報的委託狀態資料 - 專注於關鍵欄位"""
        try:
            self.add_order_message(f"【OnNewData】收到即時回報")
            self.add_order_message(f"【OnNewData】用戶: {user_id}")

            # 顯示原始資料的前100字符用於除錯
            self.add_order_message(f"【原始資料】{data[:100]}...")

            # 解析逗號分隔的資料
            if ',' in data:
                parts = data.split(',')
                total_fields = len(parts)

                # 檢查欄位數量
                if total_fields < 25:  # 至少需要25個欄位才能解析基本資訊
                    self.add_order_message(f"【警告】OnNewData欄位數量不足: {total_fields}")
                    return

                try:
                    # 根據API文件解析關鍵欄位 (專注於重要欄位)
                    key_no = parts[0] if len(parts) > 0 else ""          # KeyNo: 13碼委託序號
                    market_type = parts[1] if len(parts) > 1 else ""     # 市場類型 (TF=期貨)
                    data_type = parts[2] if len(parts) > 2 else ""       # Type: N=委託, C=取消, U=改量, P=改價, D=成交, S=動態退單
                    order_err = parts[3] if len(parts) > 3 else ""       # OrderErr: N=正常, Y=失敗, T=逾時

                    # 價格和數量 (最重要的交易資訊)
                    price = parts[11] if len(parts) > 11 else ""         # Price: 委託價格或成交價格
                    qty = parts[20] if len(parts) > 20 else ""           # Qty: 委託量或成交量

                    # 時間資訊
                    trade_time = parts[24] if len(parts) > 24 else ""    # 交易時間 (hh:mm:ss)

                    # 序號資訊 (用於追蹤委託)
                    seq_no = parts[47] if len(parts) > 47 else key_no    # SeqNo: 新增的序號欄位，如果沒有就用KeyNo

                    # 解析委託類型和結果
                    type_text = self.get_data_type_text(data_type)
                    err_text = self.get_order_err_text(order_err)

                    # 顯示關鍵資訊 (簡化顯示)
                    self.add_order_message(f"【狀態】{type_text} | 結果:{err_text} | 價格:{price} | 數量:{qty}口")

                    if seq_no:
                        self.add_order_message(f"【序號】{seq_no}")

                    # 根據委託類型處理不同情況
                    if data_type == "N" and order_err == "N":
                        # 新委託成功
                        self.add_order_message(f"✅ 【委託成功】序號:{seq_no} 已進入市場")
                        self.notify_order_update(seq_no, "委託成功")

                    elif data_type == "N" and order_err == "Y":
                        # 委託失敗
                        self.add_order_message(f"❌ 【委託失敗】序號:{seq_no} 被拒絕")
                        self.notify_order_update(seq_no, "委託失敗")

                    elif data_type == "D":
                        # 成交回報 (最重要的事件)
                        self.add_order_message("=" * 40)
                        self.add_order_message("🎉 【成交回報】")
                        self.add_order_message(f"📋 序號: {seq_no}")
                        self.add_order_message(f"💰 成交價: {price}")
                        self.add_order_message(f"📊 成交量: {qty}口")
                        self.add_order_message(f"⏰ 時間: {trade_time}")

                        # 計算成交金額 (小台指期貨每點50元)
                        try:
                            if price and qty and price.replace('.', '').isdigit() and qty.isdigit():
                                price_float = float(price)
                                qty_int = int(qty)
                                contract_value = price_float * qty_int * 50
                                self.add_order_message(f"💵 金額: {contract_value:,.0f}元")
                        except:
                            pass

                        self.add_order_message("=" * 40)

                        # 通知其他模組
                        self.notify_trade_filled(seq_no, price, qty, trade_time, "")
                        self.notify_order_update(seq_no, "部分成交")

                    elif data_type == "C":
                        # 取消委託
                        self.add_order_message(f"🗑️ 【委託取消】序號:{seq_no}")
                        self.notify_order_update(seq_no, "已取消")

                    elif data_type == "P":
                        # 改價委託
                        self.add_order_message(f"📝 【委託改價】序號:{seq_no} 新價格:{price}")
                        self.notify_order_update(seq_no, "改價成功")

                    elif data_type == "S":
                        # 動態退單
                        self.add_order_message(f"⚠️ 【動態退單】序號:{seq_no}")
                        self.notify_order_update(seq_no, "動態退單")

                except (IndexError, ValueError) as e:
                    self.add_order_message(f"【警告】解析OnNewData欄位時發生錯誤: {e}")
                    self.add_order_message(f"【除錯】總欄位數: {total_fields}")
            else:
                self.add_order_message(f"【警告】OnNewData格式異常，無逗號分隔")

        except Exception as e:
            self.add_order_message(f"【錯誤】解析OnNewData時發生錯誤: {str(e)}")

    def get_data_type_text(self, data_type):
        """取得資料類型文字"""
        type_map = {
            "N": "新委託",
            "C": "取消單",
            "U": "改量單",
            "P": "改價單",
            "D": "成交單",
            "B": "改價改量",
            "S": "動態退單"
        }
        return type_map.get(data_type, f"類型{data_type}")

    def get_order_err_text(self, order_err):
        """取得委託結果文字"""
        err_map = {
            "N": "正常",
            "Y": "失敗",
            "T": "逾時"
        }
        return err_map.get(order_err, f"結果{order_err}")

    def notify_order_update(self, seq_no, status):
        """通知期貨下單頁面更新委託狀態"""
        try:
            # 嘗試找到期貨下單頁面並通知更新
            if hasattr(self.master, 'master') and hasattr(self.master.master, 'future_order_frame'):
                future_frame = self.master.master.future_order_frame
                if hasattr(future_frame, 'on_order_status_update'):
                    future_frame.on_order_status_update(seq_no, status)
        except Exception as e:
            self.add_order_message(f"【提示】無法通知委託狀態更新: {str(e)}")

    def notify_trade_filled(self, seq_no, price, qty, trade_time, order_no):
        """通知期貨下單頁面顯示成交回報"""
        try:
            # 嘗試找到期貨下單頁面並通知成交
            if hasattr(self.master, 'master') and hasattr(self.master.master, 'future_order_frame'):
                future_frame = self.master.master.future_order_frame
                if hasattr(future_frame, 'on_trade_filled'):
                    future_frame.on_trade_filled(seq_no, price, qty, trade_time, order_no)
        except Exception as e:
            self.add_order_message(f"【提示】無法通知成交回報: {str(e)}")

    def connect_reply_server(self):
        """連線到回報主機以接收OnNewData事件"""
        try:
            self.add_order_message("【回報連線】開始連線到回報主機...")

            if not self.m_pSKReply:
                self.add_order_message("【錯誤】SKReply物件未初始化，無法連線回報主機")
                return False

            # 使用登入ID
            login_id = "E123354882"

            try:
                # 步驟1: 確保SKReply已初始化
                self.add_order_message("【步驟1】檢查SKReply初始化狀態...")
                try:
                    nCode = self.m_pSKReply.SKReplyLib_Initialize()
                    self.add_order_message(f"【SKReply初始化】結果: {nCode}")
                except Exception as init_error:
                    self.add_order_message(f"【初始化錯誤】{str(init_error)}")
                    # 如果初始化失敗，可能是因為還沒登入，直接嘗試連線
                    self.add_order_message("【提示】初始化失敗，可能需要先登入，嘗試直接連線...")

                # 步驟2: 嘗試連線到回報主機 (根據官方案例)
                self.add_order_message("【步驟2】連線到回報主機...")
                nCode = self.m_pSKReply.SKReplyLib_ConnectByID(login_id)

                if nCode == 0:
                    self.add_order_message("【成功】回報主機連線成功！")
                    self.add_order_message("【提示】現在可以接收即時的委託和成交回報")
                    return True
                elif nCode == 1000:
                    self.add_order_message("【失敗】回報連線失敗 - 代碼1000 (連線錯誤)")
                    self.add_order_message("【分析】可能原因：網路問題、伺服器忙碌或帳號權限")

                    # 嘗試使用SKOrder的連線方法
                    self.add_order_message("【嘗試】使用SKOrder的回報連線方法...")
                    if self.m_pSKOrder:
                        try:
                            nCode2 = self.m_pSKOrder.SKOrderLib_ConnectByID(login_id)
                            self.add_order_message(f"【SKOrder連線】結果: {nCode2}")
                            if nCode2 == 0:
                                self.add_order_message("【成功】透過SKOrder連線回報主機成功")
                                return True
                        except Exception as e:
                            self.add_order_message(f"【SKOrder連線失敗】{str(e)}")

                    return False
                else:
                    self.add_order_message(f"【失敗】回報主機連線失敗，代碼: {nCode}")
                    return False

            except Exception as api_error:
                self.add_order_message(f"【API錯誤】回報連線API調用失敗: {str(api_error)}")
                return False

        except Exception as e:
            self.add_order_message(f"【錯誤】回報連線時發生錯誤: {str(e)}")
            return False

    def register_reply_events(self):
        """註冊SKReply事件處理 - 根據官方案例"""
        try:
            self.add_order_message("【SKReply事件】開始註冊SKReply事件處理...")

            if not self.m_pSKReply:
                self.add_order_message("【錯誤】SKReply物件未初始化，無法註冊事件")
                return False

            # 根據官方案例建立SKReplyLib事件處理類別
            class SKReplyLibEvent():
                def __init__(self, parent):
                    self.parent = parent

                def OnConnect(self, bstrUserID, nErrorCode):
                    """回報連線事件 - 線程安全處理"""
                    try:
                        if nErrorCode == 0:
                            msg = f"【OnConnect】{bstrUserID} 連線成功！"
                        else:
                            msg = f"【OnConnect】{bstrUserID} 連線錯誤: {nErrorCode}"
                        self.parent.master.after(0, self.parent.add_order_message, msg)
                    except:
                        pass  # 避免崩潰
                    return 0

                def OnDisconnect(self, bstrUserID, nErrorCode):
                    """回報斷線事件 - 線程安全處理"""
                    try:
                        if nErrorCode == 3002:
                            msg = "【OnDisconnect】您已經斷線囉~~~"
                        else:
                            msg = f"【OnDisconnect】斷線代碼: {nErrorCode}"
                        self.parent.master.after(0, self.parent.add_order_message, msg)
                    except:
                        pass  # 避免崩潰
                    return 0

                def OnComplete(self, bstrUserID):
                    """回報完成事件 - 線程安全處理"""
                    try:
                        msg = f"【OnComplete】{bstrUserID} 回報資料載入完成"
                        self.parent.master.after(0, self.parent.add_order_message, msg)
                    except:
                        pass  # 避免崩潰
                    return 0

                def OnNewData(self, bstrUserID, bstrData):
                    """即時回報事件 - 使用線程安全處理避免GIL錯誤"""
                    try:
                        # 使用after方法將處理推遲到主線程，避免GIL衝突
                        self.parent.master.after(0, self.parent.safe_parse_new_data, bstrUserID, bstrData)
                    except Exception as e:
                        # 即使發生錯誤也要安全返回，避免崩潰
                        try:
                            self.parent.master.after(0, self.parent.add_order_message, f"【OnNewData錯誤】{str(e)}")
                        except:
                            pass  # 如果連錯誤處理都失敗，就忽略以避免崩潰
                    return 0

                def OnData(self, bstrUserID, bstrData):
                    """一般回報事件 - 主要用於查詢結果回報 (不處理即時數據)"""
                    try:
                        # OnData主要用於查詢API的結果回報，不需要解析即時數據
                        # 即時數據由OnNewData處理
                        self.parent.master.after(0, self.parent.add_order_message, f"【OnData】收到查詢結果回報")
                        # 不調用parse_new_data，因為這通常是查詢結果，不是即時回報
                    except Exception as e:
                        try:
                            self.parent.master.after(0, self.parent.add_order_message, f"【OnData錯誤】{str(e)}")
                        except:
                            pass
                    return 0

                def OnReplyMessage(self, bstrUserID, bstrMessages):
                    """回報訊息事件 - 線程安全處理"""
                    try:
                        msg = f"【OnReplyMessage】{bstrUserID}: {bstrMessages}"
                        self.parent.master.after(0, self.parent.add_order_message, msg)
                    except:
                        pass  # 避免崩潰
                    return -1  # 根據官方案例返回-1

                def OnSolaceReplyDisconnect(self, bstrUserID, nErrorCode):
                    """Solace回報斷線事件 - 線程安全處理"""
                    try:
                        if nErrorCode == 3002:
                            msg = "【OnSolaceReplyDisconnect】SK_SUBJECT_CONNECTION_DISCONNECT"
                        else:
                            msg = f"【OnSolaceReplyDisconnect】{nErrorCode}"
                        self.parent.master.after(0, self.parent.add_order_message, msg)
                    except:
                        pass  # 避免崩潰
                    return 0

            # 建立事件處理器
            self.reply_event = SKReplyLibEvent(self)

            # 註冊SKReply事件 (根據官方案例)
            try:
                import comtypes.client
                self.reply_event_handler = comtypes.client.GetEvents(self.m_pSKReply, self.reply_event)
                self.add_order_message("【成功】SKReply事件處理註冊成功")
                return True
            except Exception as e:
                self.add_order_message(f"【錯誤】註冊SKReply事件失敗: {str(e)}")
                return False

        except Exception as e:
            self.add_order_message(f"【錯誤】建立SKReply事件處理器失敗: {str(e)}")
            return False
