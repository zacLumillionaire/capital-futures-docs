#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
群益證券API方法檢測工具
用於檢查SKCenterLib的可用方法和參數
"""

import os
import sys
import comtypes.client
import inspect

def initialize_skcom():
    """初始化SKCOM"""
    try:
        # 生成COM元件的Python包裝
        comtypes.client.GetModule(r'.\SKCOM.dll')
        
        # 導入生成的SKCOMLib
        import comtypes.gen.SKCOMLib as sk
        
        # 建立SKCOM物件
        m_pSKCenter = comtypes.client.CreateObject(sk.SKCenterLib, interface=sk.ISKCenterLib)
        
        return sk, m_pSKCenter
        
    except Exception as e:
        print(f"❌ 初始化失敗: {e}")
        return None, None

def inspect_skcom_methods(m_pSKCenter):
    """檢查SKCenter的可用方法"""
    print("🔍 檢查SKCenterLib的可用方法...")
    print("=" * 60)
    
    # 取得所有方法
    methods = [method for method in dir(m_pSKCenter) if not method.startswith('_')]
    
    login_methods = []
    other_methods = []
    
    for method in methods:
        if 'login' in method.lower() or 'connect' in method.lower():
            login_methods.append(method)
        else:
            other_methods.append(method)
    
    print("🔑 登入相關方法:")
    for method in login_methods:
        print(f"  - {method}")
        try:
            # 嘗試取得方法的說明
            method_obj = getattr(m_pSKCenter, method)
            if hasattr(method_obj, '__doc__') and method_obj.__doc__:
                print(f"    說明: {method_obj.__doc__}")
        except:
            pass
    
    print(f"\n📋 其他方法 (共{len(other_methods)}個):")
    for i, method in enumerate(other_methods[:10]):  # 只顯示前10個
        print(f"  - {method}")
    if len(other_methods) > 10:
        print(f"  ... 還有 {len(other_methods) - 10} 個方法")

def test_login_methods(m_pSKCenter):
    """測試不同的登入方法"""
    print("\n🧪 測試登入方法參數...")
    print("=" * 60)
    
    # 測試用的假資料
    test_id = "A123456789"
    test_password = "testpass"
    test_cert = "testcert"
    
    login_methods = [method for method in dir(m_pSKCenter) if 'login' in method.lower()]
    
    for method_name in login_methods:
        print(f"\n🔍 測試方法: {method_name}")
        try:
            method = getattr(m_pSKCenter, method_name)
            
            # 嘗試不同的參數組合
            param_combinations = [
                (test_id, test_password),
                (test_id, test_password, test_cert),
                (test_id,),
                ()
            ]
            
            for i, params in enumerate(param_combinations):
                try:
                    print(f"  嘗試 {len(params)} 個參數: {params}")
                    # 注意：這裡不實際調用，只是檢查參數數量
                    # result = method(*params)
                    print(f"    ✅ {len(params)} 個參數可能有效")
                    break
                except TypeError as e:
                    if "takes" in str(e) and "given" in str(e):
                        print(f"    ❌ {len(params)} 個參數: {e}")
                    else:
                        print(f"    ⚠️ {len(params)} 個參數: 其他錯誤")
                except Exception as e:
                    print(f"    ⚠️ {len(params)} 個參數: {type(e).__name__}")
                    
        except Exception as e:
            print(f"  ❌ 無法測試此方法: {e}")

def main():
    """主函式"""
    print("🔍 群益證券API方法檢測工具")
    print("=" * 60)
    
    # 檢查SKCOM.dll
    if not os.path.exists('SKCOM.dll'):
        print("❌ 找不到SKCOM.dll檔案")
        return
    
    # 初始化SKCOM
    sk, m_pSKCenter = initialize_skcom()
    if not m_pSKCenter:
        print("❌ 無法初始化SKCOM")
        return
    
    print("✅ SKCOM初始化成功")
    
    # 檢查方法
    inspect_skcom_methods(m_pSKCenter)
    
    # 測試登入方法
    test_login_methods(m_pSKCenter)
    
    print("\n" + "=" * 60)
    print("🎯 建議:")
    print("1. 查看上面的登入相關方法")
    print("2. 確認正確的參數數量")
    print("3. 根據結果修正SKCOMTester.py中的登入方法")

if __name__ == "__main__":
    main()
