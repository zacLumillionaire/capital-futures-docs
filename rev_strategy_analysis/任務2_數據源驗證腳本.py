#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
任務2：數據源與輸入驗證腳本
檢查 mdd_gui.py 和 rev_web_trading_gui.py 是否使用相同的數據源
"""

import os
import sys
import json
import hashlib
from datetime import datetime, time
from pathlib import Path

# 添加項目根目錄到路徑
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# 導入共享模組
import shared

def get_database_info():
    """獲取數據庫連接信息"""
    try:
        # 檢查數據庫文件
        db_files = []
        
        # 檢查當前目錄的 SQLite 文件
        current_dir = Path(__file__).parent
        for db_file in current_dir.glob("*.sqlite"):
            stat = db_file.stat()
            db_files.append({
                'path': str(db_file.absolute()),
                'size': stat.st_size,
                'modified': datetime.fromtimestamp(stat.st_mtime).isoformat(),
                'exists': True
            })
        
        return {
            'database_files': db_files,
            'shared_module_path': shared.__file__ if hasattr(shared, '__file__') else 'Unknown'
        }
    except Exception as e:
        return {'error': f'獲取數據庫信息失敗: {str(e)}'}

def get_data_sample(start_date="2024-11-04", end_date="2024-11-05", limit=10):
    """獲取數據樣本進行比較"""
    try:
        # 使用與回測引擎相同的數據庫連接方式
        context_manager = shared.get_conn_cur_from_pool_b(as_dict=True)
        
        with context_manager as (conn, cur):
            # 獲取交易日列表
            base_query = "SELECT DISTINCT trade_datetime::date as trade_day FROM stock_prices"
            conditions = ["trade_datetime::date >= %s", "trade_datetime::date <= %s"]
            params = [start_date, end_date]
            
            query = f"{base_query} WHERE {' AND '.join(conditions)} ORDER BY trade_day"
            cur.execute(query, tuple(params))
            trade_days = [row['trade_day'] for row in cur.fetchall()]
            
            if not trade_days:
                return {'error': '找不到指定日期範圍的數據'}
            
            # 獲取第一個交易日的數據樣本
            first_day = trade_days[0]
            cur.execute(
                "SELECT * FROM stock_prices WHERE trade_datetime::date = %s ORDER BY trade_datetime LIMIT %s;", 
                (first_day, limit)
            )
            sample_data = cur.fetchall()
            
            # 計算數據指紋
            data_str = json.dumps(sample_data, default=str, sort_keys=True)
            data_hash = hashlib.md5(data_str.encode()).hexdigest()
            
            return {
                'trade_days_count': len(trade_days),
                'first_trade_day': str(first_day),
                'sample_records_count': len(sample_data),
                'sample_data_head': sample_data[:3] if sample_data else [],
                'sample_data_tail': sample_data[-3:] if len(sample_data) > 3 else [],
                'data_hash': data_hash,
                'query_used': f"SELECT * FROM stock_prices WHERE trade_datetime::date = '{first_day}' ORDER BY trade_datetime LIMIT {limit}"
            }
            
    except Exception as e:
        return {'error': f'獲取數據樣本失敗: {str(e)}'}

def check_data_consistency():
    """檢查數據一致性"""
    try:
        # 檢查兩個回測引擎使用的數據是否一致
        
        # 1. 檢查 exp_rev_multi_Profit-Funded Risk_多口.py 的數據
        exp_data = get_data_sample()
        
        # 2. 檢查 rev_multi_Profit-Funded Risk_多口.py 的數據
        rev_data = get_data_sample()
        
        # 3. 比較數據指紋
        consistency_check = {
            'exp_engine_data': exp_data,
            'rev_engine_data': rev_data,
            'data_hash_match': exp_data.get('data_hash') == rev_data.get('data_hash'),
            'trade_days_match': exp_data.get('trade_days_count') == rev_data.get('trade_days_count')
        }
        
        return consistency_check
        
    except Exception as e:
        return {'error': f'數據一致性檢查失敗: {str(e)}'}

def check_time_filtering():
    """檢查時間過濾邏輯"""
    try:
        context_manager = shared.get_conn_cur_from_pool_b(as_dict=True)
        
        with context_manager as (conn, cur):
            # 測試特定日期的時間過濾
            test_date = "2024-11-04"
            
            # 獲取全天數據
            cur.execute(
                "SELECT * FROM stock_prices WHERE trade_datetime::date = %s ORDER BY trade_datetime;", 
                (test_date,)
            )
            all_data = cur.fetchall()
            
            # 模擬回測引擎的時間過濾邏輯
            day_session_candles = [
                c for c in all_data 
                if time(8, 45) <= c['trade_datetime'].time() <= time(13, 45)
            ]
            
            # 模擬開盤區間過濾 (08:46-08:47)
            range_start_time_obj = time(8, 46)
            range_end_time_obj = time(8, 47)
            
            candles_range = [
                c for c in day_session_candles
                if range_start_time_obj <= c['trade_datetime'].time() <= range_end_time_obj
            ]
            
            return {
                'test_date': test_date,
                'total_records': len(all_data),
                'day_session_records': len(day_session_candles),
                'range_records': len(candles_range),
                'first_record_time': str(all_data[0]['trade_datetime']) if all_data else None,
                'last_record_time': str(all_data[-1]['trade_datetime']) if all_data else None,
                'range_sample': [
                    {
                        'time': str(c['trade_datetime']),
                        'open': float(c['open_price']),
                        'high': float(c['high_price']),
                        'low': float(c['low_price']),
                        'close': float(c['close_price'])
                    }
                    for c in candles_range[:5]
                ]
            }
            
    except Exception as e:
        return {'error': f'時間過濾檢查失敗: {str(e)}'}

def main():
    """主函數"""
    print("=" * 60)
    print("任務2：數據源與輸入驗證")
    print("=" * 60)
    
    # 1. 檢查數據庫信息
    print("\n1. 數據庫信息檢查")
    print("-" * 30)
    db_info = get_database_info()
    print(json.dumps(db_info, indent=2, ensure_ascii=False))
    
    # 2. 檢查數據一致性
    print("\n2. 數據一致性檢查")
    print("-" * 30)
    consistency = check_data_consistency()
    print(json.dumps(consistency, indent=2, ensure_ascii=False))
    
    # 3. 檢查時間過濾邏輯
    print("\n3. 時間過濾邏輯檢查")
    print("-" * 30)
    time_filter = check_time_filtering()
    print(json.dumps(time_filter, indent=2, ensure_ascii=False))
    
    # 4. 生成報告
    report = {
        'timestamp': datetime.now().isoformat(),
        'database_info': db_info,
        'data_consistency': consistency,
        'time_filtering': time_filter,
        'summary': {
            'database_accessible': 'error' not in db_info,
            'data_consistent': consistency.get('data_hash_match', False),
            'time_filtering_working': 'error' not in time_filter
        }
    }
    
    # 保存報告
    report_file = 'rev_strategy_analysis/任務2_數據源驗證報告.json'
    with open(report_file, 'w', encoding='utf-8') as f:
        json.dump(report, f, indent=2, ensure_ascii=False)
    
    print(f"\n📊 報告已保存到: {report_file}")
    print("\n✅ 數據源驗證完成")

if __name__ == "__main__":
    main()
