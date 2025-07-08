#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
修復平倉機制資料庫的重複規則問題
"""

import sqlite3
import shutil
from datetime import datetime

def main():
    print('🔧 修復平倉機制資料庫重複規則')
    print('=' * 50)
    
    # 備份資料庫
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    backup_name = f'multi_group_strategy.db.backup_exit_fix_{timestamp}'
    shutil.copy2('multi_group_strategy.db', backup_name)
    print(f'✅ 資料庫已備份: {backup_name}')
    
    conn = sqlite3.connect('multi_group_strategy.db')
    cursor = conn.cursor()
    
    try:
        # 檢查當前狀況
        cursor.execute("SELECT COUNT(*) FROM lot_exit_rules WHERE is_default = 1")
        current_count = cursor.fetchone()[0]
        print(f'📊 當前預設規則數量: {current_count}')
        
        if current_count <= 3:
            print('✅ 規則數量正常，無需修復')
            return True
        
        # 顯示重複規則
        print('\n📋 重複規則分析:')
        cursor.execute('''
            SELECT rule_name, lot_number, COUNT(*) as count
            FROM lot_exit_rules 
            WHERE is_default = 1
            GROUP BY rule_name, lot_number
            ORDER BY lot_number
        ''')
        
        duplicates = cursor.fetchall()
        for rule_name, lot_number, count in duplicates:
            print(f'  第{lot_number}口: {count}個重複規則')
        
        # 清理重複規則，只保留每個lot_number的第一個
        print('\n🧹 開始清理重複規則...')
        
        # 找出要保留的規則ID (每個lot_number的最小ID)
        cursor.execute('''
            SELECT lot_number, MIN(id) as keep_id
            FROM lot_exit_rules 
            WHERE is_default = 1
            GROUP BY lot_number
            ORDER BY lot_number
        ''')
        
        keep_rules = cursor.fetchall()
        keep_ids = [str(rule[1]) for rule in keep_rules]
        
        print(f'📝 保留規則ID: {keep_ids}')
        
        # 刪除重複規則
        if keep_ids:
            placeholders = ','.join(['?' for _ in keep_ids])
            cursor.execute(f'''
                DELETE FROM lot_exit_rules 
                WHERE is_default = 1 
                AND id NOT IN ({placeholders})
            ''', keep_ids)
            
            deleted_count = cursor.rowcount
            print(f'🗑️ 已刪除 {deleted_count} 個重複規則')
        
        # 驗證修復結果
        cursor.execute("SELECT COUNT(*) FROM lot_exit_rules WHERE is_default = 1")
        final_count = cursor.fetchone()[0]
        print(f'✅ 修復後預設規則數量: {final_count}')
        
        # 顯示保留的規則
        print('\n📋 保留的規則:')
        cursor.execute('''
            SELECT id, rule_name, lot_number, trailing_activation_points, 
                   protective_stop_multiplier, description
            FROM lot_exit_rules 
            WHERE is_default = 1
            ORDER BY lot_number
        ''')
        
        final_rules = cursor.fetchall()
        for rule in final_rules:
            print(f'  ID={rule[0]}: 第{rule[2]}口 {rule[3]}點啟動 '
                  f'保護倍數={rule[4]} - {rule[5]}')
        
        conn.commit()
        
        if final_count == 3:
            print('\n🎉 修復成功！預設規則數量已正確')
            return True
        else:
            print(f'\n⚠️ 修復後規則數量仍不正確: {final_count}/3')
            return False
            
    except Exception as e:
        print(f'❌ 修復失敗: {e}')
        conn.rollback()
        return False
    finally:
        conn.close()

def verify_exit_mechanism():
    """驗證平倉機制是否正常"""
    print('\n🧪 驗證平倉機制')
    print('=' * 30)
    
    try:
        import sys
        import os
        sys.path.append(os.path.join(os.path.dirname(__file__), 'Capital_Official_Framework'))
        
        from exit_mechanism_database_extension import ExitMechanismDatabaseExtension
        
        # 測試資料庫擴展
        extension = ExitMechanismDatabaseExtension("multi_group_strategy.db")
        
        # 驗證擴展
        if extension.verify_extension():
            print('✅ 平倉機制資料庫擴展驗證成功')
            return True
        else:
            print('❌ 平倉機制資料庫擴展驗證失敗')
            return False
            
    except Exception as e:
        print(f'❌ 驗證失敗: {e}')
        return False

if __name__ == "__main__":
    print('🚀 開始修復平倉機制資料庫')
    print('=' * 80)
    
    # 修復重複規則
    fix_success = main()
    
    if fix_success:
        # 驗證平倉機制
        verify_success = verify_exit_mechanism()
        
        print('\n📋 修復總結')
        print('=' * 80)
        
        if verify_success:
            print('🎉 修復完成！')
            print('✅ 重複規則已清理')
            print('✅ 平倉機制資料庫擴展正常')
            print('✅ 出場點位監控功能可以正常運作')
            print('\n📝 建議:')
            print('1. 重新啟動策略機')
            print('2. 觀察是否還有擴展失敗訊息')
            print('3. 測試出場點位監控功能')
        else:
            print('⚠️ 修復部分成功')
            print('✅ 重複規則已清理')
            print('❌ 平倉機制驗證失敗')
            print('💡 可能需要進一步檢查平倉機制配置')
    else:
        print('\n❌ 修復失敗')
        print('💡 建議檢查資料庫文件和權限')
