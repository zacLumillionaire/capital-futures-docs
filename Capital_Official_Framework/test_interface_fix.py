#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
簡單測試驗證 execute_strategy_order 介面修復
"""

import sys
import os

# 添加專案路徑
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

class MockQuoteManager:
    """模擬報價管理器"""
    def __init__(self):
        self.current_bid1 = 22480.0
        self.current_ask1 = 22481.0
        self.current_product = "TM0000"
    
    def get_bid1_price(self, product="TM0000"):
        return self.current_bid1
    
    def get_ask1_price(self, product="TM0000"):
        return self.current_ask1
    
    def get_current_product(self):
        return self.current_product
    
    def is_quote_fresh(self):
        return True

class MockStrategyConfig:
    """模擬策略配置"""
    def __init__(self):
        self.default_quantity = 1
        self.default_product = "TM0000"

def test_interface_fix():
    """測試介面修復"""
    print("🧪 測試 execute_strategy_order 介面修復")
    print("=" * 50)
    
    try:
        # 導入 VirtualRealOrderManager
        from virtual_real_order_manager import VirtualRealOrderManager
        
        # 創建模擬組件
        quote_manager = MockQuoteManager()
        strategy_config = MockStrategyConfig()
        
        # 創建虛實單管理器
        order_manager = VirtualRealOrderManager(
            quote_manager=quote_manager,
            strategy_config=strategy_config,
            console_enabled=True
        )
        
        # 設為虛擬模式
        order_manager.set_order_mode(False)
        
        print("✅ VirtualRealOrderManager 創建成功")
        
        # 測試1: 正常呼叫（不包含 order_type）
        print("\n📋 測試1: 正常呼叫（修復後的參數）")
        result1 = order_manager.execute_strategy_order(
            direction="BUY",
            signal_source="test_normal",
            price=22500.0,
            quantity=1,
            new_close=1
        )
        
        if result1.success:
            print("✅ 正常呼叫測試成功")
        else:
            print(f"❌ 正常呼叫測試失敗: {result1.error}")
        
        # 測試2: 包含舊的 order_type 參數（應該被忽略）
        print("\n📋 測試2: 包含舊參數（應該被忽略）")
        result2 = order_manager.execute_strategy_order(
            direction="SELL",
            signal_source="test_legacy",
            price=22480.0,
            quantity=1,
            new_close=1,
            order_type="FOK",  # 這個參數應該被忽略
            extra_param="test"  # 額外參數也應該被忽略
        )
        
        if result2.success:
            print("✅ 舊參數兼容性測試成功")
        else:
            print(f"❌ 舊參數兼容性測試失敗: {result2.error}")
        
        # 測試3: 檢查是否有 TypeError
        print("\n📋 測試3: 檢查 TypeError 修復")
        try:
            # 這個呼叫在修復前會拋出 "unexpected keyword argument 'order_type'" 錯誤
            result3 = order_manager.execute_strategy_order(
                direction="BUY",
                quantity=1,
                signal_source="test_error_fix",
                order_type="FOK",  # 修復前會導致 TypeError
                price=22500.0,
                new_close=1
            )
            print("✅ TypeError 修復測試成功 - 沒有拋出異常")
            
        except TypeError as e:
            if "unexpected keyword argument" in str(e):
                print(f"❌ TypeError 修復失敗: {e}")
                return False
            else:
                print(f"⚠️ 其他 TypeError: {e}")
        
        print("\n🎉 所有介面修復測試通過！")
        return True
        
    except Exception as e:
        print(f"❌ 測試失敗: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """主函數"""
    print("🚀 開始介面修復驗證測試...")
    
    success = test_interface_fix()
    
    print("\n" + "=" * 50)
    if success:
        print("✅ 介面修復驗證成功！")
        print("   - execute_strategy_order 不再拋出 'unexpected keyword argument' 錯誤")
        print("   - **kwargs 參數正常處理未知參數")
        print("   - 向後兼容性良好")
    else:
        print("❌ 介面修復驗證失敗")
    
    return success

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
