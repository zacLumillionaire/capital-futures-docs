#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
匯入K線資料到PostgreSQL主程式
將SQLite中的K線資料匯入到PostgreSQL的stock_price表
"""

import os
import sys
import logging
import argparse

# 添加專案路徑
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from utils.logger import setup_logger
from database.postgres_importer import PostgreSQLImporter

# 設定日誌
setup_logger()
logger = logging.getLogger(__name__)

def main():
    """主函數"""
    parser = argparse.ArgumentParser(description='匯入K線資料到PostgreSQL')
    parser.add_argument('--symbol', default='MTX00', help='商品代碼 (預設: MTX00)')
    parser.add_argument('--kline-type', default='MINUTE', 
                       choices=['MINUTE', 'DAILY', 'WEEKLY', 'MONTHLY'],
                       help='K線類型 (預設: MINUTE)')
    parser.add_argument('--batch-size', type=int, default=1000, help='批量處理大小 (預設: 1000)')
    parser.add_argument('--check-only', action='store_true', help='只檢查資料，不執行匯入')
    
    args = parser.parse_args()
    
    logger.info("🚀 PostgreSQL匯入工具啟動")
    logger.info("="*60)
    
    try:
        # 初始化匯入器
        importer = PostgreSQLImporter()
        
        # 檢查SQLite資料
        logger.info("🔍 檢查SQLite資料庫...")
        sqlite_data = importer.check_sqlite_data()
        
        if sqlite_data is None:
            logger.error("❌ SQLite資料庫中沒有可匯入的資料")
            return 1
        
        # 檢查PostgreSQL連接
        logger.info("🔍 檢查PostgreSQL連接...")
        if not importer.postgres_initialized:
            logger.error("❌ PostgreSQL連接失敗")
            return 1
        
        # 檢查PostgreSQL現有資料
        logger.info("🔍 檢查PostgreSQL現有資料...")
        importer.check_postgres_data()
        
        if args.check_only:
            logger.info("✅ 檢查完成（僅檢查模式）")
            return 0
        
        # 確認匯入
        print(f"\n📋 即將匯入設定:")
        print(f"  - 商品代碼: {args.symbol}")
        print(f"  - K線類型: {args.kline_type}")
        print(f"  - 批量大小: {args.batch_size}")
        
        confirm = input("\n❓ 確定要開始匯入嗎？(y/N): ").strip().lower()
        if confirm != 'y':
            logger.info("❌ 使用者取消匯入")
            return 0
        
        # 執行匯入
        logger.info("🚀 開始執行匯入...")
        success = importer.import_kline_to_postgres(
            symbol=args.symbol,
            kline_type=args.kline_type,
            batch_size=args.batch_size
        )
        
        if success:
            logger.info("✅ 匯入完成！")
            
            # 再次檢查PostgreSQL資料
            logger.info("🔍 檢查匯入後的PostgreSQL資料...")
            importer.check_postgres_data()
            
            return 0
        else:
            logger.error("❌ 匯入失敗")
            return 1
            
    except KeyboardInterrupt:
        logger.info("❌ 使用者中斷程式")
        return 1
    except Exception as e:
        logger.error(f"❌ 程式執行失敗: {e}", exc_info=True)
        return 1

if __name__ == "__main__":
    try:
        exit_code = main()
        sys.exit(exit_code)
    except Exception as e:
        logger.error(f"❌ 程式啟動失敗: {e}")
        sys.exit(1)
