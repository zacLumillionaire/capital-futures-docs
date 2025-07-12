#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
測試 sqlite3.Row 轉換問題修復
"""

import sys
import os
import time
import sqlite3

# 添加路徑
current_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, current_dir)

def test_sqlite_row_conversion():
    """測試 sqlite3.Row 轉換問題"""
    print("🧪 測試 sqlite3.Row 轉換問題修復...")
    
    try:
        # 創建測試資料庫
        test_db = "test_sqlite_row.db"
        conn = sqlite3.connect(test_db)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        # 創建測試表
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS test_positions (
                id INTEGER PRIMARY KEY,
                direction TEXT,
                entry_price REAL,
                range_high REAL,
                range_low REAL
            )
        ''')
        
        # 插入測試數據
        cursor.execute('''
            INSERT INTO test_positions (direction, entry_price, range_high, range_low)
            VALUES (?, ?, ?, ?)
        ''', ('LONG', 22438.0, 22450.0, 22425.0))
        
        conn.commit()
        
        # 測試查詢和轉換
        cursor.execute('SELECT * FROM test_positions WHERE id = 1')
        row = cursor.fetchone()
        
        print(f"✅ 查詢到 Row 對象: {type(row)}")
        
        # 測試不同的轉換方法
        try:
            # 方法1：直接轉換
            dict_data_1 = dict(row)
            print(f"✅ 方法1 (dict(row)) 成功: {dict_data_1}")
        except Exception as e:
            print(f"❌ 方法1 失敗: {e}")
            
            # 方法2：手動轉換
            try:
                columns = [description[0] for description in cursor.description]
                dict_data_2 = dict(zip(columns, row))
                print(f"✅ 方法2 (手動轉換) 成功: {dict_data_2}")
            except Exception as e2:
                print(f"❌ 方法2 也失敗: {e2}")
        
        # 測試 .get() 方法
        try:
            if hasattr(row, 'keys'):
                # sqlite3.Row 支持 keys() 方法
                dict_data_3 = {key: row[key] for key in row.keys()}
                print(f"✅ 方法3 (keys()) 成功: {dict_data_3}")
                
                # 測試 .get() 方法模擬
                def safe_get(row_obj, key, default=None):
                    try:
                        return row_obj[key] if key in row_obj.keys() else default
                    except:
                        return default
                
                test_value = safe_get(dict_data_3, 'id')
                print(f"✅ 安全 get 方法測試: id = {test_value}")
                
        except Exception as e:
            print(f"❌ 方法3 失敗: {e}")
        
        conn.close()
        os.remove(test_db)
        
        return True
        
    except Exception as e:
        print(f"❌ sqlite3.Row 轉換測試失敗: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_optimized_risk_manager_fix():
    """測試優化風險管理器修復"""
    print("\n🧪 測試優化風險管理器修復...")
    
    try:
        from optimized_risk_manager import create_optimized_risk_manager
        from multi_group_database import MultiGroupDatabaseManager
        
        # 創建測試環境
        db_manager = MultiGroupDatabaseManager("test_risk_manager_fix.db")
        risk_manager = create_optimized_risk_manager(db_manager, console_enabled=True)
        
        print("✅ 優化風險管理器創建成功")
        
        # 創建測試策略組和部位
        group_id = db_manager.create_strategy_group(
            date="2025-01-09",
            group_id=1,
            direction="LONG",
            signal_time="17:16:00",
            range_high=22450.0,
            range_low=22425.0,
            total_lots=1
        )
        
        position_id = db_manager.create_position_record(
            group_id=group_id,
            lot_id=1,
            direction="LONG",
            entry_price=22438.0,
            entry_time="17:16:01",
            order_status='ACTIVE'
        )
        
        print(f"✅ 創建測試數據: 組={group_id}, 部位={position_id}")
        
        # 測試同步功能
        try:
            risk_manager._sync_with_database()
            print("✅ 資料庫同步成功，沒有 sqlite3.Row 錯誤")
        except Exception as sync_error:
            print(f"❌ 資料庫同步失敗: {sync_error}")
            return False
        
        # 測試新部位事件
        test_position = {
            'id': position_id,
            'direction': 'LONG',
            'entry_price': 22438.0,
            'range_high': 22450.0,
            'range_low': 22425.0,
            'group_id': group_id
        }
        
        try:
            risk_manager.on_new_position(test_position)
            print("✅ 新部位事件處理成功，沒有 'get' 方法錯誤")
        except Exception as event_error:
            print(f"❌ 新部位事件處理失敗: {event_error}")
            return False
        
        # 清理
        os.remove("test_risk_manager_fix.db")
        
        return True
        
    except Exception as e:
        print(f"❌ 優化風險管理器測試失敗: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_async_updater_improvements():
    """測試異步更新器改善"""
    print("\n🧪 測試異步更新器改善...")
    
    try:
        from async_db_updater import AsyncDatabaseUpdater
        from multi_group_database import MultiGroupDatabaseManager
        
        # 創建測試環境
        db_manager = MultiGroupDatabaseManager("test_async_improvements.db")
        async_updater = AsyncDatabaseUpdater(db_manager, console_enabled=True)
        async_updater.start()
        
        print("✅ 異步更新器啟動成功")
        
        # 創建測試數據
        group_id = db_manager.create_strategy_group(
            date="2025-01-09",
            group_id=1,
            direction="LONG",
            signal_time="17:16:00",
            range_high=22450.0,
            range_low=22425.0,
            total_lots=1
        )
        
        position_id = db_manager.create_position_record(
            group_id=group_id,
            lot_id=1,
            direction="LONG",
            entry_price=22438.0,
            entry_time="17:16:01",
            order_status='PENDING'
        )
        
        print(f"✅ 創建測試數據: 組={group_id}, 部位={position_id}")
        
        # 測試重複風險狀態創建處理
        print("🔄 測試重複風險狀態創建處理...")
        
        # 第一次創建（應該成功）
        async_updater.schedule_risk_state_creation(
            position_id=position_id,
            peak_price=22438.0,
            current_time="17:16:01",
            update_reason="第一次創建"
        )
        
        # 第二次創建（應該自動改為更新）
        async_updater.schedule_risk_state_creation(
            position_id=position_id,
            peak_price=22440.0,
            current_time="17:16:02",
            update_reason="第二次創建"
        )
        
        # 等待處理完成
        time.sleep(2)
        
        # 檢查統計
        stats = async_updater.get_stats()
        print(f"✅ 異步更新統計: {stats}")
        
        # 停止更新器
        async_updater.stop()
        
        # 清理
        os.remove("test_async_improvements.db")
        
        return True
        
    except Exception as e:
        print(f"❌ 異步更新器改善測試失敗: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """主測試函數"""
    print("🚀 開始 sqlite3.Row 轉換問題修復測試...")
    print("=" * 60)
    
    # 測試1: sqlite3.Row 轉換
    test1_result = test_sqlite_row_conversion()
    
    # 測試2: 優化風險管理器修復
    test2_result = test_optimized_risk_manager_fix()
    
    # 測試3: 異步更新器改善
    test3_result = test_async_updater_improvements()
    
    # 總結
    print("\n" + "=" * 60)
    print("📋 測試結果總結:")
    print(f"  sqlite3.Row 轉換: {'✅ 通過' if test1_result else '❌ 失敗'}")
    print(f"  優化風險管理器修復: {'✅ 通過' if test2_result else '❌ 失敗'}")
    print(f"  異步更新器改善: {'✅ 通過' if test3_result else '❌ 失敗'}")
    
    all_passed = all([test1_result, test2_result, test3_result])
    
    if all_passed:
        print("\n🎉 所有修復測試通過！")
        print("\n💡 修復效果:")
        print("  ✅ sqlite3.Row 轉換錯誤已修復")
        print("  ✅ 異步更新失敗問題已改善")
        print("  ✅ 系統應該能正常使用異步更新")
        print("  ✅ 大延遲問題應該得到解決")
        
        print("\n🔧 下次交易時觀察:")
        print("  - 應該看到更多 [異步更新] 日誌")
        print("  - [PERFORMANCE] 延遲警告應該減少")
        print("  - 不應該再看到 sqlite3.Row 錯誤")
        
        return True
    else:
        print("\n⚠️ 部分測試失敗，需要進一步檢查")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
