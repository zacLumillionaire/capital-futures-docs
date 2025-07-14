#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
快速異步檢查工具 - 診斷緩存命中增加但失敗任務也增加的問題
"""

import time
import threading
import sqlite3
import os
from datetime import datetime

def quick_async_check(main_app):
    """快速檢查異步更新器狀態"""
    print("\n🔍 快速異步檢查開始...")
    print("=" * 60)
    
    results = {
        'async_updater_status': False,
        'database_connection': False,
        'worker_thread_status': False,
        'queue_status': False,
        'cache_status': False,
        'lock_status': False
    }
    
    # 1. 檢查異步更新器
    print("📋 步驟1: 檢查異步更新器...")
    if hasattr(main_app, 'async_updater') and main_app.async_updater:
        updater = main_app.async_updater
        print(f"   ✅ 異步更新器存在")
        
        # 檢查統計信息
        if hasattr(updater, 'stats'):
            stats = updater.stats
            print(f"   📊 統計信息:")
            print(f"      - 總任務: {stats.get('total_tasks', 0)}")
            print(f"      - 完成任務: {stats.get('completed_tasks', 0)}")
            print(f"      - 失敗任務: {stats.get('failed_tasks', 0)}")
            print(f"      - 緩存命中: {stats.get('cache_hits', 0)}")
            
            total = stats.get('total_tasks', 0)
            completed = stats.get('completed_tasks', 0)
            failed = stats.get('failed_tasks', 0)
            
            if total > 0:
                success_rate = (completed / total) * 100
                failure_rate = (failed / total) * 100
                print(f"      - 成功率: {success_rate:.1f}%")
                print(f"      - 失敗率: {failure_rate:.1f}%")
                
                if failure_rate > 5:
                    print(f"   ⚠️ 警告: 失敗率過高 ({failure_rate:.1f}%)")
                else:
                    print(f"   ✅ 失敗率正常 ({failure_rate:.1f}%)")
            
        results['async_updater_status'] = True
    else:
        print("   ❌ 異步更新器不存在")
    
    # 2. 檢查工作線程
    print("\n📋 步驟2: 檢查工作線程...")
    if hasattr(main_app, 'async_updater') and main_app.async_updater:
        updater = main_app.async_updater
        if hasattr(updater, 'worker_thread'):
            thread = updater.worker_thread
            if thread and thread.is_alive():
                print(f"   ✅ 工作線程活躍")
                results['worker_thread_status'] = True
            else:
                print(f"   ❌ 工作線程未活躍")
        else:
            print(f"   ❌ 工作線程不存在")
    
    # 3. 檢查任務隊列
    print("\n📋 步驟3: 檢查任務隊列...")
    if hasattr(main_app, 'async_updater') and main_app.async_updater:
        updater = main_app.async_updater
        if hasattr(updater, 'task_queue'):
            queue_size = updater.task_queue.qsize()
            print(f"   📊 隊列大小: {queue_size}")
            
            if queue_size > 100:
                print(f"   ⚠️ 警告: 隊列過大 ({queue_size})")
            elif queue_size > 50:
                print(f"   ⚠️ 注意: 隊列較大 ({queue_size})")
            else:
                print(f"   ✅ 隊列大小正常 ({queue_size})")
                
            results['queue_status'] = True
        else:
            print(f"   ❌ 任務隊列不存在")
    
    # 4. 檢查數據庫連接
    print("\n📋 步驟4: 檢查數據庫連接...")
    results['database_connection'] = check_database_connection(main_app)
    
    # 5. 檢查緩存狀態
    print("\n📋 步驟5: 檢查緩存狀態...")
    results['cache_status'] = check_cache_status(main_app)
    
    # 6. 檢查鎖定狀態
    print("\n📋 步驟6: 檢查鎖定狀態...")
    results['lock_status'] = check_lock_status(main_app)
    
    # 總結
    print("\n📊 檢查結果總結:")
    print("=" * 60)
    
    total_checks = len(results)
    passed_checks = sum(1 for v in results.values() if v)
    
    for check, status in results.items():
        status_icon = "✅" if status else "❌"
        print(f"   {status_icon} {check}: {'正常' if status else '異常'}")
    
    print(f"\n🎯 總體狀態: {passed_checks}/{total_checks} 項檢查通過")
    
    if passed_checks == total_checks:
        print("✅ 系統狀態良好")
    elif passed_checks >= total_checks * 0.8:
        print("⚠️ 系統狀態一般，建議檢查異常項目")
    else:
        print("❌ 系統狀態異常，需要立即處理")
    
    return results

def check_database_connection(main_app):
    """檢查數據庫連接"""
    try:
        db_path = "multi_group_strategy.db"
        if not os.path.exists(db_path):
            print("   ❌ 資料庫檔案不存在")
            return False
        
        # 測試基本連接
        conn = sqlite3.connect(db_path, timeout=5.0)
        cursor = conn.cursor()
        
        # 測試基本查詢
        cursor.execute("SELECT COUNT(*) FROM sqlite_master WHERE type='table'")
        table_count = cursor.fetchone()[0]
        print(f"   📊 資料庫表數量: {table_count}")
        
        # 測試寫入
        cursor.execute("CREATE TABLE IF NOT EXISTS connection_test (id INTEGER, timestamp TEXT)")
        cursor.execute("INSERT INTO connection_test VALUES (1, ?)", (datetime.now().isoformat(),))
        cursor.execute("DELETE FROM connection_test WHERE id = 1")
        
        conn.commit()
        conn.close()
        
        print("   ✅ 資料庫連接正常")
        return True
        
    except Exception as e:
        print(f"   ❌ 資料庫連接失敗: {e}")
        return False

def check_cache_status(main_app):
    """檢查緩存狀態"""
    try:
        cache_checks = 0
        cache_passed = 0
        
        # 檢查OptimizedRiskManager緩存
        if hasattr(main_app, 'optimized_risk_manager') and main_app.optimized_risk_manager:
            manager = main_app.optimized_risk_manager
            cache_checks += 1
            
            if hasattr(manager, 'position_cache'):
                pos_count = len(manager.position_cache)
                stop_count = len(getattr(manager, 'stop_loss_cache', {}))
                trail_count = len(getattr(manager, 'trailing_cache', {}))
                
                print(f"   📊 OptimizedRiskManager緩存:")
                print(f"      - 部位緩存: {pos_count} 項")
                print(f"      - 停損緩存: {stop_count} 項")
                print(f"      - 移動停利緩存: {trail_count} 項")
                
                cache_passed += 1
        
        # 檢查AsyncUpdater緩存
        if hasattr(main_app, 'async_updater') and main_app.async_updater:
            updater = main_app.async_updater
            cache_checks += 1
            
            if hasattr(updater, 'memory_cache'):
                cache = updater.memory_cache
                print(f"   📊 AsyncUpdater緩存:")
                for cache_type, cache_data in cache.items():
                    if isinstance(cache_data, dict):
                        print(f"      - {cache_type}: {len(cache_data)} 項")
                
                cache_passed += 1
        
        if cache_checks > 0:
            print(f"   ✅ 緩存檢查: {cache_passed}/{cache_checks} 項正常")
            return cache_passed == cache_checks
        else:
            print("   ⚠️ 未找到緩存組件")
            return False
            
    except Exception as e:
        print(f"   ❌ 緩存檢查失敗: {e}")
        return False

def check_lock_status(main_app):
    """檢查鎖定狀態"""
    try:
        lock_checks = 0
        lock_passed = 0
        
        # 檢查GlobalExitManager鎖定
        if hasattr(main_app, 'multi_group_position_manager') and main_app.multi_group_position_manager:
            if hasattr(main_app.multi_group_position_manager, 'simplified_tracker'):
                tracker = main_app.multi_group_position_manager.simplified_tracker
                if hasattr(tracker, 'global_exit_manager'):
                    manager = tracker.global_exit_manager
                    lock_checks += 1
                    
                    if hasattr(manager, 'exit_locks'):
                        lock_count = len(manager.exit_locks)
                        print(f"   📊 GlobalExitManager鎖定: {lock_count} 項")
                        
                        if lock_count > 10:
                            print(f"   ⚠️ 警告: 鎖定數量較多 ({lock_count})")
                        else:
                            print(f"   ✅ 鎖定數量正常 ({lock_count})")
                        
                        # 檢查過期鎖定
                        current_time = time.time()
                        expired_count = 0
                        for pos_id, lock_info in manager.exit_locks.items():
                            if current_time - lock_info.get('timestamp', 0) > 300:  # 5分鐘
                                expired_count += 1
                        
                        if expired_count > 0:
                            print(f"   ⚠️ 發現 {expired_count} 個過期鎖定")
                        
                        lock_passed += 1
        
        if lock_checks > 0:
            print(f"   ✅ 鎖定檢查: {lock_passed}/{lock_checks} 項正常")
            return lock_passed == lock_checks
        else:
            print("   ⚠️ 未找到鎖定組件")
            return False
            
    except Exception as e:
        print(f"   ❌ 鎖定檢查失敗: {e}")
        return False

def enable_detailed_logging(main_app):
    """啟用詳細日誌"""
    try:
        print("\n🔧 啟用詳細日誌...")
        
        if hasattr(main_app, 'async_updater') and main_app.async_updater:
            updater = main_app.async_updater
            if hasattr(updater, 'set_log_options'):
                updater.set_log_options(enable_task_logs=True)
                print("   ✅ AsyncUpdater詳細日誌已啟用")
            else:
                print("   ⚠️ AsyncUpdater不支援日誌選項")
        
        print("   💡 建議監控Console輸出以查看詳細錯誤信息")
        return True
        
    except Exception as e:
        print(f"   ❌ 啟用詳細日誌失敗: {e}")
        return False

def restart_async_updater(main_app):
    """重啟異步更新器"""
    try:
        print("\n🔄 重啟異步更新器...")
        
        if hasattr(main_app, 'async_updater') and main_app.async_updater:
            updater = main_app.async_updater
            
            # 停止現有更新器
            if hasattr(updater, 'stop'):
                updater.stop()
                print("   ✅ 已停止現有異步更新器")
            
            # 等待一下
            time.sleep(1)
            
            # 重新啟動
            if hasattr(updater, 'start'):
                updater.start()
                print("   ✅ 已重新啟動異步更新器")
            else:
                print("   ⚠️ 需要手動重新創建異步更新器")
            
            return True
        else:
            print("   ❌ 異步更新器不存在")
            return False
            
    except Exception as e:
        print(f"   ❌ 重啟異步更新器失敗: {e}")
        return False

if __name__ == "__main__":
    print("快速異步檢查工具")
    print("請在 simple_integrated.py 中調用此模組的函數")
