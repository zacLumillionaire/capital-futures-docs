#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
測試 enhanced_mdd_optimizer.py 的進場模式處理功能
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from enhanced_mdd_optimizer import EnhancedMDDOptimizer

def test_entry_mode_generation():
    """測試進場模式組合生成"""
    print("🧪 測試進場模式組合生成...")

    # 直接測試組合生成邏輯
    from enhanced_mdd_optimizer import EnhancedMDDOptimizer

    # 創建一個簡單的測試配置
    optimizer = EnhancedMDDOptimizer('quick')  # 使用預設配置

    # 測試新格式：明確指定進場模式
    config_new_boundary = {
        'analysis_mode': 'per_time_interval',
        'stop_loss_ranges': {
            'lot1': [15],
            'lot2': [15],
            'lot3': [15]
        },
        'take_profit_modes': ['unified_fixed', 'range_boundary'],
        'take_profit_ranges': {
            'unified': [55],
            'individual': []
        },
        'time_intervals': [('10:30', '10:32')],
        'entry_price_mode': 'range_boundary'  # 新格式
    }

    # 暫時替換配置進行測試
    optimizer.config = config_new_boundary
    combinations = optimizer.generate_experiment_combinations()
    
    # 檢查是否只生成了指定的進場模式
    entry_modes = set()
    for combo in combinations:
        if 'entry_price_mode' in combo:
            entry_modes.add(combo['entry_price_mode'])
    
    print(f"✅ 新格式 range_boundary: 生成 {len(combinations)} 個組合")
    print(f"   進場模式: {entry_modes}")
    
    if 'range_boundary' not in entry_modes or len(entry_modes) != 1:
        print("❌ 新格式測試失敗")
        return False
    
    # 測試新格式：breakout_low
    config_new_breakout = config_new_boundary.copy()
    config_new_breakout['entry_price_mode'] = 'breakout_low'

    optimizer2 = EnhancedMDDOptimizer('quick')  # 使用預設配置
    optimizer2.config = config_new_breakout  # 替換配置
    combinations2 = optimizer2.generate_experiment_combinations()
    
    entry_modes2 = set()
    for combo in combinations2:
        if 'entry_price_mode' in combo:
            entry_modes2.add(combo['entry_price_mode'])
    
    print(f"✅ 新格式 breakout_low: 生成 {len(combinations2)} 個組合")
    print(f"   進場模式: {entry_modes2}")
    
    if 'breakout_low' not in entry_modes2 or len(entry_modes2) != 1:
        print("❌ 新格式測試失敗")
        return False
    
    return True

def test_backward_compatibility():
    """測試向後兼容性"""
    print("\n🧪 測試向後兼容性...")
    
    # 測試舊格式：enable_breakout_low = False
    config_old_false = {
        'analysis_mode': 'per_time_interval',
        'stop_loss_ranges': {
            'lot1': [15],
            'lot2': [15], 
            'lot3': [15]
        },
        'take_profit_modes': ['unified_fixed', 'range_boundary'],
        'take_profit_ranges': {
            'unified': [55],
            'individual': []
        },
        'time_intervals': [('10:30', '10:32')],
        'enable_breakout_low': False  # 舊格式
    }
    
    optimizer = EnhancedMDDOptimizer('quick')  # 使用預設配置
    optimizer.config = config_old_false  # 替換配置
    combinations = optimizer.generate_experiment_combinations()

    entry_modes = set()
    for combo in combinations:
        if 'entry_price_mode' in combo:
            entry_modes.add(combo['entry_price_mode'])

    print(f"✅ 舊格式 enable_breakout_low=False: 生成 {len(combinations)} 個組合")
    print(f"   進場模式: {entry_modes}")

    if 'range_boundary' not in entry_modes or len(entry_modes) != 1:
        print("❌ 舊格式測試失敗")
        return False

    # 測試舊格式：enable_breakout_low = True
    config_old_true = config_old_false.copy()
    config_old_true['enable_breakout_low'] = True

    optimizer2 = EnhancedMDDOptimizer('quick')  # 使用預設配置
    optimizer2.config = config_old_true  # 替換配置
    combinations2 = optimizer2.generate_experiment_combinations()
    
    entry_modes2 = set()
    for combo in combinations2:
        if 'entry_price_mode' in combo:
            entry_modes2.add(combo['entry_price_mode'])
    
    print(f"✅ 舊格式 enable_breakout_low=True: 生成 {len(combinations2)} 個組合")
    print(f"   進場模式: {entry_modes2}")
    
    if len(entry_modes2) != 2 or 'range_boundary' not in entry_modes2 or 'breakout_low' not in entry_modes2:
        print("❌ 舊格式測試失敗")
        return False
    
    return True

if __name__ == '__main__':
    print("🚀 開始測試 enhanced_mdd_optimizer.py 進場模式處理...")
    
    success = True
    success &= test_entry_mode_generation()
    success &= test_backward_compatibility()
    
    if success:
        print("\n🎉 所有測試通過！enhanced_mdd_optimizer.py 進場模式處理正常")
    else:
        print("\n❌ 測試失敗，請檢查進場模式處理邏輯")
        sys.exit(1)
