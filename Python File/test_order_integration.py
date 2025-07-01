#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
下單功能整合測試腳本
"""

import sys
import os
import logging

# 設定日誌
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def test_stable_order_api_import():
    """測試穩定版下單API導入"""
    try:
        from stable_order_api import get_stable_order_api, strategy_place_order
        logger.info("✅ 穩定版下單API導入成功")
        return True
    except ImportError as e:
        logger.error(f"❌ 穩定版下單API導入失敗: {e}")
        return False

def test_order_api_functionality():
    """測試下單API基本功能"""
    try:
        from stable_order_api import get_stable_order_api, strategy_place_order
        
        # 測試API實例創建
        api = get_stable_order_api()
        if api:
            logger.info("✅ 下單API實例創建成功")
        else:
            logger.error("❌ 下單API實例創建失敗")
            return False
        
        # 測試下單函數（不實際執行，只測試函數調用）
        try:
            # 這會返回失敗，因為沒有連接到OrderTester，但不會拋出異常
            result = strategy_place_order(
                product='MTX00',
                direction='BUY',
                price=22000,
                quantity=1,
                order_type='ROD'
            )
            
            if isinstance(result, dict) and 'success' in result:
                logger.info("✅ 下單函數調用成功（預期返回失敗，因為未連接OrderTester）")
                logger.info(f"   返回結果: {result}")
                return True
            else:
                logger.error("❌ 下單函數返回格式錯誤")
                return False
                
        except Exception as e:
            logger.error(f"❌ 下單函數調用異常: {e}")
            return False
            
    except Exception as e:
        logger.error(f"❌ 下單API功能測試失敗: {e}")
        return False

def test_ordertester_integration():
    """測試OrderTester整合功能"""
    try:
        # 檢查OrderTester.py是否包含策略相關代碼
        with open('OrderTester.py', 'r', encoding='utf-8') as f:
            content = f.read()
        
        # 檢查關鍵整合代碼
        checks = [
            ('策略模組導入', 'from strategy.strategy_panel import StrategyControlPanel'),
            ('策略頁面創建', 'def create_strategy_page'),
            ('下單API設定', 'def setup_strategy_order_api'),
            ('策略下單接口', 'def strategy_place_order'),
            ('報價橋接', 'def setup_strategy_quote_bridge'),
        ]
        
        all_passed = True
        for check_name, check_code in checks:
            if check_code in content:
                logger.info(f"✅ {check_name}: 已整合")
            else:
                logger.error(f"❌ {check_name}: 未找到")
                all_passed = False
        
        return all_passed
        
    except Exception as e:
        logger.error(f"❌ OrderTester整合檢查失敗: {e}")
        return False

def test_strategy_panel_compatibility():
    """測試策略面板兼容性"""
    try:
        from strategy.strategy_panel import StrategyControlPanel
        import tkinter as tk
        
        # 創建測試視窗（不顯示）
        root = tk.Tk()
        root.withdraw()  # 隱藏視窗
        
        # 創建策略面板
        panel = StrategyControlPanel(root)
        
        # 檢查必要方法
        required_methods = [
            'process_price_update',
            'start_strategy',
            'stop_strategy',
            'log_message'
        ]
        
        all_methods_exist = True
        for method in required_methods:
            if hasattr(panel, method):
                logger.info(f"✅ 策略面板方法 {method}: 存在")
            else:
                logger.error(f"❌ 策略面板方法 {method}: 不存在")
                all_methods_exist = False
        
        # 清理
        root.destroy()
        
        return all_methods_exist
        
    except Exception as e:
        logger.error(f"❌ 策略面板兼容性測試失敗: {e}")
        return False

def main():
    """主測試函數"""
    logger.info("🧪 開始下單功能整合測試...")
    
    tests = [
        ("穩定版下單API導入", test_stable_order_api_import),
        ("下單API基本功能", test_order_api_functionality),
        ("OrderTester整合檢查", test_ordertester_integration),
        ("策略面板兼容性", test_strategy_panel_compatibility),
    ]
    
    passed = 0
    total = len(tests)
    
    for test_name, test_func in tests:
        logger.info(f"📋 執行測試: {test_name}")
        try:
            if test_func():
                logger.info(f"✅ {test_name}: 通過")
                passed += 1
            else:
                logger.error(f"❌ {test_name}: 失敗")
        except Exception as e:
            logger.error(f"❌ {test_name}: 異常 - {e}")
    
    logger.info(f"🎯 測試結果: {passed}/{total} 通過")
    
    if passed == total:
        logger.info("🎉 所有下單功能整合測試通過！")
        print("\n🎉 下單功能整合測試完成！")
        print("✅ 穩定版下單API已成功整合到OrderTester.py")
        print("✅ 策略面板可以調用下單功能")
        print("💡 現在可以啟動OrderTester.py測試完整功能")
        return True
    else:
        logger.error("❌ 部分測試失敗，請檢查錯誤訊息")
        print(f"\n❌ 下單功能整合測試失敗！({passed}/{total} 通過)")
        print("💡 請檢查錯誤訊息並修復問題")
        return False

if __name__ == "__main__":
    try:
        success = main()
        sys.exit(0 if success else 1)
    except Exception as e:
        logger.error(f"❌ 測試執行失敗: {e}")
        print(f"\n❌ 測試執行失敗: {e}")
        sys.exit(1)
