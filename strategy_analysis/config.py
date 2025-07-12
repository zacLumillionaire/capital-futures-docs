# config.py - 策略分析工具設定檔
"""
策略分析工具的設定檔
包含所有可調整的參數和路徑設定
"""

import os
from pathlib import Path

# 專案路徑設定
PROJECT_ROOT = Path(__file__).parent
DATA_DIR = PROJECT_ROOT / "data"
RAW_LOGS_DIR = DATA_DIR / "raw_logs"
PROCESSED_DIR = DATA_DIR / "processed"
REPORTS_DIR = DATA_DIR / "reports"
CHARTS_DIR = PROJECT_ROOT / "charts"

# 確保目錄存在
for dir_path in [DATA_DIR, RAW_LOGS_DIR, PROCESSED_DIR, REPORTS_DIR, CHARTS_DIR]:
    dir_path.mkdir(parents=True, exist_ok=True)

# 回測程式設定
BACKTEST_FILE = PROJECT_ROOT / "multi_Profit-Funded Risk_多口.py"

# 日誌解析設定
LOG_PATTERNS = {
    'trade_entry': r'📈 LONG|📉 SHORT',
    'trailing_stop_activation': r'🔔.*移動停利啟動',
    'trailing_stop_exit': r'✅.*移動停利',
    'initial_stop_loss': r'❌ 第\d+口初始停損',
    'protective_stop': r'🛡️ 第\d+口.*保護性停損',
    'eod_close': r'⚪️ 收盤平倉',
    'daily_summary': r'--- \d{4}-\d{2}-\d{2} \|',
    'stop_update': r'停損點更新為'
}

# 分析參數設定
ANALYSIS_CONFIG = {
    'risk_free_rate': 0.01,  # 無風險利率 (年化)
    'trading_days_per_year': 252,  # 每年交易日數
    'initial_capital': 1000000,  # 初始資金 (假設)
    'point_value': 50,  # 每點價值 (台指期一點50元台幣)
    'commission_per_lot': 50,  # 每口手續費
    'currency_symbol': 'NT$',  # 貨幣符號
    'show_currency': True,  # 是否顯示貨幣金額
}

# 圖表設定
CHART_CONFIG = {
    'figure_size': (12, 8),
    'dpi': 300,
    'style': 'seaborn-v0_8',
    'color_palette': ['#2E86AB', '#A23B72', '#F18F01', '#C73E1D', '#592E83'],
    'font_size': 12,
    'title_size': 16,
    'save_format': ['png', 'svg'],
}

# 報告設定
REPORT_CONFIG = {
    'title': '策略分析報告',
    'author': '策略分析工具',
    'template_file': 'report_template.html',
    'output_formats': ['html', 'pdf'],
    'include_charts': True,
    'chart_width': 800,
    'chart_height': 600,
}

# 統計指標設定
METRICS_CONFIG = {
    'percentiles': [5, 25, 50, 75, 95],  # 百分位數
    'rolling_windows': [5, 10, 20, 60],  # 移動平均視窗
    'drawdown_threshold': 0.05,  # 回撤閾值 (5%)
}

# 輸出檔案名稱格式
OUTPUT_FILES = {
    'processed_data': 'processed_trades.csv',
    'daily_pnl': 'daily_pnl.csv',
    'statistics': 'strategy_statistics.json',
    'html_report': 'strategy_analysis_report.html',
    'pdf_report': 'strategy_analysis_report.pdf',
}

# 日誌等級設定
LOGGING_CONFIG = {
    'level': 'INFO',
    'format': '[%(asctime)s] %(levelname)s [%(name)s:%(lineno)d] %(message)s',
    'date_format': '%Y-%m-%d %H:%M:%S',
    'file': PROJECT_ROOT / 'analysis.log'
}
