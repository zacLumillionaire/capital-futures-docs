"""
階段2整合測試：驗證API事件處理改造
測試Queue基礎設施與現有系統的整合
"""

import sys
import os
import time
from datetime import datetime

print("🧪 階段2整合測試開始...")

# 測試1: Queue基礎設施導入
print("\n📦 測試1: Queue基礎設施導入")
try:
    from queue_infrastructure import (
        get_queue_infrastructure, 
        TickData, 
        get_queue_manager,
        get_tick_processor,
        get_ui_updater
    )
    print("✅ Queue基礎設施導入成功")
except ImportError as e:
    print(f"❌ Queue基礎設施導入失敗: {e}")
    sys.exit(1)

# 測試2: 基礎設施初始化
print("\n🔧 測試2: 基礎設施初始化")
try:
    # 創建Queue基礎設施
    queue_manager = get_queue_manager()
    tick_processor = get_tick_processor()
    
    # 初始化
    queue_manager.start()
    print("✅ QueueManager啟動成功")
    
    # 啟動Tick處理器
    tick_processor.start_processing()
    print("✅ TickProcessor啟動成功")
    
except Exception as e:
    print(f"❌ 基礎設施初始化失敗: {e}")
    sys.exit(1)

# 測試3: 模擬OnNotifyTicksLONG事件處理
print("\n🎯 測試3: 模擬API事件處理")

def simulate_api_event():
    """模擬OnNotifyTicksLONG事件的Queue模式處理"""
    try:
        # 模擬事件參數
        sMarketNo = "TW"
        nStockidx = 1
        lDate = 20250703
        lTimehms = 143000
        lTimemillismicros = 500
        nBid = 2246100
        nAsk = 2246200
        nClose = 2246150
        nQty = 3
        
        # 創建TickData物件 (模擬Queue模式處理)
        tick_data = TickData(
            market_no=sMarketNo,
            stock_idx=nStockidx,
            date=lDate,
            time_hms=lTimehms,
            time_millis=lTimemillismicros,
            bid=nBid,
            ask=nAsk,
            close=nClose,
            qty=nQty,
            timestamp=datetime.now()
        )
        
        # 將Tick資料放入Queue (非阻塞)
        success = queue_manager.put_tick_data(tick_data)
        
        if success:
            print("✅ API事件Queue模式處理成功")
            return True
        else:
            print("❌ Queue已滿，處理失敗")
            return False
            
    except Exception as e:
        print(f"❌ API事件處理錯誤: {e}")
        return False

# 執行多次模擬
success_count = 0
total_tests = 10

for i in range(total_tests):
    if simulate_api_event():
        success_count += 1
    time.sleep(0.1)  # 間隔100ms

success_rate = (success_count / total_tests) * 100
print(f"📊 API事件處理成功率: {success_rate:.1f}% ({success_count}/{total_tests})")

# 測試4: 等待處理完成並檢查統計
print("\n⏳ 測試4: 等待處理完成...")
time.sleep(2.0)  # 等待處理

# 檢查統計
status = queue_manager.get_queue_status()
tick_received = status.get('stats', {}).get('tick_received', 0)
tick_processed = status.get('stats', {}).get('tick_processed', 0)

print(f"📈 統計結果:")
print(f"  • 已接收Tick: {tick_received}")
print(f"  • 已處理Tick: {tick_processed}")
print(f"  • Tick佇列大小: {status.get('tick_queue_size', 0)}")
print(f"  • 日誌佇列大小: {status.get('log_queue_size', 0)}")

# 測試5: 策略回調測試
print("\n🎯 測試5: 策略回調機制")

callback_received = []

def test_strategy_callback(tick_dict):
    """測試策略回調函數"""
    try:
        price = tick_dict.get('corrected_price', 0)
        formatted_time = tick_dict.get('formatted_time', '')
        callback_received.append({
            'price': price,
            'time': formatted_time,
            'timestamp': datetime.now()
        })
        print(f"📊 策略回調: 價格={price}, 時間={formatted_time}")
    except Exception as e:
        print(f"❌ 策略回調錯誤: {e}")

# 添加策略回調
tick_processor.add_strategy_callback(test_strategy_callback)
print("✅ 策略回調函數已添加")

# 發送更多測試資料
print("📤 發送測試資料...")
for i in range(5):
    tick_data = TickData(
        market_no="TW",
        stock_idx=1,
        date=20250703,
        time_hms=143000 + i,
        time_millis=i * 100,
        bid=2246100 + i,
        ask=2246200 + i,
        close=2246150 + i,
        qty=1 + i,
        timestamp=datetime.now()
    )
    queue_manager.put_tick_data(tick_data)
    time.sleep(0.2)

# 等待回調處理
time.sleep(2.0)

print(f"📊 策略回調結果: 收到 {len(callback_received)} 個回調")

# 測試6: 清理和停止
print("\n🧹 測試6: 清理和停止")
try:
    tick_processor.stop_processing()
    print("✅ TickProcessor已停止")
    
    queue_manager.stop()
    print("✅ QueueManager已停止")
    
except Exception as e:
    print(f"❌ 清理錯誤: {e}")

# 最終結果
print("\n" + "="*60)
print("📊 階段2整合測試結果:")
print(f"✅ Queue基礎設施: 正常")
print(f"✅ API事件處理: {success_rate:.1f}%成功率")
print(f"✅ 資料處理: {tick_processed}個Tick已處理")
print(f"✅ 策略回調: {len(callback_received)}個回調")

if success_rate >= 90 and tick_processed > 0 and len(callback_received) > 0:
    print("🎉 階段2整合測試全部通過！")
    print("✅ Queue架構已準備就緒，可以進入階段3")
else:
    print("⚠️ 部分測試未達標準，需要檢查")

print("="*60)
