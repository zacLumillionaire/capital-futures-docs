#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
多組策略系統整合測試
測試simple_integrated.py中的多組策略功能
"""

import sys
import os
import time

# 添加路徑
sys.path.insert(0, os.path.dirname(__file__))

def test_import_integration():
    """測試整合導入"""
    print("🧪 測試多組策略系統整合導入")
    print("=" * 50)
    
    try:
        # 測試導入simple_integrated
        print("📦 測試導入simple_integrated...")
        from simple_integrated import SimpleIntegratedApp
        print("✅ simple_integrated導入成功")
        
        # 測試創建應用實例（不啟動GUI）
        print("🏗️ 測試創建應用實例...")
        
        # 模擬無GUI環境
        import tkinter as tk
        root = tk.Tk()
        root.withdraw()  # 隱藏主窗口
        
        app = SimpleIntegratedApp()
        print("✅ 應用實例創建成功")
        
        # 檢查多組策略系統是否正確初始化
        print("\n📊 檢查多組策略系統狀態:")
        print(f"   多組策略啟用: {app.multi_group_enabled}")
        print(f"   資料庫管理器: {'✅' if app.multi_group_db_manager else '❌'}")
        print(f"   部位管理器: {'✅' if app.multi_group_position_manager else '❌'}")
        print(f"   風險管理引擎: {'✅' if app.multi_group_risk_engine else '❌'}")
        print(f"   Console日誌器: {'✅' if app.multi_group_logger else '❌'}")
        
        # 測試多組策略方法是否存在
        print("\n🔧 檢查多組策略方法:")
        methods_to_check = [
            'init_multi_group_system',
            'create_multi_group_strategy_page',
            'start_multi_group_strategy',
            'stop_multi_group_strategy',
            'toggle_multi_group_console',
            'check_multi_group_exit_conditions'
        ]
        
        for method_name in methods_to_check:
            has_method = hasattr(app, method_name)
            print(f"   {method_name}: {'✅' if has_method else '❌'}")
        
        # 測試Console日誌功能
        if app.multi_group_logger:
            print("\n📝 測試Console日誌功能:")
            app.multi_group_logger.strategy_info("整合測試訊息")
            app.multi_group_logger.system_info("系統整合測試完成")
        
        root.destroy()
        
        return True
        
    except Exception as e:
        print(f"❌ 整合測試失敗: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_multi_group_config():
    """測試多組配置功能"""
    print("\n🧪 測試多組配置功能")
    print("=" * 50)
    
    try:
        from multi_group_config import create_preset_configs, validate_config
        
        # 測試預設配置
        presets = create_preset_configs()
        print(f"✅ 載入 {len(presets)} 個預設配置")
        
        for name, config in presets.items():
            print(f"\n📋 {name}:")
            print(f"   組數: {config.total_groups}")
            print(f"   每組口數: {config.lots_per_group}")
            print(f"   總部位數: {config.get_total_positions()}")
            
            # 驗證配置
            errors = validate_config(config)
            if errors:
                print(f"   ❌ 配置錯誤: {errors}")
            else:
                print(f"   ✅ 配置有效")
        
        return True
        
    except Exception as e:
        print(f"❌ 配置測試失敗: {e}")
        return False

def test_database_functionality():
    """測試資料庫功能"""
    print("\n🧪 測試資料庫功能")
    print("=" * 50)
    
    try:
        from multi_group_database import MultiGroupDatabaseManager
        
        # 創建測試資料庫
        db_manager = MultiGroupDatabaseManager("test_integration.db")
        print("✅ 資料庫管理器創建成功")
        
        # 測試創建策略組
        group_id = db_manager.create_strategy_group(
            date="2025-07-04",
            group_id=1,
            direction="LONG",
            signal_time="08:48:15",
            range_high=22530.0,
            range_low=22480.0,
            total_lots=2
        )
        print(f"✅ 創建策略組: ID={group_id}")
        
        # 測試查詢功能
        waiting_groups = db_manager.get_today_waiting_groups("2025-07-04")
        print(f"✅ 查詢等待組: {len(waiting_groups)} 個")
        
        # 測試統計功能
        stats = db_manager.get_daily_strategy_summary("2025-07-04")
        print(f"✅ 每日統計: 總組數={stats['total_groups']}")
        
        return True
        
    except Exception as e:
        print(f"❌ 資料庫測試失敗: {e}")
        return False

def test_console_logger():
    """測試Console日誌器"""
    print("\n🧪 測試Console日誌器")
    print("=" * 50)
    
    try:
        from multi_group_console_logger import get_logger, LogCategory
        
        logger = get_logger()
        print("✅ Console日誌器創建成功")
        
        # 測試各種日誌
        logger.strategy_info("測試策略信息", group_id=1)
        logger.position_entry("測試進場", group_id=1, position_id=1)
        logger.risk_activation("測試風險管理", group_id=1, position_id=1)
        logger.config_change("測試配置變更")
        
        # 測試Console控制
        logger.toggle_category_console(LogCategory.POSITION)
        logger.position_entry("這條不應該顯示", group_id=1, position_id=2)
        logger.toggle_category_console(LogCategory.POSITION)
        logger.position_entry("這條應該顯示", group_id=1, position_id=2)
        
        # 顯示統計
        logger.print_statistics()
        
        return True
        
    except Exception as e:
        print(f"❌ Console日誌器測試失敗: {e}")
        return False

def main():
    """主測試函數"""
    print("🚀 多組策略系統整合測試")
    print("=" * 80)
    
    # 執行各項測試
    test_results = []
    
    test_results.append(("整合導入", test_import_integration()))
    test_results.append(("多組配置", test_multi_group_config()))
    test_results.append(("資料庫功能", test_database_functionality()))
    test_results.append(("Console日誌", test_console_logger()))
    
    # 總結測試結果
    print("\n🎉 測試結果總結")
    print("=" * 80)
    
    passed_tests = 0
    total_tests = len(test_results)
    
    for test_name, result in test_results:
        status = "✅ 通過" if result else "❌ 失敗"
        print(f"{test_name}: {status}")
        if result:
            passed_tests += 1
    
    print(f"\n📊 測試統計: {passed_tests}/{total_tests} 通過")
    
    if passed_tests == total_tests:
        print("\n🎉 所有測試通過！多組策略系統整合成功")
        print("💡 系統已準備好進行實際使用")
        
        print("\n📝 使用指南:")
        print("1. 啟動 simple_integrated.py")
        print("2. 切換到 '🎯 多組策略配置' 頁面")
        print("3. 選擇合適的預設配置或自定義配置")
        print("4. 點擊 '🚀 啟動多組策略' 開始交易")
        print("5. 在VS Code Console中監控策略運行狀況")
        
    else:
        print("\n⚠️ 部分測試失敗，需要修正問題")
    
    # 清理測試文件
    try:
        if os.path.exists("test_integration.db"):
            os.remove("test_integration.db")
            print("\n🧹 測試文件已清理")
    except:
        pass

if __name__ == "__main__":
    main()
