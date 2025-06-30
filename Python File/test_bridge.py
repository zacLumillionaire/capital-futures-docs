#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
橋接模式測試工具
用於測試OrderTester和UI之間的價格橋接是否正常
"""

import time
import json
from datetime import datetime
from price_bridge import PriceBridge, write_price_to_bridge, get_latest_price

def test_bridge():
    """測試橋接功能"""
    print("🧪 橋接模式測試工具")
    print("=" * 50)
    
    # 測試1: 檢查橋接檔案
    print("\n📋 測試1: 檢查橋接檔案")
    try:
        import os
        if os.path.exists("price_data.json"):
            print("✅ price_data.json 存在")
            
            # 讀取檔案內容
            with open("price_data.json", 'r', encoding='utf-8') as f:
                content = f.read()
                print(f"📄 檔案內容長度: {len(content)} 字符")
                
                if content.strip():
                    try:
                        data = json.loads(content)
                        print(f"✅ JSON格式正確")
                        print(f"   價格: {data.get('price', 'N/A')}")
                        print(f"   時間: {data.get('timestamp', 'N/A')}")
                        print(f"   更新時間戳: {data.get('update_time', 'N/A')}")
                        
                        # 檢查時間戳是否合理
                        update_time = data.get('update_time', 0)
                        current_time = time.time()
                        age = current_time - update_time
                        print(f"   數據年齡: {age:.1f} 秒")
                        
                        if age > 10:
                            print("⚠️ 數據過舊")
                        else:
                            print("✅ 數據新鮮")
                            
                    except json.JSONDecodeError as e:
                        print(f"❌ JSON格式錯誤: {e}")
                        print(f"📄 檔案內容: {repr(content[:100])}")
                else:
                    print("❌ 檔案為空")
        else:
            print("❌ price_data.json 不存在")
    except Exception as e:
        print(f"❌ 檢查檔案失敗: {e}")
    
    # 測試2: 測試寫入功能
    print("\n📋 測試2: 測試寫入功能")
    try:
        test_price = 22100.0
        result = write_price_to_bridge(test_price, 50, datetime.now())
        if result:
            print(f"✅ 寫入測試成功: {test_price}")
        else:
            print("❌ 寫入測試失敗")
    except Exception as e:
        print(f"❌ 寫入測試異常: {e}")
    
    # 測試3: 測試讀取功能
    print("\n📋 測試3: 測試讀取功能")
    try:
        price = get_latest_price()
        if price:
            print(f"✅ 讀取測試成功: {price}")
        else:
            print("❌ 讀取測試失敗")
    except Exception as e:
        print(f"❌ 讀取測試異常: {e}")
    
    # 測試4: 連續讀寫測試
    print("\n📋 測試4: 連續讀寫測試")
    try:
        bridge = PriceBridge()
        
        for i in range(5):
            test_price = 22000 + i
            bridge.write_price(test_price, 100 + i, datetime.now())
            time.sleep(0.1)
            
            data = bridge.read_price()
            if data:
                print(f"  第{i+1}次: 寫入{test_price} → 讀取{data['price']}")
            else:
                print(f"  第{i+1}次: 寫入{test_price} → 讀取失敗")
        
        print("✅ 連續讀寫測試完成")
    except Exception as e:
        print(f"❌ 連續讀寫測試失敗: {e}")
    
    print("\n" + "=" * 50)
    print("🎯 測試完成")
    
    # 給出建議
    print("\n💡 建議:")
    print("1. 如果所有測試都通過，橋接功能正常")
    print("2. 如果有錯誤，請檢查OrderTester是否正在寫入價格")
    print("3. 確認OrderTester中看到「✅ 價格橋接已啟動」訊息")
    print("4. 重新啟動OrderTester和UI程式")

if __name__ == "__main__":
    test_bridge()
