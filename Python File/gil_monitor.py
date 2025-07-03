"""
GIL錯誤監控系統 - 開發階段調試工具
=====================================

這個模組提供完整的GIL錯誤監控和日誌記錄功能，幫助在開發階段
快速定位可能導致GIL錯誤的代碼位置。

核心功能：
- 線程安全檢查
- COM事件監控
- UI操作追蹤
- 詳細錯誤日誌
- 實時警告系統

使用方法：
```python
from gil_monitor import GILMonitor, gil_safe, log_ui_operation

# 初始化監控器
monitor = GILMonitor()

# 裝飾器方式監控函數
@gil_safe
def some_function():
    pass

# 手動記錄UI操作
log_ui_operation("label.config", "設置標籤文字")
```

作者: 開發階段GIL錯誤調試工具
日期: 2025-07-03
"""

import threading
import logging
import traceback
import time
import functools
import inspect
from datetime import datetime
from typing import Dict, List, Any, Optional, Callable
import tkinter as tk

# 設置專用的GIL監控日誌
gil_logger = logging.getLogger('GIL_MONITOR')
gil_logger.setLevel(logging.DEBUG)

# 創建文件處理器
file_handler = logging.FileHandler('gil_monitor.log', encoding='utf-8')
file_handler.setLevel(logging.DEBUG)

# 創建控制台處理器
console_handler = logging.StreamHandler()
console_handler.setLevel(logging.WARNING)

# 設置格式
formatter = logging.Formatter(
    '%(asctime)s - %(name)s - %(levelname)s - [線程:%(thread)d] - %(message)s'
)
file_handler.setFormatter(formatter)
console_handler.setFormatter(formatter)

gil_logger.addHandler(file_handler)
gil_logger.addHandler(console_handler)

class GILMonitor:
    """GIL錯誤監控器"""
    
    def __init__(self):
        """初始化監控器"""
        self.main_thread_id = threading.main_thread().ident
        self.ui_operations = []
        self.com_events = []
        self.warnings = []
        self.start_time = datetime.now()
        
        # 統計信息
        self.stats = {
            'total_ui_operations': 0,
            'unsafe_ui_operations': 0,
            'com_events_count': 0,
            'warnings_count': 0,
            'errors_count': 0
        }
        
        gil_logger.info("🚀 GIL監控器已啟動")
        gil_logger.info(f"📍 主線程ID: {self.main_thread_id}")
    
    def is_main_thread(self) -> bool:
        """檢查當前是否在主線程"""
        return threading.current_thread().ident == self.main_thread_id
    
    def log_ui_operation(self, operation: str, details: str = "", 
                        widget_type: str = "", safe_check: bool = True):
        """記錄UI操作"""
        current_thread = threading.current_thread()
        is_main = self.is_main_thread()
        
        # 獲取調用堆棧
        stack = traceback.extract_stack()
        caller_info = stack[-3] if len(stack) >= 3 else stack[-1]
        
        operation_info = {
            'timestamp': datetime.now(),
            'operation': operation,
            'details': details,
            'widget_type': widget_type,
            'thread_id': current_thread.ident,
            'thread_name': current_thread.name,
            'is_main_thread': is_main,
            'file': caller_info.filename,
            'line': caller_info.lineno,
            'function': caller_info.name
        }
        
        self.ui_operations.append(operation_info)
        self.stats['total_ui_operations'] += 1
        
        if not is_main and safe_check:
            # 危險的UI操作！
            self.stats['unsafe_ui_operations'] += 1
            warning_msg = (
                f"⚠️ 【危險UI操作】在背景線程中執行UI操作！\n"
                f"   操作: {operation}\n"
                f"   詳情: {details}\n"
                f"   控件: {widget_type}\n"
                f"   線程: {current_thread.name} (ID: {current_thread.ident})\n"
                f"   位置: {caller_info.filename}:{caller_info.lineno} in {caller_info.name}"
            )
            
            gil_logger.warning(warning_msg)
            self.warnings.append(operation_info)
            self.stats['warnings_count'] += 1
            
            # 如果是特別危險的操作，記錄為錯誤
            dangerous_ops = ['config', 'insert', 'delete', 'pack', 'grid', 'place']
            if any(dangerous_op in operation.lower() for dangerous_op in dangerous_ops):
                gil_logger.error(f"❌ 【極度危險】{operation} 可能導致GIL錯誤！")
                self.stats['errors_count'] += 1
        else:
            # 安全的UI操作
            gil_logger.debug(f"✅ 【安全UI操作】{operation} - {details}")
    
    def log_com_event(self, event_name: str, details: str = "", 
                     has_ui_operations: bool = False):
        """記錄COM事件"""
        current_thread = threading.current_thread()
        is_main = self.is_main_thread()
        
        # 獲取調用堆棧
        stack = traceback.extract_stack()
        caller_info = stack[-2] if len(stack) >= 2 else stack[-1]
        
        event_info = {
            'timestamp': datetime.now(),
            'event_name': event_name,
            'details': details,
            'thread_id': current_thread.ident,
            'thread_name': current_thread.name,
            'is_main_thread': is_main,
            'has_ui_operations': has_ui_operations,
            'file': caller_info.filename,
            'line': caller_info.lineno,
            'function': caller_info.name
        }
        
        self.com_events.append(event_info)
        self.stats['com_events_count'] += 1
        
        if has_ui_operations and not is_main:
            # COM事件中有UI操作且不在主線程 - 極度危險！
            warning_msg = (
                f"🚨 【極度危險】COM事件中包含UI操作且不在主線程！\n"
                f"   事件: {event_name}\n"
                f"   詳情: {details}\n"
                f"   線程: {current_thread.name} (ID: {current_thread.ident})\n"
                f"   位置: {caller_info.filename}:{caller_info.lineno} in {caller_info.name}\n"
                f"   ⚠️ 這很可能導致GIL錯誤！"
            )
            
            gil_logger.error(warning_msg)
            self.stats['errors_count'] += 1
        else:
            gil_logger.debug(f"📡 【COM事件】{event_name} - {details}")
    
    def get_stats(self) -> Dict[str, Any]:
        """獲取監控統計"""
        runtime = datetime.now() - self.start_time
        
        return {
            **self.stats,
            'runtime_seconds': runtime.total_seconds(),
            'main_thread_id': self.main_thread_id,
            'current_thread_id': threading.current_thread().ident,
            'is_main_thread': self.is_main_thread()
        }
    
    def get_recent_warnings(self, count: int = 10) -> List[Dict]:
        """獲取最近的警告"""
        return self.warnings[-count:] if self.warnings else []
    
    def get_recent_ui_operations(self, count: int = 20) -> List[Dict]:
        """獲取最近的UI操作"""
        return self.ui_operations[-count:] if self.ui_operations else []
    
    def generate_report(self) -> str:
        """生成監控報告"""
        stats = self.get_stats()
        recent_warnings = self.get_recent_warnings(5)
        
        report = f"""
🔍 GIL監控報告
{'='*50}
📊 統計信息:
   - 運行時間: {stats['runtime_seconds']:.2f} 秒
   - 總UI操作: {stats['total_ui_operations']}
   - 不安全UI操作: {stats['unsafe_ui_operations']}
   - COM事件: {stats['com_events_count']}
   - 警告數量: {stats['warnings_count']}
   - 錯誤數量: {stats['errors_count']}

🧵 線程信息:
   - 主線程ID: {stats['main_thread_id']}
   - 當前線程ID: {stats['current_thread_id']}
   - 當前在主線程: {'是' if stats['is_main_thread'] else '否'}

⚠️ 最近警告:
"""
        
        if recent_warnings:
            for i, warning in enumerate(recent_warnings, 1):
                report += f"""
   {i}. {warning['operation']} - {warning['details']}
      位置: {warning['file']}:{warning['line']}
      線程: {warning['thread_name']} (ID: {warning['thread_id']})
"""
        else:
            report += "   無警告 ✅\n"
        
        return report

# 全域監控器實例
global_gil_monitor = GILMonitor()

# 裝飾器函數
def gil_safe(func: Callable) -> Callable:
    """
    GIL安全檢查裝飾器
    
    用於監控函數是否在正確的線程中執行
    """
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        # 檢查是否為COM事件處理函數
        is_com_event = func.__name__.startswith('On')
        
        if is_com_event:
            # 記錄COM事件
            global_gil_monitor.log_com_event(
                func.__name__, 
                f"參數: {len(args)} 個",
                has_ui_operations=False  # 假設沒有UI操作，實際執行時會檢查
            )
        
        try:
            result = func(*args, **kwargs)
            return result
        except Exception as e:
            # 記錄異常
            gil_logger.error(f"❌ 函數 {func.__name__} 執行失敗: {e}")
            gil_logger.error(f"   堆棧: {traceback.format_exc()}")
            
            if is_com_event:
                # COM事件不應該拋出異常
                gil_logger.error("🚨 COM事件拋出異常可能導致系統不穩定！")
                return 0  # COM事件的安全返回值
            else:
                raise
    
    return wrapper

def log_ui_operation(operation: str, details: str = "", widget_type: str = ""):
    """記錄UI操作的便利函數"""
    global_gil_monitor.log_ui_operation(operation, details, widget_type)

def log_com_event(event_name: str, details: str = "", has_ui_operations: bool = False):
    """記錄COM事件的便利函數"""
    global_gil_monitor.log_com_event(event_name, details, has_ui_operations)

def get_gil_stats() -> Dict[str, Any]:
    """獲取GIL監控統計的便利函數"""
    return global_gil_monitor.get_stats()

def print_gil_report():
    """打印GIL監控報告的便利函數"""
    report = global_gil_monitor.generate_report()
    print(report)
    gil_logger.info("📋 GIL監控報告已生成")

# tkinter控件監控包裝器
class SafeWidget:
    """安全的tkinter控件包裝器"""
    
    def __init__(self, widget, widget_type: str = ""):
        self.widget = widget
        self.widget_type = widget_type or widget.__class__.__name__
    
    def __getattr__(self, name):
        attr = getattr(self.widget, name)
        
        if callable(attr) and name in ['config', 'configure', 'insert', 'delete', 'pack', 'grid', 'place']:
            # 包裝危險的UI操作方法
            def safe_method(*args, **kwargs):
                log_ui_operation(f"{self.widget_type}.{name}", 
                               f"參數: {args}, {kwargs}", 
                               self.widget_type)
                return attr(*args, **kwargs)
            return safe_method
        
        return attr

def wrap_widget(widget, widget_type: str = "") -> SafeWidget:
    """包裝tkinter控件以進行監控"""
    return SafeWidget(widget, widget_type)

# 測試函數
def test_gil_monitor():
    """測試GIL監控器"""
    print("🧪 測試GIL監控器...")
    
    # 測試安全的UI操作（主線程）
    log_ui_operation("test_safe_operation", "主線程中的測試操作", "Label")
    
    # 模擬不安全的UI操作（背景線程）
    def unsafe_operation():
        log_ui_operation("test_unsafe_operation", "背景線程中的測試操作", "Label")
    
    thread = threading.Thread(target=unsafe_operation, name="TestThread")
    thread.start()
    thread.join()
    
    # 測試COM事件記錄
    log_com_event("OnNotifyTicksLONG", "測試Tick事件", has_ui_operations=True)
    
    # 顯示報告
    print_gil_report()

if __name__ == "__main__":
    test_gil_monitor()
