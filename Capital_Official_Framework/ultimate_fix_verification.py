#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
终极修复验证测试
验证"内存与数据库状态不同步"问题的完整解决方案
"""

import os
import sys
import time
import sqlite3
from datetime import datetime

# 添加项目路径
sys.path.insert(0, os.path.dirname(__file__))

from multi_group_database import MultiGroupDatabaseManager
from optimized_risk_manager import OptimizedRiskManager
from stop_loss_executor import StopLossExecutor
from stop_loss_monitor import StopLossTrigger

def ultimate_fix_verification():
    """终极修复验证测试"""
    print("🎯 终极修复验证测试")
    print("=" * 80)
    print("目标：验证'内存与数据库状态不同步'问题的完整解决方案")
    print("=" * 80)
    
    # 设置测试数据库
    db_name = "ultimate_fix_verification.db"
    if os.path.exists(db_name):
        os.remove(db_name)
    
    print("🔧 初始化测试组件...")
    
    # 初始化组件
    db_manager = MultiGroupDatabaseManager(db_name)
    
    stop_executor = StopLossExecutor(
        db_manager=db_manager,
        console_enabled=True
    )
    
    risk_manager = OptimizedRiskManager(
        db_manager=db_manager,
        console_enabled=True
    )
    
    risk_manager.set_stop_loss_executor(stop_executor)
    
    print("✅ 组件初始化完成")
    
    # 创建测试环境
    print("\n📝 创建测试环境...")
    
    group_db_id = db_manager.create_strategy_group(
        date=datetime.now().strftime('%Y-%m-%d'),
        group_id=1,
        direction='SHORT',
        signal_time=datetime.now().strftime('%H:%M:%S'),
        range_high=21500.0,
        range_low=21400.0,
        total_lots=1
    )
    
    position_id = db_manager.create_position_record(
        group_id=1,
        lot_id=1,
        direction='SHORT',
        entry_price=None,  # 关键：数据库中初始为 None
        entry_time=datetime.now().strftime('%H:%M:%S'),
        order_id='ULTIMATE_TEST_001'
    )
    
    print(f"✅ 测试环境创建完成")
    print(f"   - 策略组 DB ID: {group_db_id}")
    print(f"   - 部位 ID: {position_id}")
    
    # 验证初始状态
    print(f"\n🔍 验证初始状态...")
    with db_manager.get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute('SELECT entry_price FROM position_records WHERE id = ?', (position_id,))
        row = cursor.fetchone()
        db_initial_price = row[0] if row else None
    
    print(f"   - 数据库中初始进场价: {db_initial_price}")
    
    # 步骤1：模拟成交回报（内存更新）
    print(f"\n📈 步骤1：模拟成交回报（内存更新）")
    print("-" * 60)
    
    entry_price = 21441.0
    
    # 直接更新内存状态（模拟成交回报）
    position_data = {
        'id': position_id,
        'group_id': 1,
        'direction': 'SHORT',
        'entry_price': entry_price,
        'quantity': 1,
        'lot_id': 1,
        'range_high': 21500.0,
        'range_low': 21400.0,
        'status': 'ACTIVE'
    }
    
    risk_manager.on_new_position(position_data)
    
    print(f"✅ 成交回报处理完成:")
    print(f"   - 内存中进场价: {entry_price}")
    print(f"   - 数据库中进场价: {db_initial_price} (异步延迟)")
    
    # 验证内存状态
    cached_position = risk_manager.position_cache.get(str(position_id))
    memory_entry_price = cached_position.get('entry_price') if cached_position else None
    print(f"   - 内存缓存验证: {memory_entry_price}")
    
    # 步骤2：测试内存保护机制
    print(f"\n🛡️ 步骤2：测试内存保护机制")
    print("-" * 60)
    
    print("🔄 强制触发数据库同步（测试内存保护）...")
    risk_manager._sync_with_database()
    
    # 检查内存保护是否有效
    cached_position_after = risk_manager.position_cache.get(str(position_id))
    memory_entry_price_after = cached_position_after.get('entry_price') if cached_position_after else None
    
    if memory_entry_price_after == entry_price:
        print("✅ 内存保护机制工作正常")
        print(f"   - 同步后内存进场价: {memory_entry_price_after}")
        memory_protection_ok = True
    else:
        print("❌ 内存保护机制失败")
        print(f"   - 同步后内存进场价: {memory_entry_price_after}")
        memory_protection_ok = False
    
    # 步骤3：测试新的数据流（关键测试）
    print(f"\n🎯 步骤3：测试新的数据流（关键测试）")
    print("-" * 60)
    
    # 创建包含完整数据的触发器
    trigger_info = StopLossTrigger(
        position_id=position_id,
        group_id=1,
        direction='SHORT',
        current_price=21435.0,
        stop_loss_price=21435.0,
        trigger_time=datetime.now().strftime('%H:%M:%S'),
        trigger_reason='移动停利: SHORT部位20%回撤触发',
        breach_amount=0.0,
        # 关键：触发器现在包含完整数据
        entry_price=entry_price,
        peak_price=21420.0,
        quantity=1,
        lot_id=1,
        range_high=21500.0,
        range_low=21400.0
    )
    
    print(f"📋 新数据流触发器:")
    print(f"   - 触发器中进场价: {trigger_info.entry_price}")
    print(f"   - 触发器中平仓价: {trigger_info.current_price}")
    print(f"   - 预期损益: {trigger_info.entry_price - trigger_info.current_price} 点")
    
    print(f"\n🚀 执行停损（使用新数据流）:")
    print("-" * 40)
    
    # 执行停损
    result = stop_executor.execute_stop_loss(trigger_info)
    
    print(f"\n📊 执行结果:")
    print(f"   - 成功: {result.success}")
    print(f"   - 错误信息: {result.error_message}")
    print(f"   - 订单ID: {result.order_id}")
    print(f"   - 执行价格: {result.execution_price}")
    print(f"   - 损益: {result.pnl} 点")
    
    # 步骤4：验证数据库状态（可选）
    print(f"\n📊 步骤4：验证数据库状态")
    print("-" * 60)
    
    with db_manager.get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute('SELECT entry_price, status FROM position_records WHERE id = ?', (position_id,))
        row = cursor.fetchone()
        if row:
            final_db_entry_price, final_db_status = row
            print(f"   - 数据库最终进场价: {final_db_entry_price}")
            print(f"   - 数据库最终状态: {final_db_status}")
        else:
            print("   - 数据库记录未找到")
    
    # 最终评估
    print(f"\n" + "=" * 80)
    print(f"🏁 最终评估结果")
    print(f"=" * 80)
    
    success_criteria = [
        ("内存保护机制", memory_protection_ok),
        ("停损执行成功", result.success),
        ("无进场价格错误", result.error_message is None or "缺少进场价格" not in result.error_message)
    ]
    
    all_success = all(criteria[1] for criteria in success_criteria)
    
    for name, status in success_criteria:
        status_icon = "✅" if status else "❌"
        print(f"{status_icon} {name}: {'通过' if status else '失败'}")
    
    if all_success:
        print(f"\n🎉 终极修复验证成功！")
        print(f"✅ 所有关键功能正常工作:")
        print(f"   1. 内存保护机制防止数据覆盖")
        print(f"   2. 触发器携带完整部位信息")
        print(f"   3. 执行器使用触发器数据，不依赖数据库")
        print(f"   4. 不再出现'缺少进场价格'错误")
        print(f"\n🔧 技术成就:")
        print(f"   - 数据源统一：决策层内存 → 执行层触发器")
        print(f"   - 执行解耦：不再依赖延迟的数据库查询")
        print(f"   - 数据保护：内存状态不被数据库覆盖")
        print(f"   - 最终一致性：异步更新保证数据库同步")
        
        if result.pnl:
            print(f"\n💰 交易结果: {result.pnl:+.1f} 点")
    else:
        print(f"\n❌ 终极修复验证失败")
        print(f"需要进一步调试以下问题:")
        for name, status in success_criteria:
            if not status:
                print(f"   - {name}")
    
    print(f"\n🎯 终极修复验证测试完成！")
    print(f"=" * 80)
    
    return all_success

if __name__ == "__main__":
    success = ultimate_fix_verification()
    exit(0 if success else 1)
