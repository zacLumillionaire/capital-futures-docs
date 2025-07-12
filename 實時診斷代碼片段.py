#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
實時診斷代碼片段
這些代碼需要添加到 simple_integrated.py 中，用於實時診斷平倉問題
"""

def add_diagnostic_methods_to_simple_integrated():
    """
    將這些方法添加到 SimpleIntegratedStrategy 類中
    """
    
    diagnostic_methods = '''
    def diagnose_async_updater_status(self):
        """診斷異步更新器狀態 - 添加到 SimpleIntegratedStrategy 類中"""
        try:
            print("\\n🔍 異步更新器診斷:")
            
            if hasattr(self, 'multi_group_position_manager') and self.multi_group_position_manager:
                manager = self.multi_group_position_manager
                
                # 檢查異步更新器
                if hasattr(manager, 'async_updater') and manager.async_updater:
                    updater = manager.async_updater
                    print(f"  ✅ 異步更新器存在")
                    
                    # 檢查隊列狀態
                    if hasattr(updater, 'update_queue'):
                        queue_size = len(updater.update_queue) if updater.update_queue else 0
                        print(f"  📊 更新隊列大小: {queue_size}")
                        
                        if queue_size > 10:
                            print(f"  ⚠️ 隊列積壓嚴重: {queue_size}個任務")
                    
                    # 檢查運行狀態
                    if hasattr(updater, 'is_running'):
                        print(f"  📊 運行狀態: {updater.is_running}")
                    
                    # 檢查最後更新時間
                    if hasattr(updater, 'last_update_time'):
                        import time
                        if updater.last_update_time:
                            elapsed = time.time() - updater.last_update_time
                            print(f"  📊 最後更新: {elapsed:.1f}秒前")
                            if elapsed > 30:
                                print(f"  ⚠️ 更新延遲過久: {elapsed:.1f}秒")
                    
                    # 檢查統計信息
                    if hasattr(updater, 'get_stats'):
                        stats = updater.get_stats()
                        print(f"  📊 更新統計: {stats}")
                
                else:
                    print(f"  ❌ 異步更新器不存在")
            else:
                print(f"  ❌ multi_group_position_manager 不存在")
                
        except Exception as e:
            print(f"  ❌ 異步更新器診斷失敗: {e}")
    
    def diagnose_optimized_risk_manager_cache(self):
        """診斷OptimizedRiskManager緩存狀態"""
        try:
            print("\\n🔍 OptimizedRiskManager緩存診斷:")
            
            if hasattr(self, 'optimized_risk_manager') and self.optimized_risk_manager:
                manager = self.optimized_risk_manager
                
                # 檢查問題部位
                problem_positions = [133, 134, 135]
                
                for position_id in problem_positions:
                    position_id_str = str(position_id)
                    
                    # 檢查position_cache
                    in_position_cache = position_id_str in manager.position_cache
                    print(f"  📊 部位{position_id}:")
                    print(f"    - position_cache: {in_position_cache}")
                    
                    if in_position_cache:
                        pos_data = manager.position_cache[position_id_str]
                        print(f"    - 緩存方向: {pos_data.get('direction', 'N/A')}")
                        print(f"    - 緩存狀態: {pos_data.get('status', 'N/A')}")
                    
                    # 檢查stop_loss_cache
                    in_stop_loss_cache = position_id_str in manager.stop_loss_cache
                    print(f"    - stop_loss_cache: {in_stop_loss_cache}")
                    if in_stop_loss_cache:
                        stop_loss = manager.stop_loss_cache[position_id_str]
                        print(f"    - 停損價格: {stop_loss}")
                    
                    # 檢查trailing_cache
                    in_trailing_cache = position_id_str in manager.trailing_cache
                    print(f"    - trailing_cache: {in_trailing_cache}")
                    if in_trailing_cache:
                        trailing_data = manager.trailing_cache[position_id_str]
                        print(f"    - 移動停利狀態: {trailing_data}")
                
                # 檢查總體緩存大小
                print(f"  📊 總體緩存狀態:")
                print(f"    - position_cache: {len(manager.position_cache)}個部位")
                print(f"    - stop_loss_cache: {len(manager.stop_loss_cache)}個停損")
                print(f"    - trailing_cache: {len(manager.trailing_cache)}個移動停利")
                
            else:
                print(f"  ❌ optimized_risk_manager 不存在")
                
        except Exception as e:
            print(f"  ❌ 緩存診斷失敗: {e}")
    
    def diagnose_simplified_tracker_status(self):
        """診斷SimplifiedOrderTracker狀態"""
        try:
            print("\\n🔍 SimplifiedOrderTracker診斷:")
            
            # 檢查stop_loss_executor
            if hasattr(self, 'stop_loss_executor') and self.stop_loss_executor:
                executor = self.stop_loss_executor
                
                # 檢查simplified_tracker
                if hasattr(executor, 'simplified_tracker') and executor.simplified_tracker:
                    tracker = executor.simplified_tracker
                    print(f"  ✅ simplified_tracker 存在")
                    
                    # 檢查exit_groups
                    if hasattr(tracker, 'exit_groups'):
                        exit_groups_count = len(tracker.exit_groups)
                        print(f"  📊 exit_groups: {exit_groups_count}個")
                        
                        # 檢查問題部位的exit_groups
                        problem_positions = [133, 134, 135]
                        for position_id in problem_positions:
                            if position_id in tracker.exit_groups:
                                exit_group = tracker.exit_groups[position_id]
                                print(f"    - 部位{position_id}: 存在exit_group")
                                print(f"      方向: {exit_group.direction}")
                                print(f"      總口數: {exit_group.total_lots}")
                                print(f"      追價次數: {exit_group.individual_retry_counts}")
                            else:
                                print(f"    - 部位{position_id}: 無exit_group")
                    
                    # 檢查global_exit_manager
                    if hasattr(tracker, 'global_exit_manager'):
                        manager = tracker.global_exit_manager
                        print(f"  📊 global_exit_manager:")
                        print(f"    - 鎖定超時: {manager.exit_timeout}秒")
                        print(f"    - 當前鎖定: {len(manager.exit_locks)}個")
                        
                        # 顯示當前鎖定
                        import time
                        for key, info in manager.exit_locks.items():
                            elapsed = time.time() - info['timestamp']
                            print(f"      {key}: {elapsed:.1f}秒前 ({info['trigger_source']})")
                
                else:
                    print(f"  ❌ simplified_tracker 不存在")
            else:
                print(f"  ❌ stop_loss_executor 不存在")
                
        except Exception as e:
            print(f"  ❌ SimplifiedTracker診斷失敗: {e}")
    
    def diagnose_database_query_performance(self):
        """診斷資料庫查詢性能"""
        try:
            print("\\n🔍 資料庫查詢性能診斷:")
            
            if hasattr(self, 'stop_loss_executor') and self.stop_loss_executor:
                executor = self.stop_loss_executor
                
                # 測試查詢性能
                problem_positions = [133, 134, 135]
                
                for position_id in problem_positions:
                    import time
                    start_time = time.time()
                    
                    # 調用實際的查詢方法
                    if hasattr(executor, '_get_position_info'):
                        result = executor._get_position_info(position_id)
                        elapsed = (time.time() - start_time) * 1000
                        
                        print(f"  📊 部位{position_id}查詢:")
                        print(f"    - 耗時: {elapsed:.1f}ms")
                        print(f"    - 結果: {'成功' if result else '失敗'}")
                        
                        if elapsed > 100:
                            print(f"    ⚠️ 查詢延遲過高: {elapsed:.1f}ms")
                        
                        if not result:
                            print(f"    ❌ 查詢失敗，需要詳細診斷")
                
        except Exception as e:
            print(f"  ❌ 資料庫查詢診斷失敗: {e}")
    
    def run_comprehensive_diagnosis(self):
        """運行綜合診斷 - 在報價處理中調用"""
        print("\\n" + "="*60)
        print("🚨 平倉問題綜合診斷")
        print("="*60)
        
        # 運行所有診斷
        self.diagnose_async_updater_status()
        self.diagnose_optimized_risk_manager_cache()
        self.diagnose_simplified_tracker_status()
        self.diagnose_database_query_performance()
        
        print("\\n" + "="*60)
        print("🔍 診斷完成")
        print("="*60)
    '''
    
    return diagnostic_methods

def get_ondata_diagnostic_code():
    """
    獲取需要添加到OnNewData中的診斷代碼
    """
    
    ondata_code = '''
    # 🔍 在OnNewData中添加診斷代碼（在報價處理延遲警告後）
    
    # 📊 性能監控：計算報價處理總耗時
    quote_elapsed = (time.time() - quote_start_time) * 1000
    
    # 🚨 延遲警告：如果報價處理超過100ms，輸出警告
    if quote_elapsed > 100:
        print(f"[PERFORMANCE] ⚠️ 報價處理延遲: {quote_elapsed:.1f}ms")
        
        # 🔍 觸發診斷（只在延遲嚴重時）
        if quote_elapsed > 1000:  # 超過1秒才診斷
            print(f"[DIAGNOSTIC] 🚨 觸發緊急診斷")
            self.run_comprehensive_diagnosis()
    
    # 🔍 定期診斷（每1000次報價）
    if hasattr(self, 'diagnostic_counter'):
        self.diagnostic_counter += 1
    else:
        self.diagnostic_counter = 1
    
    if self.diagnostic_counter % 1000 == 0:
        print(f"[DIAGNOSTIC] 📊 定期診斷 (第{self.diagnostic_counter}次報價)")
        self.run_comprehensive_diagnosis()
    '''
    
    return ondata_code

if __name__ == "__main__":
    print("🔍 實時診斷代碼片段")
    print("請將這些代碼添加到 simple_integrated.py 中")
    print("\n1. 將診斷方法添加到 SimpleIntegratedStrategy 類中")
    print("2. 在 OnNewData 中添加診斷觸發代碼")
    print("3. 運行系統並觀察診斷輸出")
