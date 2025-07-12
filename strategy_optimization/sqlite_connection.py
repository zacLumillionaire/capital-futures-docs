#!/usr/bin/env python3
"""
SQLite 連接模組
提供與 shared.py 相同的接口，實現無縫切換
"""

import sqlite3
import logging
from pathlib import Path
from contextlib import contextmanager
from typing import Tuple, Any

logger = logging.getLogger(__name__)

class SQLiteConnection:
    """SQLite連接管理器，模擬PostgreSQL連接池接口"""
    
    def __init__(self, db_path="stock_data.sqlite"):
        self.db_path = Path(__file__).parent / db_path
        self._ensure_db_exists()
    
    def _ensure_db_exists(self):
        """確保數據庫文件存在"""
        if not self.db_path.exists():
            logger.warning(f"SQLite數據庫不存在: {self.db_path}")
            logger.info("請先運行 export_to_sqlite.py 導出數據")
    
    def get_connection(self, as_dict=True):
        """獲取SQLite連接"""
        conn = sqlite3.connect(self.db_path)

        # 註冊日期時間轉換器
        sqlite3.register_converter("timestamp", self._parse_timestamp)
        sqlite3.register_converter("datetime", self._parse_timestamp)

        if as_dict:
            # 設置row_factory以返回字典格式，並處理日期時間轉換
            conn.row_factory = self._dict_factory

        return conn

    def _parse_timestamp(self, timestamp_bytes):
        """解析時間戳字符串為datetime對象"""
        from datetime import datetime
        timestamp_str = timestamp_bytes.decode('utf-8')

        # 處理不同的日期時間格式
        formats = [
            '%Y-%m-%d %H:%M:%S',
            '%Y-%m-%dT%H:%M:%S',
            '%Y-%m-%d %H:%M:%S.%f',
            '%Y-%m-%dT%H:%M:%S.%f'
        ]

        for fmt in formats:
            try:
                return datetime.strptime(timestamp_str, fmt)
            except ValueError:
                continue

        # 如果都不匹配，嘗試ISO格式
        try:
            return datetime.fromisoformat(timestamp_str.replace('Z', '+00:00'))
        except ValueError:
            logger.warning(f"無法解析時間戳: {timestamp_str}")
            return timestamp_str

    def _dict_factory(self, cursor, row):
        """自定義row factory，返回字典並處理日期時間轉換"""
        from datetime import datetime

        columns = [column[0] for column in cursor.description]
        result = {}

        for i, value in enumerate(row):
            column_name = columns[i]

            # 如果是trade_datetime欄位且是字符串，轉換為datetime
            if column_name == 'trade_datetime' and isinstance(value, str):
                try:
                    # 嘗試解析ISO格式
                    result[column_name] = datetime.fromisoformat(value.replace('Z', '+00:00'))
                except ValueError:
                    # 嘗試其他格式
                    formats = [
                        '%Y-%m-%d %H:%M:%S',
                        '%Y-%m-%dT%H:%M:%S',
                        '%Y-%m-%d %H:%M:%S.%f',
                        '%Y-%m-%dT%H:%M:%S.%f'
                    ]

                    parsed = False
                    for fmt in formats:
                        try:
                            result[column_name] = datetime.strptime(value, fmt)
                            parsed = True
                            break
                        except ValueError:
                            continue

                    if not parsed:
                        logger.warning(f"無法解析trade_datetime: {value}")
                        result[column_name] = value
            else:
                result[column_name] = value

        return result
    
    @contextmanager
    def get_conn_cur(self, as_dict=True):
        """
        上下文管理器，模擬 shared.get_conn_cur_from_pool_b 接口
        返回 (connection, cursor) 元組
        """
        conn = None
        try:
            conn = self.get_connection(as_dict=as_dict)
            cursor = conn.cursor()
            
            logger.debug("✅ SQLite連接已建立")
            yield conn, cursor
            
        except Exception as e:
            if conn:
                conn.rollback()
            logger.error(f"❌ SQLite操作失敗: {e}")
            raise
        finally:
            if conn:
                conn.close()
                logger.debug("🚪 SQLite連接已關閉")

class SQLiteQueryAdapter:
    """SQL查詢適配器，將PostgreSQL查詢轉換為SQLite兼容格式"""
    
    @staticmethod
    def adapt_query(query: str, params: tuple = None) -> Tuple[str, tuple]:
        """
        適配PostgreSQL查詢語法到SQLite
        主要處理日期函數和參數占位符
        """
        adapted_query = query
        adapted_params = params or ()
        
        # 轉換參數占位符：%s -> ?
        adapted_query = adapted_query.replace('%s', '?')
        
        # 轉換日期函數：trade_datetime::date -> date(trade_datetime)
        adapted_query = adapted_query.replace('trade_datetime::date', 'date(trade_datetime)')
        
        # 轉換其他PostgreSQL特定語法
        adapted_query = adapted_query.replace('EXTRACT(hour FROM trade_datetime)', 
                                            "CAST(strftime('%H', trade_datetime) AS INTEGER)")
        adapted_query = adapted_query.replace('EXTRACT(minute FROM trade_datetime)', 
                                            "CAST(strftime('%M', trade_datetime) AS INTEGER)")
        
        logger.debug(f"查詢適配: {query[:50]}... -> {adapted_query[:50]}...")
        
        return adapted_query, adapted_params

# 全局SQLite連接實例
_sqlite_connection = None

def init_sqlite_connection(db_path="stock_data.sqlite"):
    """初始化SQLite連接"""
    global _sqlite_connection
    _sqlite_connection = SQLiteConnection(db_path)
    logger.info(f"🔌 SQLite連接已初始化: {db_path}")

def get_conn_cur_from_sqlite(as_dict=True):
    """
    模擬 shared.get_conn_cur_from_pool_b 接口
    返回SQLite連接的上下文管理器
    """
    if _sqlite_connection is None:
        init_sqlite_connection()
    
    return _sqlite_connection.get_conn_cur(as_dict=as_dict)

class SQLiteCursor:
    """SQLite游標包裝器，提供自動查詢適配"""
    
    def __init__(self, sqlite_cursor):
        self._cursor = sqlite_cursor
        self._adapter = SQLiteQueryAdapter()
    
    def execute(self, query: str, params: tuple = None):
        """執行查詢，自動適配PostgreSQL語法"""
        adapted_query, adapted_params = self._adapter.adapt_query(query, params)
        return self._cursor.execute(adapted_query, adapted_params)
    
    def fetchall(self):
        """獲取所有結果"""
        return self._cursor.fetchall()
    
    def fetchone(self):
        """獲取單個結果"""
        return self._cursor.fetchone()
    
    def fetchmany(self, size=None):
        """獲取多個結果"""
        return self._cursor.fetchmany(size)
    
    def __getattr__(self, name):
        """代理其他方法到原始cursor"""
        return getattr(self._cursor, name)

@contextmanager
def get_conn_cur_from_sqlite_with_adapter(as_dict=True):
    """
    帶查詢適配器的SQLite連接上下文管理器
    自動轉換PostgreSQL查詢語法
    """
    with get_conn_cur_from_sqlite(as_dict=as_dict) as (conn, cursor):
        # 包裝cursor以提供自動適配
        adapted_cursor = SQLiteCursor(cursor)
        yield conn, adapted_cursor

# 測試函數
def test_sqlite_connection():
    """測試SQLite連接和查詢"""
    try:
        init_sqlite_connection()
        
        with get_conn_cur_from_sqlite_with_adapter(as_dict=True) as (conn, cur):
            # 測試基本查詢
            cur.execute("SELECT COUNT(*) as count FROM stock_prices")
            result = cur.fetchone()
            print(f"📊 SQLite記錄總數: {result['count'] if result else 0}")
            
            # 測試日期查詢（PostgreSQL語法）
            cur.execute("SELECT COUNT(*) as count FROM stock_prices WHERE trade_datetime::date = ?", 
                       ('2024-11-01',))
            result = cur.fetchone()
            print(f"📅 2024-11-01 記錄數: {result['count'] if result else 0}")
            
            # 測試日期範圍查詢
            cur.execute("""
                SELECT 
                    MIN(date(trade_datetime)) as min_date,
                    MAX(date(trade_datetime)) as max_date
                FROM stock_prices
            """)
            result = cur.fetchone()
            if result:
                print(f"📈 數據範圍: {result['min_date']} 至 {result['max_date']}")
        
        print("✅ SQLite連接測試成功")
        return True
        
    except Exception as e:
        print(f"❌ SQLite連接測試失敗: {e}")
        return False

if __name__ == "__main__":
    # 運行測試
    test_sqlite_connection()
