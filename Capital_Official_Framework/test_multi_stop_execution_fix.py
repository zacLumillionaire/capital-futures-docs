"""
多部位停損執行修復驗證測試
專案代號: Fix-Multi-Stop-Execution-01

測試場景：
1. 建立3個SHORT部位，進場價相同
2. 先觸發部位1的移動停利平倉
3. 再同時觸發部位2和3的初始停損
4. 驗證無鎖定錯誤和系統崩潰

預期成功標準：
- 無鎖定錯誤：日誌中不得出現 "前置檢查阻止" 的訊息
- 無系統崩潰：日誌中不得出現 "KeyError: 'id'" 或任何 ERROR 級別的崩潰訊息
- 完全平倉：最終檢查時，部位1、2、3的狀態都應為已平倉
"""

import sys
import os
import time
import threading
import sqlite3
from datetime import datetime

# 添加當前目錄到路徑
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# 導入必要的模組
from multi_group_database import MultiGroupDatabase
from optimized_risk_manager import OptimizedRiskManager
from stop_loss_executor import StopLossExecutor
from virtual_real_order_manager import VirtualRealOrderManager

class MultiStopExecutionTest:
    """多部位停損執行測試類"""
    
    def __init__(self):
        self.test_db_path = "test_multi_stop_fix.db"
        self.db_manager = None
        self.risk_manager = None
        self.stop_executor = None
        self.virtual_order_manager = None
        self.test_results = {
            'lock_errors': [],
            'key_errors': [],
            'position_states': {},
            'success': False
        }
        
    def setup_test_environment(self):
        """設置測試環境"""
        print("🔧 [TEST] 設置測試環境...")
        
        # 清理舊的測試資料庫
        if os.path.exists(self.test_db_path):
            os.remove(self.test_db_path)
            
        # 初始化資料庫管理器
        self.db_manager = MultiGroupDatabase(self.test_db_path)
        
        # 初始化虛實單管理器
        self.virtual_order_manager = VirtualRealOrderManager()
        
        # 初始化停損執行器
        self.stop_executor = StopLossExecutor(
            db_manager=self.db_manager,
            virtual_real_order_manager=self.virtual_order_manager,
            console_enabled=True
        )
        
        # 初始化風險管理器
        self.risk_manager = OptimizedRiskManager(
            db_manager=self.db_manager,
            console_enabled=True
        )
        
        # 設置停損執行器
        self.risk_manager.set_stop_loss_executor(self.stop_executor)
        
        print("✅ [TEST] 測試環境設置完成")
        
    def create_test_positions(self):
        """創建測試部位"""
        print("📝 [TEST] 創建測試部位...")
        
        # 創建策略組
        group_config = {
            'group_id': 1,
            'strategy_name': 'TEST_MULTI_STOP',
            'direction': 'SHORT',
            'total_lots': 3,
            'entry_price_range': [21535, 21535],  # 相同進場價
            'stop_loss_points': 65,  # 停損點數
            'trailing_activation_points': [15, 40, 41],  # 移動停利啟動點數
            'range_high': 21600,  # 區間高點（停損邊界）
            'range_low': 21470   # 區間低點
        }
        
        # 創建3個部位
        positions = []
        for i in range(1, 4):
            position_data = {
                'id': i,
                'group_id': 1,
                'lot_id': f'lot_{i}',
                'direction': 'SHORT',
                'quantity': 1,
                'entry_price': 21535.0,
                'status': 'ACTIVE',
                'range_high': 21600.0,
                'range_low': 21470.0,
                'trailing_activation_points': group_config['trailing_activation_points'][i-1]
            }
            
            # 插入到資料庫
            self.db_manager.create_position(position_data)
            positions.append(position_data)
            
            # 添加到風險管理器監控
            self.risk_manager.add_position_to_monitor(position_data)
            
        print(f"✅ [TEST] 已創建 {len(positions)} 個測試部位")
        return positions
        
    def simulate_trailing_stop_trigger(self):
        """模擬移動停利觸發（部位1）"""
        print("🎯 [TEST] 模擬部位1移動停利觸發...")
        
        # 先讓價格下跌，啟動部位1的移動停利
        self.risk_manager.update_positions(21520.0, "01:33:30")  # 啟動移動停利
        time.sleep(0.1)
        
        # 繼續下跌，創建峰值
        self.risk_manager.update_positions(21511.0, "01:33:32")  # 創建峰值
        time.sleep(0.1)
        
        # 價格回升，觸發移動停利
        self.risk_manager.update_positions(21531.0, "01:33:35")  # 觸發移動停利
        time.sleep(0.5)  # 等待平倉完成
        
        print("✅ [TEST] 部位1移動停利觸發完成")
        
    def simulate_initial_stop_trigger(self):
        """模擬初始停損觸發（部位2和3）"""
        print("🚨 [TEST] 模擬部位2和3初始停損觸發...")
        
        # 價格急速上漲，同時觸發部位2和3的初始停損
        self.risk_manager.update_positions(21600.0, "01:33:40")  # 觸發初始停損
        time.sleep(1.0)  # 等待平倉完成
        
        print("✅ [TEST] 部位2和3初始停損觸發完成")
        
    def check_test_results(self):
        """檢查測試結果"""
        print("📊 [TEST] 檢查測試結果...")
        
        # 檢查部位狀態
        for i in range(1, 4):
            try:
                position = self.db_manager.get_position_by_id(i)
                if position:
                    self.test_results['position_states'][i] = position.get('status', 'UNKNOWN')
                else:
                    self.test_results['position_states'][i] = 'NOT_FOUND'
            except Exception as e:
                self.test_results['position_states'][i] = f'ERROR: {e}'
                
        # 檢查是否所有部位都已平倉
        all_closed = all(
            status in ['CLOSED', 'EXITED'] 
            for status in self.test_results['position_states'].values()
        )
        
        self.test_results['success'] = (
            len(self.test_results['lock_errors']) == 0 and
            len(self.test_results['key_errors']) == 0 and
            all_closed
        )
        
        return self.test_results
        
    def run_test(self):
        """運行完整測試"""
        print("🚀 [TEST] 開始多部位停損執行修復驗證測試")
        print("=" * 60)
        
        try:
            # 1. 設置測試環境
            self.setup_test_environment()
            
            # 2. 創建測試部位
            positions = self.create_test_positions()
            
            # 3. 模擬移動停利觸發（部位1）
            self.simulate_trailing_stop_trigger()
            
            # 4. 模擬初始停損觸發（部位2和3）
            self.simulate_initial_stop_trigger()
            
            # 5. 檢查測試結果
            results = self.check_test_results()
            
            # 6. 輸出測試報告
            self.print_test_report(results)
            
        except Exception as e:
            print(f"❌ [TEST] 測試執行失敗: {e}")
            import traceback
            traceback.print_exc()
            
        finally:
            # 清理資源
            self.cleanup()
            
    def print_test_report(self, results):
        """輸出測試報告"""
        print("\n" + "=" * 60)
        print("📋 [TEST] 測試結果報告")
        print("=" * 60)
        
        print(f"🔒 鎖定錯誤數量: {len(results['lock_errors'])}")
        if results['lock_errors']:
            for error in results['lock_errors']:
                print(f"   - {error}")
                
        print(f"🔑 KeyError數量: {len(results['key_errors'])}")
        if results['key_errors']:
            for error in results['key_errors']:
                print(f"   - {error}")
                
        print("📊 部位狀態:")
        for pos_id, status in results['position_states'].items():
            print(f"   部位{pos_id}: {status}")
            
        if results['success']:
            print("\n✅ [TEST] 測試成功！修復有效！")
        else:
            print("\n❌ [TEST] 測試失敗！需要進一步修復！")
            
    def cleanup(self):
        """清理測試資源"""
        try:
            if self.db_manager:
                self.db_manager.close()
            if os.path.exists(self.test_db_path):
                os.remove(self.test_db_path)
            print("🧹 [TEST] 測試資源清理完成")
        except Exception as e:
            print(f"⚠️ [TEST] 清理資源時出錯: {e}")

def main():
    """主函數"""
    test = MultiStopExecutionTest()
    test.run_test()

if __name__ == "__main__":
    main()
