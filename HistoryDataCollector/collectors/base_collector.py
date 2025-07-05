#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
基礎資料收集器類別
提供所有收集器的共同功能和介面
"""

import logging
import sys
import os
from abc import ABC, abstractmethod
from datetime import datetime

# 添加專案路徑
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from utils.date_utils import combine_date_time, format_display_datetime
from utils.logger import log_data_collection, log_error_with_traceback

logger = logging.getLogger(__name__)

class BaseCollector(ABC):
    """基礎資料收集器抽象類別"""

    def __init__(self, skcom_manager, db_manager):
        """
        初始化基礎收集器
        
        Args:
            skcom_manager: SKCOM API管理器
            db_manager: 資料庫管理器
        """
        self.skcom_manager = skcom_manager
        self.db_manager = db_manager
        self.is_collecting = False
        self.collected_count = 0
        self.error_count = 0
        self.start_time = None
        self.collection_log_id = None

    @abstractmethod
    def start_collection(self, symbol, **kwargs):
        """
        開始收集資料 - 子類別必須實現
        
        Args:
            symbol: 商品代碼
            **kwargs: 其他參數
            
        Returns:
            bool: 是否成功開始收集
        """
        pass

    @abstractmethod
    def stop_collection(self):
        """
        停止收集資料 - 子類別必須實現
        """
        pass

    def format_price(self, price_value):
        """
        格式化價格 - 群益API回傳的價格需要除以100.0
        
        Args:
            price_value: 原始價格值
            
        Returns:
            float: 格式化後的價格，None表示無效價格
        """
        if price_value is None or price_value == 0:
            return None
        try:
            return float(price_value) / 100.0
        except (ValueError, TypeError):
            return None

    def format_datetime(self, date_value, time_value):
        """
        格式化日期時間
        
        Args:
            date_value: 日期值 (YYYYMMDD)
            time_value: 時間值 (HHMMSS)
            
        Returns:
            datetime: 格式化後的datetime物件，失敗時返回None
        """
        try:
            return combine_date_time(str(date_value), str(time_value))
        except Exception as e:
            logger.debug(f"時間格式化錯誤: {e}")
            return None

    def validate_data(self, data_dict, required_fields):
        """
        驗證資料完整性
        
        Args:
            data_dict: 資料字典
            required_fields: 必要欄位列表
            
        Returns:
            bool: 資料是否有效
        """
        try:
            for field in required_fields:
                if field not in data_dict or data_dict[field] is None:
                    logger.warning(f"資料驗證失敗: 缺少必要欄位 {field}")
                    return False
            return True
        except Exception as e:
            logger.error(f"資料驗證時發生錯誤: {e}")
            return False

    def log_collection_progress(self, data_type, symbol, interval=1000):
        """
        記錄收集進度
        
        Args:
            data_type: 資料類型
            symbol: 商品代碼
            interval: 記錄間隔
        """
        if self.collected_count % interval == 0 and self.collected_count > 0:
            elapsed_time = ""
            if self.start_time:
                elapsed = datetime.now() - self.start_time
                elapsed_time = f" (耗時: {elapsed.total_seconds():.1f}秒)"
            
            log_data_collection(
                logger, data_type, symbol, 
                self.collected_count, f"進行中{elapsed_time}"
            )

    def handle_collection_error(self, error_msg, exception=None):
        """
        處理收集錯誤
        
        Args:
            error_msg: 錯誤訊息
            exception: 例外物件
        """
        self.error_count += 1
        log_error_with_traceback(logger, error_msg, exception)
        
        # 如果錯誤太多，停止收集
        if self.error_count > 100:
            logger.error("❌ 錯誤次數過多，停止資料收集")
            self.stop_collection()

    def start_collection_log(self, collection_type, symbol, parameters=None):
        """
        開始收集記錄
        
        Args:
            collection_type: 收集類型
            symbol: 商品代碼
            parameters: 收集參數
            
        Returns:
            int: 記錄ID
        """
        try:
            self.start_time = datetime.now()
            self.collected_count = 0
            self.error_count = 0
            
            if self.db_manager:
                self.collection_log_id = self.db_manager.log_collection_start(
                    collection_type, symbol, parameters
                )
            
            logger.info(f"🚀 開始收集 {collection_type} 資料 - 商品: {symbol}")
            return self.collection_log_id
            
        except Exception as e:
            log_error_with_traceback(logger, "開始收集記錄失敗", e)
            return None

    def end_collection_log(self, status='COMPLETED', error_message=None):
        """
        結束收集記錄
        
        Args:
            status: 完成狀態
            error_message: 錯誤訊息
        """
        try:
            if self.db_manager and self.collection_log_id:
                self.db_manager.log_collection_end(
                    self.collection_log_id, self.collected_count, 
                    status, error_message
                )
            
            elapsed_time = ""
            if self.start_time:
                elapsed = datetime.now() - self.start_time
                elapsed_time = f" (總耗時: {elapsed.total_seconds():.1f}秒)"
            
            if status == 'COMPLETED':
                logger.info(f"✅ 資料收集完成 - 共收集 {self.collected_count:,} 筆資料{elapsed_time}")
            else:
                logger.error(f"❌ 資料收集失敗 - 狀態: {status}, 錯誤: {error_message}")
                
        except Exception as e:
            log_error_with_traceback(logger, "結束收集記錄失敗", e)

    def get_collection_stats(self):
        """
        取得收集統計資訊
        
        Returns:
            dict: 統計資訊
        """
        elapsed_time = 0
        if self.start_time:
            elapsed_time = (datetime.now() - self.start_time).total_seconds()
        
        return {
            'is_collecting': self.is_collecting,
            'collected_count': self.collected_count,
            'error_count': self.error_count,
            'elapsed_time': elapsed_time,
            'start_time': format_display_datetime(self.start_time) if self.start_time else None
        }

    def reset_stats(self):
        """重置統計資訊"""
        self.collected_count = 0
        self.error_count = 0
        self.start_time = None
        self.collection_log_id = None
