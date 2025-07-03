"""
Queue基礎設施模組
提供完整的Queue架構來解決GIL錯誤問題

主要組件：
- QueueManager: 管理Tick資料佇列和日誌佇列
- TickDataProcessor: 在獨立線程中處理Tick資料
- UIUpdateManager: 安全地更新UI控件

使用方式：
1. 初始化Queue基礎設施
2. 啟動Tick處理器
3. 啟動UI更新管理器
4. API事件將資料塞入Queue
5. 策略處理和UI更新自動進行

設計原則：
- API事件只負責塞資料，不做任何UI操作
- 策略處理在獨立線程中進行
- UI更新只在主線程中進行
- 所有組件都是線程安全的
"""

from .queue_manager import (
    QueueManager,
    TickData,
    LogMessage,
    get_queue_manager,
    reset_queue_manager
)

from .tick_processor import (
    TickDataProcessor,
    get_tick_processor,
    reset_tick_processor
)

from .ui_updater import (
    UIUpdateManager,
    SafeUIHelper,
    get_ui_updater,
    reset_ui_updater
)

import logging

logger = logging.getLogger(__name__)

class QueueInfrastructure:
    """Queue基礎設施統一管理類別"""
    
    def __init__(self, root_widget=None):
        """
        初始化Queue基礎設施
        
        Args:
            root_widget: tkinter根視窗 (用於UI更新)
        """
        self.queue_manager = get_queue_manager()
        self.tick_processor = get_tick_processor()
        self.ui_updater = get_ui_updater(root_widget) if root_widget else None
        
        self.initialized = False
        self.running = False
        
        logger.info("Queue基礎設施管理器初始化完成")
    
    def initialize(self):
        """初始化所有組件"""
        try:
            # 啟動Queue管理器
            self.queue_manager.start()
            
            # 初始化完成
            self.initialized = True
            logger.info("✅ Queue基礎設施初始化成功")
            
            return True
            
        except Exception as e:
            logger.error(f"❌ Queue基礎設施初始化失敗: {e}")
            return False
    
    def start_all(self):
        """啟動所有服務"""
        if not self.initialized:
            logger.error("請先初始化Queue基礎設施")
            return False
        
        try:
            # 啟動Tick處理器
            self.tick_processor.start_processing()
            
            # 啟動UI更新管理器
            if self.ui_updater:
                self.ui_updater.start_updates()
            
            self.running = True
            logger.info("🚀 Queue基礎設施全部服務已啟動")
            
            return True
            
        except Exception as e:
            logger.error(f"❌ 啟動Queue基礎設施服務失敗: {e}")
            return False
    
    def stop_all(self):
        """停止所有服務"""
        try:
            # 停止UI更新管理器
            if self.ui_updater:
                self.ui_updater.stop_updates()
            
            # 停止Tick處理器
            self.tick_processor.stop_processing()
            
            # 停止Queue管理器
            self.queue_manager.stop()
            
            self.running = False
            logger.info("🛑 Queue基礎設施全部服務已停止")
            
            return True
            
        except Exception as e:
            logger.error(f"❌ 停止Queue基礎設施服務失敗: {e}")
            return False
    
    def get_status(self):
        """取得整體狀態"""
        return {
            'initialized': self.initialized,
            'running': self.running,
            'queue_manager': self.queue_manager.get_queue_status(),
            'tick_processor': self.tick_processor.get_status(),
            'ui_updater': self.ui_updater.get_status() if self.ui_updater else None
        }
    
    def add_strategy_callback(self, callback):
        """添加策略回調函數"""
        self.tick_processor.add_strategy_callback(callback)
    
    def add_log_callback(self, callback):
        """添加日誌回調函數"""
        if self.ui_updater:
            self.ui_updater.add_log_callback(callback)
    
    def put_tick_data(self, market_no, stock_idx, date, time_hms, time_millis, 
                     bid, ask, close, qty, timestamp=None):
        """便捷方法：放入Tick資料"""
        from datetime import datetime
        
        if timestamp is None:
            timestamp = datetime.now()
        
        tick_data = TickData(
            market_no=market_no,
            stock_idx=stock_idx,
            date=date,
            time_hms=time_hms,
            time_millis=time_millis,
            bid=bid,
            ask=ask,
            close=close,
            qty=qty,
            timestamp=timestamp
        )
        
        return self.queue_manager.put_tick_data(tick_data)
    
    def put_log_message(self, message, level="INFO", source="SYSTEM"):
        """便捷方法：放入日誌訊息"""
        return self.queue_manager.put_log_message(message, level, source)

# 全域基礎設施實例
_infrastructure_instance = None

def get_queue_infrastructure(root_widget=None):
    """取得全域Queue基礎設施實例"""
    global _infrastructure_instance
    if _infrastructure_instance is None:
        _infrastructure_instance = QueueInfrastructure(root_widget)
    return _infrastructure_instance

def reset_queue_infrastructure():
    """重置全域Queue基礎設施實例"""
    global _infrastructure_instance
    if _infrastructure_instance:
        _infrastructure_instance.stop_all()
    
    # 重置所有子組件
    reset_ui_updater()
    reset_tick_processor()
    reset_queue_manager()
    
    _infrastructure_instance = None

# 便捷函數
def quick_setup(root_widget):
    """快速設定Queue基礎設施"""
    infrastructure = get_queue_infrastructure(root_widget)
    
    if infrastructure.initialize() and infrastructure.start_all():
        logger.info("🎉 Queue基礎設施快速設定成功")
        return infrastructure
    else:
        logger.error("❌ Queue基礎設施快速設定失敗")
        return None

__all__ = [
    'QueueManager', 'TickData', 'LogMessage',
    'TickDataProcessor', 
    'UIUpdateManager', 'SafeUIHelper',
    'QueueInfrastructure',
    'get_queue_manager', 'get_tick_processor', 'get_ui_updater',
    'get_queue_infrastructure', 'quick_setup',
    'reset_queue_manager', 'reset_tick_processor', 'reset_ui_updater', 'reset_queue_infrastructure'
]
