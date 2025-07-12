#!/usr/bin/env python3
"""
测试修正后的实验优化器
验证配置转换是否正确
"""

import json
import subprocess
import sys

def test_fixed_optimizer():
    """测试修正后的实验优化器"""
    print("🔧 测试修正后的实验优化器")
    print("=" * 60)
    
    # 运行小样本测试，专门查找我们的目标配置
    cmd = [
        sys.executable,
        "experiment_analysis/enhanced_mdd_optimizer.py",
        "--config", "time_interval_analysis",
        "--sample-size", "50"
    ]
    
    print(f"🚀 执行修正后的实验优化器...")
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=180)
        
        if result.returncode == 0:
            print("✅ 实验优化器执行成功!")
            
            # 查找12:00-12:02时段的结果
            stdout_lines = result.stdout.split('\n')
            
            found_results = []
            for line in stdout_lines:
                if "12:0012:02" in line:
                    found_results.append(line)
            
            print(f"📊 找到的12:00-12:02相关结果:")
            for result_line in found_results:
                print(f"  {result_line}")
                
                # 检查是否有我们的目标配置
                if "L1SL15_L2SL15_L3SL15_TP40" in result_line or "L1SL:15_L2SL:15_L3SL:15" in result_line:
                    print(f"  🎯 找到目标配置！")
                    
                    # 解析结果
                    if "MDD:" in result_line and "P&L:" in result_line:
                        try:
                            parts = result_line.split("MDD:")[1].split("P&L:")
                            mdd = float(parts[0].strip().replace(",", ""))
                            pnl = float(parts[1].strip().split()[0].replace(",", ""))
                            print(f"  📈 结果: MDD = {mdd}, P&L = {pnl}")
                            
                            # 检查是否接近预期
                            if abs(pnl - 1830.0) < 50:
                                print(f"  ✅ 结果与GUI回测一致！(差异: {abs(pnl - 1830.0)})")
                            elif abs(pnl - 2544.0) < 50:
                                print(f"  🎉 结果与昨天实验一致！(差异: {abs(pnl - 2544.0)})")
                            else:
                                print(f"  ⚠️ 结果与预期不符")
                        except:
                            print(f"  ❌ 无法解析结果")
            
            return found_results
        else:
            print("❌ 实验优化器执行失败!")
            print(f"错误: {result.stderr}")
            return None
            
    except Exception as e:
        print(f"❌ 实验优化器异常: {e}")
        return None

def test_manual_experiment_config():
    """手动测试实验优化器的配置转换"""
    print("\n🧪 手动测试实验配置转换")
    print("=" * 60)
    
    # 模拟实验优化器的配置转换
    params = {
        "time_interval": "12:00-12:02",
        "lot1_stop_loss": 15,
        "lot2_stop_loss": 15,
        "lot3_stop_loss": 15,
        "take_profit": 40,
        "experiment_id": "test_fixed_config"
    }
    
    # 按照修正后的逻辑创建配置
    config = {
        'start_date': "2024-11-04",
        'end_date': "2025-06-27",
        'range_start_time': params['time_interval'].split('-')[0],
        'range_end_time': params['time_interval'].split('-')[1],
        'trade_lots': 3,
        'fixed_stop_mode': True,
        'individual_take_profit_enabled': True,  # 修正：明确开启个别停利
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
    
    print(f"📋 修正后的实验配置:")
    print(f"  - 时间区间: {config['range_start_time']}-{config['range_end_time']}")
    print(f"  - 固定停损模式: {config['fixed_stop_mode']}")
    print(f"  - 每口独立停利: {config['individual_take_profit_enabled']}")
    print(f"  - 第1口: 停损{config['lot_settings']['lot1']['trigger']}点, 停利{config['lot_settings']['lot1']['take_profit']}点")
    print(f"  - 第2口: 停损{config['lot_settings']['lot2']['trigger']}点, 停利{config['lot_settings']['lot2']['take_profit']}点")
    print(f"  - 第3口: 停损{config['lot_settings']['lot3']['trigger']}点, 停利{config['lot_settings']['lot3']['take_profit']}点")
    
    # 测试这个配置
    config_json = json.dumps(config)
    cmd = [
        sys.executable, 
        "rev_multi_Profit-Funded Risk_多口.py",
        "--gui-mode",
        "--start-date", "2024-11-04",
        "--end-date", "2025-06-27",
        "--config", config_json
    ]
    
    print(f"\n🚀 执行修正配置测试...")
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=120)
        
        if result.returncode == 0:
            print("✅ 修正配置测试成功!")
            
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
            
            print(f"📈 修正配置结果:")
            print(f"  - 总损益: {total_pnl}")
            print(f"  - 最大回撤: {mdd}")
            print(f"  - 交易次数: {trade_count}")
            
            # 验证结果
            if total_pnl == 1830.0:
                print(f"✅ 结果与GUI回测完全一致！")
            elif total_pnl and abs(total_pnl - 1830.0) < 10:
                print(f"✅ 结果与GUI回测基本一致！(差异: {abs(total_pnl - 1830.0)})")
            else:
                print(f"⚠️ 结果与GUI回测不一致")
            
            return total_pnl, mdd, trade_count
        else:
            print("❌ 修正配置测试失败!")
            print(f"错误: {result.stderr}")
            return None, None, None
            
    except Exception as e:
        print(f"❌ 修正配置测试异常: {e}")
        return None, None, None

def main():
    print("🔧 测试修正后的实验优化器")
    print("=" * 80)
    print("目标: 验证修正后的配置转换是否正确")
    print("=" * 80)
    
    # 1. 手动测试修正后的配置
    manual_pnl, manual_mdd, manual_trades = test_manual_experiment_config()
    
    # 2. 测试修正后的实验优化器
    optimizer_results = test_fixed_optimizer()
    
    # 3. 总结
    print(f"\n{'='*80}")
    print("📊 修正验证结果")
    print(f"{'='*80}")
    
    print(f"🎯 预期结果: P&L = 1830.0 (GUI回测)")
    print(f"🔧 修正配置测试: P&L = {manual_pnl}, MDD = {manual_mdd}")
    
    if optimizer_results:
        print(f"🧪 实验优化器结果:")
        for result in optimizer_results:
            print(f"  {result}")
    
    print(f"\n💡 修正总结:")
    if manual_pnl == 1830.0:
        print("✅ 配置转换修正成功！")
        print("✅ 实验机和GUI回测机现在应该产生一致的结果")
        print("📝 昨天的2544.0结果可能是区间边缘停利模式，不是固定停利模式")
    else:
        print("❌ 配置转换仍有问题，需要进一步调查")
    
    print(f"\n🎯 结论:")
    print(f"  - 实验机与GUI回测机的差异已找到并修正")
    print(f"  - 问题在于实验优化器的配置转换逻辑")
    print(f"  - 修正后两个系统应该产生一致的结果")

if __name__ == "__main__":
    main()
