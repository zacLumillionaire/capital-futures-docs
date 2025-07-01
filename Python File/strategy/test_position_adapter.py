#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
測試部位持久化適配器
驗證適配器功能的正確性和完整性
"""

import sys
import os
from datetime import datetime, time
from decimal import Decimal

# 添加路徑以便導入模組
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

try:
    from strategy.position_persistence_adapter import (
        PositionPersistenceAdapter, create_position_manager,
        LIVE_TRADING_AVAILABLE, DATABASE_AVAILABLE, CONFIG_AVAILABLE
    )
    ADAPTER_AVAILABLE = True
except ImportError as e:
    print(f"❌ 導入適配器失敗: {e}")
    ADAPTER_AVAILABLE = False

try:
    from strategy.strategy_config import StrategyConfig, LotRule, StopLossType
    CONFIG_IMPORT_SUCCESS = True
except ImportError as e:
    print(f"❌ 導入策略配置失敗: {e}")
    CONFIG_IMPORT_SUCCESS = False

def test_adapter_initialization():
    """測試適配器初始化"""
    print("\n🧪 測試適配器初始化...")
    
    if not CONFIG_IMPORT_SUCCESS:
        print("⚠️  策略配置不可用，跳過初始化測試")
        return False
    
    try:
        # 創建測試配置
        config = StrategyConfig(
            trade_size_in_lots=2,
            stop_loss_type=StopLossType.RANGE_BASED,
            lot_rules=[
                LotRule(trailing_activation=15, trailing_pullback=0.20),
                LotRule(trailing_activation=20, trailing_pullback=0.25)
            ]
        )
        
        # 測試不啟用持久化
        adapter = PositionPersistenceAdapter(config, enable_persistence=False)
        print(f"✅ 適配器初始化成功 (持久化關閉): {adapter}")
        
        # 測試啟用持久化
        adapter_with_persistence = PositionPersistenceAdapter(config, enable_persistence=True)
        print(f"✅ 適配器初始化成功 (持久化開啟): {adapter_with_persistence}")
        
        # 測試便利函數
        adapter_from_function = create_position_manager(config, enable_persistence=True)
        print(f"✅ 便利函數創建成功: {adapter_from_function}")
        
        return True
        
    except Exception as e:
        print(f"❌ 適配器初始化失敗: {e}")
        return False

def test_persistence_status():
    """測試持久化狀態檢查"""
    print("\n🧪 測試持久化狀態檢查...")
    
    if not CONFIG_IMPORT_SUCCESS:
        print("⚠️  策略配置不可用，跳過狀態測試")
        return False
    
    try:
        config = StrategyConfig(trade_size_in_lots=1)
        adapter = PositionPersistenceAdapter(config, enable_persistence=True)
        
        # 取得持久化狀態
        status = adapter.get_persistence_status()
        print(f"持久化狀態: {status}")
        
        # 檢查關鍵狀態
        expected_keys = [
            "persistence_enabled", "database_available", "session_created",
            "session_id", "position_count", "position_ids"
        ]
        
        for key in expected_keys:
            if key in status:
                print(f"✅ {key}: {status[key]}")
            else:
                print(f"❌ 缺少狀態鍵: {key}")
        
        return True
        
    except Exception as e:
        print(f"❌ 持久化狀態測試失敗: {e}")
        return False

def test_property_proxy():
    """測試屬性代理功能"""
    print("\n🧪 測試屬性代理功能...")
    
    if not CONFIG_IMPORT_SUCCESS:
        print("⚠️  策略配置不可用，跳過屬性測試")
        return False
    
    try:
        config = StrategyConfig(trade_size_in_lots=1)
        adapter = PositionPersistenceAdapter(config, enable_persistence=False)
        
        # 測試屬性訪問
        properties_to_test = [
            'position', 'entry_price', 'entry_time', 'lots',
            'range_high', 'range_low', 'range_detected',
            'daily_entry_completed', 'first_breakout_detected', 'breakout_direction'
        ]
        
        for prop in properties_to_test:
            try:
                value = getattr(adapter, prop)
                print(f"✅ {prop}: {value}")
            except Exception as e:
                print(f"❌ 屬性 {prop} 訪問失敗: {e}")
        
        return True
        
    except Exception as e:
        print(f"❌ 屬性代理測試失敗: {e}")
        return False

def test_method_proxy():
    """測試方法代理功能"""
    print("\n🧪 測試方法代理功能...")
    
    if not CONFIG_IMPORT_SUCCESS:
        print("⚠️  策略配置不可用，跳過方法測試")
        return False
    
    try:
        config = StrategyConfig(trade_size_in_lots=1)
        adapter = PositionPersistenceAdapter(config, enable_persistence=False)
        
        # 測試方法調用
        methods_to_test = [
            ('get_position_summary', []),
            ('is_after_range_period', [datetime.now().time()]),
            ('reset_daily_state', []),
            ('close_all_positions', [22000.0, "manual"])
        ]
        
        for method_name, args in methods_to_test:
            try:
                method = getattr(adapter, method_name)
                result = method(*args)
                print(f"✅ {method_name}: {result}")
            except Exception as e:
                print(f"❌ 方法 {method_name} 調用失敗: {e}")
        
        return True
        
    except Exception as e:
        print(f"❌ 方法代理測試失敗: {e}")
        return False

def test_persistence_mode_toggle():
    """測試持久化模式切換"""
    print("\n🧪 測試持久化模式切換...")
    
    if not CONFIG_IMPORT_SUCCESS:
        print("⚠️  策略配置不可用，跳過模式切換測試")
        return False
    
    try:
        config = StrategyConfig(trade_size_in_lots=1)
        adapter = PositionPersistenceAdapter(config, enable_persistence=False)
        
        # 初始狀態
        print(f"初始持久化狀態: {adapter.enable_persistence}")
        
        # 嘗試啟用持久化
        success = adapter.enable_persistence_mode()
        print(f"啟用持久化結果: {success}")
        print(f"啟用後狀態: {adapter.enable_persistence}")
        
        # 關閉持久化
        adapter.disable_persistence_mode()
        print(f"關閉後狀態: {adapter.enable_persistence}")
        
        return True
        
    except Exception as e:
        print(f"❌ 持久化模式切換測試失敗: {e}")
        return False

def test_string_representation():
    """測試字串表示"""
    print("\n🧪 測試字串表示...")
    
    if not CONFIG_IMPORT_SUCCESS:
        print("⚠️  策略配置不可用，跳過字串測試")
        return False
    
    try:
        config = StrategyConfig(trade_size_in_lots=1)
        
        # 測試不同狀態的字串表示
        adapter_no_persistence = PositionPersistenceAdapter(config, enable_persistence=False)
        adapter_with_persistence = PositionPersistenceAdapter(config, enable_persistence=True)
        
        print(f"無持久化適配器: {adapter_no_persistence}")
        print(f"有持久化適配器: {adapter_with_persistence}")
        print(f"詳細表示: {repr(adapter_no_persistence)}")
        
        return True
        
    except Exception as e:
        print(f"❌ 字串表示測試失敗: {e}")
        return False

def test_database_operations():
    """測試資料庫操作"""
    print("\n🧪 測試資料庫操作...")
    
    if not CONFIG_IMPORT_SUCCESS:
        print("⚠️  策略配置不可用，跳過資料庫測試")
        return False
    
    if not DATABASE_AVAILABLE:
        print("⚠️  資料庫不可用，跳過資料庫測試")
        return False
    
    try:
        config = StrategyConfig(trade_size_in_lots=1)
        adapter = PositionPersistenceAdapter(config, enable_persistence=True)
        
        # 測試資料庫查詢方法
        active_positions = adapter.get_active_positions_from_db()
        print(f"✅ 活躍部位查詢: {len(active_positions)} 筆")
        
        # 測試停損歷史查詢 (假設lot_id=1)
        history = adapter.get_stop_loss_history(1)
        print(f"✅ 停損歷史查詢: {len(history)} 筆")
        
        # 測試快照創建
        adapter.create_position_snapshot(22000.0)
        print("✅ 快照創建測試完成")
        
        return True
        
    except Exception as e:
        print(f"❌ 資料庫操作測試失敗: {e}")
        return False

def main():
    """主測試函數"""
    print("🚀 開始測試部位持久化適配器")
    
    # 檢查依賴狀態
    print(f"\n📋 依賴檢查:")
    print(f"適配器可用: {ADAPTER_AVAILABLE}")
    print(f"LiveTradingPositionManager可用: {LIVE_TRADING_AVAILABLE}")
    print(f"資料庫模組可用: {DATABASE_AVAILABLE}")
    print(f"策略配置可用: {CONFIG_AVAILABLE}")
    print(f"配置導入成功: {CONFIG_IMPORT_SUCCESS}")
    
    if not ADAPTER_AVAILABLE:
        print("❌ 適配器不可用，無法執行測試")
        return False
    
    # 執行測試
    tests = [
        test_adapter_initialization,
        test_persistence_status,
        test_property_proxy,
        test_method_proxy,
        test_persistence_mode_toggle,
        test_string_representation,
        test_database_operations
    ]
    
    passed = 0
    total = len(tests)
    
    for test in tests:
        try:
            if test():
                passed += 1
            else:
                print(f"❌ 測試失敗: {test.__name__}")
        except Exception as e:
            print(f"❌ 測試異常: {test.__name__} - {e}")
    
    print(f"\n📊 測試結果: {passed}/{total} 通過")
    
    if passed == total:
        print("🎉 所有測試通過！")
        return True
    else:
        print("❌ 部分測試失敗")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
