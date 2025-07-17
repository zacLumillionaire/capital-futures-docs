# 事件分發器
# Event Dispatcher for Virtual Quote Machine

import threading
import time
import queue
from typing import List, Any, Optional, Callable
from dataclasses import dataclass

@dataclass
class EventData:
    """事件數據結構"""
    event_type: str
    data: Any
    timestamp: float

class EventDispatcher:
    """事件分發器 - 管理所有事件的分發和處理"""
    
    def __init__(self):
        """初始化事件分發器"""
        # 事件處理器列表
        self.quote_handlers = []  # 報價事件處理器
        self.reply_handlers = []  # 回報事件處理器
        self.connect_handlers = []  # 連線事件處理器
        
        # 事件隊列
        self.event_queue = queue.Queue(maxsize=1000)
        
        # 控制變數
        self.running = False
        self.dispatch_thread = None
        
        # 統計
        self.event_count = 0
        self.error_count = 0
        
        print("✅ [EventDispatcher] 事件分發器初始化完成")
    
    def start(self) -> None:
        """啟動事件分發器"""
        if self.running:
            return
        
        self.running = True
        self.dispatch_thread = threading.Thread(target=self._dispatch_loop, daemon=True)
        self.dispatch_thread.start()
        
        print("🚀 [EventDispatcher] 事件分發器已啟動")
    
    def stop(self) -> None:
        """停止事件分發器"""
        if not self.running:
            return
        
        self.running = False
        
        # 等待分發線程結束
        if self.dispatch_thread and self.dispatch_thread.is_alive():
            self.dispatch_thread.join(timeout=1.0)
        
        print(f"🛑 [EventDispatcher] 事件分發器已停止 - 處理事件: {self.event_count}, 錯誤: {self.error_count}")
    
    def register_quote_handler(self, handler) -> None:
        """註冊報價事件處理器"""
        if handler not in self.quote_handlers:
            self.quote_handlers.append(handler)
            print(f"📝 [EventDispatcher] 註冊報價事件處理器: {type(handler).__name__}")
    
    def register_reply_handler(self, handler) -> None:
        """註冊回報事件處理器"""
        if handler not in self.reply_handlers:
            self.reply_handlers.append(handler)
            print(f"📝 [EventDispatcher] 註冊回報事件處理器: {type(handler).__name__}")
    
    def register_connect_handler(self, handler) -> None:
        """註冊連線事件處理器"""
        if handler not in self.connect_handlers:
            self.connect_handlers.append(handler)
            print(f"📝 [EventDispatcher] 註冊連線事件處理器: {type(handler).__name__}")

    def register_best5_handler(self, handler) -> None:
        """註冊五檔報價事件處理器"""
        # 五檔事件也通過quote_handlers處理
        if handler not in self.quote_handlers:
            self.quote_handlers.append(handler)
            print(f"📝 [EventDispatcher] 註冊五檔報價事件處理器: {type(handler).__name__}")
    
    def dispatch_quote_event(self, quote_data) -> None:
        """分發報價事件"""
        event = EventData(
            event_type="quote",
            data=quote_data,
            timestamp=time.time()
        )
        
        try:
            self.event_queue.put_nowait(event)
        except queue.Full:
            print("⚠️ [EventDispatcher] 事件隊列已滿，丟棄報價事件")
    
    def dispatch_best5_event(self, best5_data) -> None:
        """分發五檔事件"""
        event = EventData(
            event_type="best5",
            data=best5_data,
            timestamp=time.time()
        )
        
        try:
            self.event_queue.put_nowait(event)
        except queue.Full:
            print("⚠️ [EventDispatcher] 事件隊列已滿，丟棄五檔事件")
    
    def dispatch_reply_event(self, reply_data: str) -> None:
        """分發回報事件"""
        event = EventData(
            event_type="reply",
            data=reply_data,
            timestamp=time.time()
        )
        
        try:
            self.event_queue.put_nowait(event)
        except queue.Full:
            print("⚠️ [EventDispatcher] 事件隊列已滿，丟棄回報事件")
    
    def trigger_connect_event(self, user_id: str, error_code: int) -> None:
        """觸發連線事件"""
        event = EventData(
            event_type="connect",
            data={"user_id": user_id, "error_code": error_code},
            timestamp=time.time()
        )
        
        try:
            self.event_queue.put_nowait(event)
        except queue.Full:
            print("⚠️ [EventDispatcher] 事件隊列已滿，丟棄連線事件")
    
    def _dispatch_loop(self) -> None:
        """事件分發主循環"""
        print("📡 [EventDispatcher] 事件分發循環開始")
        
        while self.running:
            try:
                # 取得事件 (超時1秒)
                event = self.event_queue.get(timeout=1.0)
                
                # 分發事件
                self._process_event(event)
                
                self.event_count += 1
                
            except queue.Empty:
                continue  # 超時，繼續等待
            except Exception as e:
                print(f"❌ [EventDispatcher] 事件處理錯誤: {e}")
                self.error_count += 1
        
        print("📡 [EventDispatcher] 事件分發循環結束")
    
    def _process_event(self, event: EventData) -> None:
        """處理單個事件"""
        try:
            if event.event_type == "quote":
                self._process_quote_event(event.data)
            elif event.event_type == "best5":
                self._process_best5_event(event.data)
            elif event.event_type == "reply":
                self._process_reply_event(event.data)
            elif event.event_type == "connect":
                self._process_connect_event(event.data)
            else:
                print(f"⚠️ [EventDispatcher] 未知事件類型: {event.event_type}")
                
        except Exception as e:
            print(f"❌ [EventDispatcher] 事件處理失敗: {e}")
            self.error_count += 1
    
    def _process_quote_event(self, quote_data) -> None:
        """處理報價事件"""
        for handler in self.quote_handlers:
            try:
                # 調用 OnNotifyTicksLONG 方法
                if hasattr(handler, 'OnNotifyTicksLONG'):
                    handler.OnNotifyTicksLONG(
                        quote_data.market_no,
                        quote_data.stock_idx,
                        0,  # nPtr
                        quote_data.date,
                        quote_data.time_hms,
                        quote_data.time_ms,
                        quote_data.bid_price,
                        quote_data.ask_price,
                        quote_data.close_price,
                        quote_data.quantity,
                        quote_data.simulate
                    )
            except Exception as e:
                print(f"❌ [EventDispatcher] 報價事件處理失敗: {e}")
    
    def _process_best5_event(self, best5_data) -> None:
        """處理五檔事件"""
        for handler in self.quote_handlers:
            try:
                # 調用 OnNotifyBest5LONG 方法
                if hasattr(handler, 'OnNotifyBest5LONG'):
                    # 🔧 修復：匹配virtual_simple_integrated.py第二個方法的參數格式
                    # 格式：sMarketNo, nStockidx, nPtr, 買方五檔, 賣方五檔, nSimulate
                    handler.OnNotifyBest5LONG(
                        best5_data.market_no,
                        best5_data.stock_idx,
                        0,  # nPtr
                        # 買方五檔 (價格, 數量) x 5
                        best5_data.bid_prices[0], best5_data.bid_qtys[0],
                        best5_data.bid_prices[1], best5_data.bid_qtys[1],
                        best5_data.bid_prices[2], best5_data.bid_qtys[2],
                        best5_data.bid_prices[3], best5_data.bid_qtys[3],
                        best5_data.bid_prices[4], best5_data.bid_qtys[4],
                        # 賣方五檔 (價格, 數量) x 5
                        best5_data.ask_prices[0], best5_data.ask_qtys[0],
                        best5_data.ask_prices[1], best5_data.ask_qtys[1],
                        best5_data.ask_prices[2], best5_data.ask_qtys[2],
                        best5_data.ask_prices[3], best5_data.ask_qtys[3],
                        best5_data.ask_prices[4], best5_data.ask_qtys[4],
                        # 模擬標記
                        best5_data.simulate
                    )
            except Exception as e:
                print(f"❌ [EventDispatcher] 五檔事件處理失敗: {e}")
    
    def _process_reply_event(self, reply_data: str) -> None:
        """處理回報事件"""
        for handler in self.reply_handlers:
            try:
                # 調用 OnNewData 方法
                if hasattr(handler, 'OnNewData'):
                    handler.OnNewData("virtual_user", reply_data)
            except Exception as e:
                print(f"❌ [EventDispatcher] 回報事件處理失敗: {e}")
    
    def _process_connect_event(self, connect_data: dict) -> None:
        """處理連線事件"""
        for handler in self.connect_handlers:
            try:
                # 調用 OnConnect 方法
                if hasattr(handler, 'OnConnect'):
                    handler.OnConnect(connect_data["user_id"], connect_data["error_code"])
            except Exception as e:
                print(f"❌ [EventDispatcher] 連線事件處理失敗: {e}")
    
    def get_statistics(self) -> dict:
        """取得統計資訊"""
        return {
            "running": self.running,
            "event_count": self.event_count,
            "error_count": self.error_count,
            "queue_size": self.event_queue.qsize(),
            "handlers": {
                "quote": len(self.quote_handlers),
                "reply": len(self.reply_handlers),
                "connect": len(self.connect_handlers)
            }
        }
    
    def clear_handlers(self) -> None:
        """清除所有事件處理器"""
        self.quote_handlers.clear()
        self.reply_handlers.clear()
        self.connect_handlers.clear()
        print("🧹 [EventDispatcher] 所有事件處理器已清除")
