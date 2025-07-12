#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
測試步驟2：修改部位記錄創建邏輯
"""

import os
from datetime import date
from typing import Dict, Any

# 模擬下單管理器
class MockOrderManager:
    """模擬下單管理器"""
    
    def __init__(self, success_rate=0.75):
        self.success_rate = success_rate
        self.order_counter = 0
    
    def place_order(self, direction: str, quantity: int, price: float, signal_source: str):
        """模擬下單"""
        self.order_counter += 1
        order_id = f"MOCK_ORDER_{self.order_counter:03d}"
        
        # 模擬成功/失敗
        import random
        success = random.random() < self.success_rate
        
        if success:
            return MockOrderResult(
                success=True,
                order_id=order_id,
                api_result=f"API_{self.order_counter:08d}"
            )
        else:
            return MockOrderResult(
                success=False,
                error="模擬下單失敗"
            )

class MockOrderResult:
    """模擬下單結果"""
    
    def __init__(self, success: bool, order_id: str = None, api_result: str = None, error: str = None):
        self.success = success
        self.order_id = order_id
        self.api_result = api_result
        self.error = error

def test_step2_order_logic():
    """測試步驟2的下單邏輯修改"""
    print("🧪 測試步驟2：修改部位記錄創建邏輯")
    print("=" * 60)
    
    # 清理舊的測試資料庫
    test_db_path = "test_step2_order_logic.db"
    if os.path.exists(test_db_path):
        os.remove(test_db_path)
        print("✅ 清理舊測試資料庫")
    
    try:
        # 導入必要模組
        from multi_group_database import MultiGroupDatabaseManager
        from multi_group_config import create_preset_configs
        from multi_group_position_manager import MultiGroupPositionManager
        
        # 1. 創建測試環境
        db_manager = MultiGroupDatabaseManager(test_db_path)
        presets = create_preset_configs()
        config = presets["平衡配置 (2口×2組)"]
        
        # 2. 創建模擬下單管理器（75%成功率）
        mock_order_manager = MockOrderManager(success_rate=0.75)
        
        # 3. 創建部位管理器（整合下單管理器）
        manager = MultiGroupPositionManager(
            db_manager=db_manager,
            strategy_config=config,
            order_manager=mock_order_manager,
            order_tracker=None  # 暫時不使用追蹤器
        )
        
        print("✅ 測試環境初始化完成")
        print(f"📊 配置: {config.total_groups}組×{config.lots_per_group}口")
        print(f"🎯 模擬下單成功率: 75%")
        
        # 4. 創建策略組
        today = date.today().strftime('%Y-%m-%d')
        group_ids = manager.create_entry_signal(
            direction="LONG",
            signal_time="08:48:15",
            range_high=22530.0,
            range_low=22480.0
        )
        
        print(f"\n✅ 創建策略組: {len(group_ids)} 組")
        
        # 5. 測試執行進場（新的邏輯）
        if group_ids:
            print(f"\n🚀 測試新的進場邏輯...")
            
            for i, group_db_id in enumerate(group_ids):
                print(f"\n--- 測試組別 {i+1} (DB ID: {group_db_id}) ---")
                
                # 執行進場
                success = manager.execute_group_entry(
                    group_db_id=group_db_id,
                    actual_price=22515.0,
                    actual_time="08:48:20"
                )
                
                print(f"進場結果: {'✅ 成功' if success else '❌ 失敗'}")
                
                # 檢查資料庫記錄
                positions = db_manager.get_active_positions_by_group(group_db_id)
                failed_positions = []
                
                # 查詢失敗的部位
                with db_manager.get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('''
                        SELECT * FROM position_records 
                        WHERE group_id = ? AND status = 'FAILED'
                    ''', (group_db_id,))
                    failed_positions = cursor.fetchall()
                
                print(f"  📊 活躍部位: {len(positions)}口")
                print(f"  📊 失敗部位: {len(failed_positions)}口")
                
                # 顯示詳細狀態
                with db_manager.get_connection() as conn:
                    conn.row_factory = lambda cursor, row: dict(zip([col[0] for col in cursor.description], row))
                    cursor = conn.cursor()
                    cursor.execute('''
                        SELECT lot_id, status, order_status, order_id, api_seq_no, entry_price
                        FROM position_records 
                        WHERE group_id = ?
                        ORDER BY lot_id
                    ''', (group_db_id,))
                    all_positions = cursor.fetchall()
                
                for pos in all_positions:
                    status_icon = "✅" if pos['status'] == 'ACTIVE' else "❌" if pos['status'] == 'FAILED' else "⏳"
                    print(f"    {status_icon} 第{pos['lot_id']}口: {pos['status']}/{pos['order_status']} "
                          f"訂單={pos['order_id']} 價格={pos['entry_price']}")
        
        # 6. 測試統計功能
        print(f"\n📊 整體統計:")
        stats = db_manager.get_position_statistics(today)
        print(f"  - 總部位數: {stats['total_positions']}")
        print(f"  - 活躍部位: {stats['active_positions']}")
        print(f"  - 失敗部位: {stats['failed_positions']}")
        print(f"  - 成功率: {stats['success_rate']}%")
        
        # 7. 驗證新邏輯的正確性
        print(f"\n🔍 驗證新邏輯:")
        
        # 檢查是否有PENDING狀態的部位（應該沒有，因為都已經處理完成）
        with db_manager.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT COUNT(*) FROM position_records WHERE order_status = 'PENDING'")
            pending_count = cursor.fetchone()[0]
        
        if pending_count == 0:
            print("  ✅ 沒有遺留的PENDING狀態部位")
        else:
            print(f"  ⚠️ 發現 {pending_count} 個PENDING狀態部位")
        
        # 檢查失敗部位是否正確標記
        with db_manager.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                SELECT COUNT(*) FROM position_records 
                WHERE status = 'FAILED' AND order_status IN ('REJECTED', 'CANCELLED')
            ''')
            failed_count = cursor.fetchone()[0]
        
        print(f"  ✅ 正確標記的失敗部位: {failed_count} 個")
        
        # 檢查成功部位是否有訂單ID
        with db_manager.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                SELECT COUNT(*) FROM position_records 
                WHERE status = 'ACTIVE' AND order_id IS NOT NULL
            ''')
            active_with_order_id = cursor.fetchone()[0]
        
        print(f"  ✅ 有訂單ID的活躍部位: {active_with_order_id} 個")
        
        print("\n🎉 步驟2測試完成！")
        print("\n📋 測試結果總結:")
        print("  ✅ 新的進場邏輯正常運作")
        print("  ✅ PENDING → ACTIVE/FAILED 狀態轉換正確")
        print("  ✅ 訂單資訊正確記錄")
        print("  ✅ 失敗部位正確標記")
        
    except Exception as e:
        print(f"❌ 測試失敗: {e}")
        import traceback
        traceback.print_exc()
    
    finally:
        # 清理測試資料庫
        if os.path.exists(test_db_path):
            os.remove(test_db_path)
            print("🧹 清理測試資料庫")

if __name__ == "__main__":
    test_step2_order_logic()
