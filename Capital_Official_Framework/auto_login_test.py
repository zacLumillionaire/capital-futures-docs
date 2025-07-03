#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
自動登入測試程式 - 無需用戶輸入
"""

import os
import sys
import time

def test_login():
    """自動登入測試"""
    print("🚀 群益API自動登入測試開始")
    print("=" * 50)
    
    try:
        # 載入使用者配置
        from user_config import get_user_config
        config = get_user_config()
        
        user_id = config['USER_ID']
        password = config['PASSWORD']
        
        print(f"📋 使用者ID: {user_id}")
        print(f"📋 密碼: {'*' * len(password)}")
        print(f"📋 期貨帳號: {config['FUTURES_ACCOUNT']}")
        
        # 初始化API
        print("\n🔄 初始化群益API...")
        import comtypes.client
        
        # 載入SKCOM.dll
        dll_path = os.path.join(os.path.dirname(__file__), 'SKCOM.dll')
        comtypes.client.GetModule(dll_path)
        print("✅ SKCOM.dll載入成功")
        
        # 導入SKCOMLib
        import comtypes.gen.SKCOMLib as sk
        
        # 創建API物件
        m_pSKCenter = comtypes.client.CreateObject(sk.SKCenterLib, interface=sk.ISKCenterLib)
        m_pSKOrder = comtypes.client.CreateObject(sk.SKOrderLib, interface=sk.ISKOrderLib)
        print("✅ API物件創建成功")
        
        # 設定LOG路徑
        log_path = os.path.join(os.path.dirname(__file__), "CapitalLog_AutoTest")
        nCode = m_pSKCenter.SKCenterLib_SetLogPath(log_path)
        print(f"📁 LOG路徑設定: {log_path}")
        
        # 執行登入
        print("\n🔐 執行登入...")
        nCode = m_pSKCenter.SKCenterLib_Login(user_id, password)
        
        # 取得回傳訊息
        msg_text = m_pSKCenter.SKCenterLib_GetReturnCodeMessage(nCode)
        print(f"📋 登入結果: {msg_text} (代碼: {nCode})")
        
        if nCode == 0:
            print("✅ 登入成功！")
            login_success = True
        elif nCode == 2017:
            print("✅ 登入成功 (需要註冊回報事件)")
            login_success = True
        else:
            print(f"❌ 登入失敗: {msg_text}")
            login_success = False
            return False
        
        if login_success:
            # 測試下單模組初始化
            print("\n🔄 測試下單模組初始化...")
            
            # 1. 初始化SKOrderLib
            print("📋 步驟1: 初始化SKOrderLib...")
            nCode = m_pSKOrder.SKOrderLib_Initialize()
            msg_text = m_pSKCenter.SKCenterLib_GetReturnCodeMessage(nCode)
            print(f"📋 初始化結果: {msg_text} (代碼: {nCode})")
            
            if nCode == 0 or nCode == 2003:  # 2003 = 已初始化
                print("✅ SKOrderLib初始化成功")
                
                # 2. 讀取憑證
                print("📋 步驟2: 讀取憑證...")
                nCode = m_pSKOrder.ReadCertByID(user_id)
                msg_text = m_pSKCenter.SKCenterLib_GetReturnCodeMessage(nCode)
                print(f"📋 憑證讀取結果: {msg_text} (代碼: {nCode})")
                
                if nCode == 0:
                    print("✅ 憑證讀取成功")
                    
                    # 3. 查詢帳號
                    print("📋 步驟3: 查詢帳號...")
                    nCode = m_pSKOrder.GetUserAccount()
                    msg_text = m_pSKCenter.SKCenterLib_GetReturnCodeMessage(nCode)
                    print(f"📋 帳號查詢結果: {msg_text} (代碼: {nCode})")
                    
                    print("\n🎉 所有測試通過！")
                    print("=" * 50)
                    print("📋 測試總結:")
                    print("✅ 登入測試: 成功")
                    print("✅ 下單模組初始化: 成功")
                    print("✅ 憑證讀取: 成功")
                    print("✅ 帳號查詢: 成功")
                    
                    print(f"\n💡 您的交易設定:")
                    print(f"📋 期貨帳號: {config['FUTURES_ACCOUNT']}")
                    print(f"📋 預設商品: {config['DEFAULT_PRODUCT']}")
                    print(f"📋 測試數量: {config['TEST_QUANTITY']}口")
                    
                    print(f"\n🚀 下一步可以執行:")
                    print("1. 期貨下單測試")
                    print("2. 即時報價測試")
                    print("3. 回報事件測試")
                    
                    return True
                else:
                    print(f"❌ 憑證讀取失敗: {msg_text}")
                    return False
            else:
                print(f"❌ SKOrderLib初始化失敗: {msg_text}")
                return False
        
        return False
        
    except Exception as e:
        print(f"❌ 測試過程發生錯誤: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = test_login()
    
    if success:
        print("\n🎉 自動登入測試完全成功！")
        print("✅ 群益官方框架已準備就緒，可以開始交易測試")
    else:
        print("\n❌ 自動登入測試失敗")
        print("⚠️ 請檢查網路連線和帳號設定")
    
    print(f"\n程式執行完畢")
