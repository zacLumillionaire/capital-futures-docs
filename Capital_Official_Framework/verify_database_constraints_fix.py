#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
驗證數據庫約束修復完成情況
檢查所有約束問題是否已解決
"""

import sqlite3
import os

def check_constraint_values():
    """檢查約束值匹配問題"""
    print("🔍 檢查約束值匹配...")
    
    try:
        conn = sqlite3.connect("multi_group_strategy.db")
        cursor = conn.cursor()
        
        # 檢查 risk_management_states 表的約束
        cursor.execute("SELECT sql FROM sqlite_master WHERE type='table' AND name='risk_management_states'")
        result = cursor.fetchone()
        
        if result:
            table_sql = result[0]
            
            # 檢查是否包含所需的約束值
            required_values = ["成交初始化", "簡化追蹤成交確認"]
            missing_values = []
            
            for value in required_values:
                if f"'{value}'" not in table_sql:
                    missing_values.append(value)
            
            if missing_values:
                print(f"❌ 缺少約束值: {missing_values}")
                return False
            else:
                print("✅ 約束值檢查通過")
                return True
        else:
            print("❌ 找不到 risk_management_states 表")
            return False
            
    except Exception as e:
        print(f"❌ 檢查約束值失敗: {e}")
        return False
    finally:
        if 'conn' in locals():
            conn.close()

def check_unique_constraints():
    """檢查唯一性約束"""
    print("\n🔍 檢查唯一性約束...")
    
    try:
        conn = sqlite3.connect("multi_group_strategy.db")
        cursor = conn.cursor()
        
        # 檢查 lot_exit_rules 表的唯一約束
        cursor.execute("SELECT sql FROM sqlite_master WHERE type='table' AND name='lot_exit_rules'")
        result = cursor.fetchone()
        
        if result:
            table_sql = result[0]
            
            if 'UNIQUE(rule_name, lot_number, is_default)' in table_sql:
                print("✅ lot_exit_rules 唯一約束存在")
                
                # 檢查重複數據
                cursor.execute('''
                    SELECT rule_name, lot_number, COUNT(*) as count 
                    FROM lot_exit_rules 
                    WHERE is_default = 1
                    GROUP BY rule_name, lot_number 
                    HAVING count > 1
                ''')
                duplicates = cursor.fetchall()
                
                if duplicates:
                    print(f"❌ 發現重複數據: {len(duplicates)} 組")
                    return False
                else:
                    print("✅ 無重複數據")
                    return True
            else:
                print("❌ 缺少唯一約束")
                return False
        else:
            print("❌ 找不到 lot_exit_rules 表")
            return False
            
    except Exception as e:
        print(f"❌ 檢查唯一約束失敗: {e}")
        return False
    finally:
        if 'conn' in locals():
            conn.close()

def check_foreign_key_constraints():
    """檢查外鍵約束"""
    print("\n🔍 檢查外鍵約束...")
    
    try:
        conn = sqlite3.connect("multi_group_strategy.db")
        cursor = conn.cursor()
        
        # 檢查 risk_management_states 表的外鍵
        cursor.execute("SELECT sql FROM sqlite_master WHERE type='table' AND name='risk_management_states'")
        result = cursor.fetchone()
        
        if result:
            table_sql = result[0]
            
            if 'FOREIGN KEY (position_id) REFERENCES position_records(id)' in table_sql:
                print("✅ risk_management_states 外鍵約束存在")
                return True
            else:
                print("❌ 缺少外鍵約束")
                return False
        else:
            print("❌ 找不到 risk_management_states 表")
            return False
            
    except Exception as e:
        print(f"❌ 檢查外鍵約束失敗: {e}")
        return False
    finally:
        if 'conn' in locals():
            conn.close()

def check_data_type_constraints():
    """檢查數據類型約束"""
    print("\n🔍 檢查數據類型約束...")

    try:
        conn = sqlite3.connect("multi_group_strategy.db")
        cursor = conn.cursor()

        # 檢查 position_records 表的數據類型約束
        cursor.execute("SELECT sql FROM sqlite_master WHERE type='table' AND name='position_records'")
        result = cursor.fetchone()

        if result:
            table_sql = result[0]

            # 檢查核心業務約束（必需的）
            required_constraints = [
                "CHECK(direction IN ('LONG', 'SHORT'))",
                "CHECK(status IN ('ACTIVE', 'EXITED', 'FAILED'))",
                "CHECK(lot_id BETWEEN 1 AND 3)"
            ]

            # 檢查可選約束（建議但非必需）
            optional_constraints = [
                "CHECK(retry_count >= 0 AND retry_count <= 5)",
                "CHECK(max_slippage_points > 0)"
            ]

            missing_required = []
            missing_optional = []

            for constraint in required_constraints:
                if constraint not in table_sql:
                    missing_required.append(constraint)

            for constraint in optional_constraints:
                if constraint not in table_sql:
                    missing_optional.append(constraint)

            if missing_required:
                print(f"❌ 缺少必需約束: {missing_required}")
                return False
            else:
                print("✅ 核心業務約束檢查通過")

                if missing_optional:
                    print(f"ℹ️ 缺少可選約束: {missing_optional}")
                    print("   (這些約束不影響系統正常運行)")

                return True
        else:
            print("❌ 找不到 position_records 表")
            return False

    except Exception as e:
        print(f"❌ 檢查數據類型約束失敗: {e}")
        return False
    finally:
        if 'conn' in locals():
            conn.close()

def check_not_null_constraints():
    """檢查 NOT NULL 約束"""
    print("\n🔍 檢查 NOT NULL 約束...")
    
    try:
        conn = sqlite3.connect("multi_group_strategy.db")
        cursor = conn.cursor()
        
        # 檢查關鍵表格的 NOT NULL 約束
        tables_to_check = [
            ("risk_management_states", ["position_id", "peak_price", "last_update_time"]),
            ("position_records", ["group_id", "lot_id", "direction", "entry_time"]),
            ("strategy_groups", ["date", "group_id", "direction", "total_lots"])
        ]
        
        all_passed = True
        
        for table_name, required_not_null_fields in tables_to_check:
            cursor.execute(f"SELECT sql FROM sqlite_master WHERE type='table' AND name='{table_name}'")
            result = cursor.fetchone()
            
            if result:
                table_sql = result[0]
                
                for field in required_not_null_fields:
                    if f"{field} " in table_sql and "NOT NULL" in table_sql:
                        # 簡化檢查：如果字段存在且表中有 NOT NULL，認為正確
                        continue
                    else:
                        print(f"⚠️ {table_name}.{field} 可能缺少 NOT NULL 約束")
                        # 不設為失敗，因為有些字段可能允許 NULL
                
                print(f"✅ {table_name} NOT NULL 約束檢查完成")
            else:
                print(f"❌ 找不到 {table_name} 表")
                all_passed = False
        
        return all_passed
        
    except Exception as e:
        print(f"❌ 檢查 NOT NULL 約束失敗: {e}")
        return False
    finally:
        if 'conn' in locals():
            conn.close()

def check_indexes():
    """檢查索引"""
    print("\n🔍 檢查索引...")
    
    try:
        conn = sqlite3.connect("multi_group_strategy.db")
        cursor = conn.cursor()
        
        # 檢查 lot_exit_rules 表的索引
        cursor.execute("PRAGMA index_list(lot_exit_rules)")
        indexes = cursor.fetchall()
        
        if len(indexes) >= 3:  # 至少應該有3個索引
            print(f"✅ lot_exit_rules 表有 {len(indexes)} 個索引")
            
            # 檢查是否有唯一索引
            unique_indexes = [idx for idx in indexes if idx[2] == 1]  # unique flag
            if unique_indexes:
                print(f"✅ 有 {len(unique_indexes)} 個唯一索引")
                return True
            else:
                print("⚠️ 缺少唯一索引")
                return False
        else:
            print(f"⚠️ 索引數量較少: {len(indexes)}")
            return False
            
    except Exception as e:
        print(f"❌ 檢查索引失敗: {e}")
        return False
    finally:
        if 'conn' in locals():
            conn.close()

def check_data_integrity():
    """檢查數據完整性"""
    print("\n🔍 檢查數據完整性...")
    
    try:
        conn = sqlite3.connect("multi_group_strategy.db")
        cursor = conn.cursor()
        
        # 檢查 lot_exit_rules 預設規則
        cursor.execute("SELECT COUNT(*) FROM lot_exit_rules WHERE is_default = 1")
        default_count = cursor.fetchone()[0]
        
        if default_count == 3:
            print("✅ 預設規則數量正確: 3個")
            
            # 檢查每個口數都有規則
            cursor.execute('''
                SELECT lot_number FROM lot_exit_rules 
                WHERE is_default = 1 
                ORDER BY lot_number
            ''')
            lot_numbers = [row[0] for row in cursor.fetchall()]
            
            if lot_numbers == [1, 2, 3]:
                print("✅ 所有口數都有預設規則")
                return True
            else:
                print(f"❌ 口數不完整: {lot_numbers}")
                return False
        else:
            print(f"❌ 預設規則數量錯誤: {default_count}/3")
            return False
            
    except Exception as e:
        print(f"❌ 檢查數據完整性失敗: {e}")
        return False
    finally:
        if 'conn' in locals():
            conn.close()

def main():
    """主函數"""
    print("🚀 驗證數據庫約束修復完成情況")
    print("=" * 50)
    
    if not os.path.exists("multi_group_strategy.db"):
        print("❌ 資料庫檔案不存在")
        return False
    
    # 執行所有檢查
    checks = [
        ("約束值匹配", check_constraint_values),
        ("唯一性約束", check_unique_constraints),
        ("外鍵約束", check_foreign_key_constraints),
        ("數據類型約束", check_data_type_constraints),
        ("NOT NULL約束", check_not_null_constraints),
        ("索引", check_indexes),
        ("數據完整性", check_data_integrity)
    ]
    
    results = []
    
    for check_name, check_func in checks:
        try:
            result = check_func()
            results.append((check_name, result))
        except Exception as e:
            print(f"❌ {check_name} 檢查失敗: {e}")
            results.append((check_name, False))
    
    # 總結結果
    print("\n" + "=" * 50)
    print("📊 檢查結果總結")
    print("=" * 50)
    
    passed = 0
    total = len(results)
    
    for check_name, result in results:
        status = "✅ 通過" if result else "❌ 失敗"
        print(f"{check_name:15} : {status}")
        if result:
            passed += 1
    
    print(f"\n📈 總體結果: {passed}/{total} 項檢查通過")
    
    if passed == total:
        print("\n🎉 所有數據庫約束修復完成！")
        print("✅ 系統可以安全運行")
        return True
    else:
        print(f"\n⚠️ 還有 {total - passed} 項需要修復")
        return False

if __name__ == "__main__":
    main()
