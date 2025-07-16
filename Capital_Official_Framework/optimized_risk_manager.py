"""
優化風險管理器 - 事件觸發 + 內存緩存
採用最安全的漸進式實施方法，確保系統穩定性
"""

import time
import threading
import sqlite3
from typing import Dict, List, Optional, Any
from datetime import datetime
import logging

logger = logging.getLogger(__name__)

# 🔧 導入全局平倉管理器
try:
    from simplified_order_tracker import GlobalExitManager
except ImportError:
    # 如果導入失敗，創建一個簡化版本
    class GlobalExitManager:
        def __init__(self):
            self.exit_locks = {}

        def mark_exit(self, position_id: str, trigger_source: str = "unknown", exit_type: str = "stop_loss") -> bool:
            return True  # 簡化版本總是允許


class OptimizedRiskManager:
    """
    優化風險管理器
    
    核心特性：
    1. 事件觸發更新 - 新部位立即監控
    2. 內存緩存 - 純內存比較，極快速度
    3. 5秒備份同步 - 確保數據一致性
    4. 安全回退機制 - 出錯時自動回退到原始方法
    """
    
    def __init__(self, db_manager, original_managers: Dict = None, console_enabled: bool = True):
        """
        初始化優化風險管理器

        Args:
            db_manager: 資料庫管理器
            original_managers: 原始管理器字典 (用於回退)
            console_enabled: 是否啟用Console日誌
        """
        self.db_manager = db_manager
        self.console_enabled = console_enabled

        # 🛡️ 安全機制：保留原始管理器作為回退
        self.original_managers = original_managers or {}
        self.fallback_mode = False

        # 🔧 新增：停損執行器支持
        self.stop_loss_executor = None

        # 🔧 新增：全局平倉管理器
        self.global_exit_manager = GlobalExitManager()

        # 🚀 任務2新增：異步更新器支持
        self.async_updater = None

        # 📊 內存緩存
        self.position_cache = {}  # {position_id: position_data}
        self.stop_loss_cache = {}  # {position_id: stop_loss_price}
        self.activation_cache = {}  # {position_id: activation_price}
        self.trailing_cache = {}  # {position_id: trailing_data}
        
        # ⏰ 時間控制
        self.last_backup_update = 0
        self.backup_interval = 60.0  # 🔧 修復：改為60秒備份更新，減少延遲
        self.last_cache_refresh = 0
        self.sync_skip_count = 0  # 🔧 新增：跳過計數器
        
        # 📈 統計信息
        self.stats = {
            'cache_hits': 0,
            'cache_misses': 0,
            'backup_syncs': 0,
            'fallback_calls': 0,
            'processing_errors': 0
        }
        
        # 🔒 線程安全
        self.cache_lock = threading.RLock()

        # 🔧 新增：觸發去重機制（正式報價環境適配）
        self.trigger_dedup_cache = {}  # {position_id: {'price': float, 'timestamp': float, 'trigger_type': str}}
        self.quote_intervals = []  # 記錄報價間隔，用於環境檢測
        self.last_quote_time = 0

        # 🔧 環境自適應參數
        self._detect_and_set_dedup_params()

        # 🚀 初始化緩存
        self._initial_cache_load()

        # 🔧 新增：清除所有遺留的平倉鎖定
        self._clear_all_exit_locks()

        if self.console_enabled:
            print("[OPTIMIZED_RISK] ✅ 優化風險管理器初始化完成")

    def set_async_updater(self, async_updater):
        """
        設置異步更新器 - 任務2新增

        Args:
            async_updater: 異步資料庫更新器實例
        """
        self.async_updater = async_updater
        if self.console_enabled:
            print("[OPTIMIZED_RISK] 🚀 異步更新器已設置")

    def _clear_all_exit_locks(self):
        """清除所有遺留的平倉鎖定"""
        try:
            if self.global_exit_manager:
                cleared_count = self.global_exit_manager.clear_all_exits()
                if self.console_enabled:
                    print(f"[OPTIMIZED_RISK] 🧹 初始化時清除了 {cleared_count} 個遺留鎖定")
        except Exception as e:
            if self.console_enabled:
                print(f"[OPTIMIZED_RISK] ⚠️ 清除遺留鎖定失敗: {e}")

    def _should_skip_trigger(self, position_id: str, current_price: float, trigger_type: str) -> bool:
        """
        檢查是否應該跳過觸發（去重機制）

        Args:
            position_id: 部位ID
            current_price: 當前價格
            trigger_type: 觸發類型 (stop_loss, trailing_stop, activation)

        Returns:
            bool: True表示應該跳過，False表示可以執行
        """
        current_time = time.time()
        cache_key = position_id

        # 檢查是否有最近的觸發記錄
        if cache_key in self.trigger_dedup_cache:
            last_trigger = self.trigger_dedup_cache[cache_key]
            time_diff = current_time - last_trigger['timestamp']
            price_diff = abs(current_price - last_trigger['price'])

            # 🔧 任務4：智能頻率限制
            # 如果在去重時間內且價格變化不大，跳過觸發
            if (time_diff < self.dedup_timeout and
                price_diff < self.min_price_change and  # 價格變化小於最小閾值
                last_trigger['trigger_type'] == trigger_type):

                if self.console_enabled:
                    print(f"[OPTIMIZED_RISK] 🔄 跳過重複觸發: 部位{position_id} {trigger_type}")
                    print(f"[OPTIMIZED_RISK]   時間間隔: {time_diff:.3f}秒, 價格差: {price_diff:.1f}點")
                    print(f"[OPTIMIZED_RISK]   閾值: 時間>{self.dedup_timeout}秒 或 價格>{self.min_price_change}點")
                return True

            # 🔧 特殊情況：如果價格變化顯著，允許立即重新觸發
            if price_diff >= self.min_price_change * 2:  # 價格變化超過2倍閾值
                if self.console_enabled:
                    print(f"[OPTIMIZED_RISK] 🚀 價格顯著變化，允許重新觸發: 部位{position_id}")
                    print(f"[OPTIMIZED_RISK]   價格變化: {price_diff:.1f}點 (閾值: {self.min_price_change * 2:.1f}點)")
                # 不跳過，允許觸發

        # 記錄本次觸發
        self.trigger_dedup_cache[cache_key] = {
            'price': current_price,
            'timestamp': current_time,
            'trigger_type': trigger_type
        }

        # 清理過期記錄
        self._cleanup_dedup_cache(current_time)

        return False

    def _detect_and_set_dedup_params(self):
        """檢測報價環境並設置適當的去重參數"""
        try:
            # 🔧 修正：正式機和虛擬機都有500ms頻率控制，使用統一參數
            # 基於您的確認：正式機也有 enable_quote_throttle = True, interval = 500ms

            self.dedup_timeout = 1.0  # 1秒（報價間隔500ms的2倍，安全餘量）
            self.min_price_change = 3.0  # 3點（期貨常見的合理跳動）

            if self.console_enabled:
                print("[OPTIMIZED_RISK] 🔧 統一去重參數：1秒+3點（適配500ms報價間隔）")

        except Exception as e:
            # 預設參數
            self.dedup_timeout = 1.0
            self.min_price_change = 3.0
            if self.console_enabled:
                print(f"[OPTIMIZED_RISK] ⚠️ 環境檢測失敗，使用預設參數: {e}")

    def _update_quote_interval_stats(self):
        """更新報價間隔統計"""
        current_time = time.time()
        if self.last_quote_time > 0:
            interval = current_time - self.last_quote_time
            self.quote_intervals.append(interval)

            # 只保留最近50個間隔
            if len(self.quote_intervals) > 50:
                self.quote_intervals.pop(0)

            # 每50次更新檢查一次環境
            if len(self.quote_intervals) == 50:
                avg_interval = sum(self.quote_intervals) / len(self.quote_intervals)
                if avg_interval > 0.3:  # 大於300ms，可能是虛擬環境
                    if self.dedup_timeout < 1.0:
                        self.dedup_timeout = 1.0
                        self.min_price_change = 3.0
                        if self.console_enabled:
                            print(f"[OPTIMIZED_RISK] 🔧 檢測到低頻報價({avg_interval:.3f}s)，調整為寬鬆參數")

        self.last_quote_time = current_time

    def _cleanup_dedup_cache(self, current_time: float):
        """清理過期的去重記錄"""
        expired_keys = []
        for key, data in self.trigger_dedup_cache.items():
            if current_time - data['timestamp'] > self.dedup_timeout * 2:
                expired_keys.append(key)

        for key in expired_keys:
            self.trigger_dedup_cache.pop(key, None)

    def set_stop_loss_executor(self, stop_loss_executor):
        """設置停損執行器"""
        self.stop_loss_executor = stop_loss_executor
        if self.console_enabled:
            print("[OPTIMIZED_RISK] 🔗 停損執行器已設置")

    def invalidate_position_cache(self, position_id: str):
        """
        使部位緩存失效 - 用於平倉後清理緩存

        Args:
            position_id: 部位ID (字符串或整數)
        """
        try:
            # 🔧 確保 position_id 為字符串格式
            position_id_str = str(position_id)

            with self.cache_lock:
                # 🧹 安全地從各個緩存中移除部位數據
                removed_items = []

                if position_id_str in self.position_cache:
                    self.position_cache.pop(position_id_str, None)
                    removed_items.append("position_cache")

                if position_id_str in self.stop_loss_cache:
                    self.stop_loss_cache.pop(position_id_str, None)
                    removed_items.append("stop_loss_cache")

                if position_id_str in self.activation_cache:
                    self.activation_cache.pop(position_id_str, None)
                    removed_items.append("activation_cache")

                if position_id_str in self.trailing_cache:
                    self.trailing_cache.pop(position_id_str, None)
                    removed_items.append("trailing_cache")

                if self.console_enabled and removed_items:
                    print(f"[OPTIMIZED_RISK] 🧹 緩存失效: 部位{position_id_str}")
                    print(f"[OPTIMIZED_RISK]   清理項目: {', '.join(removed_items)}")
                elif self.console_enabled:
                    print(f"[OPTIMIZED_RISK] ⚠️ 緩存失效: 部位{position_id_str} 不在緩存中")

        except Exception as e:
            logger.error(f"緩存失效失敗: {e}")
            if self.console_enabled:
                print(f"[OPTIMIZED_RISK] ❌ 緩存失效異常: 部位{position_id}, 錯誤: {e}")

    def _initial_cache_load(self):
        """初始化時載入緩存"""
        try:
            with self.cache_lock:
                self._sync_with_database()
                if self.console_enabled:
                    print(f"[OPTIMIZED_RISK] 📊 初始緩存載入: {len(self.position_cache)} 個部位")
        except Exception as e:
            logger.error(f"初始緩存載入失敗: {e}")
            if self.console_enabled:
                print(f"[OPTIMIZED_RISK] ❌ 初始緩存載入失敗: {e}")
    
    def on_new_position(self, position_data):
        """
        新部位事件觸發 - 立即加入監控

        Args:
            position_data: 部位數據（可能是字典或sqlite3.Row）
        """
        try:
            # 🔧 修復：安全轉換 sqlite3.Row 為字典
            if hasattr(position_data, 'keys'):
                # 這是 sqlite3.Row 對象
                try:
                    position_dict = dict(position_data)
                except Exception:
                    # 手動轉換
                    position_dict = {key: position_data[key] for key in position_data.keys()}
                if self.console_enabled:
                    print(f"[OPTIMIZED_RISK] 🔧 轉換 sqlite3.Row 為字典")
            elif isinstance(position_data, dict):
                position_dict = position_data.copy()
            else:
                if self.console_enabled:
                    print(f"[OPTIMIZED_RISK] ⚠️ 部位數據類型無效: {type(position_data)}")
                return

            position_id = position_dict.get('id')
            if not position_id:
                if self.console_enabled:
                    print(f"[OPTIMIZED_RISK] ⚠️ 部位ID無效或缺失")
                return

            with self.cache_lock:
                # 🎯 立即加入緩存並標記為需要同步
                position_dict['_needs_sync'] = True  # 標記新部位需要同步到資料庫
                position_dict['_cache_timestamp'] = time.time()  # 記錄緩存時間
                # 🔧 修復：確保鍵為字串類型，保持一致性
                self.position_cache[str(position_id)] = position_dict

                # 🔢 預計算關鍵價格點位
                self._precalculate_levels(position_dict)

                # 🔧 新增：清除該部位的任何遺留鎖定
                if self.global_exit_manager:
                    try:
                        self.global_exit_manager.clear_exit(str(position_id))
                        if self.console_enabled:
                            print(f"[OPTIMIZED_RISK] 🧹 清除部位{position_id}的遺留鎖定")
                    except Exception as clear_error:
                        if self.console_enabled:
                            print(f"[OPTIMIZED_RISK] ⚠️ 清除鎖定失敗: {clear_error}")

                if self.console_enabled:
                    direction = position_dict.get('direction', 'UNKNOWN')
                    entry_price = position_dict.get('entry_price', 0)
                    print(f"[OPTIMIZED_RISK] 🎯 新部位監控: {position_id} {direction} @{entry_price}")

        except Exception as e:
            logger.error(f"新部位事件處理失敗: {e}")
            if self.console_enabled:
                print(f"[OPTIMIZED_RISK] ❌ 新部位事件失敗: {e}")
                # 🔍 詳細錯誤信息用於調試
                import traceback
                print(f"[OPTIMIZED_RISK] 🔍 詳細錯誤: {traceback.format_exc()}")
    
    def on_position_closed(self, position_id: str):
        """
        部位平倉事件觸發 - 立即移除監控
        
        Args:
            position_id: 部位ID
        """
        try:
            with self.cache_lock:
                # 🗑️ 從所有緩存中移除
                self.position_cache.pop(position_id, None)
                self.stop_loss_cache.pop(position_id, None)
                self.activation_cache.pop(position_id, None)
                self.trailing_cache.pop(position_id, None)
                
                if self.console_enabled:
                    print(f"[OPTIMIZED_RISK] 🗑️ 移除部位監控: {position_id}")
                    
        except Exception as e:
            logger.error(f"部位移除失敗: {e}")
            if self.console_enabled:
                print(f"[OPTIMIZED_RISK] ❌ 部位移除失敗: {e}")
    
    def update_price(self, current_price: float, timestamp: str = None) -> Dict:
        """
        優化版價格更新處理

        Args:
            current_price: 當前價格
            timestamp: 時間戳

        Returns:
            Dict: 處理結果統計
        """
        if timestamp is None:
            timestamp = datetime.now().strftime('%H:%M:%S')

        try:
            # 🔧 更新報價間隔統計（用於環境檢測）
            self._update_quote_interval_stats()

            # 🛡️ 安全檢查：如果在回退模式，使用原始方法
            if self.fallback_mode:
                return self._fallback_update(current_price, timestamp)

            # ⏰ 備份同步機制
            current_time = time.time()
            if current_time - self.last_backup_update >= self.backup_interval:
                self._sync_with_database()
                self.last_backup_update = current_time
                self.stats['backup_syncs'] += 1

            # 🚀 主要邏輯：純內存比較
            results = self._process_cached_positions(current_price, timestamp)

            # 任務2：整合 RiskManagementEngine 的檢查邏輯
            # 檢查初始停損、收盤平倉、每日風控等
            additional_results = self._check_additional_risk_conditions(current_price, timestamp)

            # 合併結果
            for key, value in additional_results.items():
                if key in results:
                    results[key] += value
                else:
                    results[key] = value

            self.stats['cache_hits'] += 1
            return results

        except Exception as e:
            logger.error(f"優化價格更新失敗: {e}")
            self.stats['processing_errors'] += 1

            # 🛡️ 自動回退到原始方法
            if self.console_enabled:
                print(f"[OPTIMIZED_RISK] ⚠️ 自動回退到原始方法: {e}")

            return self._fallback_update(current_price, timestamp)
    
    def _precalculate_levels(self, position_data: Dict):
        """預計算關鍵價格點位"""
        try:
            position_id = position_data.get('id')
            direction = position_data.get('direction')
            entry_price = position_data.get('entry_price', 0)

            # 🛡️ 安全檢查：確保必要數據不為空
            range_high = position_data.get('range_high')
            range_low = position_data.get('range_low')

            # 🔧 修復：檢查 None 值和無效數據
            if not position_id:
                if self.console_enabled:
                    print(f"[OPTIMIZED_RISK] ⚠️ 部位ID無效，跳過預計算")
                return

            if range_high is None or range_low is None:
                if self.console_enabled:
                    print(f"[OPTIMIZED_RISK] ⚠️ 部位 {position_id} 區間數據無效 (high={range_high}, low={range_low})，跳過預計算")
                return

            if not isinstance(range_high, (int, float)) or not isinstance(range_low, (int, float)):
                if self.console_enabled:
                    print(f"[OPTIMIZED_RISK] ⚠️ 部位 {position_id} 區間數據類型無效，跳過預計算")
                return

            if not isinstance(entry_price, (int, float)) or entry_price <= 0:
                if self.console_enabled:
                    print(f"[OPTIMIZED_RISK] ⚠️ 部位 {position_id} 進場價格無效 ({entry_price})，跳過預計算")
                return

            # 🔧 修復：安全的數學運算
            try:
                if direction == 'LONG':
                    stop_loss = float(range_low)
                    activation_price = float(entry_price) + 15  # 15點啟動移動停利
                elif direction == 'SHORT':
                    stop_loss = float(range_high)
                    activation_price = float(entry_price) - 15
                else:
                    if self.console_enabled:
                        print(f"[OPTIMIZED_RISK] ⚠️ 部位 {position_id} 方向無效 ({direction})，跳過預計算")
                    return

                # 💾 存儲到緩存
                self.stop_loss_cache[position_id] = stop_loss
                self.activation_cache[position_id] = activation_price
                self.trailing_cache[position_id] = {
                    'activated': False,
                    'peak_price': float(entry_price),
                    'direction': direction
                }

                if self.console_enabled:
                    print(f"[OPTIMIZED_RISK] ✅ 部位 {position_id} 預計算完成: 停損={stop_loss}, 啟動={activation_price}")

            except (TypeError, ValueError) as calc_error:
                if self.console_enabled:
                    print(f"[OPTIMIZED_RISK] ⚠️ 部位 {position_id} 數學運算失敗: {calc_error}")
                return

        except Exception as e:
            logger.error(f"預計算價格點位失敗: {e}")
            if self.console_enabled:
                print(f"[OPTIMIZED_RISK] ❌ 部位預計算失敗: {e}")
    
    def _process_cached_positions(self, current_price: float, timestamp: str) -> Dict:
        """處理緩存中的部位 - 純內存比較"""
        results = {
            'stop_loss_triggers': 0,
            'trailing_activations': 0,
            'peak_updates': 0,
            'drawdown_triggers': 0
        }

        try:
            with self.cache_lock:
                # 🔧 任務1修復：確保每個部位的處理都是獨立且原子化的
                for position_id, position_data in self.position_cache.items():
                    try:
                        # 🛡️ 檢查初始停損
                        if self._check_stop_loss_trigger(position_id, current_price):
                            results['stop_loss_triggers'] += 1

                        # 🎯 檢查移動停利啟動
                        elif self._check_activation_trigger(position_id, current_price):
                            results['trailing_activations'] += 1

                        # 📈 更新已啟動的移動停利
                        elif self._update_trailing_stop(position_id, current_price):
                            results['peak_updates'] += 1

                    except Exception as position_error:
                        # 🔧 任務1修復：單個部位處理失敗不影響其他部位
                        logger.error(f"處理部位 {position_id} 失敗: {position_error}")
                        if self.console_enabled:
                            print(f"[OPTIMIZED_RISK] ❌ 部位 {position_id} 處理失敗: {position_error}")

            return results

        except Exception as e:
            logger.error(f"緩存處理失敗: {e}")
            return results

    def _check_additional_risk_conditions(self, current_price: float, timestamp: str) -> Dict:
        """
        任務2：檢查額外的風險條件 (從 RiskManagementEngine 遷移)
        包括：初始停損、收盤平倉、每日風控等
        """
        results = {
            'initial_stop_triggers': 0,
            'eod_close_triggers': 0,
            'daily_risk_triggers': 0,
            'protective_stop_triggers': 0
        }

        try:
            # 獲取所有活躍部位 (使用資料庫查詢，因為這些檢查需要完整的部位信息)
            active_positions = self.db_manager.get_all_active_positions()
            if not active_positions:
                return results

            # 按組分組檢查
            groups = {}
            for position in active_positions:
                group_id = position.get('group_id', 0)
                if group_id not in groups:
                    groups[group_id] = []
                groups[group_id].append(position)

            # 檢查每組的風險條件
            for group_id, positions in groups.items():
                # 檢查收盤平倉 (最高優先級)
                if self._check_eod_close_conditions(positions, current_price, timestamp):
                    results['eod_close_triggers'] += len(positions)
                    continue

                # 檢查初始停損 (第二優先級)
                if self._check_initial_stop_loss_conditions(positions, current_price):
                    results['initial_stop_triggers'] += len(positions)
                    continue

                # 檢查保護性停損 (個別部位)
                for position in positions:
                    if self._check_protective_stop_loss_conditions(position, current_price):
                        results['protective_stop_triggers'] += 1

            return results

        except Exception as e:
            logger.error(f"額外風險條件檢查失敗: {e}")
            if self.console_enabled:
                print(f"[OPTIMIZED_RISK] ❌ 額外風險檢查失敗: {e}")
            return results

    def _check_eod_close_conditions(self, positions: List[Dict], current_price: float, timestamp: str) -> bool:
        """檢查收盤平倉條件"""
        try:
            # 預設關閉收盤平倉功能 (適合測試階段)
            enable_eod_close = getattr(self, 'enable_eod_close', False)
            if not enable_eod_close:
                return False

            # 解析當前時間
            hour, minute, second = map(int, timestamp.split(':'))
            eod_close_hour = getattr(self, 'eod_close_hour', 13)
            eod_close_minute = getattr(self, 'eod_close_minute', 30)

            # 檢查是否到達收盤時間
            if hour >= eod_close_hour and minute >= eod_close_minute:
                if self.console_enabled:
                    print(f"[OPTIMIZED_RISK] 🕐 觸發收盤平倉: {timestamp} (設定: {eod_close_hour:02d}:{eod_close_minute:02d})")

                # 執行收盤平倉
                for position in positions:
                    self._execute_exit_action(position, current_price, timestamp, '收盤平倉')

                return True

            return False

        except Exception as e:
            logger.error(f"檢查收盤平倉條件失敗: {e}")
            return False

    def _check_initial_stop_loss_conditions(self, positions: List[Dict], current_price: float) -> bool:
        """檢查初始停損條件"""
        try:
            if not positions:
                return False

            # 取得區間邊界停損價格
            first_position = positions[0]
            direction = first_position['direction']
            range_high = first_position.get('range_high')
            range_low = first_position.get('range_low')
            group_id = first_position.get('group_id')

            # 檢查區間邊界是否為None
            if range_high is None or range_low is None:
                return False

            # 檢查初始停損條件
            stop_triggered = False
            if direction == 'LONG':
                # 做多：價格跌破區間低點
                stop_triggered = current_price <= range_low
                boundary_price = range_low
                boundary_type = "區間低點"
            else:  # SHORT
                # 做空：價格漲破區間高點
                stop_triggered = current_price >= range_high
                boundary_price = range_high
                boundary_type = "區間高點"

            # 初始停損觸發事件
            if stop_triggered:
                if self.console_enabled:
                    print(f"[OPTIMIZED_RISK] 💥 初始停損觸發! 組{group_id}({direction})")
                    print(f"[OPTIMIZED_RISK]   觸發價格: {current_price:.0f}")
                    print(f"[OPTIMIZED_RISK]   停損邊界: {boundary_type} {boundary_price:.0f}")
                    print(f"[OPTIMIZED_RISK]   影響部位: {len(positions)}個")

                # 執行初始停損 - 全組出場
                for position in positions:
                    self._execute_exit_action(position, current_price,
                                            datetime.now().strftime('%H:%M:%S'), '初始停損')

            return stop_triggered

        except Exception as e:
            logger.error(f"檢查初始停損失敗: {e}")
            return False

    def _check_protective_stop_loss_conditions(self, position: Dict, current_price: float) -> bool:
        """檢查保護性停損條件"""
        try:
            # 只有非初始停損的部位才檢查保護性停損
            if not position.get('current_stop_loss') or not position.get('protection_activated'):
                return False

            direction = position['direction']
            stop_loss_price = position['current_stop_loss']
            position_id = position['id']

            # 檢查保護性停損條件
            stop_triggered = False
            if direction == 'LONG':
                # 做多：價格跌破保護性停損價格
                stop_triggered = current_price <= stop_loss_price
            else:  # SHORT
                # 做空：價格漲破保護性停損價格
                stop_triggered = current_price >= stop_loss_price

            if stop_triggered:
                if self.console_enabled:
                    print(f"[OPTIMIZED_RISK] 🛡️ 保護性停損觸發! 部位{position_id}({direction})")
                    print(f"[OPTIMIZED_RISK]   觸發價格: {current_price:.0f}")
                    print(f"[OPTIMIZED_RISK]   停損價格: {stop_loss_price:.0f}")

                # 執行保護性停損
                self._execute_exit_action(position, stop_loss_price,
                                        datetime.now().strftime('%H:%M:%S'), '保護性停損')

            return stop_triggered

        except Exception as e:
            logger.error(f"檢查保護性停損失敗: {e}")
            return False

    def _execute_exit_action(self, position: Dict, exit_price: float, exit_time: str, exit_reason: str):
        """執行出場動作"""
        try:
            position_id = position['id']

            # 使用全局平倉管理器檢查是否可以平倉
            if not self.global_exit_manager.mark_exit(str(position_id), "OptimizedRiskManager", exit_reason):
                if self.console_enabled:
                    print(f"[OPTIMIZED_RISK] ⚠️ 部位{position_id}已有進行中的平倉訂單")
                return False

            # 如果有停損執行器，使用它來執行平倉
            if self.stop_loss_executor:
                try:
                    result = self.stop_loss_executor.execute_stop_loss(
                        position_id=position_id,
                        stop_price=exit_price,
                        trigger_source="OptimizedRiskManager",
                        exit_reason=exit_reason
                    )

                    if result and result.success:
                        if self.console_enabled:
                            print(f"[OPTIMIZED_RISK] ✅ 部位{position_id}平倉執行成功: {exit_reason} @{exit_price:.0f}")

                        # 清理緩存
                        self.invalidate_position_cache(str(position_id))
                        return True
                    else:
                        if self.console_enabled:
                            error_msg = result.error_message if result else "未知錯誤"
                            print(f"[OPTIMIZED_RISK] ❌ 部位{position_id}平倉執行失敗: {error_msg}")
                        return False

                except Exception as e:
                    logger.error(f"停損執行器執行失敗: {e}")
                    if self.console_enabled:
                        print(f"[OPTIMIZED_RISK] ❌ 停損執行器錯誤: {e}")
                    return False
            else:
                # 如果沒有停損執行器，記錄日誌但不執行實際平倉
                if self.console_enabled:
                    print(f"[OPTIMIZED_RISK] ⚠️ 停損執行器未設置，無法執行部位{position_id}平倉")
                return False

        except Exception as e:
            logger.error(f"執行出場動作失敗: {e}")
            if self.console_enabled:
                print(f"[OPTIMIZED_RISK] ❌ 出場動作執行失敗: {e}")
            return False
    
    def _check_stop_loss_trigger(self, position_id: str, current_price: float) -> bool:
        """檢查初始停損觸發 - 純內存比較"""
        try:
            stop_loss = self.stop_loss_cache.get(position_id)
            if stop_loss is None:
                return False
            
            position_data = self.position_cache.get(position_id)
            if not position_data:
                return False
            
            direction = position_data.get('direction')
            
            # 🚨 停損觸發條件
            if direction == 'LONG' and current_price <= stop_loss:
                if self.console_enabled:
                    print(f"[OPTIMIZED_RISK] 🚨 LONG停損觸發: {position_id} {current_price} <= {stop_loss}")
                # 🔧 新增：執行停損平倉
                self._execute_stop_loss(position_id, current_price, stop_loss, direction)
                return True
            elif direction == 'SHORT' and current_price >= stop_loss:
                if self.console_enabled:
                    print(f"[OPTIMIZED_RISK] 🚨 SHORT停損觸發: {position_id} {current_price} >= {stop_loss}")
                # 🔧 新增：執行停損平倉
                self._execute_stop_loss(position_id, current_price, stop_loss, direction)
                return True

            return False
            
        except Exception as e:
            logger.error(f"停損檢查失敗: {e}")
            return False

    def _execute_stop_loss(self, position_id: str, current_price: float, stop_loss: float, direction: str):
        """執行停損平倉"""
        try:
            # 🔧 新增：觸發去重檢查
            if self._should_skip_trigger(position_id, current_price, 'stop_loss'):
                return False

            # 🔧 任務3：提前檢查鎖定狀態，避免不必要的執行器調用
            lock_reason = self.global_exit_manager.check_exit_in_progress(str(position_id))
            if lock_reason is not None:
                if self.console_enabled:
                    print(f"[OPTIMIZED_RISK] 🔒 停損被全局管理器阻止: 部位{position_id}")
                    print(f"[OPTIMIZED_RISK]   鎖定原因: {lock_reason}")
                return False

            if not self.stop_loss_executor:
                if self.console_enabled:
                    print(f"[OPTIMIZED_RISK] ⚠️ 停損執行器未設置，無法執行平倉: 部位{position_id}")
                return False

            # 🔧 新增：全局平倉管理器檢查
            trigger_source = f"optimized_risk_initial_stop_{direction}"
            if not self.global_exit_manager.mark_exit(str(position_id), trigger_source, "initial_stop_loss"):
                existing_info = self.global_exit_manager.get_exit_info(str(position_id))
                if self.console_enabled:
                    print(f"[OPTIMIZED_RISK] 🔒 停損被全局管理器阻止: 部位{position_id}")
                    print(f"[OPTIMIZED_RISK]   已有平倉: {existing_info.get('trigger_source', 'unknown')}")

                # 🔧 新增：檢查是否為過期鎖定，如果是則強制清除並重試
                current_time = time.time()
                lock_time = existing_info.get('timestamp', 0)
                if current_time - lock_time > 10.0:  # 如果鎖定超過10秒，視為過期
                    if self.console_enabled:
                        print(f"[OPTIMIZED_RISK] 🧹 檢測到過期鎖定({current_time - lock_time:.1f}秒)，強制清除並重試")
                    self.global_exit_manager.clear_exit(str(position_id))
                    # 重新嘗試標記
                    if not self.global_exit_manager.mark_exit(str(position_id), trigger_source, "initial_stop_loss"):
                        if self.console_enabled:
                            print(f"[OPTIMIZED_RISK] ❌ 清除後仍無法標記平倉: 部位{position_id}")
                        return False
                else:
                    return False

            # 創建停損觸發信息
            from stop_loss_monitor import StopLossTrigger

            # 🔧 任務2：獲取完整部位信息
            position_data = self.position_cache.get(position_id, {})
            group_id = position_data.get('group_id', 1)  # 預設為1

            # 🔧 任務2：創建包含完整數據的觸發器，避免執行器查詢數據庫
            trigger_info = StopLossTrigger(
                position_id=int(position_id),
                group_id=int(group_id),
                direction=direction,
                current_price=current_price,
                stop_loss_price=stop_loss,
                trigger_time=datetime.now().strftime("%H:%M:%S"),
                trigger_reason=f"初始停損觸發: {direction}部位",
                breach_amount=abs(current_price - stop_loss),
                # 🔧 任務2：從內存緩存中提供完整部位信息
                entry_price=position_data.get('entry_price'),
                peak_price=position_data.get('entry_price'),  # 初始停損時峰值=進場價
                quantity=position_data.get('quantity', 1),
                lot_id=position_data.get('lot_id', 1),
                range_high=position_data.get('range_high'),
                range_low=position_data.get('range_low')
            )

            if self.console_enabled:
                print(f"[OPTIMIZED_RISK] 🚀 執行停損平倉: 部位{position_id} @{current_price}")

            # 執行停損平倉
            execution_result = self.stop_loss_executor.execute_stop_loss(trigger_info)

            if execution_result.success:
                if self.console_enabled:
                    print(f"[OPTIMIZED_RISK] ✅ 停損平倉成功: 部位{position_id}, 訂單{execution_result.order_id}")
                return True
            else:
                if self.console_enabled:
                    print(f"[OPTIMIZED_RISK] ❌ 停損平倉失敗: 部位{position_id}, 錯誤: {execution_result.error_message}")
                # 🔧 任務1修復：移除鎖釋放邏輯，由 StopLossExecutor 負責
                return False

        except Exception as e:
            logger.error(f"執行停損平倉失敗: {e}")
            if self.console_enabled:
                print(f"[OPTIMIZED_RISK] ❌ 執行停損平倉異常: 部位{position_id}, 錯誤: {e}")
            # 🔧 任務1修復：移除鎖釋放邏輯，由 StopLossExecutor 負責
            return False

    def _check_activation_trigger(self, position_id: str, current_price: float) -> bool:
        """檢查移動停利啟動 - 純內存比較"""
        try:
            activation_price = self.activation_cache.get(position_id)
            trailing_data = self.trailing_cache.get(position_id)
            
            if not activation_price or not trailing_data or trailing_data.get('activated'):
                return False
            
            direction = trailing_data.get('direction')
            
            # 🎯 啟動條件檢查
            if direction == 'LONG' and current_price >= activation_price:
                trailing_data['activated'] = True
                trailing_data['peak_price'] = current_price
                if self.console_enabled:
                    print(f"[OPTIMIZED_RISK] 🎯 LONG移動停利啟動: {position_id} {current_price} >= {activation_price}")
                return True
            elif direction == 'SHORT' and current_price <= activation_price:
                trailing_data['activated'] = True
                trailing_data['peak_price'] = current_price
                if self.console_enabled:
                    print(f"[OPTIMIZED_RISK] 🎯 SHORT移動停利啟動: {position_id} {current_price} <= {activation_price}")
                return True
            
            return False
            
        except Exception as e:
            logger.error(f"啟動檢查失敗: {e}")
            return False
    
    def _check_trailing_trigger(self, position_id: str, current_price: float,
                              peak_price: float, entry_price: float, direction: str) -> bool:
        """
        檢查移動停利回撤觸發條件

        Args:
            position_id: 部位ID
            current_price: 當前價格
            peak_price: 峰值價格
            entry_price: 進場價格
            direction: 交易方向 (LONG/SHORT)

        Returns:
            bool: 是否觸發移動停利
        """
        try:
            # 🔧 使用固定的20%回撤比例（與回測程式一致）
            pullback_percent = 0.20

            if direction == 'LONG':
                # 多單：計算從峰值的回撤幅度
                total_gain = peak_price - entry_price
                pullback_amount = total_gain * pullback_percent
                trailing_stop_price = peak_price - pullback_amount

                # 觸發條件：當前價格 <= 停利價格
                if current_price <= trailing_stop_price:
                    if self.console_enabled:
                        print(f"[OPTIMIZED_RISK] 💥 LONG移動停利觸發: {position_id}")
                        print(f"[OPTIMIZED_RISK]   峰值:{peak_price:.0f} 進場:{entry_price:.0f} 當前:{current_price:.0f}")
                        print(f"[OPTIMIZED_RISK]   停利價:{trailing_stop_price:.0f} 回撤:{pullback_amount:.1f}點")
                    return True

            elif direction == 'SHORT':
                # 空單：計算從峰值的回撤幅度
                total_gain = entry_price - peak_price
                pullback_amount = total_gain * pullback_percent
                trailing_stop_price = peak_price + pullback_amount

                # 觸發條件：當前價格 >= 停利價格
                if current_price >= trailing_stop_price:
                    if self.console_enabled:
                        print(f"[OPTIMIZED_RISK] 💥 SHORT移動停利觸發: {position_id}")
                        print(f"[OPTIMIZED_RISK]   峰值:{peak_price:.0f} 進場:{entry_price:.0f} 當前:{current_price:.0f}")
                        print(f"[OPTIMIZED_RISK]   停利價:{trailing_stop_price:.0f} 回撤:{pullback_amount:.1f}點")
                    return True

            return False

        except Exception as e:
            logger.error(f"移動停利觸發檢查失敗: {e}")
            if self.console_enabled:
                print(f"[OPTIMIZED_RISK] ❌ 移動停利觸發檢查異常: {position_id}, 錯誤: {e}")
            return False

    def _execute_trailing_stop(self, position_id: str, current_price: float, direction: str):
        """
        執行移動停利平倉

        Args:
            position_id: 部位ID
            current_price: 當前觸發價格
            direction: 交易方向 (LONG/SHORT)
        """
        try:
            # 🔧 新增：觸發去重檢查
            if self._should_skip_trigger(position_id, current_price, 'trailing_stop'):
                return False

            # 🔧 任務3：提前檢查鎖定狀態，避免不必要的執行器調用
            lock_reason = self.global_exit_manager.check_exit_in_progress(str(position_id))
            if lock_reason is not None:
                if self.console_enabled:
                    print(f"[OPTIMIZED_RISK] 🔒 移動停利被全局管理器阻止: 部位{position_id}")
                    print(f"[OPTIMIZED_RISK]   鎖定原因: {lock_reason}")
                return False

            if not self.stop_loss_executor:
                if self.console_enabled:
                    print(f"[OPTIMIZED_RISK] ⚠️ 停損執行器未設置，無法執行移動停利平倉: 部位{position_id}")
                return False

            # 創建移動停利觸發信息
            from stop_loss_monitor import StopLossTrigger

            # 🔧 任務2：獲取完整部位信息
            position_data = self.position_cache.get(position_id, {})
            group_id = position_data.get('group_id', 1)  # 預設為1
            trailing_data = self.trailing_cache.get(position_id, {})

            # 🔧 任務2：創建包含完整數據的移動停利觸發器
            trigger_info = StopLossTrigger(
                position_id=int(position_id),
                group_id=int(group_id),
                direction=direction,
                current_price=current_price,
                stop_loss_price=current_price,  # 使用當前價格作為平倉價
                trigger_time=datetime.now().strftime("%H:%M:%S"),
                trigger_reason=f"移動停利: {direction}部位20%回撤觸發",
                breach_amount=0.0,  # 移動停利不需要突破金額
                # 🔧 任務2：從內存緩存中提供完整部位信息
                entry_price=position_data.get('entry_price'),
                peak_price=trailing_data.get('peak_price'),
                quantity=position_data.get('quantity', 1),
                lot_id=position_data.get('lot_id', 1),
                range_high=position_data.get('range_high'),
                range_low=position_data.get('range_low')
            )

            if self.console_enabled:
                print(f"[OPTIMIZED_RISK] 🚀 執行移動停利平倉: 部位{position_id} @{current_price}")

            # 執行移動停利平倉
            execution_result = self.stop_loss_executor.execute_stop_loss(trigger_info)

            if execution_result.success:
                if self.console_enabled:
                    print(f"[OPTIMIZED_RISK] ✅ 移動停利平倉成功: 部位{position_id}, 訂單{execution_result.order_id}")
                return True
            else:
                if self.console_enabled:
                    print(f"[OPTIMIZED_RISK] ❌ 移動停利平倉失敗: 部位{position_id}, 錯誤: {execution_result.error_message}")
                # 🔧 任務1修復：移除鎖釋放邏輯，由 StopLossExecutor 負責
                return False

        except Exception as e:
            logger.error(f"執行移動停利平倉失敗: {e}")
            if self.console_enabled:
                print(f"[OPTIMIZED_RISK] ❌ 執行移動停利平倉異常: 部位{position_id}, 錯誤: {e}")
            # 🔧 任務1修復：移除鎖釋放邏輯，由 StopLossExecutor 負責
            return False

    def _update_trailing_stop(self, position_id: str, current_price: float) -> bool:
        """更新移動停利 - 純內存比較"""
        try:
            trailing_data = self.trailing_cache.get(position_id)
            if not trailing_data or not trailing_data.get('activated'):
                return False

            direction = trailing_data.get('direction')
            current_peak = trailing_data.get('peak_price')

            # 📈 更新峰值價格
            peak_updated = False
            if direction == 'LONG' and current_price > current_peak:
                trailing_data['peak_price'] = current_price
                peak_updated = True
            elif direction == 'SHORT' and current_price < current_peak:
                trailing_data['peak_price'] = current_price
                peak_updated = True

            # 🔧 新增：檢查回撤觸發
            if trailing_data.get('activated'):
                position_data = self.position_cache.get(position_id, {})
                entry_price = position_data.get('entry_price')
                peak_price = trailing_data.get('peak_price')

                if entry_price and peak_price:
                    # 檢查是否觸發移動停利
                    if self._check_trailing_trigger(position_id, current_price, peak_price, entry_price, direction):
                        # 執行移動停利平倉
                        self._execute_trailing_stop(position_id, current_price, direction)
                        return True

            return peak_updated

        except Exception as e:
            logger.error(f"移動停利更新失敗: {e}")
            return False

    def _push_memory_to_database(self):
        """
        將內存中需要同步的數據推送到資料庫 - 任務2新增
        這是同步的正確方向：從內存到資料庫
        """
        try:
            if not hasattr(self, 'async_updater') or not self.async_updater:
                return  # 沒有異步更新器，跳過

            with self.cache_lock:
                sync_count = 0
                for position_id, position_data in self.position_cache.items():
                    # 檢查是否需要同步
                    if position_data.get('_needs_sync'):
                        try:
                            # 使用異步更新器將內存數據推送到資料庫
                            if position_data.get('entry_price'):
                                self.async_updater.schedule_position_fill_update(
                                    position_id=int(position_id),
                                    fill_price=position_data['entry_price'],  # 修復：使用正確的參數名
                                    fill_time=position_data.get('entry_time', datetime.now().strftime('%H:%M:%S')),  # 修復：使用正確的參數名
                                    order_status='FILLED'  # 修復：使用正確的參數
                                )

                                # 清除同步標記
                                position_data['_needs_sync'] = False
                                sync_count += 1

                                if self.console_enabled:
                                    print(f"[OPTIMIZED_RISK] 🚀 推送部位 {position_id} 到資料庫: entry_price={position_data['entry_price']}")

                        except Exception as push_error:
                            logger.error(f"推送部位 {position_id} 到資料庫失敗: {push_error}")
                            if self.console_enabled:
                                print(f"[OPTIMIZED_RISK] ❌ 推送失敗: 部位{position_id}, 錯誤: {push_error}")

                if sync_count > 0 and self.console_enabled:
                    print(f"[OPTIMIZED_RISK] 🚀 內存到資料庫同步完成: {sync_count} 個部位")

        except Exception as e:
            logger.error(f"內存到資料庫推送失敗: {e}")
            if self.console_enabled:
                print(f"[OPTIMIZED_RISK] ❌ 內存推送異常: {e}")

    def _sync_with_database(self):
        """與資料庫同步 - 備份機制（任務2修復：單向同步，從內存到資料庫）"""
        try:
            # 🚀 第一步：將內存中需要同步的數據推送到資料庫
            self._push_memory_to_database()

            # 🔄 第二步：重新載入活躍部位（僅用於驗證和補充）
            with self.db_manager.get_connection() as conn:
                # 🔧 修復：確保 row_factory 設置正確
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                cursor.execute('''
                    SELECT pr.*, sg.range_high, sg.range_low
                    FROM position_records pr
                    JOIN strategy_groups sg ON pr.group_id = sg.id
                    WHERE pr.status = 'ACTIVE'
                    ORDER BY pr.group_id, pr.lot_id
                ''')

                rows = cursor.fetchall()

                # 🔄 更新緩存
                current_positions = {}
                for row in rows:
                    # 🔧 修復：安全地轉換 sqlite3.Row 為 dict
                    try:
                        position_data = dict(row)
                    except Exception as row_error:
                        # 如果 dict(row) 失敗，手動轉換
                        columns = [description[0] for description in cursor.description]
                        position_data = dict(zip(columns, row))
                        if self.console_enabled:
                            print(f"[OPTIMIZED_RISK] 🔧 手動轉換 Row 對象: {row_error}")

                    # 🔧 修復：使用正確的鍵名
                    position_id = position_data.get('id')  # 資料庫查詢返回的是 id 欄位
                    if position_id:
                        current_positions[str(position_id)] = position_data  # 確保鍵為字串

                        # 如果是新部位，預計算點位
                        if str(position_id) not in self.position_cache:
                            self._precalculate_levels(position_data)
                
                # 🗑️ 移除已平倉的部位
                closed_positions = set(self.position_cache.keys()) - set(current_positions.keys())
                for position_id in closed_positions:
                    self.on_position_closed(position_id)
                
                # 📊 智能更新緩存 - 🔧 任務2修復：強化內存保護機制
                for position_id, db_data in current_positions.items():
                    # 🔧 修復：確保 position_id 類型一致
                    position_key = str(position_id)
                    cached_data = self.position_cache.get(position_key)

                    # 🛡️ 強化保護邏輯：優先保護內存中的有效數據
                    if cached_data:
                        # 創建合併數據，優先使用內存中的有效值
                        merged_data = db_data.copy()

                        # 保護 entry_price：如果內存有效而資料庫無效，保留內存值
                        if cached_data.get('entry_price') and not db_data.get('entry_price'):
                            merged_data['entry_price'] = cached_data['entry_price']
                            if self.console_enabled:
                                print(f"[OPTIMIZED_RISK] 🛡️ 保護部位 {position_id} 內存進場價 {cached_data['entry_price']}")

                        # 保護其他關鍵字段（如果需要）
                        for key in ['status', 'direction', 'group_id']:
                            if cached_data.get(key) and not merged_data.get(key):
                                merged_data[key] = cached_data[key]
                                if self.console_enabled:
                                    print(f"[OPTIMIZED_RISK] 🛡️ 保護部位 {position_id} 內存 {key}: {cached_data[key]}")

                        self.position_cache[position_key] = merged_data
                    else:
                        # 新部位：直接使用資料庫數據
                        self.position_cache[position_key] = db_data
                
                if self.console_enabled and len(rows) > 0:
                    print(f"[OPTIMIZED_RISK] 🔄 備份同步完成: {len(rows)} 個活躍部位")
                    
        except Exception as e:
            logger.error(f"資料庫同步失敗: {e}")
            if self.console_enabled:
                print(f"[OPTIMIZED_RISK] ❌ 資料庫同步失敗: {e}")
    
    def _fallback_update(self, current_price: float, timestamp: str) -> Dict:
        """回退到原始方法"""
        try:
            self.stats['fallback_calls'] += 1
            
            # 🛡️ 使用原始管理器
            results = {
                'stop_loss_triggers': 0,
                'trailing_activations': 0,
                'peak_updates': 0,
                'drawdown_triggers': 0
            }
            
            # 如果有原始管理器，使用它們
            if 'exit_mechanism_manager' in self.original_managers:
                original_results = self.original_managers['exit_mechanism_manager'].process_price_update(
                    current_price, timestamp
                )
                if original_results:
                    results.update(original_results)
            
            return results
            
        except Exception as e:
            logger.error(f"回退方法也失敗: {e}")
            return {'error': str(e)}
    
    def get_stats(self) -> Dict:
        """獲取統計信息"""
        with self.cache_lock:
            return {
                **self.stats,
                'cached_positions': len(self.position_cache),
                'fallback_mode': self.fallback_mode,
                'last_backup_sync': self.last_backup_update
            }
    
    def enable_fallback_mode(self):
        """啟用回退模式"""
        self.fallback_mode = True
        if self.console_enabled:
            print("[OPTIMIZED_RISK] ⚠️ 已啟用回退模式")
    
    def disable_fallback_mode(self):
        """禁用回退模式"""
        self.fallback_mode = False
        if self.console_enabled:
            print("[OPTIMIZED_RISK] ✅ 已禁用回退模式")


def create_optimized_risk_manager(db_manager, original_managers: Dict = None, console_enabled: bool = True) -> OptimizedRiskManager:
    """
    創建優化風險管理器的工廠函數
    
    Args:
        db_manager: 資料庫管理器
        original_managers: 原始管理器字典
        console_enabled: 是否啟用Console日誌
        
    Returns:
        OptimizedRiskManager: 優化風險管理器實例
    """
    return OptimizedRiskManager(db_manager, original_managers, console_enabled)


if __name__ == "__main__":
    print("優化風險管理器模組")
    print("請在主程式中調用 create_optimized_risk_manager() 函數")
