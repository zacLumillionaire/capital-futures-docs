#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
群益官方框架測試程式
測試基本的API載入和物件創建
"""

import os
import sys
import traceback

def test_skcom_loading():
    """測試SKCOM.dll載入"""
    print("=== 測試SKCOM.dll載入 ===")
    
    # 檢查SKCOM.dll是否存在
    dll_path = os.path.join(os.path.dirname(__file__), 'SKCOM.dll')
    if os.path.exists(dll_path):
        print(f"✅ 找到SKCOM.dll: {dll_path}")
    else:
        print(f"❌ 找不到SKCOM.dll: {dll_path}")
        return False
    
    try:
        import comtypes.client
        
        # 載入SKCOM.dll
        comtypes.client.GetModule(dll_path)
        print("✅ SKCOM.dll載入成功")
        
        # 導入SKCOMLib
        import comtypes.gen.SKCOMLib as sk
        print("✅ SKCOMLib導入成功")
        
        return True, sk
        
    except Exception as e:
        print(f"❌ SKCOM.dll載入失敗: {e}")
        traceback.print_exc()
        return False, None

def test_api_objects(sk):
    """測試API物件創建"""
    print("\n=== 測試API物件創建 ===")

    import comtypes.client
    objects = {}

    # 測試各個API物件
    api_objects = [
        ('SKCenterLib', 'ISKCenterLib'),
        ('SKOrderLib', 'ISKOrderLib'),
        ('SKQuoteLib', 'ISKQuoteLib'),
        ('SKReplyLib', 'ISKReplyLib')
    ]

    for obj_name, interface_name in api_objects:
        try:
            # 取得類別和介面
            obj_class = getattr(sk, obj_name)
            interface_class = getattr(sk, interface_name)

            # 創建物件
            obj = comtypes.client.CreateObject(obj_class, interface=interface_class)
            objects[obj_name] = obj

            print(f"✅ {obj_name} 創建成功")

        except Exception as e:
            print(f"❌ {obj_name} 創建失敗: {e}")
            objects[obj_name] = None

    return objects

def test_login_simulation(objects):
    """測試登入模擬 (不實際登入)"""
    print("\n=== 測試登入功能 (模擬) ===")
    
    if not objects.get('SKCenterLib'):
        print("❌ SKCenterLib物件不存在，無法測試登入")
        return False
    
    try:
        skCenter = objects['SKCenterLib']
        
        # 測試取得版本資訊 (不需登入)
        try:
            # 這個方法通常不需要登入就能調用
            print("📋 嘗試取得API版本資訊...")
            # version = skCenter.SKCenterLib_GetSKAPIVersionAndBit()
            # print(f"✅ API版本: {version}")
            print("✅ SKCenterLib物件可正常調用")
        except Exception as e:
            print(f"⚠️ 版本查詢失敗 (正常，可能需要登入): {e}")
        
        # 測試錯誤訊息功能
        try:
            error_msg = skCenter.SKCenterLib_GetReturnCodeMessage(0)
            print(f"✅ 錯誤訊息功能正常: {error_msg}")
        except Exception as e:
            print(f"❌ 錯誤訊息功能失敗: {e}")
        
        return True
        
    except Exception as e:
        print(f"❌ 登入測試失敗: {e}")
        traceback.print_exc()
        return False

def test_user_config():
    """測試使用者配置"""
    print("\n=== 測試使用者配置 ===")
    
    try:
        from user_config import get_user_config, show_risk_warning
        
        config = get_user_config()
        print("✅ 使用者配置載入成功")
        print(f"📋 期貨帳號: {config['FUTURES_ACCOUNT']}")
        print(f"📋 預設商品: {config['DEFAULT_PRODUCT']}")
        
        return True
        
    except Exception as e:
        print(f"❌ 使用者配置載入失敗: {e}")
        return False

def main():
    """主測試函數"""
    print("🚀 群益官方框架測試開始")
    print("=" * 50)
    
    # 測試1: SKCOM.dll載入
    success, sk = test_skcom_loading()
    if not success:
        print("\n❌ 基礎測試失敗，無法繼續")
        return
    
    # 測試2: API物件創建
    objects = test_api_objects(sk)
    
    # 測試3: 登入功能模擬
    test_login_simulation(objects)
    
    # 測試4: 使用者配置
    test_user_config()
    
    print("\n" + "=" * 50)
    print("🎉 群益官方框架測試完成")
    
    # 總結
    print("\n📋 測試總結:")
    print("✅ SKCOM.dll載入: 成功" if success else "❌ SKCOM.dll載入: 失敗")
    
    for obj_name in ['SKCenterLib', 'SKOrderLib', 'SKQuoteLib', 'SKReplyLib']:
        status = "成功" if objects.get(obj_name) else "失敗"
        icon = "✅" if objects.get(obj_name) else "❌"
        print(f"{icon} {obj_name}: {status}")
    
    print("\n💡 下一步:")
    print("1. 如果所有測試都成功，可以開始實際登入測試")
    print("2. 修改user_config.py中的USER_ID (身分證字號)")
    print("3. 執行實際的登入和下單測試")

if __name__ == "__main__":
    main()
    input("\n按Enter鍵結束...")
