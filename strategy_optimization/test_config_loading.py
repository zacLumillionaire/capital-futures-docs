#!/usr/bin/env python3
"""
測試配置載入問題
"""

import logging
from time_interval_config import TimeIntervalConfig

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def test_config_loading():
    """測試配置載入"""
    logger.info("🧪 測試配置載入")
    
    try:
        config_manager = TimeIntervalConfig()
        
        # 測試 list_available_configs
        logger.info("📋 測試 list_available_configs:")
        configs = config_manager.list_available_configs()
        
        for name, info in configs.items():
            logger.info(f"✅ 配置: {name}")
            logger.info(f"   名稱: {info.get('name', 'N/A')}")
            logger.info(f"   描述: {info.get('description', 'N/A')}")
            logger.info(f"   時間區間數: {len(info.get('time_intervals', []))}")
            logger.info(f"   預估實驗數: {info.get('estimated_experiments', 'N/A')}")
            print()
        
        # 測試 focused_mdd 配置載入
        logger.info("🎯 測試 focused_mdd 配置載入:")
        focused_config = config_manager.get_config('focused_mdd')
        
        logger.info(f"✅ 成功載入 focused_mdd 配置")
        logger.info(f"   分析模式: {focused_config.get('analysis_mode')}")
        logger.info(f"   時間區間: {focused_config.get('time_intervals')}")
        logger.info(f"   停損範圍: {focused_config.get('stop_loss_ranges')}")
        logger.info(f"   停損模式: {focused_config.get('stop_loss_modes')}")
        logger.info(f"   移動停利配置: {focused_config.get('trailing_stop_config')}")
        
    except Exception as e:
        logger.error(f"❌ 測試失敗: {e}")
        import traceback
        traceback.print_exc()

def test_interactive_flow():
    """測試互動流程"""
    logger.info("🧪 測試互動流程")
    
    try:
        # 模擬 run_time_interval_analysis.py 的邏輯
        from time_interval_config import TimeIntervalConfig
        
        config_manager = TimeIntervalConfig()
        configs = config_manager.list_available_configs()
        
        logger.info("📋 可用的配置:")
        for name, info in configs.items():
            logger.info(f"🔹 {name}")
            logger.info(f"   名稱: {info['name']}")
            logger.info(f"   描述: {info['description']}")
            logger.info(f"   時間區間: {len(info['time_intervals'])} 個")
            logger.info(f"   預估實驗數: {info.get('estimated_experiments', 'N/A')}")
            print()
        
        # 測試 focused_mdd 配置的停損模式選擇
        config_name = 'focused_mdd'
        config = config_manager.get_config(config_name)
        
        if config.get('stop_loss_modes'):
            logger.info(f"🛡️ {config_name} 的停損模式:")
            
            available_modes = []
            if config['stop_loss_modes'].get('range_boundary', False):
                available_modes.append(('range_boundary', '區間邊緣停損 (原策略預設)'))
            if config['stop_loss_modes'].get('fixed_points', False):
                available_modes.append(('fixed_points', '固定點數停損'))
            
            for i, (mode, desc) in enumerate(available_modes, 1):
                logger.info(f"   {i}. {desc}")
            
            logger.info("   3. 兩種模式都測試")
            
            # 模擬選擇兩種模式都測試
            selected_modes = [mode[0] for mode in available_modes]
            logger.info(f"✅ 模擬選擇: {', '.join(selected_modes)}")
        
    except Exception as e:
        logger.error(f"❌ 互動流程測試失敗: {e}")
        import traceback
        traceback.print_exc()

def main():
    """主測試函數"""
    logger.info("🎯 開始測試配置載入問題")
    
    test_config_loading()
    print("\n" + "="*60)
    
    test_interactive_flow()
    print("\n" + "="*60)
    
    logger.info("🎊 測試完成！")

if __name__ == "__main__":
    main()
