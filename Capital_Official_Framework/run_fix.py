#!/usr/bin/env python3
import sqlite3
import shutil
from datetime import datetime

def main():
    db_path = 'multi_group_strategy.db'
    
    # 備份
    backup_path = f'{db_path}.backup_{datetime.now().strftime("%Y%m%d_%H%M%S")}'
    shutil.copy2(db_path, backup_path)
    print(f'備份完成: {backup_path}')
    
    # 執行修復
    with sqlite3.connect(db_path) as conn:
        with open('fix_database_constraints.sql', 'r', encoding='utf-8') as f:
            sql_script = f.read()
        
        # 分割並執行每個語句
        statements = [s.strip() for s in sql_script.split(';') if s.strip() and not s.strip().startswith('--')]
        
        for stmt in statements:
            try:
                conn.execute(stmt)
                print(f'執行成功: {stmt[:50]}...')
            except Exception as e:
                print(f'執行失敗: {stmt[:50]}... 錯誤: {e}')
        
        conn.commit()
    
    print('修復完成!')

if __name__ == '__main__':
    main()
