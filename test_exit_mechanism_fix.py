#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
測試平倉機制修復
"""

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), 'Capital_Official_Framework'))

def test_exit_mechanism_verification():
    """測試平倉機制驗證"""
    print('🧪 測試平倉機制驗證修復')
    print('=' * 50)
    
    try:
        from multi_group_database import MultiGroupDatabaseManager
        from exit_mechanism_database_extension import ExitMechanismDatabaseExtension
        
        # 使用實際資料庫
        db_manager = MultiGroupDatabaseManager("multi_group_strategy.db")
        print("✅ 連接到資料庫")
        
        # 創建平倉機制擴展
        extension = ExitMechanismDatabaseExtension(db_manager)
        print("✅ 創建平倉機制擴展")
        
        # 測試驗證功能
        print("\n🔍 執行驗證...")
        verification_result = extension.verify_extension()
        
        if verification_result:
            print("🎉 驗證成功！")
            print("✅ 平倉機制資料庫擴展正常")
            print("✅ 預設規則數量正確")
            print("✅ 所有必要表格和欄位存在")
            return True
        else:
            print("❌ 驗證失敗")
            print("💡 可能仍有其他問題需要解決")
            return False
            
    except Exception as e:
        print(f"❌ 測試失敗: {e}")
        import traceback
        print(traceback.format_exc())
        return False

def test_database_queries():
    """測試資料庫查詢"""
    print('\n🔍 測試資料庫查詢')
    print('=' * 30)
    
    try:
        import sqlite3
        
        conn = sqlite3.connect('multi_group_strategy.db')
        cursor = conn.cursor()
        
        # 測試修復後的查詢
        print("測試1: 使用 is_default = 1")
        cursor.execute("SELECT COUNT(*) FROM lot_exit_rules WHERE is_default = 1")
        count1 = cursor.fetchone()[0]
        print(f"  結果: {count1} 個規則")
        
        print("測試2: 使用 is_default = TRUE")
        cursor.execute("SELECT COUNT(*) FROM lot_exit_rules WHERE is_default = TRUE")
        count2 = cursor.fetchone()[0]
        print(f"  結果: {count2} 個規則")
        
        print("測試3: 使用 is_default = 'true'")
        cursor.execute("SELECT COUNT(*) FROM lot_exit_rules WHERE is_default = 'true'")
        count3 = cursor.fetchone()[0]
        print(f"  結果: {count3} 個規則")
        
        # 檢查實際存儲的值
        print("\n📊 檢查實際存儲的 is_default 值:")
        cursor.execute("SELECT DISTINCT is_default FROM lot_exit_rules")
        values = cursor.fetchall()
        for value in values:
            print(f"  值: {value[0]} (類型: {type(value[0])})")
        
        conn.close()
        
        if count1 == 3:
            print("\n✅ 查詢修復成功")
            return True
        else:
            print(f"\n❌ 查詢結果不正確: {count1}/3")
            return False
            
    except Exception as e:
        print(f"❌ 資料庫查詢測試失敗: {e}")
        return False

if __name__ == "__main__":
    print('🚀 開始測試平倉機制修復')
    print('=' * 80)
    
    # 測試1: 資料庫查詢
    query_success = test_database_queries()
    
    # 測試2: 平倉機制驗證
    verification_success = test_exit_mechanism_verification()
    
    print('\n📋 測試總結')
    print('=' * 80)
    
    if query_success and verification_success:
        print('🎉 修復完全成功！')
        print('✅ 資料庫查詢正常')
        print('✅ 平倉機制驗證通過')
        print('✅ 不再會出現「預設規則數量不正確」錯誤')
        print('\n📝 建議:')
        print('1. 重新啟動策略機')
        print('2. 確認LOG中顯示「資料庫擴展成功」')
        print('3. 出場點位監控功能完全正常')
    else:
        print('⚠️ 修復部分成功')
        if not query_success:
            print('❌ 資料庫查詢仍有問題')
        if not verification_success:
            print('❌ 平倉機制驗證仍失敗')
        print('💡 可能需要進一步檢查')
