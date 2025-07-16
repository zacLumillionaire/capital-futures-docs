#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
鎖生命週期診斷工具
詳細追蹤每個鎖的創建、檢查和釋放過程
"""

import os
import sys
import time
from datetime import datetime

# 添加當前目錄到路徑
current_dir = os.path.dirname(os.path.abspath(__file__))
if current_dir not in sys.path:
    sys.path.insert(0, current_dir)

class LockLifecycleDiagnostic:
    """鎖生命週期診斷器"""
    
    def __init__(self):
        self.lock_history = []
        self.console_enabled = True
    
    def log_event(self, event_type: str, position_id: str, details: dict = None):
        """記錄鎖事件"""
        event = {
            'timestamp': time.time(),
            'time_str': datetime.now().strftime('%H:%M:%S.%f')[:-3],
            'event_type': event_type,
            'position_id': position_id,
            'details': details or {}
        }
        self.lock_history.append(event)
        
        if self.console_enabled:
            print(f"[LOCK_DIAG] {event['time_str']} {event_type}: 部位{position_id}")
            if details:
                for key, value in details.items():
                    print(f"[LOCK_DIAG]   {key}: {value}")
    
    def check_current_locks(self):
        """檢查當前所有鎖定狀態"""
        try:
            from simplified_order_tracker import GlobalExitManager
            
            manager = GlobalExitManager()
            current_locks = dict(manager.exit_locks)
            
            print(f"\n[LOCK_DIAG] 📊 當前鎖定狀態檢查 ({datetime.now().strftime('%H:%M:%S')})")
            print(f"[LOCK_DIAG] 總鎖定數: {len(current_locks)}")
            
            if not current_locks:
                print(f"[LOCK_DIAG] ✅ 無任何鎖定")
                return
            
            for position_id, lock_info in current_locks.items():
                timestamp = lock_info.get('timestamp', 0)
                age = time.time() - timestamp
                trigger_source = lock_info.get('trigger_source', 'unknown')
                reason = lock_info.get('reason', 'unknown')
                
                print(f"[LOCK_DIAG] 🔒 部位{position_id}:")
                print(f"[LOCK_DIAG]   鎖定時間: {age:.1f}秒前")
                print(f"[LOCK_DIAG]   觸發源: {trigger_source}")
                print(f"[LOCK_DIAG]   原因: {reason}")
                
                # 檢查是否過期
                if age > 10.0:
                    print(f"[LOCK_DIAG]   ⚠️ 過期鎖定！")
                
        except Exception as e:
            print(f"[LOCK_DIAG] ❌ 檢查鎖定狀態失敗: {e}")
    
    def test_position_specific_locking(self):
        """測試部位特定的鎖定機制"""
        print(f"\n[LOCK_DIAG] 🧪 測試部位特定鎖定機制")
        
        try:
            from simplified_order_tracker import GlobalExitManager
            
            manager = GlobalExitManager()
            manager.clear_all_exits()
            
            # 測試場景：兩個部位使用相同的 trigger_source
            position_19 = "19"
            position_20 = "20"
            trigger_source = "optimized_risk_trailing_stop_LONG"
            
            print(f"[LOCK_DIAG] 測試場景: 兩個部位使用相同 trigger_source")
            print(f"[LOCK_DIAG] trigger_source: {trigger_source}")
            
            # 部位19嘗試鎖定
            success_19 = manager.mark_exit(
                position_19, 
                trigger_source, 
                "trailing_stop",
                "部位19移動停利測試",
                {"test": True}
            )
            
            self.log_event("LOCK_ATTEMPT", position_19, {
                "success": success_19,
                "trigger_source": trigger_source
            })
            
            # 部位20嘗試鎖定
            success_20 = manager.mark_exit(
                position_20, 
                trigger_source, 
                "trailing_stop",
                "部位20移動停利測試",
                {"test": True}
            )
            
            self.log_event("LOCK_ATTEMPT", position_20, {
                "success": success_20,
                "trigger_source": trigger_source
            })
            
            # 檢查結果
            print(f"\n[LOCK_DIAG] 📊 測試結果:")
            print(f"[LOCK_DIAG] 部位19鎖定: {'✅ 成功' if success_19 else '❌ 失敗'}")
            print(f"[LOCK_DIAG] 部位20鎖定: {'✅ 成功' if success_20 else '❌ 失敗'}")
            
            if success_19 and success_20:
                print(f"[LOCK_DIAG] ✅ 正常：不同部位可以獨立鎖定")
            elif success_19 and not success_20:
                print(f"[LOCK_DIAG] ❌ 異常：部位20被部位19的鎖阻止")
                
                # 檢查部位20的鎖定狀態
                lock_reason_20 = manager.check_exit_in_progress(position_20)
                print(f"[LOCK_DIAG] 部位20鎖定原因: {lock_reason_20}")
                
            # 檢查當前鎖定狀態
            self.check_current_locks()
            
            # 清理
            manager.clear_exit(position_19)
            manager.clear_exit(position_20)
            
            return success_19 and success_20
            
        except Exception as e:
            print(f"[LOCK_DIAG] ❌ 測試失敗: {e}")
            return False
    
    def diagnose_real_scenario(self):
        """診斷真實場景中的問題"""
        print(f"\n[LOCK_DIAG] 🔍 診斷真實場景問題")
        
        try:
            from simplified_order_tracker import GlobalExitManager
            
            manager = GlobalExitManager()
            
            # 檢查是否有遺留的鎖定
            print(f"[LOCK_DIAG] 檢查系統啟動時的鎖定狀態...")
            self.check_current_locks()
            
            # 模擬部位建立後的狀態
            print(f"\n[LOCK_DIAG] 模擬部位建立完成後的狀態...")
            
            # 清除所有鎖定（模擬部位建立時的清理）
            cleared_count = manager.clear_all_exits()
            print(f"[LOCK_DIAG] 清除了 {cleared_count} 個遺留鎖定")
            
            # 再次檢查
            self.check_current_locks()
            
            return True
            
        except Exception as e:
            print(f"[LOCK_DIAG] ❌ 診斷失敗: {e}")
            return False
    
    def suggest_fixes(self):
        """建議修復方案"""
        print(f"\n[LOCK_DIAG] 💡 建議修復方案:")
        print(f"[LOCK_DIAG] 1. 在部位建立成功後立即清除該部位的所有鎖定")
        print(f"[LOCK_DIAG] 2. 在區間監控開始前檢查並清除過期鎖定")
        print(f"[LOCK_DIAG] 3. 添加更詳細的鎖定日誌，包含完整的鎖定上下文")
        print(f"[LOCK_DIAG] 4. 實現鎖定狀態的定期清理機制")
        print(f"[LOCK_DIAG] 5. 在 OptimizedRiskManager 初始化時清除所有鎖定")

def main():
    """主診斷函數"""
    print("🔍 鎖生命週期診斷工具")
    print("詳細追蹤鎖的創建、檢查和釋放過程")
    print("="*60)
    
    diagnostic = LockLifecycleDiagnostic()
    
    # 執行診斷步驟
    print("\n📋 執行診斷步驟:")
    
    # 1. 檢查當前鎖定狀態
    diagnostic.check_current_locks()
    
    # 2. 測試部位特定鎖定
    test_result = diagnostic.test_position_specific_locking()
    
    # 3. 診斷真實場景
    diagnostic.diagnose_real_scenario()
    
    # 4. 提供修復建議
    diagnostic.suggest_fixes()
    
    print(f"\n{'='*60}")
    if test_result:
        print("✅ 鎖定機制基本正常，問題可能在於鎖定的時機或清理")
    else:
        print("❌ 鎖定機制存在問題，需要進一步修復")
    
    print("建議：在部位建立成功後立即清除該部位的鎖定狀態")

if __name__ == "__main__":
    main()
