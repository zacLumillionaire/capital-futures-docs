#!/usr/bin/env python3
"""
自定義時間區間配置範例
展示如何創建和使用自定義的時間區間配置
"""

from time_interval_config import TimeIntervalConfig
from experiment_controller import ExperimentController
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def create_morning_focus_config():
    """創建專注早盤的配置"""
    config_manager = TimeIntervalConfig()
    
    morning_config = config_manager.create_custom_config(
        name="早盤專注分析",
        description="專注於早盤時段的深度分析",
        time_intervals=[
            ("09:00", "09:02"),  # 開盤
            ("09:15", "09:17"),  # 開盤後穩定
            ("09:30", "09:32"),  # 早盤活躍
            ("09:45", "09:47"),  # 早盤中段
            ("10:00", "10:02"),  # 早盤後段
        ],
        stop_loss_ranges={
            'lot1': [15, 20, 25],      # 較保守的停損
            'lot2': [20, 25, 30],      
            'lot3': [25, 30, 35]       
        },
        take_profit_ranges={
            'unified': [40, 50, 60],           # 早盤波動較大，停利可設較高
            'individual': [30, 40, 50, 60]     
        },
        optimization_target='mdd_minimization'
    )
    
    logger.info(f"✅ 創建早盤配置: {morning_config['name']}")
    return morning_config

def create_afternoon_focus_config():
    """創建專注午後的配置"""
    config_manager = TimeIntervalConfig()
    
    afternoon_config = config_manager.create_custom_config(
        name="午後專注分析", 
        description="專注於午後時段的分析",
        time_intervals=[
            ("12:30", "12:32"),  # 午後開始
            ("13:00", "13:02"),  # 午後活躍
            ("13:15", "13:17"),  # 午後中段
            ("13:30", "13:32"),  # 尾盤準備
            ("13:45", "13:47"),  # 尾盤
        ],
        stop_loss_ranges={
            'lot1': [10, 15, 20],      # 午後波動較小，可用較緊停損
            'lot2': [15, 20, 25],      
            'lot3': [20, 25, 30]       
        },
        take_profit_ranges={
            'unified': [30, 40, 50],           # 午後停利可較保守
            'individual': [25, 30, 40, 50]     
        },
        optimization_target='mdd_minimization'
    )
    
    logger.info(f"✅ 創建午後配置: {afternoon_config['name']}")
    return afternoon_config

def create_high_frequency_config():
    """創建高頻交易配置"""
    config_manager = TimeIntervalConfig()
    
    high_freq_config = config_manager.create_custom_config(
        name="高頻交易分析",
        description="短時間區間高頻交易分析", 
        time_intervals=[
            ("10:30", "10:31"),  # 1分鐘區間
            ("10:31", "10:32"),  
            ("11:30", "11:31"),  
            ("11:31", "11:32"),
            ("13:30", "13:31"),
            ("13:31", "13:32"),
        ],
        stop_loss_ranges={
            'lot1': [5, 10, 15],       # 高頻交易用較小停損
            'lot2': [10, 15, 20],      
            'lot3': [15, 20, 25]       
        },
        take_profit_ranges={
            'unified': [20, 30, 40],           # 高頻交易停利也較小
            'individual': [15, 20, 30, 40]     
        },
        optimization_target='mdd_minimization'
    )
    
    logger.info(f"✅ 創建高頻配置: {high_freq_config['name']}")
    return high_freq_config

def create_conservative_config():
    """創建保守型配置"""
    config_manager = TimeIntervalConfig()
    
    conservative_config = config_manager.create_custom_config(
        name="保守型分析",
        description="風險較低的保守型參數配置",
        time_intervals=[
            ("10:00", "10:02"),
            ("11:00", "11:02"), 
            ("12:00", "12:02"),
            ("13:00", "13:02"),
        ],
        stop_loss_ranges={
            'lot1': [20, 25, 30],      # 較大的停損空間
            'lot2': [25, 30, 35],      
            'lot3': [30, 35, 40]       
        },
        take_profit_ranges={
            'unified': [50, 60, 70, 80],       # 較大的停利目標
            'individual': [40, 50, 60, 70, 80] 
        },
        optimization_target='mdd_minimization'
    )
    
    logger.info(f"✅ 創建保守配置: {conservative_config['name']}")
    return conservative_config

def create_aggressive_config():
    """創建積極型配置"""
    config_manager = TimeIntervalConfig()
    
    aggressive_config = config_manager.create_custom_config(
        name="積極型分析",
        description="追求高收益的積極型參數配置",
        time_intervals=[
            ("09:30", "09:32"),  # 選擇波動較大的時段
            ("10:30", "10:32"),
            ("11:30", "11:32"),
            ("13:30", "13:32"),
        ],
        stop_loss_ranges={
            'lot1': [10, 15, 20],      # 較緊的停損
            'lot2': [15, 20, 25],      
            'lot3': [20, 25, 30]       
        },
        take_profit_ranges={
            'unified': [30, 40, 50],           # 較小的停利，追求高頻獲利
            'individual': [25, 30, 40, 50]     
        },
        optimization_target='mdd_minimization'
    )
    
    logger.info(f"✅ 創建積極配置: {aggressive_config['name']}")
    return aggressive_config

def run_custom_analysis_example():
    """執行自定義分析範例"""
    logger.info("🚀 開始自定義時間區間分析範例")
    
    # 創建自定義配置
    morning_config = create_morning_focus_config()
    
    # 執行分析
    try:
        controller = ExperimentController()
        
        # 注意：這裡使用動態配置，需要先將配置添加到系統中
        # 或者直接使用 TimeIntervalOptimizer
        from time_interval_optimizer import TimeIntervalOptimizer
        
        optimizer = TimeIntervalOptimizer("2024-11-04", "2024-11-10")
        
        # 將自定義配置轉換為MDD配置格式
        mdd_config = optimizer._convert_to_mdd_config(morning_config)
        
        logger.info("📊 開始執行早盤專注分析...")
        logger.info(f"時間區間數: {len(morning_config['time_intervals'])}")
        logger.info(f"預估實驗數: {morning_config.get('estimated_experiments', 'N/A')}")
        
        # 這裡可以執行實際分析
        # results = optimizer.run_time_interval_analysis_with_config(mdd_config)
        
        logger.info("✅ 自定義分析範例完成")
        
    except Exception as e:
        logger.error(f"❌ 自定義分析失敗: {e}")

def show_all_custom_configs():
    """展示所有自定義配置"""
    logger.info("📋 展示所有自定義配置範例")
    
    configs = [
        create_morning_focus_config(),
        create_afternoon_focus_config(), 
        create_high_frequency_config(),
        create_conservative_config(),
        create_aggressive_config()
    ]
    
    print("\n" + "="*60)
    print("📊 自定義配置總覽")
    print("="*60)
    
    for config in configs:
        print(f"\n🔹 {config['name']}")
        print(f"   描述: {config['description']}")
        print(f"   時間區間: {len(config['time_intervals'])} 個")
        print(f"   區間詳情: {config['time_intervals']}")
        print(f"   停損範圍: L1:{config['stop_loss_ranges']['lot1']}")
        print(f"            L2:{config['stop_loss_ranges']['lot2']}")  
        print(f"            L3:{config['stop_loss_ranges']['lot3']}")
        print(f"   統一停利: {config['take_profit_ranges']['unified']}")
        print(f"   獨立停利: {config['take_profit_ranges']['individual']}")
        print(f"   預估實驗: {config.get('estimated_experiments', 'N/A')} 個")

def main():
    """主函數"""
    print("🎯 自定義時間區間配置範例")
    print("="*40)
    
    print("\n請選擇操作:")
    print("1. 展示所有自定義配置")
    print("2. 執行早盤專注分析範例")
    print("3. 創建並保存自定義配置")
    
    choice = input("\n請輸入選項 (1-3): ").strip()
    
    if choice == '1':
        show_all_custom_configs()
    elif choice == '2':
        run_custom_analysis_example()
    elif choice == '3':
        logger.info("💡 提示：您可以修改此文件中的配置函數來創建自己的配置")
        show_all_custom_configs()
    else:
        print("❌ 無效選項")

if __name__ == "__main__":
    main()
