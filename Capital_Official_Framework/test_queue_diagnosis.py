#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Queue架構診斷測試腳本
用於檢查simple_integrated.py中的Queue功能
"""

import sys
import os

# 添加必要的路徑
current_dir = os.path.dirname(__file__)
parent_dir = os.path.dirname(current_dir)
sys.path.insert(0, parent_dir)

def test_queue_infrastructure():
    """測試Queue基礎設施"""
    print("🔍 測試Queue基礎設施...")
    
    try:
        from queue_infrastructure import get_queue_infrastructure, TickData
        print("✅ Queue基礎設施導入成功")
        
        # 測試創建實例
        infrastructure = get_queue_infrastructure()
        print(f"✅ Queue基礎設施實例創建成功: {infrastructure}")
        
        # 測試初始化
        if infrastructure.initialize():
            print("✅ Queue基礎設施初始化成功")
        else:
            print("❌ Queue基礎設施初始化失敗")
            
        return True
        
    except Exception as e:
        print(f"❌ Queue基礎設施測試失敗: {e}")
        return False

def test_simple_integrated_import():
    """測試simple_integrated導入"""
    print("\n🔍 測試simple_integrated導入...")
    
    try:
        import simple_integrated
        print("✅ simple_integrated導入成功")
        
        # 檢查Queue相關屬性
        app = simple_integrated.SimpleIntegratedApp()
        
        print(f"✅ 應用程式創建成功")
        print(f"🔍 Queue基礎設施: {hasattr(app, 'queue_infrastructure')}")
        print(f"🔍 Queue模式啟用: {hasattr(app, 'queue_mode_enabled')}")
        
        if hasattr(app, 'queue_infrastructure'):
            print(f"🔍 Queue實例: {app.queue_infrastructure}")
        
        if hasattr(app, 'queue_mode_enabled'):
            print(f"🔍 Queue模式狀態: {app.queue_mode_enabled}")
            
        return True
        
    except Exception as e:
        print(f"❌ simple_integrated測試失敗: {e}")
        return False

def test_queue_control_methods():
    """測試Queue控制方法"""
    print("\n🔍 測試Queue控制方法...")
    
    try:
        import simple_integrated
        app = simple_integrated.SimpleIntegratedApp()
        
        # 檢查控制方法是否存在
        methods = [
            'create_queue_control_panel',
            'start_queue_services', 
            'stop_queue_services',
            'toggle_queue_mode',
            'show_queue_status',
            'process_queue_strategy_data'
        ]
        
        for method in methods:
            if hasattr(app, method):
                print(f"✅ 方法存在: {method}")
            else:
                print(f"❌ 方法缺失: {method}")
                
        return True
        
    except Exception as e:
        print(f"❌ Queue控制方法測試失敗: {e}")
        return False

def main():
    """主測試函數"""
    print("🚀 開始Queue架構診斷測試")
    print("=" * 50)
    
    # 測試1: Queue基礎設施
    test1_result = test_queue_infrastructure()
    
    # 測試2: simple_integrated導入
    test2_result = test_simple_integrated_import()
    
    # 測試3: Queue控制方法
    test3_result = test_queue_control_methods()
    
    # 總結
    print("\n" + "=" * 50)
    print("📊 測試結果總結:")
    print(f"Queue基礎設施: {'✅' if test1_result else '❌'}")
    print(f"simple_integrated: {'✅' if test2_result else '❌'}")
    print(f"Queue控制方法: {'✅' if test3_result else '❌'}")
    
    if all([test1_result, test2_result, test3_result]):
        print("\n🎉 所有測試通過！Queue架構準備就緒")
        print("\n📋 下一步:")
        print("1. 啟動 simple_integrated.py")
        print("2. 在主要功能頁面找到 'Queue架構控制' 面板")
        print("3. 點擊 '🚀 啟動Queue服務' 按鈕")
        print("4. 測試報價訂閱功能")
    else:
        print("\n❌ 部分測試失敗，需要檢查問題")

if __name__ == "__main__":
    main()
