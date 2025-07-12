#!/usr/bin/env python3
"""
分析 focused_mdd 優化結果
"""

import pandas as pd
import numpy as np
from datetime import datetime

def analyze_results():
    """分析最新的優化結果"""
    
    # 讀取最新結果
    results_file = "data/processed/mdd_optimization_results_20250710_014028.csv"
    
    try:
        df = pd.read_csv(results_file)
        print(f"🎉 成功載入結果文件: {results_file}")
        print(f"📊 總實驗數: {len(df)}")
        print(f"✅ 成功實驗數: {len(df[df['status'] == 'success'])}")
        print()
        
        # 基本統計
        successful_df = df[df['status'] == 'success'].copy()
        
        print("📈 基本統計:")
        print(f"   平均總損益: {successful_df['total_pnl'].mean():.2f}")
        print(f"   平均 MDD: {successful_df['mdd'].mean():.2f}")
        print(f"   平均勝率: {successful_df['win_rate'].mean():.2f}%")
        print(f"   平均交易次數: {successful_df['total_trades'].mean():.2f}")
        print()
        
        # 找出最佳配置（MDD最小）
        best_mdd = successful_df.loc[successful_df['mdd'].idxmin()]
        print("🏆 最佳 MDD 配置:")
        print(f"   實驗ID: {best_mdd['experiment_id']}")
        print(f"   時間區間: {best_mdd['time_interval']}")
        print(f"   MDD: {best_mdd['mdd']:.2f}")
        print(f"   總損益: {best_mdd['total_pnl']:.2f}")
        print(f"   勝率: {best_mdd['win_rate']:.2f}%")
        print(f"   交易次數: {best_mdd['total_trades']}")
        print(f"   停損: L1={best_mdd['lot1_stop_loss']}, L2={best_mdd['lot2_stop_loss']}, L3={best_mdd['lot3_stop_loss']}")
        print()
        
        # 找出最佳收益配置
        best_pnl = successful_df.loc[successful_df['total_pnl'].idxmax()]
        print("💰 最佳收益配置:")
        print(f"   實驗ID: {best_pnl['experiment_id']}")
        print(f"   時間區間: {best_pnl['time_interval']}")
        print(f"   總損益: {best_pnl['total_pnl']:.2f}")
        print(f"   MDD: {best_pnl['mdd']:.2f}")
        print(f"   勝率: {best_pnl['win_rate']:.2f}%")
        print(f"   交易次數: {best_pnl['total_trades']}")
        print()
        
        # 各時間區間分析
        time_intervals = successful_df['time_interval'].unique()
        print("📊 各時間區間最佳配置:")
        print("=" * 80)
        
        daily_total_pnl = 0
        daily_total_mdd = 0
        
        for interval in sorted(time_intervals):
            interval_df = successful_df[successful_df['time_interval'] == interval]
            
            # 找出該區間的最佳MDD配置
            best_interval = interval_df.loc[interval_df['mdd'].idxmin()]
            
            print(f"\n🕙 {interval}:")
            print(f"   最佳配置: {best_interval['experiment_id']}")
            print(f"   MDD: {best_interval['mdd']:.2f} | P&L: {best_interval['total_pnl']:.2f}")
            print(f"   勝率: {best_interval['win_rate']:.2f}% | 交易次數: {best_interval['total_trades']}")
            print(f"   停損: L1={best_interval['lot1_stop_loss']}, L2={best_interval['lot2_stop_loss']}, L3={best_interval['lot3_stop_loss']}")
            
            # 停利設定
            if pd.notna(best_interval['take_profit']):
                print(f"   停利: 統一 {best_interval['take_profit']:.0f} 點")
            elif best_interval['take_profit_mode'] == 'trailing_stop':
                print(f"   停利: 移動停利")
            elif pd.notna(best_interval['lot1_take_profit']):
                tp1 = best_interval['lot1_take_profit'] if pd.notna(best_interval['lot1_take_profit']) else 'N/A'
                tp2 = best_interval['lot2_take_profit'] if pd.notna(best_interval['lot2_take_profit']) else 'N/A'
                tp3 = best_interval['lot3_take_profit'] if pd.notna(best_interval['lot3_take_profit']) else 'N/A'
                print(f"   停利: L1={tp1}, L2={tp2}, L3={tp3}")
            else:
                print(f"   停利: 區間邊緣")
            
            daily_total_pnl += best_interval['total_pnl']
            daily_total_mdd += best_interval['mdd']
        
        print(f"\n📈 一日交易配置總計:")
        print("=" * 80)
        print(f"預期每日總損益: {daily_total_pnl:.2f}")
        print(f"預期每日總MDD: {daily_total_mdd:.2f}")
        print()
        
        # 停利模式分析
        print("📊 停利模式分析:")
        print("=" * 50)
        
        mode_analysis = successful_df.groupby('take_profit_mode').agg({
            'total_pnl': ['mean', 'max', 'min'],
            'mdd': ['mean', 'max', 'min'],
            'win_rate': 'mean'
        }).round(2)
        
        for mode in successful_df['take_profit_mode'].unique():
            if pd.notna(mode):
                mode_data = successful_df[successful_df['take_profit_mode'] == mode]
                print(f"\n{mode}:")
                print(f"   實驗數: {len(mode_data)}")
                print(f"   平均P&L: {mode_data['total_pnl'].mean():.2f}")
                print(f"   平均MDD: {mode_data['mdd'].mean():.2f}")
                print(f"   平均勝率: {mode_data['win_rate'].mean():.2f}%")
        
        # 最佳配置推薦
        print(f"\n🎯 推薦配置 (基於MDD最小化):")
        print("=" * 80)
        
        for interval in sorted(time_intervals):
            interval_df = successful_df[successful_df['time_interval'] == interval]
            best_interval = interval_df.loc[interval_df['mdd'].idxmin()]
            
            config_str = f"{interval}: "
            if best_interval['take_profit_mode'] == 'trailing_stop':
                config_str += "移動停利"
            elif pd.notna(best_interval['take_profit']):
                config_str += f"統一停利{best_interval['take_profit']:.0f}點"
            else:
                config_str += "各口獨立停利"
            
            config_str += f", L1SL:{best_interval['lot1_stop_loss']} L2SL:{best_interval['lot2_stop_loss']} L3SL:{best_interval['lot3_stop_loss']}"
            config_str += f" (MDD:{best_interval['mdd']:.2f}, P&L:{best_interval['total_pnl']:.2f})"
            
            print(config_str)
        
        return True
        
    except Exception as e:
        print(f"❌ 分析失敗: {e}")
        return False

if __name__ == "__main__":
    analyze_results()
