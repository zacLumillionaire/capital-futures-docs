#!/usr/bin/env python3
"""
測試 NaN 值修復
"""

import math

def is_nan(value):
    """檢查是否為 NaN"""
    try:
        return math.isnan(value)
    except (TypeError, ValueError):
        return False

def test_nan_handling():
    """測試 NaN 值處理"""

    # 模擬包含 NaN 值的數據
    test_cases = [
        {'take_profit': float('nan'), 'description': 'NaN 值'},
        {'take_profit': 80.0, 'description': '正常值'},
        {'take_profit': None, 'description': 'None 值'},
        {'take_profit': 0.0, 'description': '零值'},
    ]

    print("=== 測試 NaN 值處理 ===")

    for i, case in enumerate(test_cases):
        take_profit_val = case['take_profit']
        print(f"\n測試案例 {i+1}: {case['description']}")
        print(f"  原始值: {take_profit_val}")

        # 模擬修復邏輯
        try:
            # 檢查是否為 NaN 或 None
            if take_profit_val is None or is_nan(take_profit_val):
                take_profit_val = 0
                print(f"  修復後: {take_profit_val}")

            # 測試轉換為整數
            int_val = int(take_profit_val)
            print(f"  轉換為整數: {int_val}")
            print(f"  ✅ 成功")

            # 測試格式化字符串
            formatted = f"TP:{int_val:2d}"
            print(f"  格式化結果: {formatted}")

        except Exception as e:
            print(f"  ❌ 失敗: {e}")

def test_edge_cases():
    """測試邊緣情況"""
    print("\n=== 測試邊緣情況 ===")

    edge_cases = [
        float('nan'),
        None,
        float('inf'),
        float('-inf'),
        0.0,
        -1.5,
        100.7,
        "",
        "invalid"
    ]

    for case in edge_cases:
        print(f"\n測試值: {case} (類型: {type(case).__name__})")
        try:
            # 模擬修復邏輯
            if case is None or is_nan(case):
                fixed_val = 0
            else:
                fixed_val = case

            int_val = int(fixed_val)
            print(f"  修復後: {fixed_val} -> 整數: {int_val} ✅")
        except Exception as e:
            print(f"  ❌ 失敗: {e}")

def test_complete_formatting():
    """測試完整的格式化邏輯"""
    print("\n=== 測試完整格式化 ===")

    # 模擬行數據
    test_rows = [
        {
            'long_pnl': 1200.0,
            'total_pnl': 2586.0,
            'short_pnl': 1386.0,
            'lot1_stop_loss': 15,
            'lot2_stop_loss': 15,
            'lot3_stop_loss': 15,
            'take_profit': float('nan'),  # NaN 值
            'time_interval': '12:00-12:02'
        },
        {
            'long_pnl': 1100.0,
            'total_pnl': 2400.0,
            'short_pnl': 1300.0,
            'lot1_stop_loss': 20,
            'lot2_stop_loss': 20,
            'lot3_stop_loss': 20,
            'take_profit': 80.0,  # 正常值
            'time_interval': '10:30-10:32'
        }
    ]

    for i, row in enumerate(test_rows):
        print(f"\n行 {i+1}:")
        try:
            long_pnl = row.get('long_pnl', 0)
            short_pnl = row.get('short_pnl', 0)
            take_profit_val = row.get('take_profit', 0)

            # 處理 NaN 值
            if take_profit_val is None or is_nan(take_profit_val):
                take_profit_val = 0

            formatted_string = (f"{i+1:2.0f}. LONG:{long_pnl:8.2f} | "
                               f"總P&L:{row['total_pnl']:8.2f} | SHORT:{short_pnl:8.2f} | "
                               f"L1SL:{int(row['lot1_stop_loss']):2d} L2SL:{int(row['lot2_stop_loss']):2d} L3SL:{int(row['lot3_stop_loss']):2d} | "
                               f"TP:{int(take_profit_val):2d} | {row['time_interval']}")
            print(f"  ✅ {formatted_string}")
        except Exception as e:
            print(f"  ❌ 格式化失敗: {e}")

if __name__ == "__main__":
    print("開始測試 NaN 值修復...")
    test_nan_handling()
    test_edge_cases()
    test_complete_formatting()
    print("\n🎉 測試完成！")
