#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
資料模型定義
定義各種資料結構的類別和驗證方法
"""

from dataclasses import dataclass
from datetime import datetime
from typing import Optional, Dict, Any
import logging

logger = logging.getLogger(__name__)

@dataclass
class TickData:
    """逐筆資料模型"""
    symbol: str
    trade_date: str
    trade_time: str
    close_price: float
    volume: int
    market_no: Optional[int] = None
    index_code: Optional[int] = None
    ptr: Optional[int] = None
    trade_time_ms: Optional[int] = None
    bid_price: Optional[float] = None
    ask_price: Optional[float] = None
    simulate_flag: int = 0
    data_type: str = 'HISTORY'
    created_at: Optional[datetime] = None

    def to_dict(self) -> Dict[str, Any]:
        """轉換為字典格式"""
        return {
            'symbol': self.symbol,
            'market_no': self.market_no,
            'index_code': self.index_code,
            'ptr': self.ptr,
            'trade_date': self.trade_date,
            'trade_time': self.trade_time,
            'trade_time_ms': self.trade_time_ms,
            'bid_price': self.bid_price,
            'ask_price': self.ask_price,
            'close_price': self.close_price,
            'volume': self.volume,
            'simulate_flag': self.simulate_flag,
            'data_type': self.data_type
        }

    def validate(self) -> bool:
        """驗證資料有效性"""
        try:
            # 必要欄位檢查
            if not self.symbol or not self.trade_date or not self.trade_time:
                return False
            if self.close_price is None or self.volume is None:
                return False
            
            # 格式檢查
            if len(self.trade_date) != 8 or len(self.trade_time) != 6:
                return False
            
            # 數值檢查
            if self.close_price <= 0 or self.volume < 0:
                return False
                
            return True
        except Exception:
            return False

@dataclass
class Best5Data:
    """五檔資料模型"""
    symbol: str
    trade_date: str
    trade_time: str
    market_no: Optional[int] = None
    index_code: Optional[int] = None
    
    # 五檔買價買量
    bid_price_1: Optional[float] = None
    bid_volume_1: Optional[int] = None
    bid_price_2: Optional[float] = None
    bid_volume_2: Optional[int] = None
    bid_price_3: Optional[float] = None
    bid_volume_3: Optional[int] = None
    bid_price_4: Optional[float] = None
    bid_volume_4: Optional[int] = None
    bid_price_5: Optional[float] = None
    bid_volume_5: Optional[int] = None
    
    # 五檔賣價賣量
    ask_price_1: Optional[float] = None
    ask_volume_1: Optional[int] = None
    ask_price_2: Optional[float] = None
    ask_volume_2: Optional[int] = None
    ask_price_3: Optional[float] = None
    ask_volume_3: Optional[int] = None
    ask_price_4: Optional[float] = None
    ask_volume_4: Optional[int] = None
    ask_price_5: Optional[float] = None
    ask_volume_5: Optional[int] = None
    
    # 延伸買賣
    extend_bid: Optional[float] = None
    extend_bid_qty: Optional[int] = None
    extend_ask: Optional[float] = None
    extend_ask_qty: Optional[int] = None
    
    simulate_flag: int = 0
    created_at: Optional[datetime] = None

    def to_dict(self) -> Dict[str, Any]:
        """轉換為字典格式"""
        return {
            'symbol': self.symbol,
            'market_no': self.market_no,
            'index_code': self.index_code,
            'trade_date': self.trade_date,
            'trade_time': self.trade_time,
            'bid_price_1': self.bid_price_1, 'bid_volume_1': self.bid_volume_1,
            'bid_price_2': self.bid_price_2, 'bid_volume_2': self.bid_volume_2,
            'bid_price_3': self.bid_price_3, 'bid_volume_3': self.bid_volume_3,
            'bid_price_4': self.bid_price_4, 'bid_volume_4': self.bid_volume_4,
            'bid_price_5': self.bid_price_5, 'bid_volume_5': self.bid_volume_5,
            'ask_price_1': self.ask_price_1, 'ask_volume_1': self.ask_volume_1,
            'ask_price_2': self.ask_price_2, 'ask_volume_2': self.ask_volume_2,
            'ask_price_3': self.ask_price_3, 'ask_volume_3': self.ask_volume_3,
            'ask_price_4': self.ask_price_4, 'ask_volume_4': self.ask_volume_4,
            'ask_price_5': self.ask_price_5, 'ask_volume_5': self.ask_volume_5,
            'extend_bid': self.extend_bid, 'extend_bid_qty': self.extend_bid_qty,
            'extend_ask': self.extend_ask, 'extend_ask_qty': self.extend_ask_qty,
            'simulate_flag': self.simulate_flag
        }

    def validate(self) -> bool:
        """驗證資料有效性"""
        try:
            # 必要欄位檢查
            if not self.symbol or not self.trade_date or not self.trade_time:
                return False
            
            # 格式檢查
            if len(self.trade_date) != 8 or len(self.trade_time) != 6:
                return False
            
            # 至少要有一檔買價或賣價
            has_valid_data = (
                self.bid_price_1 is not None or 
                self.ask_price_1 is not None
            )
            
            return has_valid_data
        except Exception:
            return False

@dataclass
class KLineData:
    """K線資料模型"""
    symbol: str
    kline_type: str
    trade_date: str
    open_price: float
    high_price: float
    low_price: float
    close_price: float
    trade_time: Optional[str] = None
    volume: Optional[int] = None
    created_at: Optional[datetime] = None

    def to_dict(self) -> Dict[str, Any]:
        """轉換為字典格式"""
        return {
            'symbol': self.symbol,
            'kline_type': self.kline_type,
            'trade_date': self.trade_date,
            'trade_time': self.trade_time,
            'open_price': self.open_price,
            'high_price': self.high_price,
            'low_price': self.low_price,
            'close_price': self.close_price,
            'volume': self.volume
        }

    def validate(self) -> bool:
        """驗證資料有效性"""
        try:
            # 必要欄位檢查
            if not self.symbol or not self.kline_type or not self.trade_date:
                return False
            if any(price is None for price in [self.open_price, self.high_price, 
                                             self.low_price, self.close_price]):
                return False
            
            # 格式檢查
            if len(self.trade_date) != 8:
                return False
            
            # 價格邏輯檢查
            if not (self.low_price <= self.open_price <= self.high_price and
                   self.low_price <= self.close_price <= self.high_price):
                return False
            
            # 數值檢查
            if any(price <= 0 for price in [self.open_price, self.high_price, 
                                          self.low_price, self.close_price]):
                return False
                
            return True
        except Exception:
            return False

@dataclass
class CollectionLog:
    """收集記錄模型"""
    collection_type: str
    symbol: str
    start_time: datetime
    end_time: Optional[datetime] = None
    records_count: int = 0
    status: str = 'RUNNING'
    error_message: Optional[str] = None
    parameters: Optional[Dict[str, Any]] = None
    created_at: Optional[datetime] = None

    def to_dict(self) -> Dict[str, Any]:
        """轉換為字典格式"""
        return {
            'collection_type': self.collection_type,
            'symbol': self.symbol,
            'start_time': self.start_time,
            'end_time': self.end_time,
            'records_count': self.records_count,
            'status': self.status,
            'error_message': self.error_message,
            'parameters': self.parameters
        }

class DataValidator:
    """資料驗證器"""
    
    @staticmethod
    def validate_symbol(symbol: str) -> bool:
        """驗證商品代碼"""
        if not symbol or not isinstance(symbol, str):
            return False
        return len(symbol.strip()) > 0
    
    @staticmethod
    def validate_date(date_str: str) -> bool:
        """驗證日期格式 YYYYMMDD"""
        if not date_str or len(date_str) != 8:
            return False
        try:
            datetime.strptime(date_str, '%Y%m%d')
            return True
        except ValueError:
            return False
    
    @staticmethod
    def validate_time(time_str: str) -> bool:
        """驗證時間格式 HHMMSS"""
        if not time_str or len(time_str) != 6:
            return False
        try:
            datetime.strptime(time_str, '%H%M%S')
            return True
        except ValueError:
            return False
    
    @staticmethod
    def validate_price(price: float) -> bool:
        """驗證價格"""
        return price is not None and price > 0
    
    @staticmethod
    def validate_volume(volume: int) -> bool:
        """驗證成交量"""
        return volume is not None and volume >= 0
