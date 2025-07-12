#!/usr/bin/env python3
"""
測試停損模式功能
驗證區間邊緣停損和固定點數停損的配置轉換
"""

import logging
import json
from enhanced_mdd_optimizer_adapted import EnhancedMDDOptimizer
from time_interval_config import TimeIntervalConfig

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def test_stop_loss_modes():
    """測試停損模式配置"""
    logger.info("🧪 測試停損模式配置")
    
    # 使用focused_mdd配置（已包含停損模式）
    optimizer = EnhancedMDDOptimizer('focused_mdd')
    optimizer.set_date_range("2024-11-04", "2024-11-10")
    
    # 測試1: 區間邊緣停損 + 區間邊緣停利
    params1 = {
        'experiment_id': 'test_range_boundary_sl',
        'time_interval': '10:30-10:32',
        'lot1_stop_loss': 15,
        'lot2_stop_loss': 25,
        'lot3_stop_loss': 35,
        'take_profit_mode': 'range_boundary',
        'stop_loss_mode': 'range_boundary'
    }
    
    config1 = optimizer.create_experiment_config(params1)
    logger.info("✅ 區間邊緣停損 + 區間邊緣停利配置:")
    logger.info(f"   停損模式: {config1['filters']['stop_loss_filter']['stop_loss_type']}")
    logger.info(f"   停利模式: {params1['take_profit_mode']}")
    logger.info(f"   第1口移動停利觸發: {config1['lot_settings']['lot1']['trigger']}")
    logger.info(f"   第2口移動停利觸發: {config1['lot_settings']['lot2']['trigger']}")
    logger.info(f"   第3口移動停利觸發: {config1['lot_settings']['lot3']['trigger']}")
    
    # 測試2: 固定點數停損 + 各口獨立停利
    params2 = {
        'experiment_id': 'test_fixed_points_sl',
        'time_interval': '10:30-10:32',
        'lot1_stop_loss': 15,
        'lot2_stop_loss': 25,
        'lot3_stop_loss': 35,
        'lot1_take_profit': 45,
        'lot2_take_profit': 55,
        'lot3_take_profit': 65,
        'stop_loss_mode': 'fixed_points'
    }
    
    config2 = optimizer.create_experiment_config(params2)
    logger.info("✅ 固定點數停損 + 各口獨立停利配置:")
    logger.info(f"   停損模式: {config2['filters']['stop_loss_filter']['stop_loss_type']}")
    logger.info(f"   固定停損點數: {config2['filters']['stop_loss_filter']['fixed_stop_loss_points']}")
    logger.info(f"   第1口移動停利觸發: {config2['lot_settings']['lot1']['trigger']}")
    logger.info(f"   第2口移動停利觸發: {config2['lot_settings']['lot2']['trigger']}")
    logger.info(f"   第3口移動停利觸發: {config2['lot_settings']['lot3']['trigger']}")

def test_combination_generation():
    """測試組合生成功能"""
    logger.info("🧪 測試組合生成功能")

    optimizer = EnhancedMDDOptimizer('focused_mdd')

    # 檢查配置
    logger.info(f"配置分析模式: {optimizer.config.get('analysis_mode')}")
    logger.info(f"停損模式配置: {optimizer.config.get('stop_loss_modes')}")

    combinations = optimizer.generate_experiment_combinations()
    
    # 統計不同模式的組合數量
    range_boundary_sl_count = 0
    fixed_points_sl_count = 0
    range_boundary_tp_count = 0
    unified_tp_count = 0
    individual_tp_count = 0
    
    for combo in combinations:
        if combo.get('stop_loss_mode') == 'range_boundary':
            range_boundary_sl_count += 1
        elif combo.get('stop_loss_mode') == 'fixed_points':
            fixed_points_sl_count += 1
            
        if combo.get('take_profit_mode') == 'range_boundary':
            range_boundary_tp_count += 1
        elif 'take_profit' in combo:
            unified_tp_count += 1
        elif 'lot1_take_profit' in combo:
            individual_tp_count += 1
    
    logger.info("✅ 組合生成統計:")
    logger.info(f"   總組合數: {len(combinations)}")
    logger.info(f"   區間邊緣停損: {range_boundary_sl_count}")
    logger.info(f"   固定點數停損: {fixed_points_sl_count}")
    logger.info(f"   區間邊緣停利: {range_boundary_tp_count}")
    logger.info(f"   統一停利: {unified_tp_count}")
    logger.info(f"   各口獨立停利: {individual_tp_count}")
    
    # 顯示幾個範例組合
    logger.info("📋 範例組合:")
    for i, combo in enumerate(combinations[:5]):
        logger.info(f"   組合{i+1}: {combo['experiment_id']}")
        logger.info(f"     停損模式: {combo.get('stop_loss_mode', 'N/A')}")
        logger.info(f"     停利模式: {combo.get('take_profit_mode', 'individual/unified')}")

def test_config_validation():
    """測試配置驗證"""
    logger.info("🧪 測試配置驗證")
    
    config_manager = TimeIntervalConfig()
    focused_config = config_manager.get_config('focused_mdd')
    
    # 檢查停損模式配置
    if 'stop_loss_modes' in focused_config:
        logger.info("✅ 找到停損模式配置:")
        for mode, enabled in focused_config['stop_loss_modes'].items():
            logger.info(f"   {mode}: {'啟用' if enabled else '停用'}")
    else:
        logger.warning("⚠️ 未找到停損模式配置")
    
    # 檢查停利模式配置
    if 'take_profit_ranges' in focused_config:
        tp_ranges = focused_config['take_profit_ranges']
        logger.info("✅ 找到停利模式配置:")
        if 'range_boundary' in tp_ranges:
            logger.info(f"   區間邊緣停利: {'啟用' if tp_ranges['range_boundary'] else '停用'}")
        if 'unified' in tp_ranges:
            logger.info(f"   統一停利範圍: {tp_ranges['unified']}")
        if 'individual' in tp_ranges:
            logger.info(f"   各口獨立停利範圍: {tp_ranges['individual']}")

def test_original_strategy_compatibility():
    """測試與原始策略的兼容性"""
    logger.info("🧪 測試與原始策略的兼容性")
    
    try:
        import importlib
        strategy_module = importlib.import_module('multi_Profit-Funded Risk_多口')
        
        # 檢查StopLossType枚舉
        if hasattr(strategy_module, 'StopLossType'):
            StopLossType = strategy_module.StopLossType
            logger.info("✅ 找到StopLossType枚舉:")
            
            # 檢查支援的停損類型
            if hasattr(StopLossType, 'RANGE_BOUNDARY'):
                logger.info("   ✅ 支援 RANGE_BOUNDARY (區間邊緣停損)")
            if hasattr(StopLossType, 'FIXED_POINTS'):
                logger.info("   ✅ 支援 FIXED_POINTS (固定點數停損)")
            if hasattr(StopLossType, 'OPENING_PRICE'):
                logger.info("   ✅ 支援 OPENING_PRICE (開盤價停損)")
        
        # 檢查StopLossConfig類別
        if hasattr(strategy_module, 'StopLossConfig'):
            StopLossConfig = strategy_module.StopLossConfig
            logger.info("✅ 找到StopLossConfig類別")
            
            # 檢查預設值
            default_config = StopLossConfig()
            logger.info(f"   預設停損類型: {default_config.stop_loss_type}")
            logger.info(f"   預設固定停損點數: {default_config.fixed_stop_loss_points}")
            logger.info(f"   預設使用區間中點: {default_config.use_range_midpoint}")
        
        # 檢查get_initial_stop_loss函數
        if hasattr(strategy_module, 'get_initial_stop_loss'):
            logger.info("✅ 找到get_initial_stop_loss函數")
        
    except ImportError as e:
        logger.error(f"❌ 無法導入原始策略模組: {e}")

def main():
    """主測試函數"""
    logger.info("🎯 開始測試停損模式功能")
    
    try:
        test_stop_loss_modes()
        print("\n" + "="*60)
        
        test_combination_generation()
        print("\n" + "="*60)
        
        test_config_validation()
        print("\n" + "="*60)
        
        test_original_strategy_compatibility()
        print("\n" + "="*60)
        
        logger.info("🎊 所有測試完成！")
        
    except Exception as e:
        logger.error(f"❌ 測試失敗: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
