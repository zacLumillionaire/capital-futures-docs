#!/usr/bin/env python3
"""
測試用戶自定義配置
驗證新的 user_custom 配置是否正常工作
"""

import sys
from pathlib import Path
from mdd_search_config import MDDSearchConfig
from enhanced_mdd_optimizer import EnhancedMDDOptimizer

def test_user_custom_config():
    """測試用戶自定義配置"""
    print("🧪 測試用戶自定義配置...")
    
    # 測試配置載入
    try:
        config = MDDSearchConfig.get_user_custom_search_config()
        print("✅ 用戶自定義配置載入成功")
        
        # 顯示配置詳情
        print("\n📊 配置詳情:")
        print(f"   第1口停損範圍: {config['stop_loss_ranges']['lot1']}")
        print(f"   第2口停損範圍: {config['stop_loss_ranges']['lot2']}")
        print(f"   第3口停損範圍: {config['stop_loss_ranges']['lot3']}")
        print(f"   統一停利範圍: {config['take_profit_ranges']['unified']}")
        print(f"   時間區間數量: {len(config['time_intervals'])}")
        print(f"   時間區間: {config['time_intervals']}")
        print(f"   預估組合數 (統一停利): {config['estimated_combinations']['unified']:,}")
        print(f"   預估組合數 (獨立停利): {config['estimated_combinations']['individual']:,}")
        
    except Exception as e:
        print(f"❌ 配置載入失敗: {e}")
        return False
    
    # 測試優化器初始化
    try:
        optimizer = EnhancedMDDOptimizer('user_custom')
        print("✅ 增強版優化器初始化成功")
        
        # 測試組合生成
        combinations = optimizer.generate_experiment_combinations(individual_tp=False)
        print(f"✅ 生成 {len(combinations)} 個實驗組合")
        
        # 顯示前3個組合示例
        print("\n📋 前3個實驗組合示例:")
        for i, combo in enumerate(combinations[:3]):
            print(f"   {i+1}. {combo}")
            
    except Exception as e:
        print(f"❌ 優化器測試失敗: {e}")
        return False
    
    print("\n🎉 用戶自定義配置測試完成！")
    return True

def show_all_configs():
    """顯示所有可用配置"""
    print("\n📊 所有可用配置:")
    print("=" * 60)
    
    configs = ['quick', 'detailed', 'focused', 'time_focus', 'user_custom']
    
    for config_name in configs:
        try:
            config = MDDSearchConfig.get_config_by_name(config_name)
            print(f"\n🎯 {config_name.upper()} 配置:")
            print(f"   停損範圍: L1={len(config['stop_loss_ranges']['lot1'])}, "
                  f"L2={len(config['stop_loss_ranges']['lot2'])}, "
                  f"L3={len(config['stop_loss_ranges']['lot3'])}")
            print(f"   時間區間: {len(config['time_intervals'])} 個")
            print(f"   預估組合數:")
            print(f"     統一停利: {config['estimated_combinations']['unified']:,}")
            if 'individual' in config['estimated_combinations']:
                print(f"     獨立停利: {config['estimated_combinations']['individual']:,}")
        except Exception as e:
            print(f"❌ {config_name} 配置載入失敗: {e}")

if __name__ == "__main__":
    print("🚀 用戶自定義 MDD 配置測試")
    print("=" * 50)
    
    # 測試用戶自定義配置
    success = test_user_custom_config()
    
    # 顯示所有配置
    show_all_configs()
    
    if success:
        print("\n✅ 所有測試通過！可以開始使用 user_custom 配置")
        print("\n🎯 使用方法:")
        print("python enhanced_mdd_optimizer.py --config user_custom --sample-size 100")
    else:
        print("\n❌ 測試失敗，請檢查配置")
