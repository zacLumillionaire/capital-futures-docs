"""
UI更新管理器
負責安全地從log_queue讀取訊息並更新UI，避免GIL錯誤

設計原則：
1. 只在主線程中運行
2. 使用root.after()定期檢查log_queue
3. 安全地更新UI控件
4. 不執行任何策略計算
"""

import tkinter as tk
import logging
from datetime import datetime
from typing import Optional, Callable, Dict, Any, List
from queue_infrastructure.queue_manager import QueueManager, LogMessage, get_queue_manager

logger = logging.getLogger(__name__)

class UIUpdateManager:
    """UI更新管理器 - 安全的UI更新機制"""
    
    def __init__(self, root: tk.Tk, queue_manager: Optional[QueueManager] = None):
        """
        初始化UI更新管理器
        
        Args:
            root: tkinter根視窗
            queue_manager: Queue管理器實例，如果為None則使用全域實例
        """
        self.root = root
        self.queue_manager = queue_manager or get_queue_manager()
        
        # 更新控制
        self.running = False
        self.update_interval = 50  # 毫秒，每50ms檢查一次
        self.after_id = None
        
        # UI更新回調函數
        self.log_callbacks = []  # 日誌顯示回調
        self.data_callbacks = []  # 資料顯示回調
        
        # 統計資訊
        self.stats = {
            'ui_updates': 0,
            'log_updates': 0,
            'data_updates': 0,
            'error_count': 0,
            'last_update_time': None
        }
        
        # 批次處理設定
        self.max_batch_size = 10  # 每次最多處理10個訊息
        
        logger.info("UIUpdateManager 初始化完成")
    
    def add_log_callback(self, callback: Callable[[str, str, str], None]):
        """
        添加日誌更新回調函數
        
        Args:
            callback: 回調函數，接收 (message, level, source) 參數
        """
        if callback not in self.log_callbacks:
            self.log_callbacks.append(callback)
            logger.info(f"已添加日誌更新回調: {callback.__name__}")
    
    def remove_log_callback(self, callback: Callable[[str, str, str], None]):
        """移除日誌更新回調函數"""
        if callback in self.log_callbacks:
            self.log_callbacks.remove(callback)
            logger.info(f"已移除日誌更新回調: {callback.__name__}")
    
    def add_data_callback(self, callback: Callable[[Dict[str, Any]], None]):
        """
        添加資料更新回調函數
        
        Args:
            callback: 回調函數，接收資料字典
        """
        if callback not in self.data_callbacks:
            self.data_callbacks.append(callback)
            logger.info(f"已添加資料更新回調: {callback.__name__}")
    
    def remove_data_callback(self, callback: Callable[[Dict[str, Any]], None]):
        """移除資料更新回調函數"""
        if callback in self.data_callbacks:
            self.data_callbacks.remove(callback)
            logger.info(f"已移除資料更新回調: {callback.__name__}")
    
    def start_updates(self):
        """啟動UI更新循環"""
        if self.running:
            logger.warning("UI更新管理器已在運行中")
            return
        
        self.running = True
        self._schedule_next_update()
        logger.info("UI更新循環已啟動")
    
    def stop_updates(self):
        """停止UI更新循環"""
        if not self.running:
            logger.warning("UI更新管理器未在運行")
            return
        
        self.running = False
        
        # 取消排程的更新
        if self.after_id:
            self.root.after_cancel(self.after_id)
            self.after_id = None
        
        logger.info("UI更新循環已停止")
    
    def _schedule_next_update(self):
        """排程下一次更新"""
        if self.running:
            self.after_id = self.root.after(self.update_interval, self._update_ui)
    
    def _update_ui(self):
        """主要UI更新函數 (在主線程中運行)"""
        try:
            # 批次處理日誌訊息
            processed_count = 0
            
            while processed_count < self.max_batch_size:
                log_msg = self.queue_manager.get_log_message(timeout=0.001)
                
                if log_msg is None:
                    break  # 沒有更多訊息
                
                # 調用所有日誌回調函數
                self._process_log_message(log_msg)
                processed_count += 1
            
            # 更新統計
            if processed_count > 0:
                self.stats['ui_updates'] += 1
                self.stats['log_updates'] += processed_count
                self.stats['last_update_time'] = datetime.now()
            
        except Exception as e:
            self.stats['error_count'] += 1
            error_msg = f"UI更新錯誤: {str(e)}"
            logger.error(error_msg)
            
            # 即使出錯也要繼續更新循環
        
        finally:
            # 排程下一次更新
            self._schedule_next_update()
    
    def _process_log_message(self, log_msg: LogMessage):
        """
        處理單個日誌訊息
        
        Args:
            log_msg: 日誌訊息物件
        """
        try:
            # 調用所有日誌回調函數
            for callback in self.log_callbacks:
                try:
                    callback(log_msg.message, log_msg.level, log_msg.source)
                except Exception as callback_error:
                    logger.error(f"日誌回調錯誤 ({callback.__name__}): {str(callback_error)}")
            
        except Exception as e:
            logger.error(f"處理日誌訊息錯誤: {str(e)}")
    
    def update_data_display(self, data: Dict[str, Any]):
        """
        更新資料顯示 (從外部調用)
        
        Args:
            data: 要顯示的資料字典
        """
        try:
            # 調用所有資料回調函數
            for callback in self.data_callbacks:
                try:
                    callback(data)
                except Exception as callback_error:
                    logger.error(f"資料回調錯誤 ({callback.__name__}): {str(callback_error)}")
            
            self.stats['data_updates'] += 1
            
        except Exception as e:
            self.stats['error_count'] += 1
            logger.error(f"更新資料顯示錯誤: {str(e)}")
    
    def set_update_interval(self, interval_ms: int):
        """
        設定更新間隔
        
        Args:
            interval_ms: 更新間隔（毫秒）
        """
        if interval_ms < 10:
            interval_ms = 10  # 最小10ms
        elif interval_ms > 1000:
            interval_ms = 1000  # 最大1秒
        
        self.update_interval = interval_ms
        logger.info(f"UI更新間隔設定為 {interval_ms}ms")
    
    def get_status(self) -> Dict[str, Any]:
        """取得更新管理器狀態"""
        return {
            'running': self.running,
            'update_interval': self.update_interval,
            'log_callback_count': len(self.log_callbacks),
            'data_callback_count': len(self.data_callbacks),
            'stats': self.stats.copy(),
            'queue_status': self.queue_manager.get_queue_status()
        }
    
    def is_running(self) -> bool:
        """檢查更新管理器是否在運行"""
        return self.running
    
    def force_update(self):
        """強制執行一次UI更新"""
        if self.running:
            self._update_ui()

class SafeUIHelper:
    """安全UI操作輔助類別"""
    
    @staticmethod
    def safe_config(widget, **kwargs):
        """安全地配置UI控件"""
        try:
            widget.config(**kwargs)
            return True
        except Exception as e:
            logger.error(f"UI控件配置錯誤: {str(e)}")
            return False
    
    @staticmethod
    def safe_insert(text_widget, position, text):
        """安全地插入文字到Text控件"""
        try:
            text_widget.insert(position, text)
            return True
        except Exception as e:
            logger.error(f"Text控件插入錯誤: {str(e)}")
            return False
    
    @staticmethod
    def safe_see(text_widget, position):
        """安全地滾動Text控件"""
        try:
            text_widget.see(position)
            return True
        except Exception as e:
            logger.error(f"Text控件滾動錯誤: {str(e)}")
            return False
    
    @staticmethod
    def safe_set(var, value):
        """安全地設定tkinter變數"""
        try:
            var.set(value)
            return True
        except Exception as e:
            logger.error(f"tkinter變數設定錯誤: {str(e)}")
            return False

# 全域UI更新管理器實例
_ui_updater_instance = None

def get_ui_updater(root: tk.Tk = None) -> Optional[UIUpdateManager]:
    """取得全域UI更新管理器實例"""
    global _ui_updater_instance
    if _ui_updater_instance is None and root is not None:
        _ui_updater_instance = UIUpdateManager(root)
    return _ui_updater_instance

def reset_ui_updater():
    """重置全域UI更新管理器實例 (主要用於測試)"""
    global _ui_updater_instance
    if _ui_updater_instance:
        _ui_updater_instance.stop_updates()
    _ui_updater_instance = None
