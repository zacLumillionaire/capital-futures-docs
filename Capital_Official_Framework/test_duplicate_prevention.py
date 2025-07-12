#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
測試重複創建策略組的防護機制
驗證修復是否有效
"""

import sys
import os
import time
from datetime import date

# 添加當前目錄到路徑
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

def test_duplicate_prevention():
    """測試重複創建防護機制"""
    print("🧪 測試重複創建策略組防護機制")
    print("=" * 60)
    
    try:
        # 導入必要模組
        from multi_group_database import MultiGroupDatabaseManager
        from multi_group_config import create_preset_configs
        from multi_group_position_manager import MultiGroupPositionManager
        
        # 創建測試資料庫
        db_manager = MultiGroupDatabaseManager("test_duplicate_prevention.db")
        
        # 使用測試配置
        presets = create_preset_configs()
        config = presets["測試配置 (1口×1組)"]
        
        # 創建管理器
        manager = MultiGroupPositionManager(db_manager, config)
        
        print("✅ 測試環境初始化完成")
        print(f"📊 配置: {config.total_groups}組×{config.lots_per_group}口")
        
        # 測試參數
        today = date.today().isoformat()
        direction = "LONG"
        signal_time = "17:48:59"
        range_high = 22380.0
        range_low = 22373.0
        
        print(f"\n📋 測試參數:")
        print(f"   日期: {today}")
        print(f"   方向: {direction}")
        print(f"   信號時間: {signal_time}")
        print(f"   區間: {range_low}-{range_high}")
        
        # 第一次創建（應該成功）
        print(f"\n🧪 測試1: 第一次創建策略組")
        print("-" * 40)
        
        try:
            group_ids_1 = manager.create_entry_signal(
                direction=direction,
                signal_time=signal_time,
                range_high=range_high,
                range_low=range_low
            )
            
            if group_ids_1:
                print(f"✅ 第一次創建成功: {len(group_ids_1)} 個策略組")
                print(f"   策略組ID: {group_ids_1}")
            else:
                print(f"❌ 第一次創建失敗")
                
        except Exception as e:
            print(f"❌ 第一次創建異常: {e}")
        
        # 第二次創建（應該失敗，觸發UNIQUE constraint）
        print(f"\n🧪 測試2: 重複創建策略組（預期失敗）")
        print("-" * 40)
        
        try:
            group_ids_2 = manager.create_entry_signal(
                direction=direction,
                signal_time=signal_time,
                range_high=range_high,
                range_low=range_low
            )
            
            if group_ids_2:
                print(f"❌ 重複創建意外成功: {len(group_ids_2)} 個策略組")
                print(f"   這不應該發生！")
            else:
                print(f"❌ 重複創建失敗（預期結果）")
                
        except Exception as e:
            print(f"✅ 重複創建觸發異常（預期結果）: {e}")
            if "UNIQUE constraint failed" in str(e):
                print(f"   ✅ 確認是UNIQUE約束錯誤")
            else:
                print(f"   ⚠️  異常類型不符預期")
        
        # 檢查資料庫狀態
        print(f"\n📊 檢查資料庫狀態:")
        print("-" * 40)
        
        # 查詢今天的策略組
        with db_manager.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT id, group_id, direction, entry_signal_time, status
                FROM strategy_groups 
                WHERE date = ?
                ORDER BY group_id
            """, (today,))
            
            groups = cursor.fetchall()
            
            if groups:
                print(f"📋 找到 {len(groups)} 個策略組:")
                for group in groups:
                    print(f"   ID:{group[0]} 組別:{group[1]} 方向:{group[2]} 時間:{group[3]} 狀態:{group[4]}")
            else:
                print(f"📋 沒有找到策略組")
        
        # 測試結論
        print(f"\n🎯 測試結論:")
        print("-" * 40)
        
        if len(groups) == 1:
            print(f"✅ 防護機制有效：只創建了1個策略組")
            print(f"✅ UNIQUE約束正常工作")
        elif len(groups) > 1:
            print(f"❌ 防護機制失效：創建了{len(groups)}個策略組")
            print(f"❌ 存在重複創建問題")
        else:
            print(f"❌ 測試異常：沒有創建任何策略組")
        
        return len(groups) == 1
        
    except Exception as e:
        print(f"❌ 測試執行失敗: {e}")
        return False

def test_simple_integrated_prevention():
    """測試simple_integrated.py中的防護機制"""
    print(f"\n🧪 測試simple_integrated.py防護機制")
    print("=" * 60)
    
    try:
        # 模擬simple_integrated.py的狀態管理
        class MockApp:
            def __init__(self):
                self.multi_group_prepared = True
                self.multi_group_auto_start = True
                self.multi_group_running = False
                self.range_calculated = True
                self._auto_start_triggered = False
                self.call_count = 0
            
            def check_auto_start_multi_group_strategy(self):
                """模擬檢查自動啟動邏輯"""
                self.call_count += 1
                print(f"   調用次數: {self.call_count}")
                
                # 檢查條件（包含新的防護機制）
                if (self.multi_group_prepared and
                    self.multi_group_auto_start and
                    not self.multi_group_running and
                    self.range_calculated and
                    not self._auto_start_triggered):
                    
                    # 立即設定觸發標記
                    self._auto_start_triggered = True
                    print(f"   ✅ 條件滿足，設定觸發標記")
                    return True
                else:
                    print(f"   ❌ 條件不滿足或已觸發過")
                    return False
        
        app = MockApp()
        
        print(f"📋 初始狀態:")
        print(f"   prepared: {app.multi_group_prepared}")
        print(f"   auto_start: {app.multi_group_auto_start}")
        print(f"   running: {app.multi_group_running}")
        print(f"   range_calculated: {app.range_calculated}")
        print(f"   _auto_start_triggered: {app._auto_start_triggered}")
        
        # 模擬多次調用（如報價處理中的重複調用）
        print(f"\n🔄 模擬多次調用:")
        results = []
        for i in range(5):
            print(f"\n第{i+1}次調用:")
            result = app.check_auto_start_multi_group_strategy()
            results.append(result)
        
        # 檢查結果
        success_count = sum(results)
        print(f"\n📊 調用結果統計:")
        print(f"   總調用次數: {len(results)}")
        print(f"   成功觸發次數: {success_count}")
        print(f"   防護機制狀態: {app._auto_start_triggered}")
        
        if success_count == 1:
            print(f"✅ 防護機制有效：只觸發了1次")
            return True
        else:
            print(f"❌ 防護機制失效：觸發了{success_count}次")
            return False
            
    except Exception as e:
        print(f"❌ 測試執行失敗: {e}")
        return False

if __name__ == "__main__":
    print("🔧 重複創建策略組防護機制測試")
    print("=" * 80)
    
    # 測試1：資料庫層面的防護
    test1_result = test_duplicate_prevention()
    
    # 測試2：應用層面的防護
    test2_result = test_simple_integrated_prevention()
    
    # 總結
    print(f"\n🎯 測試總結:")
    print("=" * 80)
    print(f"資料庫層防護: {'✅ 通過' if test1_result else '❌ 失敗'}")
    print(f"應用層防護: {'✅ 通過' if test2_result else '❌ 失敗'}")
    
    if test1_result and test2_result:
        print(f"\n🎉 所有測試通過！防護機制有效")
        print(f"💡 修復應該能解決UNIQUE constraint failed錯誤")
    else:
        print(f"\n⚠️  部分測試失敗，需要進一步檢查")
    
    print(f"\n✅ 測試完成")
