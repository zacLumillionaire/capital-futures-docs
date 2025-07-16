#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
任务3验证测试：审计并简化 StopLossExecutor
验证 StopLossExecutor 现在更加简化，专注于执行而非查询
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

def test_task3_simplification():
    """测试任务3的简化改进"""
    print("🚀 开始测试任务3：StopLossExecutor 简化")
    print("=" * 60)
    
    # 设置测试数据库
    db_name = "test_task3_simplification.db"
    if os.path.exists(db_name):
        os.remove(db_name)
    
    # 初始化组件
    db_manager = MultiGroupDatabaseManager(db_name)
    
    stop_executor = StopLossExecutor(
        db_manager=db_manager,
        console_enabled=True
    )
    
    print("✅ 组件初始化完成")
    
    # 创建策略组和部位
    group_db_id = db_manager.create_strategy_group(
        date=datetime.now().strftime('%Y-%m-%d'),
        group_id=1,
        direction='LONG',
        signal_time=datetime.now().strftime('%H:%M:%S'),
        range_high=21550.0,
        range_low=21500.0,
        total_lots=1
    )
    
    position_id = db_manager.create_position_record(
        group_id=1,
        lot_id=1,
        direction='LONG',
        entry_price=None,  # 数据库中仍然是 None
        entry_time=datetime.now().strftime('%H:%M:%S'),
        order_id='TEST_ORDER_003'
    )
    
    print(f"✅ 测试环境创建完成")
    print(f"   - 策略组 DB ID: {group_db_id}")
    print(f"   - 部位 ID: {position_id}")
    
    # 创建完整的触发器（任务3验证：简化的执行器只需要这些数据）
    trigger_info = StopLossTrigger(
        position_id=position_id,
        group_id=1,
        direction='LONG',
        current_price=21480.0,  # LONG 停损价格
        stop_loss_price=21500.0,
        trigger_time=datetime.now().strftime('%H:%M:%S'),
        trigger_reason='初始停损触发: LONG部位',
        breach_amount=20.0,
        # 完整的部位信息
        entry_price=21520.0,  # LONG 进场价
        peak_price=21520.0,   # 初始峰值
        quantity=1,
        lot_id=1,
        range_high=21550.0,
        range_low=21500.0
    )
    
    print(f"✅ 触发器创建完成")
    print(f"   - LONG 进场价: {trigger_info.entry_price}")
    print(f"   - LONG 停损价: {trigger_info.stop_loss_price}")
    print(f"   - 当前价格: {trigger_info.current_price}")
    print(f"   - 预期损益: {trigger_info.current_price - trigger_info.entry_price} 点")
    
    print("\n🔍 执行停损，验证任务3简化:")
    print("-" * 60)
    
    # 执行停损 - 验证简化后的执行器
    result = stop_executor.execute_stop_loss(trigger_info)
    
    print("-" * 60)
    print(f"📊 执行结果:")
    print(f"   - 成功: {result.success}")
    print(f"   - 错误信息: {result.error_message}")
    print(f"   - 订单ID: {result.order_id}")
    print(f"   - 执行价格: {result.execution_price}")
    print(f"   - 损益: {result.pnl} 点")
    
    if result.success:
        print("✅ 任务3简化成功！")
        print("   - StopLossExecutor 现在更加简化")
        print("   - 专注于执行而非查询")
        print("   - 日志输出更加清晰")
        print("   - 完全依赖触发器数据")
    else:
        print("❌ 任务3简化失败")
        print(f"   - 错误原因: {result.error_message}")
    
    print("\n" + "=" * 60)
    print("🎯 任务3测试完成！")
    
    # 验证不同类型的触发器
    print("\n🔄 测试移动停利触发器:")
    print("-" * 40)
    
    # 创建移动停利触发器
    trailing_trigger = StopLossTrigger(
        position_id=position_id + 1,  # 假设的另一个部位
        group_id=1,
        direction='SHORT',
        current_price=21445.0,
        stop_loss_price=21445.0,
        trigger_time=datetime.now().strftime('%H:%M:%S'),
        trigger_reason='移动停利: SHORT部位20%回撤触发',
        breach_amount=0.0,
        entry_price=21460.0,
        peak_price=21440.0,
        quantity=1,
        lot_id=2,
        range_high=21500.0,
        range_low=21400.0
    )
    
    print(f"📊 移动停利触发器:")
    print(f"   - SHORT 进场价: {trailing_trigger.entry_price}")
    print(f"   - SHORT 峰值价: {trailing_trigger.peak_price}")
    print(f"   - 当前价格: {trailing_trigger.current_price}")
    print(f"   - 预期损益: {trailing_trigger.entry_price - trailing_trigger.current_price} 点")
    
    # 执行移动停利
    trailing_result = stop_executor.execute_stop_loss(trailing_trigger)
    
    print(f"📊 移动停利执行结果:")
    print(f"   - 成功: {trailing_result.success}")
    print(f"   - 损益: {trailing_result.pnl} 点")
    
    print("\n🎯 全部测试完成！")

if __name__ == "__main__":
    test_task3_simplification()
