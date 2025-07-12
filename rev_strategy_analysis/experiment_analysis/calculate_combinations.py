#!/usr/bin/env python3
"""
計算實際組合數量
考慮停損遞增約束
"""

def calculate_combinations():
    """計算滿足約束的組合數量"""
    
    # 配置參數
    stop_loss_values = [15, 20, 25, 30, 45, 50, 55, 60, 65, 70]  # 10個值
    take_profit_values = [40, 50, 60, 70, 80]  # 5個值
    time_intervals = 7  # 7個時間區間
    
    # 計算滿足 lot1_sl <= lot2_sl <= lot3_sl 約束的組合數
    valid_stop_loss_combinations = 0
    
    for lot1_sl in stop_loss_values:
        for lot2_sl in stop_loss_values:
            for lot3_sl in stop_loss_values:
                if lot1_sl <= lot2_sl <= lot3_sl:
                    valid_stop_loss_combinations += 1
    
    print(f"停損值: {stop_loss_values}")
    print(f"停利值: {take_profit_values}")
    print(f"時間區間數: {time_intervals}")
    print(f"滿足約束的停損組合數: {valid_stop_loss_combinations}")
    
    # 總組合數 = 時間區間 × 有效停損組合 × 停利選項
    total_combinations = time_intervals * valid_stop_loss_combinations * len(take_profit_values)
    
    print(f"實際總組合數: {total_combinations:,}")
    
    # 如果沒有約束的話
    no_constraint_combinations = time_intervals * (len(stop_loss_values) ** 3) * len(take_profit_values)
    print(f"無約束總組合數: {no_constraint_combinations:,}")
    
    # 顯示一些滿足約束的停損組合示例
    print(f"\n滿足約束的停損組合示例:")
    count = 0
    for lot1_sl in stop_loss_values:
        for lot2_sl in stop_loss_values:
            for lot3_sl in stop_loss_values:
                if lot1_sl <= lot2_sl <= lot3_sl:
                    if count < 10:  # 只顯示前10個
                        print(f"  L1SL:{lot1_sl} L2SL:{lot2_sl} L3SL:{lot3_sl}")
                    count += 1
    
    return total_combinations, valid_stop_loss_combinations

if __name__ == "__main__":
    calculate_combinations()
