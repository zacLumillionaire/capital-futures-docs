#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
信號偵測模組
負責開盤區間監控和突破信號偵測
"""

from datetime import datetime, time
from decimal import Decimal
from typing import Optional, Dict, List, Tuple
import logging

logger = logging.getLogger(__name__)

class KBarData:
    """K線資料結構"""
    def __init__(self, start_time: datetime):
        self.start_time = start_time
        self.end_time = None
        self.open_price = None
        self.high_price = None
        self.low_price = None
        self.close_price = None
        self.volume = 0
        self.tick_count = 0
        
    def update_tick(self, price: float, volume: int = 0, timestamp: datetime = None):
        """更新tick資料"""
        if self.open_price is None:
            self.open_price = price
        
        if self.high_price is None or price > self.high_price:
            self.high_price = price
            
        if self.low_price is None or price < self.low_price:
            self.low_price = price
            
        self.close_price = price
        self.volume += volume
        self.tick_count += 1
        
        if timestamp:
            self.end_time = timestamp
    
    def is_complete(self) -> bool:
        """檢查K線是否完整"""
        return all([
            self.open_price is not None,
            self.high_price is not None,
            self.low_price is not None,
            self.close_price is not None
        ])
    
    def to_dict(self) -> Dict:
        """轉換為字典格式"""
        return {
            'start_time': self.start_time.isoformat(),
            'end_time': self.end_time.isoformat() if self.end_time else None,
            'open': self.open_price,
            'high': self.high_price,
            'low': self.low_price,
            'close': self.close_price,
            'volume': self.volume,
            'tick_count': self.tick_count
        }

class OpeningRangeDetector:
    """開盤區間偵測器 - 監控指定時間的兩根K棒"""

    def __init__(self, start_time=None, end_time=None):
        # 預設為08:46-08:47，但可以動態設定
        self.range_start_time = start_time or time(8, 46, 0)
        self.range_end_time = end_time or time(8, 47, 59)
        
        # K線資料
        self.kbar_846 = None  # 08:46-08:47 K線
        self.kbar_847 = None  # 08:47-08:48 K線
        self.current_kbar = None
        
        # 區間資料
        self.range_high = None
        self.range_low = None
        self.range_complete = False
        
        # 狀態追蹤
        self.monitoring_active = False
        self.last_minute = None
        
        logger.info("🔍 開盤區間偵測器已初始化")

    def update_time_range(self, start_time: time, end_time: time):
        """更新監控時間範圍"""
        self.range_start_time = start_time
        self.range_end_time = end_time
        logger.info(f"🕐 更新監控時間: {start_time.strftime('%H:%M')} ~ {end_time.strftime('%H:%M')}")

    def start_monitoring(self):
        """開始監控開盤區間"""
        self.monitoring_active = True
        self.reset_daily_data()
        logger.info("🔍 開始監控開盤區間 (08:46-08:47)")
    
    def stop_monitoring(self):
        """停止監控"""
        self.monitoring_active = False
        logger.info("🔍 停止監控開盤區間")
    
    def reset_daily_data(self):
        """重置每日資料"""
        self.kbar_846 = None
        self.kbar_847 = None
        self.current_kbar = None
        self.range_high = None
        self.range_low = None
        self.range_complete = False
        self.last_minute = None
        logger.debug("🔄 重置開盤區間資料")
    
    def process_tick(self, price: float, volume: int = 0, timestamp: datetime = None) -> bool:
        """
        處理即時tick資料
        
        Args:
            price: 價格
            volume: 成交量
            timestamp: 時間戳記
            
        Returns:
            是否更新了區間資料
        """
        if not self.monitoring_active:
            return False
        
        if timestamp is None:
            timestamp = datetime.now()
        
        current_time = timestamp.time()
        
        # 檢查是否在監控時間內
        if not (self.range_start_time <= current_time <= self.range_end_time):
            return False
        
        # 判斷當前分鐘
        current_minute = timestamp.replace(second=0, microsecond=0)
        
        # 如果分鐘改變，切換K線
        if self.last_minute != current_minute:
            self._switch_kbar(current_minute)
            self.last_minute = current_minute
        
        # 更新當前K線
        if self.current_kbar:
            self.current_kbar.update_tick(price, volume, timestamp)
            
            # 檢查是否完成兩根K線
            if not self.range_complete:
                self._check_range_completion(timestamp)
        
        return True
    
    def _switch_kbar(self, minute_time: datetime):
        """切換K線"""
        current_time = minute_time.time()

        # 檢查是否為第一分鐘（開始時間）
        if current_time.hour == self.range_start_time.hour and current_time.minute == self.range_start_time.minute:
            # 第一分鐘 K線
            self.kbar_846 = KBarData(minute_time)
            self.current_kbar = self.kbar_846
            logger.debug(f"📊 開始第一分鐘 K線 ({current_time.strftime('%H:%M')})")

        elif (current_time.hour == self.range_start_time.hour and current_time.minute == self.range_start_time.minute + 1) or \
             (self.range_start_time.minute == 59 and current_time.hour == self.range_start_time.hour + 1 and current_time.minute == 0):
            # 第二分鐘 K線
            self.kbar_847 = KBarData(minute_time)
            self.current_kbar = self.kbar_847
            logger.debug(f"📊 開始第二分鐘 K線 ({current_time.strftime('%H:%M')})")

        else:
            self.current_kbar = None
    
    def _check_range_completion(self, timestamp: datetime):
        """檢查區間是否完成"""
        current_time = timestamp.time()

        # 當前時間超過監控範圍時檢查是否完成
        if current_time > self.range_end_time and not self.range_complete:
            self._try_complete_range()

        # 也在監控時間內檢查是否已經有足夠資料
        elif self.range_start_time <= current_time <= self.range_end_time and not self.range_complete:
            # 如果已經有兩根K線且都有資料，可以嘗試完成
            if self.kbar_846 and self.kbar_847:
                if (self.kbar_846.tick_count > 10 and self.kbar_847.tick_count > 10):
                    logger.info("🎯 檢測到足夠的K線資料，嘗試完成區間計算")
                    self._try_complete_range()

    def _try_complete_range(self):
        """嘗試完成區間計算"""
        if self.range_complete:
            return

        if self.kbar_846 and self.kbar_847:
            if self.kbar_846.is_complete() and self.kbar_847.is_complete():
                self._calculate_range()
            elif self.kbar_846.tick_count > 0 and self.kbar_847.tick_count > 0:
                # 即使K線未標記為完成，但有資料就可以計算
                logger.info("🎯 使用現有K線資料計算區間")
                self._calculate_range()
            elif self.kbar_846 and self.kbar_846.tick_count > 0:
                # 如果只有第一根K線有資料，使用單根K線計算區間
                logger.warning("⚠️ 只有第一根K線有資料，使用單根K線計算區間")
                self.range_high = self.kbar_846.high_price
                self.range_low = self.kbar_846.low_price
                self.range_complete = True
                logger.info(f"🎯 單根K線區間: 高點{self.range_high} 低點{self.range_low}")
        elif self.kbar_846 and self.kbar_846.tick_count > 0:
            # 只有第一根K線
            logger.warning("⚠️ 只有第一根K線，使用單根K線計算區間")
            self.range_high = self.kbar_846.high_price
            self.range_low = self.kbar_846.low_price
            self.range_complete = True
            logger.info(f"🎯 單根K線區間: 高點{self.range_high} 低點{self.range_low}")
    
    def _calculate_range(self):
        """計算開盤區間"""
        try:
            # 檢查K線資料是否完整
            if not (self.kbar_846 and self.kbar_847):
                logger.error("❌ K線資料不完整")
                return

            if not (self.kbar_846.is_complete() and self.kbar_847.is_complete()):
                logger.error("❌ K線資料未完成")
                return

            # 計算兩根K線的最高點和最低點
            high_846 = self.kbar_846.high_price
            low_846 = self.kbar_846.low_price
            high_847 = self.kbar_847.high_price
            low_847 = self.kbar_847.low_price

            # 檢查價格資料
            if None in [high_846, low_846, high_847, low_847]:
                logger.error("❌ 價格資料包含空值")
                return

            self.range_high = max(high_846, high_847)
            self.range_low = min(low_846, low_847)
            self.range_complete = True

            range_size = self.range_high - self.range_low

            logger.info(f"🎯 開盤區間計算完成!")
            logger.info(f"📈 區間高點: {self.range_high}")
            logger.info(f"📉 區間低點: {self.range_low}")
            logger.info(f"📏 區間大小: {range_size} 點")

            # 記錄K線資料
            logger.debug(f"📊 08:46 K線: O:{self.kbar_846.open_price} H:{high_846} L:{low_846} C:{self.kbar_846.close_price}")
            logger.debug(f"📊 08:47 K線: O:{self.kbar_847.open_price} H:{high_847} L:{low_847} C:{self.kbar_847.close_price}")

        except Exception as e:
            logger.error(f"❌ 計算開盤區間失敗: {e}")
    
    def get_range_data(self) -> Optional[Dict]:
        """取得區間資料"""
        if not self.range_complete:
            return None
        
        return {
            'range_high': self.range_high,
            'range_low': self.range_low,
            'range_size': self.range_high - self.range_low,
            'kbar_846': self.kbar_846.to_dict() if self.kbar_846 else None,
            'kbar_847': self.kbar_847.to_dict() if self.kbar_847 else None,
            'completed_at': datetime.now().isoformat()
        }
    
    def is_range_ready(self) -> bool:
        """檢查區間是否準備就緒"""
        return self.range_complete and self.range_high is not None and self.range_low is not None

    def force_check_completion(self):
        """強制檢查區間完成狀態 (用於定時觸發)"""
        if self.range_complete:
            return True

        current_time = datetime.now().time()

        # 如果已經超過監控時間，強制嘗試完成
        if current_time > self.range_end_time:
            logger.info(f"🕐 監控時間已結束 ({current_time.strftime('%H:%M:%S')} > {self.range_end_time.strftime('%H:%M:%S')})，強制檢查區間完成")
            self._try_complete_range()
            return self.range_complete

        return False

class BreakoutSignalDetector:
    """突破信號偵測器"""
    
    def __init__(self, range_high: float, range_low: float, buffer_points: float = 0):
        """
        初始化突破信號偵測器
        
        Args:
            range_high: 區間高點
            range_low: 區間低點
            buffer_points: 突破緩衝點數
        """
        self.range_high = range_high
        self.range_low = range_low
        self.buffer_points = buffer_points
        
        # 計算突破點位
        self.long_trigger = range_high + buffer_points
        self.short_trigger = range_low - buffer_points
        
        # 信號狀態
        self.signal_generated = False
        self.signal_type = None
        self.signal_price = None
        self.signal_time = None
        
        logger.info(f"🎯 突破信號偵測器已初始化")
        logger.info(f"📈 做多觸發點: {self.long_trigger}")
        logger.info(f"📉 做空觸發點: {self.short_trigger}")
    
    def check_breakout(self, current_price: float, timestamp: datetime = None) -> Optional[str]:
        """
        檢查突破信號
        
        Args:
            current_price: 當前價格
            timestamp: 時間戳記
            
        Returns:
            信號類型 ('LONG', 'SHORT', None)
        """
        if self.signal_generated:
            return None
        
        if timestamp is None:
            timestamp = datetime.now()
        
        signal = None
        
        # 檢查向上突破
        if current_price >= self.long_trigger:
            signal = 'LONG'
            
        # 檢查向下突破
        elif current_price <= self.short_trigger:
            signal = 'SHORT'
        
        # 記錄信號
        if signal:
            self.signal_generated = True
            self.signal_type = signal
            self.signal_price = current_price
            self.signal_time = timestamp
            
            logger.info(f"🚨 突破信號產生!")
            logger.info(f"📊 信號類型: {signal}")
            logger.info(f"💰 突破價格: {current_price}")
            logger.info(f"⏰ 信號時間: {timestamp.strftime('%H:%M:%S')}")
        
        return signal
    
    def get_signal_data(self) -> Optional[Dict]:
        """取得信號資料"""
        if not self.signal_generated:
            return None
        
        return {
            'signal_type': self.signal_type,
            'signal_price': self.signal_price,
            'signal_time': self.signal_time.isoformat(),
            'range_high': self.range_high,
            'range_low': self.range_low,
            'long_trigger': self.long_trigger,
            'short_trigger': self.short_trigger
        }
    
    def reset_signal(self):
        """重置信號狀態"""
        self.signal_generated = False
        self.signal_type = None
        self.signal_price = None
        self.signal_time = None
        logger.debug("🔄 重置突破信號狀態")

if __name__ == "__main__":
    # 測試信號偵測器
    print("🧪 測試信號偵測模組")
    
    # 測試開盤區間偵測器
    detector = OpeningRangeDetector()
    detector.start_monitoring()
    
    # 模擬08:46 K線資料
    base_time = datetime(2025, 6, 30, 8, 46, 0)
    for i in range(60):  # 模擬1分鐘的tick
        timestamp = base_time.replace(second=i)
        price = 22000 + (i % 10) - 5  # 模擬價格波動
        detector.process_tick(price, 100, timestamp)
    
    # 模擬08:47 K線資料
    base_time = datetime(2025, 6, 30, 8, 47, 0)
    for i in range(60):
        timestamp = base_time.replace(second=i)
        price = 22010 + (i % 8) - 4
        detector.process_tick(price, 100, timestamp)
    
    # 檢查08:48:00時的狀態
    final_time = datetime(2025, 6, 30, 8, 48, 0)
    detector.process_tick(22005, 100, final_time)
    
    # 取得區間資料
    range_data = detector.get_range_data()
    if range_data:
        print(f"✅ 區間資料: 高點{range_data['range_high']} 低點{range_data['range_low']}")
        
        # 測試突破信號偵測器
        breakout_detector = BreakoutSignalDetector(
            range_data['range_high'], 
            range_data['range_low']
        )
        
        # 測試突破
        signal = breakout_detector.check_breakout(range_data['range_high'] + 1)
        print(f"突破測試: {signal}")
    
    print("✅ 信號偵測測試完成")
