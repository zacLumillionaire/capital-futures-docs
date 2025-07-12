#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
K線資料收集器 - 收集歷史K線資料
基於群益官方API實現，支援多種K線週期和交易時段
"""

import logging
import sys
import os
from datetime import datetime, timedelta

# 添加專案路徑
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from .base_collector import BaseCollector
from history_config import (
    DEFAULT_SYMBOL, KLINE_TYPES, TRADING_SESSIONS, 
    TRADING_SESSION_NAMES, DEFAULT_DATE_RANGE
)
from utils.date_utils import get_date_range, validate_date_format

logger = logging.getLogger(__name__)

class KLineCollector(BaseCollector):
    """K線資料收集器"""

    def __init__(self, skcom_manager, db_manager):
        """
        初始化K線資料收集器

        Args:
            skcom_manager: SKCOM API管理器
            db_manager: 資料庫管理器
        """
        super().__init__(skcom_manager, db_manager)
        self.kline_buffer = []
        self.current_symbol = None
        self.current_kline_type = None
        self.is_complete = False
        self.printed_count = 0  # 追蹤已列印的資料筆數

        # 註冊事件回調函數
        self._register_callbacks()

    def _register_callbacks(self):
        """註冊事件回調函數"""
        if self.skcom_manager:
            self.skcom_manager.on_kline_received = self.on_kline_received
            self.skcom_manager.on_kline_complete = self.on_kline_complete

    def start_collection(self, symbol=DEFAULT_SYMBOL, kline_type='MINUTE',
                        start_date=None, end_date=None, trading_session='ALL', 
                        minute_number=1):
        """
        開始收集K線資料
        
        Args:
            symbol: 商品代碼
            kline_type: K線類型 ('MINUTE', 'DAILY', 'WEEKLY', 'MONTHLY')
            start_date: 起始日期 (YYYYMMDD)，None表示使用預設範圍
            end_date: 結束日期 (YYYYMMDD)，None表示使用當前日期
            trading_session: 交易時段 ('ALL', 'AM_ONLY')
            minute_number: 分鐘數（當kline_type='MINUTE'時有效）
            
        Returns:
            bool: 是否成功開始收集
        """
        if not self.skcom_manager.is_ready_for_data_collection():
            logger.error("❌ SKCOM API未準備完成，無法開始收集K線資料")
            return False

        try:
            # 處理日期參數
            if not start_date or not end_date:
                start_date, end_date = get_date_range(DEFAULT_DATE_RANGE)
            
            # 驗證日期格式
            if not validate_date_format(start_date) or not validate_date_format(end_date):
                logger.error("❌ 日期格式錯誤，請使用 YYYYMMDD 格式")
                return False

            # 驗證K線類型
            if kline_type not in KLINE_TYPES:
                logger.error(f"❌ 不支援的K線類型: {kline_type}")
                return False

            # 驗證交易時段
            if trading_session not in TRADING_SESSIONS:
                logger.error(f"❌ 不支援的交易時段: {trading_session}")
                return False

            logger.info(f"🔄 開始收集 {symbol} K線資料...")
            logger.info(f"📊 參數: {kline_type}K線, {start_date}~{end_date}, {TRADING_SESSION_NAMES[trading_session]}")

            # 開始收集記錄
            self.start_collection_log('KLINE', symbol, {
                'kline_type': kline_type,
                'start_date': start_date,
                'end_date': end_date,
                'trading_session': trading_session,
                'minute_number': minute_number
            })

            self.is_collecting = True
            self.is_complete = False
            self.current_symbol = symbol
            self.current_kline_type = kline_type
            self.kline_buffer.clear()
            self.printed_count = 0  # 重置列印計數器

            # 轉換參數
            api_kline_type = KLINE_TYPES[kline_type]
            api_trading_session = TRADING_SESSIONS[trading_session]

            # 請求K線資料
            if not self.skcom_manager.request_kline_data(
                symbol, api_kline_type, start_date, end_date, 
                api_trading_session, minute_number):
                self.stop_collection()
                return False

            logger.info("✅ K線資料收集已啟動，等待資料回傳...")
            return True

        except Exception as e:
            self.handle_collection_error("開始收集K線資料失敗", e)
            self.stop_collection()
            return False

    def stop_collection(self):
        """停止收集K線資料"""
        try:
            self.is_collecting = False

            # 處理剩餘的緩衝區資料
            if self.kline_buffer:
                self._flush_buffer()

            # 結束收集記錄
            status = 'COMPLETED' if self.is_complete else 'STOPPED'
            self.end_collection_log(status)

        except Exception as e:
            self.handle_collection_error("停止收集K線資料失敗", e)
            self.end_collection_log('FAILED', str(e))

    def on_kline_received(self, stock_no, data):
        """
        處理K線資料事件
        
        Args:
            stock_no: 商品代碼
            data: K線資料字串，格式可能為：日期,時間,開,高,低,收,量
        """
        if not self.is_collecting:
            return

        try:
            # 解析K線資料字串
            data_parts = data.split(',')
            if len(data_parts) < 6:
                logger.warning(f"⚠️ K線資料格式不正確: {data}")
                return

            # 根據K線類型決定是否有時間欄位
            has_time = self.current_kline_type == 'MINUTE'
            
            if has_time and len(data_parts) >= 7:
                # 分線資料：日期,時間,開,高,低,收,量
                kline_data = {
                    'symbol': stock_no,
                    'kline_type': self.current_kline_type,
                    'trade_date': data_parts[0],
                    'trade_time': data_parts[1],
                    'open_price': self._parse_price(data_parts[2]),
                    'high_price': self._parse_price(data_parts[3]),
                    'low_price': self._parse_price(data_parts[4]),
                    'close_price': self._parse_price(data_parts[5]),
                    'volume': self._parse_volume(data_parts[6])
                }
            else:
                # 日線/週線/月線資料：日期,開,高,低,收,量
                kline_data = {
                    'symbol': stock_no,
                    'kline_type': self.current_kline_type,
                    'trade_date': data_parts[0],
                    'trade_time': None,
                    'open_price': self._parse_price(data_parts[1]),
                    'high_price': self._parse_price(data_parts[2]),
                    'low_price': self._parse_price(data_parts[3]),
                    'close_price': self._parse_price(data_parts[4]),
                    'volume': self._parse_volume(data_parts[5]) if len(data_parts) > 5 else None
                }

            # 驗證資料
            required_fields = ['symbol', 'trade_date', 'open_price', 'high_price', 
                             'low_price', 'close_price']
            if not self.validate_data(kline_data, required_fields):
                self.handle_collection_error("K線資料驗證失敗")
                return

            # 添加到緩衝區
            self.kline_buffer.append(kline_data)
            self.collected_count += 1

            # 列印前10行轉換後的資料到console
            if self.printed_count < 10:
                self.printed_count += 1
                print(f"\n=== 第 {self.printed_count} 筆轉換後的K線資料 ===")
                print(f"原始資料: {data}")
                print(f"轉換後資料:")
                print(f"  商品代碼: {kline_data['symbol']}")
                print(f"  K線類型: {kline_data['kline_type']}")
                print(f"  交易日期: {kline_data['trade_date']}")
                print(f"  交易時間: {kline_data['trade_time']}")
                print(f"  開盤價: {kline_data['open_price']}")
                print(f"  最高價: {kline_data['high_price']}")
                print(f"  最低價: {kline_data['low_price']}")
                print(f"  收盤價: {kline_data['close_price']}")
                print(f"  成交量: {kline_data['volume']}")
                print("=" * 50)

            # 記錄進度
            self.log_collection_progress('KLINE', self.current_symbol, 100)

            # 詳細日誌（可選）
            if logger.isEnabledFor(logging.DEBUG):
                ohlc = f"O:{kline_data['open_price']} H:{kline_data['high_price']} L:{kline_data['low_price']} C:{kline_data['close_price']}"
                time_info = f" @{kline_data['trade_time']}" if kline_data['trade_time'] else ""
                logger.debug(f"📈 K線: {ohlc} V:{kline_data['volume']} {kline_data['trade_date']}{time_info}")

        except Exception as e:
            self.handle_collection_error("處理K線資料失敗", e)

    def on_kline_complete(self, end_string):
        """
        K線查詢完成事件
        
        Args:
            end_string: 結束字串，通常為 "##"
        """
        if end_string == "##":
            logger.info("✅ K線資料查詢完成")
            self.is_complete = True

            # 處理剩餘的緩衝區資料
            if self.kline_buffer:
                self._flush_buffer()

            self.stop_collection()

    def _parse_price(self, price_str):
        """解析價格字串"""
        try:
            if not price_str or price_str.strip() == '':
                return None
            return float(price_str)
        except (ValueError, TypeError):
            return None

    def _parse_volume(self, volume_str):
        """解析成交量字串"""
        try:
            if not volume_str or volume_str.strip() == '':
                return None
            return int(float(volume_str))
        except (ValueError, TypeError):
            return None

    def _flush_buffer(self):
        """清空緩衝區並批量插入資料庫"""
        if not self.kline_buffer or not self.db_manager:
            return

        try:
            self.db_manager.batch_insert_kline_data(self.kline_buffer)
            logger.debug(f"💾 批量插入 {len(self.kline_buffer)} 筆K線資料")
            self.kline_buffer.clear()
            
        except Exception as e:
            self.handle_collection_error("批量插入K線資料失敗", e)

    def get_buffer_status(self):
        """
        取得緩衝區狀態
        
        Returns:
            dict: 緩衝區狀態資訊
        """
        return {
            'buffer_size': len(self.kline_buffer),
            'is_complete': self.is_complete,
            'kline_type': self.current_kline_type
        }
