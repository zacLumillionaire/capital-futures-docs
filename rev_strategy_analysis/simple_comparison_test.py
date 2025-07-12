#!/usr/bin/env python3
"""
简单对比测试：直接运行GUI回测和实验优化器，对比相同配置的结果
"""

import json
import subprocess
import sys
import os

def test_gui_with_specific_config():
    """测试GUI回测 - 12:00-12:02, L1SL:15 L2SL:15 L3SL:15, TP:40"""
    print("🎮 GUI回测测试: 12:00-12:02_L1SL15_L2SL15_L3SL15_TP40")
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
    
    print(f"📋 配置: 12:00-12:02, 每口停损15点, 每口停利40点")
    
    config_json = json.dumps(config)
    cmd = [
        sys.executable, 
        "rev_multi_Profit-Funded Risk_多口.py",
        "--gui-mode",
        "--start-date", "2024-11-04",
        "--end-date", "2025-06-27",
        "--config", config_json
    ]
    
    print(f"🚀 执行GUI回测...")
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=120)
        
        if result.returncode == 0:
            print("✅ GUI回测执行成功!")
            
            # 解析结果
            stderr_lines = result.stderr.split('\n')
            
            # 查找总损益和MDD
            total_pnl = None
            mdd = None
            
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
            
            print(f"📊 GUI结果: P&L = {total_pnl}, MDD = {mdd}")
            return total_pnl, mdd
        else:
            print("❌ GUI回测执行失败!")
            print(f"错误: {result.stderr}")
            return None, None
            
    except Exception as e:
        print(f"❌ GUI回测异常: {e}")
        return None, None

def test_experiment_optimizer():
    """测试实验优化器 - 相同配置"""
    print("\n🧪 实验优化器测试: 12:00-12:02_L1SL15_L2SL15_L3SL15_TP40")
    print("=" * 60)
    
    print(f"📋 配置: 12:00-12:02, 每口停损15点, 统一停利40点")
    
    # 运行实验优化器的单个实验
    cmd = [
        sys.executable,
        "experiment_analysis/enhanced_mdd_optimizer.py",
        "--config", "quick",
        "--sample-size", "1"
    ]
    
    # 创建临时配置来测试特定参数
    print(f"🚀 执行实验优化器...")
    
    # 直接运行一个包含我们目标配置的小样本测试
    cmd_sample = [
        sys.executable,
        "experiment_analysis/enhanced_mdd_optimizer.py", 
        "--config", "time_interval_analysis",
        "--sample-size", "20"
    ]
    
    try:
        result = subprocess.run(cmd_sample, capture_output=True, text=True, timeout=180)
        
        if result.returncode == 0:
            print("✅ 实验优化器执行成功!")
            
            # 解析结果 - 查找12:00-12:02时段的L1SL:15 L2SL:15 L3SL:15 TP:40配置
            stdout_lines = result.stdout.split('\n')
            
            target_found = False
            exp_pnl = None
            exp_mdd = None
            
            for line in stdout_lines:
                # 查找包含我们目标配置的行
                if "12:0012:02_L1SL15_L2SL15_L3SL15_TP40" in line:
                    target_found = True
                    # 解析MDD和P&L
                    if "MDD:" in line and "P&L:" in line:
                        try:
                            parts = line.split("MDD:")[1].split("P&L:")
                            exp_mdd = float(parts[0].strip().replace(",", ""))
                            exp_pnl = float(parts[1].strip().split()[0].replace(",", ""))
                        except:
                            pass
                    break
            
            if target_found:
                print(f"📊 实验结果: P&L = {exp_pnl}, MDD = {exp_mdd}")
                return exp_pnl, exp_mdd
            else:
                print("⚠️ 目标配置未在样本中找到，尝试手动创建实验...")
                return None, None
        else:
            print("❌ 实验优化器执行失败!")
            print(f"错误: {result.stderr}")
            return None, None
            
    except Exception as e:
        print(f"❌ 实验优化器异常: {e}")
        return None, None

def run_manual_experiment():
    """手动运行单个实验配置"""
    print("\n🔧 手动实验测试")
    print("=" * 60)
    
    # 直接调用策略引擎进行单个配置测试
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
    
    print(f"📋 手动配置: 12:00-12:02, L1SL:15 L2SL:15 L3SL:15, TP:40")
    
    config_json = json.dumps(config)
    cmd = [
        sys.executable,
        "rev_multi_Profit-Funded Risk_多口.py",
        "--gui-mode",
        "--start-date", "2024-11-04",
        "--end-date", "2025-06-27", 
        "--config", config_json
    ]
    
    print(f"🚀 执行手动实验...")
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=120)
        
        if result.returncode == 0:
            print("✅ 手动实验执行成功!")
            
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
            
            print(f"📊 手动实验结果:")
            print(f"  - 总损益: {total_pnl}")
            print(f"  - 最大回撤: {mdd}")
            print(f"  - 交易次数: {trade_count}")
            
            return total_pnl, mdd, trade_count
        else:
            print("❌ 手动实验执行失败!")
            print(f"错误输出: {result.stderr}")
            return None, None, None
            
    except Exception as e:
        print(f"❌ 手动实验异常: {e}")
        return None, None, None

def main():
    print("🔍 策略运作差异分析")
    print("=" * 80)
    print("目标配置: 12:00-12:02, L1SL:15 L2SL:15 L3SL:15, TP:40")
    print("对比昨天实验结果: MDD: -228.00 | P&L: 2544.00")
    print("=" * 80)
    
    # 运行手动实验
    manual_pnl, manual_mdd, manual_trades = run_manual_experiment()
    
    # 运行实验优化器测试
    exp_pnl, exp_mdd = test_experiment_optimizer()
    
    # 结果对比
    print(f"\n{'='*80}")
    print("📊 结果对比分析")
    print(f"{'='*80}")
    
    print(f"🎯 目标配置: 12:00-12:02, L1SL:15 L2SL:15 L3SL:15, TP:40")
    print(f"📅 昨天实验结果: MDD: -228.00, P&L: 2544.00")
    print(f"🔧 今天手动测试: MDD: {manual_mdd}, P&L: {manual_pnl}, 交易数: {manual_trades}")
    print(f"🧪 今天实验优化器: MDD: {exp_mdd}, P&L: {exp_pnl}")
    
    if manual_pnl is not None:
        if manual_pnl == 2544.0:
            print("✅ 手动测试结果与昨天一致")
        else:
            diff = abs(manual_pnl - 2544.0) if manual_pnl else 0
            print(f"⚠️ 手动测试结果与昨天不同，差异: {diff}")
    
    if exp_pnl is not None and manual_pnl is not None:
        diff = abs(exp_pnl - manual_pnl)
        print(f"🔄 实验优化器与手动测试差异: {diff}")
    
    print(f"\n💡 分析结论:")
    if manual_pnl == 2544.0:
        print("  - 策略引擎本身运作正常，结果可重现")
        print("  - 如果实验优化器结果不同，可能是配置转换问题")
    else:
        print("  - 策略引擎结果与昨天不同，需要检查:")
        print("    1. 数据是否有变化")
        print("    2. 策略逻辑是否有修改")
        print("    3. 配置参数是否正确")

if __name__ == "__main__":
    main()
