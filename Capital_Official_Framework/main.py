#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
群益官方框架主程式
整合四個核心服務：order_service, Quote_Service, Reply_Service, Login
"""

import os
import sys
import tkinter as tk
from tkinter import ttk, messagebox

# 確保SKCOM.dll在當前目錄
if not os.path.exists("SKCOM.dll"):
    messagebox.showerror("錯誤", "找不到SKCOM.dll檔案！\n請確認檔案在程式目錄中。")
    sys.exit(1)

class CapitalMainApp:
    """群益主應用程式"""
    
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("群益證券API - 官方框架")
        self.root.geometry("800x600")
        
        self.create_widgets()
    
    def create_widgets(self):
        """創建主介面"""
        
        # 標題
        title_label = tk.Label(self.root, text="群益證券API - 官方框架", 
                              font=("Arial", 16, "bold"))
        title_label.pack(pady=10)
        
        # 說明
        info_text = """
        本程式整合群益證券提供的四個核心服務：
        
        1. Login - 登入服務
        2. order_service - 下單服務  
        3. Quote_Service - 報價服務
        4. Reply_Service - 回報服務
        
        請選擇要啟動的服務：
        """
        
        info_label = tk.Label(self.root, text=info_text, justify=tk.LEFT)
        info_label.pack(pady=10)
        
        # 按鈕框架
        button_frame = tk.Frame(self.root)
        button_frame.pack(pady=20)
        
        # 服務按鈕
        services = [
            ("登入服務 (Login)", self.launch_login),
            ("下單服務 (Order)", self.launch_order),
            ("報價服務 (Quote)", self.launch_quote),
            ("回報服務 (Reply)", self.launch_reply)
        ]
        
        for i, (text, command) in enumerate(services):
            btn = tk.Button(button_frame, text=text, command=command,
                           width=20, height=2)
            btn.grid(row=i//2, column=i%2, padx=10, pady=5)
    
    def launch_login(self):
        """啟動登入服務"""
        try:
            os.chdir("Login")
            os.system("python LoginForm.py")
            os.chdir("..")
        except Exception as e:
            messagebox.showerror("錯誤", f"啟動登入服務失敗：{e}")
    
    def launch_order(self):
        """啟動下單服務"""
        try:
            os.chdir("order_service")
            os.system("python Order.py")
            os.chdir("..")
        except Exception as e:
            messagebox.showerror("錯誤", f"啟動下單服務失敗：{e}")
    
    def launch_quote(self):
        """啟動報價服務"""
        try:
            os.chdir("Quote_Service")
            os.system("python Quote.py")
            os.chdir("..")
        except Exception as e:
            messagebox.showerror("錯誤", f"啟動報價服務失敗：{e}")
    
    def launch_reply(self):
        """啟動回報服務"""
        try:
            os.chdir("Reply_Service")
            os.system("python Reply.py")
            os.chdir("..")
        except Exception as e:
            messagebox.showerror("錯誤", f"啟動回報服務失敗：{e}")
    
    def run(self):
        """執行主程式"""
        self.root.mainloop()

if __name__ == "__main__":
    app = CapitalMainApp()
    app.run()
