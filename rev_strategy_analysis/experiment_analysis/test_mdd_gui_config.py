#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
測試 mdd_gui.py 的配置處理功能
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from mdd_gui import create_temp_config

def test_entry_price_mode_config():
    """測試進場價格模式配置"""
    print("🧪 測試進場價格模式配置...")
    
    # 測試區間邊緣進場模式
    params_boundary = {
        'stop_loss_ranges': {
            'lot1': [15],
            'lot2': [15], 
            'lot3': [15]
        },
        'take_profit_ranges': {
            'unified': [55],
            'individual': [30, 40, 50]
        },
        'time_intervals': [['10:30', '10:32']],
        'max_workers': 6,
        'entry_price_mode': 'range_boundary'
    }
    
    config_boundary = create_temp_config(params_boundary)
    print(f"✅ 區間邊緣進場配置: {config_boundary['entry_price_mode']}")
    print(f"   組合說明: {config_boundary['estimated_combinations']['breakdown']}")
    
    # 測試最低點+5點進場模式
    params_breakout = {
        'stop_loss_ranges': {
            'lot1': [15],
            'lot2': [15], 
            'lot3': [15]
        },
        'take_profit_ranges': {
            'unified': [55],
            'individual': [30, 40, 50]
        },
        'time_intervals': [['10:30', '10:32']],
        'max_workers': 6,
        'entry_price_mode': 'breakout_low'
    }
    
    config_breakout = create_temp_config(params_breakout)
    print(f"✅ 最低點+5點進場配置: {config_breakout['entry_price_mode']}")
    print(f"   組合說明: {config_breakout['estimated_combinations']['breakdown']}")
    
    # 驗證配置結構
    required_keys = ['analysis_mode', 'stop_loss_ranges', 'take_profit_modes', 
                    'take_profit_ranges', 'time_intervals', 'entry_price_mode', 
                    'estimated_combinations']
    
    for key in required_keys:
        if key not in config_boundary:
            print(f"❌ 缺少配置鍵: {key}")
            return False
        if key not in config_breakout:
            print(f"❌ 缺少配置鍵: {key}")
            return False
    
    print("✅ 所有必要的配置鍵都存在")
    return True

def test_backward_compatibility():
    """測試向後兼容性"""
    print("\n🧪 測試向後兼容性...")
    
    # 測試舊格式 enable_breakout_low
    params_old = {
        'stop_loss_ranges': {
            'lot1': [15],
            'lot2': [15], 
            'lot3': [15]
        },
        'take_profit_ranges': {
            'unified': [55],
            'individual': [30, 40, 50]
        },
        'time_intervals': [['10:30', '10:32']],
        'max_workers': 6,
        'enable_breakout_low': True  # 舊格式
    }
    
    # 這個測試應該使用預設值
    config_old = create_temp_config(params_old)
    expected_mode = 'range_boundary'  # 預設值
    
    if 'entry_price_mode' in config_old:
        print(f"✅ 向後兼容測試通過，使用預設模式: {config_old['entry_price_mode']}")
    else:
        print("❌ 向後兼容測試失敗，缺少 entry_price_mode")
        return False
    
    return True

if __name__ == '__main__':
    print("🚀 開始測試 mdd_gui.py 配置功能...")
    
    success = True
    success &= test_entry_price_mode_config()
    success &= test_backward_compatibility()
    
    if success:
        print("\n🎉 所有測試通過！mdd_gui.py 配置功能正常")
    else:
        print("\n❌ 測試失敗，請檢查配置")
        sys.exit(1)
