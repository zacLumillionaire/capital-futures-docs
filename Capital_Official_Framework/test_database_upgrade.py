#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
測試資料庫結構升級功能
"""

import os
import sqlite3
from multi_group_database import MultiGroupDatabaseManager

def test_database_upgrade():
    """測試資料庫結構升級"""
    print("🧪 測試資料庫結構升級")
    print("=" * 50)
    
    # 使用測試資料庫
    test_db_path = "test_database_upgrade.db"
    
    # 清理舊的測試資料庫
    if os.path.exists(test_db_path):
        os.remove(test_db_path)
        print("✅ 清理舊測試資料庫")
    
    try:
        # 1. 創建資料庫管理器
        db_manager = MultiGroupDatabaseManager(test_db_path)
        print("✅ 資料庫管理器創建成功")
        
        # 2. 檢查表結構
        with db_manager.get_connection() as conn:
            cursor = conn.cursor()
            
            # 檢查 position_records 表結構
            cursor.execute("PRAGMA table_info(position_records)")
            columns = cursor.fetchall()
            
            print("\n📋 position_records 表結構:")
            for column in columns:
                print(f"  - {column[1]} ({column[2]}) {'NOT NULL' if column[3] else 'NULL'} "
                      f"{'DEFAULT: ' + str(column[4]) if column[4] else ''}")
            
            # 檢查新欄位是否存在
            column_names = [column[1] for column in columns]
            required_columns = ['order_id', 'api_seq_no', 'order_status']
            
            print("\n🔍 檢查新欄位:")
            for col in required_columns:
                if col in column_names:
                    print(f"  ✅ {col} - 存在")
                else:
                    print(f"  ❌ {col} - 不存在")
            
            # 檢查索引
            cursor.execute("SELECT name FROM sqlite_master WHERE type='index' AND tbl_name='position_records'")
            indexes = cursor.fetchall()
            
            print("\n📊 position_records 表索引:")
            for index in indexes:
                print(f"  - {index[0]}")
        
        # 3. 測試新的資料庫操作方法
        print("\n🧪 測試新的資料庫操作方法")
        
        # 創建測試策略組
        from datetime import date
        group_id = db_manager.create_strategy_group(
            date=date.today().strftime('%Y-%m-%d'),
            group_id=1,
            direction="LONG",
            total_lots=2,
            range_high=22530.0,
            range_low=22480.0,
            signal_time="08:48:15"
        )
        print(f"✅ 創建測試策略組: {group_id}")
        
        # 測試創建部位記錄（PENDING狀態）
        position_id = db_manager.create_position_record(
            group_id=group_id,
            lot_id=1,
            direction="LONG",
            entry_time="08:48:20",
            rule_config='{"lot_id": 1, "stop_loss": 20, "take_profit": 40}',
            order_status='PENDING'
        )
        print(f"✅ 創建PENDING部位記錄: {position_id}")
        
        # 測試更新訂單資訊
        success = db_manager.update_position_order_info(
            position_id=position_id,
            order_id="TEST_ORDER_001",
            api_seq_no="12345678901234567"
        )
        print(f"✅ 更新訂單資訊: {success}")
        
        # 測試確認成交
        success = db_manager.confirm_position_filled(
            position_id=position_id,
            actual_fill_price=22515.0,
            fill_time="08:48:25",
            order_status='FILLED'
        )
        print(f"✅ 確認部位成交: {success}")
        
        # 創建第二個部位測試失敗情況
        position_id_2 = db_manager.create_position_record(
            group_id=group_id,
            lot_id=2,
            direction="LONG",
            entry_time="08:48:20",
            rule_config='{"lot_id": 2, "stop_loss": 20, "take_profit": 40}',
            order_status='PENDING'
        )
        
        # 測試標記失敗
        success = db_manager.mark_position_failed(
            position_id=position_id_2,
            failure_reason="FOK失敗",
            order_status='CANCELLED'
        )
        print(f"✅ 標記部位失敗: {success}")
        
        # 測試統計查詢
        stats = db_manager.get_position_statistics()
        print(f"\n📊 部位統計:")
        print(f"  - 總部位數: {stats['total_positions']}")
        print(f"  - 活躍部位: {stats['active_positions']}")
        print(f"  - 失敗部位: {stats['failed_positions']}")
        print(f"  - 成功率: {stats['success_rate']}%")
        
        # 測試根據訂單ID查詢
        position = db_manager.get_position_by_order_id("TEST_ORDER_001")
        if position:
            print(f"\n🔍 根據訂單ID查詢部位:")
            print(f"  - 部位ID: {position['id']}")
            print(f"  - 狀態: {position['status']}")
            print(f"  - 訂單狀態: {position['order_status']}")
            print(f"  - 成交價格: {position['entry_price']}")
        
        print("\n🎉 資料庫升級測試完成！")
        
    except Exception as e:
        print(f"❌ 測試失敗: {e}")
        import traceback
        traceback.print_exc()
    
    finally:
        # 清理測試資料庫
        if os.path.exists(test_db_path):
            os.remove(test_db_path)
            print("🧹 清理測試資料庫")

if __name__ == "__main__":
    test_database_upgrade()
