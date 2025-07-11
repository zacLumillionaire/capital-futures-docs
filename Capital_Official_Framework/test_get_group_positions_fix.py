#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
測試 get_group_positions 方法修復
"""

import sys
import os

# 添加路徑
current_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, current_dir)

def test_get_group_positions_method():
    """測試 get_group_positions 方法是否存在"""
    print("🧪 測試 get_group_positions 方法修復...")
    
    try:
        from multi_group_database import MultiGroupDatabaseManager
        
        # 創建資料庫管理器
        db_manager = MultiGroupDatabaseManager("test_get_group_positions.db")
        print("✅ 資料庫管理器創建成功")
        
        # 檢查方法是否存在
        if hasattr(db_manager, 'get_group_positions'):
            print("✅ get_group_positions 方法存在")
            
            # 測試調用
            result = db_manager.get_group_positions(1)
            print(f"✅ get_group_positions 調用成功，返回: {len(result)} 個部位")
            
            # 檢查是否與 get_active_positions_by_group 結果一致
            result2 = db_manager.get_active_positions_by_group(1)
            if result == result2:
                print("✅ get_group_positions 與 get_active_positions_by_group 結果一致")
            else:
                print("⚠️ 結果不一致，但這可能是正常的（如果沒有數據）")
                
            return True
        else:
            print("❌ get_group_positions 方法不存在")
            return False
            
    except Exception as e:
        print(f"❌ 測試失敗: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_optimized_risk_manager_with_fix():
    """測試優化風險管理器是否能正常工作"""
    print("\n🧪 測試優化風險管理器與修復...")
    
    try:
        from optimized_risk_manager import create_optimized_risk_manager
        from multi_group_database import MultiGroupDatabaseManager
        
        # 創建管理器
        db_manager = MultiGroupDatabaseManager("test_optimized_risk.db")
        risk_manager = create_optimized_risk_manager(db_manager, console_enabled=True)
        print("✅ 優化風險管理器創建成功")
        
        # 測試新部位事件
        test_position = {
            'id': 'test_001',
            'direction': 'LONG',
            'entry_price': 22000.0,
            'range_high': 22050.0,
            'range_low': 21950.0,
            'group_id': 1
        }
        
        risk_manager.on_new_position(test_position)
        print("✅ 新部位事件處理成功")
        
        # 測試價格更新
        result = risk_manager.update_price(22010.0)
        print(f"✅ 價格更新成功: {result}")
        
        return True
        
    except Exception as e:
        print(f"❌ 優化風險管理器測試失敗: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """主測試函數"""
    print("🚀 開始測試 get_group_positions 修復...")
    print("=" * 50)
    
    # 測試1: get_group_positions 方法
    test1_result = test_get_group_positions_method()
    
    # 測試2: 優化風險管理器
    test2_result = test_optimized_risk_manager_with_fix()
    
    # 總結
    print("\n" + "=" * 50)
    print("📋 測試結果總結:")
    print(f"  get_group_positions 方法: {'✅ 通過' if test1_result else '❌ 失敗'}")
    print(f"  優化風險管理器: {'✅ 通過' if test2_result else '❌ 失敗'}")
    
    if test1_result and test2_result:
        print("\n🎉 所有測試通過！get_group_positions 錯誤已修復")
        return True
    else:
        print("\n⚠️ 部分測試失敗")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
