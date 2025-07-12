#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
PostgreSQL匯入器擴展
包含 Tick 和 Best5 資料的匯入方法
"""

import logging
import sqlite3
import time
from datetime import datetime
from decimal import Decimal

logger = logging.getLogger(__name__)

class PostgreSQLImporterExtensions:
    """PostgreSQL匯入器擴展類別"""
    
    def import_best5_to_postgres(self, symbol='MTX00', batch_size=5000, optimize_performance=True):
        """匯入五檔資料到PostgreSQL"""
        if not self.postgres_initialized:
            logger.error("❌ PostgreSQL未初始化，無法匯入")
            return False

        try:
            total_start_time = time.time()
            
            logger.info(f"🚀 開始匯入 {symbol} 五檔資料到PostgreSQL...")
            logger.info(f"⚡ 性能優化模式: {'開啟' if optimize_performance else '關閉'}")
            logger.info(f"📦 批次大小: {batch_size}")
            
            # 連接SQLite讀取資料
            sqlite_conn = sqlite3.connect(self.sqlite_db_path)
            sqlite_conn.row_factory = sqlite3.Row
            
            # 查詢五檔資料
            query_sql = """
                SELECT * FROM best5_data
                WHERE symbol = ?
                ORDER BY trade_date, trade_time
            """
            logger.info(f"🔍 執行SQLite查詢: {query_sql.strip()}")
            logger.info(f"🔍 查詢參數: symbol='{symbol}'")

            sqlite_cursor = sqlite_conn.execute(query_sql, (symbol,))
            all_rows = sqlite_cursor.fetchall()
            logger.info(f"📊 從SQLite查詢到 {len(all_rows)} 筆 {symbol} 五檔資料")

            if len(all_rows) == 0:
                logger.warning(f"⚠️ 沒有找到 {symbol} 五檔資料")
                sqlite_conn.close()
                return False

            # 使用PostgreSQL連接
            import shared
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
                
                # 檢查best5_prices表是否存在，如果不存在則創建
                pg_cursor.execute("""
                    CREATE TABLE IF NOT EXISTS best5_prices (
                        trade_datetime timestamp without time zone NOT NULL,
                        symbol varchar(20) NOT NULL,
                        
                        -- 五檔買價買量
                        bid_price_1 numeric(10,2), bid_volume_1 integer,
                        bid_price_2 numeric(10,2), bid_volume_2 integer,
                        bid_price_3 numeric(10,2), bid_volume_3 integer,
                        bid_price_4 numeric(10,2), bid_volume_4 integer,
                        bid_price_5 numeric(10,2), bid_volume_5 integer,
                        
                        -- 五檔賣價賣量
                        ask_price_1 numeric(10,2), ask_volume_1 integer,
                        ask_price_2 numeric(10,2), ask_volume_2 integer,
                        ask_price_3 numeric(10,2), ask_volume_3 integer,
                        ask_price_4 numeric(10,2), ask_volume_4 integer,
                        ask_price_5 numeric(10,2), ask_volume_5 integer,
                        
                        -- 延伸買賣
                        extend_bid numeric(10,2), extend_bid_qty integer,
                        extend_ask numeric(10,2), extend_ask_qty integer,
                        
                        CONSTRAINT pk_best5_prices PRIMARY KEY (trade_datetime, symbol)
                    )
                """)
                logger.info("✅ 確認best5_prices表存在")
                
                # 預先轉換所有資料
                logger.info("🔄 預先轉換所有五檔資料...")
                conversion_start = time.time()
                converted_data = []
                conversion_errors = 0
                
                for row in all_rows:
                    best5_postgres_data = self.convert_best5_to_postgres_format(dict(row))
                    if best5_postgres_data is None:
                        conversion_errors += 1
                        continue
                    converted_data.append(best5_postgres_data)
                
                conversion_time = time.time() - conversion_start
                logger.info(f"✅ 五檔資料轉換完成 (耗時: {conversion_time:.2f}秒)")
                logger.info(f"📊 成功轉換: {len(converted_data)} 筆，錯誤: {conversion_errors} 筆")
                
                if len(converted_data) == 0:
                    logger.warning("⚠️ 沒有有效的五檔資料可匯入")
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
                    inserted_count = self._insert_best5_batch_to_postgres(pg_cursor, batch_data, optimize_performance)
                    batch_time = time.time() - batch_start
                    
                    total_inserted += inserted_count
                    
                    # 每個批次提交
                    pg_conn.commit()
                    
                    # 減少日誌輸出頻率
                    if batch_count % 5 == 0 or batch_count == 1:
                        logger.info(f"📦 五檔批次 {batch_count}: {inserted_count}/{len(batch_data)} 筆 (耗時: {batch_time:.2f}秒)")
                
                # 恢復正常設定
                if optimize_performance:
                    try:
                        pg_cursor.execute("SET synchronous_commit = ON")
                        logger.info("✅ 已恢復同步提交設定")
                    except:
                        pass
                
                total_time = time.time() - total_start_time
                logger.info(f"✅ 五檔資料匯入完成！")
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
            logger.error(f"❌ 匯入五檔資料過程中發生錯誤: {e}", exc_info=True)
            return False

    def import_all_data_to_postgres(self, symbol='MTX00', batch_size=5000, optimize_performance=True):
        """匯入所有類型資料到PostgreSQL"""
        logger.info(f"🚀 開始匯入 {symbol} 所有資料到PostgreSQL...")
        
        results = {
            'kline': False,
            'tick': False,
            'best5': False
        }
        
        # 匯入K線資料
        logger.info("📈 匯入K線資料...")
        try:
            results['kline'] = self.import_kline_to_postgres(
                symbol=symbol, 
                kline_type='MINUTE',
                batch_size=batch_size,
                optimize_performance=optimize_performance
            )
        except Exception as e:
            logger.error(f"❌ K線資料匯入失敗: {e}")
        
        # 匯入逐筆資料
        logger.info("📊 匯入逐筆資料...")
        try:
            results['tick'] = self.import_tick_to_postgres(
                symbol=symbol,
                batch_size=batch_size,
                optimize_performance=optimize_performance
            )
        except Exception as e:
            logger.error(f"❌ 逐筆資料匯入失敗: {e}")
        
        # 匯入五檔資料
        logger.info("📋 匯入五檔資料...")
        try:
            results['best5'] = self.import_best5_to_postgres(
                symbol=symbol,
                batch_size=batch_size,
                optimize_performance=optimize_performance
            )
        except Exception as e:
            logger.error(f"❌ 五檔資料匯入失敗: {e}")
        
        # 總結結果
        success_count = sum(1 for success in results.values() if success)
        total_count = len(results)
        
        logger.info(f"✅ 全部資料匯入完成！")
        logger.info(f"📊 匯入結果: {success_count}/{total_count} 成功")
        logger.info(f"  - K線資料: {'✅' if results['kline'] else '❌'}")
        logger.info(f"  - 逐筆資料: {'✅' if results['tick'] else '❌'}")
        logger.info(f"  - 五檔資料: {'✅' if results['best5'] else '❌'}")
        
        return success_count == total_count

    def get_postgres_data_statistics(self):
        """取得PostgreSQL資料統計"""
        if not self.postgres_initialized:
            logger.error("❌ PostgreSQL未初始化")
            return None
        
        try:
            import shared
            with shared.get_conn_cur_from_pool_b(as_dict=True) as (pg_conn, pg_cursor):
                stats = {}
                
                # K線資料統計
                try:
                    pg_cursor.execute("SELECT COUNT(*) as count FROM stock_prices")
                    result = pg_cursor.fetchone()
                    stats['kline_count'] = result['count'] if result else 0
                except:
                    stats['kline_count'] = 0
                
                # 逐筆資料統計
                try:
                    pg_cursor.execute("SELECT COUNT(*) as count FROM tick_prices")
                    result = pg_cursor.fetchone()
                    stats['tick_count'] = result['count'] if result else 0
                except:
                    stats['tick_count'] = 0
                
                # 五檔資料統計
                try:
                    pg_cursor.execute("SELECT COUNT(*) as count FROM best5_prices")
                    result = pg_cursor.fetchone()
                    stats['best5_count'] = result['count'] if result else 0
                except:
                    stats['best5_count'] = 0
                
                stats['total_count'] = stats['kline_count'] + stats['tick_count'] + stats['best5_count']
                
                return stats
                
        except Exception as e:
            logger.error(f"❌ 取得PostgreSQL統計資料失敗: {e}")
            return None
