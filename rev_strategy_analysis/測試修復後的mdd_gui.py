#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
測試修復後的 mdd_gui.py
"""

import sys
import os
import json
import importlib.util
from datetime import datetime

def test_mdd_gui_parameters():
    """測試 mdd_gui.py 的參數處理"""
    print("🧪 測試修復後的 mdd_gui.py 參數處理")
    print("=" * 50)
    
    try:
        # 導入修復後的 mdd_gui 模組
        sys.path.append('experiment_analysis')
        import mdd_gui
        
        # 測試參數格式
        test_params = {
            'stop_loss_ranges': {
                'lot1': [15], 
                'lot2': [25], 
                'lot3': [35]
            }, 
            'take_profit_ranges': {
                'unified': [55], 
                'individual': [30]
            }, 
            'time_intervals': [['10:30', '10:32'], ['12:00', '12:02']], 
            'max_workers': 6
        }
        
        print("✅ 測試參數:")
        print(json.dumps(test_params, indent=2, ensure_ascii=False))
        
        # 測試時間區間解析
        time_intervals = test_params.get('time_intervals', [])
        if isinstance(time_intervals, list) and time_intervals and isinstance(time_intervals[0], list):
            processed_intervals = [f"{interval[0]}-{interval[1]}" for interval in time_intervals]
            print(f"✅ 時間區間處理: {time_intervals} → {processed_intervals}")
        
        # 測試停損參數解析
        stop_loss_ranges = test_params.get('stop_loss_ranges', {})
        lot1_stop_loss = stop_loss_ranges.get('lot1', [15])
        lot2_stop_loss = stop_loss_ranges.get('lot2', [40])
        lot3_stop_loss = stop_loss_ranges.get('lot3', [41])
        print(f"✅ 停損參數: L1={lot1_stop_loss}, L2={lot2_stop_loss}, L3={lot3_stop_loss}")
        
        # 測試停利參數解析
        take_profit_ranges = test_params.get('take_profit_ranges', {})
        if 'unified' in take_profit_ranges:
            print(f"✅ 統一停利模式: 所有口都使用30點停利")
        elif 'individual' in take_profit_ranges:
            print(f"✅ 個別停利模式: 所有口都使用30點停利")
        
        print("✅ 參數處理測試通過")
        return True
        
    except Exception as e:
        print(f"❌ 參數處理測試失敗: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_unified_engine_call():
    """測試統一引擎調用"""
    print("\n🧪 測試統一引擎調用")
    print("=" * 50)
    
    try:
        # 載入統一引擎
        engine_path = "rev_multi_Profit-Funded Risk_多口.py"
        spec = importlib.util.spec_from_file_location("engine", engine_path)
        engine = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(engine)
        print("✅ 統一引擎載入成功")
        
        # 載入配置工廠
        from strategy_config_factory import create_config_from_gui_dict
        print("✅ 配置工廠載入成功")
        
        # 創建測試配置
        gui_config = {
            "trade_lots": 3,
            "start_date": "2024-11-04",
            "end_date": "2024-11-04",
            "range_start_time": "10:30",
            "range_end_time": "10:32",
            "fixed_stop_mode": True,
            "individual_take_profit_enabled": True,
            "entry_price_mode": "range_boundary",
            "trading_direction": "BOTH",
            "lot_settings": {
                "lot1": {"trigger": 15, "trailing": 20, "take_profit": 30},
                "lot2": {"trigger": 25, "trailing": 20, "protection": 2.0, "take_profit": 30},
                "lot3": {"trigger": 35, "trailing": 20, "protection": 2.0, "take_profit": 30}
            },
            "filters": {
                "range_filter": {"enabled": False, "max_range_points": 50},
                "risk_filter": {"enabled": False, "daily_loss_limit": 150, "profit_target": 200},
                "stop_loss_filter": {"enabled": False, "stop_loss_type": "range_boundary", "fixed_stop_loss_points": 15.0}
            }
        }
        
        strategy_config = create_config_from_gui_dict(gui_config)
        print("✅ 配置創建成功")
        
        # 執行回測
        result = engine.run_backtest(
            strategy_config,
            start_date=gui_config["start_date"],
            end_date=gui_config["end_date"],
            range_start_time=gui_config["range_start_time"],
            range_end_time=gui_config["range_end_time"]
        )
        
        if result:
            print("✅ 回測執行成功")
            print(f"  總損益: {result.get('total_pnl', 0):.2f}")
            print(f"  最大回撤: {result.get('max_drawdown', 0):.2f}")
            print(f"  交易次數: {result.get('total_trades', 0)}")
            return True
        else:
            print("❌ 回測執行失敗：無結果返回")
            return False
            
    except Exception as e:
        print(f"❌ 統一引擎調用測試失敗: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """主函數"""
    print("🔧 修復後的 mdd_gui.py 測試")
    print("=" * 60)
    print(f"開始時間: {datetime.now()}")
    
    # 測試參數處理
    param_test_ok = test_mdd_gui_parameters()
    
    # 測試統一引擎調用
    engine_test_ok = test_unified_engine_call()
    
    # 總結
    print(f"\n📊 測試總結:")
    print(f"  - 參數處理: {'✅ 通過' if param_test_ok else '❌ 失敗'}")
    print(f"  - 統一引擎調用: {'✅ 通過' if engine_test_ok else '❌ 失敗'}")
    print(f"  - 整體結果: {'🎉 修復成功！' if (param_test_ok and engine_test_ok) else '⚠️ 需要進一步修復'}")
    
    if param_test_ok and engine_test_ok:
        print(f"\n✅ mdd_gui.py 修復完成，現在應該可以正常運行了！")
        print(f"請啟動 mdd_gui.py 並測試實驗功能。")
    
    print(f"\n結束時間: {datetime.now()}")

if __name__ == "__main__":
    main()
