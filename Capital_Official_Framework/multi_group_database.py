#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
多組多口策略資料庫管理器
擴展SQLite功能以支援多組策略交易記錄
"""

import sqlite3
import json
import logging
from contextlib import contextmanager
from datetime import datetime, date
from typing import List, Dict, Optional, Tuple
from decimal import Decimal

# 設定日誌
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class MultiGroupDatabaseManager:
    """多組策略專用資料庫管理器"""
    
    def __init__(self, db_path: str = "multi_group_strategy.db"):
        self.db_path = db_path
        self.init_database()
        logger.info(f"多組策略資料庫管理器初始化完成: {db_path}")
    
    def init_database(self):
        """初始化資料庫表結構"""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                
                # 創建策略組主表
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS strategy_groups (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        date TEXT NOT NULL,
                        group_id INTEGER NOT NULL,
                        direction TEXT NOT NULL,
                        entry_signal_time TEXT NOT NULL,
                        range_high REAL,
                        range_low REAL,
                        total_lots INTEGER NOT NULL,
                        status TEXT DEFAULT 'WAITING',
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        
                        UNIQUE(date, group_id),
                        CHECK(direction IN ('LONG', 'SHORT')),
                        CHECK(status IN ('WAITING', 'ACTIVE', 'COMPLETED', 'CANCELLED')),
                        CHECK(total_lots BETWEEN 1 AND 3)
                    )
                ''')
                
                # 創建部位記錄詳細表
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS position_records (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        group_id INTEGER NOT NULL,
                        lot_id INTEGER NOT NULL,
                        direction TEXT NOT NULL,
                        entry_price REAL NOT NULL,
                        entry_time TEXT NOT NULL,
                        exit_price REAL,
                        exit_time TEXT,
                        exit_reason TEXT,
                        pnl REAL,
                        pnl_amount REAL,
                        rule_config TEXT,
                        status TEXT DEFAULT 'ACTIVE',
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        
                        FOREIGN KEY (group_id) REFERENCES strategy_groups(id),
                        CHECK(direction IN ('LONG', 'SHORT')),
                        CHECK(status IN ('ACTIVE', 'EXITED')),
                        CHECK(lot_id BETWEEN 1 AND 3),
                        CHECK(exit_reason IN ('移動停利', '保護性停損', '初始停損', '手動出場') OR exit_reason IS NULL)
                    )
                ''')
                
                # 創建風險管理狀態表
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS risk_management_states (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        position_id INTEGER NOT NULL,
                        peak_price REAL NOT NULL,
                        current_stop_loss REAL,
                        trailing_activated BOOLEAN DEFAULT FALSE,
                        protection_activated BOOLEAN DEFAULT FALSE,
                        last_update_time TEXT NOT NULL,
                        update_reason TEXT,
                        previous_stop_loss REAL,
                        
                        FOREIGN KEY (position_id) REFERENCES position_records(id),
                        CHECK(update_reason IN ('價格更新', '移動停利啟動', '保護性停損更新', '初始化') OR update_reason IS NULL)
                    )
                ''')
                
                # 創建每日策略統計表
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS daily_strategy_stats (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        date TEXT NOT NULL UNIQUE,
                        total_groups INTEGER DEFAULT 0,
                        completed_groups INTEGER DEFAULT 0,
                        total_positions INTEGER DEFAULT 0,
                        exited_positions INTEGER DEFAULT 0,
                        total_pnl REAL DEFAULT 0,
                        total_pnl_amount REAL DEFAULT 0,
                        win_rate REAL DEFAULT 0,
                        avg_pnl REAL DEFAULT 0,
                        max_profit REAL DEFAULT 0,
                        max_loss REAL DEFAULT 0,
                        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    )
                ''')
                
                # 創建性能優化索引
                cursor.execute('CREATE INDEX IF NOT EXISTS idx_strategy_groups_date_status ON strategy_groups(date, status)')
                cursor.execute('CREATE INDEX IF NOT EXISTS idx_position_records_group_status ON position_records(group_id, status)')
                cursor.execute('CREATE INDEX IF NOT EXISTS idx_risk_states_position_update ON risk_management_states(position_id, last_update_time)')
                
                conn.commit()
                logger.info("✅ 多組策略資料庫表結構創建完成")
                
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
    
    def create_strategy_group(self, date: str, group_id: int, direction: str, 
                            signal_time: str, range_high: float, range_low: float, 
                            total_lots: int) -> int:
        """創建策略組記錄"""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    INSERT INTO strategy_groups 
                    (date, group_id, direction, entry_signal_time, range_high, range_low, total_lots)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                ''', (date, group_id, direction, signal_time, range_high, range_low, total_lots))
                
                strategy_group_id = cursor.lastrowid
                conn.commit()
                
                logger.info(f"創建策略組: ID={strategy_group_id}, 組別={group_id}, 方向={direction}")
                return strategy_group_id
                
        except Exception as e:
            logger.error(f"創建策略組失敗: {e}")
            raise
    
    def create_position_record(self, group_id: int, lot_id: int, direction: str,
                             entry_price: float, entry_time: str, rule_config: str) -> int:
        """創建部位記錄"""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    INSERT INTO position_records 
                    (group_id, lot_id, direction, entry_price, entry_time, rule_config)
                    VALUES (?, ?, ?, ?, ?, ?)
                ''', (group_id, lot_id, direction, entry_price, entry_time, rule_config))
                
                position_id = cursor.lastrowid
                conn.commit()
                
                logger.info(f"創建部位記錄: ID={position_id}, 組={group_id}, 口={lot_id}, 價格={entry_price}")
                return position_id
                
        except Exception as e:
            logger.error(f"創建部位記錄失敗: {e}")
            raise
    
    def update_position_exit(self, position_id: int, exit_price: float, 
                           exit_time: str, exit_reason: str, pnl: float):
        """更新部位出場資訊"""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                
                # 計算損益金額 (小台指每點50元)
                pnl_amount = pnl * 50
                
                cursor.execute('''
                    UPDATE position_records 
                    SET exit_price = ?, exit_time = ?, exit_reason = ?, 
                        pnl = ?, pnl_amount = ?, status = 'EXITED',
                        updated_at = CURRENT_TIMESTAMP
                    WHERE id = ?
                ''', (exit_price, exit_time, exit_reason, pnl, pnl_amount, position_id))
                
                conn.commit()
                logger.info(f"更新部位出場: ID={position_id}, 損益={pnl}點")
                
        except Exception as e:
            logger.error(f"更新部位出場失敗: {e}")
            raise
    
    def create_risk_management_state(self, position_id: int, peak_price: float, 
                                   current_time: str, update_reason: str = "初始化"):
        """創建風險管理狀態記錄"""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    INSERT INTO risk_management_states 
                    (position_id, peak_price, last_update_time, update_reason)
                    VALUES (?, ?, ?, ?)
                ''', (position_id, peak_price, current_time, update_reason))
                
                conn.commit()
                logger.info(f"創建風險管理狀態: 部位={position_id}, 峰值={peak_price}")
                
        except Exception as e:
            logger.error(f"創建風險管理狀態失敗: {e}")
            raise
    
    def update_risk_management_state(self, position_id: int, peak_price: float = None,
                                   current_stop_loss: float = None, trailing_activated: bool = None,
                                   protection_activated: bool = None, update_time: str = None,
                                   update_reason: str = None):
        """更新風險管理狀態"""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                
                # 構建動態更新語句
                update_fields = []
                params = []
                
                if peak_price is not None:
                    update_fields.append("peak_price = ?")
                    params.append(peak_price)
                
                if current_stop_loss is not None:
                    update_fields.append("current_stop_loss = ?")
                    params.append(current_stop_loss)
                
                if trailing_activated is not None:
                    update_fields.append("trailing_activated = ?")
                    params.append(trailing_activated)
                
                if protection_activated is not None:
                    update_fields.append("protection_activated = ?")
                    params.append(protection_activated)
                
                if update_time is not None:
                    update_fields.append("last_update_time = ?")
                    params.append(update_time)
                
                if update_reason is not None:
                    update_fields.append("update_reason = ?")
                    params.append(update_reason)
                
                if update_fields:
                    params.append(position_id)
                    sql = f"UPDATE risk_management_states SET {', '.join(update_fields)} WHERE position_id = ?"
                    cursor.execute(sql, params)
                    conn.commit()
                
        except Exception as e:
            logger.error(f"更新風險管理狀態失敗: {e}")
            raise

    def get_active_positions_by_group(self, group_id: int) -> List[Dict]:
        """取得指定組的活躍部位"""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    SELECT p.*, r.peak_price, r.current_stop_loss, r.trailing_activated, r.protection_activated
                    FROM position_records p
                    LEFT JOIN risk_management_states r ON p.id = r.position_id
                    WHERE p.group_id = ? AND p.status = 'ACTIVE'
                    ORDER BY p.lot_id
                ''', (group_id,))

                rows = cursor.fetchall()
                return [dict(row) for row in rows]

        except Exception as e:
            logger.error(f"查詢活躍部位失敗: {e}")
            return []

    def get_all_active_positions(self) -> List[Dict]:
        """取得所有活躍部位"""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    SELECT p.*, r.peak_price, r.current_stop_loss, r.trailing_activated, r.protection_activated,
                           sg.range_high, sg.range_low
                    FROM position_records p
                    LEFT JOIN risk_management_states r ON p.id = r.position_id
                    LEFT JOIN strategy_groups sg ON p.group_id = sg.id
                    WHERE p.status = 'ACTIVE'
                    ORDER BY p.group_id, p.lot_id
                ''')

                rows = cursor.fetchall()
                return [dict(row) for row in rows]

        except Exception as e:
            logger.error(f"查詢所有活躍部位失敗: {e}")
            return []

    def get_strategy_group_info(self, group_id: int) -> Optional[Dict]:
        """取得策略組資訊"""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    SELECT * FROM strategy_groups WHERE id = ?
                ''', (group_id,))

                row = cursor.fetchone()
                return dict(row) if row else None

        except Exception as e:
            logger.error(f"查詢策略組資訊失敗: {e}")
            return None

    def get_daily_strategy_summary(self, date_str: Optional[str] = None) -> Dict:
        """取得每日策略統計摘要"""
        if not date_str:
            date_str = date.today().isoformat()

        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()

                # 查詢基本統計
                cursor.execute('''
                    SELECT
                        COUNT(DISTINCT sg.id) as total_groups,
                        COUNT(DISTINCT CASE WHEN sg.status = 'COMPLETED' THEN sg.id END) as completed_groups,
                        COUNT(pr.id) as total_positions,
                        COUNT(CASE WHEN pr.status = 'EXITED' THEN pr.id END) as exited_positions,
                        COALESCE(SUM(pr.pnl), 0) as total_pnl,
                        COALESCE(SUM(pr.pnl_amount), 0) as total_pnl_amount,
                        COALESCE(AVG(pr.pnl), 0) as avg_pnl,
                        COALESCE(MAX(pr.pnl), 0) as max_profit,
                        COALESCE(MIN(pr.pnl), 0) as max_loss
                    FROM strategy_groups sg
                    LEFT JOIN position_records pr ON sg.id = pr.group_id
                    WHERE sg.date = ?
                ''', (date_str,))

                row = cursor.fetchone()
                if row:
                    stats = dict(row)
                    # 計算勝率
                    if stats['exited_positions'] > 0:
                        cursor.execute('''
                            SELECT COUNT(*) as winning_positions
                            FROM position_records pr
                            JOIN strategy_groups sg ON pr.group_id = sg.id
                            WHERE sg.date = ? AND pr.status = 'EXITED' AND pr.pnl > 0
                        ''', (date_str,))

                        winning_row = cursor.fetchone()
                        winning_positions = winning_row['winning_positions'] if winning_row else 0
                        stats['win_rate'] = (winning_positions / stats['exited_positions']) * 100
                    else:
                        stats['win_rate'] = 0

                    return stats
                else:
                    return self._get_empty_stats()

        except Exception as e:
            logger.error(f"查詢每日統計失敗: {e}")
            return self._get_empty_stats()

    def _get_empty_stats(self) -> Dict:
        """取得空的統計數據"""
        return {
            'total_groups': 0,
            'completed_groups': 0,
            'total_positions': 0,
            'exited_positions': 0,
            'total_pnl': 0,
            'total_pnl_amount': 0,
            'win_rate': 0,
            'avg_pnl': 0,
            'max_profit': 0,
            'max_loss': 0
        }

    def update_group_status(self, group_id: int, status: str):
        """更新策略組狀態"""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    UPDATE strategy_groups SET status = ? WHERE id = ?
                ''', (status, group_id))
                conn.commit()

        except Exception as e:
            logger.error(f"更新組狀態失敗: {e}")
            raise

    def get_today_waiting_groups(self, date_str: Optional[str] = None) -> List[Dict]:
        """取得今日等待進場的策略組"""
        if not date_str:
            date_str = date.today().isoformat()

        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    SELECT * FROM strategy_groups
                    WHERE date = ? AND status = 'WAITING'
                    ORDER BY group_id
                ''', (date_str,))

                rows = cursor.fetchall()
                return [dict(row) for row in rows]

        except Exception as e:
            logger.error(f"查詢等待組失敗: {e}")
            return []

    def get_today_strategy_groups(self, date_str: Optional[str] = None) -> List[Dict]:
        """取得今日所有策略組"""
        if not date_str:
            date_str = date.today().isoformat()

        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    SELECT * FROM strategy_groups
                    WHERE date = ?
                    ORDER BY group_id
                ''', (date_str,))

                rows = cursor.fetchall()
                return [dict(row) for row in rows]
        except Exception as e:
            logger.error(f"查詢今日策略組失敗: {e}")
            return []
