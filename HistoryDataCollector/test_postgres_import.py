#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
測試PostgreSQL匯入功能
"""

import os
import sys
import logging

# 添加專案路徑
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from utils.logger import setup_logger
from database.postgres_importer import PostgreSQLImporter

# 設定日誌
setup_logger()
logger = logging.getLogger(__name__)

def test_postgres_import():
    """測試PostgreSQL匯入功能"""
    try:
        logger.info("🧪 測試PostgreSQL匯入功能...")
        
        # 初始化匯入器
        importer = PostgreSQLImporter()
        
        # 檢查SQLite資料
        logger.info("🔍 檢查SQLite資料...")
        sqlite_data = importer.check_sqlite_data()
        
        if sqlite_data is None:
            logger.error("❌ 沒有SQLite資料可測試")
            return False
        
        # 檢查PostgreSQL連接
        logger.info("🔍 檢查PostgreSQL連接...")
        if not importer.postgres_initialized:
            logger.error("❌ PostgreSQL連接失敗")
            logger.error("請確認：")
            logger.error("1. PostgreSQL資料庫已啟動")
            logger.error("2. app_setup.py和shared.py在正確路徑")
            logger.error("3. 資料庫連線設定正確")
            return False
        
        # 檢查PostgreSQL現有資料
        logger.info("🔍 檢查PostgreSQL現有資料...")
        importer.check_postgres_data()
        
        logger.info("✅ PostgreSQL匯入功能測試完成")
        logger.info("💡 如要執行實際匯入，請使用：")
        logger.info("   python import_to_postgres.py")
        
        return True
        
    except Exception as e:
        logger.error(f"❌ 測試失敗: {e}", exc_info=True)
        return False

if __name__ == "__main__":
    success = test_postgres_import()
    print(f"\n測試結果: {'成功' if success else '失敗'}")
    sys.exit(0 if success else 1)
