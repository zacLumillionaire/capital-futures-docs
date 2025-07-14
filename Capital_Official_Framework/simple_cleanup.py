#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
簡化版清理腳本 - 修復SQLite Row對象問題
"""

import os
import sqlite3
from datetime import date

def simple_cleanup():
    """簡化版清理功能"""
    print("🧹 簡化版測試環境清理")
    print("=" * 50)
    
    db_path = "multi_group_strategy.db"
    
    if not os.path.exists(db_path):
        print("❌ 資料庫檔案不存在")
        return
    
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # 1. 檢查當前狀態
        print("🔍 檢查當前狀態...")
        
        cursor.execute("SELECT COUNT(*) FROM position_records WHERE status = 'ACTIVE'")
        active_positions = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM risk_management_states")
        risk_states = cursor.fetchone()[0]
        
        today = date.today().strftime('%Y-%m-%d')
        cursor.execute("SELECT COUNT(*) FROM strategy_groups WHERE date = ?", (today,))
        today_groups = cursor.fetchone()[0]
        
        print(f"   - 活躍部位: {active_positions}")
        print(f"   - 風險管理狀態: {risk_states}")
        print(f"   - 今日策略組: {today_groups}")
        
        total_items = active_positions + risk_states + today_groups
        
        if total_items == 0:
            print("✅ 環境已經是乾淨狀態，無需清理")
            conn.close()
            return
        
        # 2. 顯示詳細信息
        if active_positions > 0:
            print(f"\n📋 活躍部位詳情:")
            cursor.execute('''
                SELECT pr.id, pr.direction, pr.entry_price, pr.created_at
                FROM position_records pr
                WHERE pr.status = 'ACTIVE'
                ORDER BY pr.created_at
            ''')
            
            positions = cursor.fetchall()
            for pos in positions:
                print(f"   - 部位{pos[0]}: {pos[1]}, @{pos[2]}, 時間:{pos[3]}")
        
        # 3. 執行清理
        print(f"\n⚠️ 檢測到 {total_items} 項需要清理的數據")
        print("🔧 將執行以下清理操作:")
        print("   - 清理所有活躍部位")
        print("   - 清理風險管理狀態")
        print("   - 清理今日策略組")
        
        choice = input("\n確定要執行清理嗎？(y/N): ").strip().lower()
        if choice != 'y':
            print("❌ 取消清理")
            conn.close()
            return
        
        print("\n🚀 開始執行清理...")
        
        # 4. 執行清理操作
        # 清理活躍部位
        if active_positions > 0:
            cursor.execute("DELETE FROM position_records WHERE status = 'ACTIVE'")
            deleted_positions = cursor.rowcount
            print(f"   ✅ 清理活躍部位: {deleted_positions} 個")
        
        # 清理風險管理狀態
        if risk_states > 0:
            cursor.execute("DELETE FROM risk_management_states")
            deleted_risk_states = cursor.rowcount
            print(f"   ✅ 清理風險管理狀態: {deleted_risk_states} 個")
        
        # 清理今日策略組
        if today_groups > 0:
            cursor.execute("DELETE FROM strategy_groups WHERE date = ?", (today,))
            deleted_groups = cursor.rowcount
            print(f"   ✅ 清理今日策略組: {deleted_groups} 個")
        
        # 清理舊報價數據（檢查表是否存在）
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
        
        # 5. 提交變更
        conn.commit()
        
        # 6. 驗證清理結果
        print(f"\n📊 清理後狀態:")
        cursor.execute("SELECT COUNT(*) FROM position_records WHERE status = 'ACTIVE'")
        final_active = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM risk_management_states")
        final_risk = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM strategy_groups WHERE date = ?", (today,))
        final_groups = cursor.fetchone()[0]
        
        print(f"   - 活躍部位: {final_active}")
        print(f"   - 風險管理狀態: {final_risk}")
        print(f"   - 今日策略組: {final_groups}")
        
        conn.close()
        
        print("\n🎉 清理完成！")
        print("💡 建議重啟 simple_integrated.py 程序以確保內存狀態也被清除")
        print("💡 現在可以重新測試策略，環境已完全重置")
        
        # 7. 清理內存狀態提示
        print("\n🧠 內存狀態清理:")
        print("   📋 建議重啟程序以清理內存狀態")
        print("   📋 或者在程序中調用:")
        print("      - global_exit_manager.clear_all_exits()")
        print("      - optimized_risk_manager.clear_all_caches()")
        
    except Exception as e:
        print(f"❌ 清理失敗: {e}")
        import traceback
        traceback.print_exc()

def quick_status_check():
    """快速狀態檢查"""
    print("🔍 快速狀態檢查")
    print("=" * 30)
    
    db_path = "multi_group_strategy.db"
    
    if not os.path.exists(db_path):
        print("❌ 資料庫檔案不存在")
        return
    
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        cursor.execute("SELECT COUNT(*) FROM position_records WHERE status = 'ACTIVE'")
        active_positions = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM risk_management_states")
        risk_states = cursor.fetchone()[0]
        
        today = date.today().strftime('%Y-%m-%d')
        cursor.execute("SELECT COUNT(*) FROM strategy_groups WHERE date = ?", (today,))
        today_groups = cursor.fetchone()[0]
        
        print(f"📊 當前狀態:")
        print(f"   - 活躍部位: {active_positions}")
        print(f"   - 風險管理狀態: {risk_states}")
        print(f"   - 今日策略組: {today_groups}")
        
        total = active_positions + risk_states + today_groups
        if total == 0:
            print("✅ 環境乾淨，可以開始測試")
        else:
            print(f"⚠️ 發現 {total} 項數據，建議清理")
        
        conn.close()
        
    except Exception as e:
        print(f"❌ 狀態檢查失敗: {e}")

def force_cleanup():
    """強制清理（不詢問）"""
    print("🚀 強制清理模式")
    print("=" * 30)
    
    db_path = "multi_group_strategy.db"
    
    if not os.path.exists(db_path):
        print("❌ 資料庫檔案不存在")
        return
    
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # 直接清理所有測試數據
        cursor.execute("DELETE FROM position_records WHERE status = 'ACTIVE'")
        cursor.execute("DELETE FROM risk_management_states")
        
        today = date.today().strftime('%Y-%m-%d')
        cursor.execute("DELETE FROM strategy_groups WHERE date = ?", (today,))

        # 檢查real_time_quotes表是否存在
        try:
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='real_time_quotes'")
            if cursor.fetchone():
                cursor.execute("DELETE FROM real_time_quotes WHERE timestamp < datetime('now', '-1 hour')")
        except:
            pass  # 忽略報價表相關錯誤
        
        conn.commit()
        conn.close()
        
        print("✅ 強制清理完成")
        
    except Exception as e:
        print(f"❌ 強制清理失敗: {e}")

if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1:
        if sys.argv[1] == "status":
            quick_status_check()
        elif sys.argv[1] == "force":
            force_cleanup()
        else:
            print("用法:")
            print("  python simple_cleanup.py        # 互動式清理")
            print("  python simple_cleanup.py status # 快速狀態檢查")
            print("  python simple_cleanup.py force  # 強制清理")
    else:
        simple_cleanup()
