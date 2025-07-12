#!/usr/bin/env python3
"""
详细测试每口独立停利功能
使用更小的停利点数来确保固定停利先于区间边缘触发
"""

import json
import subprocess
import sys
import os
from datetime import datetime

def test_small_take_profit():
    """测试小停利点数，确保固定停利先触发"""
    
    print("🧪 测试每口独立停利功能 - 小停利点数")
    print("=" * 60)
    
    # 使用很小的停利点数，确保比区间边缘更容易触发
    config = {
        "trade_lots": 3,
        "start_date": "2024-11-04",
        "end_date": "2024-11-05",
        "range_start_time": "10:30",
        "range_end_time": "10:31",
        "fixed_stop_mode": True,
        "individual_take_profit_enabled": True,  # 🎯 启用每口独立停利
        "lot_settings": {
            "lot1": {
                "trigger": 15,
                "trailing": 0,
                "take_profit": 5   # 🎯 很小的停利点数
            },
            "lot2": {
                "trigger": 25,
                "trailing": 0,
                "protection": 0,
                "take_profit": 8   # 🎯 很小的停利点数
            },
            "lot3": {
                "trigger": 35,
                "trailing": 0,
                "protection": 0,
                "take_profit": 12  # 🎯 很小的停利点数
            }
        },
        "filters": {
            "range_filter": {"enabled": False},
            "risk_filter": {"enabled": False},
            "stop_loss_filter": {"enabled": True, "stop_loss_type": "range_boundary"}
        }
    }
    
    print("📋 测试配置:")
    print(f"  - 第1口: 停利{config['lot_settings']['lot1']['take_profit']}点")
    print(f"  - 第2口: 停利{config['lot_settings']['lot2']['take_profit']}点")
    print(f"  - 第3口: 停利{config['lot_settings']['lot3']['take_profit']}点")
    print(f"  - 每口独立停利: {config['individual_take_profit_enabled']}")
    
    # 执行测试
    config_json = json.dumps(config)
    cmd = [
        sys.executable,
        "rev_multi_Profit-Funded Risk_多口.py",
        "--gui-mode",  # 🎯 添加GUI模式参数
        "--start-date", config["start_date"],
        "--end-date", config["end_date"],
        "--config", config_json
    ]
    
    print(f"\n🚀 执行测试...")
    
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=60)
        
        print("📊 执行结果:")
        print("=" * 40)
        
        if result.returncode == 0:
            print("✅ 测试执行成功!")
        else:
            print(f"❌ 测试执行失败 (返回码: {result.returncode})")
        
        print("\n📈 回测输出:")
        print("-" * 60)
        print(result.stdout)
        print("-" * 60)
        
        if result.stderr:
            print("⚠️ 错误输出:")
            print(result.stderr)
            print("-" * 60)
        
        # 检查是否有固定停利的日志
        if "固定停利" in result.stderr:
            print("✅ 检测到固定停利功能正常运作")
        else:
            print("⚠️ 未检测到固定停利日志，可能仍在使用区间边缘停利")
            
        # 分析区间大小
        if "區間大小" in result.stderr:
            import re
            range_matches = re.findall(r'區間大小 (\d+) 點', result.stderr)
            if range_matches:
                for i, range_size in enumerate(range_matches):
                    print(f"📏 第{i+1}天区间大小: {range_size}点")
                    if int(range_size) > 12:  # 最大停利点数
                        print(f"   ✅ 区间大小({range_size}点) > 最大停利点数(12点)，固定停利应该先触发")
                    else:
                        print(f"   ⚠️ 区间大小({range_size}点) <= 最大停利点数(12点)，区间边缘可能先触发")
        
    except subprocess.TimeoutExpired:
        print("❌ 测试超时")
    except Exception as e:
        print(f"❌ 测试失败: {str(e)}")

def test_without_individual_tp():
    """对比测试：不启用每口独立停利"""
    
    print("\n🧪 对比测试 - 不启用每口独立停利")
    print("=" * 60)
    
    config = {
        "trade_lots": 3,
        "start_date": "2024-11-04",
        "end_date": "2024-11-05",
        "range_start_time": "10:30",
        "range_end_time": "10:31",
        "fixed_stop_mode": True,
        "individual_take_profit_enabled": False,  # 🎯 不启用每口独立停利
        "lot_settings": {
            "lot1": {"trigger": 15, "trailing": 0, "take_profit": 5},
            "lot2": {"trigger": 25, "trailing": 0, "protection": 0, "take_profit": 8},
            "lot3": {"trigger": 35, "trailing": 0, "protection": 0, "take_profit": 12}
        },
        "filters": {
            "range_filter": {"enabled": False},
            "risk_filter": {"enabled": False},
            "stop_loss_filter": {"enabled": True, "stop_loss_type": "range_boundary"}
        }
    }
    
    print(f"📋 每口独立停利: {config['individual_take_profit_enabled']}")
    
    config_json = json.dumps(config)
    cmd = [
        sys.executable,
        "rev_multi_Profit-Funded Risk_多口.py",
        "--gui-mode",  # 🎯 添加GUI模式参数
        "--start-date", config["start_date"],
        "--end-date", config["end_date"],
        "--config", config_json
    ]
    
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=60)
        
        if "固定停利" in result.stderr:
            print("❌ 错误：不应该出现固定停利日志")
        else:
            print("✅ 正确：没有固定停利日志，使用区间边缘停利")
            
    except Exception as e:
        print(f"❌ 对比测试失败: {str(e)}")

if __name__ == "__main__":
    print("🎯 每口独立停利功能详细测试")
    print("=" * 60)
    
    # 测试1: 启用每口独立停利（小停利点数）
    test_small_take_profit()
    
    # 测试2: 不启用每口独立停利
    test_without_individual_tp()
    
    print("\n🎊 测试完成")
