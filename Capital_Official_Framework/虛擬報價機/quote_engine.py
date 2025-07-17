# 報價生成引擎
# Quote Engine for Virtual Quote Machine

import time
import threading
import random
import math
from datetime import datetime, timedelta
from typing import Optional, Dict, Any, Callable
from dataclasses import dataclass

@dataclass
class QuoteData:
    """報價數據結構"""
    market_no: int = 1
    stock_idx: int = 0
    date: int = 0  # YYYYMMDD
    time_hms: int = 0  # HHMMSS
    time_ms: int = 0  # 毫秒
    bid_price: int = 0  # 買一價 (*100)
    ask_price: int = 0  # 賣一價 (*100)
    close_price: int = 0  # 成交價 (*100)
    quantity: int = 1  # 成交量
    simulate: int = 0  # 模擬標記

@dataclass
class Best5Data:
    """五檔數據結構"""
    market_no: int = 1
    stock_idx: int = 0
    date: int = 0
    time_hms: int = 0
    time_ms: int = 0
    # 買方五檔 (由高到低)
    bid_prices: list = None
    bid_qtys: list = None
    # 賣方五檔 (由低到高)
    ask_prices: list = None
    ask_qtys: list = None
    simulate: int = 0

class VirtualQuoteEngine:
    """虛擬報價引擎"""
    
    def __init__(self, config_manager, event_dispatcher):
        """
        初始化報價引擎
        
        Args:
            config_manager: 配置管理器
            event_dispatcher: 事件分發器
        """
        self.config = config_manager
        self.event_dispatcher = event_dispatcher
        
        # 報價參數
        self.base_price = self.config.get_base_price()
        self.price_range = self.config.get_price_range()
        self.spread = self.config.get_spread()
        self.quote_interval = self.config.get_quote_interval()
        self.volatility = self.config.get('virtual_quote_config.volatility', 0.02)
        self.trend_factor = self.config.get('virtual_quote_config.trend_factor', 0.0)
        
        # 當前狀態
        self.current_price = self.base_price
        self.current_bid = self.base_price - self.spread // 2
        self.current_ask = self.base_price + self.spread // 2
        self.last_update_time = time.time()
        
        # 控制變數
        self.running = False
        self.quote_thread = None
        self.product = "MTX00"
        
        # 統計
        self.quote_count = 0
        self.start_time = None
        
        print(f"✅ [QuoteEngine] 初始化完成 - 基準價格: {self.base_price}")
    
    def start_quote_feed(self, product: str = "MTX00") -> None:
        """啟動報價推送"""
        if self.running:
            print("⚠️ [QuoteEngine] 報價推送已在運行中")
            return
        
        self.product = product
        self.running = True
        self.start_time = time.time()
        self.quote_count = 0
        
        # 啟動報價線程
        self.quote_thread = threading.Thread(target=self._quote_loop, daemon=True)
        self.quote_thread.start()
        
        print(f"🚀 [QuoteEngine] 報價推送已啟動 - 商品: {product}, 間隔: {self.quote_interval}秒")
    
    def stop_quote_feed(self) -> None:
        """停止報價推送"""
        if not self.running:
            return
        
        self.running = False
        
        if self.quote_thread and self.quote_thread.is_alive():
            self.quote_thread.join(timeout=1.0)
        
        elapsed = time.time() - self.start_time if self.start_time else 0
        print(f"🛑 [QuoteEngine] 報價推送已停止 - 運行時間: {elapsed:.1f}秒, 推送次數: {self.quote_count}")
    
    def _quote_loop(self) -> None:
        """報價推送主循環"""
        print(f"📊 [QuoteEngine] 報價循環開始")
        
        while self.running:
            try:
                # 生成新報價
                quote_data = self._generate_quote()
                
                # 推送報價事件
                self._dispatch_quote_event(quote_data)
                
                # 生成五檔數據 (如果啟用)
                if self.config.get('best5_config.enabled', True):
                    best5_data = self._generate_best5(quote_data)
                    self._dispatch_best5_event(best5_data)
                
                self.quote_count += 1
                
                # 等待下次推送
                time.sleep(self.quote_interval)
                
            except Exception as e:
                print(f"❌ [QuoteEngine] 報價循環錯誤: {e}")
                time.sleep(0.1)  # 短暫等待後繼續
        
        print(f"📊 [QuoteEngine] 報價循環結束")
    
    def _generate_quote(self) -> QuoteData:
        """生成報價數據"""
        now = datetime.now()
        
        # 價格變動模擬
        self._update_price()
        
        # 建立報價數據
        quote = QuoteData(
            market_no=self.config.get('market_config.market_no', 1),
            stock_idx=self.config.get('market_config.stock_idx', 0),
            date=int(now.strftime('%Y%m%d')),
            time_hms=int(now.strftime('%H%M%S')),
            time_ms=now.microsecond // 1000,
            bid_price=int(self.current_bid * 100),  # 群益API格式 (*100)
            ask_price=int(self.current_ask * 100),
            close_price=int(self.current_price * 100),
            quantity=random.randint(1, 5),
            simulate=0
        )
        
        return quote
    
    def _update_price(self) -> None:
        """更新價格 (模擬市場波動)"""
        # 隨機波動
        random_change = random.gauss(0, self.volatility) * self.price_range

        # 趨勢因子
        trend_change = self.trend_factor * self.price_range

        # 🔧 修復：邊界反彈機制，避免價格卡住
        price_min = self.base_price - self.price_range
        price_max = self.base_price + self.price_range

        # 如果接近邊界，增加反向力量
        if self.current_price >= price_max - 5:  # 接近上限
            trend_change -= abs(trend_change) * 2  # 強制向下
            random_change -= abs(random_change) * 0.5
        elif self.current_price <= price_min + 5:  # 接近下限
            trend_change += abs(trend_change) * 2  # 強制向上
            random_change += abs(random_change) * 0.5

        # 總變化
        total_change = random_change + trend_change

        # 更新價格 (限制在合理範圍內)
        new_price = self.current_price + total_change
        self.current_price = max(price_min, min(price_max, new_price))

        # 🔧 修復：如果仍然卡在邊界，強制小幅移動
        if self.current_price == price_max:
            self.current_price -= random.randint(1, 3)
        elif self.current_price == price_min:
            self.current_price += random.randint(1, 3)

        # 更新買賣價
        half_spread = self.spread / 2
        self.current_bid = self.current_price - half_spread
        self.current_ask = self.current_price + half_spread

        # 確保價格為整數
        self.current_price = round(self.current_price)
        self.current_bid = round(self.current_bid)
        self.current_ask = round(self.current_ask)
    
    def _generate_best5(self, quote_data: QuoteData) -> Best5Data:
        """生成五檔數據"""
        step = self.config.get('best5_config.price_step', 5)
        qty_range = self.config.get('best5_config.quantity_range', [10, 50])
        
        # 買方五檔 (由高到低)
        bid_prices = []
        bid_qtys = []
        for i in range(5):
            price = self.current_bid - (i * step)
            qty = random.randint(qty_range[0], qty_range[1])
            bid_prices.append(int(price * 100))
            bid_qtys.append(qty)
        
        # 賣方五檔 (由低到高)
        ask_prices = []
        ask_qtys = []
        for i in range(5):
            price = self.current_ask + (i * step)
            qty = random.randint(qty_range[0], qty_range[1])
            ask_prices.append(int(price * 100))
            ask_qtys.append(qty)
        
        best5 = Best5Data(
            market_no=quote_data.market_no,
            stock_idx=quote_data.stock_idx,
            date=quote_data.date,
            time_hms=quote_data.time_hms,
            time_ms=quote_data.time_ms,
            bid_prices=bid_prices,
            bid_qtys=bid_qtys,
            ask_prices=ask_prices,
            ask_qtys=ask_qtys,
            simulate=0
        )
        
        return best5
    
    def _dispatch_quote_event(self, quote_data: QuoteData) -> None:
        """分發報價事件"""
        if self.event_dispatcher:
            self.event_dispatcher.dispatch_quote_event(quote_data)
    
    def _dispatch_best5_event(self, best5_data: Best5Data) -> None:
        """分發五檔事件"""
        if self.event_dispatcher:
            self.event_dispatcher.dispatch_best5_event(best5_data)
    
    def get_current_price(self) -> float:
        """取得當前價格"""
        return self.current_price
    
    def get_current_bid(self) -> float:
        """取得當前買一價"""
        return self.current_bid
    
    def get_current_ask(self) -> float:
        """取得當前賣一價"""
        return self.current_ask
    
    def get_statistics(self) -> Dict[str, Any]:
        """取得統計資訊"""
        elapsed = time.time() - self.start_time if self.start_time else 0
        return {
            "running": self.running,
            "quote_count": self.quote_count,
            "elapsed_time": elapsed,
            "quotes_per_second": self.quote_count / elapsed if elapsed > 0 else 0,
            "current_price": self.current_price,
            "current_bid": self.current_bid,
            "current_ask": self.current_ask
        }
    
    def stop(self) -> None:
        """停止引擎"""
        self.stop_quote_feed()
