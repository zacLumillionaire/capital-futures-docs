#!/usr/bin/env python3
"""
測試小樣本敏感度分析
"""

import logging
import strategy_sensitivity_analyzer

logging.basicConfig(level=logging.INFO, format='[%(asctime)s] %(levelname)s: %(message)s')
logger = logging.getLogger(__name__)

def main():
    """運行小樣本敏感度分析測試"""
    logger.info("🚀 開始小樣本敏感度分析測試")
    
    # 運行小樣本分析
    results = strategy_sensitivity_analyzer.run_sensitivity_analysis(
        target_time_slot=('08:46', '08:47'),  # 使用正確的時間區間
        sample_size=16,  # 小樣本快速測試
        start_date="2024-11-04",
        end_date="2025-06-28"
    )
    
    logger.info("\n🎉 小樣本測試完成！")
    
    # 檢查結果
    for direction, result in results.items():
        if 'error' in result:
            logger.error(f"❌ {direction}: {result['error']}")
        else:
            logger.info(f"✅ {direction}: 分析成功")

if __name__ == '__main__':
    main()
