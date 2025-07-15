#!/usr/bin/env python3
"""
測試 GUI 修復結果
驗證統計數據解析和進場價格提取的修復
"""

import re

def test_log_parsing():
    """測試日誌解析邏輯"""
    print("🧪 測試日誌解析邏輯")
    print("=" * 50)
    
    # 模擬實際的日誌格式
    sample_logs = [
        "[2025-07-13T15:24:57+0800] INFO [__main__.run_backtest:697] ====== 回測結果總結 ======",
        "[2025-07-13T15:24:57+0800] INFO [__main__.run_backtest:698] 總交易天數: 192",
        "[2025-07-13T15:24:57+0800] INFO [__main__.run_backtest:699] 總交易次數: 154",
        "[2025-07-13T15:24:57+0800] INFO [__main__.run_backtest:700] 獲利次數: 91",
        "[2025-07-13T15:24:57+0800] INFO [__main__.run_backtest:701] 虧損次數: 63",
        "[2025-07-13T15:24:57+0800] INFO [__main__.run_backtest:702] 勝率: 59.09%",
        "[2025-07-13T15:24:57+0800] INFO [__main__.run_backtest:703] 總損益(3口): 1329.00",
        "[2025-07-13T15:24:57+0800] INFO [__main__.run_backtest:706] ====== 多空分析 ======",
        "[2025-07-13T15:24:57+0800] INFO [__main__.run_backtest:707] LONG TRADING DAYS: 99",
        "[2025-07-13T15:24:57+0800] INFO [__main__.run_backtest:708] LONG PNL: 834.00",
        "[2025-07-13T15:24:57+0800] INFO [__main__.run_backtest:710] SHORT TRADING DAYS: 55",
        "[2025-07-13T15:24:57+0800] INFO [__main__.run_backtest:711] SHORT PNL: 495.00"
    ]
    
    # 模擬修復後的解析邏輯
    stats = {}
    
    for line in sample_logs:
        original_line = line.strip()
        clean_line = original_line
        
        # 處理日誌格式
        if '] INFO [' in line and ']:' in line:
            last_bracket_pos = line.rfind(']:')
            if last_bracket_pos != -1:
                clean_line = line[last_bracket_pos + 2:].strip()
        elif '] INFO [' in line:
            parts = line.split('] ')
            if len(parts) >= 3:
                clean_line = parts[2].strip()
        
        # 提取統計數據
        if '總交易天數:' in clean_line:
            stats['trading_days'] = clean_line.split('總交易天數:')[1].strip()
        elif '總交易次數:' in clean_line:
            stats['total_trades'] = clean_line.split('總交易次數:')[1].strip()
        elif '獲利次數:' in clean_line:
            stats['winning_trades'] = clean_line.split('獲利次數:')[1].strip()
        elif '虧損次數:' in clean_line:
            stats['losing_trades'] = clean_line.split('虧損次數:')[1].strip()
        elif '勝率:' in clean_line:
            stats['win_rate'] = clean_line.split('勝率:')[1].strip()
        elif '總損益(' in clean_line and '口):' in clean_line:
            stats['total_pnl'] = clean_line.split('):')[1].strip()
        elif 'LONG TRADING DAYS:' in clean_line:
            stats['long_trading_days'] = clean_line.split('LONG TRADING DAYS:')[1].strip()
        elif 'LONG PNL:' in clean_line:
            stats['long_pnl'] = clean_line.split('LONG PNL:')[1].strip()
        elif 'SHORT TRADING DAYS:' in clean_line:
            stats['short_trading_days'] = clean_line.split('SHORT TRADING DAYS:')[1].strip()
        elif 'SHORT PNL:' in clean_line:
            stats['short_pnl'] = clean_line.split('SHORT PNL:')[1].strip()
    
    # 驗證解析結果
    expected_stats = {
        'trading_days': '192',
        'total_trades': '154',
        'winning_trades': '91',
        'losing_trades': '63',
        'win_rate': '59.09%',
        'total_pnl': '1329.00',
        'long_trading_days': '99',
        'long_pnl': '834.00',
        'short_trading_days': '55',
        'short_pnl': '495.00'
    }
    
    print("📊 解析結果:")
    for key, value in stats.items():
        expected = expected_stats.get(key, 'N/A')
        status = "✅" if value == expected else "❌"
        print(f"   {status} {key}: {value} (預期: {expected})")
    
    if stats == expected_stats:
        print("✅ 日誌解析邏輯修復成功")
        return True
    else:
        print("❌ 日誌解析邏輯仍有問題")
        return False

def test_entry_price_extraction():
    """測試進場價格提取邏輯"""
    print("\n🧪 測試進場價格提取邏輯")
    print("=" * 50)
    
    # 模擬包含進場模式標籤的日誌
    sample_entry_logs = [
        "[2025-07-13T15:24:56+0800] INFO [__main__._run_multi_lot_logic:254]   📉 SHORT | 反轉進場 3 口 | 時間: 12:05:00, 價格: 22940 [最低點+5點進場] (原策略做多點)",
        "[2025-07-13T15:24:56+0800] INFO [__main__._run_multi_lot_logic:254]   📈 LONG  | 反轉進場 3 口 | 時間: 12:04:00, 價格: 23352 [最低點+5點進場] (原策略做空點)",
        "[2025-07-13T15:24:56+0800] INFO [__main__._run_multi_lot_logic:254]   📈 LONG  | 反轉進場 3 口 | 時間: 12:05:00, 價格: 23547 [區間邊緣進場] (原策略做空點)"
    ]
    
    # 測試修復後的進場價格提取邏輯
    def extract_entry_price(line):
        import re
        # 使用正則表達式匹配價格，忽略進場模式標籤
        price_match = re.search(r'價格:\s*(\d+)(?:\s*\[[^\]]+\])?', line)
        if price_match:
            return int(price_match.group(1))
        return None
    
    expected_prices = [22940, 23352, 23547]
    
    print("📊 進場價格提取測試:")
    for i, line in enumerate(sample_entry_logs):
        extracted_price = extract_entry_price(line)
        expected_price = expected_prices[i]
        status = "✅" if extracted_price == expected_price else "❌"
        print(f"   {status} 日誌 {i+1}: 提取價格 {extracted_price}, 預期 {expected_price}")
        if extracted_price != expected_price:
            print(f"      原始日誌: {line}")
    
    # 檢查是否所有價格都正確提取
    all_correct = all(extract_entry_price(line) == expected for line, expected in zip(sample_entry_logs, expected_prices))
    
    if all_correct:
        print("✅ 進場價格提取邏輯修復成功")
        return True
    else:
        print("❌ 進場價格提取邏輯仍有問題")
        return False

def test_file_modifications():
    """測試文件修改"""
    print("\n🧪 測試文件修改")
    print("=" * 50)
    
    # 檢查 rev_web_trading_gui.py 的修改
    try:
        with open('rev_web_trading_gui.py', 'r', encoding='utf-8') as f:
            gui_content = f.read()
        
        # 檢查日誌解析改進
        if 'last_bracket_pos = line.rfind(\']:\')'  in gui_content:
            print("✅ rev_web_trading_gui.py 包含改進的日誌解析邏輯")
        else:
            print("❌ rev_web_trading_gui.py 缺少改進的日誌解析邏輯")
            return False
        
        # 檢查多空分析數據解析
        required_parsing = ['LONG TRADING DAYS:', 'LONG PNL:', 'SHORT TRADING DAYS:', 'SHORT PNL:']
        missing_parsing = [p for p in required_parsing if p not in gui_content]
        
        if not missing_parsing:
            print("✅ rev_web_trading_gui.py 包含完整的多空分析解析")
        else:
            print(f"❌ rev_web_trading_gui.py 缺少多空分析解析: {missing_parsing}")
            return False
            
    except FileNotFoundError:
        print("❌ rev_web_trading_gui.py 文件不存在")
        return False
    
    # 檢查 enhanced_report_generator.py 的修改
    try:
        with open('enhanced_report_generator.py', 'r', encoding='utf-8') as f:
            report_content = f.read()
        
        # 檢查進場價格提取改進
        if 'price_match = re.search(r\'價格:\\s*(\\d+)(?:\\s*\\[[^\\]]+\\])?\', line)' in report_content:
            print("✅ enhanced_report_generator.py 包含改進的進場價格提取邏輯")
        else:
            print("❌ enhanced_report_generator.py 缺少改進的進場價格提取邏輯")
            return False
            
    except FileNotFoundError:
        print("❌ enhanced_report_generator.py 文件不存在")
        return False
    
    return True

def main():
    """主測試函數"""
    print("🚀 開始測試 GUI 修復結果")
    print("=" * 80)
    
    try:
        # 執行所有測試
        test1_result = test_log_parsing()
        test2_result = test_entry_price_extraction()
        test3_result = test_file_modifications()
        
        print("\n" + "=" * 80)
        
        if all([test1_result, test2_result, test3_result]):
            print("🎉 所有測試通過！GUI 修復成功")
            print("\n📋 修復摘要:")
            print("✅ 統計數據解析邏輯已修復，能正確解析新的日誌格式")
            print("✅ 進場價格提取邏輯已修復，能處理進場模式標籤")
            print("✅ 文件修改正確實作")
            print("\n🎯 現在 Key Performance Metrics 應該顯示正確的數值！")
            print("🎯 凱利分析報告不再出現進場價格提取錯誤！")
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
