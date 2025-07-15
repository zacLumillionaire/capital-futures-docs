#!/usr/bin/env python3
"""
測試週期風險估算功能
展示時間平方根法則的實現
"""

import math
from var_cvar_analyzer import print_risk_report

def test_time_scaling_feature():
    """測試週期風險估算功能"""
    
    print("🚀 VaR/CVaR 週期風險估算功能測試")
    print("="*60)
    
    # 模擬測試數據
    test_var = -196.5  # 每日 VaR
    test_cvar = -252.6  # 每日 CVaR
    test_pnl_list = [
        20.5, -85.2, 45.8, -120.3, 67.9, 
        -45.6, 89.2, -67.8, 34.5, -23.1,
        78.4, -156.7, 92.3, -34.8, 56.7
    ]
    
    print("📊 測試數據：")
    print(f"   每日 VaR (95%): {test_var:.1f} 點")
    print(f"   每日 CVaR: {test_cvar:.1f} 點")
    print(f"   樣本交易日數: {len(test_pnl_list)} 天")
    print()
    
    # 測試不同時間週期
    time_horizons = [5, 10, 21, 63, 252]
    horizon_names = ["1週", "2週", "1月", "1季", "1年"]
    
    print("📈 時間平方根法則計算結果：")
    print("   時間週期    交易日數    週期性VaR    縮放倍數")
    print("   " + "-"*45)
    
    for days, name in zip(time_horizons, horizon_names):
        scaled_var = test_var * math.sqrt(days)
        scaling_factor = math.sqrt(days)
        print(f"   {name:<8}    {days:>3}天      {scaled_var:>8.1f} 點    {scaling_factor:.2f}x")
    
    print()
    print("="*60)
    print("📋 完整風險報告示例 (21個交易日週期)：")
    print("="*60)
    
    # 調用完整的風險報告函數
    print_risk_report(
        var_value=test_var,
        cvar_value=test_cvar,
        confidence_level=0.95,
        total_days=len(test_pnl_list),
        pnl_list=test_pnl_list,
        time_horizon_days=21  # 21個交易日（約1個月）
    )

if __name__ == "__main__":
    test_time_scaling_feature()
