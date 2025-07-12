#!/usr/bin/env python3
"""
修复已生成的实验结果文件，生成完整的分析报告
避免重新运行2小时的实验
"""

import pandas as pd
import logging
from pathlib import Path

# 设置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('results/fix_results.log')
    ]
)
logger = logging.getLogger(__name__)

def analyze_results(csv_file):
    """分析结果文件并生成报告"""
    logger.info(f"📊 开始分析结果文件: {csv_file}")
    
    # 读取结果
    df = pd.read_csv(csv_file)
    logger.info(f"📈 总实验数: {len(df)}")
    logger.info(f"✅ 有效结果数: {len(df[df['mdd'].notna()])}")
    
    # 过滤有效结果
    valid_df = df[df['mdd'].notna()].copy()
    
    # MDD 最小 TOP 10
    top_mdd = valid_df.nlargest(10, 'mdd')  # MDD 是负数，所以用 nlargest
    logger.info("\n🏆 MDD最小 TOP 10:")
    logger.info("-" * 80)
    for i, (idx, row) in enumerate(top_mdd.iterrows(), 1):
        if 'lot1_take_profit' in row and pd.notna(row['lot1_take_profit']):
            logger.info(f"{i:2d}. MDD:{row['mdd']:8.2f} | "
                       f"總P&L:{row['total_pnl']:8.2f} | "
                       f"L1SL:{int(row['lot1_stop_loss']):2d}TP:{int(row['lot1_take_profit']):2d} "
                       f"L2SL:{int(row['lot2_stop_loss']):2d}TP:{int(row['lot2_take_profit']):2d} "
                       f"L3SL:{int(row['lot3_stop_loss']):2d}TP:{int(row['lot3_take_profit']):2d} | "
                       f"{row['time_interval']}")
        elif 'take_profit_mode' in row and row['take_profit_mode'] == 'range_boundary':
            logger.info(f"{i:2d}. MDD:{row['mdd']:8.2f} | "
                       f"總P&L:{row['total_pnl']:8.2f} | "
                       f"L1SL:{int(row['lot1_stop_loss']):2d} L2SL:{int(row['lot2_stop_loss']):2d} L3SL:{int(row['lot3_stop_loss']):2d} | "
                       f"區間邊緣停利 | {row['time_interval']}")
        else:
            take_profit_val = row.get('take_profit', 0)
            if pd.notna(take_profit_val):
                logger.info(f"{i:2d}. MDD:{row['mdd']:8.2f} | "
                           f"總P&L:{row['total_pnl']:8.2f} | "
                           f"L1SL:{int(row['lot1_stop_loss']):2d} L2SL:{int(row['lot2_stop_loss']):2d} L3SL:{int(row['lot3_stop_loss']):2d} | "
                           f"TP:{int(take_profit_val):2d} | {row['time_interval']}")
    
    # 风险调整收益 TOP 10
    valid_df['risk_adjusted_return'] = abs(valid_df['total_pnl'] / valid_df['mdd'])
    top_risk_adj = valid_df.nlargest(10, 'risk_adjusted_return')
    logger.info("\n💎 風險調整收益 TOP 10 (總收益/|MDD|):")
    logger.info("-" * 80)
    for i, (idx, row) in enumerate(top_risk_adj.iterrows(), 1):
        if 'lot1_take_profit' in row and pd.notna(row['lot1_take_profit']):
            logger.info(f"{i:2d}. 風險調整收益:{row['risk_adjusted_return']:6.2f} | "
                       f"MDD:{row['mdd']:8.2f} | 總P&L:{row['total_pnl']:8.2f} | "
                       f"L1SL:{int(row['lot1_stop_loss']):2d}TP:{int(row['lot1_take_profit']):2d} "
                       f"L2SL:{int(row['lot2_stop_loss']):2d}TP:{int(row['lot2_take_profit']):2d} "
                       f"L3SL:{int(row['lot3_stop_loss']):2d}TP:{int(row['lot3_take_profit']):2d}")
        elif 'take_profit_mode' in row and row['take_profit_mode'] == 'range_boundary':
            logger.info(f"{i:2d}. 風險調整收益:{row['risk_adjusted_return']:6.2f} | "
                       f"MDD:{row['mdd']:8.2f} | 總P&L:{row['total_pnl']:8.2f} | "
                       f"L1SL:{int(row['lot1_stop_loss']):2d} L2SL:{int(row['lot2_stop_loss']):2d} L3SL:{int(row['lot3_stop_loss']):2d} | "
                       f"區間邊緣停利")
        else:
            take_profit_val = row.get('take_profit', 0)
            if pd.notna(take_profit_val):
                logger.info(f"{i:2d}. 風險調整收益:{row['risk_adjusted_return']:6.2f} | "
                           f"MDD:{row['mdd']:8.2f} | 總P&L:{row['total_pnl']:8.2f} | "
                           f"L1SL:{int(row['lot1_stop_loss']):2d} L2SL:{int(row['lot2_stop_loss']):2d} L3SL:{int(row['lot3_stop_loss']):2d} | "
                           f"TP:{int(take_profit_val):2d}")
    
    # 时间区间分析
    generate_time_interval_analysis_report(valid_df)

def generate_time_interval_analysis_report(df):
    """生成时间区间分析报告"""
    logger.info("\n" + "="*80)
    logger.info("📊 時間區間 MDD 分析結果")
    logger.info("="*80)
    
    # 获取所有时间区间
    time_intervals = df['time_interval'].unique()
    daily_recommendations = []
    
    for interval in sorted(time_intervals):
        logger.info(f"\n🕙 {interval} 最佳配置:")
        logger.info("-" * 60)
        
        # 筛选该时间区间的结果
        interval_df = df[df['time_interval'] == interval]
        
        # 分别找固定停利和区间边缘停利的最佳结果
        if 'take_profit_mode' in interval_df.columns:
            fixed_tp_df = interval_df[interval_df['take_profit_mode'] != 'range_boundary']
            boundary_df = interval_df[interval_df['take_profit_mode'] == 'range_boundary']
        else:
            boundary_df = interval_df[interval_df['experiment_id'].str.contains('RangeBoundary', na=False)]
            fixed_tp_df = interval_df[~interval_df['experiment_id'].str.contains('RangeBoundary', na=False)]
        
        best_fixed = None
        best_boundary = None
        
        if not fixed_tp_df.empty:
            best_fixed = fixed_tp_df.loc[fixed_tp_df['mdd'].idxmax()]  # MDD最大(最小负值)
            # 检查是统一停利还是各口独立停利
            if 'take_profit' in best_fixed and pd.notna(best_fixed['take_profit']):
                tp_info = f"TP:{int(best_fixed['take_profit']):2d}"
            elif 'lot1_take_profit' in best_fixed and pd.notna(best_fixed['lot1_take_profit']):
                tp_info = f"L1TP:{int(best_fixed['lot1_take_profit']):2d} L2TP:{int(best_fixed['lot2_take_profit']):2d} L3TP:{int(best_fixed['lot3_take_profit']):2d}"
            else:
                tp_info = "停利配置未知"
            
            logger.info(f"   固定停利: MDD:{best_fixed['mdd']:8.2f} | P&L:{best_fixed['total_pnl']:8.2f} | "
                       f"L1SL:{int(best_fixed['lot1_stop_loss']):2d} L2SL:{int(best_fixed['lot2_stop_loss']):2d} "
                       f"L3SL:{int(best_fixed['lot3_stop_loss']):2d} | {tp_info}")
        
        if not boundary_df.empty:
            best_boundary = boundary_df.loc[boundary_df['mdd'].idxmax()]  # MDD最大(最小负值)
            logger.info(f"   區間邊緣: MDD:{best_boundary['mdd']:8.2f} | P&L:{best_boundary['total_pnl']:8.2f} | "
                       f"L1SL:{int(best_boundary['lot1_stop_loss']):2d} L2SL:{int(best_boundary['lot2_stop_loss']):2d} "
                       f"L3SL:{int(best_boundary['lot3_stop_loss']):2d} | 區間邊緣停利")
        
        # 决定推荐配置
        if best_fixed is not None and best_boundary is not None:
            if best_boundary['mdd'] > best_fixed['mdd']:  # 区间边缘MDD更小
                recommended = best_boundary
                mode = "區間邊緣停利"
                logger.info(f"   ⭐ 推薦: 區間邊緣停利 (MDD更小: {best_boundary['mdd']:.2f} vs {best_fixed['mdd']:.2f})")
            else:
                recommended = best_fixed
                if 'take_profit' in best_fixed and pd.notna(best_fixed['take_profit']):
                    mode = f"固定停利 TP:{int(best_fixed['take_profit']):2d}"
                else:
                    mode = "固定停利 (各口獨立)"
                logger.info(f"   ⭐ 推薦: 固定停利 (MDD更小: {best_fixed['mdd']:.2f} vs {best_boundary['mdd']:.2f})")
        elif best_boundary is not None:
            recommended = best_boundary
            mode = "區間邊緣停利"
            logger.info(f"   ⭐ 推薦: 區間邊緣停利 (唯一選項)")
        elif best_fixed is not None:
            recommended = best_fixed
            if 'take_profit' in best_fixed and pd.notna(best_fixed['take_profit']):
                mode = f"固定停利 TP:{int(best_fixed['take_profit']):2d}"
            else:
                mode = "固定停利 (各口獨立)"
            logger.info(f"   ⭐ 推薦: 固定停利 (唯一選項)")
        else:
            logger.info(f"   ❌ 該時間區間無有效結果")
            continue
        
        daily_recommendations.append({
            'interval': interval,
            'mode': mode,
            'config': f"L1SL:{int(recommended['lot1_stop_loss']):2d} L2SL:{int(recommended['lot2_stop_loss']):2d} L3SL:{int(recommended['lot3_stop_loss']):2d}",
            'mdd': recommended['mdd'],
            'pnl': recommended['total_pnl']
        })
    
    # 生成一日交易配置建议
    if daily_recommendations:
        logger.info(f"\n📋 一日交易配置建議:")
        logger.info("="*80)
        total_mdd = 0
        total_pnl = 0
        for rec in daily_recommendations:
            logger.info(f"{rec['interval']}: {rec['mode']}, {rec['config']} (MDD:{rec['mdd']:.2f}, P&L:{rec['pnl']:.2f})")
            total_mdd += rec['mdd']
            total_pnl += rec['pnl']
        
        logger.info(f"\n📈 預期每日總計: MDD:{total_mdd:.2f} | P&L: {total_pnl:.2f}")

def main():
    """主函数"""
    # 查找最新的结果文件
    results_dir = Path('results')
    csv_files = list(results_dir.glob('enhanced_mdd_results_time_interval_analysis_*.csv'))
    
    if not csv_files:
        logger.error("❌ 找不到结果文件")
        return
    
    # 使用最新的文件
    latest_file = max(csv_files, key=lambda x: x.stat().st_mtime)
    logger.info(f"🎯 使用最新结果文件: {latest_file}")
    
    try:
        analyze_results(latest_file)
        logger.info("\n🎊 分析完成！")
    except Exception as e:
        logger.error(f"❌ 分析失败: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
