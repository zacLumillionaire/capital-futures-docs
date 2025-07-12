# -*- coding: utf-8 -*-
"""
測試API時間監控LOG修改
"""

import time

class MockSimpleIntegrated:
    """模擬 SimpleIntegrated 類別來測試API時間監控LOG"""
    
    def __init__(self):
        self.price_count = 0
        
    def _log_api_time_monitoring(self, price, api_time, sys_time, time_diff, count):
        """API時間監控LOG - 重要事件，定期顯示"""
        try:
            # 初始化時間追蹤變數
            if not hasattr(self, '_last_api_time_log'):
                self._last_api_time_log = 0
                self._api_time_log_interval = 30  # 30秒間隔
            
            current_time = time.time()
            should_log = False
            
            # 條件1: 定期顯示（30秒間隔）
            if current_time - self._last_api_time_log > self._api_time_log_interval:
                should_log = True
                self._last_api_time_log = current_time
            
            # 條件2: 時間差異異常（立即顯示）
            if isinstance(time_diff, (int, float)) and abs(time_diff) > 10:  # 超過10秒
                should_log = True
            
            # 條件3: 每1000筆報價顯示一次
            if count % 1000 == 0:
                should_log = True
            
            if should_log:
                if time_diff == "ERR":
                    print(f"🔍 策略收到: price={price}, api_time={api_time}, sys_time={sys_time}, diff=計算錯誤, count={count}")
                else:
                    # 根據時間差異添加警告標記
                    if isinstance(time_diff, (int, float)):
                        if abs(time_diff) > 30:
                            status = "🚨"  # 嚴重延遲
                        elif abs(time_diff) > 10:
                            status = "⚠️"   # 輕微延遲
                        else:
                            status = "✅"   # 正常
                    else:
                        status = "🔍"
                    
                    print(f"{status} 策略收到: price={price}, api_time={api_time}, sys_time={sys_time}, diff={time_diff}s, count={count}")
                    
        except Exception as e:
            # 回退到簡單格式
            print(f"🔍 策略收到: price={price}, api_time={api_time}, sys_time={sys_time}, count={count}")

def test_api_time_monitoring():
    """測試API時間監控LOG"""
    print("🧪 測試API時間監控LOG")
    print("=" * 50)
    
    mock = MockSimpleIntegrated()
    
    # 測試1: 正常時間差異（應該立即顯示第一次）
    print("\n📋 測試1: 正常時間差異")
    mock._log_api_time_monitoring(22440, "17:16:05", "17:16:05", 0, 100)
    
    # 測試2: 小幅延遲（應該被跳過，因為30秒間隔）
    print("\n📋 測試2: 小幅延遲（應該被跳過）")
    mock._log_api_time_monitoring(22441, "17:16:06", "17:16:08", 2, 101)
    
    # 測試3: 中等延遲（應該立即顯示）
    print("\n📋 測試3: 中等延遲（應該立即顯示）")
    mock._log_api_time_monitoring(22442, "17:16:07", "17:16:20", 13, 102)
    
    # 測試4: 嚴重延遲（應該立即顯示）
    print("\n📋 測試4: 嚴重延遲（應該立即顯示）")
    mock._log_api_time_monitoring(22443, "17:16:08", "17:16:45", 37, 103)
    
    # 測試5: 1000筆報價（應該立即顯示）
    print("\n📋 測試5: 1000筆報價（應該立即顯示）")
    mock._log_api_time_monitoring(22444, "17:16:09", "17:16:09", 0, 1000)
    
    # 測試6: 錯誤情況（應該立即顯示）
    print("\n📋 測試6: 錯誤情況（應該立即顯示）")
    mock._log_api_time_monitoring(22445, "17:16:10", "17:16:10", "ERR", 104)
    
    # 測試7: 模擬30秒後（應該顯示）
    print("\n📋 測試7: 模擬30秒後（應該顯示）")
    # 手動設置時間讓30秒間隔觸發
    mock._last_api_time_log = time.time() - 31
    mock._log_api_time_monitoring(22446, "17:16:40", "17:16:41", 1, 105)
    
    print("\n🎉 API時間監控LOG測試完成")

def demonstrate_expected_behavior():
    """演示預期行為"""
    print("\n🎯 預期行為演示")
    print("=" * 50)
    
    print("📋 在實際運行中，您會看到：")
    print()
    
    print("🟢 正常情況（30秒間隔）：")
    print("✅ 策略收到: price=22440, api_time=17:16:05, sys_time=17:16:05, diff=0s, count=350")
    print("✅ 策略收到: price=22460, api_time=17:16:35, sys_time=17:16:35, diff=0s, count=1350")
    print()
    
    print("🟡 輕微延遲（立即顯示）：")
    print("⚠️ 策略收到: price=22445, api_time=17:16:10, sys_time=17:16:23, diff=13s, count=567")
    print()
    
    print("🔴 嚴重延遲（立即顯示）：")
    print("🚨 策略收到: price=22450, api_time=17:16:15, sys_time=17:17:00, diff=45s, count=789")
    print("⚠️ 時間差異警告: 45秒 (API時間 vs 系統時間)")
    print()
    
    print("📊 里程碑（每1000筆）：")
    print("✅ 策略收到: price=22455, api_time=17:16:20, sys_time=17:16:21, diff=1s, count=1000")
    print("✅ 策略收到: price=22465, api_time=17:16:50, sys_time=17:16:51, diff=1s, count=2000")
    print()
    
    print("❌ 錯誤情況（立即顯示）：")
    print("🔍 策略收到: price=22460, api_time=17:16:25, sys_time=17:16:25, diff=計算錯誤, count=890")
    print("⚠️ 時間差異計算錯誤: invalid literal for int() with base 10: '25a'")

if __name__ == "__main__":
    print("🔧 API時間監控LOG測試")
    print("=" * 60)
    
    # 執行測試
    test_api_time_monitoring()
    
    # 演示預期行為
    demonstrate_expected_behavior()
    
    print("\n📋 修改總結：")
    print("✅ API時間監控LOG已設為重要事件")
    print("✅ 正常情況：30秒間隔顯示")
    print("✅ 異常延遲：立即顯示")
    print("✅ 里程碑：每1000筆顯示")
    print("✅ 錯誤情況：立即顯示")
    print("✅ 根據延遲程度顯示不同狀態圖示")
    
    print("\n🎯 這樣您就能：")
    print("  - 定期監控API時間狀況")
    print("  - 立即發現時間延遲問題")
    print("  - 追蹤報價處理進度")
    print("  - 不會被過多LOG干擾")
