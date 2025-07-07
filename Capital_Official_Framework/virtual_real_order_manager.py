# -*- coding: utf-8 -*-
"""
虛實單切換管理器
Virtual/Real Order Manager

功能：
1. 統一下單介面 - 提供統一的下單API，內部分流處理
2. 商品自動識別 - 根據當前監控的報價商品決定下單商品
3. 策略配置整合 - 自動取得策略配置的數量和參數
4. ASK1價格整合 - 整合RealTimeQuoteManager的ASK1價格
5. 虛實單切換 - 支援虛擬/實單模式切換

作者: Stage2 虛實單整合系統
日期: 2025-07-04
"""

import time
import uuid
from datetime import datetime
from typing import Dict, Any, Optional, Union
import threading

# 群益API相關 (實際下單時使用)
try:
    import comtypes.client
    import Global  # 群益Global模組
    CAPITAL_API_AVAILABLE = True
except ImportError:
    CAPITAL_API_AVAILABLE = False
    print("⚠️ [ORDER_MGR] 群益API模組未載入，僅支援虛擬模式")


class OrderParams:
    """下單參數結構"""
    
    def __init__(self, account: str, product: str, direction: str, 
                 quantity: int, price: float, order_type: str = "FOK",
                 new_close: int = 0, day_trade: str = "N", 
                 signal_source: str = "strategy"):
        """
        初始化下單參數
        
        Args:
            account: 期貨帳號 (如: F0200006363839)
            product: 商品代碼 (MTX00/TM0000)
            direction: 買賣方向 (BUY/SELL)
            quantity: 數量
            price: 價格
            order_type: 訂單類型 (FOK/IOC/ROD)
            new_close: 新平倉 (0=新倉, 1=平倉, 2=自動)
            day_trade: 當沖 (Y/N)
            signal_source: 信號來源
        """
        self.account = account
        self.product = product
        self.direction = direction
        self.quantity = quantity
        self.price = price
        self.order_type = order_type
        self.new_close = new_close
        self.day_trade = day_trade
        self.signal_source = signal_source
        self.timestamp = datetime.now()
        self.order_id = str(uuid.uuid4())[:8]  # 8位訂單ID


class OrderResult:
    """下單結果結構"""
    
    def __init__(self, success: bool, mode: str, order_id: str = None, 
                 error: str = None, api_result: Any = None):
        """
        初始化下單結果
        
        Args:
            success: 是否成功
            mode: 模式 (virtual/real)
            order_id: 訂單ID
            error: 錯誤訊息
            api_result: API返回結果
        """
        self.success = success
        self.mode = mode
        self.order_id = order_id
        self.error = error
        self.api_result = api_result
        self.timestamp = datetime.now()


class VirtualRealOrderManager:
    """虛實單切換管理器"""
    
    def __init__(self, quote_manager=None, strategy_config=None, 
                 console_enabled=True, default_account="F0200006363839"):
        """
        初始化虛實單管理器
        
        Args:
            quote_manager: 報價管理器 (RealTimeQuoteManager)
            strategy_config: 策略配置
            console_enabled: 是否啟用Console輸出
            default_account: 預設期貨帳號
        """
        # 基本設定
        self.quote_manager = quote_manager
        self.strategy_config = strategy_config
        self.console_enabled = console_enabled
        self.default_account = default_account
        
        # 模式控制
        self.is_real_mode = False  # 預設虛擬模式
        self.mode_lock = threading.Lock()
        
        # 商品映射
        self.product_mapping = {
            'MTX00': '小台指期貨',
            'TM0000': '微型台指期貨'
        }
        self.supported_products = list(self.product_mapping.keys())
        
        # 訂單追蹤
        self.pending_orders = {}  # {order_id: OrderParams}
        self.order_history = []   # 訂單歷史
        
        # 統計數據
        self.total_orders = 0
        self.virtual_orders = 0
        self.real_orders = 0
        self.success_orders = 0
        self.failed_orders = 0
        
        # 線程安全鎖
        self.data_lock = threading.Lock()
        
        if self.console_enabled:
            print(f"[ORDER_MGR] 虛實單管理器已初始化")
            print(f"[ORDER_MGR] 預設模式: {'實單' if self.is_real_mode else '虛擬'}模式")
            print(f"[ORDER_MGR] 支援商品: {', '.join(self.supported_products)}")
            print(f"[ORDER_MGR] 預設帳號: {self.default_account}")

            # 動態檢查API狀態
            if CAPITAL_API_AVAILABLE:
                api_ready = self.check_api_availability()
                if api_ready:
                    print(f"[ORDER_MGR] ✅ 群益API已就緒，支援實單模式")
                else:
                    print(f"[ORDER_MGR] ⚠️ 群益API未就緒，請先登入後再切換實單模式")
            else:
                print(f"[ORDER_MGR] ⚠️ 群益API模組未載入，僅支援虛擬模式")
    
    def check_api_availability(self) -> bool:
        """
        動態檢查群益API可用性

        Returns:
            bool: API是否可用
        """
        try:
            # 檢查模組是否已導入
            if not CAPITAL_API_AVAILABLE:
                return False

            # 檢查Global模組是否有skO物件
            if not hasattr(Global, 'skO') or Global.skO is None:
                return False

            # 檢查是否已設定Global_IID (表示已登入)
            if not hasattr(Global, 'Global_IID') or not Global.Global_IID:
                return False

            return True

        except Exception as e:
            if self.console_enabled:
                print(f"[ORDER_MGR] ⚠️ API檢查失敗: {e}")
            return False

    def set_order_mode(self, is_real_mode: bool) -> bool:
        """
        設定下單模式

        Args:
            is_real_mode: True=實單模式, False=虛擬模式

        Returns:
            bool: 設定是否成功
        """
        try:
            with self.mode_lock:
                # 動態檢查實單模式的前置條件
                if is_real_mode:
                    api_available = self.check_api_availability()
                    if not api_available:
                        if self.console_enabled:
                            print("[ORDER_MGR] ❌ 無法切換到實單模式：群益API未就緒")
                            print("[ORDER_MGR] 💡 請確認：1)已登入 2)API已初始化 3)有下單權限")
                        return False

                old_mode = "實單" if self.is_real_mode else "虛擬"
                new_mode = "實單" if is_real_mode else "虛擬"

                self.is_real_mode = is_real_mode

                if self.console_enabled:
                    print(f"[ORDER_MGR] 🔄 模式切換: {old_mode} → {new_mode}")

                return True

        except Exception as e:
            if self.console_enabled:
                print(f"[ORDER_MGR] ❌ 模式切換失敗: {e}")
            return False
    
    def get_current_mode(self) -> str:
        """取得當前模式"""
        return "real" if self.is_real_mode else "virtual"
    
    def get_current_product(self) -> Optional[str]:
        """
        取得當前監控商品
        
        Returns:
            str: 商品代碼 (MTX00/TM0000) 或 None
        """
        try:
            if not self.quote_manager:
                return "MTX00"  # 預設商品
            
            # 檢查報價管理器中有數據的商品
            for product in self.supported_products:
                if self.quote_manager.is_quote_fresh(product):
                    return product
            
            # 如果沒有新鮮數據，返回第一個有數據的商品
            for product in self.supported_products:
                summary = self.quote_manager.get_quote_summary(product)
                if summary and summary.get('update_count', 0) > 0:
                    return product
            
            # 都沒有則返回預設
            return "MTX00"
            
        except Exception as e:
            if self.console_enabled:
                print(f"[ORDER_MGR] ❌ 取得當前商品失敗: {e}")
            return "MTX00"
    
    def get_strategy_quantity(self) -> int:
        """
        取得策略配置的數量
        
        Returns:
            int: 交易數量
        """
        try:
            if self.strategy_config and hasattr(self.strategy_config, 'trade_size_in_lots'):
                return self.strategy_config.trade_size_in_lots
            return 1  # 預設1口
        except:
            return 1
    
    def get_ask1_price(self, product: str) -> Optional[float]:
        """
        取得ASK1價格

        Args:
            product: 商品代碼

        Returns:
            float: ASK1價格 或 None
        """
        try:
            if not self.quote_manager:
                return None

            return self.quote_manager.get_best_ask_price(product)

        except Exception as e:
            if self.console_enabled:
                print(f"[ORDER_MGR] ❌ 取得ASK1價格失敗: {e}")
            return None

    def get_bid1_price(self, product: str) -> Optional[float]:
        """
        取得BID1價格 - 多單出場使用

        Args:
            product: 商品代碼

        Returns:
            float: BID1價格 或 None
        """
        try:
            if not self.quote_manager:
                return None

            return self.quote_manager.get_best_bid_price(product)

        except Exception as e:
            if self.console_enabled:
                print(f"[ORDER_MGR] ❌ 取得BID1價格失敗: {e}")
            return None

    def get_exit_price(self, position_direction: str, product: str) -> Optional[float]:
        """
        取得出場價格 - 根據部位方向選擇BID1或ASK1

        Args:
            position_direction: 部位方向 (LONG/SHORT)
            product: 商品代碼

        Returns:
            float: 出場價格 或 None
        """
        try:
            if position_direction.upper() == "LONG":
                # 多單出場 → 賣出 → 使用BID1價格
                price = self.get_bid1_price(product)
                if self.console_enabled and price:
                    print(f"[EXIT_PRICE] 多單出場使用BID1: {price}")
                return price

            elif position_direction.upper() == "SHORT":
                # 空單出場 → 買回 → 使用ASK1價格
                price = self.get_ask1_price(product)
                if self.console_enabled and price:
                    print(f"[EXIT_PRICE] 空單出場使用ASK1: {price}")
                return price

            else:
                if self.console_enabled:
                    print(f"[EXIT_PRICE] ❌ 無效的部位方向: {position_direction}")
                return None

        except Exception as e:
            if self.console_enabled:
                print(f"[EXIT_PRICE] ❌ 取得出場價格失敗: {e}")
            return None

    def execute_strategy_order(self, direction: str, signal_source: str = "strategy_breakout",
                             product: Optional[str] = None, price: Optional[float] = None,
                             quantity: Optional[int] = None) -> OrderResult:
        """
        執行策略下單 - 統一入口

        Args:
            direction: 買賣方向 (BUY/SELL 或 LONG/SHORT)
            signal_source: 信號來源
            product: 商品代碼 (可選，自動取得)
            price: 價格 (可選，自動取得ASK1)
            quantity: 數量 (可選，自動取得策略配置)

        Returns:
            OrderResult: 下單結果
        """
        try:
            with self.data_lock:
                # 1. 標準化方向參數
                if direction.upper() in ['LONG', 'BUY']:
                    direction = 'BUY'
                elif direction.upper() in ['SHORT', 'SELL']:
                    direction = 'SELL'
                else:
                    return OrderResult(False, self.get_current_mode(),
                                     error=f"無效的方向參數: {direction}")

                # 2. 取得當前監控商品
                if not product:
                    product = self.get_current_product()
                    if not product:
                        return OrderResult(False, self.get_current_mode(),
                                         error="無法取得當前監控商品")

                # 3. 根據方向取得正確價格
                if not price:
                    if direction == 'BUY':  # 多單進場
                        price = self.get_ask1_price(product)
                        price_type = "ASK1"
                    elif direction == 'SELL':  # 空單進場
                        price = self.get_bid1_price(product)
                        price_type = "BID1"
                    else:
                        return OrderResult(False, self.get_current_mode(),
                                         error=f"無效的方向: {direction}")

                    if not price:
                        return OrderResult(False, self.get_current_mode(),
                                         error=f"無法取得{product}的{price_type}價格")

                    if self.console_enabled:
                        print(f"[ENTRY_PRICE] {direction}進場使用{price_type}: {price}")

                # 4. 取得策略配置數量
                if not quantity:
                    quantity = self.get_strategy_quantity()

                # 5. 建立下單參數
                order_params = OrderParams(
                    account=self.default_account,
                    product=product,
                    direction=direction,
                    quantity=quantity,
                    price=price,
                    order_type="FOK",
                    new_close=0,  # 新倉
                    day_trade="N",  # 非當沖
                    signal_source=signal_source
                )

                # 6. 根據模式分流處理
                if self.is_real_mode:
                    result = self.execute_real_order(order_params)
                else:
                    result = self.execute_virtual_order(order_params)

                # 7. 更新統計
                self.total_orders += 1
                if result.success:
                    self.success_orders += 1
                else:
                    self.failed_orders += 1

                if result.mode == "real":
                    self.real_orders += 1
                else:
                    self.virtual_orders += 1

                # 8. 記錄訂單
                self.order_history.append({
                    'timestamp': datetime.now(),
                    'params': order_params,
                    'result': result
                })

                # 9. 註冊訂單ID到回報過濾器 (暫時跳過，使用時間過濾)
                # TODO: 實現訂單ID註冊機制

                # 10. Console通知
                if self.console_enabled:
                    status = "成功" if result.success else "失敗"
                    mode_desc = "實單" if result.mode == "real" else "虛擬"
                    print(f"[ORDER_MGR] 🚀 {direction} {mode_desc}下單{status} - {product} {quantity}口 @{price:.0f}")
                    if not result.success:
                        print(f"[ORDER_MGR] ❌ 錯誤: {result.error}")

                return result

        except Exception as e:
            error_msg = f"策略下單執行失敗: {e}"
            if self.console_enabled:
                print(f"[ORDER_MGR] ❌ {error_msg}")
            return OrderResult(False, self.get_current_mode(), error=error_msg)

    def execute_virtual_order(self, order_params: OrderParams) -> OrderResult:
        """
        執行虛擬下單

        Args:
            order_params: 下單參數

        Returns:
            OrderResult: 下單結果
        """
        try:
            # 模擬下單延遲
            time.sleep(0.1)

            # 記錄待追蹤訂單
            self.pending_orders[order_params.order_id] = order_params

            # 模擬成功結果
            result = OrderResult(
                success=True,
                mode="virtual",
                order_id=order_params.order_id
            )

            if self.console_enabled:
                print(f"[ORDER_MGR] 📝 虛擬下單: {order_params.direction} {order_params.product} "
                      f"{order_params.quantity}口 @{order_params.price:.0f} ID:{order_params.order_id}")

            return result

        except Exception as e:
            return OrderResult(False, "virtual", error=f"虛擬下單失敗: {e}")

    def execute_real_order(self, order_params: OrderParams) -> OrderResult:
        """
        執行實際下單 - 使用群益API

        Args:
            order_params: 下單參數

        Returns:
            OrderResult: 下單結果
        """
        try:
            if not CAPITAL_API_AVAILABLE:
                return OrderResult(False, "real", error="群益API未載入")

            # 導入sk模組 (在函數內部導入)
            import comtypes.gen.SKCOMLib as sk

            # 建立FUTUREORDER物件 (使用您測試成功的方式)
            oOrder = sk.FUTUREORDER()
            oOrder.bstrFullAccount = order_params.account
            oOrder.bstrStockNo = order_params.product
            oOrder.sBuySell = 0 if order_params.direction == 'BUY' else 1
            oOrder.sTradeType = 2  # FOK
            oOrder.nQty = order_params.quantity
            oOrder.bstrPrice = str(int(order_params.price))  # 價格轉整數字串
            oOrder.sNewClose = order_params.new_close
            oOrder.sDayTrade = 1 if order_params.day_trade == 'Y' else 0

            # 執行下單 (使用您測試成功的方式)
            api_result = Global.skO.SendFutureOrderCLR(Global.Global_IID, True, oOrder)

            # 記錄待追蹤訂單
            self.pending_orders[order_params.order_id] = order_params

            # 建立結果
            result = OrderResult(
                success=True,
                mode="real",
                order_id=order_params.order_id,
                api_result=api_result
            )

            if self.console_enabled:
                print(f"[ORDER_MGR] ⚡ 實際下單: {order_params.direction} {order_params.product} "
                      f"{order_params.quantity}口 @{order_params.price:.0f} API結果:{api_result}")

            return result

        except Exception as e:
            error_msg = f"實際下單失敗: {e}"
            return OrderResult(False, "real", error=error_msg)

    def get_pending_orders(self) -> Dict[str, OrderParams]:
        """取得待追蹤訂單"""
        with self.data_lock:
            return self.pending_orders.copy()

    def remove_pending_order(self, order_id: str) -> bool:
        """移除待追蹤訂單"""
        try:
            with self.data_lock:
                if order_id in self.pending_orders:
                    del self.pending_orders[order_id]
                    return True
                return False
        except:
            return False

    def get_statistics(self) -> Dict[str, Any]:
        """
        取得統計資訊

        Returns:
            Dict: 統計數據
        """
        with self.data_lock:
            # 動態檢查API狀態
            api_ready = self.check_api_availability() if CAPITAL_API_AVAILABLE else False

            return {
                'current_mode': '實單' if self.is_real_mode else '虛擬',
                'total_orders': self.total_orders,
                'virtual_orders': self.virtual_orders,
                'real_orders': self.real_orders,
                'success_orders': self.success_orders,
                'failed_orders': self.failed_orders,
                'success_rate': (self.success_orders / self.total_orders * 100) if self.total_orders > 0 else 0,
                'pending_orders_count': len(self.pending_orders),
                'supported_products': self.supported_products,
                'default_account': self.default_account,
                'api_module_loaded': CAPITAL_API_AVAILABLE,
                'api_ready': api_ready
            }

    def reset_statistics(self):
        """重置統計數據"""
        with self.data_lock:
            self.total_orders = 0
            self.virtual_orders = 0
            self.real_orders = 0
            self.success_orders = 0
            self.failed_orders = 0
            self.order_history.clear()
            if self.console_enabled:
                print("[ORDER_MGR] 📊 統計數據已重置")

    def validate_order_params(self, order_params: OrderParams) -> tuple[bool, str]:
        """
        驗證下單參數

        Args:
            order_params: 下單參數

        Returns:
            tuple: (是否有效, 錯誤訊息)
        """
        try:
            # 檢查帳號格式
            if not order_params.account.startswith('F020000'):
                return False, f"期貨帳號格式錯誤: {order_params.account}"

            # 檢查商品代碼
            if order_params.product not in self.supported_products:
                return False, f"不支援的商品: {order_params.product}"

            # 檢查方向
            if order_params.direction not in ['BUY', 'SELL']:
                return False, f"無效的方向: {order_params.direction}"

            # 檢查數量
            if order_params.quantity <= 0 or order_params.quantity > 10:
                return False, f"數量超出範圍: {order_params.quantity}"

            # 檢查價格
            if order_params.price <= 0:
                return False, f"價格無效: {order_params.price}"

            return True, ""

        except Exception as e:
            return False, f"參數驗證失敗: {e}"

    def print_status(self):
        """列印當前狀態"""
        if not self.console_enabled:
            return

        stats = self.get_statistics()
        print("\n" + "="*50)
        print("📊 虛實單管理器狀態")
        print("="*50)
        print(f"當前模式: {stats['current_mode']}")
        print(f"總下單數: {stats['total_orders']}")
        print(f"虛擬下單: {stats['virtual_orders']}")
        print(f"實際下單: {stats['real_orders']}")
        print(f"成功率: {stats['success_rate']:.1f}%")
        print(f"待追蹤: {stats['pending_orders_count']}筆")
        print(f"API模組: {'已載入' if stats['api_module_loaded'] else '未載入'}")
        print(f"API狀態: {'就緒' if stats['api_ready'] else '未就緒'}")
        if stats['api_module_loaded'] and not stats['api_ready']:
            print("💡 提示: 請先登入系統後再切換實單模式")
        print("="*50 + "\n")


# 測試函數
def test_virtual_real_order_manager():
    """測試虛實單管理器"""
    print("🧪 測試虛實單管理器...")

    # 創建管理器 (無依賴測試)
    manager = VirtualRealOrderManager(console_enabled=True)

    # 測試模式切換
    print("\n🔄 測試模式切換...")
    print(f"初始模式: {manager.get_current_mode()}")

    # 測試虛擬下單
    print("\n📝 測試虛擬下單...")
    result = manager.execute_strategy_order(
        direction="LONG",
        signal_source="test_breakout"
    )
    print(f"虛擬下單結果: 成功={result.success}, 模式={result.mode}")

    # 測試統計
    print("\n📊 測試統計...")
    manager.print_status()

    print("✅ 虛實單管理器測試完成")


if __name__ == "__main__":
    test_virtual_real_order_manager()
