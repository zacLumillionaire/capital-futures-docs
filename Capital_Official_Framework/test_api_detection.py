# -*- coding: utf-8 -*-
"""
API檢測修正測試
Test API Detection Fix

測試虛實單管理器的動態API檢測功能

作者: API檢測修正
日期: 2025-07-04
"""

import sys
import os

# 添加路徑以便導入模組
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

try:
    from virtual_real_order_manager import VirtualRealOrderManager
    print("✅ 虛實單管理器模組載入成功")
except ImportError as e:
    print(f"❌ 模組載入失敗: {e}")
    exit(1)

def test_api_detection():
    """測試API檢測功能"""
    print("🧪 測試API檢測功能...")
    
    # 創建管理器
    manager = VirtualRealOrderManager(console_enabled=True)
    
    print("\n📊 初始狀態:")
    manager.print_status()
    
    print("🔍 測試API可用性檢查:")
    api_available = manager.check_api_availability()
    print(f"API檢查結果: {'可用' if api_available else '不可用'}")
    
    print("\n🔄 測試模式切換:")
    
    # 測試切換到實單模式
    print("嘗試切換到實單模式...")
    success = manager.set_order_mode(True)
    print(f"切換結果: {'成功' if success else '失敗'}")
    
    # 測試切換回虛擬模式
    print("切換回虛擬模式...")
    success = manager.set_order_mode(False)
    print(f"切換結果: {'成功' if success else '失敗'}")
    
    print("\n📊 最終狀態:")
    manager.print_status()

def simulate_api_ready():
    """模擬API就緒狀態"""
    print("\n🔧 模擬API就緒狀態...")
    
    # 創建模擬的Global模組
    class MockGlobal:
        skO = "mock_order_object"
        UserAccount = "F0200006363839"
    
    # 將模擬模組添加到sys.modules
    sys.modules['Global'] = MockGlobal
    
    # 重新創建管理器
    manager = VirtualRealOrderManager(console_enabled=True)
    
    print("\n📊 模擬API就緒後的狀態:")
    manager.print_status()
    
    print("🔄 測試實單模式切換:")
    success = manager.set_order_mode(True)
    print(f"切換結果: {'成功' if success else '失敗'}")
    
    if success:
        print("✅ 實單模式切換成功！")
        # 切換回虛擬模式
        manager.set_order_mode(False)
    else:
        print("❌ 實單模式切換失敗")

def main():
    """主測試函數"""
    print("🚀 開始API檢測修正測試")
    print("="*50)
    
    # 測試當前狀態
    test_api_detection()
    
    # 模擬API就緒狀態
    simulate_api_ready()
    
    print("\n" + "="*50)
    print("✅ API檢測測試完成")
    
    print("\n💡 使用說明:")
    print("1. 如果API模組已載入但未就緒，請先登入系統")
    print("2. 登入成功後，API狀態會自動變為就緒")
    print("3. 就緒後即可切換到實單模式")

if __name__ == "__main__":
    main()
