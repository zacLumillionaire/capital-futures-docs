#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
一鍵清理腳本 - 徹底重置測試環境
結合資料庫清理和內存狀態清理，確保測試環境完全乾淨
"""

import os
import sys
import subprocess
import sqlite3
from datetime import date

def check_database_status():
    """檢查資料庫狀態"""
    print("🔍 檢查資料庫狀態...")
    
    db_path = "multi_group_strategy.db"
    if not os.path.exists(db_path):
        print("✅ 資料庫檔案不存在，環境已是乾淨狀態")
        return True, 0, 0, 0
    
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # 檢查活躍部位
        cursor.execute("SELECT COUNT(*) FROM position_records WHERE status = 'ACTIVE'")
        active_positions = cursor.fetchone()[0]
        
        # 檢查風險管理狀態
        cursor.execute("SELECT COUNT(*) FROM risk_management_states")
        risk_states = cursor.fetchone()[0]
        
        # 檢查今日策略組
        today = date.today().strftime('%Y-%m-%d')
        cursor.execute("SELECT COUNT(*) FROM strategy_groups WHERE date = ?", (today,))
        today_groups = cursor.fetchone()[0]
        
        conn.close()
        
        print(f"   - 活躍部位: {active_positions}")
        print(f"   - 風險管理狀態: {risk_states}")
        print(f"   - 今日策略組: {today_groups}")
        
        return True, active_positions, risk_states, today_groups
        
    except Exception as e:
        print(f"❌ 檢查資料庫失敗: {e}")
        return False, 0, 0, 0

def perform_database_cleanup():
    """執行資料庫清理"""
    print("\n🗃️ 執行資料庫清理...")
    
    db_path = "multi_group_strategy.db"
    if not os.path.exists(db_path):
        print("✅ 資料庫檔案不存在，跳過清理")
        return True
    
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # 1. 清理活躍部位
        cursor.execute("DELETE FROM position_records WHERE status = 'ACTIVE'")
        deleted_positions = cursor.rowcount
        print(f"   ✅ 清理活躍部位: {deleted_positions} 個")
        
        # 2. 清理風險管理狀態
        cursor.execute("DELETE FROM risk_management_states")
        deleted_risk_states = cursor.rowcount
        print(f"   ✅ 清理風險管理狀態: {deleted_risk_states} 個")
        
        # 3. 清理今日策略組
        today = date.today().strftime('%Y-%m-%d')
        cursor.execute("DELETE FROM strategy_groups WHERE date = ?", (today,))
        deleted_groups = cursor.rowcount
        print(f"   ✅ 清理今日策略組: {deleted_groups} 個")
        
        # 4. 清理舊報價數據（檢查表是否存在）
        try:
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='real_time_quotes'")
            if cursor.fetchone():
                cursor.execute("DELETE FROM real_time_quotes WHERE timestamp < datetime('now', '-1 hour')")
                deleted_quotes = cursor.rowcount
                print(f"   ✅ 清理舊報價數據: {deleted_quotes} 個")
            else:
                print(f"   ⚠️ real_time_quotes表不存在，跳過清理")
        except Exception as e:
            print(f"   ⚠️ 清理報價數據失敗: {e}")
        
        # 5. 清理失敗和已出場的測試數據（可選）
        cursor.execute("DELETE FROM position_records WHERE exit_reason LIKE '%測試%' OR exit_reason LIKE '%清理%'")
        deleted_test_data = cursor.rowcount
        print(f"   ✅ 清理測試數據: {deleted_test_data} 個")
        
        conn.commit()
        conn.close()
        
        print("✅ 資料庫清理完成")
        return True
        
    except Exception as e:
        print(f"❌ 資料庫清理失敗: {e}")
        return False

def perform_memory_cleanup():
    """執行內存清理"""
    print("\n🧠 執行內存清理...")
    
    try:
        # 嘗試清理GlobalExitManager
        try:
            from simplified_order_tracker import GlobalExitManager
            global_exit_manager = GlobalExitManager()
            cleared_count = global_exit_manager.clear_all_exits()
            print(f"   ✅ 清理GlobalExitManager鎖定: {cleared_count} 個")
        except Exception as e:
            print(f"   ⚠️ 無法清理GlobalExitManager: {e}")
        
        print("   📋 其他內存狀態需要程序重啟才能完全清除")
        print("✅ 內存清理指令已執行")
        return True
        
    except Exception as e:
        print(f"❌ 內存清理失敗: {e}")
        return False

def main():
    """主函數"""
    print("🚀 一鍵清理腳本 - 徹底重置測試環境")
    print("=" * 60)
    
    # 1. 檢查當前狀態
    success, active_pos, risk_states, groups = check_database_status()
    if not success:
        print("❌ 無法檢查資料庫狀態，退出")
        return
    
    # 2. 判斷是否需要清理
    total_items = active_pos + risk_states + groups
    if total_items == 0:
        print("\n✅ 環境已經是乾淨狀態，無需清理")
        return
    
    # 3. 確認清理
    print(f"\n⚠️ 檢測到 {total_items} 項需要清理的數據")
    print("🔧 將執行以下清理操作:")
    print("   - 清理所有活躍部位")
    print("   - 清理風險管理狀態")
    print("   - 清理今日策略組")
    print("   - 清理內存鎖定狀態")
    print("   - 清理舊報價數據")
    
    choice = input("\n確定要執行一鍵清理嗎？(y/N): ").strip().lower()
    if choice != 'y':
        print("❌ 取消清理")
        return
    
    # 4. 執行清理
    print("\n🚀 開始執行一鍵清理...")
    
    # 資料庫清理
    db_success = perform_database_cleanup()
    
    # 內存清理
    mem_success = perform_memory_cleanup()
    
    # 5. 驗證結果
    print("\n🔍 驗證清理結果...")
    success, active_pos, risk_states, groups = check_database_status()
    
    if success:
        total_remaining = active_pos + risk_states + groups
        print(f"   - 剩餘數據項: {total_remaining}")
        
        if total_remaining == 0:
            print("✅ 清理完全成功！")
        else:
            print("⚠️ 仍有部分數據未清理")
    
    # 6. 總結和建議
    print("\n🎉 一鍵清理完成！")
    print("\n📋 清理總結:")
    print(f"   - 資料庫清理: {'✅ 成功' if db_success else '❌ 失敗'}")
    print(f"   - 內存清理: {'✅ 成功' if mem_success else '❌ 失敗'}")
    
    print("\n💡 建議:")
    print("   1. 重啟 simple_integrated.py 程序以確保內存完全清除")
    print("   2. 重新開始測試，環境已重置為全新狀態")
    print("   3. 如果仍有問題，可以手動刪除 multi_group_strategy.db 檔案")

if __name__ == "__main__":
    main()
