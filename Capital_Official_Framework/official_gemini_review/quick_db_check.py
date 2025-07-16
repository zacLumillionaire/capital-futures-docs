import sqlite3
import os

def quick_check():
    db_path = "multi_group_strategy.db"
    if not os.path.exists(db_path):
        print(f"資料庫不存在: {db_path}")
        return
    
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # 檢查表格是否存在
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='lot_exit_rules'")
        if not cursor.fetchone():
            print("lot_exit_rules 表格不存在")
            conn.close()
            return
        
        # 檢查規則數量
        cursor.execute("SELECT COUNT(*) FROM lot_exit_rules WHERE is_default = 1")
        count = cursor.fetchone()[0]
        print(f"預設規則數量: {count}")
        
        # 如果數量過多，清理
        if count > 3:
            print(f"清理重複規則...")
            
            # 保留每個口數的第一個規則
            cursor.execute('''
                DELETE FROM lot_exit_rules 
                WHERE is_default = 1 AND id NOT IN (
                    SELECT MIN(id) 
                    FROM lot_exit_rules 
                    WHERE is_default = 1 
                    GROUP BY lot_number
                )
            ''')
            
            deleted = cursor.rowcount
            print(f"刪除了 {deleted} 個重複規則")
            
            # 檢查結果
            cursor.execute("SELECT COUNT(*) FROM lot_exit_rules WHERE is_default = 1")
            new_count = cursor.fetchone()[0]
            print(f"清理後規則數量: {new_count}")
            
            conn.commit()
        
        conn.close()
        print("修復完成")
        
    except Exception as e:
        print(f"錯誤: {e}")

if __name__ == "__main__":
    quick_check()
