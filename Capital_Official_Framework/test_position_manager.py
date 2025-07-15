#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Test Position Manager (多組部位管理器測試腳本)

此腳本為 MultiGroupPositionManager 提供獨立的測試環境，
用於在不啟動完整交易系統的情況下測試其功能。

測試重點：
1. ID一致性問題的重現和修復驗證
2. execute_group_entry 功能測試
3. 數據庫操作的正確性驗證
"""

import unittest
import os
import sys
import tempfile
import shutil
from datetime import datetime, date
from unittest.mock import Mock, patch

# 添加當前目錄到路徑
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# 導入必要模組
from multi_group_database import MultiGroupDatabaseManager
from multi_group_position_manager import MultiGroupPositionManager
from multi_group_config import MultiGroupStrategyConfig, StrategyGroupConfig, LotRule, GroupStatus


class TestPositionManager(unittest.TestCase):
    """MultiGroupPositionManager 測試類"""

    def setUp(self):
        """測試前準備：創建乾淨的測試環境"""
        print(f"\n🔧 設置測試環境...")
        
        # 創建臨時測試資料庫
        self.test_db_dir = tempfile.mkdtemp()
        self.test_db_path = os.path.join(self.test_db_dir, "test_position_manager.db")
        
        # 創建資料庫管理器
        self.db_manager = MultiGroupDatabaseManager(self.test_db_path)
        print(f"✅ 測試資料庫創建: {self.test_db_path}")
        
        # 創建測試配置
        self.strategy_config = self._create_test_config()
        print(f"✅ 測試配置創建完成")
        
        # 創建模擬的依賴組件
        self.mock_order_manager = Mock()
        self.mock_simplified_tracker = Mock()
        self.mock_total_lot_manager = Mock()
        
        # 創建 PositionManager 實例
        self.position_manager = MultiGroupPositionManager(
            db_manager=self.db_manager,
            strategy_config=self.strategy_config,
            order_manager=self.mock_order_manager,
            simplified_tracker=self.mock_simplified_tracker,
            total_lot_manager=self.mock_total_lot_manager
        )
        print(f"✅ PositionManager 實例創建完成")

    def tearDown(self):
        """測試後清理：刪除測試資料庫和臨時文件"""
        print(f"🧹 清理測試環境...")
        
        # 關閉資料庫連接
        if hasattr(self.db_manager, 'close'):
            self.db_manager.close()
        
        # 刪除臨時目錄
        if os.path.exists(self.test_db_dir):
            shutil.rmtree(self.test_db_dir)
        
        print(f"✅ 測試環境清理完成")

    def _create_test_config(self):
        """創建測試用的策略配置"""
        # 創建測試組配置
        lot_rules = [
            LotRule(lot_id=1),
            LotRule(lot_id=2)
        ]

        group_config = StrategyGroupConfig(
            group_id=1,
            lots_per_group=2,
            lot_rules=lot_rules,
            is_active=True
        )

        config = MultiGroupStrategyConfig(
            total_groups=1,
            lots_per_group=2,
            groups=[group_config]
        )

        return config

    def _create_test_strategy_group(self, group_id=1, direction="LONG"):
        """創建測試用的策略組"""
        current_date = date.today().isoformat()
        
        group_db_id = self.db_manager.create_strategy_group(
            date=current_date,
            group_id=group_id,
            direction=direction,
            signal_time="10:30:00",
            range_high=22900.0,
            range_low=22850.0,
            total_lots=2
        )
        
        return group_db_id

    def test_database_setup(self):
        """測試資料庫設置是否正確"""
        print("🧪 測試資料庫設置...")
        
        # 檢查資料庫文件是否存在
        self.assertTrue(os.path.exists(self.test_db_path))
        
        # 檢查表是否創建
        tables = self.db_manager.get_table_list()
        expected_tables = ['strategy_groups', 'position_records']
        
        for table in expected_tables:
            self.assertIn(table, tables, f"表 {table} 應該存在")
        
        print("✅ 資料庫設置測試通過")

    def test_create_entry_signal(self):
        """測試創建進場信號功能"""
        print("🧪 測試創建進場信號...")
        
        # 執行創建進場信號
        created_groups = self.position_manager.create_entry_signal(
            direction="LONG",
            signal_time="10:30:00",
            range_high=22900.0,
            range_low=22850.0
        )
        
        # 驗證結果
        self.assertIsInstance(created_groups, list)
        self.assertGreater(len(created_groups), 0, "應該創建至少一個策略組")
        
        # 檢查資料庫中是否有記錄
        today_groups = self.db_manager.get_today_strategy_groups()
        self.assertGreater(len(today_groups), 0, "資料庫中應該有策略組記錄")
        
        print(f"✅ 成功創建 {len(created_groups)} 個策略組")

    def test_execute_group_entry_basic(self):
        """測試基本的組進場功能"""
        print("🧪 測試基本組進場功能...")
        
        # 先創建策略組
        group_db_id = self._create_test_strategy_group()
        self.assertIsNotNone(group_db_id, "策略組應該創建成功")
        
        # 模擬下單成功
        mock_order_result = Mock()
        mock_order_result.success = True
        mock_order_result.order_id = "TEST_ORDER_001"
        mock_order_result.mode = "virtual"
        self.mock_order_manager.execute_strategy_order.return_value = mock_order_result
        
        # 執行組進場
        result = self.position_manager.execute_group_entry(
            group_db_id=group_db_id,
            actual_price=22875.0,
            actual_time="10:30:15"
        )
        
        # 驗證結果
        self.assertTrue(result, "組進場應該成功")
        
        # 檢查是否創建了部位記錄
        positions = self.db_manager.get_group_positions(group_db_id)
        self.assertGreater(len(positions), 0, "應該創建部位記錄")
        
        print(f"✅ 組進場測試通過，創建了 {len(positions)} 個部位")

    def test_execute_group_entry_id_consistency(self):
        """測試組進場中的ID一致性問題"""
        print("🧪 測試組進場ID一致性...")
        
        # 創建策略組
        group_db_id = self._create_test_strategy_group(group_id=5)
        
        # 檢查策略組是否正確創建
        today_groups = self.db_manager.get_today_strategy_groups()
        target_group = None
        for group in today_groups:
            if group['group_pk'] == group_db_id:
                target_group = group
                break
        
        self.assertIsNotNone(target_group, f"應該找到 DB_ID={group_db_id} 的策略組")
        self.assertEqual(target_group['logical_group_id'], 5, "邏輯組ID應該是5")
        
        print(f"✅ ID一致性檢查通過: DB_ID={group_db_id}, logical_group_id={target_group['logical_group_id']}")

    def test_get_strategy_group_info_consistency(self):
        """測試策略組信息查詢的一致性"""
        print("🧪 測試策略組信息查詢一致性...")
        
        # 創建策略組
        group_db_id = self._create_test_strategy_group(group_id=3)
        
        # 測試通過DB_ID查詢基本信息
        basic_info = self.db_manager.get_strategy_group_by_db_id(group_db_id)
        self.assertIsNotNone(basic_info, "應該能通過DB_ID查詢到基本信息")
        
        # 測試通過logical_group_id查詢完整信息
        logical_group_id = basic_info['logical_group_id']
        full_info = self.db_manager.get_strategy_group_info(logical_group_id)
        self.assertIsNotNone(full_info, "應該能通過logical_group_id查詢到完整信息")
        
        # 驗證ID一致性
        self.assertEqual(basic_info['group_pk'], group_db_id, "主鍵ID應該一致")
        self.assertEqual(basic_info['logical_group_id'], logical_group_id, "邏輯組ID應該一致")
        
        print(f"✅ 策略組信息查詢一致性測試通過")

    def test_position_creation_with_correct_group_id(self):
        """測試部位創建時使用正確的group_id"""
        print("🧪 測試部位創建的group_id正確性...")
        
        # 創建策略組
        group_db_id = self._create_test_strategy_group(group_id=7)
        
        # 獲取策略組信息
        basic_info = self.db_manager.get_strategy_group_by_db_id(group_db_id)
        logical_group_id = basic_info['logical_group_id']
        
        # 創建部位記錄
        position_pk = self.db_manager.create_position_record(
            group_id=logical_group_id,  # 使用邏輯組ID
            lot_id=1,
            direction="LONG",
            entry_time="10:30:15",
            target_price=22875.0,
            stop_loss_price=22855.0,
            take_profit_price=22915.0
        )
        
        self.assertIsNotNone(position_pk, "部位記錄應該創建成功")
        
        # 驗證部位記錄中的group_id
        position_info = self.db_manager.get_position_by_id(position_pk)
        self.assertIsNotNone(position_info, "應該能查詢到部位信息")
        
        # 這裡應該檢查部位記錄中的group_id是否正確
        # 注意：根據當前實現，position_records.group_id 存儲的是 DB_ID
        self.assertEqual(position_info['group_id'], group_db_id, "部位記錄中的group_id應該是DB_ID")
        
        print(f"✅ 部位創建group_id正確性測試通過")


def run_specific_test(test_name=None):
    """運行特定測試或所有測試"""
    if test_name:
        suite = unittest.TestSuite()
        suite.addTest(TestPositionManager(test_name))
        runner = unittest.TextTestRunner(verbosity=2)
        result = runner.run(suite)
    else:
        unittest.main(verbosity=2)


if __name__ == "__main__":
    print("🎯 MultiGroupPositionManager 獨立測試環境")
    print("=" * 60)
    
    # 檢查是否指定了特定測試
    if len(sys.argv) > 1 and sys.argv[1].startswith('test_'):
        test_name = sys.argv[1]
        print(f"🔍 運行特定測試: {test_name}")
        run_specific_test(test_name)
    else:
        print("🔍 運行所有測試")
        unittest.main(verbosity=2)
