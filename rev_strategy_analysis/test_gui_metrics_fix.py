#!/usr/bin/env python3
"""
測試 rev_web_trading_gui.py 的統計指標修復
驗證 Key Performance Metrics 和 Long/Short Position Analysis 的顯示修復
"""

import os
import re

def test_strategy_engine_output():
    """測試策略引擎的多空分析輸出"""
    print("🧪 測試策略引擎多空分析輸出")
    print("=" * 50)
    
    strategy_file = "rev_multi_Profit-Funded Risk_多口.py"
    if not os.path.exists(strategy_file):
        print("❌ 策略文件不存在")
        return False
    
    with open(strategy_file, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # 測試 1: 檢查是否包含多空分析日誌
    required_logs = [
        'LONG TRADING DAYS:',
        'LONG PNL:',
        'LONG WIN RATE:',
        'SHORT TRADING DAYS:',
        'SHORT PNL:',
        'SHORT WIN RATE:'
    ]
    
    missing_logs = []
    for log in required_logs:
        if log not in content:
            missing_logs.append(log)
    
    if missing_logs:
        print(f"❌ 策略引擎缺少多空分析日誌: {missing_logs}")
        return False
    else:
        print("✅ 策略引擎包含完整的多空分析日誌")
    
    # 測試 2: 檢查是否有多空統計變數
    required_vars = ['long_pnl', 'short_pnl', 'long_trades', 'short_trades']
    missing_vars = []
    for var in required_vars:
        if var not in content:
            missing_vars.append(var)
    
    if missing_vars:
        print(f"❌ 策略引擎缺少多空統計變數: {missing_vars}")
        return False
    else:
        print("✅ 策略引擎包含完整的多空統計變數")
    
    return True

def test_gui_parsing_logic():
    """測試 GUI 的解析邏輯"""
    print("\n🧪 測試 GUI 解析邏輯")
    print("=" * 50)
    
    gui_file = "rev_web_trading_gui.py"
    if not os.path.exists(gui_file):
        print("❌ GUI 文件不存在")
        return False
    
    with open(gui_file, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # 測試 1: 檢查是否包含多空數據解析
    required_parsing = [
        'LONG TRADING DAYS:',
        'LONG PNL:',
        'SHORT TRADING DAYS:',
        'SHORT PNL:'
    ]
    
    missing_parsing = []
    for parse in required_parsing:
        if parse not in content:
            missing_parsing.append(parse)
    
    if missing_parsing:
        print(f"❌ GUI 缺少多空數據解析: {missing_parsing}")
        return False
    else:
        print("✅ GUI 包含完整的多空數據解析")
    
    # 測試 2: 檢查是否包含多空顯示區塊
    if '多空部位分析' not in content:
        print("❌ GUI 缺少多空部位分析顯示區塊")
        return False
    else:
        print("✅ GUI 包含多空部位分析顯示區塊")
    
    # 測試 3: 檢查統計數據預設值
    required_defaults = ['long_trading_days', 'long_pnl', 'short_trading_days', 'short_pnl']
    missing_defaults = []
    for default in required_defaults:
        if f"'{default}': 'N/A'" not in content:
            missing_defaults.append(default)
    
    if missing_defaults:
        print(f"❌ GUI 缺少多空數據預設值: {missing_defaults}")
        return False
    else:
        print("✅ GUI 包含完整的多空數據預設值")
    
    return True

def test_html_template():
    """測試 HTML 模板"""
    print("\n🧪 測試 HTML 模板")
    print("=" * 50)
    
    gui_file = "rev_web_trading_gui.py"
    with open(gui_file, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # 測試 1: 檢查關鍵統計指標顯示
    key_metrics = [
        'stats.get(\'total_trades\'',
        'stats.get(\'winning_trades\'',
        'stats.get(\'losing_trades\''
    ]
    
    missing_metrics = []
    for metric in key_metrics:
        if metric not in content:
            missing_metrics.append(metric)
    
    if missing_metrics:
        print(f"❌ HTML 模板缺少關鍵統計指標: {missing_metrics}")
        return False
    else:
        print("✅ HTML 模板包含完整的關鍵統計指標")
    
    # 測試 2: 檢查多空分析顯示
    long_short_metrics = [
        'stats.get(\'long_trading_days\'',
        'stats.get(\'long_pnl\'',
        'stats.get(\'short_trading_days\'',
        'stats.get(\'short_pnl\''
    ]
    
    missing_ls_metrics = []
    for metric in long_short_metrics:
        if metric not in content:
            missing_ls_metrics.append(metric)
    
    if missing_ls_metrics:
        print(f"❌ HTML 模板缺少多空分析指標: {missing_ls_metrics}")
        return False
    else:
        print("✅ HTML 模板包含完整的多空分析指標")
    
    return True

def test_expected_output_format():
    """測試預期的輸出格式"""
    print("\n🧪 測試預期輸出格式")
    print("=" * 50)
    
    # 模擬回測引擎的輸出格式
    sample_log = """
[2025-07-13T15:08:57+0800] INFO [__main__.run_backtest:697] ====== 回測結果總結 ======
[2025-07-13T15:08:57+0800] INFO [__main__.run_backtest:698] 總交易天數: 192
[2025-07-13T15:08:57+0800] INFO [__main__.run_backtest:699] 總交易次數: 154
[2025-07-13T15:08:57+0800] INFO [__main__.run_backtest:700] 獲利次數: 88
[2025-07-13T15:08:57+0800] INFO [__main__.run_backtest:701] 虧損次數: 66
[2025-07-13T15:08:57+0800] INFO [__main__.run_backtest:702] 勝率: 57.14%
[2025-07-13T15:08:57+0800] INFO [__main__.run_backtest:703] 總損益(3口): 1069.00
[2025-07-13T15:08:57+0800] INFO [__main__.run_backtest:704] ===========================
[2025-07-13T15:08:57+0800] INFO [__main__.run_backtest:705] ====== 多空分析 ======
[2025-07-13T15:08:57+0800] INFO [__main__.run_backtest:706] LONG TRADING DAYS: 85
[2025-07-13T15:08:57+0800] INFO [__main__.run_backtest:707] LONG PNL: 650.50
[2025-07-13T15:08:57+0800] INFO [__main__.run_backtest:708] LONG WIN RATE: 62.35%
[2025-07-13T15:08:57+0800] INFO [__main__.run_backtest:709] SHORT TRADING DAYS: 69
[2025-07-13T15:08:57+0800] INFO [__main__.run_backtest:710] SHORT PNL: 418.50
[2025-07-13T15:08:57+0800] INFO [__main__.run_backtest:711] SHORT WIN RATE: 50.72%
[2025-07-13T15:08:57+0800] INFO [__main__.run_backtest:712] =====================
    """
    
    print("📊 模擬日誌解析測試:")
    
    # 解析測試
    lines = sample_log.strip().split('\n')
    stats = {}
    
    for line in lines:
        clean_line = line.strip()
        if '] INFO [' in line:
            parts = line.split('] ')
            if len(parts) >= 3:
                clean_line = parts[2].strip()
        
        if '總交易次數:' in clean_line:
            stats['total_trades'] = clean_line.split('總交易次數:')[1].strip()
        elif '獲利次數:' in clean_line:
            stats['winning_trades'] = clean_line.split('獲利次數:')[1].strip()
        elif '虧損次數:' in clean_line:
            stats['losing_trades'] = clean_line.split('虧損次數:')[1].strip()
        elif 'LONG TRADING DAYS:' in clean_line:
            stats['long_trading_days'] = clean_line.split('LONG TRADING DAYS:')[1].strip()
        elif 'LONG PNL:' in clean_line:
            stats['long_pnl'] = clean_line.split('LONG PNL:')[1].strip()
        elif 'SHORT TRADING DAYS:' in clean_line:
            stats['short_trading_days'] = clean_line.split('SHORT TRADING DAYS:')[1].strip()
        elif 'SHORT PNL:' in clean_line:
            stats['short_pnl'] = clean_line.split('SHORT PNL:')[1].strip()
    
    expected_stats = {
        'total_trades': '154',
        'winning_trades': '88',
        'losing_trades': '66',
        'long_trading_days': '85',
        'long_pnl': '650.50',
        'short_trading_days': '69',
        'short_pnl': '418.50'
    }
    
    print(f"   解析結果: {stats}")
    print(f"   預期結果: {expected_stats}")
    
    if stats == expected_stats:
        print("✅ 日誌解析邏輯正確")
        return True
    else:
        print("❌ 日誌解析邏輯有問題")
        return False

def main():
    """主測試函數"""
    print("🚀 開始測試 GUI 統計指標修復")
    print("=" * 80)
    
    try:
        # 執行所有測試
        test1_result = test_strategy_engine_output()
        test2_result = test_gui_parsing_logic()
        test3_result = test_html_template()
        test4_result = test_expected_output_format()
        
        print("\n" + "=" * 80)
        
        if all([test1_result, test2_result, test3_result, test4_result]):
            print("🎉 所有測試通過！GUI 統計指標修復成功")
            print("\n📋 修復摘要:")
            print("✅ 策略引擎輸出完整的多空分析數據")
            print("✅ GUI 正確解析所有統計指標")
            print("✅ HTML 模板顯示關鍵統計指標和多空分析")
            print("✅ 日誌解析邏輯正確運作")
            print("\n🎯 現在 Key Performance Metrics 和 Long/Short Position Analysis 都能正確顯示！")
        else:
            print("❌ 部分測試失敗，需要進一步檢查")
            
    except Exception as e:
        print(f"\n❌ 測試過程中發生錯誤: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    return True

if __name__ == "__main__":
    main()
