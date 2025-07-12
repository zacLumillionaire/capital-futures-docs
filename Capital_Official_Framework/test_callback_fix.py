#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
測試回調修復效果
"""

print("🧪 測試SimplifiedTracker回調修復...")

try:
    from multi_group_database import MultiGroupDatabaseManager
    from multi_group_config import create_preset_configs
    from multi_group_position_manager import MultiGroupPositionManager
    
    # 創建測試環境
    db_manager = MultiGroupDatabaseManager("test_callback_fix.db")
    presets = create_preset_configs()
    config = presets["標準配置 (3口×1組)"]
    
    # 創建部位管理器（會自動創建SimplifiedTracker並註冊回調）
    print("📋 步驟1: 創建MultiGroupPositionManager...")
    manager = MultiGroupPositionManager(db_manager, config)
    
    # 檢查SimplifiedTracker狀態
    if hasattr(manager, 'simplified_tracker') and manager.simplified_tracker:
        tracker = manager.simplified_tracker
        callback_count = len(tracker.fill_callbacks)
        print(f"✅ SimplifiedTracker存在，回調數量: {callback_count}")
        
        if callback_count > 0:
            print("✅ 回調已正確註冊")
        else:
            print("❌ 回調未註冊")
    else:
        print("❌ SimplifiedTracker不存在")
    
    # 模擬simple_integrated.py的邏輯
    print("\n📋 步驟2: 模擬simple_integrated.py的初始化邏輯...")
    
    # 檢查是否需要重新創建（模擬修復後的邏輯）
    if not hasattr(manager, 'simplified_tracker') or not manager.simplified_tracker:
        from simplified_order_tracker import SimplifiedOrderTracker
        manager.simplified_tracker = SimplifiedOrderTracker()
        manager._setup_simplified_tracker_callbacks()
        print("[MULTI_GROUP] ✅ 簡化追蹤器初始化完成")
    else:
        print("[MULTI_GROUP] ✅ 簡化追蹤器已存在，跳過重複創建")
        # 檢查回調
        if hasattr(manager.simplified_tracker, 'fill_callbacks'):
            callback_count = len(manager.simplified_tracker.fill_callbacks)
            print(f"[MULTI_GROUP] 📊 當前回調數量: {callback_count}")
            if callback_count == 0:
                print("[MULTI_GROUP] ⚠️ 檢測到回調丟失，重新設置...")
                manager._setup_simplified_tracker_callbacks()
    
    # 再次檢查回調狀態
    print("\n📋 步驟3: 檢查修復後的回調狀態...")
    if hasattr(manager, 'simplified_tracker') and manager.simplified_tracker:
        tracker = manager.simplified_tracker
        callback_count = len(tracker.fill_callbacks)
        print(f"✅ 修復後回調數量: {callback_count}")
        
        # 測試回調功能
        print("\n📋 步驟4: 測試回調功能...")
        
        # 註冊策略組
        tracker.register_strategy_group(
            group_id=10,
            total_lots=3,
            direction="SHORT",
            target_price=22573.0,
            product="TM0000"
        )
        
        # 更新已送出口數
        tracker.update_submitted_lots(group_id=10, lots=3)
        
        # 測試成交回報處理
        print("🔥 測試第一口成交...")
        result1 = tracker._handle_fill_report_fifo(22574.0, 1, "TM2507")
        print(f"結果: {result1}")
        
        print("🔥 測試第二口成交...")
        result2 = tracker._handle_fill_report_fifo(22573.0, 1, "TM2507")
        print(f"結果: {result2}")
        
        print("🔥 測試第三口成交...")
        result3 = tracker._handle_fill_report_fifo(22573.0, 1, "TM2507")
        print(f"結果: {result3}")
        
        # 檢查最終狀態
        group = tracker.get_strategy_group(10)
        if group:
            print(f"📊 最終狀態: {group.filled_lots}/3口")
            print(f"✅ 測試結果: {'成功' if group.filled_lots == 3 else '失敗'}")
        
    print("\n🎉 測試完成")
    
except Exception as e:
    print(f"❌ 測試失敗: {e}")
    import traceback
    traceback.print_exc()
