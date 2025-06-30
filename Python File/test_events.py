#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
測試comtypes事件處理
"""

import os
import sys
import comtypes.client

def test_comtypes_events():
    """測試comtypes的事件處理功能"""
    print("🔍 測試comtypes事件處理功能...")
    
    try:
        # 生成COM元件的Python包裝
        print("🔄 生成COM元件包裝...")
        comtypes.client.GetModule(r'.\SKCOM.dll')
        
        # 導入生成的SKCOMLib
        print("🔄 導入SKCOMLib...")
        import comtypes.gen.SKCOMLib as sk
        
        # 建立SKReplyLib物件
        print("🔄 建立SKReplyLib物件...")
        m_pSKReply = comtypes.client.CreateObject(sk.SKReplyLib, interface=sk.ISKReplyLib)
        print("✅ SKReplyLib物件建立成功")
        
        # 測試事件處理
        print("🔄 測試事件處理...")
        
        # 建立事件處理類別
        class SKReplyLibEvent():
            def OnReplyMessage(self, bstrUserID, bstrMessages):
                print(f"📨 收到事件: {bstrUserID} - {bstrMessages}")
                return -1
        
        # 測試不同的GetEvents方式
        methods = [
            "comtypes.client.GetEvents",
            "直接導入GetEvents",
            "使用__import__",
            "檢查comtypes版本"
        ]
        
        for i, method in enumerate(methods, 1):
            print(f"\n🧪 方法{i}: {method}")
            
            try:
                if i == 1:
                    # 方法1: 直接使用
                    event_handler = comtypes.client.GetEvents(m_pSKReply, SKReplyLibEvent())
                    print("✅ 方法1成功")
                    break
                    
                elif i == 2:
                    # 方法2: 嘗試導入
                    from comtypes.client import GetEvents
                    event_handler = GetEvents(m_pSKReply, SKReplyLibEvent())
                    print("✅ 方法2成功")
                    break
                    
                elif i == 3:
                    # 方法3: 動態導入
                    comtypes_client = __import__('comtypes.client', fromlist=['GetEvents'])
                    GetEvents = getattr(comtypes_client, 'GetEvents')
                    event_handler = GetEvents(m_pSKReply, SKReplyLibEvent())
                    print("✅ 方法3成功")
                    break
                    
                elif i == 4:
                    # 方法4: 檢查comtypes版本和可用方法
                    print(f"   comtypes版本: {comtypes.__version__ if hasattr(comtypes, '__version__') else '未知'}")
                    print(f"   comtypes.client可用方法: {[attr for attr in dir(comtypes.client) if not attr.startswith('_')]}")
                    
                    # 檢查是否有GetEvents
                    if hasattr(comtypes.client, 'GetEvents'):
                        print("   ✅ GetEvents方法存在")
                        event_handler = comtypes.client.GetEvents(m_pSKReply, SKReplyLibEvent())
                        print("✅ 方法4成功")
                        break
                    else:
                        print("   ❌ GetEvents方法不存在")
                        
            except Exception as e:
                print(f"   ❌ 方法{i}失敗: {e}")
        
        print("\n🎯 事件處理測試完成")
        return True
        
    except Exception as e:
        print(f"❌ 測試失敗: {e}")
        return False

def check_comtypes_installation():
    """檢查comtypes安裝狀態"""
    print("\n🔍 檢查comtypes安裝狀態...")
    
    try:
        import comtypes
        print(f"✅ comtypes已安裝")
        print(f"   版本: {getattr(comtypes, '__version__', '未知')}")
        print(f"   路徑: {comtypes.__file__}")
        
        import comtypes.client
        print(f"✅ comtypes.client可用")
        
        # 列出可用方法
        methods = [attr for attr in dir(comtypes.client) if not attr.startswith('_')]
        print(f"   可用方法: {methods}")
        
        # 特別檢查GetEvents
        if 'GetEvents' in methods:
            print("   ✅ GetEvents方法可用")
        else:
            print("   ❌ GetEvents方法不可用")
            
        return True
        
    except Exception as e:
        print(f"❌ comtypes檢查失敗: {e}")
        return False

def main():
    """主函式"""
    print("🔍 comtypes事件處理測試工具")
    print("=" * 50)
    
    # 檢查comtypes
    if not check_comtypes_installation():
        return
    
    # 測試事件處理
    if not test_comtypes_events():
        return
    
    print("\n" + "=" * 50)
    print("🎯 測試完成")

if __name__ == "__main__":
    main()
