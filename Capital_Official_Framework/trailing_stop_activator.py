#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
移動停利啟動器
負責15/40/65點分層啟動的移動停利邏輯，對應回測程式的 LotRule
"""

import logging
import time
from datetime import datetime
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass

logger = logging.getLogger(__name__)

@dataclass
class TrailingStopActivation:
    """移動停利啟動資訊"""
    position_id: int
    group_id: int
    lot_number: int
    direction: str
    entry_price: float
    current_price: float
    activation_points: int
    profit_points: float
    activation_time: str
    is_activated: bool = True

class TrailingStopActivator:
    """
    移動停利啟動器
    負責15/40/65點分層啟動的移動停利邏輯
    """
    
    def __init__(self, db_manager, console_enabled: bool = True):
        """
        初始化移動停利啟動器
        
        Args:
            db_manager: 資料庫管理器
            console_enabled: 是否啟用Console日誌
        """
        self.db_manager = db_manager
        self.console_enabled = console_enabled
        self.activated_positions: Dict[int, TrailingStopActivation] = {}  # position_id -> activation
        self.activation_callbacks: List = []  # 啟動回調函數
        
        if self.console_enabled:
            print("[TRAILING] ⚙️ 移動停利啟動器初始化完成")
    
    def add_activation_callback(self, callback):
        """
        添加移動停利啟動回調函數
        
        Args:
            callback: 回調函數，接收 TrailingStopActivation 參數
        """
        self.activation_callbacks.append(callback)
        if self.console_enabled:
            print(f"[TRAILING] 📞 添加啟動回調函數: {callback.__name__}")
    
    def check_trailing_stop_activation(self, current_price: float, timestamp: str = None) -> List[TrailingStopActivation]:
        """
        檢查移動停利啟動條件
        
        Args:
            current_price: 當前價格
            timestamp: 時間戳 (可選)
            
        Returns:
            List[TrailingStopActivation]: 新啟動的移動停利列表
        """
        if timestamp is None:
            timestamp = datetime.now().strftime('%H:%M:%S')
        
        try:
            # 取得所有未啟動移動停利的活躍部位
            eligible_positions = self._get_eligible_positions()
            
            if not eligible_positions:
                return []
            
            new_activations = []
            
            for position in eligible_positions:
                activation = self._check_position_activation(position, current_price, timestamp)
                if activation:
                    new_activations.append(activation)
            
            # 處理新啟動的移動停利
            if new_activations:
                self._process_new_activations(new_activations)
            
            return new_activations
            
        except Exception as e:
            logger.error(f"檢查移動停利啟動失敗: {e}")
            if self.console_enabled:
                print(f"[TRAILING] ❌ 啟動檢查失敗: {e}")
            return []
    
    def _get_eligible_positions(self) -> List[Dict]:
        """取得符合移動停利啟動條件的部位"""
        try:
            with self.db_manager.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    SELECT pr.*, sg.range_high, sg.range_low, sg.direction as group_direction
                    FROM position_records pr
                    JOIN strategy_groups sg ON pr.group_id = sg.group_id AND sg.date = date('now', 'localtime')
                    WHERE pr.status = 'ACTIVE'
                      AND pr.trailing_activated = FALSE
                      AND pr.is_initial_stop = TRUE
                      AND pr.trailing_activation_points IS NOT NULL
                    ORDER BY pr.group_id, pr.lot_id
                ''')
                
                rows = cursor.fetchall()
                columns = [description[0] for description in cursor.description]
                return [dict(zip(columns, row)) for row in rows]
                
        except Exception as e:
            logger.error(f"查詢符合條件的部位失敗: {e}")
            return []
    
    def _check_position_activation(self, position: Dict, current_price: float,
                                 timestamp: str) -> Optional[TrailingStopActivation]:
        """
        檢查單個部位的移動停利啟動

        Args:
            position: 部位資料
            current_price: 當前價格
            timestamp: 時間戳

        Returns:
            Optional[TrailingStopActivation]: 啟動資訊 (如果啟動)
        """
        position_id = None  # 🔧 修復：初始化變數避免異常處理時未定義錯誤
        try:
            # 🔧 修復：使用正確的鍵名，支援新舊格式
            position_id = position.get('position_pk') or position.get('id')
            if position_id is None:
                logger.error(f"部位資料缺少ID: {position}")
                return None

            direction = position['direction']
            entry_price = position['entry_price']
            activation_points = position['trailing_activation_points']
            lot_id = position.get('lot_id', 1)
            # 🔧 修復：使用正確的鍵名，支援新舊格式
            group_id = position.get('group_pk') or position.get('group_id')

            # 計算當前獲利點數
            profit_points = self._calculate_profit_points(direction, entry_price, current_price)

            # 檢查是否達到啟動條件
            if profit_points >= activation_points:
                if self.console_enabled:
                    print(f"[TRAILING] 🎯 移動停利啟動!")
                    print(f"[TRAILING]   部位ID: {position_id} (第{lot_id}口)")
                    print(f"[TRAILING]   方向: {direction}")
                    print(f"[TRAILING]   進場價格: {entry_price}")
                    print(f"[TRAILING]   當前價格: {current_price}")
                    print(f"[TRAILING]   當前獲利: {profit_points:.1f} 點")
                    print(f"[TRAILING]   啟動條件: {activation_points} 點")
                    print(f"[TRAILING]   啟動時間: {timestamp}")

                return TrailingStopActivation(
                    position_id=position_id,
                    group_id=group_id,
                    lot_number=lot_id,
                    direction=direction,
                    entry_price=entry_price,
                    current_price=current_price,
                    activation_points=activation_points,
                    profit_points=profit_points,
                    activation_time=timestamp
                )

            return None

        except Exception as e:
            logger.error(f"檢查部位移動停利啟動失敗: {e}")
            if self.console_enabled:
                # 🔧 修復：安全地顯示position_id，避免未定義變數錯誤
                position_display = position_id if position_id is not None else "未知"
                print(f"[TRAILING] ❌ 部位 {position_display} 移動停利檢查失敗: {e}")
            return None
    
    def _calculate_profit_points(self, direction: str, entry_price: float, current_price: float) -> float:
        """
        計算獲利點數
        
        Args:
            direction: 交易方向
            entry_price: 進場價格
            current_price: 當前價格
            
        Returns:
            float: 獲利點數
        """
        if direction == "LONG":
            return current_price - entry_price
        elif direction == "SHORT":
            return entry_price - current_price
        else:
            return 0.0
    
    def _process_new_activations(self, new_activations: List[TrailingStopActivation]):
        """
        處理新啟動的移動停利
        
        Args:
            new_activations: 新啟動的移動停利列表
        """
        if self.console_enabled:
            print(f"[TRAILING] ⚡ 處理 {len(new_activations)} 個移動停利啟動")
        
        for activation in new_activations:
            try:
                # 更新資料庫
                self._update_position_trailing_status(activation)
                
                # 記錄啟動資訊
                self.activated_positions[activation.position_id] = activation
                
                # 觸發回調函數
                for callback in self.activation_callbacks:
                    try:
                        callback(activation)
                    except Exception as e:
                        logger.error(f"移動停利啟動回調函數執行失敗: {e}")
                        if self.console_enabled:
                            print(f"[TRAILING] ❌ 回調函數 {callback.__name__} 執行失敗: {e}")
                
                if self.console_enabled:
                    print(f"[TRAILING] ✅ 部位 {activation.position_id} 移動停利啟動完成")
                    
            except Exception as e:
                logger.error(f"處理移動停利啟動失敗: {e}")
                if self.console_enabled:
                    print(f"[TRAILING] ❌ 部位 {activation.position_id} 啟動處理失敗: {e}")
    
    def _update_position_trailing_status(self, activation: TrailingStopActivation):
        """
        更新部位移動停利狀態
        
        Args:
            activation: 啟動資訊
        """
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
                    activation.current_price,  # 設定初始峰值價格
                    activation.activation_time,
                    activation.position_id
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
                    activation.current_price,
                    activation.activation_time,
                    f"移動停利啟動 ({activation.activation_points}點)",
                    activation.position_id
                ))
                
                # 記錄啟動事件
                event_id = f"trailing_activation_{activation.position_id}_{int(time.time())}"
                cursor.execute('''
                    INSERT INTO exit_events 
                    (event_id, position_id, group_id, event_type, trigger_price, 
                     trigger_time, trigger_reason, execution_status)
                    VALUES (?, ?, ?, 'TRAILING_ACTIVATION', ?, ?, ?, 'EXECUTED')
                ''', (
                    event_id,
                    activation.position_id,
                    activation.group_id,
                    activation.current_price,
                    activation.activation_time,
                    f"移動停利啟動: {activation.activation_points}點獲利"
                ))
                
                conn.commit()
                
                if self.console_enabled:
                    print(f"[TRAILING] 📝 部位 {activation.position_id} 移動停利狀態已更新")
                    
        except Exception as e:
            logger.error(f"更新移動停利狀態失敗: {e}")
    
    def get_activated_positions(self) -> List[TrailingStopActivation]:
        """取得所有已啟動移動停利的部位"""
        return list(self.activated_positions.values())
    
    def get_activation_by_position(self, position_id: int) -> Optional[TrailingStopActivation]:
        """根據部位ID取得啟動資訊"""
        return self.activated_positions.get(position_id)
    
    def get_activation_summary(self) -> Dict:
        """取得啟動狀態摘要"""
        activations = self.get_activated_positions()
        
        # 按啟動點位分組統計
        by_points = {}
        for activation in activations:
            points = activation.activation_points
            if points not in by_points:
                by_points[points] = 0
            by_points[points] += 1
        
        return {
            'total_activations': len(activations),
            'by_activation_points': by_points,
            'callback_count': len(self.activation_callbacks)
        }
    
    def print_activation_status(self):
        """列印啟動狀態 (Console輸出)"""
        if not self.console_enabled:
            return
        
        summary = self.get_activation_summary()
        activations = self.get_activated_positions()
        
        print(f"[TRAILING] 📊 移動停利啟動狀態:")
        print(f"[TRAILING]   總啟動數: {summary['total_activations']} 個")
        print(f"[TRAILING]   回調函數: {summary['callback_count']} 個")
        
        if summary['by_activation_points']:
            print(f"[TRAILING] 🎯 按啟動點位分組:")
            for points, count in sorted(summary['by_activation_points'].items()):
                print(f"[TRAILING]   {points}點啟動: {count} 個部位")
        
        if activations:
            print(f"[TRAILING] 🔥 已啟動移動停利詳情:")
            for activation in activations:
                direction_text = "做多" if activation.direction == "LONG" else "做空"
                print(f"[TRAILING]   部位{activation.position_id} ({direction_text}): {activation.activation_points}點啟動, 獲利{activation.profit_points:.1f}點")


def create_trailing_stop_activator(db_manager, console_enabled: bool = True) -> TrailingStopActivator:
    """
    創建移動停利啟動器的工廠函數
    
    Args:
        db_manager: 資料庫管理器
        console_enabled: 是否啟用Console日誌
        
    Returns:
        TrailingStopActivator: 移動停利啟動器實例
    """
    return TrailingStopActivator(db_manager, console_enabled)


if __name__ == "__main__":
    # 測試用途
    print("移動停利啟動器模組")
    print("請在主程式中調用 create_trailing_stop_activator() 函數")
