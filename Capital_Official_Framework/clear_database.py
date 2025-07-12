#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
清空多組策略資料庫
用於重新測試
"""

import os
import sqlite3
import logging
from datetime import datetime

# 設置日誌
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def clear_multi_group_database():
    """清空多組策略資料庫"""
    try:
        # 資料庫路徑
        db_path = "multi_group_strategy.db"
        
        if not os.path.exists(db_path):
            logger.info("❌ 資料庫文件不存在")
            return False
        
        # 備份當前資料庫
        backup_path = f"multi_group_strategy_backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}.db"
        
        # 連接資料庫
        with sqlite3.connect(db_path) as conn:
            cursor = conn.cursor()
            
            # 1. 備份到新文件
            backup_conn = sqlite3.connect(backup_path)
            conn.backup(backup_conn)
            backup_conn.close()
            logger.info(f"✅ 資料庫已備份到: {backup_path}")
            
            # 2. 清空所有表的數據
            tables_to_clear = [
                'strategy_groups',
                'position_records', 
                'risk_management_states',
                'daily_strategy_stats'
            ]
            
            for table in tables_to_clear:
                try:
                    # 檢查表是否存在
                    cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name=?", (table,))
                    if cursor.fetchone():
                        cursor.execute(f"DELETE FROM {table}")
                        count = cursor.rowcount
                        logger.info(f"✅ 清空表 {table}: 刪除 {count} 筆記錄")
                    else:
                        logger.info(f"⚠️ 表 {table} 不存在")
                except Exception as e:
                    logger.error(f"❌ 清空表 {table} 失敗: {e}")
            
            # 3. 重置自增ID
            for table in tables_to_clear:
                try:
                    cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name=?", (table,))
                    if cursor.fetchone():
                        cursor.execute(f"DELETE FROM sqlite_sequence WHERE name='{table}'")
                        logger.info(f"✅ 重置表 {table} 的自增ID")
                except Exception as e:
                    logger.warning(f"⚠️ 重置表 {table} 自增ID失敗: {e}")
            
            # 4. 提交更改
            conn.commit()
            logger.info("✅ 所有更改已提交")
            
            # 5. 驗證清空結果
            logger.info("\n📊 清空後的表狀態:")
            for table in tables_to_clear:
                try:
                    cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name=?", (table,))
                    if cursor.fetchone():
                        cursor.execute(f"SELECT COUNT(*) FROM {table}")
                        count = cursor.fetchone()[0]
                        logger.info(f"   {table}: {count} 筆記錄")
                except Exception as e:
                    logger.error(f"   {table}: 檢查失敗 - {e}")
        
        logger.info("\n🎉 資料庫清空完成！")
        logger.info(f"📁 備份文件: {backup_path}")
        logger.info("🚀 現在可以重新測試了")
        
        return True
        
    except Exception as e:
        logger.error(f"❌ 清空資料庫失敗: {e}")
        return False

def clear_position_management_database():
    """清空部位管理資料庫（如果存在）"""
    try:
        db_path = "position_management.db"
        
        if not os.path.exists(db_path):
            logger.info("ℹ️ 部位管理資料庫不存在，跳過")
            return True
        
        with sqlite3.connect(db_path) as conn:
            cursor = conn.cursor()
            
            # 清空部位管理相關表
            position_tables = [
                'positions',
                'trading_sessions', 
                'stop_loss_adjustments',
                'position_snapshots'
            ]
            
            for table in position_tables:
                try:
                    cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name=?", (table,))
                    if cursor.fetchone():
                        cursor.execute(f"DELETE FROM {table}")
                        count = cursor.rowcount
                        logger.info(f"✅ 清空部位管理表 {table}: 刪除 {count} 筆記錄")
                except Exception as e:
                    logger.warning(f"⚠️ 清空部位管理表 {table} 失敗: {e}")
            
            conn.commit()
            logger.info("✅ 部位管理資料庫清空完成")
        
        return True
        
    except Exception as e:
        logger.error(f"❌ 清空部位管理資料庫失敗: {e}")
        return False

if __name__ == "__main__":
    print("🧹 開始清空資料庫...")
    print("=" * 50)
    
    # 清空多組策略資料庫
    success1 = clear_multi_group_database()
    
    print("\n" + "=" * 50)
    
    # 清空部位管理資料庫
    success2 = clear_position_management_database()
    
    print("\n" + "=" * 50)
    
    if success1 and success2:
        print("🎉 所有資料庫清空完成！")
        print("🚀 現在可以重新測試建倉機制了")
    else:
        print("❌ 部分資料庫清空失敗，請檢查錯誤訊息")
    
    input("\n按 Enter 鍵退出...")
