#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
實驗系統測試腳本
用於驗證實驗架構是否正常工作
"""

import json
import sys
from pathlib import Path

# 添加當前目錄到路徑
current_dir = Path(__file__).parent
sys.path.insert(0, str(current_dir))

def test_basic_functionality():
    """測試基本功能"""
    print("🧪 開始基本功能測試...")
    
    # 測試1: 導入模組
    try:
        from parameter_optimizer import ParameterOptimizer
        from heatmap_generator import HeatmapGenerator
        from experiment_runner import ExperimentRunner
        print("✅ 模組導入成功")
    except Exception as e:
        print(f"❌ 模組導入失敗: {e}")
        return False
    
    # 測試2: 創建優化器
    try:
        optimizer = ParameterOptimizer()
        print("✅ 參數優化器創建成功")
    except Exception as e:
        print(f"❌ 參數優化器創建失敗: {e}")
        return False
    
    # 測試3: 生成實驗組合
    try:
        combinations = optimizer.generate_experiment_combinations()
        print(f"✅ 生成實驗組合成功: {len(combinations)} 個組合")
    except Exception as e:
        print(f"❌ 生成實驗組合失敗: {e}")
        return False
    
    # 測試4: 創建實驗配置
    try:
        test_combination = combinations[0]
        config = optimizer.create_experiment_config(test_combination)
        print(f"✅ 創建實驗配置成功: {test_combination['experiment_id']}")
    except Exception as e:
        print(f"❌ 創建實驗配置失敗: {e}")
        return False
    
    # 測試5: 測試配置JSON序列化
    try:
        config_json = json.dumps(config, ensure_ascii=False)
        print("✅ 配置JSON序列化成功")
    except Exception as e:
        print(f"❌ 配置JSON序列化失敗: {e}")
        return False
    
    print("🎉 基本功能測試全部通過！")
    return True

def test_mock_experiment():
    """測試模擬實驗"""
    print("\n🧪 開始模擬實驗測試...")
    
    # 創建模擬實驗結果
    mock_result = {
        'experiment_id': 'test_1030-1031_SL15_TP30',
        'time_interval': '10:30-10:31',
        'stop_loss_points': 15,
        'take_profit_points': 30,
        'total_pnl': 100.5,
        'total_trades': 10,
        'win_rate': 60.0,
        'long_pnl': 50.0,
        'short_pnl': 50.5,
        'long_trades': 5,
        'short_trades': 5,
        'max_drawdown': -20.0,
        'sharpe_ratio': 1.2,
        'both_profitable': True
    }
    
    try:
        from parameter_optimizer import ParameterOptimizer
        optimizer = ParameterOptimizer()
        optimizer.results = [mock_result]
        
        # 測試結果保存
        csv_path = optimizer.save_results_to_csv("test_results.csv")
        print(f"✅ 模擬結果保存成功: {csv_path}")
        
        # 測試結果分析
        optimizer.analyze_results()
        print("✅ 模擬結果分析成功")
        
    except Exception as e:
        print(f"❌ 模擬實驗測試失敗: {e}")
        return False
    
    print("🎉 模擬實驗測試通過！")
    return True

def test_heatmap_generation():
    """測試熱力圖生成"""
    print("\n🧪 開始熱力圖生成測試...")
    
    try:
        from heatmap_generator import HeatmapGenerator
        import pandas as pd
        
        # 創建測試數據
        test_data = []
        for sl in [15, 20, 25]:
            for tp in [30, 40, 50]:
                for interval in ['10:30-10:31', '11:30-11:31']:
                    test_data.append({
                        'experiment_id': f'test_{interval.replace(":", "").replace("-", "_")}_SL{sl}_TP{tp}',
                        'time_interval': interval,
                        'stop_loss_points': sl,
                        'take_profit_points': tp,
                        'total_pnl': sl * tp * 0.1,  # 模擬數據
                        'win_rate': 50 + sl,
                        'long_pnl': sl * tp * 0.05,
                        'short_pnl': sl * tp * 0.05,
                        'both_profitable': True
                    })
        
        df = pd.DataFrame(test_data)
        
        # 測試熱力圖生成器
        generator = HeatmapGenerator(df)
        
        # 測試透視表創建
        pivot = generator.create_pivot_table(metric='total_pnl')
        print(f"✅ 透視表創建成功: {pivot.shape}")
        
        # 測試最佳參數查找
        top_results = generator.find_optimal_parameters('total_pnl', top_n=3)
        print(f"✅ 最佳參數查找成功: {len(top_results)} 個結果")
        
    except Exception as e:
        print(f"❌ 熱力圖生成測試失敗: {e}")
        return False
    
    print("🎉 熱力圖生成測試通過！")
    return True

def main():
    """主測試函數"""
    print("=" * 60)
    print("反轉策略實驗系統測試")
    print("=" * 60)
    
    all_passed = True
    
    # 執行所有測試
    tests = [
        test_basic_functionality,
        test_mock_experiment,
        test_heatmap_generation
    ]
    
    for test_func in tests:
        if not test_func():
            all_passed = False
    
    print("\n" + "=" * 60)
    if all_passed:
        print("🎊 所有測試通過！實驗系統準備就緒。")
        return 0
    else:
        print("💥 部分測試失敗！請檢查錯誤信息。")
        return 1

if __name__ == "__main__":
    sys.exit(main())
