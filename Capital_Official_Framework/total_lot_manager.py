# -*- coding: utf-8 -*-
"""
總量追蹤管理器
管理多個總量追蹤器，處理回報分發
"""

import time
import threading
from typing import Dict, List, Optional
from datetime import datetime
import logging

from total_lot_tracker import TotalLotTracker, TrackerStatus

class TotalLotManager:
    """
    總量追蹤管理器
    統一管理所有活躍的總量追蹤器
    """
    
    def __init__(self, console_enabled: bool = True):
        self.console_enabled = console_enabled
        self.logger = logging.getLogger(self.__class__.__name__)
        
        # 追蹤器管理
        self.active_trackers: Dict[str, TotalLotTracker] = {}
        
        # 統計數據
        self.total_strategies = 0
        self.completed_strategies = 0
        self.failed_strategies = 0
        
        # 線程安全
        self.data_lock = threading.Lock()
        
        # 全局回調
        self.global_fill_callbacks: List = []
        self.global_retry_callbacks: List = []
        self.global_complete_callbacks: List = []
        
        if self.console_enabled:
            print("[TOTAL_MANAGER] 總量追蹤管理器已初始化")
    
    def create_strategy_tracker(self, strategy_id: str, total_target_lots: int, 
                              lots_per_group: int, direction: str, 
                              product: str = "TM0000") -> bool:
        """
        創建策略追蹤器
        
        Args:
            strategy_id: 策略ID (唯一標識)
            total_target_lots: 總目標口數
            lots_per_group: 每組口數
            direction: 方向 (LONG/SHORT)
            product: 商品代碼
            
        Returns:
            bool: 創建是否成功
        """
        try:
            with self.data_lock:
                if strategy_id in self.active_trackers:
                    if self.console_enabled:
                        print(f"[TOTAL_MANAGER] ⚠️ 策略{strategy_id}已存在")
                    return False
                
                # 創建追蹤器
                tracker = TotalLotTracker(
                    strategy_id=strategy_id,
                    total_target_lots=total_target_lots,
                    lots_per_group=lots_per_group,
                    direction=direction,
                    product=product,
                    console_enabled=self.console_enabled
                )
                
                # 設置回調
                tracker.add_fill_callback(self._on_strategy_fill)
                tracker.add_retry_callback(self._on_strategy_retry)
                tracker.add_complete_callback(self._on_strategy_complete)
                
                # 註冊追蹤器
                self.active_trackers[strategy_id] = tracker
                self.total_strategies += 1
                
                if self.console_enabled:
                    print(f"[TOTAL_MANAGER] 📝 創建策略追蹤器: {strategy_id}")
                    print(f"    目標: {direction} {product} {total_target_lots}口 ({lots_per_group}口/組)")
                
                return True
                
        except Exception as e:
            if self.console_enabled:
                print(f"[TOTAL_MANAGER] ❌ 創建策略追蹤器失敗: {e}")
            return False
    
    def update_strategy_submitted_lots(self, strategy_id: str, lots: int) -> bool:
        """更新策略已送出口數"""
        try:
            with self.data_lock:
                if strategy_id not in self.active_trackers:
                    if self.console_enabled:
                        print(f"[TOTAL_MANAGER] ⚠️ 找不到策略: {strategy_id}")
                    return False
                
                tracker = self.active_trackers[strategy_id]
                return tracker.update_submitted_lots(lots)
                
        except Exception as e:
            if self.console_enabled:
                print(f"[TOTAL_MANAGER] ❌ 更新送出口數失敗: {e}")
            return False
    
    def process_order_reply(self, reply_data: str) -> bool:
        """
        處理訂單回報
        
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
            
            # 判斷方向
            direction = self._detect_direction(fields)
            
            if order_type == "D":  # 成交
                return self._handle_fill_report(price, qty, direction, product)
            elif order_type == "C":  # 取消
                return self._handle_cancel_report(price, qty, direction, product)
                
            return True
            
        except Exception as e:
            if self.console_enabled:
                print(f"[TOTAL_MANAGER] ❌ 處理回報失敗: {e}")
            return False
    
    def _detect_direction(self, fields: List[str]) -> str:
        """檢測交易方向"""
        try:
            if len(fields) > 40:
                bs_flag = fields[40] if len(fields) > 40 else ""
                if bs_flag == "B":
                    return "LONG"
                elif bs_flag == "S":
                    return "SHORT"
            return "LONG"  # 預設
        except:
            return "LONG"
    
    def _find_matching_tracker(self, price: float, direction: str, 
                             product: str) -> Optional[TotalLotTracker]:
        """
        找到匹配的追蹤器
        基於方向、商品、時間窗口匹配
        """
        try:
            current_time = time.time()
            candidates = []
            
            for tracker in self.active_trackers.values():
                # 基本條件檢查
                if (tracker.direction == direction and 
                    tracker.product == product and
                    not tracker.is_complete()):
                    
                    # 時間窗口檢查 (5分鐘)
                    if current_time - tracker.start_time <= 300:
                        candidates.append(tracker)
            
            if not candidates:
                return None
            
            # 如果有多個候選，選擇最新創建的
            return max(candidates, key=lambda t: t.start_time)
            
        except Exception as e:
            if self.console_enabled:
                print(f"[TOTAL_MANAGER] ❌ 匹配追蹤器失敗: {e}")
            return None
    
    def _handle_fill_report(self, price: float, qty: int, direction: str, 
                          product: str) -> bool:
        """處理成交回報"""
        try:
            tracker = self._find_matching_tracker(price, direction, product)
            if not tracker:
                if self.console_enabled:
                    print(f"[TOTAL_MANAGER] ⚠️ 找不到匹配的追蹤器: "
                          f"{direction} {product} {qty}口 @{price}")
                return False
            
            return tracker.process_fill_report(price, qty)
            
        except Exception as e:
            if self.console_enabled:
                print(f"[TOTAL_MANAGER] ❌ 處理成交回報失敗: {e}")
            return False
    
    def _handle_cancel_report(self, price: float, qty: int, direction: str, 
                            product: str) -> bool:
        """處理取消回報"""
        try:
            tracker = self._find_matching_tracker(price, direction, product)
            if not tracker:
                if self.console_enabled:
                    print(f"[TOTAL_MANAGER] ⚠️ 找不到匹配的追蹤器(取消): "
                          f"{direction} {product} {qty}口 @{price}")
                return False
            
            return tracker.process_cancel_report(price, qty)
            
        except Exception as e:
            if self.console_enabled:
                print(f"[TOTAL_MANAGER] ❌ 處理取消回報失敗: {e}")
            return False
    
    def _on_strategy_fill(self, strategy_id: str, price: float, qty: int, 
                        filled_lots: int, total_lots: int):
        """策略成交回調"""
        try:
            # 觸發全局成交回調
            for callback in self.global_fill_callbacks:
                try:
                    callback(strategy_id, price, qty, filled_lots, total_lots)
                except Exception as e:
                    if self.console_enabled:
                        print(f"[TOTAL_MANAGER] ⚠️ 全局成交回調失敗: {e}")
        except Exception as e:
            if self.console_enabled:
                print(f"[TOTAL_MANAGER] ❌ 策略成交回調失敗: {e}")
    
    def _on_strategy_retry(self, strategy_id: str, qty: int, price: float, retry_count: int):
        """策略追價回調"""
        try:
            # 觸發全局追價回調
            for callback in self.global_retry_callbacks:
                try:
                    callback(strategy_id, qty, price, retry_count)
                except Exception as e:
                    if self.console_enabled:
                        print(f"[TOTAL_MANAGER] ⚠️ 全局追價回調失敗: {e}")
        except Exception as e:
            if self.console_enabled:
                print(f"[TOTAL_MANAGER] ❌ 策略追價回調失敗: {e}")
    
    def _on_strategy_complete(self, strategy_id: str, fill_records: List):
        """策略完成回調"""
        try:
            with self.data_lock:
                if strategy_id in self.active_trackers:
                    tracker = self.active_trackers[strategy_id]
                    if tracker.status == TrackerStatus.COMPLETED:
                        self.completed_strategies += 1
                    elif tracker.status == TrackerStatus.FAILED:
                        self.failed_strategies += 1
            
            # 觸發全局完成回調
            for callback in self.global_complete_callbacks:
                try:
                    callback(strategy_id, fill_records)
                except Exception as e:
                    if self.console_enabled:
                        print(f"[TOTAL_MANAGER] ⚠️ 全局完成回調失敗: {e}")
                        
        except Exception as e:
            if self.console_enabled:
                print(f"[TOTAL_MANAGER] ❌ 策略完成回調失敗: {e}")
    
    def get_tracker(self, strategy_id: str) -> Optional[TotalLotTracker]:
        """獲取指定的追蹤器"""
        return self.active_trackers.get(strategy_id)
    
    def get_all_statistics(self) -> Dict:
        """獲取所有統計信息"""
        try:
            with self.data_lock:
                stats = {
                    'total_strategies': self.total_strategies,
                    'completed_strategies': self.completed_strategies,
                    'failed_strategies': self.failed_strategies,
                    'active_strategies': len([t for t in self.active_trackers.values() 
                                            if not t.is_complete()]),
                    'trackers': {}
                }
                
                for strategy_id, tracker in self.active_trackers.items():
                    stats['trackers'][strategy_id] = tracker.get_statistics()
                
                return stats
                
        except Exception as e:
            if self.console_enabled:
                print(f"[TOTAL_MANAGER] ❌ 獲取統計信息失敗: {e}")
            return {}
    
    def cleanup_completed_trackers(self, max_age_seconds: int = 3600):
        """清理已完成的追蹤器"""
        try:
            with self.data_lock:
                current_time = time.time()
                to_remove = []
                
                for strategy_id, tracker in self.active_trackers.items():
                    if tracker.is_complete() or tracker.status == TrackerStatus.FAILED:
                        if current_time - tracker.start_time > max_age_seconds:
                            to_remove.append(strategy_id)
                
                for strategy_id in to_remove:
                    del self.active_trackers[strategy_id]
                    if self.console_enabled:
                        print(f"[TOTAL_MANAGER] 🧹 清理已完成策略: {strategy_id}")
                
        except Exception as e:
            if self.console_enabled:
                print(f"[TOTAL_MANAGER] ❌ 清理追蹤器失敗: {e}")
    
    def add_global_fill_callback(self, callback):
        """添加全局成交回調"""
        self.global_fill_callbacks.append(callback)
    
    def add_global_retry_callback(self, callback):
        """添加全局追價回調"""
        self.global_retry_callbacks.append(callback)
    
    def add_global_complete_callback(self, callback):
        """添加全局完成回調"""
        self.global_complete_callbacks.append(callback)
