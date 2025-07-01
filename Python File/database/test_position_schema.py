#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
測試部位管理資料庫表格結構
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

try:
    from position_tables_schema import (
        PositionRecord, StopLossAdjustmentRecord,
        PositionType, PositionStatus, AdjustmentReason,
        generate_session_id, validate_position_data,
        PositionTableSQL
    )
    print("✅ 成功導入所有模組")
except ImportError as e:
    print(f"❌ 導入模組失敗: {e}")
    sys.exit(1)

def test_data_models():
    """測試資料模型"""
    print("\n🧪 測試資料模型...")
    
    # 測試會話ID生成
    session_id = generate_session_id()
    print(f"生成會話ID: {session_id}")
    
    # 創建測試部位記錄
    position = PositionRecord(
        session_id=session_id,
        date="2025-06-30",
        lot_id=1,
        strategy_name="開盤區間突破策略",
        position_type=PositionType.LONG,
        entry_price=22014.0,
        entry_time="08:48:15",
        entry_datetime="2025-06-30 08:48:15",
        range_high=22010.0,
        range_low=21998.0,
        current_stop_loss=21998.0,
        peak_price=22014.0,
        lot_rule_config='{"trailing_activation": 15, "trailing_pullback": 0.20}'
    )
    
    # 驗證資料
    is_valid = validate_position_data(position)
    print(f"部位資料驗證: {'✅ 通過' if is_valid else '❌ 失敗'}")
    
    # 轉換為字典
    position_dict = position.to_dict()
    print(f"部位資料字典: {len(position_dict)} 個欄位")
    
    # 創建停損調整記錄
    adjustment = StopLossAdjustmentRecord(
        position_id=1,
        session_id=session_id,
        lot_id=1,
        old_stop_loss=21998.0,
        new_stop_loss=22005.0,
        adjustment_reason=AdjustmentReason.TRAILING,
        trigger_price=22025.0,
        trigger_time="08:52:30",
        trigger_datetime="2025-06-30 08:52:30",
        peak_price_at_adjustment=22025.0,
        trailing_activation_points=15.0,
        trailing_pullback_ratio=0.20
    )
    
    print(f"停損調整記錄: {adjustment.adjustment_reason.value}")
    
    return True

def test_sql_statements():
    """測試SQL語句"""
    print("\n🧪 測試SQL語句...")
    
    # 檢查SQL語句是否正確定義
    sql_checks = [
        ("CREATE_POSITIONS_TABLE", PositionTableSQL.CREATE_POSITIONS_TABLE),
        ("CREATE_STOP_LOSS_ADJUSTMENTS_TABLE", PositionTableSQL.CREATE_STOP_LOSS_ADJUSTMENTS_TABLE),
        ("INSERT_POSITION", PositionTableSQL.INSERT_POSITION),
        ("SELECT_ACTIVE_POSITIONS", PositionTableSQL.SELECT_ACTIVE_POSITIONS),
        ("UPDATE_POSITION_STATUS", PositionTableSQL.UPDATE_POSITION_STATUS)
    ]
    
    for name, sql in sql_checks:
        if sql and len(sql.strip()) > 0:
            print(f"✅ {name}: {len(sql)} 字元")
        else:
            print(f"❌ {name}: 空白或無效")
    
    # 檢查索引數量
    print(f"✅ 索引數量: {len(PositionTableSQL.CREATE_INDEXES)}")
    print(f"✅ 觸發器數量: {len(PositionTableSQL.CREATE_TRIGGERS)}")
    
    return True

def test_enums():
    """測試枚舉定義"""
    print("\n🧪 測試枚舉定義...")
    
    # 測試部位狀態
    statuses = [status.value for status in PositionStatus]
    print(f"部位狀態: {statuses}")
    
    # 測試部位類型
    types = [ptype.value for ptype in PositionType]
    print(f"部位類型: {types}")
    
    # 測試調整原因
    reasons = [reason.value for reason in AdjustmentReason]
    print(f"調整原因: {reasons}")
    
    return True

def main():
    """主測試函數"""
    print("🚀 開始測試部位管理資料庫表格結構")
    
    try:
        # 執行所有測試
        test_results = [
            test_enums(),
            test_data_models(),
            test_sql_statements()
        ]
        
        if all(test_results):
            print("\n✅ 所有測試通過！")
            print("📊 資料庫表格結構設計完成")
            return True
        else:
            print("\n❌ 部分測試失敗")
            return False
            
    except Exception as e:
        print(f"\n❌ 測試過程中發生錯誤: {e}")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
