#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
策略模組修復測試
"""

import sys
import os
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def test_strategy_import():
    """測試策略模組導入"""
    print("🧪 測試策略模組導入...")
    
    # 測試完整版
    try:
        from strategy.strategy_panel import StrategyControlPanel as FullPanel
        print("✅ 完整版策略面板導入成功")
        full_available = True
    except Exception as e:
        print(f"❌ 完整版策略面板導入失敗: {e}")
        full_available = False
    
    # 測試簡化版
    try:
        from strategy.strategy_panel_simple import StrategyControlPanel as SimplePanel
        print("✅ 簡化版策略面板導入成功")
        simple_available = True
    except Exception as e:
        print(f"❌ 簡化版策略面板導入失敗: {e}")
        simple_available = False
    
    return full_available, simple_available

def test_ordertester_import():
    """測試OrderTester導入邏輯"""
    print("\n🧪 測試OrderTester導入邏輯...")
    
    try:
        # 模擬OrderTester的導入邏輯
        try:
            from strategy.strategy_panel import StrategyControlPanel
            STRATEGY_AVAILABLE = True
            STRATEGY_VERSION = "完整版"
            print("✅ OrderTester會使用完整版策略模組")
        except ImportError as e:
            try:
                from strategy.strategy_panel_simple import StrategyControlPanel
                STRATEGY_AVAILABLE = True
                STRATEGY_VERSION = "簡化版"
                print("✅ OrderTester會使用簡化版策略模組")
            except ImportError as e2:
                STRATEGY_AVAILABLE = False
                STRATEGY_VERSION = "無"
                print(f"❌ OrderTester無法載入任何策略模組: {e2}")
        
        return STRATEGY_AVAILABLE, STRATEGY_VERSION
        
    except Exception as e:
        print(f"❌ OrderTester導入邏輯測試失敗: {e}")
        return False, "錯誤"

def test_simple_panel_creation():
    """測試簡化版面板創建"""
    print("\n🧪 測試簡化版面板創建...")
    
    try:
        import tkinter as tk
        from strategy.strategy_panel_simple import StrategyControlPanel
        
        # 創建測試視窗（不顯示）
        root = tk.Tk()
        root.withdraw()
        
        # 創建策略面板
        panel = StrategyControlPanel(root)
        
        # 測試基本方法
        if hasattr(panel, 'process_price_update'):
            print("✅ process_price_update方法存在")
        
        if hasattr(panel, 'start_strategy'):
            print("✅ start_strategy方法存在")
        
        if hasattr(panel, 'stop_strategy'):
            print("✅ stop_strategy方法存在")
        
        if hasattr(panel, 'log_message'):
            print("✅ log_message方法存在")
        
        # 測試價格更新
        panel.process_price_update(22000)
        print("✅ 價格更新功能正常")
        
        # 清理
        root.destroy()
        
        return True
        
    except Exception as e:
        print(f"❌ 簡化版面板創建失敗: {e}")
        return False

def main():
    """主測試函數"""
    print("🔧 策略模組修復測試")
    print("=" * 50)
    
    # 測試1: 策略模組導入
    full_ok, simple_ok = test_strategy_import()
    
    # 測試2: OrderTester導入邏輯
    strategy_available, strategy_version = test_ordertester_import()
    
    # 測試3: 簡化版面板創建
    if simple_ok:
        panel_ok = test_simple_panel_creation()
    else:
        panel_ok = False
    
    # 總結
    print("\n" + "=" * 50)
    print("🎯 測試結果總結:")
    print(f"   完整版策略面板: {'✅ 可用' if full_ok else '❌ 不可用'}")
    print(f"   簡化版策略面板: {'✅ 可用' if simple_ok else '❌ 不可用'}")
    print(f"   OrderTester策略: {'✅ 可用' if strategy_available else '❌ 不可用'}")
    print(f"   策略版本: {strategy_version}")
    print(f"   面板創建: {'✅ 正常' if panel_ok else '❌ 異常'}")
    
    if strategy_available:
        print("\n🎉 修復成功！")
        print("💡 現在可以啟動OrderTester.py測試策略功能")
        if strategy_version == "簡化版":
            print("ℹ️ 目前使用簡化版策略面板，基本功能可用")
            print("ℹ️ 如需完整功能，請修復完整版策略模組的依賴問題")
    else:
        print("\n❌ 修復失敗！")
        print("💡 請檢查strategy資料夾和相關模組")
    
    return strategy_available

if __name__ == "__main__":
    try:
        success = main()
        sys.exit(0 if success else 1)
    except Exception as e:
        print(f"\n❌ 測試執行失敗: {e}")
        sys.exit(1)
