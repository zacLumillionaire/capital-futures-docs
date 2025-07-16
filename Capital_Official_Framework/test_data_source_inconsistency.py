#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
数据源不一致问题验证测试
专门测试 OptimizedRiskManager 内存状态与数据库状态的不同步问题
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
from simplified_order_tracker import GlobalExitManager
from async_db_updater import AsyncDatabaseUpdater

class DataSourceInconsistencyTest:
    """数据源不一致测试类"""
    
    def __init__(self):
        self.db_name = "test_data_inconsistency.db"
        self.setup_test_environment()
    
    def setup_test_environment(self):
        """设置测试环境"""
        print("🔧 设置测试环境...")
        
        # 清理旧数据库
        if os.path.exists(self.db_name):
            os.remove(self.db_name)
        
        # 初始化数据库管理器
        self.db_manager = MultiGroupDatabaseManager(self.db_name)
        
        # 初始化异步更新器
        self.async_updater = AsyncDatabaseUpdater(self.db_manager)
        
        # 初始化全局退出管理器 (简化版本，只用于锁管理)
        self.global_exit_manager = GlobalExitManager()
        
        # 初始化停损执行器
        self.stop_executor = StopLossExecutor(
            db_manager=self.db_manager,
            global_exit_manager=self.global_exit_manager,
            async_updater=self.async_updater,
            console_enabled=True
        )
        
        # 初始化优化风险管理器
        self.risk_manager = OptimizedRiskManager(
            db_manager=self.db_manager,
            stop_loss_executor=self.stop_executor,
            global_exit_manager=self.global_exit_manager,
            console_enabled=True
        )
        
        print("✅ 测试环境设置完成")
    
    def create_test_position(self):
        """创建测试部位"""
        print("\n📝 创建测试部位...")
        
        # 创建策略组
        group_config = {
            'group_id': 1,
            'direction': 'SHORT',
            'range_high': 21500,
            'range_low': 21400,
            'total_lots': 1,
            'date': datetime.now().strftime('%Y-%m-%d')
        }
        
        group_db_id = self.db_manager.create_strategy_group(group_config)
        print(f"✅ 策略组创建完成，DB ID: {group_db_id}")
        
        # 创建部位记录
        position_data = {
            'group_id': 1,
            'direction': 'SHORT',
            'entry_price': None,  # 🔧 关键：故意设置为 None 模拟异步更新延迟
            'quantity': 1,
            'status': 'ACTIVE',
            'entry_time': datetime.now().strftime('%H:%M:%S'),
            'order_id': 'TEST_ORDER_001'
        }
        
        position_id = self.db_manager.create_position_record(position_data)
        print(f"✅ 部位记录创建完成，Position ID: {position_id}")
        
        # 🔧 关键：立即更新 OptimizedRiskManager 的内存状态
        # 模拟成交回报更新内存，但数据库更新被延迟
        entry_price = 21441.0
        self.risk_manager.position_cache[str(position_id)] = {
            'id': position_id,
            'group_id': 1,
            'direction': 'SHORT',
            'entry_price': entry_price,  # 内存中有正确的进场价
            'quantity': 1,
            'status': 'ACTIVE'
        }
        
        # 预计算停损价格
        self.risk_manager.stop_loss_cache[str(position_id)] = 21500  # SHORT 停损在高价
        self.risk_manager.activation_cache[str(position_id)] = 21426  # 15点启动移动停利
        self.risk_manager.trailing_cache[str(position_id)] = {
            'activated': False,
            'peak_price': entry_price,
            'direction': 'SHORT'
        }
        
        print(f"✅ OptimizedRiskManager 内存状态已更新:")
        print(f"   - 内存中进场价: {entry_price}")
        print(f"   - 数据库中进场价: None (模拟异步延迟)")
        
        return position_id
    
    def simulate_trailing_stop_trigger(self, position_id):
        """模拟移动停利触发"""
        print(f"\n🎯 模拟移动停利触发 (部位 {position_id})...")
        
        # 首先激活移动停利
        print("📈 价格下跌，激活移动停利...")
        self.risk_manager.trailing_cache[str(position_id)]['activated'] = True
        self.risk_manager.trailing_cache[str(position_id)]['peak_price'] = 21426  # 新的峰值
        
        # 模拟价格继续下跌，触发移动停利
        trigger_price = 21435  # 触发价格
        print(f"💥 价格回升至 {trigger_price}，触发移动停利...")
        
        # 调用 OptimizedRiskManager 的价格更新
        result = self.risk_manager.update_price(trigger_price)
        
        print(f"📊 价格更新结果: {result}")
        
        return result
    
    def verify_data_inconsistency(self, position_id):
        """验证数据源不一致问题"""
        print(f"\n🔍 验证数据源不一致问题 (部位 {position_id})...")
        
        # 检查内存状态
        memory_data = self.risk_manager.position_cache.get(str(position_id))
        memory_entry_price = memory_data.get('entry_price') if memory_data else None
        
        # 检查数据库状态
        with self.db_manager.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('SELECT entry_price FROM position_records WHERE id = ?', (position_id,))
            row = cursor.fetchone()
            db_entry_price = row[0] if row else None
        
        print(f"📊 数据源对比:")
        print(f"   - 内存中进场价: {memory_entry_price}")
        print(f"   - 数据库中进场价: {db_entry_price}")
        
        if memory_entry_price is not None and db_entry_price is None:
            print("❌ 确认数据源不一致问题存在！")
            print("   - OptimizedRiskManager 内存状态正确")
            print("   - 数据库状态滞后 (entry_price = None)")
            return True
        else:
            print("✅ 数据源一致")
            return False
    
    def run_test(self):
        """运行完整测试"""
        print("🚀 开始数据源不一致问题验证测试")
        print("=" * 60)
        
        try:
            # 1. 创建测试部位
            position_id = self.create_test_position()
            
            # 2. 验证初始数据不一致
            inconsistency_exists = self.verify_data_inconsistency(position_id)
            
            if not inconsistency_exists:
                print("⚠️ 未检测到数据不一致，测试环境可能有问题")
                return
            
            # 3. 模拟移动停利触发
            result = self.simulate_trailing_stop_trigger(position_id)
            
            # 4. 等待一下让日志输出完整
            time.sleep(2)
            
            print("\n" + "=" * 60)
            print("🎯 测试完成！请查看上方日志中的数据源交叉验证信息")
            print("   特别关注 [TRIGGER_INFO] 和 [DATABASE_INFO] 的对比")
            
        except Exception as e:
            print(f"❌ 测试执行失败: {e}")
            import traceback
            traceback.print_exc()
        
        finally:
            # 清理
            if hasattr(self, 'async_updater'):
                self.async_updater.stop()

if __name__ == "__main__":
    test = DataSourceInconsistencyTest()
    test.run_test()
