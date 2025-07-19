#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
簡化版數據源驗證測試
檢查兩個系統使用的數據源是否一致
"""

import os
import logging
from datetime import time
from pathlib import Path
import hashlib
import json

# 設定日誌
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def check_sqlite_database():
    """檢查SQLite數據庫"""
    logger.info("🔍 檢查SQLite數據庫...")
    
    db_path = Path("stock_data.sqlite")
    
    if not db_path.exists():
        logger.error(f"❌ SQLite數據庫不存在: {db_path}")
        return None
    
    db_info = {
        'database_path': str(db_path.absolute()),
        'database_size': db_path.stat().st_size,
        'database_mtime': db_path.stat().st_mtime,
        'database_exists': True
    }
    
    logger.info(f"✅ 數據庫路徑: {db_info['database_path']}")
    logger.info(f"✅ 數據庫大小: {db_info['database_size']:,} bytes")
    
    return db_info

def check_data_consistency():
    """檢查數據一致性"""
    logger.info("🔍 檢查數據一致性...")
    
    try:
        import sqlite_connection
        
        # 初始化連接
        sqlite_connection.init_sqlite_connection()
        
        test_date = "2024-11-15"
        
        with sqlite_connection.get_conn_cur_from_sqlite_with_adapter(as_dict=True) as (conn, cur):
            # 獲取測試日期的數據
            cur.execute(
                "SELECT * FROM stock_prices WHERE trade_datetime::date = %s ORDER BY trade_datetime;", 
                (test_date,)
            )
            all_data = cur.fetchall()
            
            if not all_data:
                logger.warning(f"⚠️ 測試日期 {test_date} 沒有數據")
                return None
            
            # 過濾交易時段數據
            session_data = [
                c for c in all_data 
                if time(8, 45) <= c['trade_datetime'].time() <= time(13, 45)
            ]
            
            # 獲取開盤區間數據
            range_data = [
                c for c in session_data 
                if c['trade_datetime'].time() in [time(8, 46), time(8, 47)]
            ]
            
            data_info = {
                'test_date': test_date,
                'total_records': len(all_data),
                'session_records': len(session_data),
                'range_records': len(range_data),
                'data_available': len(session_data) > 0
            }
            
            if session_data:
                # 計算數據摘要
                first_record = session_data[0]
                last_record = session_data[-1]
                
                data_info.update({
                    'first_time': first_record['trade_datetime'].isoformat(),
                    'last_time': last_record['trade_datetime'].isoformat(),
                    'first_close': float(first_record['close_price']),
                    'last_close': float(last_record['close_price'])
                })
                
                # 計算簡單哈希
                price_sum = sum(float(c['close_price']) for c in session_data[:10])  # 只用前10筆
                data_info['price_checksum'] = round(price_sum, 2)
            
            logger.info(f"✅ 測試日期: {data_info['test_date']}")
            logger.info(f"✅ 總記錄數: {data_info['total_records']}")
            logger.info(f"✅ 交易時段記錄數: {data_info['session_records']}")
            logger.info(f"✅ 開盤區間記錄數: {data_info['range_records']}")
            
            if 'price_checksum' in data_info:
                logger.info(f"✅ 價格校驗和: {data_info['price_checksum']}")
            
            return data_info
            
    except Exception as e:
        logger.error(f"❌ 數據檢查失敗: {e}")
        return None

def check_core_engines():
    """檢查核心引擎文件"""
    logger.info("🔍 檢查核心引擎文件...")
    
    engines = {
        'rev_web_trading_gui': 'rev_multi_Profit-Funded Risk_多口.py',
        'mdd_gui': 'experiment_analysis/exp_rev_multi_Profit-Funded Risk_多口.py'
    }
    
    engine_info = {}
    
    for name, path in engines.items():
        file_path = Path(path)
        if file_path.exists():
            engine_info[name] = {
                'file_path': str(file_path),
                'file_size': file_path.stat().st_size,
                'file_mtime': file_path.stat().st_mtime,
                'exists': True
            }
            logger.info(f"✅ {name}: {path} (大小: {file_path.stat().st_size:,} bytes)")
        else:
            engine_info[name] = {
                'file_path': str(file_path),
                'exists': False
            }
            logger.warning(f"⚠️ {name}: {path} 不存在")
    
    return engine_info

def compare_engines():
    """比較兩個引擎的關鍵差異"""
    logger.info("🔍 比較引擎差異...")
    
    try:
        # 讀取兩個文件的關鍵部分
        rev_web_file = Path('rev_multi_Profit-Funded Risk_多口.py')
        mdd_file = Path('experiment_analysis/exp_rev_multi_Profit-Funded Risk_多口.py')
        
        differences = []
        
        if rev_web_file.exists() and mdd_file.exists():
            # 檢查文件大小差異
            rev_size = rev_web_file.stat().st_size
            mdd_size = mdd_file.stat().st_size
            
            if rev_size != mdd_size:
                differences.append(f"文件大小不同: rev_web({rev_size}) vs mdd({mdd_size})")
            
            # 檢查關鍵字符串
            with open(rev_web_file, 'r', encoding='utf-8') as f:
                rev_content = f.read()
            
            with open(mdd_file, 'r', encoding='utf-8') as f:
                mdd_content = f.read()
            
            # 檢查關鍵差異
            key_patterns = [
                'USE_SQLITE',
                'max_drawdown',
                'total_pnl',
                'Decimal',
                'float'
            ]
            
            for pattern in key_patterns:
                rev_count = rev_content.count(pattern)
                mdd_count = mdd_content.count(pattern)
                
                if rev_count != mdd_count:
                    differences.append(f"'{pattern}' 出現次數不同: rev_web({rev_count}) vs mdd({mdd_count})")
            
            logger.info(f"✅ 發現 {len(differences)} 個差異")
            for diff in differences:
                logger.warning(f"❌ {diff}")
        
        return differences
        
    except Exception as e:
        logger.error(f"❌ 比較引擎失敗: {e}")
        return []

def main():
    """主函數"""
    logger.info("🚀 開始簡化數據源驗證...")
    logger.info("=" * 60)
    
    # 1. 檢查SQLite數據庫
    db_info = check_sqlite_database()
    
    logger.info("=" * 60)
    
    # 2. 檢查數據一致性
    data_info = check_data_consistency()
    
    logger.info("=" * 60)
    
    # 3. 檢查核心引擎文件
    engine_info = check_core_engines()
    
    logger.info("=" * 60)
    
    # 4. 比較引擎差異
    differences = compare_engines()
    
    logger.info("=" * 60)
    
    # 5. 生成報告
    report = {
        'database_info': db_info,
        'data_info': data_info,
        'engine_info': engine_info,
        'differences': differences,
        'summary': {
            'database_available': db_info is not None,
            'data_available': data_info is not None and data_info.get('data_available', False),
            'engines_available': all(info.get('exists', False) for info in engine_info.values()),
            'differences_found': len(differences) > 0
        }
    }
    
    # 保存報告
    try:
        with open('任務2_簡化數據源驗證報告.json', 'w', encoding='utf-8') as f:
            json.dump(report, f, ensure_ascii=False, indent=2, default=str)
        logger.info("📋 報告已保存: 任務2_簡化數據源驗證報告.json")
    except Exception as e:
        logger.error(f"❌ 保存報告失敗: {e}")
    
    # 總結
    logger.info("=" * 60)
    logger.info("驗證總結")
    logger.info("=" * 60)
    
    if report['summary']['database_available']:
        logger.info("✅ 數據庫可用")
    else:
        logger.error("❌ 數據庫不可用")
    
    if report['summary']['data_available']:
        logger.info("✅ 測試數據可用")
    else:
        logger.error("❌ 測試數據不可用")
    
    if report['summary']['engines_available']:
        logger.info("✅ 核心引擎文件都存在")
    else:
        logger.error("❌ 部分核心引擎文件缺失")
    
    if report['summary']['differences_found']:
        logger.warning(f"⚠️ 發現 {len(differences)} 個差異")
    else:
        logger.info("✅ 未發現明顯差異")

if __name__ == "__main__":
    main()
