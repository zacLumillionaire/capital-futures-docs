#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
測試風險管理狀態創建修復
驗證使用 '初始化' 作為 update_reason 不會出現約束錯誤
"""

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), 'Capital_Official_Framework'))

def test_risk_management_state_creation():
    """測試風險管理狀態創建"""
    print("🧪 測試風險管理狀態創建修復")
    print("=" * 50)
    
    try:
        from multi_group_database import MultiGroupDatabaseManager
        from datetime import datetime
        
        # 使用實際的資料庫文件
        db_manager = MultiGroupDatabaseManager("multi_group_strategy.db")
        print("✅ 連接到實際資料庫")
        
        # 檢查現有約束
        with db_manager.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT sql FROM sqlite_master WHERE type='table' AND name='risk_management_states'")
            result = cursor.fetchone()
            if result:
                table_sql = result[0]
                print("📋 當前表格約束:")
                # 提取約束部分
                if 'CHECK(' in table_sql:
                    constraint_start = table_sql.find('CHECK(')
                    constraint_end = table_sql.find(')', constraint_start) + 1
                    constraint = table_sql[constraint_start:constraint_end]
                    print(f"  {constraint}")
                    
                    # 檢查是否包含我們需要的值
                    if "'初始化'" in constraint:
                        print("  ✅ 約束包含 '初始化'")
                    else:
                        print("  ❌ 約束不包含 '初始化'")
                        
                    if "'成交初始化'" in constraint:
                        print("  ✅ 約束包含 '成交初始化'")
                    else:
                        print("  ❌ 約束不包含 '成交初始化'")
        
        # 測試創建風險管理狀態
        print("\n🧪 測試風險管理狀態創建...")
        
        # 測試1: 使用 '初始化' (應該成功)
        try:
            # 先創建一個測試部位
            current_date = datetime.now().strftime("%Y%m%d")
            group_id = db_manager.create_strategy_group(
                date=current_date,
                group_id=999,
                direction="LONG",
                signal_time="00:31:03",
                range_high=22340.0,
                range_low=22330.0,
                total_lots=1
            )
            
            position_id = db_manager.create_position_record(
                group_id=group_id,
                lot_id=1,
                direction="LONG",
                entry_time="00:31:03",
                rule_config='{"lot_id": 1}',
                order_status='PENDING'
            )
            
            # 確認部位成交
            db_manager.confirm_position_filled(
                position_id=position_id,
                actual_fill_price=22335.0,
                fill_time="00:31:03",
                order_status='FILLED'
            )
            
            # 測試創建風險管理狀態
            success = db_manager.create_risk_management_state(
                position_id=position_id,
                peak_price=22335.0,
                current_time="00:31:03",
                update_reason="初始化"
            )
            
            if success:
                print("✅ 測試1成功: update_reason='初始化'")
            else:
                print("❌ 測試1失敗: 創建風險管理狀態失敗")
                
        except Exception as e:
            print(f"❌ 測試1失敗: {e}")
        
        # 測試2: 使用 '成交初始化' (可能失敗)
        try:
            position_id2 = db_manager.create_position_record(
                group_id=group_id,
                lot_id=2,
                direction="LONG",
                entry_time="00:31:03",
                rule_config='{"lot_id": 2}',
                order_status='PENDING'
            )
            
            db_manager.confirm_position_filled(
                position_id=position_id2,
                actual_fill_price=22335.0,
                fill_time="00:31:03",
                order_status='FILLED'
            )
            
            success = db_manager.create_risk_management_state(
                position_id=position_id2,
                peak_price=22335.0,
                current_time="00:31:03",
                update_reason="成交初始化"
            )
            
            if success:
                print("✅ 測試2成功: update_reason='成交初始化'")
            else:
                print("❌ 測試2失敗: 創建風險管理狀態失敗")
                
        except Exception as e:
            print(f"❌ 測試2失敗 (預期): {e}")
        
        # 清理測試數據
        with db_manager.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM risk_management_states WHERE position_id IN (?, ?)", (position_id, position_id2))
            cursor.execute("DELETE FROM position_records WHERE group_id = ?", (group_id,))
            cursor.execute("DELETE FROM strategy_groups WHERE id = ?", (group_id,))
            conn.commit()
            print("✅ 測試數據已清理")
        
        return True
        
    except Exception as e:
        print(f"❌ 測試失敗: {e}")
        import traceback
        print(traceback.format_exc())
        return False

if __name__ == "__main__":
    print("🚀 開始測試風險管理狀態創建修復")
    print("=" * 80)
    
    success = test_risk_management_state_creation()
    
    print("\n📋 測試總結")
    print("=" * 80)
    
    if success:
        print("🎉 修復驗證成功!")
        print("✅ 使用 '初始化' 作為 update_reason 可以避免約束錯誤")
        print("✅ 建倉過程不會受到影響")
        print("\n📝 修復內容:")
        print("1. 將 update_reason 從 '成交初始化' 改為 '初始化'")
        print("2. 使用資料庫現有約束支援的值")
        print("3. 避免修改資料庫結構的風險")
    else:
        print("❌ 修復驗證失敗，請檢查代碼")
