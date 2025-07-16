#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
平倉機制資料庫擴展模組
基於回測程式邏輯，擴展現有資料庫結構以支援完整的平倉機制
"""

import sqlite3
import logging
from typing import Dict, List, Optional
from datetime import datetime

logger = logging.getLogger(__name__)

class ExitMechanismDatabaseExtension:
    """平倉機制資料庫擴展管理器"""
    
    def __init__(self, db_manager):
        """
        初始化資料庫擴展管理器
        
        Args:
            db_manager: 現有的多組策略資料庫管理器
        """
        self.db_manager = db_manager
        self.console_enabled = True
        
    def extend_database_schema(self):
        """擴展資料庫結構以支援平倉機制"""
        try:
            with self.db_manager.get_connection() as conn:
                cursor = conn.cursor()
                
                # 1. 擴展 position_records 表格 - 新增平倉相關欄位
                self._extend_position_records_table(cursor)
                
                # 2. 創建 group_exit_status 表格 - 組別層級的平倉狀態
                self._create_group_exit_status_table(cursor)
                
                # 3. 創建 exit_events 表格 - 平倉事件記錄
                self._create_exit_events_table(cursor)
                
                # 4. 創建 lot_exit_rules 表格 - 口數平倉規則配置
                self._create_lot_exit_rules_table(cursor)
                
                # 5. 創建相關索引
                self._create_exit_mechanism_indexes(cursor)
                
                conn.commit()
                
                if self.console_enabled:
                    print("[EXIT_DB] ✅ 平倉機制資料庫擴展完成")
                    print("[EXIT_DB] 📊 新增表格: group_exit_status, exit_events, lot_exit_rules")
                    print("[EXIT_DB] 🔧 擴展 position_records 表格平倉相關欄位")
                
                logger.info("平倉機制資料庫擴展成功")
                return True
                
        except Exception as e:
            logger.error(f"平倉機制資料庫擴展失敗: {e}")
            if self.console_enabled:
                print(f"[EXIT_DB] ❌ 資料庫擴展失敗: {e}")
            return False
    
    def _extend_position_records_table(self, cursor):
        """擴展 position_records 表格"""
        
        # 檢查現有欄位
        cursor.execute("PRAGMA table_info(position_records)")
        existing_columns = {row[1] for row in cursor.fetchall()}
        
        # 需要新增的欄位定義
        new_columns = {
            'initial_stop_loss': 'REAL',                    # 初始停損價 (range_low/high)
            'current_stop_loss': 'REAL',                    # 當前停損價
            'is_initial_stop': 'BOOLEAN DEFAULT TRUE',      # 是否為初始停損狀態
            'trailing_activated': 'BOOLEAN DEFAULT FALSE',  # 移動停利啟動狀態
            'peak_price': 'REAL',                          # 峰值價格追蹤
            'trailing_activation_points': 'INTEGER',        # 啟動點位 (15/40/65)
            'trailing_pullback_ratio': 'REAL DEFAULT 0.20', # 回撤比例 (0.20)
            'protective_multiplier': 'REAL',               # 保護倍數 (2.0)
            'cumulative_profit_before': 'REAL DEFAULT 0',  # 前序累積獲利
            'realized_pnl': 'REAL DEFAULT 0',              # 已實現損益
            'lot_rule_id': 'INTEGER',                      # 風險規則ID (1,2,3)
            'exit_trigger_type': 'TEXT',                   # 平倉觸發類型
            'exit_order_id': 'TEXT',                       # 平倉訂單ID
            'last_price_update_time': 'TEXT'               # 最後價格更新時間
        }
        
        # 新增缺少的欄位
        for column_name, column_def in new_columns.items():
            if column_name not in existing_columns:
                try:
                    cursor.execute(f"ALTER TABLE position_records ADD COLUMN {column_name} {column_def}")
                    if self.console_enabled:
                        print(f"[EXIT_DB] ➕ 新增欄位: position_records.{column_name}")
                except sqlite3.OperationalError as e:
                    if "duplicate column name" not in str(e):
                        raise e

        # 確保 lot_rule_id 欄位與 lot_exit_rules 表格關聯
        cursor.execute("PRAGMA table_info(position_records)")
        columns = {row[1] for row in cursor.fetchall()}
        if 'lot_rule_id' in columns:
            # 更新現有部位的 lot_rule_id (根據 lot_id 設定)
            cursor.execute('''
                UPDATE position_records
                SET lot_rule_id = lot_id
                WHERE lot_rule_id IS NULL AND lot_id IS NOT NULL
            ''')
            if self.console_enabled:
                print(f"[EXIT_DB] 🔗 更新 position_records.lot_rule_id 關聯")
    
    def _create_group_exit_status_table(self, cursor):
        """創建組別平倉狀態表"""
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS group_exit_status (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                group_id INTEGER NOT NULL,
                date TEXT NOT NULL,
                total_lots INTEGER NOT NULL,
                active_lots INTEGER DEFAULT 0,
                exited_lots INTEGER DEFAULT 0,
                cumulative_realized_pnl REAL DEFAULT 0,
                cumulative_pnl_amount REAL DEFAULT 0,
                range_high REAL NOT NULL,
                range_low REAL NOT NULL,
                direction TEXT NOT NULL,
                exit_mechanism_enabled BOOLEAN DEFAULT TRUE,
                last_update_time TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                
                FOREIGN KEY (group_id) REFERENCES strategy_groups (id),
                CHECK(direction IN ('LONG', 'SHORT')),
                CHECK(active_lots >= 0),
                CHECK(exited_lots >= 0),
                CHECK(total_lots = active_lots + exited_lots)
            )
        ''')
        
        if self.console_enabled:
            print("[EXIT_DB] 📋 創建 group_exit_status 表格 - 組別平倉狀態追蹤")
    
    def _create_exit_events_table(self, cursor):
        """創建平倉事件記錄表"""
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS exit_events (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                event_id TEXT UNIQUE NOT NULL,
                position_id INTEGER NOT NULL,
                group_id INTEGER NOT NULL,
                event_type TEXT NOT NULL,
                trigger_price REAL NOT NULL,
                exit_price REAL,
                trigger_time TEXT NOT NULL,
                execution_time TEXT,
                pnl REAL,
                pnl_amount REAL,
                trigger_reason TEXT,
                execution_status TEXT DEFAULT 'PENDING',
                order_id TEXT,
                error_message TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                
                FOREIGN KEY (position_id) REFERENCES position_records (id),
                FOREIGN KEY (group_id) REFERENCES strategy_groups (id),
                CHECK(event_type IN ('INITIAL_STOP', 'TRAILING_STOP', 'PROTECTIVE_STOP', 'EOD_CLOSE', 'MANUAL_EXIT')),
                CHECK(execution_status IN ('PENDING', 'EXECUTED', 'FAILED', 'CANCELLED'))
            )
        ''')
        
        if self.console_enabled:
            print("[EXIT_DB] 📝 創建 exit_events 表格 - 平倉事件記錄")
    
    def _create_lot_exit_rules_table(self, cursor):
        """創建口數平倉規則配置表"""
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS lot_exit_rules (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                rule_name TEXT NOT NULL,
                lot_number INTEGER NOT NULL,
                trailing_activation_points INTEGER NOT NULL,
                trailing_pullback_ratio REAL NOT NULL DEFAULT 0.20,
                protective_stop_multiplier REAL,
                description TEXT,
                is_default BOOLEAN DEFAULT FALSE,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                
                CHECK(lot_number BETWEEN 1 AND 3),
                CHECK(trailing_activation_points > 0),
                CHECK(trailing_pullback_ratio BETWEEN 0.1 AND 0.5),
                CHECK(protective_stop_multiplier IS NULL OR protective_stop_multiplier > 0)
            )
        ''')
        
        # 🔧 修復：先檢查是否已有預設規則，避免重複插入
        cursor.execute("SELECT COUNT(*) FROM lot_exit_rules WHERE is_default = 1")
        existing_default_count = cursor.fetchone()[0]

        if existing_default_count == 0:
            # 只有在沒有預設規則時才插入 - 🔧 用戶自定義配置
            default_rules = [
                ('回測標準規則', 1, 15, 0.10, None, '第1口: 15點啟動移動停利, 10%回撤'),
                ('回測標準規則', 2, 40, 0.10, 2.0, '第2口: 40點啟動移動停利, 10%回撤, 2倍保護'),
                ('回測標準規則', 3, 41, 0.20, 2.0, '第3口: 41點啟動移動停利, 20%回撤, 2倍保護')
            ]

            for rule_data in default_rules:
                cursor.execute('''
                    INSERT INTO lot_exit_rules
                    (rule_name, lot_number, trailing_activation_points, trailing_pullback_ratio,
                     protective_stop_multiplier, description, is_default)
                    VALUES (?, ?, ?, ?, ?, ?, 1)
                ''', rule_data)

            if self.console_enabled:
                print("[EXIT_DB] 📊 插入預設規則: 15/40/41點啟動, 10%/10%/20%回撤, 2倍保護")
        else:
            if self.console_enabled:
                print(f"[EXIT_DB] ℹ️ 預設規則已存在 ({existing_default_count}個)，跳過插入")
        
        if self.console_enabled:
            print("[EXIT_DB] ⚙️ 創建 lot_exit_rules 表格 - 口數平倉規則配置")
            print("[EXIT_DB] 📊 插入預設規則: 15/40/65點啟動, 2倍保護")
    
    def _create_exit_mechanism_indexes(self, cursor):
        """創建平倉機制相關索引"""
        indexes = [
            'CREATE INDEX IF NOT EXISTS idx_position_records_exit_status ON position_records(group_id, status, is_initial_stop)',
            'CREATE INDEX IF NOT EXISTS idx_position_records_trailing ON position_records(trailing_activated, peak_price)',
            'CREATE INDEX IF NOT EXISTS idx_group_exit_status_date ON group_exit_status(date, group_id)',
            'CREATE INDEX IF NOT EXISTS idx_exit_events_position ON exit_events(position_id, event_type)',
            'CREATE INDEX IF NOT EXISTS idx_exit_events_time ON exit_events(trigger_time, execution_time)',
            'CREATE INDEX IF NOT EXISTS idx_lot_exit_rules_lookup ON lot_exit_rules(rule_name, lot_number)'
        ]
        
        for index_sql in indexes:
            cursor.execute(index_sql)
        
        if self.console_enabled:
            print("[EXIT_DB] 🔍 創建平倉機制性能索引")
    
    def verify_extension(self) -> bool:
        """驗證資料庫擴展是否成功"""
        try:
            with self.db_manager.get_connection() as conn:
                cursor = conn.cursor()
                
                # 檢查新表格是否存在
                required_tables = ['group_exit_status', 'exit_events', 'lot_exit_rules']
                for table in required_tables:
                    cursor.execute(
                        "SELECT name FROM sqlite_master WHERE type='table' AND name=?",
                        (table,)
                    )
                    if not cursor.fetchone():
                        if self.console_enabled:
                            print(f"[EXIT_DB] ❌ 表格 {table} 不存在")
                        return False
                
                # 檢查 position_records 新欄位
                cursor.execute("PRAGMA table_info(position_records)")
                columns = {row[1] for row in cursor.fetchall()}
                required_columns = [
                    'initial_stop_loss', 'current_stop_loss', 'is_initial_stop',
                    'trailing_activated', 'peak_price', 'trailing_activation_points'
                ]
                
                for column in required_columns:
                    if column not in columns:
                        if self.console_enabled:
                            print(f"[EXIT_DB] ❌ 欄位 position_records.{column} 不存在")
                        return False
                
                # 🔧 修復：檢查預設規則並自動修復重複問題
                cursor.execute("SELECT COUNT(*) FROM lot_exit_rules WHERE is_default = 1")
                default_rules_count = cursor.fetchone()[0]

                if default_rules_count > 3:
                    if self.console_enabled:
                        print(f"[EXIT_DB] ⚠️ 發現重複預設規則: {default_rules_count}/3，自動清理...")

                    # 自動清理重複規則，保留每個口數的第一個
                    cursor.execute('''
                        DELETE FROM lot_exit_rules
                        WHERE is_default = 1 AND id NOT IN (
                            SELECT MIN(id)
                            FROM lot_exit_rules
                            WHERE is_default = 1
                            GROUP BY lot_number
                        )
                    ''')

                    # 重新檢查
                    cursor.execute("SELECT COUNT(*) FROM lot_exit_rules WHERE is_default = 1")
                    default_rules_count = cursor.fetchone()[0]

                    if self.console_enabled:
                        print(f"[EXIT_DB] 🧹 清理完成，當前規則數: {default_rules_count}")

                if default_rules_count != 3:
                    if self.console_enabled:
                        print(f"[EXIT_DB] ❌ 預設規則數量仍不正確: {default_rules_count}/3")
                    return False
                
                if self.console_enabled:
                    print("[EXIT_DB] ✅ 資料庫擴展驗證通過")
                    print("[EXIT_DB] 📊 所有表格和欄位已正確創建")
                    print("[EXIT_DB] ⚙️ 預設平倉規則已載入")
                
                return True
                
        except Exception as e:
            logger.error(f"資料庫擴展驗證失敗: {e}")
            if self.console_enabled:
                print(f"[EXIT_DB] ❌ 驗證失敗: {e}")
            return False


def extend_database_for_exit_mechanism(db_manager):
    """
    為現有資料庫擴展平倉機制支援
    
    Args:
        db_manager: 現有的資料庫管理器
        
    Returns:
        bool: 擴展是否成功
    """
    extension = ExitMechanismDatabaseExtension(db_manager)
    
    print("[EXIT_DB] 🚀 開始平倉機制資料庫擴展...")
    
    # 執行擴展
    if not extension.extend_database_schema():
        return False
    
    # 驗證擴展
    if not extension.verify_extension():
        return False
    
    print("[EXIT_DB] 🎉 平倉機制資料庫擴展完成!")
    return True


if __name__ == "__main__":
    # 測試用途
    print("平倉機制資料庫擴展模組")
    print("請在主程式中調用 extend_database_for_exit_mechanism() 函數")
