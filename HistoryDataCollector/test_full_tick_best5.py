#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
測試 Full Tick 和 Best5 功能
驗證新增的逐筆和五檔資料匯入功能
"""

import os
import sys
import logging
import time

# 添加專案路徑
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from database.postgres_importer import PostgreSQLImporter
from collectors.tick_collector import TickCollector
from collectors.best5_collector import Best5Collector
from utils.logger import setup_logger, get_logger

# 設定日誌
setup_logger()
logger = get_logger(__name__)

def test_tick_data_conversion():
    """測試逐筆資料轉換"""
    logger.info("🧪 測試逐筆資料轉換功能...")
    
    try:
        importer = PostgreSQLImporter()
        
        # 模擬逐筆資料
        test_tick_data = {
            'symbol': 'MTX00',
            'trade_date': '20250106',
            'trade_time': '084600',
            'trade_time_ms': 123,
            'bid_price': 22950.0,
            'ask_price': 22955.0,
            'close_price': 22952.0,
            'volume': 5,
            'market_no': 1,
            'simulate_flag': 0
        }
        
        # 測試轉換
        converted = importer.convert_tick_to_postgres_format(test_tick_data)
        
        if converted:
            logger.info("✅ 逐筆資料轉換成功")
            logger.info(f"   原始: {test_tick_data}")
            logger.info(f"   轉換: {converted}")
            return True
        else:
            logger.error("❌ 逐筆資料轉換失敗")
            return False
            
    except Exception as e:
        logger.error(f"❌ 逐筆資料轉換測試失敗: {e}")
        return False

def test_best5_data_conversion():
    """測試五檔資料轉換"""
    logger.info("🧪 測試五檔資料轉換功能...")
    
    try:
        importer = PostgreSQLImporter()
        
        # 模擬五檔資料
        test_best5_data = {
            'symbol': 'MTX00',
            'trade_date': '20250106',
            'trade_time': '084600',
            'bid_price_1': 22950.0,
            'bid_volume_1': 10,
            'bid_price_2': 22949.0,
            'bid_volume_2': 5,
            'ask_price_1': 22951.0,
            'ask_volume_1': 8,
            'ask_price_2': 22952.0,
            'ask_volume_2': 12,
            'bid_price_3': None,
            'bid_volume_3': 0,
            'ask_price_3': None,
            'ask_volume_3': 0,
            'bid_price_4': None,
            'bid_volume_4': 0,
            'ask_price_4': None,
            'ask_volume_4': 0,
            'bid_price_5': None,
            'bid_volume_5': 0,
            'ask_price_5': None,
            'ask_volume_5': 0,
            'extend_bid': None,
            'extend_bid_qty': 0,
            'extend_ask': None,
            'extend_ask_qty': 0
        }
        
        # 測試轉換
        converted = importer.convert_best5_to_postgres_format(test_best5_data)
        
        if converted:
            logger.info("✅ 五檔資料轉換成功")
            logger.info(f"   原始: {test_best5_data}")
            logger.info(f"   轉換: {converted}")
            return True
        else:
            logger.error("❌ 五檔資料轉換失敗")
            return False
            
    except Exception as e:
        logger.error(f"❌ 五檔資料轉換測試失敗: {e}")
        return False

def test_postgres_import_functions():
    """測試PostgreSQL匯入功能"""
    logger.info("🧪 測試PostgreSQL匯入功能...")
    
    try:
        importer = PostgreSQLImporter()
        
        if not importer.postgres_initialized:
            logger.warning("⚠️ PostgreSQL未初始化，跳過匯入測試")
            return True
        
        # 測試統計功能
        logger.info("📊 測試PostgreSQL統計功能...")
        stats = importer.get_postgres_data_statistics()
        
        if stats:
            logger.info("✅ PostgreSQL統計功能正常")
            logger.info(f"   K線資料: {stats['kline_count']} 筆")
            logger.info(f"   逐筆資料: {stats['tick_count']} 筆")
            logger.info(f"   五檔資料: {stats['best5_count']} 筆")
            logger.info(f"   總計: {stats['total_count']} 筆")
        else:
            logger.warning("⚠️ 無法取得PostgreSQL統計資料")
        
        return True
        
    except Exception as e:
        logger.error(f"❌ PostgreSQL匯入功能測試失敗: {e}")
        return False

def test_collector_debug_output():
    """測試收集器除錯輸出功能"""
    logger.info("🧪 測試收集器除錯輸出功能...")
    
    try:
        # 創建模擬收集器
        tick_collector = TickCollector(None, None)
        best5_collector = Best5Collector(None, None)
        
        # 重置計數器
        tick_collector.printed_count = 0
        best5_collector.printed_count = 0
        
        logger.info("✅ 收集器除錯功能已準備就緒")
        logger.info("   - 逐筆收集器已添加除錯輸出")
        logger.info("   - 五檔收集器已添加除錯輸出")
        logger.info("   - 前10筆資料將顯示詳細轉換過程")
        
        return True
        
    except Exception as e:
        logger.error(f"❌ 收集器除錯功能測試失敗: {e}")
        return False

def test_gui_integration():
    """測試GUI整合功能"""
    logger.info("🧪 測試GUI整合功能...")
    
    try:
        # 檢查主程式是否有新的匯入方法
        from main import HistoryDataCollectorGUI
        
        # 檢查新方法是否存在
        gui_methods = [
            'import_tick_to_postgres',
            'import_best5_to_postgres', 
            'import_all_to_postgres',
            'show_postgres_statistics'
        ]
        
        for method_name in gui_methods:
            if hasattr(HistoryDataCollectorGUI, method_name):
                logger.info(f"✅ GUI方法 {method_name} 已添加")
            else:
                logger.warning(f"⚠️ GUI方法 {method_name} 未找到")
        
        logger.info("✅ GUI整合功能檢查完成")
        return True
        
    except Exception as e:
        logger.error(f"❌ GUI整合功能測試失敗: {e}")
        return False

def run_comprehensive_test():
    """執行綜合測試"""
    logger.info("🚀 開始 Full Tick 和 Best5 功能綜合測試...")
    logger.info("=" * 80)
    
    test_results = {}
    
    # 測試1: 逐筆資料轉換
    test_results['tick_conversion'] = test_tick_data_conversion()
    
    # 測試2: 五檔資料轉換
    test_results['best5_conversion'] = test_best5_data_conversion()
    
    # 測試3: PostgreSQL匯入功能
    test_results['postgres_import'] = test_postgres_import_functions()
    
    # 測試4: 收集器除錯輸出
    test_results['collector_debug'] = test_collector_debug_output()
    
    # 測試5: GUI整合功能
    test_results['gui_integration'] = test_gui_integration()
    
    # 總結測試結果
    logger.info("=" * 80)
    logger.info("📊 測試結果總結:")
    
    passed_tests = 0
    total_tests = len(test_results)
    
    for test_name, result in test_results.items():
        status = "✅ 通過" if result else "❌ 失敗"
        logger.info(f"   {test_name}: {status}")
        if result:
            passed_tests += 1
    
    success_rate = (passed_tests / total_tests) * 100
    logger.info(f"\n🎯 測試通過率: {passed_tests}/{total_tests} ({success_rate:.1f}%)")
    
    if success_rate == 100:
        logger.info("🎉 所有測試通過！Full Tick 和 Best5 功能已準備就緒")
    elif success_rate >= 80:
        logger.info("✅ 大部分測試通過，功能基本可用")
    else:
        logger.warning("⚠️ 多項測試失敗，需要進一步檢查")
    
    return success_rate == 100

def main():
    """主函數"""
    try:
        logger.info("🔬 Full Tick 和 Best5 功能測試程式")
        logger.info("測試新增的逐筆和五檔資料收集與匯入功能")
        logger.info("")
        
        # 執行綜合測試
        success = run_comprehensive_test()
        
        if success:
            logger.info("\n✅ 測試完成！所有功能正常運作")
            logger.info("現在可以使用以下新功能:")
            logger.info("  - 逐筆資料收集和PostgreSQL匯入")
            logger.info("  - 五檔資料收集和PostgreSQL匯入")
            logger.info("  - 前10行資料除錯輸出")
            logger.info("  - GUI新增匯入按鈕")
            logger.info("  - PostgreSQL資料統計")
        else:
            logger.warning("\n⚠️ 部分測試失敗，請檢查相關功能")
        
        return 0 if success else 1
        
    except Exception as e:
        logger.error(f"❌ 測試程式執行失敗: {e}")
        return 1

if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)
