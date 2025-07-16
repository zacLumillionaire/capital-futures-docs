import sqlite3

def check_schema():
    try:
        conn = sqlite3.connect("multi_group_strategy.db")
        cursor = conn.cursor()
        
        # 檢查表格結構
        cursor.execute("PRAGMA table_info(lot_exit_rules)")
        columns = cursor.fetchall()
        
        print("lot_exit_rules 表格結構:")
        for col in columns:
            print(f"  {col[1]} {col[2]} {'NOT NULL' if col[3] else 'NULL'} {'PRIMARY KEY' if col[5] else ''}")
        
        # 檢查索引
        cursor.execute("PRAGMA index_list(lot_exit_rules)")
        indexes = cursor.fetchall()
        
        print("\n索引:")
        for idx in indexes:
            print(f"  {idx[1]} {'UNIQUE' if idx[2] else 'NON-UNIQUE'}")
            
            # 檢查索引詳情
            cursor.execute(f"PRAGMA index_info({idx[1]})")
            idx_info = cursor.fetchall()
            for info in idx_info:
                print(f"    欄位: {info[2]}")
        
        # 檢查當前數據
        cursor.execute("SELECT COUNT(*) FROM lot_exit_rules")
        total = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM lot_exit_rules WHERE is_default = 1")
        default_count = cursor.fetchone()[0]
        
        print(f"\n數據統計:")
        print(f"  總規則數: {total}")
        print(f"  預設規則數: {default_count}")
        
        # 檢查重複
        cursor.execute('''
            SELECT rule_name, lot_number, COUNT(*) as count
            FROM lot_exit_rules 
            WHERE is_default = 1
            GROUP BY rule_name, lot_number
            HAVING count > 1
        ''')
        duplicates = cursor.fetchall()
        
        if duplicates:
            print("\n重複規則:")
            for dup in duplicates:
                print(f"  {dup[0]} 第{dup[1]}口: {dup[2]}次")
        else:
            print("\n✅ 無重複規則")
        
        conn.close()
        
    except Exception as e:
        print(f"錯誤: {e}")

if __name__ == "__main__":
    check_schema()
