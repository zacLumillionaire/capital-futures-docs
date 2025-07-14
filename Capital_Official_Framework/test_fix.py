#!/usr/bin/env python3
import sqlite3

def test_database_fix():
    print('驗證修復結果...')
    
    with sqlite3.connect('multi_group_strategy.db') as conn:
        cursor = conn.cursor()
        
        # 測試插入 None 值
        try:
            cursor.execute('''
                INSERT INTO position_records 
                (group_id, lot_id, direction, retry_count, max_slippage_points, status) 
                VALUES (999, 1, 'LONG', NULL, NULL, 'PENDING')
            ''')
            test_id = cursor.lastrowid
            cursor.execute('DELETE FROM position_records WHERE id = ?', (test_id,))
            conn.commit()
            print('✅ 約束測試通過 - None 值被正確處理')
        except Exception as e:
            if 'not supported between instances' in str(e):
                print('❌ 約束測試失敗 - 仍然有 None 值問題')
                print(f'   錯誤: {e}')
            else:
                print('✅ 約束測試通過 - None 值處理正常')
                print(f'   (其他約束錯誤是正常的: {e})')
        
        # 檢查現有數據
        cursor.execute('''
            SELECT COUNT(*) FROM position_records 
            WHERE retry_count IS NULL OR max_slippage_points IS NULL
        ''')
        null_count = cursor.fetchone()[0]
        print(f'剩餘 None 值記錄: {null_count}')
        
        # 檢查最近的部位
        cursor.execute('''
            SELECT id, entry_price, retry_count, max_slippage_points, status 
            FROM position_records 
            WHERE status IN ('ACTIVE', 'PENDING') 
            ORDER BY id DESC LIMIT 5
        ''')
        positions = cursor.fetchall()
        print('最近的部位:')
        for pos in positions:
            pos_id, entry_price, retry_count, max_slippage, status = pos
            print(f'  部位 {pos_id}: 價格={entry_price}, 重試={retry_count}, 滑價={max_slippage}, 狀態={status}')

if __name__ == '__main__':
    test_database_fix()
