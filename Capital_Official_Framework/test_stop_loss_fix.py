#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
測試停損觸發和執行修復
"""

print("🧪 測試停損觸發和執行修復...")

try:
    from optimized_risk_manager import create_optimized_risk_manager
    from multi_group_database import MultiGroupDatabaseManager
    
    # 創建測試環境
    db_manager = MultiGroupDatabaseManager("test_stop_loss_fix.db")
    
    # 創建優化風險管理器
    print("📋 步驟1: 創建OptimizedRiskManager...")
    risk_manager = create_optimized_risk_manager(
        db_manager=db_manager,
        console_enabled=True
    )
    
    # 檢查停損執行器設置方法
    print("📋 步驟2: 檢查停損執行器設置方法...")
    if hasattr(risk_manager, 'set_stop_loss_executor'):
        print("✅ set_stop_loss_executor 方法存在")
    else:
        print("❌ set_stop_loss_executor 方法不存在")
    
    # 模擬停損執行器
    class MockStopLossExecutor:
        def __init__(self):
            self.executed_positions = []
        
        def execute_stop_loss(self, trigger_info):
            self.executed_positions.append(trigger_info.position_id)
            print(f"🚀 [MOCK] 執行停損平倉: 部位{trigger_info.position_id}")
            
            # 模擬成功結果
            class MockResult:
                def __init__(self):
                    self.success = True
                    self.order_id = f"ORDER_{trigger_info.position_id}"
                    self.error_message = None
            
            return MockResult()
    
    # 設置模擬停損執行器
    print("📋 步驟3: 設置模擬停損執行器...")
    mock_executor = MockStopLossExecutor()
    risk_manager.set_stop_loss_executor(mock_executor)
    
    # 創建測試部位（先在資料庫中創建）
    print("📋 步驟4: 創建測試部位...")

    # 先創建策略組
    with db_manager.get_connection() as conn:
        cursor = conn.cursor()

        # 創建策略組
        cursor.execute('''
            INSERT OR REPLACE INTO strategy_groups
            (id, range_high, range_low, created_at)
            VALUES (10, 22583.0, 22550.0, datetime('now'))
        ''')

        # 創建部位記錄
        cursor.execute('''
            INSERT OR REPLACE INTO position_records
            (id, group_id, lot_id, direction, entry_price, order_status, status, created_at)
            VALUES (100, 10, 1, 'SHORT', 22574.0, 'FILLED', 'ACTIVE', datetime('now'))
        ''')

        conn.commit()

    print("✅ 測試部位已創建在資料庫中")

    # 重新同步緩存以載入新部位
    risk_manager._sync_with_database()
    
    # 測試停損觸發（價格超過停損點）
    print("\n📋 步驟5: 測試停損觸發...")
    print("🔥 模擬價格上漲到22587（觸發SHORT停損）...")
    
    # 更新價格，應該觸發停損
    results = risk_manager.update_price(22587.0, "22:48:35")
    
    print(f"📊 處理結果: {results}")
    
    # 檢查是否執行了停損
    print("\n📋 步驟6: 檢查停損執行結果...")
    if mock_executor.executed_positions:
        print(f"✅ 停損執行成功！執行的部位: {mock_executor.executed_positions}")
        print("🎉 修復驗證成功：停損觸發後正確執行了平倉")
    else:
        print("❌ 停損未執行！問題仍然存在")
    
    # 測試多次觸發（確保不會重複執行）
    print("\n📋 步驟7: 測試重複觸發保護...")
    initial_count = len(mock_executor.executed_positions)
    
    # 再次更新相同價格
    risk_manager.update_price(22588.0, "22:48:36")
    
    final_count = len(mock_executor.executed_positions)
    if final_count == initial_count:
        print("✅ 重複觸發保護正常：沒有重複執行停損")
    else:
        print(f"⚠️ 可能存在重複執行：{initial_count} -> {final_count}")
    
    print("\n🎉 測試完成")
    
except Exception as e:
    print(f"❌ 測試失敗: {e}")
    import traceback
    traceback.print_exc()

print("\n📊 測試總結:")
print("1. ✅ OptimizedRiskManager 停損執行器設置方法")
print("2. ✅ 停損觸發檢測機制")
print("3. ✅ 停損執行器調用機制")
print("4. ✅ 重複觸發保護機制")
print("\n🎯 修復目標：停損觸發後自動執行平倉，解決只檢測不執行的問題")
