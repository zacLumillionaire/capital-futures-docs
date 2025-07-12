#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
凱利公式分析工具
用於分析回測結果並計算最佳資金配置建議
"""

import logging
from decimal import Decimal
from dataclasses import dataclass
from typing import List, Dict, Tuple
import statistics

logger = logging.getLogger(__name__)

@dataclass
class TradeResult:
    """單筆交易結果"""
    date: str
    pnl: Decimal
    is_win: bool

@dataclass
class KellyAnalysis:
    """凱利公式分析結果"""
    total_trades: int
    winning_trades: int
    losing_trades: int
    win_rate: float
    avg_win: Decimal
    avg_loss: Decimal
    win_loss_ratio: float
    kelly_fraction: float
    recommended_lots: int
    max_lots_available: int
    risk_assessment: str

class KellyFormulaAnalyzer:
    """凱利公式分析器"""
    
    def __init__(self, max_lots_available: int = 10):
        """
        初始化分析器
        
        Args:
            max_lots_available: 可用的最大交易口數
        """
        self.max_lots_available = max_lots_available
        self.trade_results: List[TradeResult] = []
    
    def add_trade_result(self, date: str, pnl: Decimal) -> None:
        """新增交易結果"""
        is_win = pnl > 0
        self.trade_results.append(TradeResult(date, pnl, is_win))
    
    def parse_backtest_log(self, log_content: str) -> None:
        """從回測日誌解析交易結果"""
        lines = log_content.split('\n')
        current_date = None
        daily_pnl = Decimal(0)
        
        for line in lines:
            # 解析日期
            if '---' in line and '開盤區間:' in line:
                # 如果有前一天的數據，先保存
                if current_date and daily_pnl != 0:
                    self.add_trade_result(current_date, daily_pnl)
                
                # 提取新日期
                parts = line.split('|')
                if len(parts) >= 2:
                    date_part = parts[0].strip().replace('---', '').strip()
                    current_date = date_part
                    daily_pnl = Decimal(0)
            
            # 解析損益
            elif '損益:' in line and current_date:
                try:
                    # 提取損益數字
                    if '損益: +' in line:
                        pnl_str = line.split('損益: +')[1].split()[0]
                        daily_pnl += Decimal(pnl_str)
                    elif '損益: -' in line:
                        pnl_str = line.split('損益: -')[1].split()[0]
                        daily_pnl -= Decimal(pnl_str)
                except (IndexError, ValueError):
                    continue
        
        # 保存最後一天的數據
        if current_date and daily_pnl != 0:
            self.add_trade_result(current_date, daily_pnl)
    
    def calculate_kelly_analysis(self) -> KellyAnalysis:
        """計算凱利公式分析"""
        if not self.trade_results:
            raise ValueError("沒有交易結果數據")
        
        # 基本統計
        total_trades = len(self.trade_results)
        winning_trades = sum(1 for trade in self.trade_results if trade.is_win)
        losing_trades = total_trades - winning_trades
        
        if total_trades == 0:
            raise ValueError("沒有有效的交易數據")
        
        win_rate = winning_trades / total_trades
        
        # 計算平均獲利和虧損
        wins = [trade.pnl for trade in self.trade_results if trade.is_win]
        losses = [abs(trade.pnl) for trade in self.trade_results if not trade.is_win]
        
        avg_win = Decimal(statistics.mean(wins)) if wins else Decimal(0)
        avg_loss = Decimal(statistics.mean(losses)) if losses else Decimal(1)  # 避免除零
        
        # 計算獲利虧損比
        win_loss_ratio = float(avg_win / avg_loss) if avg_loss > 0 else 0
        
        # 凱利公式計算
        # f = (bp - q) / b
        # 其中 b = 獲利虧損比, p = 勝率, q = 敗率
        if win_loss_ratio > 0 and avg_loss > 0:
            kelly_fraction = (win_loss_ratio * win_rate - (1 - win_rate)) / win_loss_ratio
        else:
            kelly_fraction = 0
        
        # 建議口數 (保守起見，使用凱利係數的一半)
        conservative_kelly = kelly_fraction * 0.5
        recommended_lots = max(1, min(self.max_lots_available, int(conservative_kelly * self.max_lots_available)))
        
        # 風險評估
        risk_assessment = self._assess_risk(kelly_fraction, win_rate, win_loss_ratio)
        
        return KellyAnalysis(
            total_trades=total_trades,
            winning_trades=winning_trades,
            losing_trades=losing_trades,
            win_rate=win_rate,
            avg_win=avg_win,
            avg_loss=avg_loss,
            win_loss_ratio=win_loss_ratio,
            kelly_fraction=kelly_fraction,
            recommended_lots=recommended_lots,
            max_lots_available=self.max_lots_available,
            risk_assessment=risk_assessment
        )
    
    def _assess_risk(self, kelly_fraction: float, win_rate: float, win_loss_ratio: float) -> str:
        """評估風險等級"""
        if kelly_fraction <= 0:
            return "高風險：凱利係數為負，不建議交易"
        elif kelly_fraction < 0.1:
            return "中高風險：凱利係數較低，建議謹慎交易"
        elif kelly_fraction < 0.25:
            return "中等風險：凱利係數適中，可適度交易"
        elif kelly_fraction < 0.5:
            return "中低風險：凱利係數良好，可積極交易"
        else:
            return "注意：凱利係數過高，建議降低風險"
    
    def generate_report(self) -> str:
        """生成分析報告"""
        try:
            analysis = self.calculate_kelly_analysis()
        except ValueError as e:
            return f"❌ 無法生成報告：{e}"
        
        report = f"""
📊 ======= 凱利公式資金管理分析報告 =======

📈 基本統計
  - 總交易次數：{analysis.total_trades}
  - 獲利次數：{analysis.winning_trades}
  - 虧損次數：{analysis.losing_trades}
  - 勝率：{analysis.win_rate:.2%}

💰 損益分析
  - 平均獲利：{analysis.avg_win:.2f} 點
  - 平均虧損：{analysis.avg_loss:.2f} 點
  - 獲利虧損比：{analysis.win_loss_ratio:.2f}

🎯 凱利公式分析
  - 凱利係數：{analysis.kelly_fraction:.4f}
  - 建議資金比例：{analysis.kelly_fraction:.2%}
  - 保守建議比例：{analysis.kelly_fraction * 0.5:.2%}

🔢 口數建議
  - 可用最大口數：{analysis.max_lots_available}
  - 建議交易口數：{analysis.recommended_lots}
  - 風險評估：{analysis.risk_assessment}

📋 使用說明
  - 凱利公式提供理論最佳資金配置
  - 實際應用建議使用保守係數（凱利係數的50%）
  - 請結合個人風險承受能力調整
  - 建議定期重新計算以適應策略表現變化

⚠️ 風險提醒
  - 凱利公式假設未來表現與歷史一致
  - 市場環境變化可能影響策略效果
  - 建議搭配其他風險管理措施
==========================================
"""
        return report

def analyze_backtest_results(log_file_path: str = None, log_content: str = None, max_lots: int = 10) -> str:
    """
    分析回測結果的便利函數
    
    Args:
        log_file_path: 日誌文件路径
        log_content: 日誌內容字符串
        max_lots: 最大可用口數
    
    Returns:
        分析報告字符串
    """
    analyzer = KellyFormulaAnalyzer(max_lots)
    
    if log_file_path:
        try:
            with open(log_file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            analyzer.parse_backtest_log(content)
        except FileNotFoundError:
            return f"❌ 找不到日誌文件：{log_file_path}"
        except Exception as e:
            return f"❌ 讀取日誌文件時發生錯誤：{e}"
    elif log_content:
        analyzer.parse_backtest_log(log_content)
    else:
        return "❌ 請提供日誌文件路径或日誌內容"
    
    return analyzer.generate_report()

if __name__ == "__main__":
    # 測試用例
    analyzer = KellyFormulaAnalyzer(max_lots_available=5)
    
    # 模擬一些交易結果
    test_results = [
        ("2024-11-01", Decimal(112)),
        ("2024-11-06", Decimal(118)),
        ("2024-11-07", Decimal(-52)),
        ("2024-11-08", Decimal(-144)),
        ("2024-11-11", Decimal(-204)),
        ("2024-11-12", Decimal(145)),
    ]
    
    for date, pnl in test_results:
        analyzer.add_trade_result(date, pnl)
    
    print(analyzer.generate_report())
