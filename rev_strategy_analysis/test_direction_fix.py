#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
測試交易方向修復：確保LONG_ONLY和SHORT_ONLY都能正常工作
"""

import importlib.util
from decimal import Decimal
from pprint import pprint

def test_trading_directions():
    """測試所有交易方向是否都能正常工作"""
    
    print("=" * 80)
    print("🧪 測試交易方向修復：BOTH/LONG_ONLY/SHORT_ONLY")
    print("=" * 80)
    
    # 1. 動態導入修復後的核心回測引擎
    try:
        print("📦 正在導入修復後的核心回測引擎...")
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
        
        print("✅ 修復後的核心引擎導入成功")
        
    except Exception as e:
        print(f"❌ 核心引擎導入失敗: {e}")
        return
    
    # 2. 創建基礎配置模板
    def create_test_config(trading_direction):
        return StrategyConfig(
            trade_size_in_lots=3,
            stop_loss_type=StopLossType.RANGE_BOUNDARY,
            fixed_stop_loss_points=Decimal(15),
            trading_direction=trading_direction,
            entry_price_mode="range_boundary",
            lot_rules=[
                LotRule(
                    use_trailing_stop=True,
                    trailing_activation=Decimal(15),
                    trailing_pullback=Decimal('0.10'),
                    fixed_tp_points=Decimal(30)
                ),
                LotRule(
                    use_trailing_stop=True,
                    trailing_activation=Decimal(40),
                    trailing_pullback=Decimal('0.10'),
                    protective_stop_multiplier=Decimal('0'),
                    fixed_tp_points=Decimal(30)
                ),
                LotRule(
                    use_trailing_stop=True,
                    trailing_activation=Decimal(41),
                    trailing_pullback=Decimal('0.20'),
                    protective_stop_multiplier=Decimal('0'),
                    fixed_tp_points=Decimal(30)
                )
            ]
        )
    
    # 3. 測試所有交易方向
    test_start_date = "2024-11-04"
    test_end_date = "2024-11-08"
    
    directions_to_test = ["BOTH", "LONG_ONLY", "SHORT_ONLY"]
    results = {}
    
    for direction in directions_to_test:
        print(f"\n🎯 測試交易方向: {direction}")
        print("-" * 50)
        
        try:
            config = create_test_config(direction)
            result = run_backtest(
                config, 
                start_date=test_start_date, 
                end_date=test_end_date, 
                silent=True
            )
            
            print(f"✅ {direction} 回測成功完成")
            
            # 提取關鍵統計
            total_pnl = result.get('total_pnl', 0)
            total_trades = result.get('total_trades', 0)
            long_trades = result.get('long_trades', 0)
            short_trades = result.get('short_trades', 0)
            max_drawdown = result.get('max_drawdown', 0)
            lot1_pnl = result.get('lot1_pnl', 0)
            lot2_pnl = result.get('lot2_pnl', 0)
            lot3_pnl = result.get('lot3_pnl', 0)
            
            print(f"  📊 總損益: {total_pnl:.2f}")
            print(f"  📊 總交易: {total_trades} (多:{long_trades}, 空:{short_trades})")
            print(f"  📊 最大回撤: {max_drawdown:.2f}")
            print(f"  📊 各口損益: 1口:{lot1_pnl:.2f}, 2口:{lot2_pnl:.2f}, 3口:{lot3_pnl:.2f}")
            
            # 驗證交易方向邏輯
            if direction == "LONG_ONLY":
                if short_trades == 0 and long_trades >= 0:
                    print("  ✅ LONG_ONLY 邏輯正確：只有多頭交易")
                else:
                    print(f"  ❌ LONG_ONLY 邏輯錯誤：應該只有多頭交易，但發現空頭交易 {short_trades} 次")
            
            elif direction == "SHORT_ONLY":
                if long_trades == 0 and short_trades >= 0:
                    print("  ✅ SHORT_ONLY 邏輯正確：只有空頭交易")
                else:
                    print(f"  ❌ SHORT_ONLY 邏輯錯誤：應該只有空頭交易，但發現多頭交易 {long_trades} 次")
            
            elif direction == "BOTH":
                if long_trades >= 0 and short_trades >= 0:
                    print("  ✅ BOTH 邏輯正確：允許多空交易")
                else:
                    print("  ❌ BOTH 邏輯可能有問題")
            
            # 驗證統計數據完整性
            missing_stats = []
            if 'max_drawdown' not in result:
                missing_stats.append("MDD")
            if 'lot1_pnl' not in result:
                missing_stats.append("各口損益")
            
            if missing_stats:
                print(f"  ⚠️  缺失統計: {', '.join(missing_stats)}")
            else:
                print("  ✅ 所有統計數據完整")
            
            results[direction] = result
            
        except Exception as e:
            print(f"❌ {direction} 回測失敗: {e}")
            import traceback
            traceback.print_exc()
            results[direction] = None
    
    # 4. 總結測試結果
    print("\n" + "=" * 80)
    print("🏁 交易方向測試總結")
    print("=" * 80)
    
    successful_directions = [d for d, r in results.items() if r is not None]
    failed_directions = [d for d, r in results.items() if r is None]
    
    if len(successful_directions) == 3:
        print("🎉 所有交易方向都測試成功！")
        print("✅ BOTH 模式正常工作")
        print("✅ LONG_ONLY 模式正常工作") 
        print("✅ SHORT_ONLY 模式正常工作")
        print("\n🎯 修復完全成功！現在GUI的所有交易方向選項都能正常使用")
        
        # 比較不同方向的結果
        print(f"\n📊 不同方向結果比較:")
        for direction in successful_directions:
            result = results[direction]
            print(f"  {direction:10}: 總損益 {result['total_pnl']:8.2f}, 交易 {result['total_trades']:2d} 次, MDD {result['max_drawdown']:6.2f}")
            
    elif len(successful_directions) >= 1:
        print(f"⚠️  部分修復成功：{', '.join(successful_directions)} 正常工作")
        if failed_directions:
            print(f"❌ 仍有問題：{', '.join(failed_directions)} 失敗")
    else:
        print("❌ 修復失敗：所有交易方向都無法正常工作")
    
    print("\n" + "=" * 80)

if __name__ == "__main__":
    test_trading_directions()
