#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Simple Test Position Manager (簡化版部位管理器測試)
"""

import os
import sys
import tempfile
import shutil

# 添加當前目錄到路徑
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

def test_imports():
    """測試模組導入"""
    print("🧪 測試模組導入...")
    
    try:
        from multi_group_database import MultiGroupDatabaseManager
        print("✅ MultiGroupDatabaseManager 導入成功")
    except Exception as e:
        print(f"❌ MultiGroupDatabaseManager 導入失敗: {e}")
        return False
    
    try:
        from multi_group_position_manager import MultiGroupPositionManager
        print("✅ MultiGroupPositionManager 導入成功")
    except Exception as e:
        print(f"❌ MultiGroupPositionManager 導入失敗: {e}")
        return False
    
    try:
        from multi_group_config import MultiGroupStrategyConfig, StrategyGroupConfig, LotRule, GroupStatus
        print("✅ 配置類導入成功")
    except Exception as e:
        print(f"❌ 配置類導入失敗: {e}")
        return False
    
    return True

def test_database_creation():
    """測試資料庫創建"""
    print("\n🧪 測試資料庫創建...")
    
    try:
        from multi_group_database import MultiGroupDatabaseManager
        
        # 創建臨時資料庫
        test_db_dir = tempfile.mkdtemp()
        test_db_path = os.path.join(test_db_dir, "test.db")
        
        # 創建資料庫管理器
        db_manager = MultiGroupDatabaseManager(test_db_path)
        print(f"✅ 資料庫創建成功: {test_db_path}")
        
        # 檢查表是否存在
        tables = db_manager.get_table_list()
        print(f"📋 資料庫表: {tables}")
        
        # 清理
        shutil.rmtree(test_db_dir)
        print("✅ 資料庫測試完成")
        
        return True
        
    except Exception as e:
        print(f"❌ 資料庫測試失敗: {e}")
        return False

def test_config_creation():
    """測試配置創建"""
    print("\n🧪 測試配置創建...")
    
    try:
        from multi_group_config import MultiGroupStrategyConfig, StrategyGroupConfig, LotRule
        
        # 創建測試配置
        lot_rules = [
            LotRule(lot_id=1),
            LotRule(lot_id=2)
        ]
        
        group_config = StrategyGroupConfig(
            group_id=1,
            lots_per_group=2,
            lot_rules=lot_rules,
            is_active=True
        )
        
        config = MultiGroupStrategyConfig(
            total_groups=1,
            lots_per_group=2,
            groups=[group_config]
        )
        
        print(f"✅ 配置創建成功: {config.total_groups} 組, {config.lots_per_group} 口/組")
        return True
        
    except Exception as e:
        print(f"❌ 配置創建失敗: {e}")
        return False

def test_position_manager_creation():
    """測試 PositionManager 創建"""
    print("\n🧪 測試 PositionManager 創建...")
    
    try:
        from multi_group_database import MultiGroupDatabaseManager
        from multi_group_position_manager import MultiGroupPositionManager
        from multi_group_config import MultiGroupStrategyConfig, StrategyGroupConfig, LotRule
        from unittest.mock import Mock
        
        # 創建臨時資料庫
        test_db_dir = tempfile.mkdtemp()
        test_db_path = os.path.join(test_db_dir, "test.db")
        db_manager = MultiGroupDatabaseManager(test_db_path)
        
        # 創建配置
        lot_rules = [LotRule(lot_id=1)]
        group_config = StrategyGroupConfig(
            group_id=1,
            lots_per_group=1,
            lot_rules=lot_rules,
            is_active=True
        )
        config = MultiGroupStrategyConfig(
            total_groups=1,
            lots_per_group=1,
            groups=[group_config]
        )
        
        # 創建模擬組件
        mock_order_manager = Mock()
        mock_simplified_tracker = Mock()
        mock_total_lot_manager = Mock()
        
        # 創建 PositionManager
        position_manager = MultiGroupPositionManager(
            db_manager=db_manager,
            strategy_config=config,
            order_manager=mock_order_manager,
            simplified_tracker=mock_simplified_tracker,
            total_lot_manager=mock_total_lot_manager
        )
        
        print("✅ PositionManager 創建成功")
        
        # 清理
        shutil.rmtree(test_db_dir)
        return True
        
    except Exception as e:
        print(f"❌ PositionManager 創建失敗: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_strategy_group_creation():
    """測試策略組創建"""
    print("\n🧪 測試策略組創建...")
    
    try:
        from multi_group_database import MultiGroupDatabaseManager
        from datetime import date
        
        # 創建臨時資料庫
        test_db_dir = tempfile.mkdtemp()
        test_db_path = os.path.join(test_db_dir, "test.db")
        db_manager = MultiGroupDatabaseManager(test_db_path)
        
        # 創建策略組
        current_date = date.today().isoformat()
        group_db_id = db_manager.create_strategy_group(
            date=current_date,
            group_id=1,
            direction="LONG",
            signal_time="10:30:00",
            range_high=22900.0,
            range_low=22850.0,
            total_lots=2
        )
        
        print(f"✅ 策略組創建成功: DB_ID={group_db_id}")
        
        # 測試查詢
        today_groups = db_manager.get_today_strategy_groups()
        print(f"📊 今日策略組數量: {len(today_groups)}")
        
        if today_groups:
            group = today_groups[0]
            print(f"📋 策略組字段: {list(group.keys())}")
            print(f"📋 group_pk: {group.get('group_pk')}")
            print(f"📋 logical_group_id: {group.get('logical_group_id')}")
        
        # 清理
        shutil.rmtree(test_db_dir)
        return True
        
    except Exception as e:
        print(f"❌ 策略組創建失敗: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """主測試函數"""
    print("🎯 簡化版 PositionManager 測試")
    print("=" * 50)
    
    tests = [
        test_imports,
        test_database_creation,
        test_config_creation,
        test_position_manager_creation,
        test_strategy_group_creation
    ]
    
    passed = 0
    total = len(tests)
    
    for test in tests:
        try:
            if test():
                passed += 1
            else:
                print("❌ 測試失敗")
        except Exception as e:
            print(f"❌ 測試異常: {e}")
    
    print(f"\n📊 測試結果: {passed}/{total} 通過")
    
    if passed == total:
        print("🎉 所有測試通過！測試環境準備就緒。")
        return True
    else:
        print("⚠️ 部分測試失敗，需要修復。")
        return False

if __name__ == "__main__":
    main()
