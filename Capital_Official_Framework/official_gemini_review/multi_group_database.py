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
                        entry_price REAL,
                        entry_time TEXT NOT NULL,
                        exit_price REAL,
                        exit_time TEXT,
                        exit_reason TEXT,
                        pnl REAL,
                        pnl_amount REAL,
                        rule_config TEXT,
                        status TEXT DEFAULT 'ACTIVE',
                        order_id TEXT,
                        api_seq_no TEXT,
                        order_status TEXT DEFAULT 'PENDING',
                        retry_count INTEGER DEFAULT 0,
                        original_price REAL,
                        max_slippage_points INTEGER DEFAULT 5,
                        last_retry_time TEXT,
                        retry_reason TEXT,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

                        FOREIGN KEY (group_id) REFERENCES strategy_groups(id),
                        CHECK(direction IN ('LONG', 'SHORT')),
                        CHECK(status IN ('ACTIVE', 'EXITED', 'FAILED')),
                        CHECK(order_status IN ('PENDING', 'FILLED', 'CANCELLED', 'REJECTED') OR order_status IS NULL),
                        CHECK(lot_id BETWEEN 1 AND 3),
                        CHECK(exit_reason IN ('移動停利', '保護性停損', '初始停損', '手動出場', 'FOK失敗', '下單失敗') OR exit_reason IS NULL),
                        CHECK(retry_count IS NULL OR (retry_count >= 0 AND retry_count <= 5)),
                        CHECK(max_slippage_points IS NULL OR max_slippage_points > 0)
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
                        update_category TEXT,
                        update_message TEXT,
                        previous_stop_loss REAL,

                        FOREIGN KEY (position_id) REFERENCES position_records(id),
                        CHECK(update_category IN ('價格更新', '移動停利啟動', '保護性停損更新', '初始化', '成交初始化', '簡化追蹤成交確認') OR update_category IS NULL),
                        CHECK(update_message IS NULL OR LENGTH(update_message) > 0)
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
                
                # 檢查並升級現有資料庫結構
                self._upgrade_database_schema(cursor)

                # 🔧 強制檢查並添加缺失欄位
                self._ensure_required_columns(cursor)

                # 🛡️ 升級保護性停損資料庫結構
                self._upgrade_protective_stop_schema(cursor)

                # 創建性能優化索引
                cursor.execute('CREATE INDEX IF NOT EXISTS idx_strategy_groups_date_status ON strategy_groups(date, status)')
                cursor.execute('CREATE INDEX IF NOT EXISTS idx_position_records_group_status ON position_records(group_id, status)')
                cursor.execute('CREATE INDEX IF NOT EXISTS idx_position_records_order_id ON position_records(order_id)')
                cursor.execute('CREATE INDEX IF NOT EXISTS idx_position_records_api_seq_no ON position_records(api_seq_no)')
                cursor.execute('CREATE INDEX IF NOT EXISTS idx_risk_states_position_update ON risk_management_states(position_id, last_update_time)')

                conn.commit()
                logger.info("✅ 多組策略資料庫表結構創建完成")
                
        except Exception as e:
            logger.error(f"❌ 資料庫初始化失敗: {e}")
            raise

    def _upgrade_protective_stop_schema(self, cursor):
        """升級資料庫結構以支援保護性停損"""
        try:
            # 檢查position_records表是否需要添加保護性停損欄位
            cursor.execute("PRAGMA table_info(position_records)")
            pr_columns = [column[1] for column in cursor.fetchall()]

            # 添加保護性停損相關欄位到position_records
            protective_fields = [
                ('protective_stop_price', 'REAL'),
                ('protective_stop_activated', 'INTEGER DEFAULT 0'),
                ('first_lot_exit_profit', 'REAL')
            ]

            for field_name, field_type in protective_fields:
                if field_name not in pr_columns:
                    try:
                        cursor.execute(f'ALTER TABLE position_records ADD COLUMN {field_name} {field_type}')
                        logger.info(f"✅ 添加position_records.{field_name}欄位")
                    except Exception as e:
                        logger.warning(f"⚠️ 添加position_records.{field_name}失敗: {e}")

            # 檢查risk_management_states表是否需要添加保護性停損欄位
            cursor.execute("PRAGMA table_info(risk_management_states)")
            rms_columns = [column[1] for column in cursor.fetchall()]

            # 添加保護性停損相關欄位到risk_management_states
            if 'protective_stop_price' not in rms_columns:
                try:
                    cursor.execute('ALTER TABLE risk_management_states ADD COLUMN protective_stop_price REAL')
                    logger.info("✅ 添加risk_management_states.protective_stop_price欄位")
                except Exception as e:
                    logger.warning(f"⚠️ 添加protective_stop_price失敗: {e}")

            if 'cumulative_profit_before' not in rms_columns:
                try:
                    cursor.execute('ALTER TABLE risk_management_states ADD COLUMN cumulative_profit_before REAL DEFAULT 0')
                    logger.info("✅ 添加risk_management_states.cumulative_profit_before欄位")
                except Exception as e:
                    logger.warning(f"⚠️ 添加cumulative_profit_before失敗: {e}")

            logger.info("🛡️ 保護性停損資料庫結構升級完成")

        except Exception as e:
            logger.error(f"❌ 保護性停損資料庫結構升級失敗: {e}")

    def _upgrade_database_schema(self, cursor):
        """升級資料庫結構以支援訂單追蹤"""
        try:
            # 檢查是否需要添加新欄位
            cursor.execute("PRAGMA table_info(position_records)")
            columns = [column[1] for column in cursor.fetchall()]

            # 添加 order_id 欄位
            if 'order_id' not in columns:
                cursor.execute('ALTER TABLE position_records ADD COLUMN order_id TEXT')
                logger.info("✅ 添加 order_id 欄位")

            # 添加 api_seq_no 欄位
            if 'api_seq_no' not in columns:
                cursor.execute('ALTER TABLE position_records ADD COLUMN api_seq_no TEXT')
                logger.info("✅ 添加 api_seq_no 欄位")

            # 添加 order_status 欄位
            if 'order_status' not in columns:
                cursor.execute('ALTER TABLE position_records ADD COLUMN order_status TEXT DEFAULT "PENDING"')
                logger.info("✅ 添加 order_status 欄位")

            # 檢查並修復 entry_price 的 NOT NULL 約束
            self._fix_entry_price_constraint(cursor)

            logger.info("✅ 資料庫結構升級完成")

        except Exception as e:
            logger.error(f"❌ 資料庫升級失敗: {e}")
            # 不拋出異常，讓系統繼續運行

    def _ensure_required_columns(self, cursor):
        """確保所有必要欄位都存在"""
        try:
            # 檢查position_records表的欄位
            cursor.execute("PRAGMA table_info(position_records)")
            columns = [column[1] for column in cursor.fetchall()]

            required_columns = {
                'retry_count': 'INTEGER DEFAULT 0',
                'original_price': 'REAL',
                'max_slippage_points': 'INTEGER DEFAULT 5',
                'last_retry_time': 'TEXT',
                'retry_reason': 'TEXT'
            }

            for column_name, column_def in required_columns.items():
                if column_name not in columns:
                    try:
                        cursor.execute(f'ALTER TABLE position_records ADD COLUMN {column_name} {column_def}')
                        logger.info(f"✅ 添加缺失欄位: {column_name}")
                    except Exception as e:
                        logger.warning(f"⚠️ 添加欄位 {column_name} 失敗: {e}")

            logger.info("✅ 必要欄位檢查完成")

        except Exception as e:
            logger.error(f"❌ 檢查必要欄位失敗: {e}")

    def _fix_entry_price_constraint(self, cursor):
        """修復 entry_price 的 NOT NULL 約束問題"""
        try:
            # 檢查表結構中是否有 NOT NULL 約束
            cursor.execute("SELECT sql FROM sqlite_master WHERE type='table' AND name='position_records'")
            table_sql = cursor.fetchone()

            if table_sql and 'entry_price REAL NOT NULL' in table_sql[0]:
                logger.info("🔧 檢測到舊的 entry_price NOT NULL 約束，開始修復...")

                # 重建表結構（移除 NOT NULL 約束）
                self._rebuild_position_records_table(cursor)
                logger.info("✅ entry_price 約束修復完成")
            else:
                logger.info("✅ entry_price 約束已正確（允許 NULL）")

        except Exception as e:
            logger.error(f"❌ 修復 entry_price 約束失敗: {e}")

    def _rebuild_position_records_table(self, cursor):
        """重建 position_records 表以移除 entry_price 的 NOT NULL 約束"""
        try:
            # 1. 備份現有數據
            cursor.execute('''
                CREATE TEMPORARY TABLE position_records_backup AS
                SELECT * FROM position_records
            ''')

            # 2. 刪除舊表
            cursor.execute('DROP TABLE position_records')

            # 3. 創建新表（正確的結構）
            cursor.execute('''
                CREATE TABLE position_records (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    group_id INTEGER NOT NULL,
                    lot_id INTEGER NOT NULL,
                    direction TEXT NOT NULL,
                    entry_price REAL,
                    entry_time TEXT NOT NULL,
                    exit_price REAL,
                    exit_time TEXT,
                    exit_reason TEXT,
                    pnl REAL,
                    pnl_amount REAL,
                    rule_config TEXT,
                    status TEXT DEFAULT 'ACTIVE',
                    order_id TEXT,
                    api_seq_no TEXT,
                    order_status TEXT DEFAULT 'PENDING',
                    retry_count INTEGER DEFAULT 0,
                    original_price REAL,
                    max_slippage_points INTEGER DEFAULT 5,
                    last_retry_time TEXT,
                    retry_reason TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

                    FOREIGN KEY (group_id) REFERENCES strategy_groups(id),
                    CHECK(direction IN ('LONG', 'SHORT')),
                    CHECK(status IN ('ACTIVE', 'EXITED', 'FAILED')),
                    CHECK(order_status IN ('PENDING', 'FILLED', 'CANCELLED', 'REJECTED') OR order_status IS NULL),
                    CHECK(lot_id BETWEEN 1 AND 3),
                    CHECK(exit_reason IN ('移動停利', '保護性停損', '初始停損', '手動出場', 'FOK失敗', '下單失敗') OR exit_reason IS NULL),
                    CHECK(retry_count IS NULL OR (retry_count >= 0 AND retry_count <= 5)),
                    CHECK(max_slippage_points IS NULL OR max_slippage_points > 0)
                )
            ''')

            # 4. 恢復數據
            cursor.execute('''
                INSERT INTO position_records
                SELECT * FROM position_records_backup
            ''')

            # 5. 清理臨時表
            cursor.execute('DROP TABLE position_records_backup')

            logger.info("🔄 position_records 表重建完成")

        except Exception as e:
            logger.error(f"❌ 重建 position_records 表失敗: {e}")
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
                             entry_price: Optional[float] = None, entry_time: Optional[str] = None,
                             rule_config: Optional[str] = None, order_id: Optional[str] = None,
                             api_seq_no: Optional[str] = None, order_status: str = 'PENDING',
                             retry_count: int = 0, max_slippage_points: int = 5) -> int:
        """
        創建部位記錄 - 支援訂單追蹤，包含group_id驗證

        包含防禦性檢查以確保數字參數不會是 None，避免後續的 TypeError。

        Args:
            group_id: 組別ID
            lot_id: 口數ID
            direction: 交易方向
            entry_price: 進場價格（可選）
            entry_time: 進場時間（可選）
            rule_config: 規則配置（可選）
            order_id: 訂單ID（可選）
            api_seq_no: API序號（可選）
            order_status: 訂單狀態，默認為 'PENDING'
            retry_count: 重試次數，默認為 0
            max_slippage_points: 最大滑價點數，默認為 5

        Returns:
            int: 創建的部位記錄ID
        """
        try:
            # 🛡️ 根源性修復：確保數字參數不是 None，避免後續比較操作出現 TypeError
            if retry_count is None:
                retry_count = 0
                logger.warning(f"retry_count為None，設為默認值0")
            if max_slippage_points is None:
                max_slippage_points = 5
                logger.warning(f"max_slippage_points為None，設為默認值5")

            with self.get_connection() as conn:
                cursor = conn.cursor()

                # 🔧 新增：驗證group_id是否為有效的邏輯組別編號
                today = date.today().isoformat()
                cursor.execute('''
                    SELECT COUNT(*) FROM strategy_groups
                    WHERE group_id = ? AND date = ?
                ''', (group_id, today))

                group_exists = cursor.fetchone()[0] > 0
                if not group_exists:
                    # 檢查是否錯誤傳入了DB_ID
                    cursor.execute('''
                        SELECT id AS group_pk, group_id AS logical_group_id FROM strategy_groups
                        WHERE id = ? AND date = ?
                    ''', (group_id, today))

                    db_id_result = cursor.fetchone()
                    if db_id_result:
                        correct_group_id = db_id_result[0]
                        logger.error(f"❌ group_id驗證失敗: 傳入{group_id}是DB_ID，正確的group_id應為{correct_group_id}")
                        raise ValueError(f"Invalid group_id: {group_id} is a DB_ID, should be {correct_group_id}")
                    else:
                        logger.error(f"❌ group_id驗證失敗: 找不到group_id={group_id}的策略組")
                        raise ValueError(f"Strategy group not found: group_id={group_id}")

                cursor.execute('''
                    INSERT INTO position_records
                    (group_id, lot_id, direction, entry_price, entry_time, rule_config,
                     order_id, api_seq_no, order_status, retry_count, max_slippage_points)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', (group_id, lot_id, direction, entry_price, entry_time, rule_config,
                      order_id, api_seq_no, order_status, retry_count, max_slippage_points))

                position_id = cursor.lastrowid
                conn.commit()

                logger.info(f"創建部位記錄: ID={position_id}, 組={group_id}, 口={lot_id}, "
                           f"狀態={order_status}, 訂單ID={order_id}")
                return position_id

        except Exception as e:
            logger.error(f"創建部位記錄失敗: {e}")
            raise
    
    def update_position_exit(self, position_id: int, exit_price: float,
                           exit_time: str, exit_reason: str, pnl: float,
                           on_success_callback=None):
        """
        更新部位出場資訊

        Args:
            position_id: 部位ID
            exit_price: 出場價格
            exit_time: 出場時間
            exit_reason: 出場原因
            pnl: 損益點數
            on_success_callback: 成功後的回呼函數 (可選)
        """
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

                # 🔧 新增：成功後調用回呼函數
                if on_success_callback:
                    try:
                        on_success_callback(position_id)
                        logger.debug(f"部位{position_id}出場回呼執行成功")
                    except Exception as callback_error:
                        logger.error(f"部位{position_id}出場回呼執行失敗: {callback_error}")
                        # 注意：回呼失敗不影響主要的資料庫更新操作

        except Exception as e:
            logger.error(f"更新部位出場失敗: {e}")
            raise
    
    def create_risk_management_state(self, position_id: int, peak_price: float,
                                   current_time: str, update_category: str = "初始化",
                                   update_message: str = None):
        """創建風險管理狀態記錄"""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    INSERT INTO risk_management_states
                    (position_id, peak_price, last_update_time, update_category, update_message)
                    VALUES (?, ?, ?, ?, ?)
                ''', (position_id, peak_price, current_time, update_category, update_message))

                conn.commit()
                logger.info(f"創建風險管理狀態: 部位={position_id}, 峰值={peak_price}")
                return True

        except Exception as e:
            logger.error(f"創建風險管理狀態失敗: {e}")
            return False
    
    def update_risk_management_state(self, position_id: int, peak_price: float = None,
                                   current_stop_loss: float = None, trailing_activated: bool = None,
                                   protection_activated: bool = None, update_time: str = None,
                                   update_category: str = None, update_message: str = None):
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

                if update_category is not None:
                    update_fields.append("update_category = ?")
                    params.append(update_category)

                if update_message is not None:
                    update_fields.append("update_message = ?")
                    params.append(update_message)

                if update_fields:
                    params.append(position_id)
                    sql = f"UPDATE risk_management_states SET {', '.join(update_fields)} WHERE position_id = ?"
                    cursor.execute(sql, params)
                    conn.commit()

        except Exception as e:
            logger.error(f"更新風險管理狀態失敗: {e}")
            raise

    def update_protective_stop(self, position_id: int, protective_price: float,
                             activated: bool = True, first_lot_profit: float = None) -> bool:
        """
        更新保護性停損狀態

        Args:
            position_id: 部位ID
            protective_price: 保護性停損價格
            activated: 是否啟動保護性停損
            first_lot_profit: 第一口平倉獲利

        Returns:
            bool: 是否成功更新
        """
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()

                # 更新position_records表
                update_fields = []
                params = []

                if protective_price is not None:
                    update_fields.append("protective_stop_price = ?")
                    params.append(protective_price)

                if activated is not None:
                    update_fields.append("protective_stop_activated = ?")
                    params.append(1 if activated else 0)

                if first_lot_profit is not None:
                    update_fields.append("first_lot_exit_profit = ?")
                    params.append(first_lot_profit)

                if update_fields:
                    params.append(position_id)
                    sql = f"UPDATE position_records SET {', '.join(update_fields)} WHERE id = ?"
                    cursor.execute(sql, params)

                # 同時更新risk_management_states表
                if protective_price is not None:
                    cursor.execute('''
                        UPDATE risk_management_states
                        SET protective_stop_price = ?, protection_activated = ?
                        WHERE position_id = ?
                    ''', (protective_price, activated, position_id))

                conn.commit()
                logger.info(f"✅ 保護性停損狀態更新成功: 部位{position_id}")
                return True

        except Exception as e:
            logger.error(f"❌ 更新保護性停損狀態失敗: {e}")
            return False

    def get_active_positions_by_group(self, group_id: int) -> List[Dict]:
        """取得指定組的活躍部位 - 🔧 修復：正確關聯邏輯組ID"""
        try:
            from datetime import date
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    SELECT p.id AS position_pk, p.group_id AS group_pk, p.lot_id, p.direction, p.entry_price,
                           p.entry_time, p.exit_price, p.exit_time, p.exit_reason, p.pnl, p.pnl_amount,
                           p.rule_config, p.status, p.order_id, p.api_seq_no, p.order_status, p.retry_count,
                           p.original_price, p.max_slippage_points, p.last_retry_time, p.retry_reason,
                           p.created_at, p.updated_at,
                           r.peak_price, r.current_stop_loss, r.trailing_activated, r.protection_activated,
                           sg.range_high, sg.range_low, sg.direction
                    FROM position_records p
                    LEFT JOIN risk_management_states r ON p.id = r.position_id
                    LEFT JOIN (
                        SELECT id AS group_pk, group_id AS logical_group_id, date, direction, entry_signal_time,
                               range_high, range_low, total_lots, status, created_at
                        FROM strategy_groups
                        WHERE date = ?
                        ORDER BY id DESC
                    ) sg ON p.group_id = sg.logical_group_id
                    WHERE p.group_id = ? AND p.status = 'ACTIVE'
                    ORDER BY p.lot_id
                ''', (date.today().isoformat(), group_id))

                rows = cursor.fetchall()
                return [dict(row) for row in rows]

        except Exception as e:
            logger.error(f"查詢活躍部位失敗: {e}")
            return []

    def get_group_positions(self, group_id: int) -> List[Dict]:
        """取得指定組的部位 - 別名方法，向後兼容"""
        # 🔧 修復：添加此方法解決 'get_group_positions' 不存在的錯誤
        return self.get_active_positions_by_group(group_id)

    def get_all_active_positions(self) -> List[Dict]:
        """取得所有活躍部位 - 🔧 修復：正確關聯策略組"""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    SELECT p.id AS position_pk, p.group_id AS group_pk, p.lot_id, p.direction, p.entry_price,
                           p.entry_time, p.exit_price, p.exit_time, p.exit_reason, p.pnl, p.pnl_amount,
                           p.rule_config, p.status, p.order_id, p.api_seq_no, p.order_status, p.retry_count,
                           p.original_price, p.max_slippage_points, p.last_retry_time, p.retry_reason,
                           p.created_at, p.updated_at,
                           r.peak_price, r.current_stop_loss, r.trailing_activated, r.protection_activated,
                           sg.range_high, sg.range_low
                    FROM position_records p
                    LEFT JOIN risk_management_states r ON p.id = r.position_id
                    LEFT JOIN (
                        SELECT id AS group_pk, group_id AS logical_group_id, date, direction, entry_signal_time,
                               range_high, range_low, total_lots, status, created_at
                        FROM strategy_groups
                        WHERE date = ?
                        ORDER BY id DESC
                    ) sg ON p.group_id = sg.group_pk
                    WHERE p.status = 'ACTIVE'
                    ORDER BY p.group_id, p.lot_id
                ''', (date.today().isoformat(),))

                rows = cursor.fetchall()
                return [dict(row) for row in rows]

        except Exception as e:
            logger.error(f"查詢所有活躍部位失敗: {e}")
            return []

    def get_strategy_group_info(self, group_id: int) -> Optional[Dict]:
        """取得策略組資訊 - 🔧 修復：根據group_id查詢，不是主鍵id"""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                # 🔧 修復：查詢條件改為 group_id，並限制為今日記錄
                cursor.execute('''
                    SELECT id AS group_pk, group_id AS logical_group_id, date, direction, entry_signal_time,
                           range_high, range_low, total_lots, status, created_at
                    FROM strategy_groups
                    WHERE group_id = ? AND date = ?
                    ORDER BY id DESC LIMIT 1
                ''', (group_id, date.today().isoformat()))

                row = cursor.fetchone()
                return dict(row) if row else None

        except Exception as e:
            logger.error(f"查詢策略組資訊失敗: {e}")
            return None

    def get_strategy_group_by_db_id(self, db_id: int) -> Optional[Dict]:
        """根據主鍵ID取得策略組基本資訊 - 🔧 新增：解決進場邏輯問題"""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    SELECT id AS group_pk, group_id AS logical_group_id, date, direction, entry_signal_time,
                           range_high, range_low, total_lots, status, created_at
                    FROM strategy_groups
                    WHERE id = ?
                ''', (db_id,))

                row = cursor.fetchone()
                return dict(row) if row else None

        except Exception as e:
            logger.error(f"根據DB_ID查詢策略組失敗: {e}")
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
                            JOIN strategy_groups sg ON pr.group_id = sg.group_id AND sg.date = ?
                            WHERE pr.status = 'EXITED' AND pr.pnl > 0
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
                    SELECT id AS group_pk, group_id AS logical_group_id, date, direction, entry_signal_time,
                           range_high, range_low, total_lots, status, created_at
                    FROM strategy_groups
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
                    SELECT id AS group_pk, group_id AS logical_group_id, date, direction, entry_signal_time,
                           range_high, range_low, total_lots, status, created_at
                    FROM strategy_groups
                    WHERE date = ?
                    ORDER BY group_id
                ''', (date_str,))

                rows = cursor.fetchall()
                return [dict(row) for row in rows]
        except Exception as e:
            logger.error(f"查詢今日策略組失敗: {e}")
            return []

    # 🔧 新增：訂單追蹤相關方法

    def update_position_order_info(self, position_id: int, order_id: str, api_seq_no: str) -> bool:
        """更新部位記錄的訂單資訊"""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    UPDATE position_records
                    SET order_id = ?, api_seq_no = ?, updated_at = CURRENT_TIMESTAMP
                    WHERE id = ?
                ''', (order_id, api_seq_no, position_id))
                conn.commit()
                logger.info(f"更新部位{position_id}訂單資訊: order_id={order_id}, api_seq_no={api_seq_no}")
                return True
        except Exception as e:
            logger.error(f"更新部位訂單資訊失敗: {e}")
            return False

    def confirm_position_filled(self, position_id: int, actual_fill_price: float,
                              fill_time: str, order_status: str = 'FILLED') -> bool:
        """確認部位成交"""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()

                # 任務4診斷：檢查更新前的狀態
                cursor.execute('SELECT entry_price, status FROM position_records WHERE id = ?', (position_id,))
                before_update = cursor.fetchone()
                if before_update:
                    logger.info(f"[DB] 部位{position_id}更新前: entry_price={before_update[0]}, status={before_update[1]}")

                cursor.execute('''
                    UPDATE position_records
                    SET entry_price = ?, entry_time = ?, status = 'ACTIVE',
                        order_status = ?, updated_at = CURRENT_TIMESTAMP
                    WHERE id = ?
                ''', (actual_fill_price, fill_time, order_status, position_id))

                # 檢查是否有行被更新
                rows_affected = cursor.rowcount
                conn.commit()

                if rows_affected > 0:
                    logger.info(f"✅ 確認部位{position_id}成交: entry_price={actual_fill_price}, 影響行數={rows_affected}")
                    return True
                else:
                    logger.warning(f"⚠️ 部位{position_id}成交確認: 沒有行被更新")
                    return False

        except Exception as e:
            logger.error(f"確認部位成交失敗: {e}")
            return False

    def mark_position_failed(self, position_id: int, failure_reason: str,
                           order_status: str = 'CANCELLED') -> bool:
        """標記部位失敗"""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    UPDATE position_records
                    SET status = 'FAILED', order_status = ?,
                        exit_reason = ?, updated_at = CURRENT_TIMESTAMP
                    WHERE id = ?
                ''', (order_status, failure_reason, position_id))
                conn.commit()
                logger.info(f"❌ 標記部位{position_id}失敗: {failure_reason}")
                return True
        except Exception as e:
            logger.error(f"標記部位失敗失敗: {e}")
            return False

    def update_position_status(self, position_id: int, status: str,
                             exit_reason: str = None, exit_price: float = None,
                             order_status: str = None) -> bool:
        """
        更新部位狀態 - 統一出場管理器專用

        Args:
            position_id: 部位ID
            status: 新狀態 (EXITING, EXITED, FAILED等)
            exit_reason: 出場原因 (可選)
            exit_price: 出場價格 (可選)
            order_status: 訂單狀態 (可選)

        Returns:
            bool: 更新是否成功
        """
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()

                # 構建動態更新語句
                update_fields = ["status = ?", "updated_at = CURRENT_TIMESTAMP"]
                params = [status]

                if exit_reason is not None:
                    update_fields.append("exit_reason = ?")
                    params.append(exit_reason)

                if exit_price is not None:
                    update_fields.append("exit_price = ?")
                    params.append(exit_price)

                if order_status is not None:
                    update_fields.append("order_status = ?")
                    params.append(order_status)

                # 添加WHERE條件的position_id
                params.append(position_id)

                sql = f'''
                    UPDATE position_records
                    SET {", ".join(update_fields)}
                    WHERE id = ?
                '''

                cursor.execute(sql, params)
                conn.commit()

                logger.info(f"✅ 更新部位{position_id}狀態: {status}")
                if exit_reason:
                    logger.info(f"   出場原因: {exit_reason}")
                if exit_price:
                    logger.info(f"   出場價格: {exit_price}")

                return True

        except Exception as e:
            logger.error(f"更新部位狀態失敗: {e}")
            return False

    def get_position_by_order_id(self, order_id: str) -> Optional[Dict]:
        """根據訂單ID查詢部位記錄"""
        try:
            with self.get_connection() as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                cursor.execute('''
                    SELECT id AS position_pk, group_id AS group_pk, lot_id, direction, entry_price, entry_time,
                           exit_price, exit_time, exit_reason, pnl, pnl_amount, rule_config, status, order_id,
                           api_seq_no, order_status, retry_count, original_price, max_slippage_points,
                           last_retry_time, retry_reason, created_at, updated_at
                    FROM position_records WHERE order_id = ?
                ''', (order_id,))
                row = cursor.fetchone()
                return dict(row) if row else None
        except Exception as e:
            logger.error(f"根據訂單ID查詢部位失敗: {e}")
            return None

    def get_position_statistics(self, date_str: Optional[str] = None) -> Dict:
        """取得部位統計資訊"""
        try:
            if date_str is None:
                date_str = date.today().strftime('%Y-%m-%d')

            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    SELECT
                        COUNT(*) as total_positions,
                        SUM(CASE WHEN pr.status = 'ACTIVE' THEN 1 ELSE 0 END) as active_positions,
                        SUM(CASE WHEN pr.status = 'FAILED' THEN 1 ELSE 0 END) as failed_positions,
                        SUM(CASE WHEN pr.status = 'EXITED' THEN 1 ELSE 0 END) as exited_positions,
                        ROUND(SUM(CASE WHEN pr.status = 'ACTIVE' THEN 1 ELSE 0 END) * 100.0 / COUNT(*), 2) as success_rate
                    FROM position_records pr
                    JOIN strategy_groups sg ON pr.group_id = sg.group_id AND sg.date = ?
                    WHERE 1=1
                ''', (date_str,))

                row = cursor.fetchone()
                if row:
                    return {
                        'total_positions': row[0],
                        'active_positions': row[1],
                        'failed_positions': row[2],
                        'exited_positions': row[3],
                        'success_rate': row[4] or 0.0
                    }
                return {
                    'total_positions': 0,
                    'active_positions': 0,
                    'failed_positions': 0,
                    'exited_positions': 0,
                    'success_rate': 0.0
                }
        except Exception as e:
            logger.error(f"取得部位統計失敗: {e}")
            return {
                'total_positions': 0,
                'active_positions': 0,
                'failed_positions': 0,
                'exited_positions': 0,
                'success_rate': 0.0
            }

    # 🔧 新增：追價機制相關方法
    def update_retry_info(self, position_id: int, retry_count: int,
                         retry_price: float, retry_reason: str) -> bool:
        """更新重試資訊"""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    UPDATE position_records
                    SET retry_count = ?, last_retry_time = CURRENT_TIMESTAMP,
                        retry_reason = ?, updated_at = CURRENT_TIMESTAMP
                    WHERE id = ?
                ''', (retry_count, retry_reason, position_id))
                conn.commit()
                logger.info(f"✅ 更新部位{position_id}重試資訊: 第{retry_count}次, 原因:{retry_reason}")
                return True
        except Exception as e:
            logger.error(f"更新重試資訊失敗: {e}")
            return False

    def get_failed_positions_for_retry(self, max_retry_count: int = 5,
                                      time_window_seconds: int = 30) -> List[Dict]:
        """取得可重試的失敗部位"""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    SELECT pr.*, sg.direction as group_direction, sg.date
                    FROM position_records pr
                    JOIN strategy_groups sg ON pr.group_id = sg.group_id AND sg.date = date('now', 'localtime')
                    WHERE pr.status = 'FAILED'
                    AND pr.order_status = 'CANCELLED'
                    AND pr.retry_count < ?
                    AND (pr.last_retry_time IS NULL OR
                         (julianday('now') - julianday(pr.last_retry_time)) * 86400 < ?)
                    ORDER BY pr.created_at ASC
                ''', (max_retry_count, time_window_seconds))

                rows = cursor.fetchall()
                columns = [description[0] for description in cursor.description]

                result = []
                for row in rows:
                    position_dict = dict(zip(columns, row))
                    result.append(position_dict)

                logger.info(f"📋 查詢到{len(result)}個可重試的失敗部位")
                return result

        except Exception as e:
            logger.error(f"查詢可重試失敗部位失敗: {e}")
            return []

    def increment_retry_count(self, position_id: int) -> bool:
        """增加重試計數"""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    UPDATE position_records
                    SET retry_count = retry_count + 1,
                        last_retry_time = CURRENT_TIMESTAMP,
                        updated_at = CURRENT_TIMESTAMP
                    WHERE id = ?
                ''', (position_id,))
                conn.commit()

                # 取得更新後的重試次數
                cursor.execute('SELECT retry_count AS retry_count_value FROM position_records WHERE id = ?', (position_id,))
                row = cursor.fetchone()
                retry_count = row[0] if row else 0

                logger.info(f"📈 部位{position_id}重試計數增加至: {retry_count}")
                return True
        except Exception as e:
            logger.error(f"增加重試計數失敗: {e}")
            return False

    def set_original_price(self, position_id: int, original_price: float) -> bool:
        """設定原始價格（用於滑價計算）"""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    UPDATE position_records
                    SET original_price = ?, updated_at = CURRENT_TIMESTAMP
                    WHERE id = ?
                ''', (original_price, position_id))
                conn.commit()
                logger.info(f"💰 設定部位{position_id}原始價格: {original_price}")
                return True
        except Exception as e:
            logger.error(f"設定原始價格失敗: {e}")
            return False

    def get_position_by_id(self, position_id: int) -> Optional[Dict]:
        """根據ID取得部位資訊 - 🔧 修復：使用分步查詢避免JOIN失敗"""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()

                # 🔧 步驟1：查詢部位基本信息
                cursor.execute('''
                    SELECT id AS position_pk, group_id AS group_pk, lot_id, direction, entry_price, entry_time,
                           exit_price, exit_time, exit_reason, pnl, pnl_amount, rule_config, status, order_id,
                           api_seq_no, order_status, retry_count, original_price, max_slippage_points,
                           last_retry_time, retry_reason, created_at, updated_at
                    FROM position_records WHERE id = ?
                ''', (position_id,))

                row = cursor.fetchone()
                if not row:
                    return None

                # 轉換為字典
                columns = [description[0] for description in cursor.description]
                position_data = dict(zip(columns, row))

                # 🔧 步驟2：查詢策略組信息（容錯處理）
                group_id = position_data.get('group_pk')
                if group_id:
                    # 首先嘗試按 group_id 查詢
                    cursor.execute('''
                        SELECT range_high, range_low, direction as group_direction
                        FROM strategy_groups
                        WHERE group_id = ? AND date = ?
                        ORDER BY id DESC
                        LIMIT 1
                    ''', (group_id, date.today().isoformat()))

                    group_row = cursor.fetchone()
                    if group_row:
                        # 成功找到策略組
                        position_data['range_high'] = group_row[0]
                        position_data['range_low'] = group_row[1]
                        position_data['group_direction'] = group_row[2]
                        position_data['date'] = date.today().isoformat()
                    else:
                        # 🔧 容錯：嘗試按 DB_ID 查詢（處理數據不一致問題）
                        logger.warning(f"按group_id={group_id}找不到策略組，嘗試按DB_ID查詢")
                        cursor.execute('''
                            SELECT range_high, range_low, direction as group_direction, group_id as real_group_id
                            FROM strategy_groups
                            WHERE id = ? AND date = ?
                            LIMIT 1
                        ''', (group_id, date.today().isoformat()))

                        fallback_row = cursor.fetchone()
                        if fallback_row:
                            # 找到了，說明是數據不一致問題
                            position_data['range_high'] = fallback_row[0]
                            position_data['range_low'] = fallback_row[1]
                            position_data['group_direction'] = fallback_row[2]
                            position_data['date'] = date.today().isoformat()
                            logger.warning(f"部位{position_id}的group_id={group_id}實際是DB_ID，真實group_id={fallback_row[3]}")
                        else:
                            # 完全找不到策略組信息
                            logger.warning(f"找不到部位{position_id}對應的策略組信息: group_id={group_id}, date={date.today().isoformat()}")
                            # 使用默認值，不讓平倉失敗
                            position_data['range_high'] = None
                            position_data['range_low'] = None
                            position_data['group_direction'] = position_data.get('direction')
                            position_data['date'] = date.today().isoformat()

                return position_data

        except Exception as e:
            logger.error(f"根據ID查詢部位失敗: {e}")
            return None
