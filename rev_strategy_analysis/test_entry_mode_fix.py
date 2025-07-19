#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
測試進場價格模式修復：確保不同的進場模式產生不同的結果
"""

import importlib.util
from decimal import Decimal
from pprint import pprint

def test_entry_price_modes():
    """測試所有進場價格模式是否都能正常工作"""
    
    print("=" * 80)
    print("🧪 測試進場價格模式修復：range_boundary/breakout_close/breakout_low")
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
    def create_test_config(entry_price_mode):
        return StrategyConfig(
            trade_size_in_lots=3,
            stop_loss_type=StopLossType.RANGE_BOUNDARY,
            fixed_stop_loss_points=Decimal(15),
            trading_direction="BOTH",  # 多空都做，增加測試機會
            entry_price_mode=entry_price_mode,  # 關鍵差異點
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
    
    # 3. 測試所有進場價格模式
    test_start_date = "2024-11-04"
    test_end_date = "2024-11-08"
    
    entry_modes_to_test = ["range_boundary", "breakout_close", "breakout_low"]
    results = {}
    
    for entry_mode in entry_modes_to_test:
        print(f"\n🎯 測試進場價格模式: {entry_mode}")
        print("-" * 50)
        
        try:
            config = create_test_config(entry_mode)
            result = run_backtest(
                config, 
                start_date=test_start_date, 
                end_date=test_end_date, 
                silent=False  # 不靜默，要看日誌中的進場模式信息
            )
            
            print(f"✅ {entry_mode} 回測成功完成")
            
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
            
            results[entry_mode] = result
            
        except Exception as e:
            print(f"❌ {entry_mode} 回測失敗: {e}")
            import traceback
            traceback.print_exc()
            results[entry_mode] = None
    
    # 4. 比較不同進場模式的結果
    print("\n" + "=" * 80)
    print("🔍 進場價格模式比較分析")
    print("=" * 80)
    
    successful_modes = [m for m, r in results.items() if r is not None]
    failed_modes = [m for m, r in results.items() if r is None]
    
    if len(successful_modes) >= 2:
        print("📊 不同進場模式結果比較:")
        for mode in successful_modes:
            result = results[mode]
            mode_desc = {
                'range_boundary': '區間邊緣',
                'breakout_close': '突破收盤價', 
                'breakout_low': '最低點+5點'
            }.get(mode, mode)
            print(f"  {mode_desc:12}: 總損益 {result['total_pnl']:8.2f}, 交易 {result['total_trades']:2d} 次, MDD {result['max_drawdown']:6.2f}")
        
        # 檢查結果是否有差異
        pnl_values = [results[mode]['total_pnl'] for mode in successful_modes]
        trade_counts = [results[mode]['total_trades'] for mode in successful_modes]
        
        pnl_all_same = len(set(pnl_values)) == 1
        trades_all_same = len(set(trade_counts)) == 1
        
        if pnl_all_same and trades_all_same:
            print("\n❌ 警告：所有進場模式的結果完全相同！")
            print("🔍 這表明進場價格模式可能仍然沒有被正確實現")
            print("🎯 建議檢查日誌中是否顯示了正確的進場模式信息")
        else:
            print("\n✅ 不同進場模式產生了不同的結果！")
            print("🎯 進場價格模式修復成功")
            
            # 分析差異
            if not pnl_all_same:
                print(f"  💰 損益差異: 最高 {max(pnl_values):.2f} vs 最低 {min(pnl_values):.2f}")
            if not trades_all_same:
                print(f"  📊 交易次數差異: 最多 {max(trade_counts)} vs 最少 {min(trade_counts)}")
        
    elif len(successful_modes) == 1:
        print(f"⚠️  只有 {successful_modes[0]} 模式測試成功")
        if failed_modes:
            print(f"❌ 失敗的模式：{', '.join(failed_modes)}")
    else:
        print("❌ 所有進場模式都測試失敗")
    
    # 5. 總結測試結果
    print("\n" + "=" * 80)
    print("🏁 進場價格模式測試總結")
    print("=" * 80)
    
    if len(successful_modes) == 3:
        # 檢查是否真的有差異
        pnl_values = [results[mode]['total_pnl'] for mode in successful_modes]
        if len(set(pnl_values)) > 1:
            print("🎉 所有進場價格模式都測試成功且產生不同結果！")
            print("✅ range_boundary (區間邊緣) 模式正常工作")
            print("✅ breakout_close (突破收盤價) 模式正常工作") 
            print("✅ breakout_low (最低點+5點) 模式正常工作")
            print("\n🎯 修復完全成功！現在GUI的進場價格模式選項都能正常使用")
        else:
            print("⚠️  所有進場模式都能執行，但結果相同")
            print("🔍 可能需要進一步檢查進場邏輯的實現")
    else:
        print(f"⚠️  部分修復成功：{len(successful_modes)}/3 個模式正常工作")
        if failed_modes:
            print(f"❌ 仍有問題：{', '.join(failed_modes)} 失敗")
    
    print("\n" + "=" * 80)

if __name__ == "__main__":
    test_entry_price_modes()
