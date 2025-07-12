#!/usr/bin/env python3
# -*- coding: utf-8 -*-

print("🧪 簡單停損測試...")

try:
    from optimized_risk_manager import OptimizedRiskManager
    from multi_group_database import MultiGroupDatabaseManager
    
    # 創建資料庫
    db_manager = MultiGroupDatabaseManager("simple_test.db")
    
    # 創建風險管理器
    risk_manager = OptimizedRiskManager(db_manager, console_enabled=True)
    
    # 檢查方法
    print(f"✅ 停損執行器設置方法: {hasattr(risk_manager, 'set_stop_loss_executor')}")
    print(f"✅ 停損檢查方法: {hasattr(risk_manager, '_check_stop_loss_trigger')}")
    print(f"✅ 停損執行方法: {hasattr(risk_manager, '_execute_stop_loss')}")
    
    # 模擬執行器
    class MockExecutor:
        def __init__(self):
            self.calls = []
        
        def execute_stop_loss(self, trigger):
            self.calls.append(trigger.position_id)
            print(f"🚀 [MOCK] 執行停損: {trigger.position_id}")
            
            class Result:
                success = True
                order_id = "TEST_ORDER"
                error_message = None
            return Result()
    
    # 設置執行器
    executor = MockExecutor()
    risk_manager.set_stop_loss_executor(executor)
    
    # 手動測試停損檢查
    print("\n🔥 手動測試停損檢查...")
    
    # 設置測試數據
    risk_manager.position_cache['100'] = {'direction': 'SHORT'}
    risk_manager.stop_loss_cache['100'] = 22583.0
    
    # 測試觸發條件
    result = risk_manager._check_stop_loss_trigger('100', 22587.0)
    print(f"停損檢查結果: {result}")
    print(f"執行器調用次數: {len(executor.calls)}")
    
    if executor.calls:
        print("✅ 停損執行成功！")
    else:
        print("❌ 停損未執行")
    
except Exception as e:
    print(f"❌ 錯誤: {e}")
    import traceback
    traceback.print_exc()

print("🎉 測試完成")
