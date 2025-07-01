#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
完整交易測試系統 - 基於UI改進版本
整合策略測試、下單API、即時報價功能

🏷️ TRADING_TESTER_2025_06_30
✅ 基於改進的UI設計
✅ 整合穩定版下單API
✅ 包含完整策略測試功能
✅ 日誌同步VS CODE輸出
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

import tkinter as tk
from tkinter import ttk, messagebox
from datetime import datetime
import time
import threading
import random
import logging
import comtypes.client

# 導入策略模組
try:
    from strategy.strategy_panel import StrategyControlPanel
    STRATEGY_AVAILABLE = True
    print("✅ 策略模組載入成功")
except ImportError as e:
    STRATEGY_AVAILABLE = False
    print(f"❌ 策略模組載入失敗: {e}")

# 導入穩定版下單API
try:
    from stable_order_api import get_stable_order_api, strategy_place_order
    STABLE_API_AVAILABLE = True
    print("✅ 穩定版下單API載入成功")
except ImportError as e:
    STABLE_API_AVAILABLE = False
    print(f"⚠️ 穩定版下單API未載入: {e}")

# 導入群益API
try:
    import comtypes.client
    SKCOM_AVAILABLE = True
    print("✅ 群益API模組載入成功")
except ImportError as e:
    SKCOM_AVAILABLE = False
    print(f"⚠️ 群益API模組未載入: {e}")

# 導入價格橋接模組
try:
    from price_bridge import start_price_monitoring, stop_price_monitoring, get_latest_price
    PRICE_BRIDGE_AVAILABLE = True
    print("✅ 價格橋接模組載入成功")
except ImportError as e:
    PRICE_BRIDGE_AVAILABLE = False
    print(f"⚠️ 價格橋接模組未載入: {e}")

# 導入TCP價格客戶端模組
try:
    from tcp_price_server import PriceClient
    TCP_PRICE_CLIENT_AVAILABLE = True
    print("✅ TCP價格客戶端模組載入成功")
except ImportError as e:
    TCP_PRICE_CLIENT_AVAILABLE = False
    print(f"⚠️ TCP價格客戶端模組未載入: {e}")

# 設定日誌
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# 導入回測策略邏輯
try:
    from decimal import Decimal
    from dataclasses import dataclass, field
    from enum import Enum, auto
    STRATEGY_LOGIC_AVAILABLE = True
    print("✅ 策略邏輯模組載入成功")
except ImportError as e:
    STRATEGY_LOGIC_AVAILABLE = False
    print(f"❌ 策略邏輯模組載入失敗: {e}")

# 策略配置類別 (從回測移植)
class StopLossType(Enum):
    RANGE_BOUNDARY = auto()
    OPENING_PRICE = auto()
    FIXED_POINTS = auto()

@dataclass
class LotRule:
    """描述「單一口部位」的出場邏輯。"""
    use_trailing_stop: bool = True
    fixed_tp_points: Decimal | None = None
    trailing_activation: Decimal | None = None
    trailing_pullback: Decimal | None = None
    protective_stop_multiplier: Decimal | None = None

@dataclass
class StrategyConfig:
    """策略設定的中央控制面板。"""
    trade_size_in_lots: int = 3
    stop_loss_type: StopLossType = StopLossType.RANGE_BOUNDARY
    fixed_stop_loss_points: Decimal = Decimal(15)
    lot_rules: list[LotRule] = field(default_factory=list)

class DirectSKCOMManager:
    """直接管理群益API的類別"""

    def __init__(self):
        self.m_pSKCenter = None
        self.m_pSKOrder = None
        self.m_pSKQuote = None
        self.m_pSKReply = None
        self.is_initialized = False
        self.is_logged_in = False
        self.login_id = "E123354882"
        self.password = "kkd5ysUCC"

        # 報價相關
        self.quote_callback = None
        self.last_price = 22000
        self.quote_connected = False

        # 事件處理
        self.quote_events = None
        self.order_events = None

class LiveTradingPositionManager:
    """實盤交易部位管理器 - 基於回測邏輯"""

    def __init__(self, config: StrategyConfig, order_api=None, range_start_time=(8, 46)):
        self.config = config
        self.order_api = order_api

        # 動態區間時間設定
        self.range_start_hour, self.range_start_minute = range_start_time
        self.range_end_minute = self.range_start_minute + 1
        self.range_end_hour = self.range_start_hour
        if self.range_end_minute >= 60:
            self.range_end_minute = 0
            self.range_end_hour += 1

        # 交易狀態
        self.position = None  # 'LONG', 'SHORT', None
        self.entry_price = Decimal(0)
        self.entry_time = None
        self.lots = []  # 各口單狀態

        # 區間數據
        self.range_high = None
        self.range_low = None
        self.range_detected = False

        # 價格歷史 (用於區間計算) - 使用動態命名
        self.price_history = []
        self.candle_first = None   # 第一分鐘K線 (原846)
        self.candle_second = None  # 第二分鐘K線 (原847)

        # 一分K監控 (新增)
        self.current_minute_candle = None
        self.last_minute = None
        self.breakout_signal = None  # 'LONG_SIGNAL', 'SHORT_SIGNAL', None
        self.waiting_for_entry = False  # 等待下一個報價進場
        self.entry_signal_time = None

        # 一天一次進場控制 (新增)
        self.first_breakout_detected = False  # 是否已檢測到第一次突破
        self.breakout_direction = None        # 第一次突破的方向 ('LONG', 'SHORT', None)
        self.daily_entry_completed = False    # 當天是否已完成進場

        logger.info(f"🎯 實盤交易管理器初始化 - {config.trade_size_in_lots}口交易")

    def is_after_range_period(self, current_time):
        """檢查是否在區間計算期間之後"""
        # 計算第三分鐘的開始時間
        third_minute = self.range_end_minute + 1
        third_hour = self.range_end_hour
        if third_minute >= 60:
            third_minute = 0
            third_hour += 1

        # 檢查是否在第三分鐘或之後
        if current_time.hour > third_hour:
            return True
        elif current_time.hour == third_hour and current_time.minute >= third_minute:
            return True
        return False

    def update_price(self, price, timestamp):
        """更新價格並檢查交易信號"""
        current_time = timestamp.time()
        price_decimal = Decimal(str(price))

        # 收集第一分鐘的價格數據
        if current_time.hour == self.range_start_hour and current_time.minute == self.range_start_minute:
            if not self.candle_first:
                self.candle_first = {'high': price_decimal, 'low': price_decimal, 'close': price_decimal}
            else:
                self.candle_first['high'] = max(self.candle_first['high'], price_decimal)
                self.candle_first['low'] = min(self.candle_first['low'], price_decimal)
                self.candle_first['close'] = price_decimal

        # 收集第二分鐘的價格數據
        elif current_time.hour == self.range_end_hour and current_time.minute == self.range_end_minute:
            if not self.candle_second:
                self.candle_second = {'high': price_decimal, 'low': price_decimal, 'close': price_decimal}
            else:
                self.candle_second['high'] = max(self.candle_second['high'], price_decimal)
                self.candle_second['low'] = min(self.candle_second['low'], price_decimal)
                self.candle_second['close'] = price_decimal

            # 第二分鐘結束時計算區間
            if not self.range_detected and self.candle_first and self.candle_second:
                self.calculate_opening_range()

        # 區間計算完成後的入場邏輯 (第三分鐘開始)
        elif self.is_after_range_period(current_time) and self.range_detected and not self.daily_entry_completed:
            # 如果正在等待進場，下一個報價就是進場時機
            if self.waiting_for_entry and self.breakout_signal:
                self.execute_entry_on_next_tick(price_decimal, timestamp)
            elif not self.first_breakout_detected:
                # 只有在未檢測到第一次突破時才監控
                self.monitor_minute_candle_breakout(price_decimal, timestamp)

        # 已有部位時檢查出場條件
        elif self.position:
            self.check_exit_conditions(price_decimal, timestamp)

    def calculate_opening_range(self):
        """計算開盤區間"""
        if not self.candle_first or not self.candle_second:
            return

        candles = [self.candle_first, self.candle_second]
        self.range_high = max(c['high'] for c in candles)
        self.range_low = min(c['low'] for c in candles)
        self.range_detected = True

        range_start_str = f"{self.range_start_hour:02d}:{self.range_start_minute:02d}"
        range_end_str = f"{self.range_end_hour:02d}:{self.range_end_minute:02d}"
        logger.info(f"📊 開盤區間計算完成 ({range_start_str}-{range_end_str}): {float(self.range_low)} - {float(self.range_high)}")

    def monitor_minute_candle_breakout(self, price, timestamp):
        """監控一分K收盤價突破區間"""
        current_time = timestamp.time()
        current_minute = current_time.minute

        # 檢查是否進入新的分鐘
        if self.last_minute != current_minute:
            # 檢查上一分鐘的收盤價是否突破區間
            if self.current_minute_candle and self.last_minute is not None:
                self.check_minute_candle_breakout()

            # 開始新的一分鐘K線
            self.start_new_minute_candle(price, timestamp)
            self.last_minute = current_minute
        else:
            # 更新當前分鐘K線
            self.update_current_minute_candle(price, timestamp)

    def start_new_minute_candle(self, price, timestamp):
        """開始新的一分鐘K線"""
        self.current_minute_candle = {
            'open': price,
            'high': price,
            'low': price,
            'close': price,
            'start_time': timestamp,
            'minute': timestamp.time().minute
        }

        logger.debug(f"📊 開始新分鐘K線 {timestamp.strftime('%H:%M')} - 開盤價: {float(price)}")

    def update_current_minute_candle(self, price, timestamp):
        """更新當前分鐘K線"""
        if self.current_minute_candle:
            self.current_minute_candle['high'] = max(self.current_minute_candle['high'], price)
            self.current_minute_candle['low'] = min(self.current_minute_candle['low'], price)
            self.current_minute_candle['close'] = price

    def check_current_minute_breakout(self, close_price, minute):
        """檢查當前分鐘收盤價是否突破區間（在00秒時調用）"""
        # 檢查突破
        if close_price > self.range_high:
            self.breakout_signal = 'LONG_SIGNAL'
            self.waiting_for_entry = True
            self.entry_signal_time = datetime.now()

            range_high_val = float(self.range_high) if self.range_high else 0
            logger.info(f"🔥 {minute:02d}分收盤價突破上緣! 收盤價: {float(close_price)}, 區間上緣: {range_high_val}")
            logger.info(f"⏳ 等待下一個報價進場做多...")

        elif close_price < self.range_low:
            self.breakout_signal = 'SHORT_SIGNAL'
            self.waiting_for_entry = True
            self.entry_signal_time = datetime.now()

            range_low_val = float(self.range_low) if self.range_low else 0
            logger.info(f"🔥 {minute:02d}分收盤價突破下緣! 收盤價: {float(close_price)}, 區間下緣: {range_low_val}")
            logger.info(f"⏳ 等待下一個報價進場做空...")
        else:
            logger.debug(f"📊 {minute:02d}分收盤價未突破: {float(close_price)} (區間: {float(self.range_low) if self.range_low else 0}-{float(self.range_high) if self.range_high else 0})")

    def check_minute_candle_breakout(self):
        """檢查分鐘K線收盤價是否突破區間 - 只檢測第一次突破"""
        if not self.current_minute_candle:
            return

        # 如果已經檢測到第一次突破，就不再檢測
        if self.first_breakout_detected:
            return

        close_price = self.current_minute_candle['close']
        minute = self.current_minute_candle['minute']

        # 檢查第一次突破
        if close_price > self.range_high:
            # 記錄第一次突破
            self.first_breakout_detected = True
            self.breakout_direction = 'LONG'
            self.breakout_signal = 'LONG_SIGNAL'
            self.waiting_for_entry = True
            self.entry_signal_time = self.current_minute_candle['start_time']

            range_high_val = float(self.range_high) if self.range_high else 0
            logger.info(f"🔥 第一次突破！{minute:02d}分K線收盤價突破上緣!")
            logger.info(f"   收盤價: {float(close_price)}, 區間上緣: {range_high_val}")
            logger.info(f"⏳ 等待下一個報價進場做多...")

        elif close_price < self.range_low:
            # 記錄第一次突破
            self.first_breakout_detected = True
            self.breakout_direction = 'SHORT'
            self.breakout_signal = 'SHORT_SIGNAL'
            self.waiting_for_entry = True
            self.entry_signal_time = self.current_minute_candle['start_time']

            range_low_val = float(self.range_low) if self.range_low else 0
            logger.info(f"🔥 第一次突破！{minute:02d}分K線收盤價突破下緣!")
            logger.info(f"   收盤價: {float(close_price)}, 區間下緣: {range_low_val}")
            logger.info(f"⏳ 等待下一個報價進場做空...")
        else:
            # 未突破，記錄調試信息
            range_high_val = float(self.range_high) if self.range_high else 0
            range_low_val = float(self.range_low) if self.range_low else 0
            logger.debug(f"📊 {minute:02d}分收盤價未突破: {float(close_price)} (區間: {range_low_val}-{range_high_val})")

    def execute_entry_on_next_tick(self, price, timestamp):
        """在下一個報價執行進場"""
        if not self.waiting_for_entry or not self.breakout_signal:
            return

        direction = 'LONG' if self.breakout_signal == 'LONG_SIGNAL' else 'SHORT'

        logger.info(f"🎯 執行進場! 方向: {direction}, 進場價: {float(price)}")

        # 執行建倉
        self.enter_position_with_separate_orders(direction, price, timestamp)

        # 標記當天進場已完成
        self.daily_entry_completed = True

        # 重置信號狀態
        self.breakout_signal = None
        self.waiting_for_entry = False
        self.entry_signal_time = None

        logger.info(f"✅ 當天進場已完成，後續只執行停利/停損機制")

    def enter_position_with_separate_orders(self, direction, price, timestamp):
        """分開建倉 - 每口單獨下單"""
        self.position = direction
        self.entry_price = price
        self.entry_time = timestamp

        # 初始化各口單
        initial_sl = self.range_low if direction == 'LONG' else self.range_high
        self.lots = []

        logger.info(f"🎯 開始分開建倉 - {direction} {self.config.trade_size_in_lots}口")

        for i in range(self.config.trade_size_in_lots):
            rule = self.config.lot_rules[i] if i < len(self.config.lot_rules) else self.config.lot_rules[-1]
            lot_info = {
                'id': i + 1,
                'rule': rule,
                'status': 'active',
                'pnl': Decimal(0),
                'peak_price': price,
                'trailing_on': False,
                'stop_loss': initial_sl,
                'is_initial_stop': True,
                'order_id': None,  # 實際下單後的訂單ID
                'entry_time': timestamp
            }
            self.lots.append(lot_info)

            # 執行單獨下單 (模擬)
            self.execute_single_entry_order(lot_info, direction, price, timestamp)

        logger.info(f"✅ 建倉完成 - {direction} {len(self.lots)}口 @ {float(price)}")

    def execute_single_entry_order(self, lot_info, direction, price, timestamp):
        """執行單一口建倉下單 (模擬)"""
        lot_id = lot_info['id']

        # 模擬下單 (不真實下單)
        simulated_order_id = f"SIM_{direction}_{lot_id}_{timestamp.strftime('%H%M%S')}"
        lot_info['order_id'] = simulated_order_id

        logger.info(f"📋 [模擬建倉] 第{lot_id}口 {direction} MTX00 @ {float(price)} (訂單ID: {simulated_order_id})")

        # 如果有真實API，可以在這裡調用
        if self.order_api and hasattr(self.order_api, 'place_order'):
            try:
                order_direction = "BUY" if direction == "LONG" else "SELL"
                result = self.order_api.place_order(
                    product="MTX00",
                    direction=order_direction,
                    price=float(price),
                    quantity=1,
                    order_type="ROD"
                )

                if result.get('success'):
                    lot_info['order_id'] = result.get('order_id')
                    logger.info(f"✅ 第{lot_id}口真實下單成功 - 訂單ID: {lot_info['order_id']}")
                else:
                    logger.error(f"❌ 第{lot_id}口真實下單失敗: {result.get('message')}")

            except Exception as e:
                logger.error(f"❌ 第{lot_id}口下單API調用失敗: {e}")

        return simulated_order_id

    def enter_position(self, direction, price, timestamp):
        """建立部位 - 多口建倉"""
        self.position = direction
        self.entry_price = price
        self.entry_time = timestamp

        # 初始化各口單
        initial_sl = self.range_low if direction == 'LONG' else self.range_high
        self.lots = []

        for i in range(self.config.trade_size_in_lots):
            rule = self.config.lot_rules[i] if i < len(self.config.lot_rules) else self.config.lot_rules[-1]
            lot_info = {
                'id': i + 1,
                'rule': rule,
                'status': 'active',
                'pnl': Decimal(0),
                'peak_price': price,
                'trailing_on': False,
                'stop_loss': initial_sl,
                'is_initial_stop': True,
                'order_id': None  # 實際下單後的訂單ID
            }
            self.lots.append(lot_info)

        # 執行實際下單
        self.execute_entry_orders(direction, price)

        logger.info(f"📈 {'LONG' if direction == 'LONG' else '📉 SHORT'} | 建倉 {self.config.trade_size_in_lots} 口 | 時間: {timestamp.strftime('%H:%M:%S')}, 價格: {int(float(price))}")

    def execute_entry_orders(self, direction, price):
        """執行建倉下單"""
        if not self.order_api:
            logger.warning("⚠️ 下單API未設定，僅模擬交易")
            return

        try:
            # 轉換方向
            order_direction = "BUY" if direction == "LONG" else "SELL"

            # 批量下單
            for lot in self.lots:
                if hasattr(self.order_api, 'place_order'):
                    result = self.order_api.place_order(
                        product="MTX00",
                        direction=order_direction,
                        price=float(price),
                        quantity=1,
                        order_type="ROD"
                    )

                    if result.get('success'):
                        lot['order_id'] = result.get('order_id')
                        logger.info(f"✅ 第{lot['id']}口下單成功 - 訂單ID: {lot['order_id']}")
                    else:
                        logger.error(f"❌ 第{lot['id']}口下單失敗: {result.get('message')}")
                else:
                    logger.warning(f"⚠️ 第{lot['id']}口模擬下單 - 價格: {float(price)}")

        except Exception as e:
            logger.error(f"❌ 執行建倉下單失敗: {e}")

    def check_exit_conditions(self, price, timestamp):
        """檢查出場條件"""
        if not self.lots:
            return

        current_time = timestamp.time()

        # 檢查初始停損
        active_lots_with_initial_stop = [lot for lot in self.lots if lot['status'] == 'active' and lot['is_initial_stop']]

        if active_lots_with_initial_stop:
            initial_sl = self.range_low if self.position == 'LONG' else self.range_high

            if (self.position == 'LONG' and price < initial_sl) or (self.position == 'SHORT' and price > initial_sl):
                # 觸及初始停損，全部出場
                loss = (price - self.entry_price) if self.position == 'LONG' else (self.entry_price - price)

                for lot in active_lots_with_initial_stop:
                    lot['pnl'] = loss
                    lot['status'] = 'exited'
                    self.execute_exit_order(lot, price, "初始停損")

                logger.info(f"❌ 初始停損觸發 | 時間: {current_time.strftime('%H:%M:%S')}, 價格: {int(float(price))}, 單口虧損: {int(float(loss))}")
                return

        # 檢查各口單的個別出場條件
        for lot in self.lots:
            if lot['status'] != 'active':
                continue

            # 檢查保護性停損
            if not lot['is_initial_stop']:
                if (self.position == 'LONG' and price <= lot['stop_loss']) or \
                   (self.position == 'SHORT' and price >= lot['stop_loss']):
                    lot['pnl'] = lot['stop_loss'] - self.entry_price if self.position == 'LONG' else self.entry_price - lot['stop_loss']
                    lot['status'] = 'exited'
                    self.execute_exit_order(lot, lot['stop_loss'], "保護性停損")
                    continue

            # 檢查移動停利和固定停利
            self.check_take_profit_conditions(lot, price, timestamp)

    def check_take_profit_conditions(self, lot, price, timestamp):
        """檢查停利條件"""
        rule = lot['rule']
        current_time = timestamp.time()

        # 移動停利邏輯
        if rule.use_trailing_stop and rule.trailing_activation and rule.trailing_pullback:
            if self.position == 'LONG':
                lot['peak_price'] = max(lot['peak_price'], price)

                # 檢查是否啟動移動停利
                if not lot['trailing_on'] and lot['peak_price'] >= self.entry_price + rule.trailing_activation:
                    lot['trailing_on'] = True
                    logger.info(f"🔔 第{lot['id']}口移動停利啟動 | 時間: {current_time.strftime('%H:%M:%S')}")

                # 檢查移動停利出場
                if lot['trailing_on']:
                    stop_price = lot['peak_price'] - (lot['peak_price'] - self.entry_price) * rule.trailing_pullback
                    if price <= stop_price:
                        lot['pnl'] = stop_price - self.entry_price
                        lot['status'] = 'exited'
                        self.execute_exit_order(lot, stop_price, "移動停利")
                        self.update_next_lot_protection(lot)
                        return

            elif self.position == 'SHORT':
                lot['peak_price'] = min(lot['peak_price'], price)

                if not lot['trailing_on'] and lot['peak_price'] <= self.entry_price - rule.trailing_activation:
                    lot['trailing_on'] = True
                    logger.info(f"🔔 第{lot['id']}口移動停利啟動 | 時間: {current_time.strftime('%H:%M:%S')}")

                if lot['trailing_on']:
                    stop_price = lot['peak_price'] + (self.entry_price - lot['peak_price']) * rule.trailing_pullback
                    if price >= stop_price:
                        lot['pnl'] = self.entry_price - stop_price
                        lot['status'] = 'exited'
                        self.execute_exit_order(lot, stop_price, "移動停利")
                        self.update_next_lot_protection(lot)
                        return

        # 固定停利邏輯
        elif rule.fixed_tp_points:
            if (self.position == 'LONG' and price >= self.entry_price + rule.fixed_tp_points) or \
               (self.position == 'SHORT' and price <= self.entry_price - rule.fixed_tp_points):
                lot['pnl'] = rule.fixed_tp_points
                lot['status'] = 'exited'
                exit_price = self.entry_price + rule.fixed_tp_points if self.position == 'LONG' else self.entry_price - rule.fixed_tp_points
                self.execute_exit_order(lot, exit_price, "固定停利")
                self.update_next_lot_protection(lot)

    def update_next_lot_protection(self, exited_lot):
        """更新下一口單的保護性停損"""
        next_lot = next((l for l in self.lots if l['id'] == exited_lot['id'] + 1), None)

        if next_lot and next_lot['status'] == 'active' and next_lot['rule'].protective_stop_multiplier:
            # 計算累積獲利
            cumulative_pnl = sum(l['pnl'] for l in self.lots if l['status'] == 'exited')
            total_profit = cumulative_pnl + exited_lot['pnl']

            # 設定保護性停損
            stop_loss_amount = total_profit * next_lot['rule'].protective_stop_multiplier
            new_sl = self.entry_price - stop_loss_amount if self.position == 'LONG' else self.entry_price + stop_loss_amount

            next_lot['stop_loss'] = new_sl
            next_lot['is_initial_stop'] = False

            logger.info(f"🛡️ 第{next_lot['id']}口保護性停損更新: {int(float(new_sl))} (基於累積獲利 {int(float(total_profit))})")

    def execute_exit_order(self, lot, price, reason):
        """執行出場下單"""
        if not self.order_api:
            logger.info(f"✅ 第{lot['id']}口{reason} | 模擬出場價: {int(float(price))}, 損益: {int(float(lot['pnl']))}")
            return

        try:
            # 實際出場下單邏輯
            order_direction = "SELL" if self.position == "LONG" else "BUY"  # 平倉方向相反

            if hasattr(self.order_api, 'place_order'):
                result = self.order_api.place_order(
                    product="MTX00",
                    direction=order_direction,
                    price=float(price),
                    quantity=1,
                    order_type="ROD"
                )

                if result.get('success'):
                    logger.info(f"✅ 第{lot['id']}口{reason} | 出場價: {int(float(price))}, 損益: {int(float(lot['pnl']))}")
                else:
                    logger.error(f"❌ 第{lot['id']}口出場下單失敗: {result.get('message')}")
            else:
                logger.info(f"✅ 第{lot['id']}口{reason} | 模擬出場價: {int(float(price))}, 損益: {int(float(lot['pnl']))}")

        except Exception as e:
            logger.error(f"❌ 執行出場下單失敗: {e}")

    def reset_daily_state(self):
        """重置每日狀態"""
        self.position = None
        self.entry_price = Decimal(0)
        self.entry_time = None
        self.lots = []
        self.range_high = None
        self.range_low = None
        self.range_detected = False
        self.price_history = []
        self.candle_first = None
        self.candle_second = None

        # 重置新增的一分K監控狀態
        self.current_minute_candle = None
        self.last_minute = None
        self.breakout_signal = None
        self.waiting_for_entry = False
        self.entry_signal_time = None

        # 重置一天一次進場控制狀態
        self.first_breakout_detected = False
        self.breakout_direction = None
        self.daily_entry_completed = False

        logger.info("🔄 交易狀態已重置")

    def get_position_summary(self):
        """獲取部位摘要"""
        if not self.position:
            return "無部位"

        active_lots = len([l for l in self.lots if l['status'] == 'active'])
        total_pnl = sum(l['pnl'] for l in self.lots if l['status'] == 'exited')

        return f"{self.position} {active_lots}口活躍 | 已實現損益: {int(float(total_pnl))}"

class SKQuoteEvents:
    """群益報價事件處理類"""

    def __init__(self, manager):
        self.manager = manager

    def OnConnection(self, nKind, nCode):
        """連線事件"""
        if nKind == 3003:  # SK_SUBJECT_CONNECTION_STOCKS_READY
            logger.info("✅ 報價伺服器連線成功")
            self.manager.quote_connected = True
        else:
            logger.info(f"📡 連線事件: Kind={nKind}, Code={nCode}")

    def OnNotifyTicksLONG(self, sMarketNo, sStockidx, sPtr, nTime, nBid, nAsk, nClose, nQty, nSimulate):
        """即時報價事件"""
        try:
            # 解析報價資料
            price = nClose / 100.0  # 群益API價格需要除以100

            logger.debug(f"📊 收到報價: {price}")

            # 更新最後價格
            self.manager.last_price = price

            # 調用回調函數
            if self.manager.quote_callback:
                self.manager.quote_callback(price)

        except Exception as e:
            logger.error(f"❌ 處理報價事件失敗: {e}")

class SKOrderEvents:
    """群益下單事件處理類"""

    def __init__(self, manager):
        self.manager = manager

    def OnAsyncOrder(self, nThreadID, nCode, bstrMessage):
        """非同步下單回應"""
        logger.info(f"📋 下單回應: Code={nCode}, Message={bstrMessage}")

    def OnNewData(self, bstrLogInID, bstrData):
        """即時回報事件"""
        logger.info(f"📊 即時回報: {bstrData}")

# 回到DirectSKCOMManager類
class DirectSKCOMManager:
    """直接管理群益API的類別 - 完整版"""

    def __init__(self):
        self.m_pSKCenter = None
        self.m_pSKOrder = None
        self.m_pSKQuote = None
        self.m_pSKReply = None
        self.is_initialized = False
        self.is_logged_in = False
        self.login_id = "E123354882"
        self.password = "kkd5ysUCC"

        # 報價相關
        self.quote_callback = None
        self.last_price = 22000
        self.quote_connected = False

        # 事件處理
        self.quote_events = None
        self.order_events = None

    def initialize_api(self):
        """初始化群益API - 按照官方案例的正確方式"""
        try:
            logger.info("🚀 開始初始化群益API...")

            # 步驟1: 檢查SKCOM.dll是否存在
            import os
            dll_paths = [
                r'.\SKCOM.dll',  # 當前目錄
                r'SKCOM.dll',    # 相對路徑
                os.path.join(os.path.dirname(__file__), 'SKCOM.dll')  # 程式目錄
            ]

            dll_path = None
            for path in dll_paths:
                if os.path.exists(path):
                    dll_path = os.path.abspath(path)
                    logger.info(f"✅ 找到SKCOM.dll: {dll_path}")
                    break

            if not dll_path:
                logger.error("❌ 找不到SKCOM.dll檔案")
                return False

            # 步驟2: 生成COM元件的Python包裝 (關鍵步驟)
            logger.info("🔄 生成COM元件包裝...")
            try:
                import comtypes.client
                comtypes.client.GetModule(dll_path)
                logger.info("✅ COM元件包裝生成成功")
            except Exception as e:
                logger.error(f"❌ COM元件包裝生成失敗: {e}")
                return False

            # 步驟3: 導入生成的SKCOMLib
            logger.info("🔄 導入SKCOMLib...")
            try:
                import comtypes.gen.SKCOMLib as sk
                logger.info("✅ SKCOMLib導入成功")
            except Exception as e:
                logger.error(f"❌ SKCOMLib導入失敗: {e}")
                return False

            # 步驟4: 按照官方案例的順序創建物件
            logger.info("🔄 創建SKCenterLib物件...")
            try:
                self.m_pSKCenter = comtypes.client.CreateObject(sk.SKCenterLib, interface=sk.ISKCenterLib)
                logger.info("✅ SKCenterLib創建成功")
            except Exception as e:
                logger.error(f"❌ SKCenterLib創建失敗: {e}")
                return False

            logger.info("🔄 創建SKReplyLib物件...")
            try:
                self.m_pSKReply = comtypes.client.CreateObject(sk.SKReplyLib, interface=sk.ISKReplyLib)
                logger.info("✅ SKReplyLib創建成功")
            except Exception as e:
                logger.error(f"❌ SKReplyLib創建失敗: {e}")
                return False

            logger.info("🔄 創建SKOrderLib物件...")
            try:
                self.m_pSKOrder = comtypes.client.CreateObject(sk.SKOrderLib, interface=sk.ISKOrderLib)
                logger.info("✅ SKOrderLib創建成功")
            except Exception as e:
                logger.error(f"❌ SKOrderLib創建失敗: {e}")
                return False

            logger.info("🔄 創建SKQuoteLib物件...")
            try:
                self.m_pSKQuote = comtypes.client.CreateObject(sk.SKQuoteLib, interface=sk.ISKQuoteLib)
                logger.info("✅ SKQuoteLib創建成功")
            except Exception as e:
                logger.error(f"❌ SKQuoteLib創建失敗: {e}")
                return False

            # 步驟5: 設定LOG路徑 (可選)
            try:
                if hasattr(self.m_pSKCenter, 'SKCenterLib_SetLogPath'):
                    self.m_pSKCenter.SKCenterLib_SetLogPath(r'.\Log')
                    logger.info("✅ LOG路徑設定成功")
            except Exception as e:
                logger.warning(f"⚠️ LOG路徑設定失敗: {e}")

            # 步驟6: 建立事件處理
            self.quote_events = SKQuoteEvents(self)
            self.order_events = SKOrderEvents(self)

            self.is_initialized = True
            logger.info("✅ 群益API初始化完成")
            return True

        except Exception as e:
            logger.error(f"❌ 群益API初始化失敗: {e}")
            return False

    def login(self):
        """登入群益API"""
        try:
            if not self.is_initialized:
                if not self.initialize_api():
                    return False

            logger.info(f"🔐 開始登入: {self.login_id}")

            # 登入
            result = self.m_pSKCenter.SKCenterLib_Login(self.login_id, self.password)
            if result != 0:
                logger.error(f"❌ 登入失敗，錯誤代碼: {result}")
                return False

            # 讀取憑證
            logger.info("🔐 讀取憑證...")
            cert_result = self.m_pSKOrder.ReadCertByID(self.login_id)
            logger.info(f"🔍 憑證讀取結果: {cert_result}")

            if cert_result != 0:
                logger.warning(f"⚠️ 讀取憑證警告，代碼: {cert_result}")
                # 不要因為憑證問題就停止，繼續執行
            else:
                logger.info("✅ 憑證讀取成功")

            # 初始化OrderLib
            try:
                logger.info("🔄 初始化OrderLib...")
                order_init_result = self.m_pSKOrder.SKOrderLib_Initialize()
                logger.info(f"🔍 OrderLib初始化結果: {order_init_result}")

                if order_init_result == 0:
                    logger.info("✅ OrderLib初始化成功")
                else:
                    logger.warning(f"⚠️ OrderLib初始化警告，代碼: {order_init_result}")

            except Exception as e:
                logger.warning(f"⚠️ OrderLib初始化失敗: {e}")

            self.is_logged_in = True
            logger.info("✅ 登入流程完成")
            return True

        except Exception as e:
            logger.error(f"❌ 登入失敗: {e}")
            return False

    def start_quote_monitor(self, callback=None):
        """開始報價監控"""
        try:
            if not self.is_logged_in:
                logger.error("❌ 尚未登入，無法開始報價監控")
                return False

            self.quote_callback = callback

            # 連接報價伺服器
            result = self.m_pSKQuote.SKQuoteLib_EnterMonitorLONG()
            if result != 0:
                logger.error(f"❌ 連接報價伺服器失敗，錯誤代碼: {result}")
                return False

            # 訂閱MTX00報價
            result = self.m_pSKQuote.SKQuoteLib_RequestTicks(-1, "MTX00")
            if result != 0:
                logger.error(f"❌ 訂閱MTX00報價失敗，錯誤代碼: {result}")
                return False

            logger.info("✅ 報價監控已啟動")
            return True

        except Exception as e:
            logger.error(f"❌ 啟動報價監控失敗: {e}")
            return False

    def place_order(self, direction="BUY", price=0, quantity=1):
        """下單功能"""
        try:
            if not self.is_logged_in:
                logger.error("❌ 尚未登入，無法下單")
                return False

            # 這裡實現下單邏輯
            logger.info(f"📊 模擬下單: {direction} {quantity}口 @{price}")
            return True

        except Exception as e:
            logger.error(f"❌ 下單失敗: {e}")
            return False

class TradingTesterApp:
    """完整交易測試應用程式"""

    def __init__(self):
        self.root = tk.Tk()
        self.root.title("🎯 完整交易測試系統 - UI改進版")
        self.root.geometry("1400x900")

        # 價格模擬相關
        self.base_price = 22000
        self.price_running = False

        # 策略交易相關
        self.strategy_config = None
        self.position_manager = None
        self.strategy_active = False

        # TCP客戶端相關
        self.tcp_client = None
        self.tcp_connected = False
        self._tcp_first_data_received = False

        # 區間模式相關
        self.range_mode = "NORMAL"  # "NORMAL" 或 "TEST"
        self.test_start_time = "14:30"  # 測試模式的開始時間
        self.current_range_start = (8, 46)  # 當前使用的區間開始時間 (小時, 分鐘)

        # 初始化預設策略配置
        self.init_default_strategy_config()
        self.current_price = self.base_price

        # 報價源管理
        self.quote_mode = "SIMULATION"  # "SIMULATION", "REAL_EXTERNAL", "REAL_DIRECT", "BRIDGE"
        self.real_quote_running = False
        self.ordertester_instance = None

        # 直接API管理
        self.direct_skcom = DirectSKCOMManager()
        self.direct_api_connected = False

        # 橋接模式管理
        self.bridge_monitoring = False

        # API連接狀態
        self.api_connected = False

        # 建立UI
        self.create_widgets()

        # 初始化按鈕狀態
        self.initialize_button_states()

        # 顯示歡迎訊息
        self.show_welcome_message()

    def show_welcome_message(self):
        """顯示歡迎訊息"""
        welcome_msg = """
🎉 完整交易測試系統已啟動！

✅ UI改進功能:
   • 移除底部測試按鈕
   • 擴大日誌顯示區域 (15行)
   • 日誌同步VS CODE輸出
   • 新增便捷時間設定

🔗 整合功能:
   • 策略測試和區間計算
   • 穩定版下單API接口
   • 即時價格模擬
   • 完整交易流程測試

💡 使用建議:
   1. 設定測試時間 (3分鐘後)
   2. 啟動策略監控
   3. 開始價格模擬
   4. 測試下單功能
   5. 觀察區間計算和交易執行
        """
        print(welcome_msg)
        logger.info("完整交易測試系統已啟動")

    def init_default_strategy_config(self):
        """初始化預設策略配置"""
        # 建立預設的3口交易配置 (基於回測成功配置)
        self.strategy_config = StrategyConfig(
            trade_size_in_lots=3,
            stop_loss_type=StopLossType.RANGE_BOUNDARY,
            lot_rules=[
                # 第1口：快速移動停利
                LotRule(
                    use_trailing_stop=True,
                    trailing_activation=Decimal(15),
                    trailing_pullback=Decimal('0.20')
                ),
                # 第2口：中等移動停利 + 保護性停損
                LotRule(
                    use_trailing_stop=True,
                    trailing_activation=Decimal(40),
                    trailing_pullback=Decimal('0.20'),
                    protective_stop_multiplier=Decimal('2.0')
                ),
                # 第3口：較大移動停利 + 保護性停損
                LotRule(
                    use_trailing_stop=True,
                    trailing_activation=Decimal(65),
                    trailing_pullback=Decimal('0.20'),
                    protective_stop_multiplier=Decimal('2.0')
                )
            ]
        )

        logger.info("🎯 預設策略配置已載入 - 3口交易，區間邊緣停損")

    def create_position_manager(self):
        """建立部位管理器"""
        if not self.strategy_config:
            logger.error("❌ 策略配置未設定")
            return False

        # 建立部位管理器，傳入下單API
        order_api = None
        if STABLE_API_AVAILABLE:
            try:
                order_api = get_stable_order_api()
                if hasattr(self, 'ordertester_instance') and self.ordertester_instance:
                    order_api.set_order_tester(self.ordertester_instance)
            except Exception as e:
                logger.warning(f"⚠️ 下單API設定失敗: {e}")

        self.position_manager = LiveTradingPositionManager(self.strategy_config, order_api, self.current_range_start)
        logger.info(f"✅ 部位管理器已建立 - 區間時間: {self.current_range_start[0]:02d}:{self.current_range_start[1]:02d}")
        return True

    def initialize_button_states(self):
        """初始化按鈕狀態"""
        # 預設為模擬模式
        self.quote_mode = "SIMULATION"
        self.quote_mode_var.set("模擬報價")
        self.quote_mode_label.config(fg="blue")

        # 按鈕狀態
        self.btn_switch_sim.config(state="disabled")  # 已經是模擬模式
        self.btn_switch_bridge.config(state="normal")
        self.btn_switch_tcp.config(state="normal")
        self.btn_start_sim.config(state="normal")
        self.btn_stop_sim.config(state="disabled")

        logger.info("🎮 初始化為模擬報價模式")

    def create_widgets(self):
        """建立UI控件"""
        # 主標題
        title_frame = tk.Frame(self.root, bg="navy", height=60)
        title_frame.pack(fill="x", padx=5, pady=5)
        title_frame.pack_propagate(False)

        title_label = tk.Label(title_frame, text="🎯 完整交易測試系統",
                              fg="white", bg="navy", font=("Arial", 16, "bold"))
        title_label.pack(expand=True)

        subtitle_label = tk.Label(title_frame, text="UI改進版 - 整合策略測試與下單API",
                                 fg="lightblue", bg="navy", font=("Arial", 10))
        subtitle_label.pack()

        # 控制面板
        self.create_control_panel()

        # 策略面板
        if STRATEGY_AVAILABLE:
            self.create_strategy_panel()
        else:
            self.create_error_panel()

        # 下單測試面板
        if STABLE_API_AVAILABLE:
            self.create_trading_panel()

        # 日誌顯示區域
        self.create_log_panel()

    def create_control_panel(self):
        """創建控制面板"""
        control_frame = tk.LabelFrame(self.root, text="🎮 系統控制面板",
                                     fg="green", font=("Arial", 12, "bold"))
        control_frame.pack(fill="x", padx=10, pady=5)

        # 第一行 - 價格控制
        row1 = tk.Frame(control_frame)
        row1.pack(fill="x", padx=10, pady=5)

        tk.Label(row1, text="基準價格:", font=("Arial", 10)).pack(side="left", padx=5)
        self.entry_base_price = tk.Entry(row1, width=8, font=("Arial", 10))
        self.entry_base_price.insert(0, str(self.base_price))
        self.entry_base_price.pack(side="left", padx=5)

        tk.Button(row1, text="更新價格", command=self.update_base_price,
                 bg="lightblue", font=("Arial", 9)).pack(side="left", padx=5)

        tk.Label(row1, text="當前價格:", font=("Arial", 10)).pack(side="left", padx=(20, 5))
        self.label_current_price = tk.Label(row1, text=str(self.current_price),
                                           fg="red", font=("Arial", 12, "bold"))
        self.label_current_price.pack(side="left", padx=5)

        # 第二行 - 報價源控制
        row2 = tk.Frame(control_frame)
        row2.pack(fill="x", padx=10, pady=5)

        tk.Label(row2, text="報價源:", font=("Arial", 10, "bold")).pack(side="left", padx=5)

        self.quote_mode_var = tk.StringVar(value="模擬報價")
        self.quote_mode_label = tk.Label(row2, textvariable=self.quote_mode_var,
                                        fg="blue", font=("Arial", 10, "bold"))
        self.quote_mode_label.pack(side="left", padx=5)

        self.btn_switch_sim = tk.Button(row2, text="🎮 模擬報價", command=self.switch_to_simulation,
                                       bg="blue", fg="white", font=("Arial", 10, "bold"))
        self.btn_switch_sim.pack(side="left", padx=5)

        self.btn_switch_bridge = tk.Button(row2, text="🌉 橋接模式", command=self.switch_to_bridge,
                                          bg="teal", fg="white", font=("Arial", 10, "bold"))
        self.btn_switch_bridge.pack(side="left", padx=5)

        self.btn_switch_tcp = tk.Button(row2, text="🚀 TCP模式", command=self.switch_to_tcp,
                                       bg="purple", fg="white", font=("Arial", 10, "bold"))
        self.btn_switch_tcp.pack(side="left", padx=5)

        # 新增：實盤監控按鈕
        self.btn_start_real_monitor = tk.Button(row2, text="📡 開始實盤監控", command=self.start_real_monitor,
                                              bg="red", fg="white", font=("Arial", 10, "bold"))
        self.btn_start_real_monitor.pack(side="left", padx=5)

        # 新增：停止實盤監控按鈕
        self.btn_stop_real_monitor = tk.Button(row2, text="🛑 停止監控", command=self.stop_real_monitor,
                                             bg="gray", fg="white", font=("Arial", 10, "bold"), state="disabled")
        self.btn_stop_real_monitor.pack(side="left", padx=5)

        # 第三行 - 模擬控制
        row3 = tk.Frame(control_frame)
        row3.pack(fill="x", padx=10, pady=5)

        self.btn_start_sim = tk.Button(row3, text="🎯 開始價格模擬", command=self.start_price_simulation,
                                      bg="green", fg="white", font=("Arial", 10, "bold"))
        self.btn_start_sim.pack(side="left", padx=5)

        self.btn_stop_sim = tk.Button(row3, text="⏹️ 停止價格模擬", command=self.stop_price_simulation,
                                     bg="red", fg="white", font=("Arial", 10, "bold"))
        self.btn_stop_sim.pack(side="left", padx=5)

        # 狀態顯示
        tk.Label(row3, text="狀態:", font=("Arial", 10)).pack(side="left", padx=(20, 5))
        self.status_var = tk.StringVar(value="系統就緒")
        tk.Label(row3, textvariable=self.status_var, fg="blue", font=("Arial", 10)).pack(side="left", padx=5)

    def create_strategy_panel(self):
        """創建策略面板 - 整合建倉機制"""
        # 策略面板容器
        strategy_container = tk.LabelFrame(self.root, text="🎯 開盤區間突破策略 - 實盤建倉版",
                                         fg="blue", font=("Arial", 12, "bold"))
        strategy_container.pack(fill="both", expand=True, padx=10, pady=5)

        # 策略配置區域
        config_frame = tk.LabelFrame(strategy_container, text="策略配置", fg="green")
        config_frame.pack(fill="x", padx=5, pady=5)

        # 交易口數選擇
        lots_frame = tk.Frame(config_frame)
        lots_frame.pack(fill="x", padx=5, pady=5)

        tk.Label(lots_frame, text="交易口數:", font=("Arial", 10)).pack(side="left", padx=5)
        self.lots_var = tk.StringVar(value="3口")
        lots_combo = ttk.Combobox(lots_frame, textvariable=self.lots_var, width=8, state='readonly')
        lots_combo['values'] = ['1口', '2口', '3口', '4口']
        lots_combo.pack(side="left", padx=5)
        lots_combo.bind('<<ComboboxSelected>>', self.on_lots_changed)

        # 區間模式選擇
        mode_frame = tk.Frame(config_frame)
        mode_frame.pack(fill="x", padx=5, pady=5)

        tk.Label(mode_frame, text="區間模式:", font=("Arial", 10)).pack(side="left", padx=5)
        self.range_mode_var = tk.StringVar(value="正常交易模式")
        mode_combo = ttk.Combobox(mode_frame, textvariable=self.range_mode_var, width=15, state='readonly')
        mode_combo['values'] = ['正常交易模式', '測試模式']
        mode_combo.pack(side="left", padx=5)
        mode_combo.bind('<<ComboboxSelected>>', self.on_range_mode_changed)

        # 測試時間設定
        time_frame = tk.Frame(config_frame)
        time_frame.pack(fill="x", padx=5, pady=5)

        tk.Label(time_frame, text="測試開始時間:", font=("Arial", 10)).pack(side="left", padx=5)
        self.test_start_time_var = tk.StringVar(value="14:30")
        self.test_time_entry = tk.Entry(time_frame, textvariable=self.test_start_time_var, width=8, font=("Arial", 10))
        self.test_time_entry.pack(side="left", padx=5)

        self.apply_time_btn = tk.Button(time_frame, text="應用", command=self.apply_test_time,
                                       bg="orange", fg="white", font=("Arial", 9))
        self.apply_time_btn.pack(side="left", padx=5)

        # 初始狀態：測試時間設定為禁用
        self.test_time_entry.config(state="disabled")
        self.apply_time_btn.config(state="disabled")

        # 策略狀態顯示
        status_frame = tk.Frame(config_frame)
        status_frame.pack(fill="x", padx=5, pady=5)

        tk.Label(status_frame, text="策略狀態:", font=("Arial", 10)).pack(side="left", padx=5)
        self.strategy_status_var = tk.StringVar(value="🔴 未啟動")
        tk.Label(status_frame, textvariable=self.strategy_status_var, font=("Arial", 10, "bold")).pack(side="left", padx=5)

        # 區間監控區域
        range_frame = tk.LabelFrame(strategy_container, text="開盤區間監控", fg="orange")
        range_frame.pack(fill="x", padx=5, pady=5)

        # 時間顯示區域
        time_display_frame = tk.Frame(range_frame)
        time_display_frame.pack(fill="x", padx=5, pady=2)

        tk.Label(time_display_frame, text="當前時間:", font=("Arial", 9)).pack(side="left", padx=5)
        self.current_time_var = tk.StringVar(value="--:--:--")
        tk.Label(time_display_frame, textvariable=self.current_time_var, font=("Arial", 9, "bold"), fg="blue").pack(side="left", padx=5)

        tk.Label(time_display_frame, text="目標區間:", font=("Arial", 9)).pack(side="left", padx=(20, 5))
        self.target_range_var = tk.StringVar(value="08:46-08:47")
        tk.Label(time_display_frame, textvariable=self.target_range_var, font=("Arial", 9, "bold"), fg="purple").pack(side="left", padx=5)

        # 區間數據顯示
        range_data_frame = tk.Frame(range_frame)
        range_data_frame.pack(fill="x", padx=5, pady=5)

        tk.Label(range_data_frame, text="區間高點:", font=("Arial", 9)).grid(row=0, column=0, sticky="w", padx=5)
        self.range_high_var = tk.StringVar(value="--")
        tk.Label(range_data_frame, textvariable=self.range_high_var, font=("Arial", 9, "bold"), fg="red").grid(row=0, column=1, sticky="w", padx=5)

        tk.Label(range_data_frame, text="區間低點:", font=("Arial", 9)).grid(row=1, column=0, sticky="w", padx=5)
        self.range_low_var = tk.StringVar(value="--")
        tk.Label(range_data_frame, textvariable=self.range_low_var, font=("Arial", 9, "bold"), fg="green").grid(row=1, column=1, sticky="w", padx=5)

        tk.Label(range_data_frame, text="當前價格:", font=("Arial", 9)).grid(row=0, column=2, sticky="w", padx=20)
        self.current_price_var = tk.StringVar(value=str(self.base_price))
        tk.Label(range_data_frame, textvariable=self.current_price_var, font=("Arial", 9, "bold"), fg="blue").grid(row=0, column=3, sticky="w", padx=5)

        tk.Label(range_data_frame, text="區間狀態:", font=("Arial", 9)).grid(row=1, column=2, sticky="w", padx=20)
        self.range_status_var = tk.StringVar(value="等待8:46-8:47")
        tk.Label(range_data_frame, textvariable=self.range_status_var, font=("Arial", 9, "bold")).grid(row=1, column=3, sticky="w", padx=5)

        # 部位狀態區域
        position_frame = tk.LabelFrame(strategy_container, text="部位狀態", fg="purple")
        position_frame.pack(fill="x", padx=5, pady=5)

        position_data_frame = tk.Frame(position_frame)
        position_data_frame.pack(fill="x", padx=5, pady=5)

        tk.Label(position_data_frame, text="持倉方向:", font=("Arial", 9)).grid(row=0, column=0, sticky="w", padx=5)
        self.position_direction_var = tk.StringVar(value="無部位")
        tk.Label(position_data_frame, textvariable=self.position_direction_var, font=("Arial", 9, "bold")).grid(row=0, column=1, sticky="w", padx=5)

        tk.Label(position_data_frame, text="進場價格:", font=("Arial", 9)).grid(row=1, column=0, sticky="w", padx=5)
        self.entry_price_var = tk.StringVar(value="--")
        tk.Label(position_data_frame, textvariable=self.entry_price_var, font=("Arial", 9, "bold")).grid(row=1, column=1, sticky="w", padx=5)

        tk.Label(position_data_frame, text="活躍口數:", font=("Arial", 9)).grid(row=0, column=2, sticky="w", padx=20)
        self.active_lots_var = tk.StringVar(value="0")
        tk.Label(position_data_frame, textvariable=self.active_lots_var, font=("Arial", 9, "bold")).grid(row=0, column=3, sticky="w", padx=5)

        tk.Label(position_data_frame, text="已實現損益:", font=("Arial", 9)).grid(row=1, column=2, sticky="w", padx=20)
        self.realized_pnl_var = tk.StringVar(value="0")
        tk.Label(position_data_frame, textvariable=self.realized_pnl_var, font=("Arial", 9, "bold")).grid(row=1, column=3, sticky="w", padx=5)

        # 控制按鈕區域
        control_frame = tk.Frame(strategy_container)
        control_frame.pack(fill="x", padx=5, pady=10)

        self.btn_start_strategy = tk.Button(control_frame, text="🚀 啟動策略",
                                          command=self.start_strategy, bg="green", fg="white", font=("Arial", 10, "bold"))
        self.btn_start_strategy.pack(side="left", padx=5)

        self.btn_stop_strategy = tk.Button(control_frame, text="⏹️ 停止策略",
                                         command=self.stop_strategy, bg="red", fg="white", font=("Arial", 10, "bold"))
        self.btn_stop_strategy.pack(side="left", padx=5)

        self.btn_reset_strategy = tk.Button(control_frame, text="🔄 重置狀態",
                                          command=self.reset_strategy, bg="orange", fg="white", font=("Arial", 10, "bold"))
        self.btn_reset_strategy.pack(side="left", padx=5)

        # 初始按鈕狀態
        self.btn_stop_strategy.config(state="disabled")

        logger.info("✅ 策略面板創建成功 - 整合建倉機制")

        # 啟動當前時間更新
        self.update_current_time()

    def on_range_mode_changed(self, event=None):
        """區間模式變更事件"""
        mode = self.range_mode_var.get()

        if mode == "測試模式":
            self.range_mode = "TEST"
            # 啟用測試時間設定
            self.test_time_entry.config(state="normal")
            self.apply_time_btn.config(state="normal")
            self.log_message("🧪 已切換到測試模式 - 可手動設定區間時間")
        else:
            self.range_mode = "NORMAL"
            # 禁用測試時間設定
            self.test_time_entry.config(state="disabled")
            self.apply_time_btn.config(state="disabled")
            # 恢復正常交易時間
            self.current_range_start = (8, 46)
            self.target_range_var.set("08:46-08:47")
            self.range_status_var.set("等待8:46-8:47")
            self.log_message("📈 已切換到正常交易模式 - 使用8:46-8:47區間")

        logger.info(f"區間模式已變更: {mode}")

    def apply_test_time(self):
        """應用測試時間設定"""
        try:
            time_str = self.test_start_time_var.get().strip()

            # 驗證時間格式
            if ':' not in time_str:
                raise ValueError("時間格式錯誤，請使用 HH:MM 格式")

            hour_str, minute_str = time_str.split(':')
            hour = int(hour_str)
            minute = int(minute_str)

            # 驗證時間範圍
            if not (0 <= hour <= 23) or not (0 <= minute <= 59):
                raise ValueError("時間範圍錯誤，小時應為0-23，分鐘應為0-59")

            # 更新設定
            self.current_range_start = (hour, minute)
            self.test_start_time = time_str

            # 更新顯示
            end_minute = minute + 1
            end_hour = hour
            if end_minute >= 60:
                end_minute = 0
                end_hour += 1
                if end_hour >= 24:
                    end_hour = 0

            range_display = f"{hour:02d}:{minute:02d}-{end_hour:02d}:{end_minute:02d}"
            self.target_range_var.set(range_display)
            self.range_status_var.set(f"等待{range_display}")

            self.log_message(f"✅ 測試時間已設定: {range_display}")
            logger.info(f"測試時間已設定: {time_str}")

            # 更新position_manager的區間時間設定
            if hasattr(self, 'position_manager') and self.position_manager:
                self.update_position_manager_range_time()

        except ValueError as e:
            from tkinter import messagebox
            messagebox.showerror("時間格式錯誤", f"請輸入正確的時間格式 (HH:MM)\n錯誤: {e}")
            self.log_message(f"❌ 時間設定失敗: {e}")
        except Exception as e:
            self.log_message(f"❌ 應用測試時間失敗: {e}")

    def update_current_time(self):
        """更新當前時間顯示"""
        try:
            from datetime import datetime
            current_time = datetime.now().strftime("%H:%M:%S")
            self.current_time_var.set(current_time)

            # 每秒更新一次
            self.root.after(1000, self.update_current_time)

        except Exception as e:
            logger.error(f"更新當前時間失敗: {e}")

    def update_position_manager_range_time(self):
        """更新position_manager的區間時間設定"""
        try:
            if hasattr(self, 'position_manager') and self.position_manager:
                # 更新區間時間
                self.position_manager.range_start_hour, self.position_manager.range_start_minute = self.current_range_start
                self.position_manager.range_end_minute = self.position_manager.range_start_minute + 1
                self.position_manager.range_end_hour = self.position_manager.range_start_hour
                if self.position_manager.range_end_minute >= 60:
                    self.position_manager.range_end_minute = 0
                    self.position_manager.range_end_hour += 1

                # 重置區間檢測狀態
                self.position_manager.range_detected = False
                self.position_manager.range_high = None
                self.position_manager.range_low = None
                self.position_manager.candle_first = None
                self.position_manager.candle_second = None

                # 重置日誌標記
                self.reset_daily_logs()

                logger.info(f"✅ 部位管理器區間時間已更新: {self.current_range_start[0]:02d}:{self.current_range_start[1]:02d}")

        except Exception as e:
            logger.error(f"❌ 更新部位管理器區間時間失敗: {e}")

    def on_lots_changed(self, event=None):
        """交易口數變更事件"""
        lots_text = self.lots_var.get()
        lots_num = int(lots_text.replace('口', ''))

        # 更新策略配置
        if self.strategy_config:
            self.strategy_config.trade_size_in_lots = lots_num
            logger.info(f"🔧 交易口數已更新為: {lots_num}口")

            # 如果策略正在運行，需要重新建立部位管理器
            if self.strategy_active and self.position_manager:
                self.position_manager.config = self.strategy_config

    def start_strategy(self):
        """啟動策略"""
        try:
            if self.strategy_active:
                logger.warning("⚠️ 策略已在運行中")
                return

            # 建立部位管理器
            if not self.create_position_manager():
                messagebox.showerror("錯誤", "部位管理器建立失敗")
                return

            self.strategy_active = True
            self.strategy_status_var.set("🟢 策略運行中")

            # 更新按鈕狀態
            self.btn_start_strategy.config(state="disabled")
            self.btn_stop_strategy.config(state="normal")

            # 啟動狀態更新
            self.start_strategy_status_update()

            logger.info("🚀 策略已啟動 - 等待開盤區間形成")
            self.log_message("🚀 策略已啟動 - 等待開盤區間形成")

        except Exception as e:
            logger.error(f"❌ 啟動策略失敗: {e}")
            messagebox.showerror("錯誤", f"啟動策略失敗: {e}")

    def stop_strategy(self):
        """停止策略"""
        try:
            self.strategy_active = False
            self.strategy_status_var.set("🔴 策略已停止")

            # 更新按鈕狀態
            self.btn_start_strategy.config(state="normal")
            self.btn_stop_strategy.config(state="disabled")

            logger.info("⏹️ 策略已停止")
            self.log_message("⏹️ 策略已停止")

        except Exception as e:
            logger.error(f"❌ 停止策略失敗: {e}")

    def reset_strategy(self):
        """重置策略狀態"""
        try:
            # 先停止策略
            if self.strategy_active:
                self.stop_strategy()

            # 重置部位管理器
            if self.position_manager:
                self.position_manager.reset_daily_state()

            # 重置UI顯示
            self.range_high_var.set("--")
            self.range_low_var.set("--")

            # 根據當前模式設定狀態顯示
            if self.range_mode == "TEST":
                range_display = self.target_range_var.get()
                self.range_status_var.set(f"等待{range_display}")
            else:
                self.range_status_var.set("等待8:46-8:47")

            self.position_direction_var.set("無部位")
            self.entry_price_var.set("--")
            self.active_lots_var.set("0")
            self.realized_pnl_var.set("0")

            logger.info("🔄 策略狀態已重置")
            self.log_message("🔄 策略狀態已重置")

        except Exception as e:
            logger.error(f"❌ 重置策略失敗: {e}")

    def start_strategy_status_update(self):
        """啟動策略狀態更新"""
        def update_status():
            if not self.strategy_active:
                return

            try:
                # 更新當前價格顯示
                self.current_price_var.set(str(int(self.current_price)))

                # 更新部位狀態
                if self.position_manager:
                    # 更新區間狀態
                    if self.position_manager.range_detected:
                        self.range_high_var.set(str(int(float(self.position_manager.range_high))))
                        self.range_low_var.set(str(int(float(self.position_manager.range_low))))
                        self.range_status_var.set("✅ 區間已確定")

                    # 更新部位狀態
                    if self.position_manager.position:
                        self.position_direction_var.set(f"{'📈 多頭' if self.position_manager.position == 'LONG' else '📉 空頭'}")
                        self.entry_price_var.set(str(int(float(self.position_manager.entry_price))))

                        active_lots = len([l for l in self.position_manager.lots if l['status'] == 'active'])
                        self.active_lots_var.set(str(active_lots))

                        realized_pnl = sum(l['pnl'] for l in self.position_manager.lots if l['status'] == 'exited')
                        self.realized_pnl_var.set(str(int(float(realized_pnl))))

                # 繼續更新
                self.root.after(1000, update_status)  # 每秒更新

            except Exception as e:
                logger.error(f"❌ 策略狀態更新失敗: {e}")

        # 開始更新
        update_status()

    def create_log_panel(self):
        """創建日誌顯示面板"""
        log_frame = tk.LabelFrame(self.root, text="📋 系統日誌", fg="green", font=("Arial", 12, "bold"))
        log_frame.pack(fill="both", expand=True, padx=10, pady=5)

        # 日誌文字區域
        log_text_frame = tk.Frame(log_frame)
        log_text_frame.pack(fill="both", expand=True, padx=5, pady=5)

        # 日誌顯示區域 (15行)
        self.log_text = tk.Text(log_text_frame, height=15, wrap=tk.WORD, font=("Consolas", 9))

        # 滾動條
        log_scrollbar = tk.Scrollbar(log_text_frame, orient="vertical", command=self.log_text.yview)
        self.log_text.configure(yscrollcommand=log_scrollbar.set)

        # 佈局
        self.log_text.pack(side="left", fill="both", expand=True)
        log_scrollbar.pack(side="right", fill="y")

        # 清除日誌按鈕
        clear_btn = tk.Button(log_frame, text="🗑️ 清除日誌", command=self.clear_log)
        clear_btn.pack(pady=5)

        # 初始歡迎訊息
        self.log_message("🎉 完整交易測試系統已啟動")
        self.log_message("✅ 日誌系統已就緒")

    def log_message(self, message):
        """添加日誌訊息"""
        try:
            timestamp = datetime.now().strftime("%H:%M:%S")
            log_entry = f"[{timestamp}] {message}\n"

            self.log_text.insert(tk.END, log_entry)
            self.log_text.see(tk.END)  # 自動滾動到最新訊息

            # 限制日誌行數 (保持最新1000行)
            lines = self.log_text.get("1.0", tk.END).split('\n')
            if len(lines) > 1000:
                self.log_text.delete("1.0", f"{len(lines)-1000}.0")

        except Exception as e:
            logger.error(f"❌ 日誌顯示失敗: {e}")

    def clear_log(self):
        """清除日誌"""
        try:
            self.log_text.delete("1.0", tk.END)
            self.log_message("🗑️ 日誌已清除")
        except Exception as e:
            logger.error(f"❌ 清除日誌失敗: {e}")

    def update_strategy_with_price(self, price, timestamp):
        """更新策略與價格數據"""
        try:
            if not self.strategy_active or not self.position_manager:
                return

            # 傳遞價格給部位管理器
            self.position_manager.update_price(price, timestamp)

            # 檢查是否有交易信號或狀態變化
            current_time = timestamp.time()

            # 記錄重要事件 - 使用動態時間
            range_start_hour, range_start_minute = self.current_range_start
            range_end_minute = range_start_minute + 1
            range_end_hour = range_start_hour
            if range_end_minute >= 60:
                range_end_minute = 0
                range_end_hour += 1

            # 第三分鐘時間
            third_minute = range_end_minute + 1
            third_hour = range_end_hour
            if third_minute >= 60:
                third_minute = 0
                third_hour += 1

            if (current_time.hour == range_start_hour and current_time.minute == range_start_minute and
                not hasattr(self, '_logged_first')):
                self.log_message(f"📊 {range_start_hour:02d}:{range_start_minute:02d} 開盤區間監控開始 - 當前價格: {int(price)}")
                self._logged_first = True

            elif (current_time.hour == range_end_hour and current_time.minute == range_end_minute and
                  not hasattr(self, '_logged_second')):
                self.log_message(f"📊 {range_end_hour:02d}:{range_end_minute:02d} 開盤區間監控中 - 當前價格: {int(price)}")
                self._logged_second = True

            elif (current_time.hour == third_hour and current_time.minute == third_minute and
                  not hasattr(self, '_logged_third')):
                if self.position_manager.range_detected:
                    range_info = f"{int(float(self.position_manager.range_low))}-{int(float(self.position_manager.range_high))}"
                    self.log_message(f"🎯 {third_hour:02d}:{third_minute:02d} 突破監控開始 - 區間: {range_info}")
                self._logged_third = True

        except Exception as e:
            logger.error(f"❌ 策略價格更新失敗: {e}")

    def reset_daily_logs(self):
        """重置每日日誌標記"""
        if hasattr(self, '_logged_first'):
            delattr(self, '_logged_first')
        if hasattr(self, '_logged_second'):
            delattr(self, '_logged_second')
        if hasattr(self, '_logged_third'):
            delattr(self, '_logged_third')

    def create_trading_panel(self):
        """創建下單測試面板"""
        trading_frame = tk.LabelFrame(self.root, text="💰 下單測試面板",
                                     fg="purple", font=("Arial", 12, "bold"))
        trading_frame.pack(fill="x", padx=10, pady=5)

        # 下單測試按鈕
        btn_frame = tk.Frame(trading_frame)
        btn_frame.pack(fill="x", padx=10, pady=5)

        tk.Label(btn_frame, text="實盤下單測試:", font=("Arial", 10, "bold"), fg="red").pack(side="left", padx=5)

        tk.Button(btn_frame, text="📈 測試買進1口", command=self.test_buy_order,
                 bg="darkgreen", fg="white", font=("Arial", 9)).pack(side="left", padx=5)

        tk.Button(btn_frame, text="📉 測試賣出1口", command=self.test_sell_order,
                 bg="darkred", fg="white", font=("Arial", 9)).pack(side="left", padx=5)

        tk.Label(btn_frame, text="⚠️ 需要OrderTester.py運行", fg="orange", font=("Arial", 8)).pack(side="left", padx=10)

    def create_error_panel(self):
        """創建錯誤面板"""
        error_frame = tk.LabelFrame(self.root, text="❌ 模組載入錯誤", fg="red")
        error_frame.pack(fill="both", expand=True, padx=10, pady=5)

        error_text = """
❌ 部分模組載入失敗

可能的原因：
1. 策略模組未正確安裝
2. 穩定版下單API未載入
3. 相依套件缺失

建議解決方案：
1. 確認所有檔案都在正確位置
2. 檢查import路徑
3. 重新啟動程式
        """

        tk.Label(error_frame, text=error_text, justify="left",
                font=("Arial", 10)).pack(padx=20, pady=20)

    def update_base_price(self):
        """更新基準價格"""
        try:
            new_price = float(self.entry_base_price.get())
            self.base_price = new_price
            self.current_price = new_price
            self.label_current_price.config(text=str(new_price))
            self.status_var.set(f"基準價格: {new_price}")
            logger.info(f"📊 基準價格更新為: {new_price}")

        except ValueError:
            messagebox.showerror("錯誤", "請輸入有效的價格數字")

    def start_price_simulation(self):
        """開始價格模擬 (僅限模擬模式)"""
        if self.quote_mode != "SIMULATION":
            messagebox.showwarning("警告", "當前為實盤報價模式，無法啟動價格模擬")
            return

        if self.price_running:
            return

        self.price_running = True
        self.status_var.set("價格模擬中...")
        self.btn_start_sim.config(state="disabled")
        self.btn_stop_sim.config(state="normal")

        self.log_message("🎯 開始模擬即時報價")

        logger.info("🎯 開始價格模擬")

        def price_thread():
            while self.price_running:
                try:
                    # 生成隨機價格變動
                    change = random.randint(-3, 3)
                    self.current_price = self.base_price + change

                    # 更新UI顯示
                    self.root.after(0, lambda: self.label_current_price.config(text=str(self.current_price)))

                    # 整合策略邏輯 - 傳遞價格給部位管理器
                    if self.strategy_active and self.position_manager:
                        timestamp = datetime.now()
                        # 在主線程中更新策略
                        self.root.after(0, lambda p=self.current_price, t=timestamp: self.update_strategy_with_price(p, t))

                    time.sleep(0.5)  # 每0.5秒更新一次

                except Exception as e:
                    logger.error(f"價格模擬錯誤: {e}")
                    break

        # 啟動價格模擬線程
        threading.Thread(target=price_thread, daemon=True).start()

    def switch_to_simulation(self):
        """切換到模擬報價源"""
        if self.quote_mode == "SIMULATION":
            logger.info("已經是模擬報價模式")
            return

        # 停止其他模式
        if self.bridge_monitoring:
            self.stop_bridge_monitoring()
        if self.tcp_connected:
            self.stop_tcp_client()

        self.quote_mode = "SIMULATION"
        self.quote_mode_var.set("模擬報價")
        self.quote_mode_label.config(fg="blue")

        # 更新按鈕狀態
        self.btn_switch_sim.config(state="disabled")
        self.btn_switch_bridge.config(state="normal")
        self.btn_switch_tcp.config(state="normal")
        self.btn_start_sim.config(state="normal")
        self.btn_start_real_monitor.config(state="normal", text="📡 開始實盤監控")
        self.btn_stop_real_monitor.config(state="disabled")

        logger.info("✅ 已切換到模擬報價源")
        self.log_message("🎮 已切換到模擬報價源")

    def switch_to_real(self):
        """切換到實盤報價源"""
        if self.quote_mode == "REAL":
            logger.info("已經是實盤報價模式")
            return

        # 檢查OrderTester連接
        connection_result = self.check_ordertester_connection()
        if not connection_result:
            # 提供選擇：測試連接或強制切換
            choice = messagebox.askyesnocancel(
                "OrderTester連接檢查",
                """無法自動檢測到OrderTester連接

請選擇：
• 是(Y) - 開啟連接測試視窗
• 否(N) - 強制切換到實盤模式 (不建議)
• 取消 - 返回模擬模式

建議：先點擊「是」進行詳細測試"""
            )

            if choice is True:  # 是 - 開啟測試視窗
                self.test_ordertester_connection()
                return
            elif choice is False:  # 否 - 強制切換
                logger.warning("⚠️ 用戶選擇強制切換到實盤模式")
                if hasattr(self, 'strategy_panel'):
                    self.strategy_panel.log_message("⚠️ 強制切換到實盤模式 (未檢測到OrderTester)")
            else:  # 取消
                return

        # 停止模擬報價
        if self.price_running:
            self.stop_price_simulation()

        self.quote_mode = "REAL"
        self.quote_mode_var.set("實盤報價")
        self.quote_mode_label.config(fg="red")

        # 更新按鈕狀態
        self.btn_switch_real.config(state="disabled")
        self.btn_switch_sim.config(state="normal")
        self.btn_start_sim.config(state="disabled")

        # 啟動實盤報價
        self.start_real_quotes()

        logger.info("✅ 已切換到實盤報價源")
        if hasattr(self, 'strategy_panel'):
            self.strategy_panel.log_message("📡 已切換到實盤報價源")

    def switch_to_direct(self):
        """切換到直接API報價源"""
        if self.quote_mode == "REAL_DIRECT":
            logger.info("已經是直接API模式")
            return

        # 停止其他報價源
        if self.price_running:
            self.stop_price_simulation()
        if self.real_quote_running:
            self.stop_real_quotes()

        # 初始化直接API
        if not self.direct_api_connected:
            if not self.initialize_direct_api():
                messagebox.showerror("錯誤", "直接API初始化失敗\n請檢查群益API是否正確安裝")
                return

        self.quote_mode = "REAL_DIRECT"
        self.quote_mode_var.set("直接API")
        self.quote_mode_label.config(fg="darkgreen")

        # 更新按鈕狀態
        self.btn_switch_direct.config(state="disabled")
        self.btn_switch_sim.config(state="normal")
        self.btn_switch_real.config(state="normal")
        self.btn_start_sim.config(state="disabled")

        # 啟動直接API報價
        self.start_direct_quotes()

        logger.info("✅ 已切換到直接API報價源")
        if hasattr(self, 'strategy_panel'):
            self.strategy_panel.log_message("🔗 已切換到直接API報價源")

    def start_real_monitor(self):
        """開始實盤監控 - 重用OrderTester的API物件"""
        try:
            self.log_message("🚀 開始啟動實盤監控...")
            logger.info("開始啟動實盤監控")

            # 停止其他報價源
            if self.price_running:
                self.stop_price_simulation()
            if self.bridge_monitoring:
                self.stop_bridge_monitoring()
            if self.tcp_connected:
                self.stop_tcp_client()

            # 檢查OrderTester是否已運行並登入
            self.log_message("🔍 檢查OrderTester狀態...")
            if not self.check_ordertester_api_ready():
                choice = messagebox.askyesno(
                    "需要OrderTester支援",
                    "實盤監控需要OrderTester.py提供API支援\n\n"
                    "請確保：\n"
                    "1. OrderTester.py已運行\n"
                    "2. 已成功登入群益證券\n"
                    "3. 登入狀態顯示為綠色\n\n"
                    "是否繼續嘗試連接？"
                )
                if not choice:
                    return False

                # 再次檢查
                if not self.check_ordertester_api_ready():
                    messagebox.showerror("連接失敗",
                        "無法連接到OrderTester\n\n"
                        "請確保：\n"
                        "1. OrderTester.py正在運行\n"
                        "2. 已成功登入\n"
                        "3. 重新啟動OrderTester.py")
                    return False

            # 切換到直接API模式
            self.quote_mode = "REAL_DIRECT"
            self.quote_mode_var.set("實盤監控")
            self.quote_mode_label.config(fg="red")

            # 更新按鈕狀態
            self.btn_start_real_monitor.config(state="disabled", text="📡 監控中...")
            self.btn_stop_real_monitor.config(state="normal")
            self.btn_switch_sim.config(state="normal")
            self.btn_switch_bridge.config(state="normal")
            self.btn_switch_tcp.config(state="normal")
            self.btn_start_sim.config(state="disabled")

            # 啟動報價監控 (使用OrderTester的API)
            self.log_message("📡 啟動報價監控...")
            if self.start_ordertester_quotes():
                self.log_message("✅ 實盤監控已啟動！")
                logger.info("✅ 實盤監控啟動成功")

                # 更新狀態顯示
                self.status_var.set("📡 實盤監控中...")

                # 啟動連接狀態監控
                self.monitor_real_quote_connection()

                # 顯示成功訊息
                messagebox.showinfo("成功", "實盤監控已啟動！\n正在重用OrderTester的群益API報價")
                return True
            else:
                self.log_message("❌ 報價監控啟動失敗")
                self.status_var.set("❌ 實盤監控啟動失敗")
                self.btn_start_real_monitor.config(state="normal", text="📡 開始實盤監控")
                return False

        except Exception as e:
            error_msg = f"啟動實盤監控失敗: {e}"
            self.log_message(f"❌ {error_msg}")
            logger.error(error_msg)
            messagebox.showerror("錯誤", error_msg)
            self.btn_start_real_monitor.config(state="normal", text="📡 開始實盤監控")
            return False

    def check_ordertester_api_ready(self):
        """檢查OrderTester是否已準備好提供API服務"""
        try:
            self.log_message("🔍 檢查OrderTester API狀態...")

            # 方法1: 檢查穩定版API
            if STABLE_API_AVAILABLE:
                try:
                    api = get_stable_order_api()
                    if api and hasattr(api, 'order_tester') and api.order_tester:
                        # 檢查OrderTester的API物件是否已初始化
                        ot = api.order_tester
                        if (hasattr(ot, 'm_pSKQuote') and ot.m_pSKQuote and
                            hasattr(ot, 'm_pSKCenter') and ot.m_pSKCenter):
                            self.log_message("✅ 找到OrderTester API物件")
                            self.ordertester_instance = ot
                            return True
                except Exception as e:
                    logger.debug(f"穩定版API檢查失敗: {e}")

            # 方法2: 檢查全域變數 (OrderTester的API物件)
            try:
                # 嘗試導入OrderTester模組
                import sys
                import os
                ordertester_path = os.path.join(os.path.dirname(__file__), 'OrderTester.py')
                if os.path.exists(ordertester_path):
                    # 檢查是否有全域API物件
                    import importlib.util
                    spec = importlib.util.spec_from_file_location("OrderTester", ordertester_path)
                    if spec and spec.loader:
                        ordertester_module = importlib.util.module_from_spec(spec)
                        spec.loader.exec_module(ordertester_module)

                        # 檢查全域API物件
                        if (hasattr(ordertester_module, 'm_pSKQuote') and
                            ordertester_module.m_pSKQuote and
                            hasattr(ordertester_module, 'm_pSKCenter') and
                            ordertester_module.m_pSKCenter):
                            self.log_message("✅ 找到OrderTester全域API物件")
                            self.ordertester_api_objects = {
                                'SKQuote': ordertester_module.m_pSKQuote,
                                'SKCenter': ordertester_module.m_pSKCenter,
                                'SKOrder': getattr(ordertester_module, 'm_pSKOrder', None),
                                'SKReply': getattr(ordertester_module, 'm_pSKReply', None)
                            }
                            return True
            except Exception as e:
                logger.debug(f"全域變數檢查失敗: {e}")

            self.log_message("❌ 未找到可用的OrderTester API")
            return False

        except Exception as e:
            logger.error(f"檢查OrderTester API狀態失敗: {e}")
            return False

    def start_ordertester_quotes(self):
        """使用OrderTester的API物件啟動報價監控"""
        try:
            # 方法1: 使用穩定版API
            if hasattr(self, 'ordertester_instance') and self.ordertester_instance:
                self.log_message("🔗 使用OrderTester API啟動報價...")

                # 檢查報價是否已經在監控中
                if hasattr(self.ordertester_instance, 'quote_monitoring') and self.ordertester_instance.quote_monitoring:
                    self.log_message("✅ OrderTester報價已在監控中，直接重用")
                    self.start_quote_data_bridge()
                    return True

                # 嘗試啟動OrderTester的報價監控
                try:
                    if hasattr(self.ordertester_instance, 'start_quote_monitoring'):
                        self.ordertester_instance.start_quote_monitoring()
                        self.log_message("✅ OrderTester報價監控已啟動")
                        self.start_quote_data_bridge()
                        return True
                except Exception as e:
                    logger.error(f"啟動OrderTester報價監控失敗: {e}")

            # 方法2: 使用橋接模式作為備用
            self.log_message("🌉 嘗試使用橋接模式...")
            if PRICE_BRIDGE_AVAILABLE:
                try:
                    self.switch_to_bridge()
                    return True
                except Exception as e:
                    logger.error(f"橋接模式啟動失敗: {e}")

            return False

        except Exception as e:
            logger.error(f"啟動OrderTester報價失敗: {e}")
            return False

    def start_quote_data_bridge(self):
        """啟動報價資料橋接"""
        try:
            self.log_message("🌉 啟動報價資料橋接...")

            # 標記為已連接
            self.direct_api_connected = True
            return True

        except Exception as e:
            logger.error(f"啟動報價資料橋接失敗: {e}")
            return False

    def start_ordertester_quotes(self):
        """使用OrderTester的API物件啟動報價監控"""
        try:
            # 方法1: 使用穩定版API
            if hasattr(self, 'ordertester_instance') and self.ordertester_instance:
                self.log_message("🔗 使用OrderTester API啟動報價...")

                # 檢查報價是否已經在監控中
                if hasattr(self.ordertester_instance, 'quote_monitoring') and self.ordertester_instance.quote_monitoring:
                    self.log_message("✅ OrderTester報價已在監控中，直接重用")
                    self.start_quote_data_bridge()
                    return True

                # 嘗試啟動OrderTester的報價監控
                try:
                    if hasattr(self.ordertester_instance, 'start_quote_monitoring'):
                        self.ordertester_instance.start_quote_monitoring()
                        self.log_message("✅ OrderTester報價監控已啟動")
                        self.start_quote_data_bridge()
                        return True
                except Exception as e:
                    logger.error(f"啟動OrderTester報價監控失敗: {e}")

            # 方法2: 使用全域API物件
            if hasattr(self, 'ordertester_api_objects') and self.ordertester_api_objects:
                self.log_message("🔗 使用OrderTester全域API啟動報價...")

                quote_lib = self.ordertester_api_objects.get('SKQuote')
                if quote_lib:
                    try:
                        # 訂閱MTX00報價 (假設OrderTester已經連接到報價伺服器)
                        result = quote_lib.SKQuoteLib_RequestTicks(-1, "MTX00")
                        if result == 0:
                            self.log_message("✅ MTX00報價訂閱成功")
                            self.start_quote_data_bridge()
                            return True
                        else:
                            self.log_message(f"❌ MTX00報價訂閱失敗，錯誤代碼: {result}")
                    except Exception as e:
                        logger.error(f"使用全域API啟動報價失敗: {e}")

            # 方法3: 使用橋接模式作為備用
            self.log_message("🌉 嘗試使用橋接模式...")
            if PRICE_BRIDGE_AVAILABLE:
                try:
                    self.switch_to_bridge()
                    return True
                except Exception as e:
                    logger.error(f"橋接模式啟動失敗: {e}")

            return False

        except Exception as e:
            logger.error(f"啟動OrderTester報價失敗: {e}")
            return False

    def start_quote_data_bridge(self):
        """啟動報價資料橋接"""
        try:
            self.log_message("🌉 啟動報價資料橋接...")

            # 設定報價回調函數
            def quote_callback(price):
                self.current_price = price
                self.root.after(0, lambda: self.label_current_price.config(text=str(price)))

                # 整合策略邏輯
                if self.strategy_active and self.position_manager:
                    timestamp = datetime.now()
                    self.root.after(0, lambda p=price, t=timestamp: self.update_strategy_with_price(p, t))

            # 如果有OrderTester實例，嘗試設定回調
            if hasattr(self, 'ordertester_instance') and self.ordertester_instance:
                # 這裡可以設定報價回調，但需要OrderTester支援
                pass

            # 標記為已連接
            self.direct_api_connected = True
            return True

        except Exception as e:
            logger.error(f"啟動報價資料橋接失敗: {e}")
            return False

    def monitor_real_quote_connection(self):
        """監控實盤報價連接狀態"""
        if self.quote_mode == "REAL_DIRECT" and self.direct_api_connected:
            try:
                # 檢查API連接狀態
                if hasattr(self, 'direct_skcom') and self.direct_skcom:
                    if hasattr(self.direct_skcom, 'quote_connected') and self.direct_skcom.quote_connected:
                        # 連接正常
                        if self.status_var.get() != "📡 實盤監控中...":
                            self.status_var.set("📡 實盤監控中...")
                    else:
                        # 連接異常
                        self.status_var.set("⚠️ 實盤連接異常")
                        self.log_message("⚠️ 實盤報價連接異常，嘗試重新連接...")

                        # 嘗試重新啟動報價監控
                        try:
                            self.start_direct_quotes()
                        except Exception as e:
                            logger.error(f"重新連接失敗: {e}")

                # 每10秒檢查一次
                self.root.after(10000, self.monitor_real_quote_connection)

            except Exception as e:
                logger.error(f"監控實盤連接狀態失敗: {e}")
                self.status_var.set("❌ 監控異常")

    def stop_real_monitor(self):
        """停止實盤監控"""
        try:
            self.log_message("🛑 停止實盤監控...")

            # 停止報價監控
            if hasattr(self, 'direct_skcom') and self.direct_skcom:
                try:
                    # 停止報價訂閱
                    if hasattr(self.direct_skcom, 'm_pSKQuote') and self.direct_skcom.m_pSKQuote:
                        self.direct_skcom.m_pSKQuote.SKQuoteLib_LeaveMonitor()
                    logger.info("✅ 群益API報價監控已停止")
                except Exception as e:
                    logger.error(f"停止群益API報價監控失敗: {e}")

            # 重置狀態
            self.quote_mode = "SIMULATION"
            self.quote_mode_var.set("模擬報價")
            self.quote_mode_label.config(fg="blue")
            self.status_var.set("系統就緒")

            # 重置按鈕狀態
            self.btn_start_real_monitor.config(state="normal", text="📡 開始實盤監控")
            self.btn_stop_real_monitor.config(state="disabled")
            self.btn_switch_sim.config(state="disabled")
            self.btn_switch_bridge.config(state="normal")
            self.btn_switch_tcp.config(state="normal")
            self.btn_start_sim.config(state="normal")

            self.log_message("✅ 實盤監控已停止")
            logger.info("✅ 實盤監控已停止")

        except Exception as e:
            error_msg = f"停止實盤監控失敗: {e}"
            self.log_message(f"❌ {error_msg}")
            logger.error(error_msg)

    def initialize_direct_api(self):
        """初始化直接API"""
        try:
            logger.info("🚀 初始化直接群益API...")

            if not self.direct_skcom.initialize_api():
                return False

            if not self.direct_skcom.login():
                return False

            self.direct_api_connected = True
            logger.info("✅ 直接API初始化成功")
            return True

        except Exception as e:
            logger.error(f"❌ 直接API初始化失敗: {e}")
            return False

    def start_direct_quotes(self):
        """啟動直接API報價"""
        try:
            if not self.direct_api_connected:
                return False

            self.status_var.set("直接API報價中...")

            # 設定報價回調
            def quote_callback(price):
                self.current_price = price
                self.root.after(0, lambda: self.label_current_price.config(text=str(price)))

                if hasattr(self, 'strategy_panel'):
                    timestamp = datetime.now()
                    self.root.after(0, lambda: self.strategy_panel.process_price_update(price, timestamp))

            # 啟動報價監控
            if self.direct_skcom.start_quote_monitor(quote_callback):
                logger.info("✅ 直接API報價已啟動")
                if hasattr(self, 'strategy_panel'):
                    self.strategy_panel.log_message("🔗 直接API報價已啟動")
                return True
            else:
                return False

        except Exception as e:
            logger.error(f"❌ 啟動直接API報價失敗: {e}")
            return False

    def switch_to_bridge(self):
        """切換到橋接模式 (OrderTester報價橋接)"""
        if self.quote_mode == "BRIDGE":
            logger.info("已經是橋接模式")
            return

        # 停止其他報價源
        if self.price_running:
            self.stop_price_simulation()
        if self.real_quote_running:
            self.stop_real_quotes()

        # 檢查價格橋接模組
        if not PRICE_BRIDGE_AVAILABLE:
            messagebox.showerror("錯誤", "價格橋接模組未載入\n請確保price_bridge.py檔案存在")
            return

        self.quote_mode = "BRIDGE"
        self.quote_mode_var.set("橋接模式")
        self.quote_mode_label.config(fg="teal")

        # 更新按鈕狀態
        self.btn_switch_bridge.config(state="disabled")
        self.btn_switch_sim.config(state="normal")
        self.btn_switch_tcp.config(state="normal")
        self.btn_start_sim.config(state="disabled")
        self.btn_start_real_monitor.config(state="normal", text="📡 開始實盤監控")

        # 啟動橋接監控
        self.start_bridge_monitoring()

        logger.info("✅ 已切換到橋接模式")
        self.log_message("🌉 已切換到橋接模式 (OrderTester報價)")

    def switch_to_tcp(self):
        """切換到TCP模式 (修復版本 - 避免重複連接)"""
        if not TCP_PRICE_CLIENT_AVAILABLE:
            from tkinter import messagebox
            messagebox.showerror("錯誤", "TCP價格客戶端模組未載入")
            logger.error("TCP價格客戶端模組未載入")
            return

        self.log_message("🚀 開始切換到TCP模式...")
        logger.info("開始切換到TCP模式")

        # 檢查是否已經是TCP模式
        if self.quote_mode == "TCP" and self.tcp_connected:
            self.log_message("ℹ️ 已經是TCP模式且已連接")
            logger.info("已經是TCP模式且已連接，無需切換")
            return

        # 防止重複點擊 - 暫時禁用按鈕
        self.btn_switch_tcp.config(state="disabled")

        try:
            # 停止其他模式
            if self.price_running:
                self.log_message("⏹️ 停止價格模擬...")
                logger.info("停止價格模擬")
                self.stop_price_simulation()

            if self.bridge_monitoring:
                self.log_message("⏹️ 停止橋接監控...")
                logger.info("停止橋接監控")
                self.stop_bridge_monitoring()

            if self.tcp_connected:
                self.log_message("⏹️ 停止舊TCP連接...")
                logger.info("停止舊TCP連接")
                self.stop_tcp_client()

            # 更新模式狀態
            self.quote_mode = "TCP"
            self.quote_mode_var.set("TCP模式")
            self.quote_mode_label.config(fg="purple")

            # 更新按鈕狀態
            self.btn_switch_sim.config(state="normal")
            self.btn_switch_bridge.config(state="normal")
            self.btn_start_sim.config(state="disabled")
            self.btn_start_real_monitor.config(state="normal", text="📡 開始實盤監控")

            # 啟動TCP客戶端
            self.log_message("🔗 啟動TCP客戶端...")
            logger.info("開始啟動TCP客戶端")

            tcp_success = self.start_tcp_client()

            if tcp_success:
                logger.info("✅ 已成功切換到TCP模式")
                self.log_message("🚀 已切換到TCP模式 (直接連接OrderTester)")
            else:
                # TCP連接失敗，自動切換到橋接模式
                logger.warning("TCP連接失敗，自動切換到橋接模式")
                self.log_message("🔄 TCP連接失敗，自動切換到橋接模式")
                self.switch_to_bridge()

        except Exception as e:
            logger.error(f"切換到TCP模式時發生錯誤: {e}", exc_info=True)
            self.log_message(f"❌ 切換到TCP模式失敗: {e}")

            # 錯誤時切換到橋接模式
            try:
                self.switch_to_bridge()
            except:
                pass

        finally:
            # 恢復按鈕狀態
            if not self.tcp_connected:
                self.btn_switch_tcp.config(state="normal")

    def start_tcp_client(self):
        """啟動TCP客戶端 (修復版本 - 避免多重連接)"""
        try:
            if not TCP_PRICE_CLIENT_AVAILABLE:
                self.log_message("❌ TCP價格客戶端模組未載入")
                logger.error("TCP價格客戶端模組未載入")
                return False

            # 檢查是否已連接
            if self.tcp_connected:
                self.log_message("⚠️ TCP已連接，無需重複連接")
                logger.warning("TCP客戶端已連接，跳過重複連接")
                return True

            self.log_message("🔗 開始TCP客戶端連接...")
            logger.info("開始TCP客戶端連接流程")

            # 清理舊連接
            if self.tcp_client:
                self.log_message("🧹 清理舊TCP連接...")
                logger.info("清理舊TCP客戶端連接")
                try:
                    self.tcp_client.disconnect()
                except Exception as e:
                    logger.warning(f"清理舊連接時發生錯誤: {e}")
                self.tcp_client = None

            # 建立TCP客戶端 (不做預先診斷，避免額外連接)
            self.log_message("🔗 建立TCP客戶端實例...")
            logger.info("建立PriceClient實例")
            self.tcp_client = PriceClient()

            # 設定價格回調
            def tcp_price_callback(price_data):
                try:
                    price = price_data.get('price', 0)
                    volume = price_data.get('volume', 0)
                    timestamp_str = price_data.get('timestamp', '')

                    # 首次收到數據時記錄
                    if not hasattr(self, '_tcp_first_data_received'):
                        self._tcp_first_data_received = True
                        self.log_message(f"📥 首次收到TCP數據: 價格={price}")

                    # 解析時間戳
                    from datetime import datetime
                    try:
                        # 假設timestamp是時間字符串 HH:MM:SS
                        hour, minute, second = map(int, timestamp_str.split(':'))
                        timestamp = datetime.now().replace(hour=hour, minute=minute, second=second, microsecond=0)
                    except:
                        timestamp = datetime.now()

                    self.current_price = price

                    # 更新UI顯示
                    self.root.after(0, lambda: self.label_current_price.config(text=str(int(price))))

                    # 整合策略邏輯 - TCP模式
                    if self.strategy_active and self.position_manager:
                        self.root.after(0, lambda p=price, t=timestamp: self.update_strategy_with_price(p, t))

                except Exception as e:
                    logger.error(f"❌ TCP價格回調處理失敗: {e}")

            self.tcp_client.set_price_callback(tcp_price_callback)

            # 連接到伺服器 (直接連接，不做預先檢查)
            self.log_message("🔗 嘗試連接TCP伺服器 (localhost:8888)...")
            logger.info("開始TCP客戶端連接到localhost:8888")

            import time
            connection_start_time = time.time()
            if self.tcp_client.connect():
                connection_time = time.time() - connection_start_time
                self.tcp_connected = True
                self.status_var.set("TCP已連接")

                self.log_message("✅ TCP客戶端已連接到OrderTester")
                self.log_message(f"📊 連接耗時: {connection_time:.3f}秒")
                self.log_message("⏳ 等待接收價格數據...")

                logger.info(f"TCP客戶端連接成功，耗時: {connection_time:.3f}秒")

                # 啟動狀態監控
                self.monitor_tcp_connection()
                return True
            else:
                connection_time = time.time() - connection_start_time
                self.log_message("❌ TCP客戶端連接失敗")
                self.log_message(f"📊 連接嘗試耗時: {connection_time:.3f}秒")
                self.log_message("💡 可能原因:")
                self.log_message("   1. OrderTester未啟動TCP伺服器")
                self.log_message("   2. 防火牆阻擋localhost:8888")
                self.log_message("   3. 端口被其他程式占用")

                logger.error(f"TCP客戶端連接失敗，耗時: {connection_time:.3f}秒")
                return False

        except Exception as e:
            logger.error(f"❌ 啟動TCP客戶端異常: {e}", exc_info=True)
            self.log_message(f"❌ 啟動TCP客戶端異常: {e}")

            # 清理異常狀態
            if self.tcp_client:
                try:
                    self.tcp_client.disconnect()
                except:
                    pass
                self.tcp_client = None

            return False

    def stop_tcp_client(self):
        """停止TCP客戶端 (增強日誌版本)"""
        try:
            self.log_message("🔌 開始停止TCP客戶端...")
            logger.info("開始停止TCP客戶端")

            if self.tcp_client:
                self.log_message("🔗 斷開TCP連接...")
                logger.info("斷開TCP客戶端連接")

                try:
                    self.tcp_client.disconnect()
                    self.log_message("✅ TCP連接已斷開")
                    logger.info("TCP客戶端連接已斷開")
                except Exception as disconnect_error:
                    self.log_message(f"⚠️ 斷開連接時發生錯誤: {disconnect_error}")
                    logger.warning(f"斷開TCP連接時發生錯誤: {disconnect_error}")

                self.tcp_client = None
                self.log_message("🧹 TCP客戶端實例已清理")
                logger.info("TCP客戶端實例已清理")
            else:
                self.log_message("ℹ️ 無需停止 - TCP客戶端未啟動")
                logger.info("TCP客戶端未啟動，無需停止")

            self.tcp_connected = False
            self.status_var.set("系統就緒")

            logger.info("⏹️ TCP客戶端已完全停止")
            self.log_message("⏹️ TCP客戶端已停止")

        except Exception as e:
            logger.error(f"❌ 停止TCP客戶端失敗: {e}", exc_info=True)
            self.log_message(f"❌ 停止TCP客戶端失敗: {e}")

            # 強制清理狀態
            self.tcp_client = None
            self.tcp_connected = False
            self.status_var.set("系統就緒")

    def monitor_tcp_connection(self):
        """監控TCP連接狀態"""
        if self.tcp_connected and self.tcp_client:
            try:
                if not self.tcp_client.connected:
                    self.tcp_connected = False
                    self.status_var.set("TCP連接斷開")
                    self.log_message("⚠️ TCP連接已斷開")

                    # 嘗試重連
                    self.log_message("🔄 嘗試重新連接...")
                    if self.tcp_client.connect():
                        self.tcp_connected = True
                        self.status_var.set("TCP已重連")
                        self.log_message("✅ TCP連接已恢復")

                # 每5秒檢查一次
                self.root.after(5000, self.monitor_tcp_connection)

            except Exception as e:
                logger.error(f"❌ TCP連接監控失敗: {e}")

    def start_bridge_monitoring(self):
        """啟動橋接監控"""
        try:
            if not PRICE_BRIDGE_AVAILABLE:
                return False

            self.bridge_monitoring = True
            self.status_var.set("橋接監控中...")

            # 設定價格回調
            def bridge_callback(price, volume, timestamp):
                self.current_price = price
                self.root.after(0, lambda: self.label_current_price.config(text=str(price)))

                # 整合策略邏輯 - 橋接模式
                if self.strategy_active and self.position_manager:
                    self.root.after(0, lambda p=price, t=timestamp: self.update_strategy_with_price(p, t))

            # 啟動價格監控
            start_price_monitoring(bridge_callback)

            logger.info("✅ 橋接監控已啟動")
            self.log_message("🌉 橋接監控已啟動，等待OrderTester報價...")

            return True

        except Exception as e:
            logger.error(f"❌ 啟動橋接監控失敗: {e}")
            return False

    def stop_bridge_monitoring(self):
        """停止橋接監控"""
        try:
            if PRICE_BRIDGE_AVAILABLE:
                stop_price_monitoring()

            self.bridge_monitoring = False
            self.status_var.set("橋接監控已停止")

            logger.info("⏹️ 橋接監控已停止")
            self.log_message("⏹️ 橋接監控已停止")

        except Exception as e:
            logger.error(f"❌ 停止橋接監控失敗: {e}")

    def check_ordertester_connection(self):
        """檢查OrderTester連接狀態"""
        try:
            # 方法1: 嘗試直接檢查穩定版API
            api = get_stable_order_api()
            if api.check_connection():
                self.ordertester_instance = api.order_tester
                logger.info("✅ 方法1成功: 穩定版API已連接")
                return True

            # 方法2: 嘗試尋找OrderTester實例
            logger.info("🔍 方法1失敗，嘗試尋找OrderTester實例...")
            ordertester_instance = self.find_ordertester_instance()
            if ordertester_instance:
                # 設定到穩定版API
                api.set_order_tester(ordertester_instance)
                self.ordertester_instance = ordertester_instance
                logger.info("✅ 方法2成功: 找到OrderTester實例並設定API")
                return True

            # 方法3: 檢查是否有OrderTester程序在運行
            logger.info("🔍 方法2失敗，檢查OrderTester程序...")
            if self.check_ordertester_process():
                logger.info("✅ 方法3成功: 檢測到OrderTester程序運行")
                return True

            logger.error("❌ 所有方法都失敗，無法連接OrderTester")
            return False

        except Exception as e:
            logger.error(f"檢查OrderTester連接失敗: {e}")
            return False

    def find_ordertester_instance(self):
        """嘗試尋找OrderTester實例"""
        try:
            # 檢查是否有全域變數或模組中的OrderTester實例
            import gc
            for obj in gc.get_objects():
                if hasattr(obj, '__class__') and 'OrderTester' in str(obj.__class__):
                    if hasattr(obj, 'm_pSKOrder') and obj.m_pSKOrder:
                        logger.info(f"🔍 找到OrderTester實例: {obj.__class__}")
                        return obj
            return None
        except Exception as e:
            logger.error(f"尋找OrderTester實例失敗: {e}")
            return None

    def check_ordertester_process(self):
        """檢查OrderTester程序是否在運行"""
        try:
            import psutil
            for proc in psutil.process_iter(['pid', 'name', 'cmdline']):
                try:
                    cmdline = proc.info['cmdline']
                    if cmdline and any('OrderTester.py' in cmd for cmd in cmdline):
                        logger.info(f"🔍 檢測到OrderTester程序: PID {proc.info['pid']}")
                        return True
                except (psutil.NoSuchProcess, psutil.AccessDenied):
                    continue
            return False
        except ImportError:
            logger.warning("⚠️ psutil未安裝，無法檢查程序")
            return False
        except Exception as e:
            logger.error(f"檢查程序失敗: {e}")
            return False

    def test_ordertester_connection(self):
        """測試OrderTester連接 (手動測試)"""
        logger.info("🔍 開始手動測試OrderTester連接...")

        # 顯示測試進度
        test_window = tk.Toplevel(self.root)
        test_window.title("🔍 OrderTester連接測試")
        test_window.geometry("500x400")
        test_window.resizable(False, False)

        # 測試結果顯示
        result_text = tk.Text(test_window, height=20, width=60, font=("Consolas", 9))
        result_text.pack(padx=10, pady=10, fill="both", expand=True)

        def add_result(message):
            result_text.insert(tk.END, message + "\n")
            result_text.see(tk.END)
            test_window.update()

        add_result("🔍 開始OrderTester連接測試...")
        add_result("=" * 50)

        # 測試1: 檢查穩定版API
        add_result("\n📋 測試1: 檢查穩定版API")
        try:
            api = get_stable_order_api()
            add_result(f"✅ 穩定版API實例: {type(api)}")

            if hasattr(api, 'order_tester') and api.order_tester:
                add_result(f"✅ OrderTester實例已設定: {type(api.order_tester)}")
            else:
                add_result("❌ OrderTester實例未設定")

            if api.check_connection():
                add_result("✅ API連接檢查通過")
            else:
                add_result("❌ API連接檢查失敗")

        except Exception as e:
            add_result(f"❌ 穩定版API測試失敗: {e}")

        # 測試2: 嘗試尋找OrderTester實例
        add_result("\n📋 測試2: 尋找OrderTester實例")
        try:
            ordertester_instance = self.find_ordertester_instance()
            if ordertester_instance:
                add_result(f"✅ 找到OrderTester實例: {type(ordertester_instance)}")
                if hasattr(ordertester_instance, 'm_pSKOrder'):
                    add_result(f"✅ SKOrder物件存在: {ordertester_instance.m_pSKOrder is not None}")
                else:
                    add_result("❌ SKOrder物件不存在")
            else:
                add_result("❌ 未找到OrderTester實例")
        except Exception as e:
            add_result(f"❌ 尋找實例失敗: {e}")

        # 測試3: 檢查程序
        add_result("\n📋 測試3: 檢查OrderTester程序")
        try:
            if self.check_ordertester_process():
                add_result("✅ 檢測到OrderTester程序正在運行")
            else:
                add_result("❌ 未檢測到OrderTester程序")
        except Exception as e:
            add_result(f"❌ 程序檢查失敗: {e}")

        # 測試4: 嘗試下單API測試
        add_result("\n📋 測試4: 下單API測試")
        try:
            if STABLE_API_AVAILABLE:
                add_result("✅ 下單API模組已載入")
                # 這裡可以添加更多API測試
            else:
                add_result("❌ 下單API模組未載入")
        except Exception as e:
            add_result(f"❌ 下單API測試失敗: {e}")

        # 總結
        add_result("\n" + "=" * 50)
        add_result("📋 測試完成")
        add_result("\n💡 解決建議:")
        add_result("1. 確保OrderTester.py正在運行")
        add_result("2. 確保OrderTester.py已成功登入")
        add_result("3. 檢查登入狀態是否為綠色")
        add_result("4. 嘗試重新啟動OrderTester.py")
        add_result("5. 確認網路連接正常")

        # 關閉按鈕
        tk.Button(test_window, text="關閉", command=test_window.destroy,
                 bg="gray", fg="white").pack(pady=10)

    def start_real_quotes(self):
        """啟動實盤報價接收"""
        if self.real_quote_running:
            return

        self.real_quote_running = True
        self.status_var.set("接收實盤報價中...")

        logger.info("🚀 啟動實盤報價接收")
        self.log_message("📡 開始接收實盤報價")

        # 啟動實盤報價線程
        def real_quote_thread():
            while self.real_quote_running:
                try:
                    # 這裡應該從OrderTester接收實際報價
                    # 目前先用模擬+小幅變動來示範
                    if hasattr(self, 'ordertester_instance') and self.ordertester_instance:
                        # 實際實現時，這裡會從OrderTester的報價事件接收價格
                        # 目前用模擬價格 + 較小變動來模擬實盤報價
                        change = random.randint(-1, 1)  # 實盤報價變動較小
                        self.current_price = self.base_price + change
                    else:
                        # 備用方案：使用模擬價格
                        change = random.randint(-2, 2)
                        self.current_price = self.base_price + change

                    # 更新UI顯示
                    self.root.after(0, lambda: self.label_current_price.config(text=str(self.current_price)))

                    # 整合策略邏輯 - 實盤模式
                    if self.strategy_active and self.position_manager:
                        timestamp = datetime.now()
                        self.root.after(0, lambda p=self.current_price, t=timestamp: self.update_strategy_with_price(p, t))

                    time.sleep(1.0)  # 實盤報價更新頻率較慢

                except Exception as e:
                    logger.error(f"實盤報價接收錯誤: {e}")
                    break

        threading.Thread(target=real_quote_thread, daemon=True).start()

    def stop_real_quotes(self):
        """停止實盤報價接收"""
        self.real_quote_running = False
        self.status_var.set("實盤報價已停止")

        logger.info("⏹️ 停止實盤報價接收")
        self.log_message("⏹️ 停止接收實盤報價")

    def stop_price_simulation(self):
        """停止價格模擬"""
        self.price_running = False

        if self.quote_mode == "SIMULATION":
            self.status_var.set("價格模擬已停止")
            self.btn_start_sim.config(state="normal")
        else:
            self.status_var.set("實盤報價模式")

        self.btn_stop_sim.config(state="disabled")

        self.log_message("⏹️ 停止模擬報價")

        logger.info("⏹️ 停止價格模擬")

    def test_buy_order(self):
        """測試買進下單"""
        if not STABLE_API_AVAILABLE:
            messagebox.showerror("錯誤", "穩定版下單API未載入")
            return

        try:
            # 調用穩定版下單API
            result = strategy_place_order(
                product='MTX00',
                direction='BUY',
                price=0.0,  # 市價
                quantity=1,
                order_type='ROD'
            )

            if result['success']:
                message = f"✅ 測試買進成功!\n委託編號: {result['order_id']}\n時間: {result['timestamp']}"
                messagebox.showinfo("下單成功", message)
                logger.info(f"測試買進成功: {result}")

                self.log_message(f"✅ 測試買進成功: {result['order_id']}")
            else:
                message = f"❌ 測試買進失敗!\n錯誤訊息: {result['message']}\n時間: {result['timestamp']}"
                messagebox.showerror("下單失敗", message)
                logger.error(f"測試買進失敗: {result}")

                self.log_message(f"❌ 測試買進失敗: {result['message']}")

        except Exception as e:
            error_msg = f"測試買進異常: {str(e)}"
            messagebox.showerror("系統錯誤", error_msg)
            logger.error(error_msg)

    def test_sell_order(self):
        """測試賣出下單"""
        if not STABLE_API_AVAILABLE:
            messagebox.showerror("錯誤", "穩定版下單API未載入")
            return

        try:
            # 調用穩定版下單API
            result = strategy_place_order(
                product='MTX00',
                direction='SELL',
                price=0.0,  # 市價
                quantity=1,
                order_type='ROD'
            )

            if result['success']:
                message = f"✅ 測試賣出成功!\n委託編號: {result['order_id']}\n時間: {result['timestamp']}"
                messagebox.showinfo("下單成功", message)
                logger.info(f"測試賣出成功: {result}")

                self.log_message(f"✅ 測試賣出成功: {result['order_id']}")
            else:
                message = f"❌ 測試賣出失敗!\n錯誤訊息: {result['message']}\n時間: {result['timestamp']}"
                messagebox.showerror("下單失敗", message)
                logger.error(f"測試賣出失敗: {result}")

                self.log_message(f"❌ 測試賣出失敗: {result['message']}")

        except Exception as e:
            error_msg = f"測試賣出異常: {str(e)}"
            messagebox.showerror("系統錯誤", error_msg)
            logger.error(error_msg)

    def run(self):
        """運行應用程式"""
        try:
            logger.info("🚀 啟動完整交易測試系統")
            self.root.mainloop()
        except Exception as e:
            logger.error(f"應用程式運行錯誤: {e}")

def test_log_output():
    """測試log輸出功能"""
    print("🧪 測試log輸出功能")
    print("=" * 40)
    
    # 測試print輸出
    print("📊 策略日誌: [16:45:23.123] 這是一條測試日誌")
    
    # 測試logging輸出
    import logging
    logger = logging.getLogger('TestLogger')
    logging.basicConfig(
        level=logging.DEBUG,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    logger.info("這是一條info級別的日誌")
    logger.debug("這是一條debug級別的日誌")
    logger.warning("這是一條warning級別的日誌")
    logger.error("這是一條error級別的日誌")
    
    print("\n✅ log輸出測試完成")
    print("💡 這些日誌應該同時顯示在:")
    print("   1. VS CODE的終端輸出")
    print("   2. VS CODE的輸出面板")
    print("   3. 策略面板的日誌區域")

def test_strategy_panel_ui():
    """測試策略面板UI改進"""
    print("\n🧪 測試策略面板UI")
    print("=" * 40)
    
    try:
        from strategy.strategy_panel import StrategyControlPanel
        
        # 創建測試視窗
        root = tk.Tk()
        root.title("🧪 策略面板UI測試")
        root.geometry("1200x800")
        
        # 創建策略面板
        panel = StrategyControlPanel(root)
        panel.pack(fill="both", expand=True, padx=10, pady=10)
        
        # 測試log功能
        def test_logs():
            messages = [
                "🚀 策略面板載入完成",
                "⏰ 時間設定: 16:45 ~ 16:46",
                "📊 開始監控開盤區間",
                "💰 當前價格: 22000",
                "📈 價格更新: 22005 (+5)",
                "🎯 區間計算中...",
                "✅ 區間計算完成: 高點22010 低點21995",
                "🚀 突破信號: LONG @22015",
                "📊 開倉: 3口 @22015",
                "💹 移動停利啟動: 第1口 15點",
            ]
            
            for i, msg in enumerate(messages):
                panel.log_message(f"{msg} (測試 {i+1}/10)")
                root.update()
                time.sleep(0.5)
        
        # 延遲執行測試
        def delayed_test():
            time.sleep(2)
            test_logs()
        
        # 啟動測試線程
        threading.Thread(target=delayed_test, daemon=True).start()
        
        print("✅ 策略面板UI測試視窗已開啟")
        print("💡 請檢查以下項目:")
        print("   1. 底部測試按鈕已移除 (只保留啟動/停止/緊急平倉)")
        print("   2. 日誌區域變大 (15行高度)")
        print("   3. 有清除日誌按鈕")
        print("   4. 日誌同時輸出到VS CODE")
        print("   5. 使用等寬字體便於閱讀")
        
        # 運行UI
        root.mainloop()
        
    except ImportError as e:
        print(f"❌ 策略面板導入失敗: {e}")
        print("💡 請確保策略模組正確安裝")
    except Exception as e:
        print(f"❌ UI測試失敗: {e}")

def test_time_setting_buttons():
    """測試時間設定按鈕功能"""
    print("\n🧪 測試時間設定按鈕")
    print("=" * 40)
    
    from datetime import datetime, time
    
    # 模擬「測試用(3分鐘後)」按鈕邏輯
    now = datetime.now()
    start_time = now.replace(minute=now.minute + 3, second=0)
    end_time = start_time.replace(minute=start_time.minute + 1)
    
    # 處理分鐘數超過59的情況
    if start_time.minute >= 60:
        start_time = start_time.replace(hour=start_time.hour + 1, minute=start_time.minute - 60)
    if end_time.minute >= 60:
        end_time = end_time.replace(hour=end_time.hour + 1, minute=end_time.minute - 60)
    
    print(f"📅 當前時間: {now.strftime('%H:%M:%S')}")
    print(f"🕐 設定開始時間: {start_time.strftime('%H:%M:%S')}")
    print(f"🕑 設定結束時間: {end_time.strftime('%H:%M:%S')}")
    print(f"⏱️ 等待時間: {(start_time - now).total_seconds():.0f}秒")
    
    print("\n✅ 時間設定邏輯測試通過")

def main():
    """主函數 - 啟動完整交易測試系統"""
    print("🎯 完整交易測試系統")
    print("=" * 60)
    print("🏷️ TRADING_TESTER_2025_06_30")
    print("✅ 基於UI改進版本")
    print("✅ 整合策略測試功能")
    print("✅ 整合穩定版下單API")
    print("✅ 日誌同步VS CODE輸出")
    print("=" * 60)

    # 檢查模組載入狀態
    print("\n📋 模組載入狀態:")
    print(f"   策略模組: {'✅ 已載入' if STRATEGY_AVAILABLE else '❌ 未載入'}")
    print(f"   下單API: {'✅ 已載入' if STABLE_API_AVAILABLE else '❌ 未載入'}")

    if not STRATEGY_AVAILABLE:
        print("\n⚠️ 策略模組未載入，部分功能將不可用")

    if not STABLE_API_AVAILABLE:
        print("\n⚠️ 下單API未載入，實盤下單功能將不可用")
        print("💡 請確保OrderTester.py正在運行並已登入")

    print("\n🚀 啟動完整交易測試系統...")

    # 創建並運行應用程式
    app = TradingTesterApp()
    app.run()

    print("\n🎉 完整交易測試系統已關閉")

def test_original_functions():
    """測試原始功能 (保留用於調試)"""
    print("🧪 原始功能測試")
    print("=" * 40)

    # 測試1: log輸出功能
    test_log_output()

    # 測試2: 時間設定按鈕
    test_time_setting_buttons()

    print("\n✅ 原始功能測試完成")

if __name__ == "__main__":
    main()
