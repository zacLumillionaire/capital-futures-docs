"""
訊息處理器模組 - Queue方案的UI更新處理器
=============================================

這個模組包含所有類型訊息的處理器，負責在主線程中安全地更新UI控件。
所有處理器都設計為線程安全，只在主線程中執行UI操作。

核心功能：
- 報價訊息處理器 (Quote Handler)
- Tick訊息處理器 (Tick Handler)  
- 委託訊息處理器 (Order Handler)
- 回報訊息處理器 (Reply Handler)
- 連線訊息處理器 (Connection Handler)

作者: 根據GIL_ERROR_SOLUTION_PLAN.md制定
日期: 2025-07-03
"""

import logging
import math
from datetime import datetime
from typing import Any, Dict, Optional
import tkinter as tk

logger = logging.getLogger(__name__)

class MessageHandlers:
    """
    訊息處理器集合
    
    包含所有類型訊息的處理邏輯，確保UI更新在主線程中安全執行
    """
    
    def __init__(self):
        """初始化處理器"""
        # UI控件引用字典 - 由外部設置
        self.ui_widgets = {}
        
        # 處理統計
        self.handler_stats = {
            'quote_count': 0,
            'tick_count': 0,
            'order_count': 0,
            'reply_count': 0,
            'connection_count': 0,
            'error_count': 0
        }
        
        logger.info("📋 MessageHandlers初始化完成")
    
    def set_ui_widget(self, widget_name: str, widget):
        """
        設置UI控件引用
        
        Args:
            widget_name: 控件名稱
            widget: tkinter控件對象
        """
        self.ui_widgets[widget_name] = widget
        logger.debug(f"🔗 設置UI控件: {widget_name}")
    
    def safe_write_message(self, message: str, listbox_name: str):
        """
        安全地寫入訊息到指定的Listbox
        
        Args:
            message: 要顯示的訊息
            listbox_name: Listbox控件名稱
        """
        try:
            listbox = self.ui_widgets.get(listbox_name)
            if listbox:
                # 確保在主線程中執行
                listbox.insert('end', message)
                listbox.see('end')
                logger.debug(f"✅ 訊息已寫入 {listbox_name}: {str(message)[:50]}...")
            else:
                logger.warning(f"⚠️ 未找到UI控件: {listbox_name}")
        except Exception as e:
            logger.error(f"❌ 寫入訊息失敗 {listbox_name}: {e}")
            self.handler_stats['error_count'] += 1
    
    def handle_quote_message(self, data: Dict[str, Any], timestamp: datetime):
        """
        處理報價訊息

        Args:
            data: 報價數據字典
            timestamp: 訊息時間戳
        """
        try:
            # 根據數據類型處理不同的報價訊息
            data_type = data.get('type', 'quote')

            if data_type == 'quote':
                # 標準報價數據
                stock_no = data.get('stock_no', 'N/A')
                stock_name = data.get('stock_name', 'N/A')
                open_price = data.get('open_price', 0)
                high_price = data.get('high_price', 0)
                low_price = data.get('low_price', 0)
                close_price = data.get('close_price', 0)
                total_qty = data.get('total_qty', 0)

                message = (f'代碼:{stock_no} 名稱:{stock_name} '
                          f'開盤:{open_price} 最高:{high_price} 最低:{low_price} '
                          f'成交:{close_price} 總量:{total_qty}')

                self.safe_write_message(message, 'quote_listbox')

            elif data_type == 'kline':
                # K線數據
                stock_no = data.get('stock_no', 'N/A')
                kline_data = data.get('data', 'N/A')
                message = f'[K線] {stock_no}: {kline_data}'
                self.safe_write_message(message, 'quote_listbox')

            elif data_type == 'market_total':
                # 市場總計數據
                market_no = data.get('market_no', 0)
                total_value = data.get('total_value', 0)
                total_shares = data.get('total_shares', 0)
                total_count = data.get('total_count', 0)

                message = f'[市場總計] 市場:{market_no} 成交值:{total_value}億 張數:{total_shares} 筆數:{total_count}'
                self.safe_write_message(message, 'quote_listbox')

            elif data_type == 'market_highlow':
                # 市場漲跌數據
                market_no = data.get('market_no', 0)
                up = data.get('up', 0)
                down = data.get('down', 0)
                high = data.get('high', 0)
                low = data.get('low', 0)
                no_change = data.get('no_change', 0)

                message = f'[市場漲跌] 市場:{market_no} 上漲/下跌:{up}/{down} 漲停/跌停:{high}/{low} 平盤:{no_change}'
                self.safe_write_message(message, 'quote_listbox')

            elif data_type == 'stock_list':
                # 股票清單數據
                market_no = data.get('market_no', 0)
                stock_data = data.get('stock_data', 'N/A')
                message = f'[股票清單] 市場:{market_no} 數據:{stock_data}'
                self.safe_write_message(message, 'quote_listbox')

            elif data_type == 'market_buysell':
                # 市場買賣數據
                market_no = data.get('market_no', 0)
                buy_count = data.get('buy_count', 0)
                sell_count = data.get('sell_count', 0)
                buy_shares = data.get('buy_shares', 0)
                sell_shares = data.get('sell_shares', 0)

                message = f'[市場買賣] 市場:{market_no} 買進(張/筆):{buy_shares}/{buy_count} 賣出(張/筆):{sell_shares}/{sell_count}'
                self.safe_write_message(message, 'quote_listbox')

            else:
                # 未知類型，顯示原始數據
                message = f'[未知報價類型] {data_type}: {str(data)}'
                self.safe_write_message(message, 'quote_listbox')

            self.handler_stats['quote_count'] += 1
            logger.debug(f"📊 處理報價: {data_type}")

        except Exception as e:
            logger.error(f"❌ 處理報價訊息失敗: {e}")
            self.handler_stats['error_count'] += 1
    
    def handle_tick_message(self, data: Dict[str, Any], timestamp: datetime):
        """
        處理Tick訊息
        
        Args:
            data: Tick數據字典
            timestamp: 訊息時間戳
        """
        try:
            # 解析Tick數據
            stock_idx = data.get('stock_idx', 0)
            ptr = data.get('ptr', 0)
            date = data.get('date', 0)
            time_hms = data.get('time_hms', 0)
            time_millis = data.get('time_millis', 0)
            bid = data.get('bid', 0)
            ask = data.get('ask', 0)
            close = data.get('close', 0)
            qty = data.get('qty', 0)
            simulate = data.get('simulate', 0)
            
            # 格式化訊息
            message = (f"[Tick] 指數:{stock_idx} Ptr:{ptr} 日期:{date} "
                      f"時間:{time_hms} 毫秒:{time_millis} "
                      f"買:{bid} 賣:{ask} 成交:{close} 量:{qty} 模擬:{simulate}")
            
            # 寫入到Tick Listbox
            self.safe_write_message(message, 'tick_listbox')
            
            self.handler_stats['tick_count'] += 1
            logger.debug(f"📈 處理Tick: {stock_idx} @ {close}")
            
        except Exception as e:
            logger.error(f"❌ 處理Tick訊息失敗: {e}")
            self.handler_stats['error_count'] += 1
    
    def handle_order_message(self, data: Dict[str, Any], timestamp: datetime):
        """
        處理委託訊息
        
        Args:
            data: 委託數據字典
            timestamp: 訊息時間戳
        """
        try:
            # 解析委託數據
            order_no = data.get('order_no', 'N/A')
            stock_no = data.get('stock_no', 'N/A')
            price = data.get('price', 0)
            qty = data.get('qty', 0)
            order_type = data.get('order_type', 'N/A')
            status = data.get('status', 'N/A')
            
            # 格式化訊息
            message = (f"[委託] 序號:{order_no} 商品:{stock_no} "
                      f"價格:{price} 數量:{qty} 類型:{order_type} 狀態:{status}")
            
            # 寫入到委託Listbox
            self.safe_write_message(message, 'order_listbox')
            
            self.handler_stats['order_count'] += 1
            logger.debug(f"📝 處理委託: {order_no}")
            
        except Exception as e:
            logger.error(f"❌ 處理委託訊息失敗: {e}")
            self.handler_stats['error_count'] += 1
    
    def handle_reply_message(self, data: Dict[str, Any], timestamp: datetime):
        """
        處理回報訊息

        Args:
            data: 回報數據字典
            timestamp: 訊息時間戳
        """
        try:
            # 如果是原始字符串數據
            if isinstance(data, str):
                message = f"[回報] {data}"
            else:
                # 根據回報類型處理不同的回報訊息
                reply_type = data.get('type', 'unknown')
                user_id = data.get('user_id', 'N/A')

                if reply_type == 'connect':
                    error_code = data.get('error_code', -1)
                    status = "成功" if error_code == 0 else "失敗"
                    message = f"[連線] 用戶:{user_id} 狀態:{status} 代碼:{error_code}"

                elif reply_type == 'disconnect':
                    error_code = data.get('error_code', -1)
                    message = f"[斷線] 用戶:{user_id} 代碼:{error_code}"

                elif reply_type == 'complete':
                    message = f"[完成] 用戶:{user_id}"

                elif reply_type == 'data':
                    raw_data = data.get('raw_data', 'N/A')
                    message = f"[數據] 用戶:{user_id} 數據:{raw_data}"

                elif reply_type == 'reply_message':
                    reply_msg = data.get('message', 'N/A')
                    message = f"[回報訊息] 用戶:{user_id} 內容:{reply_msg}"

                elif reply_type == 'clear_message':
                    message = f"[清除訊息] 用戶:{user_id}"

                elif reply_type == 'solace_disconnect':
                    error_code = data.get('error_code', -1)
                    message = f"[Solace斷線] 用戶:{user_id} 代碼:{error_code}"

                elif reply_type == 'smart_data':
                    raw_data = data.get('raw_data', 'N/A')
                    message = f"[智慧單] 用戶:{user_id} 數據:{raw_data}"

                elif reply_type == 'reply_clear':
                    market = data.get('market', 'N/A')
                    message = f"[清除回報] 市場:{market}"

                else:
                    # 未知類型，顯示原始數據
                    message_text = data.get('message', str(data))
                    message = f"[未知回報] 用戶:{user_id} 類型:{reply_type} 內容:{message_text}"

            # 寫入到回報Listbox
            self.safe_write_message(message, 'reply_listbox')

            self.handler_stats['reply_count'] += 1
            logger.debug(f"📢 處理回報: {reply_type if isinstance(data, dict) else 'string'}")

        except Exception as e:
            logger.error(f"❌ 處理回報訊息失敗: {e}")
            self.handler_stats['error_count'] += 1
    
    def handle_connection_message(self, data: Dict[str, Any], timestamp: datetime):
        """
        處理連線訊息
        
        Args:
            data: 連線數據字典
            timestamp: 訊息時間戳
        """
        try:
            # 解析連線數據
            kind = data.get('kind', 0)
            code = data.get('code', 0)
            
            # 根據kind確定訊息內容
            if kind == 3001:
                message = "Connected!"
            elif kind == 3002:
                message = "DisConnected!"
            elif kind == 3003:
                message = "Stocks ready!"
            elif kind == 3021:
                message = "Connect Error!"
            else:
                message = f"Connection event: Kind={kind}, Code={code}"
            
            # 寫入到全域訊息Listbox
            self.safe_write_message(message, 'global_listbox')
            
            self.handler_stats['connection_count'] += 1
            logger.debug(f"🔗 處理連線: {message}")
            
        except Exception as e:
            logger.error(f"❌ 處理連線訊息失敗: {e}")
            self.handler_stats['error_count'] += 1
    
    def get_stats(self) -> Dict[str, int]:
        """獲取處理統計"""
        return self.handler_stats.copy()
    
    def reset_stats(self):
        """重置統計"""
        for key in self.handler_stats:
            self.handler_stats[key] = 0
        logger.info("📊 處理統計已重置")

# 全域處理器實例
global_message_handlers = MessageHandlers()

# 便利函數
def set_ui_widget(widget_name: str, widget):
    """設置UI控件"""
    global_message_handlers.set_ui_widget(widget_name, widget)

def get_handler_stats() -> Dict[str, int]:
    """獲取處理統計"""
    return global_message_handlers.get_stats()

def reset_handler_stats():
    """重置處理統計"""
    global_message_handlers.reset_stats()

# 處理器函數 - 供queue_manager註冊使用
def quote_handler(data, timestamp):
    """報價處理器"""
    global_message_handlers.handle_quote_message(data, timestamp)

def tick_handler(data, timestamp):
    """Tick處理器"""
    global_message_handlers.handle_tick_message(data, timestamp)

def order_handler(data, timestamp):
    """委託處理器"""
    global_message_handlers.handle_order_message(data, timestamp)

def reply_handler(data, timestamp):
    """回報處理器"""
    global_message_handlers.handle_reply_message(data, timestamp)

def connection_handler(data, timestamp):
    """連線處理器"""
    global_message_handlers.handle_connection_message(data, timestamp)

if __name__ == "__main__":
    # 測試代碼
    import tkinter as tk
    
    # 創建測試窗口
    root = tk.Tk()
    root.title("訊息處理器測試")
    
    # 創建測試Listbox
    quote_listbox = tk.Listbox(root)
    quote_listbox.pack()
    
    # 設置UI控件
    set_ui_widget('quote_listbox', quote_listbox)
    
    # 測試處理器
    test_data = {
        'stock_no': 'MTX00',
        'stock_name': '小台指',
        'close_price': 22000
    }
    
    quote_handler(test_data, datetime.now())
    
    print("處理統計:", get_handler_stats())
    
    root.mainloop()
