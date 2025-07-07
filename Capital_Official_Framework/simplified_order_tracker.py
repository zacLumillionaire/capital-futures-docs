# -*- coding: utf-8 -*-
"""
簡化訂單追蹤器
基於策略組統計的追蹤機制，避免群益API序號映射問題
"""

import time
import threading
from datetime import datetime
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
from enum import Enum
import logging

# 導入FIFO匹配器以保持一致性
try:
    from fifo_order_matcher import FIFOOrderMatcher, OrderInfo as FIFOOrderInfo
except ImportError:
    # 如果直接導入失敗，嘗試相對路徑
    import sys
    import os
    current_dir = os.path.dirname(os.path.abspath(__file__))
    sys.path.append(current_dir)
    from fifo_order_matcher import FIFOOrderMatcher, OrderInfo as FIFOOrderInfo

class GroupStatus(Enum):
    """策略組狀態"""
    PENDING = "PENDING"      # 等待中
    PARTIAL = "PARTIAL"      # 部分成交
    FILLED = "FILLED"        # 全部成交
    CANCELLED = "CANCELLED"  # 已取消
    FAILED = "FAILED"        # 失敗

@dataclass
class StrategyGroup:
    """策略組追蹤器"""
    group_id: int
    total_lots: int          # 預期下單口數
    direction: str           # LONG/SHORT
    target_price: float      # 目標價格
    product: str             # 商品代碼
    
    # 統計數據
    submitted_lots: int = 0   # 已送出口數  
    filled_lots: int = 0      # 已成交口數
    cancelled_lots: int = 0   # 已取消口數
    
    # 追價控制
    retry_count: int = 0      # 追價次數
    max_retries: int = 5      # 最大追價次數
    price_tolerance: float = 5.0  # 價格容差(點)

    # 時間控制
    submit_time: float = 0    # 提交時間
    last_retry_time: float = 0  # 最後重試時間

    # 🔧 新增：追價狀態控制
    pending_retry_lots: int = 0  # 等待追價的口數
    is_retrying: bool = False    # 是否正在追價中
    
    def __post_init__(self):
        self.submit_time = time.time()
    
    @property
    def status(self) -> GroupStatus:
        """獲取當前狀態"""
        if self.filled_lots >= self.total_lots:
            return GroupStatus.FILLED
        elif self.filled_lots > 0:
            return GroupStatus.PARTIAL
        elif self.cancelled_lots > 0 and self.retry_count >= self.max_retries:
            return GroupStatus.CANCELLED
        elif self.submitted_lots > 0:
            return GroupStatus.PENDING
        else:
            return GroupStatus.PENDING
    
    def is_complete(self) -> bool:
        """檢查策略組是否完成"""
        return self.filled_lots >= self.total_lots
        
    def needs_retry(self) -> bool:
        """檢查是否需要追價"""
        # 🔧 改進：考慮已送出但未回報的口數，避免多下單
        remaining_lots = self.total_lots - self.filled_lots
        return (remaining_lots > 0 and
                self.retry_count < self.max_retries and
                self.submitted_lots <= self.total_lots)  # 防止超量下單
    
    def can_match_price(self, price: float) -> bool:
        """檢查價格是否在容差範圍內"""
        return abs(price - self.target_price) <= self.price_tolerance

class SimplifiedOrderTracker:
    """
    簡化訂單追蹤器
    基於策略組統計，避免API序號映射問題
    """
    
    def __init__(self, console_enabled: bool = True):
        self.console_enabled = console_enabled
        self.logger = logging.getLogger(self.__class__.__name__)

        # 策略組追蹤 - 使用字典避免線程問題
        self.strategy_groups: Dict[int, StrategyGroup] = {}

        # 🔧 新增：平倉訂單追蹤
        self.exit_orders = {}  # {order_id: exit_order_info}
        self.exit_position_mapping = {}  # {position_id: order_id}

        # 統計數據
        self.total_groups = 0
        self.completed_groups = 0
        self.failed_groups = 0

        # 線程安全鎖 - 避免GIL問題
        self.data_lock = threading.Lock()

        # 回調函數
        self.fill_callbacks: List = []
        self.retry_callbacks: List = []
        self.exit_fill_callbacks: List = []  # 🔧 新增：平倉成交回調
        self.exit_retry_callbacks: List = []  # 🔧 新增：平倉追價回調

        if self.console_enabled:
            print("[SIMPLIFIED_TRACKER] 簡化追蹤器已初始化")

    def register_exit_order(self, position_id: int, order_id: str, direction: str,
                           quantity: int, price: float, product: str = "TM0000") -> bool:
        """
        註冊平倉訂單

        Args:
            position_id: 部位ID
            order_id: 訂單ID
            direction: 平倉方向
            quantity: 數量
            price: 價格
            product: 商品代碼

        Returns:
            bool: 註冊是否成功
        """
        try:
            with self.data_lock:
                exit_info = {
                    'position_id': position_id,
                    'order_id': order_id,
                    'direction': direction,
                    'quantity': quantity,
                    'price': price,
                    'product': product,
                    'submit_time': time.time(),
                    'status': 'PENDING'
                }

                self.exit_orders[order_id] = exit_info
                self.exit_position_mapping[position_id] = order_id

                if self.console_enabled:
                    print(f"[SIMPLIFIED_TRACKER] 📝 註冊平倉訂單: 部位{position_id} "
                          f"{direction} {quantity}口 @{price}")

                return True

        except Exception as e:
            if self.console_enabled:
                print(f"[SIMPLIFIED_TRACKER] ❌ 註冊平倉訂單失敗: {e}")
            return False

    def register_strategy_group(self, group_id: int, total_lots: int,
                              direction: str, target_price: float,
                              product: str = "TM0000") -> bool:
        """
        註冊策略組
        
        Args:
            group_id: 策略組ID
            total_lots: 總口數
            direction: 方向 (LONG/SHORT)
            target_price: 目標價格
            product: 商品代碼
            
        Returns:
            bool: 註冊是否成功
        """
        try:
            with self.data_lock:
                # 創建策略組
                strategy_group = StrategyGroup(
                    group_id=group_id,
                    total_lots=total_lots,
                    direction=direction,
                    target_price=target_price,
                    product=product
                )
                
                self.strategy_groups[group_id] = strategy_group
                self.total_groups += 1
                
                if self.console_enabled:
                    print(f"[SIMPLIFIED_TRACKER] 📝 註冊策略組: {group_id} "
                          f"{direction} {product} {total_lots}口 @{target_price:.0f}")
                
                return True
                
        except Exception as e:
            if self.console_enabled:
                print(f"[SIMPLIFIED_TRACKER] ❌ 註冊策略組失敗: {e}")
            return False
    
    def update_submitted_lots(self, group_id: int, lots: int) -> bool:
        """
        更新已送出口數

        Args:
            group_id: 策略組ID
            lots: 送出口數

        Returns:
            bool: 更新是否成功
        """
        try:
            with self.data_lock:
                if group_id not in self.strategy_groups:
                    return False

                group = self.strategy_groups[group_id]
                group.submitted_lots += lots

                # 🔧 新增：重置追價狀態（新的下單已送出）
                if group.is_retrying:
                    group.is_retrying = False
                    group.pending_retry_lots = 0

                if self.console_enabled:
                    print(f"[SIMPLIFIED_TRACKER] 📤 組{group_id}送出: {lots}口, "
                          f"總計: {group.submitted_lots}/{group.total_lots}")

                return True

        except Exception as e:
            if self.console_enabled:
                print(f"[SIMPLIFIED_TRACKER] ❌ 更新送出口數失敗: {e}")
            return False
    
    def process_order_reply(self, reply_data: str) -> bool:
        """
        統一處理進場和平倉回報 - 避免重複處理

        Args:
            reply_data: OnNewData回報數據 (逗號分隔)

        Returns:
            bool: 處理是否成功
        """
        try:
            fields = reply_data.split(',')
            if len(fields) < 25:
                return False

            order_type = fields[2] if len(fields) > 2 else ""  # N/C/D
            price = float(fields[11]) if fields[11] else 0     # 價格
            qty = int(fields[20]) if fields[20] else 0         # 數量
            product = fields[8] if len(fields) > 8 else ""     # 商品代號

            if self.console_enabled:
                print(f"[SIMPLIFIED_TRACKER] 🔍 FIFO處理回報: Type={order_type}, Product={product}, Price={price}, Qty={qty}")

            processed = False

            if order_type == "D":  # 成交
                # 🔧 修復: 先嘗試進場成交處理 (更常見的情況)
                processed = self._handle_fill_report_fifo(price, qty, product)
                if processed:
                    if self.console_enabled:
                        print(f"[SIMPLIFIED_TRACKER] ✅ 進場成交處理完成")
                    return True

                # 再嘗試平倉成交處理
                processed = self._handle_exit_fill_report(price, qty, product)
                if processed:
                    if self.console_enabled:
                        print(f"[SIMPLIFIED_TRACKER] ✅ 平倉成交處理完成")
                    return True

            elif order_type == "C":  # 取消
                # 🔧 修復: 先嘗試進場取消處理 (更常見的情況)
                processed = self._handle_cancel_report_fifo(price, qty, product)
                if processed:
                    if self.console_enabled:
                        print(f"[SIMPLIFIED_TRACKER] ✅ 進場取消處理完成")
                    return True

                # 再嘗試平倉取消處理
                processed = self._handle_exit_cancel_report(price, qty, product)
                if processed:
                    if self.console_enabled:
                        print(f"[SIMPLIFIED_TRACKER] ✅ 平倉取消處理完成")
                    return True

            return False

        except Exception as e:
            if self.console_enabled:
                print(f"[SIMPLIFIED_TRACKER] ❌ 處理回報失敗: {e}")
            return False
    
    def _handle_fill_report_fifo(self, price: float, qty: int, product: str) -> bool:
        """
        處理成交回報 - 純FIFO版本

        Args:
            price: 成交價格
            qty: 成交數量
            product: 商品代碼

        Returns:
            bool: 處理是否成功
        """
        try:
            with self.data_lock:
                # 使用純FIFO匹配找到策略組
                group = self._find_matching_group_fifo(price, qty, product)
                if not group:
                    if self.console_enabled:
                        normalized_product = self._normalize_product_code(product)
                        print(f"[SIMPLIFIED_TRACKER] ⚠️ FIFO找不到匹配的策略組: "
                              f"{normalized_product} {qty}口 @{price:.0f}")
                    return False

                # 更新成交統計
                group.filled_lots += qty

                if self.console_enabled:
                    print(f"[SIMPLIFIED_TRACKER] ✅ 策略組{group.group_id}成交: "
                          f"{qty}口 @{price:.0f}, 總計: {group.filled_lots}/{group.total_lots}")

                # 檢查是否完成
                if group.is_complete():
                    self.completed_groups += 1
                    if self.console_enabled:
                        print(f"[SIMPLIFIED_TRACKER] 🎉 策略組{group.group_id}建倉完成!")

                    # 觸發完成回調
                    self._trigger_fill_callbacks(group, price, qty)

                return True

        except Exception as e:
            if self.console_enabled:
                print(f"[SIMPLIFIED_TRACKER] ❌ 處理成交回報失敗: {e}")
            return False

    def _handle_cancel_report_fifo(self, price: float, qty: int, product: str) -> bool:
        """
        處理取消回報 - 純FIFO版本

        Args:
            price: 取消價格 (通常為0)
            qty: 取消數量 (通常為0)
            product: 商品代碼

        Returns:
            bool: 處理是否成功
        """
        try:
            with self.data_lock:
                # 🔧 取消回報特殊處理：找到最早的未完成策略組
                group = self._find_earliest_pending_group_by_product(product)
                if not group:
                    if self.console_enabled:
                        normalized_product = self._normalize_product_code(product)
                        print(f"[SIMPLIFIED_TRACKER] ⚠️ 找不到待處理的策略組(取消): {normalized_product}")
                    return False

                # 🔧 取消時增加取消口數（假設每次取消1口）
                cancel_qty = 1  # 取消回報通常數量為0，我們假設取消1口
                group.cancelled_lots += cancel_qty

                if self.console_enabled:
                    print(f"[SIMPLIFIED_TRACKER] ❌ 策略組{group.group_id}取消: "
                          f"{cancel_qty}口 (原回報: {qty}口 @{price})")
                    print(f"[SIMPLIFIED_TRACKER] 📊 組{group.group_id}狀態: "
                          f"總{group.total_lots}口, 成交{group.filled_lots}口, 取消{group.cancelled_lots}口")

                # 觸發追價邏輯
                if group.needs_retry() and not group.is_retrying:
                    current_time = time.time()
                    # 避免頻繁重試 (至少間隔1秒)
                    if current_time - group.last_retry_time >= 1.0:
                        # 🔧 修復: 計算需要追價的口數 (取消回報qty通常為0，使用cancel_qty)
                        remaining_lots = group.total_lots - group.filled_lots
                        retry_lots = min(cancel_qty, remaining_lots)  # 使用實際取消的口數

                        if self.console_enabled:
                            print(f"[SIMPLIFIED_TRACKER] 🔄 追價邏輯檢查:")
                            print(f"[SIMPLIFIED_TRACKER]   總口數: {group.total_lots}, 已成交: {group.filled_lots}")
                            print(f"[SIMPLIFIED_TRACKER]   剩餘口數: {remaining_lots}, 追價口數: {retry_lots}")

                        if retry_lots > 0:
                            group.is_retrying = True
                            group.last_retry_time = current_time
                            group.retry_count += 1

                            if self.console_enabled:
                                print(f"[SIMPLIFIED_TRACKER] 🚀 觸發追價: {retry_lots}口")

                            # 觸發追價回調
                            self._trigger_retry_callbacks(group, retry_lots, price)
                        else:
                            if self.console_enabled:
                                print(f"[SIMPLIFIED_TRACKER] ⚠️ 追價口數為0，跳過追價")

                return True

        except Exception as e:
            if self.console_enabled:
                print(f"[SIMPLIFIED_TRACKER] ❌ 處理取消回報失敗: {e}")
            return False

    def _find_earliest_pending_group_by_product(self, product: str) -> Optional[StrategyGroup]:
        """
        根據商品找到最早的未完成策略組

        Args:
            product: 商品代碼

        Returns:
            Optional[StrategyGroup]: 最早的未完成策略組
        """
        try:
            normalized_product = self._normalize_product_code(product)
            candidates = []

            # 收集所有符合條件的策略組
            for group in self.strategy_groups.values():
                # 檢查商品匹配
                if self._normalize_product_code(group.product) != normalized_product:
                    continue

                # 檢查是否未完成
                if group.is_complete():
                    continue

                # 檢查是否有已送出但未成交的口數
                if hasattr(group, 'sent_lots') and hasattr(group, 'filled_lots'):
                    if group.sent_lots > group.filled_lots:
                        candidates.append((group, group.submit_time))
                else:
                    # 如果沒有sent_lots屬性，檢查其他條件
                    if not group.is_complete():
                        candidates.append((group, group.submit_time))

            # 返回最早的策略組
            if candidates:
                return min(candidates, key=lambda x: x[1])[0]

            return None

        except Exception as e:
            if self.console_enabled:
                print(f"[SIMPLIFIED_TRACKER] ❌ 查找最早策略組失敗: {e}")
            return None

    def _find_matching_group_fifo(self, price: float, qty: int, product: str) -> Optional[StrategyGroup]:
        """
        純FIFO匹配策略組 - 不依賴方向

        Args:
            price: 回報價格
            qty: 回報數量
            product: 商品代碼

        Returns:
            Optional[StrategyGroup]: 匹配的策略組，None表示無匹配
        """
        try:
            current_time = time.time()
            normalized_product = self._normalize_product_code(product)
            candidates = []

            # 收集所有符合條件的候選組
            for group in self.strategy_groups.values():
                # 檢查商品匹配
                if self._normalize_product_code(group.product) != normalized_product:
                    continue

                # 檢查完成狀態
                if group.is_complete():
                    continue

                # 檢查時間窗口 (30秒內)
                if current_time - group.submit_time > 30:
                    continue

                # 檢查數量匹配（簡化追蹤器可能不需要嚴格匹配數量）
                # 這裡我們放寬條件，只要組還需要成交就可以匹配
                if group.filled_lots >= group.total_lots:
                    continue

                # 檢查價格匹配 (±5點容差)
                if abs(price - group.target_price) <= group.price_tolerance:
                    candidates.append((group, group.submit_time))

            # FIFO: 返回最早的策略組
            if candidates:
                return min(candidates, key=lambda x: x[1])[0]

            return None

        except Exception as e:
            if self.console_enabled:
                print(f"[SIMPLIFIED_TRACKER] ❌ FIFO匹配失敗: {e}")
            return None

    def _convert_api_to_strategy_direction(self, api_direction: str) -> str:
        """
        將API方向轉換為策略方向

        Args:
            api_direction: API方向 ('BUY'/'SELL')

        Returns:
            策略方向 ('LONG'/'SHORT')
        """
        if api_direction == "BUY":
            return "LONG"
        elif api_direction == "SELL":
            return "SHORT"
        else:
            return "UNKNOWN"

    def _normalize_product_code(self, product: str) -> str:
        """
        標準化商品代碼，處理TM0000與TM2507的映射

        Args:
            product: 原始商品代碼

        Returns:
            標準化後的商品代碼
        """
        # TM2507 -> TM0000 (將具體合約映射為通用代碼)
        if product.startswith("TM") and len(product) == 6:
            return "TM0000"
        # MTX07 -> MTX00 (同樣邏輯)
        elif product.startswith("MTX") and len(product) == 5:
            return "MTX00"
        else:
            return product

    def _find_matching_group(self, price: float, api_direction: str,
                           product: str) -> Optional[StrategyGroup]:
        """
        找到匹配的策略組 - 純FIFO匹配（不依賴方向）

        Args:
            price: 成交價格
            api_direction: API方向（已知為UNKNOWN，不使用）
            product: 商品代碼
        """
        try:
            current_time = time.time()
            candidates = []

            # 🔧 最終修正：不依賴方向，純粹基於FIFO + 價格 + 商品匹配
            normalized_product = self._normalize_product_code(product)

            # 收集所有符合條件的候選組（不檢查方向）
            for group in self.strategy_groups.values():
                # 🚀 新邏輯：只檢查商品和完成狀態，不檢查方向
                if (self._normalize_product_code(group.product) == normalized_product and
                    not group.is_complete()):

                    # 檢查時間窗口 (30秒內，FIFO原則)
                    if current_time - group.submit_time <= 30:
                        # 檢查價格匹配 (±5點容差)
                        if group.can_match_price(price):
                            price_diff = abs(price - group.target_price)
                            # FIFO優先：最早的時間優先
                            time_factor = group.submit_time
                            candidates.append((group, price_diff, time_factor))

            # 🔍 衝突檢測日誌
            if len(candidates) > 1:
                candidate_info = []
                for group, price_diff, time_factor in candidates:
                    candidate_info.append(f"組{group.group_id}(目標{group.target_price:.0f}, 差距{price_diff:.1f}點)")

                if self.console_enabled:
                    print(f"[SIMPLIFIED_TRACKER] ⚠️ 價格匹配衝突檢測:")
                    print(f"    成交價格: {price}")
                    print(f"    商品: {normalized_product}")
                    print(f"    候選組: {', '.join(candidate_info)}")

                # 記錄到日誌
                self.logger.warning(f"多組匹配衝突: 價格{price} {normalized_product}, "
                                  f"候選組{[c[0].group_id for c in candidates]}")

            if not candidates:
                return None

            # 🎯 FIFO優先選擇 (最早時間優先，然後是最近價格)
            best_group, min_price_diff, earliest_time = min(candidates, key=lambda x: (x[2], x[1]))

            if self.console_enabled and len(candidates) > 1:
                print(f"[SIMPLIFIED_TRACKER] 🎯 FIFO選擇: 組{best_group.group_id} "
                      f"(差距{min_price_diff:.1f}點, 時間{earliest_time})")

            return best_group

        except Exception as e:
            if self.console_enabled:
                print(f"[SIMPLIFIED_TRACKER] ❌ 匹配策略組失敗: {e}")
            return None

    def _handle_fill_report(self, price: float, qty: int, api_direction: str,
                          product: str) -> bool:
        """
        處理成交回報 - 修正版本

        Args:
            price: 成交價格
            qty: 成交數量
            api_direction: API方向 ('BUY'/'SELL')
            product: 商品代碼

        Returns:
            bool: 處理是否成功
        """
        try:
            with self.data_lock:
                # 🔧 修正：使用新的匹配邏輯
                group = self._find_matching_group(price, api_direction, product)
                if not group:
                    if self.console_enabled:
                        strategy_direction = self._convert_api_to_strategy_direction(api_direction)
                        normalized_product = self._normalize_product_code(product)
                        print(f"[SIMPLIFIED_TRACKER] ⚠️ 找不到匹配的策略組: "
                              f"{strategy_direction} {normalized_product} {qty}口 @{price:.0f}")
                    return False

                # 更新成交統計
                group.filled_lots += qty

                if self.console_enabled:
                    print(f"[SIMPLIFIED_TRACKER] ✅ 策略組{group.group_id}成交: "
                          f"{qty}口 @{price:.0f}, 總計: {group.filled_lots}/{group.total_lots}")

                # 檢查是否完成
                if group.is_complete():
                    self.completed_groups += 1
                    if self.console_enabled:
                        print(f"[SIMPLIFIED_TRACKER] 🎉 策略組{group.group_id}建倉完成!")

                    # 觸發完成回調
                    self._trigger_fill_callbacks(group, price, qty)

                return True

        except Exception as e:
            if self.console_enabled:
                print(f"[SIMPLIFIED_TRACKER] ❌ 處理成交回報失敗: {e}")
            return False

    def _handle_cancel_report(self, price: float, qty: int, direction: str,
                            product: str) -> bool:
        """
        處理取消回報 - 觸發追價

        Args:
            price: 取消價格
            qty: 取消數量
            direction: 交易方向
            product: 商品代碼

        Returns:
            bool: 處理是否成功
        """
        try:
            with self.data_lock:
                # 找到匹配的策略組
                group = self._find_matching_group(price, direction, product)
                if not group:
                    if self.console_enabled:
                        print(f"[SIMPLIFIED_TRACKER] ⚠️ 找不到匹配的策略組(取消): "
                              f"{direction} {product} {qty}口 @{price}")
                    return False

                # 更新取消統計
                group.cancelled_lots += qty

                if self.console_enabled:
                    print(f"[SIMPLIFIED_TRACKER] ❌ 策略組{group.group_id}取消: "
                          f"{qty}口 @{price}")

                # 🔧 改進：精確的追價控制邏輯
                if group.needs_retry() and not group.is_retrying:
                    current_time = time.time()
                    # 避免頻繁重試 (至少間隔1秒)
                    if current_time - group.last_retry_time >= 1.0:
                        # 計算需要追價的口數
                        remaining_lots = group.total_lots - group.filled_lots
                        retry_lots = min(qty, remaining_lots)  # 不超過剩餘需求

                        if retry_lots > 0:
                            group.retry_count += 1
                            group.last_retry_time = current_time
                            group.pending_retry_lots = retry_lots
                            group.is_retrying = True  # 標記為追價中

                            if self.console_enabled:
                                print(f"[SIMPLIFIED_TRACKER] 🔄 觸發策略組{group.group_id}追價: "
                                      f"第{group.retry_count}次重試, {retry_lots}口")

                            # 觸發追價回調
                            self._trigger_retry_callbacks(group, retry_lots, price)
                else:
                    if group.retry_count >= group.max_retries:
                        self.failed_groups += 1
                        if self.console_enabled:
                            print(f"[SIMPLIFIED_TRACKER] 💀 策略組{group.group_id}達到最大重試次數")

                return True

        except Exception as e:
            if self.console_enabled:
                print(f"[SIMPLIFIED_TRACKER] ❌ 處理取消回報失敗: {e}")
            return False

    def _trigger_fill_callbacks(self, group: StrategyGroup, price: float, qty: int):
        """觸發成交回調 - 避免GIL問題"""
        try:
            # 直接調用回調，不使用線程
            for callback in self.fill_callbacks:
                try:
                    callback(group.group_id, price, qty, group.filled_lots, group.total_lots)
                except Exception as e:
                    if self.console_enabled:
                        print(f"[SIMPLIFIED_TRACKER] ⚠️ 成交回調失敗: {e}")
        except Exception as e:
            if self.console_enabled:
                print(f"[SIMPLIFIED_TRACKER] ❌ 觸發成交回調失敗: {e}")

    def _trigger_retry_callbacks(self, group: StrategyGroup, qty: int, price: float):
        """觸發追價回調 - 避免GIL問題"""
        try:
            # 直接調用回調，不使用線程
            for callback in self.retry_callbacks:
                try:
                    callback(group.group_id, qty, price, group.retry_count)
                except Exception as e:
                    if self.console_enabled:
                        print(f"[SIMPLIFIED_TRACKER] ⚠️ 追價回調失敗: {e}")
        except Exception as e:
            if self.console_enabled:
                print(f"[SIMPLIFIED_TRACKER] ❌ 觸發追價回調失敗: {e}")

    def add_fill_callback(self, callback):
        """添加成交回調"""
        self.fill_callbacks.append(callback)

    def add_retry_callback(self, callback):
        """添加追價回調"""
        self.retry_callbacks.append(callback)

    def get_group_status(self, group_id: int) -> Optional[Dict]:
        """
        獲取策略組狀態

        Args:
            group_id: 策略組ID

        Returns:
            Dict: 策略組狀態信息
        """
        try:
            with self.data_lock:
                if group_id not in self.strategy_groups:
                    return None

                group = self.strategy_groups[group_id]
                return {
                    'group_id': group.group_id,
                    'status': group.status.value,
                    'total_lots': group.total_lots,
                    'filled_lots': group.filled_lots,
                    'cancelled_lots': group.cancelled_lots,
                    'retry_count': group.retry_count,
                    'target_price': group.target_price,
                    'direction': group.direction,
                    'product': group.product
                }

        except Exception as e:
            if self.console_enabled:
                print(f"[SIMPLIFIED_TRACKER] ❌ 獲取策略組狀態失敗: {e}")
            return None

    def get_statistics(self) -> Dict:
        """獲取統計信息"""
        try:
            with self.data_lock:
                return {
                    'total_groups': self.total_groups,
                    'completed_groups': self.completed_groups,
                    'failed_groups': self.failed_groups,
                    'active_groups': len([g for g in self.strategy_groups.values()
                                        if not g.is_complete() and g.status != GroupStatus.CANCELLED])
                }
        except Exception as e:
            if self.console_enabled:
                print(f"[SIMPLIFIED_TRACKER] ❌ 獲取統計信息失敗: {e}")
            return {}

    def cleanup_completed_groups(self, max_age_seconds: int = 3600):
        """清理已完成的策略組 (避免記憶體洩漏)"""
        try:
            with self.data_lock:
                current_time = time.time()
                to_remove = []

                for group_id, group in self.strategy_groups.items():
                    if (group.is_complete() or group.status == GroupStatus.CANCELLED):
                        if current_time - group.submit_time > max_age_seconds:
                            to_remove.append(group_id)

                for group_id in to_remove:
                    del self.strategy_groups[group_id]
                    if self.console_enabled:
                        print(f"[SIMPLIFIED_TRACKER] 🧹 清理已完成策略組: {group_id}")

        except Exception as e:
            if self.console_enabled:
                print(f"[SIMPLIFIED_TRACKER] ❌ 清理策略組失敗: {e}")

    def get_strategy_group(self, group_id: int) -> Optional[StrategyGroup]:
        """獲取策略組"""
        with self.data_lock:
            return self.strategy_groups.get(group_id)

    def _handle_exit_fill_report(self, price: float, qty: int, product: str) -> bool:
        """
        處理平倉成交回報

        Args:
            price: 成交價格
            qty: 成交數量
            product: 商品代碼

        Returns:
            bool: 處理是否成功
        """
        try:
            with self.data_lock:
                # 🔍 DEBUG: 平倉成交回報處理 (重要事件，立即輸出)
                if self.console_enabled:
                    print(f"[SIMPLIFIED_TRACKER] 📥 收到平倉成交回報:")
                    print(f"[SIMPLIFIED_TRACKER]   價格: {price:.0f} 數量: {qty} 商品: {product}")
                    print(f"[SIMPLIFIED_TRACKER]   待匹配平倉訂單: {len(self.exit_orders)}個")

                # 找到匹配的平倉訂單
                exit_order = self._find_matching_exit_order(price, qty, product)
                if not exit_order:
                    if self.console_enabled:
                        print(f"[SIMPLIFIED_TRACKER] ⚠️ 找不到匹配的平倉訂單")
                        print(f"[SIMPLIFIED_TRACKER]   搜尋條件: 價格={price:.0f}, 數量={qty}, 商品={product}")
                        # 顯示現有的平倉訂單供調試
                        if len(self.exit_orders) > 0:
                            print(f"[SIMPLIFIED_TRACKER]   現有平倉訂單:")
                            for order_id, order in self.exit_orders.items():
                                print(f"[SIMPLIFIED_TRACKER]     訂單{order_id}: 價格={order['price']:.0f}, 數量={order['quantity']}, 商品={order['product']}")
                        else:
                            print(f"[SIMPLIFIED_TRACKER]   目前沒有待匹配的平倉訂單")
                    return False

                # 🔍 DEBUG: 找到匹配訂單
                if self.console_enabled:
                    print(f"[SIMPLIFIED_TRACKER] ✅ 找到匹配的平倉訂單:")
                    print(f"[SIMPLIFIED_TRACKER]   訂單ID: {exit_order['order_id']}")
                    print(f"[SIMPLIFIED_TRACKER]   部位ID: {exit_order['position_id']}")
                    print(f"[SIMPLIFIED_TRACKER]   方向: {exit_order['direction']}")
                    print(f"[SIMPLIFIED_TRACKER]   註冊時間: {exit_order.get('register_time', 'N/A')}")

                # 更新平倉訂單狀態
                exit_order['status'] = 'FILLED'
                position_id = exit_order['position_id']

                if self.console_enabled:
                    print(f"[SIMPLIFIED_TRACKER] ✅ 平倉成交確認: 部位{position_id} "
                          f"{qty}口 @{price:.0f}")

                # 🔍 DEBUG: 觸發回調函數
                if self.console_enabled:
                    print(f"[SIMPLIFIED_TRACKER] 📞 觸發平倉成交回調...")

                # 觸發平倉成交回調
                self._trigger_exit_fill_callbacks(exit_order, price, qty)

                # 🔍 DEBUG: 清理訂單
                if self.console_enabled:
                    print(f"[SIMPLIFIED_TRACKER] 🧹 清理已完成的平倉訂單...")

                # 清理已完成的平倉訂單
                self._cleanup_completed_exit_order(exit_order['order_id'])

                # 🔍 DEBUG: 處理完成
                if self.console_enabled:
                    print(f"[SIMPLIFIED_TRACKER] ✅ 平倉成交處理完成")
                    print(f"[SIMPLIFIED_TRACKER]   部位{position_id} 已成功平倉")
                    print(f"[SIMPLIFIED_TRACKER] ═══════════════════════════════════════")

                return True

        except Exception as e:
            if self.console_enabled:
                print(f"[SIMPLIFIED_TRACKER] ❌ 處理平倉成交失敗: {e}")
                import traceback
                print(f"[SIMPLIFIED_TRACKER] 錯誤詳情: {traceback.format_exc()}")
            return False

    def _handle_exit_cancel_report(self, price: float, qty: int, product: str) -> bool:
        """
        處理平倉取消回報

        Args:
            price: 取消價格 (通常為0)
            qty: 取消數量 (通常為0)
            product: 商品代碼

        Returns:
            bool: 處理是否成功
        """
        try:
            with self.data_lock:
                # 🔍 DEBUG: 平倉取消回報處理 (重要事件，立即輸出)
                if self.console_enabled:
                    print(f"[SIMPLIFIED_TRACKER] 📤 收到平倉取消回報:")
                    print(f"[SIMPLIFIED_TRACKER]   價格: {price:.0f} 數量: {qty} 商品: {product}")
                    print(f"[SIMPLIFIED_TRACKER]   待匹配平倉訂單: {len(self.exit_orders)}個")

                # 找到匹配的平倉訂單
                exit_order = self._find_matching_exit_order(price, qty, product, for_cancel=True)
                if not exit_order:
                    if self.console_enabled:
                        print(f"[SIMPLIFIED_TRACKER] ⚠️ 找不到匹配的平倉取消訂單")
                        print(f"[SIMPLIFIED_TRACKER]   搜尋條件: 價格={price:.0f}, 數量={qty}, 商品={product}")
                        # 顯示現有的平倉訂單供調試
                        if len(self.exit_orders) > 0:
                            print(f"[SIMPLIFIED_TRACKER]   現有平倉訂單:")
                            for order_id, order in self.exit_orders.items():
                                print(f"[SIMPLIFIED_TRACKER]     訂單{order_id}: 價格={order['price']:.0f}, 數量={order['quantity']}, 商品={order['product']}")
                    return False

                position_id = exit_order['position_id']

                # 🔍 DEBUG: 找到匹配的取消訂單
                if self.console_enabled:
                    print(f"[SIMPLIFIED_TRACKER] ⚠️ 找到匹配的平倉取消訂單:")
                    print(f"[SIMPLIFIED_TRACKER]   訂單ID: {exit_order['order_id']}")
                    print(f"[SIMPLIFIED_TRACKER]   部位ID: {position_id}")
                    print(f"[SIMPLIFIED_TRACKER]   原始價格: {exit_order['price']:.0f}")
                    print(f"[SIMPLIFIED_TRACKER]   原始數量: {exit_order['quantity']}")
                    print(f"[SIMPLIFIED_TRACKER]   方向: {exit_order['direction']}")

                if self.console_enabled:
                    print(f"[SIMPLIFIED_TRACKER] ❌ 平倉取消確認: 部位{position_id}")

                # 🔍 DEBUG: 觸發追價回調
                if self.console_enabled:
                    print(f"[SIMPLIFIED_TRACKER] 🔄 觸發平倉追價回調...")
                    print(f"[SIMPLIFIED_TRACKER]   註冊的回調數量: {len(self.exit_retry_callbacks)}")

                # 觸發平倉追價
                self._trigger_exit_retry_callbacks(exit_order)

                # 🔍 DEBUG: 清理取消訂單
                if self.console_enabled:
                    print(f"[SIMPLIFIED_TRACKER] 🧹 清理取消的平倉訂單...")

                # 清理取消的平倉訂單
                self._cleanup_completed_exit_order(exit_order['order_id'])

                # 🔍 DEBUG: 取消處理完成
                if self.console_enabled:
                    print(f"[SIMPLIFIED_TRACKER] ✅ 平倉取消處理完成")
                    print(f"[SIMPLIFIED_TRACKER]   部位{position_id} 將進行追價重試")
                    print(f"[SIMPLIFIED_TRACKER] ═══════════════════════════════════════")

                return True

        except Exception as e:
            if self.console_enabled:
                print(f"[SIMPLIFIED_TRACKER] ❌ 處理平倉取消失敗: {e}")
                import traceback
                print(f"[SIMPLIFIED_TRACKER] 錯誤詳情: {traceback.format_exc()}")
            return False

    def _find_matching_exit_order(self, price: float, qty: int, product: str, for_cancel=False):
        """
        找到匹配的平倉訂單

        Args:
            price: 回報價格
            qty: 回報數量
            product: 商品代碼
            for_cancel: 是否為取消回報

        Returns:
            dict: 匹配的平倉訂單資訊，None表示無匹配
        """
        try:
            normalized_product = self._normalize_product_code(product)
            current_time = time.time()

            for order_id, exit_info in self.exit_orders.items():
                # 檢查商品匹配
                if self._normalize_product_code(exit_info['product']) != normalized_product:
                    continue

                # 檢查時間窗口（30秒內）
                if current_time - exit_info['submit_time'] > 30:
                    continue

                # 取消回報特殊處理
                if for_cancel:
                    return exit_info

                # 成交回報：檢查價格和數量
                if (exit_info['quantity'] == qty and
                    abs(exit_info['price'] - price) <= 10):  # ±10點容差
                    return exit_info

            return None

        except Exception as e:
            if self.console_enabled:
                print(f"[SIMPLIFIED_TRACKER] ❌ 查找平倉訂單失敗: {e}")
            return None

    def _trigger_exit_fill_callbacks(self, exit_order, price, qty):
        """觸發平倉成交回調"""
        try:
            for callback in self.exit_fill_callbacks:
                callback(exit_order, price, qty)
        except Exception as e:
            if self.console_enabled:
                print(f"[SIMPLIFIED_TRACKER] ❌ 觸發平倉成交回調失敗: {e}")

    def _trigger_exit_retry_callbacks(self, exit_order):
        """觸發平倉追價回調"""
        try:
            position_id = exit_order['position_id']

            for callback in self.exit_retry_callbacks:
                callback(position_id, exit_order)

            if self.console_enabled:
                print(f"[SIMPLIFIED_TRACKER] 🔄 觸發平倉追價: 部位{position_id}")

        except Exception as e:
            if self.console_enabled:
                print(f"[SIMPLIFIED_TRACKER] ❌ 觸發平倉追價失敗: {e}")

    def _cleanup_completed_exit_order(self, order_id):
        """清理已完成的平倉訂單"""
        try:
            if order_id in self.exit_orders:
                exit_info = self.exit_orders[order_id]
                position_id = exit_info['position_id']

                # 清理映射
                if position_id in self.exit_position_mapping:
                    del self.exit_position_mapping[position_id]

                # 清理訂單
                del self.exit_orders[order_id]

        except Exception as e:
            if self.console_enabled:
                print(f"[SIMPLIFIED_TRACKER] ❌ 清理平倉訂單失敗: {e}")
