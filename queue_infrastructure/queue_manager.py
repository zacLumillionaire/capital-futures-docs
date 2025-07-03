"""
Queue基礎設施管理器
用於管理Tick數據佇列和日誌佇列，解決GIL錯誤問題

設計原則：
1. API事件只負責塞資料到Queue
2. 策略處理在獨立線程中進行
3. UI更新通過安全的Queue機制
"""

import queue
import threading
import time
import logging
from datetime import datetime
from typing import Dict, Any, Optional, Callable
from dataclasses import dataclass

# 設定日誌
logger = logging.getLogger(__name__)

@dataclass
class TickData:
    """Tick資料結構"""
    market_no: str
    stock_idx: int
    date: int
    time_hms: int
    time_millis: int
    bid: int
    ask: int
    close: int
    qty: int
    timestamp: datetime
    
    def to_dict(self) -> Dict[str, Any]:
        """轉換為字典格式"""
        return {
            'market_no': self.market_no,
            'stock_idx': self.stock_idx,
            'date': self.date,
            'time_hms': self.time_hms,
            'time_millis': self.time_millis,
            'bid': self.bid,
            'ask': self.ask,
            'close': self.close,
            'qty': self.qty,
            'timestamp': self.timestamp,
            'formatted_time': f"{self.time_hms:06d}"[:2] + ":" + f"{self.time_hms:06d}"[2:4] + ":" + f"{self.time_hms:06d}"[4:6],
            'corrected_price': self.close / 100.0 if self.close > 100000 else self.close
        }

@dataclass
class LogMessage:
    """日誌訊息結構"""
    message: str
    level: str = "INFO"  # INFO, WARNING, ERROR
    timestamp: datetime = None
    source: str = "SYSTEM"  # TICK, STRATEGY, UI, SYSTEM
    
    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = datetime.now()
    
    def to_display_string(self) -> str:
        """轉換為顯示字串"""
        time_str = self.timestamp.strftime("%H:%M:%S")
        return f"[{time_str}] {self.message}"

class QueueManager:
    """Queue管理器 - 核心基礎設施"""
    
    def __init__(self, tick_queue_size: int = 1000, log_queue_size: int = 500):
        """
        初始化Queue管理器
        
        Args:
            tick_queue_size: Tick資料佇列大小
            log_queue_size: 日誌佇列大小
        """
        # 核心佇列
        self.tick_data_queue = queue.Queue(maxsize=tick_queue_size)
        self.log_queue = queue.Queue(maxsize=log_queue_size)
        
        # 狀態管理
        self.running = False
        self.stats = {
            'tick_received': 0,
            'tick_processed': 0,
            'log_generated': 0,
            'log_displayed': 0,
            'queue_full_errors': 0,
            'processing_errors': 0
        }
        
        # 線程安全鎖
        self.stats_lock = threading.Lock()
        
        logger.info("QueueManager 初始化完成")
    
    def put_tick_data(self, tick_data: TickData) -> bool:
        """
        將Tick資料放入佇列 (非阻塞)
        
        Args:
            tick_data: Tick資料物件
            
        Returns:
            是否成功放入佇列
        """
        try:
            self.tick_data_queue.put_nowait(tick_data)
            with self.stats_lock:
                self.stats['tick_received'] += 1
            return True
        except queue.Full:
            with self.stats_lock:
                self.stats['queue_full_errors'] += 1
            logger.warning("Tick資料佇列已滿，丟棄資料")
            return False
        except Exception as e:
            logger.error(f"放入Tick資料失敗: {e}")
            return False
    
    def get_tick_data(self, timeout: float = 1.0) -> Optional[TickData]:
        """
        從佇列取出Tick資料
        
        Args:
            timeout: 超時時間（秒）
            
        Returns:
            Tick資料物件或None
        """
        try:
            tick_data = self.tick_data_queue.get(timeout=timeout)
            with self.stats_lock:
                self.stats['tick_processed'] += 1
            return tick_data
        except queue.Empty:
            return None
        except Exception as e:
            logger.error(f"取出Tick資料失敗: {e}")
            return None
    
    def put_log_message(self, message: str, level: str = "INFO", source: str = "SYSTEM") -> bool:
        """
        將日誌訊息放入佇列 (非阻塞)
        
        Args:
            message: 日誌訊息
            level: 日誌等級
            source: 訊息來源
            
        Returns:
            是否成功放入佇列
        """
        try:
            log_msg = LogMessage(message=message, level=level, source=source)
            self.log_queue.put_nowait(log_msg)
            with self.stats_lock:
                self.stats['log_generated'] += 1
            return True
        except queue.Full:
            # 日誌佇列滿了就丟棄舊的訊息
            try:
                self.log_queue.get_nowait()  # 移除最舊的訊息
                self.log_queue.put_nowait(LogMessage(message=message, level=level, source=source))
                return True
            except:
                logger.warning("日誌佇列處理失敗")
                return False
        except Exception as e:
            logger.error(f"放入日誌訊息失敗: {e}")
            return False
    
    def get_log_message(self, timeout: float = 0.1) -> Optional[LogMessage]:
        """
        從佇列取出日誌訊息
        
        Args:
            timeout: 超時時間（秒）
            
        Returns:
            日誌訊息物件或None
        """
        try:
            log_msg = self.log_queue.get(timeout=timeout)
            with self.stats_lock:
                self.stats['log_displayed'] += 1
            return log_msg
        except queue.Empty:
            return None
        except Exception as e:
            logger.error(f"取出日誌訊息失敗: {e}")
            return None
    
    def get_queue_status(self) -> Dict[str, Any]:
        """取得佇列狀態資訊"""
        with self.stats_lock:
            return {
                'tick_queue_size': self.tick_data_queue.qsize(),
                'log_queue_size': self.log_queue.qsize(),
                'tick_queue_maxsize': self.tick_data_queue.maxsize,
                'log_queue_maxsize': self.log_queue.maxsize,
                'stats': self.stats.copy(),
                'running': self.running
            }
    
    def clear_queues(self):
        """清空所有佇列"""
        try:
            while not self.tick_data_queue.empty():
                self.tick_data_queue.get_nowait()
        except queue.Empty:
            pass
        
        try:
            while not self.log_queue.empty():
                self.log_queue.get_nowait()
        except queue.Empty:
            pass
        
        logger.info("所有佇列已清空")
    
    def start(self):
        """啟動Queue管理器"""
        self.running = True
        logger.info("QueueManager 已啟動")
    
    def stop(self):
        """停止Queue管理器"""
        self.running = False
        logger.info("QueueManager 已停止")

# 全域Queue管理器實例 (單例模式)
_queue_manager_instance = None

def get_queue_manager() -> QueueManager:
    """取得全域Queue管理器實例"""
    global _queue_manager_instance
    if _queue_manager_instance is None:
        _queue_manager_instance = QueueManager()
    return _queue_manager_instance

def reset_queue_manager():
    """重置全域Queue管理器實例 (主要用於測試)"""
    global _queue_manager_instance
    if _queue_manager_instance:
        _queue_manager_instance.stop()
        _queue_manager_instance.clear_queues()
    _queue_manager_instance = None
