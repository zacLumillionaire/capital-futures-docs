#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
快速匯入測試
測試優化後的PostgreSQL匯入性能
"""

import os
import sys
import time
import logging

# 添加專案路徑
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from database.postgres_importer import PostgreSQLImporter
from utils.logger import setup_logger, get_logger

# 設定日誌
setup_logger()
logger = get_logger(__name__)

def test_optimized_import():
    """測試優化後的匯入性能"""
    logger.info("🚀 開始測試優化後的PostgreSQL匯入性能...")
    
    try:
        # 創建匯入器
        importer = PostgreSQLImporter()
        
        if not importer.postgres_initialized:
            logger.error("❌ PostgreSQL未初始化，無法進行測試")
            return False
        
        # 記錄開始時間
        start_time = time.time()
        
        # 執行匯入 - 使用優化參數
        logger.info("📊 開始匯入，使用以下優化設定:")
        logger.info("  - batch_size: 5000 (原本1000)")
        logger.info("  - optimize_performance: True")
        logger.info("  - 使用 execute_values 進行高效插入")
        
        success = importer.import_kline_to_postgres(
            symbol='MTX00',
            kline_type='MINUTE',
            batch_size=5000,
            optimize_performance=True
        )
        
        # 計算總耗時
        total_time = time.time() - start_time
        
        if success:
            logger.info("✅ 匯入測試完成！")
            logger.info(f"📊 總耗時: {total_time:.2f}秒")
            
            # 與原本5分鐘比較
            original_time = 5 * 60  # 5分鐘 = 300秒
            if total_time < original_time:
                improvement = original_time / total_time
                logger.info(f"🚀 性能提升: {improvement:.1f}倍")
                logger.info(f"   從 {original_time/60:.1f}分鐘 縮短到 {total_time:.1f}秒")
            
            # 檢查匯入結果
            if importer.check_postgres_data():
                logger.info("✅ 資料驗證通過")
            
            return True
        else:
            logger.error("❌ 匯入測試失敗")
            return False
            
    except Exception as e:
        logger.error(f"❌ 測試過程中發生錯誤: {e}", exc_info=True)
        return False

def test_copy_import():
    """測試COPY命令匯入 (如果可用)"""
    logger.info("🧪 測試COPY命令匯入...")
    
    try:
        importer = PostgreSQLImporter()
        
        if not importer.postgres_initialized:
            logger.error("❌ PostgreSQL未初始化")
            return False
        
        start_time = time.time()
        
        # 嘗試使用COPY命令
        success = importer.import_kline_to_postgres(
            symbol='MTX00',
            kline_type='MINUTE',
            use_copy=True
        )
        
        total_time = time.time() - start_time
        
        if success:
            logger.info(f"✅ COPY命令匯入完成: {total_time:.2f}秒")
            return True
        else:
            logger.warning("⚠️ COPY命令匯入失敗，可能不支援")
            return False
            
    except Exception as e:
        logger.warning(f"⚠️ COPY命令測試失敗: {e}")
        return False

def show_optimization_tips():
    """顯示優化建議"""
    logger.info("\n" + "="*60)
    logger.info("💡 PostgreSQL匯入性能優化建議")
    logger.info("="*60)
    
    tips = [
        "1. 使用更大的批次大小 (5000-10000)",
        "2. 啟用 execute_values 進行高效批量插入",
        "3. 暫時關閉同步提交 (synchronous_commit = OFF)",
        "4. 增加工作記憶體 (work_mem = 256MB)",
        "5. 預先轉換所有資料，避免在插入循環中轉換",
        "6. 減少日誌輸出頻率",
        "7. 考慮使用COPY命令進行超高速匯入",
        "8. 在匯入前暫時移除非必要索引"
    ]
    
    for tip in tips:
        logger.info(f"  {tip}")
    
    logger.info("\n預期性能提升:")
    logger.info("  - 簡單優化: 10-50倍提升")
    logger.info("  - execute_values: 50-100倍提升") 
    logger.info("  - COPY命令: 100-300倍提升")

def main():
    """主函數"""
    logger.info("🔬 PostgreSQL匯入性能優化測試")
    logger.info("="*60)
    
    # 顯示優化建議
    show_optimization_tips()
    
    # 測試優化後的匯入
    logger.info("\n" + "="*60)
    logger.info("測試1: 優化後的批量匯入")
    logger.info("="*60)
    
    success1 = test_optimized_import()
    
    # 測試COPY命令匯入
    logger.info("\n" + "="*60)
    logger.info("測試2: COPY命令匯入")
    logger.info("="*60)
    
    success2 = test_copy_import()
    
    # 總結
    logger.info("\n" + "="*60)
    logger.info("測試結果總結")
    logger.info("="*60)
    
    logger.info(f"優化批量匯入: {'✅ 成功' if success1 else '❌ 失敗'}")
    logger.info(f"COPY命令匯入: {'✅ 成功' if success2 else '❌ 失敗'}")
    
    if success1 or success2:
        logger.info("\n🎉 恭喜！至少有一種優化方法成功")
        logger.info("建議在實際使用中採用成功的方法")
    else:
        logger.warning("\n⚠️ 所有測試都失敗了")
        logger.warning("請檢查PostgreSQL連接和資料庫設定")
    
    logger.info("\n✅ 測試完成")

if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        logger.error(f"❌ 測試程式執行失敗: {e}", exc_info=True)
        sys.exit(1)
