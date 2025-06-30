#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
實盤交易部位管理器測試
測試建倉機制和策略邏輯整合

🏷️ POSITION_MANAGER_TEST_2025_06_30
✅ 測試開盤區間計算
✅ 測試突破信號檢測
✅ 測試多口建倉邏輯
✅ 測試移動停利機制
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
        order_id = f"TEST{self.order_counter:04d}"
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

def test_opening_range_calculation():
    """測試開盤區間計算"""
    print("\n" + "="*60)
    print("🧪 測試1: 開盤區間計算")
    print("="*60)
    
    # 建立策略配置
    config = StrategyConfig(
        trade_size_in_lots=2,
        stop_loss_type=StopLossType.RANGE_BOUNDARY,
        lot_rules=[
            LotRule(use_trailing_stop=True, trailing_activation=Decimal(15), trailing_pullback=Decimal('0.20')),
            LotRule(use_trailing_stop=True, trailing_activation=Decimal(30), trailing_pullback=Decimal('0.20'))
        ]
    )
    
    # 建立部位管理器
    mock_api = MockOrderAPI()
    manager = LiveTradingPositionManager(config, mock_api)
    
    # 模擬8:46價格數據
    print("📊 模擬8:46價格數據...")
    manager.update_price(22000, datetime(2025, 6, 30, 8, 46, 10))
    manager.update_price(22005, datetime(2025, 6, 30, 8, 46, 30))
    manager.update_price(21998, datetime(2025, 6, 30, 8, 46, 50))
    
    # 模擬8:47價格數據
    print("📊 模擬8:47價格數據...")
    manager.update_price(22010, datetime(2025, 6, 30, 8, 47, 10))
    manager.update_price(22015, datetime(2025, 6, 30, 8, 47, 30))
    manager.update_price(22008, datetime(2025, 6, 30, 8, 47, 50))
    
    # 檢查區間計算結果
    if manager.range_detected:
        print(f"✅ 區間計算成功:")
        print(f"   高點: {float(manager.range_high)}")
        print(f"   低點: {float(manager.range_low)}")
        print(f"   區間大小: {float(manager.range_high - manager.range_low)}點")
    else:
        print("❌ 區間計算失敗")
    
    return manager

def test_breakout_signal_long(manager):
    """測試多頭突破信號"""
    print("\n" + "="*60)
    print("🧪 測試2: 多頭突破信號與建倉")
    print("="*60)
    
    if not manager.range_detected:
        print("❌ 區間未檢測到，跳過測試")
        return
    
    # 模擬8:48突破價格
    breakout_price = float(manager.range_high) + 2
    print(f"📈 模擬突破價格: {breakout_price} (區間高點: {float(manager.range_high)})")
    
    manager.update_price(breakout_price, datetime(2025, 6, 30, 8, 48, 15))
    
    # 檢查建倉結果
    if manager.position:
        print(f"✅ 建倉成功:")
        print(f"   方向: {manager.position}")
        print(f"   進場價: {float(manager.entry_price)}")
        print(f"   口數: {len(manager.lots)}")
        
        for lot in manager.lots:
            print(f"   第{lot['id']}口: 狀態={lot['status']}, 停損={float(lot['stop_loss'])}")
    else:
        print("❌ 建倉失敗")
    
    return manager

def test_trailing_stop_mechanism(manager):
    """測試移動停利機制"""
    print("\n" + "="*60)
    print("🧪 測試3: 移動停利機制")
    print("="*60)
    
    if not manager.position:
        print("❌ 無部位，跳過測試")
        return
    
    entry_price = float(manager.entry_price)
    
    # 模擬價格上漲，觸發第1口移動停利
    print("📈 模擬價格上漲...")
    test_prices = [
        entry_price + 5,   # 小幅上漲
        entry_price + 10,  # 繼續上漲
        entry_price + 18,  # 觸發第1口移動停利啟動
        entry_price + 25,  # 繼續上漲
        entry_price + 20,  # 回檔，可能觸發第1口出場
    ]
    
    for i, price in enumerate(test_prices):
        print(f"   價格更新 {i+1}: {price}")
        manager.update_price(price, datetime(2025, 6, 30, 8, 50 + i, 0))
        
        # 檢查部位狀態
        active_lots = [l for l in manager.lots if l['status'] == 'active']
        exited_lots = [l for l in manager.lots if l['status'] == 'exited']
        
        print(f"     活躍口數: {len(active_lots)}, 已出場: {len(exited_lots)}")
        
        if exited_lots:
            for lot in exited_lots:
                if lot['pnl'] != 0:
                    print(f"     第{lot['id']}口已出場，損益: {float(lot['pnl'])}")

def test_complete_trading_scenario():
    """完整交易場景測試"""
    print("\n" + "🎯 完整交易場景測試")
    print("="*80)
    
    # 測試1: 開盤區間計算
    manager = test_opening_range_calculation()
    
    # 測試2: 突破建倉
    test_breakout_signal_long(manager)
    
    # 測試3: 移動停利
    test_trailing_stop_mechanism(manager)
    
    # 顯示最終結果
    print("\n" + "="*60)
    print("📊 最終交易結果")
    print("="*60)
    
    if manager.position:
        total_pnl = sum(float(l['pnl']) for l in manager.lots if l['status'] == 'exited')
        active_lots = len([l for l in manager.lots if l['status'] == 'active'])
        
        print(f"持倉方向: {manager.position}")
        print(f"進場價格: {float(manager.entry_price)}")
        print(f"活躍口數: {active_lots}")
        print(f"已實現損益: {total_pnl}")
        
        print("\n各口單詳情:")
        for lot in manager.lots:
            status_text = "活躍" if lot['status'] == 'active' else "已出場"
            pnl_text = f"{float(lot['pnl'])}" if lot['pnl'] != 0 else "0"
            print(f"  第{lot['id']}口: {status_text}, 損益: {pnl_text}")
    
    # 顯示模擬訂單
    print(f"\n📋 模擬訂單記錄 (共{len(manager.order_api.orders)}筆):")
    for order in manager.order_api.orders:
        print(f"  {order['timestamp'].strftime('%H:%M:%S')} - {order['direction']} {order['quantity']}口 @ {order['price']} (ID: {order['order_id']})")

if __name__ == "__main__":
    print("🚀 實盤交易部位管理器測試開始")
    print("基於回測策略邏輯的建倉機制驗證")
    
    try:
        test_complete_trading_scenario()
        print("\n✅ 所有測試完成")
        
    except Exception as e:
        logger.error(f"❌ 測試過程發生錯誤: {e}", exc_info=True)
        print(f"\n❌ 測試失敗: {e}")
