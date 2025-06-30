#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
測試開盤區間偵測功能
驗證時間設定和區間計算是否正常
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from datetime import datetime, time
import random
import time as time_module
from strategy.signal_detector import OpeningRangeDetector

def test_range_detection_with_custom_time():
    """測試自定義時間的區間偵測"""
    print("🧪 測試開盤區間偵測功能")
    print("=" * 50)
    
    # 設定測試時間 (當前時間+1分鐘開始)
    now = datetime.now()
    start_time = time(now.hour, now.minute + 1, 0)
    end_time = time(now.hour, now.minute + 2, 59)
    
    # 處理分鐘數超過59的情況
    if now.minute + 1 >= 60:
        start_time = time(now.hour + 1, (now.minute + 1) % 60, 0)
    if now.minute + 2 >= 60:
        end_time = time(now.hour + 1, (now.minute + 2) % 60, 59)
    
    print(f"📅 測試時間設定: {start_time.strftime('%H:%M')} ~ {end_time.strftime('%H:%M')}")
    print(f"🕐 當前時間: {now.strftime('%H:%M:%S')}")
    
    # 建立偵測器
    detector = OpeningRangeDetector(start_time, end_time)
    detector.start_monitoring()
    
    print("🎯 開始模擬價格資料...")
    
    # 模擬第一分鐘的價格資料
    base_price = 22000
    first_minute = now.replace(minute=now.minute + 1, second=0, microsecond=0)
    
    print(f"\n📊 模擬第一分鐘 ({first_minute.strftime('%H:%M')}):")
    first_min_prices = []
    for i in range(60):  # 60秒的tick
        timestamp = first_minute.replace(second=i)
        price = base_price + random.randint(-10, 10)
        first_min_prices.append(price)
        detector.process_tick(price, 100, timestamp)
        
        if i % 15 == 0:  # 每15秒顯示一次
            print(f"  {timestamp.strftime('%H:%M:%S')} - 價格: {price}")
    
    print(f"  第一分鐘價格範圍: {min(first_min_prices)} ~ {max(first_min_prices)}")
    
    # 模擬第二分鐘的價格資料
    second_minute = first_minute.replace(minute=first_minute.minute + 1)

    print(f"\n📊 模擬第二分鐘 ({second_minute.strftime('%H:%M')}):")
    second_min_prices = []
    for i in range(60):  # 60秒的tick
        timestamp = second_minute.replace(second=i)
        price = base_price + 10 + random.randint(-8, 8)  # 稍微偏高
        second_min_prices.append(price)
        detector.process_tick(price, 100, timestamp)

        if i % 15 == 0:  # 每15秒顯示一次
            print(f"  {timestamp.strftime('%H:%M:%S')} - 價格: {price}")

    print(f"  第二分鐘價格範圍: {min(second_min_prices)} ~ {max(second_min_prices)}")

    # 模擬第三分鐘的第一個tick來觸發區間完成檢查
    third_minute = second_minute.replace(minute=second_minute.minute + 1, second=0)
    print(f"\n🔚 觸發區間完成檢查 ({third_minute.strftime('%H:%M:%S')}):")
    detector.process_tick(base_price, 100, third_minute)
    
    # 檢查區間是否完成
    print(f"\n🔍 檢查區間計算結果:")
    if detector.is_range_ready():
        range_data = detector.get_range_data()
        print(f"✅ 區間計算完成!")
        print(f"   區間高點: {range_data['range_high']}")
        print(f"   區間低點: {range_data['range_low']}")
        print(f"   區間大小: {range_data['range_size']:.0f}點")
        print(f"   計算時間: {range_data['completed_at']}")
        
        # 驗證結果
        expected_high = max(max(first_min_prices), max(second_min_prices))
        expected_low = min(min(first_min_prices), min(second_min_prices))
        
        print(f"\n🧮 驗證結果:")
        print(f"   預期高點: {expected_high} | 實際高點: {range_data['range_high']} | {'✅' if expected_high == range_data['range_high'] else '❌'}")
        print(f"   預期低點: {expected_low} | 實際低點: {range_data['range_low']} | {'✅' if expected_low == range_data['range_low'] else '❌'}")
        
        return True
    else:
        print("❌ 區間計算未完成")
        return False

def test_real_time_detection():
    """測試即時區間偵測"""
    print("\n🕐 測試即時區間偵測")
    print("=" * 50)
    
    # 設定為當前時間開始的2分鐘
    now = datetime.now()
    start_time = time(now.hour, now.minute, 0)
    end_time = time(now.hour, now.minute + 1, 59)
    
    # 處理分鐘數超過59的情況
    if now.minute + 1 >= 60:
        end_time = time(now.hour + 1, (now.minute + 1) % 60, 59)
    
    print(f"📅 即時測試時間: {start_time.strftime('%H:%M')} ~ {end_time.strftime('%H:%M')}")
    print(f"🕐 當前時間: {now.strftime('%H:%M:%S')}")
    
    # 建立偵測器
    detector = OpeningRangeDetector(start_time, end_time)
    detector.start_monitoring()
    
    print("🎯 開始即時價格模擬 (30秒)...")
    
    base_price = 22000
    start_timestamp = datetime.now()
    
    for i in range(30):  # 30秒測試
        current_time = datetime.now()
        price = base_price + random.randint(-5, 5)
        
        # 處理tick
        updated = detector.process_tick(price, 100, current_time)
        
        if updated and i % 5 == 0:
            print(f"  {current_time.strftime('%H:%M:%S')} - 價格: {price} | 已更新")
        
        # 檢查是否完成
        if detector.is_range_ready():
            range_data = detector.get_range_data()
            print(f"\n✅ 即時區間計算完成!")
            print(f"   區間高點: {range_data['range_high']}")
            print(f"   區間低點: {range_data['range_low']}")
            print(f"   區間大小: {range_data['range_size']:.0f}點")
            break
        
        time_module.sleep(1)  # 等待1秒
    
    return detector.is_range_ready()

def main():
    """主測試函數"""
    print("🧪 開盤區間偵測功能測試")
    print("=" * 60)
    
    # 測試1: 模擬資料測試
    print("📋 測試1: 模擬資料測試")
    result1 = test_range_detection_with_custom_time()
    
    # 測試2: 即時資料測試
    print("\n📋 測試2: 即時資料測試")
    result2 = test_real_time_detection()
    
    # 總結
    print("\n" + "=" * 60)
    print("🎯 測試結果總結:")
    print(f"   模擬資料測試: {'✅ 通過' if result1 else '❌ 失敗'}")
    print(f"   即時資料測試: {'✅ 通過' if result2 else '❌ 失敗'}")
    
    if result1 and result2:
        print("\n🎉 所有測試通過！開盤區間偵測功能正常運作")
        print("💡 您現在可以在策略面板中使用自定義時間功能")
    else:
        print("\n⚠️ 部分測試失敗，請檢查程式碼")
    
    print("\n📝 使用建議:")
    print("1. 在策略面板中點擊「手動設定未來時間」")
    print("2. 設定為當前時間+3分鐘")
    print("3. 點擊「🚀 啟動策略」")
    print("4. 開始價格模擬")
    print("5. 等待區間計算完成")

if __name__ == "__main__":
    main()
