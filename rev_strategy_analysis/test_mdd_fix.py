#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
測試MDD和各口損益修復
"""

import importlib.util
from decimal import Decimal
from pprint import pprint

def test_mdd_and_lot_pnl_fix():
    """測試MDD和各口損益修復是否成功"""
    
    print("=" * 80)
    print("🧪 測試MDD和各口損益修復")
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
    
    # 2. 創建測試配置
    print("\n🎯 創建測試配置...")
    
    test_config = StrategyConfig(
        trade_size_in_lots=3,
        stop_loss_type=StopLossType.RANGE_BOUNDARY,
        fixed_stop_loss_points=Decimal(15),
        trading_direction="BOTH",
        entry_price_mode="range_boundary",
        lot_rules=[
            LotRule(
                use_trailing_stop=True,
                trailing_activation=Decimal(14),
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
    
    # 3. 執行回測測試
    test_start_date = "2024-11-04"
    test_end_date = "2024-11-08"  # 使用較短的測試期間
    
    print(f"\n🚀 開始執行修復測試 (測試期間: {test_start_date} ~ {test_end_date})")
    print("=" * 80)
    
    try:
        result = run_backtest(
            test_config, 
            start_date=test_start_date, 
            end_date=test_end_date, 
            silent=True  # 靜默模式，減少日誌干擾
        )
        print("✅ 修復後回測完成")
        print("📊 完整結果字典:")
        pprint(result, width=100, depth=3)
        
        # 4. 檢查修復結果
        print("\n" + "=" * 80)
        print("🔍 修復結果檢查")
        print("=" * 80)
        
        # 檢查MDD
        mdd = result.get('max_drawdown', 'MISSING')
        peak_pnl = result.get('peak_pnl', 'MISSING')
        print(f"📈 最大回撤 (MDD): {mdd}")
        print(f"📈 峰值損益: {peak_pnl}")
        
        if mdd != 'MISSING' and mdd != 0:
            print("✅ MDD 計算修復成功！")
        elif mdd == 0:
            print("⚠️  MDD 為 0，可能是測試期間沒有回撤")
        else:
            print("❌ MDD 仍然缺失")
        
        # 檢查各口損益
        lot1_pnl = result.get('lot1_pnl', 'MISSING')
        lot2_pnl = result.get('lot2_pnl', 'MISSING')
        lot3_pnl = result.get('lot3_pnl', 'MISSING')
        
        print(f"💰 第1口累積損益: {lot1_pnl}")
        print(f"💰 第2口累積損益: {lot2_pnl}")
        print(f"💰 第3口累積損益: {lot3_pnl}")
        
        if all(x != 'MISSING' for x in [lot1_pnl, lot2_pnl, lot3_pnl]):
            print("✅ 各口損益統計修復成功！")
            
            # 驗證各口損益總和
            total_lot_pnl = lot1_pnl + lot2_pnl + lot3_pnl
            total_pnl = result.get('total_pnl', 0)
            print(f"🔍 各口損益總和: {total_lot_pnl:.2f}")
            print(f"🔍 總損益: {total_pnl:.2f}")
            
            if abs(total_lot_pnl - total_pnl) < 0.01:  # 允許小數點誤差
                print("✅ 各口損益總和與總損益一致！")
            else:
                print("⚠️  各口損益總和與總損益不一致，可能需要進一步檢查")
        else:
            print("❌ 各口損益統計仍然缺失")
        
        # 5. 總結
        print("\n" + "=" * 80)
        print("🏁 修復測試總結")
        print("=" * 80)
        
        fixes_working = []
        if mdd != 'MISSING':
            fixes_working.append("MDD計算")
        if all(x != 'MISSING' for x in [lot1_pnl, lot2_pnl, lot3_pnl]):
            fixes_working.append("各口損益統計")
        
        if len(fixes_working) == 2:
            print("🎉 所有修復都成功！MDD和各口損益統計現在都正常工作")
        elif len(fixes_working) == 1:
            print(f"⚠️  部分修復成功：{fixes_working[0]} 正常工作")
        else:
            print("❌ 修復失敗，問題仍然存在")
        
    except Exception as e:
        print(f"❌ 修復測試失敗: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_mdd_and_lot_pnl_fix()
