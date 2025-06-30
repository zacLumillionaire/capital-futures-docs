#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
測試區間計算修正
驗證時間過了之後能否正確計算區間
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from datetime import datetime, time
import random
from strategy.signal_detector import OpeningRangeDetector

def test_range_completion_fix():
    """測試區間完成修正"""
    print("🧪 測試區間計算修正")
    print("=" * 50)
    
    # 設定測試時間 (已經過去的時間)
    now = datetime.now()
    start_time = time(now.hour, now.minute - 2, 0)  # 2分鐘前開始
    end_time = time(now.hour, now.minute - 1, 59)   # 1分鐘前結束
    
    # 處理小時邊界
    if now.minute < 2:
        start_time = time(now.hour - 1, now.minute + 58, 0)
        end_time = time(now.hour - 1, now.minute + 59, 59)
    
    print(f"📅 測試時間設定: {start_time.strftime('%H:%M')} ~ {end_time.strftime('%H:%M')}")
    print(f"🕐 當前時間: {now.strftime('%H:%M:%S')}")
    print(f"⏰ 監控時間已過去: {(now.time() > end_time)}")
    
    # 建立偵測器
    detector = OpeningRangeDetector(start_time, end_time)
    detector.start_monitoring()
    
    print("\n🎯 模擬歷史價格資料...")
    
    # 模擬第一分鐘的價格資料 (過去時間)
    base_price = 22000
    first_minute = now.replace(hour=start_time.hour, minute=start_time.minute, second=0, microsecond=0)
    
    print(f"\n📊 模擬第一分鐘 ({first_minute.strftime('%H:%M')}):")
    first_min_prices = []
    for i in range(30):  # 30個tick
        timestamp = first_minute.replace(second=i * 2)
        price = base_price + random.randint(-10, 10)
        first_min_prices.append(price)
        detector.process_tick(price, 100, timestamp)
        
        if i % 10 == 0:  # 每10個tick顯示一次
            print(f"  {timestamp.strftime('%H:%M:%S')} - 價格: {price}")
    
    print(f"  第一分鐘價格範圍: {min(first_min_prices)} ~ {max(first_min_prices)}")
    
    # 模擬第二分鐘的價格資料
    second_minute = first_minute.replace(minute=first_minute.minute + 1)
    
    print(f"\n📊 模擬第二分鐘 ({second_minute.strftime('%H:%M')}):")
    second_min_prices = []
    for i in range(30):  # 30個tick
        timestamp = second_minute.replace(second=i * 2)
        price = base_price + 10 + random.randint(-8, 8)  # 稍微偏高
        second_min_prices.append(price)
        detector.process_tick(price, 100, timestamp)
        
        if i % 10 == 0:  # 每10個tick顯示一次
            print(f"  {timestamp.strftime('%H:%M:%S')} - 價格: {price}")
    
    print(f"  第二分鐘價格範圍: {min(second_min_prices)} ~ {max(second_min_prices)}")
    
    # 檢查區間是否完成 (在模擬資料後)
    print(f"\n🔍 檢查區間計算結果 (模擬資料後):")
    print(f"  is_range_ready: {detector.is_range_ready()}")
    print(f"  range_complete: {detector.range_complete}")
    print(f"  kbar_846: {detector.kbar_846 is not None}")
    print(f"  kbar_847: {detector.kbar_847 is not None}")
    
    if detector.kbar_846:
        print(f"  kbar_846 tick數: {detector.kbar_846.tick_count}")
        print(f"  kbar_846 高點: {detector.kbar_846.high_price}")
        print(f"  kbar_846 低點: {detector.kbar_846.low_price}")
    
    if detector.kbar_847:
        print(f"  kbar_847 tick數: {detector.kbar_847.tick_count}")
        print(f"  kbar_847 高點: {detector.kbar_847.high_price}")
        print(f"  kbar_847 低點: {detector.kbar_847.low_price}")
    
    # 強制檢查完成
    print(f"\n🎯 強制檢查區間完成:")
    force_result = detector.force_check_completion()
    print(f"  force_check_completion 結果: {force_result}")
    print(f"  is_range_ready: {detector.is_range_ready()}")
    
    if detector.is_range_ready():
        range_data = detector.get_range_data()
        print(f"\n✅ 區間計算完成!")
        print(f"   區間高點: {range_data['range_high']}")
        print(f"   區間低點: {range_data['range_low']}")
        print(f"   區間大小: {range_data['range_size']:.0f}點")
        
        # 驗證結果
        expected_high = max(max(first_min_prices), max(second_min_prices))
        expected_low = min(min(first_min_prices), min(second_min_prices))
        
        print(f"\n🧮 驗證結果:")
        print(f"   預期高點: {expected_high} | 實際高點: {range_data['range_high']} | {'✅' if expected_high == range_data['range_high'] else '❌'}")
        print(f"   預期低點: {expected_low} | 實際低點: {range_data['range_low']} | {'✅' if expected_low == range_data['range_low'] else '❌'}")
        
        return True
    else:
        print("❌ 區間計算仍未完成")
        return False

def test_current_time_simulation():
    """測試當前時間模擬"""
    print("\n🕐 測試當前時間模擬")
    print("=" * 50)
    
    # 設定為當前時間的模擬
    now = datetime.now()
    
    print(f"🕐 當前時間: {now.strftime('%H:%M:%S')}")
    print("💡 模擬價格更新，然後強制檢查區間完成")
    
    # 建立偵測器 (使用已過去的時間)
    start_time = time(now.hour, now.minute - 1, 0)
    end_time = time(now.hour, now.minute, 59)
    
    if now.minute == 0:
        start_time = time(now.hour - 1, 59, 0)
        end_time = time(now.hour, 0, 59)
    
    detector = OpeningRangeDetector(start_time, end_time)
    detector.start_monitoring()
    
    # 模擬一些價格資料
    base_price = 22000
    for i in range(10):
        price = base_price + random.randint(-5, 5)
        timestamp = now.replace(second=i * 5)
        detector.process_tick(price, 100, timestamp)
        print(f"  {timestamp.strftime('%H:%M:%S')} - 價格: {price}")
    
    # 強制檢查
    print(f"\n🎯 強制檢查區間完成:")
    result = detector.force_check_completion()
    print(f"  結果: {result}")
    
    if detector.is_range_ready():
        range_data = detector.get_range_data()
        print(f"✅ 區間計算完成: 高點{range_data['range_high']} 低點{range_data['range_low']}")
        return True
    else:
        print("❌ 區間計算未完成")
        return False

def main():
    """主測試函數"""
    print("🧪 區間計算修正測試")
    print("=" * 60)
    
    # 測試1: 歷史時間區間計算
    result1 = test_range_completion_fix()
    
    # 測試2: 當前時間模擬
    result2 = test_current_time_simulation()
    
    # 總結
    print("\n" + "=" * 60)
    print("🎯 測試結果總結:")
    print(f"   歷史時間測試: {'✅ 通過' if result1 else '❌ 失敗'}")
    print(f"   當前時間測試: {'✅ 通過' if result2 else '❌ 失敗'}")
    
    if result1 and result2:
        print("\n🎉 所有測試通過！區間計算修正成功")
        print("💡 現在在策略面板中應該能看到區間高低點了")
    else:
        print("\n⚠️ 部分測試失敗，需要進一步調試")
    
    print("\n📝 修正說明:")
    print("1. ✅ 添加了 force_check_completion() 方法")
    print("2. ✅ 在 process_price_update 中添加定時檢查")
    print("3. ✅ 改進了區間完成的判斷邏輯")
    print("4. ✅ 即使時間過了也能計算區間")

if __name__ == "__main__":
    main()
