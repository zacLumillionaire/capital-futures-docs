#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
資料收集並自動匯入PostgreSQL工具
用於收集期貨歷史資料並自動匯入到PostgreSQL資料庫
"""

import argparse
import logging
import sys
import os
from datetime import datetime, timedelta

# 添加專案路徑
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from database.db_manager import DatabaseManager
from utils.skcom_manager import SKCOMManager
from collectors.kline_collector import KLineCollector
from database.postgres_importer import PostgreSQLImporter

# 設定日誌
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/collect_and_import.log', encoding='utf-8'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class CollectAndImportTool:
    """資料收集並自動匯入工具"""
    
    def __init__(self):
        """初始化工具"""
        self.db_manager = None
        self.skcom_manager = None
        self.kline_collector = None
        self.postgres_importer = None
        
    def initialize(self):
        """初始化所有元件"""
        try:
            logger.info("🚀 初始化資料收集並匯入工具...")
            
            # 初始化資料庫管理器
            self.db_manager = DatabaseManager()
            logger.info("✅ 資料庫管理器初始化完成")
            
            # 初始化SKCOM管理器
            self.skcom_manager = SKCOMManager()
            
            if not self.skcom_manager.initialize_skcom():
                raise Exception("SKCOM API初始化失敗")
            
            if not self.skcom_manager.initialize_skcom_objects():
                raise Exception("SKCOM物件初始化失敗")
            
            logger.info("✅ SKCOM API初始化完成")
            
            # 初始化K線收集器
            self.kline_collector = KLineCollector(self.db_manager, self.skcom_manager)
            logger.info("✅ K線收集器初始化完成")
            
            # 初始化PostgreSQL匯入器
            self.postgres_importer = PostgreSQLImporter()
            logger.info("✅ PostgreSQL匯入器初始化完成")
            
            logger.info("✅ 所有元件初始化完成")
            return True
            
        except Exception as e:
            logger.error(f"❌ 初始化失敗: {e}")
            return False
    
    def login(self, user_id, password):
        """登入群益API"""
        try:
            logger.info("🔐 開始登入群益API...")
            
            if not self.skcom_manager.login(user_id, password):
                logger.error("❌ 登入失敗")
                return False
            
            logger.info("✅ 登入成功")
            
            # 連線報價主機
            logger.info("📡 連線報價主機...")
            if not self.skcom_manager.connect_quote_server():
                logger.error("❌ 連線報價主機失敗")
                return False
            
            logger.info("✅ 報價主機連線成功")
            return True
            
        except Exception as e:
            logger.error(f"❌ 登入過程發生錯誤: {e}")
            return False
    
    def collect_data(self, symbol, kline_type, start_date, end_date, trading_session='DAY'):
        """收集K線資料"""
        try:
            logger.info(f"📊 開始收集 {symbol} {kline_type} K線資料...")
            logger.info(f"📅 日期範圍: {start_date} ~ {end_date}")
            logger.info(f"🕐 交易時段: {trading_session}")
            
            # 開始收集K線資料
            success = self.kline_collector.start_collection(
                symbol=symbol,
                kline_type=kline_type,
                start_date=start_date,
                end_date=end_date,
                trading_session=trading_session
            )
            
            if not success:
                logger.error("❌ K線資料收集失敗")
                return False
            
            # 等待收集完成
            logger.info("⏳ 等待資料收集完成...")
            import time
            time.sleep(5)  # 等待資料收集
            
            # 檢查收集結果
            stats = self.db_manager.get_data_statistics(symbol)
            logger.info(f"✅ 資料收集完成 - K線: {stats['kline_count']} 筆")
            
            return stats['kline_count'] > 0
            
        except Exception as e:
            logger.error(f"❌ 資料收集失敗: {e}")
            return False
    
    def import_to_postgres(self, symbol, kline_type):
        """匯入資料到PostgreSQL"""
        try:
            logger.info("🚀 開始匯入資料到PostgreSQL...")
            
            # 檢查PostgreSQL連接
            if not self.postgres_importer.check_connections():
                logger.error("❌ PostgreSQL連接檢查失敗")
                return False
            
            # 執行匯入
            success = self.postgres_importer.import_kline_to_postgres(
                symbol=symbol,
                kline_type=kline_type,
                batch_size=100
            )
            
            if success:
                logger.info("✅ PostgreSQL匯入完成")
                return True
            else:
                logger.error("❌ PostgreSQL匯入失敗")
                return False
                
        except Exception as e:
            logger.error(f"❌ PostgreSQL匯入過程發生錯誤: {e}")
            return False
    
    def run(self, user_id, password, symbol, kline_type, start_date, end_date, 
            trading_session='DAY', auto_import=True):
        """執行完整的收集和匯入流程"""
        try:
            # 1. 初始化
            if not self.initialize():
                return False
            
            # 2. 登入
            if not self.login(user_id, password):
                return False
            
            # 3. 收集資料
            if not self.collect_data(symbol, kline_type, start_date, end_date, trading_session):
                return False
            
            # 4. 自動匯入（如果啟用）
            if auto_import:
                if not self.import_to_postgres(symbol, kline_type):
                    logger.warning("⚠️ 自動匯入失敗，但資料收集成功")
                    return True  # 收集成功，匯入失敗不算整體失敗
            
            logger.info("🎉 完整流程執行成功！")
            return True
            
        except Exception as e:
            logger.error(f"❌ 執行流程時發生錯誤: {e}")
            return False
        finally:
            # 清理資源
            if self.skcom_manager:
                self.skcom_manager.cleanup()

def main():
    """主程式"""
    parser = argparse.ArgumentParser(description='期貨歷史資料收集並自動匯入PostgreSQL工具')
    
    # 登入參數
    parser.add_argument('--user-id', required=True, help='群益證券帳號')
    parser.add_argument('--password', required=True, help='群益證券密碼')
    
    # 收集參數
    parser.add_argument('--symbol', default='MTX00', help='商品代碼 (預設: MTX00)')
    parser.add_argument('--kline-type', default='MINUTE', 
                       choices=['MINUTE', 'DAILY', 'WEEKLY', 'MONTHLY'],
                       help='K線類型 (預設: MINUTE)')
    parser.add_argument('--start-date', required=True, help='開始日期 (YYYYMMDD)')
    parser.add_argument('--end-date', required=True, help='結束日期 (YYYYMMDD)')
    parser.add_argument('--trading-session', default='DAY',
                       choices=['DAY', 'NIGHT', 'ALL'],
                       help='交易時段 (預設: DAY)')
    
    # 匯入參數
    parser.add_argument('--no-auto-import', action='store_true',
                       help='不自動匯入到PostgreSQL')
    
    args = parser.parse_args()
    
    # 建立工具實例
    tool = CollectAndImportTool()
    
    # 執行流程
    success = tool.run(
        user_id=args.user_id,
        password=args.password,
        symbol=args.symbol,
        kline_type=args.kline_type,
        start_date=args.start_date,
        end_date=args.end_date,
        trading_session=args.trading_session,
        auto_import=not args.no_auto_import
    )
    
    return 0 if success else 1

if __name__ == "__main__":
    sys.exit(main())
