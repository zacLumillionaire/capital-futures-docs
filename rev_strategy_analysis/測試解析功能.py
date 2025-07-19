#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
測試修復後的解析功能
"""

import sys
import os
from datetime import datetime

def test_parse_function():
    """測試解析函數"""
    print("🧪 測試修復後的解析功能")
    print("=" * 50)
    
    try:
        # 導入修復後的 mdd_gui 模組
        sys.path.append('experiment_analysis')
        import mdd_gui
        
        # 創建測試報告內容
        test_log_content = """
📊 實驗結果報告 (共 4 個實驗)
================================================================================

📊 各時間區間 MDD 最佳前3名:
------------------------------------------------------------

🕐 時間區間: 10:30-10:32
  1. MDD:   50.0 | PNL:  -50.0 | 參數:15/25/35 | 多頭:  10.0 | 空頭: -60.0
  2. MDD:   60.0 | PNL:  -60.0 | 參數:20/30/40 | 多頭:   5.0 | 空頭: -65.0
  3. MDD:   70.0 | PNL:  -70.0 | 參數:25/35/45 | 多頭:   0.0 | 空頭: -70.0

🕐 時間區間: 12:00-12:02
  1. MDD:   40.0 | PNL:  -40.0 | 參數:15/25/35 | 多頭:  15.0 | 空頭: -55.0
  2. MDD:   55.0 | PNL:  -55.0 | 參數:20/30/40 | 多頭:  10.0 | 空頭: -65.0

🏆 MDD 最小 TOP 10:
------------------------------------------------------------
 1. 實驗  1 | 時間:10:30-10:32 | MDD:  40.0 | PNL:  -40.0 | 參數:15/25/35 | 多頭:  15.0 | 空頭: -55.0
 2. 實驗  2 | 時間:12:00-12:02 | MDD:  50.0 | PNL:  -50.0 | 參數:20/30/40 | 多頭:  10.0 | 空頭: -60.0

💎 風險調整收益 TOP 10:
------------------------------------------------------------
 1. 實驗  1 | 時間:10:30-10:32 | 風險調整:  1.25 | PNL:  -50.0 | MDD:  40.0 | 參數:15/25/35
 2. 實驗  2 | 時間:12:00-12:02 | 風險調整:  1.10 | PNL:  -55.0 | MDD:  50.0 | 參數:20/30/40

🟢 LONG 部位 PNL TOP 10:
------------------------------------------------------------
 1. 實驗  1 | 時間:10:30-10:32 | 多頭PNL:  15.0 | 總PNL:  -40.0 | MDD:  40.0 | 參數:15/25/35
 2. 實驗  2 | 時間:12:00-12:02 | 多頭PNL:  10.0 | 總PNL:  -50.0 | MDD:  50.0 | 參數:20/30/40

🔴 SHORT 部位 PNL TOP 10:
------------------------------------------------------------
 1. 實驗  1 | 時間:10:30-10:32 | 空頭PNL: -55.0 | 總PNL:  -40.0 | MDD:  40.0 | 參數:15/25/35
 2. 實驗  2 | 時間:12:00-12:02 | 空頭PNL: -60.0 | 總PNL:  -50.0 | MDD:  50.0 | 參數:20/30/40

============================================================
"""
        
        print("✅ 測試報告內容:")
        print(test_log_content[:500] + "...")
        
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
                print(f"  區間 {i+1}: {interval['interval']}")
                print(f"    前3名數量: {len(interval.get('top3', []))}")
                for j, top in enumerate(interval.get('top3', [])):
                    print(f"      第{j+1}名: MDD={top.get('mdd')}, PNL={top.get('pnl')}")
        
        # 詳細檢查 MDD TOP 10
        if parsed_results.get('mdd_top10'):
            print(f"\n🏆 MDD TOP 10 詳情:")
            for i, item in enumerate(parsed_results['mdd_top10'][:3]):
                print(f"  第{i+1}名: {item}")
        
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
    print("🔧 修復後的解析功能測試")
    print("=" * 60)
    print(f"開始時間: {datetime.now()}")
    
    # 測試解析功能
    parse_test_ok = test_parse_function()
    
    # 總結
    print(f"\n📊 測試總結:")
    print(f"  - 解析功能: {'✅ 通過' if parse_test_ok else '❌ 失敗'}")
    print(f"  - 整體結果: {'🎉 解析修復成功！' if parse_test_ok else '⚠️ 需要進一步修復'}")
    
    if parse_test_ok:
        print(f"\n✅ 解析功能修復完成，現在 mdd_gui.py 應該能正確顯示實驗結果了！")
        print(f"請重新啟動 mdd_gui.py 並執行實驗測試。")
    
    print(f"\n結束時間: {datetime.now()}")

if __name__ == "__main__":
    main()
