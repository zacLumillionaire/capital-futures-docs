#!/usr/bin/env python3
"""
測試 JSON 解析邏輯
"""

import json

def test_json_parsing():
    """測試 JSON 解析邏輯"""
    
    # 模擬 exp_rev_multi_Profit-Funded Risk_多口.py 的輸出
    mock_stderr_output = """
2025-07-11 21:08:31,402 - INFO - 🔍 找到 5 個交易日進行回測。
2025-07-11 21:08:31,402 - INFO - 📅 2024-11-04: 無交易
2025-07-11 21:08:31,402 - INFO - 📅 2024-11-05: 無交易
2025-07-11 21:08:31,402 - INFO - 📅 2024-11-06: 
2025-07-11 21:08:31,402 - INFO -   🎯 進場: LONG @ 21850, 時間: 12:01:00
2025-07-11 21:08:31,402 - INFO -   ✅ 第1口區間邊緣停利 | 時間: 12:15:00, 價格: 21900, 損益: +50
2025-07-11 21:08:31,402 - INFO -   ✅ 第2口區間邊緣停利 | 時間: 12:15:00, 價格: 21900, 損益: +50
2025-07-11 21:08:31,402 - INFO -   ✅ 第3口區間邊緣停利 | 時間: 12:15:00, 價格: 21900, 損益: +50
2025-07-11 21:08:31,402 - INFO - 📅 2024-11-07: 
2025-07-11 21:08:31,402 - INFO -   🎯 進場: SHORT @ 21800, 時間: 12:01:00
2025-07-11 21:08:31,402 - INFO -   ✅ 第1口區間邊緣停利 | 時間: 12:15:00, 價格: 21750, 損益: +50
2025-07-11 21:08:31,402 - INFO -   ✅ 第2口區間邊緣停利 | 時間: 12:15:00, 價格: 21750, 損益: +50
2025-07-11 21:08:31,402 - INFO -   ✅ 第3口區間邊緣停利 | 時間: 12:15:00, 價格: 21750, 損益: +50
總損益(3口): 300.00
{"total_pnl": 300.0, "long_pnl": 150.0, "short_pnl": 150.0, "total_trades": 6, "long_trades": 3, "short_trades": 3, "winning_trades": 6, "losing_trades": 0, "long_wins": 3, "short_wins": 3, "win_rate": 1.0, "long_win_rate": 1.0, "short_win_rate": 1.0, "trade_days": 2}
"""

    print("=== 測試 JSON 解析邏輯 ===")
    
    # 模擬 enhanced_mdd_optimizer.py 的解析邏輯
    def parse_strategy_output(stderr_output):
        """解析策略引擎輸出"""
        try:
            lines = stderr_output.strip().split('\n')

            # 提取總損益 - 修正解析邏輯
            total_pnl = None
            long_pnl = None
            short_pnl = None
            
            for line in lines:
                if '總損益(' in line and '):' in line:
                    # 格式: 總損益(3口): -17.00
                    try:
                        parts = line.split('總損益(')
                        if len(parts) > 1:
                            pnl_part = parts[1].split('):')
                            if len(pnl_part) > 1:
                                pnl_str = pnl_part[1].strip()
                                total_pnl = float(pnl_str)
                                print(f"✅ 從日誌解析總損益: {total_pnl}")
                    except Exception as e:
                        print(f"❌ 解析總損益失敗: {e}")
                        continue

            # 從 JSON 結果中提取 LONG/SHORT PNL（如果有的話）
            # 尋找 JSON 格式的結果輸出
            for line in lines:
                print(f"檢查行: {line.strip()[:50]}...")
                if line.strip().startswith('{') and 'long_pnl' in line:
                    print(f"🔍 找到 JSON 行: {line.strip()}")
                    try:
                        result_data = json.loads(line.strip())
                        print(f"✅ JSON 解析成功: {result_data}")
                        
                        if 'long_pnl' in result_data:
                            long_pnl = float(result_data['long_pnl'])
                            print(f"✅ 提取 long_pnl: {long_pnl}")
                        if 'short_pnl' in result_data:
                            short_pnl = float(result_data['short_pnl'])
                            print(f"✅ 提取 short_pnl: {short_pnl}")
                        if 'total_pnl' in result_data and total_pnl is None:
                            total_pnl = float(result_data['total_pnl'])
                            print(f"✅ 從 JSON 更新 total_pnl: {total_pnl}")
                        break
                    except Exception as e:
                        print(f"❌ JSON 解析失敗: {e}")
                        continue

            return total_pnl, long_pnl, short_pnl

        except Exception as e:
            print(f"❌ 解析輸出時發生錯誤: {str(e)}")
            return None, None, None
    
    # 執行測試
    total_pnl, long_pnl, short_pnl = parse_strategy_output(mock_stderr_output)
    
    print(f"\n=== 解析結果 ===")
    print(f"總損益: {total_pnl}")
    print(f"LONG PNL: {long_pnl}")
    print(f"SHORT PNL: {short_pnl}")
    
    # 驗證結果
    if total_pnl == 300.0 and long_pnl == 150.0 and short_pnl == 150.0:
        print("✅ 解析結果正確！")
        return True
    else:
        print("❌ 解析結果不正確！")
        return False

def test_edge_cases():
    """測試邊緣情況"""
    print("\n=== 測試邊緣情況 ===")
    
    # 測試沒有 JSON 的情況
    no_json_output = """
總損益(3口): 150.00
一些其他日誌信息
"""
    
    def parse_strategy_output_simple(stderr_output):
        lines = stderr_output.strip().split('\n')
        total_pnl = None
        long_pnl = None
        short_pnl = None
        
        for line in lines:
            if '總損益(' in line and '):' in line:
                try:
                    parts = line.split('總損益(')
                    if len(parts) > 1:
                        pnl_part = parts[1].split('):')
                        if len(pnl_part) > 1:
                            pnl_str = pnl_part[1].strip()
                            total_pnl = float(pnl_str)
                except:
                    continue
        
        for line in lines:
            if line.strip().startswith('{') and 'long_pnl' in line:
                try:
                    result_data = json.loads(line.strip())
                    if 'long_pnl' in result_data:
                        long_pnl = float(result_data['long_pnl'])
                    if 'short_pnl' in result_data:
                        short_pnl = float(result_data['short_pnl'])
                    break
                except:
                    continue
        
        return total_pnl, long_pnl, short_pnl
    
    total_pnl, long_pnl, short_pnl = parse_strategy_output_simple(no_json_output)
    print(f"沒有 JSON 的情況: total_pnl={total_pnl}, long_pnl={long_pnl}, short_pnl={short_pnl}")
    
    if total_pnl == 150.0 and long_pnl is None and short_pnl is None:
        print("✅ 邊緣情況處理正確")
        return True
    else:
        print("❌ 邊緣情況處理不正確")
        return False

if __name__ == "__main__":
    print("開始測試 JSON 解析邏輯...")
    
    success1 = test_json_parsing()
    success2 = test_edge_cases()
    
    if success1 and success2:
        print("\n🎉 所有測試通過！JSON 解析邏輯正確。")
    else:
        print("\n❌ 測試失敗，需要檢查解析邏輯。")
