#!/usr/bin/env python3
"""
測試MDD優化器是否能正確解析修復後的MDD輸出
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from enhanced_mdd_optimizer_adapted import EnhancedMDDOptimizer
from time_interval_config import TimeIntervalConfig

def test_mdd_optimizer():
    """測試MDD優化器"""
    
    print("🧪 測試MDD優化器修復...")
    
    # 創建優化器
    optimizer = EnhancedMDDOptimizer()
    
    # 使用快速測試配置（只有2個實驗）
    config_manager = TimeIntervalConfig()
    config = config_manager.get_config('quick_test')
    config['date_range'] = {
        'start_date': '2024-11-04',
        'end_date': '2024-12-31'  # 使用更長的測試期間
    }
    
    print(f"📋 配置: {config['name']}")
    print(f"📅 測試期間: {config['date_range']['start_date']} 至 {config['date_range']['end_date']}")
    print(f"🔢 預期實驗數: {len(config['time_intervals']) * len(config['stop_loss_ranges']['lot1']) * len(config['take_profit_settings'])}")
    
    try:
        # 運行優化
        results = optimizer.run_optimization(config)
        
        print(f"\n📊 優化結果:")
        print(f"✅ 成功實驗數: {len(results)}")
        
        if len(results) > 0:
            # 檢查MDD值
            mdd_values = [r['mdd'] for r in results]
            pnl_values = [r['total_pnl'] for r in results]
            
            print(f"📈 MDD範圍: {min(mdd_values):.2f} 至 {max(mdd_values):.2f}")
            print(f"💰 P&L範圍: {min(pnl_values):.2f} 至 {max(pnl_values):.2f}")
            
            # 顯示前3個結果
            print(f"\n🔝 前3個實驗結果:")
            for i, result in enumerate(results[:3]):
                print(f"{i+1}. {result['experiment_id']}")
                print(f"   MDD: {result['mdd']:.2f}, P&L: {result['total_pnl']:.2f}")
                print(f"   勝率: {result['win_rate']:.2f}%, 交易次數: {result['total_trades']}")
            
            # 檢查是否有非零MDD
            non_zero_mdd = [r for r in results if r['mdd'] != 0]
            print(f"\n🎯 非零MDD實驗數: {len(non_zero_mdd)}")
            
            if len(non_zero_mdd) > 0:
                print("✅ MDD修復成功！發現真實的回撤數據")
                return True
            else:
                print("⚠️ 所有MDD仍為0，可能需要更長的測試期間")
                return False
        else:
            print("❌ 沒有成功的實驗結果")
            return False
            
    except Exception as e:
        print(f"❌ 測試失敗: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = test_mdd_optimizer()
    if success:
        print("\n🎉 MDD優化器測試成功！")
    else:
        print("\n💥 MDD優化器測試失敗！")
