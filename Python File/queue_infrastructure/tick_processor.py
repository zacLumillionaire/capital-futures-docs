"""
Tick資料處理器
負責在獨立線程中處理Tick資料，避免GIL錯誤

設計原則：
1. 從tick_data_queue讀取資料
2. 執行策略計算
3. 將結果放入log_queue
4. 完全不直接操作UI
"""

import threading
import time
import logging
from datetime import datetime
from typing import Optional, Callable, Dict, Any
from queue_infrastructure.queue_manager import QueueManager, TickData, LogMessage, get_queue_manager

logger = logging.getLogger(__name__)

class TickDataProcessor:
    """Tick資料處理器 - 策略處理線程"""
    
    def __init__(self, queue_manager: Optional[QueueManager] = None):
        """
        初始化Tick資料處理器
        
        Args:
            queue_manager: Queue管理器實例，如果為None則使用全域實例
        """
        self.queue_manager = queue_manager or get_queue_manager()
        
        # 線程管理
        self.processing_thread = None
        self.running = False
        self.thread_lock = threading.Lock()
        
        # 策略回調函數
        self.strategy_callbacks = []
        
        # 處理統計
        self.stats = {
            'processed_count': 0,
            'error_count': 0,
            'last_process_time': None,
            'average_process_time': 0.0
        }
        
        # 最後處理的資料
        self.last_tick_data = None
        
        logger.info("TickDataProcessor 初始化完成")
    
    def add_strategy_callback(self, callback: Callable[[Dict[str, Any]], None]):
        """
        添加策略回調函數
        
        Args:
            callback: 策略處理函數，接收tick資料字典
        """
        if callback not in self.strategy_callbacks:
            self.strategy_callbacks.append(callback)
            logger.info(f"已添加策略回調函數: {callback.__name__}")
    
    def remove_strategy_callback(self, callback: Callable[[Dict[str, Any]], None]):
        """移除策略回調函數"""
        if callback in self.strategy_callbacks:
            self.strategy_callbacks.remove(callback)
            logger.info(f"已移除策略回調函數: {callback.__name__}")
    
    def start_processing(self):
        """啟動Tick資料處理線程"""
        with self.thread_lock:
            if self.running:
                logger.warning("Tick資料處理器已在運行中")
                return
            
            self.running = True
            self.processing_thread = threading.Thread(
                target=self._processing_loop,
                name="TickDataProcessor",
                daemon=True
            )
            self.processing_thread.start()
            
            logger.info("Tick資料處理線程已啟動")
            self.queue_manager.put_log_message("🚀 策略處理引擎已啟動", "INFO", "PROCESSOR")
    
    def stop_processing(self):
        """停止Tick資料處理線程"""
        with self.thread_lock:
            if not self.running:
                logger.warning("Tick資料處理器未在運行")
                return
            
            self.running = False
            
            # 等待線程結束
            if self.processing_thread and self.processing_thread.is_alive():
                self.processing_thread.join(timeout=2.0)
                if self.processing_thread.is_alive():
                    logger.warning("Tick資料處理線程未能正常結束")
            
            logger.info("Tick資料處理線程已停止")
            self.queue_manager.put_log_message("🛑 策略處理引擎已停止", "INFO", "PROCESSOR")
    
    def _processing_loop(self):
        """主要處理循環 (在獨立線程中運行)"""
        logger.info("Tick資料處理循環開始")
        
        while self.running:
            try:
                # 從佇列取出Tick資料
                tick_data = self.queue_manager.get_tick_data(timeout=1.0)
                
                if tick_data is None:
                    continue  # 超時，繼續等待
                
                # 處理Tick資料
                self._process_single_tick(tick_data)
                
            except Exception as e:
                self.stats['error_count'] += 1
                error_msg = f"Tick資料處理錯誤: {str(e)}"
                logger.error(error_msg)
                self.queue_manager.put_log_message(f"❌ {error_msg}", "ERROR", "PROCESSOR")
                
                # 短暫休息避免錯誤循環
                time.sleep(0.1)
        
        logger.info("Tick資料處理循環結束")
    
    def _process_single_tick(self, tick_data: TickData):
        """
        處理單個Tick資料
        
        Args:
            tick_data: Tick資料物件
        """
        start_time = time.time()
        
        try:
            # 轉換為字典格式
            tick_dict = tick_data.to_dict()
            self.last_tick_data = tick_dict
            
            # 生成基本日誌訊息
            price = tick_dict['corrected_price']
            formatted_time = tick_dict['formatted_time']
            
            # 控制日誌頻率 (每秒最多一次)
            current_time = time.time()
            if not hasattr(self, '_last_log_time') or current_time - self._last_log_time > 1.0:
                self._last_log_time = current_time
                tick_msg = f"【Tick】價格:{price} 買:{tick_data.bid} 賣:{tick_data.ask} 量:{tick_data.qty} 時間:{formatted_time}"
                self.queue_manager.put_log_message(tick_msg, "INFO", "TICK")
            
            # 調用所有策略回調函數
            for callback in self.strategy_callbacks:
                try:
                    callback(tick_dict)
                except Exception as callback_error:
                    error_msg = f"策略回調錯誤 ({callback.__name__}): {str(callback_error)}"
                    logger.error(error_msg)
                    self.queue_manager.put_log_message(f"⚠️ {error_msg}", "WARNING", "STRATEGY")
            
            # 更新統計
            process_time = time.time() - start_time
            self.stats['processed_count'] += 1
            self.stats['last_process_time'] = datetime.now()
            
            # 計算平均處理時間
            if self.stats['average_process_time'] == 0:
                self.stats['average_process_time'] = process_time
            else:
                self.stats['average_process_time'] = (
                    self.stats['average_process_time'] * 0.9 + process_time * 0.1
                )
            
        except Exception as e:
            self.stats['error_count'] += 1
            error_msg = f"處理Tick資料時發生錯誤: {str(e)}"
            logger.error(error_msg)
            self.queue_manager.put_log_message(f"❌ {error_msg}", "ERROR", "PROCESSOR")
    
    def get_status(self) -> Dict[str, Any]:
        """取得處理器狀態"""
        with self.thread_lock:
            return {
                'running': self.running,
                'thread_alive': self.processing_thread.is_alive() if self.processing_thread else False,
                'callback_count': len(self.strategy_callbacks),
                'stats': self.stats.copy(),
                'last_tick_data': self.last_tick_data
            }
    
    def is_running(self) -> bool:
        """檢查處理器是否在運行"""
        return self.running
    
    def get_last_tick_data(self) -> Optional[Dict[str, Any]]:
        """取得最後處理的Tick資料"""
        return self.last_tick_data

# 全域Tick處理器實例 (單例模式)
_tick_processor_instance = None

def get_tick_processor() -> TickDataProcessor:
    """取得全域Tick處理器實例"""
    global _tick_processor_instance
    if _tick_processor_instance is None:
        _tick_processor_instance = TickDataProcessor()
    return _tick_processor_instance

def reset_tick_processor():
    """重置全域Tick處理器實例 (主要用於測試)"""
    global _tick_processor_instance
    if _tick_processor_instance:
        _tick_processor_instance.stop_processing()
    _tick_processor_instance = None
