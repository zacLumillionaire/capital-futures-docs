#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
停損監控器
監控停損點突破和觸發條件，執行停損平倉
"""

import logging
import time
from datetime import datetime
from typing import Dict, List, Optional, Callable
from dataclasses import dataclass

logger = logging.getLogger(__name__)

@dataclass
class StopLossTrigger:
    """停損觸發資訊 - 🔧 任務2：擴展為完整數據載體"""
    position_id: int
    group_id: int
    direction: str
    current_price: float
    stop_loss_price: float
    trigger_time: str
    trigger_reason: str
    breach_amount: float  # 突破金額

    # 🔧 任務2：新增完整部位信息，避免執行器查詢數據庫
    entry_price: Optional[float] = None  # 進場價格（來自內存）
    peak_price: Optional[float] = None   # 峰值價格（移動停利用）
    quantity: int = 1                    # 部位數量
    lot_id: int = 1                      # 口數ID
    range_high: Optional[float] = None   # 區間上限
    range_low: Optional[float] = None    # 區間下限

class StopLossMonitor:
    """
    停損監控器
    監控停損點突破和觸發條件
    """
    
    def __init__(self, db_manager, console_enabled: bool = True):
        """
        初始化停損監控器
        
        Args:
            db_manager: 資料庫管理器
            console_enabled: 是否啟用Console日誌
        """
        self.db_manager = db_manager
        self.console_enabled = console_enabled
        self.stop_loss_callbacks: List[Callable] = []  # 停損觸發回調函數
        self.last_check_time = 0
        self.check_interval = 1.0  # 檢查間隔 (秒)
        
        if self.console_enabled:
            print("[STOP_MONITOR] ⚙️ 停損監控器初始化完成")
    
    def add_stop_loss_callback(self, callback: Callable):
        """
        添加停損觸發回調函數
        
        Args:
            callback: 回調函數，接收 StopLossTrigger 參數
        """
        self.stop_loss_callbacks.append(callback)
        if self.console_enabled:
            print(f"[STOP_MONITOR] 📞 添加停損回調函數: {callback.__name__}")
    
    def monitor_stop_loss_breach(self, current_price: float, timestamp: str = None) -> List[StopLossTrigger]:
        """
        監控停損點突破
        
        Args:
            current_price: 當前價格
            timestamp: 時間戳 (可選)
            
        Returns:
            List[StopLossTrigger]: 觸發的停損列表
        """
        if timestamp is None:
            timestamp = datetime.now().strftime('%H:%M:%S')
        
        # 檢查頻率控制
        current_time = time.time()
        if current_time - self.last_check_time < self.check_interval:
            return []
        
        self.last_check_time = current_time
        
        try:
            # 取得所有活躍的停損部位
            active_positions = self._get_active_stop_loss_positions()
            
            if not active_positions:
                return []
            
            triggered_stops = []
            
            for position in active_positions:
                trigger = self._check_position_stop_loss(position, current_price, timestamp)
                if trigger:
                    triggered_stops.append(trigger)
            
            # 處理觸發的停損
            if triggered_stops:
                self._process_triggered_stops(triggered_stops)
            
            return triggered_stops
            
        except Exception as e:
            logger.error(f"停損監控失敗: {e}")
            if self.console_enabled:
                print(f"[STOP_MONITOR] ❌ 停損監控失敗: {e}")
            return []
    
    def _get_active_stop_loss_positions(self) -> List[Dict]:
        """取得所有活躍的停損部位 - 🔧 修復：正確關聯策略組"""
        try:
            from datetime import date
            with self.db_manager.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    SELECT pr.*, sg.range_high, sg.range_low
                    FROM position_records pr
                    JOIN (
                        SELECT * FROM strategy_groups
                        WHERE date = ?
                        ORDER BY id DESC
                    ) sg ON pr.group_id = sg.group_id
                    WHERE pr.status = 'ACTIVE'
                      AND pr.current_stop_loss IS NOT NULL
                      AND pr.is_initial_stop = TRUE
                    ORDER BY pr.group_id, pr.lot_id
                ''', (date.today().isoformat(),))

                rows = cursor.fetchall()
                columns = [description[0] for description in cursor.description]
                return [dict(zip(columns, row)) for row in rows]

        except Exception as e:
            logger.error(f"查詢活躍停損部位失敗: {e}")
            return []
    
    def _check_position_stop_loss(self, position: Dict, current_price: float,
                                timestamp: str) -> Optional[StopLossTrigger]:
        """
        檢查單個部位的停損觸發

        Args:
            position: 部位資料
            current_price: 當前價格
            timestamp: 時間戳

        Returns:
            Optional[StopLossTrigger]: 停損觸發資訊 (如果觸發)
        """
        position_id = None  # 🔧 修復：初始化變數避免異常處理時未定義錯誤
        try:
            # 🔧 修復：使用正確的鍵名，支援新舊格式
            position_id = position.get('position_pk') or position.get('id')
            if position_id is None:
                logger.error(f"部位資料缺少ID: {position}")
                return None

            direction = position['direction']
            stop_loss_price = position['current_stop_loss']
            # 🔧 修復：使用正確的鍵名，支援新舊格式
            group_id = position.get('group_pk') or position.get('group_id')

            # 檢查停損觸發條件
            is_triggered, breach_amount = self._is_stop_loss_triggered(
                direction, current_price, stop_loss_price
            )

            if is_triggered:
                trigger_reason = f"{direction}部位價格突破停損點"

                if self.console_enabled:
                    print(f"[STOP_MONITOR] 🚨 停損觸發!")
                    print(f"[STOP_MONITOR]   部位ID: {position_id}")
                    print(f"[STOP_MONITOR]   方向: {direction}")
                    print(f"[STOP_MONITOR]   當前價格: {current_price}")
                    print(f"[STOP_MONITOR]   停損價格: {stop_loss_price}")
                    print(f"[STOP_MONITOR]   突破金額: {breach_amount:.1f} 點")
                    print(f"[STOP_MONITOR]   觸發時間: {timestamp}")

                return StopLossTrigger(
                    position_id=position_id,
                    group_id=group_id,
                    direction=direction,
                    current_price=current_price,
                    stop_loss_price=stop_loss_price,
                    trigger_time=timestamp,
                    trigger_reason=trigger_reason,
                    breach_amount=breach_amount
                )

            return None

        except Exception as e:
            logger.error(f"檢查部位停損失敗: {e}")
            if self.console_enabled:
                # 🔧 修復：安全地顯示position_id，避免未定義變數錯誤
                position_display = position_id if position_id is not None else "未知"
                print(f"[STOP_MONITOR] ❌ 部位 {position_display} 停損檢查失敗: {e}")
            return None
    
    def _is_stop_loss_triggered(self, direction: str, current_price: float, 
                              stop_loss_price: float) -> tuple[bool, float]:
        """
        檢查停損是否觸發
        
        Args:
            direction: 交易方向
            current_price: 當前價格
            stop_loss_price: 停損價格
            
        Returns:
            tuple[bool, float]: (是否觸發, 突破金額)
        """
        if direction == "LONG":
            # 做多：價格跌破停損點
            if current_price <= stop_loss_price:
                breach_amount = stop_loss_price - current_price
                return True, breach_amount
        elif direction == "SHORT":
            # 做空：價格漲破停損點
            if current_price >= stop_loss_price:
                breach_amount = current_price - stop_loss_price
                return True, breach_amount
        
        return False, 0.0
    
    def _process_triggered_stops(self, triggered_stops: List[StopLossTrigger]):
        """
        處理觸發的停損
        
        Args:
            triggered_stops: 觸發的停損列表
        """
        if self.console_enabled:
            print(f"[STOP_MONITOR] ⚡ 處理 {len(triggered_stops)} 個停損觸發")
        
        for trigger in triggered_stops:
            try:
                # 記錄停損事件
                self._record_stop_loss_event(trigger)
                
                # 觸發回調函數
                for callback in self.stop_loss_callbacks:
                    try:
                        callback(trigger)
                    except Exception as e:
                        logger.error(f"停損回調函數執行失敗: {e}")
                        if self.console_enabled:
                            print(f"[STOP_MONITOR] ❌ 回調函數 {callback.__name__} 執行失敗: {e}")
                
                if self.console_enabled:
                    print(f"[STOP_MONITOR] ✅ 部位 {trigger.position_id} 停損處理完成")
                    
            except Exception as e:
                logger.error(f"處理停損觸發失敗: {e}")
                if self.console_enabled:
                    print(f"[STOP_MONITOR] ❌ 部位 {trigger.position_id} 停損處理失敗: {e}")
    
    def _record_stop_loss_event(self, trigger: StopLossTrigger):
        """
        記錄停損事件到資料庫
        
        Args:
            trigger: 停損觸發資訊
        """
        try:
            event_id = f"stop_loss_{trigger.position_id}_{int(time.time())}"
            
            with self.db_manager.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    INSERT INTO exit_events 
                    (event_id, position_id, group_id, event_type, trigger_price, 
                     trigger_time, trigger_reason, execution_status)
                    VALUES (?, ?, ?, 'INITIAL_STOP', ?, ?, ?, 'PENDING')
                ''', (
                    event_id,
                    trigger.position_id,
                    trigger.group_id,
                    trigger.current_price,
                    trigger.trigger_time,
                    trigger.trigger_reason
                ))
                
                conn.commit()
                
                if self.console_enabled:
                    print(f"[STOP_MONITOR] 📝 停損事件已記錄: {event_id}")
                    
        except Exception as e:
            logger.error(f"記錄停損事件失敗: {e}")
    
    def get_monitoring_status(self) -> Dict:
        """取得監控狀態"""
        try:
            active_positions = self._get_active_stop_loss_positions()
            
            return {
                'monitoring_positions': len(active_positions),
                'last_check_time': datetime.fromtimestamp(self.last_check_time).strftime('%H:%M:%S') if self.last_check_time > 0 else "未開始",
                'check_interval': self.check_interval,
                'callback_count': len(self.stop_loss_callbacks)
            }
            
        except Exception as e:
            logger.error(f"取得監控狀態失敗: {e}")
            return {}
    
    def print_monitoring_status(self):
        """列印監控狀態 (Console輸出)"""
        if not self.console_enabled:
            return
        
        status = self.get_monitoring_status()
        
        print(f"[STOP_MONITOR] 📊 停損監控狀態:")
        print(f"[STOP_MONITOR]   監控部位: {status.get('monitoring_positions', 0)} 個")
        print(f"[STOP_MONITOR]   最後檢查: {status.get('last_check_time', '未開始')}")
        print(f"[STOP_MONITOR]   檢查間隔: {status.get('check_interval', 0)} 秒")
        print(f"[STOP_MONITOR]   回調函數: {status.get('callback_count', 0)} 個")
    
    def set_check_interval(self, interval: float):
        """設定檢查間隔"""
        self.check_interval = max(0.1, interval)  # 最小0.1秒
        if self.console_enabled:
            print(f"[STOP_MONITOR] ⏱️ 檢查間隔設定為: {self.check_interval} 秒")
    
    def force_check_all_positions(self, current_price: float) -> List[StopLossTrigger]:
        """
        強制檢查所有部位 (忽略時間間隔)
        
        Args:
            current_price: 當前價格
            
        Returns:
            List[StopLossTrigger]: 觸發的停損列表
        """
        self.last_check_time = 0  # 重置時間，強制檢查
        return self.monitor_stop_loss_breach(current_price)


def create_stop_loss_monitor(db_manager, console_enabled: bool = True) -> StopLossMonitor:
    """
    創建停損監控器的工廠函數
    
    Args:
        db_manager: 資料庫管理器
        console_enabled: 是否啟用Console日誌
        
    Returns:
        StopLossMonitor: 停損監控器實例
    """
    return StopLossMonitor(db_manager, console_enabled)


if __name__ == "__main__":
    # 測試用途
    print("停損監控器模組")
    print("請在主程式中調用 create_stop_loss_monitor() 函數")
