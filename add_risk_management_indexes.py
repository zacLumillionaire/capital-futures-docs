#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
🚀 添加 risk_management_states 表索引
為優化查詢提供支援
"""

import sqlite3
import time

def add_risk_management_indexes(db_path="multi_group_strategy.db"):
    """添加 risk_management_states 表索引"""
    
    new_indexes = [
        {
            'name': 'idx_risk_management_states_position_id',
            'sql': 'CREATE INDEX IF NOT EXISTS idx_risk_management_states_position_id ON risk_management_states(position_id)',
            'purpose': '優化 LEFT JOIN 查詢 (position_id)'
        },
        {
            'name': 'idx_risk_management_states_position_protection',
            'sql': 'CREATE INDEX IF NOT EXISTS idx_risk_management_states_position_protection ON risk_management_states(position_id, protection_activated)',
            'purpose': '優化保護性停損查詢 (position_id + protection_activated)'
        }
    ]
    
    try:
        print("🚀 添加 risk_management_states 表索引...")
        print(f"📁 資料庫路徑: {db_path}")
        
        with sqlite3.connect(db_path) as conn:
            cursor = conn.cursor()
            
            # 檢查 risk_management_states 表是否存在
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='risk_management_states'")
            table_exists = cursor.fetchone()
            
            if not table_exists:
                print("⚠️ risk_management_states 表不存在，跳過索引創建")
                return False
            
            success_count = 0
            for index in new_indexes:
                try:
                    start_time = time.time()
                    cursor.execute(index['sql'])
                    elapsed = (time.time() - start_time) * 1000
                    print(f"  ✅ {index['name']}: 創建成功 ({elapsed:.1f}ms)")
                    print(f"     用途: {index['purpose']}")
                    success_count += 1
                    
                except Exception as e:
                    print(f"  ❌ {index['name']}: 創建失敗 - {e}")
            
            conn.commit()
            
            print(f"\n📊 新索引添加結果:")
            print(f"  成功: {success_count}/{len(new_indexes)}")
            
            return success_count == len(new_indexes)
            
    except Exception as e:
        print(f"❌ 添加索引失敗: {e}")
        return False

def test_optimized_query_performance(db_path="multi_group_strategy.db"):
    """測試優化查詢性能"""
    
    test_queries = [
        {
            'name': '優化平倉查詢',
            'sql': '''
                SELECT 
                    pr.*,
                    r.current_stop_loss,
                    r.protection_activated,
                    r.trailing_activated,
                    r.peak_price
                FROM position_records pr
                LEFT JOIN risk_management_states r ON pr.id = r.position_id
                WHERE pr.id = ? AND pr.status = 'ACTIVE'
            ''',
            'params': (133,)
        },
        {
            'name': '批量部位查詢',
            'sql': '''
                SELECT 
                    pr.*,
                    r.current_stop_loss,
                    r.protection_activated
                FROM position_records pr
                LEFT JOIN risk_management_states r ON pr.id = r.position_id
                WHERE pr.id IN (133, 134, 135) AND pr.status = 'ACTIVE'
            ''',
            'params': ()
        }
    ]
    
    try:
        print("\n🧪 測試優化查詢性能...")
        
        with sqlite3.connect(db_path) as conn:
            cursor = conn.cursor()
            
            for query in test_queries:
                try:
                    start_time = time.time()
                    cursor.execute(query['sql'], query['params'])
                    results = cursor.fetchall()
                    elapsed = (time.time() - start_time) * 1000
                    
                    print(f"  📊 {query['name']}: {elapsed:.1f}ms ({len(results)}筆結果)")
                    
                    if elapsed < 10:
                        print(f"    ✅ 性能優秀 (目標達成)")
                    elif elapsed < 30:
                        print(f"    ✅ 性能良好")
                    elif elapsed < 50:
                        print(f"    ⚠️ 性能可接受")
                    else:
                        print(f"    ❌ 性能需要改善")
                        
                except Exception as e:
                    print(f"  ❌ {query['name']}: 查詢失敗 - {e}")
                    
    except Exception as e:
        print(f"❌ 性能測試失敗: {e}")

def main():
    """主函數"""
    print("🚀 risk_management_states 表索引優化")
    print("="*50)
    
    # 添加新索引
    success = add_risk_management_indexes()
    
    if success:
        print("\n✅ 新索引添加完成")
        
        # 測試優化查詢性能
        test_optimized_query_performance()
        
        print("\n💡 索引狀態總結:")
        print("✅ position_records 索引：已優化（適用於新查詢）")
        print("✅ risk_management_states 索引：已添加")
        print("⚠️ strategy_groups 索引：保留（不影響性能）")
        
    else:
        print("\n❌ 新索引添加失敗")

if __name__ == "__main__":
    main()
