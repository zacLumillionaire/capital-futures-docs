#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
日誌工具模組
設置統一的日誌格式和輸出方式
"""

import logging
import os
import sys
from datetime import datetime

# 添加專案路徑
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from history_config import LOG_LEVEL, LOG_FORMAT, LOG_FILE, LOGS_DIR

def setup_logger(name=None, level=None, log_file=None):
    """
    設置日誌記錄器
    
    Args:
        name: 記錄器名稱，預設為根記錄器
        level: 日誌等級，預設從配置檔讀取
        log_file: 日誌檔案路徑，預設從配置檔讀取
    
    Returns:
        logger: 配置好的日誌記錄器
    """
    
    # 確保日誌目錄存在
    os.makedirs(LOGS_DIR, exist_ok=True)
    
    # 設置日誌等級
    if level is None:
        level = getattr(logging, LOG_LEVEL.upper(), logging.INFO)
    
    # 設置日誌檔案
    if log_file is None:
        log_file = LOG_FILE
    
    # 建立記錄器
    logger = logging.getLogger(name)
    logger.setLevel(level)
    
    # 避免重複添加處理器
    if logger.handlers:
        return logger
    
    # 建立格式器
    formatter = logging.Formatter(LOG_FORMAT)
    
    # 建立控制台處理器
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(level)
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)
    
    # 建立檔案處理器
    try:
        file_handler = logging.FileHandler(log_file, encoding='utf-8')
        file_handler.setLevel(level)
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)
    except Exception as e:
        logger.warning(f"無法建立檔案日誌處理器: {e}")
    
    return logger

def get_logger(name):
    """取得指定名稱的日誌記錄器"""
    return logging.getLogger(name)

def log_api_call(logger, api_name, params, result_code, message):
    """
    記錄API調用資訊
    
    Args:
        logger: 日誌記錄器
        api_name: API名稱
        params: 參數
        result_code: 結果代碼
        message: 回傳訊息
    """
    if result_code == 0:
        logger.info(f"✅ 【{api_name}】成功 - 參數: {params}, 訊息: {message}")
    else:
        logger.error(f"❌ 【{api_name}】失敗 - 參數: {params}, 代碼: {result_code}, 訊息: {message}")

def log_data_collection(logger, data_type, symbol, count, status="進行中"):
    """
    記錄資料收集進度
    
    Args:
        logger: 日誌記錄器
        data_type: 資料類型 (TICK/BEST5/KLINE)
        symbol: 商品代碼
        count: 收集筆數
        status: 狀態
    """
    timestamp = datetime.now().strftime("%H:%M:%S")
    logger.info(f"📊 [{timestamp}] {data_type}資料收集 - {symbol}: {count:,} 筆 ({status})")

def log_error_with_traceback(logger, error_msg, exception=None):
    """
    記錄錯誤訊息和堆疊追蹤
    
    Args:
        logger: 日誌記錄器
        error_msg: 錯誤訊息
        exception: 例外物件
    """
    logger.error(f"❌ {error_msg}")
    if exception:
        logger.exception(f"例外詳情: {str(exception)}")

# 設置根日誌記錄器
setup_logger()
