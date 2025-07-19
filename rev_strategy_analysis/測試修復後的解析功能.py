#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
測試修復後的解析功能
"""

import sys
import os
import json
from datetime import datetime

def test_parse_function_with_real_data():
    """測試解析函數使用真實數據格式"""
    print("🧪 測試修復後的解析功能（真實數據格式）")
    print("=" * 60)
    
    try:
        # 導入修復後的 mdd_gui 模組
        sys.path.append('experiment_analysis')
        import mdd_gui
        
        # 創建真實格式的測試報告內容
        test_log_content = """
📊 實驗結果報告 (共 4 個實驗)
================================================================================

📊 各時間區間 MDD 最佳前3名:
------------------------------------------------------------

🕐 時間區間: 10:30-10:32
  1. MDD:   50.0 | PNL:  -50.0 | 參數:15/25/35 | 多頭:  10.0 | 空頭: -60.0
  2. MDD:   60.0 | PNL:  -60.0 | 參數:20/30/40 | 多頭:   5.0 | 空頭: -65.0

🕐 時間區間: 12:00-12:02
  1. MDD:   40.0 | PNL:  -40.0 | 參數:15/25/35 | 多頭:  15.0 | 空頭: -55.0

🏆 MDD 最小 TOP 10:
------------------------------------------------------------
 1. 實驗  1 | 時間:10:30-10:32 | MDD:  40.0 | PNL:  -40.0 | 參數:15/25/35 | 多頭:  15.0 | 空頭: -55.0
 2. 實驗  2 | 時間:12:00-12:02 | MDD:  50.0 | PNL:  -50.0 | 參數:20/30/40 | 多頭:  10.0 | 空頭: -60.0

💎 風險調整收益 TOP 10:
------------------------------------------------------------
 1. 實驗  1 | 時間:10:30-10:32 | 風險調整:  1.25 | PNL:  -50.0 | MDD:  40.0 | 參數:15/25/35

🟢 LONG 部位 PNL TOP 10:
------------------------------------------------------------
 1. 實驗  1 | 時間:10:30-10:32 | 多頭PNL:  15.0 | 總PNL:  -40.0 | MDD:  40.0 | 參數:15/25/35

🔴 SHORT 部位 PNL TOP 10:
------------------------------------------------------------
 1. 實驗  1 | 時間:10:30-10:32 | 空頭PNL: -55.0 | 總PNL:  -40.0 | MDD:  40.0 | 參數:15/25/35

============================================================
"""
        
        print("✅ 測試報告內容:")
        print(test_log_content[:300] + "...")
        
        # 執行解析
        parsed_results = mdd_gui.parse_experiment_results(test_log_content)
        
        print("\n📊 解析結果:")
        print(f"  - 時間區間分析: {len(parsed_results.get('time_intervals', []))}")
        print(f"  - MDD TOP 10: {len(parsed_results.get('mdd_top10', []))}")
        print(f"  - 風險調整收益 TOP 10: {len(parsed_results.get('risk_adjusted_top10', []))}")
        print(f"  - LONG PNL TOP 10: {len(parsed_results.get('long_pnl_top10', []))}")
        print(f"  - SHORT PNL TOP 10: {len(parsed_results.get('short_pnl_top10', []))}")
        
        # 詳細檢查時間區間分析
        if parsed_results.get('time_intervals'):
            print(f"\n🕐 時間區間分析詳情:")
            for i, interval in enumerate(parsed_results['time_intervals']):
                print(f"  區間 {i+1}: {interval.get('time', interval.get('interval', 'N/A'))}")
                print(f"    configs 數量: {len(interval.get('configs', []))}")
                print(f"    top3 數量: {len(interval.get('top3', []))}")
                
                # 檢查前端期望的數據結構
                if interval.get('configs'):
                    for j, config in enumerate(interval['configs'][:2]):
                        print(f"      配置{j+1}: 類型={config.get('type')}, MDD={config.get('mdd')}, PNL={config.get('pnl')}")
        
        # 詳細檢查 MDD TOP 10
        if parsed_results.get('mdd_top10'):
            print(f"\n🏆 MDD TOP 10 詳情:")
            for i, item in enumerate(parsed_results['mdd_top10'][:2]):
                print(f"  第{i+1}名:")
                print(f"    排名: {item.get('rank')}")
                print(f"    MDD: {item.get('mdd')}")
                print(f"    PNL: {item.get('pnl')}")
                print(f"    多頭PNL: {item.get('long_pnl')}")
                print(f"    空頭PNL: {item.get('short_pnl')}")
                print(f"    參數: {item.get('params')}")
                print(f"    時間: {item.get('time')}")
                print(f"    策略: {item.get('strategy')}")
        
        # 檢查數據結構是否符合前端期望
        success_checks = []
        
        # 檢查時間區間數據結構
        if parsed_results.get('time_intervals'):
            interval = parsed_results['time_intervals'][0]
            has_time = 'time' in interval
            has_configs = 'configs' in interval
            success_checks.append(f"時間區間結構: time={has_time}, configs={has_configs}")
        
        # 檢查 MDD TOP 10 數據結構
        if parsed_results.get('mdd_top10'):
            item = parsed_results['mdd_top10'][0]
            required_fields = ['rank', 'mdd', 'pnl', 'long_pnl', 'short_pnl', 'params', 'strategy', 'time']
            missing_fields = [field for field in required_fields if field not in item]
            success_checks.append(f"MDD TOP 10 結構: 缺少字段={missing_fields}")
        
        print(f"\n✅ 數據結構檢查:")
        for check in success_checks:
            print(f"  - {check}")
        
        # 檢查是否有數據
        has_data = any([
            parsed_results.get('time_intervals'),
            parsed_results.get('mdd_top10'),
            parsed_results.get('risk_adjusted_top10'),
            parsed_results.get('long_pnl_top10'),
            parsed_results.get('short_pnl_top10')
        ])
        
        if has_data:
            print("✅ 解析功能測試通過！")
            return True
        else:
            print("❌ 解析功能測試失敗：沒有解析到任何數據")
            return False
        
    except Exception as e:
        print(f"❌ 解析功能測試失敗: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """主函數"""
    print("🔧 修復後的解析功能測試（真實數據格式）")
    print("=" * 70)
    print(f"開始時間: {datetime.now()}")
    
    # 測試解析功能
    parse_test_ok = test_parse_function_with_real_data()
    
    # 總結
    print(f"\n📊 測試總結:")
    print(f"  - 解析功能: {'✅ 通過' if parse_test_ok else '❌ 失敗'}")
    print(f"  - 整體結果: {'🎉 解析修復成功！' if parse_test_ok else '⚠️ 需要進一步修復'}")
    
    if parse_test_ok:
        print(f"\n✅ 解析功能修復完成！")
        print(f"現在請重新啟動 mdd_gui.py 並執行實驗測試：")
        print(f"  1. cd experiment_analysis")
        print(f"  2. python mdd_gui.py")
        print(f"  3. 打開 http://localhost:8081")
        print(f"  4. 執行實驗並檢查結果表格")
    
    print(f"\n結束時間: {datetime.now()}")

if __name__ == "__main__":
    main()
