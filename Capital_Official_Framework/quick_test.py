#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
快速測試程式
"""

import os
import sys

print("🚀 快速測試開始")

try:
    # 測試配置載入
    print("📋 測試配置載入...")
    from user_config import get_user_config
    config = get_user_config()
    print(f"✅ 使用者ID: {config['USER_ID']}")
    print(f"✅ 期貨帳號: {config['FUTURES_ACCOUNT']}")
    
    # 測試API載入
    print("📋 測試API載入...")
    import comtypes.client
    
    dll_path = os.path.join(os.path.dirname(__file__), 'SKCOM.dll')
    if os.path.exists(dll_path):
        print(f"✅ 找到SKCOM.dll: {dll_path}")
        
        # 載入DLL
        comtypes.client.GetModule(dll_path)
        print("✅ SKCOM.dll載入成功")
        
        # 導入SKCOMLib
        import comtypes.gen.SKCOMLib as sk
        print("✅ SKCOMLib導入成功")
        
        # 創建SKCenter物件
        m_pSKCenter = comtypes.client.CreateObject(sk.SKCenterLib, interface=sk.ISKCenterLib)
        print("✅ SKCenterLib創建成功")
        
        # 測試錯誤訊息功能
        error_msg = m_pSKCenter.SKCenterLib_GetReturnCodeMessage(0)
        print(f"✅ 錯誤訊息功能正常: {error_msg}")
        
        print("\n🎉 所有基礎測試通過！")
        print("💡 可以嘗試登入測試")
        
    else:
        print(f"❌ 找不到SKCOM.dll: {dll_path}")
        
except Exception as e:
    print(f"❌ 測試失敗: {e}")
    import traceback
    traceback.print_exc()

print("程式結束")
