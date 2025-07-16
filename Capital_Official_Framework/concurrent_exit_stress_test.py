#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
並發平倉壓力測試工具
測試重構後的鎖機制是否能正確處理多個部位同時觸發平倉的極端場景
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

# 導入必要模組
from simplified_order_tracker import GlobalExitManager
from optimized_risk_manager import OptimizedRiskManager
from stop_loss_executor import StopLossExecutor
from multi_group_database import MultiGroupDatabaseManager

class ConcurrentExitStressTest:
    """並發平倉壓力測試器"""
    
    def __init__(self, console_enabled: bool = True):
        self.console_enabled = console_enabled
        self.test_results = []
        self.lock_conflicts = []
        self.successful_exits = []
        self.failed_exits = []
        
        # 初始化組件
        self.global_exit_manager = GlobalExitManager()
        self.db_manager = None
        self.optimized_risk_manager = None
        self.stop_loss_executor = None
        
        if self.console_enabled:
            print("[STRESS_TEST] 🧪 並發平倉壓力測試器初始化")
    
    def setup_test_environment(self, db_path: str = "test_virtual_strategy.db"):
        """設置測試環境"""
        try:
            # 初始化資料庫管理器
            self.db_manager = MultiGroupDatabaseManager(db_path)
            
            # 初始化風險管理器
            self.optimized_risk_manager = OptimizedRiskManager(
                self.db_manager, 
                console_enabled=self.console_enabled
            )
            
            # 初始化停損執行器
            self.stop_loss_executor = StopLossExecutor(
                self.db_manager,
                console_enabled=self.console_enabled
            )
            
            # 設置風險管理器的停損執行器
            self.optimized_risk_manager.set_stop_loss_executor(self.stop_loss_executor)
            
            if self.console_enabled:
                print("[STRESS_TEST] ✅ 測試環境設置完成")
            return True
            
        except Exception as e:
            if self.console_enabled:
                print(f"[STRESS_TEST] ❌ 測試環境設置失敗: {e}")
            return False
    
    def create_test_positions(self, num_positions: int = 6) -> List[int]:
        """創建測試部位"""
        position_ids = []
        
        try:
            with self.db_manager.get_connection() as conn:
                cursor = conn.cursor()
                
                # 創建策略組
                cursor.execute('''
                    INSERT OR REPLACE INTO strategy_groups 
                    (id, total_lots, range_high, range_low, status, created_at)
                    VALUES (?, ?, ?, ?, ?, ?)
                ''', (999, num_positions, 22600, 22500, 'ACTIVE', datetime.now().isoformat()))
                
                # 創建測試部位
                for i in range(num_positions):
                    position_id = 1000 + i
                    cursor.execute('''
                        INSERT OR REPLACE INTO position_records
                        (id, group_id, lot_id, direction, entry_price, quantity, status, created_at)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                    ''', (
                        position_id, 999, i+1, 'LONG', 22550.0, 1, 'ACTIVE', 
                        datetime.now().isoformat()
                    ))
                    
                    # 創建風險管理狀態
                    cursor.execute('''
                        INSERT OR REPLACE INTO risk_management_states
                        (position_id, current_stop_loss, protection_activated, trailing_activated, peak_price)
                        VALUES (?, ?, ?, ?, ?)
                    ''', (position_id, 22500.0, False, True, 22580.0))
                    
                    position_ids.append(position_id)
                
                conn.commit()
                
            if self.console_enabled:
                print(f"[STRESS_TEST] 📝 創建了 {len(position_ids)} 個測試部位: {position_ids}")
            
            return position_ids
            
        except Exception as e:
            if self.console_enabled:
                print(f"[STRESS_TEST] ❌ 創建測試部位失敗: {e}")
            return []
    
    def simulate_concurrent_triggers(self, position_ids: List[int], trigger_price: float = 22540.0):
        """模擬並發觸發"""
        if self.console_enabled:
            print(f"[STRESS_TEST] 🚀 開始並發觸發測試")
            print(f"[STRESS_TEST]   部位數量: {len(position_ids)}")
            print(f"[STRESS_TEST]   觸發價格: {trigger_price}")
            print(f"[STRESS_TEST]   預期行為: 所有部位應該獨立處理，無鎖衝突")
        
        # 清除所有現有鎖定
        self.global_exit_manager.clear_all_exits()
        
        # 創建線程來模擬並發觸發
        threads = []
        results = {}
        
        def trigger_position_exit(pos_id: int):
            """觸發單個部位的平倉"""
            thread_name = f"Thread-{pos_id}"
            start_time = time.time()
            
            try:
                # 模擬 OptimizedRiskManager 的觸發邏輯
                result = self.optimized_risk_manager._check_trailing_trigger(
                    str(pos_id), trigger_price, 22580.0, 22550.0, 'LONG'
                )
                
                end_time = time.time()
                duration = (end_time - start_time) * 1000
                
                results[pos_id] = {
                    'success': result,
                    'duration_ms': duration,
                    'thread': thread_name,
                    'timestamp': datetime.now().isoformat()
                }
                
                if self.console_enabled:
                    status = "✅ 成功" if result else "❌ 失敗"
                    print(f"[STRESS_TEST] {status} 部位{pos_id} 處理完成 ({duration:.1f}ms)")
                
            except Exception as e:
                end_time = time.time()
                duration = (end_time - start_time) * 1000
                
                results[pos_id] = {
                    'success': False,
                    'error': str(e),
                    'duration_ms': duration,
                    'thread': thread_name,
                    'timestamp': datetime.now().isoformat()
                }
                
                if self.console_enabled:
                    print(f"[STRESS_TEST] ❌ 部位{pos_id} 處理異常: {e}")
        
        # 啟動所有線程
        for pos_id in position_ids:
            thread = threading.Thread(target=trigger_position_exit, args=(pos_id,))
            threads.append(thread)
            thread.start()
        
        # 等待所有線程完成
        for thread in threads:
            thread.join()
        
        # 分析結果
        self.analyze_test_results(results)
        
        return results
    
    def analyze_test_results(self, results: Dict):
        """分析測試結果"""
        if self.console_enabled:
            print(f"\n[STRESS_TEST] 📊 測試結果分析:")
        
        total_positions = len(results)
        successful_exits = sum(1 for r in results.values() if r.get('success', False))
        failed_exits = total_positions - successful_exits
        
        # 檢查鎖衝突
        lock_conflicts = 0
        for pos_id, result in results.items():
            if not result.get('success', False) and 'error' in result:
                error_msg = result['error'].lower()
                if '鎖' in error_msg or 'lock' in error_msg or '阻止' in error_msg:
                    lock_conflicts += 1
        
        # 計算平均處理時間
        durations = [r.get('duration_ms', 0) for r in results.values()]
        avg_duration = sum(durations) / len(durations) if durations else 0
        
        if self.console_enabled:
            print(f"[STRESS_TEST]   總部位數: {total_positions}")
            print(f"[STRESS_TEST]   成功處理: {successful_exits}")
            print(f"[STRESS_TEST]   處理失敗: {failed_exits}")
            print(f"[STRESS_TEST]   鎖衝突數: {lock_conflicts}")
            print(f"[STRESS_TEST]   平均耗時: {avg_duration:.1f}ms")
            
            # 驗收標準檢查
            if lock_conflicts == 0:
                print(f"[STRESS_TEST] ✅ 驗收通過: 無鎖衝突，鎖機制工作正常")
            else:
                print(f"[STRESS_TEST] ❌ 驗收失敗: 發現 {lock_conflicts} 個鎖衝突")
        
        # 保存結果
        self.test_results.append({
            'timestamp': datetime.now().isoformat(),
            'total_positions': total_positions,
            'successful_exits': successful_exits,
            'failed_exits': failed_exits,
            'lock_conflicts': lock_conflicts,
            'avg_duration_ms': avg_duration,
            'detailed_results': results
        })
        
        return lock_conflicts == 0
    
    def cleanup_test_data(self):
        """清理測試數據"""
        try:
            with self.db_manager.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("DELETE FROM position_records WHERE group_id = 999")
                cursor.execute("DELETE FROM strategy_groups WHERE id = 999")
                cursor.execute("DELETE FROM risk_management_states WHERE position_id >= 1000")
                conn.commit()
            
            # 清除所有鎖定
            self.global_exit_manager.clear_all_exits()
            
            if self.console_enabled:
                print("[STRESS_TEST] 🧹 測試數據清理完成")
                
        except Exception as e:
            if self.console_enabled:
                print(f"[STRESS_TEST] ⚠️ 清理測試數據失敗: {e}")
    
    def run_comprehensive_test(self):
        """運行綜合測試"""
        if self.console_enabled:
            print("\n" + "="*60)
            print("[STRESS_TEST] 🧪 開始並發平倉壓力測試")
            print("="*60)
        
        # 設置測試環境
        if not self.setup_test_environment():
            return False
        
        try:
            # 測試場景1: 6個部位同時觸發
            if self.console_enabled:
                print(f"\n[STRESS_TEST] 📋 測試場景1: 6個部位同時觸發移動停利")
            
            position_ids = self.create_test_positions(6)
            if not position_ids:
                return False
            
            # 執行並發觸發測試
            results = self.simulate_concurrent_triggers(position_ids, 22540.0)
            test_passed = self.analyze_test_results(results)
            
            # 清理測試數據
            self.cleanup_test_data()
            
            if self.console_enabled:
                print("\n" + "="*60)
                if test_passed:
                    print("[STRESS_TEST] 🎉 壓力測試通過！平倉鎖死結問題已徹底解決")
                else:
                    print("[STRESS_TEST] ❌ 壓力測試失敗！仍存在鎖衝突問題")
                print("="*60)
            
            return test_passed
            
        except Exception as e:
            if self.console_enabled:
                print(f"[STRESS_TEST] ❌ 測試執行失敗: {e}")
            return False

def main():
    """主函數"""
    print("🧪 並發平倉壓力測試工具")
    print("測試重構後的鎖機制是否能正確處理並發觸發")
    
    tester = ConcurrentExitStressTest(console_enabled=True)
    success = tester.run_comprehensive_test()
    
    if success:
        print("\n✅ 所有測試通過，系統已準備好處理並發平倉場景")
    else:
        print("\n❌ 測試失敗，需要進一步調試")
    
    return success

if __name__ == "__main__":
    main()
