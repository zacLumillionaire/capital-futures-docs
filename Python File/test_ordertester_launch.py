#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
OrderTester啟動測試
檢查OrderTester.py是否能正常啟動
"""

import sys
import os
import subprocess
import time

def test_strategy_imports():
    """測試策略模組導入"""
    print("🧪 測試策略模組導入...")
    
    # 測試最簡化版
    try:
        import tkinter as tk
        from strategy.strategy_panel_minimal import StrategyControlPanel
        
        # 創建測試視窗（不顯示）
        root = tk.Tk()
        root.withdraw()
        
        # 創建面板
        panel = StrategyControlPanel(root)
        
        # 測試基本方法
        panel.process_price_update(22000)
        
        # 清理
        root.destroy()
        
        print("✅ 最簡化版策略面板測試成功")
        return True
        
    except Exception as e:
        print(f"❌ 最簡化版策略面板測試失敗: {e}")
        return False

def test_ordertester_import():
    """測試OrderTester導入邏輯"""
    print("\n🧪 測試OrderTester導入邏輯...")
    
    try:
        # 模擬OrderTester的導入邏輯
        try:
            from strategy.strategy_panel import StrategyControlPanel
            version = "完整版"
        except ImportError:
            try:
                from strategy.strategy_panel_simple import StrategyControlPanel
                version = "簡化版"
            except ImportError:
                try:
                    from strategy.strategy_panel_minimal import StrategyControlPanel
                    version = "最簡化版"
                except ImportError:
                    version = "無"
        
        print(f"✅ OrderTester會使用: {version}")
        return version != "無"
        
    except Exception as e:
        print(f"❌ OrderTester導入邏輯測試失敗: {e}")
        return False

def launch_ordertester():
    """啟動OrderTester"""
    print("\n🚀 啟動OrderTester.py...")
    
    try:
        # 使用subprocess啟動OrderTester
        process = subprocess.Popen(
            [sys.executable, "OrderTester.py"],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            cwd=os.getcwd()
        )
        
        # 等待一段時間看是否有輸出
        time.sleep(3)
        
        # 檢查進程狀態
        if process.poll() is None:
            print("✅ OrderTester.py 正在運行")
            print("💡 請檢查是否有GUI視窗打開")
            
            # 終止進程
            process.terminate()
            process.wait()
            return True
        else:
            # 進程已結束，檢查錯誤
            stdout, stderr = process.communicate()
            print(f"❌ OrderTester.py 啟動失敗")
            if stdout:
                print(f"標準輸出: {stdout}")
            if stderr:
                print(f"錯誤輸出: {stderr}")
            return False
            
    except Exception as e:
        print(f"❌ 啟動OrderTester失敗: {e}")
        return False

def main():
    """主測試函數"""
    print("🔧 OrderTester啟動診斷測試")
    print("=" * 50)
    
    # 檢查當前目錄
    print(f"當前目錄: {os.getcwd()}")
    print(f"OrderTester.py存在: {os.path.exists('OrderTester.py')}")
    
    # 測試1: 策略模組導入
    strategy_ok = test_strategy_imports()
    
    # 測試2: OrderTester導入邏輯
    import_ok = test_ordertester_import()
    
    # 測試3: 啟動OrderTester
    if strategy_ok and import_ok:
        launch_ok = launch_ordertester()
    else:
        launch_ok = False
        print("\n⚠️ 跳過OrderTester啟動測試（前置測試失敗）")
    
    # 總結
    print("\n" + "=" * 50)
    print("🎯 診斷結果:")
    print(f"   策略模組: {'✅ 正常' if strategy_ok else '❌ 異常'}")
    print(f"   導入邏輯: {'✅ 正常' if import_ok else '❌ 異常'}")
    print(f"   程式啟動: {'✅ 正常' if launch_ok else '❌ 異常'}")
    
    if strategy_ok and import_ok and launch_ok:
        print("\n🎉 OrderTester.py 應該可以正常啟動！")
        print("💡 請直接執行: python OrderTester.py")
    else:
        print("\n❌ OrderTester.py 啟動有問題")
        print("💡 請檢查上述錯誤訊息")
    
    return strategy_ok and import_ok

if __name__ == "__main__":
    try:
        success = main()
        input("\n按Enter鍵結束...")
        sys.exit(0 if success else 1)
    except Exception as e:
        print(f"\n❌ 測試執行失敗: {e}")
        input("按Enter鍵結束...")
        sys.exit(1)
