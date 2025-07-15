#!/usr/bin/env python3
"""
測試增強報告生成器
"""

import sys
sys.path.append('.')

from enhanced_report_generator import extract_trading_data_from_log

def test_risk_management_parsing():
    """測試風險管理平倉解析"""
    
    # 模擬包含風險管理平倉和保護性停損的日誌
    test_log = """
[2025-07-06T20:34:21+0800] INFO [__main__.run_backtest:382] --- 2024-11-07 | 開盤區間: 23130 - 23180 | 區間濾網未啟用 ---
[2025-07-06T20:34:21+0800] INFO [__main__._run_multi_lot_logic:202]   📉 SHORT | 進場 3 口 | 時間: 08:48:00, 價格: 23130
[2025-07-06T20:34:21+0800] INFO [__main__._run_multi_lot_logic:261]   🔔 第1口移動停利啟動 | 時間: 08:49:00
[2025-07-06T20:34:21+0800] INFO [__main__._run_multi_lot_logic:268]   ✅ 第1口移動停利 | 時間: 08:49:00, 價格: 23115, 損益: +15
[2025-07-06T20:34:21+0800] INFO [__main__._run_multi_lot_logic:283]     - 第2口單停損點更新為: 23160 (基於累積獲利 15)
[2025-07-06T20:34:21+0800] INFO [__main__._run_multi_lot_logic:261]   🔔 第2口移動停利啟動 | 時間: 08:57:00
[2025-07-06T20:34:21+0800] INFO [__main__._run_multi_lot_logic:268]   ✅ 第2口移動停利 | 時間: 08:57:00, 價格: 23093, 損益: +37
[2025-07-06T20:34:21+0800] INFO [__main__._run_multi_lot_logic:283]     - 第3口單停損點更新為: 23234 (基於累積獲利 52)
[2025-07-06T20:34:21+0800] INFO [__main__._run_multi_lot_logic:237]   🛡️ 第3口保護性停損 | 時間: 09:05:00, 出場價: 23234, 損益: -104
[2025-07-06T20:34:26+0800] INFO [__main__.run_backtest:382] --- 2024-11-08 | 開盤區間: 23746 - 23793 | 區間濾網未啟用 ---
[2025-07-06T20:34:26+0800] INFO [__main__._run_multi_lot_logic:198]   📈 LONG  | 進場 3 口 | 時間: 08:48:00, 價格: 23794
[2025-07-06T20:34:26+0800] INFO [__main__._run_multi_lot_logic:301]   🚨 風險管理虧損平倉 | 觸發當日虧損限制，強制平倉 (-114點 <= -100點) | 時間: 08:51:00, 平倉價: 23756
[2025-07-06T20:34:26+0800] INFO [__main__._run_multi_lot_logic:309]     🚨 第1口風險平倉 | 損益: -38點
[2025-07-06T20:34:26+0800] INFO [__main__._run_multi_lot_logic:309]     🚨 第2口風險平倉 | 損益: -38點
[2025-07-06T20:34:26+0800] INFO [__main__._run_multi_lot_logic:309]     🚨 第3口風險平倉 | 損益: -38點
    """
    
    print("🧪 測試風險管理平倉解析...")
    events_df, daily_df = extract_trading_data_from_log(test_log)
    
    print(f"📊 解析結果:")
    print(f"  - 交易事件數量: {len(events_df)}")
    print(f"  - 交易日數量: {len(daily_df)}")
    
    if not events_df.empty:
        print(f"📋 交易事件詳情:")
        for _, event in events_df.iterrows():
            exit_price_str = f"出場價: {event['exit_price']}" if event['exit_price'] else "出場價: N/A"
            print(f"  - 日期: {event['trade_date']}, 方向: {event['direction']}, 口數: {event['lot_number']}, {exit_price_str}, 損益: {event['pnl']}, 出場類型: {event['exit_type']}")

    # 檢查風險管理平倉事件
    risk_exits = events_df[events_df['exit_type'] == 'risk_management']
    print(f"🚨 風險管理平倉事件數量: {len(risk_exits)}")

    # 檢查保護性停損事件
    protective_exits = events_df[events_df['exit_type'] == 'protective_stop']
    print(f"🛡️ 保護性停損事件數量: {len(protective_exits)}")

    print("✅ 測試成功")
    return len(risk_exits) >= 3 and len(protective_exits) >= 1  # 應該有風險管理平倉和保護性停損事件

if __name__ == "__main__":
    success = test_risk_management_parsing()
    print(f"✅ 測試{'成功' if success else '失敗'}")
