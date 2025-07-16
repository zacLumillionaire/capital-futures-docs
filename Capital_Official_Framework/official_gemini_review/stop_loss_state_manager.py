#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
停損狀態管理器
實作 is_initial_stop 狀態管理，支援從初始停損轉為保護性停損
"""

import logging
import time
from datetime import datetime
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
from enum import Enum

logger = logging.getLogger(__name__)

class StopLossType(Enum):
    """停損類型枚舉"""
    INITIAL = "INITIAL"           # 初始停損 (區間邊緣)
    PROTECTIVE = "PROTECTIVE"     # 保護性停損 (累積獲利保護)
    TRAILING = "TRAILING"         # 移動停利

@dataclass
class StopLossStateTransition:
    """停損狀態轉換資訊"""
    position_id: int
    group_id: int
    lot_number: int
    from_type: StopLossType
    to_type: StopLossType
    old_stop_loss: float
    new_stop_loss: float
    transition_reason: str
    transition_time: str

class StopLossStateManager:
    """
    停損狀態管理器
    管理停損狀態轉換和 is_initial_stop 標記
    """
    
    def __init__(self, db_manager, console_enabled: bool = True):
        """
        初始化停損狀態管理器
        
        Args:
            db_manager: 資料庫管理器
            console_enabled: 是否啟用Console日誌
        """
        self.db_manager = db_manager
        self.console_enabled = console_enabled
        self.state_transitions: List[StopLossStateTransition] = []  # 狀態轉換歷史
        self.transition_callbacks: List = []  # 狀態轉換回調函數
        
        if self.console_enabled:
            print("[STOP_STATE] ⚙️ 停損狀態管理器初始化完成")
    
    def add_transition_callback(self, callback):
        """
        添加狀態轉換回調函數
        
        Args:
            callback: 回調函數，接收 StopLossStateTransition 參數
        """
        self.transition_callbacks.append(callback)
        if self.console_enabled:
            print(f"[STOP_STATE] 📞 添加轉換回調函數: {callback.__name__}")
    
    def transition_to_protective_stop(self, position_id: int, new_stop_loss: float, 
                                    transition_reason: str) -> Optional[StopLossStateTransition]:
        """
        轉換為保護性停損
        
        Args:
            position_id: 部位ID
            new_stop_loss: 新停損價格
            transition_reason: 轉換原因
            
        Returns:
            Optional[StopLossStateTransition]: 狀態轉換資訊 (如果成功)
        """
        try:
            # 取得當前部位資訊
            position_info = self._get_position_info(position_id)
            if not position_info:
                if self.console_enabled:
                    print(f"[STOP_STATE] ❌ 部位 {position_id} 不存在或已平倉")
                return None
            
            # 檢查是否為初始停損狀態
            if not position_info.get('is_initial_stop', False):
                if self.console_enabled:
                    print(f"[STOP_STATE] ℹ️ 部位 {position_id} 已非初始停損狀態，跳過轉換")
                return None
            
            old_stop_loss = position_info.get('current_stop_loss')
            lot_id = position_info.get('lot_id', 1)
            group_id = position_info.get('group_id')
            
            if self.console_enabled:
                print(f"[STOP_STATE] 🔄 停損狀態轉換:")
                print(f"[STOP_STATE]   部位ID: {position_id} (第{lot_id}口)")
                print(f"[STOP_STATE]   轉換類型: 初始停損 → 保護性停損")
                print(f"[STOP_STATE]   舊停損: {old_stop_loss}")
                print(f"[STOP_STATE]   新停損: {new_stop_loss}")
                print(f"[STOP_STATE]   轉換原因: {transition_reason}")
            
            # 執行狀態轉換
            success = self._execute_state_transition(
                position_id, StopLossType.INITIAL, StopLossType.PROTECTIVE, 
                new_stop_loss, transition_reason
            )
            
            if success:
                transition = StopLossStateTransition(
                    position_id=position_id,
                    group_id=group_id,
                    lot_number=lot_id,
                    from_type=StopLossType.INITIAL,
                    to_type=StopLossType.PROTECTIVE,
                    old_stop_loss=old_stop_loss,
                    new_stop_loss=new_stop_loss,
                    transition_reason=transition_reason,
                    transition_time=datetime.now().strftime('%H:%M:%S')
                )
                
                # 記錄轉換歷史
                self.state_transitions.append(transition)
                
                # 觸發回調函數
                self._trigger_transition_callbacks(transition)
                
                if self.console_enabled:
                    print(f"[STOP_STATE] ✅ 部位 {position_id} 狀態轉換完成")
                
                return transition
            
            return None
            
        except Exception as e:
            logger.error(f"轉換為保護性停損失敗: {e}")
            if self.console_enabled:
                print(f"[STOP_STATE] ❌ 狀態轉換失敗: {e}")
            return None
    
    def transition_to_trailing_stop(self, position_id: int, peak_price: float) -> Optional[StopLossStateTransition]:
        """
        轉換為移動停利
        
        Args:
            position_id: 部位ID
            peak_price: 峰值價格
            
        Returns:
            Optional[StopLossStateTransition]: 狀態轉換資訊 (如果成功)
        """
        try:
            # 取得當前部位資訊
            position_info = self._get_position_info(position_id)
            if not position_info:
                return None
            
            old_stop_loss = position_info.get('current_stop_loss')
            lot_id = position_info.get('lot_id', 1)
            group_id = position_info.get('group_id')
            current_type = StopLossType.PROTECTIVE if not position_info.get('is_initial_stop', True) else StopLossType.INITIAL
            
            transition_reason = f"移動停利啟動，峰值價格: {peak_price}"
            
            if self.console_enabled:
                print(f"[STOP_STATE] 🎯 移動停利狀態轉換:")
                print(f"[STOP_STATE]   部位ID: {position_id} (第{lot_id}口)")
                print(f"[STOP_STATE]   轉換類型: {current_type.value} → 移動停利")
                print(f"[STOP_STATE]   峰值價格: {peak_price}")
            
            # 執行狀態轉換
            success = self._execute_trailing_transition(position_id, peak_price, transition_reason)
            
            if success:
                transition = StopLossStateTransition(
                    position_id=position_id,
                    group_id=group_id,
                    lot_number=lot_id,
                    from_type=current_type,
                    to_type=StopLossType.TRAILING,
                    old_stop_loss=old_stop_loss,
                    new_stop_loss=peak_price,  # 移動停利使用峰值價格
                    transition_reason=transition_reason,
                    transition_time=datetime.now().strftime('%H:%M:%S')
                )
                
                # 記錄轉換歷史
                self.state_transitions.append(transition)
                
                # 觸發回調函數
                self._trigger_transition_callbacks(transition)
                
                if self.console_enabled:
                    print(f"[STOP_STATE] ✅ 部位 {position_id} 移動停利轉換完成")
                
                return transition
            
            return None
            
        except Exception as e:
            logger.error(f"轉換為移動停利失敗: {e}")
            if self.console_enabled:
                print(f"[STOP_STATE] ❌ 移動停利轉換失敗: {e}")
            return None
    
    def _get_position_info(self, position_id: int) -> Optional[Dict]:
        """取得部位資訊"""
        try:
            with self.db_manager.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    SELECT * FROM position_records 
                    WHERE id = ? AND status = 'ACTIVE'
                ''', (position_id,))
                
                row = cursor.fetchone()
                if row:
                    columns = [description[0] for description in cursor.description]
                    return dict(zip(columns, row))
                return None
                
        except Exception as e:
            logger.error(f"查詢部位資訊失敗: {e}")
            return None
    
    def _execute_state_transition(self, position_id: int, from_type: StopLossType, 
                                to_type: StopLossType, new_stop_loss: float, 
                                transition_reason: str) -> bool:
        """執行狀態轉換"""
        try:
            with self.db_manager.get_connection() as conn:
                cursor = conn.cursor()
                
                # 更新 position_records
                cursor.execute('''
                    UPDATE position_records 
                    SET current_stop_loss = ?,
                        is_initial_stop = FALSE,
                        last_price_update_time = ?
                    WHERE id = ?
                ''', (
                    new_stop_loss,
                    datetime.now().strftime('%H:%M:%S'),
                    position_id
                ))
                
                # 更新 risk_management_states (如果存在)
                cursor.execute('''
                    UPDATE risk_management_states 
                    SET current_stop_loss = ?,
                        protection_activated = TRUE,
                        last_update_time = ?,
                        update_reason = ?
                    WHERE position_id = ?
                ''', (
                    new_stop_loss,
                    datetime.now().strftime('%H:%M:%S'),
                    f"狀態轉換: {from_type.value} → {to_type.value}",
                    position_id
                ))
                
                conn.commit()
                return True
                
        except Exception as e:
            logger.error(f"執行狀態轉換失敗: {e}")
            return False
    
    def _execute_trailing_transition(self, position_id: int, peak_price: float, 
                                   transition_reason: str) -> bool:
        """執行移動停利轉換"""
        try:
            with self.db_manager.get_connection() as conn:
                cursor = conn.cursor()
                
                # 更新 position_records
                cursor.execute('''
                    UPDATE position_records 
                    SET trailing_activated = TRUE,
                        peak_price = ?,
                        is_initial_stop = FALSE,
                        last_price_update_time = ?
                    WHERE id = ?
                ''', (
                    peak_price,
                    datetime.now().strftime('%H:%M:%S'),
                    position_id
                ))
                
                # 更新 risk_management_states (如果存在)
                cursor.execute('''
                    UPDATE risk_management_states 
                    SET trailing_activated = TRUE,
                        peak_price = ?,
                        last_update_time = ?,
                        update_reason = ?
                    WHERE position_id = ?
                ''', (
                    peak_price,
                    datetime.now().strftime('%H:%M:%S'),
                    transition_reason,
                    position_id
                ))
                
                conn.commit()
                return True
                
        except Exception as e:
            logger.error(f"執行移動停利轉換失敗: {e}")
            return False
    
    def _trigger_transition_callbacks(self, transition: StopLossStateTransition):
        """觸發狀態轉換回調函數"""
        for callback in self.transition_callbacks:
            try:
                callback(transition)
            except Exception as e:
                logger.error(f"狀態轉換回調函數執行失敗: {e}")
                if self.console_enabled:
                    print(f"[STOP_STATE] ❌ 回調函數 {callback.__name__} 執行失敗: {e}")
    
    def get_position_stop_type(self, position_id: int) -> Optional[StopLossType]:
        """取得部位當前停損類型"""
        try:
            position_info = self._get_position_info(position_id)
            if not position_info:
                return None
            
            if position_info.get('trailing_activated', False):
                return StopLossType.TRAILING
            elif position_info.get('is_initial_stop', True):
                return StopLossType.INITIAL
            else:
                return StopLossType.PROTECTIVE
                
        except Exception as e:
            logger.error(f"取得停損類型失敗: {e}")
            return None
    
    def get_transition_summary(self) -> Dict:
        """取得狀態轉換摘要"""
        total_transitions = len(self.state_transitions)
        
        # 按轉換類型統計
        transition_counts = {}
        for transition in self.state_transitions:
            key = f"{transition.from_type.value} → {transition.to_type.value}"
            transition_counts[key] = transition_counts.get(key, 0) + 1
        
        return {
            'total_transitions': total_transitions,
            'transition_counts': transition_counts,
            'callback_count': len(self.transition_callbacks)
        }
    
    def print_state_status(self):
        """列印狀態管理狀態 (Console輸出)"""
        if not self.console_enabled:
            return
        
        summary = self.get_transition_summary()
        
        print(f"[STOP_STATE] 📊 停損狀態管理狀態:")
        print(f"[STOP_STATE]   總轉換次數: {summary['total_transitions']}")
        print(f"[STOP_STATE]   回調函數: {summary['callback_count']} 個")
        
        if summary['transition_counts']:
            print(f"[STOP_STATE] 🔄 轉換類型統計:")
            for transition_type, count in summary['transition_counts'].items():
                print(f"[STOP_STATE]   {transition_type}: {count} 次")
        
        if self.state_transitions:
            print(f"[STOP_STATE] 🔄 最近狀態轉換:")
            for transition in self.state_transitions[-3:]:  # 顯示最近3次轉換
                print(f"[STOP_STATE]   部位{transition.position_id}: {transition.from_type.value} → {transition.to_type.value}")


def create_stop_loss_state_manager(db_manager, console_enabled: bool = True) -> StopLossStateManager:
    """
    創建停損狀態管理器的工廠函數
    
    Args:
        db_manager: 資料庫管理器
        console_enabled: 是否啟用Console日誌
        
    Returns:
        StopLossStateManager: 停損狀態管理器實例
    """
    return StopLossStateManager(db_manager, console_enabled)


if __name__ == "__main__":
    # 測試用途
    print("停損狀態管理器模組")
    print("請在主程式中調用 create_stop_loss_state_manager() 函數")
