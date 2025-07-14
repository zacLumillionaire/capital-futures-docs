#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
檢查新資料庫的索引狀態
確認性能優化索引是否正確創建
"""

import sqlite3
import os

def check_database_indexes():
    """檢查資料庫索引"""
    print("🔍 檢查新資料庫索引狀態...")
    
    db_path = "multi_group_strategy.db"
    
    if not os.path.exists(db_path):
        print(f"❌ 資料庫文件不存在: {db_path}")
        return False
    
    try:
        with sqlite3.connect(db_path) as conn:
            cursor = conn.cursor()
            
            # 檢查所有索引
            print("\n📋 檢查所有索引...")
            cursor.execute("""
                SELECT name, sql FROM sqlite_master 
                WHERE type='index' AND name NOT LIKE 'sqlite_%'
                ORDER BY name
            """)
            
            indexes = cursor.fetchall()
            
            if indexes:
                print(f"✅ 找到 {len(indexes)} 個索引:")
                for idx_name, idx_sql in indexes:
                    print(f"   📌 {idx_name}")
                    if idx_sql:
                        print(f"      SQL: {idx_sql}")
                    else:
                        print(f"      (系統自動創建的索引)")
            else:
                print("❌ 未找到任何索引")
                return False
            
            # 檢查關鍵性能索引
            print("\n🚀 檢查關鍵性能索引...")
            
            expected_indexes = [
                'idx_strategy_groups_date_status',
                'idx_position_records_group_status', 
                'idx_position_records_order_id',
                'idx_position_records_api_seq_no',
                'idx_risk_states_position_update'
            ]
            
            existing_index_names = [idx[0] for idx in indexes]
            
            all_present = True
            for expected_idx in expected_indexes:
                if expected_idx in existing_index_names:
                    print(f"   ✅ {expected_idx}")
                else:
                    print(f"   ❌ 缺少: {expected_idx}")
                    all_present = False
            
            # 檢查表的索引使用情況
            print("\n📊 檢查各表的索引覆蓋...")
            
            tables = ['strategy_groups', 'position_records', 'risk_management_states']
            
            for table in tables:
                cursor.execute(f"PRAGMA index_list({table})")
                table_indexes = cursor.fetchall()
                print(f"   📋 {table}: {len(table_indexes)} 個索引")
                
                for idx_info in table_indexes:
                    idx_name = idx_info[1]
                    is_unique = idx_info[2]
                    unique_str = " (UNIQUE)" if is_unique else ""
                    print(f"      - {idx_name}{unique_str}")
            
            if all_present:
                print(f"\n🎉 所有關鍵索引都已正確創建!")
                return True
            else:
                print(f"\n⚠️ 部分索引缺失，可能影響性能")
                return False
                
    except Exception as e:
        print(f"❌ 檢查索引時出錯: {e}")
        return False

def check_index_performance():
    """檢查索引性能"""
    print("\n⚡ 檢查索引性能...")
    
    try:
        with sqlite3.connect("multi_group_strategy.db") as conn:
            cursor = conn.cursor()
            
            # 測試查詢計劃
            test_queries = [
                "SELECT * FROM strategy_groups WHERE date = '2025-01-14' AND status = 'ACTIVE'",
                "SELECT * FROM position_records WHERE group_id = 1 AND status = 'ACTIVE'", 
                "SELECT * FROM position_records WHERE order_id = 'test123'",
                "SELECT * FROM position_records WHERE api_seq_no = 'seq123'"
            ]
            
            for query in test_queries:
                print(f"\n🔍 查詢: {query[:50]}...")
                cursor.execute(f"EXPLAIN QUERY PLAN {query}")
                plan = cursor.fetchall()
                
                uses_index = any('USING INDEX' in str(step) for step in plan)
                if uses_index:
                    print("   ✅ 使用索引")
                    for step in plan:
                        if 'USING INDEX' in str(step):
                            print(f"      {step}")
                else:
                    print("   ⚠️ 未使用索引 (可能是表掃描)")
                    for step in plan:
                        print(f"      {step}")
        
        return True
        
    except Exception as e:
        print(f"❌ 性能檢查失敗: {e}")
        return False

def main():
    """主檢查函數"""
    print("🚀 資料庫索引完整性檢查")
    print("=" * 50)
    
    # 檢查索引存在性
    indexes_ok = check_database_indexes()
    
    # 檢查索引性能
    performance_ok = check_index_performance()
    
    print(f"\n📊 檢查總結:")
    print(f"   索引完整性: {'✅ 正常' if indexes_ok else '❌ 有問題'}")
    print(f"   索引性能: {'✅ 正常' if performance_ok else '❌ 有問題'}")
    
    if indexes_ok and performance_ok:
        print(f"\n🎉 資料庫索引狀態良好，無需額外操作!")
    else:
        print(f"\n⚠️ 發現索引問題，建議檢查資料庫初始化過程")

if __name__ == "__main__":
    main()
