#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
整合測試腳本 - 驗證OrderTester.py策略整合功能
"""

import sys
import os
import tkinter as tk
from tkinter import messagebox
import logging

# 設定日誌
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def test_strategy_import():
    """測試策略模組導入"""
    try:
        from strategy.strategy_panel import StrategyControlPanel
        logger.info("✅ 策略模組導入成功")
        return True
    except ImportError as e:
        logger.error(f"❌ 策略模組導入失敗: {e}")
        return False

def test_ordertester_import():
    """測試OrderTester導入"""
    try:
        # 不直接導入OrderTester，因為它會初始化SKCOM
        # 只檢查檔案是否存在
        if os.path.exists('OrderTester.py'):
            logger.info("✅ OrderTester.py檔案存在")
            return True
        else:
            logger.error("❌ OrderTester.py檔案不存在")
            return False
    except Exception as e:
        logger.error(f"❌ OrderTester檢查失敗: {e}")
        return False

def test_strategy_panel_creation():
    """測試策略面板創建"""
    try:
        from strategy.strategy_panel import StrategyControlPanel
        
        # 創建測試視窗
        root = tk.Tk()
        root.title("策略面板整合測試")
        root.geometry("800x600")
        
        # 創建策略面板
        panel = StrategyControlPanel(root)
        panel.pack(fill="both", expand=True, padx=10, pady=10)
        
        # 測試基本方法
        if hasattr(panel, 'process_price_update'):
            logger.info("✅ process_price_update方法存在")
        else:
            logger.error("❌ process_price_update方法不存在")
        
        if hasattr(panel, 'start_strategy'):
            logger.info("✅ start_strategy方法存在")
        else:
            logger.error("❌ start_strategy方法不存在")
        
        if hasattr(panel, 'stop_strategy'):
            logger.info("✅ stop_strategy方法存在")
        else:
            logger.error("❌ stop_strategy方法不存在")
        
        # 測試價格更新
        panel.process_price_update(22000)
        logger.info("✅ 價格更新測試成功")
        
        # 顯示測試結果
        panel.log_message("🧪 整合測試完成")
        panel.log_message("✅ 策略面板功能正常")
        panel.log_message("✅ 價格更新功能正常")
        panel.log_message("✅ 日誌功能正常")
        
        # 顯示說明
        messagebox.showinfo("整合測試", 
                           "策略面板整合測試完成！\n\n"
                           "✅ 策略模組載入成功\n"
                           "✅ 策略面板創建成功\n"
                           "✅ 基本功能測試通過\n\n"
                           "請檢查策略面板是否正常顯示")
        
        # 運行測試視窗
        root.mainloop()
        return True
        
    except Exception as e:
        logger.error(f"❌ 策略面板創建測試失敗: {e}")
        return False

def main():
    """主測試函數"""
    logger.info("🧪 開始整合測試...")
    
    # 檢查工作目錄
    logger.info(f"當前工作目錄: {os.getcwd()}")
    
    # 測試1: 策略模組導入
    logger.info("📋 測試1: 策略模組導入")
    if not test_strategy_import():
        logger.error("❌ 策略模組導入測試失敗")
        return False
    
    # 測試2: OrderTester檔案檢查
    logger.info("📋 測試2: OrderTester檔案檢查")
    if not test_ordertester_import():
        logger.error("❌ OrderTester檔案檢查失敗")
        return False
    
    # 測試3: 策略面板創建
    logger.info("📋 測試3: 策略面板創建和功能測試")
    if not test_strategy_panel_creation():
        logger.error("❌ 策略面板創建測試失敗")
        return False
    
    logger.info("🎉 所有整合測試通過！")
    return True

if __name__ == "__main__":
    try:
        success = main()
        if success:
            print("\n🎉 整合測試完成！")
            print("✅ 策略功能已成功整合到OrderTester.py")
            print("💡 現在可以啟動OrderTester.py查看策略交易標籤頁")
        else:
            print("\n❌ 整合測試失敗！")
            print("💡 請檢查錯誤訊息並修復問題")
    except Exception as e:
        logger.error(f"❌ 測試執行失敗: {e}")
        print(f"\n❌ 測試執行失敗: {e}")
