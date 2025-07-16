#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
非阻塞資料庫更新管理器
用於延遲更新方案，確保不影響現有下單功能
"""

import threading
import queue
import time
import logging
from datetime import datetime
from typing import Dict, Any, Optional
from dataclasses import dataclass

# 設置日誌
logger = logging.getLogger(__name__)

@dataclass
class UpdateTask:
    """更新任務數據結構"""
    task_type: str  # 'position_fill', 'risk_state', 'position_status', 'position_exit'
    position_id: int
    data: Dict[str, Any]
    timestamp: float
    retry_count: int = 0
    max_retries: int = 3
    on_success_callback: callable = None  # 🔧 新增：成功後的回呼函數

class AsyncDatabaseUpdater:
    """
    非阻塞資料庫更新管理器
    
    特點：
    1. 不影響現有同步邏輯
    2. 提供內存緩存加速
    3. 延遲更新減少阻塞
    4. 詳細的性能追蹤
    """
    
    def __init__(self, db_manager, console_enabled=True):
        self.db_manager = db_manager
        self.console_enabled = console_enabled

        # 🔇 日誌控制選項
        self.enable_peak_update_logs = False  # 關閉峰值更新日誌
        self.enable_task_completion_logs = False  # 關閉任務完成日誌
        
        # 🔄 更新隊列
        self.update_queue = queue.Queue(maxsize=1000)
        self.worker_thread = None
        self.running = False

        # 🧹 清理機制
        self.cleanup_interval = 3600  # 1小時清理一次
        self.cache_max_age = 7200     # 緩存最大保留2小時
        self.last_cleanup_time = time.time()
        
        # 💾 內存緩存
        self.memory_cache = {
            'positions': {},  # position_id -> position_data
            'risk_states': {},  # position_id -> risk_data
            'exit_positions': {},  # position_id -> exit_data (🔧 新增：平倉緩存)
            'peak_updates': {},  # 🚀 新增：position_id -> peak_update_data (零風險峰值更新)
            'trailing_states': {},  # 🎯 新增：position_id -> trailing_state_data (移動停利狀態)
            'protection_states': {},  # 🛡️ 新增：position_id -> protection_state_data (保護性停損狀態)
            'position_status': {},  # 📊 新增：position_id -> position_status_data (部位狀態)
            'last_updates': {}  # position_id -> timestamp
        }
        
        # 📊 性能統計
        self.stats = {
            'total_tasks': 0,
            'completed_tasks': 0,
            'failed_tasks': 0,
            'cache_hits': 0,
            'avg_delay': 0.0,
            'max_delay': 0.0,
            'queue_size_peak': 0,
            'trailing_stop_updates': 0  # 🔧 新增：移動停利更新統計
        }
        
        # 🔒 線程安全
        self.cache_lock = threading.RLock()
        self.stats_lock = threading.RLock()
        
        # ⏰ 時間追蹤
        self.start_time = time.time()
        self.last_stats_report = time.time()
        
        if self.console_enabled:
            print("[ASYNC_DB] 🚀 非阻塞資料庫更新器初始化完成")

    def set_log_options(self, enable_peak_logs=False, enable_task_logs=False):
        """設置日誌選項"""
        self.enable_peak_update_logs = enable_peak_logs
        self.enable_task_completion_logs = enable_task_logs
        if self.console_enabled:
            print(f"[ASYNC_DB] 🔇 日誌選項更新: 峰值日誌={enable_peak_logs}, 任務日誌={enable_task_logs}")

    def start(self):
        """啟動異步更新工作線程"""
        if self.running:
            return
            
        self.running = True
        self.worker_thread = threading.Thread(target=self._worker_loop, daemon=True)
        self.worker_thread.start()
        
        if self.console_enabled:
            print("[ASYNC_DB] ✅ 異步更新工作線程已啟動")
    
    def stop(self):
        """停止異步更新"""
        self.running = False
        if self.worker_thread:
            self.worker_thread.join(timeout=5.0)
            
        if self.console_enabled:
            print("[ASYNC_DB] 🛑 異步更新工作線程已停止")
    
    def schedule_position_fill_update(self, position_id: int, fill_price: float,
                                    fill_time: str, order_status: str = 'FILLED',
                                    on_success_callback=None):
        """
        排程部位成交更新（非阻塞）

        Args:
            position_id: 部位ID
            fill_price: 成交價格
            fill_time: 成交時間
            order_status: 訂單狀態
            on_success_callback: 成功後的回呼函數 (可選)
        """
        start_time = time.time()
        
        # 🚀 立即更新內存緩存
        with self.cache_lock:
            self.memory_cache['positions'][position_id] = {
                'id': position_id,
                'fill_price': fill_price,
                'fill_time': fill_time,
                'order_status': order_status,
                'updated_at': start_time
            }
            self.memory_cache['last_updates'][position_id] = start_time
            self.stats['cache_hits'] += 1
        
        # 📝 排程資料庫更新
        task = UpdateTask(
            task_type='position_fill',
            position_id=position_id,
            data={
                'fill_price': fill_price,
                'fill_time': fill_time,
                'order_status': order_status
            },
            timestamp=start_time,
            on_success_callback=on_success_callback  # 🔧 新增：傳遞回呼函數
        )
        
        try:
            self.update_queue.put_nowait(task)
            with self.stats_lock:
                self.stats['total_tasks'] += 1
                current_queue_size = self.update_queue.qsize()
                if current_queue_size > self.stats['queue_size_peak']:
                    self.stats['queue_size_peak'] = current_queue_size
                    
            if self.console_enabled:
                elapsed = (time.time() - start_time) * 1000
                print(f"[ASYNC_DB] 📝 排程部位{position_id}成交更新 @{fill_price} (耗時:{elapsed:.1f}ms)")
                
        except queue.Full:
            logger.warning(f"更新隊列已滿，跳過部位{position_id}的異步更新")
            if self.console_enabled:
                print(f"[ASYNC_DB] ⚠️ 隊列已滿，跳過部位{position_id}異步更新")

    def schedule_position_exit_update(self, position_id: int, exit_price: float,
                                    exit_time: str, exit_reason: str = '手動出場',
                                    order_id: str = None, pnl: float = 0.0):
        """
        排程部位平倉更新（非阻塞）- 🔧 新增：參考建倉邏輯

        Args:
            position_id: 部位ID
            exit_price: 平倉價格
            exit_time: 平倉時間
            exit_reason: 平倉原因
            order_id: 訂單ID
            pnl: 損益
        """
        start_time = time.time()

        # 🚀 立即更新內存緩存（參考建倉邏輯）
        with self.cache_lock:
            self.memory_cache['exit_positions'][position_id] = {
                'id': position_id,
                'status': 'EXITED',
                'exit_price': exit_price,
                'exit_time': exit_time,
                'exit_reason': exit_reason,
                'order_id': order_id,
                'pnl': pnl,
                'updated_at': start_time
            }
            self.memory_cache['last_updates'][position_id] = start_time
            self.stats['cache_hits'] += 1

        # 📝 排程資料庫更新（參考建倉邏輯）
        task = UpdateTask(
            task_type='position_exit',
            position_id=position_id,
            data={
                'exit_price': exit_price,
                'exit_time': exit_time,
                'exit_reason': exit_reason,
                'order_id': order_id,
                'pnl': pnl
            },
            timestamp=start_time
        )

        try:
            self.update_queue.put_nowait(task)
            with self.stats_lock:
                self.stats['total_tasks'] += 1
                current_queue_size = self.update_queue.qsize()
                if current_queue_size > self.stats['queue_size_peak']:
                    self.stats['queue_size_peak'] = current_queue_size

            if self.console_enabled:
                elapsed = (time.time() - start_time) * 1000
                print(f"[ASYNC_DB] 📝 排程部位{position_id}平倉更新 @{exit_price} 原因:{exit_reason} (耗時:{elapsed:.1f}ms)")

        except queue.Full:
            logger.warning(f"更新隊列已滿，跳過部位{position_id}的平倉異步更新")
            if self.console_enabled:
                print(f"[ASYNC_DB] ⚠️ 隊列已滿，跳過部位{position_id}平倉異步更新")
    
    def schedule_risk_state_creation(self, position_id: int, peak_price: float,
                                   current_time: str, update_category: str = "初始化",
                                   update_message: str = "異步初始化"):
        """
        排程風險管理狀態創建（非阻塞）

        Args:
            position_id: 部位ID
            peak_price: 峰值價格
            current_time: 當前時間
            update_category: 更新分類
            update_message: 更新詳細訊息
        """
        start_time = time.time()
        
        # 🚀 立即更新內存緩存
        with self.cache_lock:
            self.memory_cache['risk_states'][position_id] = {
                'position_id': position_id,
                'peak_price': peak_price,
                'current_time': current_time,
                'update_category': update_category,
                'update_message': update_message,
                'updated_at': start_time
            }
            self.stats['cache_hits'] += 1

        # 📝 排程資料庫更新
        task = UpdateTask(
            task_type='risk_state',
            position_id=position_id,
            data={
                'peak_price': peak_price,
                'current_time': current_time,
                'update_category': update_category,
                'update_message': update_message
            },
            timestamp=start_time
        )
        
        try:
            self.update_queue.put_nowait(task)
            with self.stats_lock:
                self.stats['total_tasks'] += 1
                
            if self.console_enabled:
                elapsed = (time.time() - start_time) * 1000
                print(f"[ASYNC_DB] 📝 排程風險狀態{position_id}創建 峰值:{peak_price} (耗時:{elapsed:.1f}ms)")
                
        except queue.Full:
            logger.warning(f"更新隊列已滿，跳過部位{position_id}的風險狀態異步更新")

    def schedule_peak_update(self, position_id: int, peak_price: float,
                           update_time: str, update_category: str = "價格更新",
                           update_message: str = "峰值更新"):
        """
        🚀 零風險峰值更新排程（可選功能，預設不啟用）

        Args:
            position_id: 部位ID
            peak_price: 新峰值價格
            update_time: 更新時間
            update_category: 更新分類
            update_message: 更新詳細訊息
        """
        start_time = time.time()

        # 🚀 立即更新內存緩存
        with self.cache_lock:
            self.memory_cache['peak_updates'][position_id] = {
                'position_id': position_id,
                'peak_price': peak_price,
                'update_time': update_time,
                'update_category': update_category,
                'update_message': update_message,
                'updated_at': start_time
            }
            self.stats['cache_hits'] += 1

        # 📝 排程資料庫更新
        task = UpdateTask(
            task_type='peak_update',
            position_id=position_id,
            data={
                'peak_price': peak_price,
                'update_time': update_time,
                'update_category': update_category,
                'update_message': update_message
            },
            timestamp=start_time
        )

        try:
            self.update_queue.put_nowait(task)
            with self.stats_lock:
                self.stats['total_tasks'] += 1

            # 🔇 關閉峰值更新排程日誌（避免過多輸出）
            if self.console_enabled and False:  # 暫時關閉
                elapsed = (time.time() - start_time) * 1000
                print(f"[ASYNC_DB] 📈 排程峰值更新 部位{position_id} 峰值:{peak_price} (耗時:{elapsed:.1f}ms)")

        except queue.Full:
            logger.warning(f"更新隊列已滿，跳過部位{position_id}的峰值異步更新")

    def get_cached_peak(self, position_id: int) -> Optional[Dict]:
        """從內存緩存獲取最新峰值"""
        with self.cache_lock:
            return self.memory_cache['peak_updates'].get(position_id)

    def schedule_trailing_activation_update(self, position_id: int, trailing_activated: bool,
                                          peak_price: float, update_time: str,
                                          update_category: str = "移動停利啟動",
                                          update_message: str = "移動停利啟動"):
        """
        🚀 排程移動停利啟動更新（非阻塞，解決延遲問題）

        Args:
            position_id: 部位ID
            trailing_activated: 移動停利啟動狀態
            peak_price: 峰值價格
            update_time: 更新時間
            update_category: 更新分類
            update_message: 更新詳細訊息
        """
        start_time = time.time()

        # 🚀 立即更新內存緩存（移動停利狀態）
        with self.cache_lock:
            # 更新移動停利狀態緩存
            if 'trailing_states' not in self.memory_cache:
                self.memory_cache['trailing_states'] = {}

            self.memory_cache['trailing_states'][position_id] = {
                'position_id': position_id,
                'trailing_activated': trailing_activated,
                'peak_price': peak_price,
                'update_time': update_time,
                'update_category': update_category,
                'update_message': update_message,
                'updated_at': start_time
            }

            # 同時更新峰值緩存
            self.memory_cache['peak_updates'][position_id] = {
                'position_id': position_id,
                'peak_price': peak_price,
                'update_time': update_time,
                'update_category': update_category,
                'update_message': update_message,
                'updated_at': start_time
            }

            self.stats['cache_hits'] += 1

        # 📝 排程資料庫更新
        task = UpdateTask(
            task_type='trailing_activation',
            position_id=position_id,
            data={
                'trailing_activated': trailing_activated,
                'peak_price': peak_price,
                'update_time': update_time,
                'update_category': update_category,
                'update_message': update_message
            },
            timestamp=start_time
        )

        try:
            self.update_queue.put_nowait(task)
            with self.stats_lock:
                self.stats['total_tasks'] += 1

            if self.console_enabled:
                elapsed = (time.time() - start_time) * 1000
                print(f"[ASYNC_DB] 🎯 排程移動停利啟動 部位{position_id} (耗時:{elapsed:.1f}ms)")

        except queue.Full:
            logger.warning(f"更新隊列已滿，跳過部位{position_id}的移動停利啟動異步更新")

    def get_cached_trailing_state(self, position_id: int) -> Optional[Dict]:
        """從內存緩存獲取最新移動停利狀態"""
        with self.cache_lock:
            return self.memory_cache.get('trailing_states', {}).get(position_id)

    def schedule_protection_update(self, position_id: int, current_stop_loss: float,
                                 protection_activated: bool, update_time: str,
                                 update_category: str = "保護性停損更新",
                                 update_message: str = "保護性停損更新"):
        """
        🚀 排程保護性停損更新（非阻塞，解決延遲問題）

        Args:
            position_id: 部位ID
            current_stop_loss: 新停損價格
            protection_activated: 保護性停損啟動狀態
            update_time: 更新時間
            update_category: 更新分類
            update_message: 更新詳細訊息
        """
        start_time = time.time()

        # 🚀 立即更新內存緩存（保護性停損狀態）
        with self.cache_lock:
            # 更新保護性停損狀態緩存
            if 'protection_states' not in self.memory_cache:
                self.memory_cache['protection_states'] = {}

            self.memory_cache['protection_states'][position_id] = {
                'position_id': position_id,
                'current_stop_loss': current_stop_loss,
                'protection_activated': protection_activated,
                'update_time': update_time,
                'update_category': update_category,
                'update_message': update_message,
                'updated_at': start_time
            }

            self.stats['cache_hits'] += 1

        # 📝 排程資料庫更新
        task = UpdateTask(
            task_type='protection_update',
            position_id=position_id,
            data={
                'current_stop_loss': current_stop_loss,
                'protection_activated': protection_activated,
                'update_time': update_time,
                'update_category': update_category,
                'update_message': update_message
            },
            timestamp=start_time
        )

        try:
            self.update_queue.put_nowait(task)
            with self.stats_lock:
                self.stats['total_tasks'] += 1

            if self.console_enabled:
                elapsed = (time.time() - start_time) * 1000
                print(f"[ASYNC_DB] 🛡️ 排程保護性停損更新 部位{position_id} 停損:{current_stop_loss:.0f} (耗時:{elapsed:.1f}ms)")

        except queue.Full:
            logger.warning(f"更新隊列已滿，跳過部位{position_id}的保護性停損異步更新")

    def schedule_position_status_update(self, position_id: int, status: str,
                                      exit_reason: str = None, exit_price: float = None,
                                      update_reason: str = "部位狀態更新"):
        """
        🚀 排程部位狀態更新（非阻塞，解決平倉延遲問題）

        Args:
            position_id: 部位ID
            status: 部位狀態
            exit_reason: 出場原因
            exit_price: 出場價格
            update_reason: 更新原因
        """
        start_time = time.time()

        # 🚀 立即更新內存緩存（部位狀態）
        with self.cache_lock:
            # 更新部位狀態緩存
            if 'position_status' not in self.memory_cache:
                self.memory_cache['position_status'] = {}

            self.memory_cache['position_status'][position_id] = {
                'position_id': position_id,
                'status': status,
                'exit_reason': exit_reason,
                'exit_price': exit_price,
                'update_reason': update_reason,
                'updated_at': start_time
            }

            self.stats['cache_hits'] += 1

        # 📝 排程資料庫更新
        task = UpdateTask(
            task_type='position_status',
            position_id=position_id,
            data={
                'status': status,
                'exit_reason': exit_reason,
                'exit_price': exit_price,
                'update_reason': update_reason
            },
            timestamp=start_time
        )

        try:
            self.update_queue.put_nowait(task)
            with self.stats_lock:
                self.stats['total_tasks'] += 1

            if self.console_enabled:
                elapsed = (time.time() - start_time) * 1000
                print(f"[ASYNC_DB] 📊 排程部位狀態更新 部位{position_id} 狀態:{status} (耗時:{elapsed:.1f}ms)")

        except queue.Full:
            logger.warning(f"更新隊列已滿，跳過部位{position_id}的狀態異步更新")

    def get_cached_position(self, position_id: int) -> Optional[Dict]:
        """從內存緩存獲取部位信息"""
        with self.cache_lock:
            return self.memory_cache['positions'].get(position_id)
    
    def get_cached_risk_state(self, position_id: int) -> Optional[Dict]:
        """從內存緩存獲取風險狀態信息"""
        with self.cache_lock:
            return self.memory_cache['risk_states'].get(position_id)

    def get_cached_exit_status(self, position_id: int) -> Optional[Dict]:
        """從內存緩存獲取平倉狀態信息 - 🔧 新增：參考建倉緩存邏輯"""
        with self.cache_lock:
            return self.memory_cache['exit_positions'].get(position_id)

    def is_position_exited_in_cache(self, position_id: int) -> bool:
        """檢查部位是否在緩存中標記為已平倉 - 🔧 新增：快速狀態檢查"""
        cached_exit = self.get_cached_exit_status(position_id)
        return cached_exit is not None and cached_exit.get('status') == 'EXITED'

    def cleanup_old_cache_entries(self, force_cleanup: bool = False):
        """
        🧹 清理過期的內存緩存條目（防止長時間運行的內存累積）

        Args:
            force_cleanup: 是否強制清理
        """
        current_time = time.time()

        # 檢查是否需要清理
        if not force_cleanup and (current_time - self.last_cleanup_time) < self.cleanup_interval:
            return

        try:
            with self.cache_lock:
                cleaned_count = 0

                # 清理各類緩存中的過期條目
                for cache_type in ['positions', 'risk_states', 'exit_positions',
                                 'peak_updates', 'trailing_states', 'protection_states',
                                 'position_status']:

                    if cache_type not in self.memory_cache:
                        continue

                    cache = self.memory_cache[cache_type]
                    expired_keys = []

                    for key, data in cache.items():
                        if isinstance(data, dict) and 'updated_at' in data:
                            age = current_time - data['updated_at']
                            if age > self.cache_max_age:
                                expired_keys.append(key)

                    # 移除過期條目
                    for key in expired_keys:
                        del cache[key]
                        cleaned_count += 1

                # 清理last_updates
                if 'last_updates' in self.memory_cache:
                    expired_keys = []
                    for position_id, timestamp in self.memory_cache['last_updates'].items():
                        if (current_time - timestamp) > self.cache_max_age:
                            expired_keys.append(position_id)

                    for key in expired_keys:
                        del self.memory_cache['last_updates'][key]
                        cleaned_count += 1

                self.last_cleanup_time = current_time

                if self.console_enabled and cleaned_count > 0:
                    print(f"[ASYNC_DB] 🧹 清理過期緩存條目: {cleaned_count}個")

        except Exception as e:
            logger.error(f"清理內存緩存失敗: {e}")
            if self.console_enabled:
                print(f"[ASYNC_DB] ❌ 清理內存緩存失敗: {e}")
    
    def _worker_loop(self):
        """工作線程主循環"""
        if self.console_enabled:
            print("[ASYNC_DB] 🔄 異步更新工作線程開始運行")
            
        while self.running:
            try:
                # 等待更新任務（最多等待1秒）
                task = self.update_queue.get(timeout=1.0)
                self._process_update_task(task)
                self.update_queue.task_done()
                
            except queue.Empty:
                # 定期報告統計信息
                self._report_stats_if_needed()

                # 🧹 定期清理內存緩存（在空閒時執行）
                self.cleanup_old_cache_entries()
                continue
            except Exception as e:
                logger.error(f"異步更新工作線程錯誤: {e}")
                if self.console_enabled:
                    print(f"[ASYNC_DB] ❌ 工作線程錯誤: {e}")
    
    def _process_update_task(self, task: UpdateTask):
        """處理單個更新任務"""
        start_time = time.time()
        delay = start_time - task.timestamp
        
        try:
            if task.task_type == 'position_fill':
                # 任務4診斷：添加詳細的處理日誌
                if self.console_enabled:
                    print(f"[ASYNC_DB] 🔄 處理部位成交任務: 部位{task.position_id}")
                    print(f"[ASYNC_DB]   成交價格: {task.data['fill_price']}")
                    print(f"[ASYNC_DB]   成交時間: {task.data['fill_time']}")
                    print(f"[ASYNC_DB]   訂單狀態: {task.data['order_status']}")

                success = self.db_manager.confirm_position_filled(
                    position_id=task.position_id,
                    actual_fill_price=task.data['fill_price'],
                    fill_time=task.data['fill_time'],
                    order_status=task.data['order_status']
                )

                # ✅ 任務1：添加成功日誌，確認異步資料庫寫入任務最終成功執行
                if success:
                    if self.console_enabled:
                        print(f"✅ [ASYNC_DB] 資料庫寫入成功: 部位 {task.position_id}，entry_price 更新為 {task.data['fill_price']}")
                else:
                    if self.console_enabled:
                        print(f"❌ [ASYNC_DB] 部位 {task.position_id} 成交確認失敗")

                # 🔧 新增：成功後執行回呼函數
                if success and task.on_success_callback:
                    try:
                        task.on_success_callback(task.position_id)
                        if self.console_enabled:
                            print(f"[ASYNC_DB] ✅ 部位{task.position_id}成交確認回呼執行成功")
                    except Exception as callback_error:
                        logger.error(f"成交確認回呼執行失敗: {callback_error}")
                        if self.console_enabled:
                            print(f"[ASYNC_DB] ❌ 部位{task.position_id}成交確認回呼失敗: {callback_error}")
            elif task.task_type == 'risk_state':
                # 🔧 修復：檢查是否已存在風險管理狀態，避免重複創建
                try:
                    # 先嘗試創建
                    success = self.db_manager.create_risk_management_state(
                        position_id=task.position_id,
                        peak_price=task.data['peak_price'],
                        current_time=task.data['current_time'],
                        update_category=task.data['update_category'],
                        update_message=task.data['update_message']
                    )
                except Exception as create_error:
                    # 如果創建失敗（可能是重複），嘗試更新
                    if "UNIQUE constraint failed" in str(create_error) or "already exists" in str(create_error):
                        try:
                            success = self.db_manager.update_risk_management_state(
                                position_id=task.position_id,
                                peak_price=task.data['peak_price'],
                                update_time=task.data['current_time'],
                                update_category=task.data['update_category'],
                                update_message=f"異步更新-{task.data['update_message']}"
                            )
                            if self.console_enabled:
                                print(f"[ASYNC_DB] 🔄 風險狀態已存在，改為更新: 部位{task.position_id}")
                        except Exception as update_error:
                            success = False
                            logger.error(f"風險狀態更新也失敗: {update_error}")
                    else:
                        success = False
                        logger.error(f"風險狀態創建失敗: {create_error}")
                        raise create_error
            elif task.task_type == 'position_exit':
                # 🔧 新增：處理平倉任務（參考建倉處理邏輯）
                success = self._process_position_exit_task(task)
            elif task.task_type == 'peak_update':
                # 🚀 新增：處理峰值更新任務（零風險）
                success = self.db_manager.update_risk_management_state(
                    position_id=task.position_id,
                    peak_price=task.data['peak_price'],
                    update_time=task.data['update_time'],
                    update_category=task.data['update_category'],
                    update_message=task.data['update_message']
                )

                # 🔇 關閉峰值更新完成日誌（避免過多輸出）
                if self.console_enabled and success and False:  # 暫時關閉
                    processing_time = (time.time() - start_time) * 1000
                    print(f"[ASYNC_DB] ✅ 完成峰值更新 部位:{task.position_id} 峰值:{task.data['peak_price']} 延遲:{delay*1000:.1f}ms 處理:{processing_time:.1f}ms")
            elif task.task_type == 'trailing_activation':
                # 🎯 新增：處理移動停利啟動任務（解決延遲問題）
                success = self.db_manager.update_risk_management_state(
                    position_id=task.position_id,
                    trailing_activated=task.data['trailing_activated'],
                    peak_price=task.data['peak_price'],
                    update_time=task.data['update_time'],
                    update_category=task.data['update_category'],
                    update_message=task.data['update_message']
                )

                if self.console_enabled and success:
                    processing_time = (time.time() - start_time) * 1000
                    print(f"[ASYNC_DB] ✅ 完成移動停利啟動 部位:{task.position_id} 延遲:{delay*1000:.1f}ms 處理:{processing_time:.1f}ms")
            elif task.task_type == 'protection_update':
                # 🛡️ 新增：處理保護性停損更新任務（解決延遲問題）
                success = self.db_manager.update_risk_management_state(
                    position_id=task.position_id,
                    current_stop_loss=task.data['current_stop_loss'],
                    protection_activated=task.data['protection_activated'],
                    update_time=task.data['update_time'],
                    update_category=task.data['update_category'],
                    update_message=task.data['update_message']
                )

                if self.console_enabled and success:
                    processing_time = (time.time() - start_time) * 1000
                    print(f"[ASYNC_DB] ✅ 完成保護性停損更新 部位:{task.position_id} 停損:{task.data['current_stop_loss']:.0f} 延遲:{delay*1000:.1f}ms 處理:{processing_time:.1f}ms")
            elif task.task_type == 'position_status':
                # 📊 新增：處理部位狀態更新任務（解決平倉延遲問題）
                success = self.db_manager.update_position_status(
                    position_id=task.position_id,
                    status=task.data['status'],
                    exit_reason=task.data.get('exit_reason'),
                    exit_price=task.data.get('exit_price')
                )

                if self.console_enabled and success:
                    processing_time = (time.time() - start_time) * 1000
                    print(f"[ASYNC_DB] ✅ 完成部位狀態更新 部位:{task.position_id} 狀態:{task.data['status']} 延遲:{delay*1000:.1f}ms 處理:{processing_time:.1f}ms")
            elif task.task_type == 'trailing_stop_update':
                # 🔧 新增：處理移動停利更新任務
                success = self._process_trailing_stop_update_task(task)
            else:
                logger.warning(f"未知的任務類型: {task.task_type}")
                return
            
            # 📊 更新統計
            with self.stats_lock:
                if success:
                    self.stats['completed_tasks'] += 1
                else:
                    self.stats['failed_tasks'] += 1
                
                # 更新延遲統計
                if delay > self.stats['max_delay']:
                    self.stats['max_delay'] = delay
                
                total_completed = self.stats['completed_tasks'] + self.stats['failed_tasks']
                if total_completed > 0:
                    self.stats['avg_delay'] = (
                        (self.stats['avg_delay'] * (total_completed - 1) + delay) / total_completed
                    )
            
            # 🔇 可控的任務完成日誌（避免peak_update等過多輸出）
            if self.console_enabled and self.enable_task_completion_logs:
                elapsed = (time.time() - start_time) * 1000
                status = "✅" if success else "❌"
                print(f"[ASYNC_DB] {status} 完成{task.task_type}更新 部位:{task.position_id} "
                      f"延遲:{delay*1000:.1f}ms 處理:{elapsed:.1f}ms")
                
        except Exception as e:
            logger.error(f"處理更新任務失敗: {e}")
            with self.stats_lock:
                self.stats['failed_tasks'] += 1
            
            # 重試機制
            if task.retry_count < task.max_retries:
                task.retry_count += 1
                try:
                    self.update_queue.put_nowait(task)
                    if self.console_enabled:
                        print(f"[ASYNC_DB] 🔄 重試任務 部位:{task.position_id} 次數:{task.retry_count}")
                except queue.Full:
                    logger.warning(f"重試隊列已滿，放棄部位{task.position_id}的更新")
    
    def _report_stats_if_needed(self):
        """定期報告統計信息"""
        current_time = time.time()
        if current_time - self.last_stats_report >= 30.0:  # 每30秒報告一次
            self.report_performance_stats()
            self.last_stats_report = current_time
    
    def report_performance_stats(self):
        """報告性能統計"""
        with self.stats_lock:
            uptime = time.time() - self.start_time
            queue_size = self.update_queue.qsize()
            
            if self.console_enabled:
                print(f"\n[ASYNC_DB] 📊 性能統計報告 (運行時間: {uptime:.1f}s)")
                print(f"  總任務數: {self.stats['total_tasks']}")
                print(f"  完成任務: {self.stats['completed_tasks']}")
                print(f"  失敗任務: {self.stats['failed_tasks']}")
                print(f"  緩存命中: {self.stats['cache_hits']}")
                print(f"  平均延遲: {self.stats['avg_delay']*1000:.1f}ms")
                print(f"  最大延遲: {self.stats['max_delay']*1000:.1f}ms")
                print(f"  當前隊列: {queue_size}")
                print(f"  隊列峰值: {self.stats['queue_size_peak']}")
                
                if self.stats['total_tasks'] > 0:
                    success_rate = (self.stats['completed_tasks'] / self.stats['total_tasks']) * 100
                    print(f"  成功率: {success_rate:.1f}%")
                print()
    
    def get_stats(self) -> Dict:
        """獲取統計信息"""
        with self.stats_lock:
            return self.stats.copy()

    def _process_position_exit_task(self, task: UpdateTask) -> bool:
        """
        處理平倉任務 - 🔧 新增：參考建倉任務處理邏輯

        Args:
            task: 平倉更新任務

        Returns:
            bool: 處理是否成功
        """
        try:
            # 檢查資料庫管理器是否有平倉更新方法
            if hasattr(self.db_manager, 'update_position_exit_status'):
                # 使用專用的平倉更新方法
                success = self.db_manager.update_position_exit_status(
                    position_id=task.position_id,  # 保持與db_manager參數一致
                    exit_price=task.data['exit_price'],
                    exit_time=task.data['exit_time'],
                    exit_reason=task.data['exit_reason'],
                    order_id=task.data.get('order_id'),
                    pnl=task.data.get('pnl', 0.0)
                )
            else:
                # 回退到通用的資料庫更新方法
                success = self._update_position_exit_fallback(task)

            if self.console_enabled and success:
                print(f"[ASYNC_DB] ✅ 平倉狀態更新成功: 部位{task.position_id} "
                      f"@{task.data['exit_price']} 原因:{task.data['exit_reason']}")

            return success

        except Exception as e:
            logger.error(f"處理平倉任務失敗: {e}")
            if self.console_enabled:
                print(f"[ASYNC_DB] ❌ 平倉任務處理失敗: 部位{task.position_id} 錯誤:{e}")
            return False

    def _update_position_exit_fallback(self, task: UpdateTask) -> bool:
        """
        平倉更新回退方法 - 🔧 新增：當專用方法不存在時使用

        Args:
            task: 平倉更新任務

        Returns:
            bool: 更新是否成功
        """
        try:
            # 使用原有的資料庫連接方式更新
            with self.db_manager.get_connection() as conn:
                cursor = conn.cursor()

                # 更新 position_records 表
                cursor.execute('''
                    UPDATE position_records
                    SET status = 'EXITED',
                        exit_price = ?,
                        exit_time = ?,
                        exit_reason = ?,
                        pnl = ?,
                        updated_at = CURRENT_TIMESTAMP
                    WHERE id = ?
                ''', (
                    task.data['exit_price'],
                    task.data['exit_time'],
                    task.data['exit_reason'],
                    task.data.get('pnl', 0.0),
                    task.position_id
                ))

                # 檢查是否有更新到記錄
                if cursor.rowcount == 0:
                    logger.warning(f"平倉更新未影響任何記錄: 部位{task.position_id}")
                    return False

                conn.commit()
                return True

        except Exception as e:
            logger.error(f"平倉更新回退方法失敗: {e}")
            return False

    def schedule_trailing_stop_update(self, position_id: int, peak_price: float,
                                    stop_price: float, is_activated: bool) -> bool:
        """
        排程移動停利更新任務 - 🔧 新增：支援移動停利計算器

        Args:
            position_id: 部位ID
            peak_price: 峰值價格
            stop_price: 停利價格
            is_activated: 是否已啟動

        Returns:
            bool: 排程是否成功
        """
        try:
            # 立即更新內存緩存
            with self.cache_lock:
                if 'trailing_stops' not in self.memory_cache:
                    self.memory_cache['trailing_stops'] = {}

                cache_key = f"trailing_stop_{position_id}"
                self.memory_cache['trailing_stops'][cache_key] = {
                    'position_id': position_id,
                    'peak_price': peak_price,
                    'stop_price': stop_price,
                    'is_activated': is_activated,
                    'update_time': time.time()
                }

            # 創建更新任務
            task = UpdateTask(
                task_type='trailing_stop_update',
                position_id=position_id,
                data={
                    'peak_price': peak_price,
                    'stop_price': stop_price,
                    'is_activated': is_activated,
                    'update_time': time.time()
                },
                priority=3,  # 中等優先級
                timestamp=time.time()
            )

            # 排程到更新隊列
            self.update_queue.put_nowait(task)

            # 更新統計
            with self.stats_lock:
                self.stats['total_tasks'] += 1
                self.stats['trailing_stop_updates'] += 1

            if self.console_enabled:
                print(f"[ASYNC_DB] 📝 排程移動停利更新: 部位{position_id} "
                      f"峰值{peak_price:.0f} 停利{stop_price:.0f} 啟動:{is_activated}")

            return True

        except Exception as e:
            logger.error(f"排程移動停利更新失敗: {e}")
            if self.console_enabled:
                print(f"[ASYNC_DB] ❌ 排程移動停利更新失敗: {e}")
            return False

    def _process_trailing_stop_update_task(self, task: UpdateTask) -> bool:
        """
        處理移動停利更新任務 - 🔧 新增：支援移動停利計算器

        Args:
            task: 移動停利更新任務

        Returns:
            bool: 處理是否成功
        """
        try:
            position_id = task.position_id
            data = task.data

            with self.db_manager.get_connection() as conn:
                cursor = conn.cursor()

                # 檢查是否存在移動停利記錄
                cursor.execute('''
                    SELECT id AS record_pk FROM trailing_stop_records
                    WHERE position_id = ? AND status = 'ACTIVE'
                ''', (position_id,))

                existing_record = cursor.fetchone()

                if existing_record:
                    # 更新現有記錄
                    cursor.execute('''
                        UPDATE trailing_stop_records
                        SET peak_price = ?,
                            current_stop_price = ?,
                            is_activated = ?,
                            last_update_time = CURRENT_TIMESTAMP,
                            updated_at = CURRENT_TIMESTAMP
                        WHERE position_id = ? AND status = 'ACTIVE'
                    ''', (
                        data['peak_price'],
                        data['stop_price'],
                        1 if data['is_activated'] else 0,
                        position_id
                    ))
                else:
                    # 創建新記錄
                    cursor.execute('''
                        INSERT INTO trailing_stop_records (
                            position_id, peak_price, current_stop_price,
                            is_activated, last_update_time, status, created_at
                        ) VALUES (?, ?, ?, ?, CURRENT_TIMESTAMP, 'ACTIVE', CURRENT_TIMESTAMP)
                    ''', (
                        position_id,
                        data['peak_price'],
                        data['stop_price'],
                        1 if data['is_activated'] else 0
                    ))

                conn.commit()

                if self.console_enabled:
                    action = "更新" if existing_record else "創建"
                    print(f"[ASYNC_DB] ✅ {action}移動停利記錄: 部位{position_id} "
                          f"峰值{data['peak_price']:.0f} 停利{data['stop_price']:.0f}")

                return True

        except Exception as e:
            logger.error(f"處理移動停利更新任務失敗: {e}")
            if self.console_enabled:
                print(f"[ASYNC_DB] ❌ 移動停利更新失敗: {e}")
            return False

# 全域實例（可選）
_global_async_updater = None

def get_global_async_updater():
    """獲取全域異步更新器實例"""
    return _global_async_updater

def initialize_global_async_updater(db_manager, console_enabled=True):
    """初始化全域異步更新器"""
    global _global_async_updater
    if _global_async_updater is None:
        _global_async_updater = AsyncDatabaseUpdater(db_manager, console_enabled)
        _global_async_updater.start()
    return _global_async_updater
