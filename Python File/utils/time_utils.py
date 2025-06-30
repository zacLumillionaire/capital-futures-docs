#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
時間工具模組
用於策略交易系統的時間判斷和管理
"""

from datetime import datetime, time, date, timedelta
from typing import Tuple, Optional
import logging

logger = logging.getLogger(__name__)

class TradingTimeManager:
    """交易時間管理器"""
    
    # 台灣期貨交易時間定義
    RANGE_START_TIME = time(8, 46, 0)      # 開盤區間開始 08:46:00
    RANGE_END_TIME = time(8, 47, 59)       # 開盤區間結束 08:47:59
    TRADING_START_TIME = time(8, 48, 0)    # 交易開始時間 08:48:00
    TRADING_END_TIME = time(13, 45, 0)     # 交易結束時間 13:45:00
    MARKET_CLOSE_TIME = time(13, 45, 0)    # 收盤時間 13:45:00
    
    # 夜盤時間 (如果需要)
    NIGHT_START_TIME = time(15, 0, 0)      # 夜盤開始 15:00:00
    NIGHT_END_TIME = time(5, 0, 0)         # 夜盤結束 05:00:00 (隔日)
    
    def __init__(self, enable_night_trading: bool = False):
        """
        初始化交易時間管理器
        
        Args:
            enable_night_trading: 是否啟用夜盤交易
        """
        self.enable_night_trading = enable_night_trading
        
    def is_range_monitoring_time(self, current_time: time) -> bool:
        """
        檢查是否為開盤區間監控時間 (08:46:00 - 08:47:59)
        
        Args:
            current_time: 當前時間
            
        Returns:
            是否為開盤區間監控時間
        """
        return self.RANGE_START_TIME <= current_time <= self.RANGE_END_TIME
    
    def is_trading_time(self, current_time: time) -> bool:
        """
        檢查是否為交易時間 (08:48:00 - 13:45:00)
        
        Args:
            current_time: 當前時間
            
        Returns:
            是否為交易時間
        """
        # 日盤交易時間
        day_trading = self.TRADING_START_TIME <= current_time <= self.TRADING_END_TIME
        
        if not self.enable_night_trading:
            return day_trading
        
        # 夜盤交易時間 (跨日)
        night_trading = (current_time >= self.NIGHT_START_TIME or 
                        current_time <= self.NIGHT_END_TIME)
        
        return day_trading or night_trading
    
    def is_market_open(self, current_datetime: datetime = None) -> bool:
        """
        檢查市場是否開盤
        
        Args:
            current_datetime: 當前日期時間，預設為現在
            
        Returns:
            市場是否開盤
        """
        if current_datetime is None:
            current_datetime = datetime.now()
        
        # 檢查是否為交易日 (週一到週五)
        if current_datetime.weekday() >= 5:  # 週六=5, 週日=6
            return False
        
        current_time = current_datetime.time()
        return self.is_trading_time(current_time)
    
    def is_closing_time(self, current_time: time) -> bool:
        """
        檢查是否為收盤時間
        
        Args:
            current_time: 當前時間
            
        Returns:
            是否為收盤時間
        """
        return current_time >= self.MARKET_CLOSE_TIME
    
    def get_next_trading_day(self, current_date: date = None) -> date:
        """
        取得下一個交易日
        
        Args:
            current_date: 當前日期，預設為今天
            
        Returns:
            下一個交易日
        """
        if current_date is None:
            current_date = date.today()
        
        next_date = current_date + timedelta(days=1)
        
        # 跳過週末
        while next_date.weekday() >= 5:
            next_date += timedelta(days=1)
        
        return next_date
    
    def get_trading_session_info(self, current_datetime: datetime = None) -> dict:
        """
        取得當前交易時段資訊
        
        Args:
            current_datetime: 當前日期時間，預設為現在
            
        Returns:
            交易時段資訊字典
        """
        if current_datetime is None:
            current_datetime = datetime.now()
        
        current_time = current_datetime.time()
        current_date = current_datetime.date()
        
        info = {
            'current_time': current_time,
            'current_date': current_date,
            'is_trading_day': current_datetime.weekday() < 5,
            'is_range_monitoring': self.is_range_monitoring_time(current_time),
            'is_trading_time': self.is_trading_time(current_time),
            'is_market_open': self.is_market_open(current_datetime),
            'is_closing_time': self.is_closing_time(current_time),
            'session': self._get_current_session(current_time)
        }
        
        return info
    
    def _get_current_session(self, current_time: time) -> str:
        """取得當前交易時段名稱"""
        if self.is_range_monitoring_time(current_time):
            return "RANGE_MONITORING"
        elif self.is_trading_time(current_time):
            if current_time <= self.MARKET_CLOSE_TIME:
                return "DAY_TRADING"
            else:
                return "NIGHT_TRADING"
        elif current_time < self.RANGE_START_TIME:
            return "PRE_MARKET"
        elif current_time > self.MARKET_CLOSE_TIME:
            return "POST_MARKET"
        else:
            return "UNKNOWN"
    
    def time_until_next_session(self, target_session: str, 
                               current_datetime: datetime = None) -> Optional[timedelta]:
        """
        計算距離下一個指定時段的時間
        
        Args:
            target_session: 目標時段 ('RANGE_MONITORING', 'TRADING', 'CLOSING')
            current_datetime: 當前日期時間
            
        Returns:
            距離目標時段的時間差，如果已經在目標時段則返回None
        """
        if current_datetime is None:
            current_datetime = datetime.now()
        
        current_time = current_datetime.time()
        current_date = current_datetime.date()
        
        if target_session == "RANGE_MONITORING":
            target_time = self.RANGE_START_TIME
            if current_time >= target_time and current_time <= self.RANGE_END_TIME:
                return None  # 已經在區間監控時段
        elif target_session == "TRADING":
            target_time = self.TRADING_START_TIME
            if self.is_trading_time(current_time):
                return None  # 已經在交易時段
        elif target_session == "CLOSING":
            target_time = self.MARKET_CLOSE_TIME
            if current_time >= target_time:
                return None  # 已經收盤
        else:
            return None
        
        # 計算目標時間
        target_datetime = datetime.combine(current_date, target_time)
        
        # 如果目標時間已過，則計算明天的目標時間
        if current_datetime >= target_datetime:
            next_trading_day = self.get_next_trading_day(current_date)
            target_datetime = datetime.combine(next_trading_day, target_time)
        
        return target_datetime - current_datetime
    
    def format_time_until(self, target_session: str) -> str:
        """
        格式化顯示距離目標時段的時間
        
        Args:
            target_session: 目標時段
            
        Returns:
            格式化的時間字串
        """
        time_diff = self.time_until_next_session(target_session)
        
        if time_diff is None:
            return f"目前正在 {target_session} 時段"
        
        total_seconds = int(time_diff.total_seconds())
        hours = total_seconds // 3600
        minutes = (total_seconds % 3600) // 60
        seconds = total_seconds % 60
        
        if hours > 0:
            return f"距離 {target_session} 還有 {hours}小時{minutes}分{seconds}秒"
        elif minutes > 0:
            return f"距離 {target_session} 還有 {minutes}分{seconds}秒"
        else:
            return f"距離 {target_session} 還有 {seconds}秒"

def get_current_trading_session() -> dict:
    """取得當前交易時段資訊的便利函數"""
    manager = TradingTimeManager()
    return manager.get_trading_session_info()

def is_trading_time_now() -> bool:
    """檢查現在是否為交易時間的便利函數"""
    manager = TradingTimeManager()
    return manager.is_trading_time(datetime.now().time())

def is_range_monitoring_time_now() -> bool:
    """檢查現在是否為開盤區間監控時間的便利函數"""
    manager = TradingTimeManager()
    return manager.is_range_monitoring_time(datetime.now().time())

def format_trading_time_status() -> str:
    """格式化當前交易時間狀態"""
    session_info = get_current_trading_session()
    
    status_parts = []
    
    if session_info['is_trading_day']:
        if session_info['is_range_monitoring']:
            status_parts.append("🔍 開盤區間監控中")
        elif session_info['is_trading_time']:
            status_parts.append("📈 交易時間")
        elif session_info['is_closing_time']:
            status_parts.append("🔚 已收盤")
        else:
            status_parts.append("⏰ 非交易時間")
    else:
        status_parts.append("📅 非交易日")
    
    status_parts.append(f"時段: {session_info['session']}")
    status_parts.append(f"時間: {session_info['current_time'].strftime('%H:%M:%S')}")
    
    return " | ".join(status_parts)

if __name__ == "__main__":
    # 測試時間工具
    print("🧪 測試交易時間管理器")
    
    manager = TradingTimeManager()
    
    # 測試不同時間點
    test_times = [
        time(8, 45, 0),   # 開盤前
        time(8, 46, 30),  # 開盤區間
        time(8, 48, 0),   # 交易開始
        time(10, 30, 0),  # 交易中
        time(13, 45, 0),  # 收盤
        time(15, 0, 0),   # 收盤後
    ]
    
    for test_time in test_times:
        print(f"\n時間: {test_time}")
        print(f"  開盤區間監控: {manager.is_range_monitoring_time(test_time)}")
        print(f"  交易時間: {manager.is_trading_time(test_time)}")
        print(f"  收盤時間: {manager.is_closing_time(test_time)}")
    
    # 測試當前狀態
    print(f"\n當前狀態: {format_trading_time_status()}")
    
    # 測試時間計算
    print(f"距離開盤區間: {manager.format_time_until('RANGE_MONITORING')}")
    print(f"距離交易開始: {manager.format_time_until('TRADING')}")
    
    print("✅ 時間工具測試完成")
