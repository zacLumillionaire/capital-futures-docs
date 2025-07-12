#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
簡單測試動態 group_id 功能
"""

import sys
import os

# 添加當前目錄到路徑
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

def simple_test():
    """簡單測試"""
    print("🧪 簡單測試動態 group_id 功能")
    
    try:
        # 導入模組
        from multi_group_database import MultiGroupDatabaseManager
        from multi_group_config import create_preset_configs
        from multi_group_position_manager import MultiGroupPositionManager
        
        print("✅ 模組導入成功")
        
        # 創建資料庫
        db_manager = MultiGroupDatabaseManager("simple_test.db")
        print("✅ 資料庫創建成功")
        
        # 創建配置
        presets = create_preset_configs()
        config = presets["測試配置 (1口×1組)"]
        print("✅ 配置創建成功")
        
        # 創建管理器
        manager = MultiGroupPositionManager(db_manager, config)
        print("✅ 管理器創建成功")
        
        # 測試動態 group_id 方法
        group_ids = manager._get_next_available_group_ids(2)
        print(f"✅ 動態組別ID: {group_ids}")
        
        # 測試創建策略組
        created_groups = manager.create_entry_signal(
            direction="LONG",
            signal_time="18:30:00",
            range_high=22400.0,
            range_low=22350.0
        )
        print(f"✅ 創建策略組: {created_groups}")
        
        # 再次測試
        group_ids_2 = manager._get_next_available_group_ids(2)
        print(f"✅ 第二次動態組別ID: {group_ids_2}")
        
        return True
        
    except Exception as e:
        print(f"❌ 測試失敗: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    result = simple_test()
    print(f"測試結果: {'成功' if result else '失敗'}")
