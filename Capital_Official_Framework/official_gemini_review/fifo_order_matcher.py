# -*- coding: utf-8 -*-
"""
FIFO訂單匹配器
純FIFO匹配邏輯，完全放棄序號匹配
基於時間+價格+商品+數量的匹配機制
"""

import time
import threading
from typing import List, Optional, Tuple
from datetime import datetime
from dataclasses import dataclass
import logging

@dataclass
class OrderInfo:
    """訂單資訊"""
    order_id: str
    product: str
    direction: str  # LONG/SHORT
    quantity: int
    price: float
    submit_time: float  # 使用time.time()時間戳
    status: str = "PENDING"  # PENDING/FILLED/CANCELLED
    
class FIFOOrderMatcher:
    """
    純FIFO訂單匹配器
    完全放棄序號匹配，基於業務邏輯匹配
    """
    
    def __init__(self, console_enabled: bool = True):
        self.console_enabled = console_enabled
        self.logger = logging.getLogger(self.__class__.__name__)
        
        # FIFO訂單隊列 - 按時間排序
        self.pending_orders: List[OrderInfo] = []
        
        # 線程安全鎖
        self.data_lock = threading.Lock()
        
        # 匹配參數
        self.price_tolerance = 10.0  # ±10點價格容差（擴大以適應滑價）
        self.time_window = 30.0     # 30秒時間窗口
        
        # 統計數據
        self.total_registered = 0
        self.total_matched = 0
        self.total_expired = 0
        
        if self.console_enabled:
            print("[FIFO_MATCHER] 純FIFO匹配器已初始化")
    
    def add_pending_order(self, order_info: OrderInfo) -> bool:
        """
        添加待匹配訂單到FIFO隊列
        
        Args:
            order_info: 訂單資訊
            
        Returns:
            bool: 添加是否成功
        """
        try:
            with self.data_lock:
                # 設置提交時間
                if order_info.submit_time == 0:
                    order_info.submit_time = time.time()
                
                # 插入到正確位置以維持時間順序
                inserted = False
                for i, existing_order in enumerate(self.pending_orders):
                    if order_info.submit_time < existing_order.submit_time:
                        self.pending_orders.insert(i, order_info)
                        inserted = True
                        break
                
                if not inserted:
                    self.pending_orders.append(order_info)
                
                self.total_registered += 1
                
                if self.console_enabled:
                    print(f"[FIFO_MATCHER] 📝 註冊訂單: {order_info.product} "
                          f"{order_info.direction} {order_info.quantity}口 @{order_info.price}")
                
                return True
                
        except Exception as e:
            if self.console_enabled:
                print(f"[FIFO_MATCHER] ❌ 添加訂單失敗: {e}")
            return False
    
    def find_match(self, price: float, qty: int, product: str, order_type: str = "D") -> Optional[OrderInfo]:
        """
        FIFO匹配邏輯 - 核心方法

        Args:
            price: 回報價格
            qty: 回報數量
            product: 回報商品代碼
            order_type: 回報類型 ("D"=成交, "C"=取消, "N"=新單)

        Returns:
            Optional[OrderInfo]: 匹配的訂單，None表示無匹配
        """
        try:
            with self.data_lock:
                current_time = time.time()
                normalized_product = self._normalize_product(product)

                # 清理過期訂單
                self._cleanup_expired_orders(current_time)

                # 🔧 取消回報特殊處理：只匹配商品和時間，不匹配價格數量
                if order_type == "C":
                    return self._find_cancel_match(normalized_product, current_time)

                # FIFO搜索：從最早的訂單開始
                for i, order_info in enumerate(self.pending_orders):
                    # 檢查時間窗口
                    if current_time - order_info.submit_time > self.time_window:
                        continue

                    # 檢查商品匹配
                    if self._normalize_product(order_info.product) != normalized_product:
                        continue

                    # 檢查數量匹配
                    if order_info.quantity != qty:
                        continue

                    # 檢查價格匹配（±5點容差）
                    if abs(order_info.price - price) <= self.price_tolerance:
                        # 找到匹配，移除並返回
                        matched_order = self.pending_orders.pop(i)
                        matched_order.status = "MATCHED"
                        self.total_matched += 1

                        if self.console_enabled:
                            print(f"[FIFO_MATCHER] ✅ FIFO匹配成功: {product} {qty}口 @{price} "
                                  f"→ 訂單{matched_order.order_id}")

                        return matched_order

                # 沒有找到匹配
                if self.console_enabled:
                    print(f"[FIFO_MATCHER] ⚠️ 找不到匹配: {product} {qty}口 @{price}")

                return None

        except Exception as e:
            if self.console_enabled:
                print(f"[FIFO_MATCHER] ❌ 匹配失敗: {e}")
            return None

    def _find_cancel_match(self, normalized_product: str, current_time: float) -> Optional[OrderInfo]:
        """
        取消回報專用匹配邏輯 - 只匹配商品和時間

        Args:
            normalized_product: 標準化商品代碼
            current_time: 當前時間

        Returns:
            Optional[OrderInfo]: 匹配的訂單，None表示無匹配
        """
        try:
            # 🔧 取消回報：找到最早的同商品訂單
            for i, order_info in enumerate(self.pending_orders):
                # 檢查時間窗口
                if current_time - order_info.submit_time > self.time_window:
                    continue

                # 檢查商品匹配
                if self._normalize_product(order_info.product) != normalized_product:
                    continue

                # 找到匹配，移除並返回
                matched_order = self.pending_orders.pop(i)
                matched_order.status = "CANCELLED"
                self.total_matched += 1

                if self.console_enabled:
                    print(f"[FIFO_MATCHER] ✅ 取消匹配成功: {normalized_product} "
                          f"→ 訂單{matched_order.order_id}")

                return matched_order

            # 沒有找到匹配
            if self.console_enabled:
                print(f"[FIFO_MATCHER] ⚠️ 找不到取消匹配: {normalized_product}")

            return None

        except Exception as e:
            if self.console_enabled:
                print(f"[FIFO_MATCHER] ❌ 取消匹配失敗: {e}")
            return None
    
    def _normalize_product(self, product: str) -> str:
        """
        標準化商品代碼
        處理TM0000與TM2507等具體合約的映射
        """
        if not product:
            return ""
        
        # TM2507 -> TM0000 (將具體合約映射為通用代碼)
        if product.startswith("TM") and len(product) == 6:
            return "TM0000"
        # MTX07 -> MTX00 (同樣邏輯)
        elif product.startswith("MTX") and len(product) == 5:
            return "MTX00"
        else:
            return product
    
    def _cleanup_expired_orders(self, current_time: float):
        """清理過期訂單"""
        try:
            expired_count = 0
            self.pending_orders = [
                order for order in self.pending_orders
                if current_time - order.submit_time <= self.time_window
            ]
            
            if expired_count > 0:
                self.total_expired += expired_count
                if self.console_enabled:
                    print(f"[FIFO_MATCHER] 🗑️ 清理過期訂單: {expired_count}筆")
                    
        except Exception as e:
            if self.console_enabled:
                print(f"[FIFO_MATCHER] ❌ 清理過期訂單失敗: {e}")
    
    def get_pending_count(self) -> int:
        """獲取待匹配訂單數量"""
        with self.data_lock:
            return len(self.pending_orders)
    
    def get_statistics(self) -> dict:
        """獲取統計數據"""
        with self.data_lock:
            return {
                'total_registered': self.total_registered,
                'total_matched': self.total_matched,
                'total_expired': self.total_expired,
                'pending_count': len(self.pending_orders)
            }
    
    def clear_all_orders(self):
        """清空所有待匹配訂單"""
        with self.data_lock:
            cleared_count = len(self.pending_orders)
            self.pending_orders.clear()

            if self.console_enabled and cleared_count > 0:
                print(f"[FIFO_MATCHER] 🗑️ 清空所有待匹配訂單: {cleared_count}筆")

# 測試函數
def test_fifo_matcher():
    """測試FIFO匹配器功能"""
    print("🧪 開始測試FIFO匹配器...")

    matcher = FIFOOrderMatcher(console_enabled=True)

    # 測試1: 正常成交匹配
    print("\n📋 測試1: 正常成交匹配")
    order1 = OrderInfo(
        order_id="test_001",
        product="TM0000",
        direction="LONG",
        quantity=1,
        price=22334.0,
        submit_time=time.time()
    )
    matcher.add_pending_order(order1)

    # 模擬回報匹配
    matched = matcher.find_match(price=22334.0, qty=1, product="TM2507")
    assert matched is not None, "正常成交匹配失敗"
    assert matched.order_id == "test_001", "匹配到錯誤的訂單"
    print("✅ 正常成交匹配測試通過")

    # 測試2: 滑價成交匹配
    print("\n📋 測試2: 滑價成交匹配")
    order2 = OrderInfo(
        order_id="test_002",
        product="TM0000",
        direction="SHORT",
        quantity=2,
        price=22340.0,
        submit_time=time.time()
    )
    matcher.add_pending_order(order2)

    # 模擬滑價成交 (+3點)
    matched = matcher.find_match(price=22343.0, qty=2, product="TM2507")
    assert matched is not None, "滑價成交匹配失敗"
    assert matched.order_id == "test_002", "匹配到錯誤的訂單"
    print("✅ 滑價成交匹配測試通過")

    # 測試3: FIFO順序測試
    print("\n📋 測試3: FIFO順序測試")
    order3 = OrderInfo(
        order_id="first",
        product="TM0000",
        direction="LONG",
        quantity=1,
        price=22350.0,
        submit_time=time.time()
    )
    matcher.add_pending_order(order3)

    time.sleep(0.1)  # 確保時間差

    order4 = OrderInfo(
        order_id="second",
        product="TM0000",
        direction="LONG",
        quantity=1,
        price=22351.0,
        submit_time=time.time()
    )
    matcher.add_pending_order(order4)

    # 應該匹配到最早的訂單
    matched = matcher.find_match(price=22350.0, qty=1, product="TM2507")
    assert matched is not None, "FIFO順序匹配失敗"
    assert matched.order_id == "first", "FIFO順序錯誤"
    print("✅ FIFO順序測試通過")

    # 測試4: 無匹配情況
    print("\n📋 測試4: 無匹配情況")
    matched = matcher.find_match(price=99999.0, qty=1, product="TM2507")
    assert matched is None, "應該無匹配但返回了結果"
    print("✅ 無匹配測試通過")

    # 顯示統計
    stats = matcher.get_statistics()
    print(f"\n📊 測試統計: {stats}")
    print("🎉 所有測試通過！")

if __name__ == "__main__":
    test_fifo_matcher()
