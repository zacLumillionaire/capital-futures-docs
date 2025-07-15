#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
測試組別ID修復的簡單腳本
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

def test_group_id_fix():
    """測試組別ID查找修復"""
    try:
        print("🔧 測試組別ID查找修復...")
        
        # 導入必要模組
        from multi_group_database import MultiGroupDatabaseManager
        from multi_group_config import create_preset_configs
        from multi_group_position_manager import MultiGroupPositionManager
        from datetime import date
        
        print("✅ 模組導入成功")
        
        # 創建測試資料庫
        db_manager = MultiGroupDatabaseManager("test_group_fix.db")
        print("✅ 資料庫創建成功")
        
        # 創建配置
        presets = create_preset_configs()
        config = presets["測試配置 (1口×1組)"]
        print("✅ 配置創建成功")
        
        # 創建管理器
        manager = MultiGroupPositionManager(db_manager, config)
        print("✅ 管理器創建成功")
        
        # 測試創建策略組
        print("\n🧪 測試創建策略組...")
        created_groups = manager.create_entry_signal(
            direction="LONG",
            signal_time="20:30:00",
            range_high=22900.0,
            range_low=22850.0
        )
        print(f"✅ 創建策略組: {created_groups}")
        
        # 測試查找組別DB ID
        print("\n🔍 測試查找組別DB ID...")
        
        # 獲取今日策略組
        today_groups = db_manager.get_today_strategy_groups()
        print(f"📊 今日策略組數量: {len(today_groups)}")
        
        if today_groups:
            group = today_groups[0]
            print(f"📋 第一個組的字段: {list(group.keys())}")
            print(f"📋 組詳細信息: {group}")
            
            # 測試修復後的查找邏輯
            group_id = group['logical_group_id']
            group_pk = group['group_pk']
            
            print(f"\n🎯 測試查找邏輯:")
            print(f"   邏輯組ID: {group_id}")
            print(f"   主鍵ID: {group_pk}")
            
            # 模擬修復後的查找邏輯
            found_pk = None
            for g in today_groups:
                if g['logical_group_id'] == group_id:
                    found_pk = g['group_pk']
                    break
            
            if found_pk:
                print(f"✅ 查找成功: 組{group_id} -> DB_ID={found_pk}")
            else:
                print(f"❌ 查找失敗: 找不到組{group_id}")
        else:
            print("⚠️ 沒有找到今日策略組")
        
        print("\n🎉 測試完成!")
        
    except Exception as e:
        print(f"❌ 測試失敗: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_group_id_fix()
