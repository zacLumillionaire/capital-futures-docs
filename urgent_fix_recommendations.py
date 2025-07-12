#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
🚨 緊急修復建議
基於診斷結果的具體修復方案
"""

# ============================================================================
# 🔥 優先級1：口級別機制修復（立即執行）
# ============================================================================

def fix_global_exit_manager_timeout():
    """修復1：調整GlobalExitManager超時設置"""
    print("🔧 修復1：調整GlobalExitManager超時設置")
    
    # 在 simplified_order_tracker.py 中修改
    fix_code = '''
    class GlobalExitManager:
        def __init__(self):
            self.exit_locks = {}
            # 🔧 修復：從0.1秒增加到2.0秒，應對報價延遲
            self.exit_timeout = 2.0  # 原來是0.1秒，太短了
            self._initialized = True
    '''
    
    print("📝 修改文件：simplified_order_tracker.py")
    print("📍 位置：GlobalExitManager.__init__")
    print("🔧 修改：self.exit_timeout = 2.0")
    print("💡 原因：0.1秒無法應對4688ms的報價延遲")

def fix_stop_loss_executor_timeout():
    """修復2：調整StopLossExecutor中的超時設置"""
    print("\n🔧 修復2：調整StopLossExecutor超時設置")
    
    # 在 stop_loss_executor.py 中修改
    fix_code = '''
    class GlobalExitManager:  # 備用版本
        def __init__(self):
            self.exit_locks = {}
            # 🔧 修復：調整為2.0秒，與主版本一致
            self.exit_timeout = 2.0  # 原來是0.5秒
    '''
    
    print("📝 修改文件：stop_loss_executor.py")
    print("📍 位置：GlobalExitManager.__init__ (備用版本)")
    print("🔧 修改：self.exit_timeout = 2.0")

def fix_data_lock_contention():
    """修復3：減少數據鎖競爭"""
    print("\n🔧 修復3：減少數據鎖競爭")
    
    # 在 simplified_order_tracker.py 中優化鎖定範圍
    fix_code = '''
    def register_exit_group(self, position_id: int, total_lots: int,
                           direction: str, exit_direction: str, target_price: float,
                           product: str = "TM0000") -> bool:
        try:
            # 🔧 修復：縮小鎖定範圍，只鎖定必要操作
            exit_group = ExitGroup(
                position_id=position_id,
                total_lots=total_lots,
                direction=direction,
                exit_direction=exit_direction,
                target_price=target_price,
                product=product,
                enable_cancel_retry=self.default_enable_cancel_retry,
                enable_partial_retry=self.default_enable_partial_retry
            )
            
            # 🔧 修復：快速鎖定，立即釋放
            with self.data_lock:
                self.exit_groups[position_id] = exit_group
            
            # 🔧 修復：日誌輸出移到鎖外
            if self.console_enabled:
                print(f"[SIMPLIFIED_TRACKER] 📝 註冊平倉組: 部位{position_id}")
            
            return True
    '''
    
    print("📝 修改文件：simplified_order_tracker.py")
    print("📍 位置：register_exit_group方法")
    print("🔧 修改：縮小data_lock鎖定範圍")
    print("💡 原因：減少8次數據鎖競爭")

# ============================================================================
# 🔥 優先級2：資料庫查詢修復（立即執行）
# ============================================================================

def fix_position_query_with_retry():
    """修復4：添加查詢重試機制"""
    print("\n🔧 修復4：添加查詢重試機制")
    
    # 在 stop_loss_executor.py 中修改 _get_position_info
    fix_code = '''
    def _get_position_info(self, position_id: int) -> Optional[Dict]:
        """取得部位詳細資訊 - 🔧 修復：添加重試機制"""
        max_retries = 3
        
        for attempt in range(max_retries):
            try:
                from datetime import date
                with self.db_manager.get_connection() as conn:
                    # 🔧 修復：設置更長的超時時間
                    conn.execute("PRAGMA busy_timeout = 3000")  # 3秒超時
                    cursor = conn.cursor()
                    
                    cursor.execute('''
                        SELECT pr.*, sg.range_high, sg.range_low, sg.direction as group_direction
                        FROM position_records pr
                        JOIN (
                            SELECT * FROM strategy_groups
                            WHERE date = ?
                            ORDER BY id DESC
                        ) sg ON pr.group_id = sg.group_id
                        WHERE pr.id = ? AND pr.status = 'ACTIVE'
                    ''', (date.today().isoformat(), position_id))

                    row = cursor.fetchone()
                    if row:
                        columns = [description[0] for description in cursor.description]
                        return dict(zip(columns, row))
                    elif attempt < max_retries - 1:
                        # 🔧 修復：查詢失敗時短暫等待重試
                        if self.console_enabled:
                            print(f"[STOP_EXECUTOR] 🔄 部位{position_id}查詢重試 {attempt + 1}/{max_retries}")
                        time.sleep(0.1)
                    
                    return None

            except sqlite3.OperationalError as e:
                if "database is locked" in str(e) and attempt < max_retries - 1:
                    if self.console_enabled:
                        print(f"[STOP_EXECUTOR] 🔒 資料庫鎖定，重試 {attempt + 1}/{max_retries}")
                    time.sleep(0.2)  # 等待更長時間
                else:
                    logger.error(f"查詢部位資訊失敗: {e}")
                    return None
            except Exception as e:
                logger.error(f"查詢部位資訊失敗: {e}")
                if attempt < max_retries - 1:
                    time.sleep(0.1)
                else:
                    return None
        
        return None
    '''
    
    print("📝 修改文件：stop_loss_executor.py")
    print("📍 位置：_get_position_info方法")
    print("🔧 修改：添加3次重試 + 3秒超時")
    print("💡 原因：提高70%的併發查詢成功率")

def fix_join_query_optimization():
    """修復5：優化JOIN查詢"""
    print("\n🔧 修復5：優化JOIN查詢")
    
    # 簡化JOIN查詢，減少複雜度
    fix_code = '''
    def _get_position_info_optimized(self, position_id: int) -> Optional[Dict]:
        """優化版部位查詢 - 🔧 修復：簡化JOIN查詢"""
        try:
            from datetime import date
            with self.db_manager.get_connection() as conn:
                conn.execute("PRAGMA busy_timeout = 3000")
                cursor = conn.cursor()
                
                # 🔧 修復：分步查詢，避免複雜JOIN
                # 步驟1：查詢部位基本信息
                cursor.execute('''
                    SELECT * FROM position_records 
                    WHERE id = ? AND status = 'ACTIVE'
                ''', (position_id,))
                
                position_row = cursor.fetchone()
                if not position_row:
                    return None
                
                # 轉換為字典
                columns = [description[0] for description in cursor.description]
                position_data = dict(zip(columns, position_row))
                
                # 步驟2：查詢策略組信息
                group_id = position_data.get('group_id')
                if group_id:
                    cursor.execute('''
                        SELECT range_high, range_low, direction as group_direction
                        FROM strategy_groups
                        WHERE group_id = ? AND date = ?
                        ORDER BY id DESC
                        LIMIT 1
                    ''', (group_id, date.today().isoformat()))
                    
                    group_row = cursor.fetchone()
                    if group_row:
                        # 合併策略組信息
                        position_data['range_high'] = group_row[0]
                        position_data['range_low'] = group_row[1]
                        position_data['group_direction'] = group_row[2]
                
                return position_data

        except Exception as e:
            logger.error(f"優化查詢失敗: {e}")
            # 🔧 修復：回退到原始查詢
            return self._get_position_info_original(position_id)
    '''
    
    print("📝 修改文件：stop_loss_executor.py")
    print("📍 位置：新增_get_position_info_optimized方法")
    print("🔧 修改：分步查詢替代複雜JOIN")
    print("💡 原因：降低7.5/10的查詢複雜度")

# ============================================================================
# 🔥 優先級3：Async機制修復（後續執行）
# ============================================================================

def fix_async_queue_processing():
    """修復6：增強異步隊列處理"""
    print("\n🔧 修復6：增強異步隊列處理")
    
    # 在相關的異步更新器中修改
    fix_code = '''
    class AsyncPositionUpdater:
        def __init__(self):
            # 🔧 修復：增加處理能力
            self.max_queue_size = 20  # 從10增加到20
            self.batch_size = 5       # 批量處理5個任務
            self.worker_threads = 2   # 增加工作線程
            
        def process_queue(self):
            """🔧 修復：批量處理隊列任務"""
            while self.is_running:
                try:
                    # 批量獲取任務
                    tasks = []
                    for _ in range(self.batch_size):
                        if not self.update_queue.empty():
                            tasks.append(self.update_queue.get_nowait())
                    
                    if tasks:
                        # 批量處理
                        self.process_batch_tasks(tasks)
                    else:
                        time.sleep(0.1)  # 無任務時短暫等待
                        
                except Exception as e:
                    self.error_count += 1
                    logger.error(f"隊列處理錯誤: {e}")
    '''
    
    print("📝 修改文件：相關的異步更新器")
    print("🔧 修改：增加處理能力和批量處理")
    print("💡 原因：解決15個任務積壓和6.5秒延遲")

def fix_cache_lock_optimization():
    """修復7：優化緩存鎖定"""
    print("\n🔧 修復7：優化緩存鎖定")
    
    # 在 optimized_risk_manager.py 中修改
    fix_code = '''
    def _process_cached_positions(self, current_price: float, timestamp: str) -> Dict:
        """處理緩存中的部位 - 🔧 修復：優化鎖定策略"""
        results = {
            'stop_loss_triggers': 0,
            'trailing_activations': 0,
            'peak_updates': 0,
            'drawdown_triggers': 0
        }
        
        try:
            # 🔧 修復：使用讀鎖進行快照
            position_snapshot = {}
            with self.cache_lock:
                position_snapshot = self.position_cache.copy()
            
            # 🔧 修復：在鎖外處理，減少鎖定時間
            for position_id, position_data in position_snapshot.items():
                # 處理邏輯...
                if self._check_stop_loss_trigger(position_id, current_price):
                    results['stop_loss_triggers'] += 1
                # 其他處理...
            
            return results
            
        except Exception as e:
            logger.error(f"緩存處理失敗: {e}")
            return results
    '''
    
    print("📝 修改文件：optimized_risk_manager.py")
    print("🔧 修改：使用快照減少鎖定時間")
    print("💡 原因：減少12次緩存鎖競爭")

# ============================================================================
# 📋 修復實施計劃
# ============================================================================

def create_fix_implementation_plan():
    """創建修復實施計劃"""
    print("\n" + "="*80)
    print("📋 修復實施計劃")
    print("="*80)
    
    plan = {
        "立即修復（今天）": [
            "1. 調整GlobalExitManager超時：0.1秒 → 2.0秒",
            "2. 添加查詢重試機制：3次重試 + 3秒超時",
            "3. 縮小data_lock鎖定範圍"
        ],
        "短期修復（1-2天）": [
            "4. 優化JOIN查詢：分步查詢替代複雜JOIN",
            "5. 增強異步隊列處理能力",
            "6. 優化緩存鎖定策略"
        ],
        "驗證測試（修復後）": [
            "7. 重新運行診斷工具驗證修復效果",
            "8. 監控併發查詢成功率是否提升到>90%",
            "9. 確認鎖定競爭是否減少"
        ]
    }
    
    for phase, tasks in plan.items():
        print(f"\n🎯 {phase}:")
        for task in tasks:
            print(f"  {task}")
    
    print(f"\n💡 預期效果:")
    print(f"  ✅ 併發查詢成功率：70% → 95%+")
    print(f"  ✅ 鎖定競爭次數：12次 → <3次")
    print(f"  ✅ 查詢超時問題：基本解決")
    print(f"  ✅ 平倉失敗率：大幅降低")

def main():
    """主函數"""
    print("🚨 基於診斷結果的緊急修復建議")
    print("="*80)
    print("📊 診斷發現的關鍵問題:")
    print("  ❌ 鎖定超時過短：0.1秒")
    print("  ❌ 併發查詢成功率過低：70%")
    print("  ❌ 鎖定競爭嚴重：12次緩存鎖競爭")
    print("  ❌ JOIN查詢複雜度過高：7.5/10")
    print("="*80)
    
    # 顯示所有修復建議
    fix_global_exit_manager_timeout()
    fix_stop_loss_executor_timeout()
    fix_data_lock_contention()
    fix_position_query_with_retry()
    fix_join_query_optimization()
    fix_async_queue_processing()
    fix_cache_lock_optimization()
    
    # 創建實施計劃
    create_fix_implementation_plan()
    
    print("\n" + "="*80)
    print("⚠️ 重要提醒")
    print("="*80)
    print("1. 🛑 建議在非交易時間進行修復")
    print("2. 💾 修復前請備份相關文件")
    print("3. 🔧 一次修復一個問題，逐步驗證")
    print("4. 📊 修復後重新運行診斷工具驗證效果")
    print("5. 🎯 優先修復鎖定超時問題（影響最大）")

if __name__ == "__main__":
    main()
