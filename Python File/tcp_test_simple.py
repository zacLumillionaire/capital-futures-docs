#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
簡化TCP測試
測試修復後的TCP連接功能

🏷️ TCP_TEST_SIMPLE_2025_07_01
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

import tkinter as tk
from tkinter import ttk, messagebox
import time
import threading

# 導入TCP模組
try:
    from tcp_price_server import PriceClient
    TCP_AVAILABLE = True
    print("✅ TCP模組載入成功")
except ImportError as e:
    TCP_AVAILABLE = False
    print(f"❌ TCP模組載入失敗: {e}")

class SimpleTCPTest:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("簡化TCP測試")
        self.root.geometry("600x400")
        
        # TCP相關
        self.tcp_client = None
        self.tcp_connected = False
        
        self.create_widgets()
        
    def create_widgets(self):
        # 標題
        title = tk.Label(self.root, text="TCP連接測試", font=("Arial", 16, "bold"))
        title.pack(pady=10)
        
        # 狀態顯示
        self.status_var = tk.StringVar(value="未連接")
        status_label = tk.Label(self.root, textvariable=self.status_var, font=("Arial", 12))
        status_label.pack(pady=5)
        
        # 按鈕區域
        btn_frame = tk.Frame(self.root)
        btn_frame.pack(pady=10)
        
        # 檢查伺服器按鈕
        self.btn_check = tk.Button(btn_frame, text="檢查TCP伺服器", command=self.check_server,
                                  bg="blue", fg="white", width=15)
        self.btn_check.pack(side="left", padx=5)
        
        # 連接按鈕
        self.btn_connect = tk.Button(btn_frame, text="連接TCP", command=self.connect_tcp,
                                    bg="green", fg="white", width=15)
        self.btn_connect.pack(side="left", padx=5)
        
        # 斷開按鈕
        self.btn_disconnect = tk.Button(btn_frame, text="斷開連接", command=self.disconnect_tcp,
                                       bg="red", fg="white", width=15, state="disabled")
        self.btn_disconnect.pack(side="left", padx=5)
        
        # 日誌區域
        log_frame = tk.LabelFrame(self.root, text="日誌", padx=5, pady=5)
        log_frame.pack(fill="both", expand=True, padx=10, pady=10)
        
        self.log_text = tk.Text(log_frame, height=15, font=("Consolas", 9))
        scrollbar = tk.Scrollbar(log_frame, orient="vertical", command=self.log_text.yview)
        self.log_text.configure(yscrollcommand=scrollbar.set)
        
        self.log_text.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
        
        # 清除按鈕
        clear_btn = tk.Button(self.root, text="清除日誌", command=self.clear_log)
        clear_btn.pack(pady=5)
        
    def log_message(self, message):
        """添加日誌訊息"""
        from datetime import datetime
        timestamp = datetime.now().strftime("[%H:%M:%S]")
        full_message = f"{timestamp} {message}\n"
        
        self.log_text.insert(tk.END, full_message)
        self.log_text.see(tk.END)
        print(full_message.strip())  # 同時輸出到控制台
        
    def clear_log(self):
        """清除日誌"""
        self.log_text.delete(1.0, tk.END)
        
    def check_server(self):
        """檢查TCP伺服器狀態"""
        self.log_message("🔍 檢查TCP伺服器狀態...")
        
        import socket
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(2.0)
            result = sock.connect_ex(('localhost', 8888))
            sock.close()
            
            if result == 0:
                self.log_message("✅ TCP伺服器運行中 (localhost:8888)")
                self.status_var.set("伺服器運行中")
                return True
            else:
                self.log_message("❌ TCP伺服器未運行")
                self.log_message("💡 請啟動OrderTester並勾選TCP伺服器")
                self.status_var.set("伺服器未運行")
                return False
                
        except Exception as e:
            self.log_message(f"❌ 檢查失敗: {e}")
            self.status_var.set("檢查失敗")
            return False
            
    def connect_tcp(self):
        """連接TCP"""
        if not TCP_AVAILABLE:
            messagebox.showerror("錯誤", "TCP模組未載入")
            return
            
        if self.tcp_connected:
            self.log_message("⚠️ 已經連接")
            return
            
        self.log_message("🔗 開始TCP連接...")
        
        # 先檢查伺服器
        if not self.check_server():
            return
            
        try:
            # 建立客戶端
            self.tcp_client = PriceClient()
            
            # 設定回調
            def price_callback(price_data):
                try:
                    price = price_data.get('price', 0)
                    timestamp = price_data.get('timestamp', '')
                    source = price_data.get('source', '')
                    
                    self.root.after(0, lambda: self.log_message(
                        f"📥 收到價格: {price} (時間: {timestamp}, 來源: {source})"
                    ))
                    
                except Exception as e:
                    self.root.after(0, lambda: self.log_message(f"❌ 處理價格失敗: {e}"))
                    
            self.tcp_client.set_price_callback(price_callback)
            
            # 嘗試連接
            if self.tcp_client.connect():
                self.tcp_connected = True
                self.status_var.set("TCP已連接")
                self.log_message("✅ TCP連接成功")
                self.log_message("⏳ 等待接收價格數據...")
                
                # 更新按鈕狀態
                self.btn_connect.config(state="disabled")
                self.btn_disconnect.config(state="normal")
                
            else:
                self.log_message("❌ TCP連接失敗")
                self.status_var.set("連接失敗")
                
        except Exception as e:
            self.log_message(f"❌ TCP連接異常: {e}")
            self.status_var.set("連接異常")
            
    def disconnect_tcp(self):
        """斷開TCP連接"""
        if not self.tcp_connected:
            self.log_message("⚠️ 未連接")
            return
            
        try:
            if self.tcp_client:
                self.tcp_client.disconnect()
                self.tcp_client = None
                
            self.tcp_connected = False
            self.status_var.set("已斷開")
            self.log_message("🔌 TCP連接已斷開")
            
            # 更新按鈕狀態
            self.btn_connect.config(state="normal")
            self.btn_disconnect.config(state="disabled")
            
        except Exception as e:
            self.log_message(f"❌ 斷開連接失敗: {e}")
            
    def run(self):
        """運行測試"""
        self.log_message("🚀 簡化TCP測試已啟動")
        self.log_message("📋 使用說明:")
        self.log_message("   1. 先啟動OrderTester.py")
        self.log_message("   2. 勾選「☑️ 啟用TCP價格伺服器」")
        self.log_message("   3. 點擊「檢查TCP伺服器」")
        self.log_message("   4. 點擊「連接TCP」")
        
        self.root.mainloop()

if __name__ == "__main__":
    app = SimpleTCPTest()
    app.run()
