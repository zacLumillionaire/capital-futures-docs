#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
🚀 快速異步檢查工具
用於快速檢查異步更新器的當前狀態和錯誤
"""

def quick_async_check(simple_integrated_app):
    """快速檢查異步更新器狀態"""
    print("🚀 快速異步檢查開始...")
    print("=" * 50)
    
    # 檢查異步更新器是否存在
    async_updater = getattr(simple_integrated_app, 'async_updater', None)
    if not async_updater:
        print("❌ 異步更新器不存在")
        return
    
    print("✅ 異步更新器存在")
    
    # 獲取統計信息
    try:
        stats = async_updater.get_stats()
        print("\n📊 當前統計:")
        print(f"   總任務: {stats.get('total_tasks', 0)}")
        print(f"   完成任務: {stats.get('completed_tasks', 0)}")
        print(f"   失敗任務: {stats.get('failed_tasks', 0)}")
        print(f"   緩存命中: {stats.get('cache_hits', 0)}")
        
        total = stats.get('total_tasks', 0)
        if total > 0:
            success_rate = (stats.get('completed_tasks', 0) / total) * 100
            print(f"   成功率: {success_rate:.1f}%")
            
            # 檢查異常模式
            cache_hits = stats.get('cache_hits', 0)
            failed_tasks = stats.get('failed_tasks', 0)
            
            if cache_hits > 0 and failed_tasks > 0:
                print(f"\n⚠️ 發現問題模式:")
                print(f"   緩存命中 {cache_hits} 次但失敗 {failed_tasks} 次")
                print(f"   這表明緩存讀取成功但數據庫寫入失敗")
                
    except Exception as e:
        print(f"❌ 獲取統計失敗: {e}")
    
    # 檢查工作線程
    worker_thread = getattr(async_updater, 'worker_thread', None)
    if worker_thread:
        print(f"\n🧵 工作線程狀態:")
        print(f"   活躍: {worker_thread.is_alive()}")
        print(f"   名稱: {worker_thread.name}")
    else:
        print("\n❌ 工作線程不存在")
    
    # 檢查隊列
    try:
        queue = getattr(async_updater, 'update_queue', None)
        if queue:
            queue_size = queue.qsize()
            print(f"\n📋 隊列狀態:")
            print(f"   當前大小: {queue_size}")
            if queue_size > 50:
                print(f"   ⚠️ 隊列積壓嚴重")
    except Exception as e:
        print(f"❌ 檢查隊列失敗: {e}")
    
    # 檢查運行狀態
    running = getattr(async_updater, 'running', False)
    print(f"\n🔄 運行狀態: {running}")
    
    if not running:
        print("❌ 異步更新器未運行")
        print("💡 嘗試重啟: async_updater.start()")
    
    print("\n" + "=" * 50)
    print("🔍 如需詳細診斷，請運行:")
    print("from async_failure_diagnostic import run_diagnostic_on_simple_integrated")
    print("run_diagnostic_on_simple_integrated(self)")

def enable_detailed_logging(simple_integrated_app):
    """啟用詳細日誌記錄"""
    async_updater = getattr(simple_integrated_app, 'async_updater', None)
    if not async_updater:
        print("❌ 異步更新器不存在")
        return
    
    try:
        # 啟用詳細日誌
        async_updater.set_log_options(enable_task_logs=True, enable_peak_logs=True)
        async_updater.console_enabled = True
        print("✅ 已啟用詳細日誌記錄")
        print("💡 現在可以看到具體的錯誤信息")
    except Exception as e:
        print(f"❌ 啟用日誌失敗: {e}")

def restart_async_updater(simple_integrated_app):
    """重啟異步更新器"""
    async_updater = getattr(simple_integrated_app, 'async_updater', None)
    if not async_updater:
        print("❌ 異步更新器不存在")
        return
    
    try:
        print("🔄 正在重啟異步更新器...")
        
        # 停止
        async_updater.stop()
        print("✅ 已停止異步更新器")
        
        # 等待一秒
        import time
        time.sleep(1)
        
        # 重新啟動
        async_updater.start()
        print("✅ 已重新啟動異步更新器")
        
        # 檢查狀態
        if getattr(async_updater, 'running', False):
            print("✅ 重啟成功")
        else:
            print("❌ 重啟失敗")
            
    except Exception as e:
        print(f"❌ 重啟失敗: {e}")

def check_database_connection(simple_integrated_app):
    """檢查數據庫連接"""
    db_manager = getattr(simple_integrated_app, 'multi_group_db_manager', None)
    if not db_manager:
        print("❌ 數據庫管理器不存在")
        return
    
    try:
        with db_manager.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT 1")
            result = cursor.fetchone()
            print("✅ 數據庫連接正常")
            
            # 檢查表是否存在
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
            tables = cursor.fetchall()
            print(f"📊 發現 {len(tables)} 個表")
            
    except Exception as e:
        print(f"❌ 數據庫連接失敗: {e}")
        print("💡 這可能是失敗任務的主要原因")

if __name__ == "__main__":
    print("🚀 快速異步檢查工具")
    print("請在 simple_integrated.py 中調用:")
    print("from quick_async_check import quick_async_check")
    print("quick_async_check(self)")
