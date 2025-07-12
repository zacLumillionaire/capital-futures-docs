#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
即時報價管理器 - 五檔ASK價格提取系統
專門用於實際下單功能的報價數據管理

功能:
1. 即時接收OnNotifyBest5LONG事件
2. 緩存五檔買賣價格和數量
3. 提供最佳ASK價格查詢API
4. 數據新鮮度驗證機制
5. 線程安全保護

設計原則:
- 完全獨立模組，不影響現有功能
- Console輸出為主，避免GIL風險
- 高效能數據緩存和查詢
"""

import time
import threading
from datetime import datetime, timedelta
from typing import Optional, Dict, List, Tuple


class QuoteData:
    """報價數據結構"""
    
    def __init__(self):
        # 五檔ASK數據
        self.ask_prices = [None] * 5      # [ask1, ask2, ask3, ask4, ask5]
        self.ask_quantities = [None] * 5  # [qty1, qty2, qty3, qty4, qty5]
        
        # 五檔BID數據
        self.bid_prices = [None] * 5      # [bid1, bid2, bid3, bid4, bid5]
        self.bid_quantities = [None] * 5  # [qty1, qty2, qty3, qty4, qty5]
        
        # 成交數據
        self.last_price = None            # 最新成交價
        self.last_volume = None           # 最新成交量
        
        # 時間戳
        self.last_update = None           # 最後更新時間
        self.update_count = 0             # 更新次數
        
        # 商品資訊
        self.product_code = None          # 商品代碼
        self.market_no = None             # 市場代碼
        self.stock_idx = None             # 股票索引


class RealTimeQuoteManager:
    """即時報價管理器"""
    
    def __init__(self, console_enabled=True):
        """
        初始化報價管理器
        
        Args:
            console_enabled: 是否啟用Console輸出
        """
        # 數據存儲
        self.quote_data = {}              # {product_code: QuoteData}
        self.console_enabled = console_enabled
        
        # 線程安全鎖
        self.data_lock = threading.Lock()
        
        # 統計數據
        self.total_updates = 0
        self.start_time = time.time()
        
        # 配置參數
        self.max_data_age_seconds = 10    # 數據最大有效期(秒)
        self.supported_products = ['MTX00', 'TM0000']  # 支援的商品
        
        if self.console_enabled:
            print(f"[QUOTE_MGR] 即時報價管理器已初始化")
            print(f"[QUOTE_MGR] 支援商品: {', '.join(self.supported_products)}")
    
    def update_best5_data(self, market_no, stock_idx, 
                         ask1, ask1_qty, ask2, ask2_qty, ask3, ask3_qty,
                         ask4, ask4_qty, ask5, ask5_qty,
                         bid1, bid1_qty, bid2, bid2_qty, bid3, bid3_qty,
                         bid4, bid4_qty, bid5, bid5_qty,
                         product_code=None):
        """
        更新五檔數據 - 從OnNotifyBest5LONG事件調用
        
        Args:
            market_no: 市場代碼
            stock_idx: 股票索引
            ask1-ask5: 五檔賣價
            ask1_qty-ask5_qty: 五檔賣量
            bid1-bid5: 五檔買價
            bid1_qty-bid5_qty: 五檔買量
            product_code: 商品代碼 (可選)
        
        Returns:
            bool: 更新是否成功
        """
        try:
            with self.data_lock:
                # 確定商品代碼
                if not product_code:
                    # 根據stock_idx推斷商品代碼 (需要根據實際API調整)
                    product_code = self._infer_product_code(market_no, stock_idx)
                
                if not product_code:
                    return False
                
                # 初始化或取得報價數據
                if product_code not in self.quote_data:
                    self.quote_data[product_code] = QuoteData()
                
                quote = self.quote_data[product_code]
                
                # 更新五檔ASK數據
                quote.ask_prices = [ask1, ask2, ask3, ask4, ask5]
                quote.ask_quantities = [ask1_qty, ask2_qty, ask3_qty, ask4_qty, ask5_qty]
                
                # 更新五檔BID數據
                quote.bid_prices = [bid1, bid2, bid3, bid4, bid5]
                quote.bid_quantities = [bid1_qty, bid2_qty, bid3_qty, bid4_qty, bid5_qty]
                
                # 更新元數據
                quote.last_update = datetime.now()
                quote.update_count += 1
                quote.product_code = product_code
                quote.market_no = market_no
                quote.stock_idx = stock_idx
                
                # 統計更新
                self.total_updates += 1
                
                # Console輸出 (可控制)
                if self.console_enabled and self.total_updates % 100 == 0:  # 每100次更新輸出一次
                    print(f"[QUOTE_MGR] {product_code} 五檔更新 #{quote.update_count} ASK1:{ask1} BID1:{bid1}")
                
                return True
                
        except Exception as e:
            if self.console_enabled:
                print(f"[QUOTE_MGR] ❌ 五檔數據更新失敗: {e}")
            return False
    
    def get_best_ask_price(self, product_code: str) -> Optional[float]:
        """
        取得最佳賣價 - 策略進場使用
        
        Args:
            product_code: 商品代碼 (MTX00/TM0000)
            
        Returns:
            float: 最佳賣價，如果無數據則返回None
        """
        try:
            with self.data_lock:
                if product_code not in self.quote_data:
                    return None
                
                quote = self.quote_data[product_code]
                
                # 檢查數據新鮮度
                if not self.is_quote_fresh(product_code):
                    if self.console_enabled:
                        print(f"[QUOTE_MGR] ⚠️ {product_code} 報價數據過期")
                    return None
                
                # 返回最佳賣價 (ASK1)
                ask1 = quote.ask_prices[0] if quote.ask_prices else None
                
                if ask1 is not None and ask1 > 0:
                    return float(ask1)
                
                return None
                
        except Exception as e:
            if self.console_enabled:
                print(f"[QUOTE_MGR] ❌ 取得ASK價格失敗: {e}")
            return None
    
    def get_ask_depth(self, product_code: str, levels: int = 5) -> List[Tuple[float, int]]:
        """
        取得ASK深度 - 大量下單參考
        
        Args:
            product_code: 商品代碼
            levels: 檔數 (1-5)
            
        Returns:
            List[Tuple[float, int]]: [(價格, 數量), ...] 列表
        """
        try:
            with self.data_lock:
                if product_code not in self.quote_data:
                    return []
                
                quote = self.quote_data[product_code]
                
                if not self.is_quote_fresh(product_code):
                    return []
                
                depth = []
                levels = min(levels, 5)  # 最多5檔
                
                for i in range(levels):
                    price = quote.ask_prices[i] if i < len(quote.ask_prices) else None
                    qty = quote.ask_quantities[i] if i < len(quote.ask_quantities) else None
                    
                    if price is not None and qty is not None and price > 0 and qty > 0:
                        depth.append((float(price), int(qty)))
                
                return depth
                
        except Exception as e:
            if self.console_enabled:
                print(f"[QUOTE_MGR] ❌ 取得ASK深度失敗: {e}")
            return []
    
    def get_last_trade_price(self, product_code: str) -> Optional[float]:
        """
        取得最新成交價 - 重試時使用
        
        Args:
            product_code: 商品代碼
            
        Returns:
            float: 最新成交價，如果無數據則返回None
        """
        try:
            with self.data_lock:
                if product_code not in self.quote_data:
                    return None
                
                quote = self.quote_data[product_code]
                
                if not self.is_quote_fresh(product_code):
                    return None
                
                if quote.last_price is not None and quote.last_price > 0:
                    return float(quote.last_price)
                
                # 如果沒有成交價，使用中間價估算
                ask1 = quote.ask_prices[0] if quote.ask_prices else None
                bid1 = quote.bid_prices[0] if quote.bid_prices else None
                
                if ask1 is not None and bid1 is not None and ask1 > 0 and bid1 > 0:
                    return (float(ask1) + float(bid1)) / 2
                
                return None
                
        except Exception as e:
            if self.console_enabled:
                print(f"[QUOTE_MGR] ❌ 取得成交價失敗: {e}")
            return None
    
    def is_quote_fresh(self, product_code: str, max_age_seconds: int = None) -> bool:
        """
        檢查報價新鮮度
        
        Args:
            product_code: 商品代碼
            max_age_seconds: 最大有效期(秒)，默認使用配置值
            
        Returns:
            bool: 數據是否新鮮
        """
        try:
            if product_code not in self.quote_data:
                return False
            
            quote = self.quote_data[product_code]
            
            if quote.last_update is None:
                return False
            
            max_age = max_age_seconds or self.max_data_age_seconds
            age = (datetime.now() - quote.last_update).total_seconds()
            
            return age <= max_age
            
        except Exception as e:
            return False
    
    def get_quote_summary(self, product_code: str) -> Optional[Dict]:
        """
        取得報價摘要 - 用於監控和調試
        
        Args:
            product_code: 商品代碼
            
        Returns:
            Dict: 報價摘要資訊
        """
        try:
            with self.data_lock:
                if product_code not in self.quote_data:
                    return None
                
                quote = self.quote_data[product_code]
                
                return {
                    'product_code': product_code,
                    'ask1': quote.ask_prices[0] if quote.ask_prices else None,
                    'ask1_qty': quote.ask_quantities[0] if quote.ask_quantities else None,
                    'bid1': quote.bid_prices[0] if quote.bid_prices else None,
                    'bid1_qty': quote.bid_quantities[0] if quote.bid_quantities else None,
                    'last_price': quote.last_price,
                    'last_update': quote.last_update,
                    'update_count': quote.update_count,
                    'is_fresh': self.is_quote_fresh(product_code),
                    'age_seconds': (datetime.now() - quote.last_update).total_seconds() if quote.last_update else None
                }
                
        except Exception as e:
            if self.console_enabled:
                print(f"[QUOTE_MGR] ❌ 取得報價摘要失敗: {e}")
            return None
    
    def _infer_product_code(self, market_no, stock_idx) -> Optional[str]:
        """
        根據市場代碼和股票索引推斷商品代碼
        
        Args:
            market_no: 市場代碼
            stock_idx: 股票索引
            
        Returns:
            str: 商品代碼，如果無法推斷則返回None
        """
        # 這裡需要根據實際的群益API規則來實現
        # 暫時返回預設值，後續需要根據實際測試調整
        try:
            # 期貨市場通常是特定的市場代碼
            if market_no == "TF":  # 假設期貨市場代碼
                # 根據stock_idx判斷具體商品
                # 這裡需要實際測試來確定對應關係
                return "MTX00"  # 預設返回大台
            
            return None
            
        except Exception:
            return None
    
    def get_statistics(self) -> Dict:
        """
        取得統計資訊
        
        Returns:
            Dict: 統計資訊
        """
        try:
            with self.data_lock:
                uptime = time.time() - self.start_time
                
                return {
                    'total_updates': self.total_updates,
                    'uptime_seconds': uptime,
                    'updates_per_second': self.total_updates / uptime if uptime > 0 else 0,
                    'tracked_products': list(self.quote_data.keys()),
                    'product_count': len(self.quote_data)
                }
                
        except Exception as e:
            return {'error': str(e)}


# 測試函數
def test_quote_manager():
    """測試報價管理器功能"""
    print("🧪 測試即時報價管理器...")
    
    # 創建管理器
    manager = RealTimeQuoteManager(console_enabled=True)
    
    # 模擬五檔數據更新
    print("\n📊 模擬五檔數據更新...")
    success = manager.update_best5_data(
        market_no="TF", stock_idx=1,
        ask1=22515, ask1_qty=10, ask2=22516, ask2_qty=8, ask3=22517, ask3_qty=5,
        ask4=22518, ask4_qty=3, ask5=22519, ask5_qty=2,
        bid1=22514, bid1_qty=12, bid2=22513, bid2_qty=9, bid3=22512, bid3_qty=6,
        bid4=22511, bid4_qty=4, bid5=22510, bid5_qty=1,
        product_code="MTX00"
    )
    print(f"更新結果: {'成功' if success else '失敗'}")
    
    # 測試ASK價格取得
    print("\n💰 測試ASK價格取得...")
    ask_price = manager.get_best_ask_price("MTX00")
    print(f"最佳ASK價格: {ask_price}")
    
    # 測試ASK深度
    print("\n📈 測試ASK深度...")
    ask_depth = manager.get_ask_depth("MTX00", 3)
    print(f"ASK深度(3檔): {ask_depth}")
    
    # 測試報價摘要
    print("\n📋 測試報價摘要...")
    summary = manager.get_quote_summary("MTX00")
    if summary:
        print(f"報價摘要: ASK1={summary['ask1']} BID1={summary['bid1']} 更新次數={summary['update_count']}")
    
    # 測試統計資訊
    print("\n📊 測試統計資訊...")
    stats = manager.get_statistics()
    print(f"統計: 總更新={stats['total_updates']} 追蹤商品={stats['tracked_products']}")
    
    print("\n✅ 報價管理器測試完成")


if __name__ == "__main__":
    test_quote_manager()
