#!/usr/bin/env python3
"""
測試實驗機配置是否與web_trading_gui.py驗證配置一致
"""

import sys
import os
import json
import subprocess

def test_config_consistency():
    """測試配置一致性"""
    
    print("🧪 測試實驗機配置與web_trading_gui.py的一致性...")
    
    # 您驗證過的基礎配置
    verified_config = {
        "start_date": "2024-11-04",
        "end_date": "2025-06-28",
        "range_start_time": "08:46",
        "range_end_time": "08:47",
        "trade_lots": 3,
        "lot_settings": {
            "lot1": {
                "trigger": 15,
                "trailing": 10,
                "protection": 1.0
            },
            "lot2": {
                "trigger": 40,
                "trailing": 10,
                "protection": 2.0
            },
            "lot3": {
                "trigger": 41,
                "trailing": 20,
                "protection": 2.0
            }
        },
        "filters": {
            "range_filter": {"enabled": False},
            "risk_filter": {"enabled": False},
            "stop_loss_filter": {"enabled": True, "stop_loss_type": "range_boundary"}
        },
        "stop_loss_mode": "range_boundary",
        "take_profit_mode": "trailing_stop"
    }
    
    print("📋 您驗證的基礎配置:")
    print(f"   日期範圍: {verified_config['start_date']} 至 {verified_config['end_date']}")
    print(f"   開盤區間: {verified_config['range_start_time']}-{verified_config['range_end_time']}")
    print(f"   第1口: 觸發{verified_config['lot_settings']['lot1']['trigger']}點, 回檔{verified_config['lot_settings']['lot1']['trailing']}%")
    print(f"   第2口: 觸發{verified_config['lot_settings']['lot2']['trigger']}點, 回檔{verified_config['lot_settings']['lot2']['trailing']}%, 保護×{verified_config['lot_settings']['lot2']['protection']}")
    print(f"   第3口: 觸發{verified_config['lot_settings']['lot3']['trigger']}點, 回檔{verified_config['lot_settings']['lot3']['trailing']}%, 保護×{verified_config['lot_settings']['lot3']['protection']}")
    print(f"   停損模式: {verified_config['stop_loss_mode']}")
    print(f"   濾網: 全部停用")
    
    # 測試實驗機生成的配置
    try:
        from enhanced_mdd_optimizer_adapted import EnhancedMDDOptimizer
        
        optimizer = EnhancedMDDOptimizer()
        
        # 創建測試參數
        test_params = {
            'start_date': '2024-11-04',
            'end_date': '2025-06-28',
            'range_start_time': '08:46',
            'range_end_time': '08:47',
            'lot1_stop_loss': 15,
            'lot2_stop_loss': 15,
            'lot3_stop_loss': 15,
            'take_profit_mode': 'trailing_stop',
            'trailing_config': {
                'lot1': {'trigger': 15, 'pullback': 10},
                'lot2': {'trigger': 40, 'pullback': 10},
                'lot3': {'trigger': 41, 'pullback': 20}
            }
        }
        
        # 生成實驗機配置
        test_params['time_interval'] = '08:46-08:47'  # 添加必要的時間區間參數
        experiment_config = optimizer.create_experiment_config(test_params)
        
        print(f"\n🔬 實驗機生成的配置:")
        print(f"   日期範圍: {experiment_config['start_date']} 至 {experiment_config['end_date']}")
        print(f"   開盤區間: {experiment_config['range_start_time']}-{experiment_config['range_end_time']}")
        
        lot1 = experiment_config['lot_settings']['lot1']
        lot2 = experiment_config['lot_settings']['lot2']
        lot3 = experiment_config['lot_settings']['lot3']
        
        print(f"   第1口: 觸發{lot1['trigger']}點, 回檔{lot1['trailing']}%, 保護×{lot1.get('protection', 1.0)}")
        print(f"   第2口: 觸發{lot2['trigger']}點, 回檔{lot2['trailing']}%, 保護×{lot2.get('protection', 1.0)}")
        print(f"   第3口: 觸發{lot3['trigger']}點, 回檔{lot3['trailing']}%, 保護×{lot3.get('protection', 1.0)}")
        print(f"   停損模式: {experiment_config.get('stop_loss_mode', 'N/A')}")
        
        # 比較關鍵參數
        print(f"\n🔍 配置比較:")
        
        matches = []
        mismatches = []
        
        # 檢查觸發點
        if lot1['trigger'] == verified_config['lot_settings']['lot1']['trigger']:
            matches.append("✅ 第1口觸發點一致")
        else:
            mismatches.append(f"❌ 第1口觸發點不一致: 實驗機{lot1['trigger']} vs 驗證{verified_config['lot_settings']['lot1']['trigger']}")
            
        if lot2['trigger'] == verified_config['lot_settings']['lot2']['trigger']:
            matches.append("✅ 第2口觸發點一致")
        else:
            mismatches.append(f"❌ 第2口觸發點不一致: 實驗機{lot2['trigger']} vs 驗證{verified_config['lot_settings']['lot2']['trigger']}")
            
        if lot3['trigger'] == verified_config['lot_settings']['lot3']['trigger']:
            matches.append("✅ 第3口觸發點一致")
        else:
            mismatches.append(f"❌ 第3口觸發點不一致: 實驗機{lot3['trigger']} vs 驗證{verified_config['lot_settings']['lot3']['trigger']}")
        
        # 檢查回檔百分比
        if lot1['trailing'] == verified_config['lot_settings']['lot1']['trailing']:
            matches.append("✅ 第1口回檔%一致")
        else:
            mismatches.append(f"❌ 第1口回檔%不一致: 實驗機{lot1['trailing']}% vs 驗證{verified_config['lot_settings']['lot1']['trailing']}%")
            
        if lot2['trailing'] == verified_config['lot_settings']['lot2']['trailing']:
            matches.append("✅ 第2口回檔%一致")
        else:
            mismatches.append(f"❌ 第2口回檔%不一致: 實驗機{lot2['trailing']}% vs 驗證{verified_config['lot_settings']['lot2']['trailing']}%")
            
        if lot3['trailing'] == verified_config['lot_settings']['lot3']['trailing']:
            matches.append("✅ 第3口回檔%一致")
        else:
            mismatches.append(f"❌ 第3口回檔%不一致: 實驗機{lot3['trailing']}% vs 驗證{verified_config['lot_settings']['lot3']['trailing']}%")
        
        # 檢查保護倍數
        if lot2.get('protection', 1.0) == verified_config['lot_settings']['lot2']['protection']:
            matches.append("✅ 第2口保護倍數一致")
        else:
            mismatches.append(f"❌ 第2口保護倍數不一致: 實驗機{lot2.get('protection', 1.0)} vs 驗證{verified_config['lot_settings']['lot2']['protection']}")
            
        if lot3.get('protection', 1.0) == verified_config['lot_settings']['lot3']['protection']:
            matches.append("✅ 第3口保護倍數一致")
        else:
            mismatches.append(f"❌ 第3口保護倍數不一致: 實驗機{lot3.get('protection', 1.0)} vs 驗證{verified_config['lot_settings']['lot3']['protection']}")
        
        # 顯示結果
        for match in matches:
            print(f"   {match}")
        for mismatch in mismatches:
            print(f"   {mismatch}")
        
        if len(mismatches) == 0:
            print(f"\n🎉 配置完全一致！實驗機將使用與您驗證過的相同配置")
            return True
        else:
            print(f"\n⚠️ 發現 {len(mismatches)} 個配置差異，需要修復")
            return False
            
    except Exception as e:
        print(f"❌ 測試失敗: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = test_config_consistency()
    if success:
        print(f"\n✅ 配置測試通過！可以安心運行實驗")
    else:
        print(f"\n❌ 配置測試失敗！需要修復配置差異")
