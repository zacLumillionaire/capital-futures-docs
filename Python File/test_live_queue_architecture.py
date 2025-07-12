"""
實時Queue架構測試工具
用於驗證OrderTester.py中的Queue架構是否正常工作

測試方法：
1. 檢查Queue基礎設施狀態
2. 模擬發送Tick資料到Queue
3. 驗證數據流是否正常
4. 檢查UI更新機制
"""

import sys
import os
import time
import threading
from datetime import datetime

# 確保能導入Queue基礎設施
try:
    from queue_infrastructure import (
        get_queue_infrastructure,
        get_queue_manager,
        get_tick_processor,
        TickData
    )
    print("✅ Queue基礎設施導入成功")
except ImportError as e:
    print(f"❌ Queue基礎設施導入失敗: {e}")
    sys.exit(1)

class LiveQueueArchitectureTest:
    """實時Queue架構測試器"""
    
    def __init__(self):
        self.running = False
        
    def check_queue_infrastructure_status(self):
        """檢查Queue基礎設施狀態"""
        print("\n🔍 檢查Queue基礎設施狀態...")
        
        try:
            # 獲取全域實例
            queue_manager = get_queue_manager()
            tick_processor = get_tick_processor()
            
            # 檢查Queue管理器狀態
            queue_status = queue_manager.get_queue_status()
            print(f"📦 QueueManager狀態:")
            print(f"  • 運行中: {queue_status.get('running', False)}")
            print(f"  • Tick佇列大小: {queue_status.get('tick_queue_size', 0)}/{queue_status.get('tick_queue_maxsize', 0)}")
            print(f"  • 日誌佇列大小: {queue_status.get('log_queue_size', 0)}/{queue_status.get('log_queue_maxsize', 0)}")
            print(f"  • 已接收Tick: {queue_status.get('stats', {}).get('tick_received', 0)}")
            print(f"  • 已處理Tick: {queue_status.get('stats', {}).get('tick_processed', 0)}")
            
            # 檢查Tick處理器狀態
            processor_status = tick_processor.get_status()
            print(f"🔄 TickProcessor狀態:")
            print(f"  • 運行中: {processor_status.get('running', False)}")
            print(f"  • 線程存活: {processor_status.get('thread_alive', False)}")
            print(f"  • 回調函數數量: {processor_status.get('callback_count', 0)}")
            print(f"  • 已處理計數: {processor_status.get('stats', {}).get('processed_count', 0)}")
            print(f"  • 錯誤計數: {processor_status.get('stats', {}).get('error_count', 0)}")
            
            return queue_status.get('running', False) and processor_status.get('running', False)
            
        except Exception as e:
            print(f"❌ 檢查狀態時發生錯誤: {e}")
            return False
    
    def simulate_tick_data(self, count=10):
        """模擬發送Tick資料到Queue"""
        print(f"\n📤 模擬發送 {count} 個Tick資料...")
        
        try:
            queue_manager = get_queue_manager()
            success_count = 0
            
            base_price = 22461
            
            for i in range(count):
                # 生成模擬Tick資料
                current_time = datetime.now()
                price_change = (i % 10) - 5  # -5到+4的價格變化
                current_price = base_price + price_change
                
                tick_data = TickData(
                    market_no="TW",
                    stock_idx=1,
                    date=int(current_time.strftime("%Y%m%d")),
                    time_hms=int(current_time.strftime("%H%M%S")) + i,
                    time_millis=current_time.microsecond // 1000,
                    bid=current_price - 1,
                    ask=current_price + 1,
                    close=current_price,
                    qty=1 + (i % 5),
                    timestamp=current_time
                )
                
                # 發送到Queue
                if queue_manager.put_tick_data(tick_data):
                    success_count += 1
                    print(f"  ✅ Tick {i+1}: 價格={current_price}, 時間={current_time.strftime('%H:%M:%S')}")
                else:
                    print(f"  ❌ Tick {i+1}: Queue已滿")
                
                time.sleep(0.1)  # 間隔100ms
            
            print(f"📊 發送結果: {success_count}/{count} 成功")
            return success_count
            
        except Exception as e:
            print(f"❌ 模擬Tick資料時發生錯誤: {e}")
            return 0
    
    def monitor_queue_processing(self, duration=10):
        """監控Queue處理情況"""
        print(f"\n⏱️ 監控Queue處理 {duration} 秒...")
        
        try:
            queue_manager = get_queue_manager()
            tick_processor = get_tick_processor()
            
            start_time = time.time()
            initial_stats = queue_manager.get_queue_status().get('stats', {})
            initial_received = initial_stats.get('tick_received', 0)
            initial_processed = initial_stats.get('tick_processed', 0)
            
            print(f"📊 初始狀態: 已接收={initial_received}, 已處理={initial_processed}")
            
            while time.time() - start_time < duration:
                current_stats = queue_manager.get_queue_status().get('stats', {})
                current_received = current_stats.get('tick_received', 0)
                current_processed = current_stats.get('tick_processed', 0)
                
                queue_size = queue_manager.get_queue_status().get('tick_queue_size', 0)
                log_size = queue_manager.get_queue_status().get('log_queue_size', 0)
                
                print(f"  📈 已接收={current_received}, 已處理={current_processed}, Queue大小={queue_size}, 日誌={log_size}")
                
                time.sleep(2)  # 每2秒檢查一次
            
            final_stats = queue_manager.get_queue_status().get('stats', {})
            final_received = final_stats.get('tick_received', 0)
            final_processed = final_stats.get('tick_processed', 0)
            
            processed_during_test = final_processed - initial_processed
            received_during_test = final_received - initial_received
            
            print(f"📊 監控結果:")
            print(f"  • 新接收Tick: {received_during_test}")
            print(f"  • 新處理Tick: {processed_during_test}")
            print(f"  • 處理效率: {(processed_during_test/max(received_during_test,1)*100):.1f}%")
            
            return processed_during_test > 0
            
        except Exception as e:
            print(f"❌ 監控處理時發生錯誤: {e}")
            return False
    
    def test_strategy_callback_integration(self):
        """測試策略回調整合"""
        print("\n🎯 測試策略回調整合...")
        
        try:
            tick_processor = get_tick_processor()
            callback_results = []
            
            def test_callback(tick_dict):
                """測試回調函數"""
                try:
                    price = tick_dict.get('corrected_price', 0)
                    formatted_time = tick_dict.get('formatted_time', '')
                    callback_results.append({
                        'price': price,
                        'time': formatted_time,
                        'timestamp': datetime.now()
                    })
                    print(f"  📊 策略回調: 價格={price}, 時間={formatted_time}")
                except Exception as e:
                    print(f"  ❌ 回調錯誤: {e}")
            
            # 添加測試回調
            tick_processor.add_strategy_callback(test_callback)
            print("✅ 測試回調函數已添加")
            
            # 發送測試資料
            sent_count = self.simulate_tick_data(5)
            
            # 等待處理
            time.sleep(3)
            
            # 檢查結果
            print(f"📊 回調結果: 發送={sent_count}, 回調={len(callback_results)}")
            
            # 移除測試回調
            tick_processor.remove_strategy_callback(test_callback)
            print("🧹 測試回調函數已移除")
            
            return len(callback_results) > 0
            
        except Exception as e:
            print(f"❌ 測試策略回調時發生錯誤: {e}")
            return False
    
    def run_comprehensive_test(self):
        """運行綜合測試"""
        print("🧪 開始實時Queue架構綜合測試")
        print("=" * 60)
        
        test_results = []
        
        # 測試1: 檢查基礎設施狀態
        print("📋 測試1: 檢查Queue基礎設施狀態")
        infrastructure_ok = self.check_queue_infrastructure_status()
        test_results.append(("基礎設施狀態", infrastructure_ok))
        
        if not infrastructure_ok:
            print("❌ Queue基礎設施未正常運行，請檢查OrderTester.py中的Queue控制面板")
            print("💡 建議: 在OrderTester.py中點擊 '🚀 啟動Queue服務' 按鈕")
            return False
        
        # 測試2: 模擬Tick資料處理
        print("\n📋 測試2: 模擬Tick資料處理")
        sent_count = self.simulate_tick_data(10)
        test_results.append(("Tick資料發送", sent_count > 0))
        
        # 測試3: 監控處理情況
        print("\n📋 測試3: 監控Queue處理")
        processing_ok = self.monitor_queue_processing(8)
        test_results.append(("Queue處理", processing_ok))
        
        # 測試4: 策略回調整合
        print("\n📋 測試4: 策略回調整合")
        callback_ok = self.test_strategy_callback_integration()
        test_results.append(("策略回調", callback_ok))
        
        # 最終結果
        print("\n" + "=" * 60)
        print("📊 綜合測試結果:")
        
        passed_tests = 0
        for test_name, result in test_results:
            status = "✅ 通過" if result else "❌ 失敗"
            print(f"  {status} {test_name}")
            if result:
                passed_tests += 1
        
        success_rate = (passed_tests / len(test_results)) * 100
        print(f"\n🎯 測試通過率: {success_rate:.1f}% ({passed_tests}/{len(test_results)})")
        
        if success_rate >= 75:
            print("🎉 Queue架構運行正常！")
            print("✅ 新架構已成功整合到OrderTester.py")
            print("💡 現在可以等待實際Tick資料，或進入階段3")
        else:
            print("⚠️ 部分測試失敗，需要檢查配置")
            print("💡 建議檢查OrderTester.py中的Queue控制面板設定")
        
        return success_rate >= 75

def main():
    """主函數"""
    print("🚀 啟動實時Queue架構測試工具")
    print("📝 此工具將測試OrderTester.py中的Queue架構是否正常工作")
    print()
    
    tester = LiveQueueArchitectureTest()
    
    try:
        success = tester.run_comprehensive_test()
        
        if success:
            print("\n🎯 測試建議:")
            print("1. 在OrderTester.py中查看Queue控制面板狀態")
            print("2. 等待實際Tick資料進來時觀察處理情況")
            print("3. 可以手動切換Queue模式和傳統模式進行對比")
            print("4. 準備進入階段3：策略處理線程整合")
        else:
            print("\n🔧 故障排除建議:")
            print("1. 確認OrderTester.py已啟動")
            print("2. 在Queue控制面板中點擊 '🚀 啟動Queue服務'")
            print("3. 檢查是否有錯誤訊息")
            print("4. 嘗試切換到Queue模式")
        
    except KeyboardInterrupt:
        print("\n⏹️ 測試被用戶中斷")
    except Exception as e:
        print(f"\n❌ 測試過程中發生錯誤: {e}")

if __name__ == "__main__":
    main()
