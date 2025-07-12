#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
簡單測試腳本 - 測試登入功能
"""

import os
import sys
import logging

# 添加專案路徑
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from history_config import *
from utils.logger import setup_logger
from utils.skcom_manager import SKCOMManager

# 設定日誌
setup_logger()
logger = logging.getLogger(__name__)

def test_login():
    """測試登入功能"""
    try:
        logger.info("🚀 開始測試登入功能...")
        
        # 初始化SKCOM管理器
        skcom_manager = SKCOMManager()
        
        # 初始化API
        if not skcom_manager.initialize_skcom():
            logger.error("❌ SKCOM API初始化失敗")
            return False
        
        # 初始化物件
        if not skcom_manager.initialize_skcom_objects():
            logger.error("❌ SKCOM物件初始化失敗")
            return False
        
        # 嘗試登入
        logger.info("🔐 嘗試登入...")
        if skcom_manager.login():
            logger.info("✅ 登入成功！")
            
            # 登出
            skcom_manager.logout()
            logger.info("✅ 登出成功")
            
            return True
        else:
            logger.error("❌ 登入失敗")
            return False
            
    except Exception as e:
        logger.error(f"❌ 測試過程中發生錯誤: {e}")
        return False

if __name__ == "__main__":
    success = test_login()
    print(f"測試結果: {'成功' if success else '失敗'}")
    sys.exit(0 if success else 1)
