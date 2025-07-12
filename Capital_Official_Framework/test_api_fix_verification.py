# -*- coding: utf-8 -*-
"""
API修復驗證測試
測試修復後的實單模式切換功能

作者: API修復系統
日期: 2025-07-04
"""

import sys
import os

# 添加路徑
current_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.append(current_dir)
sys.path.append(os.path.join(current_dir, 'order_service'))

def test_global_module_fix():
    """測試Global模組修復"""
    print("🔧 測試Global模組修復...")
    
    try:
        import Global
        
        print(f"✅ Global模組載入成功")
        print(f"Global_IID初始值: {getattr(Global, 'Global_IID', '未定義')}")
        
        # 測試SetID函數
        test_user_id = "E123354882"
        Global.SetID(test_user_id)
        print(f"✅ SetID執行完成")
        print(f"Global_IID設定後: {Global.Global_IID}")
        
        return True
        
    except Exception as e:
        print(f"❌ Global模組測試失敗: {e}")
        return False

def test_virtual_real_manager_fix():
    """測試虛實單管理器修復"""
    print("\n🔧 測試虛實單管理器修復...")
    
    try:
        from virtual_real_order_manager import VirtualRealOrderManager
        
        # 創建管理器
        manager = VirtualRealOrderManager(console_enabled=True)
        
        print("\n📊 修復前狀態:")
        api_available = manager.check_api_availability()
        print(f"API可用性: {'✅ 可用' if api_available else '❌ 不可用'}")
        
        # 模擬登入
        print("\n🔐 模擬登入...")
        import Global
        Global.SetID("E123354882")
        
        print("\n📊 修復後狀態:")
        api_available = manager.check_api_availability()
        print(f"API可用性: {'✅ 可用' if api_available else '❌ 不可用'}")
        
        # 測試實單模式切換
        print("\n🔄 測試實單模式切換...")
        success = manager.set_order_mode(True)
        print(f"實單模式切換: {'✅ 成功' if success else '❌ 失敗'}")
        
        if success:
            print("🎉 修復成功！實單模式可以正常切換")
            # 切換回虛擬模式
            manager.set_order_mode(False)
            print("🔄 已切換回虛擬模式")
        else:
            print("❌ 修復未完全成功，仍無法切換實單模式")
        
        return success
        
    except Exception as e:
        print(f"❌ 虛實單管理器測試失敗: {e}")
        return False

def main():
    """主函數"""
    print("🚀 API修復驗證測試")
    print("=" * 50)
    
    # 測試1: Global模組修復
    global_ok = test_global_module_fix()
    
    # 測試2: 虛實單管理器修復
    manager_ok = test_virtual_real_manager_fix()
    
    # 總結
    print("\n" + "=" * 50)
    print("🎯 測試結果總結")
    print("=" * 50)
    print(f"Global模組修復: {'✅ 成功' if global_ok else '❌ 失敗'}")
    print(f"虛實單管理器修復: {'✅ 成功' if manager_ok else '❌ 失敗'}")
    
    if all([global_ok, manager_ok]):
        print("\n🎉 所有測試通過！實單模式切換功能已修復")
        print("💡 現在可以在simple_integrated.py中正常使用實單模式")
    else:
        print("\n⚠️ 部分測試失敗，需要進一步檢查")
    
    print("=" * 50)

if __name__ == "__main__":
    main()
