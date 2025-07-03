"""
Queue設置模組 - 統一的Queue處理器設置
=====================================

這個模組提供統一的Queue處理器設置功能，讓所有使用群益API的模組
都能輕鬆設置Queue處理器，避免GIL錯誤。

核心功能：
- 統一的處理器註冊
- UI控件映射設置
- 主線程處理器啟動
- 錯誤處理和日誌記錄

使用方法：
```python
from queue_setup import setup_queue_processing

# 在主程式中調用
setup_queue_processing(root, ui_widgets_dict)
```

作者: 根據GIL_ERROR_SOLUTION_PLAN.md制定
日期: 2025-07-03
"""

import logging
from typing import Dict, Any
import tkinter as tk

from queue_manager import (
    register_message_handler, MainThreadProcessor
)
from message_handlers import (
    quote_handler, tick_handler, connection_handler, 
    reply_handler, order_handler, set_ui_widget
)

logger = logging.getLogger(__name__)

def setup_queue_processing(root_widget: tk.Tk, ui_widgets: Dict[str, Any] = None, 
                          interval_ms: int = 50) -> MainThreadProcessor:
    """
    設置完整的Queue處理系統
    
    Args:
        root_widget: tkinter根控件
        ui_widgets: UI控件字典，格式: {'widget_name': widget_object}
        interval_ms: 處理間隔(毫秒)，默認50ms
    
    Returns:
        MainThreadProcessor: 處理器實例
    """
    try:
        logger.info("🚀 開始設置Queue處理系統...")
        
        # 1. 註冊所有訊息處理器
        register_message_handler('quote', quote_handler)
        register_message_handler('tick', tick_handler)
        register_message_handler('connection', connection_handler)
        register_message_handler('reply', reply_handler)
        register_message_handler('order', order_handler)
        
        logger.info("✅ 訊息處理器註冊完成")
        
        # 2. 設置UI控件引用
        if ui_widgets:
            for widget_name, widget in ui_widgets.items():
                if widget is not None:
                    set_ui_widget(widget_name, widget)
                    logger.debug(f"🔗 設置UI控件: {widget_name}")
        
        logger.info("✅ UI控件設置完成")
        
        # 3. 創建並啟動主線程處理器
        processor = MainThreadProcessor(root_widget, interval_ms)
        processor.start()
        
        logger.info(f"✅ 主線程處理器已啟動 (間隔: {interval_ms}ms)")
        
        return processor
        
    except Exception as e:
        logger.error(f"❌ Queue處理系統設置失敗: {e}")
        raise

def setup_quote_processing(root_widget: tk.Tk, global_listbox=None, 
                          quote_listbox=None, tick_listbox=None) -> MainThreadProcessor:
    """
    設置報價模組的Queue處理
    
    Args:
        root_widget: tkinter根控件
        global_listbox: 全域訊息listbox
        quote_listbox: 報價listbox
        tick_listbox: Tick listbox
    
    Returns:
        MainThreadProcessor: 處理器實例
    """
    ui_widgets = {}
    
    if global_listbox is not None:
        ui_widgets['global_listbox'] = global_listbox
        ui_widgets['connection_listbox'] = global_listbox  # 連線訊息使用全域listbox
    
    if quote_listbox is not None:
        ui_widgets['quote_listbox'] = quote_listbox
    
    if tick_listbox is not None:
        ui_widgets['tick_listbox'] = tick_listbox
    
    return setup_queue_processing(root_widget, ui_widgets)

def setup_reply_processing(root_widget: tk.Tk, reply_listbox=None, 
                          global_listbox=None) -> MainThreadProcessor:
    """
    設置回報模組的Queue處理
    
    Args:
        root_widget: tkinter根控件
        reply_listbox: 回報listbox
        global_listbox: 全域訊息listbox
    
    Returns:
        MainThreadProcessor: 處理器實例
    """
    ui_widgets = {}
    
    if reply_listbox is not None:
        ui_widgets['reply_listbox'] = reply_listbox
        ui_widgets['order_listbox'] = reply_listbox  # 委託回報使用同一個listbox
    
    if global_listbox is not None:
        ui_widgets['global_listbox'] = global_listbox
    
    return setup_queue_processing(root_widget, ui_widgets)

def setup_order_processing(root_widget: tk.Tk, order_listbox=None, 
                          global_listbox=None) -> MainThreadProcessor:
    """
    設置下單模組的Queue處理
    
    Args:
        root_widget: tkinter根控件
        order_listbox: 委託listbox
        global_listbox: 全域訊息listbox
    
    Returns:
        MainThreadProcessor: 處理器實例
    """
    ui_widgets = {}
    
    if order_listbox is not None:
        ui_widgets['order_listbox'] = order_listbox
        ui_widgets['reply_listbox'] = order_listbox  # 回報使用同一個listbox
    
    if global_listbox is not None:
        ui_widgets['global_listbox'] = global_listbox
    
    return setup_queue_processing(root_widget, ui_widgets)

def setup_comprehensive_processing(root_widget: tk.Tk, **kwargs) -> MainThreadProcessor:
    """
    設置綜合模組的Queue處理 (包含所有功能)
    
    Args:
        root_widget: tkinter根控件
        **kwargs: UI控件參數
            - global_listbox: 全域訊息listbox
            - quote_listbox: 報價listbox
            - tick_listbox: Tick listbox
            - reply_listbox: 回報listbox
            - order_listbox: 委託listbox
    
    Returns:
        MainThreadProcessor: 處理器實例
    """
    ui_widgets = {}
    
    # 映射所有可能的UI控件
    widget_mappings = {
        'global_listbox': ['global_listbox', 'connection_listbox'],
        'quote_listbox': ['quote_listbox'],
        'tick_listbox': ['tick_listbox'],
        'reply_listbox': ['reply_listbox'],
        'order_listbox': ['order_listbox']
    }
    
    for param_name, widget_names in widget_mappings.items():
        widget = kwargs.get(param_name)
        if widget is not None:
            for widget_name in widget_names:
                ui_widgets[widget_name] = widget
    
    return setup_queue_processing(root_widget, ui_widgets)

# 便利函數
def quick_setup_for_quote_module(root, global_list, quote_list, tick_list):
    """快速設置報價模組"""
    return setup_quote_processing(root, global_list, quote_list, tick_list)

def quick_setup_for_reply_module(root, reply_list, global_list=None):
    """快速設置回報模組"""
    return setup_reply_processing(root, reply_list, global_list)

def quick_setup_for_order_module(root, order_list, global_list=None):
    """快速設置下單模組"""
    return setup_order_processing(root, order_list, global_list)

# 測試和診斷函數
def test_queue_setup():
    """測試Queue設置"""
    import tkinter as tk
    from queue_manager import get_queue_stats
    from message_handlers import get_handler_stats
    
    # 創建測試窗口
    root = tk.Tk()
    root.title("Queue設置測試")
    
    # 創建測試listbox
    test_listbox = tk.Listbox(root)
    test_listbox.pack()
    
    # 設置Queue處理
    processor = setup_queue_processing(root, {'test_listbox': test_listbox})
    
    # 顯示統計
    def show_stats():
        queue_stats = get_queue_stats()
        handler_stats = get_handler_stats()
        print("Queue統計:", queue_stats)
        print("處理器統計:", handler_stats)
    
    # 測試按鈕
    tk.Button(root, text="顯示統計", command=show_stats).pack()
    
    # 5秒後自動關閉
    root.after(5000, root.quit)
    
    try:
        root.mainloop()
        processor.stop()
        print("✅ Queue設置測試完成")
    except Exception as e:
        print(f"❌ Queue設置測試失敗: {e}")

if __name__ == "__main__":
    # 執行測試
    test_queue_setup()
