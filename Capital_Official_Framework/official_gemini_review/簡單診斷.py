#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
簡單診斷移動停利問題
"""

import sqlite3
import os

def simple_diagnose():
    """簡單診斷"""
    print("🔍 簡單診斷移動停利問題")
    print("=" * 50)
    
    # 檢查資料庫文件
    db_files = ["test_virtual_strategy.db", "multi_group_strategy.db"]
    
    for db_file in db_files:
        if os.path.exists(db_file):
            print(f"\n📁 檢查資料庫: {db_file}")
            try:
                conn = sqlite3.connect(db_file)
                cursor = conn.cursor()
                
                # 檢查表結構
                cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
                tables = [row[0] for row in cursor.fetchall()]
                print(f"  表: {tables}")
                
                # 檢查活躍部位
                if 'position_records' in tables:
                    cursor.execute("SELECT COUNT(*) FROM position_records WHERE status = 'ACTIVE'")
                    active_count = cursor.fetchone()[0]
                    print(f"  活躍部位數量: {active_count}")
                    
                    if active_count > 0:
                        cursor.execute("SELECT id, direction, entry_price, status FROM position_records WHERE status = 'ACTIVE' LIMIT 3")
                        positions = cursor.fetchall()
                        for pos in positions:
                            print(f"    部位 {pos[0]}: {pos[1]} @{pos[2]} ({pos[3]})")
                
                # 檢查策略組
                if 'strategy_groups' in tables:
                    cursor.execute("SELECT COUNT(*) FROM strategy_groups")
                    group_count = cursor.fetchone()[0]
                    print(f"  策略組數量: {group_count}")
                    
                    if group_count > 0:
                        cursor.execute("SELECT id, range_high, range_low FROM strategy_groups LIMIT 3")
                        groups = cursor.fetchall()
                        for group in groups:
                            print(f"    組 {group[0]}: 區間 {group[2]} - {group[1]}")
                
                conn.close()
                
            except Exception as e:
                print(f"  ❌ 錯誤: {e}")
        else:
            print(f"\n❌ 資料庫不存在: {db_file}")

if __name__ == "__main__":
    simple_diagnose()
