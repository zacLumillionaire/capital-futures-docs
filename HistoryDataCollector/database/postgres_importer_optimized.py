#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
PostgreSQL匯入器 - 優化版本
針對1140筆資料從5分鐘優化到幾秒鐘
"""

import os
import sys
import logging
import sqlite3
import time
from datetime import datetime
from decimal import Decimal
import tempfile
import csv

# 添加專案路徑
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

# 導入您的資料庫模組
try:
    from app_setup import init_all_db_pools
    import shared
    HAS_POSTGRES_MODULES = True
except ImportError as e:
    HAS_POSTGRES_MODULES = False
    print(f"⚠️ 無法導入PostgreSQL模組: {e}")

from history_config import DATABASE_PATH

logger = logging.getLogger(__name__)

class PostgreSQLImporterOptimized:
    """PostgreSQL匯入器 - 優化版本"""

    def __init__(self):
        """初始化匯入器"""
        self.sqlite_db_path = "data/history_data.db"
        self.postgres_initialized = False
        
        if not HAS_POSTGRES_MODULES:
            logger.error("❌ PostgreSQL模組未找到，無法進行匯入")
            return
        
        # 初始化PostgreSQL連線池
        try:
            init_all_db_pools()
            self.postgres_initialized = True
            logger.info("✅ PostgreSQL連線池初始化成功")
        except Exception as e:
            logger.error(f"❌ PostgreSQL連線池初始化失敗: {e}")

    def import_kline_to_postgres_fast(self, symbol='MTX00', kline_type='MINUTE', method='copy'):
        """
        快速匯入K線資料到PostgreSQL
        
        Args:
            symbol: 商品代碼
            kline_type: K線類型
            method: 匯入方法 ('copy', 'batch', 'executemany')
        """
        if not self.postgres_initialized:
            logger.error("❌ PostgreSQL未初始化，無法匯入")
            return False

        total_start_time = time.time()
        logger.info(f"🚀 開始快速匯入 {symbol} {kline_type} 資料 (方法: {method})")

        try:
            # 1. 讀取SQLite資料
            data_load_start = time.time()
            sqlite_data = self._load_sqlite_data(symbol, kline_type)
            if not sqlite_data:
                return False
            
            data_load_time = time.time() - data_load_start
            logger.info(f"📊 SQLite資料讀取完成: {len(sqlite_data)} 筆 (耗時: {data_load_time:.2f}秒)")

            # 2. 轉換資料格式
            convert_start = time.time()
            converted_data = self._convert_data_batch(sqlite_data)
            convert_time = time.time() - convert_start
            logger.info(f"🔄 資料轉換完成: {len(converted_data)} 筆 (耗時: {convert_time:.2f}秒)")

            if not converted_data:
                logger.warning("⚠️ 沒有有效資料可匯入")
                return False

            # 3. 根據方法選擇匯入策略
            import_start = time.time()
            if method == 'copy':
                success = self._import_using_copy_optimized(converted_data)
            elif method == 'batch':
                success = self._import_using_batch_optimized(converted_data)
            else:  # executemany
                success = self._import_using_executemany_optimized(converted_data)
            
            import_time = time.time() - import_start
            total_time = time.time() - total_start_time

            if success:
                logger.info(f"✅ 匯入完成！")
                logger.info(f"📊 性能統計:")
                logger.info(f"  - 資料筆數: {len(converted_data)}")
                logger.info(f"  - 總耗時: {total_time:.2f}秒")
                logger.info(f"  - 匯入耗時: {import_time:.2f}秒")
                logger.info(f"  - 平均速度: {len(converted_data)/total_time:.0f} 筆/秒")
                logger.info(f"  - 匯入速度: {len(converted_data)/import_time:.0f} 筆/秒")
            
            return success

        except Exception as e:
            logger.error(f"❌ 快速匯入失敗: {e}", exc_info=True)
            return False

    def _load_sqlite_data(self, symbol, kline_type):
        """載入SQLite資料"""
        try:
            sqlite_conn = sqlite3.connect(self.sqlite_db_path)
            sqlite_conn.row_factory = sqlite3.Row
            
            query_sql = """
                SELECT * FROM kline_data
                WHERE symbol = ? AND kline_type = ?
                ORDER BY trade_date, trade_time
            """
            
            cursor = sqlite_conn.execute(query_sql, (symbol, kline_type))
            all_rows = cursor.fetchall()
            sqlite_conn.close()
            
            if len(all_rows) == 0:
                logger.warning(f"⚠️ 沒有找到 {symbol} {kline_type} 資料")
                return None
            
            return [dict(row) for row in all_rows]
            
        except Exception as e:
            logger.error(f"❌ 載入SQLite資料失敗: {e}")
            return None

    def _convert_data_batch(self, sqlite_data):
        """批量轉換資料格式"""
        converted_data = []
        
        for row_data in sqlite_data:
            try:
                # 解析日期時間
                date_str = str(row_data['trade_date']).strip()
                
                # 直接解析日期時間字串
                try:
                    trade_datetime = datetime.strptime(date_str, '%Y/%m/%d %H:%M')
                except ValueError:
                    try:
                        trade_datetime = datetime.strptime(date_str, '%Y/%m/%d')
                        trade_datetime = trade_datetime.replace(hour=13, minute=45, second=0)
                    except ValueError:
                        logger.warning(f"⚠️ 無法解析日期格式: '{date_str}'")
                        continue

                # 轉換價格資料
                open_price = Decimal(str(row_data['open_price']))
                high_price = Decimal(str(row_data['high_price']))
                low_price = Decimal(str(row_data['low_price']))
                close_price = Decimal(str(row_data['close_price']))
                volume = row_data['volume'] or 0
                price_change = Decimal('0.00')

                converted_data.append({
                    'trade_datetime': trade_datetime,
                    'open_price': open_price,
                    'high_price': high_price,
                    'low_price': low_price,
                    'close_price': close_price,
                    'price_change': price_change,
                    'percentage_change': Decimal('0.0000'),
                    'volume': volume
                })
                
            except Exception as e:
                logger.warning(f"⚠️ 轉換資料失敗: {e}")
                continue
        
        return converted_data

    def _import_using_copy_optimized(self, converted_data):
        """使用COPY命令超高速匯入"""
        try:
            logger.info("⚡ 使用COPY命令進行超高速匯入...")
            
            # 創建臨時CSV檔案
            temp_file = tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.csv', encoding='utf-8')
            csv_writer = csv.writer(temp_file)
            
            # 寫入資料
            for data in converted_data:
                csv_writer.writerow([
                    data['trade_datetime'].strftime('%Y-%m-%d %H:%M:%S'),
                    str(data['open_price']),
                    str(data['high_price']),
                    str(data['low_price']),
                    str(data['close_price']),
                    str(data['price_change']),
                    str(data['percentage_change']),
                    data['volume']
                ])
            
            temp_file.close()
            
            # 使用COPY命令匯入
            with shared.get_conn_cur_from_pool_b(as_dict=False) as (pg_conn, pg_cursor):
                with open(temp_file.name, 'r', encoding='utf-8') as f:
                    pg_cursor.copy_expert("""
                        COPY stock_prices (
                            trade_datetime, open_price, high_price, low_price,
                            close_price, price_change, percentage_change, volume
                        ) FROM STDIN WITH CSV
                    """, f)
                
                pg_conn.commit()
            
            # 清理臨時檔案
            os.unlink(temp_file.name)
            logger.info("✅ COPY命令匯入完成")
            return True
            
        except Exception as e:
            logger.error(f"❌ COPY命令匯入失敗: {e}")
            return False

    def _import_using_batch_optimized(self, converted_data):
        """使用批量插入優化匯入"""
        try:
            logger.info("⚡ 使用批量插入進行優化匯入...")
            
            with shared.get_conn_cur_from_pool_b(as_dict=False) as (pg_conn, pg_cursor):
                # 性能優化設定
                pg_cursor.execute("SET synchronous_commit = OFF")
                pg_cursor.execute("SET work_mem = '256MB'")
                
                # 準備SQL和資料
                insert_sql = """
                    INSERT INTO stock_prices (
                        trade_datetime, open_price, high_price, low_price,
                        close_price, price_change, percentage_change, volume
                    ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                    ON CONFLICT (trade_datetime) DO NOTHING
                """
                
                values_list = []
                for data in converted_data:
                    values_list.append((
                        data['trade_datetime'],
                        data['open_price'],
                        data['high_price'],
                        data['low_price'],
                        data['close_price'],
                        data['price_change'],
                        data['percentage_change'],
                        data['volume']
                    ))
                
                # 執行批量插入
                pg_cursor.executemany(insert_sql, values_list)
                pg_conn.commit()
                
                # 恢復設定
                pg_cursor.execute("SET synchronous_commit = ON")
                
            logger.info("✅ 批量插入完成")
            return True
            
        except Exception as e:
            logger.error(f"❌ 批量插入失敗: {e}")
            return False

    def _import_using_executemany_optimized(self, converted_data):
        """使用execute_values進行優化匯入"""
        try:
            from psycopg2.extras import execute_values
            logger.info("⚡ 使用execute_values進行優化匯入...")
            
            with shared.get_conn_cur_from_pool_b(as_dict=False) as (pg_conn, pg_cursor):
                # 性能優化設定
                pg_cursor.execute("SET synchronous_commit = OFF")
                
                values_list = []
                for data in converted_data:
                    values_list.append((
                        data['trade_datetime'],
                        data['open_price'],
                        data['high_price'],
                        data['low_price'],
                        data['close_price'],
                        data['price_change'],
                        data['percentage_change'],
                        data['volume']
                    ))
                
                # 使用execute_values進行高效插入
                execute_values(
                    pg_cursor,
                    """
                    INSERT INTO stock_prices (
                        trade_datetime, open_price, high_price, low_price,
                        close_price, price_change, percentage_change, volume
                    ) VALUES %s
                    ON CONFLICT (trade_datetime) DO NOTHING
                    """,
                    values_list,
                    page_size=1000
                )
                
                pg_conn.commit()
                pg_cursor.execute("SET synchronous_commit = ON")
                
            logger.info("✅ execute_values匯入完成")
            return True
            
        except Exception as e:
            logger.error(f"❌ execute_values匯入失敗: {e}")
            return False

    def benchmark_import_methods(self, symbol='MTX00', kline_type='MINUTE'):
        """測試不同匯入方法的性能"""
        logger.info("🏁 開始性能測試...")
        
        methods = ['copy', 'executemany', 'batch']
        results = {}
        
        for method in methods:
            logger.info(f"🧪 測試方法: {method}")
            start_time = time.time()
            
            success = self.import_kline_to_postgres_fast(symbol, kline_type, method)
            
            elapsed_time = time.time() - start_time
            results[method] = {
                'success': success,
                'time': elapsed_time
            }
            
            logger.info(f"📊 {method} 方法: {'成功' if success else '失敗'} (耗時: {elapsed_time:.2f}秒)")
        
        # 顯示結果
        logger.info("🏆 性能測試結果:")
        for method, result in results.items():
            if result['success']:
                logger.info(f"  {method}: {result['time']:.2f}秒")
        
        return results
