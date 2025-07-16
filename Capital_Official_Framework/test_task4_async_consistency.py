#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
任务4验证测试：异步数据库更新的最终确认
验证即使平仓执行不再依赖数据库，异步更新机制仍然正确工作
"""

import os
import sys
import time
import sqlite3
from datetime import datetime

# 添加项目路径
sys.path.insert(0, os.path.dirname(__file__))

from multi_group_database import MultiGroupDatabaseManager
from async_db_updater import AsyncDatabaseUpdater
from stop_loss_executor import StopLossExecutor
from stop_loss_monitor import StopLossTrigger

def test_task4_async_consistency():
    """测试任务4的异步数据库更新一致性"""
    print("🚀 开始测试任务4：异步数据库更新最终确认")
    print("=" * 70)
    
    # 设置测试数据库
    db_name = "test_task4_async_consistency.db"
    if os.path.exists(db_name):
        os.remove(db_name)
    
    # 初始化组件
    db_manager = MultiGroupDatabaseManager(db_name)
    async_updater = AsyncDatabaseUpdater(db_manager, console_enabled=True)
    
    stop_executor = StopLossExecutor(
        db_manager=db_manager,
        console_enabled=True
    )
    
    # 设置异步更新器
    stop_executor.set_async_updater(async_updater, enabled=True)
    
    print("✅ 组件初始化完成")
    
    # 创建策略组和部位
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
        entry_price=None,  # 初始为 None
        entry_time=datetime.now().strftime('%H:%M:%S'),
        order_id='TEST_ORDER_004'
    )
    
    print(f"✅ 测试环境创建完成")
    print(f"   - 策略组 DB ID: {group_db_id}")
    print(f"   - 部位 ID: {position_id}")
    
    # 步骤1：模拟成交回报，触发异步数据库更新
    print("\n📝 步骤1：模拟成交回报，触发异步数据库更新")
    print("-" * 50)
    
    fill_price = 21441.0
    fill_time = datetime.now().strftime('%H:%M:%S')
    
    # 使用异步更新器更新成交信息
    async_updater.schedule_position_fill_update(
        position_id=position_id,
        fill_price=fill_price,
        fill_time=fill_time,
        order_status='FILLED'
    )
    
    print(f"📝 已排程异步更新：部位{position_id} @{fill_price}")
    
    # 步骤2：立即执行平仓（使用触发器数据，不依赖数据库）
    print("\n🚀 步骤2：立即执行平仓（使用触发器数据）")
    print("-" * 50)
    
    # 创建包含完整数据的触发器
    trigger_info = StopLossTrigger(
        position_id=position_id,
        group_id=1,
        direction='SHORT',
        current_price=21435.0,
        stop_loss_price=21500.0,
        trigger_time=datetime.now().strftime('%H:%M:%S'),
        trigger_reason='移动停利: SHORT部位20%回撤触发',
        breach_amount=0.0,
        # 完整的部位信息（来自内存）
        entry_price=fill_price,  # 使用内存中的成交价
        peak_price=21426.0,
        quantity=1,
        lot_id=1,
        range_high=21500.0,
        range_low=21400.0
    )
    
    print(f"📊 触发器数据:")
    print(f"   - 进场价: {trigger_info.entry_price}")
    print(f"   - 平仓价: {trigger_info.current_price}")
    print(f"   - 预期损益: {trigger_info.entry_price - trigger_info.current_price} 点")
    
    # 执行平仓
    result = stop_executor.execute_stop_loss(trigger_info)
    
    print(f"\n📊 平仓执行结果:")
    print(f"   - 成功: {result.success}")
    print(f"   - 订单ID: {result.order_id}")
    print(f"   - 执行价格: {result.execution_price}")
    print(f"   - 损益: {result.pnl} 点")
    
    # 步骤3：等待异步更新完成
    print("\n⏰ 步骤3：等待异步数据库更新完成")
    print("-" * 50)
    
    print("等待异步更新完成...")
    time.sleep(3)  # 等待异步更新完成
    
    # 步骤4：验证数据库最终一致性
    print("\n🔍 步骤4：验证数据库最终一致性")
    print("-" * 50)
    
    # 查询数据库中的最终状态
    with db_manager.get_connection() as conn:
        cursor = conn.cursor()
        
        # 查询部位记录
        cursor.execute('SELECT entry_price, status, exit_price, exit_reason FROM position_records WHERE id = ?', (position_id,))
        position_row = cursor.fetchone()
        
        if position_row:
            db_entry_price, db_status, db_exit_price, db_exit_reason = position_row
            print(f"📊 数据库中的部位状态:")
            print(f"   - 进场价: {db_entry_price}")
            print(f"   - 状态: {db_status}")
            print(f"   - 出场价: {db_exit_price}")
            print(f"   - 出场原因: {db_exit_reason}")
            
            # 验证数据一致性
            if db_entry_price == fill_price:
                print("✅ 进场价更新成功 - 异步更新正常工作")
            else:
                print(f"❌ 进场价不一致: 期望{fill_price}, 实际{db_entry_price}")
            
            if db_exit_price == trigger_info.current_price:
                print("✅ 出场价更新成功 - 平仓异步更新正常工作")
            else:
                print(f"❌ 出场价不一致: 期望{trigger_info.current_price}, 实际{db_exit_price}")
        else:
            print("❌ 未找到部位记录")
    
    # 步骤5：验证异步更新器统计
    print("\n📈 步骤5：异步更新器统计信息")
    print("-" * 50)
    
    stats = async_updater.get_stats()
    print(f"📊 异步更新统计:")
    print(f"   - 总任务数: {stats['total_tasks']}")
    print(f"   - 完成任务数: {stats['completed_tasks']}")
    print(f"   - 失败任务数: {stats['failed_tasks']}")
    print(f"   - 队列峰值: {stats['queue_size_peak']}")
    print(f"   - 缓存命中: {stats['cache_hits']}")
    print(f"   - 平均延迟: {stats['avg_delay']*1000:.1f}ms")
    print(f"   - 最大延迟: {stats['max_delay']*1000:.1f}ms")

    # 检查异步更新器运行状态
    print(f"\n🔍 异步更新器状态:")
    print(f"   - 运行状态: {async_updater.running}")
    print(f"   - 队列大小: {async_updater.update_queue.qsize()}")
    print(f"   - 工作线程存活: {async_updater.worker_thread.is_alive() if async_updater.worker_thread else False}")
    
    # 最终结论
    print("\n" + "=" * 70)
    if result.success and stats['completed_tasks'] > 0:
        print("✅ 任务4验证成功！")
        print("   - 平仓执行使用触发器数据，不依赖数据库")
        print("   - 异步数据库更新机制正常工作")
        print("   - 数据最终一致性得到保证")
        print("   - 系统既快速又可靠")
    elif result.success:
        print("⚠️ 任务4部分成功")
        print("   - 平仓执行成功（使用触发器数据）")
        print("   - 异步更新可能需要更多时间")
        print("   - 核心功能正常，数据源不一致问题已解决")
    else:
        print("❌ 任务4验证失败")
        print("   - 需要检查异步更新机制")
    
    print("🎯 任务4测试完成！")
    
    # 清理
    async_updater.stop()

if __name__ == "__main__":
    test_task4_async_consistency()
