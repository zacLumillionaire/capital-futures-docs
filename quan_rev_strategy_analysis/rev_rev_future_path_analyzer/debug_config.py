#!/usr/bin/env python3
"""
調試配置問題的測試腳本
"""

import sys
import os
import yaml

# 添加路徑
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'rev_strategy_analysis'))

# 導入模組
from rev_strategy_core import run_rev_backtest
from strategy_config_factory import create_config_from_yaml_dict

def test_config_creation():
    """測試配置創建"""
    print("🧪 測試配置創建...")
    
    # 讀取配置文件
    with open('config.yml', 'r', encoding='utf-8') as file:
        config = yaml.safe_load(file)
    
    strategy_params = config.get('strategy_params', {})
    print(f"📋 策略參數: {strategy_params}")
    
    # 創建配置
    try:
        strategy_config = create_config_from_yaml_dict({'strategy_params': strategy_params})
        print("✅ 配置創建成功")
        print(f"📊 配置詳情:")
        print(f"   交易口數: {strategy_config.trade_size_in_lots}")
        print(f"   停損類型: {strategy_config.stop_loss_type}")
        print(f"   停損類型 (repr): {repr(strategy_config.stop_loss_type)}")
        print(f"   停損配置類型: {strategy_config.stop_loss_config.stop_loss_type}")
        print(f"   停損配置類型 (repr): {repr(strategy_config.stop_loss_config.stop_loss_type)}")
        print(f"   交易方向: {strategy_config.trading_direction}")
        print(f"   口數規則數量: {len(strategy_config.lot_rules)}")
        
        return strategy_config
    except Exception as e:
        print(f"❌ 配置創建失敗: {e}")
        import traceback
        traceback.print_exc()
        return None

def test_backtest(strategy_config):
    """測試回測執行"""
    print("\n🧪 測試回測執行...")
    
    try:
        # 讀取回測參數
        with open('config.yml', 'r', encoding='utf-8') as file:
            config = yaml.safe_load(file)
        
        backtest_params = config.get('backtest_params', {})
        start_date = backtest_params.get('start_date', '2024-11-04')
        end_date = backtest_params.get('end_date', '2025-06-28')
        range_start_time = backtest_params.get('range_start_time', '11:30')
        range_end_time = backtest_params.get('range_end_time', '11:45')
        
        print(f"📅 回測參數:")
        print(f"   時間範圍: {start_date} 至 {end_date}")
        print(f"   開盤區間: {range_start_time} - {range_end_time}")
        
        # 執行回測
        result = run_rev_backtest(
            config=strategy_config,
            start_date=start_date,
            end_date=end_date,
            silent=True,
            range_start_time=range_start_time,
            range_end_time=range_end_time,
            enable_console_log=False
        )
        
        print("✅ 回測執行成功")
        return result
        
    except Exception as e:
        print(f"❌ 回測執行失敗: {e}")
        print(f"❌ 異常類型: {type(e)}")
        import traceback
        traceback.print_exc()
        return None

if __name__ == "__main__":
    print("🚀 開始調試配置問題...")
    
    # 測試配置創建
    strategy_config = test_config_creation()
    
    if strategy_config:
        # 測試回測執行
        result = test_backtest(strategy_config)
        
        if result:
            print("🎉 所有測試通過！")
        else:
            print("❌ 回測測試失敗")
    else:
        print("❌ 配置測試失敗")
