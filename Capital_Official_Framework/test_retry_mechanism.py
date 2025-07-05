#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
追價機制測試腳本
測試FOK失敗後的自動追價補單功能
"""

import os
import sys
import time
import logging
from datetime import datetime

# 添加項目路徑
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from multi_group_database import MultiGroupDatabaseManager
from multi_group_position_manager import MultiGroupPositionManager
from multi_group_config import create_preset_configs

# 設置日誌
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def cleanup_test_database():
    """清理測試資料庫"""
    try:
        db_file = "test_retry_mechanism.db"
        if os.path.exists(db_file):
            os.remove(db_file)
            logger.info(f"✅ 已清理測試資料庫: {db_file}")
        return db_file
    except Exception as e:
        logger.error(f"❌ 清理測試資料庫失敗: {e}")
        return None

def test_database_structure():
    """測試資料庫結構是否正確"""
    logger.info("🧪 測試資料庫結構...")
    
    db_file = cleanup_test_database()
    if not db_file:
        return False
    
    try:
        # 創建資料庫管理器
        db_manager = MultiGroupDatabaseManager(db_file)
        
        # 測試創建部位記錄（包含新欄位）
        test_group_id = db_manager.create_strategy_group(
            date="2025-07-05",
            group_id=1,
            direction="SHORT",
            signal_time="08:48:15",
            range_high=22384.0,
            range_low=22379.0,
            total_lots=1
        )
        
        if test_group_id:
            # 創建部位記錄
            position_id = db_manager.create_position_record(
                group_id=test_group_id,
                lot_id=1,
                direction="SHORT",
                entry_time="08:48:20",
                rule_config='{"lot_id": 1, "stop_loss_points": 20}',
                order_status='PENDING'
            )
            
            if position_id:
                # 測試新欄位操作
                success1 = db_manager.set_original_price(position_id, 22377.0)
                success2 = db_manager.update_retry_info(position_id, 1, 22378.0, "ASK1+1點追價")
                success3 = db_manager.increment_retry_count(position_id)
                
                if success1 and success2 and success3:
                    logger.info("✅ 資料庫結構測試通過")
                    return True
                else:
                    logger.error("❌ 新欄位操作失敗")
                    return False
            else:
                logger.error("❌ 創建部位記錄失敗")
                return False
        else:
            logger.error("❌ 創建策略組失敗")
            return False
            
    except Exception as e:
        logger.error(f"❌ 資料庫結構測試失敗: {e}")
        return False

def test_retry_logic():
    """測試追價邏輯"""
    logger.info("🧪 測試追價邏輯...")
    
    try:
        # 創建測試配置
        presets = create_preset_configs()
        config = presets["測試配置 (1口×1組)"]
        
        # 創建資料庫管理器
        db_manager = MultiGroupDatabaseManager("test_retry_mechanism.db")
        
        # 創建部位管理器（無下單組件的測試）
        position_manager = MultiGroupPositionManager(
            db_manager=db_manager,
            strategy_config=config,
            order_manager=None,  # 測試模式
            order_tracker=None   # 測試模式
        )
        
        # 測試追價相關方法
        logger.info("📋 測試追價條件檢查...")
        
        # 創建測試部位
        test_position = {
            'id': 1,
            'status': 'FAILED',
            'order_status': 'CANCELLED',
            'retry_count': 0,
            'original_price': 22377.0,
            'direction': 'SHORT'
        }
        
        # 測試重試條件檢查
        is_allowed = position_manager.is_retry_allowed(test_position)
        logger.info(f"重試條件檢查: {'✅ 通過' if is_allowed else '❌ 失敗'}")
        
        # 測試滑價驗證
        valid_slippage = position_manager.validate_slippage(22377.0, 22380.0, 5)
        invalid_slippage = position_manager.validate_slippage(22377.0, 22385.0, 5)
        
        logger.info(f"滑價驗證(3點): {'✅ 通過' if valid_slippage else '❌ 失敗'}")
        logger.info(f"滑價驗證(8點): {'❌ 正確拒絕' if not invalid_slippage else '✅ 錯誤通過'}")
        
        # 測試查詢失敗部位
        failed_positions = db_manager.get_failed_positions_for_retry()
        logger.info(f"查詢失敗部位: 找到 {len(failed_positions)} 個")
        
        logger.info("✅ 追價邏輯測試完成")
        return True
        
    except Exception as e:
        logger.error(f"❌ 追價邏輯測試失敗: {e}")
        return False

def test_event_driven_trigger():
    """測試事件驅動觸發機制"""
    logger.info("🧪 測試事件驅動觸發機制...")
    
    try:
        # 模擬訂單資訊
        class MockOrderInfo:
            def __init__(self):
                self.order_id = "test_order_123"
                self.price = 22377.0
        
        # 創建測試配置
        presets = create_preset_configs()
        config = presets["測試配置 (1口×1組)"]
        
        # 創建資料庫管理器
        db_manager = MultiGroupDatabaseManager("test_retry_mechanism.db")
        
        # 創建部位管理器
        position_manager = MultiGroupPositionManager(
            db_manager=db_manager,
            strategy_config=config,
            order_manager=None,
            order_tracker=None
        )
        
        # 創建測試部位和訂單映射
        test_group_id = db_manager.create_strategy_group(
            date="2025-07-05",
            group_id=2,
            direction="SHORT",
            signal_time="08:48:15",
            range_high=22384.0,
            range_low=22379.0,
            total_lots=1
        )
        
        position_id = db_manager.create_position_record(
            group_id=test_group_id,
            lot_id=1,
            direction="SHORT",
            entry_time="08:48:20",
            rule_config='{"lot_id": 1, "stop_loss_points": 20}',
            order_status='PENDING'
        )
        
        # 設置訂單映射
        position_manager.position_order_mapping[position_id] = "test_order_123"
        
        # 模擬取消回調
        mock_order = MockOrderInfo()
        logger.info("📞 模擬取消回調觸發...")
        position_manager._on_order_cancelled(mock_order)
        
        # 等待延遲執行
        logger.info("⏰ 等待延遲追價執行...")
        time.sleep(3)
        
        # 檢查結果
        updated_position = db_manager.get_position_by_id(position_id)
        if updated_position:
            status = updated_position.get('status')
            original_price = updated_position.get('original_price')
            logger.info(f"部位狀態: {status}")
            logger.info(f"原始價格: {original_price}")
            
            if status == 'FAILED' and original_price:
                logger.info("✅ 事件驅動觸發機制測試通過")
                return True
            else:
                logger.error("❌ 事件驅動觸發機制測試失敗")
                return False
        else:
            logger.error("❌ 找不到更新後的部位")
            return False
            
    except Exception as e:
        logger.error(f"❌ 事件驅動觸發測試失敗: {e}")
        return False

def main():
    """主測試函數"""
    logger.info("🚀 開始追價機制完整測試")
    logger.info("=" * 60)
    
    # 測試計數
    total_tests = 0
    passed_tests = 0
    
    # 測試1: 資料庫結構
    total_tests += 1
    if test_database_structure():
        passed_tests += 1
    
    logger.info("-" * 60)
    
    # 測試2: 追價邏輯
    total_tests += 1
    if test_retry_logic():
        passed_tests += 1
    
    logger.info("-" * 60)
    
    # 測試3: 事件驅動觸發
    total_tests += 1
    if test_event_driven_trigger():
        passed_tests += 1
    
    # 測試結果
    logger.info("=" * 60)
    logger.info(f"📊 測試結果: {passed_tests}/{total_tests} 通過")
    
    if passed_tests == total_tests:
        logger.info("🎉 所有測試通過！追價機制已準備就緒")
        return True
    else:
        logger.error(f"❌ {total_tests - passed_tests} 個測試失敗")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
