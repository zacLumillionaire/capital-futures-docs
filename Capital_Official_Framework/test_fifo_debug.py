#!/usr/bin/env python3
# -*- coding: utf-8 -*-

print("🚀 開始FIFO調試測試...")

try:
    from simplified_order_tracker import SimplifiedOrderTracker
    print("✅ SimplifiedOrderTracker 導入成功")
    
    # 創建實例
    tracker = SimplifiedOrderTracker(console_enabled=True)
    print("✅ SimplifiedOrderTracker 創建成功")
    
    # 註冊策略組
    success = tracker.register_strategy_group(
        group_id=10,
        total_lots=3,
        direction="SHORT",
        target_price=22573.0,
        product="TM0000"
    )
    print(f"✅ 策略組註冊: {success}")
    
    # 更新已送出口數
    tracker.update_submitted_lots(group_id=10, lots=3)
    print("✅ 已送出口數更新完成")
    
    # 檢查初始狀態
    group = tracker.get_strategy_group(10)
    if group:
        print(f"📊 初始狀態: {group.filled_lots}/{group.total_lots}, 完成={group.is_complete()}")
    
    print("\n" + "="*50)
    print("🔍 開始測試成交回報...")
    
    # 第一口成交
    print("\n📋 第一口成交 @22574")
    result1 = tracker._handle_fill_report_fifo(22574.0, 1, "TM2507")
    print(f"結果: {result1}")
    
    if group:
        print(f"📊 狀態: {group.filled_lots}/{group.total_lots}")
    
    # 第二口成交
    print("\n📋 第二口成交 @22573")
    result2 = tracker._handle_fill_report_fifo(22573.0, 1, "TM2507")
    print(f"結果: {result2}")
    
    if group:
        print(f"📊 狀態: {group.filled_lots}/{group.total_lots}")
    
    # 第三口成交
    print("\n📋 第三口成交 @22573")
    result3 = tracker._handle_fill_report_fifo(22573.0, 1, "TM2507")
    print(f"結果: {result3}")
    
    if group:
        print(f"📊 最終狀態: {group.filled_lots}/{group.total_lots}")
    
    print("\n" + "="*50)
    print("📊 測試結果:")
    print(f"第一口: {'✅' if result1 else '❌'}")
    print(f"第二口: {'✅' if result2 else '❌'}")
    print(f"第三口: {'✅' if result3 else '❌'}")
    
except Exception as e:
    print(f"❌ 測試失敗: {e}")
    import traceback
    traceback.print_exc()

print("🎉 測試完成")
