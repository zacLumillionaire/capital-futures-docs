# -*- coding: utf-8 -*-
"""
統一回報追蹤器
Unified Order Tracker

功能：
1. 虛實單統一追蹤 - 虛擬和實際訂單使用相同追蹤機制
2. OnNewData事件整合 - 處理群益實際回報
3. 虛擬回報模擬 - 模擬虛擬訂單的回報流程
4. 策略狀態同步 - 更新策略的部位狀態
5. Console統一通知 - 虛實單都有一致的Console輸出

作者: Stage2 虛實單整合系統
日期: 2025-07-04
"""

import time
import threading
from datetime import datetime
from typing import Dict, Any, Optional, List, Callable
from dataclasses import dataclass
from enum import Enum


class OrderStatus(Enum):
    """訂單狀態"""
    PENDING = "pending"      # 待處理
    SUBMITTED = "submitted"  # 已送出
    FILLED = "filled"        # 已成交
    CANCELLED = "cancelled"  # 已取消
    REJECTED = "rejected"    # 已拒絕
    PARTIAL = "partial"      # 部分成交


class OrderType(Enum):
    """訂單類型"""
    VIRTUAL = "virtual"  # 虛擬訂單
    REAL = "real"       # 實際訂單


@dataclass
class OrderInfo:
    """訂單資訊"""
    order_id: str           # 訂單ID
    order_type: OrderType   # 訂單類型
    product: str           # 商品代碼
    direction: str         # 買賣方向
    quantity: int          # 數量
    price: float           # 價格
    status: OrderStatus    # 狀態
    submit_time: datetime  # 送出時間
    fill_time: Optional[datetime] = None    # 成交時間
    fill_price: Optional[float] = None      # 成交價格
    fill_quantity: int = 0                  # 成交數量
    api_seq_no: Optional[str] = None        # API序號
    signal_source: str = "unknown"          # 信號來源
    error_message: Optional[str] = None     # 錯誤訊息


class UnifiedOrderTracker:
    """統一回報追蹤器"""
    
    def __init__(self, strategy_manager=None, console_enabled=True):
        """
        初始化統一回報追蹤器
        
        Args:
            strategy_manager: 策略管理器 (用於更新策略狀態)
            console_enabled: 是否啟用Console輸出
        """
        # 基本設定
        self.strategy_manager = strategy_manager
        self.console_enabled = console_enabled
        
        # 訂單追蹤
        self.tracked_orders = {}  # {order_id: OrderInfo}
        self.api_seq_mapping = {} # {api_seq_no: order_id} API序號對應

        # 🔧 新增：時間窗口映射 (用於群益API序號不匹配的情況)
        self.pending_orders = {}   # {order_id: {'time': timestamp, 'price': price, 'direction': direction, 'product': product}}
        
        # 回調函數
        self.order_update_callbacks = []  # 訂單更新回調
        self.fill_callbacks = []          # 成交回調
        self.cancel_callbacks = []        # 🔧 新增：取消回調
        
        # 統計數據
        self.total_tracked = 0
        self.virtual_tracked = 0
        self.real_tracked = 0
        self.filled_orders = 0
        self.cancelled_orders = 0
        
        # 線程安全鎖
        self.data_lock = threading.Lock()
        
        if self.console_enabled:
            print("[ORDER_TRACKER] 統一回報追蹤器已初始化")
    
    def register_order(self, order_id: str, product: str, direction: str,
                      quantity: int, price: float, is_virtual: bool = False,
                      signal_source: str = "strategy", api_seq_no: str = None) -> bool:
        """
        註冊待追蹤訂單
        
        Args:
            order_id: 訂單ID
            product: 商品代碼
            direction: 買賣方向
            quantity: 數量
            price: 價格
            is_virtual: 是否為虛擬訂單
            signal_source: 信號來源
            api_seq_no: API序號 (實際訂單)
            
        Returns:
            bool: 註冊是否成功
        """
        try:
            with self.data_lock:
                # 建立訂單資訊
                order_info = OrderInfo(
                    order_id=order_id,
                    order_type=OrderType.VIRTUAL if is_virtual else OrderType.REAL,
                    product=product,
                    direction=direction,
                    quantity=quantity,
                    price=price,
                    status=OrderStatus.SUBMITTED,
                    submit_time=datetime.now(),
                    api_seq_no=api_seq_no,
                    signal_source=signal_source
                )
                
                # 註冊追蹤
                self.tracked_orders[order_id] = order_info
                
                # 建立API序號對應 (實際訂單)
                if api_seq_no:
                    self.api_seq_mapping[api_seq_no] = order_id

                # 🔧 新增：建立時間窗口映射 (用於群益API序號不匹配的情況)
                if not is_virtual:
                    import time
                    self.pending_orders[order_id] = {
                        'time': time.time(),
                        'price': price,
                        'direction': direction,
                        'product': product,
                        'quantity': quantity
                    }

                # 更新統計
                self.total_tracked += 1
                if is_virtual:
                    self.virtual_tracked += 1
                else:
                    self.real_tracked += 1
                
                # Console通知
                if self.console_enabled:
                    order_type_desc = "虛擬" if is_virtual else "實際"
                    print(f"[ORDER_TRACKER] 📝 註冊{order_type_desc}訂單: {order_id} "
                          f"{direction} {product} {quantity}口 @{price:.0f}")
                
                # 虛擬訂單立即模擬成交
                if is_virtual:
                    self._simulate_virtual_fill(order_id)
                
                return True
                
        except Exception as e:
            if self.console_enabled:
                print(f"[ORDER_TRACKER] ❌ 註冊訂單失敗: {e}")
            return False
    
    def process_real_order_reply(self, reply_data: str) -> bool:
        """
        處理實際訂單OnNewData回報
        
        Args:
            reply_data: OnNewData回報數據 (逗號分隔)
            
        Returns:
            bool: 處理是否成功
        """
        try:
            # 解析回報數據
            fields = reply_data.split(',')
            if len(fields) < 48:
                if self.console_enabled:
                    print(f"[ORDER_TRACKER] ⚠️ 回報欄位不足: {len(fields)} < 48")
                return False
            
            # 提取關鍵欄位 (根據您的OnNewData格式)
            order_type = fields[2] if len(fields) > 2 else ""      # Type
            order_err = fields[3] if len(fields) > 3 else ""       # OrderErr
            stock_no = fields[8] if len(fields) > 8 else ""        # 商品代號
            price = float(fields[11]) if fields[11] else 0         # 價格
            qty = int(fields[20]) if fields[20] else 0             # 數量
            key_no = fields[0] if len(fields) > 0 else ""           # 委託序號（KeyNo）
            seq_no = fields[47] if len(fields) > 47 else ""         # 序號（SeqNo）

            # 🔧 修復：使用KeyNo作為主要識別，SeqNo作為備用
            primary_id = key_no if key_no else seq_no

            # 根據委託序號找到對應訂單
            with self.data_lock:
                if self.console_enabled:
                    print(f"[ORDER_TRACKER] 🔍 處理回報: Type={order_type}, KeyNo={key_no}, SeqNo={seq_no}")
                    print(f"[ORDER_TRACKER] 🔍 已追蹤序號: {list(self.api_seq_mapping.keys())}")

                # 🔧 修復：先嘗試KeyNo，再嘗試SeqNo，最後嘗試API序號
                order_id = None
                if key_no and key_no in self.api_seq_mapping:
                    order_id = self.api_seq_mapping[key_no]
                elif seq_no and seq_no in self.api_seq_mapping:
                    order_id = self.api_seq_mapping[seq_no]
                elif primary_id and primary_id in self.api_seq_mapping:
                    order_id = self.api_seq_mapping[primary_id]

                if not order_id:
                    # 不是我們追蹤的訂單，忽略
                    if self.console_enabled:
                        print(f"[ORDER_TRACKER] ⚠️ 序號KeyNo={key_no}, SeqNo={seq_no}都不在追蹤列表中")
                    return False
                if order_id not in self.tracked_orders:
                    return False
                
                order_info = self.tracked_orders[order_id]
                
                # 處理不同類型的回報
                if order_type == "D":  # 成交
                    self._process_fill_reply(order_info, price, qty)
                elif order_type == "C":  # 取消
                    self._process_cancel_reply(order_info)
                elif order_type == "N" and order_err != "0000":  # 委託失敗
                    self._process_reject_reply(order_info, order_err)
                
                return True
                
        except Exception as e:
            if self.console_enabled:
                print(f"[ORDER_TRACKER] ❌ 處理實際回報失敗: {e}")
            return False
    
    def process_virtual_order_reply(self, order_id: str, result: Dict[str, Any]) -> bool:
        """
        處理虛擬訂單回報
        
        Args:
            order_id: 訂單ID
            result: 回報結果
            
        Returns:
            bool: 處理是否成功
        """
        try:
            with self.data_lock:
                if order_id not in self.tracked_orders:
                    return False
                
                order_info = self.tracked_orders[order_id]
                
                if result.get('success', False):
                    # 虛擬成交
                    self._process_fill_reply(order_info, order_info.price, order_info.quantity)
                else:
                    # 虛擬失敗
                    self._process_reject_reply(order_info, result.get('error', '虛擬下單失敗'))
                
                return True
                
        except Exception as e:
            if self.console_enabled:
                print(f"[ORDER_TRACKER] ❌ 處理虛擬回報失敗: {e}")
            return False
    
    def _simulate_virtual_fill(self, order_id: str):
        """模擬虛擬訂單成交"""
        def simulate_fill():
            time.sleep(0.2)  # 模擬延遲
            self.process_virtual_order_reply(order_id, {'success': True})
        
        # 在背景執行模擬
        threading.Thread(target=simulate_fill, daemon=True).start()
    
    def _process_fill_reply(self, order_info: OrderInfo, fill_price: float, fill_qty: int):
        """處理成交回報"""
        order_info.status = OrderStatus.FILLED
        order_info.fill_time = datetime.now()
        order_info.fill_price = fill_price
        order_info.fill_quantity = fill_qty
        
        # 更新統計
        self.filled_orders += 1
        
        # Console通知
        if self.console_enabled:
            order_type_desc = "虛擬" if order_info.order_type == OrderType.VIRTUAL else "實際"
            print(f"[ORDER_TRACKER] 🎉 {order_type_desc}成交: {order_info.order_id} "
                  f"{order_info.direction} {order_info.product} {fill_qty}口 @{fill_price:.0f}")
        
        # 更新策略狀態
        self._update_strategy_position(order_info)
        
        # 觸發成交回調
        self._trigger_fill_callbacks(order_info)
    
    def _process_cancel_reply(self, order_info: OrderInfo):
        """處理取消回報"""
        order_info.status = OrderStatus.CANCELLED
        self.cancelled_orders += 1

        if self.console_enabled:
            order_type_desc = "虛擬" if order_info.order_type == OrderType.VIRTUAL else "實際"
            print(f"[ORDER_TRACKER] 🗑️ {order_type_desc}取消: {order_info.order_id}")

        # 🔧 新增：觸發取消回調
        self._trigger_cancel_callbacks(order_info)
    
    def _process_reject_reply(self, order_info: OrderInfo, error_msg: str):
        """處理拒絕回報"""
        order_info.status = OrderStatus.REJECTED
        order_info.error_message = error_msg
        
        if self.console_enabled:
            order_type_desc = "虛擬" if order_info.order_type == OrderType.VIRTUAL else "實際"
            print(f"[ORDER_TRACKER] ❌ {order_type_desc}拒絕: {order_info.order_id} - {error_msg}")
    
    def _update_strategy_position(self, order_info: OrderInfo):
        """更新策略部位狀態"""
        try:
            if self.strategy_manager and hasattr(self.strategy_manager, 'update_position_from_fill'):
                self.strategy_manager.update_position_from_fill(
                    direction=order_info.direction,
                    quantity=order_info.fill_quantity,
                    price=order_info.fill_price,
                    order_id=order_info.order_id
                )
        except Exception as e:
            if self.console_enabled:
                print(f"[ORDER_TRACKER] ⚠️ 更新策略狀態失敗: {e}")
    
    def _trigger_fill_callbacks(self, order_info: OrderInfo):
        """觸發成交回調"""
        for callback in self.fill_callbacks:
            try:
                callback(order_info)
            except Exception as e:
                if self.console_enabled:
                    print(f"[ORDER_TRACKER] ⚠️ 成交回調失敗: {e}")
    
    def add_fill_callback(self, callback: Callable[[OrderInfo], None]):
        """添加成交回調函數"""
        self.fill_callbacks.append(callback)

    def add_cancel_callback(self, callback: Callable[[OrderInfo], None]):
        """添加取消回調函數"""
        self.cancel_callbacks.append(callback)

    def _trigger_cancel_callbacks(self, order_info: OrderInfo):
        """觸發取消回調"""
        for callback in self.cancel_callbacks:
            try:
                callback(order_info)
            except Exception as e:
                if self.console_enabled:
                    print(f"[ORDER_TRACKER] ⚠️ 取消回調失敗: {e}")
    
    def get_order_status(self, order_id: str) -> Optional[OrderInfo]:
        """取得訂單狀態"""
        with self.data_lock:
            return self.tracked_orders.get(order_id)
    
    def get_statistics(self) -> Dict[str, Any]:
        """取得統計資訊"""
        with self.data_lock:
            return {
                'total_tracked': self.total_tracked,
                'virtual_tracked': self.virtual_tracked,
                'real_tracked': self.real_tracked,
                'filled_orders': self.filled_orders,
                'cancelled_orders': self.cancelled_orders,
                'pending_orders': len([o for o in self.tracked_orders.values() 
                                     if o.status == OrderStatus.SUBMITTED]),
                'fill_rate': (self.filled_orders / self.total_tracked * 100) if self.total_tracked > 0 else 0
            }
    
    def print_status(self):
        """列印當前狀態"""
        if not self.console_enabled:
            return
        
        stats = self.get_statistics()
        print("\n" + "="*50)
        print("📊 統一回報追蹤器狀態")
        print("="*50)
        print(f"總追蹤數: {stats['total_tracked']}")
        print(f"虛擬訂單: {stats['virtual_tracked']}")
        print(f"實際訂單: {stats['real_tracked']}")
        print(f"已成交: {stats['filled_orders']}")
        print(f"已取消: {stats['cancelled_orders']}")
        print(f"待處理: {stats['pending_orders']}")
        print(f"成交率: {stats['fill_rate']:.1f}%")
        print("="*50 + "\n")


# 測試函數
def test_unified_order_tracker():
    """測試統一回報追蹤器"""
    print("🧪 測試統一回報追蹤器...")
    
    # 創建追蹤器
    tracker = UnifiedOrderTracker(console_enabled=True)
    
    # 測試虛擬訂單註冊
    print("\n📝 測試虛擬訂單註冊...")
    success = tracker.register_order(
        order_id="VIRT001",
        product="MTX00",
        direction="BUY",
        quantity=1,
        price=22515.0,
        is_virtual=True,
        signal_source="test_strategy"
    )
    print(f"虛擬訂單註冊: {'成功' if success else '失敗'}")
    
    # 等待虛擬成交
    time.sleep(0.5)
    
    # 測試統計
    print("\n📊 測試統計...")
    tracker.print_status()
    
    print("✅ 統一回報追蹤器測試完成")


if __name__ == "__main__":
    test_unified_order_tracker()
