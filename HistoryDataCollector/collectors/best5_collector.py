#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
五檔資料收集器 - 收集歷史和即時五檔報價
基於群益官方API實現，支援完整的五檔買賣資訊
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

class Best5Collector(BaseCollector):
    """五檔資料收集器"""

    def __init__(self, skcom_manager, db_manager):
        """
        初始化五檔資料收集器
        
        Args:
            skcom_manager: SKCOM API管理器
            db_manager: 資料庫管理器
        """
        super().__init__(skcom_manager, db_manager)
        self.best5_buffer = []  # 批量插入緩衝區
        self.current_symbol = None
        self.printed_count = 0  # 追蹤已列印的資料筆數

        # 註冊事件回調函數
        self._register_callbacks()

    def _register_callbacks(self):
        """註冊事件回調函數"""
        if self.skcom_manager:
            self.skcom_manager.on_best5_received = self.on_best5_received

    def start_collection(self, symbol=DEFAULT_SYMBOL, page_no=0):
        """
        開始收集五檔資料
        
        Args:
            symbol: 商品代碼
            page_no: 頁數（歷史資料用）
            
        Returns:
            bool: 是否成功開始收集
        """
        if not self.skcom_manager.is_ready_for_data_collection():
            logger.error("❌ SKCOM API未準備完成，無法開始收集五檔資料")
            return False

        try:
            logger.info(f"🔄 開始收集 {symbol} 五檔資料...")
            
            # 開始收集記錄
            self.start_collection_log('BEST5', symbol, {'page_no': page_no})
            
            self.is_collecting = True
            self.current_symbol = symbol
            self.best5_buffer.clear()
            self.printed_count = 0  # 重置列印計數器

            # 五檔資料與逐筆資料使用相同的API
            if not self.skcom_manager.request_history_ticks(symbol, page_no):
                self.stop_collection()
                return False

            logger.info("✅ 五檔資料收集已啟動，等待資料回傳...")
            return True

        except Exception as e:
            self.handle_collection_error("開始收集五檔資料失敗", e)
            self.stop_collection()
            return False

    def stop_collection(self):
        """停止收集五檔資料"""
        try:
            self.is_collecting = False

            # 處理剩餘的緩衝區資料
            if self.best5_buffer:
                self._flush_buffer()

            # 結束收集記錄
            self.end_collection_log('COMPLETED')

        except Exception as e:
            self.handle_collection_error("停止收集五檔資料失敗", e)
            self.end_collection_log('FAILED', str(e))

    def on_best5_received(self, sMarketNo, nIndex, nBestBid1, nBestBidQty1, nBestBid2, nBestBidQty2,
                         nBestBid3, nBestBidQty3, nBestBid4, nBestBidQty4, nBestBid5, nBestBidQty5,
                         nExtendBid, nExtendBidQty, nBestAsk1, nBestAskQty1, nBestAsk2, nBestAskQty2,
                         nBestAsk3, nBestAskQty3, nBestAsk4, nBestAskQty4, nBestAsk5, nBestAskQty5,
                         nExtendAsk, nExtendAskQty, nSimulate):
        """
        處理五檔資料事件
        
        Args:
            sMarketNo: 市場別代號
            nIndex: 系統索引代碼
            nBestBid1~5: 五檔買價
            nBestBidQty1~5: 五檔買量
            nExtendBid: 延伸買價
            nExtendBidQty: 延伸買量
            nBestAsk1~5: 五檔賣價
            nBestAskQty1~5: 五檔賣量
            nExtendAsk: 延伸賣價
            nExtendAskQty: 延伸賣量
            nSimulate: 揭示類型
        """
        if not self.is_collecting:
            return

        try:
            # 取得當前時間作為時間戳記
            now = datetime.now()
            
            # 格式化資料
            best5_data = {
                'symbol': self.current_symbol,
                'market_no': sMarketNo,
                'index_code': nIndex,
                'trade_date': now.strftime('%Y%m%d'),
                'trade_time': now.strftime('%H%M%S'),
                
                # 五檔買價買量
                'bid_price_1': self.format_price(nBestBid1),
                'bid_volume_1': nBestBidQty1,
                'bid_price_2': self.format_price(nBestBid2),
                'bid_volume_2': nBestBidQty2,
                'bid_price_3': self.format_price(nBestBid3),
                'bid_volume_3': nBestBidQty3,
                'bid_price_4': self.format_price(nBestBid4),
                'bid_volume_4': nBestBidQty4,
                'bid_price_5': self.format_price(nBestBid5),
                'bid_volume_5': nBestBidQty5,
                
                # 五檔賣價賣量
                'ask_price_1': self.format_price(nBestAsk1),
                'ask_volume_1': nBestAskQty1,
                'ask_price_2': self.format_price(nBestAsk2),
                'ask_volume_2': nBestAskQty2,
                'ask_price_3': self.format_price(nBestAsk3),
                'ask_volume_3': nBestAskQty3,
                'ask_price_4': self.format_price(nBestAsk4),
                'ask_volume_4': nBestAskQty4,
                'ask_price_5': self.format_price(nBestAsk5),
                'ask_volume_5': nBestAskQty5,
                
                # 延伸買賣
                'extend_bid': self.format_price(nExtendBid),
                'extend_bid_qty': nExtendBidQty,
                'extend_ask': self.format_price(nExtendAsk),
                'extend_ask_qty': nExtendAskQty,
                'simulate_flag': nSimulate
            }

            # 驗證資料（至少要有一檔買價或賣價）
            required_fields = ['symbol', 'trade_date', 'trade_time']
            if not self.validate_data(best5_data, required_fields):
                self.handle_collection_error("五檔資料驗證失敗")
                return

            # 檢查是否有有效的買賣價格
            has_valid_data = (
                best5_data['bid_price_1'] is not None or 
                best5_data['ask_price_1'] is not None
            )
            
            if not has_valid_data:
                logger.debug("五檔資料無有效價格，跳過")
                return

            # 列印前10行轉換後的資料到console
            if self.printed_count < 10:
                self.printed_count += 1
                print(f"\n=== 第 {self.printed_count} 筆五檔資料 ===")
                print(f"原始參數:")
                print(f"  市場別: {sMarketNo}")
                print(f"  買1價: {nBestBid1}, 量: {nBestBidQty1}")
                print(f"  買2價: {nBestBid2}, 量: {nBestBidQty2}")
                print(f"  買3價: {nBestBid3}, 量: {nBestBidQty3}")
                print(f"  賣1價: {nBestAsk1}, 量: {nBestAskQty1}")
                print(f"  賣2價: {nBestAsk2}, 量: {nBestAskQty2}")
                print(f"  賣3價: {nBestAsk3}, 量: {nBestAskQty3}")
                print(f"轉換後資料:")
                print(f"  商品代碼: {best5_data['symbol']}")
                print(f"  交易日期: {best5_data['trade_date']}")
                print(f"  交易時間: {best5_data['trade_time']}")
                print(f"  買1: {best5_data['bid_price_1']} x {best5_data['bid_volume_1']}")
                print(f"  買2: {best5_data['bid_price_2']} x {best5_data['bid_volume_2']}")
                print(f"  買3: {best5_data['bid_price_3']} x {best5_data['bid_volume_3']}")
                print(f"  賣1: {best5_data['ask_price_1']} x {best5_data['ask_volume_1']}")
                print(f"  賣2: {best5_data['ask_price_2']} x {best5_data['ask_volume_2']}")
                print(f"  賣3: {best5_data['ask_price_3']} x {best5_data['ask_volume_3']}")
                print("=" * 50)

            # 添加到緩衝區
            self.best5_buffer.append(best5_data)
            self.collected_count += 1

            # 批量插入
            if len(self.best5_buffer) >= BATCH_SIZE:
                self._flush_buffer()

            # 記錄進度
            self.log_collection_progress('BEST5', self.current_symbol, 100)

            # 詳細日誌（可選）
            if logger.isEnabledFor(logging.DEBUG):
                bid1 = best5_data['bid_price_1']
                ask1 = best5_data['ask_price_1']
                logger.debug(f"📊 五檔: 買1={bid1} 賣1={ask1} @{best5_data['trade_time']}")

        except Exception as e:
            self.handle_collection_error("處理五檔資料失敗", e)

    def _flush_buffer(self):
        """清空緩衝區並批量插入資料庫"""
        if not self.best5_buffer or not self.db_manager:
            return

        try:
            self.db_manager.batch_insert_best5_data(self.best5_buffer)
            logger.debug(f"💾 批量插入 {len(self.best5_buffer)} 筆五檔資料")
            self.best5_buffer.clear()
            
        except Exception as e:
            self.handle_collection_error("批量插入五檔資料失敗", e)

    def get_buffer_status(self):
        """
        取得緩衝區狀態
        
        Returns:
            dict: 緩衝區狀態資訊
        """
        return {
            'buffer_size': len(self.best5_buffer),
            'buffer_limit': BATCH_SIZE,
            'buffer_usage': f"{len(self.best5_buffer)}/{BATCH_SIZE}"
        }

    def get_latest_best5(self):
        """
        取得最新的五檔資料（從緩衝區）
        
        Returns:
            dict: 最新五檔資料，無資料時返回None
        """
        if self.best5_buffer:
            return self.best5_buffer[-1].copy()
        return None
