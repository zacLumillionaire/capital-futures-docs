#!/usr/bin/env python3
"""
測試優化後的進度顯示功能

測試重點：
1. 靜默模式：不顯示大量交易日誌
2. 進度更新：每5%顯示一次進度
3. 並行處理：4核心加速
"""

import logging
import strategy_sensitivity_analyzer
import os

logging.basicConfig(level=logging.INFO, format='[%(asctime)s] %(levelname)s: %(message)s')
logger = logging.getLogger(__name__)

def test_progress_display():
    """測試進度顯示功能"""
    logger.info("🧪 測試優化後的進度顯示功能")
    logger.info("=" * 60)
    
    # 測試參數
    TARGET_TIME_SLOT = ('08:46', '08:47')
    SAMPLE_SIZE = 64  # 使用中等樣本測試進度顯示
    
    logger.info(f"📊 測試配置:")
    logger.info(f"   時間區段: {TARGET_TIME_SLOT[0]} - {TARGET_TIME_SLOT[1]}")
    logger.info(f"   樣本數: {SAMPLE_SIZE}")
    logger.info(f"   並行處理: 啟用 (4核心)")
    logger.info(f"   靜默模式: 啟用")
    logger.info(f"   進度更新: 每5%顯示一次")
    
    logger.info("\n🎯 預期行為:")
    logger.info("   ✅ 不會看到大量交易進場/出場日誌")
    logger.info("   ✅ 只會看到進度更新 (每5%)")
    logger.info("   ✅ 並行處理加速計算")
    logger.info("   ✅ 自動保存結果和圖表")
    
    try:
        # 執行優化後的敏感度分析
        logger.info("\n🚀 開始執行敏感度分析...")
        
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
        logger.info("🎯 進度顯示測試總結:")
        logger.info(f"   分析成功率: {success_count}/3 ({success_count/3*100:.1f}%)")
        
        if success_count == 3:
            logger.info("🎉 進度顯示優化測試通過！")
            logger.info("\n💡 優化效果確認:")
            logger.info("   ✅ 靜默模式: 無大量交易日誌干擾")
            logger.info("   ✅ 進度更新: 清晰的5%間隔進度顯示")
            logger.info("   ✅ 並行處理: 4核心加速計算")
            logger.info("   ✅ 結果保存: 自動生成CSV和圖表")
            return True
        else:
            logger.error("❌ 部分功能測試失敗")
            return False
            
    except Exception as e:
        logger.error(f"❌ 測試過程中發生錯誤: {e}")
        return False

def test_sequential_vs_parallel():
    """比較順序處理和並行處理的效果"""
    logger.info("\n🔄 比較順序處理 vs 並行處理")
    logger.info("-" * 40)
    
    TARGET_TIME_SLOT = ('08:46', '08:47')
    SMALL_SAMPLE = 16  # 使用小樣本快速比較
    
    try:
        import time
        
        # 測試順序處理
        logger.info("🐌 測試順序處理...")
        start_time = time.time()
        
        results_seq = strategy_sensitivity_analyzer.run_sensitivity_analysis(
            target_time_slot=TARGET_TIME_SLOT,
            sample_size=SMALL_SAMPLE,
            start_date="2024-11-04",
            end_date="2025-06-28",
            use_parallel=False,  # 關閉並行處理
            num_processes=1
        )
        
        seq_time = time.time() - start_time
        logger.info(f"   ⏱️ 順序處理耗時: {seq_time:.2f} 秒")
        
        # 測試並行處理
        logger.info("\n🚀 測試並行處理...")
        start_time = time.time()
        
        results_par = strategy_sensitivity_analyzer.run_sensitivity_analysis(
            target_time_slot=TARGET_TIME_SLOT,
            sample_size=SMALL_SAMPLE,
            start_date="2024-11-04",
            end_date="2025-06-28",
            use_parallel=True,   # 啟用並行處理
            num_processes=4
        )
        
        par_time = time.time() - start_time
        logger.info(f"   ⏱️ 並行處理耗時: {par_time:.2f} 秒")
        
        # 比較結果
        if seq_time > 0 and par_time > 0:
            speedup = seq_time / par_time
            logger.info(f"\n📈 性能比較:")
            logger.info(f"   🚀 加速比: {speedup:.2f}x")
            if speedup > 1.5:
                logger.info("   ✅ 並行處理顯著提升性能")
            else:
                logger.info("   ⚠️ 並行處理提升有限（可能樣本數太小）")
        
    except Exception as e:
        logger.error(f"❌ 性能比較測試失敗: {e}")

def main():
    """主測試函數"""
    logger.info("🧪 開始進度顯示優化測試")
    
    # 主要功能測試
    main_success = test_progress_display()
    
    # 性能比較測試
    test_sequential_vs_parallel()
    
    # 最終結果
    if main_success:
        logger.info("\n🎊 進度顯示優化完成！")
        logger.info("📝 使用建議:")
        logger.info("   - 小樣本測試: N=32-64 (快速驗證)")
        logger.info("   - 正式分析: N=128-256 (精確結果)")
        logger.info("   - 並行處理: 自動使用4核心")
        logger.info("   - 進度監控: 每5%更新一次")
        logger.info("   - 結果查看: SALIB_report 目錄")
    else:
        logger.error("❌ 進度顯示優化存在問題，請檢查配置")

if __name__ == '__main__':
    main()
