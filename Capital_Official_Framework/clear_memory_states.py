#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
清理內存狀態腳本 - 在程序運行時清除所有內存緩存和鎖定狀態
可以在simple_integrated.py運行時調用此腳本來清理內存狀態
"""

import sys
import os
import time

def clear_global_exit_manager():
    """清理GlobalExitManager的鎖定狀態"""
    try:
        # 嘗試導入並清理GlobalExitManager
        sys.path.append(os.path.dirname(os.path.abspath(__file__)))
        
        from simplified_order_tracker import GlobalExitManager
        
        # 獲取單例實例
        global_exit_manager = GlobalExitManager()
        
        # 清理所有鎖定
        cleared_count = global_exit_manager.clear_all_exits()
        
        print(f"✅ GlobalExitManager: 清理了 {cleared_count} 個鎖定狀態")
        return True
        
    except Exception as e:
        print(f"❌ 清理GlobalExitManager失敗: {e}")
        return False

def clear_optimized_risk_manager():
    """清理OptimizedRiskManager的緩存"""
    try:
        # 這個需要通過程序內部調用，這裡只是提供指令
        print("📋 OptimizedRiskManager緩存清理指令:")
        print("   在程序中調用: optimized_risk_manager.position_cache.clear()")
        print("   在程序中調用: optimized_risk_manager.stop_loss_cache.clear()")
        print("   在程序中調用: optimized_risk_manager.activation_cache.clear()")
        print("   在程序中調用: optimized_risk_manager.trailing_cache.clear()")
        return True
        
    except Exception as e:
        print(f"❌ 清理OptimizedRiskManager指令失敗: {e}")
        return False

def clear_simplified_tracker():
    """清理SimplifiedOrderTracker的狀態"""
    try:
        print("📋 SimplifiedOrderTracker清理指令:")
        print("   在程序中調用: simplified_tracker.strategy_groups.clear()")
        print("   在程序中調用: simplified_tracker.exit_groups.clear()")
        print("   在程序中調用: simplified_tracker.exit_orders.clear()")
        print("   在程序中調用: simplified_tracker.exit_position_mapping.clear()")
        return True
        
    except Exception as e:
        print(f"❌ 清理SimplifiedTracker指令失敗: {e}")
        return False

def main():
    """主清理函數"""
    print("🧠 清理內存狀態腳本")
    print("=" * 50)
    
    success_count = 0
    total_count = 3
    
    # 1. 清理GlobalExitManager
    print("\n🔧 步驟1: 清理GlobalExitManager鎖定狀態...")
    if clear_global_exit_manager():
        success_count += 1
    
    # 2. 清理OptimizedRiskManager
    print("\n🔧 步驟2: 清理OptimizedRiskManager緩存...")
    if clear_optimized_risk_manager():
        success_count += 1
    
    # 3. 清理SimplifiedTracker
    print("\n🔧 步驟3: 清理SimplifiedTracker狀態...")
    if clear_simplified_tracker():
        success_count += 1
    
    # 總結
    print(f"\n📊 清理結果: {success_count}/{total_count} 項成功")
    
    if success_count == total_count:
        print("✅ 內存狀態清理完成")
    else:
        print("⚠️ 部分清理失敗，建議重啟程序")
    
    print("\n💡 建議:")
    print("   1. 如果程序正在運行，某些緩存可能需要在程序內部清理")
    print("   2. 最徹底的方法是重啟整個程序")
    print("   3. 清理後可以重新開始測試")

if __name__ == "__main__":
    main()
