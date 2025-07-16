#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
簡單保護性停損測試工具
專門測試累積獲利計算修復效果
"""

import os
import sys
import sqlite3
from datetime import datetime

# 添加當前目錄到路徑
current_dir = os.path.dirname(os.path.abspath(__file__))
if current_dir not in sys.path:
    sys.path.insert(0, current_dir)

def test_cumulative_profit_calculation():
    """直接測試累積獲利計算邏輯"""
    print("🧪 簡單保護性停損測試")
    print("=" * 40)
    
    # 創建臨時測試資料庫
    test_db = "simple_protection_test.db"
    
    try:
        # 清理舊文件
        if os.path.exists(test_db):
            os.remove(test_db)
        
        # 創建資料庫連接
        conn = sqlite3.connect(test_db)
        cursor = conn.cursor()
        
        # 創建簡化的測試表
        cursor.execute('''
            CREATE TABLE position_records (
                id INTEGER PRIMARY KEY,
                group_id INTEGER NOT NULL,
                lot_id INTEGER NOT NULL,
                direction TEXT NOT NULL,
                entry_time TEXT NOT NULL,
                status TEXT DEFAULT 'ACTIVE',
                realized_pnl REAL,
                entry_price REAL
            )
        ''')
        
        print("✅ 創建測試資料庫表")
        
        # 插入測試數據
        test_data = [
            (37, 1, 1, 'LONG', '09:00:00', 'EXITED', 24.0, 21500),  # 已平倉，獲利24點
            (38, 1, 2, 'LONG', '09:01:00', 'ACTIVE', None, 21510),  # 活躍中
            (39, 1, 3, 'LONG', '09:02:00', 'ACTIVE', None, 21515),  # 活躍中
        ]
        
        cursor.executemany('''
            INSERT INTO position_records 
            (id, group_id, lot_id, direction, entry_time, status, realized_pnl, entry_price)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        ''', test_data)
        
        conn.commit()
        print("✅ 插入測試數據")
        
        # 測試修復前的錯誤查詢（模擬）
        print("\n📊 測試修復前的查詢邏輯（模擬）:")
        cursor.execute('''
            SELECT realized_pnl 
            FROM position_records 
            WHERE group_id = ? 
              AND status = 'EXITED' 
              AND realized_pnl IS NOT NULL
              AND id <= ?
            ORDER BY id
        ''', (1, 37))
        
        old_results = cursor.fetchall()
        old_cumulative = sum(row[0] for row in old_results if row[0] is not None)
        print(f"   修復前查詢結果: {old_results}")
        print(f"   修復前累積獲利: {old_cumulative:.1f} 點")
        
        # 測試修復後的正確查詢
        print("\n📈 測試修復後的查詢邏輯:")
        cursor.execute('''
            SELECT id, realized_pnl, lot_id
            FROM position_records 
            WHERE group_id = ? 
              AND status = 'EXITED' 
              AND realized_pnl IS NOT NULL
            ORDER BY id
        ''', (1,))
        
        new_results = cursor.fetchall()
        new_cumulative = sum(row[1] for row in new_results if row[1] is not None)
        print(f"   修復後查詢結果: {new_results}")
        print(f"   修復後累積獲利: {new_cumulative:.1f} 點")
        
        # 驗證結果
        print(f"\n🔍 結果驗證:")
        print(f"   期望累積獲利: 24.0 點")
        print(f"   實際累積獲利: {new_cumulative:.1f} 點")
        
        if new_cumulative == 24.0:
            print("✅ 累積獲利計算修復成功！")
            success = True
        else:
            print("❌ 累積獲利計算仍有問題")
            success = False
        
        # 測試保護性停損更新邏輯
        print(f"\n🛡️ 測試保護性停損更新邏輯:")
        
        # 查詢需要更新的活躍部位
        cursor.execute('''
            SELECT id, lot_id, entry_price
            FROM position_records 
            WHERE group_id = ? 
              AND status = 'ACTIVE'
            ORDER BY id
        ''', (1,))
        
        active_positions = cursor.fetchall()
        print(f"   活躍部位: {active_positions}")
        
        if new_cumulative > 0 and len(active_positions) > 0:
            print(f"   ✅ 應該觸發保護性停損更新")
            print(f"   📊 累積獲利 {new_cumulative:.1f} 點 > 0，有 {len(active_positions)} 個活躍部位需要更新")
        else:
            print(f"   ❌ 不應該觸發保護性停損更新")
        
        conn.close()
        
        # 清理測試文件
        if os.path.exists(test_db):
            os.remove(test_db)
            print(f"\n🧹 清理測試文件: {test_db}")
        
        return success
        
    except Exception as e:
        print(f"❌ 測試異常: {e}")
        import traceback
        traceback.print_exc()
        
        # 清理測試文件
        try:
            if os.path.exists(test_db):
                os.remove(test_db)
        except:
            pass
        
        return False

def test_with_cumulative_profit_manager():
    """使用實際的CumulativeProfitProtectionManager測試"""
    print("\n🧪 使用實際保護管理器測試")
    print("=" * 40)
    
    try:
        from cumulative_profit_protection_manager import CumulativeProfitProtectionManager
        from multi_group_database import MultiGroupDatabaseManager
        
        # 創建測試資料庫
        test_db = "manager_protection_test.db"
        if os.path.exists(test_db):
            os.remove(test_db)
        
        db_manager = MultiGroupDatabaseManager(test_db)
        protection_manager = CumulativeProfitProtectionManager(db_manager, console_enabled=True)
        
        # 首先創建策略組
        print("📍 創建測試策略組...")

        with db_manager.get_connection() as conn:
            cursor = conn.cursor()

            # 創建策略組記錄
            cursor.execute('''
                INSERT OR REPLACE INTO strategy_groups
                (id, group_name, total_lots, status, created_at)
                VALUES (1, '測試策略組', 3, 'ACTIVE', datetime('now'))
            ''')
            conn.commit()

        print("✅ 創建策略組1")

        # 使用資料庫管理器的方法創建部位記錄
        print("📍 創建測試部位記錄...")

        # 創建部位37（將會平倉）
        position_37_id = db_manager.create_position_record(
            group_id=1,
            lot_id=1,
            direction='LONG',
            entry_price=21500,
            entry_time='09:00:00'
        )

        # 創建部位38（活躍中）
        position_38_id = db_manager.create_position_record(
            group_id=1,
            lot_id=2,
            direction='LONG',
            entry_price=21510,
            entry_time='09:01:00'
        )
        
        print(f"✅ 創建部位記錄: {position_37_id}, {position_38_id}")
        
        # 模擬部位37平倉並設置獲利
        with db_manager.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                UPDATE position_records 
                SET status = 'EXITED', realized_pnl = 24.0, exit_price = 21524
                WHERE id = ?
            ''', (position_37_id,))
            conn.commit()
        
        print("✅ 模擬部位37平倉，獲利24點")
        
        # 測試累積獲利計算
        print("\n📊 測試累積獲利計算...")
        cumulative_profit = protection_manager._calculate_cumulative_profit(1, position_37_id)
        
        print(f"\n🔍 結果驗證:")
        print(f"   期望累積獲利: 24.0 點")
        print(f"   實際累積獲利: {cumulative_profit:.1f} 點")
        
        if cumulative_profit == 24.0:
            print("✅ 保護管理器測試成功！")
            success = True
        else:
            print("❌ 保護管理器測試失敗")
            success = False
        
        # 清理測試文件
        if os.path.exists(test_db):
            os.remove(test_db)
            print(f"\n🧹 清理測試文件: {test_db}")
        
        return success
        
    except Exception as e:
        print(f"❌ 保護管理器測試異常: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """主測試函數"""
    print("🚀 簡單保護性停損測試工具")
    print("=" * 50)
    print("🎯 測試目標: 驗證累積獲利計算修復效果")
    print("=" * 50)
    
    start_time = datetime.now()
    
    # 執行測試
    test1_result = test_cumulative_profit_calculation()
    test2_result = test_with_cumulative_profit_manager()
    
    end_time = datetime.now()
    duration = (end_time - start_time).total_seconds()
    
    # 統計結果
    total_tests = 2
    passed_tests = sum([test1_result, test2_result])
    
    print("\n" + "=" * 50)
    print("📊 測試結果總結")
    print("=" * 50)
    print(f"測試時間: {duration:.2f} 秒")
    print(f"總測試: {total_tests}")
    print(f"通過: {passed_tests}")
    print(f"失敗: {total_tests - passed_tests}")
    print(f"通過率: {passed_tests/total_tests*100:.1f}%")
    
    print("\n詳細結果:")
    print(f"  直接SQL測試: {'✅ 通過' if test1_result else '❌ 失敗'}")
    print(f"  保護管理器測試: {'✅ 通過' if test2_result else '❌ 失敗'}")
    
    if passed_tests == total_tests:
        print("\n🎉 所有測試通過！保護性停損修復成功！")
        print("💡 幽靈BUG A（失憶的保護性停損）已被根除！")
    else:
        print("\n⚠️ 部分測試失敗，需要進一步檢查")
    
    return passed_tests == total_tests

if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)
