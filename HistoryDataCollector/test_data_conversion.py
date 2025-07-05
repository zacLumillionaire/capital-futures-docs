#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
測試資料轉換功能
驗證K線資料收集和PostgreSQL轉換是否正確列印前10行資料
"""

import os
import sys
import logging

# 添加專案路徑
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from collectors.kline_collector import KLineCollector
from database.postgres_importer import PostgreSQLImporter
from utils.logger import setup_logger, get_logger

# 設定日誌
setup_logger()
logger = get_logger(__name__)

def test_kline_data_conversion():
    """測試K線資料轉換"""
    print("=" * 80)
    print("測試K線資料收集器的資料轉換功能")
    print("=" * 80)
    
    # 創建一個模擬的KLineCollector
    collector = KLineCollector(None, None)
    collector.current_kline_type = 'MINUTE'
    collector.current_symbol = 'MTX00'
    collector.is_collecting = True
    collector.printed_count = 0
    
    # 模擬一些K線資料
    test_data = [
        "2025/1/6 08:46,22950,22950,22950,22950,5",
        "2025/1/6 08:47,22950,22955,22945,22950,12",
        "2025/1/6 08:48,22950,22960,22940,22955,25",
        "2025/1/6 08:49,22955,22965,22950,22960,18",
        "2025/1/6 08:50,22960,22970,22955,22965,30",
        "2025/1/6 08:51,22965,22975,22960,22970,22",
        "2025/1/6 08:52,22970,22980,22965,22975,35",
        "2025/1/6 08:53,22975,22985,22970,22980,28",
        "2025/1/6 08:54,22980,22990,22975,22985,40",
        "2025/1/6 08:55,22985,22995,22980,22990,33",
        "2025/1/6 08:56,22990,23000,22985,22995,45",
        "2025/1/6 08:57,22995,23005,22990,23000,38"
    ]
    
    print(f"模擬處理 {len(test_data)} 筆K線資料...")
    print()
    
    # 處理每筆資料
    for i, data in enumerate(test_data):
        print(f"處理第 {i+1} 筆資料...")
        collector.on_kline_received('MTX00', data)
        if i >= 9:  # 只處理前10筆來測試列印功能
            break
    
    print()
    print("K線資料收集器測試完成！")
    print("=" * 80)

def test_postgres_conversion():
    """測試PostgreSQL轉換功能"""
    print()
    print("=" * 80)
    print("測試PostgreSQL匯入器的資料轉換功能")
    print("=" * 80)
    
    # 創建PostgreSQL匯入器（不需要實際連接）
    importer = PostgreSQLImporter()
    
    # 模擬一些K線資料（已經轉換為字典格式）
    test_kline_data = [
        {
            'symbol': 'MTX00',
            'kline_type': 'MINUTE',
            'trade_date': '2025/1/6 08:46',
            'trade_time': None,
            'open_price': 22950.0,
            'high_price': 22950.0,
            'low_price': 22950.0,
            'close_price': 22950.0,
            'volume': 5
        },
        {
            'symbol': 'MTX00',
            'kline_type': 'MINUTE',
            'trade_date': '2025/1/6 08:47',
            'trade_time': None,
            'open_price': 22950.0,
            'high_price': 22955.0,
            'low_price': 22945.0,
            'close_price': 22950.0,
            'volume': 12
        },
        {
            'symbol': 'MTX00',
            'kline_type': 'MINUTE',
            'trade_date': '2025/1/6 08:48',
            'trade_time': None,
            'open_price': 22950.0,
            'high_price': 22960.0,
            'low_price': 22940.0,
            'close_price': 22955.0,
            'volume': 25
        },
        {
            'symbol': 'MTX00',
            'kline_type': 'MINUTE',
            'trade_date': '2025/1/6 08:49',
            'trade_time': None,
            'open_price': 22955.0,
            'high_price': 22965.0,
            'low_price': 22950.0,
            'close_price': 22960.0,
            'volume': 18
        },
        {
            'symbol': 'MTX00',
            'kline_type': 'MINUTE',
            'trade_date': '2025/1/6 08:50',
            'trade_time': None,
            'open_price': 22960.0,
            'high_price': 22970.0,
            'low_price': 22955.0,
            'close_price': 22965.0,
            'volume': 30
        },
        {
            'symbol': 'MTX00',
            'kline_type': 'MINUTE',
            'trade_date': '2025/1/6 08:51',
            'trade_time': None,
            'open_price': 22965.0,
            'high_price': 22975.0,
            'low_price': 22960.0,
            'close_price': 22970.0,
            'volume': 22
        },
        {
            'symbol': 'MTX00',
            'kline_type': 'MINUTE',
            'trade_date': '2025/1/6 08:52',
            'trade_time': None,
            'open_price': 22970.0,
            'high_price': 22980.0,
            'low_price': 22965.0,
            'close_price': 22975.0,
            'volume': 35
        },
        {
            'symbol': 'MTX00',
            'kline_type': 'MINUTE',
            'trade_date': '2025/1/6 08:53',
            'trade_time': None,
            'open_price': 22975.0,
            'high_price': 22985.0,
            'low_price': 22970.0,
            'close_price': 22980.0,
            'volume': 28
        },
        {
            'symbol': 'MTX00',
            'kline_type': 'MINUTE',
            'trade_date': '2025/1/6 08:54',
            'trade_time': None,
            'open_price': 22980.0,
            'high_price': 22990.0,
            'low_price': 22975.0,
            'close_price': 22985.0,
            'volume': 40
        },
        {
            'symbol': 'MTX00',
            'kline_type': 'MINUTE',
            'trade_date': '2025/1/6 08:55',
            'trade_time': None,
            'open_price': 22985.0,
            'high_price': 22995.0,
            'low_price': 22980.0,
            'close_price': 22990.0,
            'volume': 33
        },
        {
            'symbol': 'MTX00',
            'kline_type': 'MINUTE',
            'trade_date': '2025/1/6 08:56',
            'trade_time': None,
            'open_price': 22990.0,
            'high_price': 23000.0,
            'low_price': 22985.0,
            'close_price': 22995.0,
            'volume': 45
        },
        {
            'symbol': 'MTX00',
            'kline_type': 'MINUTE',
            'trade_date': '2025/1/6 08:57',
            'trade_time': None,
            'open_price': 22995.0,
            'high_price': 23005.0,
            'low_price': 22990.0,
            'close_price': 23000.0,
            'volume': 38
        }
    ]
    
    print(f"模擬轉換 {len(test_kline_data)} 筆K線資料為PostgreSQL格式...")
    print()
    
    # 轉換每筆資料
    for i, kline_data in enumerate(test_kline_data):
        print(f"轉換第 {i+1} 筆資料...")
        converted = importer.convert_kline_to_stock_price_format(kline_data)
        if converted is None:
            print(f"❌ 第 {i+1} 筆資料轉換失敗")
        if i >= 9:  # 只處理前10筆來測試列印功能
            break
    
    print()
    print("PostgreSQL轉換器測試完成！")
    print("=" * 80)

if __name__ == "__main__":
    try:
        print("開始測試資料轉換功能...")
        print()
        
        # 測試K線資料收集器
        test_kline_data_conversion()
        
        # 測試PostgreSQL轉換器
        test_postgres_conversion()
        
        print()
        print("✅ 所有測試完成！")
        
    except Exception as e:
        print(f"❌ 測試過程中發生錯誤: {e}")
        import traceback
        traceback.print_exc()
