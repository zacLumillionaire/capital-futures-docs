#!/usr/bin/env python3
"""
檢查數據中的時間分佈
"""

import logging
import sqlite_connection
from datetime import time

logging.basicConfig(level=logging.INFO, format='[%(asctime)s] %(levelname)s: %(message)s')
logger = logging.getLogger(__name__)

def check_time_distribution():
    """檢查數據中的時間分佈"""
    logger.info("🔍 檢查數據中的時間分佈...")
    
    try:
        with sqlite_connection.get_conn_cur_from_sqlite_with_adapter(as_dict=True) as (conn, cur):
            # 檢查早盤時間的數據分佈
            cur.execute("""
                SELECT 
                    strftime('%H:%M', trade_datetime) as time_str,
                    COUNT(*) as count,
                    COUNT(DISTINCT trade_datetime::date) as days
                FROM stock_prices 
                WHERE strftime('%H:%M', trade_datetime) BETWEEN '08:40' AND '09:00'
                  AND trade_datetime::date BETWEEN '2024-11-04' AND '2025-06-28'
                GROUP BY strftime('%H:%M', trade_datetime)
                ORDER BY time_str
            """)
            
            results = cur.fetchall()
            
            logger.info("📊 早盤時間分佈 (08:40-09:00):")
            for row in results:
                logger.info(f"   {row['time_str']}: {row['count']} 筆記錄, {row['days']} 天")
            
            # 特別檢查我們需要的時間點
            target_times = ['08:45', '08:46', '08:47']
            logger.info("\n🎯 檢查目標時間點:")
            
            for target_time in target_times:
                cur.execute("""
                    SELECT COUNT(DISTINCT trade_datetime::date) as days
                    FROM stock_prices 
                    WHERE strftime('%H:%M', trade_datetime) = ?
                      AND trade_datetime::date BETWEEN '2024-11-04' AND '2025-06-28'
                """, (target_time,))
                
                result = cur.fetchone()
                days = result['days']
                logger.info(f"   {target_time}: {days} 天有數據")
            
            # 檢查某一天的詳細數據
            cur.execute("""
                SELECT trade_datetime, high_price, low_price, close_price
                FROM stock_prices 
                WHERE trade_datetime::date = '2024-11-05'
                  AND strftime('%H:%M', trade_datetime) BETWEEN '08:45' AND '08:48'
                ORDER BY trade_datetime
            """)
            
            sample_data = cur.fetchall()
            logger.info(f"\n📅 樣本日期 (2024-11-05) 的早盤數據:")
            for row in sample_data:
                logger.info(f"   {row['trade_datetime']}: H={row['high_price']}, L={row['low_price']}, C={row['close_price']}")
                
    except Exception as e:
        logger.error(f"❌ 檢查時間分佈失敗: {e}")

if __name__ == '__main__':
    check_time_distribution()
