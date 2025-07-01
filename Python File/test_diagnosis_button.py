#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
測試診斷按鈕功能
"""

import tkinter as tk
import sys
import os

def test_diagnosis_ui():
    """測試診斷界面"""
    print("測試診斷界面...")
    
    # 創建測試視窗
    root = tk.Tk()
    root.title("策略診斷測試")
    root.geometry("800x600")
    
    # 模擬錯誤頁面
    main_frame = tk.Frame(root)
    main_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=20)
    
    # 錯誤標題
    error_label = tk.Label(main_frame, 
                          text="策略模組載入失敗",
                          fg="red", font=("Arial", 14, "bold"))
    error_label.pack(pady=(0, 10))
    
    # 說明文字
    info_label = tk.Label(main_frame, 
                         text="請點擊下方診斷按鈕來查看詳細錯誤資訊",
                         font=("Arial", 10))
    info_label.pack(pady=(0, 20))
    
    # 診斷按鈕
    def run_diagnosis():
        """運行診斷"""
        log_text.delete(1.0, tk.END)
        add_log("開始策略模組診斷...")
        add_log("=" * 50)
        
        # 檢查基本環境
        add_log("1. 檢查基本環境:")
        add_log(f"   Python版本: {sys.version}")
        add_log(f"   當前目錄: {os.getcwd()}")
        
        # 檢查strategy資料夾
        add_log("\n2. 檢查strategy資料夾:")
        strategy_path = "strategy"
        if os.path.exists(strategy_path):
            add_log(f"   ✓ strategy資料夾存在")
            try:
                files = os.listdir(strategy_path)
                add_log(f"   strategy資料夾內容: {files}")
            except Exception as e:
                add_log(f"   ✗ 無法讀取strategy資料夾: {e}")
        else:
            add_log(f"   ✗ strategy資料夾不存在")
        
        # 測試策略模組導入
        add_log("\n3. 測試策略模組導入:")
        
        modules_to_test = [
            ("完整版策略面板", "strategy.strategy_panel", "StrategyControlPanel"),
            ("簡化版策略面板", "strategy.strategy_panel_simple", "StrategyControlPanel"),
            ("最簡化版策略面板", "strategy.strategy_panel_minimal", "StrategyControlPanel"),
        ]
        
        for name, module_name, class_name in modules_to_test:
            add_log(f"   測試{name}...")
            try:
                module = __import__(module_name, fromlist=[class_name])
                cls = getattr(module, class_name)
                add_log(f"   ✓ {name}導入成功")
            except Exception as e:
                add_log(f"   ✗ {name}導入失敗: {e}")
                add_log(f"   詳細錯誤: {type(e).__name__}: {str(e)}")
        
        # 檢查依賴模組
        add_log("\n4. 檢查依賴模組:")
        dependencies = [
            ("tkinter", "tkinter"),
            ("資料庫管理", "database.sqlite_manager"),
            ("時間工具", "utils.time_utils"),
            ("策略配置", "strategy.strategy_config"),
            ("信號檢測", "strategy.signal_detector"),
        ]
        
        for name, module in dependencies:
            try:
                __import__(module)
                add_log(f"   ✓ {name}: 可用")
            except Exception as e:
                add_log(f"   ✗ {name}: 失敗 - {e}")
        
        add_log("\n診斷完成！")
    
    def add_log(message):
        """添加日誌"""
        from datetime import datetime
        timestamp = datetime.now().strftime("%H:%M:%S")
        log_entry = f"[{timestamp}] {message}\n"
        log_text.insert(tk.END, log_entry)
        log_text.see(tk.END)
        print(f"診斷日誌: {message}")  # 同時輸出到終端
    
    diagnose_button = tk.Button(main_frame, 
                               text="🔍 開始診斷策略模組問題",
                               command=run_diagnosis,
                               bg="#4CAF50", fg="white",
                               font=("Arial", 12, "bold"),
                               padx=20, pady=10)
    diagnose_button.pack(pady=(0, 20))
    
    # 日誌顯示區域
    log_frame = tk.LabelFrame(main_frame, text="診斷日誌", font=("Arial", 10, "bold"))
    log_frame.pack(fill=tk.BOTH, expand=True)
    
    # 日誌文本框
    log_text = tk.Text(log_frame, height=15, wrap=tk.WORD, 
                       font=("Consolas", 9))
    log_text.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=5, pady=5)
    
    # 滾動條
    scrollbar = tk.Scrollbar(log_frame, orient=tk.VERTICAL, 
                            command=log_text.yview)
    scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
    log_text.config(yscrollcommand=scrollbar.set)
    
    # 初始訊息
    add_log("策略模組診斷系統已準備就緒")
    add_log("點擊診斷按鈕開始詳細檢查...")
    
    print("診斷界面已創建，請點擊診斷按鈕測試功能")
    root.mainloop()

if __name__ == "__main__":
    test_diagnosis_ui()
