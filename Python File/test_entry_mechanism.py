#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
入場建倉機制測試
測試一分K收盤價突破 + 下一個報價進場邏輯

🏷️ ENTRY_MECHANISM_TEST_2025_06_30
✅ 測試一分K監控
✅ 測試收盤價突破檢測
✅ 測試分開建倉機制
✅ 測試模擬下單功能
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from datetime import datetime, time
from decimal import Decimal
import logging

# 導入建倉機制
from test_ui_improvements import LiveTradingPositionManager, StrategyConfig, LotRule, StopLossType

# 設定日誌
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class MockOrderAPI:
    """模擬下單API"""
    
    def __init__(self):
        self.orders = []
        self.order_counter = 1
    
    def place_order(self, product, direction, price, quantity, order_type):
        """模擬下單"""
        order_id = f"ENTRY{self.order_counter:04d}"
        self.order_counter += 1
        
        order = {
            'order_id': order_id,
            'product': product,
            'direction': direction,
            'price': price,
            'quantity': quantity,
            'order_type': order_type,
            'timestamp': datetime.now()
        }
        
        self.orders.append(order)
        
        logger.info(f"📋 模擬下單: {direction} {quantity}口 {product} @ {price} (ID: {order_id})")
        
        return {
            'success': True,
            'order_id': order_id,
            'message': '模擬下單成功',
            'timestamp': datetime.now().strftime('%H:%M:%S')
        }
    
    def get_orders(self):
        """獲取所有訂單"""
        return self.orders

def test_minute_candle_monitoring():
    """測試一分K監控功能"""
    print("\n" + "="*60)
    print("🧪 測試1: 一分K監控功能")
    print("="*60)
    
    # 建立策略配置
    config = StrategyConfig(
        trade_size_in_lots=3,
        stop_loss_type=StopLossType.RANGE_BOUNDARY,
        lot_rules=[
            LotRule(use_trailing_stop=True, trailing_activation=Decimal(15), trailing_pullback=Decimal('0.20')),
            LotRule(use_trailing_stop=True, trailing_activation=Decimal(30), trailing_pullback=Decimal('0.20')),
            LotRule(use_trailing_stop=True, trailing_activation=Decimal(45), trailing_pullback=Decimal('0.20'))
        ]
    )
    
    # 建立部位管理器
    mock_api = MockOrderAPI()
    manager = LiveTradingPositionManager(config, mock_api)
    
    # 先設定區間 (模擬8:46-8:47已完成)
    manager.range_high = Decimal(22010)
    manager.range_low = Decimal(21998)
    manager.range_detected = True
    
    print(f"📊 設定開盤區間: {float(manager.range_low)} - {float(manager.range_high)}")
    
    # 模擬8:48分鐘的價格數據
    print("\n📊 模擬8:48分鐘價格數據...")
    prices_848 = [22005, 22007, 22009, 22008, 22006]  # 未突破
    
    for i, price in enumerate(prices_848):
        timestamp = datetime(2025, 6, 30, 8, 48, i*10)
        manager.update_price(price, timestamp)
        print(f"   8:48:{i*10:02d} - 價格: {price}")
    
    # 檢查8:48分鐘K線
    if manager.current_minute_candle:
        candle = manager.current_minute_candle
        print(f"✅ 8:48分鐘K線: 開{float(candle['open'])} 高{float(candle['high'])} 低{float(candle['low'])} 收{float(candle['close'])}")
    
    return manager

def test_breakout_signal_detection(manager):
    """測試突破信號檢測"""
    print("\n" + "="*60)
    print("🧪 測試2: 突破信號檢測")
    print("="*60)

    # 模擬8:49分鐘的價格數據 - 突破上緣
    print("📊 模擬8:49分鐘價格數據 - 突破上緣...")
    prices_849 = [22008, 22010, 22012, 22015, 22013]  # 收盤價22013突破22010

    for i, price in enumerate(prices_849):
        timestamp = datetime(2025, 6, 30, 8, 49, i*10)
        manager.update_price(price, timestamp)
        print(f"   8:49:{i*10:02d} - 價格: {price}")

    # 重要：觸發分鐘變化來檢查8:49的收盤價突破
    print("📊 觸發8:50分鐘開始，檢查8:49收盤價突破...")
    trigger_timestamp = datetime(2025, 6, 30, 8, 50, 0)
    manager.update_price(22014, trigger_timestamp)  # 8:50第一個價格

    # 檢查是否產生突破信號
    if manager.breakout_signal:
        print(f"✅ 突破信號產生: {manager.breakout_signal}")
        print(f"✅ 等待進場狀態: {manager.waiting_for_entry}")

        # 顯示8:49分鐘K線詳情
        if manager.current_minute_candle:
            prev_candle = manager.current_minute_candle
            print(f"📊 8:49分鐘K線: 收盤價 {float(prev_candle.get('close', 0))}")
    else:
        print("❌ 未產生突破信號")
        # 調試信息
        if manager.current_minute_candle:
            candle = manager.current_minute_candle
            print(f"   當前K線收盤價: {float(candle.get('close', 0))}")
            print(f"   區間上緣: {float(manager.range_high)}")

    return manager

def test_entry_execution(manager):
    """測試進場執行"""
    print("\n" + "="*60)
    print("🧪 測試3: 進場執行")
    print("="*60)
    
    if not manager.waiting_for_entry:
        print("❌ 未在等待進場狀態，跳過測試")
        return manager
    
    # 模擬下一個報價 - 觸發進場
    print("📊 模擬下一個報價觸發進場...")
    entry_price = 22014
    entry_timestamp = datetime(2025, 6, 30, 8, 50, 5)
    
    manager.update_price(entry_price, entry_timestamp)
    
    # 檢查建倉結果
    if manager.position:
        print(f"✅ 建倉成功:")
        print(f"   方向: {manager.position}")
        print(f"   進場價: {float(manager.entry_price)}")
        print(f"   建倉口數: {len(manager.lots)}")
        
        print("\n各口單詳情:")
        for lot in manager.lots:
            print(f"   第{lot['id']}口: 訂單ID={lot['order_id']}, 狀態={lot['status']}")
    else:
        print("❌ 建倉失敗")
    
    return manager

def test_separate_orders_verification(manager):
    """驗證分開下單"""
    print("\n" + "="*60)
    print("🧪 測試4: 分開下單驗證")
    print("="*60)
    
    if not manager.order_api:
        print("❌ 無下單API，跳過測試")
        return
    
    orders = manager.order_api.get_orders()
    print(f"📋 總下單筆數: {len(orders)}")
    
    if len(orders) == manager.config.trade_size_in_lots:
        print("✅ 下單筆數正確 - 每口單獨下單")
        
        for i, order in enumerate(orders):
            print(f"   訂單{i+1}: {order['direction']} {order['quantity']}口 @ {order['price']} (ID: {order['order_id']})")
    else:
        print(f"❌ 下單筆數錯誤 - 預期{manager.config.trade_size_in_lots}筆，實際{len(orders)}筆")

def test_complete_entry_scenario():
    """完整入場場景測試"""
    print("\n" + "🎯 完整入場場景測試")
    print("="*80)
    
    # 測試1: 一分K監控
    manager = test_minute_candle_monitoring()
    
    # 測試2: 突破信號檢測
    test_breakout_signal_detection(manager)
    
    # 測試3: 進場執行
    test_entry_execution(manager)
    
    # 測試4: 分開下單驗證
    test_separate_orders_verification(manager)
    
    # 顯示最終狀態
    print("\n" + "="*60)
    print("📊 最終入場結果")
    print("="*60)
    
    if manager.position:
        print(f"持倉方向: {manager.position}")
        print(f"進場價格: {float(manager.entry_price)}")
        print(f"建倉口數: {len(manager.lots)}")
        print(f"突破信號: {manager.breakout_signal if manager.breakout_signal else '已執行'}")
        print(f"等待狀態: {manager.waiting_for_entry}")
        
        print("\n📋 模擬訂單記錄:")
        if manager.order_api and hasattr(manager.order_api, 'orders'):
            for order in manager.order_api.orders:
                print(f"  {order['timestamp'].strftime('%H:%M:%S')} - {order['direction']} {order['quantity']}口 @ {order['price']} (ID: {order['order_id']})")
        else:
            print("  無訂單記錄")
    else:
        print("❌ 未建立部位")

def test_short_entry_scenario():
    """測試空頭入場場景"""
    print("\n" + "🎯 空頭入場場景測試")
    print("="*80)
    
    # 建立新的管理器
    config = StrategyConfig(
        trade_size_in_lots=2,
        lot_rules=[
            LotRule(use_trailing_stop=True, trailing_activation=Decimal(15), trailing_pullback=Decimal('0.20')),
            LotRule(use_trailing_stop=True, trailing_activation=Decimal(30), trailing_pullback=Decimal('0.20'))
        ]
    )
    mock_api = MockOrderAPI()
    manager = LiveTradingPositionManager(config, mock_api)
    
    # 設定區間
    manager.range_high = Decimal(22010)
    manager.range_low = Decimal(21998)
    manager.range_detected = True
    
    print(f"📊 設定開盤區間: {float(manager.range_low)} - {float(manager.range_high)}")
    
    # 模擬8:48分鐘 - 突破下緣
    print("📊 模擬8:48分鐘價格數據 - 突破下緣...")
    prices_848 = [22000, 21999, 21996, 21994, 21995]  # 收盤價21995突破21998

    for i, price in enumerate(prices_848):
        timestamp = datetime(2025, 6, 30, 8, 48, i*10)
        manager.update_price(price, timestamp)

    # 觸發8:49分鐘開始，檢查8:48收盤價突破
    print("📊 觸發8:49分鐘開始，檢查8:48收盤價突破...")
    trigger_timestamp = datetime(2025, 6, 30, 8, 49, 0)
    manager.update_price(21992, trigger_timestamp)  # 8:49第一個價格

    print(f"突破信號: {manager.breakout_signal}")

    # 下一個報價進場
    if manager.waiting_for_entry:
        entry_price = 21993
        entry_timestamp = datetime(2025, 6, 30, 8, 49, 5)
        manager.update_price(entry_price, entry_timestamp)

        if manager.position:
            print(f"✅ 空頭建倉成功: {manager.position} @ {float(manager.entry_price)}")
            print(f"   建倉口數: {len(manager.lots)}")
    else:
        print("❌ 未進入等待進場狀態")

if __name__ == "__main__":
    print("🚀 入場建倉機制測試開始")
    print("基於一分K收盤價突破 + 下一個報價進場")
    
    try:
        # 多頭入場測試
        test_complete_entry_scenario()
        
        # 空頭入場測試
        test_short_entry_scenario()
        
        print("\n✅ 所有入場測試完成")
        
    except Exception as e:
        logger.error(f"❌ 測試過程發生錯誤: {e}", exc_info=True)
        print(f"\n❌ 測試失敗: {e}")
