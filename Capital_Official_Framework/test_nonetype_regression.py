#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
NoneType 錯誤回歸測試
專門測試 multi_group_position_manager 中的 TypeError: '>=' not supported between instances of 'NoneType' and 'int' 修復

此測試確保：
1. 在部位記錄創建時，數字欄位不會是 None
2. 在成交回調處理時，不會出現 NoneType 比較錯誤
3. 重試機制能正確處理 None 值
"""

import sys
import os
import sqlite3
import tempfile
from datetime import datetime, date
import json
import unittest

# 添加當前目錄到路徑
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from multi_group_database import MultiGroupDatabaseManager
from multi_group_position_manager import MultiGroupPositionManager

class TestNoneTypeRegression(unittest.TestCase):
    """NoneType 錯誤回歸測試類"""
    
    def setUp(self):
        """設置測試環境"""
        # 創建臨時資料庫
        self.temp_db = tempfile.NamedTemporaryFile(delete=False, suffix='.db')
        self.temp_db.close()
        
        # 創建資料庫管理器，使用臨時資料庫
        self.db_manager = MultiGroupDatabaseManager()
        # 覆蓋資料庫路徑
        self.db_manager.db_path = self.temp_db.name
        
        # 創建部位管理器
        self.position_manager = MultiGroupPositionManager(self.db_manager)
        
        print(f"✅ 測試環境設置完成，使用臨時資料庫: {self.temp_db.name}")
    
    def tearDown(self):
        """清理測試環境"""
        try:
            os.unlink(self.temp_db.name)
            print(f"✅ 清理臨時資料庫: {self.temp_db.name}")
        except:
            pass
    
    def test_fill_confirmation_without_type_error(self):
        """
        測試成交確認不會出現 TypeError
        
        這是核心回歸測試，模擬導致原始錯誤的確切場景：
        1. 創建策略組和部位記錄
        2. 觸發成交回調
        3. 確保不會出現 NoneType 比較錯誤
        """
        print("\n🧪 測試: 成交確認不會出現 TypeError")
        print("-" * 50)
        
        # Arrange: 準備測試數據
        current_date = date.today().isoformat()
        
        # 創建策略組
        group_db_id = self.db_manager.create_strategy_group(
            date=current_date,
            group_id=1,  # 邏輯組別ID
            direction="SHORT",
            signal_time="21:34:05",
            range_high=22894.0,
            range_low=22915.0,
            total_lots=2
        )
        
        # 創建部位記錄，確保數字欄位有正確的值
        position_ids = []
        for lot_id in range(1, 3):
            position_id = self.db_manager.create_position_record(
                group_id=group_db_id,
                lot_id=lot_id,
                direction="SHORT",
                entry_price=None,  # 故意設為 None，測試防禦性處理
                entry_time=None,
                rule_config=json.dumps({
                    'lot_id': lot_id,
                    'use_trailing_stop': True,
                    'trailing_activation': 15 if lot_id == 1 else 40,
                    'trailing_pullback': 0.20
                }),
                order_id=f"test_order_{lot_id}",
                api_seq_no=f"test_seq_{lot_id}",
                order_status='PENDING',
                retry_count=0,  # 明確設置，確保不是 None
                max_slippage_points=5  # 明確設置，確保不是 None
            )
            position_ids.append(position_id)
        
        print(f"✅ 創建了 {len(position_ids)} 個部位記錄")
        
        # 驗證部位記錄的數字欄位不是 None
        for position_id in position_ids:
            with self.db_manager.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    SELECT retry_count, max_slippage_points 
                    FROM position_records WHERE id = ?
                ''', (position_id,))
                row = cursor.fetchone()
                
                self.assertIsNotNone(row, f"部位 {position_id} 記錄不存在")
                self.assertIsNotNone(row[0], f"部位 {position_id} 的 retry_count 是 None")
                self.assertIsNotNone(row[1], f"部位 {position_id} 的 max_slippage_points 是 None")
                self.assertEqual(row[0], 0, f"部位 {position_id} 的 retry_count 應該是 0")
                self.assertEqual(row[1], 5, f"部位 {position_id} 的 max_slippage_points 應該是 5")
        
        print("✅ 部位記錄數字欄位驗證通過")
        
        # Act: 執行成交回調，這是原始錯誤發生的地方
        try:
            self.position_manager._update_group_positions_on_fill(
                logical_group_id=1,
                price=22892.0,
                qty=1,
                filled_lots=1,
                total_lots=2
            )
            print("✅ 成交回調執行成功，沒有出現 TypeError")
            
        except TypeError as e:
            if "'>=' not supported between instances of 'NoneType' and 'int'" in str(e):
                self.fail(f"出現了我們要修復的 NoneType TypeError: {e}")
            else:
                # 其他類型的 TypeError，重新拋出
                raise
        
        # Assert: 驗證部位狀態已正確更新
        with self.db_manager.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                SELECT COUNT(*) FROM position_records 
                WHERE group_id = ? AND order_status = 'FILLED'
            ''', (group_db_id,))
            filled_count = cursor.fetchone()[0]
            
            # 應該有至少一個部位被標記為 FILLED
            self.assertGreaterEqual(filled_count, 1, "應該有至少一個部位被確認成交")
        
        print(f"✅ 驗證通過：{filled_count} 個部位已確認成交")
    
    def test_retry_mechanism_with_none_values(self):
        """
        測試重試機制能正確處理 None 值
        
        確保 is_retry_allowed 方法不會因為 retry_count 為 None 而出錯
        """
        print("\n🧪 測試: 重試機制處理 None 值")
        print("-" * 40)
        
        # 測試 retry_count 為 None 的情況
        position_info_with_none = {
            'position_pk': 999,
            'retry_count': None  # 故意設為 None
        }
        
        # 這不應該拋出 TypeError
        try:
            result = self.position_manager.is_retry_allowed(position_info_with_none)
            self.assertTrue(result, "retry_count 為 None 時應該允許重試（被設為 0）")
            print("✅ retry_count 為 None 時正確處理")
        except TypeError as e:
            self.fail(f"重試機制出現 NoneType TypeError: {e}")
        
        # 測試正常的 retry_count
        position_info_normal = {
            'position_pk': 998,
            'retry_count': 2
        }
        
        result = self.position_manager.is_retry_allowed(position_info_normal)
        self.assertTrue(result, "正常的 retry_count 應該允許重試")
        print("✅ 正常 retry_count 處理正確")
    
    def test_database_constraints_with_none_values(self):
        """
        測試資料庫約束能正確處理 None 值
        
        確保在創建部位記錄時，即使傳入 None 值也能正確設置默認值
        """
        print("\n🧪 測試: 資料庫約束處理 None 值")
        print("-" * 40)
        
        # 創建策略組
        current_date = date.today().isoformat()
        group_db_id = self.db_manager.create_strategy_group(
            date=current_date,
            group_id=2,
            direction="LONG",
            signal_time="09:30:00",
            range_high=23000.0,
            range_low=22950.0,
            total_lots=1
        )
        
        # 故意傳入 None 值測試防禦性處理
        position_id = self.db_manager.create_position_record(
            group_id=group_db_id,
            lot_id=1,
            direction="LONG",
            retry_count=None,  # 故意傳入 None
            max_slippage_points=None  # 故意傳入 None
        )
        
        # 驗證實際存儲的值不是 None
        with self.db_manager.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                SELECT retry_count, max_slippage_points 
                FROM position_records WHERE id = ?
            ''', (position_id,))
            row = cursor.fetchone()
            
            self.assertIsNotNone(row[0], "retry_count 不應該是 None")
            self.assertIsNotNone(row[1], "max_slippage_points 不應該是 None")
            self.assertEqual(row[0], 0, "retry_count 應該被設為默認值 0")
            self.assertEqual(row[1], 5, "max_slippage_points 應該被設為默認值 5")
        
        print("✅ 資料庫約束正確處理 None 值")

def run_regression_test():
    """運行回歸測試"""
    print("🚀 開始 NoneType 錯誤回歸測試")
    print("=" * 60)
    
    # 創建測試套件
    suite = unittest.TestLoader().loadTestsFromTestCase(TestNoneTypeRegression)
    
    # 運行測試
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    print("=" * 60)
    if result.wasSuccessful():
        print("🎉 所有回歸測試通過！NoneType 錯誤修復驗證成功")
        return True
    else:
        print("❌ 回歸測試失敗，發現問題:")
        for failure in result.failures:
            print(f"  - {failure[0]}: {failure[1]}")
        for error in result.errors:
            print(f"  - {error[0]}: {error[1]}")
        return False

if __name__ == "__main__":
    success = run_regression_test()
    sys.exit(0 if success else 1)
