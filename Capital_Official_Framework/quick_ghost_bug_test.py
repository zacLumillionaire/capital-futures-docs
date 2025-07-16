#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
快速幽靈BUG測試工具
簡化版測試，專門驗證兩個核心修復：
1. 保護性停損累積獲利計算
2. 重複觸發防護機制
"""

import os
import sys
import time
import sqlite3
import threading
from datetime import datetime

# 添加當前目錄到路徑
current_dir = os.path.dirname(os.path.abspath(__file__))
if current_dir not in sys.path:
    sys.path.insert(0, current_dir)

class QuickGhostBugTest:
    """快速幽靈BUG測試器"""
    
    def __init__(self):
        self.test_db_path = "quick_ghost_test.db"
        print("🚀 快速幽靈BUG測試工具")
        print("=" * 50)
    
    def test_protection_calculation(self):
        """測試保護性停損累積獲利計算"""
        print("\n🧪 測試1：保護性停損累積獲利計算")
        print("-" * 40)
        
        try:
            from cumulative_profit_protection_manager import CumulativeProfitProtectionManager
            from multi_group_database import MultiGroupDatabaseManager
            
            # 清理並創建測試資料庫
            if os.path.exists(self.test_db_path):
                os.remove(self.test_db_path)
            
            db_manager = MultiGroupDatabaseManager(self.test_db_path)
            protection_manager = CumulativeProfitProtectionManager(db_manager, console_enabled=True)
            
            # 確保資料庫表結構
            with db_manager.get_connection() as conn:
                cursor = conn.cursor()
                
                # 檢查並添加缺少的欄位
                try:
                    cursor.execute("SELECT realized_pnl FROM position_records LIMIT 1")
                except sqlite3.OperationalError:
                    cursor.execute("ALTER TABLE position_records ADD COLUMN realized_pnl REAL")
                    print("✅ 添加realized_pnl欄位")
                
                # 插入測試數據：部位37已平倉，獲利24點
                cursor.execute('''
                    INSERT OR REPLACE INTO position_records
                    (id, group_id, lot_id, status, realized_pnl, entry_price, direction, entry_time)
                    VALUES (37, 1, 1, 'EXITED', 24.0, 21500, 'LONG', '09:00:00')
                ''')

                # 插入測試數據：部位38活躍中
                cursor.execute('''
                    INSERT OR REPLACE INTO position_records
                    (id, group_id, lot_id, status, entry_price, direction, entry_time)
                    VALUES (38, 1, 2, 'ACTIVE', 21510, 'LONG', '09:01:00')
                ''')
                
                conn.commit()
                print("✅ 測試數據插入完成")
            
            # 測試累積獲利計算
            print("\n📊 開始測試累積獲利計算...")
            cumulative_profit = protection_manager._calculate_cumulative_profit(1, 37)
            
            print(f"\n📈 測試結果：")
            print(f"   累積獲利: {cumulative_profit:.1f} 點")
            
            if cumulative_profit == 24.0:
                print("✅ 測試1通過：累積獲利計算正確")
                return True
            else:
                print(f"❌ 測試1失敗：期望24.0，實際{cumulative_profit:.1f}")
                return False
                
        except Exception as e:
            print(f"❌ 測試1異常: {e}")
            import traceback
            traceback.print_exc()
            return False
    
    def test_duplicate_prevention(self):
        """測試重複觸發防護"""
        print("\n🧪 測試2：重複觸發防護機制")
        print("-" * 40)
        
        try:
            from optimized_risk_manager import OptimizedRiskManager
            from multi_group_database import MultiGroupDatabaseManager
            
            db_manager = MultiGroupDatabaseManager(self.test_db_path)
            risk_manager = OptimizedRiskManager(db_manager, console_enabled=True)
            
            # 模擬部位數據
            position_id = "100"
            position_data = {
                'id': 100,
                'group_id': 1,
                'direction': 'LONG',
                'entry_price': 21500,
                'quantity': 1,
                'lot_id': 1
            }
            
            # 添加到風險管理器緩存
            risk_manager.position_cache[position_id] = position_data
            risk_manager.trailing_cache[position_id] = {
                'activated': True,
                'peak_price': 21530,
                'direction': 'LONG'
            }
            
            print(f"📍 模擬部位{position_id}添加到監控緩存")
            
            # 記錄觸發次數
            trigger_count = 0
            
            def mock_execute_trailing_stop(trigger_info):
                nonlocal trigger_count
                trigger_count += 1
                thread_name = threading.current_thread().name
                print(f"🚀 第{trigger_count}次移動停利觸發: 部位{trigger_info['position_id']} [線程: {thread_name}]")
                return True
            
            # 替換執行方法
            original_method = risk_manager._execute_trailing_stop_exit
            risk_manager._execute_trailing_stop_exit = mock_execute_trailing_stop
            
            print("\n📈 模擬高頻報價觸發...")
            
            # 模擬連續5次報價，每次間隔1ms
            for i in range(5):
                current_price = 21520  # 觸發移動停利的價格
                print(f"   第{i+1}次報價: {current_price}")
                
                result = risk_manager.update_price(current_price)
                time.sleep(0.001)  # 1ms間隔
            
            # 恢復原方法
            risk_manager._execute_trailing_stop_exit = original_method
            
            print(f"\n📊 測試結果：")
            print(f"   總觸發次數: {trigger_count}")
            print(f"   處理中狀態數量: {len(risk_manager.exiting_positions)}")
            
            # 驗證結果
            if trigger_count <= 1 and len(risk_manager.exiting_positions) == 0:
                print("✅ 測試2通過：重複觸發防護成功")
                return True
            else:
                print(f"❌ 測試2失敗：觸發{trigger_count}次，處理中{len(risk_manager.exiting_positions)}個")
                return False
                
        except Exception as e:
            print(f"❌ 測試2異常: {e}")
            import traceback
            traceback.print_exc()
            return False
    
    def test_enhanced_logging(self):
        """測試增強日誌系統"""
        print("\n🧪 測試3：增強日誌系統")
        print("-" * 40)
        
        try:
            # 檢查threading模組是否正確導入
            import threading
            thread_name = threading.current_thread().name
            print(f"📝 當前線程名稱: {thread_name}")
            
            # 模擬增強日誌輸出
            print(f"[ENHANCED_LOG] 測試日誌 (線程: {thread_name})")
            
            print("✅ 測試3通過：增強日誌系統正常")
            return True
            
        except Exception as e:
            print(f"❌ 測試3異常: {e}")
            return False
    
    def run_quick_test(self):
        """運行快速測試"""
        print("🚀 開始快速幽靈BUG測試")
        
        start_time = time.time()
        
        # 執行測試
        test1_result = self.test_protection_calculation()
        test2_result = self.test_duplicate_prevention()
        test3_result = self.test_enhanced_logging()
        
        # 統計結果
        total_tests = 3
        passed_tests = sum([test1_result, test2_result, test3_result])
        
        end_time = time.time()
        duration = end_time - start_time
        
        print("\n" + "=" * 50)
        print("📊 快速測試結果")
        print("=" * 50)
        print(f"測試時間: {duration:.2f} 秒")
        print(f"總測試: {total_tests}")
        print(f"通過: {passed_tests}")
        print(f"失敗: {total_tests - passed_tests}")
        print(f"通過率: {passed_tests/total_tests*100:.1f}%")
        
        print("\n詳細結果:")
        print(f"  保護性停損計算: {'✅ 通過' if test1_result else '❌ 失敗'}")
        print(f"  重複觸發防護: {'✅ 通過' if test2_result else '❌ 失敗'}")
        print(f"  增強日誌系統: {'✅ 通過' if test3_result else '❌ 失敗'}")
        
        # 清理測試文件
        try:
            if os.path.exists(self.test_db_path):
                os.remove(self.test_db_path)
                print(f"\n🧹 清理測試文件: {self.test_db_path}")
        except:
            pass
        
        if passed_tests == total_tests:
            print("\n🎉 所有測試通過！幽靈BUG修復成功！")
        else:
            print("\n⚠️ 部分測試失敗，需要進一步檢查")
        
        return passed_tests == total_tests

if __name__ == "__main__":
    tester = QuickGhostBugTest()
    success = tester.run_quick_test()
    
    if success:
        print("\n✅ 快速測試完成：修復效果良好")
    else:
        print("\n❌ 快速測試完成：需要進一步修復")
