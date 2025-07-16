#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
最终修复验证测试 - 修复版本
验证所有问题都已解决
"""

import os
import sys
import time
from datetime import datetime

# 添加项目路径
sys.path.insert(0, os.path.dirname(__file__))

from multi_group_database import MultiGroupDatabaseManager
from optimized_risk_manager import OptimizedRiskManager
from stop_loss_executor import StopLossExecutor, standardize_exit_reason
from stop_loss_monitor import StopLossTrigger
from async_db_updater import AsyncDatabaseUpdater

def final_fixed_verification():
    """最终修复验证测试"""
    print("🎯 最终修复验证测试 - 修复版本")
    print("=" * 80)
    print("目标：验证内存保护机制和数据库字段问题的修复")
    print("=" * 80)
    
    # 设置测试数据库
    db_name = "final_fixed_verification.db"
    if os.path.exists(db_name):
        os.remove(db_name)
    
    print("🔧 初始化测试组件...")
    
    # 初始化组件
    db_manager = MultiGroupDatabaseManager(db_name)

    # 初始化异步更新器
    async_updater = AsyncDatabaseUpdater(db_manager, console_enabled=True)
    async_updater.start()

    stop_executor = StopLossExecutor(
        db_manager=db_manager,
        console_enabled=True
    )

    # 设置异步更新器
    stop_executor.set_async_updater(async_updater, enabled=True)

    risk_manager = OptimizedRiskManager(
        db_manager=db_manager,
        console_enabled=True
    )

    # 设置异步更新器到风险管理器
    risk_manager.set_async_updater(async_updater)

    risk_manager.set_stop_loss_executor(stop_executor)

    # 注册平仓成功回呼
    def on_exit_success(position_id: int, execution_result, trigger_info):
        """平仓成功回呼函式"""
        try:
            print(f"[TEST] 📞 平仓成功回呼触发: 部位{position_id}")

            # 标准化 exit_reason
            raw_exit_reason = getattr(trigger_info, 'trigger_reason', '手动出场')
            standardized_reason = standardize_exit_reason(raw_exit_reason)

            async_updater.schedule_position_exit_update(
                position_id=position_id,
                exit_price=execution_result.execution_price,
                exit_time=execution_result.execution_time,
                exit_reason=standardized_reason,
                order_id=execution_result.order_id,
                pnl=execution_result.pnl
            )

            print(f"[TEST] 🚀 平仓状态已排程异步更新: 部位{position_id}")

        except Exception as e:
            print(f"[TEST] ❌ 平仓回呼处理失败: {e}")

    # 注册平仓成功回呼
    stop_executor.add_exit_success_callback(on_exit_success)
    
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
        order_id='FINAL_FIXED_TEST_001'
    )
    
    print(f"✅ 测试环境创建完成")
    print(f"   - 策略组 DB ID: {group_db_id}")
    print(f"   - 部位 ID: {position_id}")
    
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
    
    # 验证内存状态
    cached_position = risk_manager.position_cache.get(str(position_id))
    memory_entry_price = cached_position.get('entry_price') if cached_position else None
    print(f"   - 内存缓存验证: {memory_entry_price}")

    # 调试信息：显示缓存中的所有键
    if not cached_position:
        print(f"   - 调试：缓存中的键: {list(risk_manager.position_cache.keys())}")
        print(f"   - 调试：查找的键: {str(position_id)} (类型: {type(str(position_id))})")
    
    # 步骤2：测试修复后的内存保护机制
    print(f"\n🛡️ 步骤2：测试修复后的内存保护机制")
    print("-" * 60)
    
    print("🔄 强制触发数据库同步（测试修复后的内存保护）...")
    risk_manager._sync_with_database()
    
    # 检查内存保护是否有效
    cached_position_after = risk_manager.position_cache.get(str(position_id))
    memory_entry_price_after = cached_position_after.get('entry_price') if cached_position_after else None
    
    if memory_entry_price_after == entry_price:
        print("✅ 内存保护机制修复成功")
        print(f"   - 同步后内存进场价: {memory_entry_price_after}")
        memory_protection_ok = True
    else:
        print("❌ 内存保护机制仍有问题")
        print(f"   - 同步后内存进场价: {memory_entry_price_after}")
        memory_protection_ok = False
    
    # 步骤3：测试修复后的数据库更新
    print(f"\n🎯 步骤3：测试修复后的数据库更新")
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
    
    print(f"📋 修复后的触发器:")
    print(f"   - 触发器中进场价: {trigger_info.entry_price}")
    print(f"   - 触发器中平仓价: {trigger_info.current_price}")
    print(f"   - 预期损益: {trigger_info.entry_price - trigger_info.current_price} 点")
    
    print(f"\n🚀 执行停损（测试数据库字段修复）:")
    print("-" * 40)
    
    # 执行停损
    result = stop_executor.execute_stop_loss(trigger_info)
    
    print(f"\n📊 执行结果:")
    print(f"   - 成功: {result.success}")
    print(f"   - 错误信息: {result.error_message}")
    print(f"   - 订单ID: {result.order_id}")
    print(f"   - 执行价格: {result.execution_price}")
    print(f"   - 损益: {result.pnl} 点")
    
    # 检查是否还有数据库错误
    database_error_free = result.error_message is None or "no such column" not in str(result.error_message)

    # 等待异步更新完成
    print(f"\n⏰ 等待异步更新完成...")
    time.sleep(2)  # 等待异步更新完成

    # 步骤4：验证数据库最终状态
    print(f"\n📊 步骤4：验证数据库最终状态")
    print("-" * 60)
    
    with db_manager.get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute('SELECT entry_price, status, exit_price, exit_reason FROM position_records WHERE id = ?', (position_id,))
        row = cursor.fetchone()
        if row:
            final_db_entry_price, final_db_status, final_db_exit_price, final_db_exit_reason = row
            print(f"   - 数据库最终进场价: {final_db_entry_price}")
            print(f"   - 数据库最终状态: {final_db_status}")
            print(f"   - 数据库出场价: {final_db_exit_price}")
            print(f"   - 数据库出场原因: {final_db_exit_reason}")
        else:
            print("   - 数据库记录未找到")
    
    # 最终评估
    print(f"\n" + "=" * 80)
    print(f"🏁 最终修复评估结果")
    print(f"=" * 80)
    
    success_criteria = [
        ("内存保护机制", memory_protection_ok),
        ("停损执行成功", result.success),
        ("无数据库字段错误", database_error_free),
        ("无进场价格错误", result.error_message is None or "缺少进场价格" not in result.error_message)
    ]
    
    all_success = all(criteria[1] for criteria in success_criteria)
    
    for name, status in success_criteria:
        status_icon = "✅" if status else "❌"
        print(f"{status_icon} {name}: {'通过' if status else '失败'}")
    
    if all_success:
        print(f"\n🎉 最终修复验证完全成功！")
        print(f"✅ 所有问题都已解决:")
        print(f"   1. 内存保护机制正常工作")
        print(f"   2. 数据库字段错误已修复")
        print(f"   3. 触发器数据流正常")
        print(f"   4. 停损执行完全成功")
        print(f"\n🔧 修复总结:")
        print(f"   - 修复1: position_id 类型一致性问题")
        print(f"   - 修复2: 移除不存在的 exit_trigger_type 字段")
        print(f"   - 核心: 数据源不一致问题彻底解决")
        
        if result.pnl:
            print(f"\n💰 交易结果: {result.pnl:+.1f} 点")
    else:
        print(f"\n❌ 仍有问题需要解决")
        for name, status in success_criteria:
            if not status:
                print(f"   - {name}")
    
    print(f"\n🎯 最终修复验证测试完成！")
    print(f"=" * 80)

    # 清理异步更新器
    async_updater.stop()

    return all_success

if __name__ == "__main__":
    success = final_fixed_verification()
    exit(0 if success else 1)
