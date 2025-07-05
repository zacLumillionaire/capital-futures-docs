#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
日期工具模組
提供日期格式轉換、驗證、計算等功能
"""

import re
from datetime import datetime, timedelta

def validate_date_format(date_str):
    """
    驗證日期格式是否為 YYYYMMDD
    
    Args:
        date_str: 日期字串
        
    Returns:
        bool: 格式是否正確
    """
    if not date_str or len(date_str) != 8:
        return False
    
    try:
        datetime.strptime(date_str, '%Y%m%d')
        return True
    except ValueError:
        return False

def format_date_to_api(date_obj):
    """
    將datetime物件格式化為API需要的格式 (YYYYMMDD)
    
    Args:
        date_obj: datetime物件
        
    Returns:
        str: YYYYMMDD格式的日期字串
    """
    if isinstance(date_obj, datetime):
        return date_obj.strftime('%Y%m%d')
    elif isinstance(date_obj, str):
        return date_obj
    else:
        return datetime.now().strftime('%Y%m%d')

def parse_api_date(date_str):
    """
    解析API回傳的日期字串 (YYYYMMDD) 為datetime物件
    
    Args:
        date_str: YYYYMMDD格式的日期字串
        
    Returns:
        datetime: 解析後的datetime物件，失敗時返回None
    """
    try:
        return datetime.strptime(str(date_str), '%Y%m%d')
    except ValueError:
        return None

def format_time_to_api(time_obj):
    """
    將時間格式化為API需要的格式 (HHMMSS)
    
    Args:
        time_obj: datetime物件或時間字串
        
    Returns:
        str: HHMMSS格式的時間字串
    """
    if isinstance(time_obj, datetime):
        return time_obj.strftime('%H%M%S')
    elif isinstance(time_obj, str):
        return time_obj.zfill(6)  # 補齊6位數
    else:
        return datetime.now().strftime('%H%M%S')

def parse_api_time(time_str):
    """
    解析API回傳的時間字串 (HHMMSS) 為時間元組
    
    Args:
        time_str: HHMMSS格式的時間字串
        
    Returns:
        tuple: (hour, minute, second)，失敗時返回None
    """
    try:
        time_str = str(time_str).zfill(6)
        hour = int(time_str[:2])
        minute = int(time_str[2:4])
        second = int(time_str[4:6])
        return (hour, minute, second)
    except (ValueError, IndexError):
        return None

def combine_date_time(date_str, time_str):
    """
    組合日期和時間字串為datetime物件
    
    Args:
        date_str: YYYYMMDD格式的日期字串
        time_str: HHMMSS格式的時間字串
        
    Returns:
        datetime: 組合後的datetime物件，失敗時返回None
    """
    try:
        date_str = str(date_str)
        time_str = str(time_str).zfill(6)
        
        datetime_str = f"{date_str}{time_str}"
        return datetime.strptime(datetime_str, '%Y%m%d%H%M%S')
    except ValueError:
        return None

def get_date_range(days_back=30):
    """
    取得指定天數前的日期範圍
    
    Args:
        days_back: 往前推算的天數
        
    Returns:
        tuple: (start_date, end_date) YYYYMMDD格式
    """
    end_date = datetime.now()
    start_date = end_date - timedelta(days=days_back)
    
    return (
        start_date.strftime('%Y%m%d'),
        end_date.strftime('%Y%m%d')
    )

def get_trading_dates(start_date, end_date):
    """
    取得指定範圍內的交易日期列表（排除週末）
    
    Args:
        start_date: 起始日期 (YYYYMMDD)
        end_date: 結束日期 (YYYYMMDD)
        
    Returns:
        list: 交易日期列表
    """
    try:
        start = datetime.strptime(start_date, '%Y%m%d')
        end = datetime.strptime(end_date, '%Y%m%d')
        
        trading_dates = []
        current = start
        
        while current <= end:
            # 排除週末 (週六=5, 週日=6)
            if current.weekday() < 5:
                trading_dates.append(current.strftime('%Y%m%d'))
            current += timedelta(days=1)
        
        return trading_dates
    except ValueError:
        return []

def is_trading_time(check_time=None):
    """
    檢查是否為交易時間
    
    Args:
        check_time: 要檢查的時間，預設為當前時間
        
    Returns:
        dict: {'is_trading': bool, 'session': str}
    """
    if check_time is None:
        check_time = datetime.now()
    
    # 檢查是否為週末
    if check_time.weekday() >= 5:
        return {'is_trading': False, 'session': 'WEEKEND'}
    
    time_str = check_time.strftime('%H%M')
    time_int = int(time_str)
    
    # 日盤時間 08:45-13:45
    if 845 <= time_int <= 1345:
        return {'is_trading': True, 'session': 'AM'}
    
    # 夜盤時間 15:00-05:00 (跨日)
    if time_int >= 1500 or time_int <= 500:
        return {'is_trading': True, 'session': 'PM'}
    
    return {'is_trading': False, 'session': 'CLOSED'}

def format_display_datetime(datetime_obj):
    """
    格式化datetime物件為顯示用的字串
    
    Args:
        datetime_obj: datetime物件
        
    Returns:
        str: 格式化後的字串 "YYYY-MM-DD HH:MM:SS"
    """
    if isinstance(datetime_obj, datetime):
        return datetime_obj.strftime('%Y-%m-%d %H:%M:%S')
    return str(datetime_obj)
