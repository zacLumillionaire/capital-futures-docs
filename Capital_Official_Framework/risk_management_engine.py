#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
風險管理引擎
移植OrderTester.py的精密風險管理邏輯
"""

import json
import logging
import time
from datetime import datetime
from decimal import Decimal
from typing import List, Dict, Optional, Tuple

from multi_group_config import LotRule
from multi_group_database import MultiGroupDatabaseManager

# 設定日誌
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class RiskManagementEngine:
    """風險管理引擎 - 移植OrderTester.py的精密邏輯"""

    def __init__(self, db_manager: MultiGroupDatabaseManager):
        self.db_manager = db_manager
        self.logger = logging.getLogger(f"{__name__}.{self.__class__.__name__}")

        # 收盤平倉控制開關 (預設關閉，適合測試階段)
        self.enable_eod_close = False
        self.eod_close_hour = 13
        self.eod_close_minute = 30

        # 🔧 新增：統一出場管理器 (稍後設置)
        self.unified_exit_manager = None

        # 🔧 新增：停損執行器 (稍後設置)
        self.stop_loss_executor = None

        # 🔧 新增：移動停利啟動快取，避免重複觸發
        self._trailing_activated_cache = set()  # 存儲已啟動移動停利的部位ID

        # 🔧 新增：異步更新器支援（參考建倉機制）
        self.async_updater = None
        self.console_enabled = True

        # 🎯 新增：分級LOG控制系統（完全不影響現有功能）
        self.log_level = "NORMAL"  # NORMAL, DEBUG
        self._last_status_log_time = 0
        self._status_log_interval = 30  # 30秒輸出一次狀態摘要
        self._last_routine_log_time = 0
        self._routine_log_interval = 30  # 30秒輸出一次常規LOG

        # 🔍 DEBUG: 價格檢查追蹤（保留原有變數）
        self._price_check_count = 0
        self._last_price_log_time = 0
        self._last_position_log_time = 0
        self._last_group_log_time = 0
        self._last_filter_log_time = 0

        # 🚀 零風險異步更新支援（預設啟用，大幅改善性能）
        self.async_updater = None  # 將由外部設置
        self.enable_async_peak_update = True  # 🔧 修改：預設啟用，大幅改善性能

        # 🎯 峰值更新LOG頻率控制（20秒內最多顯示一次）
        self.last_peak_log_time = {}  # position_id -> last_log_time
        self.peak_log_interval = 20  # 20秒間隔

        self.logger.info("風險管理引擎初始化完成")

    def set_async_updater(self, async_updater):
        """🚀 設置異步更新器（零風險可選功能）"""
        self.async_updater = async_updater
        if self.console_enabled:
            print("[RISK_ENGINE] 🔗 異步更新器已連接（峰值更新仍預設使用同步模式）")

    def enable_async_peak_updates(self, enable=True):
        """🚀 啟用/關閉異步峰值更新（零風險控制）"""
        if not self.async_updater and enable:
            print("[RISK_ENGINE] ⚠️ 異步更新器未連接，無法啟用異步峰值更新")
            return False

        self.enable_async_peak_update = enable
        if self.console_enabled:
            status = "啟用" if enable else "關閉"
            print(f"[RISK_ENGINE] 🚀 異步峰值更新已{status}")
        return True

    def set_peak_log_interval(self, interval_seconds=20):
        """🎯 設定峰值更新LOG顯示間隔"""
        self.peak_log_interval = interval_seconds
        if self.console_enabled:
            print(f"[RISK_ENGINE] 🎯 峰值更新LOG間隔設為 {interval_seconds} 秒")

    def _get_latest_peak_price(self, position_id: int, db_peak: float) -> float:
        """🚀 獲取最新峰值價格（優先內存緩存，零風險備用）"""
        try:
            # 🚀 如果啟用異步更新，優先從內存緩存讀取
            if self.enable_async_peak_update and self.async_updater:
                cached_peak = self.async_updater.get_cached_peak(position_id)
                if cached_peak:
                    # 檢查緩存新鮮度（10秒內的更新）
                    if time.time() - cached_peak['updated_at'] < 10:
                        self._log_debug(f"[RISK_ENGINE] 🚀 使用內存峰值: 部位{position_id} 峰值{cached_peak['peak_price']}")
                        return cached_peak['peak_price']

            # 🛡️ 備用：使用資料庫峰值（確保零風險）
            self._log_debug(f"[RISK_ENGINE] 📊 使用資料庫峰值: 部位{position_id} 峰值{db_peak}")
            return db_peak

        except Exception as e:
            self.logger.error(f"獲取最新峰值失敗: {e}")
            # 🛡️ 錯誤時使用資料庫峰值
            return db_peak

    def _get_latest_trailing_state(self, position_id: int, db_trailing_state: bool) -> bool:
        """🚀 獲取最新移動停利狀態（優先內存緩存，零風險備用）"""
        try:
            # 🚀 如果啟用異步更新，優先從內存緩存讀取
            if self.enable_async_peak_update and self.async_updater:
                cached_state = self.async_updater.get_cached_trailing_state(position_id)
                if cached_state:
                    # 檢查緩存新鮮度（10秒內的更新）
                    if time.time() - cached_state['updated_at'] < 10:
                        self._log_debug(f"[RISK_ENGINE] 🚀 使用內存移動停利狀態: 部位{position_id} 狀態{cached_state['trailing_activated']}")
                        return cached_state['trailing_activated']

            # 🛡️ 備用：使用資料庫狀態（確保零風險）
            self._log_debug(f"[RISK_ENGINE] 📊 使用資料庫移動停利狀態: 部位{position_id} 狀態{db_trailing_state}")
            return db_trailing_state

        except Exception as e:
            self.logger.error(f"獲取最新移動停利狀態失敗: {e}")
            # 🛡️ 錯誤時使用資料庫狀態
            return db_trailing_state

    # 🎯 新增：分級LOG控制方法（完全不影響現有功能）
    def _log_routine(self, message):
        """常規LOG（低頻率輸出，30秒一次）"""
        if not self.console_enabled:
            return
        current_time = time.time()
        if current_time - self._last_routine_log_time > self._routine_log_interval:
            print(message)
            self._last_routine_log_time = current_time

    def _log_important(self, message):
        """重要事件LOG（立即輸出）"""
        if self.console_enabled:
            print(message)

    def _log_debug(self, message):
        """調試LOG（可選輸出）"""
        if self.console_enabled and self.log_level == "DEBUG":
            print(message)

    def _log_status_summary(self, current_price, valid_positions, groups):
        """狀態摘要LOG（30秒一次）"""
        if not self.console_enabled:
            return
        current_time = time.time()
        if current_time - self._last_status_log_time > self._status_log_interval:
            current_time_str = datetime.now().strftime("%H:%M:%S")
            active_trailing = sum(1 for pos in valid_positions if pos.get('trailing_activated'))
            active_protection = sum(1 for pos in valid_positions if pos.get('protection_activated'))

            print(f"[RISK_ENGINE] ✅ [{current_time_str}] 監控中 | {len(valid_positions)}部位 | "
                  f"價格:{current_price:.0f} | 檢查:{self._price_check_count}次 | "
                  f"移停:{active_trailing}/{len(valid_positions)} | 保護:{active_protection}/{len(valid_positions)}")
            self._last_status_log_time = current_time

    def enable_detailed_logging(self):
        """啟用詳細LOG模式（可隨時切換回原始行為）"""
        self.log_level = "DEBUG"
        self._log_important("[RISK_ENGINE] 🔧 已啟用詳細LOG模式")

    def enable_normal_logging(self):
        """啟用簡化LOG模式"""
        self.log_level = "NORMAL"
        self._log_important("[RISK_ENGINE] 🔧 已啟用簡化LOG模式")

    def set_unified_exit_manager(self, unified_exit_manager):
        """設置統一出場管理器"""
        self.unified_exit_manager = unified_exit_manager
        self.logger.info("統一出場管理器已設置")

    def set_stop_loss_executor(self, stop_loss_executor):
        """設置停損執行器"""
        self.stop_loss_executor = stop_loss_executor
        if self.console_enabled:
            print("[RISK_ENGINE] 🔗 停損執行器已設置")
        self.logger.info("停損執行器已設置")

    def set_async_updater(self, async_updater):
        """
        設定異步更新器 - 🔧 新增：參考建倉機制

        Args:
            async_updater: 異步更新器實例
        """
        self.async_updater = async_updater
        if self.console_enabled:
            print(f"[RISK_ENGINE] 🚀 異步更新器已設定")

    def set_eod_close_settings(self, enable: bool, hour: int = 13, minute: int = 30):
        """設定收盤平倉參數"""
        self.enable_eod_close = enable
        self.eod_close_hour = hour
        self.eod_close_minute = minute

        status = "啟用" if enable else "停用"
        self.logger.info(f"收盤平倉設定: {status} ({hour:02d}:{minute:02d})")

    def execute_exit_actions(self, exit_actions: List[Dict]) -> int:
        """
        執行出場動作 - 使用統一出場管理器

        Args:
            exit_actions: 出場動作列表

        Returns:
            int: 成功執行的出場數量
        """
        if not self.unified_exit_manager:
            self.logger.error("統一出場管理器未設置，無法執行出場")
            return 0

        success_count = 0

        for action in exit_actions:
            try:
                success = self.unified_exit_manager.trigger_exit(
                    position_id=action['position_id'],
                    exit_reason=action['exit_reason'],
                    exit_price=action.get('exit_price')  # 可選，讓統一出場管理器自動選擇
                )

                if success:
                    success_count += 1
                    self.logger.info(f"✅ 部位{action['position_id']}出場成功: {action['exit_reason']}")
                else:
                    self.logger.error(f"❌ 部位{action['position_id']}出場失敗: {action['exit_reason']}")

            except Exception as e:
                self.logger.error(f"執行出場動作失敗: {e}")

        return success_count

    def check_all_exit_conditions(self, current_price: float, current_time: str) -> List[Dict]:
        """檢查所有活躍部位的出場條件"""
        exit_actions = []

        try:
            # 🎯 修改：使用分級LOG系統（保留所有原有邏輯）
            if hasattr(self, 'console_enabled') and getattr(self, 'console_enabled', True):
                if not hasattr(self, '_last_price_log_time'):
                    self._last_price_log_time = 0
                    self._price_check_count = 0

                self._price_check_count += 1
                current_timestamp = time.time()

                # 🔧 原有的詳細LOG改為調試模式
                if (current_timestamp - self._last_price_log_time > 5.0 or
                    self._price_check_count % 100 == 0):
                    self._log_debug(f"[RISK_ENGINE] 🔍 價格檢查: {current_price:.0f} @{current_time} (第{self._price_check_count}次)")
                    self._last_price_log_time = current_timestamp

            active_positions = self.db_manager.get_all_active_positions()

            # 🔧 新增：多層狀態過濾（參考建倉機制）
            filtered_positions = self._filter_active_positions(active_positions)

            # 🔧 清理快取：移除已不存在的部位ID
            active_position_ids = {pos.get('id') for pos in filtered_positions if pos.get('id')}
            self._trailing_activated_cache &= active_position_ids  # 保留交集

            # 🔧 過濾掉無效部位（PENDING狀態或entry_price為None的部位）
            valid_positions = []
            invalid_count = 0
            for position in filtered_positions:
                if (position.get('entry_price') is not None and
                    position.get('order_status') == 'FILLED'):
                    valid_positions.append(position)
                else:
                    invalid_count += 1
                    self.logger.debug(f"跳過無效部位: ID={position.get('id')}, "
                                    f"entry_price={position.get('entry_price')}, "
                                    f"order_status={position.get('order_status')}")

            # 🎯 修改：使用分級LOG系統 - 詳細部位狀態改為調試模式
            if hasattr(self, 'console_enabled') and getattr(self, 'console_enabled', True):
                if len(valid_positions) > 0:
                    if not hasattr(self, '_last_position_log_time'):
                        self._last_position_log_time = 0

                    # 🔧 詳細部位狀態改為調試模式（DEBUG）
                    if time.time() - self._last_position_log_time > 10.0:
                        self._log_debug(f"[RISK_ENGINE] 📊 部位狀態: {len(valid_positions)}個有效部位 ({invalid_count}個無效)")
                        for pos in valid_positions:
                            direction = pos['direction']
                            entry_price = pos['entry_price']
                            peak_price = pos.get('peak_price', entry_price)
                            trailing_activated = pos.get('trailing_activated', False)
                            protection_activated = pos.get('protection_activated', False)
                            current_stop = pos.get('current_stop_loss', 'N/A')

                            # 🔧 修復：安全處理所有可能為 None 的值，避免格式化錯誤
                            if entry_price is None:
                                entry_price = 0.0
                            if peak_price is None:
                                peak_price = entry_price if entry_price is not None else 0.0
                            if current_stop is None:
                                current_stop = 'N/A'
                            elif isinstance(current_stop, (int, float)):
                                current_stop = f"{current_stop:.0f}"

                            # 安全計算損益
                            try:
                                pnl = (current_price - entry_price) if direction == 'LONG' else (entry_price - current_price)
                            except (TypeError, ValueError):
                                pnl = 0.0

                            status_flags = []
                            if trailing_activated:
                                status_flags.append("移動停利")
                            if protection_activated:
                                status_flags.append("保護停損")
                            status_str = f"[{','.join(status_flags)}]" if status_flags else "[初始停損]"

                            self._log_debug(f"[RISK_ENGINE]   部位{pos['id']}: {direction} @{entry_price:.0f} "
                                          f"峰值:{peak_price:.0f} 損益:{pnl:+.0f} 停損:{current_stop} {status_str}")
                        self._last_position_log_time = time.time()

            self.logger.debug(f"檢查 {len(valid_positions)}/{len(active_positions)} 個有效部位的出場條件")

            # 按組分組處理
            groups = {}
            for position in valid_positions:
                group_id = position['group_id']
                if group_id not in groups:
                    groups[group_id] = []
                groups[group_id].append(position)

            # 🎯 修改：組別狀態改為調試模式，並添加狀態摘要
            if len(groups) > 0:
                # 🔧 詳細組別狀態改為調試模式
                if hasattr(self, 'console_enabled') and getattr(self, 'console_enabled', True):
                    if not hasattr(self, '_last_group_log_time'):
                        self._last_group_log_time = 0

                    # 每15秒輸出一次詳細組別狀態（調試模式）
                    if time.time() - self._last_group_log_time > 15.0:
                        self._log_debug(f"[RISK_ENGINE] 🏢 組別狀態總覽: {len(groups)}個活躍組別")
                        for group_id, positions in groups.items():
                            # 計算組別統計
                            total_positions = len(positions)
                            long_count = sum(1 for p in positions if p['direction'] == 'LONG')
                            short_count = total_positions - long_count
                            trailing_active_count = sum(1 for p in positions if p.get('trailing_activated'))
                            protection_active_count = sum(1 for p in positions if p.get('protection_activated'))

                            self._log_debug(f"[RISK_ENGINE]   組{group_id}: {total_positions}個部位 (多:{long_count} 空:{short_count})")
                            self._log_debug(f"[RISK_ENGINE]     移動停利:{trailing_active_count}個 保護停損:{protection_active_count}個")

                            # 顯示區間資訊
                            if positions:
                                first_pos = positions[0]
                                range_high = first_pos.get('range_high')
                                range_low = first_pos.get('range_low')
                                if range_high and range_low:
                                    self._log_debug(f"[RISK_ENGINE]     區間: {range_low:.0f} - {range_high:.0f}")

                        self._last_group_log_time = time.time()

                # 🎯 新增：狀態摘要LOG（30秒一次）
                self._log_status_summary(current_price, valid_positions, groups)

            # 逐組檢查
            for group_id, positions in groups.items():
                group_exits = self._check_group_exit_conditions(positions, current_price, current_time)
                exit_actions.extend(group_exits)

            # 🎯 保持：出場動作是重要事件，立即顯示
            if len(exit_actions) > 0:
                self._log_important(f"[RISK_ENGINE] 🚨 觸發出場動作: {len(exit_actions)}個")
                for action in exit_actions:
                    self._log_important(f"[RISK_ENGINE]   部位{action['position_id']}: {action['exit_reason']} @{action['exit_price']:.0f}")

            return exit_actions

        except Exception as e:
            self.logger.error(f"檢查出場條件失敗: {e}")
            # 🎯 錯誤是重要事件，立即顯示
            self._log_important(f"[RISK_ENGINE] ❌ 檢查出場條件失敗: {e}")
            return []
    
    def _check_group_exit_conditions(self, positions: List[Dict],
                                   current_price: float, current_time: str) -> List[Dict]:
        """檢查單組的出場條件"""
        exit_actions = []

        try:
            if not positions:
                return exit_actions

            # 🕐 檢查收盤平倉 (13:30) - 最高優先級
            eod_close_exits = self._check_eod_close_conditions(positions, current_price, current_time)
            if eod_close_exits:
                exit_actions.extend(eod_close_exits)
                return exit_actions

            # 檢查初始停損 (第二優先級)
            initial_stop_exits = self._check_initial_stop_loss(positions, current_price)
            if initial_stop_exits:
                # 初始停損觸發，全組出場
                for position in positions:
                    pnl = self._calculate_pnl(position, current_price)
                    exit_actions.append({
                        'position_id': position['id'],
                        'exit_price': current_price,
                        'exit_time': current_time,
                        'exit_reason': '初始停損',
                        'pnl': pnl
                    })
                
                self.logger.info(f"組 {positions[0]['group_id']} 觸發初始停損，全組出場")
                return exit_actions
            
            # 檢查各口的個別出場條件
            for position in positions:
                # 檢查保護性停損
                if self._check_protective_stop_loss(position, current_price):
                    pnl = self._calculate_pnl(position, current_price)
                    exit_actions.append({
                        'position_id': position['id'],
                        'exit_price': position['current_stop_loss'],
                        'exit_time': current_time,
                        'exit_reason': '保護性停損',
                        'pnl': pnl
                    })
                    continue
                
                # 檢查移動停利條件
                trailing_exit = self._check_trailing_stop_conditions(position, current_price, current_time)
                if trailing_exit:
                    exit_actions.append(trailing_exit)
                    continue
                
                # 更新峰值價格和風險管理狀態
                self._update_position_risk_state(position, current_price, current_time)
            
            return exit_actions

        except Exception as e:
            self.logger.error(f"檢查組出場條件失敗: {e}")
            return []

    def _check_eod_close_conditions(self, positions: List[Dict],
                                  current_price: float, current_time: str) -> List[Dict]:
        """檢查收盤平倉條件"""
        exit_actions = []

        try:
            # 如果收盤平倉功能未啟用，直接返回
            if not self.enable_eod_close:
                return exit_actions

            # 解析當前時間
            hour, minute, second = map(int, current_time.split(':'))

            # 檢查是否到達收盤時間
            if hour >= self.eod_close_hour and minute >= self.eod_close_minute:
                self.logger.info(f"觸發收盤平倉: {current_time} (設定: {self.eod_close_hour:02d}:{self.eod_close_minute:02d})")

                # 對所有部位執行收盤平倉
                for position in positions:
                    pnl = self._calculate_pnl(position, current_price)
                    exit_actions.append({
                        'position_id': position['id'],
                        'exit_price': current_price,
                        'exit_time': current_time,
                        'exit_reason': '收盤平倉',
                        'pnl': pnl,
                        'group_id': position['group_id']
                    })

                if exit_actions:
                    self.logger.info(f"收盤平倉: {len(exit_actions)} 個部位")

            return exit_actions

        except Exception as e:
            self.logger.error(f"檢查收盤平倉條件失敗: {e}")
            return []

    def _check_initial_stop_loss(self, positions: List[Dict], current_price: float) -> bool:
        """檢查初始停損條件"""
        try:
            if not positions:
                return False

            # 取得區間邊界停損價格
            first_position = positions[0]
            direction = first_position['direction']
            range_high = first_position['range_high']
            range_low = first_position['range_low']
            group_id = first_position.get('group_id')

            # 🔧 修復：檢查區間邊界是否為None
            if range_high is None or range_low is None:
                self._log_debug(f"[RISK_ENGINE] ⚠️ 組{group_id}區間邊界未設置: high={range_high}, low={range_low}")
                return False

            # 🔍 DEBUG: 初始停損檢查追蹤 (控制頻率避免過多輸出)
            if hasattr(self, 'console_enabled') and getattr(self, 'console_enabled', True):
                if not hasattr(self, f'_last_initial_stop_log_{group_id}'):
                    setattr(self, f'_last_initial_stop_log_{group_id}', 0)

                current_time_stamp = time.time()
                # 每10秒輸出一次初始停損檢查狀態
                if current_time_stamp - getattr(self, f'_last_initial_stop_log_{group_id}') > 10.0:
                    if direction == 'LONG':
                        distance_to_stop = current_price - range_low
                        stop_condition = f"當前:{current_price:.0f} <= 區間低:{range_low:.0f}"
                    else:  # SHORT
                        distance_to_stop = range_high - current_price
                        stop_condition = f"當前:{current_price:.0f} >= 區間高:{range_high:.0f}"

                    # 🎯 修改：初始停損檢查改為調試模式
                    self._log_debug(f"[RISK_ENGINE] 🚨 初始停損檢查 - 組{group_id}({direction}):")
                    self._log_debug(f"[RISK_ENGINE]   區間: {range_low:.0f} - {range_high:.0f}")
                    self._log_debug(f"[RISK_ENGINE]   條件: {stop_condition}")
                    self._log_debug(f"[RISK_ENGINE]   距離: {distance_to_stop:+.0f}點")
                    setattr(self, f'_last_initial_stop_log_{group_id}', current_time_stamp)

            # 檢查初始停損條件
            stop_triggered = False
            if direction == 'LONG':
                # 做多：價格跌破區間低點
                stop_triggered = current_price <= range_low
            else:  # SHORT
                # 做空：價格漲破區間高點
                stop_triggered = current_price >= range_high

            # 🔍 DEBUG: 初始停損觸發事件 (重要事件，立即輸出)
            if stop_triggered and hasattr(self, 'console_enabled') and getattr(self, 'console_enabled', True):
                # 🔧 修復：分離條件邏輯避免f-string語法錯誤
                if direction == 'LONG':
                    boundary_price = range_low
                    boundary_type = "區間低點"
                else:
                    boundary_price = range_high
                    boundary_type = "區間高點"

                print(f"[RISK_ENGINE] 💥 初始停損觸發! 組{group_id}({direction})")
                print(f"[RISK_ENGINE]   觸發價格: {current_price:.0f}")
                print(f"[RISK_ENGINE]   停損邊界: {boundary_type} {boundary_price:.0f}")
                print(f"[RISK_ENGINE]   影響部位: {len(positions)}個")

            return stop_triggered

        except Exception as e:
            self.logger.error(f"檢查初始停損失敗: {e}")
            # 🎯 錯誤是重要事件，立即顯示
            self._log_important(f"[RISK_ENGINE] ❌ 初始停損檢查失敗: {e}")
            return False
    
    def _check_protective_stop_loss(self, position: Dict, current_price: float) -> bool:
        """檢查保護性停損條件"""
        try:
            # 只有非初始停損的部位才檢查保護性停損
            if not position.get('current_stop_loss') or not position.get('protection_activated'):
                return False

            direction = position['direction']
            stop_loss_price = position['current_stop_loss']
            position_id = position['id']

            # 🔍 DEBUG: 保護性停損檢查追蹤 (控制頻率)
            if hasattr(self, 'console_enabled') and getattr(self, 'console_enabled', True):
                if not hasattr(self, f'_last_protection_log_{position_id}'):
                    setattr(self, f'_last_protection_log_{position_id}', 0)

                current_time_stamp = time.time()
                # 每8秒輸出一次保護性停損狀態
                if current_time_stamp - getattr(self, f'_last_protection_log_{position_id}') > 8.0:
                    distance = abs(current_price - stop_loss_price)
                    condition = f"當前:{current_price:.0f} {'<=' if direction == 'LONG' else '>='} 停損:{stop_loss_price:.0f}"

                    # 🎯 修改：保護性停損檢查改為調試模式
                    self._log_debug(f"[RISK_ENGINE] 🛡️ 保護性停損檢查 - 部位{position_id}({direction}):")
                    self._log_debug(f"[RISK_ENGINE]   條件: {condition}")
                    self._log_debug(f"[RISK_ENGINE]   距離: {distance:.0f}點")
                    setattr(self, f'_last_protection_log_{position_id}', current_time_stamp)

            # 檢查觸發條件
            triggered = False
            if direction == 'LONG':
                triggered = current_price <= stop_loss_price
            else:  # SHORT
                triggered = current_price >= stop_loss_price

            # 🔍 DEBUG: 保護性停損觸發事件 (重要事件，立即輸出)
            if triggered and hasattr(self, 'console_enabled') and getattr(self, 'console_enabled', True):
                print(f"[RISK_ENGINE] 💥 保護性停損觸發! 部位{position_id}({direction})")
                print(f"[RISK_ENGINE]   觸發價格: {current_price:.0f}")
                print(f"[RISK_ENGINE]   停損價格: {stop_loss_price:.0f}")

            return triggered

        except Exception as e:
            self.logger.error(f"檢查保護性停損失敗: {e}")
            # 🎯 錯誤是重要事件，立即顯示
            self._log_important(f"[RISK_ENGINE] ❌ 保護性停損檢查失敗: {e}")
            return False
    
    def _check_trailing_stop_conditions(self, position: Dict, 
                                       current_price: float, current_time: str) -> Optional[Dict]:
        """檢查移動停利條件"""
        try:
            # 解析規則配置
            rule_config = json.loads(position['rule_config'])
            rule = LotRule.from_json(position['rule_config'])
            
            if not rule.use_trailing_stop or not rule.trailing_activation or not rule.trailing_pullback:
                return None
            
            direction = position['direction']
            entry_price = position['entry_price']
            db_peak_price = position['peak_price'] or entry_price
            # 🚀 使用最新峰值（優先內存緩存，零風險備用）
            peak_price = self._get_latest_peak_price(position['id'], db_peak_price)

            # 🚀 使用最新移動停利狀態（優先內存緩存）
            db_trailing_activated = position['trailing_activated']
            trailing_activated = self._get_latest_trailing_state(position['id'], db_trailing_activated)
            
            # 🔍 DEBUG: 移動停利檢查詳細追蹤
            if hasattr(self, 'console_enabled') and getattr(self, 'console_enabled', True):
                position_id = position['id']
                lot_id = rule_config.get('lot_id', 'N/A')
                activation_points = float(rule.trailing_activation)

                # 計算距離啟動條件的差距
                if direction == 'LONG':
                    activation_target = entry_price + activation_points
                    distance_to_activation = current_price - activation_target
                else:  # SHORT
                    activation_target = entry_price - activation_points
                    distance_to_activation = activation_target - current_price

                # 控制輸出頻率：未啟動時每5秒輸出一次，已啟動時每次都輸出
                if not hasattr(self, f'_last_trailing_log_{position_id}'):
                    setattr(self, f'_last_trailing_log_{position_id}', 0)

                current_time_stamp = time.time()
                should_log = (not trailing_activated and
                             current_time_stamp - getattr(self, f'_last_trailing_log_{position_id}') > 5.0) or trailing_activated

                if should_log:
                    if not trailing_activated:
                        # 🎯 修改：移動停利檢查改為調試模式
                        self._log_debug(f"[RISK_ENGINE] 🎯 移動停利檢查 - 部位{position_id}(第{lot_id}口):")
                        self._log_debug(f"[RISK_ENGINE]   方向:{direction} 進場:{entry_price:.0f} 當前:{current_price:.0f}")
                        self._log_debug(f"[RISK_ENGINE]   啟動條件:{activation_target:.0f} 距離:{distance_to_activation:+.0f}點")
                        self._log_debug(f"[RISK_ENGINE]   狀態:⏳等待啟動 (需要{activation_points:.0f}點獲利)")
                        setattr(self, f'_last_trailing_log_{position_id}', current_time_stamp)

            # 檢查移動停利啟動條件
            position_id = position['id']
            if not trailing_activated and position_id not in self._trailing_activated_cache:
                activation_triggered = False

                if direction == 'LONG':
                    activation_triggered = current_price >= entry_price + float(rule.trailing_activation)
                else:  # SHORT
                    activation_triggered = current_price <= entry_price - float(rule.trailing_activation)

                if activation_triggered:
                    # 🔧 立即加入快取，避免重複觸發
                    self._trailing_activated_cache.add(position_id)

                    # 🎯 保持：移動停利啟動是重要事件，立即顯示
                    self._log_important(f"[RISK_ENGINE] 🚀 移動停利啟動! 部位{position_id}(第{rule_config['lot_id']}口) @{current_price:.0f} (獲利{float(rule.trailing_activation):.0f}點)")

                    # 🚀 啟動移動停利（異步化以避免延遲）
                    if self.enable_async_peak_update and self.async_updater:
                        # 🚀 異步更新移動停利啟動狀態
                        self._log_debug(f"[RISK_ENGINE] 🚀 異步更新移動停利啟動: 部位{position_id}")
                        self.async_updater.schedule_trailing_activation_update(
                            position_id=position_id,
                            trailing_activated=True,
                            peak_price=current_price,
                            update_time=current_time,
                            update_category="移動停利啟動",
                            update_message="移動停利啟動"
                        )
                    else:
                        # 🛡️ 同步更新（備用模式）
                        self._log_debug(f"[RISK_ENGINE] 💾 同步更新移動停利啟動: 部位{position_id}")
                        self.db_manager.update_risk_management_state(
                            position_id=position_id,
                            trailing_activated=True,
                            update_time=current_time,
                            update_category="移動停利啟動",
                            update_message="移動停利啟動"
                        )

                    # 🔧 修復：只記錄一次移動停利啟動LOG
                    self.logger.info(f"部位 {position_id} 第{rule_config['lot_id']}口移動停利啟動")
                    return None
            
            # 🚨 診斷LOG：移動停利狀態檢查
            position_id = position['id']
            self._log_debug(f"[RISK_ENGINE] 🔍 移動停利狀態檢查 - 部位{position_id}:")
            self._log_debug(f"[RISK_ENGINE]   trailing_activated: {trailing_activated}")
            self._log_debug(f"[RISK_ENGINE]   peak_price: {peak_price:.0f} (DB: {db_peak_price:.0f})")
            self._log_debug(f"[RISK_ENGINE]   current_price: {current_price:.0f}")

            # 檢查移動停利出場條件
            if trailing_activated:
                pullback_ratio = float(rule.trailing_pullback)

                # 🔍 DEBUG: 移動停利觸發檢查 (已啟動時的詳細追蹤)
                if hasattr(self, 'console_enabled') and getattr(self, 'console_enabled', True):
                    position_id = position['id']
                    lot_id = rule_config.get('lot_id', 'N/A')

                    # 計算停利價格和距離
                    if direction == 'LONG':
                        stop_price = peak_price - (peak_price - entry_price) * pullback_ratio
                        distance_to_stop = current_price - stop_price
                        profit_range = peak_price - entry_price
                        current_profit = current_price - entry_price
                    else:  # SHORT
                        stop_price = peak_price + (entry_price - peak_price) * pullback_ratio
                        distance_to_stop = stop_price - current_price
                        profit_range = entry_price - peak_price
                        current_profit = entry_price - current_price

                    # 🚨 診斷模式：移動停利詳細追蹤（臨時啟用以診斷問題）
                    if not hasattr(self, f'_last_trailing_active_log_{position_id}'):
                        setattr(self, f'_last_trailing_active_log_{position_id}', 0)

                    current_time_stamp = time.time()
                    if current_time_stamp - getattr(self, f'_last_trailing_active_log_{position_id}') > 3.0:
                        # 🚨 臨時改為重要LOG以診斷問題
                        self._log_important(f"[RISK_ENGINE] 📈 移動停利追蹤 - 部位{position_id}(第{lot_id}口):")
                        self._log_important(f"[RISK_ENGINE]   當前價格:{current_price:.0f} 峰值:{peak_price:.0f} 停利點:{stop_price:.0f}")
                        self._log_important(f"[RISK_ENGINE]   獲利範圍:{profit_range:.0f}點 當前獲利:{current_profit:.0f}點")
                        self._log_important(f"[RISK_ENGINE]   距離觸發:{distance_to_stop:+.0f}點 回撤比例:{pullback_ratio*100:.0f}%")
                        self._log_important(f"[RISK_ENGINE]   觸發條件: {current_price:.0f} <= {stop_price:.0f} ? {current_price <= stop_price}")
                        setattr(self, f'_last_trailing_active_log_{position_id}', current_time_stamp)

                if direction == 'LONG':
                    stop_price = peak_price - (peak_price - entry_price) * pullback_ratio

                    # 🚨 診斷LOG：詳細觸發檢查
                    self._log_debug(f"[RISK_ENGINE] 🔍 LONG移動停利檢查 - 部位{position['id']}:")
                    self._log_debug(f"[RISK_ENGINE]   當前價格:{current_price:.0f} <= 停利點:{stop_price:.0f} ? {current_price <= stop_price}")
                    self._log_debug(f"[RISK_ENGINE]   峰值:{peak_price:.0f} 進場:{entry_price:.0f} 回撤比例:{pullback_ratio*100:.0f}%")

                    if current_price <= stop_price:
                        pnl = stop_price - entry_price

                        # 🎯 保持：移動停利觸發是重要事件，立即顯示
                        self._log_important(f"[RISK_ENGINE] 💥 移動停利觸發! 部位{position['id']}(第{rule_config['lot_id']}口) @{current_price:.0f} 獲利{pnl:.0f}點")

                        return {
                            'position_id': position['id'],
                            'exit_price': stop_price,
                            'exit_time': current_time,
                            'exit_reason': '移動停利',
                            'pnl': pnl
                        }
                else:  # SHORT
                    stop_price = peak_price + (entry_price - peak_price) * pullback_ratio
                    if current_price >= stop_price:
                        pnl = entry_price - stop_price

                        # 🎯 保持：移動停利觸發是重要事件，立即顯示
                        self._log_important(f"[RISK_ENGINE] 💥 移動停利觸發! 部位{position['id']}(第{rule_config['lot_id']}口) @{current_price:.0f} 獲利{pnl:.0f}點")

                        return {
                            'position_id': position['id'],
                            'exit_price': stop_price,
                            'exit_time': current_time,
                            'exit_reason': '移動停利',
                            'pnl': pnl
                        }
            
            return None
            
        except Exception as e:
            self.logger.error(f"檢查移動停利條件失敗: {e}")
            return None
    
    def _update_position_risk_state(self, position: Dict, current_price: float, current_time: str):
        """更新部位風險管理狀態"""
        try:
            # 🔧 檢查必要欄位
            if position.get('entry_price') is None:
                self.logger.debug(f"跳過部位{position.get('id')}風險狀態更新: entry_price為None")
                return

            direction = position['direction']
            current_peak = position['peak_price'] or position['entry_price']
            position_id = position['id']

            # 🔍 DEBUG: 峰值價格更新追蹤 (這是快速變化的關鍵指標)
            if hasattr(self, 'console_enabled') and getattr(self, 'console_enabled', True):
                # 控制輸出頻率：只在峰值更新時輸出，避免過多日誌
                old_peak = current_peak

                # 檢查是否會更新峰值
                will_update_peak = False
                new_peak = current_peak

                if direction == 'LONG':
                    if current_price > current_peak:
                        will_update_peak = True
                        new_peak = current_price
                else:  # SHORT
                    if current_price < current_peak:
                        will_update_peak = True
                        new_peak = current_price

                # 🎯 修改：分級處理峰值更新LOG
                if will_update_peak:
                    improvement = abs(new_peak - old_peak)
                    total_profit = abs(new_peak - position['entry_price'])

                    # 🎯 重大峰值更新（>10點）作為重要事件，但加入頻率控制
                    if improvement >= 10:
                        # 🎯 頻率控制：20秒內最多顯示一次
                        current_time = time.time()
                        last_log_time = self.last_peak_log_time.get(position_id, 0)

                        if current_time - last_log_time >= self.peak_log_interval:
                            self._log_important(f"[RISK_ENGINE] 📈 重大峰值更新! 部位{position_id}: {old_peak:.0f}→{new_peak:.0f} (+{improvement:.0f}點)")
                            self.last_peak_log_time[position_id] = current_time
                        else:
                            # 🔧 頻率控制期間改為調試模式
                            self._log_debug(f"[RISK_ENGINE] 📈 峰值更新(頻率控制): 部位{position_id}: {old_peak:.0f}→{new_peak:.0f} (+{improvement:.0f}點)")
                    else:
                        # 🔧 小幅峰值更新改為調試模式
                        self._log_debug(f"[RISK_ENGINE] 📈 峰值價格更新! 部位{position_id}:")
                        self._log_debug(f"[RISK_ENGINE]   方向:{direction} 舊峰值:{old_peak:.0f} → 新峰值:{new_peak:.0f}")
                        self._log_debug(f"[RISK_ENGINE]   改善幅度:{improvement:.0f}點 總獲利:{total_profit:.0f}點")
                        self._log_debug(f"[RISK_ENGINE]   移動停利狀態:{'✅已啟動' if position.get('trailing_activated') else '⏳未啟動'}")

            # 更新峰值價格
            peak_updated = False
            if direction == 'LONG':
                if current_price > current_peak:
                    current_peak = current_price
                    peak_updated = True
            else:  # SHORT
                if current_price < current_peak:
                    current_peak = current_price
                    peak_updated = True

            # 如果峰值有更新，更新資料庫
            if peak_updated:
                # 🚀 零風險峰值更新：可選異步，預設同步
                if self.enable_async_peak_update and self.async_updater:
                    # 🚀 異步更新模式（靜默處理，避免過多日誌）
                    self.async_updater.schedule_peak_update(
                        position_id=position['id'],
                        peak_price=current_peak,
                        update_time=current_time,
                        update_category="價格更新",
                        update_message="峰值更新"
                    )
                else:
                    # 🛡️ 同步更新模式（預設，確保零風險）
                    self.db_manager.update_risk_management_state(
                        position_id=position['id'],
                        peak_price=current_peak,
                        update_time=current_time,
                        update_category="價格更新",
                        update_message="價格更新"
                    )
                
        except Exception as e:
            self.logger.error(f"更新風險狀態失敗: {e}")
    
    def _calculate_pnl(self, position: Dict, exit_price: float) -> float:
        """計算損益"""
        try:
            direction = position['direction']
            entry_price = position['entry_price']
            
            if direction == 'LONG':
                return exit_price - entry_price
            else:  # SHORT
                return entry_price - exit_price
                
        except Exception as e:
            self.logger.error(f"計算損益失敗: {e}")
            return 0.0
    
    def update_protective_stop_loss(self, exited_position_id: int, group_id: int) -> bool:
        """更新保護性停損 - 移植OrderTester.py邏輯"""
        try:
            # 🎯 修改：保護性停損更新詳細LOG改為調試模式
            self._log_debug(f"[RISK_ENGINE] 🛡️ 開始保護性停損更新:")
            self._log_debug(f"[RISK_ENGINE]   觸發部位: {exited_position_id} 組別: {group_id}")

            # 獲取該組的所有部位
            group_positions = self.db_manager.get_active_positions_by_group(group_id)

            # 🎯 修改：組別部位分析改為調試模式
            self._log_debug(f"[RISK_ENGINE]   組{group_id}活躍部位: {len(group_positions)}個")
            for pos in group_positions:
                pos_lot_id = json.loads(pos['rule_config'])['lot_id']
                self._log_debug(f"[RISK_ENGINE]     部位{pos['id']}: 第{pos_lot_id}口")

            # 找到下一口需要更新保護的部位
            exited_position = None
            next_position = None

            # 先找到已出場的部位資訊
            all_positions = self.db_manager.get_all_active_positions()
            for pos in all_positions:
                if pos['id'] == exited_position_id:
                    exited_position = pos
                    break

            if not exited_position:
                if hasattr(self, 'console_enabled') and getattr(self, 'console_enabled', True):
                    print(f"[RISK_ENGINE] ❌ 找不到已出場部位: {exited_position_id}")
                return False

            # 解析已出場部位的規則
            exited_rule = LotRule.from_json(exited_position['rule_config'])
            exited_lot_id = exited_rule.lot_id

            # 🎯 修改：已出場部位資訊改為調試模式
            self._log_debug(f"[RISK_ENGINE]   已出場部位: 第{exited_lot_id}口")

            # 找到下一口部位
            for pos in group_positions:
                pos_rule = LotRule.from_json(pos['rule_config'])
                if pos_rule.lot_id == exited_rule.lot_id + 1:
                    next_position = pos
                    break

            if not next_position or not next_position.get('rule_config'):
                if hasattr(self, 'console_enabled') and getattr(self, 'console_enabled', True):
                    print(f"[RISK_ENGINE] ℹ️ 找不到第{exited_lot_id + 1}口部位，無需更新保護性停損")
                return False

            next_rule = LotRule.from_json(next_position['rule_config'])
            next_lot_id = next_rule.lot_id

            # 🎯 修改：目標部位資訊改為調試模式
            self._log_debug(f"[RISK_ENGINE]   目標部位: {next_position['id']} 第{next_lot_id}口")
            self._log_debug(f"[RISK_ENGINE]   保護性停損倍數: {next_rule.protective_stop_multiplier}")

            # 🔧 檢查是否啟用保護性停損
            if not getattr(next_rule, 'use_protective_stop', True):
                if hasattr(self, 'console_enabled') and getattr(self, 'console_enabled', True):
                    print(f"[RISK_ENGINE] ⚠️ 第{next_lot_id}口未啟用保護性停損")
                return False

            if not next_rule.protective_stop_multiplier:
                if hasattr(self, 'console_enabled') and getattr(self, 'console_enabled', True):
                    print(f"[RISK_ENGINE] ⚠️ 第{next_lot_id}口沒有設定保護性停損倍數")
                return False

            # 檢查前面所有口單是否都獲利
            all_previous_profitable = self._check_all_previous_lots_profitable(
                group_id, next_rule.lot_id
            )

            # 🎯 修改：前置條件檢查改為調試模式
            self._log_debug(f"[RISK_ENGINE]   前面口單獲利檢查: {'✅通過' if all_previous_profitable else '❌失敗'}")

            if not all_previous_profitable:
                self.logger.info(f"前面有口單虧損，第{next_rule.lot_id}口維持原始停損")
                if hasattr(self, 'console_enabled') and getattr(self, 'console_enabled', True):
                    print(f"[RISK_ENGINE] ⚠️ 前面有口單虧損，第{next_lot_id}口維持原始停損")
                return False
            
            # 計算累積獲利並設定保護性停損
            total_profit = self._calculate_cumulative_profit(group_id, next_rule.lot_id)

            # 🎯 修改：獲利計算追蹤改為調試模式
            self._log_debug(f"[RISK_ENGINE]   累積獲利計算: {total_profit:.0f}點")

            if total_profit <= 0:
                self.logger.info(f"累積獲利不足({total_profit:.1f}點)，第{next_rule.lot_id}口維持原始停損")
                if hasattr(self, 'console_enabled') and getattr(self, 'console_enabled', True):
                    print(f"[RISK_ENGINE] ⚠️ 累積獲利不足({total_profit:.1f}點)，維持原始停損")
                return False

            # 設定保護性停損
            direction = next_position['direction']
            entry_price = next_position['entry_price']
            stop_loss_amount = total_profit * float(next_rule.protective_stop_multiplier)

            if direction == 'LONG':
                new_stop_loss = entry_price - stop_loss_amount
            else:  # SHORT
                # 🔧 修復：SHORT部位保護性停損應該是加法
                # 邏輯：SHORT部位止損在高點，保護性停損將止損點往更高價格移動
                # 例如：進場22542，獲利20點，2倍保護 → 22542 + (20 × 2.0) = 22582
                new_stop_loss = entry_price + stop_loss_amount

            # 🎯 修改：保護性停損計算詳情改為調試模式
            self._log_debug(f"[RISK_ENGINE] 🧮 保護性停損計算:")
            self._log_debug(f"[RISK_ENGINE]   方向:{direction} 進場價:{entry_price:.0f}")
            self._log_debug(f"[RISK_ENGINE]   累積獲利:{total_profit:.0f}點 × 倍數:{next_rule.protective_stop_multiplier}")
            self._log_debug(f"[RISK_ENGINE]   停損金額:{stop_loss_amount:.0f}點")
            self._log_debug(f"[RISK_ENGINE]   新停損價:{new_stop_loss:.0f}")

            # 🚀 更新風險管理狀態（異步化以避免延遲）
            current_time = datetime.now().strftime("%H:%M:%S")
            if self.enable_async_peak_update and self.async_updater:
                # 🚀 異步更新保護性停損
                self._log_debug(f"[RISK_ENGINE] 🚀 異步更新保護性停損: 部位{next_position['id']}")
                self.async_updater.schedule_protection_update(
                    position_id=next_position['id'],
                    current_stop_loss=new_stop_loss,
                    protection_activated=True,
                    update_time=current_time,
                    update_category="保護性停損更新",
                    update_message="保護性停損更新"
                )
            else:
                # 🛡️ 同步更新（備用模式）
                self._log_debug(f"[RISK_ENGINE] 💾 同步更新保護性停損: 部位{next_position['id']}")
                self.db_manager.update_risk_management_state(
                    position_id=next_position['id'],
                    current_stop_loss=new_stop_loss,
                    protection_activated=True,
                    update_time=current_time,
                    update_category="保護性停損更新",
                    update_message="保護性停損更新"
                )

            # 🔍 DEBUG: 更新完成確認
            if hasattr(self, 'console_enabled') and getattr(self, 'console_enabled', True):
                print(f"[RISK_ENGINE] ✅ 保護性停損更新完成!")
                print(f"[RISK_ENGINE]   部位{next_position['id']} 第{next_lot_id}口 → {new_stop_loss:.0f}")

            self.logger.info(f"第{next_rule.lot_id}口保護性停損更新: {new_stop_loss:.0f} (基於累積獲利 {total_profit:.0f})")
            return True

        except Exception as e:
            self.logger.error(f"更新保護性停損失敗: {e}")
            # 🎯 錯誤是重要事件，立即顯示
            self._log_important(f"[RISK_ENGINE] ❌ 保護性停損更新失敗: {e}")
            return False
    
    def _check_all_previous_lots_profitable(self, group_id: int, target_lot_id: int) -> bool:
        """檢查目標口單之前的所有口單是否都獲利"""
        try:
            # 這裡需要查詢已出場的部位記錄
            # 由於資料庫設計限制，這裡簡化實現
            return True  # 暫時返回True，實際應該查詢歷史記錄
            
        except Exception as e:
            self.logger.error(f"檢查前面口單獲利狀況失敗: {e}")
            return False
    
    def _calculate_cumulative_profit(self, group_id: int, target_lot_id: int) -> float:
        """計算累積獲利"""
        try:
            # 這裡需要查詢已出場的部位記錄並計算累積獲利
            # 由於資料庫設計限制，這裡簡化實現
            return 50.0  # 暫時返回固定值，實際應該查詢歷史記錄
            
        except Exception as e:
            self.logger.error(f"計算累積獲利失敗: {e}")
            return 0.0

    def _filter_active_positions(self, positions: List[Dict]) -> List[Dict]:
        """
        多層狀態過濾活躍部位 - 🔧 新增：參考建倉機制

        Args:
            positions: 原始部位列表

        Returns:
            List[Dict]: 過濾後的活躍部位列表
        """
        active_positions = []
        filtered_count = 0

        for position in positions:
            position_id = position.get('id')

            # 1. 基本狀態檢查
            if position.get('status') == 'EXITED':
                filtered_count += 1
                if self.console_enabled and hasattr(self, '_debug_filter'):
                    print(f"[RISK_ENGINE] 📋 部位{position_id}已平倉(資料庫)，跳過檢查")
                continue

            # 2. 檢查異步緩存狀態 (如果可用)
            if self.async_updater and hasattr(self.async_updater, 'is_position_exited_in_cache'):
                if self.async_updater.is_position_exited_in_cache(position_id):
                    filtered_count += 1
                    if self.console_enabled and hasattr(self, '_debug_filter'):
                        print(f"[RISK_ENGINE] 📋 部位{position_id}已平倉(緩存)，跳過檢查")
                    continue

            # 3. 檢查是否有進行中的平倉（如果有停損執行器）
            if hasattr(self, 'stop_loss_executor') and self.stop_loss_executor:
                if hasattr(self.stop_loss_executor, '_has_pending_exit_execution'):
                    if self.stop_loss_executor._has_pending_exit_execution(position_id):
                        filtered_count += 1
                        if self.console_enabled and hasattr(self, '_debug_filter'):
                            print(f"[RISK_ENGINE] 📋 部位{position_id}有進行中平倉，跳過檢查")
                        continue

            # 通過所有檢查，加入活躍部位列表
            active_positions.append(position)

        # 統計輸出（控制頻率）
        if filtered_count > 0 and self.console_enabled:
            if not hasattr(self, '_last_filter_log_time'):
                self._last_filter_log_time = 0

            current_time = time.time()
            if current_time - self._last_filter_log_time > 10.0:  # 每10秒輸出一次
                # 🎯 修改：狀態過濾改為調試模式
                self._log_debug(f"[RISK_ENGINE] 🔍 狀態過濾: 原始{len(positions)}個部位 → "
                              f"活躍{len(active_positions)}個部位 (過濾{filtered_count}個)")
                self._last_filter_log_time = current_time

        return active_positions

    def enable_filter_debug(self, enabled: bool = True):
        """
        啟用/停用過濾調試輸出 - 🔧 新增：調試工具

        Args:
            enabled: 是否啟用調試輸出
        """
        if enabled:
            self._debug_filter = True
        elif hasattr(self, '_debug_filter'):
            delattr(self, '_debug_filter')

        if self.console_enabled:
            status = "啟用" if enabled else "停用"
            print(f"[RISK_ENGINE] 🔧 過濾調試輸出已{status}")

if __name__ == "__main__":
    # 測試風險管理引擎
    print("🧪 測試風險管理引擎")
    print("=" * 50)
    
    from multi_group_database import MultiGroupDatabaseManager
    
    # 使用測試資料庫
    db_manager = MultiGroupDatabaseManager("test_risk_engine.db")
    
    # 創建風險管理引擎
    engine = RiskManagementEngine(db_manager)
    
    print("✅ 風險管理引擎創建成功")
    
    # 測試檢查出場條件（需要有測試數據）
    exit_actions = engine.check_all_exit_conditions(22540.0, "09:00:00")
    print(f"✅ 檢查出場條件: {len(exit_actions)} 個出場動作")
    
    print("✅ 風險管理引擎測試完成")
