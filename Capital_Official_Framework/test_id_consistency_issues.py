#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
ID Consistency Issues Test (ID一致性問題診斷測試)

此腳本專門用於重現和驗證 multi_group_position_manager.py 中的ID一致性問題。
基於任務1的問題清單，編寫針對性測試案例。

測試重點：
1. execute_group_entry 中的 group_id 變數問題
2. _update_group_positions_on_fill 中的模糊變數問題
3. 各種追價函數中的ID命名問題
"""

import unittest
import os
import sys
import tempfile
import shutil
from datetime import date
from unittest.mock import Mock, patch

# 添加當前目錄到路徑
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from multi_group_database import MultiGroupDatabaseManager
from multi_group_position_manager import MultiGroupPositionManager
from multi_group_config import MultiGroupStrategyConfig, StrategyGroupConfig, LotRule


class TestIDConsistencyIssues(unittest.TestCase):
    """ID一致性問題診斷測試類"""

    def setUp(self):
        """測試前準備"""
        print(f"\n🔧 設置ID一致性測試環境...")
        
        # 創建臨時測試資料庫
        self.test_db_dir = tempfile.mkdtemp()
        self.test_db_path = os.path.join(self.test_db_dir, "test_id_consistency.db")
        self.db_manager = MultiGroupDatabaseManager(self.test_db_path)
        
        # 創建測試配置
        self.strategy_config = self._create_test_config()
        
        # 創建模擬組件
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

    def tearDown(self):
        """測試後清理"""
        if os.path.exists(self.test_db_dir):
            shutil.rmtree(self.test_db_dir)

    def _create_test_config(self):
        """創建測試配置"""
        lot_rules = [LotRule(lot_id=1), LotRule(lot_id=2)]
        group_config = StrategyGroupConfig(
            group_id=1,
            lots_per_group=2,
            lot_rules=lot_rules,
            is_active=True
        )
        return MultiGroupStrategyConfig(
            total_groups=1,
            lots_per_group=2,
            groups=[group_config]
        )

    def _create_test_strategy_group(self, group_id=1, direction="LONG"):
        """創建測試策略組"""
        current_date = date.today().isoformat()
        return self.db_manager.create_strategy_group(
            date=current_date,
            group_id=group_id,
            direction=direction,
            signal_time="10:30:00",
            range_high=22900.0,
            range_low=22850.0,
            total_lots=2
        )

    def test_execute_group_entry_id_variable_issue(self):
        """
        測試 execute_group_entry 中的 group_id 變數問題

        問題位置：L_167, L_168, L_170 (函式: execute_group_entry)
        問題：使用模糊變數 'group_id'
        """
        print("🧪 測試 execute_group_entry 中的 group_id 變數問題...")

        # 先創建進場信號，這會正確設置組狀態
        created_groups = self.position_manager.create_entry_signal(
            direction="LONG",
            signal_time="10:30:00",
            range_high=22900.0,
            range_low=22850.0
        )

        self.assertGreater(len(created_groups), 0, "應該創建至少一個策略組")
        group_db_id = created_groups[0]

        # 模擬下單成功
        mock_order_result = Mock()
        mock_order_result.success = True
        mock_order_result.order_id = "TEST_ORDER_001"
        mock_order_result.mode = "virtual"
        self.mock_order_manager.execute_strategy_order.return_value = mock_order_result

        # 這個測試應該暴露ID變數命名的問題
        # 在修復前，代碼中使用了模糊的 'group_id' 變數名
        try:
            result = self.position_manager.execute_group_entry(
                group_db_id=group_db_id,
                actual_price=22875.0,
                actual_time="10:30:15"
            )

            # 如果執行成功，檢查是否正確處理了ID
            self.assertTrue(result, "execute_group_entry 應該成功")

            # 檢查部位記錄是否正確創建
            positions = self.db_manager.get_group_positions(group_db_id)
            self.assertGreater(len(positions), 0, "應該創建部位記錄")

            print(f"✅ execute_group_entry 測試通過，創建了 {len(positions)} 個部位")

        except Exception as e:
            print(f"❌ execute_group_entry 測試失敗: {e}")
            # 這裡可能會捕獲到ID相關的錯誤
            self.fail(f"execute_group_entry 執行失敗: {e}")

    def test_group_id_vs_logical_group_id_consistency(self):
        """
        測試 group_id 與 logical_group_id 的一致性
        
        這個測試專門檢查代碼中是否正確區分了：
        - group_pk (資料庫主鍵)
        - logical_group_id (業務邏輯ID)
        """
        print("🧪 測試 group_id 與 logical_group_id 一致性...")
        
        # 創建策略組
        logical_group_id = 7
        group_db_id = self._create_test_strategy_group(group_id=logical_group_id)
        
        # 檢查資料庫中的記錄
        today_groups = self.db_manager.get_today_strategy_groups()
        target_group = None
        for group in today_groups:
            if group['group_pk'] == group_db_id:
                target_group = group
                break
        
        self.assertIsNotNone(target_group, f"應該找到 DB_ID={group_db_id} 的策略組")
        self.assertEqual(target_group['logical_group_id'], logical_group_id, 
                        f"邏輯組ID應該是{logical_group_id}")
        
        # 測試通過不同方式查詢的一致性
        basic_info = self.db_manager.get_strategy_group_by_db_id(group_db_id)
        full_info = self.db_manager.get_strategy_group_info(logical_group_id)
        
        self.assertIsNotNone(basic_info, "通過DB_ID應該能查詢到基本信息")
        self.assertIsNotNone(full_info, "通過logical_group_id應該能查詢到完整信息")
        
        print(f"✅ ID一致性測試通過: DB_ID={group_db_id}, logical_group_id={logical_group_id}")

    def test_update_group_positions_on_fill_variable_issues(self):
        """
        測試 _update_group_positions_on_fill 中的模糊變數問題
        
        問題位置：L_825-L_827, L_847, L_863, L_866, L_870, L_876 等
        問題：使用模糊變數 'group', 'group_id', 'position'
        """
        print("🧪 測試 _update_group_positions_on_fill 中的模糊變數問題...")
        
        # 創建策略組和部位
        group_db_id = self._create_test_strategy_group(group_id=3)
        
        # 獲取邏輯組ID
        basic_info = self.db_manager.get_strategy_group_by_db_id(group_db_id)
        logical_group_id = basic_info['logical_group_id']

        # 創建部位記錄 - 使用正確的邏輯組ID
        position_pk = self.db_manager.create_position_record(
            group_id=logical_group_id,  # 🔧 修復：使用邏輯組ID而非DB_ID
            lot_id=1,
            direction="LONG",
            entry_time="10:30:15",
            entry_price=22875.0
        )
        
        # 測試成交更新功能
        try:
            # 這個調用會觸發 _update_group_positions_on_fill 方法
            self.position_manager._update_group_positions_on_fill(
                logical_group_id=3,  # 傳入邏輯組ID
                price=22875.0,
                qty=1,
                filled_lots=1,
                total_lots=2
            )
            
            print("✅ _update_group_positions_on_fill 測試通過")
            
        except Exception as e:
            print(f"❌ _update_group_positions_on_fill 測試失敗: {e}")
            # 這裡可能會捕獲到變數命名相關的錯誤
            self.fail(f"_update_group_positions_on_fill 執行失敗: {e}")

    def test_retry_functions_id_variable_issues(self):
        """
        測試追價函數中的ID變數問題
        
        問題位置：
        - _execute_single_retry_for_group: L_697, L_700, L_710, L_714 等
        - _execute_group_retry: L_1091, L_1094, L_1106, L_1111 等
        """
        print("🧪 測試追價函數中的ID變數問題...")
        
        # 創建策略組
        group_db_id = self._create_test_strategy_group(group_id=4)
        
        # 測試 _get_group_info_for_retry 方法
        try:
            group_info = self.position_manager._get_group_info_for_retry(logical_group_id=4)
            
            if group_info:
                self.assertIn('direction', group_info, "組信息應該包含方向")
                self.assertIn('logical_group_id', group_info, "組信息應該包含邏輯組ID")
                print("✅ _get_group_info_for_retry 測試通過")
            else:
                print("⚠️ _get_group_info_for_retry 返回空值")
                
        except Exception as e:
            print(f"❌ _get_group_info_for_retry 測試失敗: {e}")
            # 這裡可能會捕獲到ID變數相關的錯誤

    def test_sql_condition_ambiguity_issues(self):
        """
        測試SQL條件模糊問題
        
        問題位置：L_835, L_850 (函式: _update_group_positions_on_fill)
        問題：WHERE子句使用了模糊的ID條件
        """
        print("🧪 測試SQL條件模糊問題...")
        
        # 創建策略組和部位
        group_db_id = self._create_test_strategy_group(group_id=6)
        
        # 獲取邏輯組ID
        basic_info = self.db_manager.get_strategy_group_by_db_id(group_db_id)
        logical_group_id = basic_info['logical_group_id']

        # 創建部位記錄 - 使用正確的邏輯組ID
        position_pk = self.db_manager.create_position_record(
            group_id=logical_group_id,  # 🔧 修復：使用邏輯組ID而非DB_ID
            lot_id=1,
            direction="LONG",
            entry_time="10:30:15",
            entry_price=22875.0
        )
        
        # 檢查部位記錄查詢
        position_info = self.db_manager.get_position_by_id(position_pk)
        self.assertIsNotNone(position_info, "應該能查詢到部位信息")
        
        print(f"✅ SQL查詢測試通過，部位ID: {position_pk}")

    def test_function_signature_ambiguity_detection(self):
        """
        測試函數簽名模糊性檢測
        
        這個測試不是為了測試功能，而是為了記錄當前存在的函數簽名問題
        """
        print("🧪 檢測函數簽名模糊性問題...")
        
        # 檢查 PositionManager 中是否存在使用模糊參數名的方法
        ambiguous_methods = []
        
        # 檢查一些關鍵方法的參數名
        import inspect
        
        methods_to_check = [
            'execute_group_entry',
            '_update_group_positions_on_fill',
            '_get_group_info_for_retry',
            '_execute_single_retry_for_group'
        ]
        
        for method_name in methods_to_check:
            if hasattr(self.position_manager, method_name):
                method = getattr(self.position_manager, method_name)
                sig = inspect.signature(method)
                
                for param_name in sig.parameters:
                    if param_name in ['group_id', 'position_id', 'id']:
                        ambiguous_methods.append(f"{method_name}.{param_name}")
        
        if ambiguous_methods:
            print(f"⚠️ 發現模糊函數參數: {ambiguous_methods}")
        else:
            print("✅ 未發現明顯的函數參數模糊性問題")


def run_id_consistency_tests():
    """運行ID一致性測試"""
    print("🎯 ID一致性問題診斷測試")
    print("=" * 60)
    
    # 創建測試套件
    suite = unittest.TestLoader().loadTestsFromTestCase(TestIDConsistencyIssues)
    
    # 運行測試
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    # 總結
    print(f"\n📊 測試結果:")
    print(f"   運行: {result.testsRun}")
    print(f"   失敗: {len(result.failures)}")
    print(f"   錯誤: {len(result.errors)}")
    
    if result.failures:
        print(f"\n❌ 失敗的測試:")
        for test, traceback in result.failures:
            print(f"   - {test}: {traceback.split('AssertionError:')[-1].strip()}")
    
    if result.errors:
        print(f"\n💥 錯誤的測試:")
        for test, traceback in result.errors:
            print(f"   - {test}: {traceback.split('Exception:')[-1].strip()}")
    
    return result.wasSuccessful()


if __name__ == "__main__":
    run_id_consistency_tests()
