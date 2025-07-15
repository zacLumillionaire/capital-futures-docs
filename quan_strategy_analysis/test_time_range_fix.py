#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
測試時間區間修復
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from parameter_matrix_generator import TimeRange

def test_time_range_combinations():
    """測試時間區間組合生成"""
    
    print("🧪 測試時間區間組合生成")
    print("=" * 50)
    
    # 測試案例1：配對模式（您的實際使用情況）
    print("\n📋 測試案例1：配對模式")
    print("輸入：08:46-08:47, 09:30-09:32")
    
    time_range1 = TimeRange(
        start_times=["08:46", "09:30"],
        end_times=["08:47", "09:32"]
    )
    
    combinations1 = time_range1.generate_combinations()
    print(f"生成的組合數量: {len(combinations1)}")
    for i, combo in enumerate(combinations1, 1):
        print(f"  組合 {i}: {combo[0]}-{combo[1]}")
    
    # 測試案例2：笛卡爾積模式（長度不等）
    print("\n📋 測試案例2：笛卡爾積模式")
    print("輸入：start_times=[08:45, 08:46], end_times=[08:47]")
    
    time_range2 = TimeRange(
        start_times=["08:45", "08:46"],
        end_times=["08:47"]
    )
    
    combinations2 = time_range2.generate_combinations()
    print(f"生成的組合數量: {len(combinations2)}")
    for i, combo in enumerate(combinations2, 1):
        print(f"  組合 {i}: {combo[0]}-{combo[1]}")
    
    # 測試案例3：無效時間區間
    print("\n📋 測試案例3：無效時間區間")
    print("輸入：09:30-08:47（結束時間早於開始時間）")
    
    time_range3 = TimeRange(
        start_times=["09:30"],
        end_times=["08:47"]
    )
    
    combinations3 = time_range3.generate_combinations()
    print(f"生成的組合數量: {len(combinations3)}")
    for i, combo in enumerate(combinations3, 1):
        print(f"  組合 {i}: {combo[0]}-{combo[1]}")
    
    print("\n" + "=" * 50)
    print("✅ 測試完成")

if __name__ == "__main__":
    test_time_range_combinations()
