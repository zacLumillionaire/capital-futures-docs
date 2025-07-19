#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
任務 2：數據源與輸入驗證測試腳本
驗證 mdd_gui.py 和 rev_web_trading_gui.py 使用的數據源是否完全一致
"""

import sys
import os
import logging
from datetime import time, date
from pathlib import Path
import hashlib
import json

# 設定日誌
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# 添加父目錄到路徑
parent_dir = Path(__file__).parent
sys.path.insert(0, str(parent_dir))

# 導入數據源模組
try:
    import sqlite_connection
    from app_setup import init_all_db_pools
    import shared
except ImportError as e:
    logger.error(f"無法導入必要模組: {e}")
    sys.exit(1)

class DataSourceValidator:
    """數據源驗證器"""
    
    def __init__(self):
        self.use_sqlite = True  # 與兩個系統保持一致
        self.test_date = "2024-11-15"  # 測試日期
        self.results = {}
        
    def init_data_source(self):
        """初始化數據源"""
        if self.use_sqlite:
            try:
                sqlite_connection.init_sqlite_connection()
                logger.info("✅ SQLite連接初始化成功")
                return True
            except Exception as e:
                logger.error(f"❌ SQLite連接初始化失敗: {e}")
                return False
        else:
            try:
                init_all_db_pools()
                logger.info("✅ PostgreSQL連線池初始化成功")
                return True
            except Exception as e:
                logger.error(f"❌ PostgreSQL連線池初始化失敗: {e}")
                return False
    
    def get_data_source_info(self, source_name):
        """獲取數據源信息"""
        logger.info(f"🔍 檢查數據源: {source_name}")
        
        try:
            if self.use_sqlite:
                context_manager = sqlite_connection.get_conn_cur_from_sqlite_with_adapter(as_dict=True)
            else:
                context_manager = shared.get_conn_cur_from_pool_b(as_dict=True)
            
            with context_manager as (conn, cur):
                # 1. 檢查數據庫文件/連接信息
                if self.use_sqlite:
                    db_path = sqlite_connection._sqlite_connection.db_path
                    db_size = db_path.stat().st_size if db_path.exists() else 0
                    db_mtime = db_path.stat().st_mtime if db_path.exists() else 0
                    
                    source_info = {
                        'database_type': 'SQLite',
                        'database_path': str(db_path),
                        'database_size': db_size,
                        'database_mtime': db_mtime,
                        'database_exists': db_path.exists()
                    }
                else:
                    source_info = {
                        'database_type': 'PostgreSQL',
                        'connection_info': 'Remote PostgreSQL'
                    }
                
                # 2. 檢查測試日期的數據
                test_data_info = self.get_test_date_data(cur)
                source_info.update(test_data_info)
                
                # 3. 檢查數據表結構
                table_info = self.get_table_structure(cur)
                source_info.update(table_info)
                
                return source_info
                
        except Exception as e:
            logger.error(f"❌ 獲取數據源信息失敗: {e}")
            return {'error': str(e)}
    
    def get_test_date_data(self, cur):
        """獲取測試日期的數據詳情"""
        try:
            # 獲取測試日期的所有數據
            cur.execute(
                "SELECT * FROM stock_prices WHERE trade_datetime::date = %s ORDER BY trade_datetime;", 
                (self.test_date,)
            )
            all_data = cur.fetchall()
            
            if not all_data:
                return {
                    'test_date': self.test_date,
                    'total_records': 0,
                    'data_available': False
                }
            
            # 過濾交易時段數據 (8:45-13:45)
            session_data = [
                c for c in all_data 
                if time(8, 45) <= c['trade_datetime'].time() <= time(13, 45)
            ]
            
            # 獲取開盤區間數據 (8:46-8:47)
            range_data = [
                c for c in session_data 
                if c['trade_datetime'].time() in [time(8, 46), time(8, 47)]
            ]
            
            # 計算數據摘要
            if session_data:
                first_record = session_data[0]
                last_record = session_data[-1]
                
                # 計算數據哈希值（用於比較一致性）
                data_str = json.dumps([
                    {
                        'time': c['trade_datetime'].isoformat(),
                        'open': float(c['open_price']),
                        'high': float(c['high_price']),
                        'low': float(c['low_price']),
                        'close': float(c['close_price'])
                    } for c in session_data
                ], sort_keys=True)
                data_hash = hashlib.md5(data_str.encode()).hexdigest()
                
                return {
                    'test_date': self.test_date,
                    'total_records': len(all_data),
                    'session_records': len(session_data),
                    'range_records': len(range_data),
                    'data_available': True,
                    'first_time': first_record['trade_datetime'].isoformat(),
                    'last_time': last_record['trade_datetime'].isoformat(),
                    'data_hash': data_hash,
                    'sample_records': {
                        'first': {
                            'time': first_record['trade_datetime'].isoformat(),
                            'open': float(first_record['open_price']),
                            'high': float(first_record['high_price']),
                            'low': float(first_record['low_price']),
                            'close': float(first_record['close_price'])
                        },
                        'last': {
                            'time': last_record['trade_datetime'].isoformat(),
                            'open': float(last_record['open_price']),
                            'high': float(last_record['high_price']),
                            'low': float(last_record['low_price']),
                            'close': float(last_record['close_price'])
                        }
                    }
                }
            else:
                return {
                    'test_date': self.test_date,
                    'total_records': len(all_data),
                    'session_records': 0,
                    'data_available': False
                }
                
        except Exception as e:
            logger.error(f"❌ 獲取測試日期數據失敗: {e}")
            return {'test_date_error': str(e)}
    
    def get_table_structure(self, cur):
        """獲取數據表結構信息"""
        try:
            if self.use_sqlite:
                cur.execute("PRAGMA table_info(stock_prices);")
                columns = cur.fetchall()
                return {
                    'table_structure': [
                        {
                            'name': col['name'],
                            'type': col['type'],
                            'notnull': bool(col['notnull']),
                            'pk': bool(col['pk'])
                        } for col in columns
                    ]
                }
            else:
                # PostgreSQL 表結構查詢
                cur.execute("""
                    SELECT column_name, data_type, is_nullable 
                    FROM information_schema.columns 
                    WHERE table_name = 'stock_prices'
                    ORDER BY ordinal_position;
                """)
                columns = cur.fetchall()
                return {
                    'table_structure': [
                        {
                            'name': col['column_name'],
                            'type': col['data_type'],
                            'nullable': col['is_nullable'] == 'YES'
                        } for col in columns
                    ]
                }
        except Exception as e:
            logger.error(f"❌ 獲取表結構失敗: {e}")
            return {'table_structure_error': str(e)}
    
    def run_validation(self):
        """執行數據源驗證"""
        logger.info("🚀 開始數據源驗證...")
        
        # 初始化數據源
        if not self.init_data_source():
            return False
        
        # 模擬兩個系統的數據源檢查
        logger.info("=" * 60)
        logger.info("檢查 rev_web_trading_gui.py 使用的數據源")
        logger.info("=" * 60)
        rev_web_data = self.get_data_source_info("rev_web_trading_gui")
        
        logger.info("=" * 60)
        logger.info("檢查 mdd_gui.py 使用的數據源")
        logger.info("=" * 60)
        mdd_gui_data = self.get_data_source_info("mdd_gui")
        
        # 保存結果
        self.results = {
            'rev_web_trading_gui': rev_web_data,
            'mdd_gui': mdd_gui_data,
            'validation_time': str(date.today())
        }
        
        # 比較結果
        self.compare_data_sources()
        
        return True
    
    def compare_data_sources(self):
        """比較兩個數據源的一致性"""
        logger.info("=" * 60)
        logger.info("數據源一致性比較")
        logger.info("=" * 60)
        
        rev_data = self.results['rev_web_trading_gui']
        mdd_data = self.results['mdd_gui']
        
        # 比較關鍵字段
        comparison_fields = [
            'database_type', 'database_path', 'database_size', 'database_mtime',
            'total_records', 'session_records', 'range_records', 'data_hash'
        ]
        
        differences = []
        matches = []
        
        for field in comparison_fields:
            if field in rev_data and field in mdd_data:
                if rev_data[field] == mdd_data[field]:
                    matches.append(field)
                    logger.info(f"✅ {field}: 一致 ({rev_data[field]})")
                else:
                    differences.append(field)
                    logger.warning(f"❌ {field}: 不一致")
                    logger.warning(f"   rev_web_trading_gui: {rev_data[field]}")
                    logger.warning(f"   mdd_gui: {mdd_data[field]}")
            else:
                logger.warning(f"⚠️ {field}: 缺少數據")
        
        # 總結
        logger.info("=" * 60)
        logger.info("驗證總結")
        logger.info("=" * 60)
        logger.info(f"✅ 一致字段: {len(matches)}")
        logger.info(f"❌ 不一致字段: {len(differences)}")
        
        if differences:
            logger.error("🚨 發現數據源不一致！")
            logger.error(f"不一致字段: {differences}")
        else:
            logger.info("🎉 數據源完全一致！")
        
        # 保存詳細報告
        self.save_report()
    
    def save_report(self):
        """保存驗證報告"""
        report_file = "任務2_數據源驗證報告.json"
        try:
            with open(report_file, 'w', encoding='utf-8') as f:
                json.dump(self.results, f, ensure_ascii=False, indent=2, default=str)
            logger.info(f"📋 驗證報告已保存: {report_file}")
        except Exception as e:
            logger.error(f"❌ 保存報告失敗: {e}")

def main():
    """主函數"""
    validator = DataSourceValidator()
    success = validator.run_validation()
    
    if not success:
        sys.exit(1)

if __name__ == "__main__":
    main()
