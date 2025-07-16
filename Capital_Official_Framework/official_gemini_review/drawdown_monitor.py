#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
20%回撤監控器
負責監控20%回撤觸發條件，執行移動停利平倉
"""

import logging
import time
from datetime import datetime
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass

logger = logging.getLogger(__name__)

@dataclass
class DrawdownTrigger:
    """回撤觸發資訊"""
    position_id: int
    group_id: int
    direction: str
    peak_price: float
    current_price: float
    drawdown_ratio: float
    drawdown_points: float
    pullback_threshold: float
    trigger_time: str
    trigger_reason: str

class DrawdownMonitor:
    """
    20%回撤監控器
    負責監控20%回撤觸發條件
    """
    
    def __init__(self, db_manager, console_enabled: bool = True):
        """
        初始化回撤監控器
        
        Args:
            db_manager: 資料庫管理器
            console_enabled: 是否啟用Console日誌
        """
        self.db_manager = db_manager
        self.console_enabled = console_enabled
        self.drawdown_callbacks: List = []  # 回撤觸發回調函數
        self.triggered_positions: Dict[int, DrawdownTrigger] = {}  # 已觸發的部位
        self.last_check_time = 0
        self.check_interval = 1.0  # 檢查間隔 (秒)
        
        if self.console_enabled:
            print("[DRAWDOWN] ⚙️ 20%回撤監控器初始化完成")
    
    def add_drawdown_callback(self, callback):
        """
        添加回撤觸發回調函數
        
        Args:
            callback: 回調函數，接收 DrawdownTrigger 參數
        """
        self.drawdown_callbacks.append(callback)
        if self.console_enabled:
            print(f"[DRAWDOWN] 📞 添加回撤回調函數: {callback.__name__}")
    
    def monitor_drawdown_triggers(self, current_price: float, timestamp: str = None) -> List[DrawdownTrigger]:
        """
        監控回撤觸發條件
        
        Args:
            current_price: 當前價格
            timestamp: 時間戳 (可選)
            
        Returns:
            List[DrawdownTrigger]: 觸發的回撤列表
        """
        if timestamp is None:
            timestamp = datetime.now().strftime('%H:%M:%S')
        
        # 檢查頻率控制
        current_time = time.time()
        if current_time - self.last_check_time < self.check_interval:
            return []
        
        self.last_check_time = current_time
        
        try:
            # 取得所有已啟動移動停利的部位
            trailing_positions = self._get_trailing_positions()
            
            if not trailing_positions:
                return []
            
            triggered_drawdowns = []
            
            for position in trailing_positions:
                trigger = self._check_drawdown_trigger(position, current_price, timestamp)
                if trigger:
                    triggered_drawdowns.append(trigger)
            
            # 處理觸發的回撤
            if triggered_drawdowns:
                self._process_triggered_drawdowns(triggered_drawdowns)
            
            return triggered_drawdowns
            
        except Exception as e:
            logger.error(f"回撤監控失敗: {e}")
            if self.console_enabled:
                print(f"[DRAWDOWN] ❌ 回撤監控失敗: {e}")
            return []
    
    def _get_trailing_positions(self) -> List[Dict]:
        """取得所有已啟動移動停利的部位 - 🔧 修復：正確關聯策略組"""
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
                      AND pr.trailing_activated = TRUE
                      AND pr.peak_price IS NOT NULL
                      AND pr.trailing_pullback_ratio IS NOT NULL
                    ORDER BY pr.group_id, pr.lot_id
                ''', (date.today().isoformat(),))

                rows = cursor.fetchall()
                columns = [description[0] for description in cursor.description]
                return [dict(zip(columns, row)) for row in rows]

        except Exception as e:
            logger.error(f"查詢移動停利部位失敗: {e}")
            return []
    
    def _check_drawdown_trigger(self, position: Dict, current_price: float, 
                              timestamp: str) -> Optional[DrawdownTrigger]:
        """
        檢查單個部位的回撤觸發
        
        Args:
            position: 部位資料
            current_price: 當前價格
            timestamp: 時間戳
            
        Returns:
            Optional[DrawdownTrigger]: 回撤觸發資訊 (如果觸發)
        """
        position_id = None  # 🔧 修復：初始化變數避免異常處理時未定義錯誤
        try:
            # 🔧 修復：使用正確的鍵名，支援新舊格式
            position_id = position.get('position_pk') or position.get('id')
            if position_id is None:
                logger.error(f"部位資料缺少ID: {position}")
                return None

            direction = position['direction']
            peak_price = position['peak_price']
            pullback_ratio = position.get('trailing_pullback_ratio', 0.20)  # 預設20%
            # 🔧 修復：使用正確的鍵名，支援新舊格式
            group_id = position.get('group_pk') or position.get('group_id')
            
            # 檢查是否已經觸發過
            if position_id in self.triggered_positions:
                return None
            
            # 計算當前回撤
            is_triggered, drawdown_ratio, drawdown_points = self._calculate_drawdown(
                direction, peak_price, current_price, pullback_ratio
            )
            
            if is_triggered:
                trigger_reason = f"{direction}部位從峰值{peak_price}回撤{drawdown_ratio:.1%}"
                
                if self.console_enabled:
                    print(f"[DRAWDOWN] 🚨 20%回撤觸發!")
                    print(f"[DRAWDOWN]   部位ID: {position_id}")
                    print(f"[DRAWDOWN]   方向: {direction}")
                    print(f"[DRAWDOWN]   峰值價格: {peak_price}")
                    print(f"[DRAWDOWN]   當前價格: {current_price}")
                    print(f"[DRAWDOWN]   回撤比例: {drawdown_ratio:.1%}")
                    print(f"[DRAWDOWN]   回撤點數: {drawdown_points:.1f} 點")
                    print(f"[DRAWDOWN]   觸發閾值: {pullback_ratio:.1%}")
                    print(f"[DRAWDOWN]   觸發時間: {timestamp}")
                
                return DrawdownTrigger(
                    position_id=position_id,
                    group_id=group_id,
                    direction=direction,
                    peak_price=peak_price,
                    current_price=current_price,
                    drawdown_ratio=drawdown_ratio,
                    drawdown_points=drawdown_points,
                    pullback_threshold=pullback_ratio,
                    trigger_time=timestamp,
                    trigger_reason=trigger_reason
                )
            
            return None
            
        except Exception as e:
            logger.error(f"檢查回撤觸發失敗: {e}")
            if self.console_enabled:
                # 🔧 修復：安全地顯示position_id，避免未定義變數錯誤
                position_display = position_id if position_id is not None else "未知"
                print(f"[DRAWDOWN] ❌ 部位 {position_display} 回撤檢查失敗: {e}")
            return None
    
    def _calculate_drawdown(self, direction: str, peak_price: float, current_price: float, 
                          pullback_ratio: float) -> Tuple[bool, float, float]:
        """
        計算回撤比例和是否觸發
        
        Args:
            direction: 交易方向
            peak_price: 峰值價格
            current_price: 當前價格
            pullback_ratio: 回撤比例閾值
            
        Returns:
            Tuple[bool, float, float]: (是否觸發, 回撤比例, 回撤點數)
        """
        if direction == "LONG":
            # 做多：從峰值下跌
            if current_price < peak_price:
                drawdown_points = peak_price - current_price
                drawdown_ratio = drawdown_points / peak_price
                return drawdown_ratio >= pullback_ratio, drawdown_ratio, drawdown_points
        elif direction == "SHORT":
            # 做空：從峰值上漲
            if current_price > peak_price:
                drawdown_points = current_price - peak_price
                drawdown_ratio = drawdown_points / peak_price
                return drawdown_ratio >= pullback_ratio, drawdown_ratio, drawdown_points
        
        return False, 0.0, 0.0
    
    def _process_triggered_drawdowns(self, triggered_drawdowns: List[DrawdownTrigger]):
        """
        處理觸發的回撤
        
        Args:
            triggered_drawdowns: 觸發的回撤列表
        """
        if self.console_enabled:
            print(f"[DRAWDOWN] ⚡ 處理 {len(triggered_drawdowns)} 個回撤觸發")
        
        for trigger in triggered_drawdowns:
            try:
                # 記錄回撤事件
                self._record_drawdown_event(trigger)
                
                # 記錄已觸發的部位
                self.triggered_positions[trigger.position_id] = trigger
                
                # 觸發回調函數
                for callback in self.drawdown_callbacks:
                    try:
                        callback(trigger)
                    except Exception as e:
                        logger.error(f"回撤回調函數執行失敗: {e}")
                        if self.console_enabled:
                            print(f"[DRAWDOWN] ❌ 回調函數 {callback.__name__} 執行失敗: {e}")
                
                if self.console_enabled:
                    print(f"[DRAWDOWN] ✅ 部位 {trigger.position_id} 回撤處理完成")
                    
            except Exception as e:
                logger.error(f"處理回撤觸發失敗: {e}")
                if self.console_enabled:
                    print(f"[DRAWDOWN] ❌ 部位 {trigger.position_id} 回撤處理失敗: {e}")
    
    def _record_drawdown_event(self, trigger: DrawdownTrigger):
        """
        記錄回撤事件到資料庫
        
        Args:
            trigger: 回撤觸發資訊
        """
        try:
            event_id = f"drawdown_trigger_{trigger.position_id}_{int(time.time())}"
            
            with self.db_manager.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    INSERT INTO exit_events 
                    (event_id, position_id, group_id, event_type, trigger_price, 
                     trigger_time, trigger_reason, execution_status)
                    VALUES (?, ?, ?, 'TRAILING_STOP', ?, ?, ?, 'PENDING')
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
                    print(f"[DRAWDOWN] 📝 回撤事件已記錄: {event_id}")
                    
        except Exception as e:
            logger.error(f"記錄回撤事件失敗: {e}")
    
    def get_triggered_drawdowns(self) -> List[DrawdownTrigger]:
        """取得所有已觸發的回撤"""
        return list(self.triggered_positions.values())
    
    def get_drawdown_by_position(self, position_id: int) -> Optional[DrawdownTrigger]:
        """根據部位ID取得回撤觸發資訊"""
        return self.triggered_positions.get(position_id)
    
    def get_monitoring_status(self) -> Dict:
        """取得監控狀態"""
        try:
            trailing_positions = self._get_trailing_positions()
            triggered_count = len(self.triggered_positions)
            
            return {
                'monitoring_positions': len(trailing_positions),
                'triggered_positions': triggered_count,
                'pending_positions': len(trailing_positions) - triggered_count,
                'last_check_time': datetime.fromtimestamp(self.last_check_time).strftime('%H:%M:%S') if self.last_check_time > 0 else "未開始",
                'check_interval': self.check_interval,
                'callback_count': len(self.drawdown_callbacks)
            }
            
        except Exception as e:
            logger.error(f"取得監控狀態失敗: {e}")
            return {}
    
    def print_monitoring_status(self):
        """列印監控狀態 (Console輸出)"""
        if not self.console_enabled:
            return
        
        status = self.get_monitoring_status()
        triggered_drawdowns = self.get_triggered_drawdowns()
        
        print(f"[DRAWDOWN] 📊 回撤監控狀態:")
        print(f"[DRAWDOWN]   監控部位: {status.get('monitoring_positions', 0)} 個")
        print(f"[DRAWDOWN]   已觸發: {status.get('triggered_positions', 0)} 個")
        print(f"[DRAWDOWN]   待監控: {status.get('pending_positions', 0)} 個")
        print(f"[DRAWDOWN]   最後檢查: {status.get('last_check_time', '未開始')}")
        print(f"[DRAWDOWN]   檢查間隔: {status.get('check_interval', 0)} 秒")
        print(f"[DRAWDOWN]   回調函數: {status.get('callback_count', 0)} 個")
        
        if triggered_drawdowns:
            print(f"[DRAWDOWN] 🔥 已觸發回撤詳情:")
            for trigger in triggered_drawdowns:
                direction_text = "做多" if trigger.direction == "LONG" else "做空"
                print(f"[DRAWDOWN]   部位{trigger.position_id} ({direction_text}): 峰值{trigger.peak_price} → 當前{trigger.current_price} (回撤{trigger.drawdown_ratio:.1%})")
    
    def set_check_interval(self, interval: float):
        """設定檢查間隔"""
        self.check_interval = max(0.1, interval)  # 最小0.1秒
        if self.console_enabled:
            print(f"[DRAWDOWN] ⏱️ 檢查間隔設定為: {self.check_interval} 秒")
    
    def force_check_all_positions(self, current_price: float) -> List[DrawdownTrigger]:
        """
        強制檢查所有部位 (忽略時間間隔)
        
        Args:
            current_price: 當前價格
            
        Returns:
            List[DrawdownTrigger]: 觸發的回撤列表
        """
        self.last_check_time = 0  # 重置時間，強制檢查
        return self.monitor_drawdown_triggers(current_price)


def create_drawdown_monitor(db_manager, console_enabled: bool = True) -> DrawdownMonitor:
    """
    創建20%回撤監控器的工廠函數
    
    Args:
        db_manager: 資料庫管理器
        console_enabled: 是否啟用Console日誌
        
    Returns:
        DrawdownMonitor: 回撤監控器實例
    """
    return DrawdownMonitor(db_manager, console_enabled)


if __name__ == "__main__":
    # 測試用途
    print("20%回撤監控器模組")
    print("請在主程式中調用 create_drawdown_monitor() 函數")
