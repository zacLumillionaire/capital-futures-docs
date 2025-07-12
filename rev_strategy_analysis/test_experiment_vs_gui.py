#!/usr/bin/env python3
"""
对比实验机(MDD优化器)和回测机(GUI)的策略运作差异
测试相同配置在两个系统中的结果是否一致
"""

import json
import subprocess
import sys
import os
from pathlib import Path

def test_gui_backtest(config, test_name):
    """测试GUI回测系统"""
    print(f"\n🎮 GUI回测测试: {test_name}")
    print("=" * 60)
    
    # 显示配置
    lot_settings = config["lot_settings"]
    print(f"📋 配置详情:")
    print(f"  - 时间区间: {config['range_start_time']}-{config['range_end_time']}")
    print(f"  - 每口独立停利: {config['individual_take_profit_enabled']}")
    if config['individual_take_profit_enabled']:
        print(f"  - 第1口: 停损{lot_settings['lot1']['trigger']}点, 停利{lot_settings['lot1']['take_profit']}点")
        print(f"  - 第2口: 停损{lot_settings['lot2']['trigger']}点, 停利{lot_settings['lot2']['take_profit']}点")
        print(f"  - 第3口: 停损{lot_settings['lot3']['trigger']}点, 停利{lot_settings['lot3']['take_profit']}点")
    else:
        print(f"  - 第1口: 停损{lot_settings['lot1']['trigger']}点")
        print(f"  - 第2口: 停损{lot_settings['lot2']['trigger']}点")
        print(f"  - 第3口: 停损{lot_settings['lot3']['trigger']}点")
        print(f"  - 停利模式: 区间边缘停利")
    
    # 执行GUI回测
    config_json = json.dumps(config)
    cmd = [
        sys.executable,
        "rev_multi_Profit-Funded Risk_多口.py",
        "--gui-mode",
        "--start-date", config["start_date"],
        "--end-date", config["end_date"],
        "--config", config_json
    ]
    
    print(f"\n🚀 执行GUI回测...")
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=120)
        
        if result.returncode == 0:
            print("✅ GUI回测执行成功!")
            
            # 解析结果
            stderr_lines = result.stderr.split('\n')
            
            # 查找总损益
            total_pnl = None
            for line in stderr_lines:
                if "總損益(3口):" in line:
                    try:
                        total_pnl = float(line.split("總損益(3口):")[1].strip())
                        break
                    except:
                        pass
            
            print(f"📊 GUI回测结果: 总损益 = {total_pnl}")
            return total_pnl
        else:
            print("❌ GUI回测执行失败!")
            print(f"错误: {result.stderr}")
            return None
            
    except Exception as e:
        print(f"❌ GUI回测异常: {e}")
        return None

def test_experiment_optimizer(params, test_name):
    """测试实验优化器"""
    print(f"\n🧪 实验优化器测试: {test_name}")
    print("=" * 60)
    
    # 显示配置
    print(f"📋 实验参数:")
    print(f"  - 时间区间: {params['time_interval']}")
    print(f"  - 第1口停损: {params['lot1_stop_loss']}点")
    print(f"  - 第2口停损: {params['lot2_stop_loss']}点")
    print(f"  - 第3口停损: {params['lot3_stop_loss']}点")
    if 'take_profit' in params:
        print(f"  - 统一停利: {params['take_profit']}点")
    elif params.get('take_profit_mode') == 'range_boundary':
        print(f"  - 停利模式: 区间边缘停利")
    
    # 创建临时配置文件
    temp_config = {
        'analysis_mode': 'single_test',
        'stop_loss_ranges': {
            'lot1': [params['lot1_stop_loss']],
            'lot2': [params['lot2_stop_loss']],
            'lot3': [params['lot3_stop_loss']]
        },
        'time_intervals': [(params['time_interval'].split('-')[0], params['time_interval'].split('-')[1])],
        'estimated_combinations': {'single_test': 1}
    }
    
    if 'take_profit' in params:
        temp_config['take_profit_ranges'] = {'unified': [params['take_profit']]}
    else:
        temp_config['take_profit_modes'] = ['range_boundary']
    
    # 直接调用实验优化器的核心函数
    try:
        # 导入实验优化器
        sys.path.append('./experiment_analysis')
        from enhanced_mdd_optimizer import EnhancedMDDOptimizer
        
        # 创建优化器实例
        optimizer = EnhancedMDDOptimizer('quick')  # 使用quick配置作为基础
        optimizer.config = temp_config  # 覆盖配置
        
        # 创建实验配置
        experiment_config = optimizer.create_experiment_config(params)
        
        print(f"\n🚀 执行实验优化器...")
        
        # 执行单个实验
        result = optimizer.run_single_experiment(params)
        
        if result and 'total_pnl' in result:
            print("✅ 实验优化器执行成功!")
            print(f"📊 实验结果: MDD = {result.get('mdd', 'N/A')}, P&L = {result['total_pnl']}")
            return result['total_pnl'], result.get('mdd')
        else:
            print("❌ 实验优化器执行失败!")
            return None, None
            
    except Exception as e:
        print(f"❌ 实验优化器异常: {e}")
        import traceback
        traceback.print_exc()
        return None, None

def main():
    print("🔍 实验机 vs 回测机 策略运作对比分析")
    print("=" * 80)
    
    # 测试配置1: 昨天的最佳配置 (12:00-12:02, L1SL:15 L2SL:15 L3SL:15, TP:40)
    test_configs = [
        {
            "name": "12:00-12:02_L1SL15_L2SL15_L3SL15_TP40",
            "gui_config": {
                "trade_lots": 3,
                "start_date": "2024-11-04",
                "end_date": "2025-06-27",
                "range_start_time": "12:00",
                "range_end_time": "12:02",
                "fixed_stop_mode": True,
                "individual_take_profit_enabled": True,
                "lot_settings": {
                    "lot1": {"trigger": 15, "trailing": 0, "take_profit": 40},
                    "lot2": {"trigger": 15, "trailing": 0, "protection": 0, "take_profit": 40},
                    "lot3": {"trigger": 15, "trailing": 0, "protection": 0, "take_profit": 40}
                },
                "filters": {
                    "range_filter": {"enabled": False},
                    "risk_filter": {"enabled": False},
                    "stop_loss_filter": {"enabled": True, "stop_loss_type": "range_boundary"}
                }
            },
            "experiment_params": {
                "time_interval": "12:00-12:02",
                "lot1_stop_loss": 15,
                "lot2_stop_loss": 15,
                "lot3_stop_loss": 15,
                "take_profit": 40,
                "experiment_id": "12:0012:02_L1SL15_L2SL15_L3SL15_TP40"
            }
        },
        {
            "name": "12:00-12:02_区间边缘停利",
            "gui_config": {
                "trade_lots": 3,
                "start_date": "2024-11-04",
                "end_date": "2025-06-27",
                "range_start_time": "12:00",
                "range_end_time": "12:02",
                "fixed_stop_mode": True,
                "individual_take_profit_enabled": False,
                "lot_settings": {
                    "lot1": {"trigger": 15, "trailing": 0},
                    "lot2": {"trigger": 60, "trailing": 0, "protection": 0},
                    "lot3": {"trigger": 60, "trailing": 0, "protection": 0}
                },
                "filters": {
                    "range_filter": {"enabled": False},
                    "risk_filter": {"enabled": False},
                    "stop_loss_filter": {"enabled": True, "stop_loss_type": "range_boundary"}
                }
            },
            "experiment_params": {
                "time_interval": "12:00-12:02",
                "lot1_stop_loss": 15,
                "lot2_stop_loss": 60,
                "lot3_stop_loss": 60,
                "take_profit_mode": "range_boundary",
                "experiment_id": "12:0012:02_L1SL15_L2SL60_L3SL60_RangeBoundary"
            }
        }
    ]
    
    # 运行对比测试
    results = []
    for test_config in test_configs:
        print(f"\n{'='*80}")
        print(f"🎯 测试配置: {test_config['name']}")
        print(f"{'='*80}")
        
        # 测试GUI回测
        gui_result = test_gui_backtest(test_config['gui_config'], test_config['name'])
        
        # 测试实验优化器
        exp_result, exp_mdd = test_experiment_optimizer(test_config['experiment_params'], test_config['name'])
        
        # 记录结果
        results.append({
            'name': test_config['name'],
            'gui_pnl': gui_result,
            'exp_pnl': exp_result,
            'exp_mdd': exp_mdd
        })
        
        # 对比分析
        if gui_result is not None and exp_result is not None:
            diff = abs(gui_result - exp_result)
            diff_pct = (diff / abs(exp_result)) * 100 if exp_result != 0 else 0
            
            print(f"\n📊 结果对比:")
            print(f"  GUI回测 P&L: {gui_result}")
            print(f"  实验优化器 P&L: {exp_result}")
            print(f"  差异: {diff} ({diff_pct:.2f}%)")
            
            if diff_pct < 1:
                print("✅ 结果基本一致")
            elif diff_pct < 5:
                print("⚠️ 结果有小幅差异")
            else:
                print("❌ 结果存在显著差异")
        else:
            print("❌ 无法进行对比 - 其中一个系统执行失败")
    
    # 总结
    print(f"\n{'='*80}")
    print("📋 对比测试总结")
    print(f"{'='*80}")
    
    for result in results:
        print(f"\n🎯 {result['name']}:")
        print(f"  GUI回测: {result['gui_pnl']}")
        print(f"  实验优化器: {result['exp_pnl']} (MDD: {result['exp_mdd']})")
        
        if result['gui_pnl'] is not None and result['exp_pnl'] is not None:
            diff = abs(result['gui_pnl'] - result['exp_pnl'])
            print(f"  差异: {diff}")

if __name__ == "__main__":
    main()
