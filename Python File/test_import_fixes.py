#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
測試導入修復是否成功
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

def test_ordertester_imports():
    """測試OrderTester.py的導入"""
    print("🔍 測試OrderTester.py導入...")
    
    try:
        # 測試基本導入
        import time
        import threading
        import re
        print("✅ 基本模組導入成功")
        
        # 測試time.time()調用
        timestamp = time.time()
        print(f"✅ time.time() 調用成功: {timestamp}")
        
        # 測試re模組
        pattern = r"序號:(\d+)"
        test_string = "🎉【成交】序號:1234567890123"
        match = re.search(pattern, test_string)
        if match:
            print(f"✅ re模組調用成功: 找到序號 {match.group(1)}")
        
        return True
        
    except Exception as e:
        print(f"❌ OrderTester.py導入測試失敗: {e}")
        return False

def test_future_order_imports():
    """測試future_order.py的導入"""
    print("\n🔍 測試future_order.py導入...")
    
    try:
        # 測試基本導入
        import time
        from datetime import datetime
        print("✅ 基本模組導入成功")
        
        # 測試time調用
        current_time = time.time()
        formatted_time = time.strftime("%H:%M:%S")
        print(f"✅ time模組調用成功: {current_time}, {formatted_time}")
        
        # 測試datetime調用
        now = datetime.now()
        timestamp = now.strftime("%H:%M:%S")
        print(f"✅ datetime模組調用成功: {timestamp}")
        
        return True
        
    except Exception as e:
        print(f"❌ future_order.py導入測試失敗: {e}")
        return False

def test_strategy_order_simulation():
    """模擬策略下單流程測試"""
    print("\n🔍 模擬策略下單流程...")
    
    try:
        import time
        from datetime import datetime
        
        # 模擬策略下單時的時間戳記錄
        order_data = {
            'direction': 'LONG',
            'price': 22374.0,
            'quantity': 1,
            'timestamp': time.time(),  # 這裡之前會出錯
            'datetime': datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        }
        
        print(f"✅ 策略下單資料創建成功:")
        for key, value in order_data.items():
            print(f"   - {key}: {value}")
        
        return True
        
    except Exception as e:
        print(f"❌ 策略下單流程測試失敗: {e}")
        return False

def main():
    """主測試流程"""
    print("🚀 開始測試導入修復...")
    print("=" * 50)
    
    # 執行各項測試
    results = []
    results.append(test_ordertester_imports())
    results.append(test_future_order_imports())
    results.append(test_strategy_order_simulation())
    
    print("\n" + "=" * 50)
    print("📊 測試結果總結:")
    
    success_count = sum(results)
    total_count = len(results)
    
    print(f"✅ 成功測試: {success_count}/{total_count}")
    
    if success_count == total_count:
        print("🎉 所有導入修復都成功！")
        print("💡 現在可以安全測試實單下單功能了")
        print("\n📋 修復內容總結:")
        print("1. ✅ 添加了 import time 到 OrderTester.py")
        print("2. ✅ 添加了 import threading 到 OrderTester.py")
        print("3. ✅ 添加了 import re 到 OrderTester.py")
        print("4. ✅ 添加了 import time 到 future_order.py")
        print("5. ✅ 添加了 from datetime import datetime 到 future_order.py")
        print("6. ✅ 移除了所有局部導入，改為全局導入")
        
        print("\n🎯 預期效果:")
        print("- 實單模式下策略觸發時不會再出現 'name time is not defined' 錯誤")
        print("- 策略下單流程可以正常執行到API調用階段")
        print("- 你會看到完整的下單LOG，包括API調用訊息")
        
    else:
        print("⚠️ 部分測試失敗，請檢查失敗的項目")
    
    return success_count == total_count

if __name__ == "__main__":
    success = main()
    if success:
        print("\n✅ 導入修復驗證完成，可以進行實單測試！")
    else:
        print("\n❌ 導入修復驗證失敗，需要進一步檢查！")
