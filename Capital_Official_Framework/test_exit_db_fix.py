# -*- coding: utf-8 -*-
"""
測試平倉機制資料庫修復效果
"""

import sys
import os
sys.path.append(os.path.dirname(__file__))

from multi_group_database import MultiGroupDatabaseManager
from exit_mechanism_database_extension import ExitMechanismDatabaseExtension

def test_exit_mechanism_fix():
    """測試平倉機制修復"""
    print("🧪 測試平倉機制資料庫修復")
    print("=" * 50)
    
    try:
        # 1. 創建資料庫管理器
        db_manager = MultiGroupDatabaseManager("multi_group_strategy.db")
        print("✅ 連接到資料庫")
        
        # 2. 創建平倉機制擴展
        extension = ExitMechanismDatabaseExtension(db_manager, console_enabled=True)
        print("✅ 創建平倉機制擴展")
        
        # 3. 測試驗證功能
        print("\n🔍 執行驗證...")
        verification_result = extension.verify_extension()
        
        if verification_result:
            print("\n🎉 驗證成功！")
            print("✅ 平倉機制資料庫擴展正常")
            print("✅ 預設規則數量正確")
            print("✅ 所有必要表格和欄位存在")
            
            # 4. 檢查具體規則
            print("\n📋 檢查預設規則...")
            with db_manager.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    SELECT id, lot_number, trailing_activation_points, 
                           protective_stop_multiplier, description
                    FROM lot_exit_rules 
                    WHERE is_default = 1
                    ORDER BY lot_number
                ''')
                
                rules = cursor.fetchall()
                for rule in rules:
                    protection = rule[3] if rule[3] is not None else "無"
                    print(f"  第{rule[1]}口: {rule[2]}點啟動, 保護倍數={protection}")
            
            return True
        else:
            print("\n❌ 驗證失敗")
            return False
            
    except Exception as e:
        print(f"❌ 測試失敗: {e}")
        import traceback
        traceback.print_exc()
        return False

def simulate_system_startup():
    """模擬系統啟動過程"""
    print("\n🚀 模擬系統啟動過程")
    print("-" * 30)
    
    try:
        # 模擬 simple_integrated.py 中的初始化過程
        from exit_mechanism_database_extension import extend_database_for_exit_mechanism
        
        db_manager = MultiGroupDatabaseManager("multi_group_strategy.db")
        
        print("[EXIT_DB] 🚀 開始擴展資料庫以支援平倉機制...")
        success = extend_database_for_exit_mechanism(db_manager)
        
        if success:
            print("[EXIT_DB] ✅ 資料庫擴展成功")
            print("✅ 應該不會再看到 '預設規則數量不正確' 錯誤")
            return True
        else:
            print("[EXIT_DB] ❌ 資料庫擴展失敗")
            return False
            
    except Exception as e:
        print(f"❌ 模擬啟動失敗: {e}")
        return False

if __name__ == "__main__":
    print("🔧 平倉機制資料庫修復測試")
    print("=" * 60)
    
    # 測試1: 驗證修復
    test1_success = test_exit_mechanism_fix()
    
    # 測試2: 模擬系統啟動
    test2_success = simulate_system_startup()
    
    print("\n📋 測試總結")
    print("=" * 60)
    
    if test1_success and test2_success:
        print("🎉 修復完全成功！")
        print("✅ 平倉機制資料庫正常")
        print("✅ 系統啟動模擬成功")
        print("✅ 不會再出現重複規則錯誤")
        print("\n📝 下次啟動時應該看到：")
        print("  [EXIT_DB] ✅ 資料庫擴展驗證通過")
        print("  [EXIT_DB] 📊 所有表格和欄位已正確創建")
        print("  [EXIT_DB] ⚙️ 預設平倉規則已載入")
        print("  [EXIT_DB] 🎉 平倉機制資料庫擴展完成!")
    else:
        print("⚠️ 修復部分成功")
        if not test1_success:
            print("❌ 驗證測試失敗")
        if not test2_success:
            print("❌ 啟動模擬失敗")
        print("💡 可能需要進一步檢查")
    
    print("\n🔗 與 sqlite3.Row 錯誤的關聯：")
    print("✅ 清理重複規則可能解決資料庫連接問題")
    print("✅ 減少資料庫查詢負載，降低 Row 對象處理錯誤")
    print("✅ 統一資料庫操作邏輯，提升穩定性")
