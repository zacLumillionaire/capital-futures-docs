#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
簡單的收盤平倉邏輯測試
"""

def test_eod_logic():
    """測試收盤平倉邏輯"""
    print("🧪 測試收盤平倉邏輯")
    print("=" * 40)
    
    test_times = [
        ("08:46:00", "開盤區間"),
        ("12:30:00", "收盤前1小時"),
        ("13:29:59", "收盤前1秒"),
        ("13:30:00", "收盤時間"),
        ("13:30:01", "收盤後1秒"),
        ("18:38:00", "您的測試時間")
    ]
    
    for time_str, description in test_times:
        try:
            hour, minute, second = map(int, time_str.split(':'))
            is_eod = hour >= 13 and minute >= 30
            
            print(f"⏰ {time_str} ({description})")
            print(f"   解析: {hour:02d}時{minute:02d}分{second:02d}秒")
            print(f"   收盤平倉: {'✅ 觸發' if is_eod else '❌ 不觸發'}")
            
            if is_eod:
                print(f"   原因: {hour} >= 13 且 {minute} >= 30")
            print()
            
        except Exception as e:
            print(f"❌ {time_str} 解析失敗: {e}")
    
    print("📋 問題分析:")
    print("✅ 您的LOG時間 18:38:00 確實會觸發收盤平倉")
    print("✅ 因為 18 >= 13 且 38 >= 30")
    print("✅ 這就是下單後立即平倉的原因")
    
    print("\n💡 解決方案:")
    print("1. 停用收盤平倉控制開關（推薦測試階段）")
    print("2. 修改收盤時間為更晚時間（如15:00）")
    print("3. 添加時間範圍檢查（如只在交易時間內生效）")

if __name__ == "__main__":
    test_eod_logic()
