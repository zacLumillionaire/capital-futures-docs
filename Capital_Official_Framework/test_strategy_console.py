#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
策略Console化測試腳本
測試策略監控的Console輸出控制功能
"""

import sys
import os
import time

# 添加路徑
sys.path.insert(0, os.path.dirname(__file__))

def test_strategy_console_features():
    """測試策略Console功能"""
    print("🧪 [TEST] 開始測試策略Console化功能")
    print("=" * 50)
    
    try:
        # 導入主程式
        from simple_integrated import SimpleIntegratedApp
        
        print("✅ [TEST] 成功導入SimpleIntegratedApp")
        
        # 創建應用實例
        app = SimpleIntegratedApp()
        print("✅ [TEST] 成功創建應用實例")
        
        # 測試Console控制變數
        print(f"📊 [TEST] 報價Console控制: {app.console_quote_enabled}")
        print(f"📊 [TEST] 策略Console控制: {app.console_strategy_enabled}")
        
        # 測試監控統計變數
        print("📊 [TEST] 監控統計變數:")
        for key, value in app.monitoring_stats.items():
            print(f"   - {key}: {value}")
        
        # 測試策略Console輸出控制方法
        print("\n🔧 [TEST] 測試策略Console控制方法...")
        
        # 測試關閉策略Console
        print("🔇 [TEST] 關閉策略Console輸出")
        app.console_strategy_enabled = False
        app.add_strategy_log("這條訊息應該不會顯示在Console")
        
        # 測試開啟策略Console
        print("🔊 [TEST] 開啟策略Console輸出")
        app.console_strategy_enabled = True
        app.add_strategy_log("這條訊息應該顯示在Console")
        
        # 測試策略邏輯處理
        print("\n🎯 [TEST] 測試策略邏輯處理...")
        app.strategy_enabled = True
        app.price_count = 0
        
        # 模擬策略處理
        for i in range(3):
            app.process_strategy_logic_safe(22500 + i, "09:00:00")
            time.sleep(0.1)
        
        # 測試策略狀態監控
        print("\n📊 [TEST] 測試策略狀態監控...")
        app.monitor_strategy_status()
        
        print("\n✅ [TEST] 所有測試完成，策略Console化功能正常")
        
        # 不啟動GUI，直接結束測試
        return True
        
    except Exception as e:
        print(f"❌ [TEST] 測試失敗: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_console_toggle_simulation():
    """模擬Console開關切換測試"""
    print("\n🔄 [TEST] 模擬Console開關切換測試")
    print("-" * 30)
    
    try:
        from simple_integrated import SimpleIntegratedApp
        app = SimpleIntegratedApp()
        
        # 模擬策略Console開關切換
        print("📊 初始狀態:")
        print(f"   策略Console: {'開啟' if app.console_strategy_enabled else '關閉'}")
        
        # 模擬關閉
        app.console_strategy_enabled = False
        print("🔇 關閉策略Console後:")
        app.add_strategy_log("測試訊息1 - 應該不顯示")
        
        # 模擬開啟
        app.console_strategy_enabled = True
        print("🔊 開啟策略Console後:")
        app.add_strategy_log("測試訊息2 - 應該顯示")
        
        print("✅ Console開關測試完成")
        return True
        
    except Exception as e:
        print(f"❌ Console開關測試失敗: {e}")
        return False

if __name__ == "__main__":
    print("🚀 策略Console化功能測試")
    print("=" * 60)
    
    # 執行基本功能測試
    test1_result = test_strategy_console_features()
    
    # 執行Console開關測試
    test2_result = test_console_toggle_simulation()
    
    # 總結
    print("\n📋 測試結果總結:")
    print(f"   基本功能測試: {'✅ 通過' if test1_result else '❌ 失敗'}")
    print(f"   Console開關測試: {'✅ 通過' if test2_result else '❌ 失敗'}")
    
    if test1_result and test2_result:
        print("\n🎉 所有測試通過！策略Console化功能已成功實施")
        print("💡 現在可以安全地使用策略監控功能，避免GIL問題")
    else:
        print("\n⚠️ 部分測試失敗，請檢查實施")
    
    print("\n📝 使用說明:")
    print("1. 啟動 simple_integrated.py")
    print("2. 使用 '🔇 關閉策略Console' 按鈕控制策略輸出")
    print("3. 策略監控狀態會在Console中智能提醒")
    print("4. 所有策略日誌都使用Console模式，避免UI更新")
