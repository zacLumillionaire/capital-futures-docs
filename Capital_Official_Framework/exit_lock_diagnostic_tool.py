#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
平倉鎖診斷工具 - 實時監控和強制清理平倉鎖狀態
解決平倉鎖死結問題的專用工具
"""

import time
import threading
from datetime import datetime
from typing import Dict, List, Optional

class ExitLockDiagnosticTool:
    """平倉鎖診斷工具"""
    
    def __init__(self, console_enabled: bool = True):
        self.console_enabled = console_enabled
        self.global_exit_manager = None
        self._init_global_exit_manager()
    
    def _init_global_exit_manager(self):
        """初始化全局平倉管理器"""
        try:
            from simplified_order_tracker import GlobalExitManager
            self.global_exit_manager = GlobalExitManager()
            if self.console_enabled:
                print("[LOCK_DIAGNOSTIC] ✅ 全局平倉管理器連接成功")
        except Exception as e:
            if self.console_enabled:
                print(f"[LOCK_DIAGNOSTIC] ❌ 全局平倉管理器連接失敗: {e}")
    
    def get_current_locks(self) -> Dict:
        """獲取當前所有平倉鎖"""
        if not self.global_exit_manager:
            return {}
        
        return dict(self.global_exit_manager.exit_locks)
    
    def display_lock_status(self):
        """顯示當前鎖狀態"""
        locks = self.get_current_locks()
        current_time = time.time()
        
        print("\n" + "="*60)
        print(f"🔍 平倉鎖狀態報告 - {datetime.now().strftime('%H:%M:%S')}")
        print("="*60)
        
        if not locks:
            print("✅ 當前沒有平倉鎖")
        else:
            print(f"🔒 當前平倉鎖數量: {len(locks)}")
            print()
            
            for position_id, lock_info in locks.items():
                lock_time = lock_info.get('timestamp', 0)
                age = current_time - lock_time
                trigger_source = lock_info.get('trigger_source', 'unknown')
                exit_type = lock_info.get('exit_type', 'unknown')
                
                status = "🟢 正常" if age < 10 else "🟡 可疑" if age < 30 else "🔴 過期"
                
                print(f"  部位{position_id}:")
                print(f"    狀態: {status} (存在 {age:.1f} 秒)")
                print(f"    來源: {trigger_source}")
                print(f"    類型: {exit_type}")
                print(f"    時間: {datetime.fromtimestamp(lock_time).strftime('%H:%M:%S')}")
                print()
        
        print("="*60)
    
    def find_problematic_locks(self, max_age_seconds: float = 30.0) -> List[str]:
        """找出有問題的鎖（存在時間過長）"""
        locks = self.get_current_locks()
        current_time = time.time()
        problematic = []
        
        for position_id, lock_info in locks.items():
            lock_time = lock_info.get('timestamp', 0)
            age = current_time - lock_time
            
            if age > max_age_seconds:
                problematic.append(position_id)
        
        return problematic
    
    def clear_specific_lock(self, position_id: str) -> bool:
        """清除特定部位的鎖"""
        if not self.global_exit_manager:
            if self.console_enabled:
                print("[LOCK_DIAGNOSTIC] ❌ 全局平倉管理器未連接")
            return False
        
        try:
            # 檢查鎖是否存在
            if position_id not in self.global_exit_manager.exit_locks:
                if self.console_enabled:
                    print(f"[LOCK_DIAGNOSTIC] ⚠️ 部位{position_id}沒有鎖定")
                return False
            
            # 獲取鎖信息
            lock_info = self.global_exit_manager.exit_locks[position_id]
            trigger_source = lock_info.get('trigger_source', 'unknown')
            
            # 清除鎖
            self.global_exit_manager.clear_exit(position_id)
            
            if self.console_enabled:
                print(f"[LOCK_DIAGNOSTIC] 🔓 已強制清除部位{position_id}的鎖")
                print(f"[LOCK_DIAGNOSTIC]   原鎖來源: {trigger_source}")
            
            return True
            
        except Exception as e:
            if self.console_enabled:
                print(f"[LOCK_DIAGNOSTIC] ❌ 清除部位{position_id}鎖失敗: {e}")
            return False
    
    def clear_all_locks(self) -> int:
        """清除所有鎖"""
        if not self.global_exit_manager:
            if self.console_enabled:
                print("[LOCK_DIAGNOSTIC] ❌ 全局平倉管理器未連接")
            return 0
        
        try:
            cleared_count = self.global_exit_manager.clear_all_locks()
            
            if self.console_enabled:
                print(f"[LOCK_DIAGNOSTIC] 🧹 已清除所有鎖，共 {cleared_count} 個")
            
            return cleared_count
            
        except Exception as e:
            if self.console_enabled:
                print(f"[LOCK_DIAGNOSTIC] ❌ 清除所有鎖失敗: {e}")
            return 0
    
    def clear_expired_locks(self, max_age_seconds: float = 30.0) -> int:
        """清除過期的鎖"""
        problematic = self.find_problematic_locks(max_age_seconds)
        cleared_count = 0
        
        for position_id in problematic:
            if self.clear_specific_lock(position_id):
                cleared_count += 1
        
        if self.console_enabled and cleared_count > 0:
            print(f"[LOCK_DIAGNOSTIC] 🧹 清除了 {cleared_count} 個過期鎖")
        
        return cleared_count
    
    def monitor_locks(self, interval_seconds: int = 5, max_iterations: int = 10):
        """持續監控鎖狀態"""
        if self.console_enabled:
            print(f"[LOCK_DIAGNOSTIC] 🔍 開始監控平倉鎖狀態 (間隔{interval_seconds}秒, 最多{max_iterations}次)")
        
        for i in range(max_iterations):
            self.display_lock_status()
            
            # 自動清理過期鎖
            expired_count = self.clear_expired_locks(30.0)
            if expired_count > 0:
                print(f"[LOCK_DIAGNOSTIC] 🧹 自動清理了 {expired_count} 個過期鎖")
            
            if i < max_iterations - 1:
                time.sleep(interval_seconds)
        
        if self.console_enabled:
            print("[LOCK_DIAGNOSTIC] 🏁 監控結束")

def create_diagnostic_tool(console_enabled: bool = True) -> ExitLockDiagnosticTool:
    """創建診斷工具實例"""
    return ExitLockDiagnosticTool(console_enabled)

# 命令行工具
if __name__ == "__main__":
    import sys
    
    tool = create_diagnostic_tool()
    
    if len(sys.argv) < 2:
        print("用法:")
        print("  python exit_lock_diagnostic_tool.py status    # 顯示當前狀態")
        print("  python exit_lock_diagnostic_tool.py clear_all # 清除所有鎖")
        print("  python exit_lock_diagnostic_tool.py clear_expired # 清除過期鎖")
        print("  python exit_lock_diagnostic_tool.py clear <position_id> # 清除特定鎖")
        print("  python exit_lock_diagnostic_tool.py monitor   # 持續監控")
        sys.exit(1)
    
    command = sys.argv[1]
    
    if command == "status":
        tool.display_lock_status()
    elif command == "clear_all":
        tool.clear_all_locks()
    elif command == "clear_expired":
        tool.clear_expired_locks()
    elif command == "clear" and len(sys.argv) > 2:
        position_id = sys.argv[2]
        tool.clear_specific_lock(position_id)
    elif command == "monitor":
        tool.monitor_locks()
    else:
        print(f"未知命令: {command}")
        sys.exit(1)
