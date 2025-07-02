#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
非同步下單事件測試腳本
檢查 OnAsyncOrder 事件是否正確設置
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

def test_async_order_event_setup():
    """測試 OnAsyncOrder 事件設置"""
    print("🧪 測試 OnAsyncOrder 事件設置...")
    
    try:
        from order.future_order import OrderExecutor
        
        # 模擬SKCOM物件
        class MockSKOrder:
            def __init__(self):
                self.OnAsyncOrder = None
                self.event_set = False
            
            def __setattr__(self, name, value):
                if name == 'OnAsyncOrder':
                    print(f"✅ OnAsyncOrder 事件已設置: {value}")
                    self.event_set = True
                super().__setattr__(name, value)
        
        mock_skcom = {
            'SKOrder': MockSKOrder(),
            'SKCenter': None,
            'SKQuote': None
        }
        
        # 創建OrderExecutor實例
        def mock_add_message(msg):
            print(f"[OrderExecutor] {msg}")
        
        executor = OrderExecutor(mock_skcom, mock_add_message)
        print("✅ OrderExecutor 創建成功")
        
        # 檢查事件是否設置
        if hasattr(executor, 'async_order_handler'):
            print("✅ async_order_handler 已創建")
            if hasattr(executor.async_order_handler, 'OnAsyncOrder'):
                print("✅ OnAsyncOrder 方法已定義")
            else:
                print("❌ OnAsyncOrder 方法未定義")
        else:
            print("❌ async_order_handler 未創建")
        
        # 檢查SKOrder事件是否設置
        if mock_skcom['SKOrder'].event_set:
            print("✅ SKOrder.OnAsyncOrder 事件已設置")
        else:
            print("❌ SKOrder.OnAsyncOrder 事件未設置")
        
    except Exception as e:
        print(f"❌ 測試失敗: {e}")
        import traceback
        traceback.print_exc()

def test_async_order_callback():
    """測試 OnAsyncOrder 回調功能"""
    print("\n🧪 測試 OnAsyncOrder 回調功能...")
    
    try:
        from order.future_order import OrderExecutor
        
        # 模擬SKCOM物件
        mock_skcom = {
            'SKOrder': None,
            'SKCenter': None,
            'SKQuote': None
        }
        
        # 收集回調訊息
        callback_messages = []
        def mock_add_message(msg):
            callback_messages.append(msg)
            print(f"[OrderExecutor] {msg}")
        
        executor = OrderExecutor(mock_skcom, mock_add_message)
        
        # 模擬 OnAsyncOrder 回調
        if hasattr(executor, 'async_order_handler'):
            handler = executor.async_order_handler
            
            print("📋 測試成功回調...")
            handler.OnAsyncOrder(0, "OF00001234567")  # 成功
            
            print("📋 測試失敗回調...")
            handler.OnAsyncOrder(1001, "錯誤訊息")  # 失敗
            
            print("✅ 回調測試完成")
            print(f"📊 收到 {len(callback_messages)} 條回調訊息")
        else:
            print("❌ async_order_handler 不存在，無法測試回調")
        
    except Exception as e:
        print(f"❌ 回調測試失敗: {e}")

def main():
    """主測試函數"""
    print("🚀 開始非同步下單事件測試...")
    print("=" * 50)
    
    test_async_order_event_setup()
    test_async_order_callback()
    
    print("\n" + "=" * 50)
    print("✅ 非同步下單事件測試完成！")
    print("\n📋 測試建議:")
    print("1. 如果事件設置正常，可以進行手動下單測試")
    print("2. 在期貨下單頁面下一筆測試單")
    print("3. 觀察是否出現 '✅【委託確認】委託序號: xxx' 訊息")
    print("4. 檢查下單回報頁面是否收到對應回報")
    print("\n⚠️ 注意事項:")
    print("- 確保已連接回報伺服器")
    print("- 使用小額測試單 (1口)")
    print("- 觀察LOG輸出的完整流程")

if __name__ == "__main__":
    main()
