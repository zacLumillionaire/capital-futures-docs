#!/usr/bin/env python3
"""
時間區間分析執行腳本
簡化的執行介面，方便用戶快速開始分析
"""

import logging
import sys
from datetime import datetime, timedelta

# 設置日誌
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)

def show_available_configs():
    """顯示可用的配置"""
    try:
        from time_interval_config import TimeIntervalConfig
        
        config_manager = TimeIntervalConfig()
        configs = config_manager.list_available_configs()
        
        print("\n📋 可用的配置:")
        print("=" * 60)
        for name, info in configs.items():
            print(f"🔹 {name}")
            print(f"   名稱: {info['name']}")
            print(f"   描述: {info['description']}")
            print(f"   時間區間: {len(info['time_intervals'])} 個")
            print(f"   預估實驗數: {info.get('estimated_experiments', 'N/A')}")
            print()
            
    except Exception as e:
        logger.error(f"❌ 無法載入配置: {e}")

def run_analysis_interactive():
    """互動式執行分析"""
    print("\n🎯 時間區間MDD分析 - 互動式執行")
    print("=" * 50)
    
    # 顯示可用配置
    show_available_configs()
    
    # 選擇配置
    config_name = input("請選擇配置名稱 (預設: focused_mdd): ").strip()
    if not config_name:
        config_name = 'focused_mdd'

    # 檢查配置是否支援停損模式選擇
    try:
        from time_interval_config import TimeIntervalConfig
        time_config = TimeIntervalConfig()
        config = time_config.get_config(config_name)

        if config.get('stop_loss_modes'):
            print(f"\n🛡️ 停損模式選擇")
            print("可用的停損模式:")

            available_modes = []
            if config['stop_loss_modes'].get('range_boundary', False):
                available_modes.append(('range_boundary', '區間邊緣停損 (原策略預設)'))
            if config['stop_loss_modes'].get('fixed_points', False):
                available_modes.append(('fixed_points', '固定點數停損'))

            for i, (mode, desc) in enumerate(available_modes, 1):
                print(f"{i}. {desc}")

            if len(available_modes) > 1:
                print("3. 兩種模式都測試")

                mode_choice = input(f"請選擇停損模式 (1-3, 預設: 3): ").strip()
                if mode_choice == '1':
                    selected_modes = [available_modes[0][0]]
                elif mode_choice == '2':
                    selected_modes = [available_modes[1][0]]
                else:
                    selected_modes = [mode[0] for mode in available_modes]

                print(f"✅ 已選擇停損模式: {', '.join(selected_modes)}")
            else:
                selected_modes = [available_modes[0][0]]
                print(f"✅ 使用停損模式: {selected_modes[0]}")
        else:
            selected_modes = ['fixed_points']  # 預設值

    except Exception as e:
        logger.warning(f"⚠️ 無法載入配置停損模式設定: {e}")
        selected_modes = ['fixed_points']
    
    # 設置日期範圍
    print(f"\n📅 設置回測日期範圍")
    start_date = input("開始日期 (YYYY-MM-DD, 預設: 2024-11-04): ").strip()
    if not start_date:
        start_date = '2024-11-04'
    
    end_date = input("結束日期 (YYYY-MM-DD, 預設: 2024-12-31): ").strip()
    if not end_date:
        end_date = '2024-12-31'
    
    # 設置執行參數
    print(f"\n⚙️ 設置執行參數")
    max_workers = input("並行進程數 (預設: 2): ").strip()
    max_workers = int(max_workers) if max_workers else 2
    
    sample_size = input("樣本大小 (預設: 50, 輸入0表示全部): ").strip()
    sample_size = int(sample_size) if sample_size else 50
    if sample_size == 0:
        sample_size = None
    
    # 確認執行
    print(f"\n✅ 執行確認")
    print(f"配置: {config_name}")
    print(f"停損模式: {', '.join(selected_modes)}")
    print(f"日期範圍: {start_date} 到 {end_date}")
    print(f"並行進程: {max_workers}")
    print(f"樣本大小: {sample_size if sample_size else '全部'}")
    
    confirm = input("\n是否開始執行? (y/N): ").strip().lower()
    if confirm != 'y':
        print("❌ 已取消執行")
        return
    
    # 執行分析
    try:
        from experiment_controller import ExperimentController
        
        print(f"\n🚀 開始執行時間區間分析...")
        controller = ExperimentController()
        
        result = controller.run_time_interval_analysis(
            config_name=config_name,
            max_workers=max_workers,
            sample_size=sample_size,
            start_date=start_date,
            end_date=end_date
        )
        
        print(f"\n🎊 分析完成！")
        print(f"📊 報告文件: {result.get('report_file', 'N/A')}")
        print(f"📈 成功實驗: {result.get('successful_experiments', 0)}")
        print(f"📋 總實驗數: {result.get('total_experiments', 0)}")
        
    except Exception as e:
        logger.error(f"❌ 分析執行失敗: {e}")
        print(f"\n❌ 執行失敗: {e}")

def run_analysis_quick():
    """快速執行分析（使用預設參數）"""
    print("\n🚀 快速執行時間區間分析")
    print("使用預設參數: quick_test 配置")
    
    try:
        from experiment_controller import ExperimentController
        
        controller = ExperimentController()
        
        result = controller.run_time_interval_analysis(
            config_name='quick_test',
            max_workers=2,
            sample_size=20,  # 小樣本快速測試
            start_date='2024-11-04',
            end_date='2024-11-10'  # 短期間快速測試
        )
        
        print(f"\n🎊 快速分析完成！")
        print(f"📊 報告文件: {result.get('report_file', 'N/A')}")
        
    except Exception as e:
        logger.error(f"❌ 快速分析失敗: {e}")
        print(f"\n❌ 執行失敗: {e}")

def run_analysis_standard():
    """標準分析執行"""
    print("\n📊 執行標準時間區間分析")
    print("使用 standard_analysis 配置")
    
    try:
        from experiment_controller import ExperimentController
        
        controller = ExperimentController()
        
        result = controller.run_time_interval_analysis(
            config_name='standard_analysis',
            max_workers=4,
            sample_size=100,
            start_date='2024-11-04',
            end_date='2024-12-31'
        )
        
        print(f"\n🎊 標準分析完成！")
        print(f"📊 報告文件: {result.get('report_file', 'N/A')}")
        
    except Exception as e:
        logger.error(f"❌ 標準分析失敗: {e}")
        print(f"\n❌ 執行失敗: {e}")

def main():
    """主函數"""
    print("🎯 時間區間MDD分析執行器")
    print("=" * 40)
    
    if len(sys.argv) > 1:
        mode = sys.argv[1].lower()
    else:
        print("\n請選擇執行模式:")
        print("1. 互動式執行 (推薦)")
        print("2. 快速測試")
        print("3. 標準分析")
        print("4. 查看可用配置")
        
        choice = input("\n請輸入選項 (1-4): ").strip()
        
        if choice == '1':
            mode = 'interactive'
        elif choice == '2':
            mode = 'quick'
        elif choice == '3':
            mode = 'standard'
        elif choice == '4':
            mode = 'configs'
        else:
            print("❌ 無效選項")
            return
    
    if mode == 'interactive':
        run_analysis_interactive()
    elif mode == 'quick':
        run_analysis_quick()
    elif mode == 'standard':
        run_analysis_standard()
    elif mode == 'configs':
        show_available_configs()
    else:
        print(f"❌ 未知模式: {mode}")
        print("可用模式: interactive, quick, standard, configs")

if __name__ == "__main__":
    main()
