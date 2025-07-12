#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
複製群益官方框架到新資料夾
"""

import os
import shutil
import sys

def copy_capital_framework():
    """複製群益官方框架"""
    
    # 目標資料夾
    target_dir = "Capital_Official_Framework"
    
    # 創建目標資料夾
    if os.path.exists(target_dir):
        print(f"⚠️ 目標資料夾 {target_dir} 已存在，將先刪除...")
        shutil.rmtree(target_dir)
    
    os.makedirs(target_dir)
    print(f"✅ 創建目標資料夾: {target_dir}")
    
    # 要複製的服務資料夾
    services = [
        "order_service",
        "Quote_Service", 
        "Reply_Service",
        "Login"
    ]
    
    # 複製各個服務資料夾
    for service in services:
        if os.path.exists(service):
            target_service_dir = os.path.join(target_dir, service)
            shutil.copytree(service, target_service_dir)
            print(f"✅ 複製服務: {service} -> {target_service_dir}")
        else:
            print(f"❌ 找不到服務資料夾: {service}")
    
    # 複製SKCOM.dll (從Python File資料夾)
    skcom_source = os.path.join("Python File", "SKCOM.dll")
    if os.path.exists(skcom_source):
        # 複製到每個服務資料夾
        for service in services:
            target_service_dir = os.path.join(target_dir, service)
            if os.path.exists(target_service_dir):
                skcom_target = os.path.join(target_service_dir, "SKCOM.dll")
                shutil.copy2(skcom_source, skcom_target)
                print(f"✅ 複製SKCOM.dll到: {skcom_target}")
        
        # 也複製到根目錄
        skcom_root_target = os.path.join(target_dir, "SKCOM.dll")
        shutil.copy2(skcom_source, skcom_root_target)
        print(f"✅ 複製SKCOM.dll到根目錄: {skcom_root_target}")
    else:
        print(f"❌ 找不到SKCOM.dll: {skcom_source}")
    
    # 複製其他必要的DLL檔案
    dll_files = [
        "SKProxyLIB.dll",
        "SKTradeLib.dll", 
        "SKWebCALib.dll",
        "Interop.SKCOMLib.dll",
        "CTSecuritiesATL.dll",
        "SecuCompx64.dll",
        "libsolclient_64.dll"
    ]
    
    for dll_file in dll_files:
        dll_source = os.path.join("Python File", dll_file)
        if os.path.exists(dll_source):
            dll_target = os.path.join(target_dir, dll_file)
            shutil.copy2(dll_source, dll_target)
            print(f"✅ 複製DLL: {dll_file}")
        else:
            print(f"⚠️ 找不到DLL: {dll_file}")
    
    # 創建主程式入口
    create_main_entry(target_dir)
    
    print(f"\n🎉 群益官方框架複製完成！")
    print(f"📁 目標資料夾: {target_dir}")
    print(f"📋 包含服務: {', '.join(services)}")
    print(f"🔧 已包含SKCOM.dll和相關DLL檔案")

def create_main_entry(target_dir):
    """創建主程式入口"""
    main_content = '''#!/usr/bin/env python3
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
    messagebox.showerror("錯誤", "找不到SKCOM.dll檔案！\\n請確認檔案在程式目錄中。")
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
'''
    
    main_file = os.path.join(target_dir, "main.py")
    with open(main_file, 'w', encoding='utf-8') as f:
        f.write(main_content)
    
    print(f"✅ 創建主程式入口: {main_file}")

if __name__ == "__main__":
    copy_capital_framework()
