#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
SQLite資料庫管理模組
用於策略交易系統的資料存儲和管理
"""

import sqlite3
import logging
import os
from datetime import datetime, date
from typing import List, Dict, Any, Optional
from contextlib import contextmanager

logger = logging.getLogger(__name__)

class SQLiteManager:
    """SQLite資料庫管理器"""
    
    def __init__(self, db_path: str = "strategy_trading.db"):
        """
        初始化資料庫管理器
        
        Args:
            db_path: 資料庫檔案路徑
        """
        self.db_path = db_path
        self.init_database()
    
    def init_database(self):
        """初始化資料庫，創建所有必要的表格"""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                
                # 創建市場資料表
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS market_data (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        datetime TEXT NOT NULL,
                        open_price REAL,
                        high_price REAL,
                        low_price REAL,
                        close_price REAL,
                        volume INTEGER,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        UNIQUE(datetime)
                    )
                ''')
                
                # 創建策略信號表
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS strategy_signals (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        date TEXT NOT NULL,
                        range_high REAL,
                        range_low REAL,
                        signal_type TEXT,
                        signal_time TEXT,
                        signal_price REAL,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        UNIQUE(date)
                    )
                ''')
                
                # 創建交易記錄表
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS trade_records (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        date TEXT NOT NULL,
                        strategy_name TEXT,
                        lot_id INTEGER,
                        entry_time TEXT,
                        entry_price REAL,
                        exit_time TEXT,
                        exit_price REAL,
                        position_type TEXT,
                        pnl REAL,
                        exit_reason TEXT,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    )
                ''')
                
                # 創建策略狀態表
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS strategy_status (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        date TEXT NOT NULL,
                        status TEXT,
                        current_position TEXT,
                        active_lots INTEGER,
                        total_pnl REAL,
                        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        UNIQUE(date)
                    )
                ''')
                
                # 創建即時報價表 (用於策略計算)
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS realtime_quotes (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        datetime TEXT NOT NULL,
                        price REAL NOT NULL,
                        volume INTEGER,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    )
                ''')
                
                conn.commit()
                logger.info("✅ 資料庫初始化完成")
                
        except Exception as e:
            logger.error(f"❌ 資料庫初始化失敗: {e}")
            raise
    
    @contextmanager
    def get_connection(self):
        """取得資料庫連線的上下文管理器"""
        conn = None
        try:
            conn = sqlite3.connect(self.db_path)
            conn.row_factory = sqlite3.Row  # 讓查詢結果可以用欄位名稱存取
            yield conn
        except Exception as e:
            if conn:
                conn.rollback()
            logger.error(f"資料庫操作錯誤: {e}")
            raise
        finally:
            if conn:
                conn.close()
    
    def insert_market_data(self, datetime_str: str, open_price: float, 
                          high_price: float, low_price: float, 
                          close_price: float, volume: int = 0):
        """插入市場資料"""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    INSERT OR REPLACE INTO market_data 
                    (datetime, open_price, high_price, low_price, close_price, volume)
                    VALUES (?, ?, ?, ?, ?, ?)
                ''', (datetime_str, open_price, high_price, low_price, close_price, volume))
                conn.commit()
                logger.debug(f"插入市場資料: {datetime_str} {close_price}")
        except Exception as e:
            logger.error(f"插入市場資料失敗: {e}")
    
    def insert_strategy_signal(self, date_str: str, range_high: float, 
                              range_low: float, signal_type: str = None,
                              signal_time: str = None, signal_price: float = None):
        """插入策略信號"""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    INSERT OR REPLACE INTO strategy_signals 
                    (date, range_high, range_low, signal_type, signal_time, signal_price)
                    VALUES (?, ?, ?, ?, ?, ?)
                ''', (date_str, range_high, range_low, signal_type, signal_time, signal_price))
                conn.commit()
                logger.info(f"插入策略信號: {date_str} 區間:{range_low}-{range_high} 信號:{signal_type}")
        except Exception as e:
            logger.error(f"插入策略信號失敗: {e}")
    
    def insert_trade_record(self, date_str: str, strategy_name: str, lot_id: int,
                           entry_time: str, entry_price: float, exit_time: str = None,
                           exit_price: float = None, position_type: str = None,
                           pnl: float = None, exit_reason: str = None):
        """插入交易記錄"""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    INSERT INTO trade_records 
                    (date, strategy_name, lot_id, entry_time, entry_price, 
                     exit_time, exit_price, position_type, pnl, exit_reason)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', (date_str, strategy_name, lot_id, entry_time, entry_price,
                      exit_time, exit_price, position_type, pnl, exit_reason))
                conn.commit()
                logger.info(f"插入交易記錄: {strategy_name} 第{lot_id}口 {position_type}")
        except Exception as e:
            logger.error(f"插入交易記錄失敗: {e}")
    
    def update_strategy_status(self, date_str: str, status: str, 
                              current_position: str = None, active_lots: int = 0,
                              total_pnl: float = 0.0):
        """更新策略狀態"""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    INSERT OR REPLACE INTO strategy_status 
                    (date, status, current_position, active_lots, total_pnl, updated_at)
                    VALUES (?, ?, ?, ?, ?, ?)
                ''', (date_str, status, current_position, active_lots, total_pnl, 
                      datetime.now().isoformat()))
                conn.commit()
                logger.debug(f"更新策略狀態: {status} 部位:{current_position} 損益:{total_pnl}")
        except Exception as e:
            logger.error(f"更新策略狀態失敗: {e}")
    
    def get_today_signal(self, date_str: str = None) -> Optional[Dict]:
        """取得今日策略信號"""
        if not date_str:
            date_str = date.today().isoformat()
        
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    SELECT * FROM strategy_signals WHERE date = ?
                ''', (date_str,))
                row = cursor.fetchone()
                return dict(row) if row else None
        except Exception as e:
            logger.error(f"查詢今日信號失敗: {e}")
            return None
    
    def get_today_trades(self, date_str: str = None) -> List[Dict]:
        """取得今日交易記錄"""
        if not date_str:
            date_str = date.today().isoformat()
        
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    SELECT * FROM trade_records WHERE date = ? ORDER BY entry_time
                ''', (date_str,))
                rows = cursor.fetchall()
                return [dict(row) for row in rows]
        except Exception as e:
            logger.error(f"查詢今日交易失敗: {e}")
            return []
    
    def get_strategy_status(self, date_str: str = None) -> Optional[Dict]:
        """取得策略狀態"""
        if not date_str:
            date_str = date.today().isoformat()
        
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    SELECT * FROM strategy_status WHERE date = ?
                ''', (date_str,))
                row = cursor.fetchone()
                return dict(row) if row else None
        except Exception as e:
            logger.error(f"查詢策略狀態失敗: {e}")
            return None
    
    def insert_realtime_quote(self, datetime_str: str, price: float, volume: int = 0):
        """插入即時報價"""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    INSERT INTO realtime_quotes (datetime, price, volume)
                    VALUES (?, ?, ?)
                ''', (datetime_str, price, volume))
                conn.commit()
        except Exception as e:
            logger.error(f"插入即時報價失敗: {e}")
    
    def cleanup_old_quotes(self, keep_hours: int = 24):
        """清理舊的即時報價資料"""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    DELETE FROM realtime_quotes 
                    WHERE datetime < datetime('now', '-{} hours')
                '''.format(keep_hours))
                conn.commit()
                logger.debug(f"清理{keep_hours}小時前的報價資料")
        except Exception as e:
            logger.error(f"清理舊報價資料失敗: {e}")
    
    def get_trading_summary(self, start_date: str = None, end_date: str = None) -> Dict:
        """取得交易統計摘要"""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                
                where_clause = ""
                params = []
                
                if start_date and end_date:
                    where_clause = "WHERE date BETWEEN ? AND ?"
                    params = [start_date, end_date]
                elif start_date:
                    where_clause = "WHERE date >= ?"
                    params = [start_date]
                
                # 基本統計
                cursor.execute(f'''
                    SELECT 
                        COUNT(*) as total_trades,
                        SUM(CASE WHEN pnl > 0 THEN 1 ELSE 0 END) as winning_trades,
                        SUM(CASE WHEN pnl < 0 THEN 1 ELSE 0 END) as losing_trades,
                        SUM(pnl) as total_pnl,
                        AVG(pnl) as avg_pnl,
                        MAX(pnl) as max_profit,
                        MIN(pnl) as max_loss
                    FROM trade_records 
                    {where_clause}
                ''', params)
                
                result = dict(cursor.fetchone())
                
                # 計算勝率
                if result['total_trades'] > 0:
                    result['win_rate'] = (result['winning_trades'] / result['total_trades']) * 100
                else:
                    result['win_rate'] = 0
                
                return result
                
        except Exception as e:
            logger.error(f"取得交易統計失敗: {e}")
            return {}

# 全域資料庫管理器實例
db_manager = SQLiteManager()

if __name__ == "__main__":
    # 測試資料庫功能
    print("🧪 測試SQLite資料庫管理器")
    
    # 測試插入市場資料
    db_manager.insert_market_data(
        "2025-06-30 08:46:00", 22000, 22050, 21980, 22020, 1000
    )
    
    # 測試插入策略信號
    db_manager.insert_strategy_signal(
        "2025-06-30", 22050, 21980, "LONG", "08:48:15", 22055
    )
    
    # 測試插入交易記錄
    db_manager.insert_trade_record(
        "2025-06-30", "三口策略", 1, "08:48:15", 22055, 
        "09:15:30", 22105, "LONG", 50, "TRAILING_STOP"
    )
    
    # 測試查詢功能
    signal = db_manager.get_today_signal("2025-06-30")
    print(f"今日信號: {signal}")
    
    trades = db_manager.get_today_trades("2025-06-30")
    print(f"今日交易: {trades}")
    
    summary = db_manager.get_trading_summary()
    print(f"交易統計: {summary}")
    
    print("✅ 資料庫測試完成")
