#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
移動停利計算器 - 實現峰值追蹤和停利點位計算
零風險設計：不影響現有功能，純粹計算和追蹤
"""

import time
import threading
from datetime import datetime
from typing import Dict, Optional, List, Tuple
from dataclasses import dataclass
import logging

logger = logging.getLogger(__name__)

@dataclass
class TrailingStopInfo:
    """移動停利信息"""
    position_id: int
    direction: str  # LONG/SHORT
    entry_price: float
    activation_points: float  # 啟動點數
    pullback_percent: float   # 回撤百分比
    peak_price: float         # 峰值價格
    current_stop_price: float # 當前停利價格
    is_activated: bool        # 是否已啟動
    last_update_time: float   # 最後更新時間
    created_time: float       # 創建時間

class TrailingStopCalculator:
    """
    移動停利計算器 - 🔧 新增：零風險實現
    
    功能：
    1. 峰值追蹤：實時追蹤價格峰值
    2. 停利計算：根據回撤百分比計算停利點位
    3. 定期更新：5秒更新資料庫（整合異步機制）
    4. 觸發檢測：檢測是否觸發移動停利平倉
    """
    
    def __init__(self, db_manager, async_updater=None, console_enabled=True):
        """
        初始化移動停利計算器
        
        Args:
            db_manager: 資料庫管理器
            async_updater: 異步更新器（可選）
            console_enabled: 是否啟用控制台輸出
        """
        self.db_manager = db_manager
        self.async_updater = async_updater
        self.console_enabled = console_enabled
        
        # 移動停利追蹤字典 {position_id: TrailingStopInfo}
        self.trailing_stops: Dict[int, TrailingStopInfo] = {}
        
        # 線程安全鎖
        self.data_lock = threading.RLock()
        
        # 更新控制
        self.update_interval = 5.0  # 5秒更新間隔
        self.last_db_update = time.time()
        
        # 統計信息
        self.stats = {
            'total_positions': 0,
            'activated_positions': 0,
            'triggered_exits': 0,
            'peak_updates': 0
        }
        
        # 觸發回調列表
        self.trigger_callbacks = []
        
        if self.console_enabled:
            print(f"[TRAILING_CALC] 🎯 移動停利計算器已初始化")
    
    def register_position(self, position_id: int, direction: str, entry_price: float,
                         activation_points: float, pullback_percent: float) -> bool:
        """
        註冊部位到移動停利追蹤
        
        Args:
            position_id: 部位ID
            direction: 方向 (LONG/SHORT)
            entry_price: 進場價格
            activation_points: 啟動點數
            pullback_percent: 回撤百分比 (0.0-1.0)
            
        Returns:
            bool: 註冊是否成功
        """
        try:
            with self.data_lock:
                # 檢查是否已存在
                if position_id in self.trailing_stops:
                    if self.console_enabled:
                        print(f"[TRAILING_CALC] ⚠️ 部位{position_id}已在追蹤中")
                    return False
                
                # 創建移動停利信息
                trailing_info = TrailingStopInfo(
                    position_id=position_id,
                    direction=direction.upper(),
                    entry_price=entry_price,
                    activation_points=activation_points,
                    pullback_percent=pullback_percent,
                    peak_price=entry_price,  # 初始峰值為進場價
                    current_stop_price=0.0,  # 未啟動時為0
                    is_activated=False,
                    last_update_time=time.time(),
                    created_time=time.time()
                )
                
                self.trailing_stops[position_id] = trailing_info
                self.stats['total_positions'] += 1
                
                if self.console_enabled:
                    print(f"[TRAILING_CALC] 📝 註冊移動停利: 部位{position_id} {direction} "
                          f"進場@{entry_price:.0f} 啟動{activation_points:.0f}點 回撤{pullback_percent*100:.0f}%")
                
                return True
                
        except Exception as e:
            logger.error(f"註冊移動停利失敗: {e}")
            if self.console_enabled:
                print(f"[TRAILING_CALC] ❌ 註冊失敗: {e}")
            return False
    
    def update_price(self, position_id: int, current_price: float) -> Optional[Dict]:
        """
        更新價格並計算移動停利
        
        Args:
            position_id: 部位ID
            current_price: 當前價格
            
        Returns:
            Dict: 如果觸發平倉，返回觸發信息；否則返回None
        """
        try:
            with self.data_lock:
                if position_id not in self.trailing_stops:
                    return None
                
                trailing_info = self.trailing_stops[position_id]
                current_time = time.time()
                
                # 更新峰值價格
                peak_updated = self._update_peak_price(trailing_info, current_price)
                
                # 檢查是否啟動移動停利
                activation_changed = self._check_activation(trailing_info)
                
                # 計算當前停利價格
                if trailing_info.is_activated:
                    trailing_info.current_stop_price = self._calculate_stop_price(trailing_info)
                
                # 檢查是否觸發平倉
                trigger_info = self._check_trigger(trailing_info, current_price)
                
                # 更新時間戳
                trailing_info.last_update_time = current_time
                
                # 定期更新資料庫（5秒間隔）
                if current_time - self.last_db_update >= self.update_interval:
                    self._update_database_async()
                    self.last_db_update = current_time
                
                # 統計更新
                if peak_updated:
                    self.stats['peak_updates'] += 1
                
                if activation_changed and trailing_info.is_activated:
                    self.stats['activated_positions'] += 1
                    if self.console_enabled:
                        print(f"[TRAILING_CALC] 🔔 移動停利啟動: 部位{position_id} "
                              f"峰值{trailing_info.peak_price:.0f} 停利@{trailing_info.current_stop_price:.0f}")
                
                return trigger_info
                
        except Exception as e:
            logger.error(f"更新移動停利價格失敗: {e}")
            if self.console_enabled:
                print(f"[TRAILING_CALC] ❌ 價格更新失敗: {e}")
            return None
    
    def _update_peak_price(self, trailing_info: TrailingStopInfo, current_price: float) -> bool:
        """更新峰值價格"""
        old_peak = trailing_info.peak_price
        
        if trailing_info.direction == "LONG":
            # 多單：追蹤最高價
            trailing_info.peak_price = max(trailing_info.peak_price, current_price)
        else:
            # 空單：追蹤最低價
            trailing_info.peak_price = min(trailing_info.peak_price, current_price)
        
        return trailing_info.peak_price != old_peak
    
    def _check_activation(self, trailing_info: TrailingStopInfo) -> bool:
        """檢查是否啟動移動停利"""
        if trailing_info.is_activated:
            return False
        
        activation_price = 0.0
        if trailing_info.direction == "LONG":
            # 多單：峰值超過進場價 + 啟動點數
            activation_price = trailing_info.entry_price + trailing_info.activation_points
            should_activate = trailing_info.peak_price >= activation_price
        else:
            # 空單：峰值低於進場價 - 啟動點數
            activation_price = trailing_info.entry_price - trailing_info.activation_points
            should_activate = trailing_info.peak_price <= activation_price
        
        if should_activate:
            trailing_info.is_activated = True
            return True
        
        return False
    
    def _calculate_stop_price(self, trailing_info: TrailingStopInfo) -> float:
        """計算當前停利價格"""
        if not trailing_info.is_activated:
            return 0.0
        
        if trailing_info.direction == "LONG":
            # 多單：峰值 - (峰值-進場價) * 回撤百分比
            profit_range = trailing_info.peak_price - trailing_info.entry_price
            stop_price = trailing_info.peak_price - (profit_range * trailing_info.pullback_percent)
        else:
            # 空單：峰值 + (進場價-峰值) * 回撤百分比
            profit_range = trailing_info.entry_price - trailing_info.peak_price
            stop_price = trailing_info.peak_price + (profit_range * trailing_info.pullback_percent)
        
        return stop_price
    
    def _check_trigger(self, trailing_info: TrailingStopInfo, current_price: float) -> Optional[Dict]:
        """檢查是否觸發移動停利平倉"""
        if not trailing_info.is_activated:
            return None
        
        should_trigger = False
        
        if trailing_info.direction == "LONG":
            # 多單：當前價格跌破停利價格
            should_trigger = current_price <= trailing_info.current_stop_price
        else:
            # 空單：當前價格漲破停利價格
            should_trigger = current_price >= trailing_info.current_stop_price
        
        if should_trigger:
            self.stats['triggered_exits'] += 1
            
            trigger_info = {
                'position_id': trailing_info.position_id,
                'direction': trailing_info.direction,
                'entry_price': trailing_info.entry_price,
                'peak_price': trailing_info.peak_price,
                'stop_price': trailing_info.current_stop_price,
                'current_price': current_price,
                'trigger_time': datetime.now().strftime('%H:%M:%S'),
                'trigger_reason': 'TRAILING_STOP',
                'pullback_percent': trailing_info.pullback_percent
            }
            
            if self.console_enabled:
                print(f"[TRAILING_CALC] 🚨 移動停利觸發: 部位{trailing_info.position_id} "
                      f"當前{current_price:.0f} 觸及停利{trailing_info.current_stop_price:.0f}")
            
            # 觸發後移除追蹤
            del self.trailing_stops[trailing_info.position_id]
            
            return trigger_info
        
        return None

    def _update_database_async(self):
        """異步更新資料庫 - 🔧 整合現有異步機制"""
        try:
            if not self.async_updater:
                return

            # 收集需要更新的移動停利信息
            updates = []
            with self.data_lock:
                for position_id, trailing_info in self.trailing_stops.items():
                    if trailing_info.is_activated:
                        updates.append({
                            'position_id': position_id,
                            'peak_price': trailing_info.peak_price,
                            'stop_price': trailing_info.current_stop_price,
                            'is_activated': trailing_info.is_activated,
                            'last_update': trailing_info.last_update_time
                        })

            # 使用異步更新器更新（非阻塞）
            if updates and hasattr(self.async_updater, 'schedule_trailing_stop_update'):
                for update in updates:
                    self.async_updater.schedule_trailing_stop_update(
                        position_id=update['position_id'],
                        peak_price=update['peak_price'],
                        stop_price=update['stop_price'],
                        is_activated=update['is_activated']
                    )

                if self.console_enabled:
                    print(f"[TRAILING_CALC] 🚀 異步更新{len(updates)}個移動停利")

        except Exception as e:
            logger.error(f"異步更新移動停利失敗: {e}")
            if self.console_enabled:
                print(f"[TRAILING_CALC] ❌ 異步更新失敗: {e}")

    def remove_position(self, position_id: int) -> bool:
        """
        移除部位追蹤

        Args:
            position_id: 部位ID

        Returns:
            bool: 移除是否成功
        """
        try:
            with self.data_lock:
                if position_id in self.trailing_stops:
                    del self.trailing_stops[position_id]
                    if self.console_enabled:
                        print(f"[TRAILING_CALC] 🗑️ 移除移動停利追蹤: 部位{position_id}")
                    return True
                return False

        except Exception as e:
            logger.error(f"移除移動停利追蹤失敗: {e}")
            return False

    def get_position_info(self, position_id: int) -> Optional[Dict]:
        """
        獲取部位的移動停利信息

        Args:
            position_id: 部位ID

        Returns:
            Dict: 移動停利信息，None表示不存在
        """
        try:
            with self.data_lock:
                if position_id not in self.trailing_stops:
                    return None

                trailing_info = self.trailing_stops[position_id]
                return {
                    'position_id': trailing_info.position_id,
                    'direction': trailing_info.direction,
                    'entry_price': trailing_info.entry_price,
                    'peak_price': trailing_info.peak_price,
                    'current_stop_price': trailing_info.current_stop_price,
                    'is_activated': trailing_info.is_activated,
                    'activation_points': trailing_info.activation_points,
                    'pullback_percent': trailing_info.pullback_percent,
                    'last_update_time': trailing_info.last_update_time
                }

        except Exception as e:
            logger.error(f"獲取移動停利信息失敗: {e}")
            return None

    def get_all_positions(self) -> List[Dict]:
        """獲取所有追蹤中的部位信息"""
        try:
            with self.data_lock:
                positions = []
                for position_id in self.trailing_stops:
                    info = self.get_position_info(position_id)
                    if info:
                        positions.append(info)
                return positions

        except Exception as e:
            logger.error(f"獲取所有移動停利信息失敗: {e}")
            return []

    def add_trigger_callback(self, callback):
        """
        添加觸發回調函數

        Args:
            callback: 回調函數，接收觸發信息作為參數
        """
        if callback not in self.trigger_callbacks:
            self.trigger_callbacks.append(callback)
            if self.console_enabled:
                print(f"[TRAILING_CALC] 📞 添加觸發回調，總數: {len(self.trigger_callbacks)}")

    def remove_trigger_callback(self, callback):
        """移除觸發回調函數"""
        if callback in self.trigger_callbacks:
            self.trigger_callbacks.remove(callback)
            if self.console_enabled:
                print(f"[TRAILING_CALC] 📞 移除觸發回調，總數: {len(self.trigger_callbacks)}")

    def get_statistics(self) -> Dict:
        """獲取統計信息"""
        with self.data_lock:
            return {
                'total_positions': self.stats['total_positions'],
                'activated_positions': self.stats['activated_positions'],
                'triggered_exits': self.stats['triggered_exits'],
                'peak_updates': self.stats['peak_updates'],
                'current_tracking': len(self.trailing_stops),
                'update_interval': self.update_interval
            }

    def set_async_updater(self, async_updater):
        """設定異步更新器"""
        self.async_updater = async_updater
        if self.console_enabled:
            print(f"[TRAILING_CALC] 🔗 異步更新器已設定")

    def cleanup(self):
        """清理資源"""
        try:
            with self.data_lock:
                self.trailing_stops.clear()
                self.trigger_callbacks.clear()

            if self.console_enabled:
                print(f"[TRAILING_CALC] 🧹 移動停利計算器已清理")

        except Exception as e:
            logger.error(f"清理移動停利計算器失敗: {e}")

# 輔助函數
def create_trailing_stop_calculator(db_manager, async_updater=None, console_enabled=True):
    """
    創建移動停利計算器實例

    Args:
        db_manager: 資料庫管理器
        async_updater: 異步更新器（可選）
        console_enabled: 是否啟用控制台輸出

    Returns:
        TrailingStopCalculator: 移動停利計算器實例
    """
    return TrailingStopCalculator(db_manager, async_updater, console_enabled)
