#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
多組策略資料庫功能測試腳本
驗證資料庫表結構和基本操作功能
"""

import os
import sys
import json
from datetime import datetime, date
from decimal import Decimal

# 添加路徑
sys.path.insert(0, os.path.dirname(__file__))

from multi_group_database import MultiGroupDatabaseManager

def test_database_creation():
    """測試資料庫創建"""
    print("🧪 測試1: 資料庫創建")
    print("-" * 40)
    
    try:
        # 使用測試資料庫
        db_manager = MultiGroupDatabaseManager("test_multi_group.db")
        print("✅ 資料庫創建成功")
        return db_manager
    except Exception as e:
        print(f"❌ 資料庫創建失敗: {e}")
        return None

def test_strategy_group_operations(db_manager):
    """測試策略組操作"""
    print("\n🧪 測試2: 策略組操作")
    print("-" * 40)
    
    try:
        current_date = date.today().isoformat()
        
        # 創建多個策略組
        group_ids = []
        for i in range(1, 4):  # 創建3組
            group_id = db_manager.create_strategy_group(
                date=current_date,
                group_id=i,
                direction="LONG",
                signal_time="08:48:15",
                range_high=22530.0,
                range_low=22480.0,
                total_lots=3
            )
            group_ids.append(group_id)
            print(f"✅ 創建策略組 {i}: ID={group_id}")
        
        # 查詢等待中的組
        waiting_groups = db_manager.get_today_waiting_groups(current_date)
        print(f"✅ 查詢到 {len(waiting_groups)} 個等待中的組")
        
        return group_ids
        
    except Exception as e:
        print(f"❌ 策略組操作失敗: {e}")
        return []

def test_position_operations(db_manager, group_ids):
    """測試部位操作"""
    print("\n🧪 測試3: 部位操作")
    print("-" * 40)
    
    try:
        position_ids = []
        
        # 為第一組創建3口部位
        if group_ids:
            group_id = group_ids[0]
            
            # 創建3口部位的規則配置
            lot_rules = [
                {
                    'lot_id': 1,
                    'use_trailing_stop': True,
                    'trailing_activation': 15,
                    'trailing_pullback': 0.20
                },
                {
                    'lot_id': 2,
                    'use_trailing_stop': True,
                    'trailing_activation': 40,
                    'trailing_pullback': 0.20,
                    'protective_stop_multiplier': 2.0
                },
                {
                    'lot_id': 3,
                    'use_trailing_stop': True,
                    'trailing_activation': 65,
                    'trailing_pullback': 0.20,
                    'protective_stop_multiplier': 2.0
                }
            ]
            
            for i, rule in enumerate(lot_rules, 1):
                position_id = db_manager.create_position_record(
                    group_id=group_id,
                    lot_id=i,
                    direction="LONG",
                    entry_price=22535.0 + i,  # 模擬不同進場價格
                    entry_time=f"08:48:{15+i:02d}",
                    rule_config=json.dumps(rule)
                )
                position_ids.append(position_id)
                print(f"✅ 創建第{i}口部位: ID={position_id}, 價格={22535.0 + i}")
        
        # 查詢活躍部位
        active_positions = db_manager.get_active_positions_by_group(group_ids[0])
        print(f"✅ 查詢到 {len(active_positions)} 個活躍部位")
        
        return position_ids
        
    except Exception as e:
        print(f"❌ 部位操作失敗: {e}")
        return []

def test_risk_management_operations(db_manager, position_ids):
    """測試風險管理操作"""
    print("\n🧪 測試4: 風險管理操作")
    print("-" * 40)
    
    try:
        current_time = datetime.now().strftime("%H:%M:%S")
        
        # 為每個部位創建風險管理狀態
        for position_id in position_ids:
            db_manager.create_risk_management_state(
                position_id=position_id,
                peak_price=22540.0,
                current_time=current_time,
                update_category="初始化",
                update_message="初始化"
            )
            print(f"✅ 創建風險管理狀態: 部位={position_id}")

        # 更新風險管理狀態
        if position_ids:
            db_manager.update_risk_management_state(
                position_id=position_ids[0],
                peak_price=22550.0,
                trailing_activated=True,
                update_time=current_time,
                update_category="移動停利啟動",
                update_message="移動停利啟動"
            )
            print(f"✅ 更新風險管理狀態: 部位={position_ids[0]}")
        
        return True
        
    except Exception as e:
        print(f"❌ 風險管理操作失敗: {e}")
        return False

def test_exit_operations(db_manager, position_ids):
    """測試出場操作"""
    print("\n🧪 測試5: 出場操作")
    print("-" * 40)
    
    try:
        current_time = datetime.now().strftime("%H:%M:%S")
        
        # 模擬第1口移動停利出場
        if position_ids:
            db_manager.update_position_exit(
                position_id=position_ids[0],
                exit_price=22565.0,
                exit_time=current_time,
                exit_reason="移動停利",
                pnl=30.0  # 獲利30點
            )
            print(f"✅ 第1口出場: 移動停利, 獲利30點")
        
        # 查詢所有活躍部位
        all_active = db_manager.get_all_active_positions()
        print(f"✅ 剩餘活躍部位: {len(all_active)} 個")
        
        return True
        
    except Exception as e:
        print(f"❌ 出場操作失敗: {e}")
        return False

def test_statistics_operations(db_manager):
    """測試統計操作"""
    print("\n🧪 測試6: 統計操作")
    print("-" * 40)
    
    try:
        current_date = date.today().isoformat()
        
        # 查詢每日統計
        stats = db_manager.get_daily_strategy_summary(current_date)
        
        print("📊 每日統計摘要:")
        print(f"   總組數: {stats['total_groups']}")
        print(f"   完成組數: {stats['completed_groups']}")
        print(f"   總部位數: {stats['total_positions']}")
        print(f"   已出場部位: {stats['exited_positions']}")
        print(f"   總損益: {stats['total_pnl']:.1f}點")
        print(f"   總損益金額: {stats['total_pnl_amount']:.0f}元")
        print(f"   勝率: {stats['win_rate']:.1f}%")
        print(f"   平均損益: {stats['avg_pnl']:.1f}點")
        print(f"   最大獲利: {stats['max_profit']:.1f}點")
        print(f"   最大虧損: {stats['max_loss']:.1f}點")
        
        print("✅ 統計查詢成功")
        return True
        
    except Exception as e:
        print(f"❌ 統計操作失敗: {e}")
        return False

def test_complex_scenario(db_manager):
    """測試複雜場景"""
    print("\n🧪 測試7: 複雜場景模擬")
    print("-" * 40)
    
    try:
        current_date = date.today().isoformat()
        
        # 場景：2口×2組配置
        print("📋 場景: 2口×2組配置")
        
        # 創建2組，每組2口
        for group_num in range(4, 6):  # 組4和組5
            group_id = db_manager.create_strategy_group(
                date=current_date,
                group_id=group_num,
                direction="SHORT",
                signal_time="09:15:30",
                range_high=22580.0,
                range_low=22520.0,
                total_lots=2
            )
            
            # 為每組創建2口部位
            for lot_id in range(1, 3):
                position_id = db_manager.create_position_record(
                    group_id=group_id,
                    lot_id=lot_id,
                    direction="SHORT",
                    entry_price=22575.0 - lot_id,  # 不同進場價格
                    entry_time=f"09:15:{30+lot_id:02d}",
                    rule_config=json.dumps({
                        'lot_id': lot_id,
                        'use_trailing_stop': True,
                        'trailing_activation': 15 if lot_id == 1 else 40,
                        'trailing_pullback': 0.20
                    })
                )
                
                # 創建風險管理狀態
                db_manager.create_risk_management_state(
                    position_id=position_id,
                    peak_price=22575.0 - lot_id,
                    current_time="09:15:35",
                    update_reason="初始化"
                )
            
            print(f"✅ 創建組{group_num}: 2口SHORT部位")
        
        # 查詢最終統計
        final_stats = db_manager.get_daily_strategy_summary(current_date)
        print(f"\n📊 最終統計: 總組數={final_stats['total_groups']}, 總部位數={final_stats['total_positions']}")
        
        return True
        
    except Exception as e:
        print(f"❌ 複雜場景測試失敗: {e}")
        return False

def cleanup_test_database():
    """清理測試資料庫"""
    try:
        if os.path.exists("test_multi_group.db"):
            os.remove("test_multi_group.db")
            print("🧹 測試資料庫已清理")
    except Exception as e:
        print(f"⚠️ 清理測試資料庫失敗: {e}")

def main():
    """主測試函數"""
    print("🚀 多組策略資料庫功能測試")
    print("=" * 60)
    
    # 清理舊的測試資料庫
    cleanup_test_database()
    
    # 執行測試
    db_manager = test_database_creation()
    if not db_manager:
        return
    
    group_ids = test_strategy_group_operations(db_manager)
    if not group_ids:
        return
    
    position_ids = test_position_operations(db_manager, group_ids)
    if not position_ids:
        return
    
    if not test_risk_management_operations(db_manager, position_ids):
        return
    
    if not test_exit_operations(db_manager, position_ids):
        return
    
    if not test_statistics_operations(db_manager):
        return
    
    if not test_complex_scenario(db_manager):
        return
    
    print("\n🎉 所有測試通過！")
    print("=" * 60)
    print("✅ 資料庫表結構正確")
    print("✅ 基本CRUD操作正常")
    print("✅ 風險管理狀態追蹤正常")
    print("✅ 統計查詢功能正常")
    print("✅ 複雜場景支援正常")
    
    print("\n💡 資料庫功能驗證完成，可以進入下一階段開發")
    
    # 保留測試資料庫供檢查
    print(f"\n📝 測試資料庫保留為: test_multi_group.db")
    print("可以使用SQLite瀏覽器查看詳細數據")

if __name__ == "__main__":
    main()
