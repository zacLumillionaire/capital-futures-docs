#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
SKCOM物件診斷工具
用於檢查SKCOM物件初始化狀態和可用方法
"""

import os
import sys
import comtypes.client

def check_skcom_dll():
    """檢查SKCOM.dll檔案"""
    print("🔍 檢查SKCOM.dll檔案...")
    print("=" * 50)
    
    dll_paths = [
        r'.\SKCOM.dll',
        r'SKCOM.dll',
        r'C:\SKCOM\SKCOM.dll',
        r'C:\Program Files (x86)\Capital\API\SKCOM.dll',
        r'C:\Program Files\Capital\API\SKCOM.dll'
    ]
    
    found_dll = None
    for path in dll_paths:
        if os.path.exists(path):
            found_dll = path
            print(f"✅ 找到SKCOM.dll: {path}")
            
            # 檢查檔案大小
            size = os.path.getsize(path)
            print(f"   檔案大小: {size:,} bytes")
            
            # 檢查修改時間
            import time
            mtime = os.path.getmtime(path)
            print(f"   修改時間: {time.ctime(mtime)}")
            break
        else:
            print(f"❌ 找不到: {path}")
    
    if not found_dll:
        print("❌ 找不到SKCOM.dll檔案")
        return False
    
    return found_dll

def initialize_skcom():
    """初始化SKCOM"""
    print("\n🔄 初始化SKCOM...")
    print("=" * 50)
    
    try:
        # 生成COM元件的Python包裝
        print("🔄 生成COM元件包裝...")
        comtypes.client.GetModule(r'.\SKCOM.dll')
        print("✅ COM元件包裝生成成功")
        
        # 導入生成的SKCOMLib
        print("🔄 導入SKCOMLib...")
        import comtypes.gen.SKCOMLib as sk
        print("✅ SKCOMLib導入成功")
        
        return sk
        
    except Exception as e:
        print(f"❌ SKCOM初始化失敗: {e}")
        return None

def test_object_creation(sk):
    """測試物件建立"""
    print("\n🧪 測試物件建立...")
    print("=" * 50)
    
    objects_to_test = [
        ('SKReplyLib', 'ISKReplyLib'),
        ('SKCenterLib', 'ISKCenterLib'),
        ('SKOrderLib', 'ISKOrderLib'),
        ('SKQuoteLib', 'ISKQuoteLib')
    ]
    
    created_objects = {}
    
    for obj_name, interface_name in objects_to_test:
        try:
            print(f"🔄 建立{obj_name}...")
            
            # 取得類別和介面
            obj_class = getattr(sk, obj_name)
            interface = getattr(sk, interface_name)
            
            # 建立物件
            obj = comtypes.client.CreateObject(obj_class, interface=interface)
            created_objects[obj_name] = obj
            
            print(f"✅ {obj_name}建立成功")
            
            # 檢查可用方法
            methods = [method for method in dir(obj) if not method.startswith('_')]
            print(f"   可用方法數量: {len(methods)}")
            
            # 顯示前5個方法
            if methods:
                print(f"   前5個方法: {', '.join(methods[:5])}")
            
        except Exception as e:
            print(f"❌ {obj_name}建立失敗: {e}")
            created_objects[obj_name] = None
    
    return created_objects

def test_login_method(objects):
    """測試登入方法"""
    print("\n🔍 檢查登入方法...")
    print("=" * 50)
    
    sk_center = objects.get('SKCenterLib')
    if sk_center is None:
        print("❌ SKCenterLib物件不存在，無法測試登入方法")
        return
    
    # 檢查登入相關方法
    login_methods = [method for method in dir(sk_center) if 'login' in method.lower()]
    
    print(f"🔍 找到{len(login_methods)}個登入相關方法:")
    for method in login_methods:
        print(f"   - {method}")
    
    # 檢查SKCenterLib_Login方法
    if hasattr(sk_center, 'SKCenterLib_Login'):
        print("✅ SKCenterLib_Login方法存在")
        
        # 嘗試檢查方法簽名（這可能會失敗，但值得一試）
        try:
            import inspect
            sig = inspect.signature(sk_center.SKCenterLib_Login)
            print(f"   方法簽名: {sig}")
        except:
            print("   無法取得方法簽名")
    else:
        print("❌ SKCenterLib_Login方法不存在")
    
    # 檢查GetReturnCodeMessage方法
    if hasattr(sk_center, 'SKCenterLib_GetReturnCodeMessage'):
        print("✅ SKCenterLib_GetReturnCodeMessage方法存在")
    else:
        print("❌ SKCenterLib_GetReturnCodeMessage方法不存在")

def main():
    """主函式"""
    print("🔍 SKCOM物件診斷工具")
    print("=" * 50)
    
    # 檢查DLL檔案
    dll_path = check_skcom_dll()
    if not dll_path:
        print("\n❌ 診斷失敗：找不到SKCOM.dll")
        return
    
    # 初始化SKCOM
    sk = initialize_skcom()
    if not sk:
        print("\n❌ 診斷失敗：SKCOM初始化失敗")
        return
    
    # 測試物件建立
    objects = test_object_creation(sk)
    
    # 測試登入方法
    test_login_method(objects)
    
    print("\n" + "=" * 50)
    print("🎯 診斷完成")
    
    # 總結
    success_count = sum(1 for obj in objects.values() if obj is not None)
    total_count = len(objects)
    
    print(f"📊 物件建立成功率: {success_count}/{total_count}")
    
    if success_count == total_count:
        print("✅ 所有SKCOM物件都可以正常建立")
    else:
        print("⚠️ 部分SKCOM物件建立失敗")
        failed_objects = [name for name, obj in objects.items() if obj is None]
        print(f"   失敗的物件: {', '.join(failed_objects)}")

if __name__ == "__main__":
    main()
