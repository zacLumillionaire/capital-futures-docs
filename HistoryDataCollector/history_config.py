#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
群益期貨歷史資料收集器專用配置檔案
基於群益官方案例程式，支援多商品、多時段資料收集
"""

import os

# 基礎配置
PROJECT_ROOT = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(PROJECT_ROOT, "data")
LOGS_DIR = os.path.join(PROJECT_ROOT, "logs")

# 資料庫配置
DATABASE_PATH = os.path.join(DATA_DIR, "history_data.db")

# 群益API配置
SKCOM_DLL_PATH = os.path.join(PROJECT_ROOT, "SKCOM.dll")

# 預設登入資訊（從記憶中獲取）
DEFAULT_USER_ID = "E123354882"
DEFAULT_PASSWORD = "kkd5ysUCC"

# 商品配置 - 支援多種期貨商品
PRODUCT_CODES = {
    'MTX00': '小台指期貨',
    'TXF00': '台指期貨', 
    'TM0000': '微型台指期貨',
    'EXF00': '電子期貨',
    'FXF00': '金融期貨',
    'GTF00': '櫃買期貨'
}

# 預設商品
DEFAULT_SYMBOL = "MTX00"

# 資料收集配置
DEFAULT_DATE_RANGE = 30        # 預設查詢30天
BATCH_SIZE = 1000             # 批量插入大小
MAX_RETRY_COUNT = 3           # 最大重試次數
RETRY_DELAY = 5               # 重試延遲秒數

# K線類型配置（對應群益API）
KLINE_TYPES = {
    'MINUTE': 0,              # 分線
    'DAILY': 4,               # 日線
    'WEEKLY': 5,              # 週線
    'MONTHLY': 6              # 月線
}

# 交易時段配置 - 支援早盤、夜盤、全部選擇
TRADING_SESSIONS = {
    'ALL': 0,                 # 全盤（包含夜盤）
    'AM_ONLY': 1,             # 僅日盤（早盤）
}

# 交易時段說明
TRADING_SESSION_NAMES = {
    'ALL': '全部時段',
    'AM_ONLY': '早盤（日盤）'
}

# 日誌配置
LOG_LEVEL = "INFO"
LOG_FORMAT = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
LOG_FILE = os.path.join(LOGS_DIR, "collector.log")

# UI配置
WINDOW_TITLE = "群益期貨歷史資料收集器"
WINDOW_SIZE = "900x700"

# 資料收集預設參數
DEFAULT_COLLECT_PARAMS = {
    'symbol': DEFAULT_SYMBOL,
    'kline_type': 'MINUTE',
    'trading_session': 'ALL',
    'minute_number': 1,
    'collect_tick': True,
    'collect_best5': True,
    'collect_kline': True
}

# 確保目錄存在
os.makedirs(DATA_DIR, exist_ok=True)
os.makedirs(LOGS_DIR, exist_ok=True)
