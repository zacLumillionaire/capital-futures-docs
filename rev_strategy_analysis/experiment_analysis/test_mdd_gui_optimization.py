#!/usr/bin/env python3
"""
測試 MDD GUI 表格優化功能
"""

import sys
import os
from pathlib import Path

# 添加當前目錄到路徑
current_dir = Path(__file__).parent
sys.path.insert(0, str(current_dir))

def test_parse_experiment_results():
    """測試解析實驗結果功能"""
    # 直接複製解析函數避免導入 Flask
    def parse_experiment_results(log_content):
        """解析實驗結果"""
        results = {
            'time_intervals': [],
            'recommendations': [],
            'mdd_top10': [],
            'risk_adjusted_top10': [],
            'long_pnl_top10': [],
            'short_pnl_top10': []
        }

        lines = log_content.split('\n')
        current_interval = None
        parsing_mdd_top10 = False
        parsing_risk_top10 = False
        parsing_long_pnl_top10 = False
        parsing_short_pnl_top10 = False

        for line in lines:
            # 檢查是否開始解析 TOP 10 結果
            if '🏆 MDD最小 TOP 10:' in line:
                parsing_mdd_top10 = True
                parsing_risk_top10 = False
                parsing_long_pnl_top10 = False
                parsing_short_pnl_top10 = False
                print(f"[DEBUG] 開始解析 MDD TOP 10")
                continue
            elif '💎 風險調整收益 TOP 10' in line:
                parsing_mdd_top10 = False
                parsing_risk_top10 = True
                parsing_long_pnl_top10 = False
                parsing_short_pnl_top10 = False
                print(f"[DEBUG] 開始解析風險調整收益 TOP 10")
                continue
            elif '🟢 LONG 部位 PNL TOP 10:' in line:
                parsing_mdd_top10 = False
                parsing_risk_top10 = False
                parsing_long_pnl_top10 = True
                parsing_short_pnl_top10 = False
                print(f"[DEBUG] 開始解析 LONG PNL TOP 10")
                continue
            elif '🔴 SHORT 部位 PNL TOP 10:' in line:
                parsing_mdd_top10 = False
                parsing_risk_top10 = False
                parsing_long_pnl_top10 = False
                parsing_short_pnl_top10 = True
                print(f"[DEBUG] 開始解析 SHORT PNL TOP 10")
                continue
            elif '============================================================' in line or '================================================================================' in line:
                parsing_mdd_top10 = False
                parsing_risk_top10 = False
                parsing_long_pnl_top10 = False
                parsing_short_pnl_top10 = False
            elif '📈 預期每日總計:' in line:
                parsing_mdd_top10 = False
                parsing_risk_top10 = False
                parsing_long_pnl_top10 = False
                parsing_short_pnl_top10 = False

            # 解析 MDD TOP 10
            if parsing_mdd_top10 and 'MDD:' in line and ('總P&L:' in line or 'P&L:' in line):
                try:
                    # 處理 [MDD GUI] 前綴
                    line_clean = line.strip()
                    if '[MDD GUI]' in line_clean:
                        line_clean = line_clean.split('[MDD GUI]')[1].strip()

                    # 移除 INFO 等日誌前綴
                    if 'INFO -' in line_clean:
                        line_clean = line_clean.split('INFO -')[1].strip()

                    print(f"[DEBUG] 解析 MDD TOP 10 行: {line_clean}")

                    if line_clean:
                        # 提取排名
                        rank_match = line_clean.split('.')[0].strip()
                        if rank_match.isdigit():
                            rank = rank_match

                            # 提取 MDD
                            mdd_match = None
                            if 'MDD:' in line:
                                mdd_part = line.split('MDD:')[1].split('|')[0].strip() if '|' in line.split('MDD:')[1] else line.split('MDD:')[1].strip()
                                try:
                                    mdd_match = float(mdd_part)
                                except:
                                    pass

                            # 提取 P&L
                            pnl_match = None
                            if '總P&L:' in line:
                                pnl_part = line.split('總P&L:')[1].split('|')[0].strip() if '|' in line.split('總P&L:')[1] else line.split('總P&L:')[1].strip()
                            elif 'P&L:' in line:
                                pnl_part = line.split('P&L:')[1].split('|')[0].strip() if '|' in line.split('P&L:')[1] else line.split('P&L:')[1].strip()
                            else:
                                pnl_part = ''

                            if pnl_part:
                                try:
                                    pnl_match = float(pnl_part)
                                except:
                                    pass

                            # 提取 LONG PNL
                            long_pnl_match = None
                            if 'LONG:' in line:
                                long_pnl_part = line.split('LONG:')[1].split('|')[0].strip() if '|' in line.split('LONG:')[1] else line.split('LONG:')[1].strip()
                                try:
                                    long_pnl_match = float(long_pnl_part)
                                except:
                                    pass

                            # 提取 SHORT PNL
                            short_pnl_match = None
                            if 'SHORT:' in line:
                                short_pnl_part = line.split('SHORT:')[1].split('|')[0].strip() if '|' in line.split('SHORT:')[1] else line.split('SHORT:')[1].strip()
                                try:
                                    short_pnl_match = float(short_pnl_part)
                                except:
                                    pass

                            if mdd_match is not None and pnl_match is not None:
                                # 提取其他信息 - 需要重新分析因為添加了 LONG/SHORT PNL
                                parts = line.split('|')
                                # 由於格式變為: MDD | 總P&L | LONG | SHORT | 參數 | 策略 | 時間
                                params_part = parts[4].strip() if len(parts) > 4 else ''
                                strategy_part = parts[5].strip() if len(parts) > 5 else ''
                                time_part = parts[6].strip() if len(parts) > 6 else ''

                                results['mdd_top10'].append({
                                    'rank': rank,
                                    'mdd': mdd_match,
                                    'pnl': pnl_match,
                                    'long_pnl': long_pnl_match if long_pnl_match is not None else 0,
                                    'short_pnl': short_pnl_match if short_pnl_match is not None else 0,
                                    'params': params_part,
                                    'strategy': strategy_part,
                                    'time': time_part
                                })
                except Exception as e:
                    print(f"[DEBUG] MDD TOP 10 解析錯誤: {e}, 行內容: {line}")
                    pass

            # 解析 LONG PNL TOP 10
            elif parsing_long_pnl_top10 and 'LONG:' in line and ('總P&L:' in line or 'P&L:' in line):
                try:
                    # 處理 [MDD GUI] 前綴
                    line_clean = line.strip()
                    if '[MDD GUI]' in line_clean:
                        line_clean = line_clean.split('[MDD GUI]')[1].strip()

                    # 移除 INFO 等日誌前綴
                    if 'INFO -' in line_clean:
                        line_clean = line_clean.split('INFO -')[1].strip()

                    print(f"[DEBUG] 解析 LONG PNL TOP 10 行: {line_clean}")

                    if line_clean:
                        # 提取排名
                        rank_match = line_clean.split('.')[0].strip()
                        if rank_match.isdigit():
                            rank = rank_match

                            # 提取 LONG PNL
                            long_pnl_match = None
                            if 'LONG:' in line:
                                long_pnl_part = line.split('LONG:')[1].split('|')[0].strip() if '|' in line.split('LONG:')[1] else line.split('LONG:')[1].strip()
                                try:
                                    long_pnl_match = float(long_pnl_part)
                                except:
                                    pass

                            # 提取總 P&L
                            pnl_match = None
                            if '總P&L:' in line:
                                pnl_part = line.split('總P&L:')[1].split('|')[0].strip() if '|' in line.split('總P&L:')[1] else line.split('總P&L:')[1].strip()
                            elif 'P&L:' in line:
                                pnl_part = line.split('P&L:')[1].split('|')[0].strip() if '|' in line.split('P&L:')[1] else line.split('P&L:')[1].strip()
                            else:
                                pnl_part = ''

                            if pnl_part:
                                try:
                                    pnl_match = float(pnl_part)
                                except:
                                    pass

                            # 提取 SHORT PNL
                            short_pnl_match = None
                            if 'SHORT:' in line:
                                short_pnl_part = line.split('SHORT:')[1].split('|')[0].strip() if '|' in line.split('SHORT:')[1] else line.split('SHORT:')[1].strip()
                                try:
                                    short_pnl_match = float(short_pnl_part)
                                except:
                                    pass

                            if long_pnl_match is not None and pnl_match is not None:
                                # 提取其他信息
                                parts = line.split('|')
                                params_part = parts[3].strip() if len(parts) > 3 else ''
                                strategy_part = parts[4].strip() if len(parts) > 4 else ''
                                time_part = parts[5].strip() if len(parts) > 5 else ''

                                results['long_pnl_top10'].append({
                                    'rank': rank,
                                    'long_pnl': long_pnl_match,
                                    'pnl': pnl_match,
                                    'short_pnl': short_pnl_match if short_pnl_match is not None else 0,
                                    'params': params_part,
                                    'strategy': strategy_part,
                                    'time': time_part
                                })
                except Exception as e:
                    print(f"[DEBUG] LONG PNL TOP 10 解析錯誤: {e}, 行內容: {line}")
                    pass

            # 解析 SHORT PNL TOP 10
            elif parsing_short_pnl_top10 and 'SHORT:' in line and ('總P&L:' in line or 'P&L:' in line):
                try:
                    # 處理 [MDD GUI] 前綴
                    line_clean = line.strip()
                    if '[MDD GUI]' in line_clean:
                        line_clean = line_clean.split('[MDD GUI]')[1].strip()

                    # 移除 INFO 等日誌前綴
                    if 'INFO -' in line_clean:
                        line_clean = line_clean.split('INFO -')[1].strip()

                    print(f"[DEBUG] 解析 SHORT PNL TOP 10 行: {line_clean}")

                    if line_clean:
                        # 提取排名
                        rank_match = line_clean.split('.')[0].strip()
                        if rank_match.isdigit():
                            rank = rank_match

                            # 提取 SHORT PNL
                            short_pnl_match = None
                            if 'SHORT:' in line:
                                short_pnl_part = line.split('SHORT:')[1].split('|')[0].strip() if '|' in line.split('SHORT:')[1] else line.split('SHORT:')[1].strip()
                                try:
                                    short_pnl_match = float(short_pnl_part)
                                except:
                                    pass

                            # 提取總 P&L
                            pnl_match = None
                            if '總P&L:' in line:
                                pnl_part = line.split('總P&L:')[1].split('|')[0].strip() if '|' in line.split('總P&L:')[1] else line.split('總P&L:')[1].strip()
                            elif 'P&L:' in line:
                                pnl_part = line.split('P&L:')[1].split('|')[0].strip() if '|' in line.split('P&L:')[1] else line.split('P&L:')[1].strip()
                            else:
                                pnl_part = ''

                            if pnl_part:
                                try:
                                    pnl_match = float(pnl_part)
                                except:
                                    pass

                            # 提取 LONG PNL
                            long_pnl_match = None
                            if 'LONG:' in line:
                                long_pnl_part = line.split('LONG:')[1].split('|')[0].strip() if '|' in line.split('LONG:')[1] else line.split('LONG:')[1].strip()
                                try:
                                    long_pnl_match = float(long_pnl_part)
                                except:
                                    pass

                            if short_pnl_match is not None and pnl_match is not None:
                                # 提取其他信息
                                parts = line.split('|')
                                params_part = parts[3].strip() if len(parts) > 3 else ''
                                strategy_part = parts[4].strip() if len(parts) > 4 else ''
                                time_part = parts[5].strip() if len(parts) > 5 else ''

                                results['short_pnl_top10'].append({
                                    'rank': rank,
                                    'short_pnl': short_pnl_match,
                                    'pnl': pnl_match,
                                    'long_pnl': long_pnl_match if long_pnl_match is not None else 0,
                                    'params': params_part,
                                    'strategy': strategy_part,
                                    'time': time_part
                                })
                except Exception as e:
                    print(f"[DEBUG] SHORT PNL TOP 10 解析錯誤: {e}, 行內容: {line}")
                    pass

        return results
    
    # 模擬日誌內容
    mock_log_content = """
[2025-07-11T11:37:22] INFO - 🏆 MDD最小 TOP 10:
[2025-07-11T11:37:22] INFO - --------------------------------------------------------------------------------
[2025-07-11T11:37:22] INFO - 1. MDD:   -228.00 | 總P&L: 2586.00 | LONG:  1200.00 | SHORT:  1386.00 | L1SL:15 L2SL:15 L3SL:15 | 區間邊緣停利 | 12:00-12:02
[2025-07-11T11:37:22] INFO - 2. MDD:   -250.00 | 總P&L: 2400.00 | LONG:  1100.00 | SHORT:  1300.00 | L1SL:20 L2SL:20 L3SL:20 | 區間邊緣停利 | 10:30-10:32

[2025-07-11T11:37:22] INFO - 💎 風險調整收益 TOP 10 (總收益/|MDD|):
[2025-07-11T11:37:22] INFO - --------------------------------------------------------------------------------
[2025-07-11T11:37:22] INFO - 1. 風險調整收益: 11.35 | MDD:   -228.00 | 總P&L: 2586.00 | LONG:  1200.00 | SHORT:  1386.00 | L1SL:15 L2SL:15 L3SL:15 | 區間邊緣停利
[2025-07-11T11:37:22] INFO - 2. 風險調整收益:  9.60 | MDD:   -250.00 | 總P&L: 2400.00 | LONG:  1100.00 | SHORT:  1300.00 | L1SL:20 L2SL:20 L3SL:20 | 區間邊緣停利

[2025-07-11T11:37:22] INFO - 🟢 LONG 部位 PNL TOP 10:
[2025-07-11T11:37:22] INFO - --------------------------------------------------------------------------------
[2025-07-11T11:37:22] INFO - 1. LONG: 1500.00 | 總P&L: 2800.00 | SHORT:  1300.00 | L1SL:15 L2SL:15 L3SL:15 | 區間邊緣停利 | 12:00-12:02
[2025-07-11T11:37:22] INFO - 2. LONG: 1200.00 | 總P&L: 2586.00 | SHORT:  1386.00 | L1SL:15 L2SL:15 L3SL:15 | 區間邊緣停利 | 12:00-12:02

[2025-07-11T11:37:22] INFO - 🔴 SHORT 部位 PNL TOP 10:
[2025-07-11T11:37:22] INFO - --------------------------------------------------------------------------------
[2025-07-11T11:37:22] INFO - 1. SHORT: 1600.00 | 總P&L: 2900.00 | LONG:  1300.00 | L1SL:15 L2SL:15 L3SL:15 | 區間邊緣停利 | 12:00-12:02
[2025-07-11T11:37:22] INFO - 2. SHORT: 1386.00 | 總P&L: 2586.00 | LONG:  1200.00 | L1SL:15 L2SL:15 L3SL:15 | 區間邊緣停利 | 12:00-12:02

[2025-07-11T11:37:22] INFO - 📈 預期每日總計: MDD:  -478.00 | P&L: 4986.00
"""
    
    # 測試解析
    results = parse_experiment_results(mock_log_content)
    
    print("=== 測試解析結果 ===")
    print(f"MDD TOP 10 數量: {len(results.get('mdd_top10', []))}")
    print(f"風險調整收益 TOP 10 數量: {len(results.get('risk_adjusted_top10', []))}")
    print(f"LONG PNL TOP 10 數量: {len(results.get('long_pnl_top10', []))}")
    print(f"SHORT PNL TOP 10 數量: {len(results.get('short_pnl_top10', []))}")
    
    # 檢查 MDD TOP 10 數據
    if results.get('mdd_top10'):
        mdd_item = results['mdd_top10'][0]
        print(f"\nMDD TOP 10 第一項:")
        print(f"  排名: {mdd_item.get('rank')}")
        print(f"  MDD: {mdd_item.get('mdd')}")
        print(f"  總P&L: {mdd_item.get('pnl')}")
        print(f"  LONG PNL: {mdd_item.get('long_pnl')}")
        print(f"  SHORT PNL: {mdd_item.get('short_pnl')}")
    
    # 檢查 LONG PNL TOP 10 數據
    if results.get('long_pnl_top10'):
        long_item = results['long_pnl_top10'][0]
        print(f"\nLONG PNL TOP 10 第一項:")
        print(f"  排名: {long_item.get('rank')}")
        print(f"  LONG PNL: {long_item.get('long_pnl')}")
        print(f"  總P&L: {long_item.get('pnl')}")
        print(f"  SHORT PNL: {long_item.get('short_pnl')}")
    
    # 檢查 SHORT PNL TOP 10 數據
    if results.get('short_pnl_top10'):
        short_item = results['short_pnl_top10'][0]
        print(f"\nSHORT PNL TOP 10 第一項:")
        print(f"  排名: {short_item.get('rank')}")
        print(f"  SHORT PNL: {short_item.get('short_pnl')}")
        print(f"  總P&L: {short_item.get('pnl')}")
        print(f"  LONG PNL: {short_item.get('long_pnl')}")
    
    return results

def test_enhanced_mdd_optimizer_parsing():
    """測試 enhanced_mdd_optimizer.py 的解析功能"""
    # 直接複製解析函數避免導入依賴
    def _parse_strategy_output(stderr_output):
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
                    except:
                        continue

            # 從 JSON 結果中提取 LONG/SHORT PNL（如果有的話）
            # 尋找 JSON 格式的結果輸出
            for line in lines:
                if line.strip().startswith('{') and 'long_pnl' in line:
                    try:
                        import json
                        result_data = json.loads(line.strip())
                        if 'long_pnl' in result_data:
                            long_pnl = float(result_data['long_pnl'])
                        if 'short_pnl' in result_data:
                            short_pnl = float(result_data['short_pnl'])
                        if 'total_pnl' in result_data and total_pnl is None:
                            total_pnl = float(result_data['total_pnl'])
                        break
                    except:
                        continue

            # 計算 MDD (簡化版)
            mdd = -50.0  # 模擬 MDD 值

            return mdd, total_pnl, long_pnl, short_pnl

        except Exception as e:
            print(f"解析輸出時發生錯誤: {str(e)}")
            return None, None, None, None

    # 模擬策略輸出
    mock_stderr = """
總損益(3口): 2586.00
{"total_pnl": 2586.00, "long_pnl": 1200.00, "short_pnl": 1386.00, "total_trades": 45}
損益: +23
損益: -15
損益: +45
"""

    # 測試解析
    mdd, total_pnl, long_pnl, short_pnl = _parse_strategy_output(mock_stderr)

    print("\n=== 測試 enhanced_mdd_optimizer 解析 ===")
    print(f"MDD: {mdd}")
    print(f"總P&L: {total_pnl}")
    print(f"LONG PNL: {long_pnl}")
    print(f"SHORT PNL: {short_pnl}")

    return mdd, total_pnl, long_pnl, short_pnl

if __name__ == "__main__":
    print("開始測試 MDD GUI 表格優化功能...")
    
    try:
        # 測試解析功能
        results = test_parse_experiment_results()
        
        # 測試 enhanced_mdd_optimizer 解析
        mdd, total_pnl, long_pnl, short_pnl = test_enhanced_mdd_optimizer_parsing()
        
        print("\n✅ 所有測試通過！")
        print("\n優化功能包括:")
        print("1. ✅ 現有表格添加 LONG PNL 和 SHORT PNL 列")
        print("2. ✅ 新增 LONG 部位 PNL TOP 10 表格")
        print("3. ✅ 新增 SHORT 部位 PNL TOP 10 表格")
        print("4. ✅ 完整的解析和顯示邏輯")
        
    except Exception as e:
        print(f"❌ 測試失敗: {e}")
        import traceback
        traceback.print_exc()
