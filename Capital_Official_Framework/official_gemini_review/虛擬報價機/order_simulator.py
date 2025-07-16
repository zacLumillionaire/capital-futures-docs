# 下單模擬器
# Order Simulator for Virtual Quote Machine

import time
import threading
import random
from datetime import datetime
from typing import Dict, Any, Optional, Tuple
from dataclasses import dataclass

@dataclass
class OrderInfo:
    """訂單資訊"""
    order_id: str
    account: str
    product: str
    buy_sell: int  # 0=買, 1=賣
    price: int
    quantity: int
    order_type: int  # 0=ROD, 1=IOC, 2=FOK
    new_close: int  # 0=新倉, 1=平倉
    day_trade: int  # 0=否, 1=當沖
    timestamp: float
    status: str = "PENDING"  # PENDING, FILLED, CANCELLED, REJECTED

class OrderSimulator:
    """下單模擬器 - 處理下單請求和生成回報"""
    
    def __init__(self, config_manager, event_dispatcher):
        """
        初始化下單模擬器
        
        Args:
            config_manager: 配置管理器
            event_dispatcher: 事件分發器
        """
        self.config = config_manager
        self.event_dispatcher = event_dispatcher
        
        # 配置參數
        self.fill_probability = self.config.get_fill_probability()
        self.fill_delay_ms = self.config.get_fill_delay_ms()
        self.default_account = self.config.get_default_account()
        
        # 訂單管理
        self.orders: Dict[str, OrderInfo] = {}
        self.order_counter = 0
        
        # 控制變數
        self.running = False
        
        # 統計
        self.total_orders = 0
        self.filled_orders = 0
        self.cancelled_orders = 0
        
        print(f"✅ [OrderSimulator] 下單模擬器初始化完成 - 成交機率: {self.fill_probability}")
    
    def start(self) -> None:
        """啟動下單模擬器"""
        self.running = True
        print("🚀 [OrderSimulator] 下單模擬器已啟動")
    
    def stop(self) -> None:
        """停止下單模擬器"""
        self.running = False
        print(f"🛑 [OrderSimulator] 下單模擬器已停止 - 總訂單: {self.total_orders}, 成交: {self.filled_orders}")
    
    def process_order(self, user_id: str, async_flag: bool, order_obj) -> Tuple[str, int]:
        """
        處理下單請求
        
        Args:
            user_id: 使用者ID
            async_flag: 異步標記
            order_obj: 下單物件
            
        Returns:
            Tuple[委託序號, 狀態碼]
        """
        try:
            # 生成委託序號
            self.order_counter += 1
            order_id = f"VQ{int(time.time() * 1000) % 100000000:08d}"
            
            # 解析下單參數
            order_info = self._parse_order_object(order_id, order_obj)
            
            # 儲存訂單
            self.orders[order_id] = order_info
            self.total_orders += 1
            
            print(f"📋 [OrderSimulator] 接收下單: {order_id} - {self._format_order_info(order_info)}")
            
            # 異步處理訂單
            threading.Thread(target=self._process_order_async, args=(order_info,), daemon=True).start()
            
            return (order_id, 0)  # 成功
            
        except Exception as e:
            print(f"❌ [OrderSimulator] 下單處理失敗: {e}")
            return ("", -1)  # 失敗
    
    def _parse_order_object(self, order_id: str, order_obj) -> OrderInfo:
        """解析下單物件"""
        return OrderInfo(
            order_id=order_id,
            account=getattr(order_obj, 'bstrFullAccount', self.default_account),
            product=getattr(order_obj, 'bstrStockNo', 'MTX00'),
            buy_sell=getattr(order_obj, 'sBuySell', 0),
            price=int(getattr(order_obj, 'bstrPrice', '21500')),
            quantity=getattr(order_obj, 'nQty', 1),
            order_type=getattr(order_obj, 'sTradeType', 2),  # 預設FOK
            new_close=getattr(order_obj, 'sNewClose', 0),
            day_trade=getattr(order_obj, 'sDayTrade', 1),
            timestamp=time.time()
        )
    
    def _process_order_async(self, order_info: OrderInfo) -> None:
        """異步處理訂單"""
        try:
            # 1. 發送新單回報
            self._send_new_order_reply(order_info)
            
            # 2. 等待處理延遲
            delay_seconds = self.fill_delay_ms / 1000.0
            time.sleep(delay_seconds)
            
            # 3. 決定是否成交
            if self._should_fill_order(order_info):
                self._fill_order(order_info)
            else:
                self._cancel_order(order_info)
                
        except Exception as e:
            print(f"❌ [OrderSimulator] 訂單處理異常: {e}")
            self._reject_order(order_info, str(e))
    
    def _should_fill_order(self, order_info: OrderInfo) -> bool:
        """判斷訂單是否應該成交"""
        # 基本成交機率
        if random.random() > self.fill_probability:
            return False
        
        # FOK單特殊處理 (全部成交或全部取消)
        if order_info.order_type == 2:  # FOK
            return True  # FOK單如果決定成交就全部成交
        
        return True
    
    def _send_new_order_reply(self, order_info: OrderInfo) -> None:
        """發送新單回報"""
        reply_data = self._generate_reply_data(order_info, "N", 0, 0)
        self.event_dispatcher.dispatch_reply_event(reply_data)
        print(f"📤 [OrderSimulator] 新單回報: {order_info.order_id}")
    
    def _fill_order(self, order_info: OrderInfo) -> None:
        """成交訂單"""
        order_info.status = "FILLED"
        self.filled_orders += 1
        
        # 計算成交價格 (使用當前市價)
        fill_price = self._get_fill_price(order_info)
        
        # 發送成交回報
        reply_data = self._generate_reply_data(order_info, "D", fill_price, order_info.quantity)
        self.event_dispatcher.dispatch_reply_event(reply_data)
        
        print(f"✅ [OrderSimulator] 訂單成交: {order_info.order_id} @ {fill_price}")
    
    def _cancel_order(self, order_info: OrderInfo) -> None:
        """取消訂單"""
        order_info.status = "CANCELLED"
        self.cancelled_orders += 1
        
        # 發送取消回報
        reply_data = self._generate_reply_data(order_info, "C", 0, 0)
        self.event_dispatcher.dispatch_reply_event(reply_data)
        
        print(f"❌ [OrderSimulator] 訂單取消: {order_info.order_id}")
    
    def _reject_order(self, order_info: OrderInfo, reason: str) -> None:
        """拒絕訂單"""
        order_info.status = "REJECTED"
        
        # 發送拒絕回報
        reply_data = self._generate_reply_data(order_info, "R", 0, 0)
        self.event_dispatcher.dispatch_reply_event(reply_data)
        
        print(f"🚫 [OrderSimulator] 訂單拒絕: {order_info.order_id} - {reason}")
    
    def _get_fill_price(self, order_info: OrderInfo) -> int:
        """取得成交價格"""
        # 簡化處理：使用委託價格
        # 實際應該根據買賣方向使用買一/賣一價格
        return order_info.price
    
    def _generate_reply_data(self, order_info: OrderInfo, status: str, fill_price: int, fill_qty: int) -> str:
        """生成回報數據"""
        now = datetime.now()
        
        # 回報數據格式 (逗號分隔)
        reply_fields = [
            order_info.order_id,                    # [0] 委託序號
            order_info.account,                     # [1] 帳號
            order_info.product,                     # [2] 商品代碼
            str(order_info.buy_sell),               # [3] 買賣別
            str(order_info.price),                  # [4] 委託價格
            str(order_info.quantity),               # [5] 委託數量
            str(fill_price),                        # [6] 成交價格
            str(fill_qty),                          # [7] 成交數量
            status,                                 # [8] 委託狀態
            now.strftime('%H%M%S'),                 # [9] 委託時間
            "0",                                    # [10] 錯誤代碼
            "",                                     # [11] 錯誤訊息
            str(order_info.order_type),             # [12] 委託類型
            str(order_info.new_close),              # [13] 新平倉
            str(order_info.day_trade),              # [14] 當沖
            "Virtual",                              # [15] 來源
            now.strftime('%Y%m%d'),                 # [16] 日期
            str(int(now.timestamp() * 1000)),       # [17] 時間戳
            "0",                                    # [18] 市場代號
            "0",                                    # [19] 商品索引
            "",                                     # [20] 備註1
            "",                                     # [21] 備註2
            "",                                     # [22] 備註3
            "",                                     # [23] 備註4
            ""                                      # [24] 備註5
        ]
        
        return ",".join(reply_fields)
    
    def _format_order_info(self, order_info: OrderInfo) -> str:
        """格式化訂單資訊"""
        buy_sell_text = "買進" if order_info.buy_sell == 0 else "賣出"
        order_type_text = ["ROD", "IOC", "FOK"][order_info.order_type]
        return f"{buy_sell_text} {order_info.product} {order_info.quantity}口 @{order_info.price} ({order_type_text})"
    
    def get_order_info(self, order_id: str) -> Optional[OrderInfo]:
        """取得訂單資訊"""
        return self.orders.get(order_id)
    
    def get_statistics(self) -> Dict[str, Any]:
        """取得統計資訊"""
        return {
            "running": self.running,
            "total_orders": self.total_orders,
            "filled_orders": self.filled_orders,
            "cancelled_orders": self.cancelled_orders,
            "pending_orders": len([o for o in self.orders.values() if o.status == "PENDING"]),
            "fill_rate": self.filled_orders / self.total_orders if self.total_orders > 0 else 0
        }
    
    def clear_orders(self) -> None:
        """清除所有訂單"""
        self.orders.clear()
        print("🧹 [OrderSimulator] 所有訂單已清除")
