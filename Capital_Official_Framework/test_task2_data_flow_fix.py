#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
任务2验证测试：数据流重构
验证 StopLossExecutor 现在使用触发器数据而不是数据库查询
"""

import os
import sys
import sqlite3
from datetime import datetime

# 添加项目路径
sys.path.insert(0, os.path.dirname(__file__))

from multi_group_database import MultiGroupDatabaseManager
from stop_loss_executor import StopLossExecutor
from stop_loss_monitor import StopLossTrigger

def test_task2_data_flow_fix():
    """测试任务2的数据流重构修复"""
    print("🚀 开始测试任务2：数据流重构修复")
    print("=" * 60)
    
    # 设置测试数据库
    db_name = "test_task2_data_flow.db"
    if os.path.exists(db_name):
        os.remove(db_name)
    
    # 初始化组件
    db_manager = MultiGroupDatabaseManager(db_name)
    
    stop_executor = StopLossExecutor(
        db_manager=db_manager,
        console_enabled=True
    )
    
    print("✅ 组件初始化完成")
    
    # 创建策略组和部位（entry_price 为 None）
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
        entry_price=None,  # 数据库中仍然是 None
        entry_time=datetime.now().strftime('%H:%M:%S'),
        order_id='TEST_ORDER_002'
    )
    
    print(f"✅ 测试环境创建完成")
    print(f"   - 策略组 DB ID: {group_db_id}")
    print(f"   - 部位 ID: {position_id}")
    print(f"   - 数据库中进场价: None (模拟延迟)")
    
    # 创建包含完整数据的触发器（任务2的关键改进）
    trigger_info = StopLossTrigger(
        position_id=position_id,
        group_id=1,
        direction='SHORT',
        current_price=21435.0,
        stop_loss_price=21500.0,
        trigger_time=datetime.now().strftime('%H:%M:%S'),
        trigger_reason='移动停利: SHORT部位20%回撤触发',
        breach_amount=0.0,
        # 🔧 任务2：触发器现在包含完整的部位信息
        entry_price=21441.0,  # 来自内存的正确进场价
        peak_price=21426.0,   # 峰值价格
        quantity=1,
        lot_id=1,
        range_high=21500.0,
        range_low=21400.0
    )
    
    print(f"✅ 触发器创建完成（包含完整数据）")
    print(f"   - 触发器中进场价: {trigger_info.entry_price}")
    print(f"   - 触发器中峰值价: {trigger_info.peak_price}")
    print(f"   - 触发器中数量: {trigger_info.quantity}")
    
    print("\n🔍 执行停损，验证任务2修复:")
    print("-" * 60)
    
    # 执行停损 - 现在应该成功，因为使用触发器数据
    result = stop_executor.execute_stop_loss(trigger_info)
    
    print("-" * 60)
    print(f"📊 执行结果:")
    print(f"   - 成功: {result.success}")
    print(f"   - 错误信息: {result.error_message}")
    print(f"   - 订单ID: {result.order_id}")
    print(f"   - 执行价格: {result.execution_price}")
    print(f"   - 损益: {result.pnl}")
    
    if result.success:
        print("✅ 任务2修复成功！")
        print("   - StopLossExecutor 现在使用触发器数据")
        print("   - 不再依赖数据库查询")
        print("   - 数据源不一致问题已解决")
    else:
        print("❌ 任务2修复失败")
        print(f"   - 错误原因: {result.error_message}")
    
    print("\n" + "=" * 60)
    print("🎯 任务2测试完成！")

if __name__ == "__main__":
    test_task2_data_flow_fix()
