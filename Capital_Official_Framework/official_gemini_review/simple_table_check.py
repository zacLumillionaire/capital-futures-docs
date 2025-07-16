#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
簡單檢查表結構
"""

import sqlite3

try:
    conn = sqlite3.connect("multi_group_strategy.db")
    cursor = conn.cursor()
    
    # 檢查 position_records 表結構
    cursor.execute("SELECT sql FROM sqlite_master WHERE type='table' AND name='position_records'")
    result = cursor.fetchone()
    
    if result:
        print("position_records 表結構:")
        print(result[0])
    else:
        print("找不到 position_records 表")
    
    conn.close()
    
except Exception as e:
    print(f"錯誤: {e}")
