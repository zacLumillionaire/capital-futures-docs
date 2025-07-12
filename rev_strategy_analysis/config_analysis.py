#!/usr/bin/env python3
"""
配置分析：检查实验机和GUI回测机的配置转换差异
"""

import json
import subprocess
import sys

def test_gui_with_debug():
    """测试GUI回测并输出详细调试信息"""
    print("🔍 GUI回测配置分析")
    print("=" * 60)
    
    config = {
        "trade_lots": 3,
        "start_date": "2024-11-04",
        "end_date": "2025-06-27",
        "range_start_time": "12:00",
        "range_end_time": "12:02",
        "fixed_stop_mode": True,
        "individual_take_profit_enabled": True,
        "lot_settings": {
            "lot1": {"trigger": 15, "trailing": 0, "take_profit": 40},
            "lot2": {"trigger": 15, "trailing": 0, "take_profit": 40},
            "lot3": {"trigger": 15, "trailing": 0, "take_profit": 40}
        },
        "filters": {
            "range_filter": {"enabled": False},
            "risk_filter": {"enabled": False},
            "stop_loss_filter": {"enabled": False}
        }
    }
    
    print(f"📋 GUI配置:")
    print(f"  - 时间区间: {config['range_start_time']}-{config['range_end_time']}")
    print(f"  - 固定停损模式: {config['fixed_stop_mode']}")
    print(f"  - 每口独立停利: {config['individual_take_profit_enabled']}")
    print(f"  - 第1口: 停损{config['lot_settings']['lot1']['trigger']}点, 停利{config['lot_settings']['lot1']['take_profit']}点")
    print(f"  - 第2口: 停损{config['lot_settings']['lot2']['trigger']}点, 停利{config['lot_settings']['lot2']['take_profit']}点")
    print(f"  - 第3口: 停损{config['lot_settings']['lot3']['trigger']}点, 停利{config['lot_settings']['lot3']['take_profit']}点")
    
    config_json = json.dumps(config)
    cmd = [
        sys.executable, 
        "rev_multi_Profit-Funded Risk_多口.py",
        "--gui-mode",
        "--start-date", "2024-11-04",
        "--end-date", "2025-06-27",
        "--config", config_json,
        "--debug"  # 添加调试模式
    ]
    
    print(f"\n🚀 执行GUI回测...")
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=120)
        
        print(f"返回码: {result.returncode}")
        
        if result.returncode == 0:
            print("✅ GUI回测执行成功!")
            
            # 分析输出
            stderr_lines = result.stderr.split('\n')
            stdout_lines = result.stdout.split('\n')
            
            # 查找配置相关信息
            print(f"\n📊 配置解析信息:")
            for line in stderr_lines:
                if any(keyword in line for keyword in ["LotRule", "固定停利", "停損", "停利", "配置"]):
                    print(f"  {line}")
            
            # 查找结果
            total_pnl = None
            mdd = None
            trade_count = 0
            
            for line in stderr_lines:
                if "總損益(3口):" in line:
                    try:
                        total_pnl = float(line.split("總損益(3口):")[1].strip())
                    except:
                        pass
                elif "最大回撤:" in line:
                    try:
                        mdd = float(line.split("最大回撤:")[1].strip())
                    except:
                        pass
                elif "交易次數:" in line:
                    try:
                        trade_count = int(line.split("交易次數:")[1].strip())
                    except:
                        pass
            
            print(f"\n📈 GUI回测结果:")
            print(f"  - 总损益: {total_pnl}")
            print(f"  - 最大回撤: {mdd}")
            print(f"  - 交易次数: {trade_count}")
            
            return total_pnl, mdd, trade_count
        else:
            print("❌ GUI回测执行失败!")
            print(f"标准错误: {result.stderr}")
            print(f"标准输出: {result.stdout}")
            return None, None, None
            
    except Exception as e:
        print(f"❌ GUI回测异常: {e}")
        return None, None, None

def analyze_experiment_config():
    """分析实验优化器的配置转换"""
    print("\n🧪 实验优化器配置分析")
    print("=" * 60)
    
    # 模拟实验优化器的配置转换过程
    params = {
        "time_interval": "12:00-12:02",
        "lot1_stop_loss": 15,
        "lot2_stop_loss": 15,
        "lot3_stop_loss": 15,
        "take_profit": 40,
        "experiment_id": "12:0012:02_L1SL15_L2SL15_L3SL15_TP40"
    }
    
    print(f"📋 实验参数:")
    print(f"  - 时间区间: {params['time_interval']}")
    print(f"  - 第1口停损: {params['lot1_stop_loss']}点")
    print(f"  - 第2口停损: {params['lot2_stop_loss']}点")
    print(f"  - 第3口停损: {params['lot3_stop_loss']}点")
    print(f"  - 统一停利: {params['take_profit']}点")
    
    # 按照实验优化器的逻辑转换配置
    experiment_config = {
        'start_date': "2024-11-04",
        'end_date': "2025-06-27",
        'range_start_time': params['time_interval'].split('-')[0],
        'range_end_time': params['time_interval'].split('-')[1],
        'trade_lots': 3,
        'fixed_stop_mode': True,
        'individual_take_profit_enabled': True,
        'lot_settings': {
            'lot1': {
                'trigger': params['lot1_stop_loss'],
                'trailing': 0,
                'take_profit': params['take_profit']
            },
            'lot2': {
                'trigger': params['lot2_stop_loss'],
                'trailing': 0,
                'take_profit': params['take_profit']
            },
            'lot3': {
                'trigger': params['lot3_stop_loss'],
                'trailing': 0,
                'take_profit': params['take_profit']
            }
        },
        'filters': {
            'range_filter': {'enabled': False},
            'risk_filter': {'enabled': False},
            'stop_loss_filter': {'enabled': False}
        }
    }
    
    print(f"\n🔄 实验优化器转换后的配置:")
    print(f"  - 时间区间: {experiment_config['range_start_time']}-{experiment_config['range_end_time']}")
    print(f"  - 固定停损模式: {experiment_config['fixed_stop_mode']}")
    print(f"  - 每口独立停利: {experiment_config['individual_take_profit_enabled']}")
    print(f"  - 第1口: 停损{experiment_config['lot_settings']['lot1']['trigger']}点, 停利{experiment_config['lot_settings']['lot1']['take_profit']}点")
    print(f"  - 第2口: 停损{experiment_config['lot_settings']['lot2']['trigger']}点, 停利{experiment_config['lot_settings']['lot2']['take_profit']}点")
    print(f"  - 第3口: 停损{experiment_config['lot_settings']['lot3']['trigger']}点, 停利{experiment_config['lot_settings']['lot3']['take_profit']}点")
    
    # 测试这个配置
    config_json = json.dumps(experiment_config)
    cmd = [
        sys.executable, 
        "rev_multi_Profit-Funded Risk_多口.py",
        "--gui-mode",
        "--start-date", "2024-11-04",
        "--end-date", "2025-06-27",
        "--config", config_json
    ]
    
    print(f"\n🚀 执行实验配置测试...")
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=120)
        
        if result.returncode == 0:
            print("✅ 实验配置测试成功!")
            
            # 解析结果
            stderr_lines = result.stderr.split('\n')
            
            total_pnl = None
            mdd = None
            trade_count = 0
            
            for line in stderr_lines:
                if "總損益(3口):" in line:
                    try:
                        total_pnl = float(line.split("總損益(3口):")[1].strip())
                    except:
                        pass
                elif "最大回撤:" in line:
                    try:
                        mdd = float(line.split("最大回撤:")[1].strip())
                    except:
                        pass
                elif "交易次數:" in line:
                    try:
                        trade_count = int(line.split("交易次數:")[1].strip())
                    except:
                        pass
            
            print(f"📈 实验配置结果:")
            print(f"  - 总损益: {total_pnl}")
            print(f"  - 最大回撤: {mdd}")
            print(f"  - 交易次数: {trade_count}")
            
            return total_pnl, mdd, trade_count
        else:
            print("❌ 实验配置测试失败!")
            print(f"错误: {result.stderr}")
            return None, None, None
            
    except Exception as e:
        print(f"❌ 实验配置测试异常: {e}")
        return None, None, None

def run_actual_experiment():
    """运行实际的实验优化器"""
    print("\n🔬 运行实际实验优化器")
    print("=" * 60)
    
    cmd = [
        sys.executable,
        "experiment_analysis/enhanced_mdd_optimizer.py",
        "--config", "time_interval_analysis",
        "--sample-size", "100"
    ]
    
    print(f"🚀 执行实验优化器...")
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=300)
        
        if result.returncode == 0:
            print("✅ 实验优化器执行成功!")
            
            # 查找12:00-12:02时段的结果
            stdout_lines = result.stdout.split('\n')
            
            found_results = []
            for line in stdout_lines:
                if "12:0012:02" in line and ("L1SL15" in line or "L1SL:15" in line):
                    found_results.append(line)
            
            print(f"📊 找到的12:00-12:02相关结果:")
            for result_line in found_results:
                print(f"  {result_line}")
            
            return found_results
        else:
            print("❌ 实验优化器执行失败!")
            print(f"错误: {result.stderr}")
            return None
            
    except Exception as e:
        print(f"❌ 实验优化器异常: {e}")
        return None

def main():
    print("🔍 配置差异分析")
    print("=" * 80)
    print("目标: 找出实验机和GUI回测机的配置转换差异")
    print("=" * 80)
    
    # 1. 测试GUI配置
    gui_pnl, gui_mdd, gui_trades = test_gui_with_debug()
    
    # 2. 测试实验优化器配置转换
    exp_pnl, exp_mdd, exp_trades = analyze_experiment_config()
    
    # 3. 运行实际实验优化器
    exp_results = run_actual_experiment()
    
    # 4. 对比分析
    print(f"\n{'='*80}")
    print("📊 配置差异分析结果")
    print(f"{'='*80}")
    
    print(f"🎯 目标配置: 12:00-12:02, L1SL:15 L2SL:15 L3SL:15, TP:40")
    print(f"📅 昨天实验结果: P&L: 2544.00, MDD: -228.00")
    print(f"🎮 GUI直接测试: P&L: {gui_pnl}, MDD: {gui_mdd}, 交易数: {gui_trades}")
    print(f"🔄 实验配置测试: P&L: {exp_pnl}, MDD: {exp_mdd}, 交易数: {exp_trades}")
    
    if exp_results:
        print(f"🧪 实验优化器结果:")
        for result in exp_results:
            print(f"  {result}")
    
    # 分析结论
    print(f"\n💡 分析结论:")
    
    if gui_pnl == exp_pnl:
        print("✅ GUI配置和实验配置转换一致")
    else:
        print("❌ GUI配置和实验配置转换不一致")
        if gui_pnl and exp_pnl:
            diff = abs(gui_pnl - exp_pnl)
            print(f"   差异: {diff}点")
    
    if gui_pnl and gui_pnl != 2544.0:
        diff = abs(gui_pnl - 2544.0)
        print(f"⚠️ 当前结果与昨天不同，差异: {diff}点")
        print("   可能原因:")
        print("   1. 策略逻辑有修改")
        print("   2. 数据有更新")
        print("   3. 配置参数理解有误")
    
    if gui_trades and gui_trades != 0:
        print(f"📈 交易数量: {gui_trades}笔")

if __name__ == "__main__":
    main()
