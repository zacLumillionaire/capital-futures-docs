# -*- coding: utf-8 -*-
"""
API診斷工具
用於檢查群益API的連線狀態和實單模式切換問題

作者: API診斷系統
日期: 2025-07-04
"""

import sys
import os

# 添加路徑
current_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.append(current_dir)
sys.path.append(os.path.join(current_dir, 'order_service'))

def check_global_module():
    """檢查Global模組狀態"""
    print("🔧 檢查Global模組狀態...")
    
    try:
        import Global
        print("✅ Global模組已載入")
        
        # 檢查API物件
        api_objects = ['skO', 'skC', 'skQ', 'skR']
        for obj_name in api_objects:
            if hasattr(Global, obj_name):
                obj = getattr(Global, obj_name)
                if obj is not None:
                    print(f"✅ Global.{obj_name}: 已初始化")
                else:
                    print(f"❌ Global.{obj_name}: 為None")
            else:
                print(f"❌ Global.{obj_name}: 不存在")
        
        # 檢查重要變數
        important_vars = ['Global_IID', 'UserAccount']
        for var_name in important_vars:
            if hasattr(Global, var_name):
                value = getattr(Global, var_name)
                print(f"✅ Global.{var_name}: {value}")
            else:
                print(f"❌ Global.{var_name}: 未設定")
                
        return True
        
    except ImportError as e:
        print(f"❌ Global模組載入失敗: {e}")
        return False
    except Exception as e:
        print(f"❌ Global模組檢查錯誤: {e}")
        return False

def check_virtual_real_manager():
    """檢查虛實單管理器狀態"""
    print("\n🔧 檢查虛實單管理器...")
    
    try:
        from virtual_real_order_manager import VirtualRealOrderManager
        
        # 創建管理器
        manager = VirtualRealOrderManager(console_enabled=True)
        
        # 檢查API可用性
        api_available = manager.check_api_availability()
        print(f"API可用性檢查: {'✅ 可用' if api_available else '❌ 不可用'}")
        
        # 嘗試切換實單模式
        print("\n🔄 測試實單模式切換...")
        success = manager.set_order_mode(True)
        print(f"實單模式切換: {'✅ 成功' if success else '❌ 失敗'}")
        
        if success:
            # 切換回虛擬模式
            manager.set_order_mode(False)
            print("🔄 已切換回虛擬模式")
        
        # 顯示統計
        print("\n📊 管理器統計:")
        stats = manager.get_statistics()
        for key, value in stats.items():
            print(f"  {key}: {value}")
            
        return manager
        
    except ImportError as e:
        print(f"❌ 虛實單管理器載入失敗: {e}")
        return None
    except Exception as e:
        print(f"❌ 虛實單管理器檢查錯誤: {e}")
        return None

def simulate_login():
    """模擬登入狀態"""
    print("\n🔧 模擬登入狀態...")
    
    try:
        import Global
        
        # 設定Global_IID (模擬登入)
        test_user_id = "E123354882"
        Global.SetID(test_user_id)
        print(f"✅ 已設定Global_IID: {Global.Global_IID}")
        
        # 設定UserAccount (如果需要)
        if not hasattr(Global, 'UserAccount'):
            Global.UserAccount = "F0200006363839"
            print(f"✅ 已設定UserAccount: {Global.UserAccount}")
        
        return True
        
    except Exception as e:
        print(f"❌ 模擬登入失敗: {e}")
        return False

def test_after_login():
    """測試登入後的API狀態"""
    print("\n🔧 測試登入後的API狀態...")
    
    # 重新檢查虛實單管理器
    manager = check_virtual_real_manager()
    
    if manager:
        print("\n🎯 登入後測試結果:")
        api_available = manager.check_api_availability()
        print(f"API可用性: {'✅ 可用' if api_available else '❌ 不可用'}")
        
        if api_available:
            print("🚀 嘗試切換到實單模式...")
            success = manager.set_order_mode(True)
            if success:
                print("✅ 實單模式切換成功！")
                manager.set_order_mode(False)
                print("🔄 已切換回虛擬模式")
            else:
                print("❌ 實單模式切換仍然失敗")

def main():
    """主函數"""
    print("🚀 群益API診斷工具")
    print("=" * 50)
    
    # 步驟1: 檢查Global模組
    global_ok = check_global_module()
    
    if not global_ok:
        print("\n❌ Global模組有問題，無法繼續診斷")
        return
    
    # 步驟2: 檢查虛實單管理器 (登入前)
    print("\n" + "=" * 50)
    print("📋 登入前狀態檢查")
    check_virtual_real_manager()
    
    # 步驟3: 模擬登入
    print("\n" + "=" * 50)
    print("🔐 模擬登入過程")
    login_ok = simulate_login()
    
    if login_ok:
        # 步驟4: 檢查登入後狀態
        print("\n" + "=" * 50)
        print("📋 登入後狀態檢查")
        test_after_login()
    
    print("\n" + "=" * 50)
    print("🎯 診斷完成")

if __name__ == "__main__":
    main()
