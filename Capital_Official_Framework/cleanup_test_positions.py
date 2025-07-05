#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
清理測試部位，避免觸發停損
"""

import os
import sqlite3
from datetime import date

def cleanup_test_positions():
    """清理測試部位"""
    print("🧹 清理測試部位")
    print("=" * 50)
    
    db_path = "Capital_Official_Framework/multi_group_strategy.db"
    
    if not os.path.exists(db_path):
        print("❌ 資料庫檔案不存在")
        return
    
    try:
        conn = sqlite3.connect(db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        # 1. 檢查當前的活躍部位
        print("🔍 檢查當前活躍部位...")
        cursor.execute('''
            SELECT pr.id, pr.group_id, pr.lot_id, pr.direction, pr.entry_price, 
                   pr.status, pr.order_status, sg.group_id as original_group_id,
                   sg.date, pr.created_at
            FROM position_records pr
            JOIN strategy_groups sg ON pr.group_id = sg.id
            WHERE pr.status = 'ACTIVE'
            ORDER BY pr.created_at
        ''')
        
        active_positions = cursor.fetchall()
        
        if not active_positions:
            print("✅ 沒有活躍部位需要清理")
            conn.close()
            return
        
        print(f"找到 {len(active_positions)} 個活躍部位:")
        for pos in active_positions:
            print(f"  - 部位{pos['id']}: 組{pos['original_group_id']}, {pos['direction']}, "
                  f"@{pos['entry_price']}, 日期:{pos['date']}")
        
        # 2. 詢問是否清理
        print(f"\n⚠️ 這些部位可能是測試數據，會觸發風險管理停損")
        choice = input("是否要清理這些部位？(y/N): ").strip().lower()
        
        if choice != 'y':
            print("❌ 取消清理")
            conn.close()
            return
        
        # 3. 清理方式選擇
        print("\n🔧 清理方式:")
        print("1. 標記為已出場 (保留記錄)")
        print("2. 直接刪除 (完全移除)")
        print("3. 標記為失敗 (測試數據)")
        
        method = input("請選擇清理方式 (1/2/3): ").strip()
        
        if method == "1":
            # 標記為已出場
            for pos in active_positions:
                cursor.execute('''
                    UPDATE position_records 
                    SET status = 'EXITED', 
                        exit_price = entry_price,
                        exit_time = datetime('now', 'localtime'),
                        exit_reason = '手動清理',
                        pnl = 0,
                        pnl_amount = 0,
                        updated_at = CURRENT_TIMESTAMP
                    WHERE id = ?
                ''', (pos['id'],))
            
            print(f"✅ 已將 {len(active_positions)} 個部位標記為已出場")
            
        elif method == "2":
            # 直接刪除部位記錄
            for pos in active_positions:
                cursor.execute('DELETE FROM position_records WHERE id = ?', (pos['id'],))
            
            print(f"✅ 已刪除 {len(active_positions)} 個部位記錄")
            
        elif method == "3":
            # 標記為失敗
            for pos in active_positions:
                cursor.execute('''
                    UPDATE position_records 
                    SET status = 'FAILED',
                        order_status = 'CANCELLED',
                        exit_reason = '測試數據清理',
                        updated_at = CURRENT_TIMESTAMP
                    WHERE id = ?
                ''', (pos['id'],))
            
            print(f"✅ 已將 {len(active_positions)} 個部位標記為失敗")
            
        else:
            print("❌ 無效選擇，取消清理")
            conn.close()
            return
        
        # 4. 檢查是否要清理風險管理狀態
        cursor.execute('''
            SELECT COUNT(*) FROM risk_management_states rms
            JOIN position_records pr ON rms.position_id = pr.id
            WHERE pr.status != 'ACTIVE'
        ''')
        
        orphaned_risk_states = cursor.fetchone()[0]
        
        if orphaned_risk_states > 0:
            print(f"\n🔍 發現 {orphaned_risk_states} 個孤立的風險管理狀態記錄")
            clean_risk = input("是否清理這些記錄？(y/N): ").strip().lower()
            
            if clean_risk == 'y':
                cursor.execute('''
                    DELETE FROM risk_management_states 
                    WHERE position_id IN (
                        SELECT pr.id FROM position_records pr 
                        WHERE pr.status != 'ACTIVE'
                    )
                ''')
                print(f"✅ 已清理 {orphaned_risk_states} 個風險管理狀態記錄")
        
        # 5. 提交變更
        conn.commit()
        
        # 6. 驗證清理結果
        print(f"\n📊 清理後狀態:")
        cursor.execute("SELECT COUNT(*) FROM position_records WHERE status = 'ACTIVE'")
        active_count = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM position_records WHERE status = 'EXITED'")
        exited_count = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM position_records WHERE status = 'FAILED'")
        failed_count = cursor.fetchone()[0]
        
        print(f"  - 活躍部位: {active_count}")
        print(f"  - 已出場部位: {exited_count}")
        print(f"  - 失敗部位: {failed_count}")
        
        conn.close()
        
        print("\n🎉 清理完成！")
        print("💡 現在可以重新測試策略，不會有舊部位觸發停損")
        
    except Exception as e:
        print(f"❌ 清理失敗: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    cleanup_test_positions()
