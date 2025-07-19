#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
核心回測引擎的獨立驗證腳本
用於隔離測試 rev_multi_Profit-Funded Risk_多口.py 的基本功能
"""

import importlib.util
import sys
import os
from decimal import Decimal
from pprint import pprint

def main():
    """主函數：執行核心引擎的隔離測試"""
    
    print("=" * 80)
    print("🔍 核心回測引擎獨立驗證測試")
    print("=" * 80)
    print("目標：驗證 rev_multi_Profit-Funded Risk_多口.py 是否能對不同配置產生不同結果")
    print()
    
    # 1. 動態導入核心回測引擎
    try:
        print("📦 正在導入核心回測引擎...")
        spec = importlib.util.spec_from_file_location(
            "rev_multi_module",
            "rev_multi_Profit-Funded Risk_多口.py"
        )
        rev_multi_module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(rev_multi_module)
        
        # 導入所需的類和函數
        StrategyConfig = rev_multi_module.StrategyConfig
        LotRule = rev_multi_module.LotRule
        StopLossType = rev_multi_module.StopLossType
        run_backtest = rev_multi_module.run_backtest
        
        print("✅ 核心引擎導入成功")
        
    except Exception as e:
        print(f"❌ 核心引擎導入失敗: {e}")
        return
    
    # 2. 創建兩組極端差異的配置
    print("\n🎯 創建兩組極端配置...")
    
    # 配置A：積極做多配置
    print("\n📈 配置A - 積極做多配置:")
    config_A = StrategyConfig(
        trade_size_in_lots=3,
        stop_loss_type=StopLossType.RANGE_BOUNDARY,
        fixed_stop_loss_points=Decimal(10),  # 較小的停損點
        trading_direction="LONG_ONLY",  # 只做多
        entry_price_mode="breakout_low",  # 最低點+5點進場
        lot_rules=[
            # 第1口：積極參數
            LotRule(
                use_trailing_stop=True,
                trailing_activation=Decimal(10),  # 較小觸發點
                trailing_pullback=Decimal('0.10'),  # 10%回檔
                fixed_tp_points=Decimal(50)  # 固定停利50點
            ),
            # 第2口：積極參數
            LotRule(
                use_trailing_stop=True,
                trailing_activation=Decimal(25),  # 較小觸發點
                trailing_pullback=Decimal('0.10'),  # 10%回檔
                protective_stop_multiplier=Decimal('1.5'),  # 較小保護係數
                fixed_tp_points=Decimal(70)  # 固定停利70點
            ),
            # 第3口：積極參數
            LotRule(
                use_trailing_stop=True,
                trailing_activation=Decimal(30),  # 較小觸發點
                trailing_pullback=Decimal('0.15'),  # 15%回檔
                protective_stop_multiplier=Decimal('1.5'),  # 較小保護係數
                fixed_tp_points=Decimal(90)  # 固定停利90點
            )
        ]
    )
    
    print(f"  - 交易方向: {config_A.trading_direction}")
    print(f"  - 進場模式: {config_A.entry_price_mode}")
    print(f"  - 第1口觸發: {config_A.lot_rules[0].trailing_activation}點")
    print(f"  - 第2口觸發: {config_A.lot_rules[1].trailing_activation}點")
    print(f"  - 第3口觸發: {config_A.lot_rules[2].trailing_activation}點")
    
    # 配置B：保守做空配置
    print("\n📉 配置B - 保守做空配置:")
    config_B = StrategyConfig(
        trade_size_in_lots=3,
        stop_loss_type=StopLossType.RANGE_BOUNDARY,
        fixed_stop_loss_points=Decimal(25),  # 較大的停損點
        trading_direction="SHORT_ONLY",  # 只做空
        entry_price_mode="range_boundary",  # 區間邊緣進場
        lot_rules=[
            # 第1口：保守參數
            LotRule(
                use_trailing_stop=True,
                trailing_activation=Decimal(50),  # 較大觸發點
                trailing_pullback=Decimal('0.30'),  # 30%回檔
                fixed_tp_points=Decimal(30)  # 固定停利30點
            ),
            # 第2口：保守參數
            LotRule(
                use_trailing_stop=True,
                trailing_activation=Decimal(80),  # 較大觸發點
                trailing_pullback=Decimal('0.30'),  # 30%回檔
                protective_stop_multiplier=Decimal('3.0'),  # 較大保護係數
                fixed_tp_points=Decimal(50)  # 固定停利50點
            ),
            # 第3口：保守參數
            LotRule(
                use_trailing_stop=True,
                trailing_activation=Decimal(100),  # 較大觸發點
                trailing_pullback=Decimal('0.35'),  # 35%回檔
                protective_stop_multiplier=Decimal('3.0'),  # 較大保護係數
                fixed_tp_points=Decimal(70)  # 固定停利70點
            )
        ]
    )
    
    print(f"  - 交易方向: {config_B.trading_direction}")
    print(f"  - 進場模式: {config_B.entry_price_mode}")
    print(f"  - 第1口觸發: {config_B.lot_rules[0].trailing_activation}點")
    print(f"  - 第2口觸發: {config_B.lot_rules[1].trailing_activation}點")
    print(f"  - 第3口觸發: {config_B.lot_rules[2].trailing_activation}點")
    
    # 3. 分別執行回測並打印結果
    test_start_date = "2024-11-04"
    test_end_date = "2024-11-08"  # 使用較短的測試期間
    
    print(f"\n🚀 開始執行隔離測試 (測試期間: {test_start_date} ~ {test_end_date})")
    print("=" * 80)
    
    # 測試配置A
    print("\n🔍 測試配置A (積極做多配置):")
    print("-" * 50)
    try:
        result_A = run_backtest(
            config_A, 
            start_date=test_start_date, 
            end_date=test_end_date, 
            silent=True  # 靜默模式，減少日誌干擾
        )
        print("✅ 配置A回測完成")
        print("📊 配置A完整結果字典:")
        pprint(result_A, width=100, depth=3)
        
    except Exception as e:
        print(f"❌ 配置A回測失敗: {e}")
        result_A = None
    
    print("\n" + "=" * 80)
    
    # 測試配置B
    print("\n🔍 測試配置B (保守做空配置):")
    print("-" * 50)
    try:
        result_B = run_backtest(
            config_B, 
            start_date=test_start_date, 
            end_date=test_end_date, 
            silent=True  # 靜默模式，減少日誌干擾
        )
        print("✅ 配置B回測完成")
        print("📊 配置B完整結果字典:")
        pprint(result_B, width=100, depth=3)
        
    except Exception as e:
        print(f"❌ 配置B回測失敗: {e}")
        result_B = None
    
    # 4. 初步比較分析
    print("\n" + "=" * 80)
    print("🔍 初步比較分析")
    print("=" * 80)
    
    if result_A is None or result_B is None:
        print("❌ 無法進行比較：其中一個或兩個配置的回測都失敗了")
        return
    
    # 比較關鍵指標
    def safe_get(result_dict, key, default="N/A"):
        """安全獲取字典值"""
        return result_dict.get(key, default) if result_dict else default
    
    print("📊 關鍵指標比較:")
    print(f"  總損益 - 配置A: {safe_get(result_A, 'total_pnl')}, 配置B: {safe_get(result_B, 'total_pnl')}")
    print(f"  總交易次數 - 配置A: {safe_get(result_A, 'total_trades')}, 配置B: {safe_get(result_B, 'total_trades')}")
    print(f"  勝率 - 配置A: {safe_get(result_A, 'win_rate')}, 配置B: {safe_get(result_B, 'win_rate')}")
    print(f"  最大回撤 - 配置A: {safe_get(result_A, 'max_drawdown')}, 配置B: {safe_get(result_B, 'max_drawdown')}")
    print(f"  多頭交易 - 配置A: {safe_get(result_A, 'long_trades')}, 配置B: {safe_get(result_B, 'long_trades')}")
    print(f"  空頭交易 - 配置A: {safe_get(result_A, 'short_trades')}, 配置B: {safe_get(result_B, 'short_trades')}")
    
    # 判斷結果是否相同
    if result_A == result_B:
        print("\n❌ 診斷結果：兩個配置的回測結果完全相同！")
        print("🔍 這表明核心回測引擎可能存在問題，無論輸入什麼配置都返回相同結果")
        print("🎯 建議下一步：深入審計 _run_multi_lot_logic 函數的內部邏輯")
    else:
        print("\n✅ 診斷結果：兩個配置的回測結果不同")
        print("🔍 這表明核心回測引擎功能正常，問題可能出在GUI層的配置傳遞")
        print("🎯 建議下一步：審計 rev_web_trading_gui.py 的配置生成和傳遞邏輯")
    
    print("\n" + "=" * 80)
    print("🏁 核心引擎獨立驗證測試完成")
    print("=" * 80)

if __name__ == "__main__":
    main()
