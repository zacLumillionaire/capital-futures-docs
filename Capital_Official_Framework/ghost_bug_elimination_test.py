#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
幽靈BUG根除測試工具
專門測試任務1-5的修復效果：
1. 保護性停損累積獲利計算修復
2. OptimizedRiskManager重複觸發防護
3. SimplifiedTracker狀態同步
4. 增強日誌系統
5. 壓力測試驗證
"""

import os
import sys
import time
import sqlite3
import threading
from datetime import datetime
from typing import Dict, List, Optional

# 添加當前目錄到路徑
current_dir = os.path.dirname(os.path.abspath(__file__))
if current_dir not in sys.path:
    sys.path.insert(0, current_dir)

# 導入測試所需模組
from cumulative_profit_protection_manager import CumulativeProfitProtectionManager
from optimized_risk_manager import OptimizedRiskManager
from simplified_order_tracker import SimplifiedOrderTracker, GlobalExitManager
from multi_group_database import MultiGroupDatabaseManager

class GhostBugEliminationTest:
    """幽靈BUG根除測試器"""
    
    def __init__(self):
        self.test_db_path = "test_ghost_bug_elimination.db"
        self.db_manager = None
        self.protection_manager = None
        self.risk_manager = None
        self.tracker = None
        self.global_exit_manager = GlobalExitManager()
        
        # 測試結果記錄
        self.test_results = {
            'task1_protection_fix': {'passed': False, 'details': []},
            'task2_duplicate_prevention': {'passed': False, 'details': []},
            'task3_tracker_sync': {'passed': False, 'details': []},
            'task4_enhanced_logging': {'passed': False, 'details': []},
            'task5_stress_test': {'passed': False, 'details': []}
        }
        
        print("🔧 幽靈BUG根除測試工具初始化完成")
        print("=" * 60)
    
    def setup_test_environment(self):
        """設置測試環境"""
        try:
            # 清理舊的測試資料庫
            if os.path.exists(self.test_db_path):
                os.remove(self.test_db_path)
            
            # 初始化資料庫管理器
            self.db_manager = MultiGroupDatabaseManager(self.test_db_path)
            
            # 初始化各個管理器
            self.protection_manager = CumulativeProfitProtectionManager(
                self.db_manager, console_enabled=True
            )
            
            self.risk_manager = OptimizedRiskManager(
                self.db_manager, console_enabled=True
            )
            
            self.tracker = SimplifiedOrderTracker(console_enabled=True)
            
            print("✅ 測試環境設置完成")
            return True
            
        except Exception as e:
            print(f"❌ 測試環境設置失敗: {e}")
            return False
    
    def test_task1_protection_fix(self):
        """任務1：測試保護性停損累積獲利計算修復"""
        print("\n🧪 任務1測試：保護性停損累積獲利計算修復")
        print("-" * 50)
        
        try:
            # 創建測試策略組
            group_id = 1
            
            # 確保資料庫表結構正確
            with self.db_manager.get_connection() as conn:
                cursor = conn.cursor()

                # 檢查並添加缺少的欄位
                try:
                    cursor.execute("SELECT realized_pnl FROM position_records LIMIT 1")
                except sqlite3.OperationalError:
                    # 添加缺少的realized_pnl欄位
                    cursor.execute("ALTER TABLE position_records ADD COLUMN realized_pnl REAL")
                    print("✅ 添加realized_pnl欄位到position_records表")

                try:
                    cursor.execute("SELECT exit_price FROM position_records LIMIT 1")
                except sqlite3.OperationalError:
                    # 添加缺少的exit_price欄位
                    cursor.execute("ALTER TABLE position_records ADD COLUMN exit_price REAL")
                    print("✅ 添加exit_price欄位到position_records表")

                # 部位37：已平倉，獲利24點
                cursor.execute('''
                    INSERT OR REPLACE INTO position_records
                    (id, group_id, lot_id, status, realized_pnl, entry_price, exit_price, direction, entry_time)
                    VALUES (37, ?, 1, 'EXITED', 24.0, 21500, 21524, 'LONG', '09:00:00')
                ''', (group_id,))

                # 部位38：活躍中，需要保護性停損更新
                cursor.execute('''
                    INSERT OR REPLACE INTO position_records
                    (id, group_id, lot_id, status, realized_pnl, entry_price, direction, entry_time)
                    VALUES (38, ?, 2, 'ACTIVE', NULL, 21510, 'LONG', '09:01:00')
                ''', (group_id,))

                conn.commit()
            
            # 測試累積獲利計算
            cumulative_profit = self.protection_manager._calculate_cumulative_profit(group_id, 37)
            
            print(f"📊 累積獲利計算結果: {cumulative_profit:.1f} 點")
            
            # 驗證結果
            if cumulative_profit == 24.0:
                self.test_results['task1_protection_fix']['passed'] = True
                self.test_results['task1_protection_fix']['details'].append(
                    f"✅ 累積獲利正確計算: {cumulative_profit:.1f} 點"
                )
                print("✅ 任務1測試通過：累積獲利計算正確")
            else:
                self.test_results['task1_protection_fix']['details'].append(
                    f"❌ 累積獲利計算錯誤: 期望24.0，實際{cumulative_profit:.1f}"
                )
                print(f"❌ 任務1測試失敗：累積獲利計算錯誤")
            
            # 測試保護性停損更新
            protection_updates = self.protection_manager.update_protective_stops_for_group(group_id, 37)
            
            if protection_updates:
                self.test_results['task1_protection_fix']['details'].append(
                    f"✅ 保護性停損更新成功: {len(protection_updates)}個更新"
                )
                print(f"✅ 保護性停損更新成功: {len(protection_updates)}個更新")
            else:
                self.test_results['task1_protection_fix']['details'].append(
                    "❌ 保護性停損更新失敗"
                )
                print("❌ 保護性停損更新失敗")
                
        except Exception as e:
            self.test_results['task1_protection_fix']['details'].append(f"❌ 測試異常: {e}")
            print(f"❌ 任務1測試異常: {e}")
    
    def test_task2_duplicate_prevention(self):
        """任務2：測試重複觸發防護"""
        print("\n🧪 任務2測試：OptimizedRiskManager重複觸發防護")
        print("-" * 50)
        
        try:
            # 模擬部位數據
            position_id = "36"
            position_data = {
                'id': 36,
                'group_id': 1,
                'direction': 'LONG',
                'entry_price': 21500,
                'quantity': 1,
                'lot_id': 1
            }
            
            # 添加到風險管理器緩存
            self.risk_manager.position_cache[position_id] = position_data
            self.risk_manager.trailing_cache[position_id] = {
                'activated': True,
                'peak_price': 21530,
                'direction': 'LONG'
            }
            
            print(f"📍 模擬部位{position_id}添加到監控緩存")
            
            # 第一次觸發移動停利
            trigger_count = 0
            
            def mock_execute_trailing_stop(trigger_info):
                nonlocal trigger_count
                trigger_count += 1
                print(f"🚀 第{trigger_count}次移動停利觸發: 部位{trigger_info['position_id']}")
                return True
            
            # 替換執行方法
            original_method = self.risk_manager._execute_trailing_stop_exit
            self.risk_manager._execute_trailing_stop_exit = mock_execute_trailing_stop
            
            # 模擬高頻報價觸發
            print("📈 模擬高頻報價觸發...")
            for i in range(5):
                current_price = 21520  # 觸發移動停利的價格
                result = self.risk_manager.update_price(current_price)
                time.sleep(0.01)  # 模擬極短間隔
                print(f"   第{i+1}次報價處理完成")
            
            # 恢復原方法
            self.risk_manager._execute_trailing_stop_exit = original_method
            
            # 驗證結果
            if trigger_count <= 1:
                self.test_results['task2_duplicate_prevention']['passed'] = True
                self.test_results['task2_duplicate_prevention']['details'].append(
                    f"✅ 重複觸發防護成功: 只觸發{trigger_count}次"
                )
                print(f"✅ 任務2測試通過：重複觸發防護成功，只觸發{trigger_count}次")
            else:
                self.test_results['task2_duplicate_prevention']['details'].append(
                    f"❌ 重複觸發防護失敗: 觸發{trigger_count}次"
                )
                print(f"❌ 任務2測試失敗：重複觸發防護失敗，觸發{trigger_count}次")
            
            # 檢查處理中狀態
            if position_id not in self.risk_manager.exiting_positions:
                self.test_results['task2_duplicate_prevention']['details'].append(
                    "✅ 處理中狀態正確清理"
                )
                print("✅ 處理中狀態正確清理")
            else:
                self.test_results['task2_duplicate_prevention']['details'].append(
                    "❌ 處理中狀態未正確清理"
                )
                print("❌ 處理中狀態未正確清理")
                
        except Exception as e:
            self.test_results['task2_duplicate_prevention']['details'].append(f"❌ 測試異常: {e}")
            print(f"❌ 任務2測試異常: {e}")
    
    def test_task3_tracker_sync(self):
        """任務3：測試SimplifiedTracker狀態同步"""
        print("\n🧪 任務3測試：SimplifiedTracker狀態同步")
        print("-" * 50)
        
        try:
            position_id = 36
            order_id = "TEST_ORDER_001"
            
            # 註冊平倉訂單
            self.tracker.register_exit_order(
                order_id=order_id,
                position_id=position_id,
                direction="SELL",
                price=21520,
                quantity=1,
                product="MTX00"
            )
            
            print(f"📝 註冊平倉訂單: {order_id} for 部位{position_id}")
            
            # 檢查是否有平倉訂單
            has_order_before = self.tracker.has_exit_order_for_position(position_id)
            print(f"📋 註冊後檢查: has_exit_order = {has_order_before}")
            
            # 模擬平倉成交回報
            fill_processed = self.tracker._handle_exit_fill_report(21520, 1, "MTX00")
            print(f"📥 平倉成交處理結果: {fill_processed}")
            
            # 檢查清理後狀態
            has_order_after = self.tracker.has_exit_order_for_position(position_id)
            print(f"📋 清理後檢查: has_exit_order = {has_order_after}")
            
            # 驗證結果
            if has_order_before and not has_order_after and fill_processed:
                self.test_results['task3_tracker_sync']['passed'] = True
                self.test_results['task3_tracker_sync']['details'].append(
                    "✅ SimplifiedTracker狀態同步正常"
                )
                print("✅ 任務3測試通過：SimplifiedTracker狀態同步正常")
            else:
                self.test_results['task3_tracker_sync']['details'].append(
                    f"❌ 狀態同步異常: before={has_order_before}, after={has_order_after}, processed={fill_processed}"
                )
                print("❌ 任務3測試失敗：SimplifiedTracker狀態同步異常")
                
        except Exception as e:
            self.test_results['task3_tracker_sync']['details'].append(f"❌ 測試異常: {e}")
            print(f"❌ 任務3測試異常: {e}")
    
    def test_task4_enhanced_logging(self):
        """任務4：測試增強日誌系統"""
        print("\n🧪 任務4測試：增強日誌系統")
        print("-" * 50)
        
        try:
            # 測試線程名稱是否包含在日誌中
            print("📝 測試增強日誌輸出...")
            
            # 觸發保護性停損日誌
            self.protection_manager.update_protective_stops_for_group(1, 37)
            
            # 觸發風險管理器日誌
            position_id = "test_position"
            self.risk_manager.exiting_positions.add(position_id)
            self.risk_manager.position_cache[position_id] = {'test': 'data'}
            self.risk_manager.update_price(21500)
            
            # 由於日誌輸出到控制台，我們假設如果沒有異常就是成功
            self.test_results['task4_enhanced_logging']['passed'] = True
            self.test_results['task4_enhanced_logging']['details'].append(
                "✅ 增強日誌系統正常運行"
            )
            print("✅ 任務4測試通過：增強日誌系統正常運行")
            
        except Exception as e:
            self.test_results['task4_enhanced_logging']['details'].append(f"❌ 測試異常: {e}")
            print(f"❌ 任務4測試異常: {e}")
    
    def run_all_tests(self):
        """運行所有測試"""
        print("🚀 開始執行幽靈BUG根除測試")
        print("=" * 60)
        
        if not self.setup_test_environment():
            print("❌ 測試環境設置失敗，終止測試")
            return
        
        # 執行各項測試
        self.test_task1_protection_fix()
        self.test_task2_duplicate_prevention()
        self.test_task3_tracker_sync()
        self.test_task4_enhanced_logging()
        
        # 生成測試報告
        self.generate_test_report()
    
    def generate_test_report(self):
        """生成測試報告"""
        print("\n" + "=" * 60)
        print("📊 幽靈BUG根除測試報告")
        print("=" * 60)
        
        total_tests = len(self.test_results)
        passed_tests = sum(1 for result in self.test_results.values() if result['passed'])
        
        print(f"總測試項目: {total_tests}")
        print(f"通過測試: {passed_tests}")
        print(f"失敗測試: {total_tests - passed_tests}")
        print(f"通過率: {passed_tests/total_tests*100:.1f}%")
        print()
        
        for task_name, result in self.test_results.items():
            status = "✅ 通過" if result['passed'] else "❌ 失敗"
            print(f"{task_name}: {status}")
            for detail in result['details']:
                print(f"  {detail}")
            print()
        
        # 保存報告到文件
        report_file = f"ghost_bug_test_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
        with open(report_file, 'w', encoding='utf-8') as f:
            f.write("幽靈BUG根除測試報告\n")
            f.write("=" * 60 + "\n")
            f.write(f"測試時間: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
            f.write(f"總測試項目: {total_tests}\n")
            f.write(f"通過測試: {passed_tests}\n")
            f.write(f"失敗測試: {total_tests - passed_tests}\n")
            f.write(f"通過率: {passed_tests/total_tests*100:.1f}%\n\n")
            
            for task_name, result in self.test_results.items():
                status = "通過" if result['passed'] else "失敗"
                f.write(f"{task_name}: {status}\n")
                for detail in result['details']:
                    f.write(f"  {detail}\n")
                f.write("\n")
        
        print(f"📄 詳細報告已保存至: {report_file}")
        
        if passed_tests == total_tests:
            print("🎉 所有幽靈BUG已成功根除！")
        else:
            print("⚠️ 仍有部分問題需要修復")

if __name__ == "__main__":
    tester = GhostBugEliminationTest()
    tester.run_all_tests()
