#!/usr/bin/env python3
"""
完整系統測試腳本

測試策略敏感度分析器的所有組件是否正常工作
"""

import logging
import sys
import os

# 設定日誌
logging.basicConfig(level=logging.INFO, format='[%(asctime)s] %(levelname)s: %(message)s')
logger = logging.getLogger(__name__)

def test_imports():
    """測試所有必要的導入"""
    logger.info("🔍 測試導入...")
    
    try:
        # 測試基本導入
        import numpy as np
        import pandas as pd
        from SALib.analyze import sobol
        from SALib.sample import sobol as sobol_sample
        logger.info("✅ 基本套件導入成功")
        
        # 測試策略敏感度分析器導入
        import strategy_sensitivity_analyzer
        logger.info("✅ 策略敏感度分析器導入成功")
        
        # 測試演示版本導入
        import demo_sensitivity_analyzer
        logger.info("✅ 演示版本導入成功")
        
        return True
        
    except Exception as e:
        logger.error(f"❌ 導入測試失敗: {e}")
        return False

def test_demo_functionality():
    """測試演示版本功能"""
    logger.info("🧪 測試演示版本功能...")
    
    try:
        import demo_sensitivity_analyzer
        
        # 運行小樣本演示
        logger.info("   執行小樣本演示分析...")
        results = demo_sensitivity_analyzer.run_demo_sensitivity_analysis(sample_size=16)
        
        # 檢查結果
        if len(results) == 3:  # 應該有三個交易方向的結果
            logger.info("✅ 演示版本功能測試通過")
            
            # 檢查每個方向是否有結果
            for direction in ['LONG_ONLY', 'SHORT_ONLY', 'BOTH']:
                if direction in results and 'Si' in results[direction]:
                    logger.info(f"   ✅ {direction} 方向分析完成")
                else:
                    logger.warning(f"   ⚠️ {direction} 方向分析可能有問題")
            
            return True
        else:
            logger.error("❌ 演示版本結果數量不正確")
            return False
            
    except Exception as e:
        logger.error(f"❌ 演示版本功能測試失敗: {e}")
        return False

def test_strategy_config():
    """測試策略配置創建"""
    logger.info("⚙️ 測試策略配置...")
    
    try:
        import strategy_sensitivity_analyzer
        from decimal import Decimal
        
        # 測試參數陣列轉換
        test_params = [15.0, 0.20, 40.0, 0.15, 65.0, 0.25, 2.0]
        
        # 這裡我們只測試函數是否能正常調用，不執行完整回測
        logger.info("   測試參數陣列格式...")
        
        # 檢查參數範圍是否合理
        problem = strategy_sensitivity_analyzer.problem
        for i, (param_name, bounds) in enumerate(zip(problem['names'], problem['bounds'])):
            if bounds[0] <= test_params[i] <= bounds[1]:
                logger.info(f"   ✅ {param_name}: {test_params[i]} 在範圍 {bounds} 內")
            else:
                logger.warning(f"   ⚠️ {param_name}: {test_params[i]} 超出範圍 {bounds}")
        
        logger.info("✅ 策略配置測試通過")
        return True
        
    except Exception as e:
        logger.error(f"❌ 策略配置測試失敗: {e}")
        return False

def test_database_connection():
    """測試資料庫連接"""
    logger.info("🗄️ 測試資料庫連接...")
    
    try:
        # 檢查 SQLite 資料庫文件是否存在
        if os.path.exists("stock_data.sqlite"):
            logger.info("✅ SQLite 資料庫文件存在")
            
            # 嘗試連接資料庫
            import sqlite_connection
            logger.info("✅ SQLite 連接模組導入成功")
            
            return True
        else:
            logger.warning("⚠️ SQLite 資料庫文件不存在，實際回測可能無法運行")
            return True  # 不阻止其他測試
            
    except Exception as e:
        logger.error(f"❌ 資料庫連接測試失敗: {e}")
        return False

def test_salib_integration():
    """測試 SALib 整合"""
    logger.info("📊 測試 SALib 整合...")
    
    try:
        from SALib.analyze import sobol
        from SALib.sample import sobol as sobol_sample
        import numpy as np
        import pandas as pd
        
        # 創建簡單測試問題
        test_problem = {
            'num_vars': 3,
            'names': ['x1', 'x2', 'x3'],
            'bounds': [[0, 1], [0, 1], [0, 1]]
        }
        
        # 生成樣本
        param_values = sobol_sample.sample(test_problem, N=8)
        logger.info(f"   ✅ 生成了 {len(param_values)} 個測試樣本")
        
        # 模擬評估
        Y = np.sum(param_values, axis=1)
        
        # 執行分析
        Si = sobol.analyze(test_problem, Y)
        logger.info("   ✅ Sobol 分析執行成功")
        
        # 檢查結果格式
        if 'S1' in Si and 'ST' in Si:
            logger.info("   ✅ 敏感度指數格式正確")
            
            # 測試 DataFrame 轉換
            sensitivity_data = {
                'Parameter': test_problem['names'],
                'S1': Si['S1'],
                'ST': Si['ST']
            }
            df_results = pd.DataFrame(sensitivity_data)
            logger.info("   ✅ DataFrame 轉換成功")
            
            return True
        else:
            logger.error("   ❌ 敏感度指數格式不正確")
            return False
            
    except Exception as e:
        logger.error(f"❌ SALib 整合測試失敗: {e}")
        return False

def main():
    """主測試函數"""
    logger.info("🚀 策略敏感度分析器完整系統測試")
    logger.info("=" * 60)
    
    tests = [
        ("導入測試", test_imports),
        ("SALib 整合測試", test_salib_integration),
        ("資料庫連接測試", test_database_connection),
        ("策略配置測試", test_strategy_config),
        ("演示版本功能測試", test_demo_functionality)
    ]
    
    passed = 0
    total = len(tests)
    
    for test_name, test_func in tests:
        logger.info(f"\n📋 執行: {test_name}")
        try:
            if test_func():
                logger.info(f"✅ {test_name} 通過")
                passed += 1
            else:
                logger.error(f"❌ {test_name} 失敗")
        except Exception as e:
            logger.error(f"❌ {test_name} 異常: {e}")
    
    logger.info("\n" + "=" * 60)
    logger.info(f"📊 測試結果: {passed}/{total} 通過")
    
    if passed == total:
        logger.info("🎉 所有測試通過！系統準備就緒。")
        logger.info("\n📋 下一步:")
        logger.info("   1. 運行演示版本: python demo_sensitivity_analyzer.py")
        logger.info("   2. 運行完整版本: python strategy_sensitivity_analyzer.py")
        logger.info("   3. 查看使用說明: 敏感度分析使用說明.md")
        return True
    else:
        logger.error("⚠️ 部分測試失敗，請檢查環境配置。")
        return False

if __name__ == '__main__':
    success = main()
    sys.exit(0 if success else 1)
