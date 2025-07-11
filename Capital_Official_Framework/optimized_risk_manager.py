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
        
        # 🚀 初始化緩存
        self._initial_cache_load()
        
        if self.console_enabled:
            print("[OPTIMIZED_RISK] ✅ 優化風險管理器初始化完成")

    def set_stop_loss_executor(self, stop_loss_executor):
        """設置停損執行器"""
        self.stop_loss_executor = stop_loss_executor
        if self.console_enabled:
            print("[OPTIMIZED_RISK] 🔗 停損執行器已設置")

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
                # 🎯 立即加入緩存
                self.position_cache[position_id] = position_dict

                # 🔢 預計算關鍵價格點位
                self._precalculate_levels(position_dict)

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
                for position_id, position_data in self.position_cache.items():
                    # 🛡️ 檢查初始停損
                    if self._check_stop_loss_trigger(position_id, current_price):
                        results['stop_loss_triggers'] += 1
                    
                    # 🎯 檢查移動停利啟動
                    elif self._check_activation_trigger(position_id, current_price):
                        results['trailing_activations'] += 1
                    
                    # 📈 更新已啟動的移動停利
                    elif self._update_trailing_stop(position_id, current_price):
                        results['peak_updates'] += 1
            
            return results
            
        except Exception as e:
            logger.error(f"緩存處理失敗: {e}")
            return results
    
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
                return False

            # 創建停損觸發信息
            from stop_loss_monitor import StopLossTrigger

            # 🔧 修復：獲取group_id信息
            position_data = self.position_cache.get(position_id, {})
            group_id = position_data.get('group_id', 1)  # 預設為1

            # 🔧 修復：使用正確的參數名稱
            trigger_info = StopLossTrigger(
                position_id=int(position_id),
                group_id=int(group_id),
                direction=direction,
                current_price=current_price,  # 🔧 修復：trigger_price -> current_price
                stop_loss_price=stop_loss,
                trigger_time=datetime.now().strftime("%H:%M:%S"),
                trigger_reason=f"初始停損觸發: {direction}部位",
                breach_amount=abs(current_price - stop_loss)
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
                return False

        except Exception as e:
            logger.error(f"執行停損平倉失敗: {e}")
            if self.console_enabled:
                print(f"[OPTIMIZED_RISK] ❌ 執行停損平倉異常: 部位{position_id}, 錯誤: {e}")
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
            
            return peak_updated
            
        except Exception as e:
            logger.error(f"移動停利更新失敗: {e}")
            return False
    
    def _sync_with_database(self):
        """與資料庫同步 - 備份機制"""
        try:
            # 🔄 重新載入活躍部位
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

                    position_id = position_data.get('id')
                    if position_id:
                        current_positions[position_id] = position_data

                        # 如果是新部位，預計算點位
                        if position_id not in self.position_cache:
                            self._precalculate_levels(position_data)
                
                # 🗑️ 移除已平倉的部位
                closed_positions = set(self.position_cache.keys()) - set(current_positions.keys())
                for position_id in closed_positions:
                    self.on_position_closed(position_id)
                
                # 📊 更新緩存
                self.position_cache.update(current_positions)
                
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
