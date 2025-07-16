#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
測試 StopLossExecutor 到 VirtualRealOrderManager 的平倉呼叫鏈
專門驗證修復後的介面不匹配問題
"""

import sys
import os
import time
import sqlite3
from datetime import datetime
from typing import Dict, Optional

# 添加專案路徑
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

def create_test_database() -> str:
    """創建測試資料庫"""
    db_path = "test_stop_loss_flow.db"
    
    # 刪除舊的測試資料庫
    if os.path.exists(db_path):
        os.remove(db_path)
    
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # 創建部位記錄表
    cursor.execute('''
        CREATE TABLE position_records (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            group_id TEXT NOT NULL,
            position_pk TEXT UNIQUE NOT NULL,
            direction TEXT NOT NULL,
            entry_price REAL NOT NULL,
            quantity INTEGER NOT NULL,
            status TEXT DEFAULT 'ACTIVE',
            entry_time TEXT,
            exit_time TEXT,
            exit_price REAL,
            exit_reason TEXT,
            pnl REAL DEFAULT 0,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    # 創建策略組表
    cursor.execute('''
        CREATE TABLE strategy_groups (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            group_id TEXT UNIQUE NOT NULL,
            date TEXT NOT NULL,
            total_lots INTEGER NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    # 插入測試策略組
    cursor.execute('''
        INSERT INTO strategy_groups (group_id, date, total_lots)
        VALUES ('TEST_GROUP_001', '20250716', 1)
    ''')
    
    # 插入測試部位
    cursor.execute('''
        INSERT INTO position_records 
        (group_id, position_pk, direction, entry_price, quantity, status, entry_time)
        VALUES ('TEST_GROUP_001', 'TEST_POS_001', 'LONG', 22500.0, 1, 'ACTIVE', '10:30:00')
    ''')
    
    conn.commit()
    conn.close()
    
    print(f"✅ 測試資料庫已創建: {db_path}")
    return db_path

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

def test_stop_loss_execution_flow():
    """測試停損執行流程"""
    print("🧪 測試 StopLossExecutor 到 VirtualRealOrderManager 平倉呼叫鏈")
    print("=" * 60)
    
    try:
        # 1. 創建測試資料庫
        db_path = create_test_database()
        
        # 2. 導入必要模組
        from multi_group_database import MultiGroupDatabaseManager
        from virtual_real_order_manager import VirtualRealOrderManager
        from stop_loss_executor import StopLossExecutor
        from unified_exit_manager import GlobalExitManager

        print("✅ 模組導入成功")

        # 3. 創建測試組件
        db_manager = MultiGroupDatabaseManager(db_path)
        quote_manager = MockQuoteManager()
        strategy_config = MockStrategyConfig()
        
        # 創建虛實單管理器（虛擬模式）
        order_manager = VirtualRealOrderManager(
            quote_manager=quote_manager,
            strategy_config=strategy_config,
            console_enabled=True
        )
        order_manager.set_order_mode(False)  # 設為虛擬模式
        
        # 創建全局出場管理器
        global_exit_manager = GlobalExitManager(console_enabled=True)
        
        # 創建停損執行器
        stop_executor = StopLossExecutor(
            db_manager=db_manager,
            virtual_real_order_manager=order_manager,
            global_exit_manager=global_exit_manager,
            console_enabled=True
        )
        
        print("✅ 測試組件創建成功")
        
        # 4. 創建停損觸發信息
        class MockStopLossTrigger:
            def __init__(self):
                self.position_id = 1
                self.direction = "LONG"
                self.current_price = 22470.0  # 觸發停損的價格
                self.trigger_reason = "stop_loss"
                self.group_id = "TEST_GROUP_001"
        
        trigger_info = MockStopLossTrigger()
        
        print("✅ 停損觸發信息創建成功")
        print(f"   部位ID: {trigger_info.position_id}")
        print(f"   方向: {trigger_info.direction}")
        print(f"   觸發價格: {trigger_info.current_price}")
        
        # 5. 執行停損測試
        print("\n🚀 開始執行停損測試...")
        
        execution_result = stop_executor.execute_stop_loss(trigger_info)
        
        # 6. 驗證結果
        print("\n📊 測試結果驗證:")
        print(f"   執行成功: {execution_result.success}")
        print(f"   部位ID: {execution_result.position_id}")
        
        if execution_result.success:
            print(f"   訂單ID: {execution_result.order_id}")
            print(f"   執行價格: {execution_result.execution_price}")
            print(f"   執行時間: {execution_result.execution_time}")
            print("✅ 停損執行測試成功！")
            
            # 驗證沒有介面錯誤
            if execution_result.error_message is None:
                print("✅ 沒有發現 'unexpected keyword argument' 錯誤")
            else:
                print(f"❌ 發現錯誤: {execution_result.error_message}")
                return False
                
        else:
            print(f"❌ 停損執行失敗: {execution_result.error_message}")
            return False
        
        # 7. 清理測試資料庫
        if os.path.exists(db_path):
            os.remove(db_path)
            print("✅ 測試資料庫已清理")
        
        return True
        
    except Exception as e:
        print(f"❌ 測試執行失敗: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_interface_compatibility():
    """測試介面兼容性"""
    print("\n🔧 測試介面兼容性...")
    
    try:
        from virtual_real_order_manager import VirtualRealOrderManager
        
        # 創建模擬組件
        quote_manager = MockQuoteManager()
        strategy_config = MockStrategyConfig()
        
        order_manager = VirtualRealOrderManager(
            quote_manager=quote_manager,
            strategy_config=strategy_config,
            console_enabled=True
        )
        
        # 測試新的 **kwargs 參數
        print("📋 測試 **kwargs 參數處理...")
        
        result = order_manager.execute_strategy_order(
            direction="BUY",
            signal_source="test_interface",
            price=22500.0,
            quantity=1,
            new_close=1,
            order_type="FOK",  # 這個參數應該被忽略而不報錯
            extra_param="test"  # 額外參數也應該被忽略
        )
        
        if result.success:
            print("✅ 介面兼容性測試成功 - **kwargs 參數正常處理")
            return True
        else:
            print(f"❌ 介面兼容性測試失敗: {result.error}")
            return False
            
    except Exception as e:
        print(f"❌ 介面兼容性測試失敗: {e}")
        return False

def main():
    """主測試函數"""
    print("🚀 開始平倉呼叫鏈測試...")
    print("=" * 60)
    
    # 測試1: 停損執行流程
    test1_result = test_stop_loss_execution_flow()
    
    # 測試2: 介面兼容性
    test2_result = test_interface_compatibility()
    
    print("\n" + "=" * 60)
    print("📋 測試總結:")
    print(f"   停損執行流程: {'✅ 通過' if test1_result else '❌ 失敗'}")
    print(f"   介面兼容性: {'✅ 通過' if test2_result else '❌ 失敗'}")
    
    if test1_result and test2_result:
        print("\n🎉 所有測試通過！平倉呼叫鏈修復成功！")
        return True
    else:
        print("\n❌ 部分測試失敗，需要進一步檢查")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
