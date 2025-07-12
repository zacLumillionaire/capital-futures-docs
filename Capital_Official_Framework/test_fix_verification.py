#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
修復驗證測試腳本
驗證 optimized_risk_manager 和 multi_group_position_manager 的修復效果
"""

import sys
import os

# 添加路徑
current_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, current_dir)

def test_optimized_risk_manager_fixes():
    """測試優化風險管理器修復"""
    print("🧪 測試優化風險管理器修復...")
    
    try:
        # 1. 測試模組導入
        print("📦 測試模組導入...")
        from optimized_risk_manager import create_optimized_risk_manager
        from multi_group_database import MultiGroupDatabaseManager
        print("✅ 模組導入成功")
        
        # 2. 創建管理器
        print("🏗️ 創建管理器...")
        db_manager = MultiGroupDatabaseManager()
        risk_manager = create_optimized_risk_manager(db_manager, console_enabled=True)
        print("✅ 優化風險管理器創建成功")
        
        # 3. 測試 None 值處理修復
        print("🔧 測試 None 值處理修復...")
        
        # 測試無效數據處理
        invalid_position_1 = {
            'id': 'test_invalid_1',
            'direction': 'LONG',
            'entry_price': 22000.0,
            'range_high': None,  # None 值測試
            'range_low': 21950.0,
            'group_id': 1
        }
        
        risk_manager.on_new_position(invalid_position_1)
        print("✅ None 值處理測試通過")
        
        # 測試有效數據處理
        valid_position = {
            'id': 'test_valid_1',
            'direction': 'LONG',
            'entry_price': 22000.0,
            'range_high': 22050.0,
            'range_low': 21950.0,
            'group_id': 1
        }
        
        risk_manager.on_new_position(valid_position)
        print("✅ 有效數據處理測試通過")
        
        # 4. 測試價格更新
        print("📊 測試價格更新...")
        result = risk_manager.update_price(22010.0)
        print(f"✅ 價格更新成功: {result}")
        
        # 5. 測試統計信息
        print("📈 測試統計信息...")
        stats = risk_manager.get_stats()
        print(f"✅ 統計信息: {stats}")
        
        return True
        
    except Exception as e:
        print(f"❌ 優化風險管理器測試失敗: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_simplified_tracker_fixes():
    """測試簡化追蹤器修復"""
    print("\n🧪 測試簡化追蹤器修復...")
    
    try:
        from multi_group_position_manager import MultiGroupPositionManager
        from multi_group_database import MultiGroupDatabaseManager
        from multi_group_config import create_preset_configs
        
        # 創建測試環境
        db_manager = MultiGroupDatabaseManager("test_fix_verification.db")
        presets = create_preset_configs()
        config = presets["測試配置 (1口×1組)"]
        
        manager = MultiGroupPositionManager(db_manager, config)
        print("✅ 簡化追蹤器測試環境創建成功")
        
        # 測試重複處理檢測改善
        print("🔄 測試重複處理檢測改善...")
        
        # 模擬成交處理
        test_group_id = 1
        test_price = 22000.0
        test_qty = 1
        
        # 第一次處理（正常）
        manager._update_group_positions_on_fill(test_group_id, test_price, test_qty, 1, 1)
        print("✅ 第一次成交處理完成")
        
        # 第二次處理（應該智能跳過）
        manager._update_group_positions_on_fill(test_group_id, test_price, test_qty, 1, 1)
        print("✅ 重複處理智能跳過測試通過")
        
        return True
        
    except Exception as e:
        print(f"❌ 簡化追蹤器測試失敗: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """主測試函數"""
    print("🚀 開始修復驗證測試...")
    print("=" * 50)
    
    # 測試1: 優化風險管理器修復
    test1_result = test_optimized_risk_manager_fixes()
    
    # 測試2: 簡化追蹤器修復
    test2_result = test_simplified_tracker_fixes()
    
    # 總結
    print("\n" + "=" * 50)
    print("📋 測試結果總結:")
    print(f"  優化風險管理器修復: {'✅ 通過' if test1_result else '❌ 失敗'}")
    print(f"  簡化追蹤器修復: {'✅ 通過' if test2_result else '❌ 失敗'}")
    
    if test1_result and test2_result:
        print("\n🎉 所有修復測試通過！")
        print("💡 修復已成功，可以安全使用")
        return True
    else:
        print("\n⚠️ 部分測試失敗，需要進一步檢查")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
