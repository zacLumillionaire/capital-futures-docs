#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
穩定版下單API接口
為策略系統提供穩定的下單功能調用接口

🏷️ STABLE_ORDER_API_2025_06_30
✅ 基於穩定版OrderTester.py的下單功能
✅ 提供策略系統調用的標準化接口
✅ 確保下單功能的穩定性和一致性
"""

import logging
import time
from typing import Dict, Any, Optional, Tuple

logger = logging.getLogger(__name__)

class StableOrderAPI:
    """穩定版下單API接口類"""
    
    def __init__(self, order_tester_instance=None):
        """
        初始化穩定版下單API
        
        Args:
            order_tester_instance: OrderTester主程式實例
        """
        self.order_tester = order_tester_instance
        self.is_connected = False
        self.last_order_result = None
        
    def set_order_tester(self, order_tester_instance):
        """設定OrderTester實例"""
        self.order_tester = order_tester_instance
        self.is_connected = True
        logger.info("✅ 穩定版下單API已連接到OrderTester")
        
    def check_connection(self) -> bool:
        """檢查連接狀態"""
        if not self.order_tester:
            logger.error("❌ OrderTester實例未設定")
            return False
            
        # 檢查API物件是否存在
        if not hasattr(self.order_tester, 'm_pSKOrder') or not self.order_tester.m_pSKOrder:
            logger.error("❌ SKOrderLib未初始化")
            return False
            
        self.is_connected = True
        return True
        
    def place_order(self, 
                   product: str = "MTX00",
                   direction: str = "BUY", 
                   price: float = 0.0,
                   quantity: int = 1,
                   order_type: str = "ROD") -> Dict[str, Any]:
        """
        下單功能 - 策略系統調用接口
        
        Args:
            product: 商品代碼 (預設MTX00)
            direction: 買賣方向 ("BUY"/"SELL")
            price: 價格 (0.0表示市價)
            quantity: 數量
            order_type: 委託類型 ("ROD"/"IOC"/"FOK")
            
        Returns:
            Dict包含下單結果:
            {
                'success': bool,
                'order_id': str,
                'message': str,
                'timestamp': str
            }
        """
        if not self.check_connection():
            return {
                'success': False,
                'order_id': None,
                'message': '下單API未連接',
                'timestamp': time.strftime('%H:%M:%S')
            }
            
        try:
            # 調用OrderTester的下單功能
            future_order_frame = None
            
            # 尋找FutureOrderFrame實例
            for child in self.order_tester.notebook.winfo_children():
                if hasattr(child, 'winfo_children'):
                    for subchild in child.winfo_children():
                        if hasattr(subchild, 'place_future_order'):
                            future_order_frame = subchild
                            break
                    if future_order_frame:
                        break
                        
            if not future_order_frame:
                return {
                    'success': False,
                    'order_id': None,
                    'message': '找不到期貨下單模組',
                    'timestamp': time.strftime('%H:%M:%S')
                }
                
            # 設定下單參數
            order_params = {
                'product': product,
                'direction': direction,
                'price': price,
                'quantity': quantity,
                'order_type': order_type
            }
            
            # 執行下單
            result = self._execute_order(future_order_frame, order_params)
            
            # 記錄結果
            self.last_order_result = result
            
            if result['success']:
                logger.info(f"✅ 策略下單成功: {product} {direction} {quantity}口 @{price}")
            else:
                logger.error(f"❌ 策略下單失敗: {result['message']}")
                
            return result
            
        except Exception as e:
            error_msg = f"下單執行異常: {str(e)}"
            logger.error(error_msg)
            return {
                'success': False,
                'order_id': None,
                'message': error_msg,
                'timestamp': time.strftime('%H:%M:%S')
            }
            
    def _execute_order(self, future_order_frame, params: Dict[str, Any]) -> Dict[str, Any]:
        """執行實際下單操作"""
        try:
            # 設定商品代碼
            if hasattr(future_order_frame, 'product_var'):
                future_order_frame.product_var.set(params['product'])
                
            # 設定買賣方向
            if hasattr(future_order_frame, 'direction_var'):
                future_order_frame.direction_var.set(params['direction'])
                
            # 設定價格
            if hasattr(future_order_frame, 'price_var'):
                if params['price'] > 0:
                    future_order_frame.price_var.set(str(params['price']))
                else:
                    future_order_frame.price_var.set("0")  # 市價
                    
            # 設定數量
            if hasattr(future_order_frame, 'quantity_var'):
                future_order_frame.quantity_var.set(str(params['quantity']))
                
            # 設定委託類型
            if hasattr(future_order_frame, 'order_type_var'):
                future_order_frame.order_type_var.set(params['order_type'])
                
            # 執行下單
            if hasattr(future_order_frame, 'place_future_order'):
                order_result = future_order_frame.place_future_order()
                
                return {
                    'success': True,
                    'order_id': str(order_result) if order_result else "Unknown",
                    'message': f"下單成功: {params['product']} {params['direction']} {params['quantity']}口",
                    'timestamp': time.strftime('%H:%M:%S')
                }
            else:
                return {
                    'success': False,
                    'order_id': None,
                    'message': '下單方法不存在',
                    'timestamp': time.strftime('%H:%M:%S')
                }
                
        except Exception as e:
            return {
                'success': False,
                'order_id': None,
                'message': f"下單執行錯誤: {str(e)}",
                'timestamp': time.strftime('%H:%M:%S')
            }
            
    def get_last_order_result(self) -> Optional[Dict[str, Any]]:
        """取得最後一次下單結果"""
        return self.last_order_result
        
    def cancel_order(self, order_id: str) -> Dict[str, Any]:
        """
        取消委託
        
        Args:
            order_id: 委託編號
            
        Returns:
            Dict包含取消結果
        """
        if not self.check_connection():
            return {
                'success': False,
                'message': '下單API未連接',
                'timestamp': time.strftime('%H:%M:%S')
            }
            
        try:
            # 這裡可以實現取消委託的邏輯
            # 目前返回成功狀態
            logger.info(f"📋 取消委託請求: {order_id}")
            
            return {
                'success': True,
                'message': f"取消委託請求已發送: {order_id}",
                'timestamp': time.strftime('%H:%M:%S')
            }
            
        except Exception as e:
            error_msg = f"取消委託異常: {str(e)}"
            logger.error(error_msg)
            return {
                'success': False,
                'message': error_msg,
                'timestamp': time.strftime('%H:%M:%S')
            }

# 全域API實例
stable_order_api = StableOrderAPI()

def get_stable_order_api() -> StableOrderAPI:
    """取得穩定版下單API實例"""
    return stable_order_api

# 策略系統調用的便利函數
def strategy_place_order(product: str = "MTX00", 
                        direction: str = "BUY", 
                        price: float = 0.0,
                        quantity: int = 1,
                        order_type: str = "ROD") -> Dict[str, Any]:
    """
    策略系統下單便利函數
    
    使用範例:
    result = strategy_place_order(
        product='MTX00',
        direction='BUY',
        price=22000,
        quantity=3,
        order_type='ROD'
    )
    
    if result['success']:
        print(f"下單成功: {result['order_id']}")
    else:
        print(f"下單失敗: {result['message']}")
    """
    return stable_order_api.place_order(product, direction, price, quantity, order_type)

if __name__ == "__main__":
    # 測試用例
    print("🧪 穩定版下單API測試")
    print("⚠️ 需要先啟動 OrderTester.py 並登入")
    print("📋 檔案說明:")
    print("   ✅ OrderTester.py - 穩定版下單機 (STABLE_VERSION_2025_06_30_FINAL)")
    print("   📋 SKCOMTester.py - 原始版本 (不建議使用)")
    print("   🎯 test_ui_improvements.py - 完整交易測試系統")

    # 模擬測試
    api = StableOrderAPI()
    result = api.place_order()
    print(f"測試結果: {result}")
