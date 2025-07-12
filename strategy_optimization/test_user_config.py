#!/usr/bin/env python3
"""
測試用戶的MDD優化配置
"""

import logging
from enhanced_mdd_optimizer_adapted import EnhancedMDDOptimizer
from time_interval_config import TimeIntervalConfig

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def test_user_mdd_config():
    """測試用戶的MDD配置"""
    logger.info("🎯 測試用戶的MDD優化配置")
    
    # 1. 檢查配置
    time_config = TimeIntervalConfig()
    config = time_config.get_config('focused_mdd')
    
    logger.info("📋 配置檢查:")
    logger.info(f"   分析模式: {config.get('analysis_mode')}")
    logger.info(f"   時間區間: {config.get('time_intervals')}")
    logger.info(f"   停損範圍: {config.get('stop_loss_ranges')}")
    logger.info(f"   停損模式: {config.get('stop_loss_modes')}")
    logger.info(f"   停利範圍: {config.get('take_profit_ranges')}")
    logger.info(f"   移動停利配置: {config.get('trailing_stop_config')}")
    
    # 2. 初始化優化器
    optimizer = EnhancedMDDOptimizer('focused_mdd')
    optimizer.set_date_range("2024-11-04", "2024-11-10")
    
    # 3. 生成實驗組合
    combinations = optimizer.generate_experiment_combinations()
    
    logger.info(f"\n📊 實驗組合統計:")
    logger.info(f"   總組合數: {len(combinations):,}")
    
    # 分析組合類型
    trailing_stop_count = 0
    range_boundary_sl_count = 0
    fixed_points_sl_count = 0
    
    for combo in combinations:
        if combo.get('take_profit_mode') == 'trailing_stop':
            trailing_stop_count += 1
        if combo.get('stop_loss_mode') == 'range_boundary':
            range_boundary_sl_count += 1
        elif combo.get('stop_loss_mode') == 'fixed_points':
            fixed_points_sl_count += 1
    
    logger.info(f"   移動停利組合: {trailing_stop_count:,}")
    logger.info(f"   區間邊緣停損: {range_boundary_sl_count:,}")
    logger.info(f"   固定點數停損: {fixed_points_sl_count:,}")
    
    # 4. 測試配置轉換
    logger.info(f"\n🧪 測試配置轉換:")
    
    # 找一個移動停利的組合來測試
    trailing_combo = None
    for combo in combinations:
        if combo.get('take_profit_mode') == 'trailing_stop':
            trailing_combo = combo
            break
    
    if trailing_combo:
        logger.info(f"測試組合: {trailing_combo['experiment_id']}")
        
        # 轉換為策略配置
        strategy_config = optimizer.create_experiment_config(trailing_combo)
        
        # 檢查移動停利設定
        lot_settings = strategy_config.get('lot_settings', {})
        
        logger.info("✅ 移動停利配置:")
        for lot_name in ['lot1', 'lot2', 'lot3']:
            if lot_name in lot_settings:
                lot_config = lot_settings[lot_name]
                trigger = lot_config.get('trigger', 'N/A')
                trailing = lot_config.get('trailing', 'N/A')
                logger.info(f"   {lot_name}: 觸發={trigger}, 回撤={trailing}%")
        
        # 檢查停損設定
        stop_loss_filter = strategy_config['filters']['stop_loss_filter']
        logger.info(f"✅ 停損配置:")
        logger.info(f"   停損類型: {stop_loss_filter['stop_loss_type']}")
        if stop_loss_filter['stop_loss_type'] == 'fixed_points':
            logger.info(f"   固定停損點數: {stop_loss_filter.get('fixed_stop_loss_points', 'N/A')}")
    
    return combinations[:3]  # 返回前3個組合

def test_expected_configuration():
    """測試期望的配置是否正確"""
    logger.info("🎯 測試期望配置")
    
    # 您期望的移動停利配置
    expected_config = {
        'lot1': {'trigger': 15, 'pullback_pct': 10},
        'lot2': {'trigger': 40, 'pullback_pct': 10}, 
        'lot3': {'trigger': 41, 'pullback_pct': 20}
    }
    
    logger.info("📋 期望的移動停利配置:")
    for lot, config in expected_config.items():
        logger.info(f"   {lot}: 觸發點={config['trigger']}, 回撤={config['pullback_pct']}%")
    
    # 檢查配置文件中的設定
    time_config = TimeIntervalConfig()
    config = time_config.get_config('focused_mdd')
    actual_config = config.get('trailing_stop_config', {})
    
    logger.info("📋 實際配置文件中的設定:")
    for lot, config in actual_config.items():
        logger.info(f"   {lot}: 觸發點={config.get('trigger')}, 回撤={config.get('pullback_pct')}%")
    
    # 驗證是否一致
    match = True
    for lot in ['lot1', 'lot2', 'lot3']:
        expected = expected_config[lot]
        actual = actual_config.get(lot, {})
        
        if (expected['trigger'] != actual.get('trigger') or 
            expected['pullback_pct'] != actual.get('pullback_pct')):
            match = False
            logger.error(f"❌ {lot} 配置不匹配")
    
    if match:
        logger.info("✅ 配置完全匹配！")
    else:
        logger.warning("⚠️ 配置不匹配，需要調整")

def main():
    """主測試函數"""
    logger.info("🎯 開始測試用戶MDD優化配置")
    
    test_expected_configuration()
    print("\n" + "="*60)
    
    sample_combinations = test_user_mdd_config()
    print("\n" + "="*60)
    
    logger.info("🎊 測試完成！")
    logger.info("💡 建議執行命令:")
    logger.info("   python run_time_interval_analysis.py interactive")
    logger.info("   選擇 focused_mdd 配置")
    logger.info("   選擇停損模式（建議選擇兩種都測試）")

if __name__ == "__main__":
    main()
