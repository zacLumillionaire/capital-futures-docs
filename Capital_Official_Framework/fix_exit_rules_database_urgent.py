# -*- coding: utf-8 -*-
"""
緊急修復平倉規則資料庫重複問題
解決 "預設規則數量不正確: 186/3" 錯誤
"""

import sqlite3
import os
from datetime import datetime

def fix_duplicate_exit_rules():
    """修復重複的平倉規則"""
    print("🚨 緊急修復平倉規則資料庫")
    print("=" * 50)
    
    db_path = "multi_group_strategy.db"
    if not os.path.exists(db_path):
        print(f"❌ 資料庫檔案不存在: {db_path}")
        return False
    
    # 備份資料庫
    backup_path = f"{db_path}.backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
    try:
        import shutil
        shutil.copy2(db_path, backup_path)
        print(f"📋 資料庫已備份: {backup_path}")
    except Exception as e:
        print(f"⚠️ 備份失敗: {e}")
    
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # 1. 檢查當前狀況
        print("\n🔍 檢查當前狀況...")
        cursor.execute("SELECT COUNT(*) FROM lot_exit_rules WHERE is_default = 1")
        current_count = cursor.fetchone()[0]
        print(f"📊 當前預設規則數量: {current_count}")
        
        if current_count <= 3:
            print("✅ 規則數量正常，無需修復")
            conn.close()
            return True
        
        # 2. 分析重複規則
        print("\n📋 分析重複規則...")
        cursor.execute('''
            SELECT rule_name, lot_number, COUNT(*) as count,
                   MIN(id) as first_id, MAX(id) as last_id
            FROM lot_exit_rules 
            WHERE is_default = 1
            GROUP BY rule_name, lot_number
            ORDER BY lot_number
        ''')
        
        duplicates = cursor.fetchall()
        total_duplicates = 0
        
        for rule_name, lot_number, count, first_id, last_id in duplicates:
            print(f"  第{lot_number}口: {count}個重複規則 (ID: {first_id}-{last_id})")
            if count > 1:
                total_duplicates += count - 1
        
        print(f"📊 需要刪除的重複規則: {total_duplicates}個")
        
        # 3. 保留每個口數的第一個規則，刪除其餘重複
        print("\n🧹 清理重複規則...")
        
        # 獲取要保留的規則ID（每個口數的最小ID）
        cursor.execute('''
            SELECT MIN(id) as keep_id, lot_number
            FROM lot_exit_rules 
            WHERE is_default = 1
            GROUP BY rule_name, lot_number
            ORDER BY lot_number
        ''')
        
        keep_ids = [row[0] for row in cursor.fetchall()]
        print(f"📋 保留規則ID: {keep_ids}")
        
        # 刪除不需要的重複規則
        if len(keep_ids) > 0:
            placeholders = ','.join(['?'] * len(keep_ids))
            delete_query = f'''
                DELETE FROM lot_exit_rules 
                WHERE is_default = 1 AND id NOT IN ({placeholders})
            '''
            
            cursor.execute(delete_query, keep_ids)
            deleted_count = cursor.rowcount
            print(f"🗑️ 已刪除 {deleted_count} 個重複規則")
        
        # 4. 驗證修復結果
        print("\n✅ 驗證修復結果...")
        cursor.execute("SELECT COUNT(*) FROM lot_exit_rules WHERE is_default = 1")
        final_count = cursor.fetchone()[0]
        print(f"📊 修復後預設規則數量: {final_count}")
        
        # 顯示保留的規則
        cursor.execute('''
            SELECT id, rule_name, lot_number, trailing_activation_points, 
                   protective_stop_multiplier, description
            FROM lot_exit_rules 
            WHERE is_default = 1
            ORDER BY lot_number
        ''')
        
        final_rules = cursor.fetchall()
        print("\n📋 保留的規則:")
        for rule in final_rules:
            protection = rule[4] if rule[4] is not None else "無"
            print(f"  ID={rule[0]}: 第{rule[2]}口 {rule[3]}點啟動 "
                  f"保護倍數={protection} - {rule[5]}")
        
        # 5. 如果規則不足，補充預設規則
        if final_count < 3:
            print(f"\n🔧 規則不足，補充預設規則...")
            
            # 檢查缺少哪些口數
            cursor.execute('''
                SELECT lot_number FROM lot_exit_rules 
                WHERE is_default = 1
                ORDER BY lot_number
            ''')
            existing_lots = [row[0] for row in cursor.fetchall()]
            
            # 預設規則定義
            default_rules = [
                ('回測標準規則', 1, 15, 0.20, None, '第1口: 15點啟動移動停利'),
                ('回測標準規則', 2, 40, 0.20, 2.0, '第2口: 40點啟動移動停利, 2倍保護'),
                ('回測標準規則', 3, 65, 0.20, 2.0, '第3口: 65點啟動移動停利, 2倍保護')
            ]
            
            for rule_data in default_rules:
                lot_number = rule_data[1]
                if lot_number not in existing_lots:
                    cursor.execute('''
                        INSERT INTO lot_exit_rules
                        (rule_name, lot_number, trailing_activation_points, trailing_pullback_ratio,
                         protective_stop_multiplier, description, is_default)
                        VALUES (?, ?, ?, ?, ?, ?, 1)
                    ''', rule_data)
                    print(f"  ➕ 補充第{lot_number}口規則")
        
        # 6. 最終驗證
        cursor.execute("SELECT COUNT(*) FROM lot_exit_rules WHERE is_default = 1")
        final_final_count = cursor.fetchone()[0]
        
        conn.commit()
        conn.close()
        
        print(f"\n🎉 修復完成！")
        print(f"📊 最終預設規則數量: {final_final_count}")
        
        if final_final_count == 3:
            print("✅ 規則數量正確")
            print("✅ 下次啟動應該不會再出現錯誤")
            return True
        else:
            print(f"⚠️ 規則數量仍不正確: {final_final_count}/3")
            return False
            
    except Exception as e:
        print(f"❌ 修復失敗: {e}")
        if 'conn' in locals():
            conn.rollback()
            conn.close()
        return False

def verify_fix():
    """驗證修復效果"""
    print("\n🧪 驗證修復效果")
    print("-" * 30)
    
    try:
        # 模擬系統驗證邏輯
        conn = sqlite3.connect("multi_group_strategy.db")
        cursor = conn.cursor()
        
        # 檢查預設規則數量
        cursor.execute("SELECT COUNT(*) FROM lot_exit_rules WHERE is_default = 1")
        count = cursor.fetchone()[0]
        
        if count == 3:
            print("✅ 驗證通過：預設規則數量正確")
            print("✅ 系統啟動時不會再出現錯誤")
            return True
        else:
            print(f"❌ 驗證失敗：規則數量 {count}/3")
            return False
            
    except Exception as e:
        print(f"❌ 驗證過程失敗: {e}")
        return False
    finally:
        if 'conn' in locals():
            conn.close()

if __name__ == "__main__":
    print("🚨 緊急修復平倉規則資料庫重複問題")
    print("解決 '預設規則數量不正確: 186/3' 錯誤")
    print("=" * 60)
    
    # 執行修復
    success = fix_duplicate_exit_rules()
    
    if success:
        # 驗證修復效果
        verify_success = verify_fix()
        
        if verify_success:
            print("\n🎉 修復完全成功！")
            print("\n📋 下次啟動時應該看到：")
            print("  ✅ [EXIT_DB] ✅ 預設規則數量正確: 3/3")
            print("  ✅ [EXIT_DB] ✅ 資料庫擴展驗證通過")
            print("  ✅ 不再出現 sqlite3.Row 相關錯誤")
        else:
            print("\n⚠️ 修復部分成功，但驗證未通過")
    else:
        print("\n❌ 修復失敗")
        print("💡 建議手動檢查資料庫或重新創建表格")
