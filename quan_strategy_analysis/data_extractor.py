# data_extractor.py - 日誌解析器
"""
從回測程式的日誌輸出中提取交易資料
解析各種交易事件並建立結構化資料
"""

import re
import logging
import pandas as pd
import numpy as np
from datetime import datetime, date, time
from decimal import Decimal
from typing import Dict, List, Tuple, Optional, Any
from dataclasses import dataclass, field
from pathlib import Path
import subprocess
import sys

from config import LOG_PATTERNS, ANALYSIS_CONFIG, OUTPUT_FILES, PROCESSED_DIR
from utils import (
    parse_datetime_from_log, parse_trade_date_from_log, parse_price_from_log,
    parse_pnl_from_log, parse_lot_number_from_log, parse_trade_time_from_log,
    save_dataframe_to_csv
)

logger = logging.getLogger(__name__)

@dataclass
class TradeEvent:
    """交易事件資料結構"""
    timestamp: datetime
    trade_date: date
    event_type: str  # 'entry', 'trailing_activation', 'trailing_exit', 'initial_stop', 'protective_stop', 'eod_close'
    direction: str  # 'LONG', 'SHORT'
    lot_number: Optional[int] = None
    price: Optional[float] = None
    pnl: Optional[float] = None
    trade_time: Optional[time] = None
    raw_log: str = ""

@dataclass
class DailyTrade:
    """每日交易資料結構"""
    trade_date: date
    direction: Optional[str] = None
    entry_price: Optional[float] = None
    entry_time: Optional[time] = None
    range_high: Optional[float] = None
    range_low: Optional[float] = None
    lot_events: List[TradeEvent] = field(default_factory=list)
    total_pnl: float = 0.0
    total_lots: int = 0

class LogExtractor:
    """日誌解析器主類別"""
    
    def __init__(self):
        self.trade_events: List[TradeEvent] = []
        self.daily_trades: Dict[date, DailyTrade] = {}
        self.current_trade_date: Optional[date] = None
        
    def run_backtest_and_capture_logs(self, backtest_file: Path) -> str:
        """執行回測程式並捕獲日誌輸出"""
        logger.info("開始執行回測程式...")

        try:
            # 先檢查是否有現有的日誌檔案
            log_file = backtest_file.parent / "analysis.log"
            if log_file.exists():
                log_file.unlink()  # 刪除舊的日誌檔案

            # 執行回測程式並捕獲輸出
            result = subprocess.run(
                [sys.executable, str(backtest_file)],
                capture_output=True,
                text=True,
                encoding='utf-8',
                cwd=backtest_file.parent
            )

            if result.returncode != 0:
                logger.error(f"回測程式執行失敗: {result.stderr}")
                # 即使執行失敗，也嘗試讀取可能產生的日誌

            logger.info("回測程式執行完成，開始解析日誌...")

            # 嘗試從多個來源獲取日誌
            log_content = ""

            # 1. 從標準輸出獲取
            if result.stdout:
                log_content += result.stdout
                logger.info("從標準輸出獲取到日誌")

            # 2. 從標準錯誤獲取
            if result.stderr:
                log_content += "\n" + result.stderr
                logger.info("從標準錯誤獲取到日誌")

            # 3. 嘗試從日誌檔案獲取
            if log_file.exists():
                try:
                    with open(log_file, 'r', encoding='utf-8') as f:
                        file_content = f.read()
                        if file_content:
                            log_content += "\n" + file_content
                            logger.info("從日誌檔案獲取到日誌")
                except Exception as e:
                    logger.warning(f"讀取日誌檔案失敗: {e}")

            # 4. 如果還是沒有日誌，嘗試讀取當前目錄的analysis.log
            current_log = Path.cwd() / "analysis.log"
            if current_log.exists() and not log_content:
                try:
                    with open(current_log, 'r', encoding='utf-8') as f:
                        file_content = f.read()
                        if file_content:
                            log_content += "\n" + file_content
                            logger.info("從當前目錄日誌檔案獲取到日誌")
                except Exception as e:
                    logger.warning(f"讀取當前目錄日誌檔案失敗: {e}")

            if not log_content:
                logger.warning("未能獲取到任何日誌內容")
                return ""

            return log_content

        except Exception as e:
            logger.error(f"執行回測程式時發生錯誤: {e}")
            return ""
    
    def parse_log_content(self, log_content: str) -> None:
        """解析日誌內容"""
        lines = log_content.split('\n')
        
        for line in lines:
            if not line.strip():
                continue
                
            # 解析日期摘要行
            if self._is_daily_summary_line(line):
                self._parse_daily_summary(line)
                continue
            
            # 解析交易事件
            event = self._parse_trade_event(line)
            if event:
                self.trade_events.append(event)
                self._add_event_to_daily_trade(event)
    
    def _is_daily_summary_line(self, line: str) -> bool:
        """檢查是否為日期摘要行"""
        return bool(re.search(LOG_PATTERNS['daily_summary'], line))
    
    def _parse_daily_summary(self, line: str) -> None:
        """解析日期摘要行"""
        trade_date = parse_trade_date_from_log(line)
        if trade_date:
            self.current_trade_date = trade_date
            if trade_date not in self.daily_trades:
                self.daily_trades[trade_date] = DailyTrade(trade_date=trade_date)
            
            # 解析開盤區間
            range_match = re.search(r'開盤區間: (\d+) - (\d+)', line)
            if range_match:
                self.daily_trades[trade_date].range_low = float(range_match.group(1))
                self.daily_trades[trade_date].range_high = float(range_match.group(2))
    
    def _parse_trade_event(self, line: str) -> Optional[TradeEvent]:
        """解析交易事件"""
        timestamp = parse_datetime_from_log(line)
        if not timestamp or not self.current_trade_date:
            return None
        
        # 進場事件
        if re.search(LOG_PATTERNS['trade_entry'], line):
            return self._parse_entry_event(line, timestamp)
        
        # 移動停利啟動
        elif re.search(LOG_PATTERNS['trailing_stop_activation'], line):
            return self._parse_trailing_activation_event(line, timestamp)
        
        # 移動停利出場
        elif re.search(LOG_PATTERNS['trailing_stop_exit'], line):
            return self._parse_trailing_exit_event(line, timestamp)
        
        # 初始停損
        elif re.search(LOG_PATTERNS['initial_stop_loss'], line):
            return self._parse_initial_stop_event(line, timestamp)
        
        # 保護性停損
        elif re.search(LOG_PATTERNS['protective_stop'], line):
            return self._parse_protective_stop_event(line, timestamp)
        
        # 收盤平倉
        elif re.search(LOG_PATTERNS['eod_close'], line):
            return self._parse_eod_close_event(line, timestamp)
        
        return None
    
    def _parse_entry_event(self, line: str, timestamp: datetime) -> Optional[TradeEvent]:
        """解析進場事件"""
        direction = 'LONG' if '📈 LONG' in line else 'SHORT'
        price = parse_price_from_log(line)
        trade_time = parse_trade_time_from_log(line)
        
        # 解析口數
        lot_match = re.search(r'進場 (\d+) 口', line)
        total_lots = int(lot_match.group(1)) if lot_match else 1
        
        # 更新每日交易資料
        if self.current_trade_date in self.daily_trades:
            daily_trade = self.daily_trades[self.current_trade_date]
            daily_trade.direction = direction
            daily_trade.entry_price = price
            daily_trade.entry_time = trade_time
            daily_trade.total_lots = total_lots
        
        return TradeEvent(
            timestamp=timestamp,
            trade_date=self.current_trade_date,
            event_type='entry',
            direction=direction,
            price=price,
            trade_time=trade_time,
            raw_log=line
        )
    
    def _parse_trailing_activation_event(self, line: str, timestamp: datetime) -> Optional[TradeEvent]:
        """解析移動停利啟動事件"""
        lot_number = parse_lot_number_from_log(line)
        trade_time = parse_trade_time_from_log(line)
        
        return TradeEvent(
            timestamp=timestamp,
            trade_date=self.current_trade_date,
            event_type='trailing_activation',
            direction=self.daily_trades[self.current_trade_date].direction if self.current_trade_date in self.daily_trades else None,
            lot_number=lot_number,
            trade_time=trade_time,
            raw_log=line
        )
    
    def _parse_trailing_exit_event(self, line: str, timestamp: datetime) -> Optional[TradeEvent]:
        """解析移動停利出場事件"""
        lot_number = parse_lot_number_from_log(line)
        price = parse_price_from_log(line)
        pnl = parse_pnl_from_log(line)
        trade_time = parse_trade_time_from_log(line)
        
        return TradeEvent(
            timestamp=timestamp,
            trade_date=self.current_trade_date,
            event_type='trailing_exit',
            direction=self.daily_trades[self.current_trade_date].direction if self.current_trade_date in self.daily_trades else None,
            lot_number=lot_number,
            price=price,
            pnl=pnl,
            trade_time=trade_time,
            raw_log=line
        )
    
    def _parse_initial_stop_event(self, line: str, timestamp: datetime) -> Optional[TradeEvent]:
        """解析初始停損事件"""
        lot_number = parse_lot_number_from_log(line)
        price = parse_price_from_log(line)
        pnl = parse_pnl_from_log(line)
        trade_time = parse_trade_time_from_log(line)

        return TradeEvent(
            timestamp=timestamp,
            trade_date=self.current_trade_date,
            event_type='initial_stop',
            direction=self.daily_trades[self.current_trade_date].direction if self.current_trade_date in self.daily_trades else None,
            lot_number=lot_number,
            price=price,
            pnl=pnl,
            trade_time=trade_time,
            raw_log=line
        )
    
    def _parse_protective_stop_event(self, line: str, timestamp: datetime) -> Optional[TradeEvent]:
        """解析保護性停損事件"""
        lot_number = parse_lot_number_from_log(line)
        price = parse_price_from_log(line)
        pnl = parse_pnl_from_log(line)
        trade_time = parse_trade_time_from_log(line)
        
        return TradeEvent(
            timestamp=timestamp,
            trade_date=self.current_trade_date,
            event_type='protective_stop',
            direction=self.daily_trades[self.current_trade_date].direction if self.current_trade_date in self.daily_trades else None,
            lot_number=lot_number,
            price=price,
            pnl=pnl,
            trade_time=trade_time,
            raw_log=line
        )
    
    def _parse_eod_close_event(self, line: str, timestamp: datetime) -> Optional[TradeEvent]:
        """解析收盤平倉事件"""
        pnl = parse_pnl_from_log(line)
        
        # 解析剩餘口數
        lot_match = re.search(r'剩餘 (\d+) 口', line)
        remaining_lots = int(lot_match.group(1)) if lot_match else 1
        
        return TradeEvent(
            timestamp=timestamp,
            trade_date=self.current_trade_date,
            event_type='eod_close',
            direction=self.daily_trades[self.current_trade_date].direction if self.current_trade_date in self.daily_trades else None,
            pnl=pnl,
            raw_log=line
        )
    
    def _add_event_to_daily_trade(self, event: TradeEvent) -> None:
        """將事件加入每日交易資料"""
        if event.trade_date in self.daily_trades:
            self.daily_trades[event.trade_date].lot_events.append(event)
    
    def calculate_daily_pnl(self) -> None:
        """計算每日損益"""
        for trade_date, daily_trade in self.daily_trades.items():
            total_pnl = 0.0
            
            for event in daily_trade.lot_events:
                if event.pnl is not None:
                    total_pnl += event.pnl
            
            daily_trade.total_pnl = total_pnl
    
    def export_to_dataframes(self) -> Tuple[pd.DataFrame, pd.DataFrame]:
        """匯出為DataFrame格式"""
        # 交易事件DataFrame
        events_data = []
        for event in self.trade_events:
            events_data.append({
                'timestamp': event.timestamp,
                'trade_date': event.trade_date,
                'event_type': event.event_type,
                'direction': event.direction,
                'lot_number': event.lot_number,
                'price': event.price,
                'pnl': event.pnl,
                'trade_time': event.trade_time,
                'raw_log': event.raw_log
            })
        
        events_df = pd.DataFrame(events_data)
        
        # 每日交易DataFrame
        daily_data = []
        for trade_date, daily_trade in self.daily_trades.items():
            daily_data.append({
                'trade_date': trade_date,
                'direction': daily_trade.direction,
                'entry_price': daily_trade.entry_price,
                'entry_time': daily_trade.entry_time,
                'range_high': daily_trade.range_high,
                'range_low': daily_trade.range_low,
                'total_pnl': daily_trade.total_pnl,
                'total_lots': daily_trade.total_lots,
                'num_events': len(daily_trade.lot_events)
            })
        
        daily_df = pd.DataFrame(daily_data)
        
        return events_df, daily_df
    
    def save_processed_data(self, events_df: pd.DataFrame, daily_df: pd.DataFrame) -> None:
        """儲存處理後的資料"""
        # 儲存事件資料
        events_file = PROCESSED_DIR / 'trade_events.csv'
        save_dataframe_to_csv(events_df, events_file)
        
        # 儲存每日資料
        daily_file = PROCESSED_DIR / OUTPUT_FILES['daily_pnl']
        save_dataframe_to_csv(daily_df, daily_file)
        
        logger.info(f"已儲存 {len(events_df)} 個交易事件和 {len(daily_df)} 個交易日資料")

def extract_trading_data(backtest_file: Path) -> Tuple[pd.DataFrame, pd.DataFrame]:
    """主要的資料提取函數"""
    extractor = LogExtractor()

    # 執行回測並捕獲日誌
    log_content = extractor.run_backtest_and_capture_logs(backtest_file)

    if not log_content:
        logger.error("無法獲取回測日誌，嘗試使用範例資料...")
        # 如果無法獲取實際日誌，使用範例資料
        return extract_from_sample_data()

    # 解析日誌
    extractor.parse_log_content(log_content)

    # 計算每日損益
    extractor.calculate_daily_pnl()

    # 匯出資料
    events_df, daily_df = extractor.export_to_dataframes()

    # 儲存資料
    extractor.save_processed_data(events_df, daily_df)

    return events_df, daily_df

def extract_from_live_log() -> Tuple[pd.DataFrame, pd.DataFrame]:
    """從即時執行的回測程式中提取日誌"""
    import time
    import subprocess
    import threading
    from pathlib import Path

    logger.info("開始即時執行回測程式並捕獲日誌...")

    # 準備日誌捕獲
    log_lines = []

    def capture_output(process):
        """捕獲程式輸出"""
        try:
            for line in iter(process.stdout.readline, ''):
                if line:
                    log_lines.append(line.strip())
                    print(line.strip())  # 同時顯示在控制台
        except Exception as e:
            logger.error(f"捕獲輸出時發生錯誤: {e}")

    try:
        # 執行回測程式
        backtest_file = Path.cwd() / "multi_Profit-Funded Risk_多口.py"
        process = subprocess.Popen(
            [sys.executable, str(backtest_file)],
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            encoding='utf-8',
            bufsize=1,
            universal_newlines=True
        )

        # 啟動輸出捕獲線程
        capture_thread = threading.Thread(target=capture_output, args=(process,))
        capture_thread.daemon = True
        capture_thread.start()

        # 等待程式完成
        return_code = process.wait()

        # 等待捕獲線程完成
        capture_thread.join(timeout=5)

        if return_code != 0:
            logger.warning(f"回測程式返回碼: {return_code}")

        # 合併所有日誌行
        log_content = '\n'.join(log_lines)

        if not log_content:
            logger.error("未能捕獲到日誌內容")
            return pd.DataFrame(), pd.DataFrame()

        logger.info(f"成功捕獲 {len(log_lines)} 行日誌")

        # 解析日誌
        extractor = LogExtractor()
        extractor.parse_log_content(log_content)
        extractor.calculate_daily_pnl()

        # 匯出資料
        events_df, daily_df = extractor.export_to_dataframes()
        extractor.save_processed_data(events_df, daily_df)

        return events_df, daily_df

    except Exception as e:
        logger.error(f"即時日誌捕獲失敗: {e}")
        return pd.DataFrame(), pd.DataFrame()

def extract_from_sample_data() -> Tuple[pd.DataFrame, pd.DataFrame]:
    """使用範例資料進行測試"""
    from sample_log_data import get_sample_log_data

    extractor = LogExtractor()
    log_content = get_sample_log_data()

    # 解析日誌
    extractor.parse_log_content(log_content)

    # 計算每日損益
    extractor.calculate_daily_pnl()

    # 匯出資料
    events_df, daily_df = extractor.export_to_dataframes()

    # 儲存資料
    extractor.save_processed_data(events_df, daily_df)

    return events_df, daily_df

if __name__ == "__main__":
    # 設定日誌
    logging.basicConfig(level=logging.INFO)

    # 使用範例資料進行測試
    print("使用範例日誌資料進行測試...")
    events_df, daily_df = extract_from_sample_data()

    print(f"提取完成：{len(events_df)} 個事件，{len(daily_df)} 個交易日")

    if not daily_df.empty:
        print("\n每日損益摘要：")
        print(daily_df[['trade_date', 'direction', 'total_pnl']].head(10))
    else:
        print("沒有找到交易資料")
