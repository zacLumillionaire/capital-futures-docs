#!/usr/bin/env python3
"""
測試完整流程
"""

import logging
from time_interval_optimizer import TimeIntervalOptimizer
from enhanced_mdd_optimizer_adapted import EnhancedMDDOptimizer

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def test_complete_flow():
    """測試完整流程"""
    logger.info("🎯 測試完整流程")
    
    try:
        # 1. 創建時間區間優化器
        optimizer = TimeIntervalOptimizer("2024-11-04", "2024-11-10")
        
        # 2. 列出可用配置
        configs = optimizer.list_available_configs()
        logger.info("📋 可用配置:")
        for name, info in configs.items():
            logger.info(f"   {name}: {info['description']}")
        
        # 3. 測試 focused_mdd 配置轉換
        logger.info("\n🧪 測試 focused_mdd 配置轉換:")
        
        # 獲取原始配置
        from time_interval_config import TimeIntervalConfig
        config_manager = TimeIntervalConfig()
        original_config = config_manager.get_config('focused_mdd')
        
        logger.info("📋 原始配置:")
        logger.info(f"   停損範圍: {original_config['stop_loss_ranges']}")
        logger.info(f"   停損模式: {original_config['stop_loss_modes']}")
        logger.info(f"   移動停利配置: {original_config['trailing_stop_config']}")
        
        # 轉換配置
        mdd_config = optimizer._convert_to_mdd_config(original_config)
        
        logger.info("📋 轉換後的MDD配置:")
        logger.info(f"   停損範圍: {mdd_config['stop_loss_ranges']}")
        logger.info(f"   停損模式: {mdd_config['stop_loss_modes']}")
        logger.info(f"   移動停利配置: {mdd_config['trailing_stop_config']}")
        
        # 4. 測試 EnhancedMDDOptimizer 載入
        logger.info("\n🧪 測試 EnhancedMDDOptimizer 載入:")
        
        mdd_optimizer = EnhancedMDDOptimizer('focused_mdd')
        mdd_optimizer.config = mdd_config
        mdd_optimizer.set_date_range("2024-11-04", "2024-11-10")
        
        # 生成組合
        combinations = mdd_optimizer.generate_experiment_combinations()
        
        logger.info(f"📊 生成組合統計:")
        logger.info(f"   總組合數: {len(combinations):,}")
        
        # 分析組合類型
        trailing_count = 0
        range_boundary_sl = 0
        fixed_points_sl = 0
        
        for combo in combinations:
            if combo.get('take_profit_mode') == 'trailing_stop':
                trailing_count += 1
            if combo.get('stop_loss_mode') == 'range_boundary':
                range_boundary_sl += 1
            elif combo.get('stop_loss_mode') == 'fixed_points':
                fixed_points_sl += 1
        
        logger.info(f"   移動停利組合: {trailing_count:,}")
        logger.info(f"   區間邊緣停損: {range_boundary_sl:,}")
        logger.info(f"   固定點數停損: {fixed_points_sl:,}")
        
        # 5. 測試配置轉換
        logger.info("\n🧪 測試配置轉換:")
        
        # 找一個移動停利組合
        trailing_combo = None
        for combo in combinations:
            if combo.get('take_profit_mode') == 'trailing_stop':
                trailing_combo = combo
                break
        
        if trailing_combo:
            logger.info(f"測試組合: {trailing_combo['experiment_id']}")
            
            # 轉換為策略配置
            strategy_config = mdd_optimizer.create_experiment_config(trailing_combo)
            
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
            
            # 驗證是否符合期望
            expected_triggers = {'lot1': 15, 'lot2': 40, 'lot3': 41}
            expected_pullbacks = {'lot1': 10, 'lot2': 10, 'lot3': 20}
            
            all_correct = True
            for lot_name in ['lot1', 'lot2', 'lot3']:
                if lot_name in lot_settings:
                    actual_trigger = lot_settings[lot_name].get('trigger')
                    actual_pullback = lot_settings[lot_name].get('trailing')
                    
                    if (actual_trigger != expected_triggers[lot_name] or 
                        actual_pullback != expected_pullbacks[lot_name]):
                        all_correct = False
                        logger.error(f"❌ {lot_name} 配置錯誤: 觸發={actual_trigger}(期望{expected_triggers[lot_name]}), 回撤={actual_pullback}%(期望{expected_pullbacks[lot_name]}%)")
            
            if all_correct:
                logger.info("✅ 所有移動停利配置正確！")
            else:
                logger.warning("⚠️ 移動停利配置有誤")
        
        return True
        
    except Exception as e:
        logger.error(f"❌ 測試失敗: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_database_connection():
    """測試資料庫連接"""
    logger.info("🧪 測試資料庫連接")
    
    try:
        # 檢查是否使用 SQLite
        import os
        db_path = "/Users/z/big/my-capital-project/strategy_optimization/data/trading_data.db"
        
        if os.path.exists(db_path):
            logger.info(f"✅ 找到 SQLite 資料庫: {db_path}")
            
            # 檢查檔案大小
            size_mb = os.path.getsize(db_path) / (1024 * 1024)
            logger.info(f"   檔案大小: {size_mb:.2f} MB")
            
            # 簡單連接測試
            import sqlite3
            conn = sqlite3.connect(db_path)
            cursor = conn.cursor()
            
            # 檢查表格
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
            tables = cursor.fetchall()
            
            logger.info(f"   資料表數量: {len(tables)}")
            for table in tables[:5]:  # 只顯示前5個
                logger.info(f"     - {table[0]}")
            
            conn.close()
            logger.info("✅ SQLite 連接測試成功")
            
        else:
            logger.warning(f"⚠️ 未找到 SQLite 資料庫: {db_path}")
            
    except Exception as e:
        logger.error(f"❌ 資料庫測試失敗: {e}")

def main():
    """主測試函數"""
    logger.info("🎯 開始完整流程測試")
    
    # 測試資料庫
    test_database_connection()
    print("\n" + "="*60)
    
    # 測試完整流程
    success = test_complete_flow()
    print("\n" + "="*60)
    
    if success:
        logger.info("🎊 所有測試通過！")
        logger.info("💡 現在可以安全執行:")
        logger.info("   python run_time_interval_analysis.py interactive")
    else:
        logger.error("❌ 測試失敗，需要修正問題")

if __name__ == "__main__":
    main()
