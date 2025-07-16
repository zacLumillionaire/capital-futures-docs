#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
檢查多組策略資料庫狀態
用於診斷 UNIQUE constraint failed 錯誤
"""

import sqlite3
from datetime import date
import os

def check_database_status():
    """檢查資料庫狀態"""
    db_path = "multi_group_strategy.db"
    
    if not os.path.exists(db_path):
        print(f"❌ 資料庫文件不存在: {db_path}")
        return
    
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        print("🔍 檢查多組策略資料庫狀態")
        print("=" * 50)
        
        # 檢查今天的策略組
        today = date.today().isoformat()
        print(f"📅 檢查日期: {today}")
        
        # 查詢今天的策略組
        cursor.execute("""
            SELECT id AS group_pk, date, group_id AS logical_group_id, direction, entry_signal_time,
                   range_high, range_low, total_lots, status, created_at
            FROM strategy_groups
            WHERE date = ?
            ORDER BY group_id
        """, (today,))
        
        groups = cursor.fetchall()
        
        if groups:
            print(f"\n📊 找到 {len(groups)} 個今天的策略組:")
            print("-" * 80)
            print("ID | 組別 | 方向 | 信號時間 | 區間高 | 區間低 | 口數 | 狀態 | 創建時間")
            print("-" * 80)
            
            for group_record in groups:
                print(f"{group_record[0]:2d} | {group_record[2]:4d} | {group_record[3]:4s} | {group_record[4]:8s} | "
                      f"{group_record[5]:6.0f} | {group_record[6]:6.0f} | {group_record[7]:4d} | {group_record[8]:8s} | {group_record[9]}")
        else:
            print(f"\n✅ 今天沒有策略組記錄")
        
        # 檢查所有日期的策略組統計
        cursor.execute("""
            SELECT date, COUNT(*) as group_count, 
                   GROUP_CONCAT(group_id) as group_ids,
                   GROUP_CONCAT(status) as statuses
            FROM strategy_groups 
            GROUP BY date 
            ORDER BY date DESC
            LIMIT 5
        """)
        
        all_groups = cursor.fetchall()
        
        if all_groups:
            print(f"\n📈 最近5天的策略組統計:")
            print("-" * 60)
            print("日期       | 組數 | 組別ID | 狀態")
            print("-" * 60)
            
            for group_stat in all_groups:
                print(f"{group_stat[0]} | {group_stat[1]:4d} | {group_stat[2]:10s} | {group_stat[3]}")
        
        # 檢查部位記錄
        cursor.execute("""
            SELECT COUNT(*) AS position_count FROM position_records pr
            JOIN strategy_groups sg ON pr.group_id = sg.id
            WHERE sg.date = ?
        """, (today,))
        
        position_count = cursor.fetchone()[0]
        print(f"\n📋 今天的部位記錄數: {position_count}")
        
        # 檢查風險管理狀態
        cursor.execute("""
            SELECT COUNT(*) AS risk_count FROM risk_management_states rms
            JOIN position_records pr ON rms.position_id = pr.id
            JOIN strategy_groups sg ON pr.group_id = sg.group_id AND sg.date = ?
        """, (today,))
        
        risk_count = cursor.fetchone()[0]
        print(f"📋 今天的風險管理記錄數: {risk_count}")
        
        conn.close()
        
        # 提供解決方案建議
        if groups:
            print(f"\n⚠️  發現問題:")
            print(f"   今天已經存在 {len(groups)} 個策略組")
            print(f"   這就是為什麼出現 UNIQUE constraint failed 錯誤")
            print(f"\n💡 解決方案:")
            print(f"   1. 清理今天的策略組記錄")
            print(f"   2. 或者修改程式邏輯，檢查是否已存在")
            print(f"   3. 或者使用不同的 group_id")
        else:
            print(f"\n✅ 資料庫狀態正常，沒有衝突記錄")
        
    except Exception as e:
        print(f"❌ 檢查資料庫失敗: {e}")

def clean_today_records():
    """清理今天的記錄（謹慎使用）"""
    db_path = "multi_group_strategy.db"
    today = date.today().isoformat()
    
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # 先查詢要刪除的記錄
        cursor.execute("SELECT COUNT(*) AS group_count FROM strategy_groups WHERE date = ?", (today,))
        count = cursor.fetchone()[0]
        
        if count == 0:
            print(f"✅ 今天沒有需要清理的記錄")
            return
        
        print(f"⚠️  將要刪除 {count} 個今天的策略組記錄")
        confirm = input("確定要刪除嗎？(輸入 'YES' 確認): ")
        
        if confirm == 'YES':
            # 刪除相關記錄（按外鍵順序）
            cursor.execute("""
                DELETE FROM risk_management_states
                WHERE position_id IN (
                    SELECT pr.id AS position_pk FROM position_records pr
                    JOIN strategy_groups sg ON pr.group_id = sg.id
                    WHERE sg.date = ?
                )
            """, (today,))

            cursor.execute("""
                DELETE FROM position_records
                WHERE group_id IN (
                    SELECT id AS group_pk FROM strategy_groups WHERE date = ?
                )
            """, (today,))
            
            cursor.execute("DELETE FROM strategy_groups WHERE date = ?", (today,))
            
            conn.commit()
            print(f"✅ 已清理今天的所有相關記錄")
        else:
            print(f"❌ 取消清理操作")
        
        conn.close()
        
    except Exception as e:
        print(f"❌ 清理記錄失敗: {e}")

if __name__ == "__main__":
    print("🔧 多組策略資料庫診斷工具")
    print("=" * 50)
    
    # 檢查狀態
    check_database_status()
    
    print("\n" + "=" * 50)
    print("選項:")
    print("1. 僅檢查狀態 (已完成)")
    print("2. 清理今天的記錄 (謹慎使用)")
    
    choice = input("\n請選擇操作 (1/2): ").strip()
    
    if choice == "2":
        print("\n⚠️  警告: 這將刪除今天的所有策略記錄!")
        clean_today_records()
    else:
        print("\n✅ 診斷完成")
