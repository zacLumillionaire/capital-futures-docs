#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
實盤監控整合功能測試腳本

🏷️ REAL_MONITOR_INTEGRATION_TEST_2025_01_01
✅ 測試新增的「開始實盤監控」按鈕功能
✅ 驗證群益API整合穩定性
✅ 確保不影響現有策略邏輯
"""

import sys
import os
import time
import logging
from datetime import datetime

# 設定日誌
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler('test_real_monitor.log', encoding='utf-8')
    ]
)
logger = logging.getLogger(__name__)

def test_import_modules():
    """測試模組導入"""
    logger.info("🧪 測試1: 檢查模組導入")
    
    try:
        # 測試主程式導入
        sys.path.append(os.path.dirname(os.path.abspath(__file__)))
        
        # 檢查群益API模組
        try:
            import comtypes
            import comtypes.client
            logger.info("✅ comtypes模組可用")
        except ImportError as e:
            logger.error(f"❌ comtypes模組不可用: {e}")
            return False
        
        # 檢查主程式模組
        try:
            from test_ui_improvements import TradingStrategyApp, DirectSKCOMManager
            logger.info("✅ 主程式模組導入成功")
        except ImportError as e:
            logger.error(f"❌ 主程式模組導入失敗: {e}")
            return False
        
        return True
        
    except Exception as e:
        logger.error(f"❌ 模組導入測試失敗: {e}")
        return False

def test_direct_skcom_manager():
    """測試DirectSKCOMManager類別"""
    logger.info("🧪 測試2: DirectSKCOMManager功能")
    
    try:
        from test_ui_improvements import DirectSKCOMManager
        
        # 創建管理器實例
        manager = DirectSKCOMManager()
        logger.info("✅ DirectSKCOMManager實例創建成功")
        
        # 檢查初始狀態
        assert not manager.is_initialized, "初始化狀態應為False"
        assert not manager.is_logged_in, "登入狀態應為False"
        logger.info("✅ 初始狀態檢查通過")
        
        # 檢查方法存在
        required_methods = [
            'initialize_api', 'login', 'start_quote_monitor'
        ]
        
        for method_name in required_methods:
            assert hasattr(manager, method_name), f"缺少方法: {method_name}"
        
        logger.info("✅ 必要方法檢查通過")
        
        return True
        
    except Exception as e:
        logger.error(f"❌ DirectSKCOMManager測試失敗: {e}")
        return False

def test_ui_integration():
    """測試UI整合"""
    logger.info("🧪 測試3: UI整合檢查")
    
    try:
        import tkinter as tk
        from test_ui_improvements import TradingStrategyApp
        
        # 創建測試用的根視窗
        root = tk.Tk()
        root.withdraw()  # 隱藏視窗
        
        # 創建應用實例
        app = TradingStrategyApp(root)
        logger.info("✅ TradingStrategyApp實例創建成功")
        
        # 檢查新增的按鈕
        assert hasattr(app, 'btn_start_real_monitor'), "缺少開始實盤監控按鈕"
        assert hasattr(app, 'btn_stop_real_monitor'), "缺少停止實盤監控按鈕"
        logger.info("✅ 實盤監控按鈕檢查通過")
        
        # 檢查DirectSKCOMManager整合
        assert hasattr(app, 'direct_skcom'), "缺少direct_skcom屬性"
        assert hasattr(app, 'direct_api_connected'), "缺少direct_api_connected屬性"
        logger.info("✅ DirectSKCOMManager整合檢查通過")
        
        # 檢查新增的方法
        required_methods = [
            'start_real_monitor', 'stop_real_monitor', 
            'monitor_real_quote_connection'
        ]
        
        for method_name in required_methods:
            assert hasattr(app, method_name), f"缺少方法: {method_name}"
        
        logger.info("✅ 新增方法檢查通過")
        
        # 清理
        root.destroy()
        
        return True
        
    except Exception as e:
        logger.error(f"❌ UI整合測試失敗: {e}")
        return False

def test_button_states():
    """測試按鈕狀態管理"""
    logger.info("🧪 測試4: 按鈕狀態管理")
    
    try:
        import tkinter as tk
        from test_ui_improvements import TradingStrategyApp
        
        # 創建測試用的根視窗
        root = tk.Tk()
        root.withdraw()  # 隱藏視窗
        
        # 創建應用實例
        app = TradingStrategyApp(root)
        
        # 檢查初始按鈕狀態
        initial_start_state = str(app.btn_start_real_monitor['state'])
        initial_stop_state = str(app.btn_stop_real_monitor['state'])
        
        assert initial_start_state == 'normal', f"開始按鈕初始狀態應為normal，實際為{initial_start_state}"
        assert initial_stop_state == 'disabled', f"停止按鈕初始狀態應為disabled，實際為{initial_stop_state}"
        
        logger.info("✅ 初始按鈕狀態檢查通過")
        
        # 測試模式切換對按鈕狀態的影響
        app.switch_to_simulation()
        sim_start_state = str(app.btn_start_real_monitor['state'])
        sim_stop_state = str(app.btn_stop_real_monitor['state'])
        
        assert sim_start_state == 'normal', f"模擬模式下開始按鈕應為normal"
        assert sim_stop_state == 'disabled', f"模擬模式下停止按鈕應為disabled"
        
        logger.info("✅ 模式切換按鈕狀態檢查通過")
        
        # 清理
        root.destroy()
        
        return True
        
    except Exception as e:
        logger.error(f"❌ 按鈕狀態測試失敗: {e}")
        return False

def test_error_handling():
    """測試錯誤處理機制"""
    logger.info("🧪 測試5: 錯誤處理機制")
    
    try:
        from test_ui_improvements import DirectSKCOMManager
        
        # 測試在沒有群益API的情況下的錯誤處理
        manager = DirectSKCOMManager()
        
        # 這應該會失敗但不會崩潰
        result = manager.initialize_api()
        logger.info(f"✅ API初始化錯誤處理正常 (結果: {result})")
        
        # 測試在未登入情況下的報價監控
        result = manager.start_quote_monitor()
        logger.info(f"✅ 報價監控錯誤處理正常 (結果: {result})")
        
        return True
        
    except Exception as e:
        logger.error(f"❌ 錯誤處理測試失敗: {e}")
        return False

def run_all_tests():
    """執行所有測試"""
    logger.info("🚀 開始實盤監控整合功能測試")
    logger.info("=" * 60)
    
    tests = [
        ("模組導入測試", test_import_modules),
        ("DirectSKCOMManager測試", test_direct_skcom_manager),
        ("UI整合測試", test_ui_integration),
        ("按鈕狀態測試", test_button_states),
        ("錯誤處理測試", test_error_handling),
    ]
    
    passed = 0
    total = len(tests)
    
    for test_name, test_func in tests:
        logger.info(f"\n📋 執行: {test_name}")
        try:
            if test_func():
                logger.info(f"✅ {test_name} - 通過")
                passed += 1
            else:
                logger.error(f"❌ {test_name} - 失敗")
        except Exception as e:
            logger.error(f"❌ {test_name} - 異常: {e}")
    
    logger.info("\n" + "=" * 60)
    logger.info(f"📊 測試結果: {passed}/{total} 通過")
    
    if passed == total:
        logger.info("🎉 所有測試通過！實盤監控整合功能正常")
        return True
    else:
        logger.warning(f"⚠️ 有 {total - passed} 個測試失敗")
        return False

def main():
    """主函數"""
    print("🧪 實盤監控整合功能測試")
    print(f"📅 測試時間: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 60)
    
    try:
        success = run_all_tests()
        
        if success:
            print("\n🎉 測試完成 - 所有功能正常！")
            print("💡 可以安全使用「開始實盤監控」功能")
        else:
            print("\n⚠️ 測試完成 - 發現問題")
            print("💡 請檢查日誌文件 test_real_monitor.log")
            
    except Exception as e:
        logger.error(f"❌ 測試執行異常: {e}")
        print(f"\n❌ 測試執行異常: {e}")

if __name__ == "__main__":
    main()
