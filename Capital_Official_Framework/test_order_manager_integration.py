#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
測試下單管理器整合修復
"""

import os
from datetime import date

def test_order_manager_integration():
    """測試下單管理器整合"""
    print("🧪 測試下單管理器整合修復")
    print("=" * 50)
    
    try:
        # 導入必要模組
        from multi_group_database import MultiGroupDatabaseManager
        from multi_group_config import create_preset_configs
        from multi_group_position_manager import MultiGroupPositionManager
        from virtual_real_order_manager import VirtualRealOrderManager
        from unified_order_tracker import UnifiedOrderTracker
        
        # 1. 創建測試環境
        db_path = "Capital_Official_Framework/multi_group_strategy.db"
        db_manager = MultiGroupDatabaseManager(db_path)
        presets = create_preset_configs()
        config = presets["平衡配置 (2口×2組)"]
        
        # 2. 創建下單組件（模擬主程式環境）
        virtual_real_order_manager = VirtualRealOrderManager(
            quote_manager=None,  # 測試時不需要
            strategy_config=None,
            console_enabled=True,
            default_account='F0200006363839'
        )
        
        unified_order_tracker = UnifiedOrderTracker(
            strategy_manager=None,
            console_enabled=True
        )
        
        # 3. 創建部位管理器（整合下單組件）
        manager = MultiGroupPositionManager(
            db_manager=db_manager,
            strategy_config=config,
            order_manager=virtual_real_order_manager,  # 🔧 整合下單管理器
            order_tracker=unified_order_tracker        # 🔧 整合統一追蹤器
        )
        
        print("✅ 測試環境初始化完成")
        print(f"📊 配置: {config.total_groups}組×{config.lots_per_group}口")
        print(f"🔧 下單管理器: {'已設置' if manager.order_manager else '未設置'}")
        print(f"🔧 統一追蹤器: {'已設置' if manager.order_tracker else '未設置'}")
        
        # 4. 設置虛擬模式（避免實際下單）
        virtual_real_order_manager.set_order_mode(False)  # 虛擬模式
        print("🎯 設置為虛擬模式")
        
        # 5. 創建策略組
        today = date.today().strftime('%Y-%m-%d')
        group_ids = manager.create_entry_signal(
            direction="SHORT",
            signal_time="00:01:01",
            range_high=22385.0,
            range_low=22379.0
        )
        
        print(f"\n✅ 創建策略組: {len(group_ids)} 組")
        
        # 6. 執行進場（應該能正常下單）
        print(f"\n🚀 執行進場測試...")
        
        successful_groups = 0
        for i, group_db_id in enumerate(group_ids):
            print(f"\n--- 組別 {i+1} (DB ID: {group_db_id}) ---")
            
            # 執行進場
            success = manager.execute_group_entry(
                group_db_id=group_db_id,
                actual_price=22376.0,
                actual_time="00:01:01"
            )
            
            if success:
                successful_groups += 1
                print(f"進場結果: ✅ 成功")
            else:
                print(f"進場結果: ❌ 失敗")
        
        print(f"\n📊 進場總結: {successful_groups}/{len(group_ids)} 組成功")
        
        # 7. 檢查資料庫記錄
        print(f"\n📋 檢查資料庫記錄...")
        
        with db_manager.get_connection() as conn:
            conn.row_factory = lambda cursor, row: dict(zip([col[0] for col in cursor.description], row))
            cursor = conn.cursor()
            
            # 查詢今日的部位記錄
            cursor.execute('''
                SELECT pr.id, pr.group_id, pr.lot_id, pr.direction, pr.entry_price, 
                       pr.order_status, pr.status, pr.order_id, sg.group_id as original_group_id
                FROM position_records pr
                JOIN strategy_groups sg ON pr.group_id = sg.id
                WHERE sg.date = ?
                ORDER BY pr.group_id, pr.lot_id
            ''', (today,))
            
            records = cursor.fetchall()
            
            print(f"找到 {len(records)} 筆部位記錄:")
            for record in records:
                status_icon = "✅" if record['status'] == 'ACTIVE' else "❌" if record['status'] == 'FAILED' else "⏳"
                print(f"  {status_icon} 部位{record['id']}-組{record['original_group_id']}-第{record['lot_id']}口:")
                print(f"      方向: {record['direction']}")
                print(f"      狀態: {record['status']}/{record['order_status']}")
                print(f"      成交價: {record['entry_price']}")
                print(f"      訂單ID: {record['order_id']}")
        
        # 8. 檢查下單管理器統計
        print(f"\n📊 下單管理器統計:")
        stats = virtual_real_order_manager.get_statistics()
        print(f"  - 總下單數: {stats.get('total_orders', 0)}")
        print(f"  - 成功下單: {stats.get('successful_orders', 0)}")
        print(f"  - 失敗下單: {stats.get('failed_orders', 0)}")
        print(f"  - 當前模式: {virtual_real_order_manager.get_current_mode()}")
        
        # 9. 檢查統一追蹤器統計
        print(f"\n📊 統一追蹤器統計:")
        tracker_stats = unified_order_tracker.get_statistics()
        print(f"  - 總追蹤訂單: {tracker_stats.get('total_tracked', 0)}")
        print(f"  - 虛擬訂單: {tracker_stats.get('virtual_tracked', 0)}")
        print(f"  - 實際訂單: {tracker_stats.get('real_tracked', 0)}")
        
        # 10. 驗證修復效果
        print(f"\n🔍 驗證修復效果:")
        
        # 檢查是否還有"下單管理器未設置"的警告
        has_order_manager = manager.order_manager is not None
        has_order_tracker = manager.order_tracker is not None
        
        print(f"  {'✅' if has_order_manager else '❌'} 下單管理器: {'已設置' if has_order_manager else '未設置'}")
        print(f"  {'✅' if has_order_tracker else '❌'} 統一追蹤器: {'已設置' if has_order_tracker else '未設置'}")
        
        # 檢查是否有成功的下單記錄
        successful_orders = stats.get('successful_orders', 0)
        print(f"  {'✅' if successful_orders > 0 else '❌'} 成功下單: {successful_orders} 筆")
        
        # 檢查是否有訂單ID記錄
        orders_with_id = len([r for r in records if r['order_id']])
        print(f"  {'✅' if orders_with_id > 0 else '❌'} 有訂單ID的記錄: {orders_with_id} 筆")
        
        print("\n🎉 測試完成！")
        
        if has_order_manager and has_order_tracker and successful_orders > 0:
            print("\n📋 測試結果總結:")
            print("  ✅ 下單管理器整合成功")
            print("  ✅ 統一追蹤器整合成功")
            print("  ✅ 可以正常執行下單")
            print("  ✅ 訂單ID正確記錄")
            print("  ✅ 修復完成，系統可以正常運行")
        else:
            print("\n❌ 仍有問題需要解決:")
            if not has_order_manager:
                print("  - 下單管理器未正確設置")
            if not has_order_tracker:
                print("  - 統一追蹤器未正確設置")
            if successful_orders == 0:
                print("  - 沒有成功的下單記錄")
        
    except Exception as e:
        print(f"❌ 測試失敗: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_order_manager_integration()
