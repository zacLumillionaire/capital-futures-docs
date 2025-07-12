#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
資料庫管理器 - 處理所有資料庫操作
支援批量插入、資料去重、完整性驗證、統計查詢等功能
"""

import sqlite3
import logging
import os
import json
import sys
from datetime import datetime, timedelta
from contextlib import contextmanager

# 添加專案路徑
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from history_config import DATABASE_PATH, DATA_DIR

logger = logging.getLogger(__name__)

class DatabaseManager:
    """資料庫管理器"""

    def __init__(self, db_path=DATABASE_PATH):
        """
        初始化資料庫管理器
        
        Args:
            db_path: 資料庫檔案路徑
        """
        self.db_path = db_path
        
        # 確保資料目錄存在
        os.makedirs(DATA_DIR, exist_ok=True)
        
        # 初始化資料庫
        self.initialize_database()

    def initialize_database(self):
        """初始化資料庫結構"""
        try:
            # 讀取SQL結構檔案
            schema_path = os.path.join(os.path.dirname(__file__), 'schema.sql')
            
            if not os.path.exists(schema_path):
                logger.error(f"❌ 找不到資料庫結構檔案: {schema_path}")
                raise FileNotFoundError(f"Schema file not found: {schema_path}")

            with open(schema_path, 'r', encoding='utf-8') as f:
                schema_sql = f.read()

            # 執行建表語句
            with self.get_connection() as conn:
                conn.executescript(schema_sql)
                conn.commit()

            logger.info("✅ 資料庫初始化完成")

        except Exception as e:
            logger.error(f"❌ 資料庫初始化失敗: {e}")
            raise

    @contextmanager
    def get_connection(self):
        """
        取得資料庫連線（使用上下文管理器）
        
        Yields:
            sqlite3.Connection: 資料庫連線
        """
        conn = None
        try:
            conn = sqlite3.connect(self.db_path)
            conn.row_factory = sqlite3.Row  # 讓查詢結果可以用欄位名稱存取
            yield conn
        except Exception as e:
            if conn:
                conn.rollback()
            logger.error(f"❌ 資料庫操作失敗: {e}")
            raise
        finally:
            if conn:
                conn.close()

    def insert_tick_data(self, tick_data):
        """
        插入單筆逐筆資料
        
        Args:
            tick_data: 逐筆資料字典
            
        Returns:
            bool: 是否成功插入
        """
        sql = """
        INSERT OR IGNORE INTO tick_data
        (symbol, market_no, index_code, ptr, trade_date, trade_time, trade_time_ms,
         bid_price, ask_price, close_price, volume, simulate_flag, data_type)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """

        values = (
            tick_data.get('symbol'),
            tick_data.get('market_no'),
            tick_data.get('index_code'),
            tick_data.get('ptr'),
            tick_data.get('trade_date'),
            tick_data.get('trade_time'),
            tick_data.get('trade_time_ms'),
            tick_data.get('bid_price'),
            tick_data.get('ask_price'),
            tick_data.get('close_price'),
            tick_data.get('volume'),
            tick_data.get('simulate_flag', 0),
            tick_data.get('data_type', 'HISTORY')
        )

        try:
            with self.get_connection() as conn:
                cursor = conn.execute(sql, values)
                conn.commit()
                return cursor.rowcount > 0
        except Exception as e:
            logger.error(f"❌ 插入逐筆資料失敗: {e}")
            return False

    def batch_insert_tick_data(self, tick_data_list):
        """
        批量插入逐筆資料
        
        Args:
            tick_data_list: 逐筆資料列表
            
        Returns:
            int: 成功插入的筆數
        """
        if not tick_data_list:
            return 0

        sql = """
        INSERT OR IGNORE INTO tick_data
        (symbol, market_no, index_code, ptr, trade_date, trade_time, trade_time_ms,
         bid_price, ask_price, close_price, volume, simulate_flag, data_type)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """

        values_list = []
        for tick_data in tick_data_list:
            values = (
                tick_data.get('symbol'),
                tick_data.get('market_no'),
                tick_data.get('index_code'),
                tick_data.get('ptr'),
                tick_data.get('trade_date'),
                tick_data.get('trade_time'),
                tick_data.get('trade_time_ms'),
                tick_data.get('bid_price'),
                tick_data.get('ask_price'),
                tick_data.get('close_price'),
                tick_data.get('volume'),
                tick_data.get('simulate_flag', 0),
                tick_data.get('data_type', 'HISTORY')
            )
            values_list.append(values)

        try:
            with self.get_connection() as conn:
                cursor = conn.executemany(sql, values_list)
                conn.commit()
                inserted_count = cursor.rowcount
                logger.debug(f"💾 批量插入 {inserted_count}/{len(values_list)} 筆逐筆資料")
                return inserted_count
        except Exception as e:
            logger.error(f"❌ 批量插入逐筆資料失敗: {e}")
            return 0

    def batch_insert_best5_data(self, best5_data_list):
        """
        批量插入五檔資料
        
        Args:
            best5_data_list: 五檔資料列表
            
        Returns:
            int: 成功插入的筆數
        """
        if not best5_data_list:
            return 0

        sql = """
        INSERT OR IGNORE INTO best5_data
        (symbol, market_no, index_code, trade_date, trade_time,
         bid_price_1, bid_volume_1, bid_price_2, bid_volume_2, bid_price_3, bid_volume_3,
         bid_price_4, bid_volume_4, bid_price_5, bid_volume_5,
         ask_price_1, ask_volume_1, ask_price_2, ask_volume_2, ask_price_3, ask_volume_3,
         ask_price_4, ask_volume_4, ask_price_5, ask_volume_5,
         extend_bid, extend_bid_qty, extend_ask, extend_ask_qty, simulate_flag)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """

        values_list = []
        for best5_data in best5_data_list:
            values = (
                best5_data.get('symbol'),
                best5_data.get('market_no'),
                best5_data.get('index_code'),
                best5_data.get('trade_date'),
                best5_data.get('trade_time'),
                best5_data.get('bid_price_1'), best5_data.get('bid_volume_1'),
                best5_data.get('bid_price_2'), best5_data.get('bid_volume_2'),
                best5_data.get('bid_price_3'), best5_data.get('bid_volume_3'),
                best5_data.get('bid_price_4'), best5_data.get('bid_volume_4'),
                best5_data.get('bid_price_5'), best5_data.get('bid_volume_5'),
                best5_data.get('ask_price_1'), best5_data.get('ask_volume_1'),
                best5_data.get('ask_price_2'), best5_data.get('ask_volume_2'),
                best5_data.get('ask_price_3'), best5_data.get('ask_volume_3'),
                best5_data.get('ask_price_4'), best5_data.get('ask_volume_4'),
                best5_data.get('ask_price_5'), best5_data.get('ask_volume_5'),
                best5_data.get('extend_bid'), best5_data.get('extend_bid_qty'),
                best5_data.get('extend_ask'), best5_data.get('extend_ask_qty'),
                best5_data.get('simulate_flag', 0)
            )
            values_list.append(values)

        try:
            with self.get_connection() as conn:
                cursor = conn.executemany(sql, values_list)
                conn.commit()
                inserted_count = cursor.rowcount
                logger.debug(f"💾 批量插入 {inserted_count}/{len(values_list)} 筆五檔資料")
                return inserted_count
        except Exception as e:
            logger.error(f"❌ 批量插入五檔資料失敗: {e}")
            return 0

    def batch_insert_kline_data(self, kline_data_list):
        """
        批量插入K線資料

        Args:
            kline_data_list: K線資料列表

        Returns:
            int: 成功插入的筆數
        """
        if not kline_data_list:
            return 0

        sql = """
        INSERT OR IGNORE INTO kline_data
        (symbol, kline_type, trade_date, trade_time, open_price, high_price, low_price, close_price, volume)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """

        values_list = []
        for kline_data in kline_data_list:
            values = (
                kline_data.get('symbol'),
                kline_data.get('kline_type', 'MINUTE'),
                kline_data.get('trade_date'),
                kline_data.get('trade_time'),
                kline_data.get('open_price'),
                kline_data.get('high_price'),
                kline_data.get('low_price'),
                kline_data.get('close_price'),
                kline_data.get('volume')
            )
            values_list.append(values)

        try:
            with self.get_connection() as conn:
                cursor = conn.executemany(sql, values_list)
                conn.commit()
                inserted_count = cursor.rowcount
                logger.debug(f"💾 批量插入 {inserted_count}/{len(values_list)} 筆K線資料")
                return inserted_count
        except Exception as e:
            logger.error(f"❌ 批量插入K線資料失敗: {e}")
            return 0

    def log_collection_start(self, collection_type, symbol, parameters=None):
        """
        記錄收集開始

        Args:
            collection_type: 收集類型
            symbol: 商品代碼
            parameters: 收集參數

        Returns:
            int: 記錄ID，失敗時返回None
        """
        sql = """
        INSERT INTO collection_log
        (collection_type, symbol, start_time, status, parameters)
        VALUES (?, ?, ?, 'RUNNING', ?)
        """

        try:
            with self.get_connection() as conn:
                cursor = conn.execute(sql, (
                    collection_type, symbol, datetime.now(),
                    json.dumps(parameters, ensure_ascii=False) if parameters else None
                ))
                conn.commit()
                return cursor.lastrowid
        except Exception as e:
            logger.error(f"❌ 記錄收集開始失敗: {e}")
            return None

    def log_collection_end(self, log_id, records_count, status='COMPLETED', error_message=None):
        """
        記錄收集結束

        Args:
            log_id: 記錄ID
            records_count: 收集筆數
            status: 完成狀態
            error_message: 錯誤訊息

        Returns:
            bool: 是否成功更新
        """
        sql = """
        UPDATE collection_log
        SET end_time = ?, records_count = ?, status = ?, error_message = ?
        WHERE id = ?
        """

        try:
            with self.get_connection() as conn:
                cursor = conn.execute(sql, (
                    datetime.now(), records_count, status, error_message, log_id
                ))
                conn.commit()
                return cursor.rowcount > 0
        except Exception as e:
            logger.error(f"❌ 記錄收集結束失敗: {e}")
            return False

    def get_data_statistics(self, symbol=None):
        """
        取得資料統計

        Args:
            symbol: 商品代碼，None表示所有商品

        Returns:
            dict: 統計資訊
        """
        try:
            with self.get_connection() as conn:
                # 基本統計查詢
                if symbol:
                    where_clause = "WHERE symbol = ?"
                    params = (symbol,)
                else:
                    where_clause = ""
                    params = ()

                # 逐筆資料統計
                tick_sql = f"SELECT COUNT(*) FROM tick_data {where_clause}"
                tick_count = conn.execute(tick_sql, params).fetchone()[0]

                # 五檔資料統計
                best5_sql = f"SELECT COUNT(*) FROM best5_data {where_clause}"
                best5_count = conn.execute(best5_sql, params).fetchone()[0]

                # K線資料統計
                kline_sql = f"SELECT COUNT(*) FROM kline_data {where_clause}"
                kline_count = conn.execute(kline_sql, params).fetchone()[0]

                # 最新資料時間
                latest_tick_sql = f"""
                SELECT MAX(trade_date || trade_time)
                FROM tick_data {where_clause}
                """
                latest_tick = conn.execute(latest_tick_sql, params).fetchone()[0]

                # 日期範圍
                date_range_sql = f"""
                SELECT MIN(trade_date) as min_date, MAX(trade_date) as max_date
                FROM tick_data {where_clause}
                """
                date_range = conn.execute(date_range_sql, params).fetchone()

                return {
                    'symbol': symbol or 'ALL',
                    'tick_count': tick_count,
                    'best5_count': best5_count,
                    'kline_count': kline_count,
                    'total_count': tick_count + best5_count + kline_count,
                    'latest_tick_time': latest_tick,
                    'date_range': {
                        'min_date': date_range['min_date'],
                        'max_date': date_range['max_date']
                    } if date_range['min_date'] else None
                }
        except Exception as e:
            logger.error(f"❌ 取得資料統計失敗: {e}")
            return None

    def get_collection_history(self, limit=10):
        """
        取得收集歷史記錄

        Args:
            limit: 限制筆數

        Returns:
            list: 收集記錄列表
        """
        sql = """
        SELECT
            collection_type, symbol, start_time, end_time,
            records_count, status, error_message, parameters
        FROM collection_log
        ORDER BY start_time DESC
        LIMIT ?
        """

        try:
            with self.get_connection() as conn:
                cursor = conn.execute(sql, (limit,))
                records = []
                for row in cursor.fetchall():
                    record = dict(row)
                    # 解析參數JSON
                    if record['parameters']:
                        try:
                            record['parameters'] = json.loads(record['parameters'])
                        except json.JSONDecodeError:
                            record['parameters'] = {}
                    records.append(record)
                return records
        except Exception as e:
            logger.error(f"❌ 取得收集歷史失敗: {e}")
            return []

    def query_tick_data(self, symbol, start_date=None, end_date=None, limit=1000):
        """
        查詢逐筆資料

        Args:
            symbol: 商品代碼
            start_date: 起始日期 (YYYYMMDD)
            end_date: 結束日期 (YYYYMMDD)
            limit: 限制筆數

        Returns:
            list: 逐筆資料列表
        """
        sql = """
        SELECT symbol, trade_date, trade_time, close_price, volume,
               bid_price, ask_price, data_type
        FROM tick_data
        WHERE symbol = ?
        """
        params = [symbol]

        if start_date:
            sql += " AND trade_date >= ?"
            params.append(start_date)

        if end_date:
            sql += " AND trade_date <= ?"
            params.append(end_date)

        sql += " ORDER BY trade_date DESC, trade_time DESC LIMIT ?"
        params.append(limit)

        try:
            with self.get_connection() as conn:
                cursor = conn.execute(sql, params)
                return [dict(row) for row in cursor.fetchall()]
        except Exception as e:
            logger.error(f"❌ 查詢逐筆資料失敗: {e}")
            return []

    def query_kline_data(self, symbol, kline_type='MINUTE', start_date=None, end_date=None, limit=1000):
        """
        查詢K線資料

        Args:
            symbol: 商品代碼
            kline_type: K線類型
            start_date: 起始日期
            end_date: 結束日期
            limit: 限制筆數

        Returns:
            list: K線資料列表
        """
        sql = """
        SELECT symbol, kline_type, trade_date, trade_time,
               open_price, high_price, low_price, close_price, volume
        FROM kline_data
        WHERE symbol = ? AND kline_type = ?
        """
        params = [symbol, kline_type]

        if start_date:
            sql += " AND trade_date >= ?"
            params.append(start_date)

        if end_date:
            sql += " AND trade_date <= ?"
            params.append(end_date)

        sql += " ORDER BY trade_date DESC, trade_time DESC LIMIT ?"
        params.append(limit)

        try:
            with self.get_connection() as conn:
                cursor = conn.execute(sql, params)
                return [dict(row) for row in cursor.fetchall()]
        except Exception as e:
            logger.error(f"❌ 查詢K線資料失敗: {e}")
            return []

    def cleanup_old_data(self, days_to_keep=90):
        """
        清理舊資料

        Args:
            days_to_keep: 保留天數

        Returns:
            dict: 清理結果
        """
        cutoff_date = (datetime.now() - timedelta(days=days_to_keep)).strftime('%Y%m%d')

        try:
            with self.get_connection() as conn:
                # 清理逐筆資料
                tick_sql = "DELETE FROM tick_data WHERE trade_date < ?"
                tick_cursor = conn.execute(tick_sql, (cutoff_date,))
                tick_deleted = tick_cursor.rowcount

                # 清理五檔資料
                best5_sql = "DELETE FROM best5_data WHERE trade_date < ?"
                best5_cursor = conn.execute(best5_sql, (cutoff_date,))
                best5_deleted = best5_cursor.rowcount

                # 清理K線資料
                kline_sql = "DELETE FROM kline_data WHERE trade_date < ?"
                kline_cursor = conn.execute(kline_sql, (cutoff_date,))
                kline_deleted = kline_cursor.rowcount

                # 清理收集記錄
                log_sql = "DELETE FROM collection_log WHERE start_time < datetime('now', '-90 days')"
                log_cursor = conn.execute(log_sql)
                log_deleted = log_cursor.rowcount

                conn.commit()

                result = {
                    'cutoff_date': cutoff_date,
                    'tick_deleted': tick_deleted,
                    'best5_deleted': best5_deleted,
                    'kline_deleted': kline_deleted,
                    'log_deleted': log_deleted,
                    'total_deleted': tick_deleted + best5_deleted + kline_deleted
                }

                logger.info(f"✅ 清理舊資料完成: {result}")
                return result

        except Exception as e:
            logger.error(f"❌ 清理舊資料失敗: {e}")
            return None

    def vacuum_database(self):
        """
        壓縮資料庫以回收空間

        Returns:
            bool: 是否成功
        """
        try:
            with self.get_connection() as conn:
                conn.execute("VACUUM")
                conn.commit()
            logger.info("✅ 資料庫壓縮完成")
            return True
        except Exception as e:
            logger.error(f"❌ 資料庫壓縮失敗: {e}")
            return False

    def get_database_info(self):
        """
        取得資料庫資訊

        Returns:
            dict: 資料庫資訊
        """
        try:
            # 檔案大小
            file_size = os.path.getsize(self.db_path) if os.path.exists(self.db_path) else 0

            with self.get_connection() as conn:
                # 資料表資訊
                tables_sql = """
                SELECT name FROM sqlite_master
                WHERE type='table' AND name NOT LIKE 'sqlite_%'
                ORDER BY name
                """
                tables = [row[0] for row in conn.execute(tables_sql).fetchall()]

                # 索引資訊
                indexes_sql = """
                SELECT name FROM sqlite_master
                WHERE type='index' AND name NOT LIKE 'sqlite_%'
                ORDER BY name
                """
                indexes = [row[0] for row in conn.execute(indexes_sql).fetchall()]

                return {
                    'database_path': self.db_path,
                    'file_size_mb': round(file_size / (1024 * 1024), 2),
                    'tables': tables,
                    'indexes': indexes,
                    'table_count': len(tables),
                    'index_count': len(indexes)
                }

        except Exception as e:
            logger.error(f"❌ 取得資料庫資訊失敗: {e}")
            return None
