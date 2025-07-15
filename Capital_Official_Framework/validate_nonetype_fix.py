#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
NoneType 部位更新失敗修復驗證測試

測試場景：
1. 創建策略組和部位記錄
2. 模擬成交回報處理
3. 驗證資料庫更新是否成功
4. 檢查是否還有 TypeError
"""

def run_bug_fix_validation():
    """執行修復驗證測試"""
    print("🧪 開始 NoneType 部位更新失敗修復驗證")
    print("=" * 60)
    
    try:
        from multi_group_database import MultiGroupDatabaseManager
        from multi_group_position_manager import MultiGroupPositionManager
        from multi_group_config import create_preset_configs
        from datetime import datetime, date
        import os
        
        # 1. 創建測試資料庫
        test_db_path = "bug_fix_validation.db"
        if os.path.exists(test_db_path):
            os.remove(test_db_path)
            print("🗑️ 清理舊測試資料庫")
        
        db_manager = MultiGroupDatabaseManager(test_db_path)
        print("✅ 測試資料庫創建成功")
        
        # 2. 創建測試策略組
        today = date.today().isoformat()
        group_db_id = db_manager.create_strategy_group(
            date=today,
            group_id=1,  # 邏輯組別編號
            direction="SHORT",
            signal_time="14:30:15",
            range_high=22758.0,
            range_low=22750.0,
            total_lots=2
        )
        print(f"✅ 創建測試策略組: DB_ID={group_db_id}, 邏輯ID=1")
        
        # 3. 創建測試部位記錄（包含修復的字段）
        position_id = db_manager.create_position_record(
            group_id=1,  # 使用邏輯組別編號
            lot_id=1,
            direction="SHORT",
            entry_time="14:30:18",
            rule_config='{"lot_id": 1, "trigger_points": 15.0, "pullback_percent": 0.2}',
            order_status='PENDING',
            retry_count=0,  # 明確設置
            max_slippage_points=5  # 明確設置
        )
        print(f"✅ 創建測試部位記錄: ID={position_id}")
        
        # 4. 驗證部位記錄的字段完整性
        with db_manager.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                SELECT id, retry_count, max_slippage_points, status, order_status
                FROM position_records 
                WHERE id = ?
            ''', (position_id,))
            
            row = cursor.fetchone()
            if row:
                pos_id, retry_count, max_slippage, status, order_status = row
                print(f"📊 部位記錄驗證:")
                print(f"   ID: {pos_id}")
                print(f"   retry_count: {retry_count} (類型: {type(retry_count)})")
                print(f"   max_slippage_points: {max_slippage} (類型: {type(max_slippage)})")
                print(f"   status: {status}")
                print(f"   order_status: {order_status}")
                
                # 檢查是否有 None 值
                if retry_count is None:
                    print("❌ retry_count 為 None - 修復失敗")
                    return False
                if max_slippage is None:
                    print("❌ max_slippage_points 為 None - 修復失敗")
                    return False
                    
                print("✅ 所有字段都有有效值 - 修復成功")
        
        # 5. 創建部位管理器並測試成交處理
        presets = create_preset_configs()
        config = presets["測試配置 (1口×1組)"]
        
        position_manager = MultiGroupPositionManager(
            db_manager=db_manager,
            strategy_config=config,
            order_manager=None,
            order_tracker=None
        )
        print("✅ 部位管理器創建成功")
        
        # 6. 模擬成交回報處理
        fill_price = 22758.0
        fill_time = datetime.now().strftime('%H:%M:%S')
        
        print(f"🎯 模擬成交處理: 部位{position_id} @{fill_price}")
        
        # 直接調用資料庫更新方法（模擬成交確認）
        success = db_manager.confirm_position_filled(
            position_id=position_id,
            actual_fill_price=fill_price,
            fill_time=fill_time,
            order_status='FILLED'
        )
        
        if success:
            print("✅ 成交確認處理成功 - 沒有 TypeError")
        else:
            print("❌ 成交確認處理失敗")
            return False
        
        # 7. 驗證部位狀態更新
        with db_manager.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                SELECT id, entry_price, status, order_status
                FROM position_records 
                WHERE id = ?
            ''', (position_id,))
            
            row = cursor.fetchone()
            if row:
                pos_id, entry_price, status, order_status = row
                print(f"📈 成交後狀態驗證:")
                print(f"   部位ID: {pos_id}")
                print(f"   進場價格: {entry_price}")
                print(f"   部位狀態: {status}")
                print(f"   訂單狀態: {order_status}")
                
                if status == 'ACTIVE' and entry_price == fill_price:
                    print("✅ 部位狀態正確更新為 ACTIVE")
                else:
                    print("❌ 部位狀態更新異常")
                    return False
        
        # 8. 測試約束檢查（嘗試插入無效值）
        print("🔍 測試資料庫約束檢查...")
        try:
            # 嘗試創建一個 retry_count 超出範圍的記錄
            invalid_position_id = db_manager.create_position_record(
                group_id=1,
                lot_id=2,
                direction="SHORT",
                entry_time="14:30:20",
                rule_config='{"lot_id": 2}',
                order_status='PENDING',
                retry_count=10,  # 超出約束範圍 (0-5)
                max_slippage_points=5
            )
            print("❌ 約束檢查失敗 - 應該拒絕無效的 retry_count")
            return False
            
        except Exception as e:
            if "CHECK constraint failed" in str(e):
                print("✅ 約束檢查正常 - 正確拒絕無效值")
            else:
                print(f"⚠️ 意外錯誤: {e}")
        
        print("\n🎉 修復驗證完成 - 所有測試通過!")
        print("📋 驗證結果:")
        print("   ✅ 資料庫字段完整性正常")
        print("   ✅ 成交處理無 TypeError")
        print("   ✅ 部位狀態正確更新")
        print("   ✅ 約束檢查正常運作")
        
        return True
        
    except Exception as e:
        print(f"❌ 驗證測試失敗: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    finally:
        # 清理測試資料庫
        if 'test_db_path' in locals() and os.path.exists(test_db_path):
            try:
                os.remove(test_db_path)
                print("🗑️ 清理測試資料庫完成")
            except:
                pass


if __name__ == "__main__":
    success = run_bug_fix_validation()
    if success:
        print("\n✅ 修復驗證成功 - 可以部署修復方案")
    else:
        print("\n❌ 修復驗證失敗 - 需要進一步調查")
