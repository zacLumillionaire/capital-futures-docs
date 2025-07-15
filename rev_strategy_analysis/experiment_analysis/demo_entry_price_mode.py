#!/usr/bin/env python3
"""
Entry Price Mode 功能演示
展示兩種進場模式的差異
"""

import json

def demo_gui_config():
    """演示 GUI 配置的兩種進場模式"""
    print("🎯 Entry Price Mode 功能演示")
    print("=" * 60)
    
    # 基本配置
    base_config = {
        "trade_lots": 3,
        "lot_settings": {
            "lot1": {"trigger": 15, "trailing": 10},
            "lot2": {"trigger": 40, "trailing": 10}, 
            "lot3": {"trigger": 65, "trailing": 20}
        },
        "filters": {
            "range_filter": {"enabled": False},
            "risk_filter": {"enabled": False},
            "stop_loss_filter": {"enabled": False}
        }
    }
    
    # 模式 1: 區間邊緣進場 (預設)
    config_boundary = base_config.copy()
    config_boundary["entry_price_mode"] = "range_boundary"
    
    print("📊 模式 1: 區間邊緣進場 (預設)")
    print("   - 當 K 棒跌破區間低點時，使用區間下邊緣價格進場")
    print("   - 優點: 進場價格保守，執行確定性高")
    print("   - 缺點: 可能錯過更好的進場價格")
    print(f"   - 配置: {json.dumps(config_boundary, ensure_ascii=False, indent=2)}")
    
    print("\n" + "-" * 60)
    
    # 模式 2: 最低點進場
    config_breakout = base_config.copy()
    config_breakout["entry_price_mode"] = "breakout_low"
    
    print("📊 模式 2: 最低點進場")
    print("   - 當 K 棒跌破區間低點時，使用該 K 棒的最低價進場")
    print("   - 優點: 可能獲得更好的進場價格")
    print("   - 缺點: 滑價風險較高，執行不確定性")
    print(f"   - 配置: {json.dumps(config_breakout, ensure_ascii=False, indent=2)}")

def demo_mdd_gui_params():
    """演示 MDD GUI 參數設定"""
    print("\n\n🎯 MDD GUI 參數設定演示")
    print("=" * 60)
    
    # MDD GUI 參數 - 只測試區間邊緣模式
    params_single = {
        'stop_loss_ranges': {
            'lot1': [15],
            'lot2': [15],
            'lot3': [15]
        },
        'take_profit_ranges': {
            'unified': [55],
            'individual': [30, 40, 50]
        },
        'time_intervals': [['10:30', '10:32']],
        'max_workers': 6,
        'enable_breakout_low': False  # 只測試區間邊緣模式
    }
    
    print("📊 單一模式測試 (只測試區間邊緣)")
    print(f"   - 預估組合數: 1 × 4 × 1 × 1 = 4 個組合")
    print(f"   - 參數: {json.dumps(params_single, ensure_ascii=False, indent=2)}")
    
    print("\n" + "-" * 60)
    
    # MDD GUI 參數 - 測試兩種模式
    params_dual = params_single.copy()
    params_dual['enable_breakout_low'] = True  # 同時測試兩種模式
    
    print("📊 雙模式測試 (同時測試兩種進場模式)")
    print(f"   - 預估組合數: 1 × 4 × 1 × 2 = 8 個組合")
    print(f"   - 每個參數組合會生成兩個實驗:")
    print(f"     * 區間邊緣進場 (ID 後綴: _RB)")
    print(f"     * 最低點進場 (ID 後綴: _BL)")
    print(f"   - 參數: {json.dumps(params_dual, ensure_ascii=False, indent=2)}")

def demo_experiment_ids():
    """演示實驗 ID 格式"""
    print("\n\n🎯 實驗 ID 格式演示")
    print("=" * 60)
    
    # 示例實驗 ID
    examples = [
        {
            "mode": "區間邊緣進場",
            "id": "10301032_L1SL15_L2SL15_L3SL15_RangeBoundary_RB",
            "description": "時間區間 10:30-10:32，三口停損都是 15 點，使用區間邊緣停利，區間邊緣進場"
        },
        {
            "mode": "最低點進場", 
            "id": "10301032_L1SL15_L2SL15_L3SL15_RangeBoundary_BL",
            "description": "時間區間 10:30-10:32，三口停損都是 15 點，使用區間邊緣停利，最低點進場"
        },
        {
            "mode": "區間邊緣進場",
            "id": "10301032_L1SL15_L2SL15_L3SL15_TP55_RB", 
            "description": "時間區間 10:30-10:32，三口停損都是 15 點，統一停利 55 點，區間邊緣進場"
        },
        {
            "mode": "最低點進場",
            "id": "10301032_L1SL15_L2SL15_L3SL15_TP55_BL",
            "description": "時間區間 10:30-10:32，三口停損都是 15 點，統一停利 55 點，最低點進場"
        }
    ]
    
    for i, example in enumerate(examples, 1):
        print(f"📊 示例 {i}: {example['mode']}")
        print(f"   - ID: {example['id']}")
        print(f"   - 說明: {example['description']}")
        print()

def demo_gui_display():
    """演示 GUI 顯示效果"""
    print("\n🎯 GUI 顯示效果演示")
    print("=" * 60)
    
    print("📊 結果表格新增欄位:")
    print("   - 所有 TOP 10 表格都新增了「進場模式」欄位")
    print("   - 區間邊緣模式顯示為藍色標籤: [區間邊緣]")
    print("   - 最低點模式顯示為橙色標籤: [最低點]")
    print("   - 可以清楚區分每個實驗使用的進場方式")
    
    print("\n📊 參數設定介面:")
    print("   - 新增「進場價格模式設定」區塊")
    print("   - 預設使用區間邊緣進場")
    print("   - 提供勾選框「同時測試最低點進場模式」")
    print("   - 勾選後會為每個參數組合生成兩個實驗")

def main():
    """主演示函數"""
    demo_gui_config()
    demo_mdd_gui_params()
    demo_experiment_ids()
    demo_gui_display()
    
    print("\n" + "=" * 60)
    print("🎉 Entry Price Mode 功能演示完成！")
    print("\n📋 功能總結:")
    print("✅ 新增兩種進場價格模式選擇")
    print("✅ GUI 介面支援模式切換")
    print("✅ 實驗組合自動生成雙模式配置")
    print("✅ 結果表格清楚標示進場模式")
    print("✅ 完全向後兼容，預設使用區間邊緣模式")

if __name__ == "__main__":
    main()
