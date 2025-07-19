#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
任務3：GUI一致性比較測試
比較修改後的 mdd_gui.py 與 rev_web_trading_gui.py 的結果
"""

import sys
import os
import json
import importlib.util
from datetime import datetime

def load_unified_engine():
    """載入統一回測引擎"""
    try:
        engine_path = "rev_multi_Profit-Funded Risk_多口.py"
        spec = importlib.util.spec_from_file_location("engine", engine_path)
        engine = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(engine)
        return engine
    except Exception as e:
        print(f"❌ 載入統一引擎失敗: {e}")
        return None

def load_config_factory():
    """載入配置工廠"""
    try:
        from strategy_config_factory import create_config_from_gui_dict
        return create_config_from_gui_dict
    except Exception as e:
        print(f"❌ 載入配置工廠失敗: {e}")
        return None

def test_mdd_gui_style():
    """模擬 mdd_gui.py 的調用方式"""
    print("🧪 測試 MDD GUI 風格調用")
    print("-" * 40)
    
    engine = load_unified_engine()
    config_factory = load_config_factory()
    
    if not engine or not config_factory:
        return None
    
    # 模擬 mdd_gui.py 的配置方式
    gui_config = {
        "trade_lots": 3,
        "start_date": "2024-11-04",
        "end_date": "2024-11-04",
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
    
    strategy_config = config_factory(gui_config)
    
    result = engine.run_backtest(
        strategy_config,
        start_date=gui_config["start_date"],
        end_date=gui_config["end_date"],
        range_start_time=gui_config["range_start_time"],
        range_end_time=gui_config["range_end_time"]
    )
    
    if result:
        print(f"✅ MDD GUI 風格: PNL={result.get('total_pnl', 0):.2f}, MDD={result.get('max_drawdown', 0):.2f}")
        return result
    else:
        print("❌ MDD GUI 風格: 執行失敗")
        return None

def test_rev_web_gui_style():
    """模擬 rev_web_trading_gui.py 的調用方式"""
    print("🧪 測試 Rev Web GUI 風格調用")
    print("-" * 40)
    
    engine = load_unified_engine()
    config_factory = load_config_factory()
    
    if not engine or not config_factory:
        return None
    
    # 模擬 rev_web_trading_gui.py 的配置方式（應該完全相同）
    gui_config = {
        "trade_lots": 3,
        "start_date": "2024-11-04",
        "end_date": "2024-11-04",
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
    
    strategy_config = config_factory(gui_config)
    
    # 使用與 rev_web_trading_gui.py 相同的調用方式
    result = engine.run_backtest(
        strategy_config,
        start_date=gui_config["start_date"],
        end_date=gui_config["end_date"],
        range_start_time=gui_config["range_start_time"],
        range_end_time=gui_config["range_end_time"]
    )
    
    if result:
        print(f"✅ Rev Web GUI 風格: PNL={result.get('total_pnl', 0):.2f}, MDD={result.get('max_drawdown', 0):.2f}")
        return result
    else:
        print("❌ Rev Web GUI 風格: 執行失敗")
        return None

def compare_results(result1, result2):
    """比較兩個結果"""
    print("\n📊 結果比較分析")
    print("=" * 50)
    
    if not result1 or not result2:
        print("❌ 無法比較：其中一個結果為空")
        return False
    
    # 關鍵指標比較
    metrics = [
        'total_pnl', 'long_pnl', 'short_pnl', 'max_drawdown', 
        'peak_pnl', 'total_trades', 'long_trades', 'short_trades'
    ]
    
    all_match = True
    
    print("指標比較:")
    print("-" * 30)
    for metric in metrics:
        val1 = result1.get(metric, 0)
        val2 = result2.get(metric, 0)
        
        if abs(val1 - val2) < 0.01:  # 允許小數點誤差
            status = "✅"
        else:
            status = "❌"
            all_match = False
        
        print(f"{status} {metric:15s}: {val1:8.2f} vs {val2:8.2f}")
    
    # 檢查各口損益（如果存在）
    if 'lot1_total_pnl' in result1 and 'lot1_total_pnl' in result2:
        print("\n各口損益比較:")
        print("-" * 30)
        for i in range(1, 4):
            lot_key = f'lot{i}_total_pnl'
            val1 = result1.get(lot_key, 0)
            val2 = result2.get(lot_key, 0)
            
            if abs(val1 - val2) < 0.01:
                status = "✅"
            else:
                status = "❌"
                all_match = False
            
            print(f"{status} 第{i}口損益: {val1:8.2f} vs {val2:8.2f}")
    
    print(f"\n🎯 整體一致性: {'✅ 完全一致' if all_match else '❌ 存在差異'}")
    return all_match

def test_multiple_scenarios():
    """測試多個場景的一致性"""
    print("\n" + "=" * 50)
    print("多場景一致性測試")
    print("=" * 50)
    
    scenarios = [
        {
            "name": "基本場景",
            "trading_direction": "BOTH",
            "entry_mode": "range_boundary"
        },
        {
            "name": "只做多",
            "trading_direction": "LONG_ONLY",
            "entry_mode": "range_boundary"
        },
        {
            "name": "只做空",
            "trading_direction": "SHORT_ONLY", 
            "entry_mode": "range_boundary"
        },
        {
            "name": "低點+5點",
            "trading_direction": "BOTH",
            "entry_mode": "breakout_low"
        }
    ]
    
    all_scenarios_match = True
    
    for scenario in scenarios:
        print(f"\n🧪 場景: {scenario['name']}")
        print("-" * 30)
        
        # 兩種風格都使用相同配置
        base_config = {
            "trade_lots": 3,
            "start_date": "2024-11-04",
            "end_date": "2024-11-04",
            "range_start_time": "08:46",
            "range_end_time": "08:47",
            "fixed_stop_mode": True,
            "individual_take_profit_enabled": True,
            "trading_direction": scenario["trading_direction"],
            "entry_price_mode": scenario["entry_mode"],
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
        
        # 執行兩種風格的測試
        engine = load_unified_engine()
        config_factory = load_config_factory()
        
        if engine and config_factory:
            strategy_config = config_factory(base_config)
            
            result1 = engine.run_backtest(
                strategy_config,
                start_date=base_config["start_date"],
                end_date=base_config["end_date"],
                range_start_time=base_config["range_start_time"],
                range_end_time=base_config["range_end_time"]
            )
            
            result2 = engine.run_backtest(
                strategy_config,
                start_date=base_config["start_date"],
                end_date=base_config["end_date"],
                range_start_time=base_config["range_start_time"],
                range_end_time=base_config["range_end_time"]
            )
            
            if result1 and result2:
                pnl1 = result1.get('total_pnl', 0)
                pnl2 = result2.get('total_pnl', 0)
                
                if abs(pnl1 - pnl2) < 0.01:
                    print(f"✅ {scenario['name']}: 結果一致 (PNL={pnl1:.2f})")
                else:
                    print(f"❌ {scenario['name']}: 結果不一致 (PNL1={pnl1:.2f}, PNL2={pnl2:.2f})")
                    all_scenarios_match = False
            else:
                print(f"❌ {scenario['name']}: 執行失敗")
                all_scenarios_match = False
    
    return all_scenarios_match

def main():
    """主函數"""
    print("=" * 60)
    print("任務3：GUI一致性比較測試")
    print("=" * 60)
    print(f"開始時間: {datetime.now()}")
    
    # 測試兩種GUI風格
    result_mdd = test_mdd_gui_style()
    result_rev = test_rev_web_gui_style()
    
    # 比較結果
    is_consistent = compare_results(result_mdd, result_rev)
    
    # 多場景測試
    all_scenarios_ok = test_multiple_scenarios()
    
    # 生成報告
    report = {
        'timestamp': datetime.now().isoformat(),
        'test_type': 'GUI一致性比較測試',
        'mdd_gui_result': result_mdd,
        'rev_web_gui_result': result_rev,
        'consistency_check': {
            'basic_test_consistent': is_consistent,
            'all_scenarios_consistent': all_scenarios_ok,
            'overall_success': is_consistent and all_scenarios_ok
        }
    }
    
    with open('任務3_GUI一致性比較報告.json', 'w', encoding='utf-8') as f:
        json.dump(report, f, indent=2, ensure_ascii=False, default=str)
    
    print(f"\n📊 測試報告已保存到: 任務3_GUI一致性比較報告.json")
    
    # 總結
    print(f"\n🎯 測試總結:")
    print(f"  - 基本一致性: {'✅ 通過' if is_consistent else '❌ 失敗'}")
    print(f"  - 多場景一致性: {'✅ 通過' if all_scenarios_ok else '❌ 失敗'}")
    print(f"  - 整體結果: {'🎉 修復成功！' if (is_consistent and all_scenarios_ok) else '⚠️ 需要進一步調查'}")
    
    print(f"\n結束時間: {datetime.now()}")

if __name__ == "__main__":
    main()
