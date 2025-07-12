#!/usr/bin/env python3
"""
测试新的时间区间分析配置
验证各口独立停利功能是否正确添加
"""

import sys
sys.path.append('experiment_analysis')

from mdd_search_config import MDDSearchConfig
from enhanced_mdd_optimizer import EnhancedMDDOptimizer

def test_new_config():
    """测试新配置"""
    print("🧪 测试新的时间区间分析配置")
    print("=" * 60)
    
    # 获取配置
    config = MDDSearchConfig.get_time_interval_analysis_config()
    
    print("📋 配置信息:")
    print(f"  - 停损范围: {len(config['stop_loss_ranges']['lot1'])} 个值")
    print(f"  - 停利模式: {config['take_profit_modes']}")
    print(f"  - 统一停利: {config['take_profit_ranges']['unified']}")
    print(f"  - 各口独立停利: {config['take_profit_ranges']['individual']}")
    print(f"  - 时间区间: {len(config['time_intervals'])} 个")
    print(f"  - 预估组合数: {config['estimated_combinations']['per_interval_analysis']}")
    
    # 创建优化器并生成组合
    optimizer = EnhancedMDDOptimizer()
    optimizer.start_date = "2024-11-04"
    optimizer.end_date = "2025-06-27"
    combinations = optimizer.generate_combinations(config)
    
    print(f"\n📊 实际生成组合数: {len(combinations)}")
    
    # 分析组合类型
    unified_count = 0
    individual_count = 0
    boundary_count = 0
    
    for combo in combinations:
        if 'take_profit' in combo:
            unified_count += 1
        elif 'lot1_take_profit' in combo:
            individual_count += 1
        elif 'take_profit_mode' in combo:
            boundary_count += 1
    
    print(f"\n📈 组合分析:")
    print(f"  - 统一停利组合: {unified_count}")
    print(f"  - 各口独立停利组合: {individual_count}")
    print(f"  - 区间边缘停利组合: {boundary_count}")
    print(f"  - 总计: {unified_count + individual_count + boundary_count}")
    
    # 显示一些示例组合
    print(f"\n📝 示例组合:")
    
    # 统一停利示例
    unified_examples = [c for c in combinations if 'take_profit' in c][:2]
    print(f"  统一停利示例:")
    for i, combo in enumerate(unified_examples, 1):
        print(f"    {i}. {combo['experiment_id']}")
    
    # 各口独立停利示例
    individual_examples = [c for c in combinations if 'lot1_take_profit' in c][:2]
    print(f"  各口独立停利示例:")
    for i, combo in enumerate(individual_examples, 1):
        print(f"    {i}. {combo['experiment_id']}")
    
    # 区间边缘停利示例
    boundary_examples = [c for c in combinations if 'take_profit_mode' in c][:2]
    print(f"  区间边缘停利示例:")
    for i, combo in enumerate(boundary_examples, 1):
        print(f"    {i}. {combo['experiment_id']}")
    
    # 验证计算
    expected_stop_combinations = 220  # 10*10*10 with constraint
    expected_unified = expected_stop_combinations * 5  # 5个统一停利值
    expected_individual = expected_stop_combinations * 27  # 3*3*3 = 27个各口独立组合
    expected_boundary = expected_stop_combinations * 1  # 1个区间边缘
    expected_per_interval = expected_unified + expected_individual + expected_boundary
    expected_total = expected_per_interval * 3  # 3个时间区间
    
    print(f"\n🔍 验证计算:")
    print(f"  - 预期停损组合: {expected_stop_combinations}")
    print(f"  - 预期统一停利: {expected_unified}")
    print(f"  - 预期各口独立: {expected_individual}")
    print(f"  - 预期区间边缘: {expected_boundary}")
    print(f"  - 预期每区间总计: {expected_per_interval}")
    print(f"  - 预期总计: {expected_total}")
    
    if len(combinations) == expected_total:
        print(f"✅ 组合数量验证通过!")
    else:
        print(f"❌ 组合数量不符: 实际{len(combinations)} vs 预期{expected_total}")
    
    return len(combinations) == expected_total

if __name__ == "__main__":
    success = test_new_config()
    if success:
        print(f"\n🎉 配置修改成功！")
        print(f"✅ 可以使用以下指令启动实验:")
        print(f"   python enhanced_mdd_optimizer.py --config time_interval_analysis --max-workers 4")
    else:
        print(f"\n❌ 配置需要调整")
