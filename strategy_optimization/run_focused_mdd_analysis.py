#!/usr/bin/env python3
"""
運行 focused_mdd 配置的完整時間區間分析
"""

import logging
import sys
from datetime import datetime

# 設置日誌
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)

def run_focused_mdd_analysis():
    """運行 focused_mdd 配置的完整分析"""
    try:
        from enhanced_mdd_optimizer_adapted import EnhancedMDDOptimizer
        
        print("🚀 開始 focused_mdd 配置的完整時間區間分析...")
        print("📅 日期範圍: 2024-11-04 到 2025-06-28")
        print("🔢 預期實驗數: 928")
        print("⚙️  使用 4 個並行進程")
        print()
        
        # 創建優化器
        optimizer = EnhancedMDDOptimizer('focused_mdd')
        optimizer.set_date_range('2024-11-04', '2025-06-28')
        
        # 運行完整優化
        start_time = datetime.now()
        results = optimizer.run_optimization(max_workers=4)
        end_time = datetime.now()
        
        # 統計結果
        total_experiments = len(results)
        successful_experiments = len([r for r in results if r["status"] == "success"])
        failed_experiments = total_experiments - successful_experiments
        
        print(f"\n✅ 優化完成！")
        print(f"⏱️  總執行時間: {end_time - start_time}")
        print(f"📊 總實驗數: {total_experiments}")
        print(f"✅ 成功實驗數: {successful_experiments}")
        print(f"❌ 失敗實驗數: {failed_experiments}")
        
        if successful_experiments > 0:
            # 顯示最佳結果
            successful_results = [r for r in results if r["status"] == "success"]
            best_result = min(successful_results, key=lambda x: x["mdd"])
            
            print(f"\n🏆 最佳 MDD 配置:")
            print(f"   實驗ID: {best_result['experiment_id']}")
            print(f"   時間區間: {best_result['time_interval']}")
            print(f"   MDD: {best_result['mdd']:.2f}")
            print(f"   總損益: {best_result['total_pnl']:.2f}")
            print(f"   勝率: {best_result['win_rate']:.2f}%")
            print(f"   總交易次數: {best_result['total_trades']}")
            
            # 顯示各時間區間的最佳配置
            time_intervals = list(set([r['time_interval'] for r in successful_results]))
            print(f"\n📊 各時間區間最佳配置:")
            print("=" * 60)
            
            for interval in sorted(time_intervals):
                interval_results = [r for r in successful_results if r['time_interval'] == interval]
                if interval_results:
                    best_interval = min(interval_results, key=lambda x: x["mdd"])
                    print(f"🕙 {interval}:")
                    print(f"   MDD: {best_interval['mdd']:.2f} | P&L: {best_interval['total_pnl']:.2f}")
                    print(f"   停損: L1={best_interval['lot1_stop_loss']}, L2={best_interval['lot2_stop_loss']}, L3={best_interval['lot3_stop_loss']}")
                    if best_interval.get('take_profit_mode') == 'trailing_stop':
                        print(f"   停利: 移動停利")
                    elif best_interval.get('take_profit'):
                        print(f"   停利: 統一 {best_interval['take_profit']} 點")
                    else:
                        tp1 = best_interval.get('lot1_take_profit', 'N/A')
                        tp2 = best_interval.get('lot2_take_profit', 'N/A')
                        tp3 = best_interval.get('lot3_take_profit', 'N/A')
                        print(f"   停利: L1={tp1}, L2={tp2}, L3={tp3}")
                    print()
        
        return True
        
    except Exception as e:
        logger.error(f"❌ 分析失敗: {e}")
        print(f"\n❌ 執行失敗: {e}")
        return False

if __name__ == "__main__":
    success = run_focused_mdd_analysis()
    sys.exit(0 if success else 1)
