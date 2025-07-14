#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
直接清理腳本 - 最簡化版本，專門解決表不存在的問題
"""

import os
import sqlite3
from datetime import date

def direct_cleanup():
    """直接清理，不詢問"""
    print("🚀 直接清理模式")
    print("=" * 30)
    
    db_path = "multi_group_strategy.db"
    
    if not os.path.exists(db_path):
        print("❌ 資料庫檔案不存在")
        return False
    
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        print("🔍 檢查清理前狀態...")
        
        # 檢查活躍部位
        try:
            cursor.execute("SELECT COUNT(*) FROM position_records WHERE status = 'ACTIVE'")
            active_before = cursor.fetchone()[0]
            print(f"   - 活躍部位: {active_before}")
        except:
            active_before = 0
            print("   - position_records表不存在")
        
        # 檢查風險管理狀態
        try:
            cursor.execute("SELECT COUNT(*) FROM risk_management_states")
            risk_before = cursor.fetchone()[0]
            print(f"   - 風險管理狀態: {risk_before}")
        except:
            risk_before = 0
            print("   - risk_management_states表不存在")
        
        # 檢查策略組
        try:
            today = date.today().strftime('%Y-%m-%d')
            cursor.execute("SELECT COUNT(*) FROM strategy_groups WHERE date = ?", (today,))
            groups_before = cursor.fetchone()[0]
            print(f"   - 今日策略組: {groups_before}")
        except:
            groups_before = 0
            print("   - strategy_groups表不存在")
        
        print("\n🧹 開始清理...")
        
        # 清理活躍部位
        try:
            cursor.execute("DELETE FROM position_records WHERE status = 'ACTIVE'")
            deleted_pos = cursor.rowcount
            print(f"   ✅ 清理活躍部位: {deleted_pos} 個")
        except Exception as e:
            print(f"   ⚠️ 清理活躍部位失敗: {e}")
        
        # 清理風險管理狀態
        try:
            cursor.execute("DELETE FROM risk_management_states")
            deleted_risk = cursor.rowcount
            print(f"   ✅ 清理風險管理狀態: {deleted_risk} 個")
        except Exception as e:
            print(f"   ⚠️ 清理風險管理狀態失敗: {e}")
        
        # 清理今日策略組
        try:
            today = date.today().strftime('%Y-%m-%d')
            cursor.execute("DELETE FROM strategy_groups WHERE date = ?", (today,))
            deleted_groups = cursor.rowcount
            print(f"   ✅ 清理今日策略組: {deleted_groups} 個")
        except Exception as e:
            print(f"   ⚠️ 清理今日策略組失敗: {e}")
        
        # 嘗試清理報價數據（如果表存在）
        try:
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='real_time_quotes'")
            if cursor.fetchone():
                cursor.execute("DELETE FROM real_time_quotes WHERE timestamp < datetime('now', '-1 hour')")
                deleted_quotes = cursor.rowcount
                print(f"   ✅ 清理舊報價數據: {deleted_quotes} 個")
            else:
                print(f"   ⚠️ real_time_quotes表不存在，跳過")
        except Exception as e:
            print(f"   ⚠️ 清理報價數據失敗: {e}")
        
        # 提交變更
        conn.commit()
        
        print("\n📊 檢查清理後狀態...")
        
        # 驗證清理結果
        try:
            cursor.execute("SELECT COUNT(*) FROM position_records WHERE status = 'ACTIVE'")
            active_after = cursor.fetchone()[0]
            print(f"   - 活躍部位: {active_after}")
        except:
            print("   - position_records表不存在")
        
        try:
            cursor.execute("SELECT COUNT(*) FROM risk_management_states")
            risk_after = cursor.fetchone()[0]
            print(f"   - 風險管理狀態: {risk_after}")
        except:
            print("   - risk_management_states表不存在")
        
        try:
            cursor.execute("SELECT COUNT(*) FROM strategy_groups WHERE date = ?", (today,))
            groups_after = cursor.fetchone()[0]
            print(f"   - 今日策略組: {groups_after}")
        except:
            print("   - strategy_groups表不存在")
        
        conn.close()
        
        print("\n✅ 直接清理完成！")
        print("💡 建議重啟 simple_integrated.py 程序")
        print("💡 現在可以重新測試策略")
        
        return True
        
    except Exception as e:
        print(f"❌ 直接清理失敗: {e}")
        import traceback
        traceback.print_exc()
        return False

def check_tables():
    """檢查數據庫表結構"""
    print("🔍 檢查數據庫表結構")
    print("=" * 30)
    
    db_path = "multi_group_strategy.db"
    
    if not os.path.exists(db_path):
        print("❌ 資料庫檔案不存在")
        return
    
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # 獲取所有表
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
        tables = cursor.fetchall()
        
        print(f"📋 發現 {len(tables)} 個表:")
        for table in tables:
            table_name = table[0]
            try:
                cursor.execute(f"SELECT COUNT(*) FROM {table_name}")
                count = cursor.fetchone()[0]
                print(f"   - {table_name}: {count} 條記錄")
            except Exception as e:
                print(f"   - {table_name}: 無法讀取 ({e})")
        
        conn.close()
        
    except Exception as e:
        print(f"❌ 檢查表結構失敗: {e}")

if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1 and sys.argv[1] == "tables":
        check_tables()
    else:
        direct_cleanup()
