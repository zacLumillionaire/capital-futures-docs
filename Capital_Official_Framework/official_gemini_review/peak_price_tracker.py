#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
峰值價格追蹤器
負責追蹤和更新峰值價格，支援移動停利機制
"""

import logging
import time
from datetime import datetime
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass

logger = logging.getLogger(__name__)

@dataclass
class PeakPriceUpdate:
    """峰值價格更新資訊"""
    position_id: int
    group_id: int
    direction: str
    old_peak: float
    new_peak: float
    current_price: float
    improvement: float
    update_time: str

class PeakPriceTracker:
    """
    峰值價格追蹤器
    負責追蹤和更新峰值價格
    """
    
    def __init__(self, db_manager, console_enabled: bool = True):
        """
        初始化峰值價格追蹤器
        
        Args:
            db_manager: 資料庫管理器
            console_enabled: 是否啟用Console日誌
        """
        self.db_manager = db_manager
        self.console_enabled = console_enabled
        self.peak_updates: List[PeakPriceUpdate] = []  # 峰值更新歷史
        self.update_callbacks: List = []  # 更新回調函數
        self.last_update_time = 0
        self.update_interval = 0.5  # 更新間隔 (秒)
        
        if self.console_enabled:
            print("[PEAK_TRACKER] ⚙️ 峰值價格追蹤器初始化完成")
    
    def add_update_callback(self, callback):
        """
        添加峰值更新回調函數
        
        Args:
            callback: 回調函數，接收 PeakPriceUpdate 參數
        """
        self.update_callbacks.append(callback)
        if self.console_enabled:
            print(f"[PEAK_TRACKER] 📞 添加更新回調函數: {callback.__name__}")
    
    def update_peak_prices(self, current_price: float, timestamp: str = None) -> List[PeakPriceUpdate]:
        """
        更新峰值價格
        
        Args:
            current_price: 當前價格
            timestamp: 時間戳 (可選)
            
        Returns:
            List[PeakPriceUpdate]: 峰值更新列表
        """
        if timestamp is None:
            timestamp = datetime.now().strftime('%H:%M:%S')
        
        # 頻率控制
        current_time = time.time()
        if current_time - self.last_update_time < self.update_interval:
            return []
        
        self.last_update_time = current_time
        
        try:
            # 取得所有已啟動移動停利的部位
            trailing_positions = self._get_trailing_positions()
            
            if not trailing_positions:
                return []
            
            peak_updates = []
            
            for position in trailing_positions:
                update = self._check_peak_update(position, current_price, timestamp)
                if update:
                    peak_updates.append(update)
            
            # 處理峰值更新
            if peak_updates:
                self._process_peak_updates(peak_updates)
            
            return peak_updates
            
        except Exception as e:
            logger.error(f"更新峰值價格失敗: {e}")
            if self.console_enabled:
                print(f"[PEAK_TRACKER] ❌ 峰值更新失敗: {e}")
            return []
    
    def _get_trailing_positions(self) -> List[Dict]:
        """取得所有已啟動移動停利的部位"""
        try:
            with self.db_manager.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    SELECT pr.*, sg.range_high, sg.range_low
                    FROM position_records pr
                    JOIN strategy_groups sg ON pr.group_id = sg.id
                    WHERE pr.status = 'ACTIVE' 
                      AND pr.trailing_activated = TRUE
                      AND pr.peak_price IS NOT NULL
                    ORDER BY pr.group_id, pr.lot_id
                ''')
                
                rows = cursor.fetchall()
                columns = [description[0] for description in cursor.description]
                return [dict(zip(columns, row)) for row in rows]
                
        except Exception as e:
            logger.error(f"查詢移動停利部位失敗: {e}")
            return []
    
    def _check_peak_update(self, position: Dict, current_price: float, 
                          timestamp: str) -> Optional[PeakPriceUpdate]:
        """
        檢查單個部位的峰值更新
        
        Args:
            position: 部位資料
            current_price: 當前價格
            timestamp: 時間戳
            
        Returns:
            Optional[PeakPriceUpdate]: 峰值更新資訊 (如果有更新)
        """
        position_id = None  # 🔧 修復：初始化變數避免異常處理時未定義錯誤
        try:
            # 🔧 修復：使用正確的鍵名，支援新舊格式
            position_id = position.get('position_pk') or position.get('id')
            if position_id is None:
                logger.error(f"部位資料缺少ID: {position}")
                return None

            direction = position['direction']
            current_peak = position['peak_price']
            # 🔧 修復：使用正確的鍵名，支援新舊格式
            group_id = position.get('group_pk') or position.get('group_id')
            
            # 檢查是否需要更新峰值
            should_update, new_peak = self._should_update_peak(direction, current_peak, current_price)
            
            if should_update:
                improvement = abs(new_peak - current_peak)
                
                if self.console_enabled:
                    print(f"[PEAK_TRACKER] 📈 峰值價格更新!")
                    print(f"[PEAK_TRACKER]   部位ID: {position_id}")
                    print(f"[PEAK_TRACKER]   方向: {direction}")
                    print(f"[PEAK_TRACKER]   舊峰值: {current_peak}")
                    print(f"[PEAK_TRACKER]   新峰值: {new_peak}")
                    print(f"[PEAK_TRACKER]   當前價格: {current_price}")
                    print(f"[PEAK_TRACKER]   改善幅度: {improvement:.1f} 點")
                    print(f"[PEAK_TRACKER]   更新時間: {timestamp}")
                
                return PeakPriceUpdate(
                    position_id=position_id,
                    group_id=group_id,
                    direction=direction,
                    old_peak=current_peak,
                    new_peak=new_peak,
                    current_price=current_price,
                    improvement=improvement,
                    update_time=timestamp
                )
            
            return None
            
        except Exception as e:
            logger.error(f"檢查峰值更新失敗: {e}")
            if self.console_enabled:
                # 🔧 修復：安全地顯示position_id，避免未定義變數錯誤
                position_display = position_id if position_id is not None else "未知"
                print(f"[PEAK_TRACKER] ❌ 部位 {position_display} 峰值檢查失敗: {e}")
            return None
    
    def _should_update_peak(self, direction: str, current_peak: float, 
                          current_price: float) -> Tuple[bool, float]:
        """
        檢查是否應該更新峰值
        
        Args:
            direction: 交易方向
            current_peak: 當前峰值
            current_price: 當前價格
            
        Returns:
            Tuple[bool, float]: (是否更新, 新峰值)
        """
        if direction == "LONG":
            # 做多：價格創新高時更新峰值
            if current_price > current_peak:
                return True, current_price
        elif direction == "SHORT":
            # 做空：價格創新低時更新峰值
            if current_price < current_peak:
                return True, current_price
        
        return False, current_peak
    
    def _process_peak_updates(self, peak_updates: List[PeakPriceUpdate]):
        """
        處理峰值更新
        
        Args:
            peak_updates: 峰值更新列表
        """
        if self.console_enabled:
            print(f"[PEAK_TRACKER] ⚡ 處理 {len(peak_updates)} 個峰值更新")
        
        for update in peak_updates:
            try:
                # 更新資料庫
                self._update_peak_in_database(update)
                
                # 記錄更新歷史
                self.peak_updates.append(update)
                
                # 觸發回調函數
                for callback in self.update_callbacks:
                    try:
                        callback(update)
                    except Exception as e:
                        logger.error(f"峰值更新回調函數執行失敗: {e}")
                        if self.console_enabled:
                            print(f"[PEAK_TRACKER] ❌ 回調函數 {callback.__name__} 執行失敗: {e}")
                
                if self.console_enabled:
                    print(f"[PEAK_TRACKER] ✅ 部位 {update.position_id} 峰值更新完成")
                    
            except Exception as e:
                logger.error(f"處理峰值更新失敗: {e}")
                if self.console_enabled:
                    print(f"[PEAK_TRACKER] ❌ 部位 {update.position_id} 峰值更新失敗: {e}")
    
    def _update_peak_in_database(self, update: PeakPriceUpdate):
        """
        更新資料庫中的峰值價格
        
        Args:
            update: 峰值更新資訊
        """
        try:
            with self.db_manager.get_connection() as conn:
                cursor = conn.cursor()
                
                # 更新 position_records
                cursor.execute('''
                    UPDATE position_records 
                    SET peak_price = ?,
                        last_price_update_time = ?
                    WHERE id = ?
                ''', (
                    update.new_peak,
                    update.update_time,
                    update.position_id
                ))
                
                # 更新 risk_management_states (如果存在)
                cursor.execute('''
                    UPDATE risk_management_states 
                    SET peak_price = ?,
                        last_update_time = ?,
                        update_reason = ?
                    WHERE position_id = ?
                ''', (
                    update.new_peak,
                    update.update_time,
                    f"峰值更新: 改善{update.improvement:.1f}點",
                    update.position_id
                ))
                
                conn.commit()
                
                if self.console_enabled:
                    print(f"[PEAK_TRACKER] 📝 部位 {update.position_id} 峰值已更新至 {update.new_peak}")
                    
        except Exception as e:
            logger.error(f"更新資料庫峰值失敗: {e}")
    
    def get_current_peaks(self) -> Dict[int, float]:
        """取得所有部位的當前峰值"""
        try:
            with self.db_manager.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    SELECT id, peak_price 
                    FROM position_records 
                    WHERE status = 'ACTIVE' 
                      AND trailing_activated = TRUE 
                      AND peak_price IS NOT NULL
                ''')
                
                return {row[0]: row[1] for row in cursor.fetchall()}
                
        except Exception as e:
            logger.error(f"查詢當前峰值失敗: {e}")
            return {}
    
    def get_peak_update_summary(self) -> Dict:
        """取得峰值更新摘要"""
        total_updates = len(self.peak_updates)
        
        if total_updates == 0:
            return {
                'total_updates': 0,
                'average_improvement': 0,
                'max_improvement': 0,
                'callback_count': len(self.update_callbacks)
            }
        
        improvements = [update.improvement for update in self.peak_updates]
        
        return {
            'total_updates': total_updates,
            'average_improvement': sum(improvements) / len(improvements),
            'max_improvement': max(improvements),
            'callback_count': len(self.update_callbacks)
        }
    
    def print_peak_status(self):
        """列印峰值追蹤狀態 (Console輸出)"""
        if not self.console_enabled:
            return
        
        summary = self.get_peak_update_summary()
        current_peaks = self.get_current_peaks()
        
        print(f"[PEAK_TRACKER] 📊 峰值追蹤狀態:")
        print(f"[PEAK_TRACKER]   總更新次數: {summary['total_updates']}")
        print(f"[PEAK_TRACKER]   平均改善: {summary['average_improvement']:.1f} 點")
        print(f"[PEAK_TRACKER]   最大改善: {summary['max_improvement']:.1f} 點")
        print(f"[PEAK_TRACKER]   回調函數: {summary['callback_count']} 個")
        print(f"[PEAK_TRACKER]   追蹤部位: {len(current_peaks)} 個")
        
        if current_peaks:
            print(f"[PEAK_TRACKER] 🔥 當前峰值:")
            for position_id, peak_price in current_peaks.items():
                print(f"[PEAK_TRACKER]   部位{position_id}: 峰值@{peak_price}")
    
    def set_update_interval(self, interval: float):
        """設定更新間隔"""
        self.update_interval = max(0.1, interval)  # 最小0.1秒
        if self.console_enabled:
            print(f"[PEAK_TRACKER] ⏱️ 更新間隔設定為: {self.update_interval} 秒")
    
    def force_update_all_peaks(self, current_price: float) -> List[PeakPriceUpdate]:
        """
        強制更新所有峰值 (忽略時間間隔)
        
        Args:
            current_price: 當前價格
            
        Returns:
            List[PeakPriceUpdate]: 峰值更新列表
        """
        self.last_update_time = 0  # 重置時間，強制更新
        return self.update_peak_prices(current_price)


def create_peak_price_tracker(db_manager, console_enabled: bool = True) -> PeakPriceTracker:
    """
    創建峰值價格追蹤器的工廠函數
    
    Args:
        db_manager: 資料庫管理器
        console_enabled: 是否啟用Console日誌
        
    Returns:
        PeakPriceTracker: 峰值價格追蹤器實例
    """
    return PeakPriceTracker(db_manager, console_enabled)


if __name__ == "__main__":
    # 測試用途
    print("峰值價格追蹤器模組")
    print("請在主程式中調用 create_peak_price_tracker() 函數")
