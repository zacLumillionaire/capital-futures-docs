"""
檢查群益API事件觸發狀況
確認OnNotifyTicksLONG事件是否正常接收資料
"""

import time
from datetime import datetime

try:
    from queue_infrastructure import get_queue_manager
    print("✅ Queue基礎設施連接成功")
except ImportError as e:
    print(f"❌ 無法連接Queue基礎設施: {e}")
    exit(1)

def check_api_event_activity():
    """檢查API事件活動"""
    print("🔍 檢查群益API事件活動狀況")
    print("=" * 50)
    
    queue_manager = get_queue_manager()
    
    # 記錄初始狀態
    initial_status = queue_manager.get_queue_status()
    initial_received = initial_status.get('stats', {}).get('tick_received', 0)
    initial_processed = initial_status.get('stats', {}).get('tick_processed', 0)
    
    print(f"📊 初始狀態 ({datetime.now().strftime('%H:%M:%S')}):")
    print(f"  • Queue運行: {'✅' if initial_status.get('running') else '❌'}")
    print(f"  • 已接收Tick: {initial_received}")
    print(f"  • 已處理Tick: {initial_processed}")
    print(f"  • Tick佇列大小: {initial_status.get('tick_queue_size', 0)}")
    print()
    
    if not initial_status.get('running'):
        print("❌ Queue未運行，請先在OrderTester.py中啟動Queue服務")
        return False
    
    print("⏳ 監控30秒，檢查是否有新的API事件...")
    print("💡 如果市場開盤且有交易，應該會看到Tick數量增加")
    print()
    
    # 監控30秒
    for i in range(6):  # 每5秒檢查一次，共30秒
        time.sleep(5)
        
        current_status = queue_manager.get_queue_status()
        current_received = current_status.get('stats', {}).get('tick_received', 0)
        current_processed = current_status.get('stats', {}).get('tick_processed', 0)
        
        new_received = current_received - initial_received
        new_processed = current_processed - initial_processed
        
        print(f"🕐 {datetime.now().strftime('%H:%M:%S')} - "
              f"新接收: {new_received}, 新處理: {new_processed}, "
              f"佇列: {current_status.get('tick_queue_size', 0)}")
        
        if new_received > 0:
            print("✅ 檢測到API事件活動！OnNotifyTicksLONG正常觸發")
            return True
    
    print("\n📊 檢查結果:")
    final_status = queue_manager.get_queue_status()
    final_received = final_status.get('stats', {}).get('tick_received', 0)
    total_new = final_received - initial_received
    
    if total_new > 0:
        print(f"✅ 檢測到 {total_new} 個新Tick，API事件正常")
        return True
    else:
        print("⏳ 未檢測到新的API事件，可能原因:")
        print("   1. 市場未開盤或無交易活動")
        print("   2. 報價訂閱未成功")
        print("   3. OnNotifyTicksLONG事件未正常註冊")
        print("   4. Queue模式未啟用")
        return False

def diagnose_quote_subscription():
    """診斷報價訂閱狀況"""
    print("\n🔧 報價訂閱診斷:")
    print("請檢查OrderTester.py中的日誌訊息，確認:")
    print("  ✅ 【連線結果】SK_SUCCESS (代碼: 0)")
    print("  ✅ 【訂閱結果】SK_SUCCESS (代碼: 0)")
    print("  ✅ 【成功】MTX00報價監控已啟動")
    print()
    print("如果以上都正常，但仍無Tick資料，可能是:")
    print("  • 市場時間: 期貨交易時間 08:45-13:45, 15:00-05:00")
    print("  • 商品代碼: 確認MTX00是否為正確的商品代碼")
    print("  • 網路連線: 檢查網路連線是否穩定")

def suggest_next_steps():
    """建議下一步操作"""
    print("\n🎯 建議測試步驟:")
    print("1. 確認市場開盤時間:")
    print("   • 台指期貨: 週一至週五 08:45-13:45, 15:00-05:00")
    print("   • 如果是非交易時間，請等待開盤")
    print()
    print("2. 在OrderTester.py中檢查:")
    print("   • Queue控制面板狀態是否為 '✅ 運行中'")
    print("   • 是否已切換到Queue模式")
    print("   • 日誌中是否有錯誤訊息")
    print()
    print("3. 如果確認是交易時間但無資料:")
    print("   • 嘗試重新點擊 '監控報價'")
    print("   • 檢查網路連線")
    print("   • 確認群益API登入狀態")
    print()
    print("4. 測試Queue架構:")
    print("   • 運行 'python simulate_tick_data.py' 進行模擬測試")
    print("   • 確認Queue架構本身運作正常")

def main():
    """主函數"""
    print("🔍 群益API事件檢查工具")
    print("📝 檢查OnNotifyTicksLONG事件是否正常接收資料")
    print()
    
    try:
        # 檢查API事件活動
        has_activity = check_api_event_activity()
        
        if has_activity:
            print("\n🎉 群益API事件正常！Queue架構成功處理實際資料")
            print("✅ 階段2測試完全成功，可以進入階段3")
        else:
            diagnose_quote_subscription()
            suggest_next_steps()
    
    except Exception as e:
        print(f"\n❌ 檢查過程中發生錯誤: {e}")

if __name__ == "__main__":
    main()
