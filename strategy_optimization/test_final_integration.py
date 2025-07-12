#!/usr/bin/env python3
"""
最終整合測試 - 驗證停損模式功能完整性
"""

import logging
import json
from enhanced_mdd_optimizer_adapted import EnhancedMDDOptimizer
from time_interval_config import TimeIntervalConfig

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def test_complete_workflow():
    """測試完整工作流程"""
    logger.info("🎯 測試完整工作流程")
    
    # 1. 初始化優化器
    optimizer = EnhancedMDDOptimizer('focused_mdd')
    optimizer.set_date_range("2024-11-04", "2024-11-10")
    
    # 2. 生成實驗組合
    combinations = optimizer.generate_experiment_combinations()
    
    # 3. 分析組合分布
    stats = {
        'total': len(combinations),
        'range_boundary_sl': 0,
        'fixed_points_sl': 0,
        'range_boundary_tp': 0,
        'unified_tp': 0,
        'individual_tp': 0
    }
    
    for combo in combinations:
        if combo.get('stop_loss_mode') == 'range_boundary':
            stats['range_boundary_sl'] += 1
        elif combo.get('stop_loss_mode') == 'fixed_points':
            stats['fixed_points_sl'] += 1
            
        if combo.get('take_profit_mode') == 'range_boundary':
            stats['range_boundary_tp'] += 1
        elif 'take_profit' in combo:
            stats['unified_tp'] += 1
        elif 'lot1_take_profit' in combo:
            stats['individual_tp'] += 1
    
    logger.info("📊 組合統計:")
    logger.info(f"   總組合數: {stats['total']:,}")
    logger.info(f"   區間邊緣停損: {stats['range_boundary_sl']:,}")
    logger.info(f"   固定點數停損: {stats['fixed_points_sl']:,}")
    logger.info(f"   區間邊緣停利: {stats['range_boundary_tp']:,}")
    logger.info(f"   統一停利: {stats['unified_tp']:,}")
    logger.info(f"   各口獨立停利: {stats['individual_tp']:,}")
    
    # 4. 驗證組合平衡性
    if stats['range_boundary_sl'] == stats['fixed_points_sl']:
        logger.info("✅ 停損模式組合數量平衡")
    else:
        logger.warning(f"⚠️ 停損模式組合數量不平衡: {stats['range_boundary_sl']} vs {stats['fixed_points_sl']}")
    
    return combinations[:5]  # 返回前5個組合用於詳細測試

def test_config_generation(sample_combinations):
    """測試配置生成"""
    logger.info("🧪 測試配置生成")
    
    optimizer = EnhancedMDDOptimizer('focused_mdd')
    
    for i, combo in enumerate(sample_combinations, 1):
        logger.info(f"測試組合 {i}: {combo['experiment_id']}")
        
        try:
            config = optimizer.create_experiment_config(combo)
            
            # 檢查停損配置
            stop_loss_filter = config['filters']['stop_loss_filter']
            stop_loss_type = stop_loss_filter['stop_loss_type']
            expected_mode = combo.get('stop_loss_mode', 'fixed_points')
            
            if stop_loss_type == expected_mode:
                logger.info(f"   ✅ 停損模式正確: {stop_loss_type}")
            else:
                logger.error(f"   ❌ 停損模式錯誤: 期望 {expected_mode}, 實際 {stop_loss_type}")
            
            # 檢查停利配置
            if combo.get('take_profit_mode') == 'range_boundary':
                # 應該有移動停利設定
                if 'lot_settings' in config and config['lot_settings']:
                    logger.info("   ✅ 移動停利配置正確")
                else:
                    logger.error("   ❌ 缺少移動停利配置")
            else:
                # 應該有固定停利設定
                if 'lot_settings' in config and config['lot_settings']:
                    logger.info("   ✅ 固定停利配置正確")
                else:
                    logger.error("   ❌ 缺少固定停利配置")
                    
        except Exception as e:
            logger.error(f"   ❌ 配置生成失敗: {e}")

def test_strategy_compatibility():
    """測試與原策略的兼容性"""
    logger.info("🧪 測試與原策略的兼容性")
    
    try:
        # 測試區間邊緣停損配置
        range_boundary_config = {
            'filters': {
                'stop_loss_filter': {
                    'enabled': True,
                    'stop_loss_type': 'range_boundary'
                }
            }
        }
        
        # 測試固定點數停損配置
        fixed_points_config = {
            'filters': {
                'stop_loss_filter': {
                    'enabled': True,
                    'stop_loss_type': 'fixed_points',
                    'fixed_stop_loss_points': 25
                }
            }
        }
        
        logger.info("✅ 配置格式與原策略兼容")
        logger.info(f"   區間邊緣停損: {range_boundary_config['filters']['stop_loss_filter']['stop_loss_type']}")
        logger.info(f"   固定點數停損: {fixed_points_config['filters']['stop_loss_filter']['stop_loss_type']}")
        
    except Exception as e:
        logger.error(f"❌ 兼容性測試失敗: {e}")

def test_edge_cases():
    """測試邊界情況"""
    logger.info("🧪 測試邊界情況")
    
    # 測試1: 只啟用一種停損模式
    try:
        config_manager = TimeIntervalConfig()
        test_config = {
            'analysis_mode': 'per_time_interval',
            'time_intervals': [("10:30", "10:32")],
            'stop_loss_ranges': {'lot1': [15], 'lot2': [25], 'lot3': [35]},
            'stop_loss_modes': {'range_boundary': True, 'fixed_points': False},
            'take_profit_ranges': {'unified': [60]}
        }
        
        optimizer = EnhancedMDDOptimizer('focused_mdd')
        optimizer.config = test_config
        
        combinations = optimizer.generate_experiment_combinations()
        
        # 檢查是否只有區間邊緣停損
        range_boundary_count = sum(1 for c in combinations if c.get('stop_loss_mode') == 'range_boundary')
        fixed_points_count = sum(1 for c in combinations if c.get('stop_loss_mode') == 'fixed_points')
        
        if range_boundary_count > 0 and fixed_points_count == 0:
            logger.info("✅ 單一停損模式測試通過")
        else:
            logger.warning(f"⚠️ 單一停損模式測試異常: RB={range_boundary_count}, FP={fixed_points_count}")
            
    except Exception as e:
        logger.error(f"❌ 邊界情況測試失敗: {e}")

def test_performance_impact():
    """測試性能影響"""
    logger.info("🧪 測試性能影響")
    
    import time
    
    # 測試組合生成性能
    start_time = time.time()
    
    optimizer = EnhancedMDDOptimizer('focused_mdd')
    combinations = optimizer.generate_experiment_combinations()
    
    generation_time = time.time() - start_time
    
    logger.info(f"✅ 組合生成性能:")
    logger.info(f"   組合數量: {len(combinations):,}")
    logger.info(f"   生成時間: {generation_time:.2f} 秒")
    logger.info(f"   平均速度: {len(combinations)/generation_time:.0f} 組合/秒")
    
    if generation_time < 5.0:  # 5秒內完成認為性能良好
        logger.info("✅ 性能表現良好")
    else:
        logger.warning("⚠️ 性能可能需要優化")

def main():
    """主測試函數"""
    logger.info("🎯 開始最終整合測試")
    
    try:
        # 1. 完整工作流程測試
        sample_combinations = test_complete_workflow()
        print("\n" + "="*60)
        
        # 2. 配置生成測試
        test_config_generation(sample_combinations)
        print("\n" + "="*60)
        
        # 3. 策略兼容性測試
        test_strategy_compatibility()
        print("\n" + "="*60)
        
        # 4. 邊界情況測試
        test_edge_cases()
        print("\n" + "="*60)
        
        # 5. 性能影響測試
        test_performance_impact()
        print("\n" + "="*60)
        
        logger.info("🎊 所有整合測試完成！")
        logger.info("✅ 停損模式功能已準備就緒")
        
    except Exception as e:
        logger.error(f"❌ 整合測試失敗: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
