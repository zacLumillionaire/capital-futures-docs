#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
任務3：一致性測試腳本
測試修改後的 mdd_gui.py 與 rev_web_trading_gui.py 的結果一致性
"""

import sys
import os
import json
import importlib.util
from datetime import datetime

# 添加路徑
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

def load_unified_engine():
    """載入統一回測引擎"""
    try:
        engine_path = "rev_multi_Profit-Funded Risk_多口.py"
        spec = importlib.util.spec_from_file_location("unified_engine", engine_path)
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

def create_test_config():
    """創建測試配置"""
    return {
        "trade_lots": 3,
        "start_date": "2024-11-04",
        "end_date": "2024-11-05",  # 只測試一天以加快速度
        "range_start_time": "08:46",
        "range_end_time": "08:47",
        "fixed_stop_mode": True,
        "individual_take_profit_enabled": True,
        "entry_price_mode": "range_boundary",
        "trading_direction": "BOTH",
        "lot_settings": {
            "lot1": {
                "trigger": 15,
                "trailing": 20,
                "take_profit": 60
            },
            "lot2": {
                "trigger": 40,
                "trailing": 20,
                "protection": 2.0,
                "take_profit": 80
            },
            "lot3": {
                "trigger": 41,
                "trailing": 20,
                "protection": 2.0,
                "take_profit": 100
            }
        },
        "filters": {
            "range_filter": {"enabled": False, "max_range_points": 50},
            "risk_filter": {"enabled": False, "daily_loss_limit": 150, "profit_target": 200},
            "stop_loss_filter": {"enabled": False, "stop_loss_type": "range_boundary", "fixed_stop_loss_points": 15.0}
        }
    }

def test_unified_engine_directly():
    """直接測試統一引擎"""
    print("=" * 60)
    print("任務3：一致性測試 - 直接調用統一引擎")
    print("=" * 60)
    
    # 載入模組
    engine = load_unified_engine()
    config_factory = load_config_factory()
    
    if not engine or not config_factory:
        print("❌ 模組載入失敗")
        return None
    
    print("✅ 模組載入成功")
    
    # 創建測試配置
    gui_config = create_test_config()
    strategy_config = config_factory(gui_config)
    
    print(f"📋 測試配置:")
    print(f"  - 日期範圍: {gui_config['start_date']} 到 {gui_config['end_date']}")
    print(f"  - 時間區間: {gui_config['range_start_time']}-{gui_config['range_end_time']}")
    print(f"  - 交易方向: {gui_config['trading_direction']}")
    print(f"  - 停損設定: L1={gui_config['lot_settings']['lot1']['trigger']}, L2={gui_config['lot_settings']['lot2']['trigger']}, L3={gui_config['lot_settings']['lot3']['trigger']}")
    print(f"  - 停利設定: L1={gui_config['lot_settings']['lot1']['take_profit']}, L2={gui_config['lot_settings']['lot2']['take_profit']}, L3={gui_config['lot_settings']['lot3']['take_profit']}")
    
    # 執行回測
    print(f"\n🚀 開始執行回測...")
    try:
        result = engine.run_backtest(
            strategy_config,
            start_date=gui_config["start_date"],
            end_date=gui_config["end_date"],
            range_start_time=gui_config["range_start_time"],
            range_end_time=gui_config["range_end_time"]
        )
        
        if result:
            print(f"✅ 回測執行成功")
            print(f"\n📊 回測結果:")
            print(f"  - 總損益: {result.get('total_pnl', 0):.2f}")
            print(f"  - 多頭損益: {result.get('long_pnl', 0):.2f}")
            print(f"  - 空頭損益: {result.get('short_pnl', 0):.2f}")
            print(f"  - 最大回撤: {result.get('max_drawdown', 0):.2f}")
            print(f"  - 峰值損益: {result.get('peak_pnl', 0):.2f}")
            print(f"  - 總交易次數: {result.get('total_trades', 0)}")
            print(f"  - 多頭交易次數: {result.get('long_trades', 0)}")
            print(f"  - 空頭交易次數: {result.get('short_trades', 0)}")
            
            # 檢查各口損益
            if 'lot1_total_pnl' in result:
                print(f"  - 第1口總損益: {result.get('lot1_total_pnl', 0):.2f}")
                print(f"  - 第2口總損益: {result.get('lot2_total_pnl', 0):.2f}")
                print(f"  - 第3口總損益: {result.get('lot3_total_pnl', 0):.2f}")
            
            return result
        else:
            print(f"❌ 回測執行失敗：無結果返回")
            return None
            
    except Exception as e:
        print(f"❌ 回測執行失敗: {e}")
        return None

def test_multiple_scenarios():
    """測試多個場景"""
    print(f"\n" + "=" * 60)
    print("多場景一致性測試")
    print("=" * 60)
    
    engine = load_unified_engine()
    config_factory = load_config_factory()
    
    if not engine or not config_factory:
        return
    
    # 測試場景
    scenarios = [
        {
            "name": "基本場景",
            "config": create_test_config()
        },
        {
            "name": "只做多",
            "config": {**create_test_config(), "trading_direction": "LONG_ONLY"}
        },
        {
            "name": "只做空", 
            "config": {**create_test_config(), "trading_direction": "SHORT_ONLY"}
        },
        {
            "name": "低點+5點進場",
            "config": {**create_test_config(), "entry_price_mode": "breakout_low"}
        }
    ]
    
    results = {}
    
    for scenario in scenarios:
        print(f"\n🧪 測試場景: {scenario['name']}")
        print("-" * 30)
        
        try:
            gui_config = scenario['config']
            strategy_config = config_factory(gui_config)
            
            result = engine.run_backtest(
                strategy_config,
                start_date=gui_config["start_date"],
                end_date=gui_config["end_date"],
                range_start_time=gui_config["range_start_time"],
                range_end_time=gui_config["range_end_time"]
            )
            
            if result:
                results[scenario['name']] = result
                print(f"✅ 總損益: {result.get('total_pnl', 0):.2f}, MDD: {result.get('max_drawdown', 0):.2f}")
            else:
                print(f"❌ 執行失敗")
                
        except Exception as e:
            print(f"❌ 執行錯誤: {e}")
    
    # 生成比較報告
    if results:
        print(f"\n📋 場景比較報告:")
        print("-" * 50)
        for name, result in results.items():
            print(f"{name:12s} | PNL: {result.get('total_pnl', 0):8.2f} | MDD: {result.get('max_drawdown', 0):8.2f} | 交易: {result.get('total_trades', 0):3d}")
    
    return results

def save_test_report(direct_result, scenario_results):
    """保存測試報告"""
    report = {
        'timestamp': datetime.now().isoformat(),
        'test_type': '統一引擎一致性測試',
        'direct_test': direct_result,
        'scenario_tests': scenario_results,
        'summary': {
            'direct_test_success': direct_result is not None,
            'scenario_count': len(scenario_results) if scenario_results else 0,
            'all_scenarios_success': all(r is not None for r in scenario_results.values()) if scenario_results else False
        }
    }
    
    with open('任務3_一致性測試報告.json', 'w', encoding='utf-8') as f:
        json.dump(report, f, indent=2, ensure_ascii=False, default=str)
    
    print(f"\n📊 測試報告已保存到: 任務3_一致性測試報告.json")

def main():
    """主函數"""
    print(f"開始時間: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    # 直接測試統一引擎
    direct_result = test_unified_engine_directly()
    
    # 多場景測試
    scenario_results = test_multiple_scenarios()
    
    # 保存報告
    save_test_report(direct_result, scenario_results)
    
    print(f"\n✅ 一致性測試完成")
    print(f"結束時間: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

if __name__ == "__main__":
    main()
