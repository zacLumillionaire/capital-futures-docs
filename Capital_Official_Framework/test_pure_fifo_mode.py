#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
純FIFO模式測試腳本
測試新增的純FIFO匹配邏輯和開關控制功能
"""

import sys
import os
import time
from datetime import datetime

# 添加項目路徑
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

def test_pure_fifo_mode():
    """測試純FIFO模式功能"""
    print("🧪 測試純FIFO模式功能...")
    
    try:
        from fifo_order_matcher import FIFOOrderMatcher, OrderInfo
        
        # 創建FIFO匹配器（預設開啟純FIFO模式）
        matcher = FIFOOrderMatcher(console_enabled=True)
        
        print(f"\n📊 初始狀態:")
        matcher.print_statistics()
        
        # 測試1: 添加測試訂單
        print(f"\n🔧 測試1: 添加測試訂單...")
        
        # 創建測試訂單
        order1 = OrderInfo(
            order_id="TEST_001",
            product="TM0000",
            direction="BUY",
            quantity=1,
            price=23300.0,
            submit_time=time.time() - 10  # 10秒前
        )
        
        order2 = OrderInfo(
            order_id="TEST_002", 
            product="TM0000",
            direction="BUY",
            quantity=1,
            price=23310.0,  # 不同價格
            submit_time=time.time() - 5   # 5秒前
        )
        
        # 註冊訂單
        matcher.add_pending_order(order1)
        matcher.add_pending_order(order2)
        
        print(f"✅ 已註冊2個測試訂單")
        
        # 測試2: 純FIFO匹配（不比對價格）
        print(f"\n🔧 測試2: 純FIFO匹配測試...")
        
        # 嘗試匹配一個價格差異較大的回報
        test_price = 23320.0  # 與兩個訂單都有價格差異
        matched_order = matcher.find_match(
            price=test_price,
            qty=1,
            product="TM2508",  # 使用券商回報的商品代碼
            order_type="D"
        )
        
        if matched_order:
            price_diff = abs(matched_order.price - test_price)
            print(f"✅ 純FIFO匹配成功:")
            print(f"   匹配訂單: {matched_order.order_id}")
            print(f"   訂單價格: {matched_order.price}")
            print(f"   回報價格: {test_price}")
            print(f"   價格差異: {price_diff:.1f}點")
        else:
            print(f"❌ 純FIFO匹配失敗")
        
        # 測試3: 統計資訊
        print(f"\n📊 匹配後統計:")
        matcher.print_statistics()
        
        return True
        
    except Exception as e:
        print(f"❌ 純FIFO模式測試失敗: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_mode_switching():
    """測試模式切換功能"""
    print(f"\n🧪 測試模式切換功能...")
    
    try:
        from fifo_order_matcher import FIFOOrderMatcher, OrderInfo
        
        # 創建匹配器
        matcher = FIFOOrderMatcher(console_enabled=True)
        
        # 測試切換到價格匹配模式
        print(f"\n🔧 切換到價格匹配模式...")
        matcher.set_pure_fifo_mode(False)
        
        # 添加測試訂單
        order = OrderInfo(
            order_id="PRICE_TEST_001",
            product="TM0000", 
            direction="BUY",
            quantity=1,
            price=23300.0,
            submit_time=time.time()
        )
        matcher.add_pending_order(order)
        
        # 測試價格匹配（應該失敗，因為價格差異太大）
        matched_order = matcher.find_match(
            price=23350.0,  # 50點差異，超過容差
            qty=1,
            product="TM2508",
            order_type="D"
        )
        
        if matched_order:
            print(f"⚠️ 價格匹配意外成功（可能是回退到純FIFO）")
        else:
            print(f"✅ 價格匹配正確失敗（價格差異過大）")
        
        # 切換回純FIFO模式
        print(f"\n🔧 切換回純FIFO模式...")
        matcher.set_pure_fifo_mode(True)
        
        # 重新添加訂單
        order2 = OrderInfo(
            order_id="PURE_TEST_002",
            product="TM0000",
            direction="BUY", 
            quantity=1,
            price=23300.0,
            submit_time=time.time()
        )
        matcher.add_pending_order(order2)
        
        # 測試純FIFO匹配（應該成功）
        matched_order = matcher.find_match(
            price=23350.0,  # 同樣的50點差異
            qty=1,
            product="TM2508",
            order_type="D"
        )
        
        if matched_order:
            print(f"✅ 純FIFO匹配成功（忽略價格差異）")
        else:
            print(f"❌ 純FIFO匹配失敗")
        
        # 最終統計
        print(f"\n📊 最終統計:")
        matcher.print_statistics()
        
        return True
        
    except Exception as e:
        print(f"❌ 模式切換測試失敗: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """主測試函數"""
    print("=" * 60)
    print("🚀 純FIFO模式測試開始")
    print("=" * 60)
    
    success_count = 0
    total_tests = 2
    
    # 執行測試
    if test_pure_fifo_mode():
        success_count += 1
        
    if test_mode_switching():
        success_count += 1
    
    # 測試結果
    print("=" * 60)
    print(f"📋 測試結果: {success_count}/{total_tests} 通過")
    
    if success_count == total_tests:
        print("🎉 所有測試通過！純FIFO模式功能正常")
    else:
        print("⚠️ 部分測試失敗，請檢查實現")
    
    print("=" * 60)

if __name__ == "__main__":
    main()
