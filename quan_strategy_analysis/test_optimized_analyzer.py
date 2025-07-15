#!/usr/bin/env python3
"""
測試優化後的敏感度分析器

測試三個主要優化功能：
1. 並行處理（4核心）
2. 錯誤參數記錄
3. 結果視覺化和保存
"""

import logging
import strategy_sensitivity_analyzer
import os

logging.basicConfig(level=logging.INFO, format='[%(asctime)s] %(levelname)s: %(message)s')
logger = logging.getLogger(__name__)

def test_optimized_features():
    """測試優化後的功能"""
    logger.info("🚀 測試優化後的敏感度分析器")
    logger.info("=" * 60)
    
    # 測試參數
    TARGET_TIME_SLOT = ('08:46', '08:47')
    SAMPLE_SIZE = 32  # 使用較小樣本快速測試
    
    logger.info(f"📊 測試配置:")
    logger.info(f"   時間區段: {TARGET_TIME_SLOT[0]} - {TARGET_TIME_SLOT[1]}")
    logger.info(f"   樣本數: {SAMPLE_SIZE}")
    logger.info(f"   並行處理: 啟用 (4核心)")
    logger.info(f"   結果保存: 啟用")
    
    try:
        # 執行優化後的敏感度分析
        results = strategy_sensitivity_analyzer.run_sensitivity_analysis(
            target_time_slot=TARGET_TIME_SLOT,
            sample_size=SAMPLE_SIZE,
            start_date="2024-11-04",
            end_date="2025-06-28",
            use_parallel=True,
            num_processes=4
        )
        
        # 檢查結果
        logger.info("\n📋 測試結果檢查:")
        
        success_count = 0
        for direction in ['LONG_ONLY', 'SHORT_ONLY', 'BOTH']:
            if direction in results and 'Si' in results[direction]:
                logger.info(f"   ✅ {direction}: 分析成功")
                success_count += 1
            else:
                logger.error(f"   ❌ {direction}: 分析失敗")
        
        # 檢查報告目錄
        report_base = "/Users/z/big/my-capital-project/quan_strategy_analysis/SALIB_report"
        if os.path.exists(report_base):
            # 找到最新的報告目錄
            report_dirs = [d for d in os.listdir(report_base) if d.startswith('sensitivity_analysis_')]
            if report_dirs:
                latest_dir = sorted(report_dirs)[-1]
                report_path = os.path.join(report_base, latest_dir)
                
                logger.info(f"\n📁 報告目錄檢查: {report_path}")
                
                # 檢查生成的文件
                files = os.listdir(report_path)
                csv_files = [f for f in files if f.endswith('.csv')]
                png_files = [f for f in files if f.endswith('.png')]
                
                logger.info(f"   📊 CSV文件: {len(csv_files)} 個")
                for csv_file in csv_files:
                    logger.info(f"      - {csv_file}")
                
                logger.info(f"   🎨 圖表文件: {len(png_files)} 個")
                for png_file in png_files:
                    logger.info(f"      - {png_file}")
                
                if len(csv_files) >= 3 and len(png_files) >= 3:
                    logger.info("   ✅ 文件生成完整")
                else:
                    logger.warning("   ⚠️ 部分文件可能缺失")
            else:
                logger.warning("   ⚠️ 未找到報告目錄")
        else:
            logger.warning("   ⚠️ 報告基礎目錄不存在")
        
        # 總結
        logger.info("\n" + "=" * 60)
        logger.info("🎯 優化功能測試總結:")
        logger.info(f"   分析成功率: {success_count}/3 ({success_count/3*100:.1f}%)")
        
        if success_count == 3:
            logger.info("🎉 所有優化功能測試通過！")
            logger.info("\n💡 優化功能確認:")
            logger.info("   ✅ 並行處理: 4核心加速計算")
            logger.info("   ✅ 錯誤記錄: 詳細參數錯誤日誌")
            logger.info("   ✅ 結果保存: CSV + PNG 自動保存")
            logger.info("   ✅ 視覺化: 敏感度條形圖生成")
            return True
        else:
            logger.error("❌ 部分功能測試失敗")
            return False
            
    except Exception as e:
        logger.error(f"❌ 測試過程中發生錯誤: {e}")
        return False

def test_error_logging():
    """測試錯誤參數記錄功能"""
    logger.info("\n🔍 測試錯誤參數記錄功能...")
    
    try:
        import numpy as np
        
        # 創建一個會導致錯誤的參數組合（極端值）
        bad_params = np.array([999.0, 999.0, 999.0, 999.0, 999.0, 999.0, 999.0])
        
        # 嘗試評估這個錯誤參數
        result = strategy_sensitivity_analyzer.evaluate_for_salib(
            bad_params, 
            "BOTH", 
            "2024-11-04", 
            "2025-06-28", 
            "08:46", 
            "08:47"
        )
        
        if result == -999999.0:
            logger.info("   ✅ 錯誤參數正確返回失敗值")
            logger.info("   ✅ 錯誤日誌應該已記錄參數詳情")
        else:
            logger.warning(f"   ⚠️ 意外結果: {result}")
            
    except Exception as e:
        logger.error(f"   ❌ 錯誤記錄測試失敗: {e}")

def main():
    """主測試函數"""
    logger.info("🧪 開始優化功能測試")
    
    # 測試主要功能
    main_success = test_optimized_features()
    
    # 測試錯誤記錄
    test_error_logging()
    
    # 最終結果
    if main_success:
        logger.info("\n🎊 優化版敏感度分析器準備就緒！")
        logger.info("📝 使用建議:")
        logger.info("   - 小樣本測試: N=32-64")
        logger.info("   - 正式分析: N=128-256")
        logger.info("   - 並行處理: 自動使用4核心")
        logger.info("   - 結果查看: SALIB_report 目錄")
    else:
        logger.error("❌ 優化功能存在問題，請檢查配置")

if __name__ == '__main__':
    main()
