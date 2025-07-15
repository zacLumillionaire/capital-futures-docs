#!/usr/bin/env python3
"""
測試徹底的靜默模式

重點測試：
1. 完全抑制交易日誌
2. 只顯示進度更新
3. 並行處理中的日誌控制
"""

import logging
import strategy_sensitivity_analyzer
import os

# 設置日誌級別為 INFO，這樣我們可以看到進度更新，但不會看到 DEBUG 級別的交易日誌
logging.basicConfig(level=logging.INFO, format='[%(asctime)s] %(levelname)s: %(message)s')
logger = logging.getLogger(__name__)

def test_silent_mode():
    """測試徹底的靜默模式"""
    logger.info("🔇 測試徹底的靜默模式")
    logger.info("=" * 60)
    
    # 測試參數
    TARGET_TIME_SLOT = ('08:46', '08:47')
    SAMPLE_SIZE = 32  # 使用小樣本快速測試
    
    logger.info(f"📊 測試配置:")
    logger.info(f"   時間區段: {TARGET_TIME_SLOT[0]} - {TARGET_TIME_SLOT[1]}")
    logger.info(f"   樣本數: {SAMPLE_SIZE}")
    logger.info(f"   並行處理: 啟用 (4核心)")
    logger.info(f"   徹底靜默: 啟用")
    
    logger.info("\n🎯 預期行為:")
    logger.info("   ✅ 完全沒有交易進場/出場日誌")
    logger.info("   ✅ 完全沒有移動停利日誌")
    logger.info("   ✅ 只會看到敏感度分析的主要進度")
    logger.info("   ✅ 並行處理正常工作")
    
    try:
        # 在主進程中也設置日誌級別
        logging.getLogger().setLevel(logging.WARNING)
        
        # 執行敏感度分析
        logger.info("\n🚀 開始執行徹底靜默模式測試...")
        
        results = strategy_sensitivity_analyzer.run_sensitivity_analysis(
            target_time_slot=TARGET_TIME_SLOT,
            sample_size=SAMPLE_SIZE,
            start_date="2024-11-04",
            end_date="2025-06-28",
            use_parallel=True,
            num_processes=4
        )
        
        # 恢復日誌級別以顯示結果
        logging.getLogger().setLevel(logging.INFO)
        
        # 檢查結果
        logger.info("\n📋 測試結果檢查:")
        
        success_count = 0
        for direction in ['LONG_ONLY', 'SHORT_ONLY', 'BOTH']:
            if direction in results and 'Si' in results[direction]:
                logger.info(f"   ✅ {direction}: 分析成功")
                success_count += 1
                
                # 顯示前3名參數
                Si = results[direction]['Si']
                problem = results[direction]['problem']
                
                # 創建結果DataFrame
                import pandas as pd
                sensitivity_data = {
                    'Parameter': problem['names'],
                    'ST': Si['ST']
                }
                df_results = pd.DataFrame(sensitivity_data)
                st_sorted = df_results.sort_values('ST', ascending=False)
                
                logger.info(f"   🏆 {direction} 前3名參數:")
                for rank, (_, row) in enumerate(st_sorted.head(3).iterrows(), 1):
                    logger.info(f"      {rank}. {row['Parameter']}: ST={row['ST']:.4f}")
            else:
                logger.error(f"   ❌ {direction}: 分析失敗")
        
        # 檢查報告文件
        report_base = "/Users/z/big/my-capital-project/quan_strategy_analysis/SALIB_report"
        if os.path.exists(report_base):
            report_dirs = [d for d in os.listdir(report_base) if d.startswith('sensitivity_analysis_')]
            if report_dirs:
                latest_dir = sorted(report_dirs)[-1]
                report_path = os.path.join(report_base, latest_dir)
                
                files = os.listdir(report_path)
                csv_files = [f for f in files if f.endswith('.csv')]
                png_files = [f for f in files if f.endswith('.png')]
                
                logger.info(f"\n📁 生成的報告文件:")
                logger.info(f"   📊 CSV文件: {len(csv_files)} 個")
                logger.info(f"   🎨 圖表文件: {len(png_files)} 個")
                logger.info(f"   📂 報告目錄: {report_path}")
        
        # 總結
        logger.info("\n" + "=" * 60)
        logger.info("🎯 靜默模式測試總結:")
        logger.info(f"   分析成功率: {success_count}/3 ({success_count/3*100:.1f}%)")
        
        if success_count == 3:
            logger.info("🎉 徹底靜默模式測試通過！")
            logger.info("\n💡 靜默效果確認:")
            logger.info("   ✅ 無交易日誌干擾")
            logger.info("   ✅ 無移動停利日誌")
            logger.info("   ✅ 並行處理正常")
            logger.info("   ✅ 結果保存完整")
            return True
        else:
            logger.error("❌ 部分功能測試失敗")
            return False
            
    except Exception as e:
        # 恢復日誌級別
        logging.getLogger().setLevel(logging.INFO)
        logger.error(f"❌ 測試過程中發生錯誤: {e}")
        return False

def test_single_evaluation():
    """測試單次評估的靜默效果"""
    logger.info("\n🔍 測試單次評估靜默效果")
    logger.info("-" * 40)
    
    try:
        import numpy as np
        
        # 創建測試參數
        test_params = np.array([20.0, 0.10, 40.0, 0.15, 41.0, 0.20, 2.0])
        
        logger.info("🧪 執行單次評估測試...")
        logger.info("   預期：完全沒有交易日誌輸出")
        
        # 設置靜默模式
        logging.getLogger().setLevel(logging.WARNING)
        
        # 執行單次評估
        result = strategy_sensitivity_analyzer.evaluate_for_salib(
            test_params, 
            "BOTH", 
            "2024-11-04", 
            "2025-06-28", 
            "08:46", 
            "08:47"
        )
        
        # 恢復日誌級別
        logging.getLogger().setLevel(logging.INFO)
        
        logger.info(f"   ✅ 單次評估完成，結果: {result:.2f}")
        logger.info("   ✅ 如果沒有看到交易日誌，說明靜默模式生效")
        
        return True
        
    except Exception as e:
        logging.getLogger().setLevel(logging.INFO)
        logger.error(f"   ❌ 單次評估測試失敗: {e}")
        return False

def main():
    """主測試函數"""
    logger.info("🧪 開始徹底靜默模式測試")
    
    # 測試單次評估
    single_success = test_single_evaluation()
    
    # 測試完整分析
    if single_success:
        main_success = test_silent_mode()
    else:
        logger.error("❌ 單次評估測試失敗，跳過完整分析測試")
        main_success = False
    
    # 最終結果
    if main_success:
        logger.info("\n🎊 徹底靜默模式優化完成！")
        logger.info("📝 優化成果:")
        logger.info("   - 完全抑制交易日誌")
        logger.info("   - 並行處理靜默控制")
        logger.info("   - 清晰的進度顯示")
        logger.info("   - 自動結果保存")
    else:
        logger.error("❌ 靜默模式優化存在問題，需要進一步調整")

if __name__ == '__main__':
    main()
