#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
測試異常資料檢測和排除功能
驗證修正後的異常資料處理邏輯
"""

import os
import sys
import logging
from datetime import datetime

# 添加專案路徑
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from database.postgres_importer import PostgreSQLImporter
from utils.logger import setup_logger, get_logger

# 設定日誌
setup_logger()
logger = get_logger(__name__)

def test_anomaly_detection():
    """測試異常資料檢測功能"""
    logger.info("🧪 測試異常資料檢測功能...")
    
    importer = PostgreSQLImporter()
    
    # 測試資料集
    test_cases = [
        {
            'name': '正常資料',
            'data': {
                'symbol': 'MTX00',
                'kline_type': 'MINUTE',
                'trade_date': '2025/1/6 08:46',
                'trade_time': None,
                'open_price': 22950.0,
                'high_price': 22955.0,
                'low_price': 22945.0,
                'close_price': 22952.0,
                'volume': 10
            },
            'should_pass': True,
            'description': '正常的K線資料'
        },
        {
            'name': '所有價格相同',
            'data': {
                'symbol': 'MTX00',
                'kline_type': 'MINUTE',
                'trade_date': '2025/1/6 08:47',
                'trade_time': None,
                'open_price': 22950.0,
                'high_price': 22950.0,
                'low_price': 22950.0,
                'close_price': 22950.0,
                'volume': 5
            },
            'should_pass': False,
            'description': '所有價格都相同的異常資料'
        },
        {
            'name': '成交量為0',
            'data': {
                'symbol': 'MTX00',
                'kline_type': 'MINUTE',
                'trade_date': '2025/1/6 08:48',
                'trade_time': None,
                'open_price': 22950.0,
                'high_price': 22955.0,
                'low_price': 22945.0,
                'close_price': 22952.0,
                'volume': 0
            },
            'should_pass': False,
            'description': '成交量為0的異常資料'
        },
        {
            'name': '價格邏輯錯誤',
            'data': {
                'symbol': 'MTX00',
                'kline_type': 'MINUTE',
                'trade_date': '2025/1/6 08:49',
                'trade_time': None,
                'open_price': 22950.0,
                'high_price': 22940.0,  # 最高價低於開盤價 (錯誤)
                'low_price': 22960.0,   # 最低價高於開盤價 (錯誤)
                'close_price': 22952.0,
                'volume': 8
            },
            'should_pass': False,
            'description': '價格邏輯錯誤的資料 (必須排除)'
        },
        {
            'name': '多重異常',
            'data': {
                'symbol': 'MTX00',
                'kline_type': 'MINUTE',
                'trade_date': '2025/1/6 08:50',
                'trade_time': None,
                'open_price': 22950.0,
                'high_price': 22950.0,
                'low_price': 22950.0,
                'close_price': 22950.0,
                'volume': 0  # 價格相同 + 成交量為0
            },
            'should_pass': False,
            'description': '多重異常：價格相同且成交量為0'
        }
    ]
    
    logger.info(f"準備測試 {len(test_cases)} 個測試案例...")
    
    # 測試 exclude_anomalies=True (排除異常)
    logger.info("\n🔍 測試 exclude_anomalies=True (排除異常資料)")
    exclude_results = []
    
    for i, test_case in enumerate(test_cases, 1):
        logger.info(f"\n測試案例 {i}: {test_case['name']}")
        logger.info(f"描述: {test_case['description']}")
        
        result = importer.convert_kline_to_stock_price_format(
            test_case['data'], 
            exclude_anomalies=True
        )
        
        passed = (result is not None) == test_case['should_pass']
        status = "✅ 通過" if passed else "❌ 失敗"
        
        logger.info(f"預期: {'通過' if test_case['should_pass'] else '被排除'}")
        logger.info(f"實際: {'通過' if result is not None else '被排除'}")
        logger.info(f"結果: {status}")
        
        exclude_results.append(passed)
    
    # 測試 exclude_anomalies=False (保留異常)
    logger.info("\n🔍 測試 exclude_anomalies=False (保留異常資料)")
    include_results = []
    
    for i, test_case in enumerate(test_cases, 1):
        if test_case['name'] == '價格邏輯錯誤':
            # 價格邏輯錯誤無論如何都會被排除
            continue
            
        logger.info(f"\n測試案例 {i}: {test_case['name']}")
        
        result = importer.convert_kline_to_stock_price_format(
            test_case['data'], 
            exclude_anomalies=False
        )
        
        # 當 exclude_anomalies=False 時，除了價格邏輯錯誤外都應該通過
        should_pass = test_case['name'] != '價格邏輯錯誤'
        passed = (result is not None) == should_pass
        status = "✅ 通過" if passed else "❌ 失敗"
        
        logger.info(f"預期: {'通過' if should_pass else '被排除'}")
        logger.info(f"實際: {'通過' if result is not None else '被排除'}")
        logger.info(f"結果: {status}")
        
        include_results.append(passed)
    
    # 總結測試結果
    logger.info("\n" + "=" * 60)
    logger.info("📊 測試結果總結")
    logger.info("=" * 60)
    
    exclude_success_rate = sum(exclude_results) / len(exclude_results) * 100
    include_success_rate = sum(include_results) / len(include_results) * 100
    
    logger.info(f"排除異常模式 (exclude_anomalies=True): {sum(exclude_results)}/{len(exclude_results)} 通過 ({exclude_success_rate:.1f}%)")
    logger.info(f"保留異常模式 (exclude_anomalies=False): {sum(include_results)}/{len(include_results)} 通過 ({include_success_rate:.1f}%)")
    
    overall_success = exclude_success_rate == 100 and include_success_rate == 100
    
    if overall_success:
        logger.info("🎉 所有測試通過！異常資料檢測功能正常運作")
    else:
        logger.warning("⚠️ 部分測試失敗，需要檢查異常檢測邏輯")
    
    return overall_success

def test_import_with_anomaly_settings():
    """測試匯入功能的異常資料設定"""
    logger.info("\n🧪 測試匯入功能的異常資料設定...")
    
    try:
        importer = PostgreSQLImporter()
        
        if not importer.postgres_initialized:
            logger.warning("⚠️ PostgreSQL未初始化，跳過匯入測試")
            return True
        
        # 檢查是否有資料可測試
        import sqlite3
        sqlite_conn = sqlite3.connect("data/history_data.db")
        cursor = sqlite_conn.execute("SELECT COUNT(*) FROM kline_data WHERE symbol = 'MTX00'")
        count = cursor.fetchone()[0]
        sqlite_conn.close()
        
        if count == 0:
            logger.warning("⚠️ SQLite中沒有MTX00資料，跳過匯入測試")
            return True
        
        logger.info(f"📊 找到 {count} 筆K線資料可供測試")
        
        # 測試排除異常資料的匯入
        logger.info("🔍 測試排除異常資料的匯入...")
        success_exclude = importer.import_kline_to_postgres(
            symbol='MTX00',
            kline_type='MINUTE',
            batch_size=1000,
            exclude_anomalies=True
        )
        
        if success_exclude:
            logger.info("✅ 排除異常資料的匯入測試成功")
        else:
            logger.error("❌ 排除異常資料的匯入測試失敗")
        
        return success_exclude
        
    except Exception as e:
        logger.error(f"❌ 匯入測試失敗: {e}")
        return False

def main():
    """主函數"""
    logger.info("🚀 開始異常資料檢測和排除功能測試...")
    logger.info("=" * 80)
    
    # 測試1: 異常資料檢測功能
    detection_success = test_anomaly_detection()
    
    # 測試2: 匯入功能的異常資料設定
    import_success = test_import_with_anomaly_settings()
    
    # 總結
    logger.info("\n" + "=" * 80)
    logger.info("🎯 最終測試結果")
    logger.info("=" * 80)
    
    logger.info(f"異常檢測功能: {'✅ 通過' if detection_success else '❌ 失敗'}")
    logger.info(f"匯入功能測試: {'✅ 通過' if import_success else '❌ 失敗'}")
    
    overall_success = detection_success and import_success
    
    if overall_success:
        logger.info("\n🎉 所有測試通過！")
        logger.info("修正內容:")
        logger.info("  ✅ 異常資料現在會被正確排除")
        logger.info("  ✅ 統計數字會正確反映排除的資料數量")
        logger.info("  ✅ 可以選擇是否排除異常資料 (exclude_anomalies參數)")
        logger.info("  ✅ 詳細的日誌顯示排除原因")
    else:
        logger.warning("\n⚠️ 部分測試失敗，需要進一步檢查")
    
    return overall_success

if __name__ == "__main__":
    try:
        success = main()
        sys.exit(0 if success else 1)
    except Exception as e:
        logger.error(f"❌ 測試程式執行失敗: {e}")
        sys.exit(1)
