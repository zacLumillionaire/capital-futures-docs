#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
系統維護管理器
負責長時間運行的交易系統的資源清理和維護
"""

import time
import threading
import logging
from typing import List, Callable, Optional
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)

class MaintenanceTask:
    """維護任務"""
    
    def __init__(self, name: str, func: Callable, interval_seconds: int, 
                 description: str = "", enabled: bool = True):
        self.name = name
        self.func = func
        self.interval_seconds = interval_seconds
        self.description = description
        self.enabled = enabled
        self.last_run_time = 0
        self.run_count = 0
        self.error_count = 0
        self.last_error = None

class SystemMaintenanceManager:
    """
    系統維護管理器
    
    負責長時間運行的交易系統的定期維護：
    - 內存緩存清理
    - 日誌文件輪轉
    - 過期訂單清理
    - 資料庫清理
    - 統計信息重置
    """
    
    def __init__(self, console_enabled: bool = True):
        self.console_enabled = console_enabled
        self.maintenance_tasks: List[MaintenanceTask] = []
        self.running = False
        self.maintenance_thread = None
        
        # 維護統計
        self.stats = {
            'start_time': 0,
            'total_maintenance_cycles': 0,
            'total_tasks_executed': 0,
            'total_errors': 0
        }
        
        # 預設維護任務
        self._register_default_tasks()
        
        if self.console_enabled:
            print("[MAINTENANCE] ✅ 系統維護管理器初始化完成")
    
    def _register_default_tasks(self):
        """註冊預設維護任務"""
        # 這些任務會在start()時根據實際組件動態註冊
        pass
    
    def register_task(self, name: str, func: Callable, interval_seconds: int, 
                     description: str = "", enabled: bool = True):
        """
        註冊維護任務
        
        Args:
            name: 任務名稱
            func: 執行函數
            interval_seconds: 執行間隔（秒）
            description: 任務描述
            enabled: 是否啟用
        """
        task = MaintenanceTask(name, func, interval_seconds, description, enabled)
        self.maintenance_tasks.append(task)
        
        if self.console_enabled:
            print(f"[MAINTENANCE] 📝 註冊維護任務: {name} (間隔:{interval_seconds}秒)")
    
    def start(self):
        """啟動維護管理器"""
        if self.running:
            return
        
        self.running = True
        self.stats['start_time'] = time.time()
        
        # 啟動維護線程
        self.maintenance_thread = threading.Thread(target=self._maintenance_loop, daemon=True)
        self.maintenance_thread.start()
        
        if self.console_enabled:
            print(f"[MAINTENANCE] 🚀 系統維護管理器已啟動 (共{len(self.maintenance_tasks)}個任務)")
    
    def stop(self):
        """停止維護管理器"""
        self.running = False
        
        if self.maintenance_thread and self.maintenance_thread.is_alive():
            self.maintenance_thread.join(timeout=5)
        
        if self.console_enabled:
            print("[MAINTENANCE] ⏹️ 系統維護管理器已停止")
    
    def _maintenance_loop(self):
        """維護循環"""
        while self.running:
            try:
                current_time = time.time()
                
                # 檢查並執行到期的維護任務
                for task in self.maintenance_tasks:
                    if not task.enabled:
                        continue
                    
                    if (current_time - task.last_run_time) >= task.interval_seconds:
                        self._execute_task(task, current_time)
                
                # 每分鐘檢查一次
                time.sleep(60)
                
                self.stats['total_maintenance_cycles'] += 1
                
            except Exception as e:
                logger.error(f"維護循環錯誤: {e}")
                self.stats['total_errors'] += 1
                time.sleep(60)  # 錯誤後等待1分鐘再繼續
    
    def _execute_task(self, task: MaintenanceTask, current_time: float):
        """執行維護任務"""
        try:
            if self.console_enabled:
                print(f"[MAINTENANCE] 🔧 執行維護任務: {task.name}")
            
            # 執行任務
            task.func()
            
            # 更新統計
            task.last_run_time = current_time
            task.run_count += 1
            self.stats['total_tasks_executed'] += 1
            
            if self.console_enabled:
                print(f"[MAINTENANCE] ✅ 維護任務完成: {task.name}")
                
        except Exception as e:
            task.error_count += 1
            task.last_error = str(e)
            self.stats['total_errors'] += 1
            
            logger.error(f"維護任務執行失敗 {task.name}: {e}")
            if self.console_enabled:
                print(f"[MAINTENANCE] ❌ 維護任務失敗: {task.name} - {e}")
    
    def get_status(self) -> dict:
        """獲取維護狀態"""
        current_time = time.time()
        uptime = current_time - self.stats['start_time'] if self.stats['start_time'] > 0 else 0
        
        status = {
            'running': self.running,
            'uptime_hours': uptime / 3600,
            'total_tasks': len(self.maintenance_tasks),
            'enabled_tasks': len([t for t in self.maintenance_tasks if t.enabled]),
            'stats': self.stats.copy(),
            'tasks': []
        }
        
        for task in self.maintenance_tasks:
            next_run = task.last_run_time + task.interval_seconds - current_time
            task_info = {
                'name': task.name,
                'description': task.description,
                'enabled': task.enabled,
                'interval_seconds': task.interval_seconds,
                'run_count': task.run_count,
                'error_count': task.error_count,
                'last_error': task.last_error,
                'next_run_in_seconds': max(0, next_run) if task.enabled else None
            }
            status['tasks'].append(task_info)
        
        return status
    
    def print_status(self):
        """打印維護狀態"""
        status = self.get_status()
        
        print("\n" + "="*60)
        print("🔧 系統維護管理器狀態")
        print("="*60)
        print(f"運行狀態: {'🟢 運行中' if status['running'] else '🔴 已停止'}")
        print(f"運行時間: {status['uptime_hours']:.1f} 小時")
        print(f"維護任務: {status['enabled_tasks']}/{status['total_tasks']} 個啟用")
        print(f"執行統計: {status['stats']['total_tasks_executed']} 次執行, {status['stats']['total_errors']} 次錯誤")
        
        print("\n📋 維護任務列表:")
        for task in status['tasks']:
            status_icon = "🟢" if task['enabled'] else "🔴"
            error_info = f" (錯誤:{task['error_count']})" if task['error_count'] > 0 else ""
            next_run = f"下次執行: {task['next_run_in_seconds']:.0f}秒後" if task['next_run_in_seconds'] is not None else "已停用"
            
            print(f"  {status_icon} {task['name']}: 執行{task['run_count']}次{error_info} - {next_run}")
            if task['description']:
                print(f"     描述: {task['description']}")
        
        print("="*60)
    
    def force_run_task(self, task_name: str) -> bool:
        """強制執行指定任務"""
        for task in self.maintenance_tasks:
            if task.name == task_name:
                if self.console_enabled:
                    print(f"[MAINTENANCE] 🔧 強制執行任務: {task_name}")
                
                self._execute_task(task, time.time())
                return True
        
        if self.console_enabled:
            print(f"[MAINTENANCE] ❌ 找不到任務: {task_name}")
        return False
    
    def enable_task(self, task_name: str, enabled: bool = True):
        """啟用/停用指定任務"""
        for task in self.maintenance_tasks:
            if task.name == task_name:
                task.enabled = enabled
                status = "啟用" if enabled else "停用"
                if self.console_enabled:
                    print(f"[MAINTENANCE] 🔄 {status}任務: {task_name}")
                return True
        
        if self.console_enabled:
            print(f"[MAINTENANCE] ❌ 找不到任務: {task_name}")
        return False

# 全局維護管理器實例
_global_maintenance_manager: Optional[SystemMaintenanceManager] = None

def get_maintenance_manager() -> SystemMaintenanceManager:
    """獲取全局維護管理器"""
    global _global_maintenance_manager
    if _global_maintenance_manager is None:
        _global_maintenance_manager = SystemMaintenanceManager()
    return _global_maintenance_manager

def init_maintenance_manager(console_enabled: bool = True) -> SystemMaintenanceManager:
    """初始化全局維護管理器"""
    global _global_maintenance_manager
    _global_maintenance_manager = SystemMaintenanceManager(console_enabled)
    return _global_maintenance_manager
