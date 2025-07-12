#!/usr/bin/env python3
"""
调查为什么相同配置产生不同结果
检查可能的原因：数据变化、策略逻辑修改、配置理解错误等
"""

import json
import subprocess
import sys
from datetime import datetime

def test_with_detailed_logs():
    """运行详细日志测试，查看具体交易情况"""
    print("🔍 详细日志分析")
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
    
    print(f"📋 测试配置: 12:00-12:02, L1SL:15 L2SL:15 L3SL:15, TP:40")
    
    config_json = json.dumps(config)
    cmd = [
        sys.executable, 
        "rev_multi_Profit-Funded Risk_多口.py",
        "--gui-mode",
        "--start-date", "2024-11-04",
        "--end-date", "2025-06-27",
        "--config", config_json
    ]
    
    print(f"🚀 执行详细测试...")
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=120)
        
        if result.returncode == 0:
            print("✅ 测试执行成功!")
            
            # 分析输出
            stderr_lines = result.stderr.split('\n')
            
            # 统计交易信息
            long_trades = 0
            short_trades = 0
            profit_trades = 0
            loss_trades = 0
            total_profit = 0
            total_loss = 0
            
            # 查找交易记录
            trade_lines = []
            for line in stderr_lines:
                if "進場" in line or "出場" in line or "損益" in line:
                    trade_lines.append(line)
                if "LONG" in line and "進場" in line:
                    long_trades += 1
                elif "SHORT" in line and "進場" in line:
                    short_trades += 1
                if "損益:" in line:
                    try:
                        pnl_str = line.split("損益:")[1].strip()
                        if "+" in pnl_str:
                            pnl = float(pnl_str.replace("+", ""))
                            profit_trades += 1
                            total_profit += pnl
                        elif "-" in pnl_str:
                            pnl = float(pnl_str.replace("-", ""))
                            loss_trades += 1
                            total_loss += pnl
                    except:
                        pass
            
            # 查找总结信息
            total_pnl = None
            trade_count = 0
            win_rate = None
            
            for line in stderr_lines:
                if "總損益(3口):" in line:
                    try:
                        total_pnl = float(line.split("總損益(3口):")[1].strip())
                    except:
                        pass
                elif "交易次數:" in line:
                    try:
                        trade_count = int(line.split("交易次數:")[1].strip())
                    except:
                        pass
                elif "勝率:" in line:
                    try:
                        win_rate = float(line.split("勝率:")[1].strip().replace("%", ""))
                    except:
                        pass
            
            print(f"\n📊 交易统计:")
            print(f"  - 总损益: {total_pnl}")
            print(f"  - 交易次数: {trade_count}")
            print(f"  - 多头交易: {long_trades}")
            print(f"  - 空头交易: {short_trades}")
            print(f"  - 盈利交易: {profit_trades}")
            print(f"  - 亏损交易: {loss_trades}")
            print(f"  - 总盈利: {total_profit}")
            print(f"  - 总亏损: {total_loss}")
            print(f"  - 胜率: {win_rate}%")
            
            # 显示前10笔交易
            print(f"\n📝 前10笔交易记录:")
            for i, line in enumerate(trade_lines[:10]):
                print(f"  {i+1}. {line}")
            
            return {
                'total_pnl': total_pnl,
                'trade_count': trade_count,
                'long_trades': long_trades,
                'short_trades': short_trades,
                'profit_trades': profit_trades,
                'loss_trades': loss_trades,
                'win_rate': win_rate
            }
        else:
            print("❌ 测试执行失败!")
            print(f"错误: {result.stderr}")
            return None
            
    except Exception as e:
        print(f"❌ 测试异常: {e}")
        return None

def test_different_configurations():
    """测试不同配置，看看是否能重现2544.0的结果"""
    print("\n🧪 测试不同配置")
    print("=" * 60)
    
    # 测试配置1: 可能的原始配置
    configs_to_test = [
        {
            "name": "配置1: 可能是区间边缘停利",
            "config": {
                "trade_lots": 3,
                "start_date": "2024-11-04",
                "end_date": "2025-06-27",
                "range_start_time": "12:00",
                "range_end_time": "12:02",
                "fixed_stop_mode": True,
                "individual_take_profit_enabled": False,  # 关闭个别停利
                "lot_settings": {
                    "lot1": {"trigger": 15, "trailing": 0},
                    "lot2": {"trigger": 15, "trailing": 0},
                    "lot3": {"trigger": 15, "trailing": 0}
                },
                "filters": {
                    "range_filter": {"enabled": False},
                    "risk_filter": {"enabled": False},
                    "stop_loss_filter": {"enabled": False}
                }
            }
        },
        {
            "name": "配置2: 移动停利模式",
            "config": {
                "trade_lots": 3,
                "start_date": "2024-11-04",
                "end_date": "2025-06-27",
                "range_start_time": "12:00",
                "range_end_time": "12:02",
                "fixed_stop_mode": False,  # 关闭固定停损
                "individual_take_profit_enabled": True,
                "lot_settings": {
                    "lot1": {"trigger": 15, "trailing": 40, "take_profit": 40},
                    "lot2": {"trigger": 15, "trailing": 40, "take_profit": 40},
                    "lot3": {"trigger": 15, "trailing": 40, "take_profit": 40}
                },
                "filters": {
                    "range_filter": {"enabled": False},
                    "risk_filter": {"enabled": False},
                    "stop_loss_filter": {"enabled": False}
                }
            }
        },
        {
            "name": "配置3: 原始实验配置",
            "config": {
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
        }
    ]
    
    results = []
    
    for test_config in configs_to_test:
        print(f"\n🎯 {test_config['name']}")
        print("-" * 40)
        
        config_json = json.dumps(test_config['config'])
        cmd = [
            sys.executable, 
            "rev_multi_Profit-Funded Risk_多口.py",
            "--gui-mode",
            "--start-date", "2024-11-04",
            "--end-date", "2025-06-27",
            "--config", config_json
        ]
        
        try:
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=120)
            
            if result.returncode == 0:
                # 解析结果
                stderr_lines = result.stderr.split('\n')
                
                total_pnl = None
                trade_count = 0
                
                for line in stderr_lines:
                    if "總損益(3口):" in line:
                        try:
                            total_pnl = float(line.split("總損益(3口):")[1].strip())
                        except:
                            pass
                    elif "交易次數:" in line:
                        try:
                            trade_count = int(line.split("交易次數:")[1].strip())
                        except:
                            pass
                
                print(f"✅ 结果: P&L = {total_pnl}, 交易数 = {trade_count}")
                results.append({
                    'name': test_config['name'],
                    'pnl': total_pnl,
                    'trades': trade_count
                })
                
                # 检查是否接近2544.0
                if total_pnl and abs(total_pnl - 2544.0) < 50:
                    print(f"🎉 找到接近目标的配置！差异: {abs(total_pnl - 2544.0)}")
                
            else:
                print(f"❌ 执行失败: {result.stderr}")
                results.append({
                    'name': test_config['name'],
                    'pnl': None,
                    'trades': None
                })
                
        except Exception as e:
            print(f"❌ 异常: {e}")
            results.append({
                'name': test_config['name'],
                'pnl': None,
                'trades': None
            })
    
    return results

def main():
    print("🔍 调查结果差异原因")
    print("=" * 80)
    print("目标: 找出为什么相同配置产生1830.0而不是2544.0")
    print("=" * 80)
    
    # 1. 详细日志分析
    detailed_result = test_with_detailed_logs()
    
    # 2. 测试不同配置
    config_results = test_different_configurations()
    
    # 3. 总结分析
    print(f"\n{'='*80}")
    print("📊 调查结果总结")
    print(f"{'='*80}")
    
    print(f"🎯 目标结果: P&L = 2544.0 (昨天实验)")
    print(f"🔧 当前结果: P&L = 1830.0 (今天测试)")
    print(f"📉 差异: {2544.0 - 1830.0} = 714.0点")
    
    if detailed_result:
        print(f"\n📊 详细分析:")
        print(f"  - 交易次数: {detailed_result['trade_count']}")
        print(f"  - 多头交易: {detailed_result['long_trades']}")
        print(f"  - 空头交易: {detailed_result['short_trades']}")
        print(f"  - 胜率: {detailed_result['win_rate']}%")
    
    print(f"\n🧪 配置测试结果:")
    for result in config_results:
        status = "✅" if result['pnl'] else "❌"
        pnl_str = f"{result['pnl']}" if result['pnl'] else "失败"
        print(f"  {status} {result['name']}: P&L = {pnl_str}")
        
        if result['pnl'] and abs(result['pnl'] - 2544.0) < 100:
            print(f"    🎯 接近目标！差异: {abs(result['pnl'] - 2544.0)}")
    
    print(f"\n💡 可能的原因:")
    print(f"  1. 策略逻辑在昨天之后有修改")
    print(f"  2. 数据源有更新或变化")
    print(f"  3. 昨天的实验配置理解有误")
    print(f"  4. 实验优化器和GUI回测的配置转换有差异")
    
    # 检查是否有配置能产生接近2544的结果
    close_results = [r for r in config_results if r['pnl'] and abs(r['pnl'] - 2544.0) < 200]
    if close_results:
        print(f"\n🎉 找到接近目标的配置:")
        for result in close_results:
            print(f"  - {result['name']}: P&L = {result['pnl']}")
    else:
        print(f"\n⚠️ 没有找到能产生接近2544.0结果的配置")
        print(f"   建议检查昨天的实验是否使用了不同的参数或逻辑")

if __name__ == "__main__":
    main()
