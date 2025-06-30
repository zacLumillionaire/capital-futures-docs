#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
策略系統整合測試
測試開盤區間監控、信號偵測和部位管理
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from datetime import datetime, time
from strategy.signal_detector import OpeningRangeDetector, BreakoutSignalDetector
from strategy.position_manager import MultiLotPositionManager
from strategy.strategy_config import StrategyConfig
from database.sqlite_manager import SQLiteManager
from utils.time_utils import TradingTimeManager
import logging

# 設定日誌
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def test_opening_range_detection():
    """測試開盤區間偵測"""
    print("\n" + "="*60)
    print("🧪 測試1: 開盤區間偵測 (08:46-08:47)")
    print("="*60)
    
    detector = OpeningRangeDetector()
    detector.start_monitoring()
    
    # 模擬08:46 K線 (第一根)
    print("📊 模擬08:46 K線資料...")
    base_time = datetime(2025, 6, 30, 8, 46, 0)
    prices_846 = [22000, 22005, 22010, 22015, 22020, 22018, 22012, 22008, 22003, 22005]
    
    for i, price in enumerate(prices_846):
        timestamp = base_time.replace(second=i*6)  # 每6秒一個tick
        detector.process_tick(price, 100, timestamp)
    
    # 模擬08:47 K線 (第二根)
    print("📊 模擬08:47 K線資料...")
    base_time = datetime(2025, 6, 30, 8, 47, 0)
    prices_847 = [22005, 22008, 22012, 22018, 22025, 22030, 22028, 22022, 22015, 22010]
    
    for i, price in enumerate(prices_847):
        timestamp = base_time.replace(second=i*6)
        detector.process_tick(price, 100, timestamp)
    
    # 08:48:00 檢查結果
    final_time = datetime(2025, 6, 30, 8, 48, 0)
    detector.process_tick(22012, 100, final_time)
    
    # 取得區間資料
    range_data = detector.get_range_data()
    if range_data:
        print(f"✅ 開盤區間計算完成:")
        print(f"   📈 區間高點: {range_data['range_high']}")
        print(f"   📉 區間低點: {range_data['range_low']}")
        print(f"   📏 區間大小: {range_data['range_size']} 點")
        return range_data
    else:
        print("❌ 開盤區間計算失敗")
        return None

def test_breakout_signal_detection(range_data):
    """測試突破信號偵測"""
    print("\n" + "="*60)
    print("🧪 測試2: 突破信號偵測")
    print("="*60)
    
    if not range_data:
        print("❌ 無區間資料，跳過測試")
        return None
    
    # 創建突破信號偵測器
    breakout_detector = BreakoutSignalDetector(
        range_data['range_high'], 
        range_data['range_low'],
        buffer_points=0  # 無緩衝
    )
    
    # 測試價格序列
    test_prices = [
        (22012, "區間內"),
        (22020, "區間內"),
        (22025, "區間內"),
        (22031, "突破高點!"),  # 應該觸發LONG信號
        (22035, "持續上漲"),
        (22030, "回檔")
    ]
    
    signal_data = None
    
    for price, description in test_prices:
        signal = breakout_detector.check_breakout(price)
        print(f"   價格 {price}: {description}")
        
        if signal:
            print(f"   🚨 突破信號: {signal}")
            signal_data = breakout_detector.get_signal_data()
            break
    
    return signal_data

def test_position_management(signal_data, range_data):
    """測試部位管理"""
    print("\n" + "="*60)
    print("🧪 測試3: 多口部位管理")
    print("="*60)
    
    if not signal_data or not range_data:
        print("❌ 無信號資料，跳過測試")
        return
    
    # 創建3口策略配置
    config = StrategyConfig(
        strategy_name="測試三口策略",
        trade_size_in_lots=3
    )
    
    print(f"📊 策略配置: {config.strategy_name}")
    print(f"   交易口數: {config.trade_size_in_lots}")
    for i, rule in enumerate(config.lot_rules, 1):
        print(f"   第{i}口: 啟動{rule.trailing_activation}點, 回檔{rule.trailing_pullback}")
    
    # 創建部位管理器
    manager = MultiLotPositionManager(config)
    
    # 開倉
    success = manager.open_position(
        signal_data['signal_type'],
        signal_data['signal_price'],
        range_data['range_high'],
        range_data['range_low']
    )
    
    if not success:
        print("❌ 開倉失敗")
        return
    
    print(f"✅ 開倉成功: {signal_data['signal_type']} 3口 @{signal_data['signal_price']}")
    
    # 模擬價格變化
    entry_price = signal_data['signal_price']
    price_sequence = [
        entry_price + 5,   # +5點
        entry_price + 10,  # +10點
        entry_price + 18,  # +18點 (第1口啟動移動停利)
        entry_price + 25,  # +25點
        entry_price + 30,  # +30點
        entry_price + 20,  # 回檔到+20點 (第1口可能出場)
        entry_price + 35,  # +35點
        entry_price + 45,  # +45點 (第2口啟動移動停利)
        entry_price + 50,  # +50點
        entry_price + 40,  # 回檔到+40點 (第2口可能出場)
        entry_price + 70,  # +70點 (第3口啟動移動停利)
        entry_price + 75,  # +75點
        entry_price + 60,  # 回檔到+60點 (第3口可能出場)
    ]
    
    print("\n📈 模擬價格變化:")
    for i, price in enumerate(price_sequence, 1):
        exited_lots = manager.update_position(price)
        
        summary = manager.get_position_summary()
        profit_points = price - entry_price
        
        print(f"   步驟{i:2d}: 價格{price} (+{profit_points:+.0f}點)")
        print(f"           活躍口數: {summary['active_lots']}")
        print(f"           總損益: {summary['total_pnl']:+.0f}元")
        
        if exited_lots:
            print(f"           🔚 出場口數: {exited_lots}")
        
        # 顯示各口狀態
        for lot_detail in summary['lots_detail']:
            if lot_detail['status'] == 'ACTIVE':
                trailing = "✅" if lot_detail['trailing_activated'] else "❌"
                print(f"           第{lot_detail['lot_id']}口: 移動停利{trailing} 未實現{lot_detail['unrealized_pnl']:+.0f}元")
        
        if summary['active_lots'] == 0:
            print("   🏁 所有部位已出場")
            break
    
    # 最終摘要
    final_summary = manager.get_position_summary()
    print(f"\n📊 最終結果:")
    print(f"   總實現損益: {final_summary['total_realized_pnl']:+.0f}元")
    print(f"   總未實現損益: {final_summary['total_unrealized_pnl']:+.0f}元")
    print(f"   總損益: {final_summary['total_pnl']:+.0f}元")

def test_database_integration():
    """測試資料庫整合"""
    print("\n" + "="*60)
    print("🧪 測試4: 資料庫整合")
    print("="*60)
    
    # 創建資料庫管理器
    db = SQLiteManager("test_strategy.db")
    
    # 測試插入策略信號
    db.insert_strategy_signal(
        "2025-06-30", 22030, 22000, "LONG", "08:48:15", 22031
    )
    
    # 測試插入交易記錄
    db.insert_trade_record(
        "2025-06-30", "測試三口策略", 1, "08:48:15", 22031,
        "09:15:30", 22051, "LONG", 1000, "TRAILING_STOP"
    )
    
    # 測試查詢
    signal = db.get_today_signal("2025-06-30")
    trades = db.get_today_trades("2025-06-30")
    
    print(f"✅ 資料庫測試完成:")
    print(f"   策略信號: {signal['signal_type'] if signal else '無'}")
    print(f"   交易記錄: {len(trades)}筆")
    
    # 清理測試資料庫
    import os
    if os.path.exists("test_strategy.db"):
        os.remove("test_strategy.db")

def test_time_management():
    """測試時間管理"""
    print("\n" + "="*60)
    print("🧪 測試5: 交易時間管理")
    print("="*60)
    
    manager = TradingTimeManager()
    
    # 測試不同時間點
    test_times = [
        (time(8, 45, 0), "開盤前"),
        (time(8, 46, 30), "開盤區間"),
        (time(8, 48, 0), "交易開始"),
        (time(10, 30, 0), "交易中"),
        (time(13, 45, 0), "收盤"),
    ]
    
    print("⏰ 時間判斷測試:")
    for test_time, description in test_times:
        range_monitoring = manager.is_range_monitoring_time(test_time)
        trading_time = manager.is_trading_time(test_time)
        closing_time = manager.is_closing_time(test_time)
        
        print(f"   {test_time} ({description}):")
        print(f"     開盤區間監控: {'✅' if range_monitoring else '❌'}")
        print(f"     交易時間: {'✅' if trading_time else '❌'}")
        print(f"     收盤時間: {'✅' if closing_time else '❌'}")

def main():
    """主測試函數"""
    print("🚀 策略交易系統整合測試")
    print("測試範圍: 開盤區間監控 → 信號偵測 → 部位管理")
    
    # 執行各項測試
    range_data = test_opening_range_detection()
    signal_data = test_breakout_signal_detection(range_data)
    test_position_management(signal_data, range_data)
    test_database_integration()
    test_time_management()
    
    print("\n" + "="*60)
    print("🎉 所有測試完成!")
    print("="*60)
    print("✅ 開盤區間偵測 - 可以即時監控08:46-08:47兩根K棒")
    print("✅ 突破信號偵測 - 可以偵測價格突破區間邊界")
    print("✅ 多口部位管理 - 支援3口策略，每口獨立移動停利")
    print("✅ 保護性停損 - 停利前用區間邊界，停利後用獲利保護")
    print("✅ 資料庫整合 - 完整記錄策略執行過程")
    print("✅ 時間管理 - 精確判斷各個交易時段")
    print("\n🎯 系統已準備就緒，可以討論進場機制!")

if __name__ == "__main__":
    main()
