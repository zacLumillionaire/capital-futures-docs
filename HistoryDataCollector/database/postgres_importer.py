#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
PostgreSQL匯入器 - 將SQLite的K線資料匯入到PostgreSQL的stock_price表
基於您現有的資料庫連接方式
"""

import os
import sys
import logging
import sqlite3
from datetime import datetime
from decimal import Decimal

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
    print("請確認app_setup.py和shared.py在正確的路徑中")

from history_config import DATABASE_PATH

logger = logging.getLogger(__name__)

class PostgreSQLImporter:
    """PostgreSQL匯入器"""

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

    def check_sqlite_data(self):
        """檢查SQLite資料庫中的K線資料"""
        try:
            if not os.path.exists(self.sqlite_db_path):
                logger.error(f"❌ SQLite資料庫檔案不存在: {self.sqlite_db_path}")
                return None

            conn = sqlite3.connect(self.sqlite_db_path)
            conn.row_factory = sqlite3.Row
            
            # 統計K線資料
            cursor = conn.execute("""
                SELECT 
                    symbol,
                    kline_type,
                    COUNT(*) as count,
                    MIN(trade_date || ' ' || COALESCE(trade_time, '00:00:00')) as min_datetime,
                    MAX(trade_date || ' ' || COALESCE(trade_time, '00:00:00')) as max_datetime
                FROM kline_data 
                GROUP BY symbol, kline_type
                ORDER BY symbol, kline_type
            """)
            
            results = cursor.fetchall()
            conn.close()
            
            if not results:
                logger.warning("⚠️ SQLite資料庫中沒有K線資料")
                return None
            
            logger.info("📊 SQLite K線資料統計:")
            for row in results:
                logger.info(f"  {row['symbol']} {row['kline_type']}: {row['count']} 筆")
                logger.info(f"    時間範圍: {row['min_datetime']} ~ {row['max_datetime']}")
            
            return results
            
        except Exception as e:
            logger.error(f"❌ 檢查SQLite資料時發生錯誤: {e}")
            return None

    def convert_kline_to_stock_price_format(self, kline_data, exclude_anomalies=True):
        """
        將K線資料轉換為stock_price表格式

        Args:
            kline_data: K線資料字典
            exclude_anomalies: 是否排除異常資料 (預設: True)
        """
        try:
            # 解析日期時間
            # 根據實際資料格式，trade_date包含完整的日期時間（如 "2025/06/05 08:46"）
            # trade_time 是 None
            date_str = str(kline_data['trade_date']).strip()  # "2025/06/05 08:46"

            # 添加調試資訊（只在前幾筆資料時顯示）
            if hasattr(self, '_debug_count'):
                self._debug_count += 1
            else:
                self._debug_count = 1

            if self._debug_count <= 3:
                logger.info(f"🔍 轉換第{self._debug_count}筆資料: trade_date='{date_str}', trade_time='{kline_data.get('trade_time')}'")

            # 直接解析日期時間字串
            # 預期格式：YYYY/MM/DD HH:MM
            try:
                # 嘗試解析完整的日期時間格式
                trade_datetime = datetime.strptime(date_str, '%Y/%m/%d %H:%M')
            except ValueError:
                # 如果解析失敗，嘗試其他格式
                try:
                    # 嘗試只有日期的格式
                    trade_datetime = datetime.strptime(date_str, '%Y/%m/%d')
                    # 設為收盤時間
                    trade_datetime = trade_datetime.replace(hour=13, minute=45, second=0)
                except ValueError:
                    # 如果還是失敗，記錄錯誤並返回None
                    logger.error(f"❌ 無法解析日期格式: '{date_str}'")
                    return None

            # 計算價格變化（這裡簡化處理，實際應該與前一筆比較）
            price_change = Decimal('0.00')  # 暫時設為0，可以後續優化

            # 轉換價格資料
            open_price = Decimal(str(kline_data['open_price']))
            high_price = Decimal(str(kline_data['high_price']))
            low_price = Decimal(str(kline_data['low_price']))
            close_price = Decimal(str(kline_data['close_price']))
            volume = kline_data['volume'] or 0

            # 資料驗證和異常檢測
            anomaly_detected = False

            # 檢查所有價格是否相同
            if open_price == high_price == low_price == close_price:
                logger.warning(f"⚠️ 發現異常資料：所有價格都相同 {open_price} at {trade_datetime}")
                anomaly_detected = True

            # 檢查成交量是否為0
            if volume == 0:
                logger.warning(f"⚠️ 發現異常資料：成交量為0 at {trade_datetime}")
                anomaly_detected = True

            # 價格合理性檢查（這是嚴重錯誤，必須排除）
            if high_price < max(open_price, close_price) or low_price > min(open_price, close_price):
                logger.error(f"❌ 價格邏輯錯誤 at {trade_datetime}: O:{open_price} H:{high_price} L:{low_price} C:{close_price}")
                return None

            # 根據設定決定是否排除異常資料
            if exclude_anomalies and anomaly_detected:
                logger.info(f"🚫 排除異常資料 at {trade_datetime}")
                return None

            converted_data = {
                'trade_datetime': trade_datetime,
                'open_price': open_price,
                'high_price': high_price,
                'low_price': low_price,
                'close_price': close_price,
                'price_change': price_change,
                'percentage_change': Decimal('0.0000'),  # 忽略此欄位
                'volume': volume
            }

            # 列印前10行轉換後的資料到console
            if self._debug_count <= 10:
                print(f"\n=== PostgreSQL匯入 - 第 {self._debug_count} 筆轉換後的資料 ===")
                print(f"原始K線資料:")
                print(f"  商品代碼: {kline_data['symbol']}")
                print(f"  K線類型: {kline_data['kline_type']}")
                print(f"  交易日期: {kline_data['trade_date']}")
                print(f"  交易時間: {kline_data['trade_time']}")
                print(f"  開盤價: {kline_data['open_price']}")
                print(f"  最高價: {kline_data['high_price']}")
                print(f"  最低價: {kline_data['low_price']}")
                print(f"  收盤價: {kline_data['close_price']}")
                print(f"  成交量: {kline_data['volume']}")
                print(f"轉換為PostgreSQL格式:")
                print(f"  交易時間: {converted_data['trade_datetime']}")
                print(f"  開盤價: {converted_data['open_price']}")
                print(f"  最高價: {converted_data['high_price']}")
                print(f"  最低價: {converted_data['low_price']}")
                print(f"  收盤價: {converted_data['close_price']}")
                print(f"  價格變化: {converted_data['price_change']}")
                print(f"  百分比變化: {converted_data['percentage_change']}")
                print(f"  成交量: {converted_data['volume']}")
                print("=" * 60)

            return converted_data

        except Exception as e:
            logger.error(f"❌ 轉換資料格式時發生錯誤: {e}")
            logger.error(f"   原始資料: {kline_data}")
            logger.error(f"   日期字串: '{date_str}'")
            return None

    def import_kline_to_postgres(self, symbol='MTX00', kline_type='MINUTE', batch_size=5000, use_copy=False, optimize_performance=True, exclude_anomalies=True):
        """匯入K線資料到PostgreSQL"""
        if not self.postgres_initialized:
            logger.error("❌ PostgreSQL未初始化，無法匯入")
            return False

        # 如果使用COPY方式（超高速）
        if use_copy:
            return self._import_using_copy(symbol, kline_type)

        try:
            import time
            total_start_time = time.time()

            logger.info(f"🚀 開始匯入 {symbol} {kline_type} K線資料到PostgreSQL...")
            logger.info(f"⚡ 性能優化模式: {'開啟' if optimize_performance else '關閉'}")
            logger.info(f"📦 批次大小: {batch_size}")

            # 連接SQLite讀取資料
            sqlite_conn = sqlite3.connect(self.sqlite_db_path)
            sqlite_conn.row_factory = sqlite3.Row

            # 查詢K線資料
            query_sql = """
                SELECT * FROM kline_data
                WHERE symbol = ? AND kline_type = ?
                ORDER BY trade_date, trade_time
            """
            logger.info(f"🔍 執行SQLite查詢: {query_sql.strip()}")
            logger.info(f"🔍 查詢參數: symbol='{symbol}', kline_type='{kline_type}'")

            sqlite_cursor = sqlite_conn.execute(query_sql, (symbol, kline_type))

            # 檢查查詢結果
            all_rows = sqlite_cursor.fetchall()
            logger.info(f"📊 從SQLite查詢到 {len(all_rows)} 筆 {symbol} {kline_type} 資料")

            # 如果沒有資料，檢查資料庫中實際有什麼
            if len(all_rows) == 0:
                logger.warning(f"⚠️ 沒有找到 {symbol} {kline_type} 資料，檢查資料庫中的實際資料...")
                check_cursor = sqlite_conn.execute("""
                    SELECT symbol, kline_type, COUNT(*) as count
                    FROM kline_data
                    GROUP BY symbol, kline_type
                """)
                existing_data = check_cursor.fetchall()
                logger.info("📊 資料庫中現有的資料:")
                for row in existing_data:
                    logger.info(f"  - {row['symbol']} {row['kline_type']}: {row['count']} 筆")
                return False
            
            # 使用您的PostgreSQL連接方式
            with shared.get_conn_cur_from_pool_b(as_dict=False) as (pg_conn, pg_cursor):

                # 性能優化設定
                if optimize_performance:
                    logger.info("⚡ 啟用性能優化設定...")
                    try:
                        # 暫時關閉同步提交以提升性能
                        pg_cursor.execute("SET synchronous_commit = OFF")
                        logger.info("✅ 已關閉同步提交")

                        # 增加工作記憶體
                        pg_cursor.execute("SET work_mem = '256MB'")
                        logger.info("✅ 已增加工作記憶體")

                    except Exception as e:
                        logger.warning(f"⚠️ 部分性能設定失敗 (可忽略): {e}")

                # 檢查stock_prices表是否存在
                pg_cursor.execute("""
                    SELECT EXISTS (
                        SELECT FROM information_schema.tables
                        WHERE table_name = 'stock_prices'
                    )
                """)

                if not pg_cursor.fetchone()[0]:
                    logger.error("❌ PostgreSQL中找不到stock_prices表")
                    return False
                
                # 優化: 預先轉換所有資料
                logger.info("🔄 預先轉換所有資料...")
                conversion_start = time.time()
                converted_data = []
                conversion_errors = 0

                for row in all_rows:
                    stock_price_data = self.convert_kline_to_stock_price_format(dict(row), exclude_anomalies)
                    if stock_price_data is None:
                        conversion_errors += 1
                        continue
                    converted_data.append(stock_price_data)

                conversion_time = time.time() - conversion_start
                logger.info(f"✅ 資料轉換完成 (耗時: {conversion_time:.2f}秒)")
                logger.info(f"📊 成功轉換: {len(converted_data)} 筆，排除異常/錯誤: {conversion_errors} 筆")

                if exclude_anomalies and conversion_errors > 0:
                    logger.info(f"🚫 異常資料排除設定: {'開啟' if exclude_anomalies else '關閉'}")
                    logger.info(f"   排除的資料包含：所有價格相同、成交量為0、價格邏輯錯誤等")

                if len(converted_data) == 0:
                    logger.warning("⚠️ 沒有有效資料可匯入")
                    return False

                # 批量處理資料
                total_inserted = 0
                batch_count = 0

                # 分批處理
                for i in range(0, len(converted_data), batch_size):
                    batch_data = converted_data[i:i + batch_size]
                    batch_count += 1

                    batch_start = time.time()
                    inserted_count = self._insert_batch_to_postgres(pg_cursor, batch_data)
                    batch_time = time.time() - batch_start

                    total_inserted += inserted_count

                    # 每個批次提交
                    pg_conn.commit()

                    # 減少日誌輸出頻率
                    if batch_count % 5 == 0 or batch_count == 1:
                        logger.info(f"📦 批次 {batch_count}: {inserted_count}/{len(batch_data)} 筆 (耗時: {batch_time:.2f}秒)")

                    # 每10個批次顯示進度
                    if batch_count % 10 == 0:
                        progress = (i + len(batch_data)) / len(converted_data) * 100
                        logger.info(f"📊 進度: {progress:.1f}% ({i + len(batch_data)}/{len(converted_data)})")

                # 恢復正常設定
                if optimize_performance:
                    try:
                        pg_cursor.execute("SET synchronous_commit = ON")
                        logger.info("✅ 已恢復同步提交設定")
                    except:
                        pass

                total_time = time.time() - total_start_time
                logger.info(f"✅ 匯入完成！")
                logger.info(f"📊 統計結果:")
                logger.info(f"  - 總處理筆數: {len(all_rows)}")
                logger.info(f"  - 成功轉換: {len(converted_data)}")
                logger.info(f"  - 成功插入: {total_inserted}")
                logger.info(f"  - 轉換錯誤: {conversion_errors}")
                logger.info(f"  - 總耗時: {total_time:.2f}秒")
                logger.info(f"  - 平均速度: {total_inserted/total_time:.0f} 筆/秒")
                
            sqlite_conn.close()
            return True
            
        except Exception as e:
            logger.error(f"❌ 匯入過程中發生錯誤: {e}", exc_info=True)
            return False

    def _insert_batch_to_postgres(self, cursor, batch_data):
        """批量插入資料到PostgreSQL - 優化版本"""
        if not batch_data:
            return 0

        import time
        start_time = time.time()

        try:
            # 性能優化: 減少日誌輸出
            if len(batch_data) > 100:
                logger.info(f"🔍 準備插入 {len(batch_data)} 筆資料到PostgreSQL")

            # 嘗試使用 execute_values (更高效)
            try:
                from psycopg2.extras import execute_values

                # 使用 execute_values 進行高效批量插入
                insert_sql = """
                    INSERT INTO stock_prices (
                        trade_datetime, open_price, high_price, low_price,
                        close_price, price_change, percentage_change, volume
                    ) VALUES %s
                    ON CONFLICT (trade_datetime) DO NOTHING
                """

                values_list = []
                for data in batch_data:
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

                # 使用 execute_values 進行高效插入
                execute_values(cursor, insert_sql, values_list, page_size=1000)
                inserted_count = len(batch_data)  # execute_values 不返回 rowcount

                total_time = time.time() - start_time
                if len(batch_data) > 100:
                    logger.info(f"✅ execute_values 插入完成: {inserted_count} 筆 (耗時: {total_time:.2f}秒)")

                return inserted_count

            except ImportError:
                # 如果沒有 execute_values，使用標準方法
                logger.warning("⚠️ execute_values 不可用，使用標準 executemany")

                # 標準批量插入方法
                insert_sql = """
                    INSERT INTO stock_prices (
                        trade_datetime, open_price, high_price, low_price,
                        close_price, price_change, percentage_change, volume
                    ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                    ON CONFLICT (trade_datetime) DO NOTHING
                """

            logger.info(f"🔍 使用優化的主鍵衝突處理SQL")

            # 準備資料（只需要8個參數）
            values_list = []
            for i, data in enumerate(batch_data):
                values = (
                    data['trade_datetime'],
                    data['open_price'],
                    data['high_price'],
                    data['low_price'],
                    data['close_price'],
                    data['price_change'],
                    data['percentage_change'],
                    data['volume']
                )
                values_list.append(values)

                # 顯示前3筆資料的詳細資訊
                if i < 3:
                    logger.info(f"🔍 第{i+1}筆資料: {data['trade_datetime']} OHLC:{data['open_price']}/{data['high_price']}/{data['low_price']}/{data['close_price']} V:{data['volume']}")

            logger.info(f"🔍 準備執行批量插入，共 {len(values_list)} 筆資料")

            try:
                # 使用主鍵約束的ON CONFLICT處理
                exec_start = time.time()
                logger.info("🔍 開始執行 cursor.executemany()...")
                cursor.executemany(insert_sql, values_list)
                exec_time = time.time() - exec_start
                logger.info(f"🔍 executemany() 執行完成 (耗時: {exec_time:.2f}秒)")

                inserted_count = cursor.rowcount
                logger.info(f"🔍 cursor.rowcount = {inserted_count}")

                # 檢查是否真的插入了資料
                cursor.execute("SELECT COUNT(*) FROM stock_prices WHERE trade_datetime >= %s", (values_list[0][0],))
                actual_count = cursor.fetchone()[0]
                logger.info(f"🔍 資料庫中實際筆數檢查: {actual_count}")

                total_time = time.time() - start_time
                logger.info(f"🔍 PostgreSQL回報：成功插入 {inserted_count} 筆資料")
                logger.info(f"⏱️ 批次總耗時: {total_time:.2f}秒 (平均: {total_time/len(batch_data)*1000:.1f}ms/筆)")

                return inserted_count

            except Exception as e:
                logger.error(f"❌ 執行批量插入時發生錯誤: {e}")
                logger.error(f"❌ 錯誤類型: {type(e).__name__}")
                import traceback
                logger.error(f"❌ 詳細錯誤: {traceback.format_exc()}")
                return 0
            
        except Exception as e:
            logger.error(f"❌ 批量插入時發生錯誤: {e}")
            return 0

    def check_postgres_data(self):
        """檢查PostgreSQL中的stock_price資料"""
        if not self.postgres_initialized:
            logger.error("❌ PostgreSQL未初始化")
            return False
        
        try:
            with shared.get_conn_cur_from_pool_b(as_dict=True) as (conn, cursor):
                # 統計資料
                cursor.execute("""
                    SELECT
                        COUNT(*) as total_count,
                        MIN(trade_datetime) as min_datetime,
                        MAX(trade_datetime) as max_datetime,
                        COUNT(DISTINCT trade_datetime::date) as trading_days
                    FROM stock_prices
                """)
                
                result = cursor.fetchone()
                
                if result['total_count'] > 0:
                    logger.info("📊 PostgreSQL stock_prices表統計:")
                    logger.info(f"  - 總筆數: {result['total_count']:,}")
                    logger.info(f"  - 交易日數: {result['trading_days']}")
                    logger.info(f"  - 時間範圍: {result['min_datetime']} ~ {result['max_datetime']}")

                    # 顯示最新幾筆資料
                    cursor.execute("""
                        SELECT trade_datetime, open_price, high_price, low_price, close_price, volume
                        FROM stock_prices
                        ORDER BY trade_datetime DESC
                        LIMIT 5
                    """)
                    
                    recent_data = cursor.fetchall()
                    logger.info("📈 最新5筆資料:")
                    for row in recent_data:
                        logger.info(f"  {row['trade_datetime']} O:{row['open_price']} H:{row['high_price']} L:{row['low_price']} C:{row['close_price']} V:{row['volume']}")
                else:
                    logger.warning("⚠️ PostgreSQL stock_prices表中沒有資料")
                
                return True
                
        except Exception as e:
            logger.error(f"❌ 檢查PostgreSQL資料時發生錯誤: {e}")
            return False

    def _import_using_copy(self, symbol, kline_type):
        """使用COPY命令超高速匯入（適合大量資料）"""
        import tempfile
        import csv
        import time

        try:
            logger.info(f"🚀 使用COPY方式匯入 {symbol} {kline_type} 資料...")
            start_time = time.time()

            # 連接SQLite讀取資料
            sqlite_conn = sqlite3.connect(self.sqlite_db_path)
            sqlite_conn.row_factory = sqlite3.Row

            # 查詢K線資料
            sqlite_cursor = sqlite_conn.execute("""
                SELECT * FROM kline_data
                WHERE symbol = ? AND kline_type = ?
                ORDER BY trade_date, trade_time
            """, (symbol, kline_type))

            all_rows = sqlite_cursor.fetchall()
            logger.info(f"📊 查詢到 {len(all_rows)} 筆資料")

            if len(all_rows) == 0:
                logger.warning("⚠️ 沒有資料可匯入")
                return False

            # 創建臨時CSV檔案
            with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.csv', encoding='utf-8') as temp_file:
                csv_writer = csv.writer(temp_file)

                converted_count = 0
                for row in all_rows:
                    # 轉換資料格式
                    stock_price_data = self.convert_kline_to_stock_price_format(dict(row))
                    if stock_price_data:
                        csv_writer.writerow([
                            stock_price_data['trade_datetime'],
                            stock_price_data['open_price'],
                            stock_price_data['high_price'],
                            stock_price_data['low_price'],
                            stock_price_data['close_price'],
                            stock_price_data['price_change'],
                            stock_price_data['percentage_change'],
                            stock_price_data['volume']
                        ])
                        converted_count += 1

                temp_file_path = temp_file.name

            logger.info(f"📝 已轉換 {converted_count} 筆資料到臨時檔案: {temp_file_path}")

            # 使用COPY命令匯入
            with shared.get_conn_cur_from_pool_b(as_dict=False) as (pg_conn, pg_cursor):
                copy_start = time.time()

                with open(temp_file_path, 'r', encoding='utf-8') as f:
                    pg_cursor.copy_expert("""
                        COPY stock_prices (
                            trade_datetime, open_price, high_price, low_price,
                            close_price, price_change, percentage_change, volume
                        ) FROM STDIN WITH CSV
                    """, f)

                pg_conn.commit()
                copy_time = time.time() - copy_start

                logger.info(f"⚡ COPY命令執行完成 (耗時: {copy_time:.2f}秒)")

                # 檢查插入結果
                pg_cursor.execute("SELECT COUNT(*) FROM stock_prices")
                total_count = pg_cursor.fetchone()[0]

                total_time = time.time() - start_time
                logger.info(f"✅ COPY匯入完成！")
                logger.info(f"📊 總耗時: {total_time:.2f}秒")
                logger.info(f"📊 平均速度: {converted_count/total_time:.0f} 筆/秒")
                logger.info(f"📊 資料庫總筆數: {total_count:,}")

            # 清理臨時檔案
            import os
            os.unlink(temp_file_path)
            sqlite_conn.close()

            return True

        except Exception as e:
            logger.error(f"❌ COPY匯入失敗: {e}")
            import traceback
            logger.error(f"❌ 詳細錯誤: {traceback.format_exc()}")
            return False

    def convert_tick_to_postgres_format(self, tick_data):
        """將逐筆資料轉換為PostgreSQL格式"""
        try:
            # 解析日期時間
            date_str = str(tick_data['trade_date']).strip()  # "20241201"
            time_str = str(tick_data['trade_time']).strip().zfill(6)  # "090000"

            # 轉換為 datetime
            trade_datetime = datetime.strptime(f"{date_str} {time_str}", '%Y%m%d %H%M%S')

            # 處理毫秒
            if tick_data.get('trade_time_ms'):
                microseconds = min(tick_data['trade_time_ms'] * 1000, 999999)
                trade_datetime = trade_datetime.replace(microsecond=microseconds)

            # 轉換價格為Decimal
            bid_price = None
            ask_price = None
            close_price = Decimal(str(tick_data['close_price'])).quantize(Decimal('0.01'))

            if tick_data.get('bid_price') is not None:
                bid_price = Decimal(str(tick_data['bid_price'])).quantize(Decimal('0.01'))
            if tick_data.get('ask_price') is not None:
                ask_price = Decimal(str(tick_data['ask_price'])).quantize(Decimal('0.01'))

            converted_data = {
                'trade_datetime': trade_datetime,
                'symbol': tick_data['symbol'],
                'bid_price': bid_price,
                'ask_price': ask_price,
                'close_price': close_price,
                'volume': tick_data['volume'],
                'trade_time_ms': tick_data.get('trade_time_ms', 0),
                'market_no': tick_data.get('market_no', 0),
                'simulate_flag': tick_data.get('simulate_flag', 0)
            }

            # 列印前10行轉換後的資料到console
            if hasattr(self, '_tick_debug_count'):
                self._tick_debug_count += 1
            else:
                self._tick_debug_count = 1

            if self._tick_debug_count <= 10:
                print(f"\n=== Tick PostgreSQL匯入 - 第 {self._tick_debug_count} 筆轉換後的資料 ===")
                print(f"原始逐筆資料:")
                print(f"  商品代碼: {tick_data['symbol']}")
                print(f"  交易日期: {tick_data['trade_date']}")
                print(f"  交易時間: {tick_data['trade_time']}")
                print(f"  買價: {tick_data.get('bid_price')}")
                print(f"  賣價: {tick_data.get('ask_price')}")
                print(f"  成交價: {tick_data['close_price']}")
                print(f"  成交量: {tick_data['volume']}")
                print(f"轉換為PostgreSQL格式:")
                print(f"  交易時間: {converted_data['trade_datetime']}")
                print(f"  商品代碼: {converted_data['symbol']}")
                print(f"  買價: {converted_data['bid_price']}")
                print(f"  賣價: {converted_data['ask_price']}")
                print(f"  成交價: {converted_data['close_price']}")
                print(f"  成交量: {converted_data['volume']}")
                print(f"  毫秒: {converted_data['trade_time_ms']}")
                print("=" * 60)

            return converted_data

        except Exception as e:
            logger.error(f"❌ 轉換逐筆資料格式時發生錯誤: {e}")
            logger.error(f"   原始資料: {tick_data}")
            return None

    def _insert_tick_batch_to_postgres(self, cursor, batch_data, optimize_performance=True):
        """批量插入逐筆資料到PostgreSQL"""
        if not batch_data:
            return 0

        import time
        start_time = time.time()

        try:
            # 嘗試使用 execute_values (更高效)
            try:
                from psycopg2.extras import execute_values

                insert_sql = """
                    INSERT INTO tick_prices (
                        trade_datetime, symbol, bid_price, ask_price, close_price,
                        volume, trade_time_ms, market_no, simulate_flag
                    ) VALUES %s
                    ON CONFLICT (trade_datetime, symbol) DO NOTHING
                """

                values_list = []
                for data in batch_data:
                    values_list.append((
                        data['trade_datetime'],
                        data['symbol'],
                        data['bid_price'],
                        data['ask_price'],
                        data['close_price'],
                        data['volume'],
                        data['trade_time_ms'],
                        data['market_no'],
                        data['simulate_flag']
                    ))

                # 使用 execute_values 進行高效插入
                execute_values(cursor, insert_sql, values_list, page_size=1000)
                inserted_count = len(batch_data)

                total_time = time.time() - start_time
                if len(batch_data) > 100:
                    logger.info(f"✅ 逐筆 execute_values 插入完成: {inserted_count} 筆 (耗時: {total_time:.2f}秒)")

                return inserted_count

            except ImportError:
                logger.warning("⚠️ execute_values 不可用，使用標準 executemany")

                # 標準批量插入方法
                insert_sql = """
                    INSERT INTO tick_prices (
                        trade_datetime, symbol, bid_price, ask_price, close_price,
                        volume, trade_time_ms, market_no, simulate_flag
                    ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
                    ON CONFLICT (trade_datetime, symbol) DO NOTHING
                """

                values_list = []
                for data in batch_data:
                    values_list.append((
                        data['trade_datetime'],
                        data['symbol'],
                        data['bid_price'],
                        data['ask_price'],
                        data['close_price'],
                        data['volume'],
                        data['trade_time_ms'],
                        data['market_no'],
                        data['simulate_flag']
                    ))

                cursor.executemany(insert_sql, values_list)
                inserted_count = cursor.rowcount

                total_time = time.time() - start_time
                logger.info(f"✅ 逐筆標準插入完成: {inserted_count} 筆 (耗時: {total_time:.2f}秒)")

                return inserted_count

        except Exception as e:
            logger.error(f"❌ 批量插入逐筆資料失敗: {e}")
            return 0

    def import_tick_to_postgres(self, symbol='MTX00', batch_size=5000, optimize_performance=True):
        """匯入逐筆資料到PostgreSQL"""
        if not self.postgres_initialized:
            logger.error("❌ PostgreSQL未初始化，無法匯入")
            return False

        try:
            import time
            total_start_time = time.time()

            logger.info(f"🚀 開始匯入 {symbol} 逐筆資料到PostgreSQL...")
            logger.info(f"⚡ 性能優化模式: {'開啟' if optimize_performance else '關閉'}")
            logger.info(f"📦 批次大小: {batch_size}")

            # 連接SQLite讀取資料
            sqlite_conn = sqlite3.connect(self.sqlite_db_path)
            sqlite_conn.row_factory = sqlite3.Row

            # 查詢逐筆資料
            query_sql = """
                SELECT * FROM tick_data
                WHERE symbol = ?
                ORDER BY trade_date, trade_time
            """
            logger.info(f"🔍 執行SQLite查詢: {query_sql.strip()}")
            logger.info(f"🔍 查詢參數: symbol='{symbol}'")

            sqlite_cursor = sqlite_conn.execute(query_sql, (symbol,))
            all_rows = sqlite_cursor.fetchall()
            logger.info(f"📊 從SQLite查詢到 {len(all_rows)} 筆 {symbol} 逐筆資料")

            if len(all_rows) == 0:
                logger.warning(f"⚠️ 沒有找到 {symbol} 逐筆資料")
                sqlite_conn.close()
                return False

            # 使用PostgreSQL連接
            with shared.get_conn_cur_from_pool_b(as_dict=False) as (pg_conn, pg_cursor):

                # 性能優化設定
                if optimize_performance:
                    logger.info("⚡ 啟用性能優化設定...")
                    try:
                        pg_cursor.execute("SET synchronous_commit = OFF")
                        pg_cursor.execute("SET work_mem = '256MB'")
                        logger.info("✅ 性能優化設定完成")
                    except Exception as e:
                        logger.warning(f"⚠️ 部分性能設定失敗 (可忽略): {e}")

                # 檢查tick_prices表是否存在，如果不存在則創建
                pg_cursor.execute("""
                    CREATE TABLE IF NOT EXISTS tick_prices (
                        trade_datetime timestamp without time zone NOT NULL,
                        symbol varchar(20) NOT NULL,
                        bid_price numeric(10,2),
                        ask_price numeric(10,2),
                        close_price numeric(10,2) NOT NULL,
                        volume integer NOT NULL,
                        trade_time_ms integer,
                        market_no integer,
                        simulate_flag integer DEFAULT 0,
                        CONSTRAINT pk_tick_prices PRIMARY KEY (trade_datetime, symbol)
                    )
                """)
                logger.info("✅ 確認tick_prices表存在")

                # 預先轉換所有資料
                logger.info("🔄 預先轉換所有逐筆資料...")
                conversion_start = time.time()
                converted_data = []
                conversion_errors = 0

                for row in all_rows:
                    tick_postgres_data = self.convert_tick_to_postgres_format(dict(row))
                    if tick_postgres_data is None:
                        conversion_errors += 1
                        continue
                    converted_data.append(tick_postgres_data)

                conversion_time = time.time() - conversion_start
                logger.info(f"✅ 逐筆資料轉換完成 (耗時: {conversion_time:.2f}秒)")
                logger.info(f"📊 成功轉換: {len(converted_data)} 筆，錯誤: {conversion_errors} 筆")

                if len(converted_data) == 0:
                    logger.warning("⚠️ 沒有有效的逐筆資料可匯入")
                    sqlite_conn.close()
                    return False

                # 批量處理資料
                total_inserted = 0
                batch_count = 0

                # 分批處理
                for i in range(0, len(converted_data), batch_size):
                    batch_data = converted_data[i:i + batch_size]
                    batch_count += 1

                    batch_start = time.time()
                    inserted_count = self._insert_tick_batch_to_postgres(pg_cursor, batch_data, optimize_performance)
                    batch_time = time.time() - batch_start

                    total_inserted += inserted_count

                    # 每個批次提交
                    pg_conn.commit()

                    # 減少日誌輸出頻率
                    if batch_count % 5 == 0 or batch_count == 1:
                        logger.info(f"📦 逐筆批次 {batch_count}: {inserted_count}/{len(batch_data)} 筆 (耗時: {batch_time:.2f}秒)")

                # 恢復正常設定
                if optimize_performance:
                    try:
                        pg_cursor.execute("SET synchronous_commit = ON")
                        logger.info("✅ 已恢復同步提交設定")
                    except:
                        pass

                total_time = time.time() - total_start_time
                logger.info(f"✅ 逐筆資料匯入完成！")
                logger.info(f"📊 統計結果:")
                logger.info(f"  - 總處理筆數: {len(all_rows)}")
                logger.info(f"  - 成功轉換: {len(converted_data)}")
                logger.info(f"  - 成功插入: {total_inserted}")
                logger.info(f"  - 轉換錯誤: {conversion_errors}")
                logger.info(f"  - 總耗時: {total_time:.2f}秒")
                logger.info(f"  - 平均速度: {total_inserted/total_time:.0f} 筆/秒")

            sqlite_conn.close()
            return True

        except Exception as e:
            logger.error(f"❌ 匯入逐筆資料過程中發生錯誤: {e}", exc_info=True)
            return False

    def convert_best5_to_postgres_format(self, best5_data):
        """將五檔資料轉換為PostgreSQL格式"""
        try:
            # 解析日期時間
            date_str = str(best5_data['trade_date']).strip()  # "20241201"
            time_str = str(best5_data['trade_time']).strip().zfill(6)  # "090000"

            # 轉換為 datetime
            trade_datetime = datetime.strptime(f"{date_str} {time_str}", '%Y%m%d %H%M%S')

            # 轉換價格為Decimal，處理None值
            def convert_price(price):
                if price is None or price == 0:
                    return None
                return Decimal(str(price)).quantize(Decimal('0.01'))

            converted_data = {
                'trade_datetime': trade_datetime,
                'symbol': best5_data['symbol'],

                # 五檔買價買量
                'bid_price_1': convert_price(best5_data.get('bid_price_1')),
                'bid_volume_1': best5_data.get('bid_volume_1', 0),
                'bid_price_2': convert_price(best5_data.get('bid_price_2')),
                'bid_volume_2': best5_data.get('bid_volume_2', 0),
                'bid_price_3': convert_price(best5_data.get('bid_price_3')),
                'bid_volume_3': best5_data.get('bid_volume_3', 0),
                'bid_price_4': convert_price(best5_data.get('bid_price_4')),
                'bid_volume_4': best5_data.get('bid_volume_4', 0),
                'bid_price_5': convert_price(best5_data.get('bid_price_5')),
                'bid_volume_5': best5_data.get('bid_volume_5', 0),

                # 五檔賣價賣量
                'ask_price_1': convert_price(best5_data.get('ask_price_1')),
                'ask_volume_1': best5_data.get('ask_volume_1', 0),
                'ask_price_2': convert_price(best5_data.get('ask_price_2')),
                'ask_volume_2': best5_data.get('ask_volume_2', 0),
                'ask_price_3': convert_price(best5_data.get('ask_price_3')),
                'ask_volume_3': best5_data.get('ask_volume_3', 0),
                'ask_price_4': convert_price(best5_data.get('ask_price_4')),
                'ask_volume_4': best5_data.get('ask_volume_4', 0),
                'ask_price_5': convert_price(best5_data.get('ask_price_5')),
                'ask_volume_5': best5_data.get('ask_volume_5', 0),

                # 延伸買賣
                'extend_bid': convert_price(best5_data.get('extend_bid')),
                'extend_bid_qty': best5_data.get('extend_bid_qty', 0),
                'extend_ask': convert_price(best5_data.get('extend_ask')),
                'extend_ask_qty': best5_data.get('extend_ask_qty', 0)
            }

            # 列印前10行轉換後的資料到console
            if hasattr(self, '_best5_debug_count'):
                self._best5_debug_count += 1
            else:
                self._best5_debug_count = 1

            if self._best5_debug_count <= 10:
                print(f"\n=== Best5 PostgreSQL匯入 - 第 {self._best5_debug_count} 筆轉換後的資料 ===")
                print(f"原始五檔資料:")
                print(f"  商品代碼: {best5_data['symbol']}")
                print(f"  交易日期: {best5_data['trade_date']}")
                print(f"  交易時間: {best5_data['trade_time']}")
                print(f"  買1: {best5_data.get('bid_price_1')} x {best5_data.get('bid_volume_1')}")
                print(f"  買2: {best5_data.get('bid_price_2')} x {best5_data.get('bid_volume_2')}")
                print(f"  賣1: {best5_data.get('ask_price_1')} x {best5_data.get('ask_volume_1')}")
                print(f"  賣2: {best5_data.get('ask_price_2')} x {best5_data.get('ask_volume_2')}")
                print(f"轉換為PostgreSQL格式:")
                print(f"  交易時間: {converted_data['trade_datetime']}")
                print(f"  商品代碼: {converted_data['symbol']}")
                print(f"  買1: {converted_data['bid_price_1']} x {converted_data['bid_volume_1']}")
                print(f"  買2: {converted_data['bid_price_2']} x {converted_data['bid_volume_2']}")
                print(f"  賣1: {converted_data['ask_price_1']} x {converted_data['ask_volume_1']}")
                print(f"  賣2: {converted_data['ask_price_2']} x {converted_data['ask_volume_2']}")
                print("=" * 60)

            return converted_data

        except Exception as e:
            logger.error(f"❌ 轉換五檔資料格式時發生錯誤: {e}")
            logger.error(f"   原始資料: {best5_data}")
            return None

    def _insert_best5_batch_to_postgres(self, cursor, batch_data, optimize_performance=True):
        """批量插入五檔資料到PostgreSQL"""
        if not batch_data:
            return 0

        import time
        start_time = time.time()

        try:
            # 嘗試使用 execute_values (更高效)
            try:
                from psycopg2.extras import execute_values

                insert_sql = """
                    INSERT INTO best5_prices (
                        trade_datetime, symbol,
                        bid_price_1, bid_volume_1, bid_price_2, bid_volume_2,
                        bid_price_3, bid_volume_3, bid_price_4, bid_volume_4,
                        bid_price_5, bid_volume_5,
                        ask_price_1, ask_volume_1, ask_price_2, ask_volume_2,
                        ask_price_3, ask_volume_3, ask_price_4, ask_volume_4,
                        ask_price_5, ask_volume_5,
                        extend_bid, extend_bid_qty, extend_ask, extend_ask_qty
                    ) VALUES %s
                    ON CONFLICT (trade_datetime, symbol) DO NOTHING
                """

                values_list = []
                for data in batch_data:
                    values_list.append((
                        data['trade_datetime'],
                        data['symbol'],
                        data['bid_price_1'], data['bid_volume_1'],
                        data['bid_price_2'], data['bid_volume_2'],
                        data['bid_price_3'], data['bid_volume_3'],
                        data['bid_price_4'], data['bid_volume_4'],
                        data['bid_price_5'], data['bid_volume_5'],
                        data['ask_price_1'], data['ask_volume_1'],
                        data['ask_price_2'], data['ask_volume_2'],
                        data['ask_price_3'], data['ask_volume_3'],
                        data['ask_price_4'], data['ask_volume_4'],
                        data['ask_price_5'], data['ask_volume_5'],
                        data['extend_bid'], data['extend_bid_qty'],
                        data['extend_ask'], data['extend_ask_qty']
                    ))

                # 使用 execute_values 進行高效插入
                execute_values(cursor, insert_sql, values_list, page_size=1000)
                inserted_count = len(batch_data)

                total_time = time.time() - start_time
                if len(batch_data) > 100:
                    logger.info(f"✅ 五檔 execute_values 插入完成: {inserted_count} 筆 (耗時: {total_time:.2f}秒)")

                return inserted_count

            except ImportError:
                logger.warning("⚠️ execute_values 不可用，使用標準 executemany")

                # 標準批量插入方法
                insert_sql = """
                    INSERT INTO best5_prices (
                        trade_datetime, symbol,
                        bid_price_1, bid_volume_1, bid_price_2, bid_volume_2,
                        bid_price_3, bid_volume_3, bid_price_4, bid_volume_4,
                        bid_price_5, bid_volume_5,
                        ask_price_1, ask_volume_1, ask_price_2, ask_volume_2,
                        ask_price_3, ask_volume_3, ask_price_4, ask_volume_4,
                        ask_price_5, ask_volume_5,
                        extend_bid, extend_bid_qty, extend_ask, extend_ask_qty
                    ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                    ON CONFLICT (trade_datetime, symbol) DO NOTHING
                """

                values_list = []
                for data in batch_data:
                    values_list.append((
                        data['trade_datetime'],
                        data['symbol'],
                        data['bid_price_1'], data['bid_volume_1'],
                        data['bid_price_2'], data['bid_volume_2'],
                        data['bid_price_3'], data['bid_volume_3'],
                        data['bid_price_4'], data['bid_volume_4'],
                        data['bid_price_5'], data['bid_volume_5'],
                        data['ask_price_1'], data['ask_volume_1'],
                        data['ask_price_2'], data['ask_volume_2'],
                        data['ask_price_3'], data['ask_volume_3'],
                        data['ask_price_4'], data['ask_volume_4'],
                        data['ask_price_5'], data['ask_volume_5'],
                        data['extend_bid'], data['extend_bid_qty'],
                        data['extend_ask'], data['extend_ask_qty']
                    ))

                cursor.executemany(insert_sql, values_list)
                inserted_count = cursor.rowcount

                total_time = time.time() - start_time
                logger.info(f"✅ 五檔標準插入完成: {inserted_count} 筆 (耗時: {total_time:.2f}秒)")

                return inserted_count

        except Exception as e:
            logger.error(f"❌ 批量插入五檔資料失敗: {e}")
            return 0

    def import_best5_to_postgres(self, symbol='MTX00', batch_size=5000, optimize_performance=True):
        """匯入五檔資料到PostgreSQL"""
        # 導入擴展功能
        from .postgres_importer_extensions import PostgreSQLImporterExtensions

        # 創建一個混合類別來使用擴展功能
        class MixedImporter(PostgreSQLImporterExtensions):
            def __init__(self, parent):
                self.postgres_initialized = parent.postgres_initialized
                self.sqlite_db_path = parent.sqlite_db_path
                self.convert_best5_to_postgres_format = parent.convert_best5_to_postgres_format
                self._insert_best5_batch_to_postgres = parent._insert_best5_batch_to_postgres

        mixed_importer = MixedImporter(self)
        return mixed_importer.import_best5_to_postgres(symbol, batch_size, optimize_performance)

    def import_all_data_to_postgres(self, symbol='MTX00', batch_size=5000, optimize_performance=True):
        """匯入所有類型資料到PostgreSQL"""
        # 導入擴展功能
        from .postgres_importer_extensions import PostgreSQLImporterExtensions

        # 創建一個混合類別來使用擴展功能
        class MixedImporter(PostgreSQLImporterExtensions):
            def __init__(self, parent):
                self.postgres_initialized = parent.postgres_initialized
                self.sqlite_db_path = parent.sqlite_db_path
                self.import_kline_to_postgres = parent.import_kline_to_postgres
                self.import_tick_to_postgres = parent.import_tick_to_postgres
                self.import_best5_to_postgres = parent.import_best5_to_postgres

        mixed_importer = MixedImporter(self)
        return mixed_importer.import_all_data_to_postgres(symbol, batch_size, optimize_performance)

    def get_postgres_data_statistics(self):
        """取得PostgreSQL資料統計"""
        # 導入擴展功能
        from .postgres_importer_extensions import PostgreSQLImporterExtensions

        # 創建一個混合類別來使用擴展功能
        class MixedImporter(PostgreSQLImporterExtensions):
            def __init__(self, parent):
                self.postgres_initialized = parent.postgres_initialized

        mixed_importer = MixedImporter(self)
        return mixed_importer.get_postgres_data_statistics()
