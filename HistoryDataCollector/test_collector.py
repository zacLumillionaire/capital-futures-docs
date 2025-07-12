#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
群益期貨歷史資料收集器測試腳本
用於驗證各個模組的基本功能
"""

import os
import sys
import logging
import time

# 添加專案路徑
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from history_config import *
from utils.logger import setup_logger, get_logger
from database.db_manager import DatabaseManager
from utils.skcom_manager import SKCOMManager

# 設定日誌
setup_logger()
logger = get_logger(__name__)

def test_database():
    """測試資料庫功能"""
    logger.info("🧪 測試資料庫功能...")
    
    try:
        # 初始化資料庫
        db_manager = DatabaseManager()
        logger.info("✅ 資料庫初始化成功")
        
        # 測試插入逐筆資料
        test_tick_data = {
            'symbol': 'MTX00',
            'trade_date': '20241201',
            'trade_time': '090000',
            'close_price': 23500.0,
            'volume': 10,
            'data_type': 'TEST'
        }
        
        if db_manager.insert_tick_data(test_tick_data):
            logger.info("✅ 逐筆資料插入測試成功")
        else:
            logger.warning("⚠️ 逐筆資料插入測試失敗（可能是重複資料）")
        
        # 測試統計功能
        stats = db_manager.get_data_statistics()
        if stats:
            logger.info(f"✅ 統計功能測試成功 - 總計: {stats['total_count']} 筆資料")
        else:
            logger.error("❌ 統計功能測試失敗")
        
        # 測試資料庫資訊
        db_info = db_manager.get_database_info()
        if db_info:
            logger.info(f"✅ 資料庫資訊: {db_info['file_size_mb']} MB, {db_info['table_count']} 個資料表")
        
        return True
        
    except Exception as e:
        logger.error(f"❌ 資料庫測試失敗: {e}")
        return False

def test_skcom_initialization():
    """測試SKCOM API初始化"""
    logger.info("🧪 測試SKCOM API初始化...")
    
    try:
        # 檢查DLL檔案
        if not os.path.exists(SKCOM_DLL_PATH):
            logger.error(f"❌ 找不到SKCOM.dll檔案: {SKCOM_DLL_PATH}")
            return False
        
        logger.info(f"✅ SKCOM.dll檔案存在: {SKCOM_DLL_PATH}")
        
        # 初始化SKCOM管理器
        skcom_manager = SKCOMManager()
        
        if not skcom_manager.initialize_skcom():
            logger.error("❌ SKCOM API初始化失敗")
            return False
        
        logger.info("✅ SKCOM API初始化成功")
        
        if not skcom_manager.initialize_skcom_objects():
            logger.error("❌ SKCOM物件初始化失敗")
            return False
        
        logger.info("✅ SKCOM物件初始化成功")
        
        # 取得API版本
        version = skcom_manager.get_api_version()
        if version:
            logger.info(f"✅ API版本: {version}")
        
        return True
        
    except Exception as e:
        logger.error(f"❌ SKCOM初始化測試失敗: {e}")
        return False

def test_login():
    """測試登入功能"""
    logger.info("🧪 測試登入功能...")
    
    try:
        # 初始化SKCOM管理器
        skcom_manager = SKCOMManager()
        
        if not skcom_manager.initialize_skcom():
            logger.error("❌ SKCOM API初始化失敗")
            return False
        
        if not skcom_manager.initialize_skcom_objects():
            logger.error("❌ SKCOM物件初始化失敗")
            return False
        
        # 嘗試登入
        logger.info("🔐 嘗試登入...")
        if skcom_manager.login():
            logger.info("✅ 登入成功")
            
            # 嘗試連線報價主機
            logger.info("📡 嘗試連線報價主機...")
            if skcom_manager.connect_quote_server():
                logger.info("✅ 報價主機連線請求已送出")
                
                # 等待商品資料準備完成
                logger.info("⏳ 等待商品資料準備完成...")
                timeout = 30
                start_time = time.time()
                
                while not skcom_manager.stocks_ready:
                    if time.time() - start_time > timeout:
                        logger.warning("⚠️ 等待商品資料準備完成超時")
                        break
                    time.sleep(1)
                
                if skcom_manager.stocks_ready:
                    logger.info("✅ 商品資料已準備完成")
                    
                    # 測試請求歷史資料
                    logger.info("📊 測試請求歷史逐筆資料...")
                    if skcom_manager.request_history_ticks('MTX00', 0):
                        logger.info("✅ 歷史逐筆資料請求成功")
                    else:
                        logger.warning("⚠️ 歷史逐筆資料請求失敗")
                
            else:
                logger.error("❌ 報價主機連線失敗")
            
            # 登出
            skcom_manager.logout()
            logger.info("✅ 登出成功")
            
        else:
            logger.error("❌ 登入失敗")
            return False
        
        # 清理資源
        skcom_manager.cleanup()
        return True
        
    except Exception as e:
        logger.error(f"❌ 登入測試失敗: {e}")
        return False

def test_configuration():
    """測試配置檔案"""
    logger.info("🧪 測試配置檔案...")
    
    try:
        # 檢查基本配置
        logger.info(f"✅ 專案根目錄: {PROJECT_ROOT}")
        logger.info(f"✅ 資料目錄: {DATA_DIR}")
        logger.info(f"✅ 日誌目錄: {LOGS_DIR}")
        logger.info(f"✅ 資料庫路徑: {DATABASE_PATH}")
        
        # 檢查商品配置
        logger.info(f"✅ 支援商品: {list(PRODUCT_CODES.keys())}")
        logger.info(f"✅ 預設商品: {DEFAULT_SYMBOL}")
        
        # 檢查K線類型
        logger.info(f"✅ K線類型: {list(KLINE_TYPES.keys())}")
        
        # 檢查交易時段
        logger.info(f"✅ 交易時段: {list(TRADING_SESSION_NAMES.keys())}")
        
        # 檢查目錄是否存在
        if os.path.exists(DATA_DIR):
            logger.info(f"✅ 資料目錄已存在")
        else:
            logger.warning(f"⚠️ 資料目錄不存在，將自動建立")
        
        if os.path.exists(LOGS_DIR):
            logger.info(f"✅ 日誌目錄已存在")
        else:
            logger.warning(f"⚠️ 日誌目錄不存在，將自動建立")
        
        return True
        
    except Exception as e:
        logger.error(f"❌ 配置測試失敗: {e}")
        return False

def run_all_tests():
    """執行所有測試"""
    logger.info("🚀 開始執行群益期貨歷史資料收集器測試...")
    
    tests = [
        ("配置檔案", test_configuration),
        ("資料庫功能", test_database),
        ("SKCOM初始化", test_skcom_initialization),
        ("登入功能", test_login),
    ]
    
    passed = 0
    total = len(tests)
    
    for test_name, test_func in tests:
        logger.info(f"\n{'='*50}")
        logger.info(f"測試項目: {test_name}")
        logger.info(f"{'='*50}")
        
        try:
            if test_func():
                logger.info(f"✅ {test_name} 測試通過")
                passed += 1
            else:
                logger.error(f"❌ {test_name} 測試失敗")
        except Exception as e:
            logger.error(f"❌ {test_name} 測試發生例外: {e}")
    
    logger.info(f"\n{'='*50}")
    logger.info(f"測試結果: {passed}/{total} 項測試通過")
    logger.info(f"{'='*50}")
    
    if passed == total:
        logger.info("🎉 所有測試都通過！系統準備就緒")
        return True
    else:
        logger.warning(f"⚠️ 有 {total - passed} 項測試失敗，請檢查相關設定")
        return False

if __name__ == "__main__":
    try:
        success = run_all_tests()
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        logger.info("❌ 測試被使用者中斷")
        sys.exit(1)
    except Exception as e:
        logger.error(f"❌ 測試執行失敗: {e}")
        sys.exit(1)
