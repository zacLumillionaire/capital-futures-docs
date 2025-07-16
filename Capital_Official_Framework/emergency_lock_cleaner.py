#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
緊急平倉鎖清理工具 - 立即解決當前的鎖定問題
"""

def emergency_clear_all_locks():
    """緊急清除所有平倉鎖"""
    try:
        from simplified_order_tracker import GlobalExitManager
        
        # 獲取全局平倉管理器
        manager = GlobalExitManager()
        
        # 顯示當前狀態
        current_locks = dict(manager.exit_locks)
        print(f"🔍 發現 {len(current_locks)} 個平倉鎖:")
        
        for position_id, lock_info in current_locks.items():
            trigger_source = lock_info.get('trigger_source', 'unknown')
            print(f"  部位{position_id}: {trigger_source}")
        
        # 清除所有鎖
        cleared_count = manager.clear_all_locks()
        print(f"🧹 已清除 {cleared_count} 個平倉鎖")
        
        # 驗證清理結果
        remaining_locks = dict(manager.exit_locks)
        if len(remaining_locks) == 0:
            print("✅ 所有平倉鎖已成功清除")
        else:
            print(f"⚠️ 仍有 {len(remaining_locks)} 個鎖未清除")
        
        return True
        
    except Exception as e:
        print(f"❌ 緊急清理失敗: {e}")
        return False

def emergency_clear_specific_lock(position_id: str):
    """緊急清除特定部位的鎖"""
    try:
        from simplified_order_tracker import GlobalExitManager
        
        # 獲取全局平倉管理器
        manager = GlobalExitManager()
        
        # 檢查鎖是否存在
        if position_id not in manager.exit_locks:
            print(f"⚠️ 部位{position_id}沒有鎖定")
            return False
        
        # 顯示鎖信息
        lock_info = manager.exit_locks[position_id]
        trigger_source = lock_info.get('trigger_source', 'unknown')
        print(f"🔍 發現部位{position_id}的鎖: {trigger_source}")
        
        # 清除鎖
        manager.clear_exit(position_id)
        
        # 驗證清理結果
        if position_id not in manager.exit_locks:
            print(f"✅ 部位{position_id}的鎖已成功清除")
            return True
        else:
            print(f"❌ 部位{position_id}的鎖清除失敗")
            return False
        
    except Exception as e:
        print(f"❌ 清除部位{position_id}鎖失敗: {e}")
        return False

if __name__ == "__main__":
    import sys
    
    print("🚨 緊急平倉鎖清理工具")
    print("="*40)
    
    if len(sys.argv) < 2:
        print("用法:")
        print("  python emergency_lock_cleaner.py all        # 清除所有鎖")
        print("  python emergency_lock_cleaner.py <position_id> # 清除特定鎖")
        print()
        print("示例:")
        print("  python emergency_lock_cleaner.py all")
        print("  python emergency_lock_cleaner.py 15")
        sys.exit(1)
    
    command = sys.argv[1]
    
    if command == "all":
        emergency_clear_all_locks()
    else:
        # 假設是部位ID
        position_id = command
        emergency_clear_specific_lock(position_id)
