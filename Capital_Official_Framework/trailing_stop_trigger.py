#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
移動停利觸發器 - 整合到現有觸發器系統
低風險設計：完全參考止損觸發器的結構
"""

import time
from datetime import datetime
from dataclasses import dataclass
from typing import Optional
import logging

logger = logging.getLogger(__name__)

@dataclass
class TrailingStopTrigger:
    """
    移動停利觸發器 - 🔧 新增：參考StopLossTrigger結構
    
    完全兼容現有的止損執行器，確保移動停利能享有：
    1. 相同的平倉執行邏輯
    2. 相同的追價機制
    3. 相同的狀態更新機制
    4. 相同的回報確認機制
    """
    position_id: int
    group_id: int
    direction: str  # LONG/SHORT (原始部位方向)
    entry_price: float
    peak_price: float
    current_price: float
    stop_loss_price: float  # 移動停利觸發價格
    trigger_time: str
    trigger_reason: str = "TRAILING_STOP"
    breach_amount: float = 0.0  # 觸發時的回撤金額
    pullback_percent: float = 0.0  # 回撤百分比
    activation_points: float = 0.0  # 啟動點數
    
    def __post_init__(self):
        """初始化後處理"""
        # 計算回撤金額
        if self.direction == "LONG":
            self.breach_amount = self.peak_price - self.current_price
        else:
            self.breach_amount = self.current_price - self.peak_price
    
    @property
    def exit_direction(self) -> str:
        """計算平倉方向 - 與止損邏輯相同"""
        return "SHORT" if self.direction == "LONG" else "LONG"
    
    @property
    def expected_pnl(self) -> float:
        """計算預期損益"""
        if self.direction == "LONG":
            return self.stop_loss_price - self.entry_price
        else:
            return self.entry_price - self.stop_loss_price
    
    def to_dict(self) -> dict:
        """轉換為字典格式 - 便於日誌和調試"""
        return {
            'position_id': self.position_id,
            'group_id': self.group_id,
            'direction': self.direction,
            'entry_price': self.entry_price,
            'peak_price': self.peak_price,
            'current_price': self.current_price,
            'stop_loss_price': self.stop_loss_price,
            'trigger_time': self.trigger_time,
            'trigger_reason': self.trigger_reason,
            'breach_amount': self.breach_amount,
            'pullback_percent': self.pullback_percent,
            'activation_points': self.activation_points,
            'exit_direction': self.exit_direction,
            'expected_pnl': self.expected_pnl
        }
    
    @classmethod
    def from_trailing_calculator_trigger(cls, trigger_info: dict, group_id: int = 1):
        """
        從移動停利計算器的觸發信息創建觸發器
        
        Args:
            trigger_info: 移動停利計算器返回的觸發信息
            group_id: 組別ID
            
        Returns:
            TrailingStopTrigger: 移動停利觸發器實例
        """
        return cls(
            position_id=trigger_info['position_id'],
            group_id=group_id,
            direction=trigger_info['direction'],
            entry_price=trigger_info['entry_price'],
            peak_price=trigger_info['peak_price'],
            current_price=trigger_info['current_price'],
            stop_loss_price=trigger_info['stop_price'],
            trigger_time=trigger_info['trigger_time'],
            trigger_reason=f"移動停利: {trigger_info['trigger_reason']}",
            pullback_percent=trigger_info.get('pullback_percent', 0.0)
        )
    
    def is_valid(self) -> bool:
        """驗證觸發器是否有效"""
        try:
            # 基本字段檢查
            if not all([
                self.position_id > 0,
                self.group_id > 0,
                self.direction in ['LONG', 'SHORT'],
                self.entry_price > 0,
                self.peak_price > 0,
                self.current_price > 0,
                self.stop_loss_price > 0
            ]):
                return False
            
            # 邏輯檢查
            if self.direction == "LONG":
                # 多單：峰值應該 >= 進場價，當前價 <= 停利價
                if self.peak_price < self.entry_price:
                    return False
                if self.current_price > self.stop_loss_price:
                    return False
            else:
                # 空單：峰值應該 <= 進場價，當前價 >= 停利價
                if self.peak_price > self.entry_price:
                    return False
                if self.current_price < self.stop_loss_price:
                    return False
            
            return True
            
        except Exception as e:
            logger.error(f"驗證移動停利觸發器失敗: {e}")
            return False
    
    def get_execution_info(self) -> dict:
        """
        獲取執行信息 - 供止損執行器使用
        
        Returns:
            dict: 執行所需的信息
        """
        return {
            'position_id': self.position_id,
            'exit_direction': self.exit_direction,
            'exit_price': self.stop_loss_price,
            'exit_reason': self.trigger_reason,
            'quantity': 1,  # 預設1口，實際由執行器決定
            'trigger_info': self.to_dict()
        }

class TrailingStopTriggerManager:
    """
    移動停利觸發器管理器 - 🔧 新增：管理移動停利觸發
    
    功能：
    1. 接收移動停利計算器的觸發信息
    2. 創建標準化的觸發器
    3. 轉發給止損執行器
    4. 記錄觸發歷史
    """
    
    def __init__(self, console_enabled=True):
        """
        初始化觸發器管理器
        
        Args:
            console_enabled: 是否啟用控制台輸出
        """
        self.console_enabled = console_enabled
        self.trigger_history = []
        self.trigger_callbacks = []
        
        # 統計信息
        self.stats = {
            'total_triggers': 0,
            'valid_triggers': 0,
            'invalid_triggers': 0,
            'executed_triggers': 0
        }
        
        if self.console_enabled:
            print(f"[TRAILING_TRIGGER] 🎯 移動停利觸發器管理器已初始化")
    
    def process_trigger(self, trigger_info: dict, group_id: int = 1) -> Optional[TrailingStopTrigger]:
        """
        處理移動停利觸發
        
        Args:
            trigger_info: 移動停利計算器的觸發信息
            group_id: 組別ID
            
        Returns:
            TrailingStopTrigger: 創建的觸發器，None表示無效
        """
        try:
            self.stats['total_triggers'] += 1
            
            # 創建觸發器
            trigger = TrailingStopTrigger.from_trailing_calculator_trigger(trigger_info, group_id)
            
            # 驗證觸發器
            if not trigger.is_valid():
                self.stats['invalid_triggers'] += 1
                if self.console_enabled:
                    print(f"[TRAILING_TRIGGER] ❌ 無效的移動停利觸發: 部位{trigger.position_id}")
                return None
            
            self.stats['valid_triggers'] += 1
            
            # 記錄觸發歷史
            self.trigger_history.append({
                'trigger': trigger,
                'timestamp': time.time(),
                'processed': True
            })
            
            if self.console_enabled:
                print(f"[TRAILING_TRIGGER] ✅ 移動停利觸發已處理: 部位{trigger.position_id} "
                      f"{trigger.direction} 峰值{trigger.peak_price:.0f} → 停利{trigger.stop_loss_price:.0f}")
            
            # 觸發回調
            self._trigger_callbacks(trigger)
            
            return trigger
            
        except Exception as e:
            logger.error(f"處理移動停利觸發失敗: {e}")
            if self.console_enabled:
                print(f"[TRAILING_TRIGGER] ❌ 處理觸發失敗: {e}")
            return None
    
    def add_trigger_callback(self, callback):
        """
        添加觸發回調函數
        
        Args:
            callback: 回調函數，接收TrailingStopTrigger作為參數
        """
        if callback not in self.trigger_callbacks:
            self.trigger_callbacks.append(callback)
            if self.console_enabled:
                print(f"[TRAILING_TRIGGER] 📞 添加觸發回調，總數: {len(self.trigger_callbacks)}")
    
    def remove_trigger_callback(self, callback):
        """移除觸發回調函數"""
        if callback in self.trigger_callbacks:
            self.trigger_callbacks.remove(callback)
            if self.console_enabled:
                print(f"[TRAILING_TRIGGER] 📞 移除觸發回調，總數: {len(self.trigger_callbacks)}")
    
    def _trigger_callbacks(self, trigger: TrailingStopTrigger):
        """觸發所有回調函數"""
        for callback in self.trigger_callbacks:
            try:
                callback(trigger)
                self.stats['executed_triggers'] += 1
            except Exception as e:
                logger.error(f"移動停利觸發回調失敗: {e}")
                if self.console_enabled:
                    print(f"[TRAILING_TRIGGER] ❌ 回調執行失敗: {e}")
    
    def get_statistics(self) -> dict:
        """獲取統計信息"""
        return {
            'total_triggers': self.stats['total_triggers'],
            'valid_triggers': self.stats['valid_triggers'],
            'invalid_triggers': self.stats['invalid_triggers'],
            'executed_triggers': self.stats['executed_triggers'],
            'trigger_history_count': len(self.trigger_history),
            'active_callbacks': len(self.trigger_callbacks)
        }
    
    def get_recent_triggers(self, limit: int = 10) -> list:
        """獲取最近的觸發記錄"""
        return self.trigger_history[-limit:] if self.trigger_history else []
    
    def cleanup(self):
        """清理資源"""
        self.trigger_history.clear()
        self.trigger_callbacks.clear()
        if self.console_enabled:
            print(f"[TRAILING_TRIGGER] 🧹 觸發器管理器已清理")

# 輔助函數
def create_trailing_stop_trigger_manager(console_enabled=True):
    """
    創建移動停利觸發器管理器
    
    Args:
        console_enabled: 是否啟用控制台輸出
        
    Returns:
        TrailingStopTriggerManager: 觸發器管理器實例
    """
    return TrailingStopTriggerManager(console_enabled)
