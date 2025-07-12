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
        
        # 統計數據
        self.total_groups = 0
        self.completed_groups = 0
        self.failed_groups = 0
        
        # 線程安全鎖 - 避免GIL問題
        self.data_lock = threading.Lock()
        
        # 回調函數
        self.fill_callbacks: List = []
        self.retry_callbacks: List = []
        
        if self.console_enabled:
            print("[SIMPLIFIED_TRACKER] 簡化追蹤器已初始化")
    
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
        處理訂單回報 - 簡化版本
        
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
            
            # 判斷方向 (簡化邏輯)
            direction = self._detect_direction(fields)
            
            if order_type == "D":  # 成交
                return self._handle_fill_report(price, qty, direction, product)
            elif order_type == "C":  # 取消
                return self._handle_cancel_report(price, qty, direction, product)
                
            return True
            
        except Exception as e:
            if self.console_enabled:
                print(f"[SIMPLIFIED_TRACKER] ❌ 處理回報失敗: {e}")
            return False
    
    def _detect_direction(self, fields: List[str]) -> str:
        """
        檢測交易方向
        基於群益API欄位判斷
        """
        try:
            # 根據群益API格式判斷方向
            # 這裡需要根據實際API格式調整
            if len(fields) > 40:
                bs_flag = fields[40] if len(fields) > 40 else ""
                if bs_flag == "B":
                    return "LONG"
                elif bs_flag == "S":
                    return "SHORT"
            
            # 備用判斷邏輯
            return "LONG"  # 預設為多頭
            
        except:
            return "LONG"
    
    def _find_matching_group(self, price: float, direction: str,
                           product: str) -> Optional[StrategyGroup]:
        """
        找到匹配的策略組 - 帶衝突檢測
        基於價格、方向、商品匹配
        """
        try:
            current_time = time.time()
            candidates = []

            # 收集所有符合條件的候選組
            for group in self.strategy_groups.values():
                # 檢查基本條件
                if (group.direction == direction and
                    group.product == product and
                    not group.is_complete()):

                    # 檢查時間窗口 (5分鐘內)
                    if current_time - group.submit_time <= 300:
                        # 檢查價格匹配
                        if group.can_match_price(price):
                            price_diff = abs(price - group.target_price)
                            candidates.append((group, price_diff))

            # 🔍 衝突檢測日誌
            if len(candidates) > 1:
                candidate_info = []
                for group, diff in candidates:
                    candidate_info.append(f"組{group.group_id}(目標{group.target_price:.0f}, 差距{diff:.1f}點)")

                if self.console_enabled:
                    print(f"[SIMPLIFIED_TRACKER] ⚠️ 價格匹配衝突檢測:")
                    print(f"    成交價格: {price}")
                    print(f"    方向商品: {direction} {product}")
                    print(f"    候選組: {', '.join(candidate_info)}")

                # 記錄到日誌
                self.logger.warning(f"多組匹配衝突: 價格{price} {direction} {product}, "
                                  f"候選組{[c[0].group_id for c in candidates]}")

            if not candidates:
                return None

            # 🎯 最近價格優先選擇
            best_group, min_diff = min(candidates, key=lambda x: x[1])

            if self.console_enabled and len(candidates) > 1:
                print(f"[SIMPLIFIED_TRACKER] 🎯 選擇最近價格組: 組{best_group.group_id} "
                      f"(差距{min_diff:.1f}點)")

            return best_group

        except Exception as e:
            if self.console_enabled:
                print(f"[SIMPLIFIED_TRACKER] ❌ 匹配策略組失敗: {e}")
            return None

    def _handle_fill_report(self, price: float, qty: int, direction: str,
                          product: str) -> bool:
        """
        處理成交回報

        Args:
            price: 成交價格
            qty: 成交數量
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
                        print(f"[SIMPLIFIED_TRACKER] ⚠️ 找不到匹配的策略組: "
                              f"{direction} {product} {qty}口 @{price}")
                    return False

                # 更新成交統計
                group.filled_lots += qty

                if self.console_enabled:
                    print(f"[SIMPLIFIED_TRACKER] ✅ 策略組{group.group_id}成交: "
                          f"{qty}口 @{price}, 總計: {group.filled_lots}/{group.total_lots}")

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
