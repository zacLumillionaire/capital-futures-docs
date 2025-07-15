#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
多空分離分析器
從batch_experiment_gui.py的實驗結果中生成只做多和只做空的策略報告
"""

import sqlite3
import csv
import json
import logging
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Any, Optional

# 設定日誌
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class LongShortSeparationAnalyzer:
    """多空分離分析器"""
    
    def __init__(self, db_path: str = "batch_experiments.db", output_subdir: Optional[str] = None):
        self.db_path = db_path
        self.base_output_dir = Path("batch_result")
        self.base_output_dir.mkdir(exist_ok=True)

        # 如果指定了子目錄，使用子目錄；否則直接使用batch_result
        if output_subdir:
            self.output_dir = self.base_output_dir / output_subdir
            self.output_dir.mkdir(exist_ok=True)
        else:
            self.output_dir = self.base_output_dir
    
    def generate_separation_reports(self) -> Dict[str, str]:
        """生成多空分離報告"""
        try:
            # 從資料庫提取數據
            experiments_data = self._extract_experiments_data()
            
            if not experiments_data:
                logger.warning("沒有找到有效的實驗數據")
                return {"success": False, "error": "沒有有效的實驗數據"}
            
            # 生成時間戳
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            
            # 生成多方報告
            long_report_path = self._generate_long_only_report(experiments_data, timestamp)
            
            # 生成空方報告  
            short_report_path = self._generate_short_only_report(experiments_data, timestamp)
            
            logger.info(f"✅ 多空分離報告生成完成")
            logger.info(f"📊 多方報告: {long_report_path}")
            logger.info(f"📊 空方報告: {short_report_path}")
            
            return {
                "success": True,
                "long_report": str(long_report_path),
                "short_report": str(short_report_path),
                "record_count": len(experiments_data)
            }
            
        except Exception as e:
            logger.error(f"生成多空分離報告失敗: {e}")
            return {"success": False, "error": str(e)}
    
    def _extract_experiments_data(self) -> List[Dict[str, Any]]:
        """從資料庫提取實驗數據"""
        experiments = []
        
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.execute("""
                SELECT experiment_id, parameters, total_pnl, long_pnl, short_pnl,
                       max_drawdown, win_rate, total_trades, long_trades, short_trades,
                       winning_trades, losing_trades
                FROM experiments 
                WHERE success = 1
                ORDER BY experiment_id
            """)
            
            for row in cursor.fetchall():
                try:
                    # 解析參數
                    params = json.loads(row['parameters'])
                    
                    # 提取時間區間
                    start_time = params.get('range_start_time', '08:46')
                    end_time = params.get('range_end_time', '08:47')
                    time_range = f"{start_time}-{end_time}"
                    
                    # 提取參數字符串（包含觸發點和回檔範圍）
                    lot1_str = f"{params.get('lot1_trigger', 0)}({params.get('lot1_trailing', 0)}%)"
                    lot2_str = f"{params.get('lot2_trigger', 0)}({params.get('lot2_trailing', 0)}%)"
                    lot3_str = f"{params.get('lot3_trigger', 0)}({params.get('lot3_trailing', 0)}%)"
                    param_str = f"{lot1_str}/{lot2_str}/{lot3_str}"
                    
                    experiment = {
                        'experiment_id': row['experiment_id'],
                        'time_range': time_range,
                        'param_str': param_str,
                        'total_pnl': row['total_pnl'],
                        'long_pnl': row['long_pnl'],
                        'short_pnl': row['short_pnl'],
                        'max_drawdown': row['max_drawdown'],
                        'win_rate': row['win_rate'],
                        'total_trades': row['total_trades'],
                        'long_trades': row['long_trades'],
                        'short_trades': row['short_trades'],
                        'winning_trades': row['winning_trades'],
                        'losing_trades': row['losing_trades']
                    }
                    
                    experiments.append(experiment)
                    
                except (json.JSONDecodeError, KeyError) as e:
                    logger.warning(f"解析實驗 {row['experiment_id']} 失敗: {e}")
                    continue
        
        logger.info(f"📊 成功提取 {len(experiments)} 個實驗數據")
        return experiments
    
    def _estimate_mdd(self, total_mdd: float, direction_pnl: float, total_pnl: float) -> float:
        """估算單方向MDD"""
        if total_pnl == 0:
            return 0.0
        
        # 方法1：如果該方向虧損，MDD至少等於虧損金額
        if direction_pnl < 0:
            return abs(direction_pnl)
        
        # 方法2：基於比例估算，但設定最小值
        proportion_mdd = total_mdd * abs(direction_pnl) / abs(total_pnl) if total_pnl != 0 else 0
        
        # 保守估計：即使獲利也可能有一定回撤
        conservative_mdd = total_mdd * 0.3
        
        return max(proportion_mdd, conservative_mdd)
    
    def _estimate_win_rate(self, total_win_rate: float, direction_pnl: float, total_pnl: float) -> float:
        """估算單方向勝率"""
        if total_pnl == 0:
            return total_win_rate
        
        # 基於損益表現調整勝率估計
        pnl_ratio = direction_pnl / total_pnl if total_pnl != 0 else 0.5
        
        # 如果該方向損益佔比較高，假設勝率也較高
        if pnl_ratio > 0.6:
            return min(total_win_rate * 1.1, 100.0)
        elif pnl_ratio < 0.4:
            return max(total_win_rate * 0.9, 0.0)
        else:
            return total_win_rate
    
    def _generate_long_only_report(self, experiments_data: List[Dict], timestamp: str) -> Path:
        """生成只做多策略報告"""
        filename = f"long_only_results_{timestamp}.csv"
        filepath = self.output_dir / filename
        
        # 準備CSV數據
        csv_data = []
        for exp in experiments_data:
            # 估算多方MDD和勝率
            long_mdd = self._estimate_mdd(exp['max_drawdown'], exp['long_pnl'], exp['total_pnl'])
            long_win_rate = self._estimate_win_rate(exp['win_rate'], exp['long_pnl'], exp['total_pnl'])
            
            csv_row = {
                '實驗ID': exp['experiment_id'],
                '時間區間': exp['time_range'],
                '多方損益': round(exp['long_pnl'], 1),
                '多方MDD估算': round(long_mdd, 1),
                '多方勝率估算': f"{round(long_win_rate, 1)}%",
                '多方交易次數': exp['long_trades'],
                '參數': exp['param_str'],
                '備註': 'MDD/勝率為估算值'
            }
            csv_data.append(csv_row)
        
        # 按多方損益排序（降序）
        csv_data.sort(key=lambda x: x['多方損益'], reverse=True)
        
        # 寫入CSV文件
        fieldnames = ['實驗ID', '時間區間', '多方損益', '多方MDD估算', '多方勝率估算', '多方交易次數', '參數', '備註']
        
        with open(filepath, 'w', newline='', encoding='utf-8-sig') as csvfile:
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(csv_data)
        
        logger.info(f"✅ 多方報告已生成: {filepath}")
        return filepath
    
    def _generate_short_only_report(self, experiments_data: List[Dict], timestamp: str) -> Path:
        """生成只做空策略報告"""
        filename = f"short_only_results_{timestamp}.csv"
        filepath = self.output_dir / filename
        
        # 準備CSV數據
        csv_data = []
        for exp in experiments_data:
            # 估算空方MDD和勝率
            short_mdd = self._estimate_mdd(exp['max_drawdown'], exp['short_pnl'], exp['total_pnl'])
            short_win_rate = self._estimate_win_rate(exp['win_rate'], exp['short_pnl'], exp['total_pnl'])
            
            csv_row = {
                '實驗ID': exp['experiment_id'],
                '時間區間': exp['time_range'],
                '空方損益': round(exp['short_pnl'], 1),
                '空方MDD估算': round(short_mdd, 1),
                '空方勝率估算': f"{round(short_win_rate, 1)}%",
                '空方交易次數': exp['short_trades'],
                '參數': exp['param_str'],
                '備註': 'MDD/勝率為估算值'
            }
            csv_data.append(csv_row)
        
        # 按空方損益排序（降序）
        csv_data.sort(key=lambda x: x['空方損益'], reverse=True)
        
        # 寫入CSV文件
        fieldnames = ['實驗ID', '時間區間', '空方損益', '空方MDD估算', '空方勝率估算', '空方交易次數', '參數', '備註']
        
        with open(filepath, 'w', newline='', encoding='utf-8-sig') as csvfile:
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(csv_data)
        
        logger.info(f"✅ 空方報告已生成: {filepath}")
        return filepath
    
    def get_top_performers(self, direction: str = "long", limit: int = 10) -> List[Dict]:
        """獲取最佳表現的實驗（用於快速查看）"""
        experiments_data = self._extract_experiments_data()
        
        if direction == "long":
            # 按多方損益排序
            sorted_data = sorted(experiments_data, key=lambda x: x['long_pnl'], reverse=True)
            return sorted_data[:limit]
        else:
            # 按空方損益排序
            sorted_data = sorted(experiments_data, key=lambda x: x['short_pnl'], reverse=True)
            return sorted_data[:limit]

def main():
    """主函數 - 用於測試"""
    analyzer = LongShortSeparationAnalyzer()
    
    # 生成報告
    result = analyzer.generate_separation_reports()
    
    if result["success"]:
        print(f"✅ 報告生成成功")
        print(f"📊 多方報告: {result['long_report']}")
        print(f"📊 空方報告: {result['short_report']}")
        print(f"📈 處理了 {result['record_count']} 個實驗")
        
        # 顯示前5名
        print("\n🏆 多方損益前5名:")
        top_long = analyzer.get_top_performers("long", 5)
        for i, exp in enumerate(top_long, 1):
            print(f"  {i}. 實驗{exp['experiment_id']} ({exp['time_range']}): {exp['long_pnl']:.1f}點")
        
        print("\n🏆 空方損益前5名:")
        top_short = analyzer.get_top_performers("short", 5)
        for i, exp in enumerate(top_short, 1):
            print(f"  {i}. 實驗{exp['experiment_id']} ({exp['time_range']}): {exp['short_pnl']:.1f}點")
    else:
        print(f"❌ 報告生成失敗: {result['error']}")

if __name__ == "__main__":
    main()
