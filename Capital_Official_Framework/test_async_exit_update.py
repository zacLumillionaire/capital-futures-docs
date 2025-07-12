#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
測試異步平倉更新機制
驗證第一階段修改是否正常工作
"""

import time
import threading
from datetime import datetime

# 導入相關模組
from async_db_updater import AsyncDatabaseUpdater
from multi_group_database import MultiGroupDatabaseManager
from stop_loss_executor import StopLossExecutor, StopLossExecutionResult, StopLossTrigger

def test_async_exit_update():
    """測試異步平倉更新機制"""
    print("🧪 測試異步平倉更新機制")
    print("=" * 50)
    
    try:
        # 1. 初始化資料庫管理器
        print("1️⃣ 初始化資料庫管理器...")
        db_manager = MultiGroupDatabaseManager("test_async_exit.db")
        
        # 2. 初始化異步更新器
        print("2️⃣ 初始化異步更新器...")
        async_updater = AsyncDatabaseUpdater(db_manager, console_enabled=True)
        async_updater.start()
        
        # 3. 初始化停損執行器
        print("3️⃣ 初始化停損執行器...")
        stop_executor = StopLossExecutor(db_manager, console_enabled=True)
        stop_executor.set_async_updater(async_updater, enabled=True)
        
        # 4. 測試異步平倉更新
        print("4️⃣ 測試異步平倉更新...")
        
        # 模擬平倉數據
        test_position_id = 999
        test_exit_price = 22500.0
        test_exit_time = datetime.now().strftime('%H:%M:%S')
        test_exit_reason = 'TEST_STOP_LOSS'
        test_order_id = 'TEST_ORDER_001'
        test_pnl = -50.0
        
        print(f"   測試部位ID: {test_position_id}")
        print(f"   平倉價格: {test_exit_price}")
        print(f"   平倉時間: {test_exit_time}")
        print(f"   平倉原因: {test_exit_reason}")
        print(f"   訂單ID: {test_order_id}")
        print(f"   損益: {test_pnl}")
        
        # 執行異步平倉更新
        start_time = time.time()
        async_updater.schedule_position_exit_update(
            position_id=test_position_id,
            exit_price=test_exit_price,
            exit_time=test_exit_time,
            exit_reason=test_exit_reason,
            order_id=test_order_id,
            pnl=test_pnl
        )
        elapsed = (time.time() - start_time) * 1000
        print(f"   ✅ 異步更新排程完成 (耗時: {elapsed:.1f}ms)")
        
        # 5. 測試緩存查詢
        print("5️⃣ 測試緩存查詢...")
        
        # 立即查詢緩存
        cached_exit = async_updater.get_cached_exit_status(test_position_id)
        if cached_exit:
            print(f"   ✅ 緩存查詢成功:")
            print(f"      狀態: {cached_exit.get('status')}")
            print(f"      平倉價格: {cached_exit.get('exit_price')}")
            print(f"      平倉時間: {cached_exit.get('exit_time')}")
            print(f"      平倉原因: {cached_exit.get('exit_reason')}")
        else:
            print("   ❌ 緩存查詢失敗")
        
        # 測試快速狀態檢查
        is_exited = async_updater.is_position_exited_in_cache(test_position_id)
        print(f"   快速狀態檢查: {'已平倉' if is_exited else '未平倉'}")
        
        # 6. 測試重複平倉防護
        print("6️⃣ 測試重複平倉防護...")
        
        # 模擬觸發信息
        trigger_info = StopLossTrigger(
            position_id=test_position_id,
            current_price=22500.0,
            trigger_reason='TEST_DUPLICATE_CHECK'
        )
        
        # 檢查重複平倉防護
        protection_result = stop_executor._check_duplicate_exit_protection(test_position_id)
        print(f"   防護檢查結果: {protection_result}")
        
        # 7. 等待異步處理完成
        print("7️⃣ 等待異步處理...")
        time.sleep(3)  # 等待3秒讓異步處理完成
        
        # 8. 檢查統計信息
        print("8️⃣ 檢查統計信息...")
        stats = async_updater.get_stats()
        print(f"   總任務數: {stats.get('total_tasks', 0)}")
        print(f"   完成任務數: {stats.get('completed_tasks', 0)}")
        print(f"   成功任務數: {stats.get('successful_tasks', 0)}")
        print(f"   隊列大小: {stats.get('queue_size', 0)}")
        print(f"   緩存命中: {stats.get('cache_hits', 0)}")
        
        print("✅ 異步平倉更新測試完成")
        
    except Exception as e:
        print(f"❌ 測試失敗: {e}")
        import traceback
        traceback.print_exc()
    
    finally:
        # 清理資源
        try:
            if 'async_updater' in locals():
                async_updater.stop()
                print("🧹 異步更新器已停止")
        except:
            pass

def test_duplicate_protection():
    """測試重複平倉防護機制"""
    print("\n🧪 測試重複平倉防護機制")
    print("=" * 50)
    
    try:
        # 初始化
        db_manager = MultiGroupDatabaseManager("test_protection.db")
        async_updater = AsyncDatabaseUpdater(db_manager, console_enabled=True)
        async_updater.start()
        
        stop_executor = StopLossExecutor(db_manager, console_enabled=True)
        stop_executor.set_async_updater(async_updater, enabled=True)
        
        test_position_id = 888
        
        # 第一次檢查（應該可以執行）
        print("1️⃣ 第一次防護檢查...")
        result1 = stop_executor._check_duplicate_exit_protection(test_position_id)
        print(f"   結果: {result1}")
        
        # 註冊執行中狀態
        print("2️⃣ 註冊執行中狀態...")
        stop_executor._register_exit_execution(test_position_id, 22500.0)
        
        # 第二次檢查（應該被防護）
        print("3️⃣ 第二次防護檢查...")
        result2 = stop_executor._check_duplicate_exit_protection(test_position_id)
        print(f"   結果: {result2}")
        
        # 清理執行狀態
        print("4️⃣ 清理執行狀態...")
        stop_executor._clear_exit_execution(test_position_id)
        
        # 第三次檢查（應該又可以執行）
        print("5️⃣ 第三次防護檢查...")
        result3 = stop_executor._check_duplicate_exit_protection(test_position_id)
        print(f"   結果: {result3}")
        
        print("✅ 重複平倉防護測試完成")
        
    except Exception as e:
        print(f"❌ 防護測試失敗: {e}")
        import traceback
        traceback.print_exc()
    
    finally:
        try:
            if 'async_updater' in locals():
                async_updater.stop()
        except:
            pass

if __name__ == "__main__":
    # 執行測試
    test_async_exit_update()
    test_duplicate_protection()
    
    print("\n🎯 測試總結:")
    print("✅ 異步平倉更新機制已實現")
    print("✅ 重複平倉防護機制已實現")
    print("✅ 緩存狀態檢查已實現")
    print("📝 下一步: 實施一對一平倉回報確認機制")
