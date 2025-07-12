# utils.py - 工具函數
"""
策略分析工具的通用工具函數
包含日期處理、數值計算、檔案操作等功能
"""

import re
import logging
import pandas as pd
import numpy as np
from datetime import datetime, time, date
from decimal import Decimal
from typing import Dict, List, Tuple, Optional, Any
from pathlib import Path

# 設定日誌
logger = logging.getLogger(__name__)

def setup_logging(config: Dict[str, Any]) -> None:
    """設定日誌系統"""
    logging.basicConfig(
        level=getattr(logging, config['level']),
        format=config['format'],
        datefmt=config['date_format'],
        handlers=[
            logging.FileHandler(config['file'], encoding='utf-8'),
            logging.StreamHandler()
        ]
    )

def parse_datetime_from_log(log_line: str) -> Optional[datetime]:
    """從日誌行中解析日期時間"""
    # 匹配格式: [2025-07-05T23:09:15+0800]
    pattern = r'\[(\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2})\+\d{4}\]'
    match = re.search(pattern, log_line)
    if match:
        try:
            return datetime.strptime(match.group(1), '%Y-%m-%dT%H:%M:%S')
        except ValueError:
            return None
    return None

def parse_trade_date_from_log(log_line: str) -> Optional[date]:
    """從日誌行中解析交易日期"""
    # 匹配格式: --- 2025-06-17 | 開盤區間: 22130 - 22177 ---
    pattern = r'--- (\d{4}-\d{2}-\d{2}) \|'
    match = re.search(pattern, log_line)
    if match:
        try:
            return datetime.strptime(match.group(1), '%Y-%m-%d').date()
        except ValueError:
            return None
    return None

def parse_price_from_log(log_line: str) -> Optional[float]:
    """從日誌行中解析價格"""
    # 匹配各種價格格式
    patterns = [
        r'價格: (\d+)',
        r'出場價: (\d+)',
        r'開盤區間: (\d+) - (\d+)',
        r'停損點更新為: (\d+)'
    ]
    
    for pattern in patterns:
        match = re.search(pattern, log_line)
        if match:
            try:
                if len(match.groups()) == 2:  # 區間格式
                    return float(match.group(1)), float(match.group(2))
                else:
                    return float(match.group(1))
            except ValueError:
                continue
    return None

def parse_pnl_from_log(log_line: str) -> Optional[float]:
    """從日誌行中解析損益"""
    # 匹配損益格式: 損益: +34, 損益: -56, 單口虧損: -56
    patterns = [
        r'損益: ([+-]?\d+)',
        r'單口虧損: ([+-]?\d+)',
        r'損益: \+(\d+)',
        r'損益: -(\d+)'
    ]
    
    for pattern in patterns:
        match = re.search(pattern, log_line)
        if match:
            try:
                value = match.group(1)
                if value.startswith('+'):
                    return float(value[1:])
                else:
                    return float(value)
            except ValueError:
                continue
    return None

def parse_lot_number_from_log(log_line: str) -> Optional[int]:
    """從日誌行中解析口數"""
    # 匹配格式: 第1口, 第2口, 第3口
    pattern = r'第(\d+)口'
    match = re.search(pattern, log_line)
    if match:
        try:
            return int(match.group(1))
        except ValueError:
            return None
    return None

def parse_trade_time_from_log(log_line: str) -> Optional[time]:
    """從日誌行中解析交易時間"""
    # 匹配格式: 時間: 08:53:00
    pattern = r'時間: (\d{2}:\d{2}:\d{2})'
    match = re.search(pattern, log_line)
    if match:
        try:
            return datetime.strptime(match.group(1), '%H:%M:%S').time()
        except ValueError:
            return None
    return None

def calculate_drawdown(equity_curve: pd.Series) -> pd.Series:
    """計算回撤序列"""
    peak = equity_curve.expanding().max()
    drawdown = (equity_curve - peak) / peak
    return drawdown

def calculate_max_drawdown(equity_curve: pd.Series) -> Tuple[float, int, int]:
    """計算最大回撤及其期間"""
    drawdown = calculate_drawdown(equity_curve)
    max_dd = drawdown.min()
    
    # 找到最大回撤的開始和結束位置
    max_dd_idx = drawdown.idxmin()
    peak_idx = equity_curve[:max_dd_idx].idxmax()
    
    return max_dd, peak_idx, max_dd_idx

def calculate_sharpe_ratio(returns: pd.Series, risk_free_rate: float = 0.01) -> float:
    """計算夏普比率"""
    if returns.std() == 0:
        return 0.0
    
    excess_returns = returns.mean() - risk_free_rate / 252  # 日化無風險利率
    return excess_returns / returns.std() * np.sqrt(252)

def calculate_sortino_ratio(returns: pd.Series, risk_free_rate: float = 0.01) -> float:
    """計算索提諾比率"""
    downside_returns = returns[returns < 0]
    if len(downside_returns) == 0 or downside_returns.std() == 0:
        return 0.0
    
    excess_returns = returns.mean() - risk_free_rate / 252
    downside_deviation = downside_returns.std()
    return excess_returns / downside_deviation * np.sqrt(252)

def calculate_profit_factor(wins: pd.Series, losses: pd.Series) -> float:
    """計算獲利因子"""
    total_wins = wins.sum() if len(wins) > 0 else 0
    total_losses = abs(losses.sum()) if len(losses) > 0 else 0
    
    if total_losses == 0:
        return float('inf') if total_wins > 0 else 0
    
    return total_wins / total_losses

def format_number(value: float, decimal_places: int = 2) -> str:
    """格式化數字顯示"""
    if abs(value) >= 1e6:
        return f"{value/1e6:.{decimal_places}f}M"
    elif abs(value) >= 1e3:
        return f"{value/1e3:.{decimal_places}f}K"
    else:
        return f"{value:.{decimal_places}f}"

def format_currency(points: float, point_value: float = 50, currency_symbol: str = 'NT$',
                   show_points: bool = True) -> str:
    """將點數轉換為貨幣格式顯示"""
    currency_amount = points * point_value

    # 格式化貨幣金額
    if abs(currency_amount) >= 1e6:
        currency_str = f"{currency_symbol}{currency_amount/1e6:.1f}M"
    elif abs(currency_amount) >= 1e3:
        currency_str = f"{currency_symbol}{currency_amount/1e3:.0f}K"
    else:
        currency_str = f"{currency_symbol}{currency_amount:,.0f}"

    if show_points:
        return f"{currency_str} ({points:+.0f}pts)"
    else:
        return currency_str

def points_to_currency(points: float, point_value: float = 50) -> float:
    """將點數轉換為貨幣金額"""
    return points * point_value

def safe_divide(numerator: float, denominator: float, default: float = 0.0) -> float:
    """安全除法，避免除零錯誤"""
    return numerator / denominator if denominator != 0 else default

def ensure_directory_exists(path: Path) -> None:
    """確保目錄存在"""
    path.mkdir(parents=True, exist_ok=True)

def save_dataframe_to_csv(df: pd.DataFrame, filepath: Path, index: bool = True) -> None:
    """儲存DataFrame到CSV檔案"""
    ensure_directory_exists(filepath.parent)
    df.to_csv(filepath, index=index, encoding='utf-8-sig')
    logger.info(f"已儲存資料到: {filepath}")

def load_dataframe_from_csv(filepath: Path) -> Optional[pd.DataFrame]:
    """從CSV檔案載入DataFrame"""
    if filepath.exists():
        try:
            return pd.read_csv(filepath, index_col=0, encoding='utf-8-sig')
        except Exception as e:
            logger.error(f"載入CSV檔案失敗: {filepath}, 錯誤: {e}")
            return None
    else:
        logger.warning(f"CSV檔案不存在: {filepath}")
        return None
