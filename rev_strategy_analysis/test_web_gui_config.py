#!/usr/bin/env python3
"""
測試 Web GUI 配置工廠的腳本
"""

import sys
import os

# 添加當前目錄到路徑
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from strategy_config_factory import create_web_gui_compatible_config

def test_web_gui_config():
    """測試 Web GUI 配置創建"""
    print("🧪 測試 Web GUI 配置工廠...")
    
    # 模擬 GUI 配置
    gui_config = {
        'trade_lots': 3,
        'start_date': '2024-11-04',
        'end_date': '2025-06-28',
        'range_start_time': '11:30',
        'range_end_time': '11:45',
        'trading_direction': 'LONG_ONLY'
    }
    
    try:
        # 創建配置
        strategy_config = create_web_gui_compatible_config(gui_config)
        print("✅ 配置創建成功")
        
        print(f"📊 配置詳情:")
        print(f"   交易口數: {strategy_config.trade_size_in_lots}")
        print(f"   停損類型: {strategy_config.stop_loss_type}")
        print(f"   停損類型 (repr): {repr(strategy_config.stop_loss_type)}")
        print(f"   停損類型 (value): {strategy_config.stop_loss_type.value}")
        print(f"   交易方向: {strategy_config.trading_direction}")
        print(f"   口數規則數量: {len(strategy_config.lot_rules)}")
        
        # 測試第一口規則
        lot1 = strategy_config.lot_rules[0]
        print(f"   第1口: 觸發{lot1.trailing_activation}點, 回檔{lot1.trailing_pullback*100:.0f}%, 停利{lot1.fixed_tp_points}點")
        
        return strategy_config
        
    except Exception as e:
        print(f"❌ 配置創建失敗: {e}")
        import traceback
        traceback.print_exc()
        return None

def test_backtest_call():
    """測試回測調用"""
    print("\n🧪 測試回測調用...")
    
    # 導入回測函數
    import importlib.util
    spec = importlib.util.spec_from_file_location(
        "rev_multi_module", 
        "rev_multi_Profit-Funded Risk_多口.py"
    )
    rev_multi_module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(rev_multi_module)
    
    # 創建配置
    gui_config = {'trading_direction': 'LONG_ONLY'}
    strategy_config = create_web_gui_compatible_config(gui_config)
    
    if strategy_config is None:
        print("❌ 無法創建配置")
        return
    
    try:
        # 測試回測調用（只測試配置摘要部分）
        from rev_multi_Profit_Funded_Risk_多口 import format_config_summary
        
        summary = format_config_summary(strategy_config)
        print("✅ 配置摘要生成成功")
        print("📋 配置摘要:")
        print(summary)
        
    except Exception as e:
        print(f"❌ 配置摘要生成失敗: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    print("🚀 開始測試 Web GUI 配置工廠...")
    
    # 測試配置創建
    config = test_web_gui_config()
    
    if config:
        # 測試回測調用
        test_backtest_call()
        print("🎉 所有測試完成！")
    else:
        print("❌ 測試失敗")
