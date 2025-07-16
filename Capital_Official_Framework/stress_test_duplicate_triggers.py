#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
重複觸發壓力測試工具
專門測試OptimizedRiskManager在高頻報價環境下的重複觸發防護機制
"""

import os
import sys
import time
import threading
import concurrent.futures
from datetime import datetime
from typing import Dict, List

# 添加當前目錄到路徑
current_dir = os.path.dirname(os.path.abspath(__file__))
if current_dir not in sys.path:
    sys.path.insert(0, current_dir)

from optimized_risk_manager import OptimizedRiskManager
from multi_group_database import MultiGroupDatabaseManager

class StressTestDuplicateTriggers:
    """重複觸發壓力測試器"""
    
    def __init__(self):
        self.test_db_path = "test_stress_duplicate_triggers.db"
        self.db_manager = None
        self.risk_manager = None
        
        # 測試統計
        self.trigger_counts = {}
        self.execution_counts = {}
        self.test_results = []
        
        print("🔥 重複觸發壓力測試工具初始化")
        print("=" * 60)
    
    def setup_test_environment(self):
        """設置測試環境"""
        try:
            # 清理舊的測試資料庫
            if os.path.exists(self.test_db_path):
                os.remove(self.test_db_path)

            # 初始化資料庫管理器
            self.db_manager = MultiGroupDatabaseManager(self.test_db_path)

            # 確保資料庫表結構完整
            self._ensure_database_schema()

            # 初始化風險管理器
            self.risk_manager = OptimizedRiskManager(
                self.db_manager, console_enabled=True
            )

            print("✅ 壓力測試環境設置完成")
            return True

        except Exception as e:
            print(f"❌ 測試環境設置失敗: {e}")
            import traceback
            print(f"詳細錯誤: {traceback.format_exc()}")
            return False

    def _ensure_database_schema(self):
        """確保資料庫表結構完整"""
        import sqlite3

        with self.db_manager.get_connection() as conn:
            cursor = conn.cursor()

            # 檢查並添加缺少的欄位
            try:
                cursor.execute("SELECT realized_pnl FROM position_records LIMIT 1")
            except sqlite3.OperationalError:
                cursor.execute("ALTER TABLE position_records ADD COLUMN realized_pnl REAL")
                print("✅ 添加realized_pnl欄位")

            try:
                cursor.execute("SELECT exit_price FROM position_records LIMIT 1")
            except sqlite3.OperationalError:
                cursor.execute("ALTER TABLE position_records ADD COLUMN exit_price REAL")
                print("✅ 添加exit_price欄位")

            conn.commit()
    
    def create_test_positions(self, count: int = 10):
        """創建測試部位"""
        print(f"📍 創建{count}個測試部位...")
        
        for i in range(count):
            position_id = str(100 + i)
            position_data = {
                'id': 100 + i,
                'group_id': 1,
                'direction': 'LONG',
                'entry_price': 21500 + i,
                'quantity': 1,
                'lot_id': i + 1
            }
            
            # 添加到風險管理器緩存
            self.risk_manager.position_cache[position_id] = position_data
            self.risk_manager.trailing_cache[position_id] = {
                'activated': True,
                'peak_price': 21530 + i,
                'direction': 'LONG'
            }
            
            # 初始化計數器
            self.trigger_counts[position_id] = 0
            self.execution_counts[position_id] = 0
        
        print(f"✅ {count}個測試部位創建完成")
    
    def mock_execution_methods(self):
        """模擬執行方法，記錄觸發次數"""
        
        def mock_trailing_stop_exit(trigger_info):
            position_id = trigger_info['position_id']
            self.execution_counts[position_id] += 1
            thread_name = threading.current_thread().name
            print(f"🚀 移動停利執行: 部位{position_id} (第{self.execution_counts[position_id]}次) [線程: {thread_name}]")
            time.sleep(0.001)  # 模擬執行時間
            return True
        
        def mock_stop_loss_exit(trigger_info):
            position_id = trigger_info['position_id']
            self.execution_counts[position_id] += 1
            thread_name = threading.current_thread().name
            print(f"🛡️ 停損執行: 部位{position_id} (第{self.execution_counts[position_id]}次) [線程: {thread_name}]")
            time.sleep(0.001)  # 模擬執行時間
            return True
        
        # 替換執行方法
        self.original_trailing_method = self.risk_manager._execute_trailing_stop_exit
        self.original_stop_method = getattr(self.risk_manager, '_execute_stop_loss_exit', None)
        
        self.risk_manager._execute_trailing_stop_exit = mock_trailing_stop_exit
        if self.original_stop_method:
            self.risk_manager._execute_stop_loss_exit = mock_stop_loss_exit
    
    def restore_execution_methods(self):
        """恢復原始執行方法"""
        self.risk_manager._execute_trailing_stop_exit = self.original_trailing_method
        if self.original_stop_method:
            self.risk_manager._execute_stop_loss_exit = self.original_stop_method
    
    def high_frequency_quote_simulation(self, duration_seconds: int = 5, quote_interval: float = 0.001):
        """高頻報價模擬"""
        print(f"📈 開始高頻報價模擬 (持續{duration_seconds}秒，間隔{quote_interval*1000:.1f}ms)")
        
        start_time = time.time()
        quote_count = 0
        
        while time.time() - start_time < duration_seconds:
            # 觸發移動停利的價格
            current_price = 21520
            
            try:
                result = self.risk_manager.update_price(current_price)
                quote_count += 1
                
                if quote_count % 100 == 0:
                    print(f"   已處理{quote_count}次報價...")
                
            except Exception as e:
                print(f"❌ 報價處理異常: {e}")
            
            time.sleep(quote_interval)
        
        print(f"✅ 高頻報價模擬完成，共處理{quote_count}次報價")
        return quote_count
    
    def concurrent_quote_simulation(self, thread_count: int = 5, quotes_per_thread: int = 100):
        """並發報價模擬"""
        print(f"🔀 開始並發報價模擬 ({thread_count}個線程，每線程{quotes_per_thread}次報價)")
        
        def worker_thread(thread_id):
            thread_name = f"QuoteThread-{thread_id}"
            threading.current_thread().name = thread_name
            
            for i in range(quotes_per_thread):
                try:
                    current_price = 21520 + (i % 10)  # 輕微價格變動
                    result = self.risk_manager.update_price(current_price)
                    time.sleep(0.001)  # 1ms間隔
                except Exception as e:
                    print(f"❌ 線程{thread_id}報價處理異常: {e}")
        
        # 啟動並發線程
        with concurrent.futures.ThreadPoolExecutor(max_workers=thread_count) as executor:
            futures = [executor.submit(worker_thread, i) for i in range(thread_count)]
            concurrent.futures.wait(futures)
        
        print(f"✅ 並發報價模擬完成")
    
    def analyze_results(self):
        """分析測試結果"""
        print("\n📊 測試結果分析")
        print("-" * 50)
        
        total_positions = len(self.execution_counts)
        total_executions = sum(self.execution_counts.values())
        max_executions = max(self.execution_counts.values()) if self.execution_counts else 0
        
        print(f"測試部位數量: {total_positions}")
        print(f"總執行次數: {total_executions}")
        print(f"最大單部位執行次數: {max_executions}")
        print(f"平均每部位執行次數: {total_executions/total_positions:.2f}")
        
        # 檢查重複觸發情況
        duplicate_positions = [pos_id for pos_id, count in self.execution_counts.items() if count > 1]
        
        print(f"\n重複觸發部位數量: {len(duplicate_positions)}")
        if duplicate_positions:
            print("重複觸發詳情:")
            for pos_id in duplicate_positions:
                print(f"  部位{pos_id}: {self.execution_counts[pos_id]}次執行")
        
        # 檢查處理中狀態
        remaining_exiting = len(self.risk_manager.exiting_positions)
        print(f"\n剩餘處理中狀態: {remaining_exiting}個")
        if remaining_exiting > 0:
            print(f"處理中部位: {list(self.risk_manager.exiting_positions)}")
        
        # 評估測試結果
        success_criteria = {
            'no_excessive_duplicates': max_executions <= 2,  # 最多允許2次執行（考慮競態條件）
            'clean_exit_state': remaining_exiting == 0,      # 處理中狀態應該清空
            'reasonable_total': total_executions <= total_positions * 2  # 總執行次數合理
        }
        
        all_passed = all(success_criteria.values())
        
        print(f"\n✅ 測試評估:")
        for criterion, passed in success_criteria.items():
            status = "✅ 通過" if passed else "❌ 失敗"
            print(f"  {criterion}: {status}")
        
        return {
            'all_passed': all_passed,
            'total_positions': total_positions,
            'total_executions': total_executions,
            'max_executions': max_executions,
            'duplicate_positions': len(duplicate_positions),
            'remaining_exiting': remaining_exiting,
            'success_criteria': success_criteria
        }
    
    def run_stress_test(self):
        """運行壓力測試"""
        print("🔥 開始重複觸發壓力測試")
        print("=" * 60)
        
        if not self.setup_test_environment():
            return
        
        try:
            # 創建測試部位
            self.create_test_positions(10)
            
            # 設置模擬執行方法
            self.mock_execution_methods()
            
            # 測試1：高頻報價測試
            print("\n🧪 測試1：高頻報價測試")
            quote_count = self.high_frequency_quote_simulation(duration_seconds=3, quote_interval=0.001)
            
            # 重置計數器
            for pos_id in self.execution_counts:
                self.execution_counts[pos_id] = 0
            
            # 測試2：並發報價測試
            print("\n🧪 測試2：並發報價測試")
            self.concurrent_quote_simulation(thread_count=3, quotes_per_thread=50)
            
            # 分析結果
            results = self.analyze_results()
            
            # 恢復原始方法
            self.restore_execution_methods()
            
            # 生成報告
            self.generate_stress_test_report(results)
            
        except Exception as e:
            print(f"❌ 壓力測試異常: {e}")
            import traceback
            traceback.print_exc()
    
    def generate_stress_test_report(self, results):
        """生成壓力測試報告"""
        print("\n" + "=" * 60)
        print("📋 重複觸發壓力測試報告")
        print("=" * 60)
        
        status = "✅ 通過" if results['all_passed'] else "❌ 失敗"
        print(f"總體結果: {status}")
        print()
        
        # 保存報告到文件
        report_file = f"stress_test_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
        with open(report_file, 'w', encoding='utf-8') as f:
            f.write("重複觸發壓力測試報告\n")
            f.write("=" * 60 + "\n")
            f.write(f"測試時間: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
            f.write(f"總體結果: {'通過' if results['all_passed'] else '失敗'}\n\n")
            
            f.write("測試統計:\n")
            f.write(f"  測試部位數量: {results['total_positions']}\n")
            f.write(f"  總執行次數: {results['total_executions']}\n")
            f.write(f"  最大單部位執行次數: {results['max_executions']}\n")
            f.write(f"  重複觸發部位數量: {results['duplicate_positions']}\n")
            f.write(f"  剩餘處理中狀態: {results['remaining_exiting']}\n\n")
            
            f.write("成功標準評估:\n")
            for criterion, passed in results['success_criteria'].items():
                f.write(f"  {criterion}: {'通過' if passed else '失敗'}\n")
        
        print(f"📄 詳細報告已保存至: {report_file}")
        
        if results['all_passed']:
            print("🎉 重複觸發防護機制運行正常！")
        else:
            print("⚠️ 重複觸發防護機制需要進一步優化")

if __name__ == "__main__":
    tester = StressTestDuplicateTriggers()
    tester.run_stress_test()
