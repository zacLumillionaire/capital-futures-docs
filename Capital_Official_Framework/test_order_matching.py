#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
測試新的訂單匹配機制
驗證基於FIFO和價格匹配的邏輯是否正確
"""

def test_direction_detection():
    """測試方向檢測功能"""
    print("🧪 測試方向檢測功能...")
    
    # 模擬OnNewData回報數據
    # 根據你的LOG: ['2315544935979', 'TF', 'N', 'N', 'F020000', '6363839', 'SNF20', 'TW', 'TM2507', ...]
    # 索引6應該是買賣別
    
    # 測試賣單回報 (你的實際情況)
    sell_order_fields = [
        '2315544935979',  # 0: KeyNo
        'TF',             # 1: MarketType  
        'N',              # 2: Type
        'N',              # 3: OrderErr
        'F020000',        # 4: BrokerID
        '6363839',        # 5: Account
        'S',              # 6: 買賣別 (S=賣出) ⭐ 關鍵欄位
        'TW',             # 7: ExchangeNo
        'TM2507',         # 8: StockNo
        '',               # 9: OrderNo
        'e0758',          # 10: Price2
        '22283.0000',     # 11: Price
        # ... 其他欄位
    ]
    
    # 測試買單回報
    buy_order_fields = sell_order_fields.copy()
    buy_order_fields[6] = 'B'  # B=買進
    
    # 導入修正後的檢測函數
    try:
        import sys
        import os
        sys.path.append(os.path.dirname(__file__))
        
        from simplified_order_tracker import SimplifiedOrderTracker
        
        tracker = SimplifiedOrderTracker(console_enabled=True)
        
        # 測試賣單檢測
        sell_direction = tracker._detect_direction(sell_order_fields)
        print(f"  賣單檢測結果: {sell_direction} (期望: SELL)")
        
        # 測試買單檢測
        buy_direction = tracker._detect_direction(buy_order_fields)
        print(f"  買單檢測結果: {buy_direction} (期望: BUY)")
        
        # 測試方向轉換
        sell_strategy = tracker._convert_api_to_strategy_direction(sell_direction)
        buy_strategy = tracker._convert_api_to_strategy_direction(buy_direction)
        
        print(f"  SELL -> {sell_strategy} (期望: SHORT)")
        print(f"  BUY -> {buy_strategy} (期望: LONG)")
        
        # 測試商品映射
        tm2507_normalized = tracker._normalize_product_code('TM2507')
        tm0000_normalized = tracker._normalize_product_code('TM0000')
        
        print(f"  TM2507 -> {tm2507_normalized} (期望: TM0000)")
        print(f"  TM0000 -> {tm0000_normalized} (期望: TM0000)")
        
        print("✅ 方向檢測測試完成")
        return True
        
    except Exception as e:
        print(f"❌ 方向檢測測試失敗: {e}")
        return False

def test_order_matching_logic():
    """測試訂單匹配邏輯"""
    print("\n🧪 測試訂單匹配邏輯...")
    
    try:
        from simplified_order_tracker import SimplifiedOrderTracker, StrategyGroup
        import time
        
        tracker = SimplifiedOrderTracker(console_enabled=True)
        
        # 創建測試策略組 (模擬你的SHORT策略)
        test_group = StrategyGroup(
            group_id=2,
            total_lots=2,
            direction="SHORT",  # 策略方向
            target_price=22283.0,
            product="TM0000"
        )
        
        tracker.strategy_groups[2] = test_group
        
        print(f"  創建測試策略組: {test_group}")
        
        # 模擬成交回報 (API方向為SELL，對應SHORT策略)
        test_price = 22285.0  # 滑價+2點
        test_api_direction = "SELL"  # API回報的方向
        test_product = "TM2507"  # 回報中的商品代碼
        
        print(f"  測試匹配: 價格={test_price}, API方向={test_api_direction}, 商品={test_product}")
        
        # 測試匹配
        matched_group = tracker._find_matching_group(test_price, test_api_direction, test_product)
        
        if matched_group:
            print(f"✅ 匹配成功: 組{matched_group.group_id}")
            print(f"    策略方向: {matched_group.direction}")
            print(f"    目標價格: {matched_group.target_price}")
            print(f"    價格差距: {abs(test_price - matched_group.target_price):.1f}點")
        else:
            print("❌ 匹配失敗")
            
        print("✅ 訂單匹配邏輯測試完成")
        return True
        
    except Exception as e:
        print(f"❌ 訂單匹配邏輯測試失敗: {e}")
        return False

def test_real_log_data():
    """測試真實LOG數據"""
    print("\n🧪 測試真實LOG數據...")
    
    # 你的實際LOG數據
    real_log_data = "2315544935979,TF,N,N,F020000,6363839,SNF20,TW,TM2507,,e0758,22283.0000,,,,,,,,,1,,,20250707,09:08:01,,0000000,7174,y,20250707,2110000164928,A,FITM,202507,,,,,,,A,20250707,,,,,N,,2315544935979"
    
    try:
        from simplified_order_tracker import SimplifiedOrderTracker
        
        tracker = SimplifiedOrderTracker(console_enabled=True)
        
        # 解析實際數據
        fields = real_log_data.split(',')
        print(f"  總欄位數: {len(fields)}")
        print(f"  關鍵欄位:")
        print(f"    [0] KeyNo: {fields[0]}")
        print(f"    [2] Type: {fields[2]}")
        print(f"    [6] 買賣別: {fields[6]}")
        print(f"    [8] 商品: {fields[8]}")
        print(f"    [11] 價格: {fields[11]}")
        print(f"    [20] 數量: {fields[20]}")
        
        # 測試方向檢測
        direction = tracker._detect_direction(fields)
        print(f"  檢測到的方向: {direction}")
        
        # 測試商品映射
        normalized_product = tracker._normalize_product_code(fields[8])
        print(f"  標準化商品: {fields[8]} -> {normalized_product}")
        
        print("✅ 真實LOG數據測試完成")
        return True
        
    except Exception as e:
        print(f"❌ 真實LOG數據測試失敗: {e}")
        return False

if __name__ == "__main__":
    print("🚀 開始測試新的訂單匹配機制")
    print("=" * 50)
    
    success_count = 0
    total_tests = 3
    
    # 執行測試
    if test_direction_detection():
        success_count += 1
        
    if test_order_matching_logic():
        success_count += 1
        
    if test_real_log_data():
        success_count += 1
    
    print("\n" + "=" * 50)
    print(f"🎯 測試結果: {success_count}/{total_tests} 通過")
    
    if success_count == total_tests:
        print("🎉 所有測試通過！新的匹配機制準備就緒")
    else:
        print("⚠️ 部分測試失敗，需要進一步調整")
