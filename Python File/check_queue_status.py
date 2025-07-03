"""
快速檢查Queue狀態工具
用於檢查OrderTester.py中的Queue架構是否正常運行
"""

import time
from datetime import datetime

try:
    from queue_infrastructure import (
        get_queue_manager,
        get_tick_processor,
        TickData
    )
    print("✅ Queue基礎設施連接成功")
except ImportError as e:
    print(f"❌ 無法連接Queue基礎設施: {e}")
    exit(1)

def check_current_status():
    """檢查當前Queue狀態"""
    print(f"\n🕐 {datetime.now().strftime('%H:%M:%S')} - Queue狀態檢查")
    print("-" * 50)
    
    try:
        # 獲取Queue管理器狀態
        queue_manager = get_queue_manager()
        queue_status = queue_manager.get_queue_status()
        
        print(f"📦 QueueManager:")
        print(f"  • 運行狀態: {'✅ 運行中' if queue_status.get('running') else '❌ 未運行'}")
        print(f"  • Tick佇列: {queue_status.get('tick_queue_size', 0)}/{queue_status.get('tick_queue_maxsize', 0)}")
        print(f"  • 日誌佇列: {queue_status.get('log_queue_size', 0)}/{queue_status.get('log_queue_maxsize', 0)}")
        
        stats = queue_status.get('stats', {})
        print(f"  • 已接收Tick: {stats.get('tick_received', 0)}")
        print(f"  • 已處理Tick: {stats.get('tick_processed', 0)}")
        print(f"  • Queue滿錯誤: {stats.get('queue_full_errors', 0)}")
        print(f"  • 處理錯誤: {stats.get('processing_errors', 0)}")
        
        # 獲取Tick處理器狀態
        tick_processor = get_tick_processor()
        processor_status = tick_processor.get_status()
        
        print(f"\n🔄 TickProcessor:")
        print(f"  • 運行狀態: {'✅ 運行中' if processor_status.get('running') else '❌ 未運行'}")
        print(f"  • 線程存活: {'✅ 存活' if processor_status.get('thread_alive') else '❌ 未存活'}")
        print(f"  • 回調函數: {processor_status.get('callback_count', 0)} 個")
        
        proc_stats = processor_status.get('stats', {})
        print(f"  • 處理計數: {proc_stats.get('processed_count', 0)}")
        print(f"  • 錯誤計數: {proc_stats.get('error_count', 0)}")
        
        last_process_time = proc_stats.get('last_process_time')
        if last_process_time:
            print(f"  • 最後處理: {last_process_time.strftime('%H:%M:%S')}")
        else:
            print(f"  • 最後處理: 無")
        
        # 判斷整體狀態
        is_healthy = (
            queue_status.get('running', False) and 
            processor_status.get('running', False) and 
            processor_status.get('thread_alive', False)
        )
        
        print(f"\n🎯 整體狀態: {'✅ 健康' if is_healthy else '⚠️ 需要檢查'}")
        
        return is_healthy
        
    except Exception as e:
        print(f"❌ 檢查狀態時發生錯誤: {e}")
        return False

def send_test_tick():
    """發送一個測試Tick"""
    try:
        queue_manager = get_queue_manager()
        
        # 創建測試Tick
        test_tick = TickData(
            market_no="TW",
            stock_idx=1,
            date=20250703,
            time_hms=int(datetime.now().strftime("%H%M%S")),
            time_millis=datetime.now().microsecond // 1000,
            bid=2246100,
            ask=2246200,
            close=2246150,
            qty=1,
            timestamp=datetime.now()
        )
        
        # 發送到Queue
        success = queue_manager.put_tick_data(test_tick)
        
        if success:
            print("✅ 測試Tick發送成功")
            return True
        else:
            print("❌ 測試Tick發送失敗 (Queue可能已滿)")
            return False
            
    except Exception as e:
        print(f"❌ 發送測試Tick時發生錯誤: {e}")
        return False

def main():
    """主函數"""
    print("🔍 Queue狀態檢查工具")
    print("=" * 50)
    print("📝 此工具將檢查OrderTester.py中的Queue架構狀態")
    print("💡 請確保OrderTester.py已經啟動並且Queue服務已啟動")
    print()
    
    # 初始狀態檢查
    print("📋 步驟1: 檢查初始狀態")
    initial_healthy = check_current_status()
    
    if not initial_healthy:
        print("\n⚠️ Queue架構未正常運行")
        print("🔧 請在OrderTester.py中:")
        print("   1. 找到 '🚀 Queue架構控制' 面板")
        print("   2. 點擊 '🚀 啟動Queue服務' 按鈕")
        print("   3. 確認狀態顯示為 '✅ 運行中'")
        print("   4. 重新運行此檢查工具")
        return
    
    print("\n📋 步驟2: 發送測試Tick")
    test_sent = send_test_tick()
    
    if test_sent:
        print("⏳ 等待3秒讓系統處理...")
        time.sleep(3)
        
        print("\n📋 步驟3: 檢查處理結果")
        final_healthy = check_current_status()
        
        if final_healthy:
            print("\n🎉 Queue架構運行正常！")
            print("✅ 新架構已成功整合到OrderTester.py")
            print("\n💡 現在您可以:")
            print("   1. 等待實際Tick資料進來觀察處理")
            print("   2. 在Queue控制面板中查看詳細狀態")
            print("   3. 嘗試切換Queue模式和傳統模式")
            print("   4. 準備進入階段3：策略處理線程整合")
        else:
            print("\n⚠️ 處理過程中出現問題")
    else:
        print("\n❌ 測試Tick發送失敗")
    
    print("\n🔄 持續監控模式 (按Ctrl+C停止)")
    try:
        while True:
            time.sleep(10)  # 每10秒檢查一次
            check_current_status()
            print()
    except KeyboardInterrupt:
        print("\n⏹️ 監控已停止")

if __name__ == "__main__":
    main()
