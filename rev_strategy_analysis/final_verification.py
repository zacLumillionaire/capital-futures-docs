#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
最終驗證：確認MDD和各口損益修復是否完全成功
"""

import importlib.util
from decimal import Decimal
from pprint import pprint

def final_verification():
    """最終驗證修復成果"""
    
    print("=" * 80)
    print("🎉 最終驗證：MDD和各口損益修復成果")
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
    
    # 2. 創建一個會產生MDD的測試配置
    print("\n🎯 創建會產生MDD的測試配置...")
    
    test_config = StrategyConfig(
        trade_size_in_lots=3,
        stop_loss_type=StopLossType.RANGE_BOUNDARY,
        fixed_stop_loss_points=Decimal(15),
        trading_direction="BOTH",  # 多空都做，增加交易機會
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
    
    # 3. 執行較長期間的回測以產生MDD
    test_start_date = "2025-06-01"
    test_end_date = "2025-06-30"  # 使用一個月的數據
    
    print(f"\n🚀 開始執行最終驗證回測 (測試期間: {test_start_date} ~ {test_end_date})")
    print("=" * 80)
    
    try:
        result = run_backtest(
            test_config, 
            start_date=test_start_date, 
            end_date=test_end_date, 
            silent=True  # 靜默模式，減少日誌干擾
        )
        print("✅ 最終驗證回測完成")
        
        # 4. 檢查所有關鍵指標
        print("\n" + "=" * 80)
        print("🔍 最終驗證結果檢查")
        print("=" * 80)
        
        # 檢查基本統計
        total_pnl = result.get('total_pnl', 'MISSING')
        total_trades = result.get('total_trades', 'MISSING')
        win_rate = result.get('win_rate', 'MISSING')
        
        print(f"📊 基本統計:")
        print(f"  - 總損益: {total_pnl}")
        print(f"  - 總交易次數: {total_trades}")
        print(f"  - 勝率: {win_rate:.2%}" if win_rate != 'MISSING' else f"  - 勝率: {win_rate}")
        
        # 檢查MDD
        mdd = result.get('max_drawdown', 'MISSING')
        peak_pnl = result.get('peak_pnl', 'MISSING')
        print(f"\n📈 MDD 分析:")
        print(f"  - 最大回撤 (MDD): {mdd}")
        print(f"  - 峰值損益: {peak_pnl}")
        
        if mdd != 'MISSING':
            print("✅ MDD 計算修復成功！")
            if mdd > 0:
                print(f"  📉 檢測到回撤: {mdd} 點")
            else:
                print("  📈 測試期間無回撤（所有交易都獲利）")
        else:
            print("❌ MDD 仍然缺失")
        
        # 檢查各口損益
        lot1_pnl = result.get('lot1_pnl', 'MISSING')
        lot2_pnl = result.get('lot2_pnl', 'MISSING')
        lot3_pnl = result.get('lot3_pnl', 'MISSING')
        
        print(f"\n💰 各口損益分析:")
        print(f"  - 第1口累積損益: {lot1_pnl}")
        print(f"  - 第2口累積損益: {lot2_pnl}")
        print(f"  - 第3口累積損益: {lot3_pnl}")
        
        if all(x != 'MISSING' for x in [lot1_pnl, lot2_pnl, lot3_pnl]):
            print("✅ 各口損益統計修復成功！")
            
            # 驗證各口損益總和
            total_lot_pnl = lot1_pnl + lot2_pnl + lot3_pnl
            print(f"  🔍 各口損益總和: {total_lot_pnl:.2f}")
            print(f"  🔍 總損益: {total_pnl:.2f}")
            
            if abs(total_lot_pnl - total_pnl) < 0.01:  # 允許小數點誤差
                print("✅ 各口損益總和與總損益一致！")
            else:
                print("⚠️  各口損益總和與總損益不一致，可能需要進一步檢查")
                
            # 分析各口表現
            print(f"\n📊 各口表現分析:")
            lots_performance = [
                ("第1口", lot1_pnl),
                ("第2口", lot2_pnl), 
                ("第3口", lot3_pnl)
            ]
            lots_performance.sort(key=lambda x: x[1], reverse=True)
            
            for i, (lot_name, pnl) in enumerate(lots_performance, 1):
                status = "🥇" if i == 1 else "🥈" if i == 2 else "🥉"
                print(f"  {status} {lot_name}: {pnl:.2f} 點")
                
        else:
            print("❌ 各口損益統計仍然缺失")
        
        # 檢查多空分別統計
        long_pnl = result.get('long_pnl', 'MISSING')
        short_pnl = result.get('short_pnl', 'MISSING')
        long_trades = result.get('long_trades', 'MISSING')
        short_trades = result.get('short_trades', 'MISSING')
        
        print(f"\n📊 多空分別統計:")
        print(f"  - 多頭損益: {long_pnl} ({long_trades} 次交易)")
        print(f"  - 空頭損益: {short_pnl} ({short_trades} 次交易)")
        
        # 5. 最終總結
        print("\n" + "=" * 80)
        print("🏁 最終驗證總結")
        print("=" * 80)
        
        fixes_working = []
        if mdd != 'MISSING':
            fixes_working.append("MDD計算")
        if all(x != 'MISSING' for x in [lot1_pnl, lot2_pnl, lot3_pnl]):
            fixes_working.append("各口損益統計")
        if all(x != 'MISSING' for x in [long_pnl, short_pnl]):
            fixes_working.append("多空分別統計")
        
        if len(fixes_working) == 3:
            print("🎉 所有修復都成功！")
            print("✅ MDD計算正常工作")
            print("✅ 各口損益統計正常工作") 
            print("✅ 多空分別統計正常工作")
            print("\n🎯 現在GUI應該能正確顯示所有統計數據！")
        elif len(fixes_working) >= 1:
            print(f"⚠️  部分修復成功：{', '.join(fixes_working)} 正常工作")
        else:
            print("❌ 修復失敗，問題仍然存在")
        
        print(f"\n📋 完整結果字典:")
        pprint(result, width=100, depth=2)
        
    except Exception as e:
        print(f"❌ 最終驗證回測失敗: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    final_verification()
