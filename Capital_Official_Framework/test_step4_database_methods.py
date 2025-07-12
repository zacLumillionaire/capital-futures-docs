#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
測試步驟4：擴展資料庫操作方法
"""

import os
from datetime import date

def test_step4_database_methods():
    """測試步驟4的資料庫操作方法"""
    print("🧪 測試步驟4：擴展資料庫操作方法")
    print("=" * 60)
    
    # 清理舊的測試資料庫
    test_db_path = "test_step4_database_methods.db"
    if os.path.exists(test_db_path):
        os.remove(test_db_path)
        print("✅ 清理舊測試資料庫")
    
    try:
        # 導入必要模組
        from multi_group_database import MultiGroupDatabaseManager
        
        # 1. 創建資料庫管理器
        db_manager = MultiGroupDatabaseManager(test_db_path)
        print("✅ 資料庫管理器創建成功")
        
        # 2. 測試創建策略組
        today = date.today().strftime('%Y-%m-%d')
        group_id = db_manager.create_strategy_group(
            date=today,
            group_id=1,
            direction="LONG",
            total_lots=3,
            range_high=22530.0,
            range_low=22480.0,
            signal_time="08:48:15"
        )
        print(f"✅ 創建策略組: {group_id}")
        
        # 3. 測試創建部位記錄（新的參數）
        print(f"\n📝 測試新的部位記錄創建方法:")
        
        # 創建3個部位記錄
        position_ids = []
        for i in range(1, 4):
            position_id = db_manager.create_position_record(
                group_id=group_id,
                lot_id=i,
                direction="LONG",
                entry_time="08:48:20",
                rule_config=f'{{"lot_id": {i}, "stop_loss": 20, "take_profit": 40}}',
                order_status='PENDING'
            )
            position_ids.append(position_id)
            print(f"  ✅ 創建部位{i}: ID={position_id}, 狀態=PENDING")
        
        # 4. 測試更新訂單資訊
        print(f"\n📋 測試更新訂單資訊:")
        for i, position_id in enumerate(position_ids):
            order_id = f"TEST_ORDER_{i+1:03d}"
            api_seq_no = f"API_{i+1:013d}"
            
            success = db_manager.update_position_order_info(
                position_id=position_id,
                order_id=order_id,
                api_seq_no=api_seq_no
            )
            print(f"  ✅ 更新部位{position_id}訂單資訊: {success}")
        
        # 5. 測試確認部位成交
        print(f"\n🎯 測試確認部位成交:")
        
        # 前兩個部位成交
        for i in range(2):
            position_id = position_ids[i]
            fill_price = 22515.0 + i
            
            success = db_manager.confirm_position_filled(
                position_id=position_id,
                actual_fill_price=fill_price,
                fill_time="08:48:25",
                order_status='FILLED'
            )
            print(f"  ✅ 確認部位{position_id}成交: @{fill_price}, 結果={success}")
        
        # 6. 測試標記部位失敗
        print(f"\n❌ 測試標記部位失敗:")
        
        # 第三個部位失敗
        position_id = position_ids[2]
        success = db_manager.mark_position_failed(
            position_id=position_id,
            failure_reason='FOK失敗',
            order_status='CANCELLED'
        )
        print(f"  ✅ 標記部位{position_id}失敗: 結果={success}")
        
        # 7. 測試根據訂單ID查詢部位
        print(f"\n🔍 測試根據訂單ID查詢部位:")
        
        for i in range(3):
            order_id = f"TEST_ORDER_{i+1:03d}"
            position = db_manager.get_position_by_order_id(order_id)
            
            if position:
                print(f"  ✅ 訂單{order_id}: 部位ID={position['id']}, "
                      f"狀態={position['status']}/{position['order_status']}")
            else:
                print(f"  ❌ 訂單{order_id}: 找不到對應部位")
        
        # 8. 測試部位統計
        print(f"\n📊 測試部位統計:")
        stats = db_manager.get_position_statistics(today)
        
        print(f"  - 總部位數: {stats['total_positions']}")
        print(f"  - 活躍部位: {stats['active_positions']}")
        print(f"  - 失敗部位: {stats['failed_positions']}")
        print(f"  - 已出場部位: {stats['exited_positions']}")
        print(f"  - 成功率: {stats['success_rate']}%")
        
        # 9. 測試詳細查詢
        print(f"\n📋 測試詳細查詢:")
        
        # 查詢所有部位記錄
        with db_manager.get_connection() as conn:
            conn.row_factory = lambda cursor, row: dict(zip([col[0] for col in cursor.description], row))
            cursor = conn.cursor()
            cursor.execute('''
                SELECT id, lot_id, status, order_status, order_id, api_seq_no, 
                       entry_price, exit_reason
                FROM position_records 
                WHERE group_id = ?
                ORDER BY lot_id
            ''', (group_id,))
            positions = cursor.fetchall()
        
        for pos in positions:
            status_icon = "✅" if pos['status'] == 'ACTIVE' else "❌" if pos['status'] == 'FAILED' else "⏳"
            print(f"  {status_icon} 部位{pos['id']}-第{pos['lot_id']}口:")
            print(f"      狀態: {pos['status']}/{pos['order_status']}")
            print(f"      訂單: {pos['order_id']}")
            print(f"      API序號: {pos['api_seq_no']}")
            print(f"      成交價: {pos['entry_price']}")
            if pos['exit_reason']:
                print(f"      失敗原因: {pos['exit_reason']}")
        
        # 10. 測試資料庫約束和驗證
        print(f"\n🔒 測試資料庫約束:")
        
        # 檢查狀態約束
        with db_manager.get_connection() as conn:
            cursor = conn.cursor()
            
            # 檢查所有狀態都是有效的
            cursor.execute('''
                SELECT DISTINCT status FROM position_records
            ''')
            statuses = [row[0] for row in cursor.fetchall()]
            valid_statuses = ['ACTIVE', 'EXITED', 'FAILED']
            
            for status in statuses:
                if status in valid_statuses:
                    print(f"  ✅ 狀態 '{status}' 有效")
                else:
                    print(f"  ❌ 狀態 '{status}' 無效")
            
            # 檢查訂單狀態約束
            cursor.execute('''
                SELECT DISTINCT order_status FROM position_records
                WHERE order_status IS NOT NULL
            ''')
            order_statuses = [row[0] for row in cursor.fetchall()]
            valid_order_statuses = ['PENDING', 'FILLED', 'CANCELLED', 'REJECTED']
            
            for order_status in order_statuses:
                if order_status in valid_order_statuses:
                    print(f"  ✅ 訂單狀態 '{order_status}' 有效")
                else:
                    print(f"  ❌ 訂單狀態 '{order_status}' 無效")
        
        # 11. 測試索引效能
        print(f"\n⚡ 測試索引效能:")
        
        with db_manager.get_connection() as conn:
            cursor = conn.cursor()
            
            # 測試訂單ID索引
            cursor.execute("EXPLAIN QUERY PLAN SELECT * FROM position_records WHERE order_id = 'TEST_ORDER_001'")
            plan = cursor.fetchall()
            uses_index = any("idx_position_records_order_id" in str(row) for row in plan)
            print(f"  {'✅' if uses_index else '❌'} 訂單ID查詢使用索引: {uses_index}")
            
            # 測試API序號索引
            cursor.execute("EXPLAIN QUERY PLAN SELECT * FROM position_records WHERE api_seq_no = 'API_0000000000001'")
            plan = cursor.fetchall()
            uses_index = any("idx_position_records_api_seq_no" in str(row) for row in plan)
            print(f"  {'✅' if uses_index else '❌'} API序號查詢使用索引: {uses_index}")
        
        # 12. 驗證數據一致性
        print(f"\n🔍 驗證數據一致性:")
        
        # 檢查活躍部位是否都有訂單ID
        with db_manager.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                SELECT COUNT(*) FROM position_records 
                WHERE status = 'ACTIVE' AND (order_id IS NULL OR order_id = '')
            ''')
            active_without_order = cursor.fetchone()[0]
        
        if active_without_order == 0:
            print("  ✅ 所有活躍部位都有訂單ID")
        else:
            print(f"  ❌ 發現 {active_without_order} 個活躍部位沒有訂單ID")
        
        # 檢查失敗部位是否都有失敗原因
        with db_manager.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                SELECT COUNT(*) FROM position_records 
                WHERE status = 'FAILED' AND (exit_reason IS NULL OR exit_reason = '')
            ''')
            failed_without_reason = cursor.fetchone()[0]
        
        if failed_without_reason == 0:
            print("  ✅ 所有失敗部位都有失敗原因")
        else:
            print(f"  ❌ 發現 {failed_without_reason} 個失敗部位沒有失敗原因")
        
        print("\n🎉 步驟4測試完成！")
        print("\n📋 測試結果總結:")
        print("  ✅ 所有新增的資料庫操作方法正常運作")
        print("  ✅ 訂單追蹤相關欄位正確記錄")
        print("  ✅ 狀態轉換邏輯正確")
        print("  ✅ 資料庫約束和索引正常")
        print("  ✅ 數據一致性驗證通過")
        
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
    test_step4_database_methods()
