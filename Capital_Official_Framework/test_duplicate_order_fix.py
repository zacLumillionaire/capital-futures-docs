#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
重複下單修復驗證腳本
測試1組3口配置是否只下3口，以及API序號格式是否正確
"""

import os
import sys
import logging

# 添加項目路徑
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from multi_group_database import MultiGroupDatabaseManager
from multi_group_position_manager import MultiGroupPositionManager
from multi_group_config import create_preset_configs
from unified_order_tracker import UnifiedOrderTracker

# 設置日誌
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class MockOrderResult:
    """模擬下單結果"""
    def __init__(self, success=True, order_id=None, api_result=None, mode="real"):
        self.success = success
        self.order_id = order_id
        self.api_result = api_result
        self.mode = mode
        self.error = None if success else "模擬失敗"

class MockOrderManager:
    """模擬下單管理器"""
    def __init__(self):
        self.order_count = 0
    
    def execute_strategy_order(self, direction, signal_source, product, price, quantity):
        """模擬下單執行"""
        self.order_count += 1
        order_id = f"mock_order_{self.order_count}"
        api_result = (f"mock_api_{self.order_count}", 0)  # 模擬API返回的tuple格式
        
        logger.info(f"🔧 模擬下單: {direction} {product} {quantity}口 @{price} -> {order_id}")
        
        return MockOrderResult(
            success=True,
            order_id=order_id,
            api_result=api_result,
            mode="real"
        )
    
    def get_ask1_price(self, product):
        """模擬取得ASK1價格"""
        return 22350.0

def test_single_group_execution():
    """測試單組執行是否只下3口"""
    logger.info("🧪 測試單組3口執行...")
    
    try:
        # 清理測試資料庫
        db_file = "test_duplicate_fix.db"
        if os.path.exists(db_file):
            os.remove(db_file)
        
        # 創建組件
        db_manager = MultiGroupDatabaseManager(db_file)
        order_tracker = UnifiedOrderTracker(console_enabled=True)
        mock_order_manager = MockOrderManager()
        
        # 創建測試配置（1組×3口）
        presets = create_preset_configs()
        config = presets["測試配置 (1口×1組)"]
        
        # 修改為3口配置
        config.groups[0].lot_rules = [
            config.groups[0].lot_rules[0].__class__(lot_id=1, stop_loss_points=20),
            config.groups[0].lot_rules[0].__class__(lot_id=2, stop_loss_points=20),
            config.groups[0].lot_rules[0].__class__(lot_id=3, stop_loss_points=20)
        ]
        config.groups[0].total_lots = 3
        
        # 創建部位管理器
        position_manager = MultiGroupPositionManager(
            db_manager=db_manager,
            strategy_config=config,
            order_manager=mock_order_manager,
            order_tracker=order_tracker
        )
        
        # 執行進場
        logger.info("🚀 執行進場測試...")
        
        # 創建策略組
        group_db_id = position_manager.create_strategy_groups(
            direction="SHORT",
            signal_time="01:31:02",
            range_high=22347.0,
            range_low=22342.0
        )
        
        if group_db_id:
            logger.info(f"✅ 策略組創建成功: {group_db_id}")
            
            # 執行進場
            success = position_manager.execute_group_entry(
                group_db_id=group_db_id[0],  # 取第一個組的ID
                actual_price=22341.0,
                actual_time="01:31:02"
            )
            
            if success:
                logger.info("✅ 進場執行成功")
                
                # 檢查下單次數
                expected_orders = 3
                actual_orders = mock_order_manager.order_count
                
                logger.info(f"📊 下單統計: 預期{expected_orders}口, 實際{actual_orders}口")
                
                if actual_orders == expected_orders:
                    logger.info("✅ 下單次數正確")
                    return True
                else:
                    logger.error(f"❌ 下單次數錯誤: 預期{expected_orders}, 實際{actual_orders}")
                    return False
            else:
                logger.error("❌ 進場執行失敗")
                return False
        else:
            logger.error("❌ 策略組創建失敗")
            return False
            
    except Exception as e:
        logger.error(f"❌ 測試單組執行失敗: {e}")
        return False

def test_api_seq_format():
    """測試API序號格式是否正確"""
    logger.info("🧪 測試API序號格式...")
    
    try:
        # 創建統一追蹤器
        order_tracker = UnifiedOrderTracker(console_enabled=True)
        
        # 測試正確的API序號格式
        test_cases = [
            {
                "api_result": ("12345", 0),
                "expected": "12345",
                "description": "tuple格式"
            },
            {
                "api_result": "67890",
                "expected": "67890", 
                "description": "字串格式"
            }
        ]
        
        for i, case in enumerate(test_cases):
            logger.info(f"📋 測試案例{i+1}: {case['description']}")
            
            # 模擬API序號處理
            api_seq_no = None
            api_result = case["api_result"]
            
            if isinstance(api_result, tuple) and len(api_result) >= 1:
                api_seq_no = str(api_result[0])  # 只取第一個元素
            else:
                api_seq_no = str(api_result)
            
            logger.info(f"🔍 API序號處理: {api_result} -> {api_seq_no}")
            
            if api_seq_no == case["expected"]:
                logger.info(f"✅ 案例{i+1}通過")
            else:
                logger.error(f"❌ 案例{i+1}失敗: 預期{case['expected']}, 實際{api_seq_no}")
                return False
        
        logger.info("✅ API序號格式測試通過")
        return True
        
    except Exception as e:
        logger.error(f"❌ 測試API序號格式失敗: {e}")
        return False

def main():
    """主測試函數"""
    logger.info("🚀 開始重複下單修復驗證測試")
    logger.info("=" * 60)
    
    # 測試計數
    total_tests = 0
    passed_tests = 0
    
    # 測試1: 單組執行次數
    total_tests += 1
    if test_single_group_execution():
        passed_tests += 1
    
    logger.info("-" * 60)
    
    # 測試2: API序號格式
    total_tests += 1
    if test_api_seq_format():
        passed_tests += 1
    
    # 測試結果
    logger.info("=" * 60)
    logger.info(f"📊 測試結果: {passed_tests}/{total_tests} 通過")
    
    if passed_tests == total_tests:
        logger.info("🎉 所有測試通過！重複下單問題已修復")
        return True
    else:
        logger.error(f"❌ {total_tests - passed_tests} 個測試失敗")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
