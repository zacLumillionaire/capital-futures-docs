"""
全域Queue管理器 - 解決GIL錯誤的核心模組
===========================================

這個模組實現了Queue方案的核心架構，確保所有COM事件都通過Queue傳遞，
避免背景線程直接操作tkinter UI控件，從而解決Fatal Python error: PyEval_RestoreThread問題。

核心設計原則：
✅ COM事件絕不碰UI - 只打包數據放入Queue
✅ 主線程安全處理 - 所有UI操作都在主線程中進行  
✅ 非阻塞機制 - 使用put_nowait()避免任何等待
✅ 定期處理 - 每50ms檢查Queue，確保即時性

作者: 根據GIL_ERROR_SOLUTION_PLAN.md制定
日期: 2025-07-03
"""

import queue
import threading
import time
import logging
from datetime import datetime
from typing import Dict, Any, Callable, Optional

# 設置日誌
logger = logging.getLogger(__name__)

class QueueManager:
    """
    全域Queue管理器
    
    負責管理所有COM事件的Queue傳遞，確保線程安全的UI更新
    """
    
    def __init__(self):
        """初始化Queue管理器"""
        # 主要的訊息隊列 - 無限大小避免阻塞
        self.message_queue = queue.Queue()
        
        # 不同類型的訊息處理器註冊表
        self.message_handlers: Dict[str, Callable] = {}
        
        # 處理狀態控制
        self.processing_active = False
        self.processing_thread = None
        
        # 統計信息
        self.stats = {
            'total_messages': 0,
            'processed_messages': 0,
            'failed_messages': 0,
            'queue_size': 0,
            'last_process_time': None
        }
        
        # 線程安全鎖
        self.stats_lock = threading.Lock()
        
        logger.info("🚀 QueueManager初始化完成")
    
    def register_handler(self, message_type: str, handler: Callable):
        """
        註冊訊息處理器
        
        Args:
            message_type: 訊息類型 (如 'quote', 'tick', 'order', 'reply')
            handler: 處理函數，接收 (data, timestamp) 參數
        """
        self.message_handlers[message_type] = handler
        logger.info(f"📝 註冊處理器: {message_type}")
    
    def put_message(self, message_type: str, data: Any, priority: int = 0):
        """
        放入訊息到Queue (線程安全，非阻塞)
        
        Args:
            message_type: 訊息類型
            data: 訊息數據
            priority: 優先級 (0=普通, 1=高, 2=緊急)
        """
        try:
            timestamp = datetime.now()
            message = {
                'type': message_type,
                'data': data,
                'timestamp': timestamp,
                'priority': priority
            }
            
            # 非阻塞放入 - 關鍵！避免COM事件線程等待
            self.message_queue.put_nowait(message)
            
            # 更新統計
            with self.stats_lock:
                self.stats['total_messages'] += 1
                self.stats['queue_size'] = self.message_queue.qsize()
            
            logger.debug(f"📤 訊息已入隊: {message_type}")
            
        except queue.Full:
            # Queue滿了，記錄但不阻塞
            logger.warning(f"⚠️ Queue已滿，丟棄訊息: {message_type}")
            with self.stats_lock:
                self.stats['failed_messages'] += 1
        except Exception as e:
            logger.error(f"❌ 放入訊息失敗: {e}")
            with self.stats_lock:
                self.stats['failed_messages'] += 1
    
    def process_messages(self, max_messages: int = 10):
        """
        處理Queue中的訊息 (必須在主線程中調用)
        
        Args:
            max_messages: 單次處理的最大訊息數量
        """
        processed_count = 0
        
        try:
            while processed_count < max_messages and not self.message_queue.empty():
                try:
                    # 非阻塞獲取訊息
                    message = self.message_queue.get_nowait()
                    
                    # 獲取對應的處理器
                    message_type = message['type']
                    handler = self.message_handlers.get(message_type)
                    
                    if handler:
                        # 調用處理器處理訊息
                        handler(message['data'], message['timestamp'])
                        logger.debug(f"📥 處理訊息: {message_type}")
                    else:
                        logger.warning(f"⚠️ 未找到處理器: {message_type}")
                    
                    processed_count += 1
                    
                    # 更新統計
                    with self.stats_lock:
                        self.stats['processed_messages'] += 1
                        self.stats['last_process_time'] = datetime.now()
                
                except queue.Empty:
                    break
                except Exception as e:
                    logger.error(f"❌ 處理訊息失敗: {e}")
                    with self.stats_lock:
                        self.stats['failed_messages'] += 1
        
        except Exception as e:
            logger.error(f"❌ 處理Queue失敗: {e}")
        
        # 更新Queue大小統計
        with self.stats_lock:
            self.stats['queue_size'] = self.message_queue.qsize()
        
        return processed_count
    
    def get_stats(self) -> Dict[str, Any]:
        """獲取統計信息"""
        with self.stats_lock:
            return self.stats.copy()
    
    def clear_queue(self):
        """清空Queue"""
        try:
            while not self.message_queue.empty():
                self.message_queue.get_nowait()
            logger.info("🗑️ Queue已清空")
        except Exception as e:
            logger.error(f"❌ 清空Queue失敗: {e}")

# 全域Queue管理器實例
global_queue_manager = QueueManager()

# 便利函數供外部使用
def put_quote_message(data):
    """放入報價訊息"""
    global_queue_manager.put_message('quote', data, priority=1)

def put_tick_message(data):
    """放入Tick訊息"""
    global_queue_manager.put_message('tick', data, priority=1)

def put_order_message(data):
    """放入委託訊息"""
    global_queue_manager.put_message('order', data, priority=2)

def put_reply_message(data):
    """放入回報訊息"""
    global_queue_manager.put_message('reply', data, priority=2)

def put_connection_message(data):
    """放入連線訊息"""
    global_queue_manager.put_message('connection', data, priority=0)

def register_message_handler(message_type: str, handler: Callable):
    """註冊訊息處理器"""
    global_queue_manager.register_handler(message_type, handler)

def process_all_messages(max_messages: int = 10) -> int:
    """處理所有訊息 (主線程調用)"""
    return global_queue_manager.process_messages(max_messages)

def get_queue_stats() -> Dict[str, Any]:
    """獲取Queue統計"""
    return global_queue_manager.get_stats()

def clear_message_queue():
    """清空訊息隊列"""
    global_queue_manager.clear_queue()

# 主線程處理器類
class MainThreadProcessor:
    """
    主線程處理器
    
    負責在主線程中定期處理Queue訊息
    """
    
    def __init__(self, root_widget, interval_ms: int = 50):
        """
        初始化主線程處理器
        
        Args:
            root_widget: tkinter根控件，用於after方法
            interval_ms: 處理間隔(毫秒)
        """
        self.root = root_widget
        self.interval = interval_ms
        self.active = False
        
        logger.info(f"🔄 主線程處理器初始化，間隔: {interval_ms}ms")
    
    def start(self):
        """啟動處理器"""
        if not self.active:
            self.active = True
            self._schedule_next_process()
            logger.info("▶️ 主線程處理器已啟動")
    
    def stop(self):
        """停止處理器"""
        self.active = False
        logger.info("⏹️ 主線程處理器已停止")
    
    def _schedule_next_process(self):
        """安排下次處理"""
        if self.active:
            # 處理訊息
            processed = process_all_messages(max_messages=20)
            
            if processed > 0:
                logger.debug(f"🔄 處理了 {processed} 條訊息")
            
            # 安排下次處理
            self.root.after(self.interval, self._schedule_next_process)

if __name__ == "__main__":
    # 測試代碼
    import tkinter as tk
    
    def test_handler(data, timestamp):
        print(f"處理訊息: {data} at {timestamp}")
    
    # 註冊處理器
    register_message_handler('test', test_handler)
    
    # 測試放入訊息
    put_quote_message("測試報價數據")
    put_tick_message("測試Tick數據")
    
    # 創建測試窗口
    root = tk.Tk()
    processor = MainThreadProcessor(root)
    processor.start()
    
    print("Queue統計:", get_queue_stats())
    
    root.after(5000, root.quit)  # 5秒後退出
    root.mainloop()
