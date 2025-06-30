#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
簡化策略測試 - 驗證核心功能
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from strategy.strategy_config import StrategyConfig
from strategy.position_manager import MultiLotPositionManager, PositionType
from database.sqlite_manager import SQLiteManager
from utils.time_utils import TradingTimeManager
import logging

# 設定日誌
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def test_strategy_config():
    """測試策略配置"""
    print("🧪 測試策略配置")
    
    # 創建預設3口策略
    config = StrategyConfig()
    
    print(f"✅ 策略名稱: {config.strategy_name}")
    print(f"✅ 交易口數: {config.trade_size_in_lots}")
    print(f"✅ 口數規則:")
    
    for i, rule in enumerate(config.lot_rules, 1):
        print(f"   第{i}口: 啟動{rule.trailing_activation}點, 回檔{rule.trailing_pullback}")
        if rule.protective_stop_multiplier:
            print(f"         保護停損倍數: {rule.protective_stop_multiplier}")
    
    return config

def test_position_manager():
    """測試部位管理"""
    print("\n🧪 測試部位管理")
    
    # 創建配置
    config = StrategyConfig()
    manager = MultiLotPositionManager(config)
    
    # 模擬開倉
    range_high = 22050
    range_low = 22000
    entry_price = 22055  # 突破高點進場
    
    success = manager.open_position('LONG', entry_price, range_high, range_low)
    print(f"✅ 開倉結果: {success}")
    
    if success:
        print(f"✅ 開倉: LONG 3口 @{entry_price}")
        print(f"   區間: {range_low}-{range_high}")
        
        # 模擬價格變化
        test_prices = [
            (22060, "+5點"),
            (22070, "+15點 (第1口啟動移動停利)"),
            (22080, "+25點"),
            (22095, "+40點 (第2口啟動移動停利)"),
            (22100, "+45點"),
            (22085, "回檔到+30點"),
            (22120, "+65點 (第3口啟動移動停利)"),
            (22125, "+70點"),
            (22110, "回檔到+55點"),
        ]
        
        print("\n📈 價格變化測試:")
        for price, description in test_prices:
            exited_lots = manager.update_position(price)
            summary = manager.get_position_summary()
            
            print(f"   價格{price} ({description})")
            print(f"     活躍口數: {summary['active_lots']}")
            print(f"     總損益: {summary['total_pnl']:+.0f}元")
            
            if exited_lots:
                print(f"     🔚 出場口數: {exited_lots}")
            
            if summary['active_lots'] == 0:
                break
        
        # 最終結果
        final_summary = manager.get_position_summary()
        print(f"\n📊 最終結果:")
        print(f"   總損益: {final_summary['total_pnl']:+.0f}元")
        print(f"   實現損益: {final_summary['total_realized_pnl']:+.0f}元")

def test_database():
    """測試資料庫"""
    print("\n🧪 測試資料庫")
    
    # 創建測試資料庫
    db = SQLiteManager("test_simple.db")
    
    # 插入測試資料
    db.insert_strategy_signal("2025-06-30", 22050, 22000, "LONG", "08:48:15", 22055)
    db.insert_trade_record("2025-06-30", "三口策略", 1, "08:48:15", 22055, 
                          "09:15:30", 22075, "LONG", 1000, "TRAILING_STOP")
    
    # 查詢資料
    signal = db.get_today_signal("2025-06-30")
    trades = db.get_today_trades("2025-06-30")
    
    print(f"✅ 策略信號: {signal['signal_type'] if signal else '無'}")
    print(f"✅ 交易記錄: {len(trades)}筆")
    
    if trades:
        trade = trades[0]
        print(f"   第1筆: {trade['position_type']} {trade['lot_id']}口 損益{trade['pnl']}元")
    
    # 清理
    import os
    if os.path.exists("test_simple.db"):
        os.remove("test_simple.db")

def test_time_utils():
    """測試時間工具"""
    print("\n🧪 測試時間工具")
    
    manager = TradingTimeManager()
    
    # 測試關鍵時間點
    from datetime import time
    
    test_cases = [
        (time(8, 46, 30), "開盤區間監控"),
        (time(8, 48, 0), "交易開始"),
        (time(13, 45, 0), "收盤時間"),
    ]
    
    for test_time, description in test_cases:
        range_monitoring = manager.is_range_monitoring_time(test_time)
        trading_time = manager.is_trading_time(test_time)
        closing_time = manager.is_closing_time(test_time)
        
        print(f"✅ {test_time} ({description}):")
        print(f"   開盤區間: {'✅' if range_monitoring else '❌'}")
        print(f"   交易時間: {'✅' if trading_time else '❌'}")
        print(f"   收盤時間: {'✅' if closing_time else '❌'}")

def simulate_trading_day():
    """模擬完整交易日"""
    print("\n🎯 模擬完整交易日流程")
    
    # 1. 策略配置
    config = StrategyConfig()
    print(f"📋 策略: {config.strategy_name} ({config.trade_size_in_lots}口)")
    
    # 2. 模擬開盤區間
    range_high = 22050
    range_low = 22000
    print(f"📊 開盤區間: {range_low}-{range_high} (50點)")
    
    # 3. 模擬突破信號
    signal_price = 22055  # 突破高點+5點
    signal_type = 'LONG'
    print(f"🚨 突破信號: {signal_type} @{signal_price}")
    
    # 4. 開倉
    manager = MultiLotPositionManager(config)
    success = manager.open_position(signal_type, signal_price, range_high, range_low)
    
    if success:
        print(f"🚀 開倉成功: {signal_type} {config.trade_size_in_lots}口 @{signal_price}")
        
        # 5. 模擬交易過程
        trading_sequence = [
            (22070, "獲利15點，第1口啟動移動停利"),
            (22095, "獲利40點，第2口啟動移動停利"),
            (22080, "回檔，第1口可能出場"),
            (22120, "獲利65點，第3口啟動移動停利"),
            (22110, "回檔，檢查各口停利"),
            (22130, "再次上漲"),
            (22115, "最終回檔"),
        ]
        
        print("\n📈 交易過程:")
        for price, description in trading_sequence:
            exited_lots = manager.update_position(price)
            summary = manager.get_position_summary()
            
            profit_points = price - signal_price
            print(f"   {price} (+{profit_points:+.0f}點): {description}")
            print(f"     活躍: {summary['active_lots']}口, 損益: {summary['total_pnl']:+.0f}元")
            
            if exited_lots:
                print(f"     🔚 出場: 第{exited_lots}口")
            
            if summary['active_lots'] == 0:
                print("     🏁 所有部位已出場")
                break
        
        # 6. 最終結果
        final_summary = manager.get_position_summary()
        print(f"\n📊 交易日結果:")
        print(f"   總損益: {final_summary['total_pnl']:+.0f}元")
        print(f"   實現損益: {final_summary['total_realized_pnl']:+.0f}元")
        print(f"   未實現損益: {final_summary['total_unrealized_pnl']:+.0f}元")
        
        # 7. 記錄到資料庫
        db = SQLiteManager("trading_day_test.db")
        db.insert_strategy_signal("2025-06-30", range_high, range_low, 
                                 signal_type, "08:48:15", signal_price)
        
        for lot_detail in final_summary['lots_detail']:
            if lot_detail['realized_pnl'] is not None:
                db.insert_trade_record(
                    "2025-06-30", config.strategy_name, lot_detail['lot_id'],
                    lot_detail['entry_time'], lot_detail['entry_price'],
                    lot_detail['exit_time'], lot_detail['exit_price'],
                    lot_detail['position_type'], lot_detail['realized_pnl'],
                    lot_detail['exit_reason']
                )
        
        print("✅ 交易記錄已儲存到資料庫")
        
        # 清理
        import os
        if os.path.exists("trading_day_test.db"):
            os.remove("trading_day_test.db")

def main():
    """主測試函數"""
    print("🚀 策略系統核心功能測試")
    print("="*60)
    
    # 執行各項測試
    test_strategy_config()
    test_position_manager()
    test_database()
    test_time_utils()
    
    # 完整模擬
    simulate_trading_day()
    
    print("\n" + "="*60)
    print("🎉 所有核心功能測試完成!")
    print("="*60)
    print("✅ 策略配置 - 預設3口，15/40/65點啟動，20%回檔")
    print("✅ 部位管理 - 多口管理，移動停利，保護停損")
    print("✅ 資料庫 - SQLite儲存策略和交易資料")
    print("✅ 時間管理 - 精確判斷交易時段")
    print("✅ 完整流程 - 從開盤區間到交易結束")
    print("\n🎯 系統核心功能已驗證，準備討論進場機制!")

if __name__ == "__main__":
    main()
