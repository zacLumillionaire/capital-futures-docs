#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
🔧 集成診斷方法
可以直接添加到 simple_integrated.py 中的診斷方法
"""

import time
import threading
import sqlite3
from datetime import datetime, date
from typing import Dict, List, Optional, Any

def diagnose_async_updater_status(self):
    """診斷異步更新器狀態 - 添加到 simple_integrated.py"""
    try:
        print("\n🔍 異步更新器診斷:")
        
        if hasattr(self, 'multi_group_position_manager') and self.multi_group_position_manager:
            manager = self.multi_group_position_manager
            
            if hasattr(manager, 'async_updater') and manager.async_updater:
                updater = manager.async_updater
                print(f"  ✅ AsyncUpdater 存在")
                
                # 檢查隊列狀態
                if hasattr(updater, 'update_queue'):
                    try:
                        queue_size = len(updater.update_queue) if updater.update_queue else 0
                        print(f"  📊 更新隊列大小: {queue_size}")
                        
                        if queue_size > 10:
                            print(f"  ⚠️ 隊列積壓嚴重: {queue_size}個任務")
                        elif queue_size > 5:
                            print(f"  ⚠️ 隊列積壓中等: {queue_size}個任務")
                    except Exception as e:
                        print(f"  ❌ 隊列檢查失敗: {e}")
                
                # 檢查運行狀態
                if hasattr(updater, 'is_running'):
                    print(f"  📊 運行狀態: {updater.is_running}")
                    if not updater.is_running:
                        print(f"  ⚠️ 異步更新器未運行")
                
                # 檢查最後更新時間
                if hasattr(updater, 'last_update_time'):
                    if updater.last_update_time:
                        elapsed = time.time() - updater.last_update_time
                        print(f"  📊 最後更新: {elapsed:.1f}秒前")
                        if elapsed > 30:
                            print(f"  ⚠️ 更新延遲過久: {elapsed:.1f}秒")
                        elif elapsed > 10:
                            print(f"  ⚠️ 更新延遲中等: {elapsed:.1f}秒")
                    else:
                        print(f"  ⚠️ 從未更新過")
                
                # 檢查統計信息
                if hasattr(updater, 'get_stats'):
                    try:
                        stats = updater.get_stats()
                        print(f"  📊 更新統計: {stats}")
                    except Exception as e:
                        print(f"  ❌ 統計獲取失敗: {e}")
                
                # 檢查錯誤計數
                if hasattr(updater, 'error_count'):
                    error_count = getattr(updater, 'error_count', 0)
                    print(f"  📊 錯誤計數: {error_count}")
                    if error_count > 5:
                        print(f"  ⚠️ 錯誤過多: {error_count}次")
            
            else:
                print(f"  ❌ AsyncUpdater 不存在")
        else:
            print(f"  ❌ multi_group_position_manager 不存在")
            
    except Exception as e:
        print(f"  ❌ 異步更新器診斷失敗: {e}")

def diagnose_optimized_risk_manager_cache(self):
    """診斷OptimizedRiskManager緩存狀態 - 添加到 simple_integrated.py"""
    try:
        print("\n🔍 OptimizedRiskManager緩存診斷:")
        
        if hasattr(self, 'optimized_risk_manager') and self.optimized_risk_manager:
            manager = self.optimized_risk_manager
            print(f"  ✅ OptimizedRiskManager 存在")
            
            # 檢查問題部位
            problem_positions = [133, 134, 135]
            
            for position_id in problem_positions:
                position_id_str = str(position_id)
                print(f"  📊 部位{position_id}:")
                
                # 檢查position_cache
                if hasattr(manager, 'position_cache'):
                    in_position_cache = position_id_str in manager.position_cache
                    print(f"    - position_cache: {in_position_cache}")
                    
                    if in_position_cache:
                        try:
                            pos_data = manager.position_cache[position_id_str]
                            print(f"    - 緩存方向: {pos_data.get('direction', 'N/A')}")
                            print(f"    - 緩存狀態: {pos_data.get('status', 'N/A')}")
                            print(f"    - 入場價格: {pos_data.get('entry_price', 'N/A')}")
                        except Exception as e:
                            print(f"    - 緩存讀取錯誤: {e}")
                
                # 檢查stop_loss_cache
                if hasattr(manager, 'stop_loss_cache'):
                    in_stop_loss_cache = position_id_str in manager.stop_loss_cache
                    print(f"    - stop_loss_cache: {in_stop_loss_cache}")
                    if in_stop_loss_cache:
                        try:
                            stop_loss = manager.stop_loss_cache[position_id_str]
                            print(f"    - 停損價格: {stop_loss}")
                        except Exception as e:
                            print(f"    - 停損緩存讀取錯誤: {e}")
                
                # 檢查trailing_cache
                if hasattr(manager, 'trailing_cache'):
                    in_trailing_cache = position_id_str in manager.trailing_cache
                    print(f"    - trailing_cache: {in_trailing_cache}")
                    if in_trailing_cache:
                        try:
                            trailing_data = manager.trailing_cache[position_id_str]
                            print(f"    - 移動停利狀態: {trailing_data}")
                        except Exception as e:
                            print(f"    - 移動停利緩存讀取錯誤: {e}")
            
            # 檢查總體緩存大小
            print(f"  📊 總體緩存狀態:")
            if hasattr(manager, 'position_cache'):
                print(f"    - position_cache: {len(manager.position_cache)}個部位")
            if hasattr(manager, 'stop_loss_cache'):
                print(f"    - stop_loss_cache: {len(manager.stop_loss_cache)}個停損")
            if hasattr(manager, 'trailing_cache'):
                print(f"    - trailing_cache: {len(manager.trailing_cache)}個移動停利")
            
            # 檢查緩存鎖定狀態
            if hasattr(manager, 'cache_lock'):
                try:
                    # 嘗試獲取鎖定狀態（非阻塞）
                    lock_acquired = manager.cache_lock.acquire(blocking=False)
                    if lock_acquired:
                        manager.cache_lock.release()
                        print(f"    - cache_lock: 可用")
                    else:
                        print(f"    - cache_lock: 被鎖定")
                except Exception as e:
                    print(f"    - cache_lock檢查失敗: {e}")
            
        else:
            print(f"  ❌ optimized_risk_manager 不存在")
            
    except Exception as e:
        print(f"  ❌ 緩存診斷失敗: {e}")

def diagnose_simplified_tracker_status(self):
    """診斷SimplifiedOrderTracker狀態 - 添加到 simple_integrated.py"""
    try:
        print("\n🔍 SimplifiedOrderTracker診斷:")
        
        # 檢查stop_loss_executor
        if hasattr(self, 'stop_loss_executor') and self.stop_loss_executor:
            executor = self.stop_loss_executor
            print(f"  ✅ stop_loss_executor 存在")
            
            # 檢查simplified_tracker
            if hasattr(executor, 'simplified_tracker') and executor.simplified_tracker:
                tracker = executor.simplified_tracker
                print(f"  ✅ simplified_tracker 存在")
                
                # 檢查exit_groups
                if hasattr(tracker, 'exit_groups'):
                    exit_groups_count = len(tracker.exit_groups)
                    print(f"  📊 exit_groups: {exit_groups_count}個")
                    
                    # 檢查問題部位的exit_groups
                    problem_positions = [133, 134, 135]
                    for position_id in problem_positions:
                        if position_id in tracker.exit_groups:
                            try:
                                exit_group = tracker.exit_groups[position_id]
                                print(f"    - 部位{position_id}: 存在exit_group")
                                print(f"      方向: {exit_group.direction}")
                                print(f"      總口數: {exit_group.total_lots}")
                                if hasattr(exit_group, 'individual_retry_counts'):
                                    print(f"      追價次數: {exit_group.individual_retry_counts}")
                            except Exception as e:
                                print(f"    - 部位{position_id}: exit_group讀取錯誤: {e}")
                        else:
                            print(f"    - 部位{position_id}: 無exit_group")
                
                # 檢查global_exit_manager
                if hasattr(tracker, 'global_exit_manager'):
                    manager = tracker.global_exit_manager
                    print(f"  📊 global_exit_manager:")
                    
                    if hasattr(manager, 'exit_timeout'):
                        print(f"    - 鎖定超時: {manager.exit_timeout}秒")
                        if manager.exit_timeout < 1.0:
                            print(f"    ⚠️ 鎖定超時過短: {manager.exit_timeout}秒")
                    
                    if hasattr(manager, 'exit_locks'):
                        print(f"    - 當前鎖定: {len(manager.exit_locks)}個")
                        
                        # 顯示當前鎖定
                        for key, info in manager.exit_locks.items():
                            try:
                                elapsed = time.time() - info['timestamp']
                                print(f"      {key}: {elapsed:.1f}秒前 ({info.get('trigger_source', 'unknown')})")
                                if elapsed > manager.exit_timeout:
                                    print(f"        ⚠️ 鎖定已超時")
                            except Exception as e:
                                print(f"      {key}: 鎖定信息讀取錯誤: {e}")
                
                # 檢查data_lock狀態
                if hasattr(tracker, 'data_lock'):
                    try:
                        lock_acquired = tracker.data_lock.acquire(blocking=False)
                        if lock_acquired:
                            tracker.data_lock.release()
                            print(f"  📊 data_lock: 可用")
                        else:
                            print(f"  ⚠️ data_lock: 被鎖定")
                    except Exception as e:
                        print(f"  ❌ data_lock檢查失敗: {e}")
            
            else:
                print(f"  ❌ simplified_tracker 不存在")
        else:
            print(f"  ❌ stop_loss_executor 不存在")
            
    except Exception as e:
        print(f"  ❌ SimplifiedTracker診斷失敗: {e}")

def diagnose_database_query_performance(self):
    """診斷資料庫查詢性能 - 添加到 simple_integrated.py"""
    try:
        print("\n🔍 資料庫查詢性能診斷:")

        if hasattr(self, 'stop_loss_executor') and self.stop_loss_executor:
            executor = self.stop_loss_executor
            print(f"  ✅ stop_loss_executor 存在")

            # 測試查詢性能
            problem_positions = [133, 134, 135]

            for position_id in problem_positions:
                start_time = time.time()

                # 調用實際的查詢方法
                try:
                    if hasattr(executor, '_get_position_info'):
                        result = executor._get_position_info(position_id)
                        elapsed = (time.time() - start_time) * 1000

                        print(f"  📊 部位{position_id}查詢:")
                        print(f"    - 耗時: {elapsed:.1f}ms")
                        print(f"    - 結果: {'成功' if result else '失敗'}")

                        if elapsed > 100:
                            print(f"    ⚠️ 查詢延遲過高: {elapsed:.1f}ms")
                        elif elapsed > 50:
                            print(f"    ⚠️ 查詢延遲中等: {elapsed:.1f}ms")

                        if not result:
                            print(f"    ❌ 查詢失敗，需要詳細診斷")
                            
                            # 嘗試簡化查詢
                            simple_start = time.time()
                            simple_result = self._test_simple_position_query(position_id)
                            simple_elapsed = (time.time() - simple_start) * 1000
                            
                            print(f"    🔍 簡化查詢:")
                            print(f"      - 耗時: {simple_elapsed:.1f}ms")
                            print(f"      - 結果: {'成功' if simple_result else '失敗'}")
                    else:
                        print(f"  ❌ _get_position_info 方法不存在")
                        
                except Exception as e:
                    elapsed = (time.time() - start_time) * 1000
                    print(f"  ❌ 部位{position_id}查詢異常:")
                    print(f"    - 耗時: {elapsed:.1f}ms")
                    print(f"    - 錯誤: {e}")
        else:
            print(f"  ❌ stop_loss_executor 不存在")

    except Exception as e:
        print(f"  ❌ 資料庫查詢診斷失敗: {e}")

def _test_simple_position_query(self, position_id: int) -> Optional[Dict]:
    """測試簡化的部位查詢 - 輔助方法"""
    try:
        if hasattr(self, 'multi_group_db_manager'):
            with self.multi_group_db_manager.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    SELECT * FROM position_records 
                    WHERE id = ? AND status = 'ACTIVE'
                ''', (position_id,))
                
                row = cursor.fetchone()
                if row:
                    columns = [description[0] for description in cursor.description]
                    return dict(zip(columns, row))
                return None
    except Exception as e:
        print(f"    ❌ 簡化查詢失敗: {e}")
        return None

def run_comprehensive_diagnosis(self):
    """運行綜合診斷 - 添加到 simple_integrated.py"""
    print("\n" + "="*80)
    print("🚨 平倉問題綜合診斷")
    print("="*80)
    print(f"🕐 診斷時間: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

    try:
        # 運行所有診斷
        self.diagnose_async_updater_status()
        self.diagnose_optimized_risk_manager_cache()
        self.diagnose_simplified_tracker_status()
        self.diagnose_database_query_performance()
        
        # 額外的系統狀態檢查
        self._diagnose_system_resources()
        
    except Exception as e:
        print(f"❌ 診斷過程出錯: {e}")

    print("\n" + "="*80)
    print("🔍 診斷完成")
    print("="*80)

def _diagnose_system_resources(self):
    """診斷系統資源狀態 - 輔助方法"""
    try:
        print("\n🔍 系統資源診斷:")
        
        # 檢查線程數量
        thread_count = threading.active_count()
        print(f"  📊 活躍線程數: {thread_count}")
        if thread_count > 20:
            print(f"  ⚠️ 線程數量過多: {thread_count}")
        
        # 檢查資料庫連接
        if hasattr(self, 'multi_group_db_manager'):
            try:
                with self.multi_group_db_manager.get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute("SELECT COUNT(*) FROM position_records WHERE status = 'ACTIVE'")
                    active_positions = cursor.fetchone()[0]
                    print(f"  📊 活躍部位數: {active_positions}")
                    
                    cursor.execute("SELECT COUNT(*) FROM strategy_groups WHERE date = ?", (date.today().isoformat(),))
                    today_groups = cursor.fetchone()[0]
                    print(f"  📊 今日策略組: {today_groups}")
                    
            except Exception as e:
                print(f"  ❌ 資料庫連接檢查失敗: {e}")
        
        # 檢查內存使用（簡化版）
        import sys
        if hasattr(sys, 'getsizeof'):
            try:
                cache_size = 0
                if hasattr(self, 'optimized_risk_manager') and self.optimized_risk_manager:
                    if hasattr(self.optimized_risk_manager, 'position_cache'):
                        cache_size += sys.getsizeof(self.optimized_risk_manager.position_cache)
                print(f"  📊 緩存內存使用: {cache_size} bytes")
            except Exception as e:
                print(f"  ❌ 內存檢查失敗: {e}")
        
    except Exception as e:
        print(f"  ❌ 系統資源診斷失敗: {e}")


# 使用說明
"""
將以下方法添加到 simple_integrated.py 類中：

1. diagnose_async_updater_status(self)
2. diagnose_optimized_risk_manager_cache(self)  
3. diagnose_simplified_tracker_status(self)
4. diagnose_database_query_performance(self)
5. _test_simple_position_query(self, position_id: int)
6. run_comprehensive_diagnosis(self)
7. _diagnose_system_resources(self)

然後在 OnNotifyTicksLONG 方法中添加診斷觸發：

# 在報價處理延遲警告後添加
if quote_elapsed > 1000:  # 超過1秒才診斷
    print(f"[DIAGNOSTIC] 🚨 觸發緊急診斷")
    self.run_comprehensive_diagnosis()

# 定期診斷（每1000次報價）
if hasattr(self, 'diagnostic_counter'):
    self.diagnostic_counter += 1
else:
    self.diagnostic_counter = 1

if self.diagnostic_counter % 1000 == 0:
    print(f"[DIAGNOSTIC] 📊 定期診斷 (第{self.diagnostic_counter}次報價)")
    self.run_comprehensive_diagnosis()
"""
