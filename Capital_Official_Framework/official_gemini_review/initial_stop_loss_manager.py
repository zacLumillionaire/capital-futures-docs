#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
初始停損管理器
負責區間邊緣停損的設定和管理，對應回測程式的停損邏輯
"""

import logging
import time
from datetime import datetime
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass

logger = logging.getLogger(__name__)

@dataclass
class StopLossInfo:
    """停損資訊"""
    position_id: int
    group_id: int
    lot_number: int
    direction: str
    entry_price: float
    stop_loss_price: float
    range_high: float
    range_low: float
    created_time: str
    is_active: bool = True

class InitialStopLossManager:
    """
    初始停損管理器
    負責區間邊緣停損的設定和管理
    """
    
    def __init__(self, db_manager, console_enabled: bool = True):
        """
        初始化停損管理器
        
        Args:
            db_manager: 資料庫管理器
            console_enabled: 是否啟用Console日誌
        """
        self.db_manager = db_manager
        self.console_enabled = console_enabled
        self.active_stop_losses: Dict[int, StopLossInfo] = {}  # position_id -> StopLossInfo
        
        if self.console_enabled:
            print("[STOP_LOSS] ⚙️ 初始停損管理器初始化完成")
    
    def setup_initial_stop_loss_for_group(self, group_db_id: int, range_data: Dict[str, float]) -> bool:
        """
        為整個策略組設定初始停損

        Args:
            group_db_id: 策略組資料庫ID
            range_data: 區間資料 {'range_high': float, 'range_low': float}

        Returns:
            bool: 設定是否成功
        """
        try:
            if self.console_enabled:
                print(f"[STOP_LOSS] 🛡️ 開始為策略組 {group_db_id} 設定初始停損")
                print(f"[STOP_LOSS] 📊 區間資料: 高點 {range_data['range_high']}, 低點 {range_data['range_low']}")

            # 🔧 修復：先獲取邏輯組ID，然後查詢活躍部位
            group_info = self.db_manager.get_strategy_group_by_db_id(group_db_id)
            if not group_info:
                if self.console_enabled:
                    print(f"[STOP_LOSS] ❌ 找不到策略組: {group_db_id}")
                return False

            logical_group_id = group_info['logical_group_id']
            positions = self.db_manager.get_active_positions_by_group(logical_group_id)

            if not positions:
                if self.console_enabled:
                    print(f"[STOP_LOSS] ⚠️ 策略組 {logical_group_id} (DB_ID:{group_db_id}) 沒有活躍部位")
                return False

            success_count = 0
            total_count = len(positions)

            for position in positions:
                if self._setup_position_initial_stop_loss(position, range_data):
                    success_count += 1

            if self.console_enabled:
                print(f"[STOP_LOSS] ✅ 初始停損設定完成: {success_count}/{total_count} 個部位")
                if success_count == total_count:
                    print(f"[STOP_LOSS] 🎯 策略組 {group_db_id} 所有部位停損設定成功")
                else:
                    print(f"[STOP_LOSS] ⚠️ 部分部位停損設定失敗")

            return success_count > 0

        except Exception as e:
            logger.error(f"設定策略組停損失敗: {e}")
            if self.console_enabled:
                print(f"[STOP_LOSS] ❌ 策略組 {group_db_id} 停損設定失敗: {e}")
            return False
    
    def _setup_position_initial_stop_loss(self, position: Dict, range_data: Dict[str, float]) -> bool:
        """
        為單個部位設定初始停損

        Args:
            position: 部位資料
            range_data: 區間資料

        Returns:
            bool: 設定是否成功
        """
        position_id = None  # 🔧 修復：初始化變數避免異常處理時未定義錯誤
        try:
            # 🔧 修復：使用正確的鍵名 'position_pk' 而不是 'id'
            position_id = position.get('position_pk') or position.get('id')
            if position_id is None:
                if self.console_enabled:
                    print(f"[STOP_LOSS] ❌ 部位資料缺少ID: {position}")
                return False

            direction = position['direction']
            entry_price = position.get('entry_price')
            lot_id = position.get('lot_id', 1)

            if entry_price is None:
                if self.console_enabled:
                    print(f"[STOP_LOSS] ⚠️ 部位 {position_id} 缺少進場價格，跳過停損設定")
                return False

            # 計算初始停損價格 (區間邊緣)
            stop_loss_price = self._calculate_initial_stop_loss_price(direction, range_data)

            if self.console_enabled:
                print(f"[STOP_LOSS] 🎯 部位 {position_id} (第{lot_id}口):")
                print(f"[STOP_LOSS]   📍 方向: {direction}")
                print(f"[STOP_LOSS]   💰 進場價格: {entry_price}")
                print(f"[STOP_LOSS]   🛡️ 初始停損: {stop_loss_price}")
                print(f"[STOP_LOSS]   📏 停損距離: {abs(entry_price - stop_loss_price):.1f} 點")

            # 更新資料庫
            success = self._update_position_stop_loss_in_db(
                position_id, stop_loss_price, range_data, entry_price
            )

            if success:
                # 創建停損資訊記錄
                stop_loss_info = StopLossInfo(
                    position_id=position_id,
                    group_id=position.get('group_pk') or position.get('group_id'),  # 🔧 修復：使用正確的鍵名
                    lot_number=lot_id,
                    direction=direction,
                    entry_price=entry_price,
                    stop_loss_price=stop_loss_price,
                    range_high=range_data['range_high'],
                    range_low=range_data['range_low'],
                    created_time=datetime.now().strftime('%H:%M:%S')
                )

                self.active_stop_losses[position_id] = stop_loss_info

                if self.console_enabled:
                    print(f"[STOP_LOSS] ✅ 部位 {position_id} 初始停損設定成功")

            return success

        except Exception as e:
            logger.error(f"設定部位停損失敗: {e}")
            if self.console_enabled:
                # 🔧 修復：安全地顯示position_id，避免未定義變數錯誤
                position_display = position_id if position_id is not None else "未知"
                print(f"[STOP_LOSS] ❌ 部位 {position_display} 停損設定失敗: {e}")
            return False
    
    def _calculate_initial_stop_loss_price(self, direction: str, range_data: Dict[str, float]) -> float:
        """
        計算初始停損價格 (區間邊緣)
        
        Args:
            direction: 交易方向 (LONG/SHORT)
            range_data: 區間資料
            
        Returns:
            float: 停損價格
        """
        if direction == "LONG":
            # 做多：停損設在區間低點
            stop_loss_price = range_data['range_low']
        elif direction == "SHORT":
            # 做空：停損設在區間高點
            stop_loss_price = range_data['range_high']
        else:
            raise ValueError(f"不支援的交易方向: {direction}")
        
        return stop_loss_price
    
    def _update_position_stop_loss_in_db(self, position_id: int, stop_loss_price: float, 
                                       range_data: Dict[str, float], entry_price: float) -> bool:
        """
        更新資料庫中的停損資訊
        
        Args:
            position_id: 部位ID
            stop_loss_price: 停損價格
            range_data: 區間資料
            entry_price: 進場價格
            
        Returns:
            bool: 更新是否成功
        """
        try:
            with self.db_manager.get_connection() as conn:
                cursor = conn.cursor()
                
                # 更新 position_records 表格
                cursor.execute('''
                    UPDATE position_records 
                    SET initial_stop_loss = ?,
                        current_stop_loss = ?,
                        is_initial_stop = TRUE,
                        peak_price = ?,
                        last_price_update_time = ?
                    WHERE id = ?
                ''', (
                    stop_loss_price,
                    stop_loss_price,
                    entry_price,  # 初始峰值價格 = 進場價格
                    datetime.now().strftime('%H:%M:%S'),
                    position_id
                ))
                
                # 檢查是否有風險管理狀態記錄
                cursor.execute('SELECT id FROM risk_management_states WHERE position_id = ?', (position_id,))
                risk_record = cursor.fetchone()
                
                if risk_record:
                    # 更新現有記錄
                    cursor.execute('''
                        UPDATE risk_management_states 
                        SET peak_price = ?,
                            current_stop_loss = ?,
                            last_update_time = ?,
                            update_reason = '初始停損設定'
                        WHERE position_id = ?
                    ''', (
                        entry_price,
                        stop_loss_price,
                        datetime.now().strftime('%H:%M:%S'),
                        position_id
                    ))
                else:
                    # 創建新記錄
                    cursor.execute('''
                        INSERT INTO risk_management_states 
                        (position_id, peak_price, current_stop_loss, trailing_activated, 
                         protection_activated, last_update_time, update_reason)
                        VALUES (?, ?, ?, FALSE, FALSE, ?, '初始停損設定')
                    ''', (
                        position_id,
                        entry_price,
                        stop_loss_price,
                        datetime.now().strftime('%H:%M:%S')
                    ))
                
                conn.commit()
                return True
                
        except Exception as e:
            logger.error(f"更新資料庫停損資訊失敗: {e}")
            return False
    
    def get_active_stop_losses(self) -> List[StopLossInfo]:
        """取得所有活躍的停損資訊"""
        return [info for info in self.active_stop_losses.values() if info.is_active]
    
    def get_stop_loss_by_position(self, position_id: int) -> Optional[StopLossInfo]:
        """根據部位ID取得停損資訊"""
        return self.active_stop_losses.get(position_id)
    
    def deactivate_stop_loss(self, position_id: int, reason: str = "手動停用"):
        """停用指定部位的停損"""
        if position_id in self.active_stop_losses:
            self.active_stop_losses[position_id].is_active = False
            
            if self.console_enabled:
                print(f"[STOP_LOSS] 🔒 部位 {position_id} 停損已停用: {reason}")
    
    def get_stop_loss_summary(self) -> Dict:
        """取得停損狀態摘要"""
        active_count = len([info for info in self.active_stop_losses.values() if info.is_active])
        total_count = len(self.active_stop_losses)
        
        return {
            'total_stop_losses': total_count,
            'active_stop_losses': active_count,
            'inactive_stop_losses': total_count - active_count
        }
    
    def print_stop_loss_status(self):
        """列印停損狀態 (Console輸出)"""
        if not self.console_enabled:
            return
        
        summary = self.get_stop_loss_summary()
        active_stop_losses = self.get_active_stop_losses()
        
        print(f"[STOP_LOSS] 📊 停損狀態摘要:")
        print(f"[STOP_LOSS]   總計: {summary['total_stop_losses']} 個")
        print(f"[STOP_LOSS]   活躍: {summary['active_stop_losses']} 個")
        print(f"[STOP_LOSS]   停用: {summary['inactive_stop_losses']} 個")
        
        if active_stop_losses:
            print(f"[STOP_LOSS] 🛡️ 活躍停損詳情:")
            for info in active_stop_losses:
                direction_text = "做多" if info.direction == "LONG" else "做空"
                distance = abs(info.entry_price - info.stop_loss_price)
                print(f"[STOP_LOSS]   部位{info.position_id} ({direction_text}): 停損@{info.stop_loss_price} (距離{distance:.1f}點)")


def create_initial_stop_loss_manager(db_manager, console_enabled: bool = True) -> InitialStopLossManager:
    """
    創建初始停損管理器的工廠函數
    
    Args:
        db_manager: 資料庫管理器
        console_enabled: 是否啟用Console日誌
        
    Returns:
        InitialStopLossManager: 停損管理器實例
    """
    return InitialStopLossManager(db_manager, console_enabled)


if __name__ == "__main__":
    # 測試用途
    print("初始停損管理器模組")
    print("請在主程式中調用 create_initial_stop_loss_manager() 函數")
