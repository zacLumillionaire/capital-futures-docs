#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
NoneType 錯誤重現測試腳本
用於重現和調試 multi_group_position_manager 中的 TypeError: '>=' not supported between instances of 'NoneType' and 'int'
"""

import sys
import os
import sqlite3
from datetime import datetime, date
import json

# 添加當前目錄到路徑
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from multi_group_database import MultiGroupDatabaseManager
from multi_group_position_manager import MultiGroupPositionManager

def setup_test_database():
    """設置測試資料庫"""
    print("🔧 設置測試資料庫...")
    
    # 創建資料庫管理器
    db_manager = MultiGroupDatabaseManager()
    
    # 清理現有數據
    try:
        with db_manager.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM position_records")
            cursor.execute("DELETE FROM strategy_groups")
            cursor.execute("DELETE FROM risk_management_states")
            conn.commit()
            print("✅ 清理現有數據完成")
    except Exception as e:
        print(f"⚠️ 清理數據時出現警告: {e}")
    
    return db_manager

def create_test_strategy_group(db_manager):
    """創建測試策略組"""
    print("📝 創建測試策略組...")
    
    current_date = date.today().isoformat()
    group_id = db_manager.create_strategy_group(
        date=current_date,
        group_id=1,  # 邏輯組別ID
        direction="SHORT",
        signal_time="21:34:05",
        range_high=22894.0,
        range_low=22915.0,
        total_lots=2
    )
    
    print(f"✅ 創建策略組完成: DB_ID={group_id}, 邏輯組別=1")
    return group_id

def create_test_positions(db_manager, group_db_id):
    """創建測試部位記錄"""
    print("📝 創建測試部位記錄...")
    
    positions = []
    
    # 創建2個部位，故意讓某些數字欄位為 None
    for lot_id in range(1, 3):
        # 故意不傳遞 retry_count 和 max_slippage_points，看看是否會導致 None
        position_id = db_manager.create_position_record(
            group_id=group_db_id,
            lot_id=lot_id,
            direction="SHORT",
            entry_price=None,  # 故意設為 None
            entry_time=None,   # 故意設為 None
            rule_config=json.dumps({
                'lot_id': lot_id,
                'use_trailing_stop': True,
                'trailing_activation': 15 if lot_id == 1 else 40,
                'trailing_pullback': 0.20
            }),
            order_id=f"test_order_{lot_id}",
            api_seq_no=f"test_seq_{lot_id}",
            order_status='PENDING'
            # 注意：這裡故意不傳遞 retry_count 和 max_slippage_points
        )
        
        positions.append(position_id)
        print(f"✅ 創建部位記錄: ID={position_id}, lot_id={lot_id}")
    
    return positions

def check_position_data(db_manager, position_ids):
    """檢查部位數據，特別是可能為 None 的欄位"""
    print("🔍 檢查部位數據...")
    
    with db_manager.get_connection() as conn:
        cursor = conn.cursor()
        
        for position_id in position_ids:
            cursor.execute('''
                SELECT id, group_id, lot_id, direction, entry_price, entry_time,
                       retry_count, max_slippage_points, order_status, status
                FROM position_records WHERE id = ?
            ''', (position_id,))
            
            row = cursor.fetchone()
            if row:
                print(f"📊 部位 {position_id} 數據:")
                print(f"   - id: {row[0]}")
                print(f"   - group_id: {row[1]}")
                print(f"   - lot_id: {row[2]}")
                print(f"   - direction: {row[3]}")
                print(f"   - entry_price: {row[4]} (type: {type(row[4])})")
                print(f"   - entry_time: {row[5]} (type: {type(row[5])})")
                print(f"   - retry_count: {row[6]} (type: {type(row[6])})")
                print(f"   - max_slippage_points: {row[7]} (type: {type(row[7])})")
                print(f"   - order_status: {row[8]}")
                print(f"   - status: {row[9]}")
                
                # 檢查是否有 None 值
                if row[6] is None:
                    print(f"   ⚠️ retry_count 為 None!")
                if row[7] is None:
                    print(f"   ⚠️ max_slippage_points 為 None!")

def simulate_fill_callback(position_manager):
    """模擬成交回調，觸發 NoneType 錯誤"""
    print("🎯 模擬成交回調...")
    
    try:
        # 模擬簡化追蹤器的成交回調
        position_manager._update_group_positions_on_fill(
            logical_group_id=1,
            price=22892.0,
            qty=1,
            filled_lots=1,
            total_lots=2
        )
        print("✅ 成交回調執行完成")
        
    except Exception as e:
        print(f"❌ 成交回調執行失敗: {e}")
        print(f"   錯誤類型: {type(e)}")
        import traceback
        traceback.print_exc()

def main():
    """主測試函數"""
    print("🚀 開始 NoneType 錯誤重現測試")
    print("=" * 50)
    
    try:
        # 1. 設置測試資料庫
        db_manager = setup_test_database()
        
        # 2. 創建測試策略組
        group_db_id = create_test_strategy_group(db_manager)
        
        # 3. 創建測試部位記錄
        position_ids = create_test_positions(db_manager, group_db_id)
        
        # 4. 檢查部位數據
        check_position_data(db_manager, position_ids)
        
        # 5. 創建 position manager
        print("🔧 創建 MultiGroupPositionManager...")
        position_manager = MultiGroupPositionManager(db_manager)
        
        # 6. 模擬成交回調
        simulate_fill_callback(position_manager)
        
        print("=" * 50)
        print("🎉 測試完成")
        
    except Exception as e:
        print(f"❌ 測試失敗: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
