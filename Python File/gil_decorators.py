"""
GIL監控裝飾器集合 - 開發階段調試工具
===================================

提供各種裝飾器和工具函數，用於監控可能導致GIL錯誤的代碼。
這些工具專為開發階段設計，幫助快速定位問題。

核心裝飾器：
- @com_event_safe - COM事件安全監控
- @ui_operation_safe - UI操作安全監控  
- @thread_safe_check - 線程安全檢查
- @gil_error_guard - GIL錯誤防護

使用方法：
```python
from gil_decorators import com_event_safe, ui_operation_safe

@com_event_safe
def OnNotifyTicksLONG(self, ...):
    # COM事件處理
    pass

@ui_operation_safe
def update_ui(self):
    # UI更新操作
    pass
```

作者: 開發階段GIL錯誤調試工具
日期: 2025-07-03
"""

import threading
import functools
import traceback
import time
import logging
from typing import Callable, Any, Optional
from datetime import datetime

# 導入GIL監控器
from gil_monitor import global_gil_monitor, gil_logger

def com_event_safe(func: Callable) -> Callable:
    """
    COM事件安全監控裝飾器
    
    專門用於監控COM事件處理函數，檢查是否有危險的UI操作
    """
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        start_time = time.time()
        current_thread = threading.current_thread()
        is_main = current_thread == threading.main_thread()
        
        # 記錄COM事件開始
        gil_logger.debug(f"🔄 【COM事件開始】{func.__name__}")
        gil_logger.debug(f"   線程: {current_thread.name} (ID: {current_thread.ident})")
        gil_logger.debug(f"   主線程: {'是' if is_main else '否'}")
        
        # 檢查參數
        if args:
            gil_logger.debug(f"   參數數量: {len(args)}")
            # 記錄前幾個參數（避免過長）
            param_str = ", ".join(str(arg)[:50] for arg in args[:3])
            if len(args) > 3:
                param_str += "..."
            gil_logger.debug(f"   參數預覽: {param_str}")
        
        try:
            # 執行原函數
            result = func(*args, **kwargs)
            
            # 記錄執行時間
            execution_time = (time.time() - start_time) * 1000
            gil_logger.debug(f"✅ 【COM事件完成】{func.__name__} ({execution_time:.2f}ms)")
            
            # 記錄到監控器
            global_gil_monitor.log_com_event(
                func.__name__,
                f"執行時間: {execution_time:.2f}ms",
                has_ui_operations=False  # 假設沒有UI操作
            )
            
            return result
            
        except Exception as e:
            # COM事件異常是非常危險的！
            execution_time = (time.time() - start_time) * 1000
            error_msg = (
                f"🚨 【COM事件異常】{func.__name__} 發生異常！\n"
                f"   錯誤: {str(e)}\n"
                f"   執行時間: {execution_time:.2f}ms\n"
                f"   線程: {current_thread.name}\n"
                f"   這可能導致COM組件不穩定！"
            )
            
            gil_logger.error(error_msg)
            gil_logger.error(f"   堆棧追蹤:\n{traceback.format_exc()}")
            
            # COM事件絕不應該拋出異常
            if func.__name__.startswith('On'):
                gil_logger.error("🚨 COM事件拋出異常可能導致系統崩潰！返回安全值。")
                return 0  # 返回安全的默認值
            else:
                raise
    
    return wrapper

def ui_operation_safe(func: Callable) -> Callable:
    """
    UI操作安全監控裝飾器
    
    監控UI相關操作，確保在主線程中執行
    """
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        current_thread = threading.current_thread()
        is_main = current_thread == threading.main_thread()
        
        # 記錄UI操作
        gil_logger.debug(f"🖥️ 【UI操作】{func.__name__}")
        
        if not is_main:
            # 在背景線程中執行UI操作 - 危險！
            warning_msg = (
                f"⚠️ 【危險UI操作】{func.__name__} 在背景線程中執行！\n"
                f"   當前線程: {current_thread.name} (ID: {current_thread.ident})\n"
                f"   主線程ID: {threading.main_thread().ident}\n"
                f"   這可能導致GIL錯誤！"
            )
            
            gil_logger.warning(warning_msg)
            
            # 記錄到監控器
            global_gil_monitor.log_ui_operation(
                func.__name__,
                "在背景線程中執行UI操作",
                "UI_Function"
            )
        
        try:
            result = func(*args, **kwargs)
            gil_logger.debug(f"✅ 【UI操作完成】{func.__name__}")
            return result
            
        except Exception as e:
            gil_logger.error(f"❌ 【UI操作失敗】{func.__name__}: {e}")
            raise
    
    return wrapper

def thread_safe_check(expected_thread: str = "main") -> Callable:
    """
    線程安全檢查裝飾器
    
    Args:
        expected_thread: 期望的線程類型 ("main" 或 "background")
    """
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            current_thread = threading.current_thread()
            is_main = current_thread == threading.main_thread()
            
            # 檢查線程類型
            if expected_thread == "main" and not is_main:
                warning_msg = (
                    f"⚠️ 【線程警告】{func.__name__} 應在主線程中執行！\n"
                    f"   當前線程: {current_thread.name} (ID: {current_thread.ident})\n"
                    f"   期望: 主線程"
                )
                gil_logger.warning(warning_msg)
                
            elif expected_thread == "background" and is_main:
                gil_logger.info(f"ℹ️ 【線程提示】{func.__name__} 在主線程中執行（期望背景線程）")
            
            return func(*args, **kwargs)
        
        return wrapper
    return decorator

def gil_error_guard(return_value: Any = None) -> Callable:
    """
    GIL錯誤防護裝飾器
    
    捕獲所有異常，防止COM事件崩潰
    
    Args:
        return_value: 發生異常時的返回值
    """
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            try:
                return func(*args, **kwargs)
            except Exception as e:
                # 記錄異常但不拋出
                error_msg = (
                    f"🛡️ 【GIL防護】{func.__name__} 發生異常，已攔截\n"
                    f"   錯誤: {str(e)}\n"
                    f"   線程: {threading.current_thread().name}\n"
                    f"   返回安全值: {return_value}"
                )
                
                gil_logger.error(error_msg)
                gil_logger.debug(f"   詳細堆棧:\n{traceback.format_exc()}")
                
                return return_value
        
        return wrapper
    return decorator

def log_function_call(include_args: bool = False, include_result: bool = False) -> Callable:
    """
    函數調用日誌裝飾器
    
    Args:
        include_args: 是否記錄參數
        include_result: 是否記錄返回值
    """
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            start_time = time.time()
            current_thread = threading.current_thread()
            
            # 記錄函數調用
            log_msg = f"📞 【函數調用】{func.__name__}"
            
            if include_args and (args or kwargs):
                args_str = ", ".join(str(arg)[:30] for arg in args[:3])
                kwargs_str = ", ".join(f"{k}={str(v)[:30]}" for k, v in list(kwargs.items())[:3])
                if args and kwargs:
                    params = f"{args_str}, {kwargs_str}"
                else:
                    params = args_str or kwargs_str
                log_msg += f"({params})"
            
            gil_logger.debug(log_msg)
            gil_logger.debug(f"   線程: {current_thread.name}")
            
            try:
                result = func(*args, **kwargs)
                
                # 記錄執行時間
                execution_time = (time.time() - start_time) * 1000
                completion_msg = f"✅ 【函數完成】{func.__name__} ({execution_time:.2f}ms)"
                
                if include_result and result is not None:
                    result_str = str(result)[:50]
                    completion_msg += f" -> {result_str}"
                
                gil_logger.debug(completion_msg)
                
                return result
                
            except Exception as e:
                execution_time = (time.time() - start_time) * 1000
                gil_logger.error(f"❌ 【函數失敗】{func.__name__} ({execution_time:.2f}ms): {e}")
                raise
        
        return wrapper
    return decorator

# 組合裝飾器
def com_event_monitor(func: Callable) -> Callable:
    """
    COM事件完整監控裝飾器（組合多個裝飾器）
    """
    # 組合多個裝飾器
    decorated = gil_error_guard(0)(func)
    decorated = thread_safe_check("background")(decorated)
    decorated = com_event_safe(decorated)
    decorated = log_function_call(include_args=True)(decorated)
    
    return decorated

def ui_function_monitor(func: Callable) -> Callable:
    """
    UI函數完整監控裝飾器
    """
    decorated = thread_safe_check("main")(func)
    decorated = ui_operation_safe(decorated)
    decorated = log_function_call()(decorated)
    
    return decorated

# 便利函數
def log_dangerous_operation(operation: str, location: str = ""):
    """記錄危險操作"""
    current_thread = threading.current_thread()
    is_main = current_thread == threading.main_thread()
    
    if not is_main:
        warning_msg = (
            f"🚨 【危險操作】{operation}\n"
            f"   位置: {location}\n"
            f"   線程: {current_thread.name} (ID: {current_thread.ident})\n"
            f"   這可能導致GIL錯誤！"
        )
        gil_logger.warning(warning_msg)
    else:
        gil_logger.debug(f"✅ 【安全操作】{operation} (主線程)")

def check_thread_safety(operation_name: str = "未知操作"):
    """檢查當前線程安全性"""
    current_thread = threading.current_thread()
    is_main = current_thread == threading.main_thread()
    
    if not is_main:
        gil_logger.warning(f"⚠️ 【線程警告】{operation_name} 在背景線程中執行")
        return False
    else:
        gil_logger.debug(f"✅ 【線程安全】{operation_name} 在主線程中執行")
        return True

# 測試函數
def test_decorators():
    """測試裝飾器功能"""
    print("🧪 測試GIL監控裝飾器...")
    
    @com_event_monitor
    def test_com_event(param1, param2=None):
        """測試COM事件"""
        gil_logger.info("執行測試COM事件")
        return "success"
    
    @ui_function_monitor  
    def test_ui_function():
        """測試UI函數"""
        gil_logger.info("執行測試UI函數")
        return "ui_success"
    
    # 測試COM事件（主線程）
    result1 = test_com_event("test_param", param2="test_value")
    print(f"COM事件結果: {result1}")
    
    # 測試UI函數（主線程）
    result2 = test_ui_function()
    print(f"UI函數結果: {result2}")
    
    # 測試背景線程中的危險操作
    def background_test():
        log_dangerous_operation("背景線程UI操作", "test_decorators")
        check_thread_safety("背景線程測試")
    
    thread = threading.Thread(target=background_test, name="TestThread")
    thread.start()
    thread.join()
    
    print("✅ 裝飾器測試完成")

if __name__ == "__main__":
    test_decorators()
