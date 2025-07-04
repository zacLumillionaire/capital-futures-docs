# -*- coding: utf-8 -*-
"""
Stage2 虛實單整合系統測試
Test Virtual/Real Order System

功能：
1. 虛擬模式完整測試
2. 系統整合測試
3. 回報追蹤測試
4. UI控制器測試

作者: Stage2 虛實單整合系統
日期: 2025-07-04
"""

import time
import threading
from datetime import datetime

# 導入測試模組
try:
    from virtual_real_order_manager import VirtualRealOrderManager
    from unified_order_tracker import UnifiedOrderTracker
    from real_time_quote_manager import RealTimeQuoteManager
    print("✅ 所有Stage2模組載入成功")
except ImportError as e:
    print(f"❌ 模組載入失敗: {e}")
    exit(1)


class MockStrategyManager:
    """模擬策略管理器"""
    
    def __init__(self):
        self.positions = []
        
    def update_position_from_fill(self, direction, quantity, price, order_id):
        """模擬策略部位更新"""
        position = {
            'direction': direction,
            'quantity': quantity,
            'price': price,
            'order_id': order_id,
            'timestamp': datetime.now()
        }
        self.positions.append(position)
        print(f"[MOCK_STRATEGY] 📊 部位更新: {direction} {quantity}口 @{price:.0f}")


class VirtualRealSystemTester:
    """虛實單系統測試器"""
    
    def __init__(self):
        self.quote_manager = None
        self.order_manager = None
        self.order_tracker = None
        self.strategy_manager = None
        
    def setup_system(self):
        """設置測試系統"""
        print("🔧 設置虛實單測試系統...")
        
        # 1. 創建報價管理器
        self.quote_manager = RealTimeQuoteManager(console_enabled=True)
        
        # 2. 創建模擬策略管理器
        self.strategy_manager = MockStrategyManager()
        
        # 3. 創建虛實單管理器
        self.order_manager = VirtualRealOrderManager(
            quote_manager=self.quote_manager,
            strategy_config=None,
            console_enabled=True,
            default_account="F0200006363839"
        )
        
        # 4. 創建統一回報追蹤器
        self.order_tracker = UnifiedOrderTracker(
            strategy_manager=self.strategy_manager,
            console_enabled=True
        )
        
        print("✅ 測試系統設置完成")
        
    def test_quote_manager(self):
        """測試報價管理器"""
        print("\n📊 測試報價管理器...")
        
        # 模擬五檔數據更新
        success = self.quote_manager.update_best5_data(
            market_no="TF", stock_idx=1,
            ask1=22515, ask1_qty=10, ask2=22516, ask2_qty=8, ask3=22517, ask3_qty=5,
            ask4=22518, ask4_qty=3, ask5=22519, ask5_qty=2,
            bid1=22514, bid1_qty=12, bid2=22513, bid2_qty=9, bid3=22512, bid3_qty=6,
            bid4=22511, bid4_qty=4, bid5=22510, bid5_qty=1,
            product_code="MTX00"
        )
        
        if success:
            print("✅ 五檔數據更新成功")
            
            # 測試ASK1價格取得
            ask1_price = self.quote_manager.get_best_ask_price("MTX00")
            print(f"📈 ASK1價格: {ask1_price}")
            
            # 測試報價摘要
            summary = self.quote_manager.get_quote_summary("MTX00")
            if summary:
                print(f"📋 報價摘要: ASK1={summary['ask1']} BID1={summary['bid1']}")
        else:
            print("❌ 五檔數據更新失敗")
            
    def test_virtual_order_flow(self):
        """測試虛擬下單流程"""
        print("\n🔄 測試虛擬下單流程...")
        
        # 確保是虛擬模式
        self.order_manager.set_order_mode(False)
        
        # 執行策略下單
        result = self.order_manager.execute_strategy_order(
            direction="LONG",
            signal_source="test_breakout"
        )
        
        if result.success:
            print(f"✅ 虛擬下單成功: {result.order_id}")
            
            # 註冊到追蹤器
            success = self.order_tracker.register_order(
                order_id=result.order_id,
                product="MTX00",
                direction="BUY",
                quantity=1,
                price=22515.0,
                is_virtual=True,
                signal_source="test_breakout"
            )
            
            if success:
                print("✅ 訂單追蹤註冊成功")
                
                # 等待虛擬成交
                time.sleep(0.5)
                
                # 檢查訂單狀態
                order_info = self.order_tracker.get_order_status(result.order_id)
                if order_info:
                    print(f"📊 訂單狀態: {order_info.status.value}")
                    print(f"📊 成交價格: {order_info.fill_price}")
                    print(f"📊 成交數量: {order_info.fill_quantity}")
            else:
                print("❌ 訂單追蹤註冊失敗")
        else:
            print(f"❌ 虛擬下單失敗: {result.error}")
            
    def test_mode_switching(self):
        """測試模式切換"""
        print("\n🔄 測試模式切換...")
        
        # 測試切換到實單模式 (應該失敗，因為沒有API)
        print("嘗試切換到實單模式...")
        success = self.order_manager.set_order_mode(True)
        if not success:
            print("✅ 正確阻止切換到實單模式 (API不可用)")
        else:
            print("⚠️ 意外成功切換到實單模式")
            
        # 確保回到虛擬模式
        self.order_manager.set_order_mode(False)
        current_mode = self.order_manager.get_current_mode()
        print(f"📊 當前模式: {current_mode}")
        
    def test_multiple_orders(self):
        """測試多筆訂單處理"""
        print("\n📦 測試多筆訂單處理...")
        
        orders = []
        for i in range(3):
            direction = "LONG" if i % 2 == 0 else "SHORT"
            result = self.order_manager.execute_strategy_order(
                direction=direction,
                signal_source=f"test_multi_{i}"
            )
            
            if result.success:
                orders.append(result.order_id)
                print(f"✅ 訂單{i+1} {direction} 下單成功: {result.order_id}")
                
                # 註冊追蹤
                self.order_tracker.register_order(
                    order_id=result.order_id,
                    product="MTX00",
                    direction=direction,
                    quantity=1,
                    price=22515.0 + i,
                    is_virtual=True,
                    signal_source=f"test_multi_{i}"
                )
            else:
                print(f"❌ 訂單{i+1} 下單失敗: {result.error}")
                
        # 等待所有虛擬成交
        time.sleep(1.0)
        
        # 檢查所有訂單狀態
        print("\n📊 檢查所有訂單狀態:")
        for order_id in orders:
            order_info = self.order_tracker.get_order_status(order_id)
            if order_info:
                print(f"   {order_id}: {order_info.status.value} - {order_info.direction}")
                
    def test_statistics(self):
        """測試統計功能"""
        print("\n📊 測試統計功能...")
        
        # 下單管理器統計
        order_stats = self.order_manager.get_statistics()
        print("下單管理器統計:")
        for key, value in order_stats.items():
            print(f"   {key}: {value}")
            
        # 回報追蹤器統計
        tracker_stats = self.order_tracker.get_statistics()
        print("\n回報追蹤器統計:")
        for key, value in tracker_stats.items():
            print(f"   {key}: {value}")
            
        # 策略管理器統計
        print(f"\n策略部位數量: {len(self.strategy_manager.positions)}")
        
    def run_all_tests(self):
        """執行所有測試"""
        print("🚀 開始Stage2虛實單整合系統測試")
        print("="*60)
        
        try:
            self.setup_system()
            self.test_quote_manager()
            self.test_virtual_order_flow()
            self.test_mode_switching()
            self.test_multiple_orders()
            self.test_statistics()
            
            print("\n" + "="*60)
            print("✅ 所有測試完成")
            
            # 顯示最終狀態
            print("\n📊 最終系統狀態:")
            self.order_manager.print_status()
            self.order_tracker.print_status()
            
        except Exception as e:
            print(f"\n❌ 測試過程中發生錯誤: {e}")
            import traceback
            traceback.print_exc()


def main():
    """主測試函數"""
    tester = VirtualRealSystemTester()
    tester.run_all_tests()


if __name__ == "__main__":
    main()
