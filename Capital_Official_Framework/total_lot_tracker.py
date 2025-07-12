# -*- coding: utf-8 -*-
"""
總量追蹤器
基於總口數統計的簡化追蹤機制，避免組間匹配問題
"""

import time
import threading
from datetime import datetime
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
from enum import Enum
import logging

class TrackerStatus(Enum):
    """追蹤器狀態"""
    PENDING = "PENDING"      # 等待中
    PARTIAL = "PARTIAL"      # 部分成交
    COMPLETED = "COMPLETED"  # 全部成交
    FAILED = "FAILED"        # 失敗

@dataclass
class FillRecord:
    """成交記錄"""
    price: float
    quantity: int
    timestamp: float
    lot_rule_id: int  # 對應的風險規則ID (1,2,3)
    group_display_id: int  # 顯示用組別ID
    position_in_group: int  # 組內位置

class TotalLotTracker:
    """
    總量追蹤器
    基於總口數統計，避免組間匹配複雜性
    """
    
    def __init__(self, strategy_id: str, total_target_lots: int, lots_per_group: int,
                 direction: str, product: str = "TM0000", console_enabled: bool = True):
        self.strategy_id = strategy_id
        self.total_target_lots = total_target_lots
        self.lots_per_group = lots_per_group
        self.direction = direction
        self.product = product
        self.console_enabled = console_enabled
        
        # 統計數據
        self.total_filled_lots = 0
        self.total_cancelled_lots = 0
        self.submitted_lots = 0
        
        # 成交記錄
        self.fill_records: List[FillRecord] = []
        
        # 追價控制
        self.retry_count = 0
        self.max_retries = 5
        self.price_tolerance = 5.0  # 價格容差
        
        # 時間控制
        self.start_time = time.time()
        self.last_retry_time = 0
        
        # 狀態控制
        self.is_retrying = False
        self.pending_retry_lots = 0
        
        # 線程安全
        self.data_lock = threading.Lock()
        
        # 回調函數
        self.fill_callbacks: List = []
        self.retry_callbacks: List = []
        self.complete_callbacks: List = []
        
        # 日誌
        self.logger = logging.getLogger(self.__class__.__name__)
        
        if self.console_enabled:
            print(f"[TOTAL_TRACKER] 總量追蹤器初始化: {strategy_id}")
            print(f"    目標: {direction} {product} {total_target_lots}口")
            print(f"    配置: {lots_per_group}口/組")
    
    @property
    def status(self) -> TrackerStatus:
        """獲取當前狀態"""
        if self.total_filled_lots >= self.total_target_lots:
            return TrackerStatus.COMPLETED
        elif self.total_filled_lots > 0:
            return TrackerStatus.PARTIAL
        elif self.retry_count >= self.max_retries:
            return TrackerStatus.FAILED
        else:
            return TrackerStatus.PENDING
    
    @property
    def remaining_lots(self) -> int:
        """剩餘需要成交的口數"""
        return max(0, self.total_target_lots - self.total_filled_lots)
    
    @property
    def completion_rate(self) -> float:
        """完成率"""
        if self.total_target_lots == 0:
            return 1.0
        return self.total_filled_lots / self.total_target_lots
    
    def update_submitted_lots(self, lots: int) -> bool:
        """更新已送出口數"""
        try:
            with self.data_lock:
                self.submitted_lots += lots
                
                # 重置追價狀態
                if self.is_retrying:
                    self.is_retrying = False
                    self.pending_retry_lots = 0
                
                if self.console_enabled:
                    print(f"[TOTAL_TRACKER] 📤 {self.strategy_id}送出: {lots}口, "
                          f"總計: {self.submitted_lots}/{self.total_target_lots}")
                
                return True
                
        except Exception as e:
            if self.console_enabled:
                print(f"[TOTAL_TRACKER] ❌ 更新送出口數失敗: {e}")
            return False
    
    def process_fill_report(self, price: float, qty: int) -> bool:
        """
        處理成交回報
        
        Args:
            price: 成交價格
            qty: 成交數量
            
        Returns:
            bool: 是否處理成功
        """
        try:
            with self.data_lock:
                # 檢查是否還需要成交
                if self.total_filled_lots >= self.total_target_lots:
                    if self.console_enabled:
                        print(f"[TOTAL_TRACKER] ⚠️ {self.strategy_id}已完成，忽略額外成交")
                    return True
                
                # 計算實際可接受的成交量
                actual_qty = min(qty, self.remaining_lots)
                
                # 更新統計
                old_filled = self.total_filled_lots
                self.total_filled_lots += actual_qty
                
                # 創建成交記錄
                for i in range(actual_qty):
                    position_index = old_filled + i
                    lot_rule_id = self._get_lot_rule_id(position_index)
                    group_display_id, position_in_group = self._get_display_position(position_index)
                    
                    fill_record = FillRecord(
                        price=price,
                        quantity=1,
                        timestamp=time.time(),
                        lot_rule_id=lot_rule_id,
                        group_display_id=group_display_id,
                        position_in_group=position_in_group
                    )
                    self.fill_records.append(fill_record)
                
                if self.console_enabled:
                    print(f"[TOTAL_TRACKER] ✅ {self.strategy_id}成交: {actual_qty}口 @{price}")
                    print(f"    進度: {self.total_filled_lots}/{self.total_target_lots} "
                          f"({self.completion_rate:.1%})")
                
                # 觸發成交回調
                self._trigger_fill_callbacks(price, actual_qty)
                
                # 檢查是否完成
                if self.is_complete():
                    if self.console_enabled:
                        print(f"[TOTAL_TRACKER] 🎉 {self.strategy_id}建倉完成!")
                    self._trigger_complete_callbacks()
                
                return True
                
        except Exception as e:
            if self.console_enabled:
                print(f"[TOTAL_TRACKER] ❌ 處理成交回報失敗: {e}")
            return False
    
    def process_cancel_report(self, price: float, qty: int) -> bool:
        """
        處理取消回報
        
        Args:
            price: 取消價格
            qty: 取消數量
            
        Returns:
            bool: 是否處理成功
        """
        try:
            with self.data_lock:
                # 更新取消統計
                self.total_cancelled_lots += qty
                
                if self.console_enabled:
                    print(f"[TOTAL_TRACKER] ❌ {self.strategy_id}取消: {qty}口 @{price}")
                
                # 檢查是否需要追價
                if self.needs_retry() and not self.is_retrying:
                    current_time = time.time()
                    
                    # 避免頻繁重試 (至少間隔1秒)
                    if current_time - self.last_retry_time >= 1.0:
                        remaining = self.remaining_lots
                        retry_lots = min(qty, remaining)
                        
                        if retry_lots > 0:
                            self.retry_count += 1
                            self.last_retry_time = current_time
                            self.is_retrying = True
                            self.pending_retry_lots = retry_lots
                            
                            if self.console_enabled:
                                print(f"[TOTAL_TRACKER] 🔄 {self.strategy_id}觸發追價: "
                                      f"第{self.retry_count}次, {retry_lots}口")
                            
                            # 觸發追價回調
                            self._trigger_retry_callbacks(retry_lots, price)
                
                return True
                
        except Exception as e:
            if self.console_enabled:
                print(f"[TOTAL_TRACKER] ❌ 處理取消回報失敗: {e}")
            return False
    
    def needs_retry(self) -> bool:
        """檢查是否需要追價"""
        return (self.remaining_lots > 0 and 
                self.retry_count < self.max_retries)
    
    def is_complete(self) -> bool:
        """檢查是否完成"""
        return self.total_filled_lots >= self.total_target_lots
    
    def _get_lot_rule_id(self, position_index: int) -> int:
        """獲取部位對應的風險規則ID"""
        return (position_index % self.lots_per_group) + 1
    
    def _get_display_position(self, position_index: int) -> Tuple[int, int]:
        """獲取顯示用的組別和組內位置"""
        group_id = (position_index // self.lots_per_group) + 1
        position_in_group = (position_index % self.lots_per_group) + 1
        return group_id, position_in_group
    
    def _trigger_fill_callbacks(self, price: float, qty: int):
        """觸發成交回調"""
        try:
            for callback in self.fill_callbacks:
                try:
                    callback(self.strategy_id, price, qty, self.total_filled_lots, self.total_target_lots)
                except Exception as e:
                    if self.console_enabled:
                        print(f"[TOTAL_TRACKER] ⚠️ 成交回調失敗: {e}")
        except Exception as e:
            if self.console_enabled:
                print(f"[TOTAL_TRACKER] ❌ 觸發成交回調失敗: {e}")
    
    def _trigger_retry_callbacks(self, qty: int, price: float):
        """觸發追價回調"""
        try:
            for callback in self.retry_callbacks:
                try:
                    callback(self.strategy_id, qty, price, self.retry_count)
                except Exception as e:
                    if self.console_enabled:
                        print(f"[TOTAL_TRACKER] ⚠️ 追價回調失敗: {e}")
        except Exception as e:
            if self.console_enabled:
                print(f"[TOTAL_TRACKER] ❌ 觸發追價回調失敗: {e}")
    
    def _trigger_complete_callbacks(self):
        """觸發完成回調"""
        try:
            for callback in self.complete_callbacks:
                try:
                    callback(self.strategy_id, self.fill_records)
                except Exception as e:
                    if self.console_enabled:
                        print(f"[TOTAL_TRACKER] ⚠️ 完成回調失敗: {e}")
        except Exception as e:
            if self.console_enabled:
                print(f"[TOTAL_TRACKER] ❌ 觸發完成回調失敗: {e}")
    
    def add_fill_callback(self, callback):
        """添加成交回調"""
        self.fill_callbacks.append(callback)
    
    def add_retry_callback(self, callback):
        """添加追價回調"""
        self.retry_callbacks.append(callback)
    
    def add_complete_callback(self, callback):
        """添加完成回調"""
        self.complete_callbacks.append(callback)
    
    def get_statistics(self) -> Dict:
        """獲取統計信息"""
        try:
            with self.data_lock:
                return {
                    'strategy_id': self.strategy_id,
                    'status': self.status.value,
                    'total_target_lots': self.total_target_lots,
                    'total_filled_lots': self.total_filled_lots,
                    'remaining_lots': self.remaining_lots,
                    'completion_rate': self.completion_rate,
                    'retry_count': self.retry_count,
                    'submitted_lots': self.submitted_lots,
                    'cancelled_lots': self.total_cancelled_lots,
                    'fill_records_count': len(self.fill_records)
                }
        except Exception as e:
            if self.console_enabled:
                print(f"[TOTAL_TRACKER] ❌ 獲取統計信息失敗: {e}")
            return {}
    
    def get_fill_records_for_database(self) -> List[Dict]:
        """獲取用於資料庫記錄的成交數據"""
        try:
            with self.data_lock:
                records = []
                for record in self.fill_records:
                    records.append({
                        'group_display_id': record.group_display_id,
                        'position_in_group': record.position_in_group,
                        'lot_rule_id': record.lot_rule_id,
                        'entry_price': record.price,
                        'entry_time': datetime.fromtimestamp(record.timestamp).strftime('%H:%M:%S'),
                        'direction': self.direction,
                        'product': self.product
                    })
                return records
        except Exception as e:
            if self.console_enabled:
                print(f"[TOTAL_TRACKER] ❌ 獲取資料庫記錄失敗: {e}")
            return []
