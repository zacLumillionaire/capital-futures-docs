#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
簡單的群益API測試
"""

import os
import sys

def test_basic_import():
    """測試基本導入"""
    print("🔄 測試基本導入...")
    
    try:
        import comtypes.client
        print("✅ comtypes.client 導入成功")
        
        # 檢查SKCOM.dll
        dll_path = os.path.join(os.path.dirname(__file__), 'SKCOM.dll')
        if os.path.exists(dll_path):
            print(f"✅ 找到SKCOM.dll: {dll_path}")
        else:
            print(f"❌ 找不到SKCOM.dll: {dll_path}")
            return False
        
        # 載入SKCOM.dll
        comtypes.client.GetModule(dll_path)
        print("✅ SKCOM.dll載入成功")
        
        # 導入SKCOMLib
        import comtypes.gen.SKCOMLib as sk
        print("✅ SKCOMLib導入成功")
        
        # 測試創建SKCenterLib
        m_pSKCenter = comtypes.client.CreateObject(sk.SKCenterLib, interface=sk.ISKCenterLib)
        print("✅ SKCenterLib創建成功")
        
        # 測試錯誤訊息功能
        error_msg = m_pSKCenter.SKCenterLib_GetReturnCodeMessage(0)
        print(f"✅ 錯誤訊息功能正常: {error_msg}")
        
        return True
        
    except Exception as e:
        print(f"❌ 測試失敗: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_order_service():
    """測試order_service導入"""
    print("\n🔄 測試order_service導入...")
    
    try:
        # 切換到order_service目錄
        order_service_path = os.path.join(os.path.dirname(__file__), 'order_service')
        if order_service_path not in sys.path:
            sys.path.insert(0, order_service_path)
        
        # 嘗試導入Global模組
        import Global
        print("✅ order_service/Global.py 導入成功")
        
        # 檢查全域物件
        if hasattr(Global, 'skC'):
            print("✅ skC (SKCenterLib) 物件存在")
        if hasattr(Global, 'skO'):
            print("✅ skO (SKOrderLib) 物件存在")
        if hasattr(Global, 'skQ'):
            print("✅ skQ (SKQuoteLib) 物件存在")
        if hasattr(Global, 'skR'):
            print("✅ skR (SKReplyLib) 物件存在")
        
        return True
        
    except Exception as e:
        print(f"❌ order_service測試失敗: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """主測試函數"""
    print("🚀 群益API簡單測試開始")
    print("=" * 40)
    
    # 測試1: 基本導入
    success1 = test_basic_import()
    
    # 測試2: order_service
    success2 = test_order_service()
    
    print("\n" + "=" * 40)
    print("📋 測試結果:")
    print(f"{'✅' if success1 else '❌'} 基本API測試: {'成功' if success1 else '失敗'}")
    print(f"{'✅' if success2 else '❌'} order_service測試: {'成功' if success2 else '失敗'}")
    
    if success1 and success2:
        print("\n🎉 所有測試通過！群益官方框架可以使用")
        print("\n💡 下一步:")
        print("1. 修改user_config.py中的USER_ID")
        print("2. 執行實際登入測試")
        print("3. 測試期貨下單功能")
    else:
        print("\n❌ 部分測試失敗，需要檢查環境設定")

if __name__ == "__main__":
    main()
    input("\n按Enter鍵結束...")
