#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
時間範圍解析功能測試腳本
測試新實現的自定義時間區段功能
"""

import sys
import os

# 添加路徑以便導入虛擬機模組
sys.path.append(os.path.join(os.path.dirname(__file__), 'Capital_Official_Framework'))

def test_time_parsing():
    """測試時間解析功能"""
    print("🧪 [TEST] 開始測試時間範圍解析功能")
    print("=" * 50)
    
    # 創建測試類來模擬時間解析方法
    class TimeRangeParser:
        def __init__(self):
            pass
            
        def _parse_single_time(self, time_str):
            """解析單一時間字串"""
            try:
                time_str = time_str.strip()
                parts = time_str.split(':')
                
                if len(parts) == 2:
                    hour, minute = map(int, parts)
                    second = 0
                    return (hour, minute, second)
                elif len(parts) == 3:
                    hour, minute, second = map(int, parts)
                    return (hour, minute, second)
                else:
                    raise ValueError(f"時間格式錯誤: {time_str}")
                    
            except Exception as e:
                raise ValueError(f"解析時間失敗: {time_str} - {e}")

        def _parse_time_range(self, time_input):
            """解析時間範圍輸入"""
            try:
                time_input = time_input.strip()
                
                if ' - ' in time_input:
                    # 範圍格式：'10:15 - 10:30'
                    start_str, end_str = time_input.split(' - ', 1)
                    start_time = self._parse_single_time(start_str)
                    end_time = self._parse_single_time(end_str)
                    
                    # 關鍵邏輯：10:15 - 10:30 實際代表 10:15:01 - 10:30:00
                    if start_time[2] == 0:  # 如果開始時間沒有指定秒數
                        start_time = (start_time[0], start_time[1], 1)  # 設為01秒
                    if end_time[2] == 0:    # 如果結束時間沒有指定秒數
                        end_time = (end_time[0], end_time[1], 0)       # 保持00秒
                        
                    return start_time, end_time
                    
                elif '-' in time_input:
                    # 無空格範圍格式：'10:15-10:30'
                    start_str, end_str = time_input.split('-', 1)
                    start_time = self._parse_single_time(start_str)
                    end_time = self._parse_single_time(end_str)
                    
                    # 同樣的邏輯處理
                    if start_time[2] == 0:
                        start_time = (start_time[0], start_time[1], 1)
                    if end_time[2] == 0:
                        end_time = (end_time[0], end_time[1], 0)
                        
                    return start_time, end_time
                    
                else:
                    # 單一時間格式（向後兼容）
                    start_time = self._parse_single_time(time_input)
                    
                    # 計算結束時間（+20秒）
                    hour, minute, second = start_time
                    end_second = second + 20
                    end_minute = minute
                    end_hour = hour
                    
                    if end_second >= 60:
                        end_second -= 60
                        end_minute += 1
                        if end_minute >= 60:
                            end_minute -= 60
                            end_hour += 1
                            
                    end_time = (end_hour, end_minute, end_second)
                    return start_time, end_time
                    
            except Exception as e:
                raise ValueError(f"解析時間範圍失敗: {time_input} - {e}")

    # 測試案例
    test_cases = [
        # 新格式測試
        ("10:15 - 10:30", "範圍格式（有空格）"),
        ("10:15-10:30", "範圍格式（無空格）"),
        ("08:46 - 08:48", "短區間測試"),
        ("09:00:30 - 09:05:45", "秒級精度範圍"),
        
        # 向後兼容測試
        ("10:15", "單一時間（HH:MM）"),
        ("10:15:30", "單一時間（HH:MM:SS）"),
        ("08:46", "預設時間測試"),
        
        # 邊界測試
        ("23:59 - 00:01", "跨日測試"),
        ("00:00 - 00:20", "零點測試"),
    ]
    
    parser = TimeRangeParser()
    
    for i, (test_input, description) in enumerate(test_cases, 1):
        print(f"\n📋 測試 {i}: {description}")
        print(f"🔤 輸入: {test_input}")
        
        try:
            start_time, end_time = parser._parse_time_range(test_input)
            start_str = f"{start_time[0]:02d}:{start_time[1]:02d}:{start_time[2]:02d}"
            end_str = f"{end_time[0]:02d}:{end_time[1]:02d}:{end_time[2]:02d}"
            
            print(f"✅ 解析成功:")
            print(f"   開始時間: {start_str}")
            print(f"   結束時間: {end_str}")
            print(f"   監控區間: {start_str} - {end_str}")
            
            # 驗證關鍵邏輯
            if ' - ' in test_input or '-' in test_input:
                if ':' in test_input.split('-')[0] and len(test_input.split('-')[0].split(':')) == 2:
                    if start_time[2] == 1:
                        print(f"   ✅ 開始秒數正確設為01秒")
                    else:
                        print(f"   ⚠️ 開始秒數異常: {start_time[2]}")
                        
                if ':' in test_input.split('-')[1] and len(test_input.split('-')[1].strip().split(':')) == 2:
                    if end_time[2] == 0:
                        print(f"   ✅ 結束秒數正確設為00秒")
                    else:
                        print(f"   ⚠️ 結束秒數異常: {end_time[2]}")
            
        except Exception as e:
            print(f"❌ 解析失敗: {e}")
    
    print("\n" + "=" * 50)
    print("🎉 [TEST] 時間範圍解析功能測試完成")

def test_time_checking():
    """測試時間檢查功能"""
    print("\n🧪 [TEST] 開始測試時間檢查功能")
    print("=" * 50)
    
    # 模擬時間檢查邏輯
    def is_in_range_time(time_str, start_time, end_time):
        """模擬時間檢查邏輯"""
        try:
            hour, minute, second = map(int, time_str.split(':'))
            current_total_seconds = hour * 3600 + minute * 60 + second
            
            start_total_seconds = start_time[0] * 3600 + start_time[1] * 60 + start_time[2]
            end_total_seconds = end_time[0] * 3600 + end_time[1] * 60 + end_time[2]
            
            return start_total_seconds <= current_total_seconds < end_total_seconds
        except:
            return False
    
    # 測試案例：10:15 - 10:30 (實際 10:15:01 - 10:30:00)
    start_time = (10, 15, 1)
    end_time = (10, 30, 0)
    
    test_times = [
        ("10:15:00", False, "開始前1秒"),
        ("10:15:01", True, "開始時間"),
        ("10:15:30", True, "區間中間"),
        ("10:29:59", True, "結束前1秒"),
        ("10:30:00", False, "結束時間（不包含）"),
        ("10:30:01", False, "結束後1秒"),
    ]
    
    print(f"📊 測試區間: 10:15:01 - 10:30:00")
    
    for test_time, expected, description in test_times:
        result = is_in_range_time(test_time, start_time, end_time)
        status = "✅" if result == expected else "❌"
        print(f"{status} {test_time}: {'在範圍內' if result else '不在範圍內'} ({description})")
    
    print("\n" + "=" * 50)
    print("🎉 [TEST] 時間檢查功能測試完成")

if __name__ == "__main__":
    test_time_parsing()
    test_time_checking()
    print("\n🎯 [SUMMARY] 所有測試完成！")
