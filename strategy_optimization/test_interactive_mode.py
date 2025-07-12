#!/usr/bin/env python3
"""
測試互動模式的停損模式選擇功能
"""

import logging
from time_interval_config import TimeIntervalConfig

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def test_stop_loss_mode_selection():
    """測試停損模式選擇功能"""
    logger.info("🧪 測試停損模式選擇功能")
    
    try:
        time_config = TimeIntervalConfig()
        config = time_config.get_config('focused_mdd')
        
        logger.info("✅ 成功載入 focused_mdd 配置")
        
        if config.get('stop_loss_modes'):
            logger.info("✅ 找到停損模式配置:")
            
            available_modes = []
            if config['stop_loss_modes'].get('range_boundary', False):
                available_modes.append(('range_boundary', '區間邊緣停損 (原策略預設)'))
                logger.info("   ✅ 支援區間邊緣停損")
            if config['stop_loss_modes'].get('fixed_points', False):
                available_modes.append(('fixed_points', '固定點數停損'))
                logger.info("   ✅ 支援固定點數停損")
            
            logger.info(f"   總共支援 {len(available_modes)} 種停損模式")
            
            # 模擬用戶選擇
            logger.info("📋 模擬用戶選擇:")
            
            # 選擇1: 只使用區間邊緣停損
            selected_modes_1 = ['range_boundary']
            logger.info(f"   選擇1: {selected_modes_1}")
            
            # 選擇2: 只使用固定點數停損
            selected_modes_2 = ['fixed_points']
            logger.info(f"   選擇2: {selected_modes_2}")
            
            # 選擇3: 兩種模式都測試
            selected_modes_3 = [mode[0] for mode in available_modes]
            logger.info(f"   選擇3: {selected_modes_3}")
            
        else:
            logger.warning("⚠️ 未找到停損模式配置")
            
    except Exception as e:
        logger.error(f"❌ 測試失敗: {e}")
        import traceback
        traceback.print_exc()

def test_config_compatibility():
    """測試配置兼容性"""
    logger.info("🧪 測試配置兼容性")
    
    try:
        time_config = TimeIntervalConfig()
        
        # 測試所有可用配置
        configs = ['quick_test', 'comprehensive', 'focused_mdd', 'custom_intervals']
        
        for config_name in configs:
            try:
                config = time_config.get_config(config_name)
                has_stop_loss_modes = 'stop_loss_modes' in config
                has_analysis_mode = config.get('analysis_mode') == 'per_time_interval'
                
                logger.info(f"✅ 配置 {config_name}:")
                logger.info(f"   停損模式支援: {'是' if has_stop_loss_modes else '否'}")
                logger.info(f"   時間區間分析: {'是' if has_analysis_mode else '否'}")
                
                if has_stop_loss_modes:
                    modes = config['stop_loss_modes']
                    logger.info(f"   支援的停損模式: {list(modes.keys())}")
                
            except Exception as e:
                logger.warning(f"⚠️ 配置 {config_name} 載入失敗: {e}")
                
    except Exception as e:
        logger.error(f"❌ 測試失敗: {e}")

def main():
    """主測試函數"""
    logger.info("🎯 開始測試互動模式停損選擇功能")
    
    test_stop_loss_mode_selection()
    print("\n" + "="*60)
    
    test_config_compatibility()
    print("\n" + "="*60)
    
    logger.info("🎊 所有測試完成！")

if __name__ == "__main__":
    main()
