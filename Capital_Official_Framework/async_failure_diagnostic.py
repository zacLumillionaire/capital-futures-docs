#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
🔍 異步更新器失敗診斷工具
專門診斷緩存命中增加但失敗任務也增加的問題
"""

import time
import threading
import sqlite3
import logging
from datetime import datetime
from typing import Dict, List, Optional, Any

class AsyncFailureDiagnostic:
    """異步更新器失敗診斷工具"""
    
    def __init__(self, async_updater=None, db_manager=None, console_enabled=True):
        self.async_updater = async_updater
        self.db_manager = db_manager
        self.console_enabled = console_enabled
        self.diagnostic_results = {}
        
    def diagnose_cache_hit_with_failures(self):
        """診斷緩存命中增加但失敗任務也增加的問題"""
        print("🔍 開始診斷異步更新器失敗問題...")
        print("=" * 60)
        
        # 1. 檢查異步更新器基本狀態
        self._check_async_updater_basic_status()
        
        # 2. 分析統計數據
        self._analyze_statistics()
        
        # 3. 檢查工作線程狀態
        self._check_worker_thread_status()
        
        # 4. 檢查數據庫連接
        self._check_database_connection()
        
        # 5. 分析隊列狀態
        self._analyze_queue_status()
        
        # 6. 檢查具體錯誤
        self._check_specific_errors()
        
        # 7. 提供修復建議
        self._provide_fix_recommendations()
        
    def _check_async_updater_basic_status(self):
        """檢查異步更新器基本狀態"""
        print("\n📊 1. 異步更新器基本狀態檢查")
        print("-" * 40)
        
        if not self.async_updater:
            print("❌ 異步更新器不存在")
            return
            
        print(f"✅ 異步更新器存在: {type(self.async_updater).__name__}")
        print(f"🔄 運行狀態: {getattr(self.async_updater, 'running', 'Unknown')}")
        print(f"🧵 工作線程: {getattr(self.async_updater, 'worker_thread', 'Unknown')}")
        
        # 檢查線程是否活躍
        worker_thread = getattr(self.async_updater, 'worker_thread', None)
        if worker_thread:
            print(f"🔍 線程活躍狀態: {worker_thread.is_alive()}")
            print(f"🔍 線程名稱: {worker_thread.name}")
        
    def _analyze_statistics(self):
        """分析統計數據"""
        print("\n📈 2. 統計數據分析")
        print("-" * 40)
        
        if not self.async_updater:
            print("❌ 無法獲取統計數據")
            return
            
        try:
            stats = self.async_updater.get_stats()
            
            total_tasks = stats.get('total_tasks', 0)
            completed_tasks = stats.get('completed_tasks', 0)
            failed_tasks = stats.get('failed_tasks', 0)
            cache_hits = stats.get('cache_hits', 0)
            
            print(f"📊 總任務數: {total_tasks}")
            print(f"✅ 完成任務: {completed_tasks}")
            print(f"❌ 失敗任務: {failed_tasks}")
            print(f"💾 緩存命中: {cache_hits}")
            
            if total_tasks > 0:
                success_rate = (completed_tasks / total_tasks) * 100
                failure_rate = (failed_tasks / total_tasks) * 100
                cache_hit_rate = (cache_hits / total_tasks) * 100
                
                print(f"📊 成功率: {success_rate:.1f}%")
                print(f"📊 失敗率: {failure_rate:.1f}%")
                print(f"📊 緩存命中率: {cache_hit_rate:.1f}%")
                
                # 分析異常模式
                if cache_hits > 0 and failed_tasks > 0:
                    print("\n⚠️ 發現異常模式:")
                    print(f"   緩存命中 {cache_hits} 次，但失敗任務 {failed_tasks} 次")
                    print("   這表明緩存讀取成功但數據庫寫入失敗")
                    
        except Exception as e:
            print(f"❌ 統計數據分析失敗: {e}")
    
    def _check_worker_thread_status(self):
        """檢查工作線程狀態"""
        print("\n🧵 3. 工作線程狀態檢查")
        print("-" * 40)
        
        if not self.async_updater:
            return
            
        worker_thread = getattr(self.async_updater, 'worker_thread', None)
        if not worker_thread:
            print("❌ 工作線程不存在")
            return
            
        print(f"🔍 線程活躍: {worker_thread.is_alive()}")
        print(f"🔍 線程守護: {worker_thread.daemon}")
        
        # 檢查線程是否卡住
        if hasattr(self.async_updater, 'last_activity_time'):
            last_activity = getattr(self.async_updater, 'last_activity_time', 0)
            if last_activity > 0:
                idle_time = time.time() - last_activity
                print(f"⏰ 上次活動: {idle_time:.1f}秒前")
                if idle_time > 30:
                    print("⚠️ 工作線程可能卡住")
    
    def _check_database_connection(self):
        """檢查數據庫連接"""
        print("\n💾 4. 數據庫連接檢查")
        print("-" * 40)
        
        if not self.db_manager:
            print("❌ 數據庫管理器不存在")
            return
            
        try:
            # 測試數據庫連接
            with self.db_manager.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT 1")
                result = cursor.fetchone()
                print("✅ 數據庫連接正常")
                
            # 檢查數據庫鎖定
            self._check_database_locks()
            
        except Exception as e:
            print(f"❌ 數據庫連接失敗: {e}")
            print("💡 這可能是失敗任務增加的主要原因")
    
    def _check_database_locks(self):
        """檢查數據庫鎖定情況"""
        try:
            with self.db_manager.get_connection() as conn:
                cursor = conn.cursor()
                
                # 檢查 SQLite 鎖定狀態
                cursor.execute("PRAGMA locking_mode")
                locking_mode = cursor.fetchone()
                print(f"🔒 鎖定模式: {locking_mode[0] if locking_mode else 'Unknown'}")
                
                cursor.execute("PRAGMA journal_mode")
                journal_mode = cursor.fetchone()
                print(f"📝 日誌模式: {journal_mode[0] if journal_mode else 'Unknown'}")
                
        except Exception as e:
            print(f"⚠️ 無法檢查數據庫鎖定: {e}")
    
    def _analyze_queue_status(self):
        """分析隊列狀態"""
        print("\n📋 5. 隊列狀態分析")
        print("-" * 40)
        
        if not self.async_updater:
            return
            
        try:
            queue = getattr(self.async_updater, 'update_queue', None)
            if queue:
                queue_size = queue.qsize()
                print(f"📊 當前隊列大小: {queue_size}")
                
                if hasattr(queue, 'maxsize'):
                    max_size = queue.maxsize
                    print(f"📊 最大隊列大小: {max_size}")
                    
                    if queue_size > max_size * 0.8:
                        print("⚠️ 隊列接近滿載")
                        
                # 檢查隊列峰值
                stats = self.async_updater.get_stats()
                peak_size = stats.get('queue_size_peak', 0)
                print(f"📊 隊列峰值: {peak_size}")
                
        except Exception as e:
            print(f"❌ 隊列狀態分析失敗: {e}")
    
    def _check_specific_errors(self):
        """檢查具體錯誤"""
        print("\n🔍 6. 具體錯誤檢查")
        print("-" * 40)
        
        # 檢查日誌記錄器
        logger = logging.getLogger('async_db_updater')
        if logger.handlers:
            print("📝 發現日誌處理器，檢查最近錯誤...")
            # 這裡可以添加日誌分析邏輯
        else:
            print("⚠️ 未找到日誌處理器")
            
        # 建議啟用詳細日誌
        print("\n💡 建議啟用詳細日誌來查看具體錯誤:")
        print("   async_updater.set_log_options(enable_task_logs=True)")
        print("   async_updater.console_enabled = True")
    
    def _provide_fix_recommendations(self):
        """提供修復建議"""
        print("\n🔧 7. 修復建議")
        print("-" * 40)
        
        print("基於診斷結果，建議按以下順序排查:")
        print()
        print("1️⃣ 立即檢查:")
        print("   • 啟用詳細日誌: async_updater.set_log_options(enable_task_logs=True)")
        print("   • 查看具體錯誤信息")
        print("   • 檢查數據庫文件權限")
        print()
        print("2️⃣ 數據庫診斷:")
        print("   • 檢查數據庫文件是否損壞")
        print("   • 檢查磁盤空間")
        print("   • 檢查併發連接數")
        print()
        print("3️⃣ 重啟異步更新器:")
        print("   • async_updater.stop()")
        print("   • time.sleep(1)")
        print("   • async_updater.start()")
        print()
        print("4️⃣ 如果問題持續:")
        print("   • 切換到同步模式")
        print("   • 檢查系統資源使用情況")
        print("   • 考慮重建數據庫索引")

def run_diagnostic_on_simple_integrated(simple_integrated_app):
    """在 simple_integrated.py 實例上運行診斷"""
    print("🔍 在 simple_integrated 實例上運行異步失敗診斷...")
    
    async_updater = getattr(simple_integrated_app, 'async_updater', None)
    db_manager = getattr(simple_integrated_app, 'multi_group_db_manager', None)
    
    diagnostic = AsyncFailureDiagnostic(async_updater, db_manager)
    diagnostic.diagnose_cache_hit_with_failures()

if __name__ == "__main__":
    print("🔍 異步失敗診斷工具")
    print("請在 simple_integrated.py 中調用:")
    print("from async_failure_diagnostic import run_diagnostic_on_simple_integrated")
    print("run_diagnostic_on_simple_integrated(self)")
