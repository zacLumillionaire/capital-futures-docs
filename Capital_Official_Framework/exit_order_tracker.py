#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
平倉訂單追蹤器
完全參考建倉機制的一對一回報確認邏輯
"""

import time
import threading
import logging
from datetime import datetime
from typing import Dict, List, Optional, Callable
from dataclasses import dataclass
from enum import Enum

# 設定日誌
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class ExitOrderStatus(Enum):
    """平倉訂單狀態"""
    PENDING = "PENDING"        # 等待中
    SUBMITTED = "SUBMITTED"    # 已提交
    FILLED = "FILLED"          # 已成交
    CANCELLED = "CANCELLED"    # 已取消
    FAILED = "FAILED"          # 失敗
    RETRY = "RETRY"            # 重試中

@dataclass
class ExitOrderInfo:
    """平倉訂單信息"""
    order_id: str
    position_id: int
    direction: str           # BUY/SELL
    quantity: int
    price: float
    product: str
    submit_time: float
    status: ExitOrderStatus
    retry_count: int = 0
    max_retries: int = 5
    
    def can_retry(self) -> bool:
        """檢查是否可以重試"""
        return self.retry_count < self.max_retries
    
    def increment_retry(self):
        """增加重試次數"""
        self.retry_count += 1
        self.status = ExitOrderStatus.RETRY

@dataclass
class ExitFillReport:
    """平倉成交回報"""
    order_id: str
    position_id: int
    fill_price: float
    fill_quantity: int
    fill_time: str
    product: str

class ExitOrderTracker:
    """
    平倉訂單追蹤器 - 🔧 新增：參考建倉追蹤邏輯
    
    功能：
    1. 一對一平倉訂單追蹤
    2. 平倉成交回報確認
    3. 平倉失敗重試管理
    4. 異步狀態更新整合
    """
    
    def __init__(self, db_manager, console_enabled=True):
        self.db_manager = db_manager
        self.console_enabled = console_enabled
        self.logger = logging.getLogger(f"{__name__}.{self.__class__.__name__}")
        
        # 線程安全鎖
        self.data_lock = threading.RLock()
        
        # 平倉訂單追蹤 - 參考建倉結構
        self.exit_orders: Dict[str, ExitOrderInfo] = {}  # {order_id: exit_info}
        self.position_order_mapping: Dict[int, str] = {}  # {position_id: order_id}
        
        # 回調函數 - 參考建倉回調機制
        self.fill_callbacks: List[Callable] = []      # 成交回調
        self.cancel_callbacks: List[Callable] = []    # 取消回調
        self.retry_callbacks: List[Callable] = []     # 重試回調
        self.complete_callbacks: List[Callable] = []  # 完成回調
        
        # 異步更新器支援
        self.async_updater = None
        
        # 統計信息
        self.stats = {
            'total_exits': 0,
            'confirmed_exits': 0,
            'failed_exits': 0,
            'retry_exits': 0,
            'cancelled_exits': 0
        }
        
        if self.console_enabled:
            print("[EXIT_TRACKER] 平倉訂單追蹤器已初始化")
    
    def set_async_updater(self, async_updater):
        """
        設定異步更新器 - 🔧 新增：整合異步更新
        
        Args:
            async_updater: 異步更新器實例
        """
        self.async_updater = async_updater
        if self.console_enabled:
            print("[EXIT_TRACKER] 🚀 異步更新器已設定")
    
    def register_exit_order(self, position_id: int, order_id: str, direction: str,
                           quantity: int, price: float, product: str = "TM0000") -> bool:
        """
        註冊平倉訂單 - 🔧 新增：參考建倉註冊邏輯
        
        Args:
            position_id: 部位ID
            order_id: 訂單ID
            direction: 平倉方向 (BUY/SELL)
            quantity: 數量
            price: 價格
            product: 商品代號
            
        Returns:
            bool: 註冊是否成功
        """
        try:
            with self.data_lock:
                # 檢查是否已有該部位的平倉訂單
                if position_id in self.position_order_mapping:
                    existing_order_id = self.position_order_mapping[position_id]
                    if existing_order_id in self.exit_orders:
                        existing_status = self.exit_orders[existing_order_id].status
                        if existing_status in [ExitOrderStatus.PENDING, ExitOrderStatus.SUBMITTED]:
                            if self.console_enabled:
                                print(f"[EXIT_TRACKER] ⚠️ 部位{position_id}已有進行中的平倉訂單{existing_order_id}")
                            return False
                
                # 創建平倉訂單信息
                exit_info = ExitOrderInfo(
                    order_id=order_id,
                    position_id=position_id,
                    direction=direction,
                    quantity=quantity,
                    price=price,
                    product=product,
                    submit_time=time.time(),
                    status=ExitOrderStatus.SUBMITTED
                )
                
                # 註冊訂單
                self.exit_orders[order_id] = exit_info
                self.position_order_mapping[position_id] = order_id
                
                # 更新統計
                self.stats['total_exits'] += 1
                
                if self.console_enabled:
                    print(f"[EXIT_TRACKER] 📝 註冊平倉訂單: 部位{position_id} 訂單{order_id} "
                          f"{direction} {quantity}口 @{price:.0f}")
                
                return True
                
        except Exception as e:
            self.logger.error(f"註冊平倉訂單失敗: {e}")
            if self.console_enabled:
                print(f"[EXIT_TRACKER] ❌ 註冊平倉訂單失敗: {e}")
            return False
    
    def process_exit_fill_report(self, fill_report: ExitFillReport) -> bool:
        """
        處理平倉成交回報 - 🔧 新增：一對一確認機制
        
        Args:
            fill_report: 平倉成交回報
            
        Returns:
            bool: 處理是否成功
        """
        try:
            with self.data_lock:
                # 🎯 一對一匹配平倉訂單（參考建倉FIFO邏輯）
                exit_order = self._find_matching_exit_order_fifo(
                    fill_report.fill_price, 
                    fill_report.fill_quantity, 
                    fill_report.product
                )
                
                if not exit_order:
                    if self.console_enabled:
                        print(f"[EXIT_TRACKER] ⚠️ 找不到匹配的平倉訂單: "
                              f"{fill_report.product} {fill_report.fill_quantity}口 @{fill_report.fill_price:.0f}")
                    return False
                
                position_id = exit_order.position_id
                
                # 更新訂單狀態
                exit_order.status = ExitOrderStatus.FILLED
                
                if self.console_enabled:
                    print(f"[EXIT_TRACKER] ✅ 平倉成交確認: 部位{position_id} 訂單{exit_order.order_id} "
                          f"{fill_report.fill_quantity}口 @{fill_report.fill_price:.0f}")
                
                # 🚀 異步更新部位狀態（參考建倉機制）
                if self.async_updater:
                    self._update_position_exit_async(position_id, fill_report, exit_order)
                
                # 觸發成交回調
                self._trigger_fill_callbacks(exit_order, fill_report)
                
                # 更新統計
                self.stats['confirmed_exits'] += 1
                
                # 清理完成的訂單
                self._cleanup_completed_exit_order(exit_order.order_id)
                
                return True
                
        except Exception as e:
            self.logger.error(f"處理平倉成交回報失敗: {e}")
            if self.console_enabled:
                print(f"[EXIT_TRACKER] ❌ 處理平倉成交回報失敗: {e}")
            return False
    
    def _find_matching_exit_order_fifo(self, price: float, qty: int, product: str) -> Optional[ExitOrderInfo]:
        """
        FIFO匹配平倉訂單 - 🔧 新增：參考建倉FIFO邏輯
        
        Args:
            price: 成交價格
            qty: 成交數量
            product: 商品代號
            
        Returns:
            Optional[ExitOrderInfo]: 匹配的平倉訂單
        """
        try:
            current_time = time.time()
            normalized_product = self._normalize_product_code(product)
            candidates = []
            
            # 收集所有符合條件的候選訂單
            for order_id, exit_order in self.exit_orders.items():
                # 檢查狀態
                if exit_order.status not in [ExitOrderStatus.SUBMITTED, ExitOrderStatus.PENDING]:
                    continue
                
                # 檢查商品匹配
                if self._normalize_product_code(exit_order.product) != normalized_product:
                    continue
                
                # 檢查時間窗口（30秒內）
                if current_time - exit_order.submit_time > 30:
                    continue
                
                # 檢查數量匹配
                if exit_order.quantity != qty:
                    continue
                
                # 檢查價格匹配（±10點容差）
                if abs(exit_order.price - price) <= 10:
                    candidates.append((exit_order, exit_order.submit_time))
            
            # FIFO: 返回最早的訂單
            if candidates:
                return min(candidates, key=lambda x: x[1])[0]
            
            return None
            
        except Exception as e:
            if self.console_enabled:
                print(f"[EXIT_TRACKER] ❌ FIFO匹配失敗: {e}")
            return None
    
    def _normalize_product_code(self, product: str) -> str:
        """標準化商品代號"""
        if not product:
            return "TM0000"
        return product.upper().strip()
    
    def _update_position_exit_async(self, position_pk: int, fill_report: ExitFillReport, exit_order: ExitOrderInfo):
        """
        異步更新部位平倉狀態 - 🔧 新增：參考建倉異步更新

        Args:
            position_pk: 部位主鍵ID
            fill_report: 成交回報
            exit_order: 平倉訂單信息
        """
        try:
            # 計算損益（簡化版本）
            pnl = self._calculate_exit_pnl(exit_order, fill_report.fill_price)
            
            # 異步更新部位狀態
            self.async_updater.schedule_position_exit_update(
                position_id=position_pk,  # 保持與async_updater參數一致
                exit_price=fill_report.fill_price,
                exit_time=fill_report.fill_time,
                exit_reason='手動出場',  # 修復：使用符合資料庫約束的值
                order_id=exit_order.order_id,
                pnl=pnl
            )
            
            if self.console_enabled:
                print(f"[EXIT_TRACKER] 🚀 異步平倉更新已排程: 部位{position_pk} @{fill_report.fill_price:.0f}")
                
        except Exception as e:
            self.logger.error(f"異步更新部位平倉狀態失敗: {e}")
    
    def _calculate_exit_pnl(self, exit_order: ExitOrderInfo, fill_price: float) -> float:
        """
        計算平倉損益 - 🔧 新增：簡化損益計算
        
        Args:
            exit_order: 平倉訂單信息
            fill_price: 成交價格
            
        Returns:
            float: 損益點數
        """
        try:
            # 簡化計算：假設每點價值相同
            # 實際應該從資料庫獲取進場價格
            # 這裡先返回價格差異作為損益
            return fill_price - exit_order.price
            
        except Exception as e:
            self.logger.error(f"計算平倉損益失敗: {e}")
            return 0.0

    def _trigger_fill_callbacks(self, exit_order: ExitOrderInfo, fill_report: ExitFillReport):
        """
        觸發平倉成交回調 - 🔧 新增：參考建倉回調機制

        Args:
            exit_order: 平倉訂單信息
            fill_report: 成交回報
        """
        try:
            for callback in self.fill_callbacks:
                callback(exit_order, fill_report)

            if self.console_enabled:
                print(f"[EXIT_TRACKER] 📞 觸發平倉成交回調: 部位{exit_order.position_id}")

        except Exception as e:
            if self.console_enabled:
                print(f"[EXIT_TRACKER] ❌ 觸發平倉成交回調失敗: {e}")

    def _cleanup_completed_exit_order(self, order_id: str):
        """
        清理已完成的平倉訂單 - 🔧 新增：清理機制

        Args:
            order_id: 訂單ID
        """
        try:
            with self.data_lock:
                if order_id in self.exit_orders:
                    exit_order = self.exit_orders[order_id]
                    position_id = exit_order.position_id

                    # 清理映射
                    if position_id in self.position_order_mapping:
                        del self.position_order_mapping[position_id]

                    # 清理訂單（保留一段時間用於調試）
                    # 實際部署時可以立即刪除
                    # del self.exit_orders[order_id]

                    if self.console_enabled:
                        print(f"[EXIT_TRACKER] 🧹 清理平倉訂單: {order_id}")

        except Exception as e:
            if self.console_enabled:
                print(f"[EXIT_TRACKER] ❌ 清理平倉訂單失敗: {e}")

    def process_exit_cancel_report(self, order_id: str, reason: str = "CANCELLED") -> bool:
        """
        處理平倉取消回報 - 🔧 新增：取消處理

        Args:
            order_id: 訂單ID
            reason: 取消原因

        Returns:
            bool: 處理是否成功
        """
        try:
            with self.data_lock:
                if order_id not in self.exit_orders:
                    if self.console_enabled:
                        print(f"[EXIT_TRACKER] ⚠️ 找不到取消的平倉訂單: {order_id}")
                    return False

                exit_order = self.exit_orders[order_id]
                position_id = exit_order.position_id

                # 更新訂單狀態
                exit_order.status = ExitOrderStatus.CANCELLED

                if self.console_enabled:
                    print(f"[EXIT_TRACKER] ⚠️ 平倉訂單已取消: 部位{position_id} 訂單{order_id} 原因:{reason}")

                # 觸發取消回調
                self._trigger_cancel_callbacks(exit_order, reason)

                # 更新統計
                self.stats['cancelled_exits'] += 1

                # 檢查是否需要重試
                if exit_order.can_retry():
                    # 🔧 修改：傳遞更多信息給追價回調
                    self._trigger_retry_callbacks(exit_order, reason)
                    self.stats['retry_exits'] += 1
                else:
                    # 清理失敗的訂單
                    self._cleanup_completed_exit_order(order_id)
                    self.stats['failed_exits'] += 1

                return True

        except Exception as e:
            self.logger.error(f"處理平倉取消回報失敗: {e}")
            if self.console_enabled:
                print(f"[EXIT_TRACKER] ❌ 處理平倉取消回報失敗: {e}")
            return False

    def _trigger_cancel_callbacks(self, exit_order: ExitOrderInfo, reason: str):
        """觸發平倉取消回調"""
        try:
            for callback in self.cancel_callbacks:
                callback(exit_order, reason)
        except Exception as e:
            if self.console_enabled:
                print(f"[EXIT_TRACKER] ❌ 觸發平倉取消回調失敗: {e}")

    def _trigger_retry_callbacks(self, exit_order: ExitOrderInfo, reason: str = "CANCELLED"):
        """
        觸發平倉重試回調 - 🔧 修改：支援追價機制

        Args:
            exit_order: 平倉訂單信息
            reason: 取消原因
        """
        try:
            exit_order.increment_retry()

            # 檢查是否為FOK失敗（需要追價）
            should_retry = self._should_trigger_retry(reason)

            if should_retry:
                if self.console_enabled:
                    print(f"[EXIT_TRACKER] 🔄 觸發平倉追價: 部位{exit_order.position_id} "
                          f"第{exit_order.retry_count}次 原因:{reason}")

                for callback in self.retry_callbacks:
                    # 傳遞更多信息給回調
                    callback(exit_order, reason)
            else:
                if self.console_enabled:
                    print(f"[EXIT_TRACKER] ⚠️ 不觸發追價: 部位{exit_order.position_id} 原因:{reason}")

        except Exception as e:
            if self.console_enabled:
                print(f"[EXIT_TRACKER] ❌ 觸發平倉重試回調失敗: {e}")

    def _should_trigger_retry(self, reason: str) -> bool:
        """
        判斷是否應該觸發追價重試 - 🔧 新增：參考建倉重試邏輯

        Args:
            reason: 取消/失敗原因

        Returns:
            bool: 是否應該重試
        """
        # 參考建倉邏輯，檢查失敗原因是否適合重試
        retry_keywords = [
            "FOK",           # FOK失敗
            "無法成交",       # 無法成交
            "價格偏離",       # 價格偏離
            "委託失敗",       # 委託失敗
            "CANCELLED",     # 一般取消
            "TIMEOUT"        # 超時
        ]

        reason_upper = reason.upper()
        for keyword in retry_keywords:
            if keyword.upper() in reason_upper:
                return True

        return False

    def has_exit_order_for_position(self, position_id: int) -> bool:
        """
        檢查部位是否有平倉訂單 - 🔧 新增：狀態檢查

        Args:
            position_id: 部位ID

        Returns:
            bool: 是否有平倉訂單
        """
        try:
            with self.data_lock:
                if position_id in self.position_order_mapping:
                    order_id = self.position_order_mapping[position_id]
                    if order_id in self.exit_orders:
                        status = self.exit_orders[order_id].status
                        return status in [ExitOrderStatus.PENDING, ExitOrderStatus.SUBMITTED, ExitOrderStatus.RETRY]
                return False
        except Exception as e:
            return False

    def get_exit_order_status(self, position_id: int) -> str:
        """
        獲取部位的平倉訂單狀態 - 🔧 新增：狀態查詢

        Args:
            position_id: 部位ID

        Returns:
            str: 訂單狀態
        """
        try:
            with self.data_lock:
                if position_id in self.position_order_mapping:
                    order_id = self.position_order_mapping[position_id]
                    if order_id in self.exit_orders:
                        return self.exit_orders[order_id].status.value
                return 'NONE'
        except Exception as e:
            return 'ERROR'

    def get_exit_order_info(self, position_id: int) -> Optional[ExitOrderInfo]:
        """
        獲取部位的平倉訂單詳細信息 - 🔧 新增：詳細查詢

        Args:
            position_id: 部位ID

        Returns:
            Optional[ExitOrderInfo]: 訂單信息
        """
        try:
            with self.data_lock:
                if position_id in self.position_order_mapping:
                    order_id = self.position_order_mapping[position_id]
                    if order_id in self.exit_orders:
                        return self.exit_orders[order_id]
                return None
        except Exception as e:
            return None

    def add_fill_callback(self, callback: Callable):
        """添加平倉成交回調"""
        self.fill_callbacks.append(callback)

    def add_cancel_callback(self, callback: Callable):
        """添加平倉取消回調"""
        self.cancel_callbacks.append(callback)

    def add_retry_callback(self, callback: Callable):
        """添加平倉重試回調"""
        self.retry_callbacks.append(callback)

    def get_stats(self) -> Dict:
        """獲取統計信息"""
        return self.stats.copy()

    def cleanup_expired_orders(self, max_age_seconds: int = 300):
        """
        清理過期訂單 - 🔧 新增：維護機制

        Args:
            max_age_seconds: 最大保留時間（秒）
        """
        try:
            current_time = time.time()
            expired_orders = []

            with self.data_lock:
                for order_id, exit_order in self.exit_orders.items():
                    if current_time - exit_order.submit_time > max_age_seconds:
                        if exit_order.status in [ExitOrderStatus.FILLED, ExitOrderStatus.CANCELLED, ExitOrderStatus.FAILED]:
                            expired_orders.append(order_id)

                for order_id in expired_orders:
                    self._cleanup_completed_exit_order(order_id)
                    del self.exit_orders[order_id]

            if expired_orders and self.console_enabled:
                print(f"[EXIT_TRACKER] 🧹 清理{len(expired_orders)}個過期平倉訂單")

        except Exception as e:
            if self.console_enabled:
                print(f"[EXIT_TRACKER] ❌ 清理過期訂單失敗: {e}")

if __name__ == "__main__":
    # 測試用途
    print("平倉訂單追蹤器模組")
    print("請在主程式中使用 ExitOrderTracker 類")
