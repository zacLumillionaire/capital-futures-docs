#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
简单的数据源不一致测试
直接测试 StopLossExecutor 的数据源对比日志功能
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
from simplified_order_tracker import GlobalExitManager

def test_data_source_logging():
    """测试数据源对比日志功能"""
    print("🚀 开始测试数据源对比日志功能")
    print("=" * 50)
    
    # 设置测试数据库
    db_name = "simple_test_data_source.db"
    if os.path.exists(db_name):
        os.remove(db_name)
    
    # 初始化组件
    db_manager = MultiGroupDatabaseManager(db_name)

    stop_executor = StopLossExecutor(
        db_manager=db_manager,
        console_enabled=True  # 启用控制台日志
    )
    
    print("✅ 组件初始化完成")
    
    # 首先创建策略组
    group_db_id = db_manager.create_strategy_group(
        date=datetime.now().strftime('%Y-%m-%d'),
        group_id=1,
        direction='SHORT',
        signal_time=datetime.now().strftime('%H:%M:%S'),
        range_high=21500.0,
        range_low=21400.0,
        total_lots=1
    )
    print(f"✅ 策略组创建完成，DB ID: {group_db_id}")

    # 创建测试部位（entry_price 为 None）
    position_id = db_manager.create_position_record(
        group_id=1,  # 逻辑组别ID
        lot_id=1,    # 口数ID
        direction='SHORT',
        entry_price=None,  # 关键：设置为 None 模拟数据库延迟
        entry_time=datetime.now().strftime('%H:%M:%S'),
        order_id='TEST_ORDER_001'
    )
    print(f"✅ 测试部位创建完成，ID: {position_id}")
    
    # 创建触发器信息（包含正确的价格信息）
    trigger_info = StopLossTrigger(
        position_id=position_id,
        group_id=1,
        direction='SHORT',
        current_price=21435.0,  # 触发器中有正确的价格
        stop_loss_price=21500.0,
        trigger_time=datetime.now().strftime('%H:%M:%S'),
        trigger_reason='移动停利: SHORT部位20%回撤触发',
        breach_amount=0.0
    )
    
    # 为触发器添加进场价格信息（模拟内存中的正确数据）
    trigger_info.entry_price = 21441.0  # 内存中的正确进场价
    
    print(f"✅ 触发器信息创建完成")
    print(f"   - 触发器中的进场价: {getattr(trigger_info, 'entry_price', '无')}")
    print(f"   - 数据库中的进场价: None (模拟延迟)")
    
    print("\n🔍 执行停损，观察数据源对比日志:")
    print("-" * 50)
    
    # 执行停损 - 这里应该会显示我们添加的数据源对比日志
    result = stop_executor.execute_stop_loss(trigger_info)
    
    print("-" * 50)
    print(f"📊 执行结果:")
    print(f"   - 成功: {result.success}")
    print(f"   - 错误信息: {result.error_message}")
    
    if not result.success and "缺少进场价格" in result.error_message:
        print("✅ 成功验证数据源不一致问题！")
        print("   - 触发器中有正确的进场价格")
        print("   - 数据库中缺少进场价格")
        print("   - StopLossExecutor 依赖数据库查询，导致执行失败")
    else:
        print("⚠️ 未能重现预期的数据源不一致问题")
    
    print("\n" + "=" * 50)
    print("🎯 测试完成！请查看上方的数据源交叉验证日志")

if __name__ == "__main__":
    test_data_source_logging()
