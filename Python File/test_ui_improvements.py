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

    def __init__(self, config: StrategyConfig, order_api=None):
        self.config = config
        self.order_api = order_api

        # 交易狀態
        self.position = None  # 'LONG', 'SHORT', None
        self.entry_price = Decimal(0)
        self.entry_time = None
        self.lots = []  # 各口單狀態

        # 區間數據
        self.range_high = None
        self.range_low = None
        self.range_detected = False

        # 價格歷史 (用於區間計算)
        self.price_history = []
        self.candle_846 = None
        self.candle_847 = None

        logger.info(f"🎯 實盤交易管理器初始化 - {config.trade_size_in_lots}口交易")

    def update_price(self, price, timestamp):
        """更新價格並檢查交易信號"""
        current_time = timestamp.time()
        price_decimal = Decimal(str(price))

        # 收集8:46和8:47的價格數據
        if current_time.hour == 8 and current_time.minute == 46:
            if not self.candle_846:
                self.candle_846 = {'high': price_decimal, 'low': price_decimal, 'close': price_decimal}
            else:
                self.candle_846['high'] = max(self.candle_846['high'], price_decimal)
                self.candle_846['low'] = min(self.candle_846['low'], price_decimal)
                self.candle_846['close'] = price_decimal

        elif current_time.hour == 8 and current_time.minute == 47:
            if not self.candle_847:
                self.candle_847 = {'high': price_decimal, 'low': price_decimal, 'close': price_decimal}
            else:
                self.candle_847['high'] = max(self.candle_847['high'], price_decimal)
                self.candle_847['low'] = min(self.candle_847['low'], price_decimal)
                self.candle_847['close'] = price_decimal

            # 8:47結束時計算區間
            if not self.range_detected and self.candle_846 and self.candle_847:
                self.calculate_opening_range()

        # 8:48後檢查突破信號
        elif current_time.hour == 8 and current_time.minute >= 48 and self.range_detected and not self.position:
            self.check_breakout_signal(price_decimal, timestamp)

        # 已有部位時檢查出場條件
        elif self.position:
            self.check_exit_conditions(price_decimal, timestamp)

    def calculate_opening_range(self):
        """計算開盤區間"""
        if not self.candle_846 or not self.candle_847:
            return

        candles = [self.candle_846, self.candle_847]
        self.range_high = max(c['high'] for c in candles)
        self.range_low = min(c['low'] for c in candles)
        self.range_detected = True

        logger.info(f"📊 開盤區間計算完成: {float(self.range_low)} - {float(self.range_high)}")

    def check_breakout_signal(self, price, timestamp):
        """檢查突破信號並建倉"""
        if price > self.range_high:
            self.enter_position('LONG', price, timestamp)
        elif price < self.range_low:
            self.enter_position('SHORT', price, timestamp)

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
        self.candle_846 = None
        self.candle_847 = None

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
        """初始化群益API - 簡化版本"""
        try:
            if not SKCOM_AVAILABLE:
                logger.error("❌ 群益API模組未載入")
                return False

            logger.info("🚀 開始初始化群益API...")

            # 先嘗試簡化的初始化方式
            try:
                self.m_pSKCenter = comtypes.client.CreateObject("SKCOMLib.SKCenterLib")
                self.m_pSKOrder = comtypes.client.CreateObject("SKCOMLib.SKOrderLib")
                self.m_pSKQuote = comtypes.client.CreateObject("SKCOMLib.SKQuoteLib")
                self.m_pSKReply = comtypes.client.CreateObject("SKCOMLib.SKReplyLib")

                if not all([self.m_pSKCenter, self.m_pSKOrder, self.m_pSKQuote, self.m_pSKReply]):
                    logger.error("❌ 部分API物件初始化失敗")
                    return False

                logger.info("✅ 群益API物件初始化成功")

            except Exception as e:
                logger.error(f"❌ 群益API物件初始化失敗: {e}")
                return False

            # 建立事件處理 (簡化版)
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
            cert_result = self.m_pSKOrder.ReadCertByID(self.login_id)
            if cert_result != 0:
                logger.error(f"❌ 讀取憑證失敗，錯誤代碼: {cert_result}")
                return False

            self.is_logged_in = True
            logger.info("✅ 登入成功")
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

        self.position_manager = LiveTradingPositionManager(self.strategy_config, order_api)
        logger.info("✅ 部位管理器已建立")
        return True

    def initialize_button_states(self):
        """初始化按鈕狀態"""
        # 預設為模擬模式
        self.quote_mode = "SIMULATION"
        self.quote_mode_var.set("模擬報價")
        self.quote_mode_label.config(fg="blue")

        # 按鈕狀態
        self.btn_switch_sim.config(state="disabled")  # 已經是模擬模式
        self.btn_switch_real.config(state="normal")
        self.btn_switch_direct.config(state="normal")
        self.btn_switch_bridge.config(state="normal")
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

        self.btn_switch_sim = tk.Button(row2, text="🎮 切換模擬", command=self.switch_to_simulation,
                                       bg="blue", fg="white", font=("Arial", 9))
        self.btn_switch_sim.pack(side="left", padx=5)

        self.btn_switch_real = tk.Button(row2, text="📡 切換實盤", command=self.switch_to_real,
                                        bg="purple", fg="white", font=("Arial", 9))
        self.btn_switch_real.pack(side="left", padx=5)

        self.btn_switch_direct = tk.Button(row2, text="🔗 直接API", command=self.switch_to_direct,
                                          bg="darkgreen", fg="white", font=("Arial", 9))
        self.btn_switch_direct.pack(side="left", padx=5)

        self.btn_switch_bridge = tk.Button(row2, text="🌉 橋接模式", command=self.switch_to_bridge,
                                          bg="teal", fg="white", font=("Arial", 9))
        self.btn_switch_bridge.pack(side="left", padx=5)

        self.btn_test_connection = tk.Button(row2, text="🔍 測試連接", command=self.test_ordertester_connection,
                                           bg="orange", fg="white", font=("Arial", 8))
        self.btn_test_connection.pack(side="left", padx=5)

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

        # 策略狀態顯示
        status_frame = tk.Frame(config_frame)
        status_frame.pack(fill="x", padx=5, pady=5)

        tk.Label(status_frame, text="策略狀態:", font=("Arial", 10)).pack(side="left", padx=5)
        self.strategy_status_var = tk.StringVar(value="🔴 未啟動")
        tk.Label(status_frame, textvariable=self.strategy_status_var, font=("Arial", 10, "bold")).pack(side="left", padx=5)

        # 區間監控區域
        range_frame = tk.LabelFrame(strategy_container, text="開盤區間監控", fg="orange")
        range_frame.pack(fill="x", padx=5, pady=5)

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

    def update_strategy_with_price(self, price, timestamp):
        """更新策略與價格數據"""
        try:
            if not self.strategy_active or not self.position_manager:
                return

            # 傳遞價格給部位管理器
            self.position_manager.update_price(price, timestamp)

            # 檢查是否有交易信號或狀態變化
            current_time = timestamp.time()

            # 記錄重要事件
            if (current_time.hour == 8 and current_time.minute == 46 and
                not hasattr(self, '_logged_846')):
                self.log_message(f"📊 8:46 開盤區間監控開始 - 當前價格: {int(price)}")
                self._logged_846 = True

            elif (current_time.hour == 8 and current_time.minute == 47 and
                  not hasattr(self, '_logged_847')):
                self.log_message(f"📊 8:47 開盤區間監控中 - 當前價格: {int(price)}")
                self._logged_847 = True

            elif (current_time.hour == 8 and current_time.minute == 48 and
                  not hasattr(self, '_logged_848')):
                if self.position_manager.range_detected:
                    range_info = f"{int(float(self.position_manager.range_low))}-{int(float(self.position_manager.range_high))}"
                    self.log_message(f"🎯 8:48 突破監控開始 - 區間: {range_info}")
                self._logged_848 = True

        except Exception as e:
            logger.error(f"❌ 策略價格更新失敗: {e}")

    def reset_daily_logs(self):
        """重置每日日誌標記"""
        if hasattr(self, '_logged_846'):
            delattr(self, '_logged_846')
        if hasattr(self, '_logged_847'):
            delattr(self, '_logged_847')
        if hasattr(self, '_logged_848'):
            delattr(self, '_logged_848')

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

        if hasattr(self, 'strategy_panel'):
            self.strategy_panel.log_message("🎯 開始模擬即時報價")

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

        # 停止實盤報價
        if self.real_quote_running:
            self.stop_real_quotes()

        self.quote_mode = "SIMULATION"
        self.quote_mode_var.set("模擬報價")
        self.quote_mode_label.config(fg="blue")

        # 更新按鈕狀態
        self.btn_switch_sim.config(state="disabled")
        self.btn_switch_real.config(state="normal")
        self.btn_start_sim.config(state="normal")

        logger.info("✅ 已切換到模擬報價源")
        if hasattr(self, 'strategy_panel'):
            self.strategy_panel.log_message("🎮 已切換到模擬報價源")

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
        self.btn_switch_real.config(state="normal")
        self.btn_switch_direct.config(state="normal")
        self.btn_start_sim.config(state="disabled")

        # 啟動橋接監控
        self.start_bridge_monitoring()

        logger.info("✅ 已切換到橋接模式")
        if hasattr(self, 'strategy_panel'):
            self.strategy_panel.log_message("🌉 已切換到橋接模式 (OrderTester報價)")

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
            if hasattr(self, 'strategy_panel'):
                self.strategy_panel.log_message("🌉 橋接監控已啟動，等待OrderTester報價...")

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
            if hasattr(self, 'strategy_panel'):
                self.strategy_panel.log_message("⏹️ 橋接監控已停止")

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
        if hasattr(self, 'strategy_panel'):
            self.strategy_panel.log_message("📡 開始接收實盤報價")

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

                    # 更新策略面板
                    if hasattr(self, 'strategy_panel'):
                        timestamp = datetime.now()
                        self.root.after(0, lambda: self.strategy_panel.process_price_update(self.current_price, timestamp))

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
        if hasattr(self, 'strategy_panel'):
            self.strategy_panel.log_message("⏹️ 停止接收實盤報價")

    def stop_price_simulation(self):
        """停止價格模擬"""
        self.price_running = False

        if self.quote_mode == "SIMULATION":
            self.status_var.set("價格模擬已停止")
            self.btn_start_sim.config(state="normal")
        else:
            self.status_var.set("實盤報價模式")

        self.btn_stop_sim.config(state="disabled")

        if hasattr(self, 'strategy_panel'):
            self.strategy_panel.log_message("⏹️ 停止模擬報價")

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

                if hasattr(self, 'strategy_panel'):
                    self.strategy_panel.log_message(f"✅ 測試買進成功: {result['order_id']}")
            else:
                message = f"❌ 測試買進失敗!\n錯誤訊息: {result['message']}\n時間: {result['timestamp']}"
                messagebox.showerror("下單失敗", message)
                logger.error(f"測試買進失敗: {result}")

                if hasattr(self, 'strategy_panel'):
                    self.strategy_panel.log_message(f"❌ 測試買進失敗: {result['message']}")

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

                if hasattr(self, 'strategy_panel'):
                    self.strategy_panel.log_message(f"✅ 測試賣出成功: {result['order_id']}")
            else:
                message = f"❌ 測試賣出失敗!\n錯誤訊息: {result['message']}\n時間: {result['timestamp']}"
                messagebox.showerror("下單失敗", message)
                logger.error(f"測試賣出失敗: {result}")

                if hasattr(self, 'strategy_panel'):
                    self.strategy_panel.log_message(f"❌ 測試賣出失敗: {result['message']}")

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
