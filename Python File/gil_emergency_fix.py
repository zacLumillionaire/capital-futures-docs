#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
GIL錯誤緊急修正方案
暫時禁用所有COM事件處理，確保程式穩定運行
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

import tkinter as tk
from tkinter import ttk
import logging

# 設定日誌
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def apply_emergency_gil_fix():
    """應用緊急GIL修正方案"""
    print("🚨 應用緊急GIL錯誤修正方案")
    print("=" * 60)
    
    # 修正方案1: 完全禁用事件處理
    print("📋 修正方案1: 禁用COM事件處理")
    print("   - 暫時註釋所有GetEvents調用")
    print("   - 保留基本功能: 登入、下單、查詢")
    print("   - 移除即時回報功能")
    
    # 修正方案2: 簡化事件處理
    print("\n📋 修正方案2: 簡化事件處理")
    print("   - 只保留最基本的事件")
    print("   - 移除複雜的字符串處理")
    print("   - 使用最簡單的返回值")
    
    # 修正方案3: 輪詢替代事件
    print("\n📋 修正方案3: 輪詢替代即時事件")
    print("   - 使用定時查詢替代即時回報")
    print("   - 每5秒查詢一次委託狀態")
    print("   - 避免COM事件的GIL問題")
    
    print("\n" + "=" * 60)
    print("🎯 建議實施順序:")
    print("1. 先試用方案1 (完全禁用事件)")
    print("2. 確認基本功能正常後")
    print("3. 再考慮方案3 (輪詢替代)")
    
def create_no_events_reply_module():
    """創建無事件版本的回報模組"""
    
    no_events_code = '''#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
無事件版本的回報處理模組 - 避免GIL錯誤
"""

import tkinter as tk
from tkinter import ttk
import logging

logger = logging.getLogger(__name__)

class OrderReplyFrame(tk.Frame):
    """無事件版本的下單回報框架"""
    
    def __init__(self, master=None, skcom_objects=None):
        super().__init__(master)
        self.master = master
        
        # SKCOM物件
        self.m_pSKCenter = skcom_objects.get('SKCenter') if skcom_objects else None
        self.m_pSKOrder = skcom_objects.get('SKOrder') if skcom_objects else None
        self.m_pSKReply = skcom_objects.get('SKReply') if skcom_objects else None
        
        # 建立UI
        self.create_widgets()
        
        # 不註冊任何事件處理，避免GIL錯誤
        self.add_order_message("【安全模式】已禁用COM事件處理，避免GIL錯誤")
        self.add_order_message("【提示】請使用查詢功能獲取委託狀態")
    
    def create_widgets(self):
        """建立UI控件"""
        # 主框架
        main_frame = tk.LabelFrame(self, text="下單回報監控 (安全模式)", padx=10, pady=10)
        main_frame.grid(column=0, row=0, columnspan=4, sticky=tk.E + tk.W, padx=5, pady=5)
        
        # 控制按鈕
        button_frame = tk.Frame(main_frame)
        button_frame.grid(column=0, row=0, columnspan=4, pady=5)
        
        # 查詢委託狀態按鈕 (替代即時監控)
        self.btn_query_status = tk.Button(button_frame, text="查詢委託狀態", 
                                         command=self.query_order_status,
                                         bg="#228B22", fg="white", width=12)
        self.btn_query_status.grid(column=0, row=0, padx=5)
        
        # 清除訊息按鈕
        self.btn_clear = tk.Button(button_frame, text="清除訊息",
                                  command=self.clear_messages,
                                  bg="#4169E1", fg="white", width=12)
        self.btn_clear.grid(column=1, row=0, padx=5)
        
        # 狀態標籤
        self.label_status = tk.Label(button_frame, text="狀態: 安全模式 (無事件)", fg="green")
        self.label_status.grid(column=2, row=0, padx=20)
        
        # 回報訊息顯示區域
        msg_frame = tk.LabelFrame(main_frame, text="委託狀態查詢", padx=5, pady=5)
        msg_frame.grid(column=0, row=1, columnspan=4, sticky=tk.E + tk.W, padx=5, pady=5)
        
        # 委託狀態顯示
        self.text_order_reply = tk.Text(msg_frame, height=15, width=80)
        scrollbar1 = tk.Scrollbar(msg_frame, orient=tk.VERTICAL, command=self.text_order_reply.yview)
        self.text_order_reply.configure(yscrollcommand=scrollbar1.set)
        self.text_order_reply.grid(column=0, row=0, sticky=tk.E + tk.W + tk.N + tk.S)
        scrollbar1.grid(column=1, row=0, sticky=tk.N + tk.S)
    
    def add_order_message(self, message):
        """添加委託狀態訊息"""
        self.text_order_reply.insert(tk.END, message + "\\n")
        self.text_order_reply.see(tk.END)
        logger.info(f"委託狀態: {message}")
    
    def clear_messages(self):
        """清除所有訊息"""
        self.text_order_reply.delete(1.0, tk.END)
        self.add_order_message("【清除】訊息已清除")
    
    def query_order_status(self):
        """查詢委託狀態 (替代即時監控)"""
        if not self.m_pSKOrder:
            self.add_order_message("【錯誤】SKOrder物件未初始化")
            return
        
        try:
            self.add_order_message("【查詢】開始查詢委託狀態...")
            
            # 使用GetOrderReport查詢最近委託
            login_id = "E123354882"
            account = "F0200006363839"
            format_type = 1  # 全部委託
            
            bstrResult = self.m_pSKOrder.GetOrderReport(login_id, account, format_type)
            
            if bstrResult:
                self.add_order_message("【成功】委託狀態查詢完成")
                # 簡單顯示結果
                lines = bstrResult.split('\\n')
                count = 0
                for line in lines:
                    if line.strip() and line.startswith('TF,'):
                        count += 1
                        if count <= 5:  # 只顯示最近5筆
                            parts = line.split(',')
                            if len(parts) >= 15:
                                order_no = parts[8] if len(parts) > 8 else ""
                                product = parts[15] if len(parts) > 15 else ""
                                status = parts[10] if len(parts) > 10 else ""
                                self.add_order_message(f"【委託】{order_no} {product} 狀態:{status}")
                
                self.add_order_message(f"【統計】共找到 {count} 筆委託記錄")
            else:
                self.add_order_message("【結果】查無委託記錄")
                
        except Exception as e:
            self.add_order_message(f"【錯誤】查詢委託狀態失敗: {str(e)}")
'''
    
    # 寫入檔案
    with open('Python File/reply/order_reply_no_events.py', 'w', encoding='utf-8') as f:
        f.write(no_events_code)
    
    print("✅ 已創建無事件版本: reply/order_reply_no_events.py")

def main():
    """主函數"""
    print("🛠️ GIL錯誤緊急修正工具")
    print("=" * 60)
    
    apply_emergency_gil_fix()
    
    print("\n🔧 創建修正檔案...")
    create_no_events_reply_module()
    
    print("\n" + "=" * 60)
    print("🎯 使用說明:")
    print("1. 備份原始檔案:")
    print("   cp reply/order_reply.py reply/order_reply_backup.py")
    print("")
    print("2. 使用無事件版本:")
    print("   cp reply/order_reply_no_events.py reply/order_reply.py")
    print("")
    print("3. 重新啟動程式:")
    print("   python OrderTester.py")
    print("")
    print("4. 測試基本功能:")
    print("   - 登入")
    print("   - 下單")
    print("   - 查詢委託狀態 (替代即時監控)")
    print("")
    print("5. 如果穩定運行，說明GIL問題已解決")
    
    print("\n🎉 緊急修正方案準備完成！")

if __name__ == "__main__":
    main()
