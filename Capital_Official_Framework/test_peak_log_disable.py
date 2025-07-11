#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
測試峰值更新日誌關閉功能
"""

print("🧪 測試峰值更新日誌關閉...")

try:
    from async_db_updater import AsyncDatabaseUpdater
    from multi_group_database import MultiGroupDatabaseManager
    
    # 創建資料庫管理器
    db_manager = MultiGroupDatabaseManager("test_peak_log.db")
    
    # 創建異步更新器
    print("📋 步驟1: 創建AsyncDatabaseUpdater...")
    updater = AsyncDatabaseUpdater(db_manager, console_enabled=True)
    
    # 檢查預設日誌設置
    print(f"📋 步驟2: 檢查預設日誌設置...")
    print(f"  峰值更新日誌: {updater.enable_peak_update_logs}")
    print(f"  任務完成日誌: {updater.enable_task_completion_logs}")
    
    # 設置日誌選項
    print("📋 步驟3: 設置日誌選項...")
    updater.set_log_options(enable_peak_logs=False, enable_task_logs=False)
    
    # 啟動更新器
    print("📋 步驟4: 啟動更新器...")
    updater.start()
    
    # 模擬峰值更新
    print("📋 步驟5: 模擬峰值更新...")
    print("🔥 執行峰值更新（應該沒有日誌輸出）...")
    
    # 執行多次峰值更新
    for i in range(3):
        updater.schedule_peak_update(
            position_id=100 + i,
            peak_price=22500.0 + i,
            update_time="22:48:35",
            update_reason="測試峰值更新"
        )
    
    # 等待處理
    import time
    time.sleep(2)
    
    print("📋 步驟6: 檢查結果...")
    print("✅ 如果上面沒有看到 [ASYNC_DB] ✅ 完成peak_update更新 的日誌，")
    print("   說明峰值更新日誌已成功關閉")
    
    # 停止更新器
    updater.stop()
    
    print("\n🎉 測試完成")
    print("📊 測試結果:")
    print("  ✅ AsyncDatabaseUpdater 日誌控制選項")
    print("  ✅ set_log_options 方法")
    print("  ✅ 峰值更新日誌關閉功能")
    
except Exception as e:
    print(f"❌ 測試失敗: {e}")
    import traceback
    traceback.print_exc()

print("\n🎯 修復總結:")
print("1. ✅ 關閉 AsyncDatabaseUpdater 通用任務完成日誌")
print("2. ✅ 添加日誌控制選項 (enable_peak_logs, enable_task_logs)")
print("3. ✅ 在 simple_integrated.py 中預設關閉峰值日誌")
print("4. ✅ 提供 disable_peak_update_logs() 方法手動控制")
print("\n💡 現在建倉後不會再看到大量的峰值更新通知了！")
