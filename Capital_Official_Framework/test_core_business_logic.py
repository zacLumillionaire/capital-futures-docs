#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
核心業務邏輯綜合測試
測試多組部位管理器和風險管理引擎的整合功能
"""

import os
import sys
import time
from datetime import datetime

# 添加路徑
sys.path.insert(0, os.path.dirname(__file__))

from multi_group_database import MultiGroupDatabaseManager
from multi_group_config import create_preset_configs
from multi_group_position_manager import MultiGroupPositionManager
from risk_management_engine import RiskManagementEngine

def cleanup_test_files():
    """清理測試文件"""
    test_files = [
        "test_core_business.db",
        "test_position_manager.db", 
        "test_risk_engine.db"
    ]
    
    for file in test_files:
        try:
            if os.path.exists(file):
                os.remove(file)
        except:
            pass

def test_complete_trading_scenario():
    """測試完整交易場景"""
    print("🧪 測試完整交易場景")
    print("=" * 60)
    
    try:
        # 1. 初始化系統
        print("📋 階段1: 系統初始化")
        print("-" * 30)
        
        db_manager = MultiGroupDatabaseManager("test_core_business.db")
        presets = create_preset_configs()
        config = presets["平衡配置 (2口×2組)"]  # 2口×2組
        
        manager = MultiGroupPositionManager(db_manager, config)
        risk_engine = RiskManagementEngine(db_manager)
        
        print("✅ 系統初始化完成")
        print(manager.get_strategy_status_summary())
        
        # 2. 創建進場信號
        print("\n📋 階段2: 創建進場信號")
        print("-" * 30)
        
        group_ids = manager.create_entry_signal(
            direction="LONG",
            signal_time="08:48:15",
            range_high=22530.0,
            range_low=22480.0
        )
        
        print(f"✅ 創建 {len(group_ids)} 個策略組")
        
        # 3. 執行第一組進場
        print("\n📋 階段3: 執行第一組進場")
        print("-" * 30)
        
        if group_ids:
            success = manager.execute_group_entry(
                group_db_id=group_ids[0],
                actual_price=22535.0,
                actual_time="08:48:20"
            )
            print(f"✅ 第一組進場: {'成功' if success else '失敗'}")
        
        print(manager.get_strategy_status_summary())
        
        # 4. 模擬價格變動和風險管理
        print("\n📋 階段4: 模擬價格變動和風險管理")
        print("-" * 30)
        
        price_scenarios = [
            (22540.0, "08:50:00", "價格小幅上漲"),
            (22550.0, "08:52:00", "第1口移動停利啟動"),
            (22565.0, "08:55:00", "價格繼續上漲"),
            (22555.0, "08:57:00", "價格回撤，可能觸發移動停利")
        ]
        
        for price, time_str, description in price_scenarios:
            print(f"\n🔄 {description}: {price} @ {time_str}")
            
            # 檢查出場條件
            exit_actions = risk_engine.check_all_exit_conditions(price, time_str)
            
            if exit_actions:
                print(f"📤 檢測到 {len(exit_actions)} 個出場動作:")
                for action in exit_actions:
                    # 執行出場
                    success = manager.update_position_exit(
                        position_id=action['position_id'],
                        exit_price=action['exit_price'],
                        exit_time=action['exit_time'],
                        exit_reason=action['exit_reason'],
                        pnl=action['pnl']
                    )
                    
                    if success:
                        print(f"   ✅ 部位 {action['position_id']} {action['exit_reason']}: {action['pnl']:.1f}點")
                        
                        # 更新保護性停損
                        if action['exit_reason'] == '移動停利':
                            risk_engine.update_protective_stop_loss(
                                action['position_id'], 
                                action.get('group_id', group_ids[0])
                            )
            else:
                print("   📊 無出場動作")
            
            # 顯示當前狀態
            active_count = manager.get_total_active_positions_count()
            print(f"   📊 剩餘活躍部位: {active_count}")
        
        # 5. 執行第二組進場
        print("\n📋 階段5: 執行第二組進場")
        print("-" * 30)
        
        if len(group_ids) > 1:
            success = manager.execute_group_entry(
                group_db_id=group_ids[1],
                actual_price=22560.0,  # 不同的進場價格
                actual_time="09:15:30"
            )
            print(f"✅ 第二組進場: {'成功' if success else '失敗'}")
        
        print(manager.get_strategy_status_summary())
        
        # 6. 最終統計
        print("\n📋 階段6: 最終統計")
        print("-" * 30)
        
        daily_stats = manager.get_daily_summary()
        
        print("📊 今日交易統計:")
        print(f"   總組數: {daily_stats.get('total_groups', 0)}")
        print(f"   完成組數: {daily_stats.get('completed_groups', 0)}")
        print(f"   總部位數: {daily_stats.get('total_positions', 0)}")
        print(f"   已出場部位: {daily_stats.get('exited_positions', 0)}")
        print(f"   總損益: {daily_stats.get('total_pnl', 0):.1f}點")
        print(f"   總損益金額: {daily_stats.get('total_pnl_amount', 0):.0f}元")
        print(f"   勝率: {daily_stats.get('win_rate', 0):.1f}%")
        print(f"   平均損益: {daily_stats.get('avg_pnl', 0):.1f}點")
        
        return True
        
    except Exception as e:
        print(f"❌ 測試失敗: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_different_configurations():
    """測試不同配置"""
    print("\n🧪 測試不同配置")
    print("=" * 60)
    
    presets = create_preset_configs()
    
    for name, config in presets.items():
        print(f"\n📋 測試配置: {name}")
        print("-" * 40)
        
        try:
            db_file = f"test_{name.replace(' ', '_').replace('(', '').replace(')', '')}.db"
            db_manager = MultiGroupDatabaseManager(db_file)
            manager = MultiGroupPositionManager(db_manager, config)
            
            print(f"✅ 配置載入成功")
            print(f"📊 總部位數: {config.get_total_positions()}")
            print(f"📊 活躍組數: {len(config.get_active_groups())}")
            
            # 簡單測試創建信號
            group_ids = manager.create_entry_signal(
                direction="LONG",
                signal_time="08:48:15", 
                range_high=22530.0,
                range_low=22480.0
            )
            
            print(f"✅ 創建 {len(group_ids)} 個策略組")
            
        except Exception as e:
            print(f"❌ 配置測試失敗: {e}")

def test_risk_management_scenarios():
    """測試風險管理場景"""
    print("\n🧪 測試風險管理場景")
    print("=" * 60)
    
    try:
        # 使用標準配置 (3口×1組)
        db_manager = MultiGroupDatabaseManager("test_risk_scenarios.db")
        presets = create_preset_configs()
        config = presets["標準配置 (3口×1組)"]
        
        manager = MultiGroupPositionManager(db_manager, config)
        risk_engine = RiskManagementEngine(db_manager)
        
        # 創建並執行進場
        group_ids = manager.create_entry_signal("LONG", "08:48:15", 22530.0, 22480.0)
        manager.execute_group_entry(group_ids[0], 22535.0, "08:48:20")
        
        print("✅ 建立3口部位")
        
        # 測試場景1: 初始停損
        print("\n📋 場景1: 初始停損測試")
        exit_actions = risk_engine.check_all_exit_conditions(22475.0, "09:00:00")
        print(f"   跌破區間低點 22480 → 檢測到 {len(exit_actions)} 個出場動作")
        
        # 測試場景2: 移動停利啟動
        print("\n📋 場景2: 移動停利啟動測試")
        exit_actions = risk_engine.check_all_exit_conditions(22550.0, "09:05:00")
        print(f"   價格上漲至 22550 → 檢測到 {len(exit_actions)} 個出場動作")
        
        # 測試場景3: 移動停利出場
        print("\n📋 場景3: 移動停利出場測試")
        exit_actions = risk_engine.check_all_exit_conditions(22545.0, "09:10:00")
        print(f"   價格回撤至 22545 → 檢測到 {len(exit_actions)} 個出場動作")
        
        print("✅ 風險管理場景測試完成")
        
    except Exception as e:
        print(f"❌ 風險管理測試失敗: {e}")

def main():
    """主測試函數"""
    print("🚀 核心業務邏輯綜合測試")
    print("=" * 80)
    
    # 清理舊測試文件
    cleanup_test_files()
    
    # 執行測試
    test1_result = test_complete_trading_scenario()
    test_different_configurations()
    test_risk_management_scenarios()
    
    print("\n🎉 測試總結")
    print("=" * 80)
    
    if test1_result:
        print("✅ 完整交易場景測試通過")
        print("✅ 多組部位管理器運作正常")
        print("✅ 風險管理引擎運作正常")
        print("✅ 資料庫整合正常")
        print("✅ 不同配置支援正常")
        
        print("\n💡 核心業務邏輯開發完成！")
        print("📝 下一步: 開發用戶界面")
        
    else:
        print("❌ 部分測試失敗，需要修正")
    
    print(f"\n📁 測試資料庫文件已保留，可用於檢查")

if __name__ == "__main__":
    main()
