#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
停損執行器
負責執行停損平倉邏輯，整合現有下單系統
"""

import logging
import time
from datetime import datetime
from typing import Dict, List, Optional, Any
from dataclasses import dataclass

logger = logging.getLogger(__name__)

@dataclass
class StopLossExecutionResult:
    """停損執行結果"""
    position_id: int
    success: bool
    order_id: Optional[str] = None
    execution_price: Optional[float] = None
    execution_time: Optional[str] = None
    error_message: Optional[str] = None
    pnl: Optional[float] = None

class StopLossExecutor:
    """
    停損執行器
    負責執行停損平倉邏輯
    """

    def __init__(self, db_manager, virtual_real_order_manager=None, console_enabled: bool = True):
        """
        初始化停損執行器

        Args:
            db_manager: 資料庫管理器
            virtual_real_order_manager: 虛實單管理器 (可選)
            console_enabled: 是否啟用Console日誌
        """
        self.db_manager = db_manager
        self.virtual_real_order_manager = virtual_real_order_manager
        self.console_enabled = console_enabled
        self.execution_history: List[StopLossExecutionResult] = []
        self.protection_manager = None  # 累積獲利保護管理器 (稍後設定)
        self.success_callbacks: List = []  # 成功平倉回調函數

        if self.console_enabled:
            print("[STOP_EXECUTOR] ⚙️ 停損執行器初始化完成")
            if virtual_real_order_manager:
                print("[STOP_EXECUTOR] 🔗 已連接虛實單管理器")
            else:
                print("[STOP_EXECUTOR] ⚠️ 未連接虛實單管理器，將使用模擬模式")

    def set_protection_manager(self, protection_manager):
        """
        設定累積獲利保護管理器

        Args:
            protection_manager: 累積獲利保護管理器實例
        """
        self.protection_manager = protection_manager
        if self.console_enabled:
            print("[STOP_EXECUTOR] 🛡️ 已連接累積獲利保護管理器")

    def add_success_callback(self, callback):
        """
        添加成功平倉回調函數

        Args:
            callback: 回調函數，接收 (trigger_info, execution_result) 參數
        """
        self.success_callbacks.append(callback)
        if self.console_enabled:
            print(f"[STOP_EXECUTOR] 📞 添加成功回調函數: {callback.__name__}")
    
    def execute_stop_loss(self, trigger_info) -> StopLossExecutionResult:
        """
        執行停損平倉
        
        Args:
            trigger_info: 停損觸發資訊 (StopLossTrigger)
            
        Returns:
            StopLossExecutionResult: 執行結果
        """
        try:
            position_id = trigger_info.position_id
            current_price = trigger_info.current_price
            
            if self.console_enabled:
                print(f"[STOP_EXECUTOR] 🚨 開始執行停損平倉")
                print(f"[STOP_EXECUTOR]   部位ID: {position_id}")
                print(f"[STOP_EXECUTOR]   觸發價格: {current_price}")
                print(f"[STOP_EXECUTOR]   方向: {trigger_info.direction}")
            
            # 取得部位詳細資訊
            position_info = self._get_position_info(position_id)
            if not position_info:
                error_msg = f"無法取得部位 {position_id} 的詳細資訊"
                if self.console_enabled:
                    print(f"[STOP_EXECUTOR] ❌ {error_msg}")
                return StopLossExecutionResult(position_id, False, error_message=error_msg)
            
            # 計算平倉參數
            exit_direction = "SHORT" if trigger_info.direction == "LONG" else "LONG"
            quantity = 1  # 每次平倉1口
            
            if self.console_enabled:
                print(f"[STOP_EXECUTOR] 📋 平倉參數:")
                print(f"[STOP_EXECUTOR]   平倉方向: {exit_direction}")
                print(f"[STOP_EXECUTOR]   平倉數量: {quantity} 口")
                print(f"[STOP_EXECUTOR]   預期價格: {current_price}")
            
            # 執行平倉下單
            execution_result = self._execute_exit_order(
                position_info, exit_direction, quantity, current_price, trigger_info
            )
            
            # 更新資料庫
            if execution_result.success:
                self._update_position_exit_status(position_id, execution_result, trigger_info)

                # 🛡️ 觸發保護性停損更新 (如果是移動停利成功平倉)
                self._trigger_protection_update_if_needed(trigger_info, execution_result)

                # 觸發成功回調函數
                self._trigger_success_callbacks(trigger_info, execution_result)

            # 記錄執行歷史
            self.execution_history.append(execution_result)

            if self.console_enabled:
                if execution_result.success:
                    print(f"[STOP_EXECUTOR] ✅ 停損平倉執行成功")
                    print(f"[STOP_EXECUTOR]   訂單ID: {execution_result.order_id}")
                    print(f"[STOP_EXECUTOR]   執行價格: {execution_result.execution_price}")
                    print(f"[STOP_EXECUTOR]   損益: {execution_result.pnl:.1f} 點")
                else:
                    print(f"[STOP_EXECUTOR] ❌ 停損平倉執行失敗: {execution_result.error_message}")

            return execution_result
            
        except Exception as e:
            error_msg = f"停損執行過程發生錯誤: {e}"
            logger.error(error_msg)
            if self.console_enabled:
                print(f"[STOP_EXECUTOR] ❌ {error_msg}")
            return StopLossExecutionResult(trigger_info.position_id, False, error_message=error_msg)
    
    def _get_position_info(self, position_id: int) -> Optional[Dict]:
        """取得部位詳細資訊"""
        try:
            with self.db_manager.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    SELECT pr.*, sg.range_high, sg.range_low, sg.direction as group_direction
                    FROM position_records pr
                    JOIN strategy_groups sg ON pr.group_id = sg.id
                    WHERE pr.id = ? AND pr.status = 'ACTIVE'
                ''', (position_id,))
                
                row = cursor.fetchone()
                if row:
                    columns = [description[0] for description in cursor.description]
                    return dict(zip(columns, row))
                return None
                
        except Exception as e:
            logger.error(f"查詢部位資訊失敗: {e}")
            return None
    
    def _execute_exit_order(self, position_info: Dict, exit_direction: str, 
                          quantity: int, current_price: float, trigger_info) -> StopLossExecutionResult:
        """
        執行平倉下單
        
        Args:
            position_info: 部位資訊
            exit_direction: 平倉方向
            quantity: 平倉數量
            current_price: 當前價格
            trigger_info: 觸發資訊
            
        Returns:
            StopLossExecutionResult: 執行結果
        """
        position_id = position_info['id']
        
        try:
            if self.virtual_real_order_manager:
                # 使用真實下單系統
                result = self._execute_real_exit_order(
                    position_info, exit_direction, quantity, current_price
                )
            else:
                # 使用模擬下單
                result = self._execute_simulated_exit_order(
                    position_info, exit_direction, quantity, current_price
                )
            
            return result
            
        except Exception as e:
            error_msg = f"平倉下單執行失敗: {e}"
            logger.error(error_msg)
            return StopLossExecutionResult(position_id, False, error_message=error_msg)
    
    def _execute_real_exit_order(self, position_info: Dict, exit_direction: str, 
                               quantity: int, current_price: float) -> StopLossExecutionResult:
        """執行真實平倉下單"""
        position_id = position_info['id']
        
        try:
            # 使用虛實單管理器執行平倉
            signal_source = f"stop_loss_exit_{position_id}"
            
            order_result = self.virtual_real_order_manager.execute_strategy_order(
                direction=exit_direction,
                quantity=quantity,
                signal_source=signal_source,
                order_type="FOK",  # 使用FOK確保立即成交或取消
                price=current_price
            )
            
            if order_result and hasattr(order_result, 'success') and order_result.success:
                # 計算損益
                entry_price = position_info.get('entry_price', current_price)
                pnl = self._calculate_pnl(
                    position_info['direction'], entry_price, current_price
                )
                
                return StopLossExecutionResult(
                    position_id=position_id,
                    success=True,
                    order_id=getattr(order_result, 'order_id', None),
                    execution_price=current_price,
                    execution_time=datetime.now().strftime('%H:%M:%S'),
                    pnl=pnl
                )
            else:
                error_msg = getattr(order_result, 'error_message', '下單失敗')
                return StopLossExecutionResult(position_id, False, error_message=error_msg)
                
        except Exception as e:
            return StopLossExecutionResult(position_id, False, error_message=str(e))
    
    def _execute_simulated_exit_order(self, position_info: Dict, exit_direction: str, 
                                    quantity: int, current_price: float) -> StopLossExecutionResult:
        """執行模擬平倉下單"""
        position_id = position_info['id']
        
        try:
            # 模擬下單成功
            order_id = f"SIM_STOP_{position_id}_{int(time.time())}"
            
            # 計算損益
            entry_price = position_info.get('entry_price', current_price)
            pnl = self._calculate_pnl(
                position_info['direction'], entry_price, current_price
            )
            
            if self.console_enabled:
                print(f"[STOP_EXECUTOR] 🎭 模擬平倉執行:")
                print(f"[STOP_EXECUTOR]   模擬訂單ID: {order_id}")
                print(f"[STOP_EXECUTOR]   進場價格: {entry_price}")
                print(f"[STOP_EXECUTOR]   平倉價格: {current_price}")
                print(f"[STOP_EXECUTOR]   模擬損益: {pnl:.1f} 點")
            
            return StopLossExecutionResult(
                position_id=position_id,
                success=True,
                order_id=order_id,
                execution_price=current_price,
                execution_time=datetime.now().strftime('%H:%M:%S'),
                pnl=pnl
            )
            
        except Exception as e:
            return StopLossExecutionResult(position_id, False, error_message=str(e))
    
    def _calculate_pnl(self, direction: str, entry_price: float, exit_price: float) -> float:
        """
        計算損益點數
        
        Args:
            direction: 交易方向
            entry_price: 進場價格
            exit_price: 出場價格
            
        Returns:
            float: 損益點數
        """
        if direction == "LONG":
            return exit_price - entry_price
        elif direction == "SHORT":
            return entry_price - exit_price
        else:
            return 0.0
    
    def _update_position_exit_status(self, position_id: int, execution_result: StopLossExecutionResult, 
                                   trigger_info):
        """更新部位出場狀態"""
        try:
            with self.db_manager.get_connection() as conn:
                cursor = conn.cursor()
                
                # 更新 position_records
                cursor.execute('''
                    UPDATE position_records 
                    SET status = 'EXITED',
                        exit_price = ?,
                        exit_time = ?,
                        exit_reason = 'INITIAL_STOP',
                        exit_trigger_type = 'INITIAL_STOP',
                        exit_order_id = ?,
                        realized_pnl = ?,
                        updated_at = CURRENT_TIMESTAMP
                    WHERE id = ?
                ''', (
                    execution_result.execution_price,
                    execution_result.execution_time,
                    execution_result.order_id,
                    execution_result.pnl,
                    position_id
                ))
                
                # 更新 exit_events
                cursor.execute('''
                    UPDATE exit_events 
                    SET execution_status = 'EXECUTED',
                        exit_price = ?,
                        execution_time = ?,
                        pnl = ?,
                        order_id = ?
                    WHERE position_id = ? AND event_type = 'INITIAL_STOP' AND execution_status = 'PENDING'
                ''', (
                    execution_result.execution_price,
                    execution_result.execution_time,
                    execution_result.pnl,
                    execution_result.order_id,
                    position_id
                ))
                
                conn.commit()
                
                if self.console_enabled:
                    print(f"[STOP_EXECUTOR] 📝 部位 {position_id} 出場狀態已更新")
                    
        except Exception as e:
            logger.error(f"更新部位出場狀態失敗: {e}")
            if self.console_enabled:
                print(f"[STOP_EXECUTOR] ❌ 更新部位狀態失敗: {e}")

    def _trigger_protection_update_if_needed(self, trigger_info, execution_result):
        """
        如果需要，觸發保護性停損更新

        Args:
            trigger_info: 觸發資訊
            execution_result: 執行結果
        """
        try:
            # 檢查是否為移動停利平倉且有獲利
            if (execution_result.pnl and execution_result.pnl > 0 and
                hasattr(trigger_info, 'trigger_reason') and
                "移動停利" in trigger_info.trigger_reason):

                if self.protection_manager:
                    if self.console_enabled:
                        print(f"[STOP_EXECUTOR] 🛡️ 觸發保護性停損更新")
                        print(f"[STOP_EXECUTOR]   成功平倉部位: {trigger_info.position_id}")
                        print(f"[STOP_EXECUTOR]   獲利: {execution_result.pnl:.1f} 點")

                    # 更新策略組的保護性停損
                    protection_updates = self.protection_manager.update_protective_stops_for_group(
                        trigger_info.group_id, trigger_info.position_id
                    )

                    if protection_updates and self.console_enabled:
                        print(f"[STOP_EXECUTOR] ✅ 已更新 {len(protection_updates)} 個保護性停損")
                else:
                    if self.console_enabled:
                        print(f"[STOP_EXECUTOR] ⚠️ 未設定保護管理器，跳過保護更新")

        except Exception as e:
            logger.error(f"觸發保護更新失敗: {e}")
            if self.console_enabled:
                print(f"[STOP_EXECUTOR] ❌ 保護更新觸發失敗: {e}")

    def _trigger_success_callbacks(self, trigger_info, execution_result):
        """
        觸發成功平倉回調函數

        Args:
            trigger_info: 觸發資訊
            execution_result: 執行結果
        """
        for callback in self.success_callbacks:
            try:
                callback(trigger_info, execution_result)
            except Exception as e:
                logger.error(f"成功回調函數執行失敗: {e}")
                if self.console_enabled:
                    print(f"[STOP_EXECUTOR] ❌ 回調函數 {callback.__name__} 執行失敗: {e}")

    def get_execution_summary(self) -> Dict:
        """取得執行摘要"""
        total_executions = len(self.execution_history)
        successful_executions = len([r for r in self.execution_history if r.success])
        
        return {
            'total_executions': total_executions,
            'successful_executions': successful_executions,
            'failed_executions': total_executions - successful_executions,
            'success_rate': (successful_executions / total_executions * 100) if total_executions > 0 else 0
        }
    
    def print_execution_summary(self):
        """列印執行摘要 (Console輸出)"""
        if not self.console_enabled:
            return
        
        summary = self.get_execution_summary()
        
        print(f"[STOP_EXECUTOR] 📊 停損執行摘要:")
        print(f"[STOP_EXECUTOR]   總執行次數: {summary['total_executions']}")
        print(f"[STOP_EXECUTOR]   成功次數: {summary['successful_executions']}")
        print(f"[STOP_EXECUTOR]   失敗次數: {summary['failed_executions']}")
        print(f"[STOP_EXECUTOR]   成功率: {summary['success_rate']:.1f}%")


def create_stop_loss_executor(db_manager, virtual_real_order_manager=None, 
                            console_enabled: bool = True) -> StopLossExecutor:
    """
    創建停損執行器的工廠函數
    
    Args:
        db_manager: 資料庫管理器
        virtual_real_order_manager: 虛實單管理器 (可選)
        console_enabled: 是否啟用Console日誌
        
    Returns:
        StopLossExecutor: 停損執行器實例
    """
    return StopLossExecutor(db_manager, virtual_real_order_manager, console_enabled)


if __name__ == "__main__":
    # 測試用途
    print("停損執行器模組")
    print("請在主程式中調用 create_stop_loss_executor() 函數")
