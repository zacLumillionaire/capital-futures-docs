#!/usr/bin/env python3
"""
數據同步工具
用於從PostgreSQL同步最新數據到SQLite
"""

import sqlite3
import logging
from datetime import datetime
from pathlib import Path
import sys

# 設置日誌
logging.basicConfig(
    level=logging.INFO,
    format='[%(asctime)s] %(levelname)s [%(name)s.%(funcName)s:%(lineno)d] %(message)s',
    datefmt='%Y-%m-%dT%H:%M:%S%z'
)
logger = logging.getLogger(__name__)

def check_sqlite_status():
    """檢查SQLite數據庫狀態"""
    db_path = Path(__file__).parent / "stock_data.sqlite"
    
    if not db_path.exists():
        logger.error("❌ SQLite數據庫文件不存在！")
        logger.info("💡 請先運行: python simple_export.py")
        return False
    
    try:
        conn = sqlite3.connect(db_path)
        cur = conn.cursor()
        
        # 檢查記錄數
        cur.execute("SELECT COUNT(*) FROM stock_prices")
        count = cur.fetchone()[0]
        
        # 檢查日期範圍
        cur.execute("SELECT MIN(date(trade_datetime)), MAX(date(trade_datetime)) FROM stock_prices")
        min_date, max_date = cur.fetchone()
        
        logger.info(f"✅ SQLite狀態正常")
        logger.info(f"📊 記錄數: {count:,}")
        logger.info(f"📅 日期範圍: {min_date} 至 {max_date}")
        
        conn.close()
        return True, count, min_date, max_date
        
    except Exception as e:
        logger.error(f"❌ SQLite檢查失敗: {e}")
        return False

def check_postgresql_status():
    """檢查PostgreSQL數據庫狀態"""
    try:
        # 導入PostgreSQL相關模組
        import shared
        from app_setup import init_all_db_pools
        
        logger.info("🔌 連接PostgreSQL...")
        init_all_db_pools()
        
        with shared.get_conn_cur_from_pool_b(as_dict=True) as (conn, cur):
            # 檢查記錄數
            cur.execute("SELECT COUNT(*) FROM stock_prices")
            count = cur.fetchone()['count']
            
            # 檢查日期範圍
            cur.execute("SELECT MIN(trade_datetime::date), MAX(trade_datetime::date) FROM stock_prices")
            result = cur.fetchone()
            min_date, max_date = result['min'], result['max']
            
            logger.info(f"✅ PostgreSQL狀態正常")
            logger.info(f"📊 記錄數: {count:,}")
            logger.info(f"📅 日期範圍: {min_date} 至 {max_date}")
            
            return True, count, str(min_date), str(max_date)
            
    except Exception as e:
        logger.error(f"❌ PostgreSQL檢查失敗: {e}")
        return False

def compare_databases():
    """比較兩個數據庫的狀態"""
    logger.info("🔍 開始數據庫狀態比較...")
    
    # 檢查SQLite
    sqlite_result = check_sqlite_status()
    if not sqlite_result:
        return False
    
    sqlite_ok, sqlite_count, sqlite_min, sqlite_max = sqlite_result
    
    # 檢查PostgreSQL
    pg_result = check_postgresql_status()
    if not pg_result:
        return False
    
    pg_ok, pg_count, pg_min, pg_max = pg_result
    
    # 比較結果
    logger.info(f"\n📊 數據庫比較結果:")
    logger.info(f"  PostgreSQL: {pg_count:,} 筆記錄 ({pg_min} 至 {pg_max})")
    logger.info(f"  SQLite:     {sqlite_count:,} 筆記錄 ({sqlite_min} 至 {sqlite_max})")
    
    missing_records = pg_count - sqlite_count
    sync_percentage = (sqlite_count / pg_count) * 100 if pg_count > 0 else 0
    
    logger.info(f"  同步完成度: {sync_percentage:.1f}%")
    
    if missing_records > 0:
        logger.warning(f"⚠️  SQLite缺少 {missing_records:,} 筆記錄")
        logger.info(f"💡 建議運行: python simple_export.py")
        return False
    elif missing_records == 0:
        logger.info(f"✅ 數據完全同步！")
        return True
    else:
        logger.warning(f"⚠️  SQLite記錄數超過PostgreSQL？這不應該發生。")
        return False

def sync_data():
    """執行數據同步"""
    logger.info("🚀 開始數據同步...")
    
    try:
        # 導入並執行simple_export
        import subprocess
        import sys
        
        result = subprocess.run([
            sys.executable, 
            'simple_export.py'
        ], capture_output=True, text=True)
        
        if result.returncode == 0:
            logger.info("✅ 數據同步完成！")
            logger.info("🔍 重新檢查數據庫狀態...")
            compare_databases()
        else:
            logger.error(f"❌ 數據同步失敗: {result.stderr}")
            
    except Exception as e:
        logger.error(f"❌ 同步過程出錯: {e}")

def main():
    """主函數"""
    logger.info("🔄 SQLite數據同步工具")
    logger.info("=" * 50)
    
    if len(sys.argv) > 1:
        command = sys.argv[1].lower()
        
        if command == "check":
            logger.info("📋 執行數據庫狀態檢查...")
            compare_databases()
            
        elif command == "sync":
            logger.info("🔄 執行數據同步...")
            sync_data()
            
        elif command == "sqlite":
            logger.info("📋 檢查SQLite狀態...")
            check_sqlite_status()
            
        elif command == "postgres":
            logger.info("📋 檢查PostgreSQL狀態...")
            check_postgresql_status()
            
        else:
            print("❌ 未知命令")
            print_usage()
    else:
        # 默認執行比較
        compare_databases()

def print_usage():
    """打印使用說明"""
    print("""
🔄 SQLite數據同步工具使用說明:

python sync_data.py [命令]

命令選項:
  check     - 比較PostgreSQL和SQLite數據狀態 (默認)
  sync      - 執行完整數據同步
  sqlite    - 僅檢查SQLite狀態
  postgres  - 僅檢查PostgreSQL狀態

使用範例:
  python sync_data.py check    # 檢查同步狀態
  python sync_data.py sync     # 執行數據同步
  python sync_data.py          # 默認檢查狀態
    """)

if __name__ == "__main__":
    main()
