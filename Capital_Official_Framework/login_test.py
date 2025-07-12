#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
群益API登入測試程式
使用您的帳號進行實際登入測試
"""

import os
import sys
import time

def initialize_api():
    """初始化API"""
    print("🔄 初始化群益API...")
    
    try:
        import comtypes.client
        
        # 載入SKCOM.dll
        dll_path = os.path.join(os.path.dirname(__file__), 'SKCOM.dll')
        comtypes.client.GetModule(dll_path)
        
        # 導入SKCOMLib
        import comtypes.gen.SKCOMLib as sk
        
        # 創建API物件
        m_pSKCenter = comtypes.client.CreateObject(sk.SKCenterLib, interface=sk.ISKCenterLib)
        m_pSKOrder = comtypes.client.CreateObject(sk.SKOrderLib, interface=sk.ISKOrderLib)
        m_pSKQuote = comtypes.client.CreateObject(sk.SKQuoteLib, interface=sk.ISKQuoteLib)
        m_pSKReply = comtypes.client.CreateObject(sk.SKReplyLib, interface=sk.ISKReplyLib)
        
        print("✅ API物件初始化成功")
        
        return {
            'SKCenter': m_pSKCenter,
            'SKOrder': m_pSKOrder,
            'SKQuote': m_pSKQuote,
            'SKReply': m_pSKReply
        }
        
    except Exception as e:
        print(f"❌ API初始化失敗: {e}")
        return None

def test_login(api_objects, user_id, password):
    """測試登入功能"""
    print(f"\n🔄 測試登入功能...")
    print(f"📋 使用者ID: {user_id}")
    print(f"📋 密碼: {'*' * len(password)}")
    
    try:
        m_pSKCenter = api_objects['SKCenter']
        
        # 設定LOG路徑
        log_path = os.path.join(os.path.dirname(__file__), "CapitalLog_Test")
        nCode = m_pSKCenter.SKCenterLib_SetLogPath(log_path)
        print(f"📁 LOG路徑設定: {log_path} (代碼: {nCode})")
        
        # 執行登入
        print("🔐 執行登入...")
        nCode = m_pSKCenter.SKCenterLib_Login(user_id, password)
        
        # 取得回傳訊息
        msg_text = m_pSKCenter.SKCenterLib_GetReturnCodeMessage(nCode)
        print(f"📋 登入結果: {msg_text} (代碼: {nCode})")
        
        if nCode == 0:
            print("✅ 登入成功！")
            return True
        elif nCode == 2017:
            print("⚠️ 登入成功但需要註冊回報事件")
            return True
        else:
            print(f"❌ 登入失敗: {msg_text}")
            return False
            
    except Exception as e:
        print(f"❌ 登入過程發生錯誤: {e}")
        return False

def test_order_initialization(api_objects, user_id):
    """測試下單模組初始化"""
    print(f"\n🔄 測試下單模組初始化...")
    
    try:
        m_pSKOrder = api_objects['SKOrder']
        m_pSKCenter = api_objects['SKCenter']
        
        # 1. 初始化SKOrderLib
        print("📋 步驟1: 初始化SKOrderLib...")
        nCode = m_pSKOrder.SKOrderLib_Initialize()
        msg_text = m_pSKCenter.SKCenterLib_GetReturnCodeMessage(nCode)
        print(f"📋 初始化結果: {msg_text} (代碼: {nCode})")
        
        if nCode != 0 and nCode != 2003:  # 2003 = 已初始化
            print(f"❌ SKOrderLib初始化失敗")
            return False
        
        # 2. 讀取憑證
        print("📋 步驟2: 讀取憑證...")
        nCode = m_pSKOrder.ReadCertByID(user_id)
        msg_text = m_pSKCenter.SKCenterLib_GetReturnCodeMessage(nCode)
        print(f"📋 憑證讀取結果: {msg_text} (代碼: {nCode})")
        
        if nCode != 0:
            print(f"❌ 憑證讀取失敗")
            return False
        
        # 3. 查詢帳號
        print("📋 步驟3: 查詢帳號...")
        nCode = m_pSKOrder.GetUserAccount()
        msg_text = m_pSKCenter.SKCenterLib_GetReturnCodeMessage(nCode)
        print(f"📋 帳號查詢結果: {msg_text} (代碼: {nCode})")
        
        print("✅ 下單模組初始化成功！")
        return True
        
    except Exception as e:
        print(f"❌ 下單模組初始化失敗: {e}")
        return False

def main():
    """主測試函數"""
    print("🚀 群益API登入測試開始")
    print("=" * 50)
    
    # 載入使用者配置
    try:
        from user_config import get_user_config
        config = get_user_config()
        
        # 檢查是否已設定USER_ID
        if not config['USER_ID']:
            print("❌ 請先在user_config.py中設定您的身分證字號 (USER_ID)")
            print("📝 範例: USER_ID = 'A123456789'")
            input("按Enter鍵結束...")
            return
        
        user_id = config['USER_ID']
        password = config['PASSWORD']
        
    except Exception as e:
        print(f"❌ 載入使用者配置失敗: {e}")
        return
    
    # 初始化API
    api_objects = initialize_api()
    if not api_objects:
        print("❌ API初始化失敗，無法繼續測試")
        return
    
    # 測試登入
    login_success = test_login(api_objects, user_id, password)
    
    if login_success:
        # 測試下單模組初始化
        order_success = test_order_initialization(api_objects, user_id)
        
        print("\n" + "=" * 50)
        print("📋 測試總結:")
        print(f"✅ 登入測試: {'成功' if login_success else '失敗'}")
        print(f"✅ 下單模組: {'成功' if order_success else '失敗'}")
        
        if login_success and order_success:
            print("\n🎉 所有測試通過！可以開始使用群益API進行交易")
            print(f"📋 您的期貨帳號: {config['FUTURES_ACCOUNT']}")
            print(f"📋 預設商品: {config['DEFAULT_PRODUCT']}")
            
            print("\n💡 下一步:")
            print("1. 測試期貨下單功能")
            print("2. 測試即時報價訂閱")
            print("3. 測試回報事件處理")
        else:
            print("\n❌ 部分測試失敗，請檢查設定")
    else:
        print("\n❌ 登入失敗，請檢查帳號密碼")
    
    input("\n按Enter鍵結束...")

if __name__ == "__main__":
    main()
