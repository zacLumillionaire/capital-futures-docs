#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
追價機制修復驗證腳本
測試訂單ID映射和追價觸發是否正常
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
from unified_order_tracker import UnifiedOrderTracker

# 設置日誌
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def test_order_id_mapping():
    """測試訂單ID映射機制"""
    logger.info("🧪 測試訂單ID映射機制...")
    
    try:
        # 清理測試資料庫
        db_file = "test_retry_fix.db"
        if os.path.exists(db_file):
            os.remove(db_file)
        
        # 創建組件
        db_manager = MultiGroupDatabaseManager(db_file)
        order_tracker = UnifiedOrderTracker(console_enabled=True)
        
        # 創建測試配置
        presets = create_preset_configs()
        config = presets["測試配置 (1口×1組)"]
        
        # 創建部位管理器
        position_manager = MultiGroupPositionManager(
            db_manager=db_manager,
            strategy_config=config,
            order_manager=None,  # 測試模式
            order_tracker=order_tracker
        )
        
        # 模擬訂單註冊
        logger.info("📝 模擬訂單註冊...")
        
        # 測試API序號映射
        test_order_id = "test_order_123"
        test_api_seq = "2315544892824"
        
        success = order_tracker.register_order(
            order_id=test_order_id,
            product="TM0000",
            direction="SHORT",
            quantity=1,
            price=22354.0,
            api_seq_no=test_api_seq,
            signal_source="test_mapping",
            is_virtual=False
        )
        
        if success:
            logger.info(f"✅ 訂單註冊成功: {test_order_id} -> API序號: {test_api_seq}")
            
            # 檢查映射
            if test_api_seq in order_tracker.api_seq_mapping:
                mapped_order_id = order_tracker.api_seq_mapping[test_api_seq]
                if mapped_order_id == test_order_id:
                    logger.info("✅ API序號映射正確")
                    return True
                else:
                    logger.error(f"❌ API序號映射錯誤: 期望{test_order_id}, 實際{mapped_order_id}")
                    return False
            else:
                logger.error("❌ API序號映射不存在")
                return False
        else:
            logger.error("❌ 訂單註冊失敗")
            return False
            
    except Exception as e:
        logger.error(f"❌ 測試訂單ID映射失敗: {e}")
        return False

def test_cancel_callback_trigger():
    """測試取消回調觸發機制"""
    logger.info("🧪 測試取消回調觸發機制...")
    
    try:
        # 創建組件
        db_file = "test_retry_fix.db"
        db_manager = MultiGroupDatabaseManager(db_file)
        order_tracker = UnifiedOrderTracker(console_enabled=True)
        
        # 創建測試配置
        presets = create_preset_configs()
        config = presets["測試配置 (1口×1組)"]
        
        # 創建部位管理器
        position_manager = MultiGroupPositionManager(
            db_manager=db_manager,
            strategy_config=config,
            order_manager=None,
            order_tracker=order_tracker
        )
        
        # 創建測試策略組和部位
        test_group_id = db_manager.create_strategy_group(
            date="2025-07-05",
            group_id=1,
            direction="SHORT",
            signal_time="01:10:05",
            range_high=22362.0,
            range_low=22356.0,
            total_lots=1
        )
        
        position_id = db_manager.create_position_record(
            group_id=test_group_id,
            lot_id=1,
            direction="SHORT",
            entry_time="01:10:06",
            rule_config='{"lot_id": 1, "stop_loss_points": 20}',
            order_status='PENDING'
        )
        
        # 模擬訂單和映射
        test_order_id = "test_cancel_order"
        test_api_seq = "2315544892999"
        
        # 註冊訂單
        order_tracker.register_order(
            order_id=test_order_id,
            product="TM0000",
            direction="SHORT",
            quantity=1,
            price=22354.0,
            api_seq_no=test_api_seq,
            signal_source="test_cancel",
            is_virtual=False
        )
        
        # 設置部位訂單映射
        position_manager.position_order_mapping[position_id] = test_order_id
        
        # 設置原始價格
        db_manager.set_original_price(position_id, 22354.0)
        
        logger.info(f"📋 設置完成: 部位{position_id} -> 訂單{test_order_id} -> API序號{test_api_seq}")
        
        # 模擬取消回報
        logger.info("📞 模擬取消回報...")
        
        # 構造取消回報數據（模擬OnNewData格式）
        # 根據實際LOG格式：['', 'TF', 'C', 'N', 'F020000', '6363839', 'SNF20', 'TW', 'TM2507', '', 'v5444', '0.000000', '', '', '', '', '', '', '', '', '0', '', '', '20250705', '01:10:09', '', '0000000', '7174', 'y', '20250707', '2120000111233', 'A', 'FITM', '202507', '', '', '', '', '0000003795', '', 'B', '20250704', '', '', '', 'N', '', '2315544892824']
        cancel_reply = f",TF,C,N,F020000,6363839,SNF20,TW,TM2507,,test,0.000000,,,,,,,,,,0,,,20250705,01:10:09,,0000000,7174,y,20250707,2120000111999,A,FITM,202507,,,,,0000009999,,B,20250704,,,,,N,,{test_api_seq}"
        
        # 處理取消回報
        logger.info(f"📋 回報數據: {cancel_reply}")
        logger.info(f"📋 回報欄位數: {len(cancel_reply.split(','))}")

        success = order_tracker.process_real_order_reply(cancel_reply)
        
        if success:
            logger.info("✅ 取消回報處理成功")
            
            # 等待延遲追價執行
            logger.info("⏰ 等待延遲追價執行...")
            time.sleep(3)
            
            # 檢查部位狀態
            updated_position = db_manager.get_position_by_id(position_id)
            if updated_position:
                status = updated_position.get('status')
                original_price = updated_position.get('original_price')
                
                logger.info(f"📊 部位狀態: {status}")
                logger.info(f"💰 原始價格: {original_price}")
                
                if status == 'FAILED' and original_price:
                    logger.info("✅ 取消回調觸發機制測試通過")
                    return True
                else:
                    logger.error("❌ 部位狀態或原始價格設置失敗")
                    return False
            else:
                logger.error("❌ 找不到更新後的部位")
                return False
        else:
            logger.error("❌ 取消回報處理失敗")
            return False
            
    except Exception as e:
        logger.error(f"❌ 測試取消回調觸發失敗: {e}")
        return False

def main():
    """主測試函數"""
    logger.info("🚀 開始追價機制修復驗證測試")
    logger.info("=" * 60)
    
    # 測試計數
    total_tests = 0
    passed_tests = 0
    
    # 測試1: 訂單ID映射
    total_tests += 1
    if test_order_id_mapping():
        passed_tests += 1
    
    logger.info("-" * 60)
    
    # 測試2: 取消回調觸發
    total_tests += 1
    if test_cancel_callback_trigger():
        passed_tests += 1
    
    # 測試結果
    logger.info("=" * 60)
    logger.info(f"📊 測試結果: {passed_tests}/{total_tests} 通過")
    
    if passed_tests == total_tests:
        logger.info("🎉 所有測試通過！追價機制修復成功")
        return True
    else:
        logger.error(f"❌ {total_tests - passed_tests} 個測試失敗")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
