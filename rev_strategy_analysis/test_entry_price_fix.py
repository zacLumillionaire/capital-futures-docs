#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
測試Entry Price修復
"""

import sys
import os
from enhanced_report_generator import generate_comprehensive_report

def main():
    """測試使用最新的回測日誌生成報告"""
    
    # 使用最新的回測日誌（從GUI服務器輸出中獲取）
    sample_log = """
[2025-07-08T13:44:25+0800] INFO [__main__.run_backtest:620] --- 2024-11-04 | 開盤區間: 22923 - 22938 | 區間濾網未啟用 ---
[2025-07-08T13:44:25+0800] INFO [__main__._run_multi_lot_logic:237]   📈 LONG  | 反轉進場 3 口 | 時間: 11:34:00, 價格: 22906 (原策略做空點)
[2025-07-08T13:44:25+0800] INFO [__main__._run_multi_lot_logic:295]     📊 第1口設定 | 🎯固定停損模式 | 停損點數: 14點 | 停損點位: 22892
[2025-07-08T13:44:25+0800] INFO [__main__._run_multi_lot_logic:295]     📊 第2口設定 | 🎯固定停損模式 | 停損點數: 40點 | 停損點位: 22866
[2025-07-08T13:44:25+0800] INFO [__main__._run_multi_lot_logic:295]     📊 第3口設定 | 🎯固定停損模式 | 停損點數: 41點 | 停損點位: 22865
[2025-07-08T13:44:25+0800] INFO [__main__._run_multi_lot_logic:355]   ✅ 第1口觸及停利點 | 時間: 11:49:00, 出場價: 22946, 損益: +40
[2025-07-08T13:44:25+0800] INFO [__main__._run_multi_lot_logic:355]   ✅ 第2口觸及停利點 | 時間: 11:49:00, 出場價: 22946, 損益: +40
[2025-07-08T13:44:25+0800] INFO [__main__._run_multi_lot_logic:355]   ✅ 第3口觸及停利點 | 時間: 11:49:00, 出場價: 22946, 損益: +40
[2025-07-08T13:44:25+0800] INFO [__main__.run_backtest:620] --- 2024-11-05 | 開盤區間: 23070 - 23102 | 區間濾網未啟用 ---
[2025-07-08T13:44:25+0800] INFO [__main__._run_multi_lot_logic:237]   📉 SHORT | 反轉進場 3 口 | 時間: 11:50:00, 價格: 23107 (原策略做多點)
[2025-07-08T13:44:25+0800] INFO [__main__._run_multi_lot_logic:295]     📊 第1口設定 | 🎯固定停損模式 | 停損點數: 14點 | 停損點位: 23121
[2025-07-08T13:44:25+0800] INFO [__main__._run_multi_lot_logic:295]     📊 第2口設定 | 🎯固定停損模式 | 停損點數: 40點 | 停損點位: 23147
[2025-07-08T13:44:25+0800] INFO [__main__._run_multi_lot_logic:295]     📊 第3口設定 | 🎯固定停損模式 | 停損點數: 41點 | 停損點位: 23148
[2025-07-08T13:44:25+0800] INFO [__main__._run_multi_lot_logic:385]   ❌ 第1口初始停損 | 時間: 12:24:00, 出場價: 23121, 損益: -14
[2025-07-08T13:44:25+0800] INFO [__main__._run_multi_lot_logic:355]   ✅ 第2口觸及停利點 | 時間: 12:34:00, 出場價: 23070, 損益: +37
[2025-07-08T13:44:25+0800] INFO [__main__._run_multi_lot_logic:355]   ✅ 第3口觸及停利點 | 時間: 12:34:00, 出場價: 23070, 損益: +37
    """
    
    # 配置數據
    config_data = {
        "trade_lots": 3,
        "start_date": "2024-11-04",
        "end_date": "2025-06-28",
        "range_start_time": "11:30",
        "range_end_time": "11:32",
        "fixed_stop_mode": "on",
        "lot_settings": {
            "lot1": {"trigger": 14, "trailing": 0},
            "lot2": {"trigger": 40, "trailing": 0, "protection": 0},
            "lot3": {"trigger": 41, "trailing": 0, "protection": 0}
        }
    }
    
    print("🧪 測試Entry Price修復...")
    
    # 生成報告
    report_file = generate_comprehensive_report(sample_log, config_data)
    
    if report_file:
        print(f"✅ 測試報告生成成功: {report_file}")
        
        # 檢查報告中的entry price
        with open(report_file, 'r', encoding='utf-8') as f:
            content = f.read()
            
        if 'N/A' in content and 'Entry Price' in content:
            print("⚠️  報告中仍然包含N/A的Entry Price")
        else:
            print("✅ Entry Price問題已修復")
            
    else:
        print("❌ 報告生成失敗")

if __name__ == "__main__":
    main()
