#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
🚀 立即執行：添加資料庫索引
安全地為資料庫添加索引，提升查詢性能
"""

import sqlite3
import time

def add_database_indexes(db_path="multi_group_strategy.db"):
    """添加資料庫索引"""
    
    indexes = [
        # position_records 表索引
        {
            'name': 'idx_position_records_id_status',
            'sql': 'CREATE INDEX IF NOT EXISTS idx_position_records_id_status ON position_records(id, status)',
            'purpose': '優化平倉查詢 (id + status)'
        },
        {
            'name': 'idx_position_records_group_status',
            'sql': 'CREATE INDEX IF NOT EXISTS idx_position_records_group_status ON position_records(group_id, status)',
            'purpose': '優化組別查詢 (group_id + status)'
        },
        {
            'name': 'idx_position_records_group_lot',
            'sql': 'CREATE INDEX IF NOT EXISTS idx_position_records_group_lot ON position_records(group_id, lot_id)',
            'purpose': '優化排序查詢 (group_id + lot_id)'
        },
        
        # strategy_groups 表索引
        {
            'name': 'idx_strategy_groups_group_date',
            'sql': 'CREATE INDEX IF NOT EXISTS idx_strategy_groups_group_date ON strategy_groups(group_id, date)',
            'purpose': '優化JOIN查詢 (group_id + date)'
        },
        {
            'name': 'idx_strategy_groups_date_id',
            'sql': 'CREATE INDEX IF NOT EXISTS idx_strategy_groups_date_id ON strategy_groups(date, id DESC)',
            'purpose': '優化日期排序查詢 (date + id DESC)'
        },
        
        # 複合索引
        {
            'name': 'idx_position_records_complete',
            'sql': 'CREATE INDEX IF NOT EXISTS idx_position_records_complete ON position_records(id, status, group_id)',
            'purpose': '優化完整查詢 (id + status + group_id)'
        }
    ]
    
    try:
        print("🚀 開始添加資料庫索引...")
        print(f"📁 資料庫路徑: {db_path}")
        
        with sqlite3.connect(db_path) as conn:
            cursor = conn.cursor()
            
            # 檢查現有索引
            cursor.execute("SELECT name FROM sqlite_master WHERE type='index'")
            existing_indexes = {row[0] for row in cursor.fetchall()}
            print(f"📊 現有索引數量: {len(existing_indexes)}")
            
            success_count = 0
            for index in indexes:
                try:
                    start_time = time.time()
                    
                    if index['name'] in existing_indexes:
                        print(f"  ✅ {index['name']}: 已存在")
                        success_count += 1
                    else:
                        cursor.execute(index['sql'])
                        elapsed = (time.time() - start_time) * 1000
                        print(f"  ✅ {index['name']}: 創建成功 ({elapsed:.1f}ms)")
                        print(f"     用途: {index['purpose']}")
                        success_count += 1
                        
                except Exception as e:
                    print(f"  ❌ {index['name']}: 創建失敗 - {e}")
            
            # 提交變更
            conn.commit()
            
            print(f"\n📊 索引添加結果:")
            print(f"  成功: {success_count}/{len(indexes)}")
            print(f"  失敗: {len(indexes) - success_count}/{len(indexes)}")
            
            # 驗證索引
            cursor.execute("SELECT name FROM sqlite_master WHERE type='index' AND name LIKE 'idx_%'")
            new_indexes = cursor.fetchall()
            print(f"  自定義索引總數: {len(new_indexes)}")
            
            return success_count == len(indexes)
            
    except Exception as e:
        print(f"❌ 添加索引失敗: {e}")
        return False

def test_query_performance(db_path="multi_group_strategy.db"):
    """測試查詢性能改善"""
    
    test_queries = [
        {
            'name': '平倉查詢',
            'sql': '''
                SELECT pr.*, sg.range_high, sg.range_low, sg.direction as group_direction
                FROM position_records pr
                JOIN (
                    SELECT * FROM strategy_groups
                    WHERE date = ?
                    ORDER BY id DESC
                ) sg ON pr.group_id = sg.group_id
                WHERE pr.id = ? AND pr.status = 'ACTIVE'
            ''',
            'params': ('2025-07-11', 133)
        },
        {
            'name': '組別查詢',
            'sql': '''
                SELECT * FROM position_records 
                WHERE group_id = ? AND status = 'ACTIVE'
                ORDER BY lot_id
            ''',
            'params': (49,)
        }
    ]
    
    try:
        print("\n🧪 測試查詢性能...")
        
        with sqlite3.connect(db_path) as conn:
            cursor = conn.cursor()
            
            for query in test_queries:
                try:
                    start_time = time.time()
                    cursor.execute(query['sql'], query['params'])
                    results = cursor.fetchall()
                    elapsed = (time.time() - start_time) * 1000
                    
                    print(f"  📊 {query['name']}: {elapsed:.1f}ms ({len(results)}筆結果)")
                    
                    if elapsed < 50:
                        print(f"    ✅ 性能優秀")
                    elif elapsed < 100:
                        print(f"    ⚠️ 性能良好")
                    else:
                        print(f"    ❌ 性能需要改善")
                        
                except Exception as e:
                    print(f"  ❌ {query['name']}: 查詢失敗 - {e}")
                    
    except Exception as e:
        print(f"❌ 性能測試失敗: {e}")

def main():
    """主函數"""
    print("🚀 資料庫索引優化工具")
    print("="*50)
    
    # 添加索引
    success = add_database_indexes()
    
    if success:
        print("\n✅ 索引添加完成")
        
        # 測試性能
        test_query_performance()
        
        print("\n💡 建議:")
        print("1. 重啟交易系統以確保索引生效")
        print("2. 監控平倉查詢性能改善")
        print("3. 如有問題可隨時刪除索引回滾")
        
    else:
        print("\n❌ 索引添加失敗，請檢查錯誤信息")

if __name__ == "__main__":
    main()
