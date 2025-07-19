#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
簡單一致性測試腳本
"""

import sys
import os
import json
import importlib.util
from datetime import datetime

def test_unified_engine():
    """測試統一回測引擎"""
    print("=" * 50)
    print("統一回測引擎測試")
    print("=" * 50)
    
    try:
        # 1. 載入統一引擎
        print("1. 載入統一回測引擎...")
        engine_path = "rev_multi_Profit-Funded Risk_多口.py"
        spec = importlib.util.spec_from_file_location("engine", engine_path)
        engine = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(engine)
        print("✅ 統一引擎載入成功")
        
        # 2. 載入配置工廠
        print("2. 載入配置工廠...")
        from strategy_config_factory import create_config_from_gui_dict
        print("✅ 配置工廠載入成功")
        
        # 3. 創建測試配置
        print("3. 創建測試配置...")
        gui_config = {
            "trade_lots": 3,
            "start_date": "2024-11-04",
            "end_date": "2024-11-04",  # 只測試一天
            "range_start_time": "08:46",
            "range_end_time": "08:47",
            "fixed_stop_mode": True,
            "individual_take_profit_enabled": True,
            "entry_price_mode": "range_boundary",
            "trading_direction": "BOTH",
            "lot_settings": {
                "lot1": {"trigger": 15, "trailing": 20, "take_profit": 60},
                "lot2": {"trigger": 40, "trailing": 20, "protection": 2.0, "take_profit": 80},
                "lot3": {"trigger": 41, "trailing": 20, "protection": 2.0, "take_profit": 100}
            },
            "filters": {
                "range_filter": {"enabled": False, "max_range_points": 50},
                "risk_filter": {"enabled": False, "daily_loss_limit": 150, "profit_target": 200},
                "stop_loss_filter": {"enabled": False, "stop_loss_type": "range_boundary", "fixed_stop_loss_points": 15.0}
            }
        }
        
        strategy_config = create_config_from_gui_dict(gui_config)
        print("✅ 測試配置創建成功")
        
        # 4. 執行回測
        print("4. 執行回測...")
        result = engine.run_backtest(
            strategy_config,
            start_date=gui_config["start_date"],
            end_date=gui_config["end_date"],
            range_start_time=gui_config["range_start_time"],
            range_end_time=gui_config["range_end_time"]
        )
        
        if result:
            print("✅ 回測執行成功")
            print("\n📊 回測結果:")
            print(f"  總損益: {result.get('total_pnl', 0):.2f}")
            print(f"  多頭損益: {result.get('long_pnl', 0):.2f}")
            print(f"  空頭損益: {result.get('short_pnl', 0):.2f}")
            print(f"  最大回撤: {result.get('max_drawdown', 0):.2f}")
            print(f"  總交易次數: {result.get('total_trades', 0)}")
            
            # 檢查各口損益
            if 'lot1_total_pnl' in result:
                print(f"  第1口損益: {result.get('lot1_total_pnl', 0):.2f}")
                print(f"  第2口損益: {result.get('lot2_total_pnl', 0):.2f}")
                print(f"  第3口損益: {result.get('lot3_total_pnl', 0):.2f}")
            
            return result
        else:
            print("❌ 回測執行失敗：無結果返回")
            return None
            
    except Exception as e:
        print(f"❌ 測試失敗: {e}")
        import traceback
        traceback.print_exc()
        return None

def test_different_modes():
    """測試不同交易模式"""
    print("\n" + "=" * 50)
    print("不同交易模式測試")
    print("=" * 50)
    
    try:
        # 載入模組
        engine_path = "rev_multi_Profit-Funded Risk_多口.py"
        spec = importlib.util.spec_from_file_location("engine", engine_path)
        engine = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(engine)
        
        from strategy_config_factory import create_config_from_gui_dict
        
        # 基礎配置
        base_config = {
            "trade_lots": 3,
            "start_date": "2024-11-04",
            "end_date": "2024-11-04",
            "range_start_time": "08:46",
            "range_end_time": "08:47",
            "fixed_stop_mode": True,
            "individual_take_profit_enabled": True,
            "entry_price_mode": "range_boundary",
            "lot_settings": {
                "lot1": {"trigger": 15, "trailing": 20, "take_profit": 60},
                "lot2": {"trigger": 40, "trailing": 20, "protection": 2.0, "take_profit": 80},
                "lot3": {"trigger": 41, "trailing": 20, "protection": 2.0, "take_profit": 100}
            },
            "filters": {
                "range_filter": {"enabled": False, "max_range_points": 50},
                "risk_filter": {"enabled": False, "daily_loss_limit": 150, "profit_target": 200},
                "stop_loss_filter": {"enabled": False, "stop_loss_type": "range_boundary", "fixed_stop_loss_points": 15.0}
            }
        }
        
        # 測試不同模式
        modes = ["BOTH", "LONG_ONLY", "SHORT_ONLY"]
        results = {}
        
        for mode in modes:
            print(f"\n🧪 測試模式: {mode}")
            config = {**base_config, "trading_direction": mode}
            strategy_config = create_config_from_gui_dict(config)
            
            result = engine.run_backtest(
                strategy_config,
                start_date=config["start_date"],
                end_date=config["end_date"],
                range_start_time=config["range_start_time"],
                range_end_time=config["range_end_time"]
            )
            
            if result:
                results[mode] = result
                print(f"✅ {mode}: PNL={result.get('total_pnl', 0):.2f}, MDD={result.get('max_drawdown', 0):.2f}, 交易={result.get('total_trades', 0)}")
            else:
                print(f"❌ {mode}: 執行失敗")
        
        return results
        
    except Exception as e:
        print(f"❌ 模式測試失敗: {e}")
        return {}

def main():
    """主函數"""
    print(f"開始時間: {datetime.now()}")
    
    # 測試統一引擎
    result1 = test_unified_engine()
    
    # 測試不同模式
    result2 = test_different_modes()
    
    # 保存結果
    report = {
        'timestamp': datetime.now().isoformat(),
        'unified_engine_test': result1,
        'mode_tests': result2
    }
    
    with open('簡單一致性測試結果.json', 'w', encoding='utf-8') as f:
        json.dump(report, f, indent=2, ensure_ascii=False, default=str)
    
    print(f"\n✅ 測試完成，結果已保存到: 簡單一致性測試結果.json")
    print(f"結束時間: {datetime.now()}")

if __name__ == "__main__":
    main()
