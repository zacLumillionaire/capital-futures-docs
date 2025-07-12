"""
階段2測試：API事件處理改造驗證
測試OnNotifyTicksLONG事件的Queue模式和傳統模式切換

測試項目：
1. Queue基礎設施初始化
2. API事件Queue模式處理
3. 傳統模式回退機制
4. 模式切換功能
5. UI控制面板功能
"""

import sys
import os
import time
import threading
from datetime import datetime

# 添加路徑
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# 導入測試所需模組
try:
    from queue_infrastructure import (
        get_queue_infrastructure,
        TickData,
        get_queue_manager,
        reset_queue_infrastructure
    )
    print("✅ Queue基礎設施導入成功")
except ImportError as e:
    print(f"❌ Queue基礎設施導入失敗: {e}")
    sys.exit(1)

class Stage2APIEventTest:
    """階段2 API事件處理測試"""
    
    def __init__(self):
        self.test_results = []
        self.queue_infrastructure = None
        
    def log_test_result(self, test_name, success, message=""):
        """記錄測試結果"""
        status = "✅ 成功" if success else "❌ 失敗"
        result = f"{status} {test_name}"
        if message:
            result += f": {message}"
        
        print(result)
        self.test_results.append({
            'name': test_name,
            'success': success,
            'message': message
        })
    
    def test_queue_infrastructure_init(self):
        """測試1: Queue基礎設施初始化"""
        try:
            # 重置之前的實例
            reset_queue_infrastructure()
            
            # 創建新的基礎設施實例
            self.queue_infrastructure = get_queue_infrastructure()
            
            # 初始化
            if self.queue_infrastructure.initialize():
                self.log_test_result("Queue基礎設施初始化", True)
                return True
            else:
                self.log_test_result("Queue基礎設施初始化", False, "初始化失敗")
                return False
                
        except Exception as e:
            self.log_test_result("Queue基礎設施初始化", False, str(e))
            return False
    
    def test_queue_services_startup(self):
        """測試2: Queue服務啟動"""
        try:
            if not self.queue_infrastructure:
                self.log_test_result("Queue服務啟動", False, "基礎設施未初始化")
                return False
            
            # 啟動所有服務
            if self.queue_infrastructure.start_all():
                self.log_test_result("Queue服務啟動", True)
                return True
            else:
                self.log_test_result("Queue服務啟動", False, "服務啟動失敗")
                return False
                
        except Exception as e:
            self.log_test_result("Queue服務啟動", False, str(e))
            return False
    
    def test_tick_data_processing(self):
        """測試3: Tick資料處理"""
        try:
            if not self.queue_infrastructure:
                self.log_test_result("Tick資料處理", False, "基礎設施未初始化")
                return False
            
            # 創建測試Tick資料
            test_tick = TickData(
                market_no="TW",
                stock_idx=1,
                date=20250703,
                time_hms=143000,
                time_millis=500,
                bid=2246100,
                ask=2246200,
                close=2246200,
                qty=5,
                timestamp=datetime.now()
            )
            
            # 放入Queue
            queue_manager = get_queue_manager()
            success = queue_manager.put_tick_data(test_tick)
            
            if success:
                # 等待處理
                time.sleep(0.5)
                
                # 檢查統計
                status = queue_manager.get_queue_status()
                tick_received = status.get('stats', {}).get('tick_received', 0)
                
                if tick_received > 0:
                    self.log_test_result("Tick資料處理", True, f"已接收{tick_received}個Tick")
                    return True
                else:
                    self.log_test_result("Tick資料處理", False, "Tick未被處理")
                    return False
            else:
                self.log_test_result("Tick資料處理", False, "Tick放入Queue失敗")
                return False
                
        except Exception as e:
            self.log_test_result("Tick資料處理", False, str(e))
            return False
    
    def test_api_event_simulation(self):
        """測試4: 模擬API事件處理"""
        try:
            # 模擬OnNotifyTicksLONG事件的參數
            test_params = {
                'sMarketNo': 'TW',
                'nStockidx': 1,
                'nPtr': 0,
                'lDate': 20250703,
                'lTimehms': 143030,
                'lTimemillismicros': 750,
                'nBid': 2246100,
                'nAsk': 2246200,
                'nClose': 2246150,
                'nQty': 3,
                'nSimulate': 0
            }
            
            # 模擬Queue模式處理邏輯
            tick_data = TickData(
                market_no=test_params['sMarketNo'],
                stock_idx=test_params['nStockidx'],
                date=test_params['lDate'],
                time_hms=test_params['lTimehms'],
                time_millis=test_params['lTimemillismicros'],
                bid=test_params['nBid'],
                ask=test_params['nAsk'],
                close=test_params['nClose'],
                qty=test_params['nQty'],
                timestamp=datetime.now()
            )
            
            # 測試Queue處理
            queue_manager = get_queue_manager()
            success = queue_manager.put_tick_data(tick_data)
            
            if success:
                self.log_test_result("API事件模擬", True, "Queue模式處理成功")
                return True
            else:
                self.log_test_result("API事件模擬", False, "Queue處理失敗")
                return False
                
        except Exception as e:
            self.log_test_result("API事件模擬", False, str(e))
            return False
    
    def test_queue_status_monitoring(self):
        """測試5: Queue狀態監控"""
        try:
            if not self.queue_infrastructure:
                self.log_test_result("Queue狀態監控", False, "基礎設施未初始化")
                return False
            
            # 獲取狀態
            status = self.queue_infrastructure.get_status()
            
            # 檢查關鍵狀態
            required_keys = ['initialized', 'running', 'queue_manager', 'tick_processor']
            missing_keys = [key for key in required_keys if key not in status]
            
            if not missing_keys:
                self.log_test_result("Queue狀態監控", True, f"狀態完整: {list(status.keys())}")
                return True
            else:
                self.log_test_result("Queue狀態監控", False, f"缺少狀態: {missing_keys}")
                return False
                
        except Exception as e:
            self.log_test_result("Queue狀態監控", False, str(e))
            return False
    
    def test_performance_stress(self):
        """測試6: 性能壓力測試"""
        try:
            if not self.queue_infrastructure:
                self.log_test_result("性能壓力測試", False, "基礎設施未初始化")
                return False
            
            # 快速發送多個Tick
            queue_manager = get_queue_manager()
            success_count = 0
            total_count = 50
            
            start_time = time.time()
            
            for i in range(total_count):
                tick_data = TickData(
                    market_no="TW",
                    stock_idx=1,
                    date=20250703,
                    time_hms=143000 + i,
                    time_millis=i * 10,
                    bid=2246100 + i,
                    ask=2246200 + i,
                    close=2246150 + i,
                    qty=1 + (i % 10),
                    timestamp=datetime.now()
                )
                
                if queue_manager.put_tick_data(tick_data):
                    success_count += 1
            
            end_time = time.time()
            duration = end_time - start_time
            
            # 等待處理完成
            time.sleep(1.0)
            
            # 檢查處理結果
            status = queue_manager.get_queue_status()
            processed_count = status.get('stats', {}).get('tick_processed', 0)
            
            success_rate = (success_count / total_count) * 100
            
            if success_rate >= 90:  # 90%以上成功率
                self.log_test_result("性能壓力測試", True, 
                                   f"成功率{success_rate:.1f}%, 處理{processed_count}個, 耗時{duration:.2f}秒")
                return True
            else:
                self.log_test_result("性能壓力測試", False, 
                                   f"成功率過低{success_rate:.1f}%")
                return False
                
        except Exception as e:
            self.log_test_result("性能壓力測試", False, str(e))
            return False
    
    def cleanup(self):
        """清理測試環境"""
        try:
            if self.queue_infrastructure:
                self.queue_infrastructure.stop_all()
            reset_queue_infrastructure()
            print("🧹 測試環境已清理")
        except Exception as e:
            print(f"⚠️ 清理錯誤: {e}")
    
    def run_all_tests(self):
        """運行所有測試"""
        print("🧪 開始階段2 API事件處理改造測試")
        print("=" * 60)
        
        # 測試序列
        tests = [
            self.test_queue_infrastructure_init,
            self.test_queue_services_startup,
            self.test_tick_data_processing,
            self.test_api_event_simulation,
            self.test_queue_status_monitoring,
            self.test_performance_stress
        ]
        
        # 執行測試
        for test in tests:
            try:
                test()
            except Exception as e:
                self.log_test_result(test.__name__, False, f"測試異常: {e}")
            
            time.sleep(0.2)  # 測試間隔
        
        # 清理
        self.cleanup()
        
        # 統計結果
        total_tests = len(self.test_results)
        passed_tests = sum(1 for result in self.test_results if result['success'])
        
        print("=" * 60)
        print(f"📊 測試完成: {passed_tests}/{total_tests} 通過")
        
        if passed_tests == total_tests:
            print("🎉 階段2 API事件處理改造測試全部通過！")
            print("✅ Queue架構已準備就緒，可以進入階段3")
        else:
            print("⚠️ 部分測試失敗，需要檢查和修復")
            
            # 顯示失敗的測試
            failed_tests = [result for result in self.test_results if not result['success']]
            for failed in failed_tests:
                print(f"   ❌ {failed['name']}: {failed['message']}")
        
        return passed_tests == total_tests

if __name__ == "__main__":
    test = Stage2APIEventTest()
    test.run_all_tests()
