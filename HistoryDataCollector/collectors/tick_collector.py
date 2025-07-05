#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
逐筆資料收集器 - 收集歷史和即時逐筆報價
基於群益官方API實現，支援批量處理和錯誤重試
"""

import logging
import sys
import os
from datetime import datetime

# 添加專案路徑
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from .base_collector import BaseCollector
from history_config import BATCH_SIZE, DEFAULT_SYMBOL

logger = logging.getLogger(__name__)

class TickCollector(BaseCollector):
    """逐筆資料收集器"""

    def __init__(self, skcom_manager, db_manager):
        """
        初始化逐筆資料收集器
        
        Args:
            skcom_manager: SKCOM API管理器
            db_manager: 資料庫管理器
        """
        super().__init__(skcom_manager, db_manager)
        self.tick_buffer = []  # 批量插入緩衝區
        self.current_symbol = None
        self.printed_count = 0  # 追蹤已列印的資料筆數

        # 註冊事件回調函數
        self._register_callbacks()

    def _register_callbacks(self):
        """註冊事件回調函數"""
        if self.skcom_manager:
            self.skcom_manager.on_history_tick_received = self.on_history_tick_received
            self.skcom_manager.on_realtime_tick_received = self.on_realtime_tick_received

    def start_collection(self, symbol=DEFAULT_SYMBOL, page_no=0, collect_realtime=False):
        """
        開始收集逐筆資料
        
        Args:
            symbol: 商品代碼
            page_no: 頁數（歷史資料用）
            collect_realtime: 是否收集即時資料
            
        Returns:
            bool: 是否成功開始收集
        """
        if not self.skcom_manager.is_ready_for_data_collection():
            logger.error("❌ SKCOM API未準備完成，無法開始收集逐筆資料")
            return False

        try:
            logger.info(f"🔄 開始收集 {symbol} 逐筆資料...")
            
            # 開始收集記錄
            self.start_collection_log('TICK', symbol, {
                'page_no': page_no,
                'collect_realtime': collect_realtime
            })
            
            self.is_collecting = True
            self.current_symbol = symbol
            self.tick_buffer.clear()
            self.printed_count = 0  # 重置列印計數器

            # 請求歷史逐筆資料
            if not self.skcom_manager.request_history_ticks(symbol, page_no):
                self.stop_collection()
                return False

            logger.info("✅ 逐筆資料收集已啟動，等待資料回傳...")
            return True

        except Exception as e:
            self.handle_collection_error("開始收集逐筆資料失敗", e)
            self.stop_collection()
            return False

    def stop_collection(self):
        """停止收集逐筆資料"""
        try:
            self.is_collecting = False

            # 處理剩餘的緩衝區資料
            if self.tick_buffer:
                self._flush_buffer()

            # 結束收集記錄
            self.end_collection_log('COMPLETED')

        except Exception as e:
            self.handle_collection_error("停止收集逐筆資料失敗", e)
            self.end_collection_log('FAILED', str(e))

    def on_history_tick_received(self, sMarketNo, nIndex, nPtr, nDate, nTimehms,
                               nTimemillismicros, nBid, nAsk, nClose, nQty, nSimulate):
        """
        處理歷史逐筆資料事件
        
        Args:
            sMarketNo: 市場別代號
            nIndex: 系統索引代碼
            nPtr: 資料位址/成交明細順序
            nDate: 交易日期 (YYYYMMDD)
            nTimehms: 交易時間 (HHMMSS)
            nTimemillismicros: 毫秒微秒
            nBid: 買價
            nAsk: 賣價
            nClose: 成交價
            nQty: 成交量
            nSimulate: 揭示類型 (0:一般, 1:試算)
        """
        if not self.is_collecting:
            return

        try:
            # 格式化資料
            tick_data = {
                'symbol': self.current_symbol,
                'market_no': sMarketNo,
                'index_code': nIndex,
                'ptr': nPtr,
                'trade_date': str(nDate),
                'trade_time': str(nTimehms).zfill(6),
                'trade_time_ms': nTimemillismicros,
                'bid_price': self.format_price(nBid),
                'ask_price': self.format_price(nAsk),
                'close_price': self.format_price(nClose),
                'volume': nQty,
                'simulate_flag': nSimulate,
                'data_type': 'HISTORY'
            }

            # 驗證資料
            required_fields = ['symbol', 'trade_date', 'trade_time', 'close_price', 'volume']
            if not self.validate_data(tick_data, required_fields):
                self.handle_collection_error("歷史逐筆資料驗證失敗")
                return

            # 列印前10行轉換後的資料到console
            if self.printed_count < 10:
                self.printed_count += 1
                print(f"\n=== 第 {self.printed_count} 筆逐筆資料 ===")
                print(f"原始參數:")
                print(f"  市場別: {sMarketNo}")
                print(f"  日期: {nDate}")
                print(f"  時間: {nTimehms}")
                print(f"  毫秒: {nTimemillismicros}")
                print(f"  買價: {nBid}")
                print(f"  賣價: {nAsk}")
                print(f"  成交價: {nClose}")
                print(f"  成交量: {nQty}")
                print(f"轉換後資料:")
                print(f"  商品代碼: {tick_data['symbol']}")
                print(f"  交易日期: {tick_data['trade_date']}")
                print(f"  交易時間: {tick_data['trade_time']}")
                print(f"  買價: {tick_data['bid_price']}")
                print(f"  賣價: {tick_data['ask_price']}")
                print(f"  成交價: {tick_data['close_price']}")
                print(f"  成交量: {tick_data['volume']}")
                print(f"  毫秒: {tick_data['trade_time_ms']}")
                print("=" * 50)

            # 添加到緩衝區
            self.tick_buffer.append(tick_data)
            self.collected_count += 1

            # 批量插入
            if len(self.tick_buffer) >= BATCH_SIZE:
                self._flush_buffer()

            # 記錄進度
            self.log_collection_progress('TICK', self.current_symbol, 1000)

        except Exception as e:
            self.handle_collection_error("處理歷史逐筆資料失敗", e)

    def on_realtime_tick_received(self, sMarketNo, nIndex, nPtr, nDate, nTimehms,
                                nTimemillismicros, nBid, nAsk, nClose, nQty, nSimulate):
        """
        處理即時逐筆資料事件
        
        Args: 同 on_history_tick_received
        """
        if not self.is_collecting:
            return

        try:
            # 格式化資料
            tick_data = {
                'symbol': self.current_symbol,
                'market_no': sMarketNo,
                'index_code': nIndex,
                'ptr': nPtr,
                'trade_date': str(nDate),
                'trade_time': str(nTimehms).zfill(6),
                'trade_time_ms': nTimemillismicros,
                'bid_price': self.format_price(nBid),
                'ask_price': self.format_price(nAsk),
                'close_price': self.format_price(nClose),
                'volume': nQty,
                'simulate_flag': nSimulate,
                'data_type': 'REALTIME'
            }

            # 驗證資料
            required_fields = ['symbol', 'trade_date', 'trade_time', 'close_price', 'volume']
            if not self.validate_data(tick_data, required_fields):
                self.handle_collection_error("即時逐筆資料驗證失敗")
                return

            # 即時資料直接插入（不使用緩衝區）
            if self.db_manager:
                self.db_manager.insert_tick_data(tick_data)
                self.collected_count += 1

            logger.debug(f"📈 即時逐筆: {tick_data['close_price']} @{tick_data['trade_time']}")

        except Exception as e:
            self.handle_collection_error("處理即時逐筆資料失敗", e)

    def _flush_buffer(self):
        """清空緩衝區並批量插入資料庫"""
        if not self.tick_buffer or not self.db_manager:
            return

        try:
            self.db_manager.batch_insert_tick_data(self.tick_buffer)
            logger.debug(f"💾 批量插入 {len(self.tick_buffer)} 筆逐筆資料")
            self.tick_buffer.clear()
            
        except Exception as e:
            self.handle_collection_error("批量插入逐筆資料失敗", e)

    def get_buffer_status(self):
        """
        取得緩衝區狀態
        
        Returns:
            dict: 緩衝區狀態資訊
        """
        return {
            'buffer_size': len(self.tick_buffer),
            'buffer_limit': BATCH_SIZE,
            'buffer_usage': f"{len(self.tick_buffer)}/{BATCH_SIZE}"
        }
