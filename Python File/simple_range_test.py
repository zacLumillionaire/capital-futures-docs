#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
簡單的區間偵測測試
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from datetime import datetime, time
from strategy.signal_detector import OpeningRangeDetector

def simple_test():
    """簡單測試"""
    print("🧪 簡單區間偵測測試")
    print("=" * 40)
    
    # 設定測試時間
    now = datetime.now()
    start_time = time(now.hour, now.minute, 0)
    end_time = time(now.hour, now.minute + 1, 59)
    
    print(f"測試時間: {start_time.strftime('%H:%M')} ~ {end_time.strftime('%H:%M')}")
    
    # 建立偵測器
    detector = OpeningRangeDetector(start_time, end_time)
    detector.start_monitoring()
    
    print("開始模擬資料...")
    
    # 模擬第一分鐘
    base_time = now.replace(second=0, microsecond=0)
    for i in range(5):  # 只模擬5個tick
        timestamp = base_time.replace(second=i * 10)
        price = 22000 + i
        result = detector.process_tick(price, 100, timestamp)
        print(f"  {timestamp.strftime('%H:%M:%S')} - 價格: {price} - 處理結果: {result}")
    
    # 模擬第二分鐘
    second_minute = base_time.replace(minute=base_time.minute + 1)
    for i in range(5):  # 只模擬5個tick
        timestamp = second_minute.replace(second=i * 10)
        price = 22010 + i
        result = detector.process_tick(price, 100, timestamp)
        print(f"  {timestamp.strftime('%H:%M:%S')} - 價格: {price} - 處理結果: {result}")
    
    # 觸發完成檢查
    trigger_time = second_minute.replace(minute=second_minute.minute + 1, second=0)
    print(f"\n觸發完成檢查: {trigger_time.strftime('%H:%M:%S')}")
    detector.process_tick(22000, 100, trigger_time)
    
    # 檢查結果
    print(f"\n檢查結果:")
    print(f"  is_range_ready: {detector.is_range_ready()}")
    print(f"  range_complete: {detector.range_complete}")
    print(f"  kbar_846: {detector.kbar_846 is not None}")
    print(f"  kbar_847: {detector.kbar_847 is not None}")
    
    if detector.kbar_846:
        print(f"  kbar_846 完整: {detector.kbar_846.is_complete()}")
        print(f"  kbar_846 高點: {detector.kbar_846.high_price}")
        print(f"  kbar_846 低點: {detector.kbar_846.low_price}")
    
    if detector.kbar_847:
        print(f"  kbar_847 完整: {detector.kbar_847.is_complete()}")
        print(f"  kbar_847 高點: {detector.kbar_847.high_price}")
        print(f"  kbar_847 低點: {detector.kbar_847.low_price}")
    
    range_data = detector.get_range_data()
    if range_data:
        print(f"\n✅ 區間資料:")
        print(f"  高點: {range_data['range_high']}")
        print(f"  低點: {range_data['range_low']}")
        print(f"  大小: {range_data['range_size']:.0f}點")
    else:
        print(f"\n❌ 無區間資料")

if __name__ == "__main__":
    simple_test()
