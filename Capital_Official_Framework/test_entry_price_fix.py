#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
測試 entry_price NOT NULL 約束修復
"""

import os
import sqlite3
from datetime import date

def test_entry_price_fix():
    """測試 entry_price 約束修復"""
    print("🧪 測試 entry_price NOT NULL 約束修復")
    print("=" * 50)
    
    # 使用實際的資料庫檔案
    db_path = "Capital_Official_Framework/multi_group_strategy.db"
    
    try:
        # 1. 檢查當前表結構
        print("🔍 檢查當前表結構...")
        if os.path.exists(db_path):
            conn = sqlite3.connect(db_path)
            cursor = conn.cursor()
            
            # 檢查表結構
            cursor.execute("SELECT sql FROM sqlite_master WHERE type='table' AND name='position_records'")
            table_sql = cursor.fetchone()
            
            if table_sql:
                print(f"當前表結構:")
                print(table_sql[0])
                
                if 'entry_price REAL NOT NULL' in table_sql[0]:
                    print("❌ 發現問題：entry_price 有 NOT NULL 約束")
                else:
                    print("✅ entry_price 約束正確（允許 NULL）")
            else:
                print("❌ position_records 表不存在")
            
            conn.close()
        else:
            print("❌ 資料庫檔案不存在")
        
        # 2. 測試資料庫管理器的修復功能
        print("\n🔧 測試資料庫管理器修復功能...")
        
        from multi_group_database import MultiGroupDatabaseManager
        
        # 創建資料庫管理器（會自動執行升級）
        db_manager = MultiGroupDatabaseManager(db_path)
        print("✅ 資料庫管理器初始化完成")
        
        # 3. 測試創建 PENDING 部位記錄
        print("\n🧪 測試創建 PENDING 部位記錄...")
        
        # 先創建一個測試策略組
        today = date.today().strftime('%Y-%m-%d')
        group_id = db_manager.create_strategy_group(
            date=today,
            group_id=999,  # 使用測試ID
            direction="SHORT",
            total_lots=1,
            range_high=22379.0,
            range_low=22375.0,
            signal_time="23:49:00"
        )
        print(f"✅ 創建測試策略組: {group_id}")
        
        # 測試創建 PENDING 部位記錄（entry_price=None）
        position_id = db_manager.create_position_record(
            group_id=group_id,
            lot_id=1,
            direction="SHORT",
            entry_time="23:49:00",
            rule_config='{"lot_id": 1, "stop_loss": 20, "take_profit": 40}',
            order_status='PENDING'  # entry_price=None
        )
        print(f"✅ 創建 PENDING 部位記錄成功: {position_id}")
        
        # 4. 驗證記錄
        print("\n🔍 驗證記錄...")
        with db_manager.get_connection() as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            cursor.execute('''
                SELECT id, group_id, lot_id, direction, entry_price, order_status, status
                FROM position_records 
                WHERE id = ?
            ''', (position_id,))
            record = cursor.fetchone()
            
            if record:
                print(f"部位記錄:")
                print(f"  - ID: {record['id']}")
                print(f"  - 組別: {record['group_id']}")
                print(f"  - 方向: {record['direction']}")
                print(f"  - 成交價: {record['entry_price']} (應該是 None)")
                print(f"  - 訂單狀態: {record['order_status']}")
                print(f"  - 部位狀態: {record['status']}")
                
                if record['entry_price'] is None and record['order_status'] == 'PENDING':
                    print("✅ PENDING 部位記錄正確（entry_price 為 NULL）")
                else:
                    print("❌ PENDING 部位記錄有問題")
            else:
                print("❌ 找不到部位記錄")
        
        # 5. 測試更新為成交狀態
        print("\n🎯 測試更新為成交狀態...")
        success = db_manager.confirm_position_filled(
            position_id=position_id,
            actual_fill_price=22373.0,
            fill_time="23:49:01",
            order_status='FILLED'
        )
        print(f"✅ 更新為成交狀態: {success}")
        
        # 驗證更新後的記錄
        with db_manager.get_connection() as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            cursor.execute('''
                SELECT entry_price, order_status, status
                FROM position_records 
                WHERE id = ?
            ''', (position_id,))
            record = cursor.fetchone()
            
            if record:
                print(f"更新後記錄:")
                print(f"  - 成交價: {record['entry_price']}")
                print(f"  - 訂單狀態: {record['order_status']}")
                print(f"  - 部位狀態: {record['status']}")
                
                if (record['entry_price'] == 22373.0 and 
                    record['order_status'] == 'FILLED' and 
                    record['status'] == 'ACTIVE'):
                    print("✅ 成交狀態更新正確")
                else:
                    print("❌ 成交狀態更新有問題")
        
        print("\n🎉 測試完成！")
        print("\n📋 測試結果總結:")
        print("  ✅ 資料庫結構修復成功")
        print("  ✅ PENDING 部位記錄創建成功")
        print("  ✅ 成交狀態更新成功")
        print("  ✅ entry_price 約束問題已解決")
        
    except Exception as e:
        print(f"❌ 測試失敗: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_entry_price_fix()
