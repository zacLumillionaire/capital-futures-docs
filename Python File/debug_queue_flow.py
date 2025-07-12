#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
調試Queue數據流問題
"""

import time
import queue

def simulate_queue_issue():
    """模擬當前的Queue問題"""
    print("🔍 模擬當前Queue問題...")
    
    # 模擬當前狀況
    print("\n📊 當前觀察到的現象:")
    print("1. ✅ 看到五檔報價LOG: 【五檔】買1:2272500(1) 賣1:2272600(4)")
    print("2. ❌ 沒有看到Tick成交價LOG")
    print("3. ❌ 策略面板價格沒有更新")
    print("4. ❌ 策略面板時間沒有更新")
    
    print("\n🔍 可能的原因分析:")
    print("1. OnNotifyTicksLONG沒有被觸發 (沒有成交)")
    print("2. OnNotifyTicksLONG被觸發但數據沒有進入Queue")
    print("3. 數據進入Queue但主線程沒有處理")
    print("4. 主線程處理了但UI沒有更新")
    
    print("\n🎯 解決方案:")
    print("1. 添加調試輸出到OnNotifyTicksLONG")
    print("2. 檢查Queue數據流")
    print("3. 確認UI變數存在")
    print("4. 測試手動數據注入")

def test_manual_queue_injection():
    """測試手動注入Queue數據"""
    print("\n🧪 測試手動Queue數據注入...")
    
    try:
        # 創建測試Queue
        tick_queue = queue.Queue(maxsize=1000)
        strategy_queue = queue.Queue(maxsize=100)
        
        # 模擬Tick數據
        test_tick = {
            'type': 'tick',
            'market': 2,
            'stock_idx': 0,
            'date': 20250703,
            'time': 91530,  # 09:15:30
            'bid': 2272400,
            'ask': 2272500,
            'close': 2272450,  # 成交價
            'qty': 5,
            'timestamp': time.time()
        }
        
        print(f"📊 注入測試數據: {test_tick}")
        tick_queue.put_nowait(test_tick)
        
        # 模擬主線程處理
        if not tick_queue.empty():
            data = tick_queue.get_nowait()
            print(f"✅ 成功從Queue取得數據: {data['type']}")
            
            # 模擬價格處理
            corrected_price = data['close'] / 100.0 if data['close'] > 100000 else data['close']
            time_str = f"{data['time']:06d}"
            formatted_time = f"{time_str[:2]}:{time_str[2:4]}:{time_str[4:6]}"
            
            print(f"💰 處理後價格: {corrected_price}")
            print(f"⏰ 處理後時間: {formatted_time}")
            
            # 模擬策略數據
            strategy_data = {
                'price': corrected_price,
                'time': formatted_time,
                'timestamp': data['timestamp']
            }
            strategy_queue.put_nowait(strategy_data)
            print(f"🎯 策略數據已準備: {strategy_data}")
            
            return True
        else:
            print("❌ Queue為空")
            return False
            
    except Exception as e:
        print(f"❌ 測試失敗: {e}")
        return False

def check_ui_variables():
    """檢查UI變數是否存在"""
    print("\n🔍 檢查UI變數...")
    
    try:
        import OrderTester
        
        # 檢查類定義
        app_class = OrderTester.OrderTesterApp
        
        # 檢查__init__方法中的UI變數定義
        import inspect
        source = inspect.getsource(app_class.__init__)
        
        ui_vars = [
            'strategy_price_var',
            'strategy_time_var',
            'range_high_var',
            'range_low_var',
            'signal_status_var',
            'position_status_var'
        ]
        
        print("📋 UI變數檢查:")
        for var in ui_vars:
            found = var in source
            status = "✅" if found else "❌"
            print(f"   {status} {var}")
        
        return True
        
    except Exception as e:
        print(f"❌ UI變數檢查失敗: {e}")
        return False

def generate_debug_suggestions():
    """生成調試建議"""
    print("\n💡 調試建議:")
    
    suggestions = [
        "1. 在OnNotifyTicksLONG中添加print輸出確認是否被觸發",
        "2. 檢查報價訂閱是否成功 (RequestTicks返回值)",
        "3. 確認市場是否有成交 (可能只有掛單沒有成交)",
        "4. 檢查策略監控是否正確啟動",
        "5. 測試手動注入數據到Queue",
        "6. 確認UI變數是否正確綁定到控件"
    ]
    
    for suggestion in suggestions:
        print(f"   📝 {suggestion}")
    
    print("\n🔧 立即可執行的修正:")
    print("   1. 重新啟動OrderTester.py")
    print("   2. 觀察控制台的Queue狀態檢查訊息")
    print("   3. 確認策略監控已啟動")
    print("   4. 檢查是否有 '🔍 Queue狀態檢查' 訊息")

def main():
    """主函數"""
    print("🚀 Queue數據流調試工具")
    print("=" * 50)
    
    tests = [
        ("問題模擬", simulate_queue_issue),
        ("手動Queue測試", test_manual_queue_injection),
        ("UI變數檢查", check_ui_variables),
        ("調試建議", generate_debug_suggestions)
    ]
    
    for test_name, test_func in tests:
        try:
            print(f"\n{'='*20} {test_name} {'='*20}")
            test_func()
        except Exception as e:
            print(f"❌ {test_name} 執行失敗: {e}")
    
    print("\n" + "=" * 50)
    print("🎯 總結:")
    print("1. 五檔報價正常，但沒有Tick成交價")
    print("2. 可能是市場沒有成交或Tick訂閱問題")
    print("3. 已添加調試輸出，重新啟動程式觀察")
    print("4. 如果仍無數據，可能需要檢查報價訂閱")

if __name__ == "__main__":
    main()
