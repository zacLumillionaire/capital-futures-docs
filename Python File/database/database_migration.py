#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
資料庫遷移腳本
安全地升級資料庫結構，新增部位管理功能
確保不影響現有資料和功能
"""

import sqlite3
import logging
import os
import sys
from datetime import datetime
from typing import List, Dict, Any, Optional, Tuple
from contextlib import contextmanager

# 添加當前目錄到路徑，以便導入其他模組
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

try:
    from position_tables_schema import PositionTableSQL
except ImportError:
    print("❌ 無法導入 position_tables_schema，請確認檔案存在")
    sys.exit(1)

logger = logging.getLogger(__name__)

class DatabaseMigration:
    """資料庫遷移管理器"""
    
    def __init__(self, db_path: str = "strategy_trading.db"):
        """
        初始化遷移管理器
        
        Args:
            db_path: 資料庫檔案路徑
        """
        self.db_path = db_path
        self.backup_path = f"{db_path}.backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        
        # 定義遷移版本
        self.current_version = self.get_database_version()
        self.target_version = "1.1.0"  # 部位管理功能版本
        
        logger.info(f"資料庫路徑: {self.db_path}")
        logger.info(f"當前版本: {self.current_version}")
        logger.info(f"目標版本: {self.target_version}")
    
    @contextmanager
    def get_connection(self):
        """取得資料庫連線的上下文管理器"""
        conn = None
        try:
            conn = sqlite3.connect(self.db_path)
            conn.row_factory = sqlite3.Row  # 讓查詢結果可以用欄位名稱存取
            yield conn
        except Exception as e:
            if conn:
                conn.rollback()
            logger.error(f"資料庫連線錯誤: {e}")
            raise
        finally:
            if conn:
                conn.close()
    
    def get_database_version(self) -> str:
        """取得當前資料庫版本"""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                
                # 檢查是否有版本表
                cursor.execute("""
                    SELECT name FROM sqlite_master 
                    WHERE type='table' AND name='database_version'
                """)
                
                if cursor.fetchone():
                    cursor.execute("SELECT version FROM database_version ORDER BY id DESC LIMIT 1")
                    result = cursor.fetchone()
                    return result[0] if result else "1.0.0"
                else:
                    return "1.0.0"  # 預設版本
                    
        except Exception as e:
            logger.warning(f"無法取得資料庫版本: {e}")
            return "1.0.0"
    
    def create_version_table(self):
        """創建版本管理表"""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS database_version (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        version TEXT NOT NULL,
                        description TEXT,
                        migration_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    )
                ''')
                
                # 如果是新建表，插入初始版本記錄
                cursor.execute("SELECT COUNT(*) FROM database_version")
                if cursor.fetchone()[0] == 0:
                    cursor.execute("""
                        INSERT INTO database_version (version, description) 
                        VALUES ('1.0.0', '初始版本 - 基礎策略交易功能')
                    """)
                
                conn.commit()
                logger.info("✅ 版本管理表創建完成")
                
        except Exception as e:
            logger.error(f"❌ 創建版本表失敗: {e}")
            raise
    
    def backup_database(self) -> bool:
        """備份現有資料庫"""
        try:
            if not os.path.exists(self.db_path):
                logger.info("資料庫檔案不存在，跳過備份")
                return True
            
            # 使用SQLite的備份API
            with sqlite3.connect(self.db_path) as source:
                with sqlite3.connect(self.backup_path) as backup:
                    source.backup(backup)
            
            logger.info(f"✅ 資料庫備份完成: {self.backup_path}")
            return True
            
        except Exception as e:
            logger.error(f"❌ 資料庫備份失敗: {e}")
            return False
    
    def check_table_exists(self, table_name: str) -> bool:
        """檢查表格是否存在"""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    SELECT name FROM sqlite_master 
                    WHERE type='table' AND name=?
                """, (table_name,))
                
                return cursor.fetchone() is not None
                
        except Exception as e:
            logger.error(f"檢查表格 {table_name} 時發生錯誤: {e}")
            return False
    
    def get_existing_tables(self) -> List[str]:
        """取得現有表格列表"""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    SELECT name FROM sqlite_master 
                    WHERE type='table' AND name NOT LIKE 'sqlite_%'
                    ORDER BY name
                """)
                
                return [row[0] for row in cursor.fetchall()]
                
        except Exception as e:
            logger.error(f"取得表格列表時發生錯誤: {e}")
            return []

    def validate_existing_data(self) -> bool:
        """驗證現有資料的完整性"""
        try:
            existing_tables = self.get_existing_tables()
            logger.info(f"現有表格: {existing_tables}")

            # 檢查關鍵表格的資料完整性
            with self.get_connection() as conn:
                cursor = conn.cursor()

                for table in existing_tables:
                    if table == 'database_version':
                        continue

                    # 檢查表格是否可以正常查詢
                    cursor.execute(f"SELECT COUNT(*) FROM {table}")
                    count = cursor.fetchone()[0]
                    logger.info(f"表格 {table}: {count} 筆記錄")

                logger.info("✅ 現有資料驗證完成")
                return True

        except Exception as e:
            logger.error(f"❌ 資料驗證失敗: {e}")
            return False

    def create_position_tables(self) -> bool:
        """創建部位管理相關表格"""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()

                # 定義要創建的表格
                tables_to_create = [
                    ("positions", PositionTableSQL.CREATE_POSITIONS_TABLE),
                    ("stop_loss_adjustments", PositionTableSQL.CREATE_STOP_LOSS_ADJUSTMENTS_TABLE),
                    ("position_snapshots", PositionTableSQL.CREATE_POSITION_SNAPSHOTS_TABLE),
                    ("trading_sessions", PositionTableSQL.CREATE_TRADING_SESSIONS_TABLE)
                ]

                created_tables = []

                for table_name, create_sql in tables_to_create:
                    if self.check_table_exists(table_name):
                        logger.info(f"⚠️  表格 {table_name} 已存在，跳過創建")
                        continue

                    try:
                        cursor.execute(create_sql)
                        created_tables.append(table_name)
                        logger.info(f"✅ 表格 {table_name} 創建成功")

                    except Exception as e:
                        logger.error(f"❌ 創建表格 {table_name} 失敗: {e}")
                        return False

                conn.commit()

                if created_tables:
                    logger.info(f"✅ 成功創建 {len(created_tables)} 個新表格: {created_tables}")
                else:
                    logger.info("ℹ️  所有表格都已存在，無需創建")

                return True

        except Exception as e:
            logger.error(f"❌ 創建部位表格失敗: {e}")
            return False

    def create_indexes(self) -> bool:
        """創建索引以提升查詢效能"""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()

                created_indexes = []

                for index_sql in PositionTableSQL.CREATE_INDEXES:
                    try:
                        cursor.execute(index_sql)
                        # 從SQL中提取索引名稱
                        index_name = index_sql.split("IF NOT EXISTS ")[1].split(" ON ")[0]
                        created_indexes.append(index_name)

                    except Exception as e:
                        logger.warning(f"創建索引時發生警告: {e}")
                        # 索引創建失敗不是致命錯誤，繼續執行
                        continue

                conn.commit()
                logger.info(f"✅ 成功創建 {len(created_indexes)} 個索引")
                return True

        except Exception as e:
            logger.error(f"❌ 創建索引失敗: {e}")
            return False

    def create_triggers(self) -> bool:
        """創建觸發器以自動維護資料一致性"""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()

                created_triggers = []

                for trigger_sql in PositionTableSQL.CREATE_TRIGGERS:
                    try:
                        cursor.execute(trigger_sql)
                        # 從SQL中提取觸發器名稱
                        trigger_name = trigger_sql.split("IF NOT EXISTS ")[1].split(" ")[0]
                        created_triggers.append(trigger_name)

                    except Exception as e:
                        logger.warning(f"創建觸發器時發生警告: {e}")
                        # 觸發器創建失敗不是致命錯誤，繼續執行
                        continue

                conn.commit()
                logger.info(f"✅ 成功創建 {len(created_triggers)} 個觸發器")
                return True

        except Exception as e:
            logger.error(f"❌ 創建觸發器失敗: {e}")
            return False

    def update_database_version(self) -> bool:
        """更新資料庫版本記錄"""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()

                cursor.execute("""
                    INSERT INTO database_version (version, description)
                    VALUES (?, ?)
                """, (self.target_version, "新增部位管理功能 - positions, stop_loss_adjustments, position_snapshots, trading_sessions"))

                conn.commit()
                logger.info(f"✅ 資料庫版本更新為: {self.target_version}")
                return True

        except Exception as e:
            logger.error(f"❌ 更新資料庫版本失敗: {e}")
            return False

    def verify_migration(self) -> bool:
        """驗證遷移結果"""
        try:
            # 檢查新表格是否都存在
            required_tables = ["positions", "stop_loss_adjustments", "position_snapshots", "trading_sessions"]

            for table in required_tables:
                if not self.check_table_exists(table):
                    logger.error(f"❌ 驗證失敗: 表格 {table} 不存在")
                    return False

            # 檢查版本是否正確更新
            current_version = self.get_database_version()
            if current_version != self.target_version:
                logger.error(f"❌ 版本驗證失敗: 期望 {self.target_version}，實際 {current_version}")
                return False

            # 測試基本的插入和查詢操作
            with self.get_connection() as conn:
                cursor = conn.cursor()

                # 測試插入一筆測試資料到 trading_sessions
                test_session_id = f"TEST_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
                cursor.execute("""
                    INSERT INTO trading_sessions (
                        session_id, date, strategy_name, total_lots
                    ) VALUES (?, ?, ?, ?)
                """, (test_session_id, datetime.now().strftime('%Y-%m-%d'), "測試策略", 1))

                # 查詢剛插入的資料
                cursor.execute("SELECT * FROM trading_sessions WHERE session_id = ?", (test_session_id,))
                result = cursor.fetchone()

                if not result:
                    logger.error("❌ 驗證失敗: 無法插入或查詢測試資料")
                    return False

                # 刪除測試資料
                cursor.execute("DELETE FROM trading_sessions WHERE session_id = ?", (test_session_id,))
                conn.commit()

            logger.info("✅ 遷移驗證完成")
            return True

        except Exception as e:
            logger.error(f"❌ 遷移驗證失敗: {e}")
            return False

    def rollback_migration(self) -> bool:
        """回滾遷移（如果需要）"""
        try:
            if not os.path.exists(self.backup_path):
                logger.error("❌ 備份檔案不存在，無法回滾")
                return False

            # 刪除當前資料庫
            if os.path.exists(self.db_path):
                os.remove(self.db_path)

            # 恢復備份
            with sqlite3.connect(self.backup_path) as backup:
                with sqlite3.connect(self.db_path) as target:
                    backup.backup(target)

            logger.info(f"✅ 成功回滾到備份版本: {self.backup_path}")
            return True

        except Exception as e:
            logger.error(f"❌ 回滾失敗: {e}")
            return False

    def run_migration(self, force: bool = False) -> bool:
        """
        執行完整的資料庫遷移

        Args:
            force: 是否強制執行遷移（即使版本已經是最新）

        Returns:
            bool: 遷移是否成功
        """
        logger.info("🚀 開始資料庫遷移...")

        try:
            # 檢查是否需要遷移
            if not force and self.current_version >= self.target_version:
                logger.info(f"ℹ️  資料庫版本已是最新 ({self.current_version})，無需遷移")
                return True

            # 步驟1: 創建版本管理表
            logger.info("📋 步驟1: 創建版本管理表...")
            self.create_version_table()

            # 步驟2: 備份現有資料庫
            logger.info("💾 步驟2: 備份現有資料庫...")
            if not self.backup_database():
                logger.error("❌ 備份失敗，中止遷移")
                return False

            # 步驟3: 驗證現有資料
            logger.info("🔍 步驟3: 驗證現有資料...")
            if not self.validate_existing_data():
                logger.error("❌ 資料驗證失敗，中止遷移")
                return False

            # 步驟4: 創建新表格
            logger.info("🏗️  步驟4: 創建部位管理表格...")
            if not self.create_position_tables():
                logger.error("❌ 創建表格失敗，嘗試回滾...")
                self.rollback_migration()
                return False

            # 步驟5: 創建索引
            logger.info("📊 步驟5: 創建效能索引...")
            if not self.create_indexes():
                logger.warning("⚠️  索引創建部分失敗，但繼續執行...")

            # 步驟6: 創建觸發器
            logger.info("⚡ 步驟6: 創建自動維護觸發器...")
            if not self.create_triggers():
                logger.warning("⚠️  觸發器創建部分失敗，但繼續執行...")

            # 步驟7: 更新版本記錄
            logger.info("📝 步驟7: 更新資料庫版本...")
            if not self.update_database_version():
                logger.error("❌ 版本更新失敗，嘗試回滾...")
                self.rollback_migration()
                return False

            # 步驟8: 驗證遷移結果
            logger.info("✅ 步驟8: 驗證遷移結果...")
            if not self.verify_migration():
                logger.error("❌ 遷移驗證失敗，嘗試回滾...")
                self.rollback_migration()
                return False

            logger.info("🎉 資料庫遷移成功完成！")
            logger.info(f"📊 新功能: 部位管理系統已啟用")
            logger.info(f"💾 備份檔案: {self.backup_path}")

            return True

        except Exception as e:
            logger.error(f"❌ 遷移過程中發生未預期錯誤: {e}")
            logger.info("🔄 嘗試回滾...")
            self.rollback_migration()
            return False

    def get_migration_status(self) -> Dict[str, Any]:
        """取得遷移狀態資訊"""
        try:
            existing_tables = self.get_existing_tables()
            required_tables = ["positions", "stop_loss_adjustments", "position_snapshots", "trading_sessions"]

            status = {
                "current_version": self.current_version,
                "target_version": self.target_version,
                "needs_migration": self.current_version < self.target_version,
                "existing_tables": existing_tables,
                "required_tables": required_tables,
                "missing_tables": [t for t in required_tables if t not in existing_tables],
                "backup_exists": os.path.exists(self.backup_path) if hasattr(self, 'backup_path') else False
            }

            return status

        except Exception as e:
            logger.error(f"取得遷移狀態失敗: {e}")
            return {}

def setup_logging():
    """設定日誌記錄"""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s',
        handlers=[
            logging.StreamHandler(),
            logging.FileHandler(f'migration_{datetime.now().strftime("%Y%m%d_%H%M%S")}.log')
        ]
    )

def main():
    """主程式入口"""
    import argparse

    parser = argparse.ArgumentParser(description='資料庫遷移工具')
    parser.add_argument('--db-path', default='strategy_trading.db', help='資料庫檔案路徑')
    parser.add_argument('--force', action='store_true', help='強制執行遷移')
    parser.add_argument('--status', action='store_true', help='顯示遷移狀態')
    parser.add_argument('--rollback', action='store_true', help='回滾到備份版本')
    parser.add_argument('--verify', action='store_true', help='僅驗證遷移結果')

    args = parser.parse_args()

    # 設定日誌
    setup_logging()

    try:
        migration = DatabaseMigration(args.db_path)

        if args.status:
            # 顯示遷移狀態
            status = migration.get_migration_status()
            print("\n📊 資料庫遷移狀態:")
            print(f"當前版本: {status.get('current_version', 'Unknown')}")
            print(f"目標版本: {status.get('target_version', 'Unknown')}")
            print(f"需要遷移: {'是' if status.get('needs_migration', False) else '否'}")
            print(f"現有表格: {status.get('existing_tables', [])}")
            print(f"缺少表格: {status.get('missing_tables', [])}")
            return

        if args.rollback:
            # 執行回滾
            print("🔄 執行資料庫回滾...")
            success = migration.rollback_migration()
            if success:
                print("✅ 回滾成功")
            else:
                print("❌ 回滾失敗")
            return

        if args.verify:
            # 僅驗證
            print("🔍 驗證遷移結果...")
            success = migration.verify_migration()
            if success:
                print("✅ 驗證通過")
            else:
                print("❌ 驗證失敗")
            return

        # 執行遷移
        print("🚀 開始資料庫遷移...")
        success = migration.run_migration(force=args.force)

        if success:
            print("✅ 遷移成功完成！")
            print("📊 部位管理功能已啟用")
        else:
            print("❌ 遷移失敗")
            sys.exit(1)

    except KeyboardInterrupt:
        print("\n⚠️  用戶中斷操作")
        sys.exit(1)
    except Exception as e:
        print(f"❌ 程式執行錯誤: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
