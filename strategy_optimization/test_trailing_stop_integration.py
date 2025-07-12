#!/usr/bin/env python3
"""
測試時間區間分析中的移動停利功能整合
驗證配置轉換和移動停利參數是否正確傳遞
"""

import logging
import json
from enhanced_mdd_optimizer_adapted import EnhancedMDDOptimizer

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def test_config_conversion():
    """測試配置轉換功能"""
    logger.info("🧪 測試配置轉換功能")

    optimizer = EnhancedMDDOptimizer('quick')
    optimizer.set_date_range("2024-11-04", "2024-11-10")
    
    # 測試1: 區間邊緣停利模式
    params1 = {
        'experiment_id': 'test_001',
        'time_interval': '10:30-10:32',
        'lot1_stop_loss': 15,
        'lot2_stop_loss': 25,
        'lot3_stop_loss': 35,
        'take_profit_mode': 'range_boundary'
    }
    
    config1 = optimizer.create_experiment_config(params1)
    logger.info("✅ 區間邊緣停利配置:")
    logger.info(f"   第1口: 觸發={config1['lot_settings']['lot1']['trigger']}, 回撤={config1['lot_settings']['lot1']['trailing']}%")
    logger.info(f"   第2口: 觸發={config1['lot_settings']['lot2']['trigger']}, 回撤={config1['lot_settings']['lot2']['trailing']}%")
    logger.info(f"   第3口: 觸發={config1['lot_settings']['lot3']['trigger']}, 回撤={config1['lot_settings']['lot3']['trailing']}%")
    
    # 測試2: 各口獨立停利模式
    params2 = {
        'experiment_id': 'test_002',
        'time_interval': '10:30-10:32',
        'lot1_stop_loss': 15,
        'lot2_stop_loss': 25,
        'lot3_stop_loss': 35,
        'lot1_take_profit': 45,
        'lot2_take_profit': 55,
        'lot3_take_profit': 65
    }
    
    config2 = optimizer.create_experiment_config(params2)
    logger.info("✅ 各口獨立停利配置:")
    logger.info(f"   第1口: 觸發={config2['lot_settings']['lot1']['trigger']}, 回撤={config2['lot_settings']['lot1']['trailing']}%")
    logger.info(f"   第2口: 觸發={config2['lot_settings']['lot2']['trigger']}, 回撤={config2['lot_settings']['lot2']['trailing']}%")
    logger.info(f"   第3口: 觸發={config2['lot_settings']['lot3']['trigger']}, 回撤={config2['lot_settings']['lot3']['trailing']}%")
    
    # 測試3: 統一停利模式
    params3 = {
        'experiment_id': 'test_003',
        'time_interval': '10:30-10:32',
        'lot1_stop_loss': 15,
        'lot2_stop_loss': 25,
        'lot3_stop_loss': 35,
        'take_profit': 60
    }
    
    config3 = optimizer.create_experiment_config(params3)
    logger.info("✅ 統一停利配置:")
    logger.info(f"   第1口: 觸發={config3['lot_settings']['lot1']['trigger']}, 回撤={config3['lot_settings']['lot1']['trailing']}%")
    logger.info(f"   第2口: 觸發={config3['lot_settings']['lot2']['trigger']}, 回撤={config3['lot_settings']['lot2']['trailing']}%")
    logger.info(f"   第3口: 觸發={config3['lot_settings']['lot3']['trigger']}, 回撤={config3['lot_settings']['lot3']['trailing']}%")

def test_gui_config_conversion():
    """測試GUI配置轉換"""
    logger.info("🧪 測試GUI配置轉換")

    optimizer = EnhancedMDDOptimizer('quick')
    optimizer.set_date_range("2024-11-04", "2024-11-10")
    
    # 創建測試配置
    test_config = {
        'start_date': '2024-11-04',
        'end_date': '2024-11-10',
        'range_start_time': '10:30',
        'range_end_time': '10:32',
        'trade_lots': 3,
        'lot_settings': {
            'lot1': {'stop_loss': 15, 'trigger': 15, 'trailing': 20, 'protection': 1.0},
            'lot2': {'stop_loss': 25, 'trigger': 40, 'trailing': 20, 'protection': 2.0},
            'lot3': {'stop_loss': 35, 'trigger': 65, 'trailing': 20, 'protection': 2.0}
        },
        'filters': {
            'range_filter': {'enabled': False},
            'risk_filter': {'enabled': False},
            'stop_loss_filter': {'enabled': False}
        },
        'take_profit_mode': 'range_boundary'
    }
    
    gui_config = optimizer._convert_to_gui_config(test_config)
    
    logger.info("✅ GUI配置轉換結果:")
    logger.info(json.dumps(gui_config, indent=2, ensure_ascii=False))
    
    # 驗證關鍵參數
    assert gui_config['trade_lots'] == 3
    assert gui_config['lot_settings']['lot1']['trigger'] == 15
    assert gui_config['lot_settings']['lot1']['trailing'] == 20
    assert gui_config['lot_settings']['lot2']['trigger'] == 40
    assert gui_config['lot_settings']['lot3']['trigger'] == 65
    assert gui_config['take_profit_mode'] == 'range_boundary'
    
    logger.info("✅ GUI配置轉換驗證通過")

def test_original_strategy_compatibility():
    """測試與原始策略的兼容性"""
    logger.info("🧪 測試與原始策略的兼容性")
    
    # 檢查原始策略是否支援GUI模式
    try:
        import importlib
        strategy_module = importlib.import_module('multi_Profit-Funded Risk_多口')
        
        # 檢查是否有create_strategy_config_from_gui函數
        if hasattr(strategy_module, 'create_strategy_config_from_gui'):
            logger.info("✅ 原始策略支援GUI配置轉換")
        else:
            logger.warning("⚠️ 原始策略缺少GUI配置轉換函數")
            
        # 檢查LotRule類別
        if hasattr(strategy_module, 'LotRule'):
            LotRule = strategy_module.LotRule
            logger.info("✅ 找到LotRule類別")
            
            # 檢查移動停利相關屬性
            lot_rule = LotRule()
            if hasattr(lot_rule, 'use_trailing_stop'):
                logger.info("✅ 支援use_trailing_stop屬性")
            if hasattr(lot_rule, 'trailing_activation'):
                logger.info("✅ 支援trailing_activation屬性")
            if hasattr(lot_rule, 'trailing_pullback'):
                logger.info("✅ 支援trailing_pullback屬性")
                
        else:
            logger.error("❌ 找不到LotRule類別")
            
    except ImportError as e:
        logger.error(f"❌ 無法導入原始策略模組: {e}")

def test_parameter_mapping():
    """測試參數映射邏輯"""
    logger.info("🧪 測試參數映射邏輯")
    
    # 驗證time_interval_config.py中的參數是否正確映射到移動停利
    from time_interval_config import TimeIntervalConfig
    
    config_manager = TimeIntervalConfig()
    configs = config_manager.list_available_configs()
    
    for name, config in configs.items():
        logger.info(f"📋 檢查配置: {name}")
        
        # 檢查take_profit_ranges
        if 'take_profit_ranges' in config:
            tp_ranges = config['take_profit_ranges']
            logger.info(f"   統一停利範圍: {tp_ranges.get('unified', [])}")
            logger.info(f"   獨立停利範圍: {tp_ranges.get('individual', [])}")
            
            # 驗證這些參數會正確轉換為移動停利觸發點
            if 'unified' in tp_ranges:
                for tp in tp_ranges['unified']:
                    logger.info(f"   統一停利 {tp} 點 -> 移動停利觸發點: {max(15, tp-20)}, {tp}, {tp+15}")
                    
            if 'individual' in tp_ranges:
                for tp in tp_ranges['individual']:
                    logger.info(f"   獨立停利 {tp} 點 -> 移動停利觸發點: {tp}")

def main():
    """主測試函數"""
    logger.info("🎯 開始測試移動停利功能整合")
    
    try:
        test_config_conversion()
        print("\n" + "="*60)
        
        test_gui_config_conversion()
        print("\n" + "="*60)
        
        test_original_strategy_compatibility()
        print("\n" + "="*60)
        
        test_parameter_mapping()
        print("\n" + "="*60)
        
        logger.info("🎊 所有測試完成！")
        
    except Exception as e:
        logger.error(f"❌ 測試失敗: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
