#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
平倉機制統一管理器
整合所有平倉邏輯元件，提供統一的平倉機制管理介面
"""

import logging
import time
from datetime import datetime
from typing import Dict, List, Optional, Any
from dataclasses import dataclass

logger = logging.getLogger(__name__)

@dataclass
class ExitMechanismStatus:
    """平倉機制狀態"""
    enabled: bool
    total_positions: int
    active_positions: int
    exited_positions: int
    initial_stops: int
    protective_stops: int
    trailing_stops: int
    last_update_time: str

class ExitMechanismManager:
    """
    平倉機制統一管理器
    整合所有平倉邏輯元件
    """
    
    def __init__(self, db_manager, console_enabled: bool = True):
        """
        初始化平倉機制管理器
        
        Args:
            db_manager: 資料庫管理器
            console_enabled: 是否啟用Console日誌
        """
        self.db_manager = db_manager
        self.console_enabled = console_enabled
        
        # 平倉機制組件
        self.initial_stop_loss_manager = None
        self.stop_loss_monitor = None
        self.stop_loss_executor = None
        self.trailing_stop_activator = None
        self.peak_price_tracker = None
        self.drawdown_monitor = None
        self.protection_manager = None
        self.stop_loss_state_manager = None
        
        # 狀態管理
        self.enabled = False
        self.last_price_update = 0
        self.price_update_count = 0
        self.exit_events_count = 0
        
        if self.console_enabled:
            print("[EXIT_MANAGER] ⚙️ 平倉機制統一管理器初始化完成")

    def set_trackers(self, order_tracker=None, simplified_tracker=None):
        """
        設定FIFO追蹤器到停損執行器

        Args:
            order_tracker: 統一追蹤器
            simplified_tracker: 簡化追蹤器
        """
        if self.stop_loss_executor:
            self.stop_loss_executor.set_trackers(order_tracker, simplified_tracker)

            if self.console_enabled:
                print("[EXIT_MANAGER] 🔗 已設定停損執行器的FIFO追蹤器")

    def initialize_all_components(self):
        """初始化所有平倉機制組件"""
        try:
            if self.console_enabled:
                print("[EXIT_MANAGER] 🚀 開始初始化所有平倉機制組件...")
            
            # 初始化各個組件
            self._init_stop_loss_components()
            self._init_trailing_stop_components()
            self._init_protection_components()
            
            # 設定組件間的連接
            self._setup_component_connections()
            
            # 設定回調函數
            self._setup_callbacks()
            
            self.enabled = True
            
            if self.console_enabled:
                print("[EXIT_MANAGER] ✅ 所有平倉機制組件初始化完成")
                self._print_component_status()
            
            return True
            
        except Exception as e:
            logger.error(f"初始化平倉機制組件失敗: {e}")
            if self.console_enabled:
                print(f"[EXIT_MANAGER] ❌ 組件初始化失敗: {e}")
            return False
    
    def _init_stop_loss_components(self):
        """初始化停損相關組件"""
        try:
            from initial_stop_loss_manager import create_initial_stop_loss_manager
            from stop_loss_monitor import create_stop_loss_monitor
            from stop_loss_executor import create_stop_loss_executor
            
            self.initial_stop_loss_manager = create_initial_stop_loss_manager(
                self.db_manager, console_enabled=self.console_enabled
            )
            
            self.stop_loss_monitor = create_stop_loss_monitor(
                self.db_manager, console_enabled=self.console_enabled
            )
            
            self.stop_loss_executor = create_stop_loss_executor(
                self.db_manager, console_enabled=self.console_enabled
            )

            # 🔧 新增：設定停損執行器的FIFO追蹤器（稍後由外部設定）
            # 這裡暫時不設定，等待外部調用 set_trackers 方法

            if self.console_enabled:
                print("[EXIT_MANAGER] 🛡️ 停損組件初始化完成")
                
        except Exception as e:
            logger.error(f"初始化停損組件失敗: {e}")
            raise e
    
    def _init_trailing_stop_components(self):
        """初始化移動停利相關組件"""
        try:
            from trailing_stop_activator import create_trailing_stop_activator
            from peak_price_tracker import create_peak_price_tracker
            from drawdown_monitor import create_drawdown_monitor
            
            self.trailing_stop_activator = create_trailing_stop_activator(
                self.db_manager, console_enabled=self.console_enabled
            )
            
            self.peak_price_tracker = create_peak_price_tracker(
                self.db_manager, console_enabled=self.console_enabled
            )
            
            self.drawdown_monitor = create_drawdown_monitor(
                self.db_manager, console_enabled=self.console_enabled
            )
            
            if self.console_enabled:
                print("[EXIT_MANAGER] 🎯 移動停利組件初始化完成")
                
        except Exception as e:
            logger.error(f"初始化移動停利組件失敗: {e}")
            raise e
    
    def _init_protection_components(self):
        """初始化保護相關組件"""
        try:
            from cumulative_profit_protection_manager import create_cumulative_profit_protection_manager
            from stop_loss_state_manager import create_stop_loss_state_manager
            
            self.protection_manager = create_cumulative_profit_protection_manager(
                self.db_manager, console_enabled=self.console_enabled
            )
            
            self.stop_loss_state_manager = create_stop_loss_state_manager(
                self.db_manager, console_enabled=self.console_enabled
            )
            
            if self.console_enabled:
                print("[EXIT_MANAGER] 🛡️ 保護組件初始化完成")
                
        except Exception as e:
            logger.error(f"初始化保護組件失敗: {e}")
            raise e
    
    def _setup_component_connections(self):
        """設定組件間的連接"""
        try:
            # 連接保護管理器到停損執行器
            if self.stop_loss_executor and self.protection_manager:
                self.stop_loss_executor.set_protection_manager(self.protection_manager)
            
            if self.console_enabled:
                print("[EXIT_MANAGER] 🔗 組件連接設定完成")
                
        except Exception as e:
            logger.error(f"設定組件連接失敗: {e}")
            raise e
    
    def _setup_callbacks(self):
        """設定回調函數"""
        try:
            # 停損觸發回調
            def on_stop_loss_triggered(trigger_info):
                try:
                    if self.console_enabled:
                        print(f"[EXIT_MANAGER] 🚨 停損觸發: 部位 {trigger_info.position_id}")
                    
                    # 執行停損平倉
                    if self.stop_loss_executor:
                        result = self.stop_loss_executor.execute_stop_loss(trigger_info)
                        self.exit_events_count += 1
                        
                        if result.success and self.console_enabled:
                            print(f"[EXIT_MANAGER] ✅ 停損執行成功: {result.order_id}")
                            
                except Exception as e:
                    logger.error(f"停損觸發回調失敗: {e}")
            
            # 移動停利啟動回調
            def on_trailing_activated(activation_info):
                try:
                    if self.console_enabled:
                        print(f"[EXIT_MANAGER] 🎯 移動停利啟動: 部位 {activation_info.position_id}")
                        
                except Exception as e:
                    logger.error(f"移動停利啟動回調失敗: {e}")
            
            # 回撤觸發回調
            def on_drawdown_triggered(trigger_info):
                try:
                    if self.console_enabled:
                        print(f"[EXIT_MANAGER] 📉 回撤觸發: 部位 {trigger_info.position_id}")
                    
                    # 執行移動停利平倉
                    if self.stop_loss_executor:
                        from stop_loss_monitor import StopLossTrigger
                        
                        trailing_trigger = StopLossTrigger(
                            position_id=trigger_info.position_id,
                            group_id=trigger_info.group_id,
                            direction=trigger_info.direction,
                            current_price=trigger_info.current_price,
                            stop_loss_price=trigger_info.current_price,
                            trigger_time=trigger_info.trigger_time,
                            trigger_reason=f"移動停利: {trigger_info.trigger_reason}",
                            breach_amount=trigger_info.drawdown_points
                        )
                        
                        result = self.stop_loss_executor.execute_stop_loss(trailing_trigger)
                        self.exit_events_count += 1
                        
                        if result.success and self.console_enabled:
                            print(f"[EXIT_MANAGER] ✅ 移動停利執行成功: {result.order_id}")
                            
                except Exception as e:
                    logger.error(f"回撤觸發回調失敗: {e}")
            
            # 保護更新回調
            def on_protection_updated(update_info):
                try:
                    if self.console_enabled:
                        print(f"[EXIT_MANAGER] 🛡️ 保護更新: 部位 {update_info.position_id}")
                        
                except Exception as e:
                    logger.error(f"保護更新回調失敗: {e}")
            
            # 註冊回調函數
            if self.stop_loss_monitor:
                self.stop_loss_monitor.add_stop_loss_callback(on_stop_loss_triggered)
            
            if self.trailing_stop_activator:
                self.trailing_stop_activator.add_activation_callback(on_trailing_activated)
            
            if self.drawdown_monitor:
                self.drawdown_monitor.add_drawdown_callback(on_drawdown_triggered)
            
            if self.protection_manager:
                self.protection_manager.add_protection_callback(on_protection_updated)
            
            if self.console_enabled:
                print("[EXIT_MANAGER] 📞 回調函數設定完成")
                
        except Exception as e:
            logger.error(f"設定回調函數失敗: {e}")
            raise e
    
    def setup_initial_stops_for_group(self, group_id: int, range_data: Dict[str, float]) -> bool:
        """
        為策略組設定初始停損
        
        Args:
            group_id: 策略組ID
            range_data: 區間資料
            
        Returns:
            bool: 設定是否成功
        """
        try:
            if not self.enabled or not self.initial_stop_loss_manager:
                if self.console_enabled:
                    print("[EXIT_MANAGER] ⚠️ 平倉機制未啟用或組件未初始化")
                return False
            
            if self.console_enabled:
                print(f"[EXIT_MANAGER] 🛡️ 為策略組 {group_id} 設定初始停損")
            
            success = self.initial_stop_loss_manager.setup_initial_stop_loss_for_group(
                group_id, range_data
            )
            
            if success and self.console_enabled:
                print(f"[EXIT_MANAGER] ✅ 策略組 {group_id} 初始停損設定完成")
            
            return success
            
        except Exception as e:
            logger.error(f"設定初始停損失敗: {e}")
            if self.console_enabled:
                print(f"[EXIT_MANAGER] ❌ 初始停損設定失敗: {e}")
            return False
    
    def process_price_update(self, current_price: float, timestamp: str = None) -> Dict[str, int]:
        """
        處理價格更新，觸發所有相關的平倉檢查
        
        Args:
            current_price: 當前價格
            timestamp: 時間戳
            
        Returns:
            Dict[str, int]: 處理結果統計
        """
        if not self.enabled:
            return {'error': 1}
        
        if timestamp is None:
            timestamp = datetime.now().strftime('%H:%M:%S')
        
        try:
            self.last_price_update = time.time()
            self.price_update_count += 1
            
            results = {
                'stop_loss_triggers': 0,
                'trailing_activations': 0,
                'peak_updates': 0,
                'drawdown_triggers': 0
            }
            
            # 1. 檢查停損觸發
            if self.stop_loss_monitor:
                triggered_stops = self.stop_loss_monitor.monitor_stop_loss_breach(current_price, timestamp)
                results['stop_loss_triggers'] = len(triggered_stops)
            
            # 2. 檢查移動停利啟動
            if self.trailing_stop_activator:
                activations = self.trailing_stop_activator.check_trailing_stop_activation(current_price, timestamp)
                results['trailing_activations'] = len(activations)
            
            # 3. 更新峰值價格
            if self.peak_price_tracker:
                peak_updates = self.peak_price_tracker.update_peak_prices(current_price, timestamp)
                results['peak_updates'] = len(peak_updates)
            
            # 4. 檢查回撤觸發
            if self.drawdown_monitor:
                drawdown_triggers = self.drawdown_monitor.monitor_drawdown_triggers(current_price, timestamp)
                results['drawdown_triggers'] = len(drawdown_triggers)
            
            return results
            
        except Exception as e:
            logger.error(f"處理價格更新失敗: {e}")
            return {'error': 1}
    
    def get_exit_mechanism_status(self) -> ExitMechanismStatus:
        """取得平倉機制狀態"""
        try:
            # 查詢部位統計
            with self.db_manager.get_connection() as conn:
                cursor = conn.cursor()
                
                # 總部位數
                cursor.execute("SELECT COUNT(*) FROM position_records")
                total_positions = cursor.fetchone()[0]
                
                # 活躍部位數
                cursor.execute("SELECT COUNT(*) FROM position_records WHERE status = 'ACTIVE'")
                active_positions = cursor.fetchone()[0]
                
                # 已平倉部位數
                cursor.execute("SELECT COUNT(*) FROM position_records WHERE status = 'EXITED'")
                exited_positions = cursor.fetchone()[0]
                
                # 停損狀態統計
                cursor.execute("SELECT COUNT(*) FROM position_records WHERE status = 'ACTIVE' AND is_initial_stop = TRUE")
                initial_stops = cursor.fetchone()[0]
                
                cursor.execute("SELECT COUNT(*) FROM position_records WHERE status = 'ACTIVE' AND is_initial_stop = FALSE AND trailing_activated = FALSE")
                protective_stops = cursor.fetchone()[0]
                
                cursor.execute("SELECT COUNT(*) FROM position_records WHERE status = 'ACTIVE' AND trailing_activated = TRUE")
                trailing_stops = cursor.fetchone()[0]
            
            return ExitMechanismStatus(
                enabled=self.enabled,
                total_positions=total_positions,
                active_positions=active_positions,
                exited_positions=exited_positions,
                initial_stops=initial_stops,
                protective_stops=protective_stops,
                trailing_stops=trailing_stops,
                last_update_time=datetime.fromtimestamp(self.last_price_update).strftime('%H:%M:%S') if self.last_price_update > 0 else "未開始"
            )
            
        except Exception as e:
            logger.error(f"取得平倉機制狀態失敗: {e}")
            return ExitMechanismStatus(False, 0, 0, 0, 0, 0, 0, "錯誤")
    
    def _print_component_status(self):
        """列印組件狀態"""
        if not self.console_enabled:
            return
        
        print("[EXIT_MANAGER] 📊 平倉機制組件狀態:")
        print(f"[EXIT_MANAGER]   初始停損管理器: {'✅' if self.initial_stop_loss_manager else '❌'}")
        print(f"[EXIT_MANAGER]   停損監控器: {'✅' if self.stop_loss_monitor else '❌'}")
        print(f"[EXIT_MANAGER]   停損執行器: {'✅' if self.stop_loss_executor else '❌'}")
        print(f"[EXIT_MANAGER]   移動停利啟動器: {'✅' if self.trailing_stop_activator else '❌'}")
        print(f"[EXIT_MANAGER]   峰值價格追蹤器: {'✅' if self.peak_price_tracker else '❌'}")
        print(f"[EXIT_MANAGER]   回撤監控器: {'✅' if self.drawdown_monitor else '❌'}")
        print(f"[EXIT_MANAGER]   保護管理器: {'✅' if self.protection_manager else '❌'}")
        print(f"[EXIT_MANAGER]   狀態管理器: {'✅' if self.stop_loss_state_manager else '❌'}")
    
    def print_exit_mechanism_status(self):
        """列印平倉機制狀態 (Console輸出)"""
        if not self.console_enabled:
            return
        
        status = self.get_exit_mechanism_status()
        
        print(f"[EXIT_MANAGER] 📊 平倉機制狀態總覽:")
        print(f"[EXIT_MANAGER]   系統狀態: {'🟢 啟用' if status.enabled else '🔴 停用'}")
        print(f"[EXIT_MANAGER]   總部位數: {status.total_positions}")
        print(f"[EXIT_MANAGER]   活躍部位: {status.active_positions}")
        print(f"[EXIT_MANAGER]   已平倉: {status.exited_positions}")
        print(f"[EXIT_MANAGER]   初始停損: {status.initial_stops}")
        print(f"[EXIT_MANAGER]   保護停損: {status.protective_stops}")
        print(f"[EXIT_MANAGER]   移動停利: {status.trailing_stops}")
        print(f"[EXIT_MANAGER]   最後更新: {status.last_update_time}")
        print(f"[EXIT_MANAGER]   價格更新次數: {self.price_update_count}")
        print(f"[EXIT_MANAGER]   平倉事件次數: {self.exit_events_count}")


def create_exit_mechanism_manager(db_manager, console_enabled: bool = True) -> ExitMechanismManager:
    """
    創建平倉機制統一管理器的工廠函數
    
    Args:
        db_manager: 資料庫管理器
        console_enabled: 是否啟用Console日誌
        
    Returns:
        ExitMechanismManager: 平倉機制管理器實例
    """
    return ExitMechanismManager(db_manager, console_enabled)


if __name__ == "__main__":
    # 測試用途
    print("平倉機制統一管理器模組")
    print("請在主程式中調用 create_exit_mechanism_manager() 函數")
