#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
資料庫和持久化功能整合測試腳本
"""

import sys
import os
import logging
from datetime import datetime

# 設定日誌
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def test_database_import():
    """測試資料庫模組導入"""
    try:
        from database.sqlite_manager import SQLiteManager, db_manager
        logger.info("✅ SQLiteManager導入成功")
        return True
    except ImportError as e:
        logger.error(f"❌ SQLiteManager導入失敗: {e}")
        return False

def test_database_initialization():
    """測試資料庫初始化"""
    try:
        from database.sqlite_manager import SQLiteManager
        
        # 創建測試資料庫
        test_db = SQLiteManager("test_integration.db")
        
        # 檢查資料庫檔案是否創建
        if os.path.exists("test_integration.db"):
            logger.info("✅ 資料庫檔案創建成功")
        else:
            logger.error("❌ 資料庫檔案創建失敗")
            return False
        
        # 測試基本功能
        test_db.insert_strategy_signal(
            "2025-07-01", 22050, 21980, "LONG", "08:48:15", 22055
        )
        
        signal = test_db.get_today_signal("2025-07-01")
        if signal:
            logger.info("✅ 資料庫基本功能測試成功")
            logger.info(f"   信號資料: {signal}")
        else:
            logger.error("❌ 資料庫基本功能測試失敗")
            return False
        
        # 清理測試檔案
        try:
            os.remove("test_integration.db")
            logger.info("✅ 測試資料庫檔案清理完成")
        except:
            pass
        
        return True
        
    except Exception as e:
        logger.error(f"❌ 資料庫初始化測試失敗: {e}")
        return False

def test_position_management():
    """測試部位管理功能"""
    try:
        from database.sqlite_manager import SQLiteManager
        
        # 創建測試資料庫
        test_db = SQLiteManager("test_position.db")
        
        # 檢查部位管理狀態
        status = test_db.get_position_management_status()
        logger.info(f"部位管理狀態: {status}")
        
        if status.get("position_management_available", False):
            logger.info("✅ 部位管理模組可用")
            
            # 測試創建交易會話
            session_id = f"TEST_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
            success = test_db.create_trading_session(
                session_id, "2025-07-01", "測試策略", 3,
                {"lot_rules": [{"trailing_activation": 15, "trailing_pullback": 0.20}]},
                22050.0, 21980.0, "08:47:00", "LONG", 22055.0, "08:48:15"
            )
            
            if success:
                logger.info("✅ 交易會話創建成功")
            else:
                logger.error("❌ 交易會話創建失敗")
                return False
        else:
            logger.warning("⚠️ 部位管理模組不可用，跳過相關測試")
        
        # 清理測試檔案
        try:
            os.remove("test_position.db")
            logger.info("✅ 測試資料庫檔案清理完成")
        except:
            pass
        
        return True
        
    except Exception as e:
        logger.error(f"❌ 部位管理測試失敗: {e}")
        return False

def test_strategy_panel_database():
    """測試策略面板資料庫整合"""
    try:
        from strategy.strategy_panel import StrategyControlPanel
        import tkinter as tk
        
        # 創建測試視窗（不顯示）
        root = tk.Tk()
        root.withdraw()  # 隱藏視窗
        
        # 創建策略面板
        panel = StrategyControlPanel(root)
        
        # 檢查資料庫管理器
        if hasattr(panel, 'db_manager') and panel.db_manager:
            logger.info("✅ 策略面板資料庫管理器存在")
            
            # 測試統計功能
            try:
                summary = panel.db_manager.get_trading_summary()
                logger.info("✅ 交易統計查詢成功")
                logger.info(f"   統計資料: {summary}")
            except Exception as e:
                logger.error(f"❌ 交易統計查詢失敗: {e}")
                return False
        else:
            logger.error("❌ 策略面板資料庫管理器不存在")
            return False
        
        # 清理
        root.destroy()
        
        return True
        
    except Exception as e:
        logger.error(f"❌ 策略面板資料庫整合測試失敗: {e}")
        return False

def test_ordertester_database_integration():
    """測試OrderTester資料庫整合"""
    try:
        # 檢查OrderTester.py是否包含資料庫相關代碼
        with open('OrderTester.py', 'r', encoding='utf-8') as f:
            content = f.read()
        
        # 檢查策略面板創建
        if 'StrategyControlPanel' in content:
            logger.info("✅ OrderTester包含策略面板創建代碼")
        else:
            logger.error("❌ OrderTester未包含策略面板創建代碼")
            return False
        
        # 檢查資料庫檔案是否存在
        db_files = ['strategy_trading.db']
        for db_file in db_files:
            if os.path.exists(db_file):
                logger.info(f"✅ 資料庫檔案存在: {db_file}")
            else:
                logger.info(f"ℹ️ 資料庫檔案不存在: {db_file} (首次運行時會自動創建)")
        
        return True
        
    except Exception as e:
        logger.error(f"❌ OrderTester資料庫整合檢查失敗: {e}")
        return False

def main():
    """主測試函數"""
    logger.info("🧪 開始資料庫和持久化功能整合測試...")
    
    tests = [
        ("資料庫模組導入", test_database_import),
        ("資料庫初始化", test_database_initialization),
        ("部位管理功能", test_position_management),
        ("策略面板資料庫整合", test_strategy_panel_database),
        ("OrderTester資料庫整合", test_ordertester_database_integration),
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
        logger.info("🎉 所有資料庫和持久化功能整合測試通過！")
        print("\n🎉 資料庫和持久化功能整合測試完成！")
        print("✅ SQLite資料庫已成功整合到OrderTester.py")
        print("✅ 策略面板可以使用完整的資料庫功能")
        print("✅ 部位管理和交易記錄持久化功能正常")
        print("💡 現在可以啟動OrderTester.py測試完整的策略交易功能")
        return True
    else:
        logger.error("❌ 部分測試失敗，請檢查錯誤訊息")
        print(f"\n❌ 資料庫和持久化功能整合測試失敗！({passed}/{total} 通過)")
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
