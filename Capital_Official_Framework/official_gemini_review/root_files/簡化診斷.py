#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
簡化診斷工具 - 快速檢查平倉問題
"""

import os
import sqlite3
from datetime import date

def check_database():
    """檢查資料庫狀態"""
    print("🔍 檢查資料庫狀態...")
    
    # 檢查資料庫文件
    db_files = [
        "Capital_Official_Framework/multi_group_strategy.db",
        "Capital_Official_Framework/trading_data.db", 
        "Capital_Official_Framework/strategy_trading.db"
    ]
    
    found_db = None
    for db_file in db_files:
        if os.path.exists(db_file):
            print(f"✅ 找到資料庫: {db_file}")
            found_db = db_file
            break
        else:
            print(f"❌ 不存在: {db_file}")
    
    if not found_db:
        print("❌ 沒有找到任何資料庫文件")
        return
    
    # 檢查資料庫內容
    try:
        conn = sqlite3.connect(found_db)
        cursor = conn.cursor()
        
        # 檢查表結構
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
        tables = cursor.fetchall()
        print(f"📊 資料庫表: {[t[0] for t in tables]}")
        
        # 檢查問題部位
        problem_positions = [133, 134, 135]
        
        if 'position_records' in [t[0] for t in tables]:
            print("\n🔍 檢查問題部位:")
            for pos_id in problem_positions:
                cursor.execute("SELECT id, status, group_id, direction FROM position_records WHERE id = ?", (pos_id,))
                row = cursor.fetchone()
                if row:
                    print(f"  部位{pos_id}: 狀態={row[1]}, 組={row[2]}, 方向={row[3]}")
                else:
                    print(f"  部位{pos_id}: 不存在")
        
        # 檢查策略組
        if 'strategy_groups' in [t[0] for t in tables]:
            today = date.today().isoformat()
            cursor.execute("SELECT COUNT(*) FROM strategy_groups WHERE date = ?", (today,))
            count = cursor.fetchone()[0]
            print(f"\n📊 今日策略組: {count}個")
        
        conn.close()
        
    except Exception as e:
        print(f"❌ 資料庫檢查失敗: {e}")

def check_modules():
    """檢查模組導入"""
    print("\n🔍 檢查模組導入...")
    
    modules_to_check = [
        "simplified_order_tracker",
        "stop_loss_executor", 
        "optimized_risk_manager",
        "multi_group_position_manager"
    ]
    
    import sys
    sys.path.append("Capital_Official_Framework")
    
    for module_name in modules_to_check:
        try:
            __import__(module_name)
            print(f"✅ {module_name}: 導入成功")
        except ImportError as e:
            print(f"❌ {module_name}: 導入失敗 - {e}")
        except Exception as e:
            print(f"⚠️ {module_name}: 其他錯誤 - {e}")

def check_files():
    """檢查關鍵文件"""
    print("\n🔍 檢查關鍵文件...")
    
    key_files = [
        "Capital_Official_Framework/simple_integrated.py",
        "Capital_Official_Framework/simplified_order_tracker.py",
        "Capital_Official_Framework/stop_loss_executor.py",
        "Capital_Official_Framework/optimized_risk_manager.py",
        "Capital_Official_Framework/multi_group_position_manager.py"
    ]
    
    for file_path in key_files:
        if os.path.exists(file_path):
            size = os.path.getsize(file_path)
            print(f"✅ {file_path} ({size} bytes)")
        else:
            print(f"❌ {file_path}: 不存在")

def main():
    print("🚨 平倉問題簡化診斷")
    print("=" * 50)
    
    check_files()
    check_database() 
    check_modules()
    
    print("\n" + "=" * 50)
    print("📋 診斷完成")
    print("\n下一步:")
    print("1. 如果資料庫中沒有部位133、134、135，說明記錄已被清理")
    print("2. 如果部位存在但狀態不是ACTIVE，說明狀態問題")
    print("3. 如果模組導入失敗，說明代碼問題")
    print("4. 需要在實際運行時檢查緩存狀態")

if __name__ == "__main__":
    main()
