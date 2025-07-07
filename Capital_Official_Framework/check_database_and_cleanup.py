#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
檢查資料庫狀態並提供清理功能
"""

import os
import sqlite3
from datetime import date

def check_database_status():
    """檢查資料庫狀態"""
    print("🔍 檢查多組策略資料庫狀態")
    print("=" * 50)
    
    db_path = "multi_group_strategy.db"
    
    if not os.path.exists(db_path):
        print("❌ 資料庫檔案不存在")
        return False
    
    try:
        conn = sqlite3.connect(db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        # 檢查資料庫表結構
        print("📋 資料庫表結構:")
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
        tables = cursor.fetchall()
        for table in tables:
            print(f"  - {table['name']}")
        
        # 檢查活躍部位
        print(f"\n📊 部位狀態統計:")
        cursor.execute('''
            SELECT status, COUNT(*) as count 
            FROM position_records 
            GROUP BY status
        ''')
        status_counts = cursor.fetchall()
        
        total_positions = 0
        for status in status_counts:
            print(f"  - {status['status']}: {status['count']} 個")
            total_positions += status['count']
        
        print(f"  - 總計: {total_positions} 個部位")
        
        # 檢查活躍部位詳細信息
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
        
        if active_positions:
            print(f"\n🔥 活躍部位詳細信息 ({len(active_positions)} 個):")
            for pos in active_positions:
                print(f"  - 部位{pos['id']}: 組{pos['original_group_id']}, {pos['direction']}, "
                      f"@{pos['entry_price']}, 狀態:{pos['order_status']}, 日期:{pos['date']}")
        else:
            print(f"\n✅ 沒有活躍部位")
        
        # 檢查策略組狀態
        print(f"\n📈 策略組狀態:")
        cursor.execute('''
            SELECT status, COUNT(*) as count 
            FROM strategy_groups 
            GROUP BY status
        ''')
        group_status = cursor.fetchall()
        
        for status in group_status:
            print(f"  - {status['status']}: {status['count']} 組")
        
        # 檢查風險管理狀態
        cursor.execute('SELECT COUNT(*) as count FROM risk_management_states')
        risk_count = cursor.fetchone()['count']
        print(f"\n🛡️ 風險管理狀態記錄: {risk_count} 個")
        
        conn.close()
        return True, active_positions
        
    except Exception as e:
        print(f"❌ 檢查資料庫失敗: {e}")
        return False, []

def cleanup_active_positions(active_positions):
    """清理活躍部位"""
    if not active_positions:
        print("✅ 沒有活躍部位需要清理")
        return
    
    print(f"\n⚠️ 發現 {len(active_positions)} 個活躍部位")
    print("這些部位可能會觸發風險管理停損")
    
    choice = input("\n是否要清理這些部位？(y/N): ").strip().lower()
    if choice != 'y':
        print("❌ 取消清理")
        return
    
    # 清理方式選擇
    print("\n🔧 清理方式:")
    print("1. 標記為已出場 (保留記錄，PnL=0)")
    print("2. 標記為失敗 (測試數據)")
    print("3. 直接刪除 (完全移除)")
    
    method = input("請選擇清理方式 (1/2/3): ").strip()
    
    try:
        conn = sqlite3.connect("multi_group_strategy.db")
        cursor = conn.cursor()
        
        if method == "1":
            # 標記為已出場
            for pos in active_positions:
                cursor.execute('''
                    UPDATE position_records 
                    SET status = 'EXITED', 
                        exit_price = COALESCE(entry_price, 0),
                        exit_time = datetime('now', 'localtime'),
                        exit_reason = '手動清理',
                        pnl = 0,
                        pnl_amount = 0,
                        updated_at = CURRENT_TIMESTAMP
                    WHERE id = ?
                ''', (pos['id'],))
            
            print(f"✅ 已將 {len(active_positions)} 個部位標記為已出場")
            
        elif method == "2":
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
            
        elif method == "3":
            # 直接刪除
            for pos in active_positions:
                cursor.execute('DELETE FROM position_records WHERE id = ?', (pos['id'],))
            
            print(f"✅ 已刪除 {len(active_positions)} 個部位記錄")
            
        else:
            print("❌ 無效選擇，取消清理")
            conn.close()
            return
        
        # 清理孤立的風險管理狀態
        cursor.execute('''
            DELETE FROM risk_management_states 
            WHERE position_id NOT IN (
                SELECT id FROM position_records WHERE status = 'ACTIVE'
            )
        ''')
        
        orphaned_count = cursor.rowcount
        if orphaned_count > 0:
            print(f"✅ 已清理 {orphaned_count} 個孤立的風險管理狀態")
        
        conn.commit()
        conn.close()
        
        print("\n🎉 清理完成！")
        print("💡 現在可以重新測試策略，不會有舊部位觸發停損")
        
    except Exception as e:
        print(f"❌ 清理失敗: {e}")

def main():
    """主函數"""
    success, active_positions = check_database_status()
    
    if success and active_positions:
        cleanup_active_positions(active_positions)
    elif success:
        print("\n✅ 資料庫狀態正常，沒有需要清理的部位")

if __name__ == "__main__":
    main()
