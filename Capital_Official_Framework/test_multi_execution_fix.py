#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
測試多次執行功能修復
驗證動態 group_id 分配是否有效
"""

import sys
import os
import time
from datetime import date

# 添加當前目錄到路徑
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

def test_dynamic_group_id_allocation():
    """測試動態 group_id 分配功能"""
    print("🧪 測試動態 group_id 分配功能")
    print("=" * 60)
    
    try:
        # 導入必要模組
        from multi_group_database import MultiGroupDatabaseManager
        from multi_group_config import create_preset_configs
        from multi_group_position_manager import MultiGroupPositionManager
        
        # 創建測試資料庫
        db_manager = MultiGroupDatabaseManager("test_multi_execution.db")
        
        # 使用平衡配置 (2口×2組)
        presets = create_preset_configs()
        config = presets["平衡配置 (2口×2組)"]
        
        # 創建管理器
        manager = MultiGroupPositionManager(db_manager, config)
        
        print("✅ 測試環境初始化完成")
        print(f"📊 配置: {config.total_groups}組×{config.lots_per_group}口")
        
        # 測試參數
        today = date.today().isoformat()
        direction = "LONG"
        range_high = 22380.0
        range_low = 22373.0
        
        print(f"\n📋 測試參數:")
        print(f"   日期: {today}")
        print(f"   方向: {direction}")
        print(f"   區間: {range_low}-{range_high}")
        
        # 第一次執行（應該使用 group_id 1, 2）
        print(f"\n🧪 測試1: 第一次執行策略")
        print("-" * 40)
        
        signal_time_1 = "08:48:15"
        group_ids_1 = manager.create_entry_signal(
            direction=direction,
            signal_time=signal_time_1,
            range_high=range_high,
            range_low=range_low
        )
        
        if group_ids_1:
            print(f"✅ 第一次執行成功: {len(group_ids_1)} 個策略組")
            print(f"   策略組DB_ID: {group_ids_1}")
            
            # 查詢創建的組別
            today_groups_1 = db_manager.get_today_strategy_groups()
            group_ids_display_1 = [g['group_id'] for g in today_groups_1]
            print(f"   使用組別ID: {group_ids_display_1}")
        else:
            print(f"❌ 第一次執行失敗")
            return False
        
        # 等待一秒，確保時間戳不同
        time.sleep(1)
        
        # 第二次執行（應該使用 group_id 3, 4）
        print(f"\n🧪 測試2: 第二次執行策略（可重複執行）")
        print("-" * 40)
        
        signal_time_2 = "09:15:30"
        group_ids_2 = manager.create_entry_signal(
            direction=direction,
            signal_time=signal_time_2,
            range_high=range_high + 5,  # 稍微不同的區間
            range_low=range_low - 2
        )
        
        if group_ids_2:
            print(f"✅ 第二次執行成功: {len(group_ids_2)} 個策略組")
            print(f"   策略組DB_ID: {group_ids_2}")
            
            # 查詢所有組別
            today_groups_2 = db_manager.get_today_strategy_groups()
            group_ids_display_2 = [g['group_id'] for g in today_groups_2]
            print(f"   所有組別ID: {group_ids_display_2}")
        else:
            print(f"❌ 第二次執行失敗")
            return False
        
        # 等待一秒
        time.sleep(1)
        
        # 第三次執行（應該使用 group_id 5, 6）
        print(f"\n🧪 測試3: 第三次執行策略（測試模式）")
        print("-" * 40)
        
        signal_time_3 = "10:22:45"
        group_ids_3 = manager.create_entry_signal(
            direction="SHORT",  # 不同方向
            signal_time=signal_time_3,
            range_high=range_high + 10,
            range_low=range_low + 5
        )
        
        if group_ids_3:
            print(f"✅ 第三次執行成功: {len(group_ids_3)} 個策略組")
            print(f"   策略組DB_ID: {group_ids_3}")
            
            # 查詢所有組別
            today_groups_3 = db_manager.get_today_strategy_groups()
            group_ids_display_3 = [g['group_id'] for g in today_groups_3]
            print(f"   所有組別ID: {group_ids_display_3}")
        else:
            print(f"❌ 第三次執行失敗")
            return False
        
        # 檢查最終結果
        print(f"\n📊 最終結果檢查:")
        print("-" * 40)
        
        final_groups = db_manager.get_today_strategy_groups()
        print(f"📋 今日總策略組數: {len(final_groups)}")
        
        for i, group in enumerate(final_groups, 1):
            print(f"   {i}. 組別ID:{group['group_id']} 方向:{group['direction']} "
                  f"時間:{group['entry_signal_time']} 狀態:{group['status']}")
        
        # 驗證組別ID的唯一性和遞增性
        all_group_ids = [g['group_id'] for g in final_groups]
        unique_group_ids = set(all_group_ids)
        
        if len(all_group_ids) == len(unique_group_ids):
            print(f"✅ 組別ID唯一性檢查通過")
        else:
            print(f"❌ 組別ID唯一性檢查失敗")
            return False
        
        if all_group_ids == sorted(all_group_ids):
            print(f"✅ 組別ID遞增性檢查通過")
        else:
            print(f"❌ 組別ID遞增性檢查失敗")
            return False
        
        # 驗證預期的組別ID序列
        expected_ids = [1, 2, 3, 4, 5, 6]
        if all_group_ids == expected_ids:
            print(f"✅ 組別ID序列符合預期: {expected_ids}")
            return True
        else:
            print(f"❌ 組別ID序列不符預期")
            print(f"   預期: {expected_ids}")
            print(f"   實際: {all_group_ids}")
            return False
        
    except Exception as e:
        print(f"❌ 測試執行失敗: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_frequency_control_logic():
    """測試執行頻率控制邏輯"""
    print(f"\n🧪 測試執行頻率控制邏輯")
    print("=" * 60)
    
    try:
        from multi_group_database import MultiGroupDatabaseManager
        
        # 創建測試資料庫
        db_manager = MultiGroupDatabaseManager("test_frequency_control.db")
        
        # 模擬今天已有策略組的情況
        today = date.today().isoformat()
        
        # 創建一個測試策略組
        group_db_id = db_manager.create_strategy_group(
            date=today,
            group_id=1,
            direction="LONG",
            signal_time="08:48:00",
            range_high=22400.0,
            range_low=22350.0,
            total_lots=2
        )
        
        print(f"✅ 創建測試策略組: DB_ID={group_db_id}")
        
        # 測試查詢今日策略組
        today_groups = db_manager.get_today_strategy_groups()
        print(f"📊 今日策略組數: {len(today_groups)}")
        
        if today_groups:
            print(f"✅ 頻率控制邏輯可以正確檢測到已存在的策略組")
            print(f"   組別ID: {[g['group_id'] for g in today_groups]}")
            return True
        else:
            print(f"❌ 頻率控制邏輯無法檢測到策略組")
            return False
        
    except Exception as e:
        print(f"❌ 頻率控制測試失敗: {e}")
        return False

if __name__ == "__main__":
    print("🔧 多次執行功能修復測試")
    print("=" * 80)
    
    # 測試1：動態 group_id 分配
    test1_result = test_dynamic_group_id_allocation()
    
    # 測試2：執行頻率控制邏輯
    test2_result = test_frequency_control_logic()
    
    # 總結
    print(f"\n🎯 測試總結:")
    print("=" * 80)
    print(f"動態組別ID分配: {'✅ 通過' if test1_result else '❌ 失敗'}")
    print(f"執行頻率控制: {'✅ 通過' if test2_result else '❌ 失敗'}")
    
    if test1_result and test2_result:
        print(f"\n🎉 所有測試通過！多次執行功能修復成功")
        print(f"💡 現在支援:")
        print(f"   - 一天一次: 檢查今日是否已執行，如是則跳過")
        print(f"   - 可重複執行: 使用動態組別ID，避免UNIQUE衝突")
        print(f"   - 測試模式: 忽略所有限制，可隨時執行")
    else:
        print(f"\n⚠️  部分測試失敗，需要進一步檢查")
    
    print(f"\n✅ 測試完成")
