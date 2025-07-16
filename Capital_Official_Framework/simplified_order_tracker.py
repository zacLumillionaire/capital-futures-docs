# -*- coding: utf-8 -*-
"""
簡化訂單追蹤器
基於策略組統計的追蹤機制，避免群益API序號映射問題
"""

import time
import threading
from datetime import datetime
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass, field
from enum import Enum
import logging

# 🔧 全局追價狀態管理器
class GlobalRetryManager:
    """全局追價狀態管理器 - 防止重複觸發"""
    _instance = None
    _lock = threading.Lock()

    def __new__(cls):
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
                    cls._instance._initialized = False
        return cls._instance

    def __init__(self):
        if not self._initialized:
            self.retry_locks = {}  # {group_key: timestamp}
            self.retry_timeout = 0.1  # 🔧 修復：調整為0.1秒，允許更快的追價響應
            self._initialized = True

    def can_retry(self, group_key: str) -> bool:
        """檢查是否可以追價"""
        current_time = time.time()
        last_retry_time = self.retry_locks.get(group_key, 0)
        return current_time - last_retry_time >= self.retry_timeout

    def mark_retry(self, group_key: str) -> bool:
        """標記追價狀態"""
        if self.can_retry(group_key):
            self.retry_locks[group_key] = time.time()
            return True
        return False

    def mark_retry_with_lot(self, group_key: str, lot_index: int) -> bool:
        """
        標記口級別追價狀態 - 🔧 修復：支援口級別鎖定

        Args:
            group_key: 組鍵值
            lot_index: 口索引
        """
        lot_key = f"{group_key}_lot_{lot_index}"
        if self.can_retry(lot_key):
            self.retry_locks[lot_key] = time.time()
            return True
        return False

    def clear_retry(self, group_key: str):
        """清除追價狀態"""
        self.retry_locks.pop(group_key, None)

    def clear_retry_for_lot(self, group_key: str, lot_index: int):
        """清除口級別追價狀態"""
        lot_key = f"{group_key}_lot_{lot_index}"
        self.retry_locks.pop(lot_key, None)

# 🔧 修復：口級別平倉追價機制
@dataclass
class ExitGroup:
    """平倉組追蹤器 - 🔧 修復：支援口級別平倉追價機制"""
    position_id: int
    total_lots: int          # 需要平倉的總口數
    direction: str           # 原始部位方向 (LONG/SHORT)
    exit_direction: str      # 平倉方向 (SHORT/LONG)
    target_price: float      # 目標平倉價格
    product: str             # 商品代碼

    # 統計數據
    submitted_lots: int = 0   # 已送出平倉口數
    filled_lots: int = 0      # 已平倉口數
    cancelled_lots: int = 0   # 已取消口數

    # 🔧 修復：口級別平倉追價控制
    retry_count: int = 0      # 組級別追價次數（統計用）
    max_retries: int = 5      # 每口最大追價次數
    individual_retry_counts: dict = field(default_factory=dict)  # 每口的追價次數 {lot_index: retry_count}
    price_tolerance: float = 10.0  # 價格容差(點)

    # 🔧 新增：平倉追價行為控制開關
    enable_cancel_retry: bool = True    # 是否啟用取消追價（FOK失敗）
    enable_partial_retry: bool = False  # 是否啟用部分成交追價（口數不符）

    # 時間控制
    submit_time: float = 0    # 提交時間
    last_retry_time: float = 0  # 最後重試時間

    # 🔧 修復：口級別平倉追價狀態控制
    pending_retry_lots: int = 0  # 等待追價的口數
    is_retrying: bool = False    # 是否正在追價中
    active_retry_lots: set = field(default_factory=set)  # 正在追價的口索引

    @property
    def remaining_lots(self) -> int:
        """獲取剩餘需要平倉的口數"""
        return max(0, self.total_lots - self.filled_lots)

    def get_current_lot_index(self) -> int:
        """獲取當前處理的口索引（基於已取消口數）"""
        return self.cancelled_lots + 1

    def needs_retry_for_lot(self, lot_index: int) -> bool:
        """
        檢查特定口是否需要平倉追價 - 🔧 修復：口級別平倉追價檢查

        Args:
            lot_index: 口索引（1-based）
        """
        # 檢查基本條件
        if self.remaining_lots <= 0:
            return False

        # 檢查該口的追價次數
        individual_retries = self.individual_retry_counts.get(lot_index, 0)
        if individual_retries >= self.max_retries:
            return False

        # 檢查該口是否正在追價中
        if lot_index in self.active_retry_lots:
            return False

        # 檢查追價開關
        is_partial_fill = (self.filled_lots > 0)
        if is_partial_fill:
            return self.enable_partial_retry
        else:
            return self.enable_cancel_retry

    def increment_retry_for_lot(self, lot_index: int) -> int:
        """
        增加特定口的平倉追價次數 - 🔧 修復：口級別平倉追價計數

        Args:
            lot_index: 口索引（1-based）

        Returns:
            int: 該口的新追價次數
        """
        if lot_index not in self.individual_retry_counts:
            self.individual_retry_counts[lot_index] = 0

        self.individual_retry_counts[lot_index] += 1
        self.retry_count += 1  # 同時更新組級別計數用於統計
        self.active_retry_lots.add(lot_index)  # 標記為正在追價

        return self.individual_retry_counts[lot_index]

    def complete_retry_for_lot(self, lot_index: int):
        """完成特定口的平倉追價（無論成功或失敗）"""
        self.active_retry_lots.discard(lot_index)
        if len(self.active_retry_lots) == 0:
            self.is_retrying = False  # 所有口都完成追價時重置狀態

# 🔧 全局平倉狀態管理器
class GlobalExitManager:
    """全局平倉狀態管理器 - 防止重複平倉"""
    _instance = None
    _lock = threading.Lock()

    def __new__(cls):
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
                    cls._instance._initialized = False
        return cls._instance

    def __init__(self):
        if not self._initialized:
            # 🔧 任務2：強化鎖定資訊結構
            self.exit_locks = {}  # {position_id: {'timestamp': float, 'trigger_source': str, 'exit_type': str, 'reason': str, 'details': dict}}
            self.exit_timeout = 2.0  # 🔧 修復：調整為2.0秒，應對平倉查詢延遲，解決"找不到部位資訊"問題
            self.exit_lock = threading.RLock()  # 🔧 任務3修復：添加線程鎖確保原子性
            self._initialized = True

    def can_exit(self, position_id: str, trigger_source: str = "unknown") -> bool:
        """檢查是否可以平倉"""
        current_time = time.time()
        exit_info = self.exit_locks.get(position_id)

        if not exit_info:
            return True

        time_diff = current_time - exit_info['timestamp']
        if time_diff >= self.exit_timeout:
            # 超時，清除鎖定
            self.exit_locks.pop(position_id, None)
            return True

        return False

    def mark_exit(self, position_id: str, trigger_source: str = "unknown", exit_type: str = "stop_loss", reason: str = None, details: dict = None) -> bool:
        """
        標記平倉狀態 - 🔧 任務2：強化鎖定資訊，任務3：添加線程安全

        Args:
            position_id: 部位ID
            trigger_source: 觸發來源
            exit_type: 平倉類型
            reason: 鎖定原因（詳細描述）
            details: 額外詳細信息
        """
        with self.exit_lock:  # 🔧 任務3修復：確保原子性操作
            if self.can_exit(position_id, trigger_source):
                self.exit_locks[position_id] = {
                    'timestamp': time.time(),
                    'trigger_source': trigger_source,
                    'exit_type': exit_type,
                    'reason': reason or f"{exit_type}_triggered_by_{trigger_source}",
                    'details': details or {}
                }
                return True
            return False

    def mark_exit_with_lot(self, position_id: str, lot_index: int, trigger_source: str = "unknown", exit_type: str = "stop_loss") -> bool:
        """
        標記口級別平倉狀態 - 🔧 修復：支援口級別鎖定

        Args:
            position_id: 部位ID
            lot_index: 口索引
            trigger_source: 觸發來源
            exit_type: 平倉類型
        """
        lot_key = f"{position_id}_lot_{lot_index}"
        if self.can_exit_lot(position_id, lot_index):
            self.exit_locks[lot_key] = {
                'timestamp': time.time(),
                'trigger_source': trigger_source,
                'exit_type': exit_type
            }
            return True
        return False

    def can_exit_lot(self, position_id: str, lot_index: int) -> bool:
        """檢查特定口是否可以平倉"""
        lot_key = f"{position_id}_lot_{lot_index}"
        current_time = time.time()
        exit_info = self.exit_locks.get(lot_key)

        if not exit_info:
            return True

        time_diff = current_time - exit_info['timestamp']
        if time_diff >= self.exit_timeout:
            # 超時，清除鎖定
            self.exit_locks.pop(lot_key, None)
            return True

        return False

    def clear_exit(self, position_id: str):
        """清除平倉狀態 - 🔧 任務3修復：線程安全"""
        with self.exit_lock:
            self.exit_locks.pop(position_id, None)

    def clear_exit_for_lot(self, position_id: str, lot_index: int):
        """清除口級別平倉狀態"""
        lot_key = f"{position_id}_lot_{lot_index}"
        self.exit_locks.pop(lot_key, None)

    def check_exit_in_progress(self, position_id: str) -> Optional[str]:
        """
        檢查平倉是否正在進行中 - 🔧 任務2：返回鎖定原因，任務3：線程安全

        Args:
            position_id: 部位ID

        Returns:
            Optional[str]: 如果已鎖定，返回鎖定原因；如果未鎖定，返回 None
        """
        with self.exit_lock:  # 🔧 任務3修復：線程安全
            exit_info = self.exit_locks.get(position_id)
            if not exit_info:
                return None

            # 檢查是否過期
            current_time = time.time()
            if current_time - exit_info['timestamp'] >= self.exit_timeout:
                # 過期，清除並返回 None
                self.exit_locks.pop(position_id, None)
                return None

            # 返回詳細的鎖定原因
            return exit_info.get('reason', f"locked_by_{exit_info.get('trigger_source', 'unknown')}")

    def get_exit_info(self, position_id: str) -> dict:
        """獲取平倉狀態信息"""
        with self.exit_lock:  # 🔧 任務3修復：線程安全
            return self.exit_locks.get(position_id, {})

    def clear_all_exits(self):
        """清除所有平倉狀態 - 用於新交易週期開始時"""
        cleared_count = len(self.exit_locks)
        self.exit_locks.clear()
        return cleared_count

    def clear_all_locks(self):
        """
        任務3：清除所有歷史遺留的平倉鎖 - 系統啟動時的安全檢查

        Returns:
            int: 清除的鎖數量
        """
        cleared_count = len(self.exit_locks)
        self.exit_locks.clear()
        return cleared_count

    def clear_expired_exits(self, max_age_seconds: float = 300.0):
        """清除過期的平倉鎖定 - 防止鎖定狀態累積"""
        current_time = time.time()
        expired_keys = []

        for position_id, exit_info in self.exit_locks.items():
            if current_time - exit_info['timestamp'] > max_age_seconds:
                expired_keys.append(position_id)

        for key in expired_keys:
            self.exit_locks.pop(key, None)

        return len(expired_keys)

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
    """策略組追蹤器 - 🔧 修復：支援口級別追價機制"""
    group_id: int
    total_lots: int          # 預期下單口數
    direction: str           # LONG/SHORT
    target_price: float      # 目標價格
    product: str             # 商品代碼

    # 統計數據
    submitted_lots: int = 0   # 已送出口數
    filled_lots: int = 0      # 已成交口數
    cancelled_lots: int = 0   # 已取消口數

    # 🔧 修復：口級別追價控制
    retry_count: int = 0      # 組級別追價次數（統計用）
    max_retries: int = 5      # 每口最大追價次數
    individual_retry_counts: dict = field(default_factory=dict)  # 每口的追價次數 {lot_index: retry_count}
    price_tolerance: float = 10.0  # 價格容差(點) - 調整為10點以適應滑價

    # 🔧 新增：追價行為控制開關
    enable_cancel_retry: bool = True    # 是否啟用取消追價（FOK失敗）
    enable_partial_retry: bool = False  # 是否啟用部分成交追價（口數不符）

    # 時間控制
    submit_time: float = 0    # 提交時間
    last_retry_time: float = 0  # 最後重試時間

    # 🔧 修復：口級別追價狀態控制
    pending_retry_lots: int = 0  # 等待追價的口數
    is_retrying: bool = False    # 是否正在追價中
    active_retry_lots: set = field(default_factory=set)  # 正在追價的口索引
    
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

    @property
    def remaining_lots(self) -> int:
        """獲取剩餘需要成交的口數"""
        return max(0, self.total_lots - self.filled_lots)

    def get_current_lot_index(self) -> int:
        """獲取當前處理的口索引（基於已取消口數）"""
        return self.cancelled_lots + 1

    def needs_retry_for_lot(self, lot_index: int) -> bool:
        """
        檢查特定口是否需要追價 - 🔧 修復：口級別追價檢查

        Args:
            lot_index: 口索引（1-based）
        """
        # 檢查基本條件
        if self.remaining_lots <= 0:
            return False

        # 檢查該口的追價次數
        individual_retries = self.individual_retry_counts.get(lot_index, 0)
        if individual_retries >= self.max_retries:
            return False

        # 檢查該口是否正在追價中
        if lot_index in self.active_retry_lots:
            return False

        # 檢查追價開關
        is_partial_fill = (self.filled_lots > 0)
        if is_partial_fill:
            return self.enable_partial_retry
        else:
            return self.enable_cancel_retry

    def increment_retry_for_lot(self, lot_index: int) -> int:
        """
        增加特定口的追價次數 - 🔧 修復：口級別追價計數

        Args:
            lot_index: 口索引（1-based）

        Returns:
            int: 該口的新追價次數
        """
        if lot_index not in self.individual_retry_counts:
            self.individual_retry_counts[lot_index] = 0

        self.individual_retry_counts[lot_index] += 1
        self.retry_count += 1  # 同時更新組級別計數用於統計
        self.active_retry_lots.add(lot_index)  # 標記為正在追價

        return self.individual_retry_counts[lot_index]

    def complete_retry_for_lot(self, lot_index: int):
        """完成特定口的追價（無論成功或失敗）"""
        self.active_retry_lots.discard(lot_index)
        if len(self.active_retry_lots) == 0:
            self.is_retrying = False  # 所有口都完成追價時重置狀態

    def needs_retry(self, is_partial_fill: bool = False) -> bool:
        """
        檢查是否需要追價 - 🔧 修復：區分取消追價和部分成交追價

        Args:
            is_partial_fill: 是否為部分成交情況
        """
        remaining_lots = self.total_lots - self.filled_lots

        # 基本條件檢查
        if remaining_lots <= 0 or self.retry_count >= self.max_retries:
            return False

        # 🔧 新增：根據追價類型檢查開關
        if is_partial_fill:
            # 部分成交追價（口數不符）- 可能造成混亂，預設關閉
            return self.enable_partial_retry
        else:
            # 取消追價（FOK失敗）- 正常追價，預設開啟
            return self.enable_cancel_retry
    
    def can_match_price(self, price: float) -> bool:
        """檢查價格是否在容差範圍內 - 支援動態容差"""
        price_diff = abs(price - self.target_price)

        # 基本容差檢查
        if price_diff <= self.price_tolerance:
            return True

        # 🔧 動態容差：如果已有部分成交，放寬容差至15點
        # 這是為了處理市場滑價情況，避免部分成交後無法完成
        if self.filled_lots > 0 and price_diff <= 15.0:
            return True

        return False

    @property
    def remaining_lots(self) -> int:
        """獲取剩餘未成交口數"""
        return max(0, self.total_lots - self.filled_lots)

class SimplifiedOrderTracker:
    """
    簡化訂單追蹤器
    基於策略組統計，避免API序號映射問題
    """

    def __init__(self, console_enabled: bool = True):
        self.console_enabled = console_enabled

        # 🔧 全局追價管理器
        self.global_retry_manager = GlobalRetryManager()

        # 🔧 新增：全局追價狀態管理（防止重複觸發）
        self._global_retry_lock = {}  # {group_id: timestamp} 追價鎖定狀態
        self.logger = logging.getLogger(self.__class__.__name__)

        # 策略組追蹤 - 使用字典避免線程問題
        self.strategy_groups: Dict[int, StrategyGroup] = {}

        # 🔧 修復：平倉組追蹤 - 口級別平倉機制
        self.exit_groups: Dict[int, ExitGroup] = {}  # {position_id: ExitGroup}

        # 🔧 新增：平倉訂單追蹤
        self.exit_orders = {}  # {order_id: exit_order_info}
        self.exit_position_mapping = {}  # {position_id: order_id}

        # 🔧 修復：全局平倉管理器
        self.global_exit_manager = GlobalExitManager()

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

        # 🔧 新增：專門的平倉訂單追蹤器（參考建倉機制）
        self.exit_tracker = None  # 稍後設定

        # 🔧 新增：全局追價控制設定
        self.default_enable_cancel_retry = True    # 預設啟用取消追價（FOK失敗）
        self.default_enable_partial_retry = False  # 預設關閉部分成交追價（口數不符）

        if self.console_enabled:
            print("[SIMPLIFIED_TRACKER] 簡化追蹤器已初始化")
            print(f"[SIMPLIFIED_TRACKER] 🔧 追價設定: 取消追價={self.default_enable_cancel_retry}, 部分成交追價={self.default_enable_partial_retry}")

    def set_exit_tracker(self, exit_tracker):
        """
        設定專門的平倉訂單追蹤器 - 🔧 新增：整合平倉追蹤器

        Args:
            exit_tracker: 平倉訂單追蹤器實例
        """
        self.exit_tracker = exit_tracker
        if self.console_enabled:
            print("[SIMPLIFIED_TRACKER] 🔗 平倉訂單追蹤器已設定")

    def configure_retry_behavior(self, enable_cancel_retry: bool = True, enable_partial_retry: bool = False):
        """
        🔧 配置追價行為設定

        Args:
            enable_cancel_retry: 是否啟用取消追價（FOK失敗時）
            enable_partial_retry: 是否啟用部分成交追價（口數不符時）
        """
        self.default_enable_cancel_retry = enable_cancel_retry
        self.default_enable_partial_retry = enable_partial_retry

        # 更新所有現有策略組的設定
        with self.data_lock:
            for group in self.strategy_groups.values():
                group.enable_cancel_retry = enable_cancel_retry
                group.enable_partial_retry = enable_partial_retry

        if self.console_enabled:
            print(f"[SIMPLIFIED_TRACKER] 🔧 追價設定已更新:")
            print(f"[SIMPLIFIED_TRACKER]   取消追價: {enable_cancel_retry}")
            print(f"[SIMPLIFIED_TRACKER]   部分成交追價: {enable_partial_retry}")
            if not enable_partial_retry:
                print(f"[SIMPLIFIED_TRACKER] 💡 部分成交追價已關閉，避免口數不符造成的混亂")

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
                    product=product,
                    # 🔧 新增：使用全局預設追價設定
                    enable_cancel_retry=self.default_enable_cancel_retry,
                    enable_partial_retry=self.default_enable_partial_retry
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

    def register_exit_group(self, position_id: int, total_lots: int,
                           direction: str, exit_direction: str, target_price: float,
                           product: str = "TM0000") -> bool:
        """
        註冊平倉組 - 🔧 修復：口級別平倉追價機制

        Args:
            position_id: 部位ID
            total_lots: 需要平倉的總口數
            direction: 原始部位方向 (LONG/SHORT)
            exit_direction: 平倉方向 (SHORT/LONG)
            target_price: 目標平倉價格
            product: 商品代碼

        Returns:
            bool: 註冊是否成功
        """
        try:
            with self.data_lock:
                # 創建平倉組
                exit_group = ExitGroup(
                    position_id=position_id,
                    total_lots=total_lots,
                    direction=direction,
                    exit_direction=exit_direction,
                    target_price=target_price,
                    product=product,
                    # 🔧 新增：使用全局預設追價設定
                    enable_cancel_retry=self.default_enable_cancel_retry,
                    enable_partial_retry=self.default_enable_partial_retry
                )

                self.exit_groups[position_id] = exit_group

                if self.console_enabled:
                    print(f"[SIMPLIFIED_TRACKER] 📝 註冊平倉組: 部位{position_id} "
                          f"{direction}→{exit_direction} {product} {total_lots}口 @{target_price:.0f}")

                return True

        except Exception as e:
            if self.console_enabled:
                print(f"[SIMPLIFIED_TRACKER] ❌ 註冊平倉組失敗: {e}")
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
            buy_sell = fields[6] if len(fields) > 6 else ""    # 🔧 新增：買賣別/新平倉標識

            if self.console_enabled:
                print(f"[SIMPLIFIED_TRACKER] 🔍 FIFO處理回報: Type={order_type}, Product={product}, Price={price}, Qty={qty}, BuySell={buy_sell}")

            processed = False

            if order_type == "D":  # 成交
                # 🔧 修復：根據BuySell欄位正確識別平倉成交
                is_close_position = self._is_close_position_order(buy_sell)

                if is_close_position:
                    # 平倉成交：直接處理平倉成交
                    if self.console_enabled:
                        print(f"[SIMPLIFIED_TRACKER] 🎯 識別為平倉成交，BuySell={buy_sell}")
                    processed = self._handle_exit_fill_report(price, qty, product)
                    if processed:
                        if self.console_enabled:
                            print(f"[SIMPLIFIED_TRACKER] ✅ 平倉成交處理完成")
                        return True
                else:
                    # 新倉成交：處理進場成交
                    if self.console_enabled:
                        print(f"[SIMPLIFIED_TRACKER] 🏗️ 識別為新倉成交，BuySell={buy_sell}")
                    processed = self._handle_fill_report_fifo(price, qty, product)
                    if processed:
                        if self.console_enabled:
                            print(f"[SIMPLIFIED_TRACKER] ✅ 進場成交處理完成")
                        return True

                    # 🔧 修復：新倉成交處理失敗時，記錄警告但不轉交其他系統
                    # 避免與總量追蹤器產生重複處理和統計混亂
                    if self.console_enabled:
                        print(f"[SIMPLIFIED_TRACKER] ⚠️ 新倉成交處理失敗: {qty}口 @{price:.0f}")
                        print(f"[SIMPLIFIED_TRACKER] 📊 當前策略組狀態:")
                        for group_id, group_info in self.strategy_groups.items():
                            print(f"  組{group_id}: {group_info.filled_lots}/{group_info.total_lots}, 完成={group_info.is_complete()}, 目標價={group_info.target_price}")
                        print(f"[SIMPLIFIED_TRACKER] 💡 建議檢查價格容差設定或市場滑價情況")
                    return False  # 明確返回失敗，避免其他系統接手

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

    def _is_close_position_order(self, buy_sell: str) -> bool:
        """
        判斷是否為平倉單

        Args:
            buy_sell: BuySell欄位內容 (如 "SOF20")

        Returns:
            bool: True表示平倉單，False表示新倉單

        根據群益API文檔：
        BuySell欄位第2個子碼：
        - N: 新倉
        - O: 平倉  ← 我們要識別的
        - Y: 當沖
        - 7: 代沖銷
        """
        try:
            if not buy_sell:
                return False

            # 🔍 DEBUG: 顯示BuySell欄位分析
            if self.console_enabled:
                print(f"[SIMPLIFIED_TRACKER] 🔍 分析BuySell欄位: '{buy_sell}'")

            # 檢查是否包含平倉標識 "O"
            # 根據文檔，第2個子碼為 "O" 表示平倉
            if len(buy_sell) >= 2:
                second_char = buy_sell[1]  # 第2個子碼
                is_close = (second_char == 'O')

                if self.console_enabled:
                    print(f"[SIMPLIFIED_TRACKER]   第2個子碼: '{second_char}' -> {'平倉' if is_close else '非平倉'}")

                return is_close

            # 容錯：如果格式不符預期，檢查是否包含 "O"
            contains_o = 'O' in buy_sell
            if self.console_enabled:
                print(f"[SIMPLIFIED_TRACKER]   容錯檢查: 包含'O' -> {contains_o}")

            return contains_o

        except Exception as e:
            if self.console_enabled:
                print(f"[SIMPLIFIED_TRACKER] ❌ 分析BuySell欄位失敗: {e}")
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
                if self.console_enabled:
                    print(f"[SIMPLIFIED_TRACKER] 🔍 開始處理成交回報: {qty}口 @{price:.0f}")

                # 使用純FIFO匹配找到策略組
                group = self._find_matching_group_fifo(price, qty, product)
                if not group:
                    if self.console_enabled:
                        print(f"[SIMPLIFIED_TRACKER] ⚠️ FIFO找不到匹配的策略組: "
                              f"{qty}口 @{price:.0f}")
                        # 輸出當前所有策略組狀態
                        print(f"[SIMPLIFIED_TRACKER] 📊 當前策略組狀態:")
                        for group_id, group_info in self.strategy_groups.items():
                            print(f"  組{group_id}: {group_info.filled_lots}/{group_info.total_lots}, 完成={group_info.is_complete()}, 目標價={group_info.target_price}")
                    return False

                # 記錄更新前狀態
                old_filled = group.filled_lots

                # 更新成交統計
                group.filled_lots += qty

                if self.console_enabled:
                    print(f"[SIMPLIFIED_TRACKER] ✅ 策略組{group.group_id}成交: "
                          f"{qty}口 @{price:.0f}, 更新: {old_filled} -> {group.filled_lots}/{group.total_lots}")

                # 🔧 修復：每次成交都觸發回調，不只是完成時
                if self.console_enabled:
                    print(f"[SIMPLIFIED_TRACKER] 🔄 觸發成交回調: 組{group.group_id}")
                self._trigger_fill_callbacks(group, price, qty)

                # 檢查是否完成
                if group.is_complete():
                    self.completed_groups += 1
                    if self.console_enabled:
                        print(f"[SIMPLIFIED_TRACKER] 🎉 策略組{group.group_id}建倉完成!")

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

                # 🔧 修復：計算當前取消的口索引
                current_lot_index = group.get_current_lot_index()
                cancel_qty = 1  # 取消回報通常數量為0，我們假設取消1口
                group.cancelled_lots += cancel_qty

                if self.console_enabled:
                    print(f"[SIMPLIFIED_TRACKER] ❌ 策略組{group.group_id}第{current_lot_index}口取消: "
                          f"{cancel_qty}口 (原回報: {qty}口 @{price})")
                    print(f"[SIMPLIFIED_TRACKER] 📊 組{group.group_id}狀態: "
                          f"總{group.total_lots}口, 成交{group.filled_lots}口, 取消{group.cancelled_lots}口")

                # 🔧 修復：添加追價觸發邏輯（使用全局管理器防重複）
                # 🔧 新增：區分取消追價和部分成交追價
                is_partial_fill = (group.filled_lots > 0)  # 已有部分成交

                # 🔧 修復：計算是否為部分成交
                is_partial_fill = (group.filled_lots > 0)  # 已有部分成交

                # 🔧 修復：使用口級別的追價檢查日誌
                if self.console_enabled:
                    remaining_lots = group.remaining_lots
                    individual_retries = group.individual_retry_counts.get(current_lot_index, 0)
                    print(f"[DEBUG] 組{group.group_id}第{current_lot_index}口追價檢查:")
                    print(f"  - 剩餘口數: {remaining_lots}")
                    print(f"  - 該口追價次數: {individual_retries}")
                    print(f"  - 最大追價次數: {group.max_retries}")
                    print(f"  - 該口是否在追價: {current_lot_index in group.active_retry_lots}")
                    print(f"  - 該口needs_retry結果: {group.needs_retry_for_lot(current_lot_index)}")
                    print(f"  - 是否部分成交: {is_partial_fill}")

                # 🔧 修復：使用口級別的追價檢查
                if group.needs_retry_for_lot(current_lot_index):
                    # 🔧 修復：使用口級別的全局追價管理器
                    group_key = f"group_{group.group_id}_{group.product}"

                    if self.global_retry_manager.mark_retry_with_lot(group_key, current_lot_index):
                        retry_lots = 1  # 每次只追價1口
                        if retry_lots > 0:
                            # 🔧 修復：使用口級別的追價計數
                            individual_retry_count = group.increment_retry_for_lot(current_lot_index)
                            group.is_retrying = True

                            retry_type = "部分成交追價" if is_partial_fill else "取消追價"
                            if self.console_enabled:
                                print(f"[SIMPLIFIED_TRACKER] 🔄 策略組{group.group_id}第{current_lot_index}口觸發{retry_type}: "
                                      f"第{individual_retry_count}次, {retry_lots}口 (口級別鎖定)")

                            # 觸發追價回調
                            self._trigger_retry_callbacks(group, retry_lots, price)
                    else:
                        if self.console_enabled:
                            print(f"[SIMPLIFIED_TRACKER] 🔒 策略組{group.group_id}第{current_lot_index}口追價被全局管理器阻止 (防重複)")
                            print(f"[SIMPLIFIED_TRACKER] 💡 如果追價訂單被取消，將在下次取消回報時重新嘗試")
                else:
                    if self.console_enabled:
                        if current_lot_index in group.active_retry_lots:
                            print(f"[SIMPLIFIED_TRACKER] ⚠️ 策略組{group.group_id}第{current_lot_index}口已在追價中，跳過")
                            # 🔧 修復：口級別的鎖定清除邏輯
                            individual_retries = group.individual_retry_counts.get(current_lot_index, 0)
                            if cancel_qty > 0 and individual_retries < group.max_retries:
                                group_key = f"group_{group.group_id}_{group.product}"
                                # 檢查該口的時間間隔
                                lot_key = f"{group_key}_lot_{current_lot_index}"
                                if self.global_retry_manager.can_retry(lot_key):
                                    self.global_retry_manager.clear_retry_for_lot(group_key, current_lot_index)
                                    group.complete_retry_for_lot(current_lot_index)
                                    if self.console_enabled:
                                        print(f"[SIMPLIFIED_TRACKER] 🔓 清除組{group.group_id}第{current_lot_index}口鎖定，允許繼續追價")
                                else:
                                    if self.console_enabled:
                                        print(f"[SIMPLIFIED_TRACKER] ⏰ 組{group.group_id}第{current_lot_index}口追價間隔未到，保持鎖定狀態")
                        elif not group.needs_retry_for_lot(current_lot_index):
                            individual_retries = group.individual_retry_counts.get(current_lot_index, 0)
                            if individual_retries >= group.max_retries:
                                reason = f"第{current_lot_index}口已達追價上限({individual_retries}/{group.max_retries})"
                            elif group.remaining_lots <= 0:
                                reason = "無剩餘口數需要追價"
                            else:
                                reason = "追價開關已關閉"
                            print(f"[SIMPLIFIED_TRACKER] ℹ️ 策略組{group.group_id}第{current_lot_index}口不需要追價: {reason}")

                if self.console_enabled:
                    print(f"[SIMPLIFIED_TRACKER] ✅ 進場取消處理完成")

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
            candidates = []

            if self.console_enabled:
                print(f"[SIMPLIFIED_TRACKER] 🔍 FIFO匹配調試: 價格={price}, 數量={qty}, 商品={product}")
                print(f"[SIMPLIFIED_TRACKER] 📊 當前策略組數量: {len(self.strategy_groups)}")

            # 收集所有符合條件的候選組
            for group_id, group in self.strategy_groups.items():
                if self.console_enabled:
                    print(f"[SIMPLIFIED_TRACKER] 🔍 檢查組{group_id}:")
                    print(f"  - 目標價格: {group.target_price}")
                    print(f"  - 成交進度: {group.filled_lots}/{group.total_lots}")
                    print(f"  - 完成狀態: {group.is_complete()}")
                    print(f"  - 時間差: {current_time - group.submit_time:.1f}秒")
                    print(f"  - 價格差: {abs(price - group.target_price):.1f}點")

                # 🔧 移除商品匹配檢查（策略不會同時跑不同商品）

                # 檢查完成狀態
                if group.is_complete():
                    if self.console_enabled:
                        print(f"  ❌ 組{group_id}已完成，跳過")
                    continue

                # 檢查時間窗口 (30秒內)
                if current_time - group.submit_time > 30:
                    if self.console_enabled:
                        print(f"  ❌ 組{group_id}超時，跳過")
                    continue

                # 檢查數量匹配（簡化追蹤器可能不需要嚴格匹配數量）
                # 這裡我們放寬條件，只要組還需要成交就可以匹配
                if group.filled_lots >= group.total_lots:
                    if self.console_enabled:
                        print(f"  ❌ 組{group_id}已滿額，跳過")
                    continue

                # 檢查價格匹配 (±5點容差)
                if abs(price - group.target_price) <= group.price_tolerance:
                    candidates.append((group, group.submit_time))
                    if self.console_enabled:
                        print(f"  ✅ 組{group_id}符合條件，加入候選")
                else:
                    if self.console_enabled:
                        print(f"  ❌ 組{group_id}價格不匹配，跳過")

            # FIFO: 返回最早的策略組
            if candidates:
                best_group = min(candidates, key=lambda x: x[1])[0]
                if self.console_enabled:
                    print(f"[SIMPLIFIED_TRACKER] ✅ FIFO選中組{best_group.group_id}")
                return best_group
            else:
                if self.console_enabled:
                    print(f"[SIMPLIFIED_TRACKER] ❌ 沒有符合條件的候選組")
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

                # 🔧 修復：每次成交都觸發回調，不只是完成時
                self._trigger_fill_callbacks(group, price, qty)

                # 檢查是否完成
                if group.is_complete():
                    self.completed_groups += 1
                    if self.console_enabled:
                        print(f"[SIMPLIFIED_TRACKER] 🎉 策略組{group.group_id}建倉完成!")

                return True

        except Exception as e:
            if self.console_enabled:
                print(f"[SIMPLIFIED_TRACKER] ❌ 處理成交回報失敗: {e}")
            return False

    def _handle_cancel_report(self, price: float, qty: int, direction: str,
                            product: str) -> bool:
        """
        處理取消回報 - 舊版本，已棄用
        🔧 修復：重定向到FIFO版本，避免重複觸發追價

        Args:
            price: 取消價格
            qty: 取消數量
            direction: 交易方向
            product: 商品代碼

        Returns:
            bool: 處理是否成功
        """
        try:
            if self.console_enabled:
                print(f"[SIMPLIFIED_TRACKER] 🔄 舊版取消處理重定向到FIFO版本")

            # 🔧 重定向到FIFO版本，避免重複邏輯
            return self._handle_cancel_report_fifo(price, qty, product)

        except Exception as e:
            if self.console_enabled:
                print(f"[SIMPLIFIED_TRACKER] ❌ 舊版取消處理重定向失敗: {e}")
            return False

    def _trigger_fill_callbacks(self, group: StrategyGroup, price: float, qty: int):
        """觸發成交回調 - 避免GIL問題"""
        try:
            if self.console_enabled:
                print(f"[SIMPLIFIED_TRACKER] 🔄 觸發回調: 組{group.group_id}, 回調數量={len(self.fill_callbacks)}")

            # 直接調用回調，不使用線程
            for i, callback in enumerate(self.fill_callbacks):
                try:
                    if self.console_enabled:
                        print(f"[SIMPLIFIED_TRACKER] 📞 執行回調{i+1}: 組{group.group_id}, 價格={price}, 數量={qty}")
                    callback(group.group_id, price, qty, group.filled_lots, group.total_lots)
                    if self.console_enabled:
                        print(f"[SIMPLIFIED_TRACKER] ✅ 回調{i+1}執行完成")
                except Exception as e:
                    if self.console_enabled:
                        print(f"[SIMPLIFIED_TRACKER] ⚠️ 成交回調{i+1}失敗: {e}")
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
        # 🔧 防止重複註冊
        if callback not in self.fill_callbacks:
            self.fill_callbacks.append(callback)
            if self.console_enabled:
                print(f"[SIMPLIFIED_TRACKER] 📝 註冊成交回調: 總數={len(self.fill_callbacks)}")
        else:
            if self.console_enabled:
                print(f"[SIMPLIFIED_TRACKER] ⚠️ 回調已存在，跳過重複註冊")

    def add_retry_callback(self, callback):
        """添加追價回調"""
        # 🔧 防止重複註冊
        if callback not in self.retry_callbacks:
            self.retry_callbacks.append(callback)
            if self.console_enabled:
                print(f"[SIMPLIFIED_TRACKER] 📝 註冊追價回調: 總數={len(self.retry_callbacks)}")
        else:
            if self.console_enabled:
                print(f"[SIMPLIFIED_TRACKER] ⚠️ 追價回調已存在，跳過重複註冊")

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

                # 🔧 優先使用專門的平倉追蹤器（參考建倉機制）
                if self.exit_tracker:
                    # 使用新的平倉追蹤器處理
                    from exit_order_tracker import ExitFillReport
                    fill_report = ExitFillReport(
                        order_id="",  # 將在匹配時確定
                        position_id=0,  # 將在匹配時確定
                        fill_price=price,
                        fill_quantity=qty,
                        fill_time=datetime.now().strftime('%H:%M:%S'),
                        product=product
                    )

                    processed = self.exit_tracker.process_exit_fill_report(fill_report)
                    if processed:
                        if self.console_enabled:
                            print(f"[SIMPLIFIED_TRACKER] ✅ 新追蹤器處理平倉成交完成")
                        return True

                # 🛡️ 備份：使用原有邏輯
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

                # 🔧 優先使用專門的平倉追蹤器處理取消（參考建倉機制）
                if self.exit_tracker and hasattr(self.exit_tracker, 'process_exit_cancel_report'):
                    # 嘗試用專門追蹤器處理
                    processed = self.exit_tracker.process_exit_cancel_report("", "FOK_CANCELLED")
                    if processed:
                        if self.console_enabled:
                            print(f"[SIMPLIFIED_TRACKER] ✅ 專門追蹤器處理平倉取消完成")
                        return True

                # 🛡️ 備份：使用原有邏輯
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

                # 🔧 修復：使用口級別平倉追價機制
                exit_group = self.exit_groups.get(position_id)
                if exit_group:
                    # 🔧 修復：計算當前取消的口索引
                    current_lot_index = exit_group.get_current_lot_index()
                    cancel_qty = 1  # 平倉取消通常是1口
                    exit_group.cancelled_lots += cancel_qty

                    if self.console_enabled:
                        print(f"[SIMPLIFIED_TRACKER] ❌ 平倉組{position_id}第{current_lot_index}口取消: "
                              f"{cancel_qty}口 (原回報: {qty}口 @{price})")

                    # 🔧 修復：使用口級別的平倉追價檢查
                    if exit_group.needs_retry_for_lot(current_lot_index):
                        # 🔧 修復：使用口級別的全局平倉管理器
                        if self.global_exit_manager.mark_exit_with_lot(str(position_id), current_lot_index, "exit_cancel_retry", "cancel_retry"):
                            # 🔧 修復：使用口級別的平倉追價計數
                            individual_retry_count = exit_group.increment_retry_for_lot(current_lot_index)
                            exit_group.is_retrying = True

                            if self.console_enabled:
                                print(f"[SIMPLIFIED_TRACKER] 🔄 平倉組{position_id}第{current_lot_index}口觸發追價: "
                                      f"第{individual_retry_count}次, {cancel_qty}口 (口級別鎖定)")

                            # 觸發平倉追價回調
                            self._trigger_exit_retry_callbacks(exit_order)
                        else:
                            if self.console_enabled:
                                print(f"[SIMPLIFIED_TRACKER] 🔒 平倉組{position_id}第{current_lot_index}口追價被全局管理器阻止")
                    else:
                        individual_retries = exit_group.individual_retry_counts.get(current_lot_index, 0)
                        if individual_retries >= exit_group.max_retries:
                            reason = f"第{current_lot_index}口已達平倉追價上限({individual_retries}/{exit_group.max_retries})"
                        elif exit_group.remaining_lots <= 0:
                            reason = "無剩餘口數需要平倉"
                        else:
                            reason = "平倉追價開關已關閉"
                        if self.console_enabled:
                            print(f"[SIMPLIFIED_TRACKER] ℹ️ 平倉組{position_id}第{current_lot_index}口不需要追價: {reason}")
                else:
                    # 🛡️ 備份：使用原有的平倉追價邏輯
                    if self.console_enabled:
                        print(f"[SIMPLIFIED_TRACKER] ❌ 平倉取消確認: 部位{position_id}")
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
        """觸發平倉追價回調 - 🔧 修復：傳遞正確的參數"""
        try:
            position_id = exit_order['position_id']

            for callback in self.exit_retry_callbacks:
                # 🔧 修復：從 exit_group 獲取正確的重試次數
                exit_group = self.exit_groups.get(position_id)
                if exit_group:
                    current_lot_index = exit_group.get_current_lot_index()
                    # 確保 individual_retry_counts 是一個字典
                    if isinstance(exit_group.individual_retry_counts, dict):
                        retry_count = exit_group.individual_retry_counts.get(current_lot_index, 0)
                    else:
                        # 如果不是字典（例如舊數據），提供一個備用值
                        retry_count = 1
                else:
                    retry_count = 1  # 備用值

                callback(exit_order, retry_count)  # ✅ 正確：傳遞 (exit_order, retry_count)

            if self.console_enabled:
                print(f"[SIMPLIFIED_TRACKER] 🔄 觸發平倉追價: 部位{position_id} 重試次數{retry_count}")

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

    def has_exit_order_for_position(self, position_id: int) -> bool:
        """
        檢查部位是否有平倉訂單 - 🔧 新增：支援重複平倉防護

        Args:
            position_id: 部位ID

        Returns:
            bool: 是否有平倉訂單
        """
        try:
            with self.data_lock:
                # 檢查平倉訂單映射
                if position_id in self.exit_position_mapping:
                    order_id = self.exit_position_mapping[position_id]
                    if order_id in self.exit_orders:
                        order_status = self.exit_orders[order_id]['status']
                        # 只有PENDING和SUBMITTED狀態才算有進行中的平倉訂單
                        return order_status in ['PENDING', 'SUBMITTED']

                return False

        except Exception as e:
            if self.console_enabled:
                print(f"[SIMPLIFIED_TRACKER] ❌ 檢查平倉訂單失敗: {e}")
            return False

    def get_exit_order_status(self, position_id: int) -> str:
        """
        獲取部位的平倉訂單狀態 - 🔧 新增：狀態查詢

        Args:
            position_id: 部位ID

        Returns:
            str: 訂單狀態 ('NONE', 'PENDING', 'SUBMITTED', 'FILLED', 'CANCELLED', 'ERROR')
        """
        try:
            with self.data_lock:
                if position_id in self.exit_position_mapping:
                    order_id = self.exit_position_mapping[position_id]
                    if order_id in self.exit_orders:
                        return self.exit_orders[order_id]['status']

                return 'NONE'

        except Exception as e:
            if self.console_enabled:
                print(f"[SIMPLIFIED_TRACKER] ❌ 獲取平倉訂單狀態失敗: {e}")
            return 'ERROR'

    def get_exit_order_info(self, position_id: int) -> Optional[Dict]:
        """
        獲取部位的平倉訂單詳細信息 - 🔧 新增：詳細信息查詢

        Args:
            position_id: 部位ID

        Returns:
            Optional[Dict]: 訂單信息或None
        """
        try:
            with self.data_lock:
                if position_id in self.exit_position_mapping:
                    order_id = self.exit_position_mapping[position_id]
                    if order_id in self.exit_orders:
                        return self.exit_orders[order_id].copy()

                return None

        except Exception as e:
            if self.console_enabled:
                print(f"[SIMPLIFIED_TRACKER] ❌ 獲取平倉訂單信息失敗: {e}")
            return None
