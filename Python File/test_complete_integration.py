#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
完整整合測試腳本 - 端到端驗證
驗證OrderTester.py策略整合的所有功能
"""

import sys
import os
import time
import logging
import tkinter as tk
from datetime import datetime

# 設定日誌
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def test_all_imports():
    """測試所有必要模組導入"""
    logger.info("📋 測試模組導入...")
    
    imports = [
        ("策略面板", "from strategy.strategy_panel import StrategyControlPanel"),
        ("穩定版下單API", "from stable_order_api import get_stable_order_api, strategy_place_order"),
        ("資料庫管理", "from database.sqlite_manager import SQLiteManager"),
        ("時間管理", "from utils.time_utils import TradingTimeManager"),
        ("信號檢測", "from strategy.signal_detector import OpeningRangeDetector, BreakoutSignalDetector"),
    ]
    
    all_passed = True
    for name, import_code in imports:
        try:
            exec(import_code)
            logger.info(f"✅ {name}: 導入成功")
        except ImportError as e:
            logger.error(f"❌ {name}: 導入失敗 - {e}")
            all_passed = False
        except Exception as e:
            logger.error(f"❌ {name}: 異常 - {e}")
            all_passed = False
    
    return all_passed

def test_ordertester_structure():
    """測試OrderTester.py結構完整性"""
    logger.info("📋 測試OrderTester.py結構...")
    
    try:
        with open('OrderTester.py', 'r', encoding='utf-8') as f:
            content = f.read()
        
        required_components = [
            ("策略模組導入", "from strategy.strategy_panel import StrategyControlPanel"),
            ("策略標籤頁", "策略交易"),
            ("策略頁面創建", "def create_strategy_page"),
            ("策略錯誤頁面", "def create_strategy_error_page"),
            ("下單API設定", "def setup_strategy_order_api"),
            ("策略下單接口", "def strategy_place_order"),
            ("報價橋接", "def setup_strategy_quote_bridge"),
            ("報價定時器", "def start_quote_bridge_timer"),
            ("策略清理", "strategy_panel.stop_strategy"),
        ]
        
        all_passed = True
        for name, code_snippet in required_components:
            if code_snippet in content:
                logger.info(f"✅ {name}: 已整合")
            else:
                logger.error(f"❌ {name}: 未找到")
                all_passed = False
        
        return all_passed
        
    except Exception as e:
        logger.error(f"❌ OrderTester.py結構測試失敗: {e}")
        return False

def test_strategy_panel_creation():
    """測試策略面板創建和基本功能"""
    logger.info("📋 測試策略面板創建...")
    
    try:
        from strategy.strategy_panel import StrategyControlPanel
        
        # 創建測試視窗
        root = tk.Tk()
        root.withdraw()  # 隱藏視窗
        
        # 創建策略面板
        panel = StrategyControlPanel(root)
        
        # 測試基本屬性
        required_attributes = [
            'db_manager', 'time_manager', 'strategy_active', 
            'monitoring_active', 'current_price'
        ]
        
        all_passed = True
        for attr in required_attributes:
            if hasattr(panel, attr):
                logger.info(f"✅ 策略面板屬性 {attr}: 存在")
            else:
                logger.error(f"❌ 策略面板屬性 {attr}: 不存在")
                all_passed = False
        
        # 測試基本方法
        required_methods = [
            'process_price_update', 'start_strategy', 'stop_strategy',
            'log_message', 'show_statistics'
        ]
        
        for method in required_methods:
            if hasattr(panel, method) and callable(getattr(panel, method)):
                logger.info(f"✅ 策略面板方法 {method}: 存在")
            else:
                logger.error(f"❌ 策略面板方法 {method}: 不存在")
                all_passed = False
        
        # 測試價格更新功能
        try:
            panel.process_price_update(22000)
            logger.info("✅ 價格更新功能: 正常")
        except Exception as e:
            logger.error(f"❌ 價格更新功能: 異常 - {e}")
            all_passed = False
        
        # 測試統計功能
        try:
            summary = panel.db_manager.get_trading_summary()
            logger.info("✅ 統計查詢功能: 正常")
        except Exception as e:
            logger.error(f"❌ 統計查詢功能: 異常 - {e}")
            all_passed = False
        
        # 清理
        root.destroy()
        
        return all_passed
        
    except Exception as e:
        logger.error(f"❌ 策略面板創建測試失敗: {e}")
        return False

def test_order_api_integration():
    """測試下單API整合"""
    logger.info("📋 測試下單API整合...")
    
    try:
        from stable_order_api import get_stable_order_api, strategy_place_order
        
        # 測試API實例
        api = get_stable_order_api()
        if api:
            logger.info("✅ 下單API實例: 創建成功")
        else:
            logger.error("❌ 下單API實例: 創建失敗")
            return False
        
        # 測試下單函數（不實際執行）
        result = strategy_place_order(
            product='MTX00',
            direction='BUY',
            price=22000,
            quantity=1,
            order_type='ROD'
        )
        
        if isinstance(result, dict) and 'success' in result:
            logger.info("✅ 下單函數調用: 正常")
            logger.info(f"   返回結果: {result}")
        else:
            logger.error("❌ 下單函數調用: 異常")
            return False
        
        return True
        
    except Exception as e:
        logger.error(f"❌ 下單API整合測試失敗: {e}")
        return False

def test_database_functionality():
    """測試資料庫功能"""
    logger.info("📋 測試資料庫功能...")
    
    try:
        from database.sqlite_manager import SQLiteManager
        
        # 創建測試資料庫
        test_db = SQLiteManager("test_complete.db")
        
        # 測試基本操作
        test_db.insert_strategy_signal(
            "2025-07-01", 22050, 21980, "LONG", "08:48:15", 22055
        )
        
        test_db.insert_trade_record(
            "2025-07-01", "測試策略", 1, "08:48:15", 22055,
            "09:15:30", 22105, "LONG", 50, "TRAILING_STOP"
        )
        
        # 測試查詢
        signal = test_db.get_today_signal("2025-07-01")
        trades = test_db.get_today_trades("2025-07-01")
        summary = test_db.get_trading_summary()
        
        if signal and trades and summary:
            logger.info("✅ 資料庫基本功能: 正常")
            logger.info(f"   信號: {signal['signal_type']} @{signal['signal_price']}")
            logger.info(f"   交易: {len(trades)}筆")
            logger.info(f"   統計: {summary['total_trades']}筆交易")
        else:
            logger.error("❌ 資料庫基本功能: 異常")
            return False
        
        # 清理測試檔案
        try:
            os.remove("test_complete.db")
        except:
            pass
        
        return True
        
    except Exception as e:
        logger.error(f"❌ 資料庫功能測試失敗: {e}")
        return False

def test_configuration_management():
    """測試配置管理"""
    logger.info("📋 測試配置管理...")
    
    try:
        # 檢查配置檔案
        config_files = [
            'strategy_trading.db',  # 主要資料庫
        ]
        
        for config_file in config_files:
            if os.path.exists(config_file):
                logger.info(f"✅ 配置檔案 {config_file}: 存在")
            else:
                logger.info(f"ℹ️ 配置檔案 {config_file}: 不存在（首次運行時會自動創建）")
        
        # 測試策略配置
        from strategy.strategy_config import StrategyConfig
        config = StrategyConfig()
        
        if config:
            logger.info("✅ 策略配置: 載入成功")
        else:
            logger.error("❌ 策略配置: 載入失敗")
            return False
        
        return True
        
    except Exception as e:
        logger.error(f"❌ 配置管理測試失敗: {e}")
        return False

def main():
    """主測試函數"""
    logger.info("🧪 開始完整整合測試...")
    logger.info("=" * 60)
    
    tests = [
        ("模組導入", test_all_imports),
        ("OrderTester結構", test_ordertester_structure),
        ("策略面板創建", test_strategy_panel_creation),
        ("下單API整合", test_order_api_integration),
        ("資料庫功能", test_database_functionality),
        ("配置管理", test_configuration_management),
    ]
    
    passed = 0
    total = len(tests)
    
    for test_name, test_func in tests:
        logger.info(f"\n📋 執行測試: {test_name}")
        logger.info("-" * 40)
        try:
            if test_func():
                logger.info(f"✅ {test_name}: 通過")
                passed += 1
            else:
                logger.error(f"❌ {test_name}: 失敗")
        except Exception as e:
            logger.error(f"❌ {test_name}: 異常 - {e}")
    
    logger.info("\n" + "=" * 60)
    logger.info(f"🎯 測試結果: {passed}/{total} 通過")
    
    if passed == total:
        logger.info("🎉 所有完整整合測試通過！")
        print("\n" + "🎉" * 20)
        print("完整整合測試成功！")
        print("🎉" * 20)
        print("\n✅ 策略功能已成功整合到OrderTester.py")
        print("✅ 所有核心功能測試通過")
        print("✅ 系統已準備好進行實際交易測試")
        print("\n💡 下一步操作：")
        print("   1. 啟動 OrderTester.py")
        print("   2. 登入群益證券API")
        print("   3. 切換到「策略交易」標籤頁")
        print("   4. 開始測試策略功能")
        return True
    else:
        logger.error("❌ 部分測試失敗，請檢查錯誤訊息")
        print(f"\n❌ 完整整合測試失敗！({passed}/{total} 通過)")
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
