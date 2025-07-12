#!/usr/bin/env python3
"""
測試固定停損模式
直接運行此腳本來測試固定停損功能
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from decimal import Decimal
import importlib.util
spec = importlib.util.spec_from_file_location("rev_multi", "rev_multi_Profit-Funded Risk_多口.py")
rev_multi = importlib.util.module_from_spec(spec)
spec.loader.exec_module(rev_multi)

# 導入需要的類和函數
StrategyConfig = rev_multi.StrategyConfig
LotRule = rev_multi.LotRule
StopLossType = rev_multi.StopLossType
run_backtest = rev_multi.run_backtest
init_all_db_pools = rev_multi.init_all_db_pools
logger = rev_multi.logger

def test_fixed_stop_mode():
    """測試固定停損模式"""
    
    # 初始化資料庫連線池
    logger.info("🔧 初始化資料庫連線池...")
    init_all_db_pools()
    logger.info("✅ 資料庫連線池初始化成功。")
    
    # 設定測試日期範圍
    start_date = "2024-11-04"
    end_date = "2024-11-10"
    
    logger.info("\n" + "="*80)
    logger.info("🎯 測試固定停損模式")
    logger.info("="*80)
    
    # === 🎯 固定停損模式測試配置 ===
    config_fixed_stop = StrategyConfig(
        trade_size_in_lots=3,
        stop_loss_type=StopLossType.RANGE_BOUNDARY,
        lot_rules=[
            # 第1口：14點固定停損
            LotRule(
                use_trailing_stop=False,
                trailing_activation=Decimal(14),  # GUI設定值
                trailing_pullback=Decimal('0.00'),  # 0%回檔
                fixed_stop_loss_points=Decimal(14)  # 14點固定停損
            ),
            # 第2口：40點固定停損，無保護性停損
            LotRule(
                use_trailing_stop=False,
                trailing_activation=Decimal(40),  # GUI設定值
                trailing_pullback=Decimal('0.00'),  # 0%回檔
                protective_stop_multiplier=None,  # 停用保護性停損
                fixed_stop_loss_points=Decimal(40)  # 40點固定停損
            ),
            # 第3口：41點固定停損，無保護性停損
            LotRule(
                use_trailing_stop=False,
                trailing_activation=Decimal(41),  # GUI設定值
                trailing_pullback=Decimal('0.00'),  # 0%回檔
                protective_stop_multiplier=None,  # 停用保護性停損
                fixed_stop_loss_points=Decimal(41)  # 41點固定停損
            ),
        ]
    )
    
    logger.info("📋 配置說明：")
    logger.info("   - 第1口：14點固定停損")
    logger.info("   - 第2口：40點固定停損，無保護性停損")
    logger.info("   - 第3口：41點固定停損，無保護性停損")
    logger.info("   - 統一停利：區間邊緣")
    logger.info("   - 每口獨立運作，不相互影響")
    logger.info("")
    
    # 執行回測
    run_backtest(config_fixed_stop, start_date, end_date)
    
    logger.info("\n" + "="*80)
    logger.info("🎯 固定停損模式測試完成")
    logger.info("="*80)

if __name__ == "__main__":
    test_fixed_stop_mode()
