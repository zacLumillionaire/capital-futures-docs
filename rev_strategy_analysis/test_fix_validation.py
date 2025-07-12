#!/usr/bin/env python3
"""
验证每口独立停利修正效果的测试脚本
测试您之前提到的配置：40,40,10 和 10,10,20 和 10,40,40
"""

import json
import subprocess
import sys
import os

def run_test_config(config, test_name):
    """运行单个测试配置"""
    print(f"\n🧪 测试配置: {test_name}")
    print("=" * 60)
    
    # 显示配置
    lot_settings = config["lot_settings"]
    print(f"📋 停利设置:")
    if config['individual_take_profit_enabled']:
        print(f"  - 第1口: {lot_settings['lot1']['take_profit']}点")
        print(f"  - 第2口: {lot_settings['lot2']['take_profit']}点")
        print(f"  - 第3口: {lot_settings['lot3']['take_profit']}点")
    else:
        print(f"  - 使用区间边缘停利")
    print(f"  - 每口独立停利: {config['individual_take_profit_enabled']}")
    
    # 执行测试
    config_json = json.dumps(config)
    cmd = [
        sys.executable, 
        "rev_multi_Profit-Funded Risk_多口.py",
        "--gui-mode",
        "--start-date", config["start_date"],
        "--end-date", config["end_date"],
        "--config", config_json
    ]
    
    print(f"\n🚀 执行测试...")
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=120)
        
        print(f"📊 执行结果:")
        print("=" * 40)
        if result.returncode == 0:
            print("✅ 测试执行成功!")
        else:
            print("❌ 测试执行失败!")
            print(f"返回码: {result.returncode}")
        
        # 分析日志输出
        stderr_lines = result.stderr.split('\n')
        
        # 查找固定停利日志
        fixed_tp_logs = []
        range_tp_logs = []
        
        for line in stderr_lines:
            if "固定停利" in line and "✅" in line:
                fixed_tp_logs.append(line)
            elif "觸及停利點" in line and "✅" in line:
                range_tp_logs.append(line)
        
        print(f"\n📈 停利执行分析:")
        print("-" * 40)
        print(f"🎯 固定停利次数: {len(fixed_tp_logs)}")
        print(f"🎯 区间边缘停利次数: {len(range_tp_logs)}")
        
        if config['individual_take_profit_enabled']:
            if len(fixed_tp_logs) > 0 and len(range_tp_logs) == 0:
                print("✅ 正确：只使用固定停利，没有区间边缘停利")
            elif len(range_tp_logs) > 0:
                print("❌ 错误：启用固定停利但仍有区间边缘停利")
                print("🔍 区间边缘停利日志:")
                for log in range_tp_logs:
                    print(f"   {log}")
            else:
                print("⚠️ 警告：没有检测到任何停利日志")
        else:
            if len(range_tp_logs) > 0 and len(fixed_tp_logs) == 0:
                print("✅ 正确：只使用区间边缘停利，没有固定停利")
            else:
                print("❌ 错误：应该使用区间边缘停利")
        
        # 显示部分日志
        print(f"\n📋 固定停利日志:")
        for log in fixed_tp_logs[:6]:  # 只显示前6条
            print(f"   {log.split('] ')[-1] if '] ' in log else log}")
        
        if len(range_tp_logs) > 0:
            print(f"\n📋 区间边缘停利日志:")
            for log in range_tp_logs[:3]:  # 只显示前3条
                print(f"   {log.split('] ')[-1] if '] ' in log else log}")
        
        return result.returncode == 0 and (
            (config['individual_take_profit_enabled'] and len(fixed_tp_logs) > 0 and len(range_tp_logs) == 0) or
            (not config['individual_take_profit_enabled'] and len(range_tp_logs) > 0 and len(fixed_tp_logs) == 0)
        )
        
    except subprocess.TimeoutExpired:
        print("❌ 测试超时!")
        return False
    except Exception as e:
        print(f"❌ 测试异常: {e}")
        return False

def main():
    print("🎯 每口独立停利修正效果验证")
    print("=" * 60)
    
    # 基础配置模板
    base_config = {
        "trade_lots": 3,
        "start_date": "2024-11-13",
        "end_date": "2024-11-20",
        "range_start_time": "12:00",
        "range_end_time": "12:02",
        "fixed_stop_mode": True,
        "filters": {
            "range_filter": {"enabled": False},
            "risk_filter": {"enabled": False},
            "stop_loss_filter": {"enabled": True, "stop_loss_type": "range_boundary"}
        }
    }
    
    # 测试配置列表
    test_configs = [
        {
            "name": "40,40,10点停利",
            "individual_take_profit_enabled": True,
            "lot_settings": {
                "lot1": {"trigger": 15, "trailing": 0, "take_profit": 40},
                "lot2": {"trigger": 15, "trailing": 0, "protection": 0, "take_profit": 40},
                "lot3": {"trigger": 15, "trailing": 0, "protection": 0, "take_profit": 10}
            }
        },
        {
            "name": "10,10,20点停利", 
            "individual_take_profit_enabled": True,
            "lot_settings": {
                "lot1": {"trigger": 15, "trailing": 0, "take_profit": 10},
                "lot2": {"trigger": 15, "trailing": 0, "protection": 0, "take_profit": 10},
                "lot3": {"trigger": 15, "trailing": 0, "protection": 0, "take_profit": 20}
            }
        },
        {
            "name": "10,40,40点停利",
            "individual_take_profit_enabled": True,
            "lot_settings": {
                "lot1": {"trigger": 15, "trailing": 0, "take_profit": 10},
                "lot2": {"trigger": 15, "trailing": 0, "protection": 0, "take_profit": 40},
                "lot3": {"trigger": 15, "trailing": 0, "protection": 0, "take_profit": 40}
            }
        },
        {
            "name": "对比测试-区间边缘停利",
            "individual_take_profit_enabled": False,
            "lot_settings": {
                "lot1": {"trigger": 15, "trailing": 0},
                "lot2": {"trigger": 15, "trailing": 0, "protection": 0},
                "lot3": {"trigger": 15, "trailing": 0, "protection": 0}
            }
        }
    ]
    
    # 运行所有测试
    results = []
    for test_config in test_configs:
        # 合并配置
        config = {**base_config}
        config.update({
            "individual_take_profit_enabled": test_config["individual_take_profit_enabled"],
            "lot_settings": test_config["lot_settings"]
        })
        
        # 运行测试
        success = run_test_config(config, test_config["name"])
        results.append((test_config["name"], success))
    
    # 总结结果
    print(f"\n🎊 测试总结")
    print("=" * 60)
    passed = 0
    for name, success in results:
        status = "✅ 通过" if success else "❌ 失败"
        print(f"{status} - {name}")
        if success:
            passed += 1
    
    print(f"\n📊 总体结果: {passed}/{len(results)} 测试通过")
    
    if passed == len(results):
        print("🎉 所有测试通过！每口独立停利功能修正成功！")
    else:
        print("⚠️ 部分测试失败，需要进一步检查")

if __name__ == "__main__":
    main()
